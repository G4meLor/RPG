"""Elemental resonance — Genshin-style party-composition buff.

Mechanically split from _legacy_data.py — bodies copied verbatim.
"""
from src.data.heroes import HERO_BY_ID  # noqa: F401 (used by team_resonances)

__all__ = ["ELEMENTAL_RESONANCE", "team_resonances"]


# ---------------------------------------------------------------------------
# Elemental resonance — a Genshin-style party-composition buff. When 2+ heroes
# in the 4-hero party share an element, a themed buff is granted to the whole
# party (capped at 2-of-a-kind; 3x/4x do NOT scale further). The buff "kind"
# matches the keys the combat code reads (atk_pct / heal_amp / move_speed /
# energy_regen / crit_dmg). Values are deliberately modest so a rainbow team
# (4 different elements) isn't crowded out — resonance is a small reward for
# committing to an element, not a dominant strategy.
#   buff kinds (applied in world_scene/world_entities):
#     atk_pct     - +flat % ATK  (fire)   -> effective_atk
#     heal_amp    - +flat % heal (water)  -> heal branch (adds with p_heal_amp)
#     move_speed  - +flat % move (wind)   -> move_speed
#     energy_regen- +flat % energy regen (light) -> add_energy / regen rate
#     crit_dmg    - +flat crit-dmg bonus (dark)  -> crit multiplier
# ---------------------------------------------------------------------------
ELEMENTAL_RESONANCE = {
    "fire":  dict(name="Fury of Embers",  buff="atk_pct",     val=0.15),
    "water": dict(name="Soothing Tides",  buff="heal_amp",    val=0.20),
    "wind":  dict(name="Swift Zephyrs",   buff="move_speed",  val=0.10),
    "light": dict(name="Radiance",       buff="energy_regen", val=0.15),
    "dark":  dict(name="Shadow Pact",    buff="crit_dmg",    val=0.10),
}

def team_resonances(team_ids):
    """Compute active elemental resonances for a 4-hero team.
    Returns a list of resonance dicts (one per element with >= 2 heroes).
    Capped at 2-of-a-kind: 3 or 4 of the same element still grants exactly one
    resonance (no scaling), matching Genshin's 2-element party-buff model."""
    counts = {}
    for hid in team_ids:
        if not hid or hid not in HERO_BY_ID:
            continue
        el = HERO_BY_ID[hid]["element"]
        counts[el] = counts.get(el, 0) + 1
    out = []
    for el, n in counts.items():
        if n >= 2:
            r = ELEMENTAL_RESONANCE.get(el)
            if r:
                # copy so callers can't mutate the shared dict
                out.append(dict(r))
    return out

