"""Tuning constants + small pure helpers (damage chart, energy, toughness,
evolve, ascension, starting state, gacha pity, asset dir).

Mechanically split from _legacy_data.py — every table/function body copied
verbatim; only the file location changed.
"""

__all__ = [
    "ASSET_DIR", "CHART", "RESIST", "WEAKNESS_FOR", "element_mult",
    "BASE_CRIT_CHANCE", "COMBO_BONUS_PER", "COMBO_MAX",
    "COMBO_MILESTONE_SKILL", "COMBO_MILESTONE_ULT", "DEFEND_MITIGATION",
    "AA_RANGE", "AA_CD", "NG_PLUS_LEVEL_BONUS", "ADVENTURE_WAVE_INTERVAL",
    "ADVENTURE_BOSS_TIME", "ADVENTURE_STAGE_LEVEL_STEP",
    "ADVENTURE_STAGE_TIME_LIMIT", "ENERGY_MAX", "ENERGY_START",
    "ENERGY_COST_MULT", "ENERGY_GAIN_BASIC", "ENERGY_GAIN_DEAL",
    "ENERGY_REGEN_PCT", "skill_energy_cost", "TOUGHNESS_BREAK_MULT",
    "TOUGHNESS_BREAK_DAMAGE", "TOUGHNESS_RECOVER_FRAC", "STAT_GROWTH",
    "MAX_LEVEL", "xp_to_next", "MAX_EVOLVE", "EVOLVE_COST", "EVOLVE_BONUS",
    "EVOLVE_TITLES", "EVOLVE_COLORS", "MAX_ASCENSION", "ASCENSION_BONUS",
    "STARTING_GEMS", "STARTING_GOLD", "STARTING_TEAM", "STARTING_OWNED",
    "STARTING_INVENTORY", "GACHA_DUPE_GEM_REFUND", "GACHA_PITY_HARD",
    "GACHA_PITY_SOFT", "GACHA_SR_GUARANTEE_EVERY",
]

import os

# Repo root = parent of src/ = two levels up from this file (src/data/tuning.py).
# Assets live at <repo-root>/assets regardless of where this module sits, so the
# path is repo-root-relative (not __file__-relative) to stay correct after the
# move into src/data/ without a symlink.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSET_DIR = os.path.join(_REPO_ROOT, "assets")

# ---------------------------------------------------------------------------
# Elements and damage chart (attacker -> defender multiplier)
# ---------------------------------------------------------------------------

# Fire > Wind > Earth(no). Fire beats Wind, Wind beats Water, Water beats Fire.
# Light and Dark are mutually strong against each other.
CHART = {
    ("fire", "wind"): 1.5,
    ("wind", "water"): 1.5,
    ("water", "fire"): 1.5,
    ("light", "dark"): 1.5,
    ("dark", "light"): 1.5,
}
# Resistance chart (attacker weaker vs that element)
RESIST = {
    ("fire", "water"): 0.75,
    ("water", "wind"): 0.75,
    ("wind", "fire"): 0.75,
}

def element_mult(atk_el, def_el):
    m = CHART.get((atk_el, def_el), 1.0)
    if m == 1.0:
        m = RESIST.get((atk_el, def_el), 1.0)
    return m

# Inverse of CHART: the element an enemy of element X is weak to (fire->water,
# water->wind, wind->fire, light->dark, dark->light). Used to derive a
# champion-enemy's weakness from its element.
WEAKNESS_FOR = {de: atk for (atk, de), m in CHART.items() if m > 1.0}

# ---------------------------------------------------------------------------
# Status effects
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Combat tuning
# ---------------------------------------------------------------------------
BASE_CRIT_CHANCE = 0.08      # base chance any hit can crit
COMBO_BONUS_PER = 0.04       # +4% damage per combo step
COMBO_MAX = 10
# combo climax milestones: at 5 the next skill is empowered (wider AoE / a 2nd
# projectile); at 10 the next ult is empowered (a free debuff on every enemy
# hit). The ult milestone (10) coincides with COMBO_MAX so reaching max combo
# also arms the empowered ult.
COMBO_MILESTONE_SKILL = 5
COMBO_MILESTONE_ULT = 10
DEFEND_MITIGATION = 0.45     # defending reduces incoming damage by this fraction
# LoL-style auto-attack (Task B3): RMB on an enemy sets the AA target; the hero
# auto-attacks at the AA cooldown while in range, or walks toward it when out.
# AA_CD is the documented cd (matches the 0.32s atk_cd set in _do_attack); the
# actual cd timer reuses wc.atk_cd so the AA + the manual J attack share a cd.
AA_RANGE = 120                # max world px between hero and AA target (in range)
AA_CD = 0.32                  # auto-attack cooldown (seconds)

# ---------------------------------------------------------------------------
# Aetheric Cycle (NG+) — per-cycle enemy level bonus applied on top of the
# base cell_level when the player has Ascended the World. Each cycle adds this
# flat amount to every enemy so a replayed world stays challenging while the
# player's heroes/equipment carry over.
# ---------------------------------------------------------------------------
NG_PLUS_LEVEL_BONUS = 8

# ---------------------------------------------------------------------------
# Adventure mode (Task D1) — a wave-survival mode distinct from the open world.
# A 10-min survival per stage; enemies spawn from the arena edges every
# ADVENTURE_WAVE_INTERVAL seconds (count + level scale with the stage level +
# elapsed time); a boss spawns at the ADVENTURE_BOSS_TIME mark (5 min) and
# defeating it clears the stage (advance the stage ladder, +5 enemy levels, full
# heal); a party wipe ends the run. ADVENTURE_STAGE_LEVEL_STEP is the per-stage
# enemy-level increment so deeper stages hit harder.
# ---------------------------------------------------------------------------
ADVENTURE_WAVE_INTERVAL = 25      # seconds between wave spawns
ADVENTURE_BOSS_TIME = 300         # seconds into the stage when the boss spawns (5 min)
ADVENTURE_STAGE_LEVEL_STEP = 5     # per-stage enemy-level increment
ADVENTURE_STAGE_TIME_LIMIT = 600  # 10-min survival per stage (cosmetic HUD reference)

# ---------------------------------------------------------------------------
# HSR-style Energy (replaces MP as the per-hero action resource)
#   - Basic attack is free and *generates* energy.
#   - Skills cost energy (cost * ENERGY_COST_MULT).
#   - Ultimates cost the full bar (ENERGY_MAX) and are gamechanging.
#   - Energy is gained by basic attacks and using skills.
# Tuned so a hero can use a skill most turns and charges its ultimate in
# roughly 2-3 rounds of active combat.
# ---------------------------------------------------------------------------
ENERGY_MAX = 120
ENERGY_START = 90
ENERGY_COST_MULT = 6         # skill["cost"] * this = energy cost (non-ult)
ENERGY_GAIN_BASIC = 25       # using a basic attack
ENERGY_GAIN_DEAL = 8         # dealing damage with a skill
ENERGY_REGEN_PCT = 0.08   # passive energy regen: 8% of max per second out of
                          # combat (~9.6/s at max 120 -> full bar in ~12s out of
                          # combat, ~4.8/s in combat). Skills recover + mana
                          # increases without needing to land a hit. Tuned up
                          # from 0.04 (v1) so the regen is felt (the user
                          # reported "mana doesn't increase" even with the v1
                          # 4%/s rate; 8%/s is visibly recovering).

def skill_energy_cost(skill):
    """Energy cost of a skill: ultimates cost the full bar, else cost*mult."""
    if skill["type"] == "ultimate":
        return ENERGY_MAX
    return skill["cost"] * ENERGY_COST_MULT

# ---------------------------------------------------------------------------
# HSR-style Toughness / Weakness Break
#   Every combatant has a toughness bar. Hits shave it (weakness-element hits
#   shave much more). At 0 the target is Broken: it is delayed (skips its next
#   turn), takes +50% damage, and suffers a one-time break damage burst. The
#   attacker gains a chunk of energy. Toughness slowly mends each round, so
#   you must focus weakness hits to break — and you can re-break after mending.
# ---------------------------------------------------------------------------
TOUGHNESS_BREAK_MULT = 1.5        # +50% damage vs broken targets
TOUGHNESS_BREAK_DAMAGE = 0.15      # one-time bonus damage on break = frac of max_hp
# HSR-accurate: toughness does NOT mend on its own. Only a broken enemy recovers
# (to full, the round after it was broken). So focused fire reliably breaks.
TOUGHNESS_RECOVER_FRAC = 0.0       # non-broken toughness does not mend

GACHA_PITY_HARD = 60      # guaranteed SSR after this many pulls without one
GACHA_PITY_SOFT = 40      # SSR chance starts ramping up here
GACHA_SR_GUARANTEE_EVERY = 10   # every Nth pull is at least SR
# Coin-back: dupes of a maxed hero refund a few gems (softens the sting).
GACHA_DUPE_GEM_REFUND = 10

# ---------------------------------------------------------------------------
# Ascension / Limit Break
#   Duplicates convert into ascension stars; each star boosts stats.
# ---------------------------------------------------------------------------
MAX_ASCENSION = 5
ASCENSION_BONUS = {0: 1.0, 1: 1.08, 2: 1.16, 3: 1.25, 4: 1.35, 5: 1.50}

# ---------------------------------------------------------------------------
# Evolve (soul-shard ascension)
#   Beyond MAX_ASCENSION, shards evolve a hero into higher tiers. Each evolve
#   tier is a big stat jump + a flair color used in the world HUD.
#   Evolve costs are in soul shards; earned from bosses/elite kills.
# ---------------------------------------------------------------------------
MAX_EVOLVE = 5
EVOLVE_COST = {1: 20, 2: 40, 3: 70, 4: 120, 5: 200}      # shards per evolve tier
EVOLVE_BONUS = {0: 1.0, 1: 1.20, 2: 1.45, 3: 1.75, 4: 2.10, 5: 2.50}
EVOLVE_TITLES = {0: "Hero", 1: "Awakened", 2: "Ascendant",
                 3: "Transcendent", 4: "Mythic", 5: "Divine"}
EVOLVE_COLORS = {0: (220, 220, 235), 1: (120, 220, 255), 2: (160, 255, 180),
                 3: (220, 180, 255), 4: (255, 200, 120), 5: (255, 120, 200)}

# ---------------------------------------------------------------------------
# Starting state
# ---------------------------------------------------------------------------
STARTING_GEMS = 300
STARTING_GOLD = 200
# A balanced starter team covering four elements so the player can engage the
# weakness-break system from the start: Ahri (wind), Lux (light), Darius (fire),
# Ashe (water) - a 4-champion open-world party.
STARTING_TEAM = ["Ahri", "Lux", "Darius", "Ashe"]
STARTING_OWNED = ["Ahri", "Lux", "Darius", "Ashe", "Garen", "Jinx"]
STARTING_INVENTORY = {"hp_potion": 3, "mp_potion": 2}

# Level curve: xp needed to reach next level
def xp_to_next(level):
    return 40 + (level - 1) * 30

# Stat growth per level (fraction of base)
STAT_GROWTH = dict(hp=0.12, atk=0.10, defn=0.10, spd=0.04, mp=0.08)

# Max level
MAX_LEVEL = 60
