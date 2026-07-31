"""Skill definitions, skill-type category map, boss ult/pattern tables.

Mechanically split from _legacy_data.py — bodies copied verbatim.
"""

__all__ = [
    "SKILLS_DB", "_SKILL_TYPE_CATEGORY", "BOSS_ULT", "BOSS_IDS",
    "BOSS_PATTERNS", "BOSS_PATTERNS_DEFAULT", "boss_patterns",
]

# ---------------------------------------------------------------------------
# Skill definitions
#   id, name, element, type, power, cost, description
#   type: attack, magic, heal, buff, debuff, aoe_attack, aoe_magic, revive,
#         ultimate
# ---------------------------------------------------------------------------
SKILLS_DB = {
    "basic_attack": dict(name="Strike",        element="fire", type="attack", power=1.0, cost=0,
                        desc="A basic physical strike."),
    # Fire
    "fire_slash":   dict(name="Flame Slash",   element="fire", type="attack", power=1.6, cost=2,
                        desc="A blazing sword strike. May burn."),
    "fire_bolt":    dict(name="Fire Bolt",     element="fire", type="magic",  power=1.9, cost=3,
                        desc="Hurl a bolt of flame."),
    "inferno":      dict(name="Inferno",       element="fire", type="aoe_magic", power=1.4, cost=5,
                        desc="Scorch all enemies. Burns."),
    "meteor":       dict(name="Meteor",        element="fire", type="ultimate", power=2.6, cost=8,
                        desc="Call a meteor to obliterate all enemies. Burns."),
    # Water
    "water_bolt":   dict(name="Frost Lance",   element="water", type="magic", power=1.8, cost=3,
                        desc="A piercing lance of ice. May freeze."),
    "water_heal":   dict(name="Soothing Tide", element="water", type="heal",  power=1.4, cost=3,
                        desc="Restore an ally's HP."),
    "tsunami":      dict(name="Tsunami",       element="water", type="ultimate", power=2.5, cost=8,
                        desc="A towering wave that engulfs all enemies."),
    "tidal_wave":   dict(name="Tidal Wave",    element="water", type="aoe_magic", power=1.5, cost=5,
                        desc="Wash over all enemies."),
    # Wind
    "wind_arrow":   dict(name="Gale Arrow",    element="wind", type="attack", power=1.7, cost=2,
                        crit_bonus=0.15,
                        desc="A swift arrow of wind. High crit."),
    "tempest":      dict(name="Tempest",       element="wind", type="ultimate", power=2.5, cost=8,
                        desc="A cataclysmic cyclone that tears through all enemies."),
    "wind_aoe":     dict(name="Cyclone",       element="wind", type="aoe_attack", power=1.8, cost=4,
                        desc="A cyclone hits all enemies."),
    "swift_buff":   dict(name="Swiftness",     element="wind", type="buff",   power=0, cost=3,
                        desc="Raise an ally's ATK.", buff="atk_up", potency=0.3, dur=3),
    # Light
    "light_slash":  dict(name="Radiant Slash", element="light", type="attack", power=1.7, cost=2,
                        desc="A holy slash of light."),
    "light_heal":   dict(name="Holy Light",    element="light", type="heal",  power=1.6, cost=3,
                        desc="Restore an ally's HP."),
    "fire_curse":   dict(name="Cinder Curse",  element="fire", type="debuff", power=0, cost=3,
                        desc="Curse an enemy: burn + ATK down.", debuff=["burn", "atk_down"], dur=3,
                        dot_potency=8),
    "blessing":     dict(name="Blessing",      element="light", type="buff",  power=0, cost=4,
                        desc="Raise all allies' DEF.", buff="def_up", potency=0.3, dur=3, target_all=True),
    "revive":       dict(name="Miracle",       element="light", type="revive", power=0.5, cost=6,
                        desc="Revive a fallen ally with half HP."),
    "light_hymn":   dict(name="Solar Hymn",    element="light", type="ultimate", power=2.4, cost=8,
                        heal=True, buff="def_up", potency=0.3, dur=3,
                        desc="Heal all allies fully and bless them."),
    # Dark
    "dark_bolt":    dict(name="Shadow Bolt",   element="dark", type="magic", power=1.9, cost=3,
                        desc="A bolt of dark energy."),
    "dark_curse":   dict(name="Curse",         element="dark", type="debuff", power=0, cost=3,
                        desc="Curse an enemy: poison + ATK down.", debuff=["poison", "atk_down"], dur=3,
                        dot_potency=6),
    "dark_aoe":     dict(name="Void Storm",    element="dark", type="aoe_magic", power=1.4, cost=5,
                        desc="Dark storm hits all enemies."),
    "shield_ward":  dict(name="Shadow Veil",   element="dark", type="buff",  power=0, cost=3,
                        desc="Shield an ally, reducing damage.", buff="shield", potency=0, dur=2),
    "void_nova":    dict(name="Void Nova",     element="dark", type="ultimate", power=2.6, cost=8,
                        desc="Unleash the void. Massive dark damage to all."),
    # --- new skills (Phase B) ---
    # Fire
    "fire_strike":  dict(name="Ember Strike",  element="fire", type="attack", power=2.0, cost=3,
                        desc="A heavy burning blow. May burn."),
    "phoenix":      dict(name="Phoenix Rise",  element="fire", type="heal",   power=1.6, cost=4,
                        buff="atk_up", potency=0.3, dur=3,
                        desc="Recover HP and gain ATK up."),
    # Water
    "frost_nova":   dict(name="Frost Nova",    element="water", type="aoe_magic", power=1.3, cost=5,
                        desc="Freeze all enemies in ice."),
    "tide_shield":  dict(name="Tide Aegis",    element="water", type="buff",   power=0, cost=3,
                        desc="Shield an ally.", buff="shield", potency=0, dur=2),
    # Wind
    "gust":         dict(name="Gale Force",    element="wind", type="aoe_attack", power=1.2, cost=3,
                        desc="A sweeping wind hits all."),
    "evasion":      dict(name="Mirage",        element="wind", type="buff",   power=0, cost=2,
                        desc="Raise an ally's SPD.", buff="spd_up", potency=0.3, dur=3),
    # Light
    "sanctuary":    dict(name="Sanctuary",      element="light", type="heal",   power=2.4, cost=4,
                        desc="A great heal for an ally."),
    "judgement_aoe":dict(name="Divine Wrath",  element="light", type="ultimate", power=2.5, cost=9,
                        desc="Holy wrath smites all enemies."),
    # Dark
    "soul_drain":   dict(name="Soul Drain",    element="dark", type="magic",  power=1.6, cost=3,
                        desc="Dark bolt; heals the user a little."),
    "death_coil":   dict(name="Death Coil",    element="dark", type="ultimate", power=2.7, cost=9,
                        desc="Drain the life of all enemies."),
    # --- new status skills (Phase C) ---
    "rupture":      dict(name="Rupture",       element="dark", type="debuff", power=0, cost=2,
                        desc="Inflict bleed + DEF down.", debuff=["bleed", "def_down"], dur=3,
                        dot_potency=10),
    "taunt_skill":  dict(name="Provoke",       element="light", type="buff",  power=0, cost=2,
                        desc="Draw enemy attacks; raise DEF.", buff="taunt", potency=0.3, dur=2),
    "reflect_ward": dict(name="Mirror Veil",   element="water", type="buff",  power=0, cost=4,
                        desc="Reflect a share of damage taken.", buff="reflect", potency=0, dur=2),
    # Boss ultimates (enemies only) — unleashed by the LoL villain bosses below
    # 50% HP (see BOSS_ULT). The desc names the boss whose ult it is.
    "hellfire":     dict(name="Hellfire",      element="fire", type="aoe_magic", power=1.8, cost=0,
                        desc="Baron Nashor's breath scorches all. Burns."),
    "abyssal_wave": dict(name="Abyssal Wave",  element="dark", type="aoe_magic", power=1.7, cost=0,
                        desc="Sylas's wave of unshackled darkness."),
    "frost_cataclysm": dict(name="Frost Cataclysm", element="water", type="aoe_magic", power=1.9, cost=0,
                        desc="Lissandra's cataclysm freezes all."),
    "storm_of_embers": dict(name="Storm of Embers", element="fire", type="aoe_magic", power=2.0, cost=0,
                        desc="Mordekaiser rains iron and fire."),
    # New skill types (summon/beam/trap) — expand the taxonomy so skills read as
    # diverse (the user's "skills kiểu summon, curse, buff, fire" request). These
    # are real combat skills: summon spawns a temporary ally, beam is a line
    # hit-scan, trap is a delayed ground hazard. `innate` is a display-only tag
    # for signature passives (no SKILLS_DB entry — the category map handles it).
    "fire_summon":  dict(name="Ember Construct",  element="fire",  type="summon", power=1.2, cost=5,
                        desc="Summon a fire construct that fights for you.", dur=6, potency=1.2),
    "water_summon": dict(name="Tide Spirit",      element="water", type="summon", power=1.0, cost=5,
                        desc="Summon a water spirit that heals the party.", dur=8, potency=0.8),
    "light_beam":   dict(name="Radiant Lance",    element="light", type="beam",   power=1.5, cost=4,
                        desc="A beam of light piercing all enemies in a line.", range=420),
    "dark_trap":    dict(name="Shadow Snare",     element="dark",  type="trap",   power=2.0, cost=3,
                        desc="Place a dark trap that triggers on the first enemy to step on it.",
                        dur=8, potency=2.0, radius=70),
}

# Assign a `category` field (the UI grouping label) to every skill based on its
# `type`. This is the single source for the skill-tooltip category badge (Task
# B1) + the HERO_ASSETS manifest (Task A2 reads `sk["category"]`). The map
# covers all existing types + the new summon/beam/trap/innate types.
_SKILL_TYPE_CATEGORY = {
    "attack": "Attack", "magic": "Magic",
    "aoe_attack": "AoE", "aoe_magic": "AoE",
    "heal": "Heal", "buff": "Buff", "debuff": "Debuff",
    "ultimate": "Ultimate", "revive": "Revive",
    "summon": "Summon", "beam": "Beam", "trap": "Trap", "innate": "Innate",
}
for _sid, _sk in SKILLS_DB.items():
    _sk.setdefault("category", _SKILL_TYPE_CATEGORY.get(_sk["type"], _sk["type"].title()))
del _sid, _sk

# Boss enemies (the big arena fights in the open world). Maps a boss id to the
# ultimate skill it unleashes below 50% HP. Also the canonical set of boss ids.
# LoL-ified: the open-world bosses are LoL villains, each mapped to one of the
# 4 boss-ult skill ids (hellfire/abyssal_wave/frost_cataclysm/storm_of_embers).
BOSS_ULT = {
    "Sylas":         "abyssal_wave",
    "Swain":         "abyssal_wave",
    "Lissandra":     "frost_cataclysm",
    "Mordekaiser":   "storm_of_embers",
    "Baron":         "hellfire",
    "Viego":         "abyssal_wave",
}
BOSS_IDS = set(BOSS_ULT.keys())

# Boss phase patterns — which telegraphed patterns a boss uses at each phase.
# Phase 1 (100-66% HP): no special pattern (just the basic strike + the 50% ult).
# Phase 2 (66-33% HP): "charge" — telegraph a line to the player, then dash.
# Phase 3 (33-0% HP): adds "slam" — an expanding ring burst the player dodges.
# Keyed per boss id so each boss fights differently; bosses without an entry
# fall back to the default pattern set for their phase.
BOSS_PATTERNS = {
    "Sylas":       {2: ["charge"],            3: ["charge", "slam"]},
    "Swain":       {2: ["charge", "slam"],    3: ["charge", "slam"]},
    "Lissandra":   {2: ["slam"],              3: ["charge", "slam"]},
    "Mordekaiser": {2: ["charge"],            3: ["charge", "slam"]},
    "Baron":       {2: ["charge", "slam"],    3: ["charge", "slam"]},
    "Viego":       {2: ["slam"],              3: ["charge", "slam"]},
}
# default patterns for a boss id without a specific entry
BOSS_PATTERNS_DEFAULT = {2: ["charge"], 3: ["charge", "slam"]}


def boss_patterns(boss_id, phase):
    """Return the list of pattern names available to a boss at a given phase."""
    pat = BOSS_PATTERNS.get(boss_id, BOSS_PATTERNS_DEFAULT)
    return pat.get(phase, [])
