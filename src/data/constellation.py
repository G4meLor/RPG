"""Constellation perks (C1-C6) — per-hero gameplay-changing perks.

Mechanically split from _legacy_data.py — bodies copied verbatim.
"""

__all__ = [
    "CONSTELLATION_PERKS", "CONSTELLATION_PERK_OVERRIDES",
    "hero_constellation_perks", "constellation_perks_for",
]

# ---------------------------------------------------------------------------
# Constellation perks (C1-C6) — per-hero gameplay-changing perks unlocked at
# each ascension star. Layer ON TOP of the flat ASCENSION_BONUS (which is
# kept) so old saves don't regress: the flat multiplier still applies; perks add
# distinct gameplay effects. Keyed by role -> list of 6 perk dicts
# (one per star C1..C6). A few hero-specific overrides are keyed by hero id in
# CONSTELLATION_PERK_OVERRIDES (a full 6-perk list that replaces the template).
#
#   perk dict: id, name, desc, effect, val, target (optional)
#   effect kinds (applied in entities.Hero + world_scene):
#     cd_reduction    - reduce skill cooldown timers (fraction: 0.10 = -10%)
#     ult_extra       - add an effect to the ultimate (target: self_heal /
#                       party_buff / atk_buff); val is the fraction
#     passive_boost   - boost the hero's passive val (fraction: 0.10 = +10%)
#     energy_cost_cut - reduce skill energy cost (fraction: 0.10 = -10%)
#     crit_dmg_up     - add to crit damage bonus (fraction: 0.15 = +15%)
#
# Coordination with EVO_TREE: passive_boost boosts the hero's *existing*
# passive val (it does NOT grant a new passive id), so it never duplicates an
# EVO_TREE passive id. The tree grants passives; perks amplify what's there.
# ---------------------------------------------------------------------------
CONSTELLATION_PERKS = {
    # --- Destruction: burst / lifesteal ---
    "destruction": [
        dict(id="c1", name="Carnage", desc="Skill cooldowns -10%.",
             effect="cd_reduction", val=0.10),
        dict(id="c2", name="Bloodfeast", desc="Crit damage +15%.",
             effect="crit_dmg_up", val=0.15),
        dict(id="c3", name="Inner Fire", desc="Passive effect +10%.",
             effect="passive_boost", val=0.10),
        dict(id="c4", name="Last Blood", desc="Ultimate heals you for 15% max HP.",
             effect="ult_extra", val=0.15, target="self_heal"),
        dict(id="c5", name="Efficient Slaughter", desc="Skill energy cost -10%.",
             effect="energy_cost_cut", val=0.10),
        dict(id="c6", name="Apex Predator", desc="Ultimate deals +30% ATK.",
             effect="ult_extra", val=0.30, target="atk_buff"),
    ],
    # --- Hunt: crit / single-target nuke ---
    "hunt": [
        dict(id="c1", name="Killer Instinct", desc="Crit damage +20%.",
             effect="crit_dmg_up", val=0.20),
        dict(id="c2", name="Swift Strike", desc="Skill cooldowns -10%.",
             effect="cd_reduction", val=0.10),
        dict(id="c3", name="Hunter's Focus", desc="Passive effect +10%.",
             effect="passive_boost", val=0.10),
        dict(id="c4", name="Mark for Death", desc="Ultimate deals +25% ATK.",
             effect="ult_extra", val=0.25, target="atk_buff"),
        dict(id="c5", name="Precision", desc="Crit damage +15%.",
             effect="crit_dmg_up", val=0.15),
        dict(id="c6", name="Coup de Grace", desc="Ultimate heals you for 10% max HP.",
             effect="ult_extra", val=0.10, target="self_heal"),
    ],
    # --- Erudition: AoE magic / energy ---
    "erudition": [
        dict(id="c1", name="Arcane Economy", desc="Skill energy cost -12%.",
             effect="energy_cost_cut", val=0.12),
        dict(id="c2", name="Quick Cast", desc="Skill cooldowns -10%.",
             effect="cd_reduction", val=0.10),
        dict(id="c3", name="Flowing Power", desc="Passive effect +10%.",
             effect="passive_boost", val=0.10),
        dict(id="c4", name="Conduit", desc="Ultimate buffs party ATK +15%.",
             effect="ult_extra", val=0.15, target="party_buff"),
        dict(id="c5", name="Frugal Spells", desc="Skill energy cost -10%.",
             effect="energy_cost_cut", val=0.10),
        dict(id="c6", name="Overload", desc="Crit damage +20%.",
             effect="crit_dmg_up", val=0.20),
    ],
    # --- Harmony: support / buffs ---
    "harmony": [
        dict(id="c1", name="Rhythmic Cast", desc="Skill cooldowns -12%.",
             effect="cd_reduction", val=0.12),
        dict(id="c2", name="Mana Thrift", desc="Skill energy cost -10%.",
             effect="energy_cost_cut", val=0.10),
        dict(id="c3", name="Inspiring Aura", desc="Passive effect +15%.",
             effect="passive_boost", val=0.15),
        dict(id="c4", name="Rallying Cry", desc="Ultimate buffs party ATK +20%.",
             effect="ult_extra", val=0.20, target="party_buff"),
        dict(id="c5", name="Self Care", desc="Ultimate heals you for 15% max HP.",
             effect="ult_extra", val=0.15, target="self_heal"),
        dict(id="c6", name="Cadence", desc="Skill cooldowns -10%.",
             effect="cd_reduction", val=0.10),
    ],
    # --- Nihility: debuffs / DoT ---
    "nihility": [
        dict(id="c1", name="Weak Point", desc="Crit damage +15%.",
             effect="crit_dmg_up", val=0.15),
        dict(id="c2", name="Relentless", desc="Skill cooldowns -10%.",
             effect="cd_reduction", val=0.10),
        dict(id="c3", name="Corrupting Touch", desc="Passive effect +10%.",
             effect="passive_boost", val=0.10),
        dict(id="c4", name="Soul Reaver", desc="Ultimate deals +25% ATK.",
             effect="ult_extra", val=0.25, target="atk_buff"),
        dict(id="c5", name="Efficient Curse", desc="Skill energy cost -10%.",
             effect="energy_cost_cut", val=0.10),
        dict(id="c6", name="Death's Mark", desc="Crit damage +15%.",
             effect="crit_dmg_up", val=0.15),
    ],
    # --- Preservation: tank / shields ---
    "preservation": [
        dict(id="c1", name="Steady Pace", desc="Skill cooldowns -10%.",
             effect="cd_reduction", val=0.10),
        dict(id="c2", name="Energy Reserve", desc="Skill energy cost -10%.",
             effect="energy_cost_cut", val=0.10),
        dict(id="c3", name="Stalwart Guard", desc="Passive effect +15%.",
             effect="passive_boost", val=0.15),
        dict(id="c4", name="Second Wind", desc="Ultimate heals you for 20% max HP.",
             effect="ult_extra", val=0.20, target="self_heal"),
        dict(id="c5", name="Patience", desc="Skill cooldowns -10%.",
             effect="cd_reduction", val=0.10),
        dict(id="c6", name="Guardian's Oath", desc="Ultimate buffs party ATK +15%.",
             effect="ult_extra", val=0.15, target="party_buff"),
    ],
    # --- Abundance: healing / sustain ---
    "abundance": [
        dict(id="c1", name="Gentle Hands", desc="Skill cooldowns -12%.",
             effect="cd_reduction", val=0.12),
        dict(id="c2", name="Mana Spring", desc="Skill energy cost -10%.",
             effect="energy_cost_cut", val=0.10),
        dict(id="c3", name="Bountiful Mercy", desc="Passive effect +15%.",
             effect="passive_boost", val=0.15),
        dict(id="c4", name="Tide of Life", desc="Ultimate buffs party ATK +25%.",
             effect="ult_extra", val=0.25, target="party_buff"),
        dict(id="c5", name="Self Renewal", desc="Ultimate heals you for 15% max HP.",
             effect="ult_extra", val=0.15, target="self_heal"),
        dict(id="c6", name="Eternal Grace", desc="Skill cooldowns -10%.",
             effect="cd_reduction", val=0.10),
    ],
}

# Hero-specific capstone overrides — a few heroes get a unique 6-perk list that
# reflects their kit instead of the role template. Keyed by hero id. (The
# pre-LoL procedural heroes that had overrides here were removed with the
# roster redesign; the table is kept for champion-specific overrides.)
CONSTELLATION_PERK_OVERRIDES = {
}


def hero_constellation_perks(hero_def):
    """Return the 6 constellation perks (C1-C6) for a hero by id, else by role.
    Hero-specific overrides take precedence over the role template."""
    hid = hero_def.get("id")
    if hid and hid in CONSTELLATION_PERK_OVERRIDES:
        return CONSTELLATION_PERK_OVERRIDES[hid]
    role = hero_def.get("role", "destruction")
    return CONSTELLATION_PERKS.get(role, CONSTELLATION_PERKS["destruction"])


def constellation_perks_for(hero_def, ascension):
    """Return the list of perks unlocked at or below the given ascension.
    Ascension 0 = no perks; ascension N unlocks perks C1..CN (capped at 6)."""
    perks = hero_constellation_perks(hero_def)
    n = max(0, min(6, int(ascension)))
    return list(perks[:n])
