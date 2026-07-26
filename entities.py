"""
Aetheria Gacha - Entities
Hero and Enemy runtime objects with stats, leveling, equipment, ascension,
crit and effects.
"""
import os
import pygame
import random
import math

import data as D

ASSET_DIR = D.ASSET_DIR
_cache = {}

def load_image(rel_path, scale=None):
    key = (rel_path, scale)
    if key in _cache:
        return _cache[key]
    path = os.path.join(ASSET_DIR, rel_path)
    img = pygame.image.load(path).convert_alpha()
    if scale:
        img = pygame.transform.smoothscale(img, scale)
    _cache[key] = img
    return img

def load_char_sprite(hero_id, size=256):
    return load_image(os.path.join("characters", hero_id + ".png"), (size, size))

def load_portrait(hero_id, size=440):
    return load_image(os.path.join("portraits", hero_id + ".png"), (size, size))

def load_enemy_sprite(enemy_id, size=256):
    return load_image(os.path.join("enemies", enemy_id + ".png"), (size, size))

def load_skill_icon(skill_id, size=64):
    return load_image(os.path.join("skills", skill_id + ".png"), (size, size))

def load_bg(name):
    return load_image(os.path.join("backgrounds", name + ".png"))

def load_ui(name):
    return load_image(os.path.join("ui", name + ".png"))

def load_item_icon(item_id, size=64):
    return load_image(os.path.join("items", item_id + ".png"), (size, size))


class StatusEffect:
    def __init__(self, etype, duration, potency=0):
        self.type = etype
        self.duration = duration
        self.potency = potency

    def tick(self):
        """Return (kind, value) to apply this turn, or None."""
        self.duration -= 1
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
        return self.duration < 0


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
    def atk_mod(self):
        m = 1.0
        for e in self.effects:
            if e.type == "atk_up":   m += e.potency
            elif e.type == "atk_down": m -= e.potency
        return max(0.1, m)

    def def_mod(self):
        m = 1.0
        for e in self.effects:
            if e.type == "def_up":   m += e.potency
            elif e.type == "def_down": m -= e.potency
        return max(0.1, m)

    def spd_mod(self):
        m = 1.0
        for e in self.effects:
            if e.type == "spd_up": m += e.potency
        return m

    def effective_spd(self):
        return int(self.spd * self.spd_mod())

    def has_shield(self):
        return any(e.type == "shield" for e in self.effects)

    def is_taunting(self):
        return any(e.type == "taunt" for e in self.effects)

    def reflect_frac(self):
        """Fraction of incoming damage reflected, if any."""
        for e in self.effects:
            if e.type == "reflect":
                return 0.3
        return 0.0

    def is_stunned(self):
        return any(e.type == "stun" for e in self.effects)

    def is_frozen(self):
        return any(e.type == "freeze" for e in self.effects)

    # --- HSR-style toughness / break ---
    def has_toughness(self):
        return self.max_toughness > 0

    def is_broken(self):
        return self.broken

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

    def tick_effects(self):
        """Apply per-turn effect ticks. Returns list of (text, color) floats."""
        results = []
        for e in list(self.effects):
            res = e.tick()
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

    def clear_round_flags(self):
        self.defending = False

    def update_anim(self, dt):
        if self.shake > 0: self.shake = max(0, self.shake - dt * 40)
        if self.flash > 0: self.flash = max(0, self.flash - dt * 3)
        self.scale_fx += (self.target_scale - self.scale_fx) * min(1, dt * 10)
        self.display_hp += (self.hp - self.display_hp) * min(1, dt * 8)
        if self.max_toughness > 0:
            self.display_toughness += (self.toughness - self.display_toughness) * min(1, dt * 8)
        if self.entry_anim > 0:
            self.entry_anim = max(0, self.entry_anim - dt * 2)
        # KO fade-out animation
        if not self.alive:
            self.ko_anim = min(1.0, self.ko_anim + dt * 2)


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
            if key == "defn": base *= (1 + eb.get("def_pct", 0))
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
        # HSR-style energy gauge (replaces MP as the action resource)
        # energy pool can be enlarged by the tree
        self.max_energy = int(D.ENERGY_MAX * (1 + eb.get("energy_pct", 0)))
        self.energy = min(D.ENERGY_START, self.max_energy)
        # skill cost multiplier from the tree (e.g. Overflow: 0.85)
        self.skill_cost_mult = eb.get("skill_cost_mult", 1.0)
        # LoL-style passive (always-on combat modifier) for this hero. The
        # evolution tree can grant an extra passive; we pick the tree's if any,
        # else the hero's base passive.
        base_passive = D.hero_passive(self.id)
        if eb.get("passive"):
            self.passive = D.PASSIVES_DB.get(eb["passive"], base_passive)
        else:
            self.passive = base_passive

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
            if key == "defn": base *= (1 + eb.get("def_pct", 0))
            if key == "mp":   base *= (1 + eb.get("energy_pct", 0))
            if key == "hp":   base *= (1 + sb.get("hp_pct", 0))
            if key == "atk":  base *= (1 + sb.get("atk_pct", 0))
            if key == "defn": base *= (1 + sb.get("defn_pct", 0))
            return max(1, int(base * asc_mul * evolve_mul))
        self.max_hp = stat("hp"); self.atk = stat("atk"); self.defn = stat("defn")
        self.spd = stat("spd"); self.max_mp = stat("mp")
        self.max_energy = int(D.ENERGY_MAX * (1 + eb.get("energy_pct", 0)))
        self.hp = self.max_hp
        self.mp = self.max_mp
        # crit bonuses from the tree
        self.crit_chance = (D.BASE_CRIT_CHANCE + 0.02 * self.ascension
                            + 0.01 * self.evolve + eb.get("crit", 0))
        if self.role == "hunt":
            self.crit_chance += 0.04
        self.crit_dmg_bonus = eb.get("crit_dmg", 0)
        self.skill_cost_mult = eb.get("skill_cost_mult", 1.0)

    def power(self):
        return self.max_hp + self.atk * 8 + self.defn * 5 + self.spd * 3 + self.max_mp * 2

    def skill_energy_cost(self, skill_id):
        cost = D.skill_energy_cost(D.SKILLS_DB[skill_id])
        # evolution tree can reduce skill energy costs (multiplicative)
        return int(cost * getattr(self, "skill_cost_mult", 1.0))

    def can_use_skill(self, skill_id):
        return self.energy >= self.skill_energy_cost(skill_id)

    def can_ultimate(self):
        return bool(self.ultimate) and self.energy >= D.ENERGY_MAX

    # --- evolution tree ---
    def evo_tree(self):
        return D.hero_evo_tree(self.def_dict)

    def evo_unlocked(self):
        return set(self.evo_nodes)

    def evo_can_unlock(self, node_id):
        tree = self.evo_tree()
        node = next((n for n in tree if n["id"] == node_id), None)
        if node is None:
            return False
        if node_id in self.evo_nodes:
            return False
        return D.evo_node_prereq_met(node, self.evo_nodes)

    def evo_unlock(self, node_id):
        """Apply a tree node. Returns True if applied."""
        if not self.evo_can_unlock(node_id):
            return False
        self.evo_nodes.append(node_id)
        self._evo_bonus = _compute_evo_bonus(self.def_dict, self.evo_nodes)
        self._recompute()
        return True


def _compute_evo_bonus(hero_def, node_ids):
    """Sum the stat bonuses + passive from the unlocked tree nodes."""
    tree = D.hero_evo_tree(hero_def)
    by_id = {n["id"]: n for n in tree}
    bonus = dict(hp_pct=0, atk_pct=0, def_pct=0, energy_pct=0,
                 crit=0, crit_dmg=0, skill_cost_mult=1.0)
    passive = None
    for nid in node_ids:
        n = by_id.get(nid)
        if not n:
            continue
        st = n.get("stats", {})
        for k, v in st.items():
            if k in bonus:
                if k == "skill_cost_mult":
                    bonus[k] *= v   # multiplicative
                else:
                    bonus[k] += v
        if n.get("passive"):
            passive = n["passive"]
    bonus["passive"] = passive
    return bonus


class Enemy(Combatant):
    def __init__(self, enemy_id, level=1):
        d = D.ENEMIES_DB[enemy_id]
        self.id = enemy_id
        self.def_dict = d
        self.level = level
        # HP scales fully with level; ATK/DEF scale more gently so higher
        # levels are tankier but not instantly lethal.
        scale = 1 + 0.20 * (level - 1)
        atk_scale = 1 + 0.10 * (level - 1)
        hp = int(d["hp"] * scale)
        atk = int(d["atk"] * atk_scale)
        defn = int(d["defn"] * atk_scale)
        spd = int(d["spd"] * scale)
        super().__init__(d["name"], d["element"], hp, hp, atk, defn, spd, 0, 0)
        self.skills = list(d["skills"])
        self.xp = int(d["xp"] * scale)
        self.gold = int(d["gold"] * scale)
        self.is_boss = enemy_id in D.BOSS_IDS
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

    def boss_ultimate_id(self):
        return D.BOSS_ULT.get(self.id)
