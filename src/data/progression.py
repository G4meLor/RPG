"""Achievements, daily quests, lore fragments, landmark lore.

Mechanically split from _legacy_data.py — bodies copied verbatim.
"""

__all__ = [
    "ACHIEVEMENTS", "DAILY_QUESTS", "LORE_FRAGMENTS", "LANDMARK_LORE",
]


# ---------------------------------------------------------------------------
# Achievements
#   id -> {name, desc, reward_gems, check(player)}
# ---------------------------------------------------------------------------
ACHIEVEMENTS = {
    "first_blood": dict(name="First Blood", desc="Defeat your first enemy.",
                        reward_gems=50,
                        check=lambda p: p.stats.get("enemies_defeated", 0) >= 1),
    "veteran":     dict(name="Veteran", desc="Defeat 50 enemies.",
                        reward_gems=150,
                        check=lambda p: p.stats.get("enemies_defeated", 0) >= 50),
    "legend":      dict(name="Legend", desc="Defeat 300 enemies.",
                        reward_gems=400,
                        check=lambda p: p.stats.get("enemies_defeated", 0) >= 300),
    "slayer":      dict(name="Slayer", desc="Defeat 200 enemies.",
                        reward_gems=120,
                        check=lambda p: p.stats.get("enemies_defeated", 0) >= 200),
    "first_ssr":   dict(name="Lucky Star", desc="Obtain an SSR hero.",
                        reward_gems=80,
                        check=lambda p: p._has_ssr()),
    "collector":   dict(name="Collector", desc="Own 10 different heroes.",
                        reward_gems=200,
                        check=lambda p: len(p.owned) >= 10),
    "completionist": dict(name="Explorer", desc="Discover 30 maps in the open world.",
                          reward_gems=500,
                          check=lambda p: len(p.ow_discovered) >= 30),
    "summoner":    dict(name="Summoner", desc="Pull 100 times total.",
                        reward_gems=150,
                        check=lambda p: p.stats.get("total_pulls", 0) >= 100),
    "boss_slayer": dict(name="Boss Slayer", desc="Defeat 5 bosses in the open world.",
                        reward_gems=300,
                        check=lambda p: p.stats.get("bosses_defeated", 0) >= 5),
    "evolved":     dict(name="Awakened", desc="Evolve a hero to a higher tier.",
                        reward_gems=200,
                        check=lambda p: any(rec.get("evolve", 0) > 0 for rec in p.owned.values())),
    "rich":        dict(name="Treasure Hoard", desc="Earn 5000 gold total.",
                        reward_gems=120,
                        check=lambda p: p.stats.get("gold_earned", 0) >= 5000),
    "dodge_master": dict(name="Untouchable", desc="Land 50 perfect dodges.",
                         reward_gems=200,
                         check=lambda p: p.stats.get("perfect_dodges", 0) >= 50),
    "combo_king":   dict(name="Combo King", desc="Reach a 10-hit combo.",
                         reward_gems=150,
                         check=lambda p: p.stats.get("max_combo", 0) >= 10),
    "alchemist":    dict(name="Alchemist", desc="Trigger 100 elemental reactions.",
                         reward_gems=200,
                         check=lambda p: p.stats.get("reactions_triggered", 0) >= 100),
    "ultimate":     dict(name="Unleashed", desc="Use your ultimate 50 times.",
                         reward_gems=150,
                         check=lambda p: p.stats.get("ults_used", 0) >= 50),
}

# ---------------------------------------------------------------------------
# Daily quests (reset each calendar day)
#   id -> {name, desc, goal, reward_gems, track}
#   track(player, kind, n) is applied by game events.
# ---------------------------------------------------------------------------
DAILY_QUESTS = {
    "win_battles":    dict(name="Slay 20 Foes", desc="Defeat 20 enemies in the world today.",
                           goal=20, reward_gems=90),
    "defeat_enemies": dict(name="Defeat 10 Foes", desc="Defeat 10 enemies today.",
                           goal=10, reward_gems=40),
    "summon":         dict(name="Summon Once", desc="Summon at least once.",
                          goal=1, reward_gems=40),
    "explore":        dict(name="Explore 3 Maps", desc="Discover 3 new maps today.",
                           goal=3, reward_gems=60),
    "open_chests":    dict(name="Treasure Hunter", desc="Open 3 treasure chests today.",
                          goal=3, reward_gems=50),
}

# ---------------------------------------------------------------------------
# Lore fragments — dropped by hidden rift mini-dungeons (task D4) on wave
# clear. A few atmospheric one-liners so the rift reads as a story beat, not
# just a loot pinata. Picked deterministically per-cell (seeded from
# cell_seed + 4242 in world_scene._clear_rift) so the same rift always drops
# the same fragment — a stable piece of worldbuilding the player can collect.
# ---------------------------------------------------------------------------
LORE_FRAGMENTS = [
    "The rift hums with a forgotten song.",
    "A shard of the old world slips through the crack.",
    "Something watched from the other side, then was gone.",
    "The void remembers a name it will not speak.",
    "Light bends here, as if afraid to land.",
    "A whisper: 'They walked here before the dark.'",
    "The seal thins. The deep stirs.",
    "Time pools around the rift like water in a sinkhole.",
    "A page of the world's first map, torn and glowing.",
    "The rift closes behind a breath you did not take.",
]

# ---------------------------------------------------------------------------
# Landmark lore (Task C3) — one atmospheric one-liner per biome, shown as a
# floating text the first time the player enters a cell with a landmark
# (world_scene tracks visited landmarks per cell in ow_landmarks_seen). The
# kind by biome: plains=statue, forest=ruin, cave=shrine, castle=obelisk,
# void=rift_anchor. Picked by biome so the same landmark always shows the same
# lore (a stable piece of worldbuilding the player collects by exploring).
# ---------------------------------------------------------------------------
LANDMARK_LORE = {
    "plains": "The statue of the First Wanderer, weathered but watchful.",
    "forest": "Moss-grown ruins of a watchtower lost to the Whispering Woods.",
    "cave":   "A crystal shrine where the cavern-keepers once prayed.",
    "castle": "The obelisk marks the citadel's fallen banner.",
    "void":   "The rift-anchor hums, holding the dark at bay - for now.",
}
