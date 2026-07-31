"""NPCs + dialogue, story quest chain + derived lookups.

Mechanically split from _legacy_data.py — bodies copied verbatim.
"""

__all__ = [
    "STORY_QUESTS", "STORY_QUEST_BY_ID", "STORY_QUEST_ORDER",
    "STORY_BIOME_QUEST", "STORY_FINAL_QUEST", "NPCS",
]

# ---------------------------------------------------------------------------
# NPCs + dialogue (Task E1) — one NPC per biome, standing in the village
# (world_scene spawns the NPC at the village's npc_spawn from gen_map). Walk up
# + press F to talk: a dialogue text box overlays the world (the world keeps
# simulating behind it — the dialogue is a UI overlay, NOT a pause). Each NPC
# reveals a piece of the world's story + the biome's boss quest (the quest_id
# references the STORY_QUESTS Task E2 will wire; for E1 it is a placeholder the
# NPC stores so E2 can read it off the NPC when the player accepts the quest).
# Each line is <=80 chars so it fits the dialogue box without wrapping.
# ---------------------------------------------------------------------------
NPCS = {
    "plains": {
        "name": "Sona",
        "quest_id": "demacia_quest",
        "dialogue": [
            "Welcome. Demacia's light once held the plains at peace.",
            "Then Sylas broke the mages' chains and turned on his kin.",
            "He rallies the broken to burn every banner of the crown.",
            "Stop him, and I will sing you into my shard-vault.",
        ],
    },
    "forest": {
        "name": "Irelia",
        "quest_id": "noxus_quest",
        "dialogue": [
            "Quiet. The Noxian warbands camp where the old grove fell.",
            "Swain commands them - three ravens, one will, no mercy.",
            "Each village he takes spreads the black standard a league further.",
            "Cut his march short, and Ionia's green may yet return.",
        ],
    },
    "cave": {
        "name": "Ashe",
        "quest_id": "freljord_quest",
        "dialogue": [
            "Mind the cold. The glaciers used to sing, once.",
            "Lissandra sleeps in the deep gallery, dreaming of ice.",
            "Her breath froze the river solid, then the keepers.",
            "Melt her heart, and the Freljord will breathe again.",
        ],
    },
    "castle": {
        "name": "Viego",
        "quest_id": "shadow_isles_quest",
        "dialogue": [
            "Halt. The citadel is no place for the living now.",
            "Mordekaiser claimed the throne the day the king fell.",
            "His iron guard holds the banner no one dares to raise.",
            "Break his helm, and I will name you the rightful heir.",
        ],
    },
    "void": {
        "name": "Kaisa",
        "quest_id": "void_quest",
        "dialogue": [
            "You came. Few do. Fewer leave with their name intact.",
            "Baron Nashor waits where the world's edge frays.",
            "It was a god-beast once - the rifts were its last mercy.",
            "End it, and the Cycle may turn at last. Or break.",
        ],
    },
}

# ---------------------------------------------------------------------------
# Story quest chain - the main quest: 5 faction-boss quests + 1 final-boss
# quest, chained demacia -> noxus -> freljord -> shadow_isles -> void ->
# baron. Each quest's `giver` is the biome whose NPC offers it (matches
# NPCS[biome]["quest_id"]); `objective` is the LoL villain boss it asks the
# player to defeat; `reward` is the payout on completion (gems + shards);
# `lore` is a one-line faction-conflict beat. The chain order is the list
# order: a quest is "available" when the previous quest in the list is
# "complete" (the first quest, demacia_quest, is available from the start).
# The boss cell for a biome (column 9 of that row) is SEALED until the
# biome's quest is "active" (accepted via the NPC dialogue - see
# world_scene._advance_dialogue); the final boss (baron at 9,4) is sealed
# until all 5 faction-boss quests are complete (the chain). The boss-defeat
# handler (world_scene._on_enemy_death) marks the faction-boss quest
# "complete" + the next quest becomes available.
# ---------------------------------------------------------------------------
STORY_QUESTS = [
    {"id": "demacia_quest", "name": "The Unshackled", "giver": "plains",
     "objective": "Defeat Sylas in the plains (row 0, east edge).",
     "reward": {"gems": 50, "shards": 5},
     "lore": "Demacia's chains bred its own monster. Break the unshackled."},
    {"id": "noxus_quest", "name": "The Noxian March", "giver": "forest",
     "objective": "Defeat Swain where the old grove fell (row 1, east edge).",
     "reward": {"gems": 80, "shards": 8},
     "lore": "Each village he takes spreads the black standard. Cut his march."},
    {"id": "freljord_quest", "name": "The Ice Witch", "giver": "cave",
     "objective": "Defeat Lissandra in the deep gallery (row 2, east edge).",
     "reward": {"gems": 120, "shards": 12},
     "lore": "Her breath froze the river solid. Melt her heart."},
    {"id": "shadow_isles_quest", "name": "The Iron Revenant", "giver": "castle",
     "objective": "Defeat Mordekaiser on the fallen throne (row 3, east edge).",
     "reward": {"gems": 160, "shards": 16},
     "lore": "His iron guard holds the banner no one dares to raise. Break his helm."},
    {"id": "void_quest", "name": "The Riftbreaker", "giver": "void",
     "objective": "Defeat Viego at the world's edge (row 4, east edge).",
     "reward": {"gems": 200, "shards": 20},
     "lore": "He was a king once. The Ruination was his last mercy. End him."},
    {"id": "baron", "name": "Baron Nashor", "giver": "void",
     "objective": "Defeat Baron Nashor at the world's end (9,4).",
     "reward": {"gems": 400, "shards": 40},
     "lore": "End the god-beast, and the Cycle may turn at last. Or break."},
]

# Fast lookups derived from STORY_QUESTS so callers don't re-derive on every
# _load_map / boss-defeat. STORY_QUEST_BY_ID is the dict {id -> quest};
# STORY_QUEST_ORDER is the chain order (the list of ids, demacia -> baron)
# so the "next quest" is the one at index+1. STORY_BIOME_QUEST maps a biome
# (the giver) to its faction-boss quest id (the 5 faction-boss quests only;
# the final baron quest shares the void giver but is gated on the chain, not
# on the void NPC). The final-boss quest id is exported as STORY_FINAL_QUEST
# so the boss-defeat handler can detect it without a magic string.
STORY_QUEST_BY_ID = {q["id"]: q for q in STORY_QUESTS}
STORY_QUEST_ORDER = [q["id"] for q in STORY_QUESTS]
STORY_BIOME_QUEST = {q["giver"]: q["id"]
                     for q in STORY_QUESTS
                     if q["id"] in {v["quest_id"] for v in NPCS.values()}}
STORY_FINAL_QUEST = "baron"
