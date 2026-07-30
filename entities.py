"""
Aetheria Gacha - Entities
Hero and Enemy runtime objects with stats, leveling, equipment, ascension,
crit and effects.
"""
import os
import pygame

import data as D

ASSET_DIR = D.ASSET_DIR
_cache = {}

def load_image(rel_path, scale=None):
    key = (rel_path, scale)
    if key in _cache:
        return _cache[key]
    path = os.path.join(ASSET_DIR, rel_path)
    img = pygame.image.load(path)
    # jpg (splash art) has no alpha channel — .convert() is correct for it;
    # png (sprites/icons) use .convert_alpha(). Detect by the file's actual
    # format rather than the extension so a renamed file still works.
    if img.get_flags() & 0x00010000:  # SRCALPHA already set (32-bit png)
        img = img.convert_alpha()
    else:
        # no alpha (24-bit jpg) — try convert_alpha; pygame adds an opaque
        # alpha channel so the surface is blittable everywhere a png would be.
        try:
            img = img.convert_alpha()
        except pygame.error:
            img = img.convert()
    if scale:
        img = pygame.transform.smoothscale(img, scale)
    _cache[key] = img
    return img

def _load_first(paths, scale=None):
    """Try each relative path in order; return the first that exists on disk
    (via load_image so the cache + convert are reused). If none exist,
    fall through to load_image on the last path so the caller gets the usual
    FileNotFoundError for a truly missing asset."""
    for rel in paths:
        full = os.path.join(ASSET_DIR, rel)
        if os.path.exists(full):
            return load_image(rel, scale)
    return load_image(paths[-1], scale)

def load_char_sprite(hero_id, size=256):
    # per-character bundle: characters/{hero_id}/sprite.png (procedural world
    # billboard). Fall back to the old flat path characters/{hero_id}.png.
    return _load_first([
        os.path.join("characters", hero_id, "sprite.png"),
        os.path.join("characters", hero_id + ".png"),
    ], (size, size))

def load_portrait(hero_id, skin_idx=0, size=440):
    # per-champion bundle: the equipped skin's splash art.
    #   skin_idx 0 -> characters/{hero_id}/portrait.jpg (the Original splash)
    #   skin_idx N -> characters/{hero_id}/skins/{N}.jpg
    # Fall back to the old flat portraits/{hero_id}.png for a pre-restructure
    # save. The splash is a jpg (no alpha) — load_image handles the convert.
    if skin_idx and skin_idx > 0:
        skin_path = os.path.join("characters", hero_id, "skins", str(skin_idx) + ".jpg")
        full = os.path.join(ASSET_DIR, skin_path)
        if os.path.exists(full):
            return load_image(skin_path, (size, size))
    return _load_first([
        os.path.join("characters", hero_id, "portrait.jpg"),
        os.path.join("characters", hero_id, "portrait.png"),
        os.path.join("portraits", hero_id + ".png"),
    ], (size, size))

def load_champ_icon(hero_id, size=128):
    # the real LoL champion icon (128x128, dark bg) for HUD/codex thumbnails.
    return _load_first([
        os.path.join("characters", hero_id, "icon.png"),
    ], (size, size))

def load_enemy_sprite(enemy_id, size=256):
    return load_image(os.path.join("enemies", enemy_id + ".png"), (size, size))

def load_skill_icon(hero_id, skill_id, size=64):
    # per-champion skill art: characters/{hero_id}/skills/{skill_id}.png (the
    # real LoL ability icon for the slot that skill_id fills). Fall back to the
    # global skills/{skill_id}.png (for boss ultimates + skills not in the
    # hero's kit). hero_id may be None to skip the per-hero lookup.
    paths = []
    if hero_id:
        paths.append(os.path.join("characters", hero_id, "skills", skill_id + ".png"))
    paths.append(os.path.join("skills", skill_id + ".png"))
    return _load_first(paths, (size, size))

def load_bg(name):
    return load_image(os.path.join("backgrounds", name + ".png"))

def load_ui(name):
    return load_image(os.path.join("ui", name + ".png"))

def load_item_icon(item_id, size=64):
    return load_image(os.path.join("items", item_id + ".png"), (size, size))

# v2 world sprites — terrain tiles, landmarks, village buildings, ground loot
# drops (Task A4). Each routes through the same load_image cache (entities.py:16)
# so the scene reuses one converted-alpha copy per (path, scale).
def load_terrain(name, scale=None):
    return load_image(os.path.join("terrain", name + ".png"), scale)

def load_landmark(kind, scale=None):
    return load_image(os.path.join("landmarks", kind + ".png"), scale)

def load_village(kind, scale=None):
    return load_image(os.path.join("villages", kind + ".png"), scale)

def load_drop(kind, scale=None):
    return load_image(os.path.join("drops", kind + ".png"), scale)


class StatusEffect:
    def __init__(self, etype, duration, potency=0):
        self.type = etype
        self.duration = duration      # now in seconds (time-based)
        self.potency = potency
        self.t = 0.0                  # time accumulator for the tick cadence

    def tick(self, dt):
        """Return (kind, value) to apply when the accumulator crosses ~0.5s,
        or None. Duration is consumed in seconds (time-based, not per-turn)."""
        self.duration -= dt
        self.t += dt
        if self.t < 0.5:
            return None
        # emit one tick per 0.5s and carry the remainder so high frame rates
        # don't drop ticks
        self.t -= 0.5
        if self.type == "poison":
            return ("damage", self.potency)
        if self.type == "burn":
            return ("damage", self.potency)
        if self.type == "bleed":
            return ("damage", self.potency)
        if self.type == "regen":
            return ("heal", self.potency)
        return None

    def expired(self):
        return self.duration <= 0


class Combatant:
    """Base class for heroes and enemies in combat."""
    def __init__(self, name, element, hp, max_hp, atk, defn, spd, mp, max_mp):
        self.name = name
        self.element = element
        self.hp = hp
        self.max_hp = max_hp
        self.atk = atk
        self.defn = defn
        self.spd = spd
        self.mp = mp
        self.max_mp = max_mp
        self.effects = []          # list of StatusEffect
        self.alive = True
        self.defending = False     # set when defending this round
        # combat presentation
        self.shake = 0
        self.flash = 0
        self.scale_fx = 1.0
        self.target_scale = 1.0
        self.display_hp = hp       # animated HP bar
        self.last_damage = None
        self.last_damage_time = 0
        self.entry_anim = 1.0      # 1.0 = full entrance; animates to 0
        self.ko_anim = 0.0         # 0.0 = alive; animates to 1 on death
        self.crit_chance = D.BASE_CRIT_CHANCE
        # HSR-style toughness / break
        self.max_toughness = 0
        self.toughness = 0
        self.broken = False        # set when toughness hits 0; cleared next round
        self.display_toughness = 0
        # HSR-style energy (replaces MP as the action resource for heroes)
        self.energy = 0
        self.max_energy = D.ENERGY_MAX

    # --- stat modifiers from effects ---
    def spd_mod(self):
        m = 1.0
        for e in self.effects:
            if e.type == "spd_up": m += e.potency
        return m

    def has_shield(self):
        return any(e.type == "shield" for e in self.effects)

    def reflect_frac(self):
        """Fraction of incoming damage reflected, if any."""
        for e in self.effects:
            if e.type == "reflect":
                return 0.3
        return 0.0

    # --- HSR-style toughness / break ---
    def has_toughness(self):
        return self.max_toughness > 0

    # --- HSR-style energy (shared by heroes and enemies) ---
    def skill_energy_cost(self, skill_id):
        return D.skill_energy_cost(D.SKILLS_DB[skill_id])

    def can_use_skill(self, skill_id):
        return self.energy >= self.skill_energy_cost(skill_id)

    def damage_toughness(self, amount, is_weak=False):
        """Shave the toughness bar. Returns True if this hit caused a break."""
        if self.max_toughness <= 0 or self.broken:
            return False
        self.toughness -= amount
        self.display_toughness = max(0, self.toughness)
        if self.toughness <= 0:
            self.toughness = 0
            self.broken = True
            return True
        return False

    def recover_toughness(self):
        """End-of-round toughness recovery (HSR-accurate).
        A broken enemy recovers to full the round after it was broken (the
        break itself is consumed when it skips its turn). Non-broken enemies
        do not mend — so focused weakness fire reliably breaks."""
        if self.max_toughness <= 0:
            return
        if self.broken:
            # break is consumed this round; come back with full toughness
            self.broken = False
            self.toughness = self.max_toughness
        else:
            self.toughness = min(self.max_toughness,
                                  self.toughness + int(self.max_toughness * D.TOUGHNESS_RECOVER_FRAC))
        self.display_toughness = self.toughness

    def take_damage(self, amount, is_crit=False, source=None):
        amount = max(0, int(amount))
        if self.has_shield():
            amount = int(amount * 0.5)
        if self.defending:
            amount = int(amount * (1 - D.DEFEND_MITIGATION))
        # HSR: broken targets take +50% damage
        if self.broken:
            amount = int(amount * D.TOUGHNESS_BREAK_MULT)
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        self.flash = 1.0
        self.shake = 10 if is_crit else 8
        self.last_damage = amount
        # reflect: bounce a fraction back to the attacker
        reflected = 0
        if source is not None and self.alive:
            frac = self.reflect_frac()
            if frac > 0:
                reflected = max(1, int(amount * frac))
                source.hp -= reflected
                if source.hp <= 0:
                    source.hp = 0
                    source.alive = False
        return amount, reflected

    def heal(self, amount):
        amount = max(0, int(amount))
        self.hp = min(self.max_hp, self.hp + amount)
        self.last_damage = -amount
        return amount

    def add_effect(self, etype, duration, potency=0):
        for e in self.effects:
            if e.type == etype:
                e.duration = max(e.duration, duration)
                e.potency = max(e.potency, potency)
                return
        self.effects.append(StatusEffect(etype, duration, potency))

    def tick_effects(self, dt):
        """Apply time-based effect ticks. Returns list of (text, color) floats."""
        results = []
        for e in list(self.effects):
            res = e.tick(dt)
            if res:
                kind, val = res
                if kind == "damage":
                    amt, _ = self.take_damage(val)
                    results.append((str(amt), (140, 240, 120) if e.type == "regen" else (220, 120, 200)))
                elif kind == "heal":
                    self.heal(val)
                    results.append(("+" + str(val), (140, 240, 120)))
        self.effects = [e for e in self.effects if not e.expired()]
        return results


class Hero(Combatant):
    def __init__(self, hero_def, level=1, ascension=0, equipment=None, evolve=0,
                 evo_nodes=None):
        s = hero_def["stats"]
        self.def_dict = hero_def
        self.level = level
        self.xp = 0
        self.id = hero_def["id"]
        self.rarity = hero_def["rarity"]
        self.role = hero_def.get("role", "destruction")
        self.skills = list(hero_def["skills"])
        self.ultimate = hero_def.get("ultimate")
        self.ascension = ascension
        self.evolve = evolve
        self.equipment = equipment or {}  # slot -> item_id
        # evolution tree nodes unlocked (list of node ids); applied as bonuses
        self.evo_nodes = list(evo_nodes) if evo_nodes else []
        # compute the tree-derived bonuses (stat multipliers + extra passive)
        self._evo_bonus = _compute_evo_bonus(hero_def, self.evo_nodes)
        # equipment set bonus (complete matching set across 3 slots)
        self._set_name, self._set_bonus = D.equipment_set_bonus(
            [v for v in (self.equipment or {}).values() if v])
        # ascension multiplier + evolve multiplier (compounding)
        asc_mul = D.ASCENSION_BONUS.get(ascension, 1.0)
        evolve_mul = D.EVOLVE_BONUS.get(evolve, 1.0)
        g = D.STAT_GROWTH
        eb = self._evo_bonus
        sb = self._set_bonus
        def stat(key):
            base = s[key] * (1 + g[key] * (level - 1))
            # equipment bonuses
            for it in self.equipment.values():
                if it and it in D.EQUIPMENT_DB:
                    base += D.EQUIPMENT_DB[it]["stats"].get(key, 0)
            # set-bonus flat additions
            base += sb.get(key, 0)
            # role stat multiplier (HSR paths)
            base *= D.role_mult(self.role, key)
            # evolution-tree stat bonuses
            if key == "hp":   base *= (1 + eb.get("hp_pct", 0))
            if key == "atk":  base *= (1 + eb.get("atk_pct", 0))
            if key == "defn": base *= (1 + eb.get("defn_pct", 0))
            if key == "mp":   base *= (1 + eb.get("energy_pct", 0))
            # set-bus percentage bonuses (applied after role/evo mults)
            if key == "hp":   base *= (1 + sb.get("hp_pct", 0))
            if key == "atk":  base *= (1 + sb.get("atk_pct", 0))
            if key == "defn": base *= (1 + sb.get("defn_pct", 0))
            return max(1, int(base * asc_mul * evolve_mul))
        hp = stat("hp"); atk = stat("atk"); defn = stat("defn")
        spd = stat("spd"); mp = stat("mp")
        super().__init__(hero_def["name"], hero_def["element"], hp, hp, atk, defn, spd, mp, mp)
        self.full_mp = mp
        # crit scales slightly with ascension; hunt role crits more
        self.crit_chance = D.BASE_CRIT_CHANCE + 0.02 * ascension + 0.01 * evolve
        if self.role == "hunt":
            self.crit_chance += 0.04
        # crit + crit-dmg bonuses from the evolution tree
        self.crit_chance += eb.get("crit", 0)
        self.crit_dmg_bonus = eb.get("crit_dmg", 0)
        # set-bonus crit/crit-dmg (applied after the tree — the void set grants
        # +10% crit + 20% crit-dmg; without this the bonus is dead weight)
        self.crit_chance += sb.get("crit", 0)
        self.crit_dmg_bonus += sb.get("crit_dmg", 0)
        # HSR-style energy gauge (replaces MP as the action resource)
        # energy pool can be enlarged by the tree and by equipment set bonuses
        self.max_energy = int(D.ENERGY_MAX * (1 + eb.get("energy_pct", 0) + sb.get("energy_pct", 0)))
        self.energy = min(D.ENERGY_START, self.max_energy)
        # skill cost multiplier from the tree and set bonus (e.g. Overflow: 0.85)
        self.skill_cost_mult = eb.get("skill_cost_mult", 1.0) * sb.get("skill_cost_mult", 1.0)
        # LoL-style passive (always-on combat modifier) for this hero. The
        # evolution tree can grant an extra passive; we pick the tree's if any,
        # else the hero's base passive.
        base_passive = D.hero_passive(self.id)
        if eb.get("passive"):
            self.passive = D.PASSIVES_DB.get(eb["passive"], base_passive)
        else:
            self.passive = base_passive
        # per-hero signature passive (C6) — ADDITIONAL to the shared base
        # passive above. The world loop checks self.signature in addition to
        # self.passive, so the signature layers on top of the evolve-tree
        # passive without replacing it. Distinct from HERO_PASSIVES so pulling
        # Ember (revive_once) vs Cinder (stacking_atk) — both fire destruction,
        # both p_lifesteal today — feels like different heroes.
        self.signature = D.hero_signature(self.id)
        # constellation perks (C1-C6) — layered on top of the flat ascension
        # bonus so old saves don't regress. The flat ASCENSION_BONUS already
        # applied above; here we add the gameplay-changing perks per star.
        # _apply_perks reads the hero's ascension + role/id and folds the effects
        # into skill_cost_mult / crit_dmg_bonus / a new ult_extra dict, and
        # boosts the passive val (passive_boost amplifies the existing passive,
        # it does NOT grant a new passive id — so no duplication with EVO_TREE).
        self.ult_extra = {}
        self._perk_cd_reduction = 0.0
        self._apply_perks()

    def _apply_perks(self):
        """Apply the unlocked constellation perks (C1..C_ascension) to the hero.
        Re-applied by _recompute so leveling/ascension changes take effect.
        Perks layer on top of the tree/set bonuses already computed.

        Idempotent: every perk-derived field (including the passive val) is
        reset to its un-perked base before re-applying, so repeated _recompute
        calls (e.g. on every level-up / evo-node unlock) don't compound the
        passive_boost multiplier. The base passive is re-derived from the hero
        / the current evo-tree bonus each call, copied so the shared
        PASSIVES_DB entry is never mutated."""
        # reset the perk-derived fields so re-application is idempotent
        self.ult_extra = {}
        self._perk_cd_reduction = 0.0
        # re-derive the base passive from the hero / current evo-tree bonus so a
        # previous passive_boost doesn't compound on an already-boosted val. A
        # copy is made so the shared PASSIVES_DB entry is never mutated.
        eb = self._evo_bonus
        base_passive = D.hero_passive(self.id)
        if eb.get("passive"):
            base_passive = D.PASSIVES_DB.get(eb["passive"], base_passive)
        self.passive = dict(base_passive) if base_passive else None
        # start from the tree/set crit_dmg and skill_cost_mult (already set by
        # the caller); perks add to crit_dmg_bonus and multiply skill_cost_mult
        perks = D.constellation_perks_for(self.def_dict, self.ascension)
        for p in perks:
            eff = p.get("effect")
            val = p.get("val", 0)
            if eff == "cd_reduction":
                # reduce skill cooldown timers (applied in _do_skill via the
                # WorldCharacter's per-skill cd). Store as a fraction to subtract.
                self._perk_cd_reduction += val
            elif eff == "energy_cost_cut":
                # reduce skill energy cost (multiplicative on skill_cost_mult)
                self.skill_cost_mult *= (1.0 - val)
            elif eff == "crit_dmg_up":
                # add to crit damage bonus (additive on the bonus term)
                self.crit_dmg_bonus += val
            elif eff == "ult_extra":
                # stash for the world scene to apply in _do_ultimate
                tgt = p.get("target")
                # accumulate per-target so multiple ult_extra perks stack
                if tgt in self.ult_extra:
                    self.ult_extra[tgt] += val
                else:
                    self.ult_extra[tgt] = val
            elif eff == "passive_boost":
                # amplify the base passive val (re-derived above, so this
                # multiplies the un-boosted val — idempotent across recomputes).
                # Does NOT change the passive id, so no duplication with
                # EVO_TREE passives.
                if self.passive and "val" in self.passive:
                    self.passive["val"] = self.passive.get("val", 0) * (1.0 + val)

    def set_name(self):
        return self._set_name

    def evolve_title(self):
        return D.EVOLVE_TITLES.get(self.evolve, "Hero")

    def evolve_color(self):
        return D.EVOLVE_COLORS.get(self.evolve, (220, 220, 235))

    def gain_xp(self, amount):
        self.xp += amount
        leveled = False
        while self.level < D.MAX_LEVEL and self.xp >= D.xp_to_next(self.level):
            self.xp -= D.xp_to_next(self.level)
            self.level += 1
            leveled = True
            self._recompute()
        return leveled

    def _recompute(self):
        s = self.def_dict["stats"]; g = D.STAT_GROWTH
        asc_mul = D.ASCENSION_BONUS.get(self.ascension, 1.0)
        evolve_mul = D.EVOLVE_BONUS.get(self.evolve, 1.0)
        eb = self._evo_bonus
        # re-evaluate the set bonus in case equipment changed
        self._set_name, self._set_bonus = D.equipment_set_bonus(
            [v for v in (self.equipment or {}).values() if v])
        sb = self._set_bonus
        def stat(key):
            base = s[key] * (1 + g[key] * (self.level - 1))
            for it in self.equipment.values():
                if it and it in D.EQUIPMENT_DB:
                    base += D.EQUIPMENT_DB[it]["stats"].get(key, 0)
            base += sb.get(key, 0)
            base *= D.role_mult(self.role, key)
            if key == "hp":   base *= (1 + eb.get("hp_pct", 0))
            if key == "atk":  base *= (1 + eb.get("atk_pct", 0))
            if key == "defn": base *= (1 + eb.get("defn_pct", 0))
            if key == "mp":   base *= (1 + eb.get("energy_pct", 0))
            if key == "hp":   base *= (1 + sb.get("hp_pct", 0))
            if key == "atk":  base *= (1 + sb.get("atk_pct", 0))
            if key == "defn": base *= (1 + sb.get("defn_pct", 0))
            return max(1, int(base * asc_mul * evolve_mul))
        self.max_hp = stat("hp"); self.atk = stat("atk"); self.defn = stat("defn")
        self.spd = stat("spd"); self.max_mp = stat("mp")
        self.max_energy = int(D.ENERGY_MAX * (1 + eb.get("energy_pct", 0) + sb.get("energy_pct", 0)))
        self.hp = self.max_hp
        self.mp = self.max_mp
        # crit bonuses from the tree and equipment set bonus
        self.crit_chance = (D.BASE_CRIT_CHANCE + 0.02 * self.ascension
                            + 0.01 * self.evolve + eb.get("crit", 0) + sb.get("crit", 0))
        if self.role == "hunt":
            self.crit_chance += 0.04
        self.crit_dmg_bonus = eb.get("crit_dmg", 0) + sb.get("crit_dmg", 0)
        self.skill_cost_mult = eb.get("skill_cost_mult", 1.0) * sb.get("skill_cost_mult", 1.0)
        # re-apply constellation perks so leveling/ascension changes take effect
        # (resets ult_extra / _perk_cd_reduction, then re-adds per effect kind)
        self._apply_perks()

    def power(self):
        # Note: max_mp and spd are not currently wired into combat (mp does not
        # feed energy, spd does not affect move/atk speed), so they are excluded
        # from Team Power to avoid inflating the displayed value with dead stats.
        return self.max_hp + self.atk * 8 + self.defn * 5 + self.spd * 3

    def skill_energy_cost(self, skill_id):
        cost = D.skill_energy_cost(D.SKILLS_DB[skill_id])
        # evolution tree can reduce skill energy costs (multiplicative)
        return int(cost * getattr(self, "skill_cost_mult", 1.0))

    def can_use_skill(self, skill_id):
        return self.energy >= self.skill_energy_cost(skill_id)

    def can_ultimate(self):
        # the ult is ready when the energy bar is full; use the hero's own
        # max_energy (which the tree can enlarge) so the HUD bar + the readiness
        # check agree (otherwise a tree-extended bar shows full but can't ult)
        return bool(self.ultimate) and self.energy >= self.max_energy


def _compute_evo_bonus(hero_def, node_ids):
    """Sum the stat bonuses + passive from the unlocked tree nodes."""
    tree = D.hero_evo_tree(hero_def)
    by_id = {n["id"]: n for n in tree}
    # base passive id for this hero — used to detect dead-upgrade nodes whose
    # passive == the hero's base passive (a pure no-op without a consolation).
    base_pid = D.HERO_PASSIVES.get(hero_def.get("id"))
    bonus = dict(hp_pct=0, atk_pct=0, defn_pct=0, energy_pct=0,
                 crit=0, crit_dmg=0, skill_cost_mult=1.0)
    passive = None
    for nid in node_ids:
        n = by_id.get(nid)
        if not n:
            continue
        st = n.get("stats", {})
        for k, v in st.items():
            # normalize legacy def_pct -> defn_pct to match the stat key, so
            # the evo tree (def_pct) and the set handler (defn_pct) share one key
            nk = "defn_pct" if k == "def_pct" else k
            if nk in bonus:
                if nk == "skill_cost_mult":
                    bonus[nk] *= v   # multiplicative
                else:
                    bonus[nk] += v
        # passive: a node whose passive == the hero's base passive is a dead
        # upgrade (it grants nothing). Fold it into a +5% ATK consolation so the
        # shard is never wasted; otherwise adopt the tree's passive.
        npid = n.get("passive")
        if npid:
            if npid == base_pid:
                bonus["atk_pct"] = bonus.get("atk_pct", 0) + 0.05
            else:
                passive = npid
    bonus["passive"] = passive
    return bonus


class Enemy(Combatant):
    def __init__(self, enemy_id, level=1, is_boss=False):
        # Champion-as-enemy: if enemy_id is a LoL champion key, build the def
        # from the champion's baked stats (champion_enemy_def) instead of
        # ENEMIES_DB. The is_boss flag scales the champ to boss-tier. This lets
        # a champion spawn as an open-world minion/boss with its real kit.
        if enemy_id in D._CH.CHAMPION_BY_KEY:
            d = D.champion_enemy_def(enemy_id, is_boss=is_boss)
            if d is None:
                d = D.ENEMIES_DB[enemy_id]
        else:
            d = D.ENEMIES_DB[enemy_id]
        self.id = enemy_id
        self.def_dict = d
        self.level = level
        # HP scales fully with level; ATK/DEF scale more gently so higher
        # levels are tankier but not instantly lethal.
        scale = 1 + 0.12 * (level - 1)
        atk_scale = 1 + 0.10 * (level - 1)
        hp = int(d["hp"] * scale)
        atk = int(d["atk"] * atk_scale)
        defn = int(d["defn"] * atk_scale)
        spd = int(d["spd"] * scale)
        super().__init__(d["name"], d["element"], hp, hp, atk, defn, spd, 0, 0)
        self.skills = list(d["skills"])
        self.xp = int(d["xp"] * scale)
        self.gold = int(d["gold"] * scale)
        self.is_boss = enemy_id in D.BOSS_IDS or is_boss
        self._used_ultimate = False
        # HSR-style weakness + toughness
        self.weakness = d.get("weakness", None)
        t = int(d.get("toughness", 0) * scale)
        self.max_toughness = t
        self.toughness = t
        self.display_toughness = t
        # enemies use the energy gauge too, so they can use their skills.
        # They start at 0 so they open with a basic attack (building energy)
        # rather than nuking with their strongest skill on turn 1.
        self.energy = 0
        self.max_energy = D.ENERGY_MAX

