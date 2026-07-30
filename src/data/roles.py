"""Combat roles (HSR-style paths) + role stat multiplier.

Mechanically split from _legacy_data.py — bodies copied verbatim.
"""

__all__ = ["ROLES", "role_mult"]

# ---------------------------------------------------------------------------
# Combat roles (HSR-style paths)
#   Each hero has a role that shapes its stat profile and energy flow:
#     destruction  - AoE/single physical burst, high ATK
#     hunt         - single-target nuke, bonus vs broken, high crit
#     erudition    - AoE magic burst
#     harmony      - team buffs (ATK/SPD/crit up)
#     nihility     - debuffs + DoT (poison/bleed/burn/atk_down)
#     preservation - shields + taunt + DEF
#     abundance    - healing + energy battery
# ---------------------------------------------------------------------------
ROLES = {
    "destruction":  dict(name="Destruction",  color=(220, 90, 70),  stat=dict(atk=1.10)),
    "hunt":         dict(name="Hunt",          color=(90, 200, 230), stat=dict(atk=1.05, spd=1.05)),
    "erudition":    dict(name="Erudition",     color=(180, 120, 220),stat=dict(atk=1.08)),
    "harmony":      dict(name="Harmony",       color=(220, 200, 90), stat=dict(spd=1.05)),
    "nihility":     dict(name="Nihility",      color=(160, 90, 200), stat=dict(atk=1.04)),
    "preservation": dict(name="Preservation",  color=(120, 180, 230),stat=dict(defn=1.12, hp=1.08)),
    "abundance":    dict(name="Abundance",     color=(120, 220, 150),stat=dict(hp=1.06, mp=1.10)),
}

def role_mult(role, key):
    """Stat multiplier for a hero's role (1.0 if no role / no bonus for key)."""
    if not role:
        return 1.0
    return ROLES.get(role, {}).get("stat", {}).get(key, 1.0)
