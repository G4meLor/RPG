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
import random

from src.entities.components import Combat, Health, Statuses, Identity, Transform
from src.data.skills import SKILLS_DB
from src.data.heroes import ULTIMATE_VARIANTS, hero_abilities
from src.data.tuning import (AA_CD, BASE_CRIT_CHANCE, COMBO_BONUS_PER,
    ENERGY_GAIN_BASIC, ENERGY_GAIN_DEAL, element_mult)
from src.data.elements import reaction_for, REACTION_WINDOW


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
