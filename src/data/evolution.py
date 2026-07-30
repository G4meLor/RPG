"""Evolution tree — branching per-hero skill tree (LoL/Honkai style).

Mechanically split from _legacy_data.py — bodies copied verbatim.
"""

__all__ = [
    "EVO_TREE", "EVO_TREE_DEFAULT", "hero_evo_tree",
    "EVO_NODE_POS", "EVO_LINKS", "evo_node_prereq_met",
]



# ---------------------------------------------------------------------------
# Evolution tree — a branching per-hero skill tree (LoL/Honkai style).
#   Each hero has a small tree of nodes arranged in tiers (rows). A node is
#   unlocked by spending soul shards once its prerequisite (the node above it
#   in the same branch) is unlocked. Nodes grant stat bonuses; some unlock a
#   bonus skill or passive. The tree is shared across all heroes of the same
#   role to keep data compact, then keyed by hero id at runtime.
#
#   Tree layout (per role):
#     tier 0 (root)        -> one starter node
#     tier 1 (branch A/B)  -> two branch heads (offensive / defensive)
#     tier 2 (branch A/B)  -> one node each (capstone)
#   So 5 nodes per hero: root, A1, A2, B1, B2.
#
#   A node dict: id, name, desc, cost (shards), stats (bonus dict),
#                skill (optional skill id to add), passive (optional passive id)
# ---------------------------------------------------------------------------
EVO_TREE = {
    # --- Destruction: burst / lifesteal ---
    "destruction": [
        dict(id="root", name="Ignition", desc="+8% ATK. The path of flame.",
             cost=10, stats=dict(atk_pct=0.08)),
        dict(id="A1", name="Bloodlust", desc="+12% lifesteal on basic attacks.",
             cost=20, stats=dict(), passive="p_lifesteal"),
        dict(id="A2", name="Overdrive", desc="+18% ATK. Capstone of carnage.",
             cost=40, stats=dict(atk_pct=0.18), req="A1"),
        dict(id="B1", name="Iron Body", desc="+20% max HP.",
             cost=20, stats=dict(hp_pct=0.20)),
        dict(id="B2", name="Last Stand", desc="+35% ATK below 35% HP.",
             cost=40, stats=dict(), passive="p_adrenaline", req="B1"),
    ],
    # --- Hunt: crit / single-target nuke ---
    "hunt": [
        dict(id="root", name="Sharp Eye", desc="+6% crit chance.",
             cost=10, stats=dict(crit=0.06)),
        dict(id="A1", name="Executioner", desc="Crits deal +25% damage.",
             cost=20, stats=dict(crit_dmg=0.25)),
        dict(id="A2", name="Death Mark", desc="+12% crit, +10% ATK.",
             cost=40, stats=dict(crit=0.12, atk_pct=0.10), req="A1"),
        dict(id="B1", name="Fleet Step", desc="+15% move speed.",
             cost=20, stats=dict(), passive="p_swift"),
        dict(id="B2", name="Keen Mind", desc="+10% crit chance.",
             cost=40, stats=dict(crit=0.10), req="B1"),
    ],
    # --- Erudition: AoE magic / energy ---
    "erudition": [
        dict(id="root", name="Arcane Flow", desc="+10% energy, +5% ATK.",
             cost=10, stats=dict(energy_pct=0.10, atk_pct=0.05), passive="p_energy"),
        dict(id="A1", name="Detonate", desc="+15% ATK.",
             cost=20, stats=dict(atk_pct=0.15)),
        dict(id="A2", name="Cataclysm", desc="+25% ATK, +10% energy, +8% crit.",
             cost=40, stats=dict(atk_pct=0.25, energy_pct=0.10, crit=0.08), req="A1"),
        dict(id="B1", name="Mana Well", desc="+20% max MP/energy.",
             cost=20, stats=dict(energy_pct=0.20)),
        dict(id="B2", name="Overflow", desc="Skills cost 15% less energy.",
             cost=40, stats=dict(skill_cost_mult=0.85), req="B1"),
    ],
    # --- Harmony: support / buffs ---
    "harmony": [
        dict(id="root", name="Inspiring", desc="+10% ATK to the party aura.",
             cost=10, stats=dict(atk_pct=0.10)),
        dict(id="A1", name="Mending", desc="Regen 2% HP/sec out of combat.",
             cost=20, stats=dict(), passive="p_regen"),
        dict(id="A2", name="Sanctuary", desc="+25% max HP.",
             cost=40, stats=dict(hp_pct=0.25), req="A1"),
        dict(id="B1", name="Haste", desc="+15% move speed.",
             cost=20, stats=dict(), passive="p_swift"),
        dict(id="B2", name="Resonance", desc="+15% ATK, +10% energy.",
             cost=40, stats=dict(atk_pct=0.15, energy_pct=0.10), req="B1"),
    ],
    # --- Nihility: debuffs / DoT ---
    "nihility": [
        dict(id="root", name="Corruption", desc="+10% ATK.",
             cost=10, stats=dict(atk_pct=0.10)),
        dict(id="A1", name="Wither", desc="+15% ATK, +6% crit.",
             cost=20, stats=dict(atk_pct=0.15, crit=0.06)),
        dict(id="A2", name="Plaguebringer", desc="+25% ATK.",
             cost=40, stats=dict(atk_pct=0.25), req="A1"),
        dict(id="B1", name="Bramble", desc="Reflect 20% melee damage.",
             cost=20, stats=dict(), passive="p_thorns"),
        dict(id="B2", name="Soul Drain", desc="+15% ATK, lifesteal.",
             cost=40, stats=dict(atk_pct=0.15), passive="p_lifesteal", req="B1"),
    ],
    # --- Preservation: tank / shields ---
    "preservation": [
        dict(id="root", name="Fortify", desc="+15% max HP, +10% DEF.",
             cost=10, stats=dict(hp_pct=0.15, def_pct=0.10)),
        dict(id="A1", name="Bulwark", desc="+25% max HP.",
             cost=20, stats=dict(hp_pct=0.25)),
        dict(id="A2", name="Unbreakable", desc="+30% HP, +15% DEF.",
             cost=40, stats=dict(hp_pct=0.30, def_pct=0.15), req="A1"),
        dict(id="B1", name="Guardian", desc="Shield when HP is low.",
             cost=20, stats=dict(), passive="p_shield_low"),
        dict(id="B2", name="Aegis", desc="+20% HP, +10% DEF, thorns.",
             cost=40, stats=dict(hp_pct=0.20, def_pct=0.10), passive="p_thorns", req="B1"),
    ],
    # --- Abundance: healing / sustain ---
    "abundance": [
        dict(id="root", name="Vitality", desc="+15% max HP.",
             cost=10, stats=dict(hp_pct=0.15)),
        dict(id="A1", name="Grace", desc="+10% ATK, +25% healing.",
             cost=20, stats=dict(atk_pct=0.10), passive="p_heal_amp"),
        dict(id="A2", name="Miracle", desc="+30% max HP.",
             cost=40, stats=dict(hp_pct=0.30), req="A1"),
        dict(id="B1", name="Flow", desc="+15% energy gain.",
             cost=20, stats=dict(), passive="p_energy"),
        dict(id="B2", name="Bounty", desc="+15% HP, +15% energy, +10% ATK.",
             cost=40, stats=dict(hp_pct=0.15, energy_pct=0.15, atk_pct=0.10), req="B1"),
    ],
}

# Default tree (any role without a specific tree) — generic offensive/defensive.
EVO_TREE_DEFAULT = [
    dict(id="root", name="Awakening", desc="+8% ATK.",
         cost=10, stats=dict(atk_pct=0.08)),
    dict(id="A1", name="Power", desc="+15% ATK.", cost=20, stats=dict(atk_pct=0.15)),
    dict(id="A2", name="Might", desc="+25% ATK.", cost=40, stats=dict(atk_pct=0.25), req="A1"),
    dict(id="B1", name="Vitality", desc="+20% HP.", cost=20, stats=dict(hp_pct=0.20)),
    dict(id="B2", name="Fortitude", desc="+30% HP.", cost=40, stats=dict(hp_pct=0.30), req="B1"),
]


def hero_evo_tree(hero_def):
    """Return the evolution tree (list of node dicts) for a hero by its role."""
    role = hero_def.get("role", "destruction")
    return EVO_TREE.get(role, EVO_TREE_DEFAULT)


# Tier/branch layout for rendering. Each node has a (col, row) position.
# root=(1,0), A1=(0,1), A2=(0,2), B1=(2,1), B2=(2,2)
EVO_NODE_POS = {
    "root": (1, 0), "A1": (0, 1), "A2": (0, 2), "B1": (2, 1), "B2": (2, 2),
}
EVO_LINKS = [("root", "A1"), ("A1", "A2"), ("root", "B1"), ("B1", "B2")]


def evo_node_prereq_met(node, unlocked_ids):
    """A node is unlockable if its req (if any) is already unlocked."""
    req = node.get("req")
    if not req:
        return True
    return req in unlocked_ids
