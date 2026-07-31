"""CombatSystem (Phase 4, Task 17 of the ECS restructure) — combat on entities.

Mirrors the legacy ``_do_attack``/``_do_skill``/``_do_ultimate``/
``_on_enemy_hit``/``_on_enemy_death`` bodies from ``src/scenes/world.py``,
but operates on ECS entity components (``Combat``, ``Health``, ``Statuses``)
instead of ``WorldCharacter``/``WorldEnemy``. Runs IN PARALLEL with the legacy
combat path (additive) — the legacy path stays the source of truth until
Task 20 (full takeover). The system does NOT spawn projectiles/particles/drops
(those are Task 20's full integration); it computes damage + energy + cooldowns
on entities self-containedly.

Damage formula (mirrors legacy ``_do_attack`` melee, world.py:1505-1514):
    mult = element_mult(atk_el, def_el)
    is_crit = random.random() < crit_chance
    combo_mul = 1.0 + combo_count * COMBO_BONUS_PER
    dmg = int(atk * (1.0 + random.uniform(-0.1, 0.2)) * mult
              * (crit_mul if is_crit else 1.0) * combo_mul)
    dmg = max(1, int(dmg))           # WorldEnemy.take_damage
    target.hp -= dmg

Energy gain (mirrors ``wc.add_energy(ENERGY_GAIN_BASIC)``):
    energy = min(max_energy, energy + ENERGY_GAIN_BASIC)

Cooldown: ``atk_cd = AA_CD`` (0.32s).

The ``stat_obj`` on ``Combat`` is the ``Hero``/``Enemy`` instance — used for
crit chance, crit damage bonus, passive modifiers, skill energy cost, and the
ultimate id. The entity ``Health`` component is kept in sync with ``stat_obj``
after each mutation so callers reading either see consistent values.
"""
import math
import random

import src.audio as audio
import src.world.data as WD
from src.data.elements import (ELEMENT_COLORS, REACTION_WINDOW, WET_EFFECT,
    reaction_for)
from src.data.equipment import EQUIPMENT_DB
from src.data.heroes import ULTIMATE_VARIANTS, hero_abilities
from src.data.progression import ACHIEVEMENTS
from src.data.skills import SKILLS_DB
from src.data.story import (STORY_BIOME_QUEST, STORY_FINAL_QUEST,
    STORY_QUEST_BY_ID, STORY_QUEST_ORDER)
from src.data.tuning import (AA_CD, BASE_CRIT_CHANCE, COMBO_BONUS_PER,
    COMBO_MAX, COMBO_MILESTONE_SKILL, COMBO_MILESTONE_ULT,
    ENERGY_GAIN_BASIC, ENERGY_GAIN_DEAL, ENERGY_START, element_mult)
from src.entities import (FloatText, Particle, Projectile, SummonAlly, Trap,
    WEAPON_STYLE)
from src.entities.components import Combat, Health, Statuses, Identity, Transform


# ---------------------------------------------------------------------------
# Aim-preview thresholds (Task B2) — copied verbatim from world.py so this
# module is self-contained (no circular import on src.scenes.world). The
# values MUST stay in sync with world.py's module-level constants.
# ---------------------------------------------------------------------------
AIM_MAX_RANGE = 300.0


# ---------------------------------------------------------------------------
# Weapon style lookup (champion id -> weapon) — copied verbatim from the
# bottom of world.py so combat.py doesn't import src.scenes.world (circular).
# Cached per hero_id; the descriptor is static (baked at build time).
# ---------------------------------------------------------------------------
import src.build.champions as _CH
_WEAPON_STYLE_CACHE = {}
def WEAPON_STYLE_KEY(hero_id):
    w = _WEAPON_STYLE_CACHE.get(hero_id)
    if w is None:
        c = _CH.CHAMPION_BY_KEY.get(hero_id)
        w = c["descriptor"]["weapon"] if c is not None else "sword"
        _WEAPON_STYLE_CACHE[hero_id] = w
    return w


def _seg_hit(x1, y1, x2, y2, px, py, r):
    """Point-to-segment distance < r — the beam skill's line hit-scan test.
    Returns True if the point (px, py) is within r of the segment (x1,y1)-(x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    seg2 = dx * dx + dy * dy
    if seg2 <= 0:
        return math.hypot(px - x1, py - y1) < r
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / seg2))
    cx, cy = x1 + t * dx, y1 + t * dy
    return math.hypot(px - cx, py - cy) < r


# ---------------------------------------------------------------------------
# Signature passive handlers (C6) — dict-lookup dispatch, NOT if/elif chains.
# These run in the combat system (where they need scene state: the enemy list,
# particles, audio, the camera). Each hook point has its own dict mapping
# kind -> handler, so only the relevant handler runs at that point. The
# signature is ADDITIONAL to the shared base passive — these run in addition to
# the lifesteal/thorns/shield_when_low/etc. handlers in _do_attack /
# _on_enemy_death, not instead of them.
# ---------------------------------------------------------------------------

def _sig_cleave(scene, wc, primary_x, primary_y, atk):
    """cleave: basic attacks splash to enemies within 60px of the primary
    target. val is the fraction of ATK dealt as splash (0.5 = 50%). Skips the
    primary target (already hit by the main arc) and dead enemies. The splash
    is a separate damage roll (not the main arc) so it doesn't double-dip with
    the combo multiplier that's already applied to the main hit."""
    sig = wc.hero.signature
    if not sig or sig.get("kind") != "cleave":
        return
    cleave_dmg = int(atk * sig.get("val", 0.5))
    col = ELEMENT_COLORS.get(wc.element, ((200, 200, 200),))[0]
    for en in scene.enemies:
        if not en.alive:
            continue
        # skip the primary target (already hit by the main arc)
        if math.hypot(en.x - primary_x, en.y - primary_y) < 5:
            continue
        if math.hypot(en.x - primary_x, en.y - primary_y) < 60 + en.r:
            dealt = en.take_damage(cleave_dmg, wc.x, wc.y, False,
                                   on_attack=scene._on_enemy_event)
            if dealt > 0:
                scene._on_enemy_hit(en, wc, dealt, False)
    # a subtle slash streak so the splash reads visually
    scene.particles.spark(primary_x, primary_y, col, n=6, speed=160, size=4, life=0.2)

def _sig_stacking_atk(scene, wc):
    """stacking_atk: +val ATK per kill (stacking). The stack is read in
    WorldCharacter.effective_atk (via _SIG_ATK_MOD) and decays out of combat
    (via _SIG_UPDATE in world_entities). Reset the decay timer here so a fresh
    kill restarts the out-of-combat countdown."""
    sig = wc.hero.signature
    if not sig or sig.get("kind") != "stacking_atk":
        return
    wc._kill_stack += 1
    wc._kill_stack_t = 0.0

# Dispatch dict for the _do_attack hook point (kind -> handler).
_SIG_ATTACK = {"cleave": _sig_cleave}
# Dispatch dict for the _on_enemy_death hook point (kind -> handler).
_SIG_ON_KILL = {"stacking_atk": _sig_stacking_atk}


class CombatSystem:
    """ECS combat system — basic_attack, use_skill, use_ultimate, on_hit,
    on_death. Operates on entity components; the legacy combat methods in
    WorldScene stay running (21-test suite). Full takeover is Task 20.

    Parameters
    ----------
    world : World
        The ECS entity world.
    data_bundle : object or None
        Reserved for future use — the data modules (skills, tuning, elements,
        heroes) are imported at module level. Kept in the signature per the
        task brief's interface contract.
    scene : WorldScene or None
        The owning scene. Used to read scene-level state (combo counter,
        elemental resonance crit_dmg). May be None for headless tests.
    """

    def __init__(self, world, data_bundle=None, scene=None):
        self.world = world
        self.data = data_bundle
        self.scene = scene
        # per-entity skill cooldowns: eid -> [cd0, cd1, cd2]
        self._skill_cd = {}
        # per-entity element aura for reactions: eid -> [last_element, timer]
        self._element_aura = {}
        # callbacks wired by WorldScene (full drop/combo/signature integration
        # is Task 20; for this task these are minimal stubs)
        self.on_death_callback = None
        self.on_hit_callback = None

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _entity(self, eid):
        return self.world.entities.get(eid)

    def _combo_count(self):
        """Read the scene's combo counter (0 if no scene)."""
        if self.scene is not None:
            return getattr(self.scene, "_combo_count", 0)
        return 0

    def _res_crit_dmg(self):
        """Read the scene's elemental resonance crit_dmg bonus (0 if none)."""
        if self.scene is not None and hasattr(self.scene, "_resonance"):
            return self.scene._resonance("crit_dmg")
        return 0

    def _nearest_enemy(self, attacker_eid):
        """Find the nearest enemy entity to the attacker (by Transform)."""
        attacker = self._entity(attacker_eid)
        at = attacker.get(Transform) if attacker else None
        best = None
        best_d = 1e9
        for e in self.world.enemies():
            t = e.get(Transform)
            if t is None:
                continue
            if at is not None:
                d = ((t.x - at.x) ** 2 + (t.y - at.y) ** 2) ** 0.5
            else:
                d = 0.0
            if d < best_d:
                best_d = d
                best = e
        return best

    # ------------------------------------------------------------------
    # basic attack
    # ------------------------------------------------------------------
    def basic_attack(self, attacker_eid, target_eid=None):
        """Mirror the legacy ``_do_attack`` melee damage formula on entities.

        - Reads ``Combat`` (element, atk, atk_cd) + ``Health`` (energy) +
          ``Combat.stat_obj`` (the Hero — for crit chance/passive modifiers).
        - If ``atk_cd > 0``: return 0 (on cooldown).
        - Sets ``Combat.atk_cd = AA_CD``.
        - Computes damage with element_mult + crit + combo bonus.
        - Reduces target ``Health.hp``.
        - Gains attacker ``Health.energy += ENERGY_GAIN_BASIC`` (capped at
          ``stat_obj.max_energy``).
        - Returns the damage dealt.
        """
        attacker = self._entity(attacker_eid)
        if attacker is None:
            return 0
        combat = attacker.get(Combat)
        health = attacker.get(Health)
        if combat is None or health is None:
            return 0
        # on cooldown — no-op (mirrors legacy ``if wc.atk_cd > 0: return``)
        if combat.atk_cd > 0:
            return 0
        # set the AA cooldown
        combat.atk_cd = AA_CD
        stat_obj = combat.stat_obj

        # crit chance: base + ascension/role/tree bonuses + keen-eye passive
        crit_chance = BASE_CRIT_CHANCE
        if stat_obj is not None:
            crit_chance = getattr(stat_obj, "crit_chance", BASE_CRIT_CHANCE)
            passive = getattr(stat_obj, "passive", None)
            if passive and passive.get("kind") == "crit_up":
                crit_chance += passive.get("val", 0.1)

        # crit damage multiplier: 1.6 + tree crit_dmg + resonance crit_dmg
        crit_mul = 1.6
        if stat_obj is not None:
            crit_mul = 1.6 + getattr(stat_obj, "crit_dmg_bonus", 0)
        crit_mul += self._res_crit_dmg()

        atk = combat.atk
        element = combat.element

        # resolve target
        if target_eid is None:
            target = self._nearest_enemy(attacker_eid)
            if target is None:
                return 0
        else:
            target = self._entity(target_eid)
        if target is None:
            return 0
        t_combat = target.get(Combat)
        t_health = target.get(Health)
        if t_combat is None or t_health is None:
            return 0

        # damage formula (mirrors legacy _do_attack melee, world.py:1509-1513)
        mult = element_mult(element, t_combat.element)
        is_crit = random.random() < crit_chance
        combo_mul = 1.0 + max(0, self._combo_count()) * COMBO_BONUS_PER
        dmg = int(atk * (1.0 + random.uniform(-0.1, 0.2)) * mult
                  * (crit_mul if is_crit else 1.0) * combo_mul)
        # WorldEnemy.take_damage: dmg = max(1, int(amount)); hp -= dmg
        dmg = max(1, int(dmg))
        t_health.hp -= dmg
        if t_health.hp <= 0:
            t_health.hp = 0
            self.on_death(target.eid, attacker_eid)
        else:
            self.on_hit(target.eid, attacker_eid, dmg, is_crit)

        # energy gain (mirrors wc.add_energy(ENERGY_GAIN_BASIC))
        if stat_obj is not None:
            max_e = getattr(stat_obj, "max_energy", health.max_energy)
            stat_obj.energy = min(max_e, stat_obj.energy + ENERGY_GAIN_BASIC)
            health.energy = stat_obj.energy
        else:
            health.energy = min(health.max_energy,
                                health.energy + ENERGY_GAIN_BASIC)
        return dmg

    # ------------------------------------------------------------------
    # skill
    # ------------------------------------------------------------------
    def use_skill(self, eid, idx, target=None):
        """Mirror the legacy ``_do_skill`` on entities.

        - Reads the hero's skill from ``stat_obj.def_dict`` via
          ``hero_abilities`` + ``SKILLS_DB``.
        - Checks cooldown + energy cost (from ``skill_energy_cost``).
        - If affordable: deducts energy, sets cooldown, applies damage to
          the target.
        - Returns the damage dealt (0 if denied).
        """
        attacker = self._entity(eid)
        if attacker is None:
            return 0
        combat = attacker.get(Combat)
        health = attacker.get(Health)
        if combat is None or health is None:
            return 0
        stat_obj = combat.stat_obj
        if stat_obj is None:
            return 0

        skills = hero_abilities(stat_obj.def_dict)
        if idx >= len(skills) or skills[idx] is None:
            return 0
        sid = skills[idx]
        skill = SKILLS_DB[sid]

        # check cooldown
        cds = self._skill_cd.get(eid, [0.0, 0.0, 0.0])
        while len(cds) <= idx:
            cds.append(0.0)
        if cds[idx] > 0:
            return 0  # on cooldown

        # check energy
        cost = stat_obj.skill_energy_cost(sid)
        if stat_obj.energy < cost:
            return 0  # can't afford

        # spend energy + set cooldown (mirrors wc.spend_skill)
        stat_obj.energy -= cost
        health.energy = stat_obj.energy
        cd = 0.6 + skill.get("cost", 2) * 0.18
        cds[idx] = cd
        self._skill_cd[eid] = cds

        # apply damage
        atk = combat.atk
        element = skill.get("element", combat.element)
        combo_mul = 1.0 + max(0, self._combo_count()) * COMBO_BONUS_PER
        kind = skill.get("type", "attack")
        # mirror the legacy per-type damage multiplier
        if kind in ("attack", "magic"):
            dmg_mul = 1.3   # melee arc (world.py:1669)
        elif kind in ("aoe_attack", "aoe_magic"):
            dmg_mul = 1.0   # AoE burst (world.py:1697)
        elif kind == "beam":
            dmg_mul = 1.0   # beam (world.py:1823)
        else:
            dmg_mul = 1.0

        total_dmg = 0
        if target is not None and isinstance(target, int):
            target_e = self._entity(target)
            if target_e is not None:
                t_combat = target_e.get(Combat)
                t_health = target_e.get(Health)
                if t_combat and t_health:
                    mult = element_mult(element, t_combat.element)
                    dmg = int(atk * skill["power"] * mult * dmg_mul * combo_mul)
                    dmg = max(1, dmg)
                    t_health.hp -= dmg
                    total_dmg = dmg
                    if t_health.hp <= 0:
                        t_health.hp = 0
                        self.on_death(target_e.eid, eid)
                    else:
                        self.on_hit(target_e.eid, eid, dmg, False)

        # small energy gain for using a skill (mirrors ENERGY_GAIN_DEAL)
        if stat_obj is not None:
            max_e = getattr(stat_obj, "max_energy", health.max_energy)
            stat_obj.energy = min(max_e, stat_obj.energy + ENERGY_GAIN_DEAL)
            health.energy = stat_obj.energy
        return total_dmg

    # ------------------------------------------------------------------
    # ultimate
    # ------------------------------------------------------------------
    def use_ultimate(self, eid, target=None):
        """Mirror the legacy ``_do_ultimate`` on entities.

        - Requires ``stat_obj.energy >= stat_obj.max_energy`` (full bar).
        - If ready: deducts all energy, applies the ult damage, and applies
          the ``ULTIMATE_VARIANTS[hero_id]`` extra effect.
        - Returns the total damage dealt (0 if not ready).
        """
        attacker = self._entity(eid)
        if attacker is None:
            return 0
        combat = attacker.get(Combat)
        health = attacker.get(Health)
        if combat is None or health is None:
            return 0
        stat_obj = combat.stat_obj
        if stat_obj is None:
            return 0

        # require full energy (mirrors wc.can_ultimate)
        max_e = getattr(stat_obj, "max_energy", health.max_energy)
        if stat_obj.energy < max_e:
            return 0

        ult_id = getattr(stat_obj, "ultimate", None)
        if ult_id is None:
            return 0
        skill = SKILLS_DB.get(ult_id)
        if skill is None:
            return 0

        # spend all energy (mirrors wc.spend_ultimate)
        stat_obj.energy = 0
        health.energy = 0

        atk = combat.atk
        element = skill.get("element", combat.element)
        combo_mul = 1.0 + max(0, self._combo_count()) * COMBO_BONUS_PER
        kind = skill.get("type", "ultimate")

        # heal ults deal 0 damage (mirrors world.py:1905-1912)
        if skill.get("heal") or kind == "heal":
            total_dmg = 0
        else:
            # mirror the legacy per-type damage multiplier
            if kind in ("aoe_attack", "aoe_magic"):
                dmg_mul = 1.4   # AoE ult (world.py:1921)
            else:
                dmg_mul = 1.5   # forward beam ult (world.py:1937)

            # resolve targets
            if target is not None and isinstance(target, int):
                targets = [self._entity(target)]
                targets = [t for t in targets if t is not None]
            else:
                targets = list(self.world.enemies())

            total_dmg = 0
            for te in targets:
                t_combat = te.get(Combat)
                t_health = te.get(Health)
                if t_combat is None or t_health is None:
                    continue
                mult = element_mult(element, t_combat.element)
                dmg = int(atk * skill["power"] * mult * dmg_mul * combo_mul)
                dmg = max(1, dmg)
                t_health.hp -= dmg
                total_dmg += dmg
                if t_health.hp <= 0:
                    t_health.hp = 0
                    self.on_death(te.eid, eid)
                else:
                    self.on_hit(te.eid, eid, dmg, True)

        # ULTIMATE_VARIANTS extra effect (mirrors world.py:1962-1996)
        var = ULTIMATE_VARIANTS.get(getattr(stat_obj, "id", None))
        if var:
            self._apply_ult_variant(stat_obj, var, total_dmg, health)
        return total_dmg

    def _apply_ult_variant(self, stat_obj, var, total_dmg, health):
        """Apply the per-hero ultimate variant's secondary effect."""
        eff = var["extra_effect"]
        pot = var.get("potency", 0)
        if eff == "self_heal" and total_dmg > 0:
            heal = int(total_dmg * pot)
            stat_obj.hp = min(stat_obj.max_hp, stat_obj.hp + heal)
            health.hp = stat_obj.hp
        elif eff == "party_shield":
            # shield the caster (full party integration is Task 20)
            stat_obj.add_effect("shield", 3, pot)
        elif eff == "energy_refund":
            max_e = getattr(stat_obj, "max_energy", health.max_energy)
            stat_obj.energy = int(max_e * pot)
            health.energy = stat_obj.energy
        elif eff == "atk_buff_self":
            stat_obj.add_effect("atk_up", 4, pot)
        # knockback requires spatial data (Transform) — deferred to Task 20

    # ------------------------------------------------------------------
    # callbacks
    # ------------------------------------------------------------------
    def on_hit(self, target_eid, attacker_eid, dmg, is_crit):
        """Record the hit for reaction tracking + fire the on_hit callback.

        Full drop/combo/signature integration is Task 20; for this task this
        records the element aura (for fire+water->steam reactions) and fires
        the callback if set.
        """
        attacker = self._entity(attacker_eid)
        if attacker is not None:
            combat = attacker.get(Combat)
            if combat is not None:
                # reaction: check if a different element hit within the window
                aura = self._element_aura.get(target_eid)
                if aura is not None and aura[0] is not None and aura[1] > 0:
                    rxn = reaction_for(aura[0], combat.element)
                    if rxn:
                        name, bonus_frac, effect, rcol = rxn
                        target = self._entity(target_eid)
                        if target is not None:
                            t_health = target.get(Health)
                            if t_health is not None:
                                bonus = int(dmg * bonus_frac)
                                if bonus > 0:
                                    t_health.hp -= bonus
                                    if t_health.hp <= 0:
                                        t_health.hp = 0
                                        self.on_death(target_eid, attacker_eid)
                # record this hit's element + refresh the reaction window
                self._element_aura[target_eid] = [combat.element, REACTION_WINDOW]
            else:
                self._element_aura[target_eid] = [None, 0.0]
        if self.on_hit_callback is not None:
            self.on_hit_callback(target_eid, attacker_eid, dmg, is_crit)

    def on_death(self, eid, killer_eid):
        """Mark the entity dead + fire the on_death callback.

        Full drop/combo/signature integration is Task 20; for this task this
        zeroes Health.hp and fires the callback if set.
        """
        e = self._entity(eid)
        if e is not None:
            health = e.get(Health)
            if health is not None:
                health.hp = 0
            # clean up the element aura
            self._element_aura.pop(eid, None)
        if self.on_death_callback is not None:
            self.on_death_callback(eid, killer_eid)

    # ------------------------------------------------------------------
    # Full-fidelity combat methods (Task 20c) — verbatim ports of the legacy
    # WorldScene._element_mult / _do_attack / _do_skill / _do_ultimate /
    # _on_enemy_hit / _on_enemy_death. The bodies are copied EXACTLY; only
    # ``self.X`` references to scene-level state are rewired to
    # ``self.scene.X``. The methods KEEP their ``wc``/``en`` (WorldCharacter /
    # WorldEnemy) parameters — they are NOT yet entity-based (that swap is
    # Task 20e). WorldScene keeps thin delegates so all call sites work
    # unchanged. The minimal entity-based stubs above (``basic_attack`` /
    # ``use_skill`` / ``use_ultimate`` / ``on_hit`` / ``on_death``) stay for
    # the verify_ecs tests.
    # ------------------------------------------------------------------
    def _element_mult(self, atk_el, def_el):
        return element_mult(atk_el, def_el)

    def _do_attack(self, wc, target=None):
        if wc.atk_cd > 0:
            return
        wc.atk_cd = AA_CD
        wc.atk_anim = 0.2
        wc._last_combat_t = 0
        style = WEAPON_STYLE.get(WEAPON_STYLE_KEY(wc.hero.id), "melee")
        col = ELEMENT_COLORS.get(wc.element, ((200, 200, 200),))[0]
        a = wc.hero
        # crit chance includes the keen-eye passive and the tree's crit bonus
        crit_chance = a.crit_chance
        if a.passive and a.passive.get("kind") == "crit_up":
            crit_chance += a.passive.get("val", 0.1)
        atk = wc.effective_atk()
        # crit damage multiplier: base 1.6 + tree crit_dmg bonus + dark elemental
        # resonance (+crit_dmg when 2+ dark heroes in party). Additive on the
        # crit multiplier's bonus term so it stacks with the tree/set crit-dmg,
        # not multiplicatively on the whole crit.
        crit_mul = 1.6 + getattr(a, "crit_dmg_bonus", 0) + wc._res_crit_dmg
        if style == "ranged":
            # projectile toward the nearest enemy in the facing direction, or a
            # straight shot in the facing dir if no target — so ranged heroes
            # actually hit enemies that aren't at exactly the same y. If an AA
            # target (Task B3) is provided, aim directly at it instead of the
            # nearest-enemy search (the AA target is the player's intent).
            if target is not None:
                tx, ty = target.x, target.y
            else:
                tx, ty = wc.x + wc.facing * 400, wc.y
                best_d = 1e9
                for en in self.scene.enemies:
                    if not en.alive:
                        continue
                    dx = en.x - wc.x
                    # only aim at enemies roughly in the facing half-plane
                    if wc.facing > 0 and dx < -40:
                        continue
                    if wc.facing < 0 and dx > 40:
                        continue
                    dd = math.hypot(dx, en.y - wc.y)
                    if dd < best_d:
                        best_d = dd; tx, ty = en.x, en.y
            dx, dy = tx - wc.x, ty - wc.y
            d = math.hypot(dx, dy) or 1
            sp = 560
            p = Projectile(wc.x + wc.facing * 20, wc.y, dx / d * sp, dy / d * sp,
                           1.4, 8, col, wc.element, wc, atk, kind="hero")
            self.scene.projectiles.append(p)
            # muzzle flash
            self.scene.particles.spark(wc.x + wc.facing * 24, wc.y, col, n=5, speed=200, size=4, life=0.18)
            audio.play("hit", 0.2)
        else:
            # melee arc - hit enemies in front. If an AA target (Task B3) is
            # provided, center the arc on the target so the melee swing actually
            # hits it (the default facing arc could miss a target slightly
            # above/below the hero). Falls back to the facing arc if no target.
            if target is not None:
                arc_x = target.x
                arc_y = target.y
            else:
                arc_x = wc.x + wc.facing * 40
                arc_y = wc.y
            ar = 60
            hit_any = False
            total_dmg = 0
            primary_x, primary_y = None, None  # for the cleave signature
            for en in self.scene.enemies:
                if not en.alive:
                    continue
                if math.hypot(en.x - arc_x, en.y - arc_y) < ar + en.r:
                    mult = self._element_mult(wc.element, en.element)
                    is_crit = random.random() < crit_chance
                    combo_mul = 1.0 + max(0, self.scene._combo_count) * COMBO_BONUS_PER
                    dmg = int(atk * (1.0 + random.uniform(-0.1, 0.2)) * mult
                              * (crit_mul if is_crit else 1.0) * combo_mul)
                    dealt = en.take_damage(dmg, wc.x, wc.y, is_crit,
                                            on_attack=self.scene._on_enemy_event)
                    if dealt > 0:
                        self._on_enemy_hit(en, wc, dealt, is_crit)
                        total_dmg += dealt
                        hit_any = True
                        if primary_x is None:
                            primary_x, primary_y = en.x, en.y
            if hit_any:
                # routed through wc.add_energy so the light resonance
                # (energy_regen) and the p_energy (Flow State) passive add
                # instead of both multiplying the base.
                wc.add_energy(ENERGY_GAIN_BASIC)
                audio.play("hit", 0.3)
                self.scene.camera.add_shake(3, self.scene._shake_mul)
                # impact shockwave ring on a clean hit
                self.scene.particles.ring(arc_x, arc_y, col, n=14, speed=260, size=4, life=0.3)
                # lifesteal passive: heal a fraction of basic-attack damage dealt
                if a.passive and a.passive.get("kind") == "lifesteal" and total_dmg > 0:
                    heal = max(1, int(total_dmg * a.passive.get("val", 0.12)))
                    wc.heal(heal)
                    if self.scene.game.player.settings.get("damage_numbers", True):
                        self.scene.floats.append(FloatText(wc.x, wc.y - 30, f"+{heal}",
                                                     (140, 240, 160), size=16))
            else:
                audio.play("hit", 0.12)
            # signature passive: cleave (dict-lookup dispatch — basic attacks
            # splash to enemies within 60px of the primary target). val is the
            # fraction of ATK dealt as splash (0.5 = 50%). Skips the primary
            # target (already hit by the main arc) and dead enemies.
            _sig = _SIG_ATTACK.get(wc._signature_kind)
            if _sig and primary_x is not None:
                _sig(self.scene, wc, primary_x, primary_y, atk)
            # melee swing arc (a brighter slash streak)
            self.scene.particles.spark(arc_x, arc_y, col, n=8, speed=180, size=4, life=0.22)
        # breakables: a melee arc or a dash both shatter any breakable props in
        # range. The arc covers the same hit area as the melee swing; the dash
        # covers the hero's current position (the dash passes *through* props,
        # so the endpoint check is enough). Each breakable drops its loot once.
        # Use the hero's facing arc for melee; for a ranged attack, fall back
        # to the hero's position so a ranged shot still shatters a prop the
        # hero dashes into (the projectile itself doesn't carry the shatter).
        if style == "ranged":
            br_x, br_y, br_r = wc.x, wc.y, 48
        else:
            br_x, br_y, br_r = arc_x, arc_y, ar
        if wc.dash_t > 0:
            # a dash widens the reach a bit so a dash-through reliably shatters
            # props the hero passes through (the dash moves fast; a tight arc
            # could miss between frames).
            br_x, br_y, br_r = wc.x, wc.y, 56
        for b in self.scene.breakables:
            if b["broken"]:
                continue
            if math.hypot(b["x"] - br_x, b["y"] - br_y) < br_r + 20:
                self.scene._break_breakable(b)

    def _do_skill(self, wc, idx, target=None):
        # Task B3: casting a skill interrupts the AA (the skill's targeting
        # shouldn't fight the AA target). Clear the AA target on a skill cast.
        wc.aa_target = None
        if not wc.can_skill(idx):
            # soft denied buzz on a rejected skill (on cooldown / no energy) so
            # the player gets audible feedback that the input was rejected
            audio.play("weak", 0.15)
            return
        sk = wc.skill_list()[idx]
        if sk is None:
            return
        skill = SKILLS_DB[sk]
        col = ELEMENT_COLORS.get(skill["element"], ((200, 200, 200),))[0]
        wc.spend_skill(idx)
        wc._last_combat_t = 0
        # constellation cd_reduction perk: shave the skill's cooldown by the hero's
        # accumulated perk fraction (applied after spend_skill sets the cd). The
        # perk is stored on the Hero as _perk_cd_reduction (a fraction 0..1).
        perk_cd = getattr(wc.hero, "_perk_cd_reduction", 0.0)
        if perk_cd > 0:
            wc.skill_cd[idx] = max(0.0, wc.skill_cd[idx] * (1.0 - perk_cd))
            wc.skill_cd_max[idx] = wc.skill_cd[idx]
        kind = skill["type"]
        a = wc.hero
        atk = wc.effective_atk()
        # combo climax: if the skill is empowered (armed at combo milestone 5),
        # widen the effect — AoE skills get a bigger radius + a second ring;
        # single-target skills get a second piercing projectile. Consumed on
        # use so the empowerment is a one-shot finisher, not a persistent buff.
        empowered = self.scene._skill_empowered
        if empowered:
            self.scene._skill_empowered = False
        # ground-targeted AoE (Task B2): if `target` (a world-space (x,y)) is
        # provided for an aoe_attack/aoe_magic skill, center the burst on the
        # clamped target instead of the hero. Clamp to AIM_MAX_RANGE so a player
        # can't AoE a target off-screen across the map. Other skill types ignore
        # `target` (melee/beam use the facing; ranged auto-targets the nearest
        # enemy; summon/trap place at the hero's side).
        aoe_cx, aoe_cy = wc.x, wc.y
        if target is not None and kind in ("aoe_attack", "aoe_magic"):
            tx, ty = target
            d = math.hypot(tx - wc.x, ty - wc.y)
            if d > AIM_MAX_RANGE:
                # clamp to the max range along the aim line
                tx = wc.x + (tx - wc.x) * (AIM_MAX_RANGE / d)
                ty = wc.y + (ty - wc.y) * (AIM_MAX_RANGE / d)
            aoe_cx, aoe_cy = tx, ty
        # most skills: a burst around the hero or a projectile
        if kind in ("attack", "magic") or (kind == "aoe_attack" and "arrow" in sk) or (kind == "magic" and "bolt" in sk):
            # single-target projectile or melee nuke
            style = WEAPON_STYLE.get(WEAPON_STYLE_KEY(wc.hero.id), "melee")
            if style == "ranged":
                # aim at the nearest enemy in the facing half-plane (same fix as
                # the basic attack — a straight horizontal shot misses anything
                # not at the hero's y)
                tx, ty = wc.x + wc.facing * 500, wc.y
                best_d = 1e9
                for en in self.scene.enemies:
                    if not en.alive:
                        continue
                    dx = en.x - wc.x
                    if wc.facing > 0 and dx < -40:
                        continue
                    if wc.facing < 0 and dx > 40:
                        continue
                    dd = math.hypot(dx, en.y - wc.y)
                    if dd < best_d:
                        best_d = dd; tx, ty = en.x, en.y
                dx, dy = tx - wc.x, ty - wc.y
                d = math.hypot(dx, dy) or 1
                sp = 660
                p = Projectile(wc.x + wc.facing * 20, wc.y, dx / d * sp, dy / d * sp,
                               1.6, 12, col, skill["element"], wc,
                               atk * skill["power"], is_crit=False, kind="hero")
                self.scene.projectiles.append(p)
                # empowered single-target: a second piercing projectile offset
                # perpendicular to the aim line so it hits a different arc of
                # the enemy cluster (a free second shot, not a damage multiplier).
                if empowered:
                    # perpendicular offset for the 2nd projectile's start
                    px = -dy / d * 24
                    py = dx / d * 24
                    p2 = Projectile(wc.x + wc.facing * 20 + px, wc.y + py,
                                    dx / d * sp, dy / d * sp,
                                    1.6, 12, col, skill["element"], wc,
                                    atk * skill["power"], is_crit=False, kind="hero")
                    self.scene.projectiles.append(p2)
            else:
                # big melee arc
                arc_x = wc.x + wc.facing * 50
                # empowered melee: widen the arc radius so the nuke reaches a
                # wider cluster (a radius bump, not a damage multiplier).
                arc_r = 130 if empowered else 90
                combo_mul = 1.0 + max(0, self.scene._combo_count) * COMBO_BONUS_PER
                for en in self.scene.enemies:
                    if en.alive and math.hypot(en.x - arc_x, en.y - wc.y) < arc_r:
                        mult = self._element_mult(skill["element"], en.element)
                        dmg = int(atk * skill["power"] * mult * 1.3 * combo_mul)
                        dealt = en.take_damage(dmg, wc.x, wc.y,
                                                on_attack=self.scene._on_enemy_event)
                        if dealt:
                            self._on_enemy_hit(en, wc, dealt, False)
                self.scene.particles.burst(arc_x, wc.y, col, n=16, speed=240, size=6, life=0.4)
                # empowered melee: a second shockwave ring so the wider nuke
                # reads visually as a bigger impact.
                if empowered:
                    self.scene.particles.ring(arc_x, wc.y, col, n=20, speed=360, size=6, life=0.45)
                self.scene.camera.add_shake(5, self.scene._shake_mul)
            audio.play("skill", 0.4)
        elif kind in ("aoe_attack", "aoe_magic"):
            # burst around the hero (or the clamped ground target — Task B2) + an
            # expanding shockwave ring. aoe_cx/aoe_cy default to the hero; a held
            # aim shifts the center to the mouse world pos (clamped to max range).
            self.scene.particles.burst(aoe_cx, aoe_cy, col, n=30, speed=320, size=7, life=0.6, grav=0)
            self.scene.particles.ring(aoe_cx, aoe_cy, col, n=28, speed=420, size=6, life=0.5)
            # empowered AoE: widen the radius (200 -> 260) + a second ring so
            # the burst covers a bigger cluster and reads as a bigger impact.
            aoe_r = 260 if empowered else 200
            if empowered:
                self.scene.particles.ring(aoe_cx, aoe_cy, (255, 255, 255),
                                    n=24, speed=380, size=6, life=0.45)
            combo_mul = 1.0 + max(0, self.scene._combo_count) * COMBO_BONUS_PER
            for en in self.scene.enemies:
                if en.alive and math.hypot(en.x - aoe_cx, en.y - aoe_cy) < aoe_r:
                    mult = self._element_mult(skill["element"], en.element)
                    dmg = int(atk * skill["power"] * mult * combo_mul)
                    dealt = en.take_damage(dmg, aoe_cx, aoe_cy,
                                            on_attack=self.scene._on_enemy_event)
                    if dealt:
                        self._on_enemy_hit(en, wc, dealt, False)
            self.scene.camera.add_shake(8, self.scene._shake_mul)
            self.scene.flash = 0.2
            audio.play("skill", 0.5)
        elif kind == "heal":
            # heal active + share a bit with party
            amt = int(atk * skill["power"] * 0.8) + 30
            wc.heal(amt)
            if self.scene.game.player.settings.get("damage_numbers", True):
                self.scene.floats.append(FloatText(wc.x, wc.y - 30, f"+{amt}", (140, 240, 160), size=24))
            for other in self.scene.party:
                if other and other is not wc and other.alive:
                    other.heal(amt // 2)
            self.scene.particles.burst(wc.x, wc.y, (140, 240, 160), n=20, speed=160, size=6, life=0.5, grav=-60)
            # rising heal motes
            for _ in range(10):
                self.scene.particles.list.append(Particle(
                    wc.x + random.uniform(-20, 20), wc.y + 20,
                    random.uniform(-10, 10), random.uniform(-90, -50),
                    0.7, (180, 255, 200), 4, -30))
            audio.play("heal", 0.5)
        elif kind in ("buff", "debuff"):
            # self buff visual — orbiting motes
            self.scene.particles.burst(wc.x, wc.y, col, n=18, speed=180, size=5, life=0.5, grav=-80)
            audio.play("buff", 0.5)
            # actually apply the status effect (the skill dict carries buff/debuff
            # keys + potency + dur — wire them into the hero's effect list so
            # shield/atk_up/def_up/poison/etc. do something instead of just VFX)
            if skill.get("buff"):
                wc.hero.add_effect(skill["buff"], skill.get("dur", 3),
                                   skill.get("potency", 0.3))
                # a small heal for support buffs so they feel helpful immediately
                if skill["buff"] in ("shield", "def_up", "atk_up"):
                    wc.heal(20)
            if skill.get("debuff"):
                # debuffs are single-target in this real-time model — apply to the
                # nearest alive enemy in the facing arc so curse/rupture land
                nearest = None
                for en in self.scene.enemies:
                    if not en.alive:
                        continue
                    if (en.x - wc.x) * wc.facing > 0 and math.hypot(en.x - wc.x, en.y - wc.y) < 200:
                        nearest = en
                        break
                if nearest:
                    # apply a short stun as the debuff's tangible effect (the
                    # real-time combat has no per-enemy effect list, so a brief
                    # telegraph-stun is the readable outcome)
                    nearest._react_stun = max(nearest._react_stun, 1.5)
                    # apply each debuff in the skill's debuff list (e.g.
                    # ["burn", "atk_down"]) so DoTs actually tick + stat debuffs
                    # land. DoT types (burn/bleed/poison) use the skill's
                    # dot_potency (distinct per debuff skill); stat debuffs use
                    # the generic potency. add_effect dedupes by type so
                    # re-application refreshes duration instead of double-stacking.
                    dur = skill.get("dur", 3)
                    dot_pot = skill.get("dot_potency", 0.3)
                    stat_pot = skill.get("potency", 0.3)
                    for db in skill["debuff"]:
                        pot = dot_pot if db in ("burn", "bleed", "poison") else stat_pot
                        nearest.enemy.add_effect(db, dur, pot)
                    self.scene.particles.burst(nearest.x, nearest.y, col, n=12, speed=160, size=5, life=0.4)
        elif kind == "revive":
            # revive a downed party member at half HP; if none downed, big heal
            # on the active hero so the skill isn't wasted
            downed = [o for o in self.scene.party if o and not o.alive]
            if downed:
                target = downed[0]
                target.alive = True
                target.hero.hp = target.hero.max_hp // 2
                target.hero.energy = ENERGY_START
                target.invuln_t = 0.5
                self.scene.particles.burst(target.x, target.y, (140, 240, 160),
                                     n=30, speed=240, size=7, life=0.7, grav=-60)
                self.scene.particles.ring(target.x, target.y, (180, 255, 200),
                                    n=24, speed=300, size=6, life=0.6)
                self.scene.floats.append(FloatText(target.x, target.y - 40,
                                             f"REVIVED {target.hero.name}!",
                                             (140, 240, 160), size=20))
                audio.play("revive", 0.6)
            else:
                # nobody to revive — big heal on the active hero instead
                wc.heal(int(wc.hero.max_hp * 0.5))
                self.scene.particles.burst(wc.x, wc.y, (140, 240, 160),
                                     n=24, speed=200, size=6, life=0.6, grav=-60)
                audio.play("heal", 0.5)
        elif kind == "summon":
            # spawn a temporary ally at the hero's side that auto-attacks nearby
            # enemies for `dur` seconds. A separate entity (SummonAlly) so the
            # 4-slot party is untouched. Water summon heals the party instead.
            sx = wc.x + wc.facing * 40
            sy = wc.y + 20
            ally = SummonAlly(sx, sy, skill["element"], col,
                              int(atk * skill["power"]), skill.get("dur", 6),
                              skill.get("potency", 1.0), wc)
            self.scene._summons.append(ally)
            self.scene.particles.burst(sx, sy, col, n=16, speed=180, size=6, life=0.5, grav=-60)
            audio.play("skill", 0.5)
        elif kind == "beam":
            # line hit-scan from hero toward the facing/aim — damage all enemies
            # along the line within `range`. Aim at the nearest enemy in the
            # facing half-plane (like the ranged attack) so the beam actually
            # hits a target, not a straight horizontal miss.
            bx = wc.x + wc.facing * 20
            by = wc.y
            ex = bx + wc.facing * skill.get("range", 420)
            ey = by
            best_d = 1e9
            for en in self.scene.enemies:
                if not en.alive:
                    continue
                if (en.x - wc.x) * wc.facing < -40:
                    continue
                dd = math.hypot(en.x - wc.x, en.y - wc.y)
                if dd < best_d:
                    best_d = dd; ex, ey = en.x + wc.facing * 60, en.y
            combo_mul = 1.0 + max(0, self.scene._combo_count) * COMBO_BONUS_PER
            for en in self.scene.enemies:
                if not en.alive:
                    continue
                if _seg_hit(bx, by, ex, ey, en.x, en.y, en.r + 22):
                    mult = self._element_mult(skill["element"], en.element)
                    dmg = int(atk * skill["power"] * mult * combo_mul)
                    dealt = en.take_damage(dmg, wc.x, wc.y,
                                            on_attack=self.scene._on_enemy_event)
                    if dealt:
                        self._on_enemy_hit(en, wc, dealt, False)
            # beam visual: a bright line + a sparkle at the endpoint
            self.scene.particles.beam(bx, by, ex, ey, col)
            self.scene.camera.add_shake(4, self.scene._shake_mul)
            audio.play("skill", 0.5)
        elif kind == "trap":
            # place a trap on the ground at the facing that triggers when an
            # enemy steps within its radius — a delayed hazard. The trap stores
            # the summoning hero (source) so a trap kill fires the death/reward
            # path via the on_enemy_hit callback (no silent kills).
            tx = wc.x + wc.facing * 60
            ty = wc.y
            tr = Trap(tx, ty, skill["element"], col,
                      int(atk * skill["power"]), skill.get("radius", 70),
                      skill.get("dur", 8), wc)
            self.scene._traps.append(tr)
            self.scene.particles.burst(tx, ty, col, n=10, speed=120, size=4, life=0.4, grav=-30)
            audio.play("skill", 0.4)
        else:
            # fallback: small burst
            self.scene.particles.burst(wc.x, wc.y, col, n=14, speed=200, size=5, life=0.4)
            audio.play("skill", 0.4)
        # variable hit-stop: heavier skills (higher cost tier) freeze the screen
        # longer than a basic attack so a cost-5 nuke lands with more weight than
        # a cost-2 poke. Capped at 0.4s; halved under reduce_motion. Uses max()
        # so multi-hit AoE doesn't stack the freeze.
        _hs = min(0.4, 0.06 + skill.get("cost", 2) * 0.03)
        if self.scene._reduce_motion:
            _hs *= 0.5
        self.scene.hit_stop = max(self.scene.hit_stop, _hs)
        # energy gain for using a skill (small); flow-state passive + light
        # elemental resonance boost it. Routed through wc.add_energy so the
        # resonance (energy_regen) and the passive (energy_gen) add rather than
        # both multiplying the base (the old inline code only applied the
        # passive; add_energy now sums them).
        gain = ENERGY_GAIN_DEAL
        wc.add_energy(gain)

    def _do_ultimate(self, wc):
        # Task B3: casting an ult interrupts the AA (same as a skill cast).
        wc.aa_target = None
        if not wc.can_ultimate():
            # soft denied buzz so a rejected ult isn't silent
            audio.play("weak", 0.15)
            return
        skill = SKILLS_DB[wc.hero.ultimate]
        col = ELEMENT_COLORS.get(skill["element"], ((255, 255, 200),))[0]
        wc.spend_ultimate()
        wc._last_combat_t = 0
        a = wc.hero
        atk = wc.effective_atk()
        kind = skill["type"]
        # combo climax: if the ult is empowered (armed at combo milestone 10,
        # which coincides with COMBO_MAX), apply a free debuff to every enemy
        # hit by the ult — a status, not raw damage, so it doesn't double-dip
        # with the combo multiplier. Consumed on use; cleared on a party swap.
        empowered = self.scene._ult_empowered
        if empowered:
            self.scene._ult_empowered = False
        self.scene.flash = 0.5
        if self.scene._reduce_motion:
            self.scene.flash *= 0.4
        self.scene.camera.add_shake(16, self.scene._shake_mul)
        # ultimates are the heaviest hit — a long hit-stop that scales with the
        # ult's cost tier (an ult with cost 8-9 -> 0.30-0.33s, capped at 0.4).
        # Halved under reduce_motion; uses max() so AoE doesn't stack the freeze.
        _hs = min(0.4, 0.06 + skill.get("cost", 8) * 0.03)
        if self.scene._reduce_motion:
            _hs *= 0.5
        self.scene.hit_stop = max(self.scene.hit_stop, _hs)
        combo_mul = 1.0 + max(0, self.scene._combo_count) * COMBO_BONUS_PER
        # total damage dealt by the ultimate — used by the per-hero variant's
        # self_heal effect (a fraction of damage dealt). Heal ults deal 0 damage
        # so their variants never pick self_heal (see ULTIMATE_VARIANTS).
        total_dmg = 0
        # heal ults (e.g. light_hymn) — the skill dict may carry heal=True even
        # though its type is "ultimate"; route to the heal branch so it actually
        # heals the party instead of falling through to the forward-beam else.
        if skill.get("heal") or kind == "heal":
            amt = a.max_hp
            for other in self.scene.party:
                if other and other.alive:
                    other.heal(amt)
            self.scene.particles.burst(wc.x, wc.y, (140, 240, 160), n=40, speed=260, size=8, life=0.8, grav=-80)
            self.scene.particles.ring(wc.x, wc.y, (180, 255, 200), n=36, speed=300, size=6, life=0.7)
            audio.play("heal", 0.6)
        elif kind in ("aoe_attack", "aoe_magic"):
            # huge burst + double shockwave ring
            self.scene.particles.burst(wc.x, wc.y, col, n=60, speed=420, size=9, life=0.9, grav=0)
            self.scene.particles.ring(wc.x, wc.y, col, n=40, speed=560, size=7, life=0.6)
            self.scene.particles.ring(wc.x, wc.y, (255, 255, 255), n=32, speed=360, size=5, life=0.5)
            for en in self.scene.enemies:
                if en.alive and math.hypot(en.x - wc.x, en.y - wc.y) < 320:
                    mult = self._element_mult(skill["element"], en.element)
                    dmg = int(atk * skill["power"] * mult * 1.4 * combo_mul)
                    dealt = en.take_damage(dmg, wc.x, wc.y,
                                            on_attack=self.scene._on_enemy_event)
                    if dealt:
                        total_dmg += dealt
                        self._on_enemy_hit(en, wc, dealt, True)
        else:
            # big forward beam — a streaking column of particles in the facing dir
            arc_x = wc.x + wc.facing * 60
            for step in range(6):
                bx = wc.x + wc.facing * (40 + step * 40)
                self.scene.particles.burst(bx, wc.y, col, n=10, speed=120, size=7, life=0.4, grav=0)
            self.scene.particles.ring(arc_x, wc.y, col, n=30, speed=400, size=7, life=0.5)
            for en in self.scene.enemies:
                if en.alive and (en.x - wc.x) * wc.facing > 0 and math.hypot(en.x - wc.x, en.y - wc.y) < 300:
                    mult = self._element_mult(skill["element"], en.element)
                    dmg = int(atk * skill["power"] * mult * 1.5 * combo_mul)
                    dealt = en.take_damage(dmg, wc.x, wc.y,
                                            on_attack=self.scene._on_enemy_event)
                    if dealt:
                        total_dmg += dealt
                        self._on_enemy_hit(en, wc, dealt, True)
        # --- B5: per-hero ultimate variant — a secondary effect on top of the
        # base ultimate. Read the variant (if any) and apply its extra. Only the
        # one-liner effects are wired (burn/freeze deferred until the DoT engine).
        # --- C5: empowered-ult free debuff — apply a short atk_down to every
        # enemy the ult actually hit (collected in _ult_hit_targets above) so
        # the climax is a status payoff, not a second damage roll. Skipped for
        # heal ults (they hit no enemies).
        if empowered:
            for en in self.scene.enemies:
                if not en.alive:
                    continue
                # only enemies within the ult's effect radius (320 for AoE, 300
                # for the forward beam) — matches the damage loops above.
                if math.hypot(en.x - wc.x, en.y - wc.y) < 320:
                    en.enemy.add_effect("atk_down", 4, 0.3)
                    self.scene.particles.burst(en.x, en.y, (255, 120, 180),
                                         n=10, speed=160, size=5, life=0.5)
            self.scene.floats.append(FloatText(wc.x, wc.y - 50, "EMPOWERED!",
                                         (255, 180, 240), size=22))
        var = ULTIMATE_VARIANTS.get(wc.hero.id)
        if var:
            eff = var["extra_effect"]
            pot = var.get("potency", 0)
            if eff == "self_heal" and total_dmg > 0:
                # heal the caster a modest fraction of the damage dealt
                wc.heal(int(total_dmg * pot))
                self.scene.particles.burst(wc.x, wc.y, (140, 240, 160),
                                     n=14, speed=160, size=5, life=0.5, grav=-60)
            elif eff == "party_shield":
                # shield each alive party member (potency = shield strength)
                for other in self.scene.party:
                    if other and other.alive:
                        other.hero.add_effect("shield", 3, pot)
                self.scene.particles.ring(wc.x, wc.y, (180, 220, 255),
                                    n=24, speed=260, size=5, life=0.5)
            elif eff == "knockback":
                # push enemies back away from the hero (potency = push speed)
                for en in self.scene.enemies:
                    if not en.alive:
                        continue
                    if math.hypot(en.x - wc.x, en.y - wc.y) < 360:
                        dx = en.x - wc.x
                        dy = en.y - wc.y
                        d = math.hypot(dx, dy) or 1
                        en.kb_x = dx / d * pot
                        en.kb_y = dy / d * pot
            elif eff == "energy_refund":
                # refund a modest fraction of the active hero's max energy
                wc.add_energy(int(wc.hero.max_energy * pot))
            elif eff == "atk_buff_self":
                # buff the active hero's ATK for a few seconds
                wc.hero.add_effect("atk_up", 4, pot)
                self.scene.particles.burst(wc.x, wc.y, (255, 200, 120),
                                     n=16, speed=180, size=5, life=0.5, grav=-40)
        # constellation ult_extra perks — applied after the ult's main effect so
        # the perk layer adds on top of the base ult. Variants shipped now:
        #   self_heal  - heal the active hero for val * max_hp
        #   party_buff - a temporary atk_up on each party member (3s, val potency)
        #   atk_buff   - a temporary atk_up on the active hero (3s, val potency)
        # Burn/freeze DoT variants are wired through the DoT engine (tick_effects
        # is now driven in the real-time world loop — see the enemy update loop).
        ux = getattr(a, "ult_extra", {}) or {}
        if ux:
            if ux.get("self_heal"):
                heal_amt = int(a.max_hp * ux["self_heal"])
                wc.heal(heal_amt)
                if self.scene.game.player.settings.get("damage_numbers", True):
                    self.scene.floats.append(FloatText(wc.x, wc.y - 30, f"+{heal_amt}",
                                                 (140, 240, 160), size=22))
            if ux.get("party_buff"):
                pot = ux["party_buff"]
                for other in self.scene.party:
                    if other and other.alive:
                        other.hero.add_effect("atk_up", 3, pot)
            if ux.get("atk_buff"):
                pot = ux["atk_buff"]
                wc.hero.add_effect("atk_up", 3, pot)
        audio.play("ultimate", 0.6)

    def _on_enemy_hit(self, en, wc, dmg, is_crit):
        # combo system: each hit within the combo window stacks a damage
        # multiplier (capped at COMBO_MAX) and a visible combo counter. The
        # window refreshes on every hit; the counter resets when it expires.
        # The multiplier itself is applied at the damage source (see _do_attack /
        # _do_skill / _do_ultimate) using the pre-increment count, so the first
        # hit of a streak gets 0% bonus and the ramp builds from there.
        self.scene._combo_count = min(COMBO_MAX, self.scene._combo_count + 1)
        self.scene._combo_t = self.scene._combo_window
        # combo climax milestones: arm the next skill/ult with a bonus effect.
        # The skill milestone (5) arms _skill_empowered; the ult milestone (10)
        # coincides with COMBO_MAX and arms _ult_empowered. Re-hitting the
        # milestone while already empowered is a no-op (the flag is set, not
        # toggled) so the player keeps the empowerment until they spend it.
        if self.scene._combo_count == COMBO_MILESTONE_SKILL:
            self.scene._skill_empowered = True
        if self.scene._combo_count == COMBO_MILESTONE_ULT:
            self.scene._ult_empowered = True
        # max-combo one-shot celebration: the first time the streak hits
        # COMBO_MAX in this window, fire a chord + a brief hit-stop. Gated by
        # _combo_max_celebrated so it only fires once per window (reset on
        # window expiry below). The hit-stop uses max() so it doesn't stack
        # with a crit's freeze on the same frame.
        if self.scene._combo_count >= COMBO_MAX and not self.scene._combo_max_celebrated:
            self.scene._combo_max_celebrated = True
            audio.play("combo_max", 0.5)
            _hs = 0.18
            if self.scene._reduce_motion:
                _hs *= 0.5
            self.scene.hit_stop = max(self.scene.hit_stop, _hs)
            self.scene.camera.add_shake(8, self.scene._shake_mul)
            self.scene.particles.ring(wc.x, wc.y, (255, 220, 120),
                                n=32, speed=420, size=7, life=0.6)
        # per-enemy weakness: a hero whose element matches the enemy's listed
        # weakness deals +50% (the Genshin-style break). Surfaced as a "WEAK!"
        # tag on the float so the player sees the counter-element pay off.
        weak_hit = bool(getattr(en.enemy, "weakness", None)) and en.enemy.weakness == wc.element
        if self.scene.game.player.settings.get("damage_numbers", True):
            col = (255, 220, 80) if is_crit else (255, 255, 255)
            # crits get a "!" suffix and a bigger font
            label = f"{dmg}!" if is_crit else str(dmg)
            self.scene.floats.append(FloatText(en.x, en.y - 20, label, col,
                                         size=30 if is_crit else 20))
            if weak_hit:
                self.scene.floats.append(FloatText(en.x, en.y - 8, "WEAK!",
                                            (255, 180, 80), size=16))
        el_col = ELEMENT_COLORS.get(wc.element, ((200, 200, 200),))[0]
        self.scene.particles.burst(en.x, en.y, el_col, n=8, speed=200, size=4, life=0.3)
        # wet effect: when the current map's weather is rain (or storm), the
        # wet multiplier (WET_EFFECT) extends the reaction window (+50%) and
        # scales the reaction bonus (water x1.2, fire x0.8). Gated to the
        # reaction window ONLY — the wet effect extends the reaction window,
        # not the Freeze stun duration (en._react_stun stays at its base 1.5s,
        # not 1.5 * 1.5, so the wet effect doesn't stack with the Freeze stun).
        wet = self.scene._weather in ("rain", "storm")
        # elemental reaction: if this hit's element differs from the last one
        # that hit this enemy within the reaction window, trigger a reaction
        # (bonus damage + a named float + a distinct particle). This rewards
        # swapping the active hero mid-fight (the Genshin-style 4-hero party).
        rxn = reaction_for(en._last_element_hit, wc.element) if en._last_element_hit else None
        if rxn and en._element_hit_t > 0:
            name, bonus_frac, effect, rcol = rxn
            # wet scales the reaction bonus: water +20%, fire -20% (the wet
            # effect amplifies water reactions and dampens fire ones)
            if wet:
                if wc.element == "water":
                    bonus_frac *= WET_EFFECT["water"]
                elif wc.element == "fire":
                    bonus_frac *= WET_EFFECT["fire"]
            bonus = int(dmg * bonus_frac)
            if bonus > 0:
                en.enemy.hp -= bonus
                if en.enemy.hp <= 0:
                    en.enemy.hp = 0
                    en.alive = False
            # a reaction-named float above the target so the player sees the proc
            self.scene.floats.append(FloatText(en.x, en.y - 44, name.upper() + "!",
                                         rcol, size=24))
            if effect == "aoe":
                # steam: bonus damage to nearby enemies + a cloud burst
                for other in self.scene.enemies:
                    if other is en or not other.alive:
                        continue
                    if math.hypot(other.x - en.x, other.y - en.y) < 120:
                        odmg = int(bonus * 0.5)
                        other.enemy.hp -= odmg
                        if other.enemy.hp <= 0:
                            other.enemy.hp = 0
                            other.alive = False
                self.scene.particles.burst(en.x, en.y, rcol, n=28, speed=260, size=7, life=0.6)
                self.scene.particles.ring(en.x, en.y, rcol, n=22, speed=320, size=6, life=0.5)
            elif effect == "stun":
                # freeze: a brief stun + an ice shard burst. The wet effect
                # does NOT extend the stun duration (only the reaction window).
                en._react_stun = 1.5
                self.scene.particles.burst(en.x, en.y, rcol, n=24, speed=180, size=6, life=0.7, grav=-40)
            else:  # burst
                self.scene.particles.burst(en.x, en.y, rcol, n=30, speed=340, size=7, life=0.6)
                self.scene.particles.ring(en.x, en.y, rcol, n=20, speed=380, size=6, life=0.5)
            self.scene.camera.add_shake(6, self.scene._shake_mul)
            audio.play("react_" + name.lower(), 0.45)
        # record this hit's element + refresh the reaction window for the next hit
        en._last_element_hit = wc.element
        # wet extends the reaction window (+50%) so the next element swap has a
        # longer window to trigger a reaction in the rain (the wet effect).
        en._element_hit_t = REACTION_WINDOW * (WET_EFFECT["reaction_window"] if wet else 1.0)
        if is_crit:
            # crits get a sharper white spark + a small ring + bigger hit-stop
            self.scene.particles.ring(en.x, en.y, (255, 240, 180), n=14, speed=300, size=4, life=0.28)
            self.scene.particles.spark(en.x, en.y, (255, 255, 255), n=6, speed=260, size=4, life=0.22)
            # crit hit-stop: base 0.11 + a small extra for combo tier >=2 so a
            # streak of crits feels heavier. Halved under reduce_motion; uses
            # max() so multi-hit AoE doesn't stack.
            _hs = 0.11 + (0.03 if self.scene._combo_count >= 2 else 0.0)
            if self.scene._reduce_motion:
                _hs *= 0.5
            self.scene.hit_stop = max(self.scene.hit_stop, _hs)
            self.scene.camera.add_shake(5, self.scene._shake_mul)
            audio.play("crit", 0.4)
        else:
            self.scene.hit_stop = max(self.scene.hit_stop, 0.05)
            self.scene.camera.add_shake(2, self.scene._shake_mul)
            # pitch the hit sound up every 5 combo so a streak feels escalating.
            # On a tier increase also fire the combo stinger (an ascending
            # arpeggio cached as combo_1/combo_2) so the milestone is heard,
            # not just the pitched hit. The stinger only plays on a tier
            # increase (not every hit at that tier) so it doesn't spam.
            tier = self.scene._combo_count // 5
            if tier > self.scene._combo_pitch_tier:
                self.scene._combo_pitch_tier = tier
                if tier in (1, 2):
                    audio.play("combo_1" if tier == 1 else "combo_2", 0.3)
                audio.play("crit", 0.18)
            else:
                audio.play("hit", 0.2)
        if not en.alive:
            self._on_enemy_death(en, wc)

    def _on_enemy_death(self, en, wc):
        # drops: xp (instant party-wide), gold/shards/potion/equipment (visible
        # ground drops the player walks over — Task C2). XP stays instant because
        # it's party-wide and shouldn't require walking over a sprite. The
        # gold/shard/potion/equipment rewards spawn as drop entities on the
        # ground at the enemy's pos; the pickup/magnet/expire logic is in update.
        p = self.scene.game.player
        hero = wc.hero
        # xp to whole party (with level-up pop) — stays instant (not a drop)
        xp = en.enemy.xp
        for other in self.scene.party:
            if other and other.alive:
                before = other.hero.level
                other.hero.gain_xp(xp)
                if other.hero.level > before:
                    self.scene._on_hero_levelup(other)
        # gold — spawn as a ground drop (visible loot). Bosses drop more (the
        # enemy.gold is already level-scaled in entities.py). The gold_earned
        # stat is tallied at pickup (in _pickup_drop), not here — the stat
        # tracks gold actually collected, not gold spawned on the ground.
        gold = en.enemy.gold
        if gold > 0:
            self.scene._spawn_drop(en.x, en.y, "gold", gold)
        # shards from bosses / elites — bosses scale by row so deeper bosses
        # are worth more (row0=3 ... row4=19); elites rarely drop 1. Non-boss
        # shard drop rate is 15% (was 8%, near-zero sustained shard income).
        # Spawned as a ground drop (visible loot) instead of straight to inventory.
        shards = 0
        if en.is_boss:
            shards = 3 + self.scene.r * 4
        elif random.random() < 0.15:
            shards = 1
        if shards:
            self.scene._spawn_drop(en.x, en.y, "shard", shards)
        # potion drop — 12% chance, spawned as a ground drop (visible loot).
        if random.random() < 0.12:
            self.scene._spawn_drop(en.x, en.y, "hp_potion", 1)
        # equipment drop from bosses — only on the first clear of the cell (gated
        # by ow_bosses_cleared) so the drop can't be farm-grounded; weight the
        # rarity by row so deeper bosses drop better gear. Spawned as a ground
        # drop (visible loot) so the player walks over to pick it up.
        cid = WD.cell_id(self.scene.c, self.scene.r)
        first_clear = en.is_boss and cid not in set(p.ow_bosses_cleared)
        if first_clear and random.random() < 0.6:
            rar = "SSR" if (self.scene.r >= 3 and random.random() < 0.5) else "SR"
            pool = [k for k, v in EQUIPMENT_DB.items() if v["rarity"] == rar]
            if pool:
                eid = random.choice(pool)
                self.scene._spawn_drop(en.x, en.y, "equipment", eid)
        # boss cleared -> mark + row-scaled bonus gems (only the first clear per
        # cell pays out, so bosses can't be farm-grounded for infinite gems).
        # Adventure mode (Task D1) has its own stage-clear reward path + must NOT
        # mutate the open-world state (ow_bosses_cleared, story_progress, the
        # NG+ banner) — the adventure boss is a golem at (0,0), not the open-
        # world boss at (9,r), so the open-world bookkeeping + the story chain
        # are skipped in adventure. The _is_adventure flag is set in
        # AdventureScene.__init__ (adventure_scene.py).
        if en.is_boss and not getattr(self.scene, "_is_adventure", False):
            cleared = set(p.ow_bosses_cleared)
            cid = WD.cell_id(self.scene.c, self.scene.r)
            first_clear = cid not in cleared
            boss_gem = (20 + self.scene.r * 50) if first_clear else 10
            p.gems += boss_gem
            p.stats["gems_earned"] = p.stats.get("gems_earned", 0) + boss_gem
            p.stats["bosses_defeated"] = p.stats.get("bosses_defeated", 0) + 1
            if first_clear:
                p.ow_bosses_cleared = sorted(cleared | {cid})
            self.scene.set_message(f"Boss defeated! +{boss_gem} gems, +{shards} shards")
            # Task E2: advance the story quest chain. The biome-boss quest for
            # this row is marked "complete" + the quest reward (gems + shards)
            # pays out once (only on the first clear, so a rematch doesn't
            # re-pay). The next quest in the chain becomes available (the next
            # NPC can now give it). The void row's boss (9,4) is the Demon King;
            # killing it marks BOTH the void_boss quest (the row's biome-boss)
            # + the demon_king quest (the chain's final marker) complete - the
            # void_boss quest is the row's gate, the demon_king quest is the
            # chain's end (the "World Ascended!" NG+ path below stays). Only
            # mark complete if the quest was active (defensive - a boss that
            # spawned through a stale gate shouldn't advance the chain; the gate
            # should have sealed it).
            biome = WD.cell_biome(self.scene.c, self.scene.r)
            fqid = STORY_BIOME_QUEST.get(biome)
            # the void row's boss (9,4) is the Demon King; killing it completes
            # BOTH the void_boss quest (the row's biome-boss gate) + the
            # demon_king quest (the chain's final marker). The void_boss quest
            # is the row's gate (the boss spawned because it was active); the
            # demon_king quest is the chain's end (the "World Ascended!" NG+
            # banner below + the chain's final reward). The void_boss quest is
            # the row's gate, so it's marked complete when the row's boss dies;
            # the demon_king quest is the chain's end, so it's marked complete
            # when the Demon King dies (the same kill, on the void row). The
            # gate on the void row is the void_boss quest (not the demon_king
            # quest), so a void boss that spawned (void_boss active) is the
            # Demon King; killing it completes both. The demon_king quest is
            # marked complete here too (the chain's end) - it was set "active"
            # by the void NPC when the void_boss quest was accepted (the void
            # NPC gives both the void_boss quest + the demon_king quest, since
            # the void row's boss IS the Demon King).
            is_final = (self.scene.r == WD.GRID_H - 1
                        and getattr(en, "id", None) == "Baron")
            if (fqid is not None and fqid in STORY_QUEST_BY_ID
                    and p.story_progress.get(fqid) == "active"
                    and first_clear):
                p.story_progress[fqid] = "complete"
                # the void row's boss (9,4) is the Demon King; killing it also
                # completes the demon_king quest (the chain's final marker). The
                # demon_king quest is the chain's end - it has its own reward +
                # the "World Ascended!" NG+ banner below. Mark it complete so
                # the chain reads as done (the next-quest toast + the NG+ path
                # both fire). Only mark it if it was active (the void NPC set it
                # active when the void_boss quest was accepted).
                if (is_final
                        and p.story_progress.get(STORY_FINAL_QUEST) == "active"):
                    p.story_progress[STORY_FINAL_QUEST] = "complete"
                q = STORY_QUEST_BY_ID[fqid]
                rw = q.get("reward", {})
                rg = int(rw.get("gems", 0))
                rs = int(rw.get("shards", 0))
                if rg:
                    p.gems += rg
                    p.stats["gems_earned"] = p.stats.get("gems_earned", 0) + rg
                if rs:
                    p.shards += rs
                # pay the demon_king quest's reward too (the chain's end pays
                # its own reward on top of the void_boss reward) so the final
                # boss feels like a climax.
                if is_final:
                    fq = STORY_QUEST_BY_ID.get(STORY_FINAL_QUEST)
                    if fq is not None:
                        frw = fq.get("reward", {})
                        frg = int(frw.get("gems", 0))
                        frs = int(frw.get("shards", 0))
                        if frg:
                            p.gems += frg
                            p.stats["gems_earned"] = p.stats.get("gems_earned", 0) + frg
                        if frs:
                            p.shards += frs
                # the next quest in the chain becomes available - surface a
                # toast so the player knows where to go next. If this was the
                # last quest (demon_king), the "World Ascended!" banner below
                # is the end-of-chain beat (no "next quest" toast).
                idx = STORY_QUEST_ORDER.index(fqid)
                if idx + 1 < len(STORY_QUEST_ORDER):
                    nq = STORY_QUEST_BY_ID[STORY_QUEST_ORDER[idx + 1]]
                    self.scene.set_message(
                        f"Quest complete: {q['name']}! Next: {nq['name']}", 3.0)
                else:
                    self.scene.set_message(
                        f"Quest complete: {q['name']}! The chain is done.", 3.0)
            # defeat celebration: a long hit-stop, a big flash, a victory burst,
            # and a "BOSS DEFEATED" banner with the boss name for ~2.5s
            self.scene.hit_stop = max(self.scene.hit_stop, 0.5)
            self.scene.flash = 0.6
            if self.scene._reduce_motion:
                self.scene.flash *= 0.4
            self.scene.particles.burst(en.x, en.y, (255, 220, 120), n=80, speed=420, size=9, life=1.0, grav=0)
            self.scene.particles.ring(en.x, en.y, (255, 240, 160), n=40, speed=560, size=8, life=0.8)
            self.scene.camera.add_shake(14, self.scene._shake_mul)
            audio.play("victory", 0.7)
            self.scene._boss_defeat_name = en.enemy.name
            self.scene._boss_defeat_t = 2.5
            # Aetheric Cycle: when the FINAL boss (Baron Nashor at 9,4) is
            # defeated for the first time this cycle, show a "World Ascended!"
            # banner so the player knows they can now Ascend the World from
            # the title screen to start NG+. The cell is (9,4) and the boss id
            # for row 4 is "Baron" — check both so a non-final boss on the
            # same row (none currently, but defensive) can't trigger this.
            if (WD.is_boss_cell(self.scene.c, self.scene.r) and self.scene.c == WD.GRID_W - 1
                    and self.scene.r == WD.GRID_H - 1
                    and getattr(en, "id", None) == "Baron"):
                self.scene._ascend_banner_t = 3.0
                self.scene.set_message(
                    "World Ascended! Return to the title to start a new cycle.",
                    4.0)
        # particles
        self.scene.particles.burst(en.x, en.y, (200, 80, 80), n=20, speed=240, size=6, life=0.5)
        # stats + quests + achievements
        p.stats["enemies_defeated"] = p.stats.get("enemies_defeated", 0) + 1
        p.quest_progress("defeat_enemies", 1)
        p.quest_progress("win_battles", 1)
        # surface newly-unlocked achievements as real-time toasts (the return
        # value was discarded, so unlocks were invisible until the Records tab)
        for aid in p.check_achievements():
            ach = ACHIEVEMENTS.get(aid, {})
            self.scene.set_message(
                f"Achievement: {ach.get('name', '?')}! +{ach.get('reward_gems', 0)} gems",
                3.0)
        # save hero levels back
        for other in self.scene.party:
            if other:
                hid = other.hero.id
                if hid in p.owned:
                    p.owned[hid]["level"] = other.hero.level
                    p.owned[hid]["xp"] = other.hero.xp
        p.save()
        # signature passive: stacking_atk (dict-lookup dispatch — +val ATK per
        # kill, decaying out of combat). The stack is read in effective_atk and
        # decays in update; here we just increment + reset the decay timer.
        _sig = _SIG_ON_KILL.get(wc._signature_kind)
        if _sig:
            _sig(self.scene, wc)
        # ECS adapter (Task 12): the legacy enemy is dead — destroy its parallel
        # entity so the entity layer stops tracking it. The legacy list is NOT
        # mutated here (the dead WorldEnemy stays in self.enemies until the next
        # _load_map rebuilds the list); only the entity is removed from self.world.
        # pop with a -1 sentinel so a missing entry (e.g. an enemy spawned before
        # the adapter existed) doesn't crash the death path.
        ee = self.scene._entity_for_enemy.pop(id(en), None)
        if ee is not None:
            self.scene.world.destroy(ee.eid)
