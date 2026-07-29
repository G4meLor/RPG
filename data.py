"""
Aetheria Gacha - Game Data
Static definitions for heroes, enemies, skills, stages, gacha pool, items,
equipment, ascension, shop and tuning constants.
"""
import os

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

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

# ---------------------------------------------------------------------------
# Elemental reactions — a bonus effect when a hit of one element lands shortly
# after a hit of a *different* element (Genshin-style). Rewards swapping the
# active hero mid-fight (the 4-hero party). The reaction fires on the SECOND
# element's hit; both elements must be different and within the reaction window.
#   key: frozenset({el_a, el_b}) -> (name, bonus_dmg_frac, effect, color)
#   effect: "aoe" = bonus damage to nearby enemies, "stun" = brief enemy stun,
#           "burst" = a big particle burst on the target
# ---------------------------------------------------------------------------
REACTIONS = {
    frozenset({"fire", "water"}):  ("Steam",    0.30, "aoe",   (220, 230, 240)),
    frozenset({"fire", "wind"}):   ("Spread",   0.25, "burst", (255, 180, 90)),
    frozenset({"water", "wind"}):  ("Freeze",   0.20, "stun",  (180, 220, 255)),
    frozenset({"light", "dark"}):  ("Rupture",  0.35, "burst", (255, 200, 220)),
}
REACTION_WINDOW = 3.0   # seconds after a hit during which a different element triggers

# Wet effect: when the current map's weather is rain, the reaction window is
# extended (x1.5) and water hits are amplified (x1.2) / fire hits are dampened
# (x0.8). Gated to the reaction window ONLY — the wet effect extends the
# window, not the Freeze stun duration (see world_scene._on_enemy_hit).
WET_EFFECT = {"water": 1.2, "fire": 0.8, "reaction_window": 1.5}

def reaction_for(el_a, el_b):
    """Return the reaction dict for two elements, or None if no reaction."""
    if el_a == el_b:
        return None
    return REACTIONS.get(frozenset({el_a, el_b}))

# ---------------------------------------------------------------------------
# Element colors (used by UI for badges, glows, text)
# ---------------------------------------------------------------------------
ELEMENT_COLORS = {
    "fire":  ( (232, 86, 60),  (255,168, 90), (120, 24, 18) ),
    "water": ( ( 64,150,230),  (140,220,255), ( 18, 48, 96) ),
    "wind":  ( ( 96,200,140),  (180,240,190), ( 24, 84, 56) ),
    "light": ( (245,210, 90),  (255,245,200), (140,110, 30) ),
    "dark":  ( (150, 90,200),  (210,170,240), ( 56, 28, 84) ),
}

# pixel-art scale: each logical pixel is rendered as a PIXEL×PIXEL block so the
# art reads as chunky pixel-art at higher density than Stardew (Stardew tiles are
# 16x16; a 256px sprite at PIXEL=5 -> ~51 logical pixels, 3x Stardew). Palette is
# locked per element (base/light/shadow/outline/accent) so gradients dither
# instead of smoothing.
PIXEL = 5
PIXEL_PALETTE = {
    "fire":   {"base": (220, 90, 40), "light": (255, 170, 90), "shadow": (130, 40, 20),
               "outline": (60, 20, 10), "accent": (255, 230, 140)},
    "water":  {"base": (40, 120, 210), "light": (120, 200, 255), "shadow": (20, 60, 120),
               "outline": (10, 30, 60), "accent": (200, 240, 255)},
    "wind":   {"base": (120, 220, 160), "light": (200, 255, 220), "shadow": (60, 130, 90),
               "outline": (20, 50, 40), "accent": (240, 255, 200)},
    "light":  {"base": (250, 220, 90), "light": (255, 250, 200), "shadow": (180, 140, 40),
               "outline": (80, 60, 20), "accent": (255, 255, 240)},
    "dark":   {"base": (110, 50, 150), "light": (180, 110, 220), "shadow": (60, 20, 90),
               "outline": (30, 10, 50), "accent": (200, 160, 255)},
}
# Colorblind-friendly element palette (deuteranopia-safe). Single RGB triples
# (main color only) chosen to stay distinct from each other AND from HP_RED
# (220,70,80), GOLD/crit-yellow (255,210,90), and HP_GREEN/heal-green
# (90,210,110). Separation relies on hue + brightness, not red/green alone:
#   fire  = bright orange   (warm, low blue; distinct from pinkish HP_RED)
#   water = sky blue        (high blue; no clash)
#   wind  = chartreuse      (yellow-green; distinct from GOLD and HP_GREEN)
#   light = pale cream      (very high brightness; distinct from GOLD)
#   dark  = purple         (high blue + red; no clash)
# REACTIONS keep their own fixed rcol tuples and are NOT routed through this.
COLORBLIND_PALETTES = {
    "fire":  (235,  90,  30),
    "water": ( 40, 140, 220),
    "wind":  (200, 230,  60),
    "light": (255, 235, 150),
    "dark":  (140,  50, 190),
}

RARITY_COLORS = {
    "R":   (140, 150, 165),
    "SR":  (220, 150, 60),
    "SSR": (220, 80, 150),
}

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
# LoL-style ability slots
#   Each hero has 4 active abilities mapped to Q / W / E / R plus a passive.
#   - passive: always-on (handled by the world combat loop, no key)
#   - Q (skill 0), W (skill 1), E (skill 2): active skills with cooldowns
#   - R: the ultimate (costs the full energy bar)
#   HERO_ABILITIES maps a hero id -> [q, w, e] skill ids (from its skill list,
#   skipping basic_attack). The ultimate stays on hero["ultimate"].
#   HERO_PASSIVES maps a hero id -> a passive id (see PASSIVES_DB).
# ---------------------------------------------------------------------------

# passive definitions — always-on combat modifiers, keyed by id.
#   kind values handled in world_scene combat:
#     lifesteal   - heal a fraction of damage dealt by basic attacks
#     thorns      - reflect a fraction of melee damage taken
#     crit_up     - +bonus crit chance
#     energy_gen  - +bonus energy on dealing damage
#     swift       - +move speed
#     regen       - slow HP regen out of combat
#     adrenaline  - +ATK when HP is low
#     shield_when_low - gain a shield when HP drops below 30%
#     heal_amp   - healing skills heal a fraction more
PASSIVES_DB = {
    "p_lifesteal": dict(name="Vampiric Touch", desc="Heal for 12% of basic-attack damage.",
                        kind="lifesteal", val=0.12),
    "p_thorns":    dict(name="Bramble Mail", desc="Reflect 20% of melee damage taken.",
                        kind="thorns", val=0.20),
    "p_crit":      dict(name="Keen Eye", desc="+10% critical strike chance.",
                        kind="crit_up", val=0.10),
    "p_energy":    dict(name="Flow State", desc="+50% energy gain on hit.",
                        kind="energy_gen", val=0.5),
    "p_swift":     dict(name="Fleet Footed", desc="+15% movement speed.",
                        kind="swift", val=0.15),
    "p_regen":     dict(name="Mending Aura", desc="Regen 2% HP/sec out of combat.",
                        kind="regen", val=0.02),
    "p_adrenaline":dict(name="Last Stand", desc="+30% ATK while below 35% HP.",
                        kind="adrenaline", val=0.30),
    "p_shield_low":dict(name="Guardian Spirit", desc="Gain a shield at low HP.",
                        kind="shield_when_low", val=0.25),
    "p_heal_amp":   dict(name="Mercy", desc="Healing skills heal 25% more.",
                        kind="heal_amp", val=0.25),
    # --- per-hero signature passives (C6) — layered on top of HERO_PASSIVES.
    # Each of the 25 heroes gets ONE signature id (see HERO_SIGNATURE). Heroes
    # sharing a kind reuse the same id; the per-hero flavor is the name/desc.
    # The signature is ADDITIONAL to the shared base passive — handlers in
    # world_entities/world_scene check the signature in addition to
    # self.hero.passive, not instead of it. Dispatch is a dict-lookup per hook
    # point (kind -> handler), NOT an if/elif chain.
    #   kind values handled in world_entities/world_scene:
    #     revive_once    - revive at val HP on death, once per combat (reset in _build_party)
    #     stacking_atk   - +val ATK per kill (stacking), decays out of combat
    #     shield_on_hit  - gain a shield when damaged (after the hit)
    #     low_hp_frenzy  - +val ATK & +20% SPD below 30% HP
    #     cleave         - basic attacks splash to enemies within 60px of the primary target
    "s_aria_frenzy":   dict(name="Dawn's Wrath",        desc="+25% ATK & SPD below 30% HP.",            kind="low_hp_frenzy",  val=0.25),
    "s_kael_cleave":   dict(name="Sweeping Strike",     desc="Basic attacks splash to nearby enemies.",  kind="cleave",         val=0.5),
    "s_luna_revive":   dict(name="Dark Pact",           desc="Revive once at 40% HP on death.",          kind="revive_once",    val=0.4),
    "s_zephyr_stack":  dict(name="Momentum",           desc="+5% ATK per kill (stacking).",             kind="stacking_atk",   val=0.05),
    "s_mira_shield":   dict(name="Tide Ward",          desc="Gain a shield when damaged.",              kind="shield_on_hit",  val=0.15),
}


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

# Build the Q/W/E ability list for a hero from its skill list (skip basic_attack,
# take up to 3). The 4th slot (R) is the hero ultimate, handled separately.
def hero_abilities(hero_def):
    sks = [s for s in hero_def["skills"] if s != "basic_attack"]
    # pad to 3 with None so the HUD always has 3 skill slots
    while len(sks) < 3:
        sks.append(None)
    return sks[:3]


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
    # Boss ultimates (enemies only)
    "hellfire":     dict(name="Hellfire",      element="fire", type="aoe_magic", power=1.8, cost=0,
                        desc="Dragon's breath scorches all. Burns."),
    "abyssal_wave": dict(name="Abyssal Wave",  element="dark", type="aoe_magic", power=1.7, cost=0,
                        desc="Demon King's wave of darkness."),
    "frost_cataclysm": dict(name="Frost Cataclysm", element="water", type="aoe_magic", power=1.9, cost=0,
                        desc="The Frost Titan's cataclysm freezes all."),
    "storm_of_embers": dict(name="Storm of Embers", element="fire", type="aoe_magic", power=2.0, cost=0,
                        desc="The Ember Tyrant rains fire."),
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

# ---------------------------------------------------------------------------
# Hero definitions — the 170 LoL champions, baked from champions.py by
# build_champions.py. The combat fields (id/name/title/element/rarity/role/
# stats/skills/ultimate) come from the bake; the cross-references below
# (HERO_PASSIVES / HERO_SIGNATURE / ULTIMATE_VARIANTS / HERO_LORE /
# _HERO_SKILL_TEXT / GACHA_POOL / STARTING_TEAM / WEAPON_STYLE_KEY) are
# auto-derived from champions.py too. Stats: hp, atk, defn, spd, mp.
# ---------------------------------------------------------------------------
import champions as _CH
HEROES_DB = [
    dict(id=c["id"], name=c["name"], title=c["title"], element=c["element"],
         rarity=c["rarity"], role=c["role"], stats=c["stats"],
         skills=c["skills"], ultimate=c["ultimate"])
    for c in _CH.CHAMPIONS_DB
]

# Quick lookup
HERO_BY_ID = {h["id"]: h for h in HEROES_DB}

# Per-hero passive assignment (one each, flavored to their role/element).
# destruction -> lifesteal/adrenaline, hunt -> crit, erudition -> energy,
# harmony -> regen, nihility -> thorns, preservation -> shield, abundance -> regen.
# Auto-derived from champions.py (PASSIVE_BY_ROLE) + flagship overrides.
_PASSIVE_BY_ROLE = {
    "destruction": "p_adrenaline", "hunt": "p_crit", "erudition": "p_energy",
    "harmony": "p_regen", "nihility": "p_thorns", "preservation": "p_shield_low",
    "abundance": "p_regen",
}
# Flagship per-champ passive overrides (champ key -> passive id).
_PASSIVE_OVERRIDE = {
    "Garen": "p_adrenaline", "Darius": "p_adrenaline", "LeeSin": "p_lifesteal",
    "Yasuo": "p_crit", "Zed": "p_crit", "Jinx": "p_crit",
    "Ahri": "p_energy", "Lux": "p_energy", "Syndra": "p_energy",
    "Thresh": "p_thorns", "Mordekaiser": "p_thorns",
    "Braum": "p_shield_low", "Leona": "p_shield_low",
    "Soraka": "p_regen", "Sona": "p_regen", "Janna": "p_swift",
}
HERO_PASSIVES = {h["id"]: _PASSIVE_OVERRIDE.get(h["id"]) or _PASSIVE_BY_ROLE.get(h["role"], "p_energy")
                 for h in HEROES_DB}

def hero_passive(hero_id):
    pid = HERO_PASSIVES.get(hero_id)
    if not pid:
        return None
    return PASSIVES_DB.get(pid)

# Per-hero signature passives (C6) — a UNIQUE signature per hero, layered on
# top of the shared HERO_PASSIVES. Each hero maps to one of the 5 signature
# passive ids (heroes sharing a kind reuse the same id). Auto-derived by role
# + flagship overrides so the 170 champions get a signature without 170 hand
# entries.
_SIGNATURE_BY_ROLE = {
    "destruction": "s_kael_cleave", "hunt": "s_zephyr_stack",
    "erudition": "s_zephyr_stack", "harmony": "s_mira_shield",
    "nihility": "s_luna_revive", "preservation": "s_mira_shield",
    "abundance": "s_luna_revive",
}
# Flagship per-champ signature overrides.
_SIGNATURE_OVERRIDE = {
    "Garen": "s_aria_frenzy", "Darius": "s_aria_frenzy", "Aatrox": "s_luna_revive",
    "Yasuo": "s_zephyr_stack", "Zed": "s_zephyr_stack", "Jinx": "s_zephyr_stack",
    "Ahri": "s_aria_frenzy", "Lux": "s_mira_shield", "Syndra": "s_zephyr_stack",
    "Thresh": "s_luna_revive", "Mordekaiser": "s_luna_revive",
    "LeeSin": "s_kael_cleave", "Jhin": "s_zephyr_stack",
    "Ashe": "s_zephyr_stack", "Lissandra": "s_luna_revive",
    "Braum": "s_mira_shield", "Soraka": "s_mira_shield",
    "Ezreal": "s_zephyr_stack", "Teemo": "s_luna_revive",
}
HERO_SIGNATURE = {h["id"]: _SIGNATURE_OVERRIDE.get(h["id"]) or _SIGNATURE_BY_ROLE.get(h["role"], "s_zephyr_stack")
                  for h in HEROES_DB}

def hero_signature(hero_id):
    """Return the signature passive dict for a hero, or None. The signature is
    ADDITIONAL to the shared base passive (hero_passive) — the world loop
    checks both."""
    pid = HERO_SIGNATURE.get(hero_id)
    return PASSIVES_DB.get(pid) if pid else None

# ---------------------------------------------------------------------------
# Per-hero ultimate variants — auto-derived by role + flagship overrides.
#   Each champion gets an ultimate name ("{Champ}'s {UltSkill}") + one
#   secondary effect on top of the base ultimate. Effect kinds handled at
#   runtime (world_scene._do_ultimate): self_heal / party_shield / knockback /
#   energy_refund / atk_buff_self. Heal ults deal 0 damage so their variant
#   never picks self_heal (the role map avoids that for abundance).
# ---------------------------------------------------------------------------
ULTIMATE_VARIANTS = {}
_ULT_BY_ROLE = {'destruction': ('atk_buff_self', 0.22, '+22% ATK for 4s.'), 'hunt': ('self_heal', 0.15, 'Heal self for 15% of damage dealt.'), 'erudition': ('knockback', 250, 'Hurl enemies back.'), 'harmony': ('energy_refund', 0.25, 'Refund 25% of max energy.'), 'nihility': ('self_heal', 0.18, 'Drain life; heal self for 18% of damage dealt.'), 'preservation': ('party_shield', 0.22, 'Shield the party for 3s.'), 'abundance': ('energy_refund', 0.28, 'Refund 28% of max energy.')}
_ULT_OVERRIDE = {'Garen': ('self_heal', 0.15, 'Demacian justice; heal self for 15% of damage dealt.'), 'Darius': ('atk_buff_self', 0.25, 'Noxian guillotine; +25% ATK for 4s.'), 'Ahri': ('self_heal', 0.15, 'Spirit rush; heal self for 15% of damage dealt.'), 'Lux': ('party_shield', 0.2, 'Final Spark; shield the party for 3s.'), 'Yasuo': ('knockback', 260, 'Last Breath; hurl enemies back.'), 'Jinx': ('knockback', 250, 'Super Mega Death Rocket; scatter enemies.'), 'Thresh': ('self_heal', 0.2, 'The Box; drain life for 20% of damage dealt.'), 'LeeSin': ('knockback', 260, "Dragon's Rage; hurl enemies back."), 'Jhin': ('atk_buff_self', 0.25, 'Curtain Call; +25% ATK for 4s.'), 'Ashe': ('knockback', 240, 'Enchanted Crystal Arrow; scatter enemies.'), 'Braum': ('party_shield', 0.28, 'Glacial Fissure; shield the party for 3s.'), 'Soraka': ('energy_refund', 0.3, 'Wish; refund 30% of max energy.')}
for _h in HEROES_DB:
    _eff, _pot, _desc = _ULT_OVERRIDE.get(_h["id"]) or _ULT_BY_ROLE.get(_h["role"], ("atk_buff_self", 0.20, "+20% ATK for 4s."))
    _un = SKILLS_DB.get(_h["ultimate"], {}).get("name", _h["ultimate"].replace("_", " ").title())
    ULTIMATE_VARIANTS[_h['id']] = dict(name=f"{_h['name']}'s {_un}", extra_effect=_eff, potency=_pot, desc=_desc)
del _h, _eff, _pot, _desc, _un

# ---------------------------------------------------------------------------
# Hero lore: bio (<=120 chars), quote (<=80 chars), personality (one word).
# Auto-derived from champions.py (the LoL lore field). Pure display data
# for the codex tooltip + hero-detail screen.
# ---------------------------------------------------------------------------
HERO_LORE = {
    'Aatrox': {"bio": 'Once honored defenders of Shurima against the Void, Aatrox and his brethren would eventually become an even greater…', "quote": 'Now, with stolen flesh, he walks Runeterra in a brutal approximation of his…', "personality": 'steadfast'},
    'Ahri': {"bio": "Innately connected to the magic of the spirit realm, Ahri is a fox-like vastaya who can manipulate her prey's emotions…", "quote": 'Once a powerful yet wayward predator, Ahri is now traveling the world in search…', "personality": 'cold'},
    'Akali': {"bio": 'Abandoning the Kinkou Order and her title of the Fist of Shadow, Akali now strikes alone, ready to be the deadly weapon…', "quote": 'Akali may strike in silence, but her message will be heard loud and clear: fear…', "personality": 'cold'},
    'Akshan': {"bio": 'Raising an eyebrow in the face of danger, Akshan fights evil with dashing charisma, righteous vengeance, and a…', "quote": '”', "personality": 'cold'},
    'Alistar': {"bio": 'Always a mighty warrior with a fearsome reputation, Alistar seeks revenge for the death of his clan at the hands of the…', "quote": 'Now, free of the chains of his former masters, he fights in the name of the…', "personality": 'gentle'},
    'Ambessa': {"bio": "All who know the name Medarda respect and fear the family's leader, Ambessa.", "quote": 'Embracing the merciless ways of the Wolf, Ambessa will do whatever it takes to…', "personality": 'cold'},
    'Amumu': {"bio": 'Legend claims that Amumu is a lonely and melancholy soul from ancient Shurima, roaming the world in search of a friend.', "quote": 'Amumu has inspired myths, songs, and folklore told and retold for generations…', "personality": 'gentle'},
    'Anivia': {"bio": 'Anivia is a benevolent winged spirit who endures endless cycles of life, death, and rebirth to protect the Freljord.', "quote": 'She fights with every ounce of her being, knowing that through her sacrifice,…', "personality": 'gentle'},
    'Annie': {"bio": 'Dangerous, yet disarmingly precocious, Annie is a child mage with immense pyromantic power.', "quote": 'Lost in the perpetual innocence of childhood, Annie wanders the dark forests,…', "personality": 'gentle'},
    'Aphelios': {"bio": "Emerging from moonlight's shadow with weapons drawn, Aphelios kills the enemies of his faith in brooding…", "quote": 'For as long as the moon shines overhead, Aphelios will never be alone', "personality": 'focused'},
    'Ashe': {"bio": 'Iceborn warmother of the Avarosan tribe, Ashe commands the most populous horde in the north.', "quote": "With her people's belief that she is the mythological hero Avarosa…", "personality": 'gentle'},
    'AurelionSol': {"bio": 'Aurelion Sol once graced the vast emptiness of the cosmos with celestial wonders of his own devising.', "quote": 'Desiring a return to his star-forging ways, Aurelion Sol will drag the very…', "personality": 'curious'},
    'Aurora': {"bio": 'From the moment she was born, Aurora navigated life with a unique ability to move between the spirit and material…', "quote": 'Witnessing his desperation, Aurora resolved to find a way to help her feral…', "personality": 'cold'},
    'Azir': {"bio": 'Azir was a mortal emperor of Shurima in a far distant age, a proud man who stood at the cusp of immortality.', "quote": 'With his buried city risen from the sand, Azir seeks to restore Shurima to its…', "personality": 'curious'},
    'Bard': {"bio": 'A traveler from beyond the stars, Bard is an agent of serendipity who fights to maintain a balance where life can…', "quote": 'in his own odd way', "personality": 'gentle'},
    'Belveth': {"bio": "A nightmarish empress created from the raw material of an entire devoured city, Bel'Veth is the end of Runeterra…", "quote": 'Yet her wants could never be sated by only one world as she turns her hungry…', "personality": 'restless'},
    'Blitzcrank': {"bio": 'Blitzcrank is an enormous, near-indestructible automaton from Zaun, originally built to dispose of hazardous waste.', "quote": 'Blitzcrank selflessly uses his strength and durability to protect others,…', "personality": 'gentle'},
    'Brand': {"bio": 'Once a tribesman of the icy Freljord named Kegan Rodhe, the creature known as Brand is a lesson in the temptation of…', "quote": 'His soul burned away, his body a vessel of living flame, Brand now roams…', "personality": 'gentle'},
    'Braum': {"bio": 'Blessed with massive biceps and an even bigger heart, Braum is a beloved hero of the Freljord.', "quote": 'Bearing an enchanted vault door as his shield, Braum roams the frozen north…', "personality": 'gentle'},
    'Briar': {"bio": "A failed experiment by the Black Rose, Briar's uncontrollable bloodlust required a special pillory to focus her…", "quote": "Now she's controlled by no one following only her hunger for knowledge and…", "personality": 'cold'},
    'Caitlyn': {"bio": "Renowned as its finest peacekeeper, Caitlyn Kiramman is also Piltover's best shot at ridding the city of its elusive…", "quote": "Even though she carries a one-of-a-kind hextech rifle, Caitlyn's most powerful…", "personality": 'focused'},
    'Camille': {"bio": 'Weaponized to operate outside the boundaries of the law, Camille is the Principal Intelligencer of Clan Ferros—an…', "quote": "With a mind as sharp as the blades she bears, Camille's pursuit of superiority…", "personality": 'cold'},
    'Cassiopeia': {"bio": 'Cassiopeia is a deadly creature bent on manipulating others to her sinister will.', "quote": 'Cunning and agile, Cassiopeia now slithers under the veil of night, petrifying…', "personality": 'curious'},
    'Chogath': {"bio": "From the moment Cho'Gath first emerged into the harsh light of Runeterra's sun, the beast was driven by the most pure…", "quote": "When growing larger does not suit the Void-spawn's needs, it vomits out the…", "personality": 'curious'},
    'Corki': {"bio": 'The yordle pilot Corki loves two things above all others: flying, and his glamorous mustache...', "quote": 'Calm under fire, Corki patrols the skies around his adopted home, and has never…', "personality": 'curious'},
    'Darius': {"bio": "There is no greater symbol of Noxian might than Darius, the nation's most feared and battle-hardened commander.", "quote": 'Knowing that he never doubts his cause is just, and never hesitates once his…', "personality": 'steadfast'},
    'Diana': {"bio": 'Bearing her crescent moonblade, Diana fights as a warrior of the Lunari—a faith all but quashed in the lands around…', "quote": "Imbued with the essence of an Aspect from beyond Targon's towering summit,…", "personality": 'cold'},
    'DrMundo': {"bio": 'Utterly mad, tragically homicidal, and horrifyingly purple, Dr.', "quote": 'With a full cabinet of medicines and zero medical knowledge, he now makes…', "personality": 'steadfast'},
    'Draven': {"bio": 'In Noxus, warriors known as Reckoners face one another in arenas where blood is spilled and strength tested—but none…', "quote": 'Addicted to the spectacle of his own brash perfection, Draven has sworn to…', "personality": 'focused'},
    'Ekko': {"bio": 'A prodigy from the rough streets of Zaun, Ekko is able to manipulate time to twist any situation to his advantage.', "quote": "Though Ekko revels in this freedom, when there's a threat to those he cares…", "personality": 'cold'},
    'Elise': {"bio": 'Elise is a deadly predator who dwells in a shuttered, lightless palace, deep within the oldest city of Noxus.', "quote": 'To maintain her eternal youth, Elise now prefers to feed upon the naive and the…', "personality": 'cold'},
    'Evelynn': {"bio": 'Within the dark seams of Runeterra, the demon Evelynn searches for her next victim.', "quote": 'To the rest of Runeterra, they are ghoulish tales of lust gone awry and…', "personality": 'cold'},
    'Ezreal': {"bio": 'A dashing adventurer, unknowingly gifted in the magical arts, Ezreal raids long-lost catacombs, tangles with ancient…', "quote": 'Probably everywhere', "personality": 'curious'},
    'Fiddlesticks': {"bio": 'Something has awoken in Runeterra. Something ancient. Something terrible.', "quote": 'Beware the sounding of the crow, or the whispering of the shape that appears…', "personality": 'gentle'},
    'Fiora': {"bio": 'The most feared duelist in all Valoran, Fiora is as renowned for her brusque manner and cunning mind as she is for the…', "quote": "House Laurent's reputation was sundered, but Fiora bends her every effort to…", "personality": 'cold'},
    'Fizz': {"bio": 'Fizz is an amphibious yordle, who dwells among the reefs surrounding Bilgewater.', "quote": 'Often mistaken for some manner of capricious ocean spirit, he seems able to…', "personality": 'cold'},
    'Galio': {"bio": 'Outside the gleaming city of Demacia, the stone colossus Galio keeps vigilant watch.', "quote": 'But his triumphs are always bittersweet, for the magic he destroys is also his…', "personality": 'curious'},
    'Gangplank': {"bio": 'As unpredictable as he is brutal, the dethroned reaver king Gangplank is feared far and wide.', "quote": 'Gangplank would see Bilgewater bathed in blood once more before letting someone…', "personality": 'stoic'},
    'Garen': {"bio": 'A proud and noble warrior, Garen fights as one of the Dauntless Vanguard.', "quote": 'Clad in magic-resistant armor and bearing a mighty broadsword, Garen stands…', "personality": 'steadfast'},
    'Gnar': {"bio": "Gnar is a primeval yordle whose playful antics can erupt into a toddler's outrage in an instant, transforming him into…", "quote": 'Delighted by danger, Gnar flings whatever he can at his enemies, be it his…', "personality": 'steadfast'},
    'Gragas': {"bio": "Equal parts jolly and imposing, Gragas is a massive, rowdy brewmaster who's always on the lookout for new ways to raise…", "quote": 'Any appearance from Gragas must surely foreshadow merriment and destruction in…', "personality": 'curious'},
    'Graves': {"bio": 'Malcolm Graves is a renowned mercenary, gambler, and thief—a wanted man in every city and empire he has visited.', "quote": 'In recent years, he has reconciled a troubled partnership with Twisted Fate,…', "personality": 'focused'},
    'Gwen': {"bio": 'A former doll transformed and brought to life by magic, Gwen wields the very tools that once created her.', "quote": 'So much is new to her, but Gwen remains joyfully determined to fight for the…', "personality": 'cold'},
    'Hecarim': {"bio": 'Hecarim is a spectral fusion of man and beast, cursed to ride down the souls of the living for all eternity.', "quote": 'Now, whenever the Black Mist reaches out across Runeterra, he leads their…', "personality": 'steadfast'},
    'Heimerdinger': {"bio": 'The eccentric Professor Cecil B.', "quote": 'Nonetheless, this brilliant scientist and teacher will always remain dedicated…', "personality": 'gentle'},
    'Hwei': {"bio": "Hwei is a brooding painter who creates brilliant art in order to confront Ionia's criminals and comfort their victims.", "quote": 'With paintbrush and palette, Hwei shapes endless possibilities as he draws ever…', "personality": 'gentle'},
    'Illaoi': {"bio": "Illaoi's powerful physique is dwarfed only by her indomitable faith.", "quote": 'All who challenge the “Truth Bearer of Nagakabouros” soon discover Illaoi never…', "personality": 'steadfast'},
    'Irelia': {"bio": 'The Noxian occupation of Ionia produced many heroes, none more unlikely than young Irelia of Navori.', "quote": 'After proving herself as a fighter, she was thrust into the role of resistance…', "personality": 'cold'},
    'Ivern': {"bio": "Ivern Bramblefoot, known to many as the Green Father, is a peculiar half man, half tree who roams Runeterra's forests,…", "quote": 'Ivern wanders the wilderness, imparting strange wisdom to any he meets,…', "personality": 'gentle'},
    'Janna': {"bio": "Armed with the power of Runeterra's gales, Janna is a mysterious, elemental wind spirit who protects the dispossessed…", "quote": "No one knows where or when she will appear, but more often than not, she's come…", "personality": 'gentle'},
    'JarvanIV': {"bio": 'Prince Jarvan, scion of the Lightshield dynasty, is heir apparent to the throne of Demacia.', "quote": 'Jarvan inspires his troops with his fearsome courage and selfless…', "personality": 'steadfast'},
    'Jax': {"bio": 'Unmatched in both his skill with unique armaments and his biting sarcasm, Jax is the last known weapons master of…', "quote": 'As magic now rises in the world, this slumbering threat stirs once more, and…', "personality": 'cold'},
    'Jayce': {"bio": 'Jayce Talis is a brilliant inventor who, along with his friend Viktor, made the first great discoveries in the field of…', "quote": 'Because of this, Jayce has begun to see the ways in which his invention has…', "personality": 'focused'},
    'Jhin': {"bio": 'Jhin is a meticulous criminal psychopath who believes murder is art.', "quote": 'He gains a cruel pleasure from putting on his gruesome theater, making him the…', "personality": 'curious'},
    'Jinx': {"bio": "An unhinged and impulsive criminal from the undercity, Jinx is haunted by the consequences of her past—but that doesn't…", "quote": 'She uses her arsenal of DIY weapons to devastating effect, unleashing torrents…', "personality": 'focused'},
    'KSante': {"bio": "Defiant and courageous, K'Sante battles colossal beasts and ruthless Ascended to protect his home of Nazumah, a coveted…", "quote": 'Only then can he avoid falling prey to his own pride and find the wisdom he…', "personality": 'steadfast'},
    'Kaisa': {"bio": "Claimed by the Void when she was only a child, Kai'Sa managed to survive through sheer tenacity and strength of will.", "quote": 'Having entered into an uneasy symbiosis with a living Void carapace, the time…', "personality": 'curious'},
    'Kalista': {"bio": 'A specter of wrath and retribution, Kalista is the undying spirit of vengeance, an armored nightmare summoned from the…', "quote": "Those who become the focus of Kalista's wrath should make their final peace,…", "personality": 'focused'},
    'Karma': {"bio": 'No mortal exemplifies the spiritual traditions of Ionia more than Karma.', "quote": 'She has done her best to guide her people in recent times of crisis, though she…', "personality": 'gentle'},
    'Karthus': {"bio": 'The harbinger of oblivion, Karthus is an undying spirit whose haunting songs are a prelude to the horror of his…', "quote": 'When Karthus emerges from the Shadow Isles, it is to bring the joy of death to…', "personality": 'curious'},
    'Kassadin': {"bio": 'Cutting a burning swath through the darkest places of the world, Kassadin knows his days are numbered.', "quote": 'Finally, Kassadin set out for the wastelands of Icathia, ready to face any…', "personality": 'cold'},
    'Katarina': {"bio": 'Decisive in judgment and lethal in combat, Katarina is a Noxian assassin of the highest caliber.', "quote": 'Her fiery ambition has driven her to pursue heavily-guarded targets, even at…', "personality": 'cold'},
    'Kayle': {"bio": "Born to a Targonian Aspect at the height of the Rune Wars, Kayle honored her mother's legacy by fighting for justice on…", "quote": 'Still, legends are told of her punishing the unjust with her fiery swords, and…', "personality": 'curious'},
    'Kayn': {"bio": 'A peerless practitioner of lethal shadow magic, Shieda Kayn battles to achieve his true destiny—to one day lead the…', "quote": 'or the malevolent blade consumes him completely, paving the way for the…', "personality": 'cold'},
    'Kennen': {"bio": 'More than just the lightning-quick enforcer of Ionian balance, Kennen is the only yordle member of the Kinkou.', "quote": 'Alongside his master Shen, Kennen patrols the spirit realm, employing…', "personality": 'curious'},
    'Khazix': {"bio": "The Void grows, and the Void adapts—in none of its myriad spawn are these truths more apparent than Kha'Zix.", "quote": 'Now, the creature plans out its hunts, and even utilizes the visceral terror it…', "personality": 'cold'},
    'Kindred': {"bio": 'Separate, but never parted, Kindred represents the twin essences of death.', "quote": "Though interpretations of Kindred's nature vary across Runeterra, every mortal…", "personality": 'focused'},
    'Kled': {"bio": 'A warrior as fearless as he is ornery, the yordle Kled embodies the furious bravado of Noxus.', "quote": 'Though the truth of the matter is often questionable, one part of his legend is…', "personality": 'steadfast'},
    'KogMaw': {"bio": "Belched forth from a rotting Void incursion deep in the wastelands of Icathia, Kog'Maw is an inquisitive yet putrid…", "quote": "Though not inherently evil, Kog'Maw's beguiling naiveté is dangerous, as it…", "personality": 'curious'},
    'Leblanc': {"bio": 'Mysterious even to other members of the Black Rose cabal, LeBlanc is but one of many names for a pale woman who has…', "quote": "Always plotting just out of sight, LeBlanc's true motives are as inscrutable as…", "personality": 'cold'},
    'LeeSin': {"bio": "A master of Ionia's ancient martial arts, Lee Sin is a principled fighter who channels the essence of the dragon spirit…", "quote": 'Enemies who underestimate his meditative demeanor will endure his fabled…', "personality": 'cold'},
    'Leona': {"bio": 'Imbued with the fire of the sun, Leona is a holy warrior of the Solari who defends Mount Targon with her Zenith Blade…', "quote": 'Armored in gold and bearing a terrible burden of ancient knowledge, Leona…', "personality": 'gentle'},
    'Lillia': {"bio": "Intensely shy, the fae fawn Lillia skittishly wanders Ionia's forests.", "quote": 'Eep!', "personality": 'curious'},
    'Lissandra': {"bio": "Lissandra's magic twists the pure power of ice into something dark and terrible.", "quote": "'' The truth is much more sinister: Lissandra is a corruptor of nature who…", "personality": 'curious'},
    'Lucian': {"bio": 'Lucian, a Sentinel of Light, is a grim hunter of wraiths and specters, pursuing them relentlessly and annihilating them…', "quote": 'Merciless and single-minded, Lucian will stop at nothing to protect the living…', "personality": 'cold'},
    'Lulu': {"bio": 'The yordle mage Lulu is known for conjuring dreamlike illusions and fanciful creatures as she roams Runeterra with her…', "quote": 'While others might consider her magic at best unnatural, and at worst…', "personality": 'gentle'},
    'Lux': {"bio": 'Luxanna Crownguard hails from Demacia, an insular realm where magical abilities are viewed with fear and suspicion.', "quote": "Nonetheless, Lux's optimism and resilience have led her to embrace her unique…", "personality": 'gentle'},
    'Malphite': {"bio": 'A massive creature of living stone, Malphite struggles to impose blessed order on a chaotic world.', "quote": 'The only survivor of the destruction that followed, Malphite now endures…', "personality": 'curious'},
    'Malzahar': {"bio": 'A zealous seer dedicated to the unification of all life, Malzahar truly believes the newly emergent Void to be the path…', "quote": 'Malzahar now sees himself as a shepherd, empowered to bring others into the…', "personality": 'cold'},
    'Maokai': {"bio": 'Maokai is a rageful, towering treant who fights the unnatural horrors of the Shadow Isles.', "quote": 'Once a peaceful nature spirit, Maokai now furiously battles to banish the…', "personality": 'gentle'},
    'MasterYi': {"bio": 'Master Yi has tempered his body and sharpened his mind, so that thought and action have become almost as one.', "quote": 'As one of the last living practitioners of the Ionian art of Wuju, Yi has…', "personality": 'cold'},
    'Mel': {"bio": 'Mel Medarda is the presumed heir of the Medarda family, once one of the most powerful in Noxus.', "quote": 'With newly awakened magical abilities, she sailed home in search of answers and…', "personality": 'gentle'},
    'Milio': {"bio": 'Milio is a warmhearted boy from Ixtal who has, despite his young age, mastered the fire axiom and discovered something…', "quote": 'Having traveled through the Ixtal jungles to the capital of Ixaocan, Milio now…', "personality": 'gentle'},
    'MissFortune': {"bio": 'A Bilgewater captain famed for her looks but feared for her ruthlessness, Sarah Fortune paints a stark figure among the…', "quote": 'Those who underestimate her will face a beguiling and unpredictable opponent……', "personality": 'curious'},
    'MonkeyKing': {"bio": 'Wukong is a vastayan trickster who uses his strength, agility, and intelligence to confuse his opponents and gain the…', "quote": 'Armed with an enchanted staff, Wukong seeks to prevent Ionia from falling to…', "personality": 'steadfast'},
    'Mordekaiser': {"bio": 'Twice slain and thrice born, Mordekaiser is a brutal warlord from a foregone epoch who uses his necromantic sorcery to…', "quote": 'Few now remain who remember his earlier conquests, or know the true extent of…', "personality": 'curious'},
    'Morgana': {"bio": 'Conflicted between her celestial and mortal natures, Morgana bound her wings to embrace humanity, and inflicts her pain…', "quote": 'More than anything else, Morgana truly believes that even the banished and…', "personality": 'gentle'},
    'Naafiri': {"bio": 'Across the sands of Shurima, a chorus of howls rings out.', "quote": 'Among them, one pack stands above all, for they are driven not only by canine…', "personality": 'cold'},
    'Nami': {"bio": 'A headstrong young vastaya of the seas, Nami was the first of the Marai tribe to leave the waves and venture onto dry…', "quote": 'Amidst the chaos of this new age, Nami faces an uncertain future with grit and…', "personality": 'gentle'},
    'Nasus': {"bio": 'Nasus is an imposing, jackal-headed Ascended being from ancient Shurima, a heroic figure regarded as a demigod by the…', "quote": 'Now that the ancient city of Shurima has risen once more, he has returned,…', "personality": 'steadfast'},
    'Nautilus': {"bio": 'A lonely legend as old as the first piers sunk in Bilgewater, the armored goliath known as Nautilus roams the dark…', "quote": 'It is said he comes for those who forget to pay the “Bilgewater tithe”, pulling…', "personality": 'gentle'},
    'Neeko': {"bio": 'Hailing from a long lost tribe of vastaya, Neeko can blend into any crowd by borrowing the appearances of others, even…', "quote": 'No one is ever sure where or who Neeko might be, but those who intend to do her…', "personality": 'gentle'},
    'Nidalee': {"bio": 'Raised in the deepest jungle, Nidalee is a master tracker who can shapeshift into a ferocious cougar at will.', "quote": 'She cripples her quarry before pouncing on them in feline form the lucky few…', "personality": 'cold'},
    'Nilah': {"bio": "Nilah is an ascetic warrior from a distant land, seeking the world's deadliest, most titanic opponents so that she…", "quote": "Channeling the demon's liquid form into a blade of unparalleled might, she…", "personality": 'cold'},
    'Nocturne': {"bio": 'A demonic amalgamation drawn from the nightmares that haunt every sentient mind, the thing known as Nocturne has become…', "quote": 'After freeing itself from the spirit realm, Nocturne descended upon the waking…', "personality": 'cold'},
    'Nunu': {"bio": 'Once upon a time, there was a boy who wanted to prove he was a hero by slaying a fearsome monster—only to discover that…', "quote": 'If they can save her, maybe they will be heroes after all…', "personality": 'curious'},
    'Olaf': {"bio": 'An unstoppable force of destruction, the axe-wielding Olaf wants nothing but to die in glorious combat.', "quote": "Now a brutal enforcer for the Winter's Claw, he seeks his end in the great wars…", "personality": 'steadfast'},
    'Orianna': {"bio": 'Once a curious girl of flesh and blood, Orianna is now a technological marvel comprised entirely of clockwork.', "quote": 'Accompanied by an extraordinary brass sphere she built for companionship and…', "personality": 'gentle'},
    'Ornn': {"bio": 'Ornn is the Freljordian spirit of forging and craftsmanship.', "quote": 'When other deities especially Volibear walk the earth and meddle in mortal…', "personality": 'steadfast'},
    'Pantheon': {"bio": 'Once an unwilling host to the Aspect of War, Atreus survived when the celestial power within him was slain, refusing to…', "quote": 'Atreus now opposes the divine as Pantheon reborn, his unbreakable will fueling…', "personality": 'cold'},
    'Poppy': {"bio": 'Runeterra has no shortage of valiant champions, but few are as tenacious as Poppy.', "quote": "Until then, she dutifully charges into battle, pushing back the kingdom's…", "personality": 'steadfast'},
    'Pyke': {"bio": 'A renowned harpooner from the slaughter docks of Bilgewater, Pyke should have met his death in the belly of a gigantic…', "quote": 'Now, stalking the dank alleys and backways of his former hometown, he uses his…', "personality": 'cold'},
    'Qiyana': {"bio": 'In the jungle city of Ixaocan, Qiyana plots her own ruthless path to the high seat of the Yun Tal.', "quote": 'With the land itself obeying her every command, Qiyana sees herself as the…', "personality": 'cold'},
    'Quinn': {"bio": 'Quinn is an elite ranger-knight of Demacia, who undertakes dangerous missions deep in enemy territory.', "quote": 'Nimble and acrobatic when required, Quinn takes aim with her crossbow while…', "personality": 'cold'},
    'Rakan': {"bio": 'As mercurial as he is charming, Rakan is an infamous vastayan troublemaker and the greatest battle-dancer in Lhotlan…', "quote": 'Few would suspect this energetic, traveling showman is also partner to the…', "personality": 'gentle'},
    'Rammus': {"bio": 'Idolized by many, dismissed by some, mystifying to all, the curious being Rammus is an enigma.', "quote": 'Whatever the truth may be, Rammus keeps his own counsel and stops for no one as…', "personality": 'steadfast'},
    'RekSai': {"bio": "An apex predator, Rek'Sai is a merciless Void-spawn that tunnels beneath the ground to ambush and devour unsuspecting…", "quote": "All know that once Rek'Sai is seen on the horizon, death from below is all but…", "personality": 'steadfast'},
    'Rell': {"bio": 'The product of brutal experimentation at the hands of the Black Rose, Rell is a defiant, living weapon determined to…', "quote": 'Now branded as a criminal, Rell attacks Noxian soldiers on sight as she…', "personality": 'gentle'},
    'Renata': {"bio": "Renata Glasc rose from the ashes of her childhood home with nothing but her name and her parents' alchemical research.", "quote": 'But everyone comes to her side, eventually', "personality": 'gentle'},
    'Renekton': {"bio": 'Renekton is a terrifying, rage-fueled Ascended being from the scorched deserts of Shurima.', "quote": 'Now free once more, he is utterly consumed with finding and killing his…', "personality": 'steadfast'},
    'Rengar': {"bio": 'Rengar is a ferocious vastayan trophy hunter who lives for the thrill of tracking down and killing dangerous creatures.', "quote": 'Rengar stalks his prey neither for food nor glory, but for the sheer beauty of…', "personality": 'cold'},
    'Riven': {"bio": 'Once a swordmaster in the warhosts of Noxus, Riven is an expatriate in a land she previously tried to conquer.', "quote": 'Having severed all ties to the empire, she now seeks to find her place in a…', "personality": 'cold'},
    'Rumble': {"bio": 'Rumble is a young inventor with a temper.', "quote": "Though others may scoff and sneer at his junkyard creations, Rumble doesn't…", "personality": 'curious'},
    'Ryze': {"bio": 'Widely considered one of the most adept sorcerers on Runeterra, Ryze is an ancient, hard-bitten archmage with an…', "quote": 'He must retrieve these artifacts before they fall into the wrong hands, for…', "personality": 'curious'},
    'Samira': {"bio": 'Samira stares death in the eye with unyielding confidence, seeking thrill wherever she goes.', "quote": 'Wielding black-powder pistols and a custom-engineered blade, Samira thrives in…', "personality": 'cold'},
    'Sejuani': {"bio": "Sejuani is the brutal, unforgiving Iceborn warmother of the Winter's Claw, one of the most feared tribes of the…", "quote": 'Sejuani herself spearheads the most dangerous of these attacks from the saddle…', "personality": 'steadfast'},
    'Senna': {"bio": 'Cursed from childhood to be haunted by the supernatural Black Mist, Senna joined a sacred order known as the Sentinels…', "quote": 'Now wielding darkness along with light, Senna seeks to end the Black Mist by…', "personality": 'gentle'},
    'Seraphine': {"bio": 'Born in Piltover to Zaunite parents, Seraphine can hear the souls of others—the world sings to her, and she sings back.', "quote": "She performs for the sister cities to remind their citizens that they're not…", "personality": 'gentle'},
    'Sett': {"bio": "A leader of Ionia's growing criminal underworld, Sett rose to prominence in the wake of the war with Noxus.", "quote": 'Now, having climbed through the ranks of local combatants, Sett has muscled to…', "personality": 'steadfast'},
    'Shaco': {"bio": 'Crafted long ago as a plaything for a lonely prince, the enchanted marionette Shaco now delights in murder and mayhem.', "quote": 'He uses toys and simple tricks to deadly effect, finding the results of his…', "personality": 'cold'},
    'Shen': {"bio": 'Among the secretive, Ionian warriors known as the Kinkou, Shen serves as their leader, the Eye of Twilight.', "quote": 'Tasked with enforcing the equilibrium between them, Shen wields blades of steel…', "personality": 'steadfast'},
    'Shyvana': {"bio": 'Shyvana is a creature with the magic of a rune shard burning within her heart.', "quote": 'Having saved the life of the crown prince Jarvan IV, Shyvana now serves…', "personality": 'curious'},
    'Singed': {"bio": 'Singed is a brilliant alchemist of dubious morality, whose experiments would turn the stomach of even the most…', "quote": 'His most infamous work is “shimmer”, which enabled the chembarons to turn Zaun…', "personality": 'curious'},
    'Sion': {"bio": 'A war hero from a bygone era, Sion was revered in Noxus for choking the life out of a Demacian king with his bare…', "quote": 'Even so, with crude armor bolted onto rotten flesh, Sion continues to charge…', "personality": 'steadfast'},
    'Sivir': {"bio": 'Sivir is a renowned fortune hunter and mercenary captain who plies her trade in the deserts of Shurima.', "quote": 'With ancient forces stirring the very bones of Shurima, Sivir finds herself…', "personality": 'focused'},
    'Skarner': {"bio": 'The ancient, colossal brackern Skarner is revered in Ixtal as one of the founding members of its ruling caste, the Yun…', "quote": "As more members of the Yun Tal begin questioning Ixtal's self-isolation,…", "personality": 'steadfast'},
    'Smolder': {"bio": 'Hidden amongst the craggy cliffs of the Noxian frontier, under the watchful eyes of his mother, a young dragon is…', "quote": "Though he's still a fledgling, his skills are nothing to sneeze at, easily…", "personality": 'curious'},
    'Sona': {"bio": "Sona is Demacia's foremost virtuoso of the stringed etwahl, speaking only through her graceful chords and vibrant…", "quote": 'Silent to outsiders but somehow understood by close companions, Sona plucks her…', "personality": 'gentle'},
    'Soraka': {"bio": 'A wanderer from the celestial dimensions beyond Mount Targon, Soraka gave up her immortality to protect the mortal…', "quote": "And, for all Soraka has seen of this world's struggles, she still believes the…", "personality": 'gentle'},
    'Swain': {"bio": 'Jericho Swain is the visionary ruler of Noxus, an expansionist nation that reveres only strength.', "quote": 'In a swirl of sacrifice and secrets, the greatest secret of all is that the…', "personality": 'gentle'},
    'Sylas': {"bio": "Raised in one of Demacia's lesser quarters, Sylas of Dregbourne has come to symbolize the darker side of the Great…", "quote": 'Having now broken free, Sylas lives as a hardened revolutionary, using the…', "personality": 'cold'},
    'Syndra': {"bio": 'Syndra is a fearsome Ionian mage with incredible power at her command.', "quote": 'Forming her feelings of betrayal and hurt into dark spheres of energy, Syndra…', "personality": 'curious'},
    'TahmKench': {"bio": 'Known by many names throughout history, the demon Tahm Kench travels the waterways of Runeterra, feeding his insatiable…', "quote": 'His lashing tongue can stun even a heavily armored warrior from a dozen paces,…', "personality": 'gentle'},
    'Taliyah': {"bio": 'Taliyah is a nomadic mage from Shurima, torn between teenage wonder and adult responsibility.', "quote": 'Some have mistaken her compassion for weakness and paid the ultimate price for…', "personality": 'gentle'},
    'Talon': {"bio": 'Talon is the knife in the darkness, a merciless killer able to strike without warning and escape before any alarm is…', "quote": 'Adopted by the notorious Du Couteau family, he now plies his deadly trade at…', "personality": 'cold'},
    'Taric': {"bio": "Taric is the Aspect of the Protector, wielding incredible power as Runeterra's guardian of life, love, and beauty.", "quote": 'Imbued with the might of ancient Targon, the Shield of Valoran now stands ever…', "personality": 'gentle'},
    'Teemo': {"bio": 'Undeterred by even the most dangerous and threatening of obstacles, Teemo scouts the world with boundless enthusiasm…', "quote": 'Though some say the existence of the Scouts is questionable, one thing is for…', "personality": 'curious'},
    'Thresh': {"bio": 'Sadistic and cunning, Thresh is an ambitious and restless specter of the Shadow Isles.', "quote": 'His victims suffer far beyond their brief mortal coil as Thresh wreaks agony…', "personality": 'gentle'},
    'Tristana': {"bio": 'While many other yordles channel their energy into discovery, invention, or just plain mischief-making, Tristana was…', "quote": 'Setting foot in the world for the first time, she took up her trusty cannon…', "personality": 'cold'},
    'Trundle': {"bio": 'Trundle is a hulking and devious troll with a particularly vicious streak, and there is nothing he cannot bludgeon into…', "quote": 'Then, his massive club of True Ice at the ready, he chills his enemies to the…', "personality": 'steadfast'},
    'Tryndamere': {"bio": 'Fueled by unbridled fury and rage, Tryndamere once carved his way through the Freljord, openly challenging the greatest…', "quote": 'His almost inhuman strength and fortitude is legendary, and has delivered him…', "personality": 'cold'},
    'TwistedFate': {"bio": 'Twisted Fate is an infamous cardsharp and swindler who has gambled and charmed his way across much of the known world,…', "quote": 'In every possible way, Twisted Fate always has an ace up his sleeve', "personality": 'curious'},
    'Twitch': {"bio": 'A Zaunite plague rat by birth, but a connoisseur of filth by passion, Twitch is not afraid to get his paws dirty.', "quote": "Always a sneaky sneak, when he's not rooting around in the Sump, he's digging…", "personality": 'cold'},
    'Udyr': {"bio": 'The most powerful spirit walker alive, Udyr communes with all the spirits of the Freljord, whether by empathically…', "quote": 'He seeks balance within, so that his mind does not get lost amidst others, but…', "personality": 'steadfast'},
    'Urgot': {"bio": 'Once a powerful Noxian headsman, Urgot was betrayed by the empire for which he had killed so many.', "quote": 'Raising his victims on the very chains that once enslaved him, he will purge…', "personality": 'steadfast'},
    'Varus': {"bio": 'One of the ancient darkin, Varus was a deadly killer who loved to torment his foes, driving them almost to insanity…', "quote": 'Varus now seeks out those who trapped him, in order to enact his brutal…', "personality": 'curious'},
    'Vayne': {"bio": 'Shauna Vayne is a deadly, remorseless Demacian monster hunter, who has dedicated her life to finding and destroying the…', "quote": 'Armed with a wrist-mounted crossbow and a heart full of vengeance, she is only…', "personality": 'cold'},
    'Veigar': {"bio": 'An enthusiastic master of dark sorcery, Veigar has embraced powers that few mortals dare approach.', "quote": 'Now a stubborn creature with an endless fascination for the mysteries of the…', "personality": 'curious'},
    'Velkoz': {"bio": "It is unclear if Vel'Koz was the first Void-spawn to emerge on Runeterra, but there has certainly never been another to…", "quote": "But Vel'Koz is far from a passive observer, striking back at threats with…", "personality": 'gentle'},
    'Vex': {"bio": 'In the black heart of the Shadow Isles, a lone yordle trudges through the spectral fog, content in its murky misery.', "quote": 'Though she lacks ambition, she is quick to strike down color and happiness,…', "personality": 'curious'},
    'Vi': {"bio": 'Raised on the mean streets of Zaun, Vi is a hotheaded, impulsive, and fearsome woman with very little respect for…', "quote": 'Now working with the Piltover Enforcers to keep the peace instead of breaking…', "personality": 'cold'},
    'Viego': {"bio": 'Once ruler of a long-lost kingdom, Viego perished over a thousand years ago when his attempt to bring his wife back…', "quote": 'Transformed into a powerful, unliving specter tortured by an obsessive longing…', "personality": 'cold'},
    'Viktor': {"bio": 'The fully biomechanical evolution of his former self, Viktor has embraced his Glorious Evolution and become something…', "quote": 'After all, to this master of the arcane, violence is merely a variable…', "personality": 'curious'},
    'Vladimir': {"bio": "A fiend with a thirst for mortal blood, Vladimir has influenced the affairs of Noxus since the empire's earliest days.", "quote": 'In the flamboyant salons of the Noxian aristocracy, this has enabled him to…', "personality": 'curious'},
    'Volibear': {"bio": 'To those who still revere him, the Volibear is the storm made manifest.', "quote": 'Cultivating a deep hatred of civilization and the weakness it brought with it,…', "personality": 'steadfast'},
    'Warwick': {"bio": 'Warwick is a monster who hunts the gray alleys of Zaun.', "quote": 'Warwick is drawn to blood, driven mad by its scent… and none who spill it can…', "personality": 'steadfast'},
    'Xayah': {"bio": 'Deadly and precise, Xayah is a vastayan revolutionary waging a personal war to save her people.', "quote": 'Xayah fights alongside her partner and lover, Rakan, to protect their dwindling…', "personality": 'focused'},
    'Xerath': {"bio": 'Xerath is an Ascended Magus of ancient Shurima, a being of arcane energy writhing in the broken shards of a magical…', "quote": 'Driven insane with power, he now seeks to take what he believes is rightfully…', "personality": 'gentle'},
    'XinZhao': {"bio": 'Xin Zhao is a resolute warrior loyal to the ruling Lightshield dynasty.', "quote": 'Armed with his favored three-talon spear, Xin Zhao now fights for his adopted…', "personality": 'steadfast'},
    'Yasuo': {"bio": 'An Ionian of deep resolve, Yasuo is an agile swordsman who wields the air itself against his enemies.', "quote": "Even after his master's true killer was revealed, Yasuo still could not forgive…", "personality": 'cold'},
    'Yone': {"bio": "In life, he was Yone—half-brother of Yasuo, and renowned student of his village's sword school.", "quote": 'Now, cursed to wear its demonic mask upon his face, Yone tirelessly hunts all…', "personality": 'cold'},
    'Yorick': {"bio": 'The last survivor of a long-forgotten religious order, Yorick is both blessed and cursed with power over the dead.', "quote": "Yorick's monstrous actions belie his noble purpose: to free his home from the…", "personality": 'steadfast'},
    'Yuumi': {"bio": 'A magical cat from Bandle City, Yuumi was once the familiar of a yordle enchantress, Norra.', "quote": 'In the end, however, she always returns to her quest to find her friend', "personality": 'gentle'},
    'Zac': {"bio": "Zac is the product of a toxic spill that ran through a chemtech seam and pooled in an isolated cavern deep in Zaun's…", "quote": 'Despite such humble origins, Zac has grown from primordial ooze into a thinking…', "personality": 'steadfast'},
    'Zed': {"bio": 'Utterly ruthless and without mercy, Zed is the leader of the Order of Shadow, an organization he created with the…', "quote": 'Zed has mastered all of these forbidden techniques to destroy anything he sees…', "personality": 'cold'},
    'Zeri': {"bio": "A headstrong, spirited young woman from Zaun's working-class, Zeri channels her electric magic to charge herself and…", "quote": 'Though her eagerness to help can sometimes backfire, Zeri believes one truth to…', "personality": 'focused'},
    'Ziggs': {"bio": 'With a love of big bombs and short fuses, the yordle Ziggs is an explosive force of nature.', "quote": 'After a wild night on the town, Ziggs took her advice and moved to Zaun, where…', "personality": 'curious'},
    'Zilean': {"bio": "Once a powerful Icathian mage, Zilean became obsessed with the passage of time after witnessing his homeland's…", "quote": 'Having become functionally immortal, Zilean now drifts through the past,…', "personality": 'gentle'},
    'Zoe': {"bio": 'As the embodiment of mischief, imagination, and change, Zoe acts as the cosmic messenger of Targon, heralding major…', "quote": 'An encounter with Zoe can be joyous and life affirming, but it is always more…', "personality": 'gentle'},
    'Zyra': {"bio": 'Born in an ancient, sorcerous catastrophe, Zyra is the wrath of nature given form—an alluring hybrid of plant and…', "quote": 'Though her true purpose has not been revealed, Zyra wanders the world,…', "personality": 'gentle'},
}

# ---------------------------------------------------------------------------
# Enemy definitions
# ---------------------------------------------------------------------------
ENEMIES_DB = {
    # --- LoL jungle mobs (open-world trash) ---
    "Razorbeaks":  dict(name="Razorbeak",    element="wind",   hp=60,  atk=14, defn=6,  spd=8,  xp=20, gold=15,
                        skills=["basic_attack"], weakness="fire", toughness=40),
    "Krugs":       dict(name="Krugs",        element="fire",   hp=80,  atk=18, defn=8,  spd=11, xp=28, gold=22,
                        skills=["basic_attack", "fire_bolt"], weakness="water", toughness=50),
    "MurkWolves":  dict(name="Murk Wolf",    element="wind",   hp=100, atk=22, defn=9,  spd=15, xp=36, gold=30,
                        skills=["basic_attack", "wind_arrow"], weakness="fire", toughness=60),
    "Raptors":     dict(name="Raptor",       element="fire",   hp=70,  atk=20, defn=6,  spd=14, xp=30, gold=24,
                        skills=["basic_attack", "fire_bolt"], weakness="water", toughness=45),
    "Gromp":       dict(name="Gromp",        element="water",  hp=90,  atk=20, defn=10, spd=9,  xp=32, gold=26,
                        skills=["basic_attack", "water_bolt"], weakness="wind", toughness=55),
    "Voidlings":   dict(name="Voidling",     element="dark",   hp=55,  atk=16, defn=5,  spd=16, xp=24, gold=18,
                        skills=["basic_attack", "dark_bolt"], weakness="light", toughness=35),
    "Wraiths":     dict(name="Wraith",       element="dark",   hp=120, atk=28, defn=12, spd=14, xp=55, gold=45,
                        skills=["basic_attack", "dark_bolt", "dark_curse"], weakness="light", toughness=70),
    "CrimsonRaptor": dict(name="Crimson Raptor", element="fire", hp=140, atk=26, defn=14, spd=8,  xp=48, gold=40,
                        skills=["basic_attack", "fire_slash"], weakness="water", toughness=80),
    "VoidHound":   dict(name="Void Hound",   element="dark",   hp=110, atk=24, defn=10, spd=12, xp=40, gold=32,
                        skills=["basic_attack", "dark_bolt"], weakness="light", toughness=65),
    "FallenKnight":dict(name="Fallen Knight",element="light",  hp=160, atk=26, defn=18, spd=10, xp=60, gold=48,
                        skills=["basic_attack", "light_slash"], weakness="dark", toughness=90),
    # --- LoL villain bosses (the open-world arena fights) ---
    "Sylas":       dict(name="Sylas",        element="dark",   hp=340, atk=34, defn=20, spd=12, xp=120, gold=120,
                        skills=["basic_attack", "dark_bolt", "dark_aoe"], weakness="light", toughness=160),
    "Swain":       dict(name="Swain",        element="fire",   hp=380, atk=36, defn=22, spd=11, xp=160, gold=160,
                        skills=["basic_attack", "fire_bolt", "inferno"], weakness="water", toughness=180),
    "Lissandra":   dict(name="Lissandra",    element="water",  hp=440, atk=36, defn=26, spd=10, xp=260, gold=260,
                        skills=["basic_attack", "water_bolt", "frost_nova"], weakness="fire", toughness=200),
    "Mordekaiser": dict(name="Mordekaiser",  element="dark",   hp=520, atk=38, defn=24, spd=13, xp=300, gold=300,
                        skills=["basic_attack", "dark_bolt", "dark_aoe", "dark_curse"], weakness="light", toughness=220),
    "Viego":       dict(name="Viego",        element="dark",   hp=460, atk=40, defn=22, spd=15, xp=280, gold=280,
                        skills=["basic_attack", "dark_bolt", "dark_aoe"], weakness="light", toughness=210),
    "Baron":       dict(name="Baron Nashor", element="dark",   hp=620, atk=42, defn=26, spd=14, xp=360, gold=360,
                        skills=["basic_attack", "fire_bolt", "inferno", "fire_slash"], weakness="light", toughness=260),
}

# ---------------------------------------------------------------------------
# Gacha pool
# ---------------------------------------------------------------------------
GACHA_RATES = {"SSR": 0.06, "SR": 0.34, "R": 0.60}
# Gacha pool — auto-derived from HEROES_DB grouped by rarity. Every champ
# is in exactly one rarity bucket so random.choice never hits an empty pool.
GACHA_POOL = {
    'SSR': ['Ahri', 'Akali', 'Akshan', 'Anivia', 'Aphelios', 'Ashe', 'AurelionSol', 'Azir', 'Bard', 'Brand', 'Camille', 'Cassiopeia', 'Darius', 'Draven', 'Ekko', 'Ezreal', 'Gangplank', 'Garen', 'Gnar', 'Hwei', 'Irelia', 'Ivern', 'Jhin', 'Jinx', 'KSante', 'Kaisa', 'Kalista', 'Katarina', 'Kindred', 'LeeSin', 'Lillia', 'Lissandra', 'Lux', 'Mordekaiser', 'Nilah', 'Ornn', 'Pyke', 'Qiyana', 'Riven', 'Sett', 'Shaco', 'Swain', 'Sylas', 'Syndra', 'Teemo', 'Thresh', 'Veigar', 'Viego', 'Viktor', 'Volibear', 'Yasuo', 'Yone', 'Zed', 'Zoe'],
    'SR': ['Aatrox', 'Ambessa', 'Aurora', 'Belveth', 'Braum', 'Briar', 'Corki', 'Elise', 'Evelynn', 'Fiddlesticks', 'Fiora', 'Fizz', 'Galio', 'Gragas', 'Graves', 'Gwen', 'Hecarim', 'Heimerdinger', 'Illaoi', 'Jayce', 'Karthus', 'Kassadin', 'Kayle', 'Kayn', 'Kennen', 'Khazix', 'Kled', 'KogMaw', 'Leblanc', 'Lucian', 'Lulu', 'Mel', 'Nami', 'Nautilus', 'Nidalee', 'Orianna', 'Poppy', 'Quinn', 'Rakan', 'RekSai', 'Rell', 'Renata', 'Rengar', 'Rumble', 'Ryze', 'Samira', 'Sejuani', 'Senna', 'Shen', 'Singed', 'Sivir', 'Skarner', 'Smolder', 'Taliyah', 'Talon', 'Taric', 'TwistedFate', 'Twitch', 'Urgot', 'Varus', 'Vayne', 'Velkoz', 'Vex', 'Vladimir', 'Xayah', 'Xerath', 'Yorick', 'Zeri', 'Ziggs', 'Zilean', 'Zyra'],
    'R': ['Alistar', 'Amumu', 'Annie', 'Blitzcrank', 'Caitlyn', 'Chogath', 'Diana', 'DrMundo', 'Janna', 'JarvanIV', 'Jax', 'Karma', 'Leona', 'Malphite', 'Malzahar', 'Maokai', 'MasterYi', 'Milio', 'MissFortune', 'MonkeyKing', 'Morgana', 'Naafiri', 'Nasus', 'Neeko', 'Nocturne', 'Nunu', 'Olaf', 'Pantheon', 'Rammus', 'Renekton', 'Seraphine', 'Shyvana', 'Sion', 'Sona', 'Soraka', 'TahmKench', 'Tristana', 'Trundle', 'Tryndamere', 'Udyr', 'Vi', 'Warwick', 'XinZhao', 'Yuumi', 'Zac'],
}

GACHA_COST = dict(single=dict(gems=10, gold=0), multi=dict(gems=90, gold=0))

# --- Banners (multi-banner summoning) --------------------------------------
#   Standard: every champion, no rate-up. Featured banners: one per element,
#   each rate-ups an iconic SSR + SR of that element (50% of SSR pulls land
#   on the featured champ). Pity rules unchanged (per-banner pity counter).
GACHA_BANNERS = [
    dict(id="standard", name="Eternal Gate",
         desc="All champions. No rate-up.",
         pool=GACHA_POOL,
         featured_ssr=None, featured_sr=None,
         color=(120, 180, 255)),
    dict(id='fire', name='Crimson Pact',
         desc='Rate-up: Brand & Rumble (Fire).',
         pool={"SSR": ['Akshan', 'Azir', 'Brand', 'Cassiopeia', 'Darius', 'Draven', 'KSante', 'Katarina'],
               "SR":  ['Aatrox', 'Ambessa', 'Briar', 'Kled', 'Leblanc', 'Mel', 'Rell', 'Rumble'],
               "R":   ['Alistar', 'Amumu', 'Annie', 'Blitzcrank', 'Caitlyn', 'Chogath']},
         featured_ssr='Brand', featured_sr='Rumble',
         color=(255, 120, 90)),
    dict(id='water', name='Tidal Covenant',
         desc='Rate-up: Ashe & Braum (Water).',
         pool={"SSR": ['Anivia', 'Ashe', 'Gangplank', 'Gnar', 'Lissandra', 'Nilah', 'Ornn', 'Pyke'],
               "SR":  ['Aurora', 'Braum', 'Gragas', 'Graves', 'Illaoi', 'Nami', 'Nautilus', 'Sejuani'],
               "R":   ['Alistar', 'Amumu', 'Annie', 'Blitzcrank', 'Caitlyn', 'Chogath']},
         featured_ssr='Ashe', featured_sr='Braum',
         color=(90, 180, 255)),
    dict(id='wind', name='Tempest Call',
         desc='Rate-up: Yasuo & Janna (Wind).',
         pool={"SSR": ['Yasuo', 'Ahri', 'Akali', 'Hwei', 'Irelia', 'Ivern', 'Jhin', 'LeeSin', 'Lillia'],
               "SR":  ['Corki', 'Janna', 'Kayn', 'Kennen', 'Lulu', 'Nidalee', 'Quinn', 'Rakan'],
               "R":   ['Alistar', 'Amumu', 'Annie', 'Blitzcrank', 'Caitlyn', 'Chogath']},
         featured_ssr='Yasuo', featured_sr='Janna',
         color=(140, 230, 170)),
    dict(id='light', name='Dawn Covenant',
         desc='Rate-up: Lux & Sona (Light).',
         pool={"SSR": ['Aphelios', 'AurelionSol', 'Camille', 'Ezreal', 'Garen', 'Lux', 'Sylas', 'Zoe'],
               "SR":  ['Fiora', 'Galio', 'Heimerdinger', 'Jayce', 'Kayle', 'Orianna', 'Poppy', 'Sona'],
               "R":   ['Alistar', 'Amumu', 'Annie', 'Blitzcrank', 'Caitlyn', 'Chogath']},
         featured_ssr='Lux', featured_sr='Sona',
         color=(255, 220, 120)),
    dict(id='dark', name='Abyssal Veil',
         desc='Rate-up: Thresh & Pyke (Dark).',
         pool={"SSR": ['Thresh', 'Bard', 'Ekko', 'Jinx', 'Kaisa', 'Kalista', 'Kindred', 'Mordekaiser', 'Shaco'],
               "SR":  ['Pyke', 'Belveth', 'Elise', 'Evelynn', 'Fiddlesticks', 'Fizz', 'Gwen', 'Hecarim', 'Karthus'],
               "R":   ['Alistar', 'Amumu', 'Annie', 'Blitzcrank', 'Caitlyn', 'Chogath']},
         featured_ssr='Thresh', featured_sr='Pyke',
         color=(190, 120, 240)),
]
GACHA_BANNER_BY_ID = {b["id"]: b for b in GACHA_BANNERS}

# Pity tuning (per-banner; shared constants)
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
# reflects their kit instead of the role template. Keyed by hero id.
CONSTELLATION_PERK_OVERRIDES = {
    # Kael: the ember warrior — his fire ult burns hotter.
    "kael": [
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
        dict(id="c6", name="Meteor Lord", desc="Ultimate deals +40% ATK.",
             effect="ult_extra", val=0.40, target="atk_buff"),
    ],
    # Lyra: the moon oracle — her heal ult overflows.
    "lyra": [
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
        dict(id="c6", name="Lunar Benediction", desc="Ultimate buffs party ATK +35%.",
             effect="ult_extra", val=0.35, target="party_buff"),
    ],
    # Raven: the blood reaper — his dark ult crits harder.
    "raven": [
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
        dict(id="c6", name="Reaper's Coup", desc="Crit damage +30%.",
             effect="crit_dmg_up", val=0.30),
    ],
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


# ---------------------------------------------------------------------------
# HERO_ASSETS — per-character manifest (Task A2)
#   The single source of truth for the codex, hero-detail screen, and (later)
#   skill tooltips. Each entry bundles the hero's identity (name/title/element/
#   role), lore, the 2-3 active skills + ultimate + basic_attack (each with a
#   human-readable description + how-to-use), the signature passive, the 6
#   constellation perks, and the ultimate variant.
#   This is a PRESENTATION layer: it REFERENCES the combat dicts
#   (SKILLS_DB / ULTIMATE_VARIANTS / HERO_SIGNATURE / CONSTELLATION_PERKS /
#   HERO_LORE) for mechanics — it does NOT duplicate the combat data. Skill
#   costs/types come from SKILLS_DB; the description/how_to_use are the
#   per-hero flavor written here.
# ---------------------------------------------------------------------------
_SKILL_CATEGORY = {
    "attack": "Attack", "magic": "Magic",
    "aoe_attack": "AoE", "aoe_magic": "AoE",
    "heal": "Heal", "buff": "Buff", "debuff": "Debuff",
    "ultimate": "Ultimate", "revive": "Revive",
    "summon": "Summon", "beam": "Beam", "trap": "Trap", "innate": "Innate",
}

# Per-hero, per-skill description + how-to-use. Keyed by (hero_id, skill_id).
#   description  - a <=100-char sentence tied to the hero's title/element/role.
#   how_to_use   - names the key (Q/W/E for the 3 active, U/Space for ult, J
#                  for basic_attack) + a hold-to-aim note for attack/aoe/magic
#                  skills + the AoE/range.
# Per-champion, per-skill description + how-to-use. Keyed by (champ_id, skill_id).
# Auto-derived: the description is the LoL ability name (from the JSON); the
# how_to_use names the key (Q/W/E for the 3 active, U/Space for ult, J for
# basic_attack) + a hold-to-aim note by skill type.
_HERO_SKILL_TEXT = {
    ('Aatrox', 'fire_summon'): dict(description='The Darkin Blade', how_to_use='Q — tap to summon (lasts several seconds).'),
    ('Aatrox', 'fire_curse'): dict(description='Infernal Chains', how_to_use='W — tap to curse the nearest foe.'),
    ('Aatrox', 'phoenix'): dict(description='Umbral Dash', how_to_use='E — tap to heal an ally.'),
    ('Aatrox', 'meteor'): dict(description='World Ender', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Aatrox', "basic_attack"): dict(description="A brute's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Ahri', 'wind_aoe'): dict(description='Orb of Deception', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Ahri', 'evasion'): dict(description='Fox-Fire', how_to_use='W — tap to buff.'),
    ('Ahri', 'wind_arrow'): dict(description='Charm', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Ahri', 'tempest'): dict(description='Spirit Rush', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Ahri', "basic_attack"): dict(description="A vastaya's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Akali', 'evasion'): dict(description='Five Point Strike', how_to_use='Q — tap to buff.'),
    ('Akali', 'wind_arrow'): dict(description='Twilight Shroud', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Akali', 'wind_aoe'): dict(description='Shuriken Flip', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Akali', 'tempest'): dict(description='Perfect Execution', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Akali', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Akshan', 'fire_summon'): dict(description='Avengerang', how_to_use='Q — tap to summon (lasts several seconds).'),
    ('Akshan', 'fire_slash'): dict(description='Going Rogue', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Akshan', 'fire_curse'): dict(description='Heroic Swing', how_to_use='E — tap to curse the nearest foe.'),
    ('Akshan', 'meteor'): dict(description='Comeuppance', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Akshan', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Alistar', 'dark_curse'): dict(description='Pulverize', how_to_use='Q — tap to curse the nearest foe.'),
    ('Alistar', 'dark_bolt'): dict(description='Headbutt', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Alistar', 'shield_ward'): dict(description='Trample', how_to_use='E — tap to buff.'),
    ('Alistar', 'void_nova'): dict(description='Unbreakable Will', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Alistar', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Ambessa', 'phoenix'): dict(description='Cunning Sweep', how_to_use='Q — tap to heal an ally.'),
    ('Ambessa', 'fire_summon'): dict(description='Repudiation', how_to_use='W — tap to summon (lasts several seconds).'),
    ('Ambessa', 'fire_slash'): dict(description='Lacerate', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Ambessa', 'meteor'): dict(description='Public Execution', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Ambessa', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Amumu', 'fire_curse'): dict(description='Bandage Toss', how_to_use='Q — tap to curse the nearest foe.'),
    ('Amumu', 'inferno'): dict(description='Despair', how_to_use='W — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Amumu', 'fire_slash'): dict(description='Tantrum', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Amumu', 'meteor'): dict(description='Curse of the Sad Mummy', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Amumu', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Anivia', 'dark_curse'): dict(description='Flash Frost', how_to_use='Q — tap to curse the nearest foe.'),
    ('Anivia', 'water_bolt'): dict(description='Crystallize', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Anivia', 'tidal_wave'): dict(description='Frostbite', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Anivia', 'tsunami'): dict(description='Glacial Storm', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Anivia', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Annie', 'fire_bolt'): dict(description='Disintegrate', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Annie', 'inferno'): dict(description='Incinerate', how_to_use='W — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Annie', 'fire_summon'): dict(description='Molten Shield', how_to_use='E — tap to summon (lasts several seconds).'),
    ('Annie', 'meteor'): dict(description='Summon: Tibbers', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Annie', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Aphelios', 'light_beam'): dict(description='Weapons of the Faithful', how_to_use='Q — tap to fire in facing; hold to aim the line.'),
    ('Aphelios', 'light_slash'): dict(description='Phase', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Aphelios', 'judgement_aoe'): dict(description='Weapon Queue System', how_to_use='E — full energy; hits all enemies on screen.'),
    ('Aphelios', 'light_hymn'): dict(description='Moonlight Vigil', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Aphelios', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Ashe', 'tide_shield'): dict(description="Ranger's Focus", how_to_use='Q — tap to buff.'),
    ('Ashe', 'dark_curse'): dict(description='Volley', how_to_use='W — tap to curse the nearest foe.'),
    ('Ashe', 'water_bolt'): dict(description='Hawkshot', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Ashe', 'tsunami'): dict(description='Enchanted Crystal Arrow', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Ashe', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('AurelionSol', 'sanctuary'): dict(description='Breath of Light', how_to_use='Q — tap to heal an ally.'),
    ('AurelionSol', 'taunt_skill'): dict(description='Astral Flight', how_to_use='W — tap to buff.'),
    ('AurelionSol', 'light_slash'): dict(description='Singularity', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('AurelionSol', 'light_hymn'): dict(description='Falling Star', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('AurelionSol', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Aurora', 'water_heal'): dict(description='Twofold Hex', how_to_use='Q — tap to heal an ally.'),
    ('Aurora', 'tide_shield'): dict(description='Across the Veil', how_to_use='W — tap to buff.'),
    ('Aurora', 'dark_curse'): dict(description='The Weirding', how_to_use='E — tap to curse the nearest foe.'),
    ('Aurora', 'tsunami'): dict(description='Between Worlds', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Aurora', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Azir', 'fire_curse'): dict(description='Conquering Sands', how_to_use='Q — tap to curse the nearest foe.'),
    ('Azir', 'inferno'): dict(description='Arise!', how_to_use='W — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Azir', 'fire_summon'): dict(description='Shifting Sands', how_to_use='E — tap to summon (lasts several seconds).'),
    ('Azir', 'meteor'): dict(description="Emperor's Divide", how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Azir', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Bard', 'dark_curse'): dict(description='Cosmic Binding', how_to_use='Q — tap to curse the nearest foe.'),
    ('Bard', 'soul_drain'): dict(description="Caretaker's Shrine", how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Bard', 'dark_bolt'): dict(description='Magical Journey', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Bard', 'void_nova'): dict(description='Tempered Fate', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Bard', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Belveth', 'shield_ward'): dict(description='Void Surge', how_to_use='Q — tap to buff.'),
    ('Belveth', 'dark_curse'): dict(description='Above and Below', how_to_use='W — tap to curse the nearest foe.'),
    ('Belveth', 'soul_drain'): dict(description='Royal Maelstrom', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Belveth', 'void_nova'): dict(description='Endless Banquet', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Belveth', "basic_attack"): dict(description="A beast's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Blitzcrank', 'dark_curse'): dict(description='Rocket Grab', how_to_use='Q — tap to curse the nearest foe.'),
    ('Blitzcrank', 'shield_ward'): dict(description='Overdrive', how_to_use='W — tap to buff.'),
    ('Blitzcrank', 'dark_bolt'): dict(description='Power Fist', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Blitzcrank', 'void_nova'): dict(description='Static Field', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Blitzcrank', "basic_attack"): dict(description="A construct's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Brand', 'fire_curse'): dict(description='Sear', how_to_use='Q — tap to curse the nearest foe.'),
    ('Brand', 'inferno'): dict(description='Pillar of Flame', how_to_use='W — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Brand', 'fire_slash'): dict(description='Conflagration', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Brand', 'meteor'): dict(description='Pyroclasm', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Brand', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Braum', 'tide_shield'): dict(description="Winter's Bite", how_to_use='Q — tap to buff.'),
    ('Braum', 'water_bolt'): dict(description='Stand Behind Me', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Braum', 'tidal_wave'): dict(description='Unbreakable', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Braum', 'tsunami'): dict(description='Glacial Fissure', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Braum', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Briar', 'fire_curse'): dict(description='Head Rush', how_to_use='Q — tap to curse the nearest foe.'),
    ('Briar', 'fire_summon'): dict(description='Blood Frenzy', how_to_use='W — tap to summon (lasts several seconds).'),
    ('Briar', 'phoenix'): dict(description='Chilling Scream', how_to_use='E — tap to heal an ally.'),
    ('Briar', 'meteor'): dict(description='Certain Death', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Briar', "basic_attack"): dict(description="A beast's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Caitlyn', 'light_slash'): dict(description='Piltover Peacemaker', how_to_use='Q — tap to strike in facing; hold to aim.'),
    ('Caitlyn', 'taunt_skill'): dict(description='Yordle Snap Trap', how_to_use='W — tap to buff.'),
    ('Caitlyn', 'light_beam'): dict(description='90 Caliber Net', how_to_use='E — tap to fire in facing; hold to aim the line.'),
    ('Caitlyn', 'light_hymn'): dict(description='Ace in the Hole', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Caitlyn', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Camille', 'blessing'): dict(description='Precision Protocol', how_to_use='Q — tap to buff.'),
    ('Camille', 'sanctuary'): dict(description='Tactical Sweep', how_to_use='W — tap to heal an ally.'),
    ('Camille', 'taunt_skill'): dict(description='Hookshot', how_to_use='E — tap to buff.'),
    ('Camille', 'light_hymn'): dict(description='The Hextech Ultimatum', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Camille', "basic_attack"): dict(description="A construct's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Cassiopeia', 'fire_summon'): dict(description='Noxious Blast', how_to_use='Q — tap to summon (lasts several seconds).'),
    ('Cassiopeia', 'fire_curse'): dict(description='Miasma', how_to_use='W — tap to curse the nearest foe.'),
    ('Cassiopeia', 'phoenix'): dict(description='Twin Fang', how_to_use='E — tap to heal an ally.'),
    ('Cassiopeia', 'meteor'): dict(description='Petrifying Gaze', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Cassiopeia', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Chogath', 'dark_curse'): dict(description='Rupture', how_to_use='Q — tap to curse the nearest foe.'),
    ('Chogath', 'dark_bolt'): dict(description='Feral Scream', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Chogath', 'soul_drain'): dict(description='Vorpal Spikes', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Chogath', 'void_nova'): dict(description='Feast', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Chogath', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Corki', 'wind_aoe'): dict(description='Phosphorus Bomb', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Corki', 'wind_arrow'): dict(description='Valkyrie', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Corki', 'gust'): dict(description='Gatling Gun', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Corki', 'tempest'): dict(description='Missile Barrage', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Corki', "basic_attack"): dict(description="A yordle's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Darius', 'phoenix'): dict(description='Decimate', how_to_use='Q — tap to heal an ally.'),
    ('Darius', 'fire_summon'): dict(description='Crippling Strike', how_to_use='W — tap to summon (lasts several seconds).'),
    ('Darius', 'fire_curse'): dict(description='Apprehend', how_to_use='E — tap to curse the nearest foe.'),
    ('Darius', 'meteor'): dict(description='Noxian Guillotine', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Darius', "basic_attack"): dict(description="A brute's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Diana', 'judgement_aoe'): dict(description='Crescent Strike', how_to_use='Q — full energy; hits all enemies on screen.'),
    ('Diana', 'blessing'): dict(description='Pale Cascade', how_to_use='W — tap to buff.'),
    ('Diana', 'light_beam'): dict(description='Lunar Rush', how_to_use='E — tap to fire in facing; hold to aim the line.'),
    ('Diana', 'light_hymn'): dict(description='Moonfall', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Diana', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('DrMundo', 'soul_drain'): dict(description='Infected Bonesaw', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('DrMundo', 'dark_bolt'): dict(description='Heart Zapper', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('DrMundo', 'dark_aoe'): dict(description='Blunt Force Trauma', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('DrMundo', 'void_nova'): dict(description='Maximum Dosage', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('DrMundo', "basic_attack"): dict(description="A brute's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Draven', 'fire_summon'): dict(description='Spinning Axe', how_to_use='Q — tap to summon (lasts several seconds).'),
    ('Draven', 'fire_slash'): dict(description='Blood Rush', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Draven', 'fire_curse'): dict(description='Stand Aside', how_to_use='E — tap to curse the nearest foe.'),
    ('Draven', 'meteor'): dict(description='Whirling Death', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Draven', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Ekko', 'dark_curse'): dict(description='Timewinder', how_to_use='Q — tap to curse the nearest foe.'),
    ('Ekko', 'soul_drain'): dict(description='Parallel Convergence', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Ekko', 'shield_ward'): dict(description='Phase Dive', how_to_use='E — tap to buff.'),
    ('Ekko', 'void_nova'): dict(description='Chronobreak', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Ekko', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Elise', 'soul_drain'): dict(description='Neurotoxin', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Elise', 'shield_ward'): dict(description='Volatile Spiderling', how_to_use='W — tap to buff.'),
    ('Elise', 'dark_curse'): dict(description='Cocoon', how_to_use='E — tap to curse the nearest foe.'),
    ('Elise', 'void_nova'): dict(description='Spider Form / Human Form', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Elise', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Evelynn', 'shield_ward'): dict(description='Hate Spike', how_to_use='Q — tap to buff.'),
    ('Evelynn', 'dark_bolt'): dict(description='Allure', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Evelynn', 'soul_drain'): dict(description='Whiplash', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Evelynn', 'void_nova'): dict(description='Last Caress', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Evelynn', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Ezreal', 'light_slash'): dict(description='Mystic Shot', how_to_use='Q — tap to strike in facing; hold to aim.'),
    ('Ezreal', 'sanctuary'): dict(description='Essence Flux', how_to_use='W — tap to heal an ally.'),
    ('Ezreal', 'light_beam'): dict(description='Arcane Shift', how_to_use='E — tap to fire in facing; hold to aim the line.'),
    ('Ezreal', 'light_hymn'): dict(description='Trueshot Barrage', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Ezreal', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Fiddlesticks', 'dark_curse'): dict(description='Terrify', how_to_use='Q — tap to curse the nearest foe.'),
    ('Fiddlesticks', 'soul_drain'): dict(description='Bountiful Harvest', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Fiddlesticks', 'dark_bolt'): dict(description='Reap', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Fiddlesticks', 'void_nova'): dict(description='Crowstorm', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Fiddlesticks', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Fiora', 'light_slash'): dict(description='Lunge', how_to_use='Q — tap to strike in facing; hold to aim.'),
    ('Fiora', 'blessing'): dict(description='Riposte', how_to_use='W — tap to buff.'),
    ('Fiora', 'light_beam'): dict(description='Bladework', how_to_use='E — tap to fire in facing; hold to aim the line.'),
    ('Fiora', 'light_hymn'): dict(description='Grand Challenge', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Fiora', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Fizz', 'dark_bolt'): dict(description='Urchin Strike', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Fizz', 'soul_drain'): dict(description='Seastone Trident', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Fizz', 'dark_curse'): dict(description='Playful', how_to_use='E — tap to curse the nearest foe.'),
    ('Fizz', 'void_nova'): dict(description='Chum the Waters', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Fizz', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Galio', 'sanctuary'): dict(description='Winds of War', how_to_use='Q — tap to heal an ally.'),
    ('Galio', 'light_slash'): dict(description='Shield of Durand', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Galio', 'taunt_skill'): dict(description='Justice Punch', how_to_use='E — tap to buff.'),
    ('Galio', 'light_hymn'): dict(description="Hero's Entrance", how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Galio', "basic_attack"): dict(description="A construct's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Gangplank', 'water_bolt'): dict(description='Parrrley', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Gangplank', 'water_heal'): dict(description='Remove Scurvy', how_to_use='W — tap to heal an ally.'),
    ('Gangplank', 'tidal_wave'): dict(description='Powder Keg', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Gangplank', 'tsunami'): dict(description='Cannon Barrage', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Gangplank', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Garen', 'blessing'): dict(description='Decisive Strike', how_to_use='Q — tap to buff.'),
    ('Garen', 'light_slash'): dict(description='Courage', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Garen', 'light_beam'): dict(description='Judgment', how_to_use='E — tap to fire in facing; hold to aim the line.'),
    ('Garen', 'light_hymn'): dict(description='Demacian Justice', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Garen', "basic_attack"): dict(description="A brute's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Gnar', 'dark_curse'): dict(description='Boomerang Throw', how_to_use='Q — tap to curse the nearest foe.'),
    ('Gnar', 'tide_shield'): dict(description='Hyper', how_to_use='W — tap to buff.'),
    ('Gnar', 'water_bolt'): dict(description='Hop', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Gnar', 'tsunami'): dict(description='GNAR!', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Gnar', "basic_attack"): dict(description="A beast's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Gragas', 'dark_curse'): dict(description='Barrel Roll', how_to_use='Q — tap to curse the nearest foe.'),
    ('Gragas', 'tide_shield'): dict(description='Drunken Rage', how_to_use='W — tap to buff.'),
    ('Gragas', 'water_bolt'): dict(description='Body Slam', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Gragas', 'tsunami'): dict(description='Explosive Cask', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Gragas', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Graves', 'frost_nova'): dict(description='End of the Line', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Graves', 'dark_curse'): dict(description='Smoke Screen', how_to_use='W — tap to curse the nearest foe.'),
    ('Graves', 'tide_shield'): dict(description='Quickdraw', how_to_use='E — tap to buff.'),
    ('Graves', 'tsunami'): dict(description='Collateral Damage', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Graves', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Gwen', 'soul_drain'): dict(description='Snip Snip!', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Gwen', 'shield_ward'): dict(description='Hallowed Mist', how_to_use='W — tap to buff.'),
    ('Gwen', 'dark_bolt'): dict(description="Skip 'n Slash", how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Gwen', 'void_nova'): dict(description='Needlework', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Gwen', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Hecarim', 'shield_ward'): dict(description='Rampage', how_to_use='Q — tap to buff.'),
    ('Hecarim', 'soul_drain'): dict(description='Spirit of Dread', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Hecarim', 'dark_bolt'): dict(description='Devastating Charge', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Hecarim', 'void_nova'): dict(description='Onslaught of Shadows', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Hecarim', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Heimerdinger', 'light_beam'): dict(description='H-28G Evolution Turret', how_to_use='Q — tap to fire in facing; hold to aim the line.'),
    ('Heimerdinger', 'judgement_aoe'): dict(description='Hextech Micro-Rockets', how_to_use='W — full energy; hits all enemies on screen.'),
    ('Heimerdinger', 'taunt_skill'): dict(description='CH-2 Electron Storm Grenade', how_to_use='E — tap to buff.'),
    ('Heimerdinger', 'light_hymn'): dict(description='UPGRADE!!!', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Heimerdinger', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Hwei', 'wind_arrow'): dict(description='Subject: Disaster', how_to_use='Q — tap to strike in facing; hold to aim.'),
    ('Hwei', 'wind_aoe'): dict(description='Subject: Serenity', how_to_use='W — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Hwei', 'gust'): dict(description='Subject: Torment', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Hwei', 'tempest'): dict(description='Spiraling Despair', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Hwei', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Illaoi', 'frost_nova'): dict(description='Tentacle Smash', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Illaoi', 'tide_shield'): dict(description='Harsh Lesson', how_to_use='W — tap to buff.'),
    ('Illaoi', 'water_heal'): dict(description='Test of Spirit', how_to_use='E — tap to heal an ally.'),
    ('Illaoi', 'tsunami'): dict(description='Leap of Faith', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Illaoi', "basic_attack"): dict(description="A brute's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Irelia', 'evasion'): dict(description='Bladesurge', how_to_use='Q — tap to buff.'),
    ('Irelia', 'gust'): dict(description='Defiant Dance', how_to_use='W — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Irelia', 'wind_arrow'): dict(description='Flawless Duet', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Irelia', 'tempest'): dict(description="Vanguard's Edge", how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Irelia', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Ivern', 'evasion'): dict(description='Rootcaller', how_to_use='Q — tap to buff.'),
    ('Ivern', 'swift_buff'): dict(description='Brushmaker', how_to_use='W — tap to buff.'),
    ('Ivern', 'wind_arrow'): dict(description='Triggerseed', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Ivern', 'tempest'): dict(description='Daisy!', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Ivern', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Janna', 'dark_curse'): dict(description='Howling Gale', how_to_use='Q — tap to curse the nearest foe.'),
    ('Janna', 'shield_ward'): dict(description='Zephyr', how_to_use='W — tap to buff.'),
    ('Janna', 'dark_bolt'): dict(description='Eye of the Storm', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Janna', 'void_nova'): dict(description='Monsoon', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Janna', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('JarvanIV', 'taunt_skill'): dict(description='Dragon Strike', how_to_use='Q — tap to buff.'),
    ('JarvanIV', 'sanctuary'): dict(description='Golden Aegis', how_to_use='W — tap to heal an ally.'),
    ('JarvanIV', 'blessing'): dict(description='Demacian Standard', how_to_use='E — tap to buff.'),
    ('JarvanIV', 'light_hymn'): dict(description='Cataclysm', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('JarvanIV', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Jax', 'dark_bolt'): dict(description='Leap Strike', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Jax', 'shield_ward'): dict(description='Empower', how_to_use='W — tap to buff.'),
    ('Jax', 'dark_curse'): dict(description='Counter Strike', how_to_use='E — tap to curse the nearest foe.'),
    ('Jax', 'void_nova'): dict(description='Grandmaster-At-Arms', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Jax', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Jayce', 'taunt_skill'): dict(description='To the Skies!', how_to_use='Q — tap to buff.'),
    ('Jayce', 'sanctuary'): dict(description='Lightning Field', how_to_use='W — tap to heal an ally.'),
    ('Jayce', 'light_slash'): dict(description='Thundering Blow', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Jayce', 'light_hymn'): dict(description='Transform Mercury Cannon', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Jayce', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Jhin', 'gust'): dict(description='Dancing Grenade', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Jhin', 'swift_buff'): dict(description='Deadly Flourish', how_to_use='W — tap to buff.'),
    ('Jhin', 'evasion'): dict(description='Captive Audience', how_to_use='E — tap to buff.'),
    ('Jhin', 'tempest'): dict(description='Curtain Call', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Jhin', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Jinx', 'shield_ward'): dict(description='Switcheroo!', how_to_use='Q — tap to buff.'),
    ('Jinx', 'dark_curse'): dict(description='Zap!', how_to_use='W — tap to curse the nearest foe.'),
    ('Jinx', 'dark_bolt'): dict(description='Flame Chompers!', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Jinx', 'void_nova'): dict(description='Super Mega Death Rocket!', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Jinx', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('KSante', 'fire_curse'): dict(description='Ntofo Strikes', how_to_use='Q — tap to curse the nearest foe.'),
    ('KSante', 'fire_summon'): dict(description='Path Maker', how_to_use='W — tap to summon (lasts several seconds).'),
    ('KSante', 'fire_slash'): dict(description='Footwork', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('KSante', 'meteor'): dict(description='All Out', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('KSante', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Kaisa', 'soul_drain'): dict(description='Icathian Rain', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Kaisa', 'dark_bolt'): dict(description='Void Seeker', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Kaisa', 'shield_ward'): dict(description='Supercharge', how_to_use='E — tap to buff.'),
    ('Kaisa', 'void_nova'): dict(description='Killer Instinct', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Kaisa', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Kalista', 'dark_bolt'): dict(description='Pierce', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Kalista', 'dark_aoe'): dict(description='Sentinel', how_to_use='W — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Kalista', 'soul_drain'): dict(description='Rend', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Kalista', 'void_nova'): dict(description="Fate's Call", how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Kalista', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Karma', 'evasion'): dict(description='Inner Flame', how_to_use='Q — tap to buff.'),
    ('Karma', 'wind_arrow'): dict(description='Focused Resolve', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Karma', 'swift_buff'): dict(description='Inspire', how_to_use='E — tap to buff.'),
    ('Karma', 'tempest'): dict(description='Mantra', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Karma', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Karthus', 'dark_bolt'): dict(description='Lay Waste', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Karthus', 'dark_curse'): dict(description='Wall of Pain', how_to_use='W — tap to curse the nearest foe.'),
    ('Karthus', 'soul_drain'): dict(description='Defile', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Karthus', 'void_nova'): dict(description='Requiem', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Karthus', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Kassadin', 'shield_ward'): dict(description='Null Sphere', how_to_use='Q — tap to buff.'),
    ('Kassadin', 'soul_drain'): dict(description='Nether Blade', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Kassadin', 'dark_curse'): dict(description='Force Pulse', how_to_use='E — tap to curse the nearest foe.'),
    ('Kassadin', 'void_nova'): dict(description='Riftwalk', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Kassadin', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Katarina', 'inferno'): dict(description='Bouncing Blade', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Katarina', 'fire_summon'): dict(description='Preparation', how_to_use='W — tap to summon (lasts several seconds).'),
    ('Katarina', 'fire_bolt'): dict(description='Shunpo', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Katarina', 'meteor'): dict(description='Death Lotus', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Katarina', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Kayle', 'taunt_skill'): dict(description='Radiant Blast', how_to_use='Q — tap to buff.'),
    ('Kayle', 'sanctuary'): dict(description='Celestial Blessing', how_to_use='W — tap to heal an ally.'),
    ('Kayle', 'blessing'): dict(description='Starfire Spellblade', how_to_use='E — tap to buff.'),
    ('Kayle', 'light_hymn'): dict(description='Divine Judgment', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Kayle', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Kayn', 'evasion'): dict(description='Reaping Slash', how_to_use='Q — tap to buff.'),
    ('Kayn', 'wind_arrow'): dict(description="Blade's Reach", how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Kayn', 'wind_aoe'): dict(description='Shadow Step', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Kayn', 'tempest'): dict(description='Umbral Trespass', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Kayn', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Kennen', 'wind_arrow'): dict(description='Thundering Shuriken', how_to_use='Q — tap to strike in facing; hold to aim.'),
    ('Kennen', 'swift_buff'): dict(description='Electrical Surge', how_to_use='W — tap to buff.'),
    ('Kennen', 'evasion'): dict(description='Lightning Rush', how_to_use='E — tap to buff.'),
    ('Kennen', 'tempest'): dict(description='Slicing Maelstrom', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Kennen', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Khazix', 'dark_curse'): dict(description='Taste Their Fear', how_to_use='Q — tap to curse the nearest foe.'),
    ('Khazix', 'soul_drain'): dict(description='Void Spike', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Khazix', 'dark_bolt'): dict(description='Leap', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Khazix', 'void_nova'): dict(description='Void Assault', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Khazix', "basic_attack"): dict(description="A beast's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Kindred', 'shield_ward'): dict(description='Dance of Arrows', how_to_use='Q — tap to buff.'),
    ('Kindred', 'soul_drain'): dict(description="Wolf's Frenzy", how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Kindred', 'dark_bolt'): dict(description='Mounting Dread', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Kindred', 'void_nova'): dict(description="Lamb's Respite", how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Kindred', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Kled', 'fire_curse'): dict(description='Bear Trap on a Rope', how_to_use='Q — tap to curse the nearest foe.'),
    ('Kled', 'fire_summon'): dict(description='Violent Tendencies', how_to_use='W — tap to summon (lasts several seconds).'),
    ('Kled', 'fire_slash'): dict(description='Jousting', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Kled', 'meteor'): dict(description='Chaaaaaaaarge!!!', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Kled', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('KogMaw', 'shield_ward'): dict(description='Caustic Spittle', how_to_use='Q — tap to buff.'),
    ('KogMaw', 'dark_bolt'): dict(description='Bio-Arcane Barrage', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('KogMaw', 'dark_curse'): dict(description='Void Ooze', how_to_use='E — tap to curse the nearest foe.'),
    ('KogMaw', 'void_nova'): dict(description='Living Artillery', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('KogMaw', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Leblanc', 'fire_summon'): dict(description='Sigil of Malice', how_to_use='Q — tap to summon (lasts several seconds).'),
    ('Leblanc', 'inferno'): dict(description='Distortion', how_to_use='W — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Leblanc', 'fire_curse'): dict(description='Ethereal Chains', how_to_use='E — tap to curse the nearest foe.'),
    ('Leblanc', 'meteor'): dict(description='Mimic', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Leblanc', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('LeeSin', 'wind_arrow'): dict(description='Sonic Wave', how_to_use='Q — tap to strike in facing; hold to aim.'),
    ('LeeSin', 'swift_buff'): dict(description='Safeguard', how_to_use='W — tap to buff.'),
    ('LeeSin', 'wind_aoe'): dict(description='Tempest', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('LeeSin', 'tempest'): dict(description="Dragon's Rage", how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('LeeSin', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Leona', 'blessing'): dict(description='Shield of Daybreak', how_to_use='Q — tap to buff.'),
    ('Leona', 'light_slash'): dict(description='Eclipse', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Leona', 'taunt_skill'): dict(description='Zenith Blade', how_to_use='E — tap to buff.'),
    ('Leona', 'light_hymn'): dict(description='Solar Flare', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Leona', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Lillia', 'swift_buff'): dict(description='Blooming Blows', how_to_use='Q — tap to buff.'),
    ('Lillia', 'wind_aoe'): dict(description='Watch Out! Eep!', how_to_use='W — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Lillia', 'evasion'): dict(description='Swirlseed', how_to_use='E — tap to buff.'),
    ('Lillia', 'tempest'): dict(description='Lilting Lullaby', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Lillia', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Lissandra', 'dark_curse'): dict(description='Ice Shard', how_to_use='Q — tap to curse the nearest foe.'),
    ('Lissandra', 'water_bolt'): dict(description='Ring of Frost', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Lissandra', 'tidal_wave'): dict(description='Glacial Path', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Lissandra', 'tsunami'): dict(description='Frozen Tomb', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Lissandra', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Lucian', 'dark_bolt'): dict(description='Piercing Light', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Lucian', 'shield_ward'): dict(description='Ardent Blaze', how_to_use='W — tap to buff.'),
    ('Lucian', 'dark_aoe'): dict(description='Relentless Pursuit', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Lucian', 'void_nova'): dict(description='The Culling', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Lucian', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Lulu', 'evasion'): dict(description='Glitterlance', how_to_use='Q — tap to buff.'),
    ('Lulu', 'swift_buff'): dict(description='Whimsy', how_to_use='W — tap to buff.'),
    ('Lulu', 'wind_arrow'): dict(description='Help, Pix!', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Lulu', 'tempest'): dict(description='Wild Growth', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Lulu', "basic_attack"): dict(description="A yordle's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Lux', 'taunt_skill'): dict(description='Light Binding', how_to_use='Q — tap to buff.'),
    ('Lux', 'blessing'): dict(description='Prismatic Barrier', how_to_use='W — tap to buff.'),
    ('Lux', 'light_slash'): dict(description='Lucent Singularity', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Lux', 'light_hymn'): dict(description='Final Spark', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Lux', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Malphite', 'swift_buff'): dict(description='Seismic Shard', how_to_use='Q — tap to buff.'),
    ('Malphite', 'wind_arrow'): dict(description='Thunderclap', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Malphite', 'wind_aoe'): dict(description='Ground Slam', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Malphite', 'tempest'): dict(description='Unstoppable Force', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Malphite', "basic_attack"): dict(description="A construct's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Malzahar', 'dark_curse'): dict(description='Call of the Void', how_to_use='Q — tap to curse the nearest foe.'),
    ('Malzahar', 'dark_aoe'): dict(description='Void Swarm', how_to_use='W — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Malzahar', 'soul_drain'): dict(description='Malefic Visions', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Malzahar', 'void_nova'): dict(description='Nether Grasp', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Malzahar', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Maokai', 'shield_ward'): dict(description='Bramble Smash', how_to_use='Q — tap to buff.'),
    ('Maokai', 'dark_curse'): dict(description='Twisted Advance', how_to_use='W — tap to curse the nearest foe.'),
    ('Maokai', 'soul_drain'): dict(description='Sapling Toss', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Maokai', 'void_nova'): dict(description="Nature's Grasp", how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Maokai', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('MasterYi', 'swift_buff'): dict(description='Alpha Strike', how_to_use='Q — tap to buff.'),
    ('MasterYi', 'evasion'): dict(description='Meditate', how_to_use='W — tap to buff.'),
    ('MasterYi', 'wind_arrow'): dict(description='Wuju Style', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('MasterYi', 'tempest'): dict(description='Highlander', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('MasterYi', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Mel', 'inferno'): dict(description='Radiant Volley', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Mel', 'fire_summon'): dict(description='Rebuttal', how_to_use='W — tap to summon (lasts several seconds).'),
    ('Mel', 'fire_curse'): dict(description='Solar Snare', how_to_use='E — tap to curse the nearest foe.'),
    ('Mel', 'meteor'): dict(description='Golden Eclipse', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Mel', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Milio', 'evasion'): dict(description='Ultra Mega Fire Kick', how_to_use='Q — tap to buff.'),
    ('Milio', 'wind_arrow'): dict(description='Cozy Campfire', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Milio', 'swift_buff'): dict(description='Warm Hugs', how_to_use='E — tap to buff.'),
    ('Milio', 'tempest'): dict(description='Breath of Life', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Milio', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('MissFortune', 'water_bolt'): dict(description='Double Up', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('MissFortune', 'tide_shield'): dict(description='Strut', how_to_use='W — tap to buff.'),
    ('MissFortune', 'dark_curse'): dict(description='Make It Rain', how_to_use='E — tap to curse the nearest foe.'),
    ('MissFortune', 'tsunami'): dict(description='Bullet Time', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('MissFortune', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('MonkeyKing', 'swift_buff'): dict(description='Crushing Blow', how_to_use='Q — tap to buff.'),
    ('MonkeyKing', 'wind_arrow'): dict(description='Warrior Trickster', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('MonkeyKing', 'wind_aoe'): dict(description='Nimbus Strike', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('MonkeyKing', 'tempest'): dict(description='Cyclone', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('MonkeyKing', "basic_attack"): dict(description="A vastaya's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Mordekaiser', 'dark_bolt'): dict(description='Obliterate', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Mordekaiser', 'soul_drain'): dict(description='Indestructible', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Mordekaiser', 'dark_curse'): dict(description="Death's Grasp", how_to_use='E — tap to curse the nearest foe.'),
    ('Mordekaiser', 'void_nova'): dict(description='Realm of Death', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Mordekaiser', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Morgana', 'taunt_skill'): dict(description='Dark Binding', how_to_use='Q — tap to buff.'),
    ('Morgana', 'sanctuary'): dict(description='Tormented Shadow', how_to_use='W — tap to heal an ally.'),
    ('Morgana', 'blessing'): dict(description='Black Shield', how_to_use='E — tap to buff.'),
    ('Morgana', 'light_hymn'): dict(description='Soul Shackles', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Morgana', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Naafiri', 'phoenix'): dict(description='Darkin Daggers', how_to_use='Q — tap to heal an ally.'),
    ('Naafiri', 'fire_summon'): dict(description='The Call of the Pack', how_to_use='W — tap to summon (lasts several seconds).'),
    ('Naafiri', 'fire_slash'): dict(description='Eviscerate', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Naafiri', 'meteor'): dict(description="Hounds' Pursuit", how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Naafiri', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Nami', 'tidal_wave'): dict(description='Aqua Prison', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Nami', 'water_heal'): dict(description='Ebb and Flow', how_to_use='W — tap to heal an ally.'),
    ('Nami', 'tide_shield'): dict(description="Tidecaller's Blessing", how_to_use='E — tap to buff.'),
    ('Nami', 'tsunami'): dict(description='Tidal Wave', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Nami', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Nasus', 'fire_summon'): dict(description='Siphoning Strike', how_to_use='Q — tap to summon (lasts several seconds).'),
    ('Nasus', 'fire_curse'): dict(description='Wither', how_to_use='W — tap to curse the nearest foe.'),
    ('Nasus', 'inferno'): dict(description='Spirit Fire', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Nasus', 'meteor'): dict(description='Fury of the Sands', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Nasus', "basic_attack"): dict(description="A brute's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Nautilus', 'dark_curse'): dict(description='Dredge Line', how_to_use='Q — tap to curse the nearest foe.'),
    ('Nautilus', 'tide_shield'): dict(description="Titan's Wrath", how_to_use='W — tap to buff.'),
    ('Nautilus', 'water_bolt'): dict(description='Riptide', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Nautilus', 'tsunami'): dict(description='Depth Charge', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Nautilus', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Neeko', 'swift_buff'): dict(description='Blooming Burst', how_to_use='Q — tap to buff.'),
    ('Neeko', 'wind_arrow'): dict(description='Shapesplitter', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Neeko', 'evasion'): dict(description='Tangle-Barbs', how_to_use='E — tap to buff.'),
    ('Neeko', 'tempest'): dict(description='Pop Blossom', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Neeko', "basic_attack"): dict(description="A vastaya's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Nidalee', 'wind_arrow'): dict(description='Javelin Toss', how_to_use='Q — tap to strike in facing; hold to aim.'),
    ('Nidalee', 'evasion'): dict(description='Bushwhack', how_to_use='W — tap to buff.'),
    ('Nidalee', 'wind_aoe'): dict(description='Primal Surge', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Nidalee', 'tempest'): dict(description='Aspect of the Cougar', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Nidalee', "basic_attack"): dict(description="A beast's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Nilah', 'water_heal'): dict(description='Formless Blade', how_to_use='Q — tap to heal an ally.'),
    ('Nilah', 'tide_shield'): dict(description='Jubilant Veil', how_to_use='W — tap to buff.'),
    ('Nilah', 'frost_nova'): dict(description='Slipstream', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Nilah', 'tsunami'): dict(description='Apotheosis', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Nilah', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Nocturne', 'shield_ward'): dict(description='Duskbringer', how_to_use='Q — tap to buff.'),
    ('Nocturne', 'dark_bolt'): dict(description='Shroud of Darkness', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Nocturne', 'dark_aoe'): dict(description='Unspeakable Horror', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Nocturne', 'void_nova'): dict(description='Paranoia', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Nocturne', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Nunu', 'water_heal'): dict(description='Consume', how_to_use='Q — tap to heal an ally.'),
    ('Nunu', 'dark_curse'): dict(description='Biggest Snowball Ever!', how_to_use='W — tap to curse the nearest foe.'),
    ('Nunu', 'water_bolt'): dict(description='Snowball Barrage', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Nunu', 'tsunami'): dict(description='Absolute Zero', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Nunu', "basic_attack"): dict(description="A beast's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Olaf', 'tide_shield'): dict(description='Undertow', how_to_use='Q — tap to buff.'),
    ('Olaf', 'water_heal'): dict(description='Tough It Out', how_to_use='W — tap to heal an ally.'),
    ('Olaf', 'water_bolt'): dict(description='Reckless Swing', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Olaf', 'tsunami'): dict(description='Ragnarok', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Olaf', "basic_attack"): dict(description="A brute's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Orianna', 'judgement_aoe'): dict(description='Command: Attack', how_to_use='Q — full energy; hits all enemies on screen.'),
    ('Orianna', 'blessing'): dict(description='Command: Dissonance', how_to_use='W — tap to buff.'),
    ('Orianna', 'light_slash'): dict(description='Command: Protect', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Orianna', 'light_hymn'): dict(description='Command: Shockwave', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Orianna', "basic_attack"): dict(description="A construct's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Ornn', 'dark_curse'): dict(description='Volcanic Rupture', how_to_use='Q — tap to curse the nearest foe.'),
    ('Ornn', 'tidal_wave'): dict(description='Bellows Breath', how_to_use='W — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Ornn', 'water_bolt'): dict(description='Searing Charge', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Ornn', 'tsunami'): dict(description='Call of the Forge God', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Ornn', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Pantheon', 'sanctuary'): dict(description='Comet Spear', how_to_use='Q — tap to heal an ally.'),
    ('Pantheon', 'blessing'): dict(description='Shield Vault', how_to_use='W — tap to buff.'),
    ('Pantheon', 'light_slash'): dict(description='Aegis Assault', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Pantheon', 'light_hymn'): dict(description='Grand Starfall', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Pantheon', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Poppy', 'sanctuary'): dict(description='Hammer Shock', how_to_use='Q — tap to heal an ally.'),
    ('Poppy', 'light_slash'): dict(description='Steadfast Presence', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Poppy', 'taunt_skill'): dict(description='Heroic Charge', how_to_use='E — tap to buff.'),
    ('Poppy', 'light_hymn'): dict(description="Keeper's Verdict", how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Poppy', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Pyke', 'dark_curse'): dict(description='Bone Skewer', how_to_use='Q — tap to curse the nearest foe.'),
    ('Pyke', 'tide_shield'): dict(description='Ghostwater Dive', how_to_use='W — tap to buff.'),
    ('Pyke', 'water_bolt'): dict(description='Phantom Undertow', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Pyke', 'tsunami'): dict(description='Death from Below', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Pyke', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Qiyana', 'gust'): dict(description='Edge of Ixtal', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Qiyana', 'swift_buff'): dict(description='Terrashape', how_to_use='W — tap to buff.'),
    ('Qiyana', 'wind_arrow'): dict(description='Audacity', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Qiyana', 'tempest'): dict(description='Supreme Display of Talent', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Qiyana', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Quinn', 'evasion'): dict(description='Blinding Assault', how_to_use='Q — tap to buff.'),
    ('Quinn', 'swift_buff'): dict(description='Heightened Senses', how_to_use='W — tap to buff.'),
    ('Quinn', 'wind_arrow'): dict(description='Vault', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Quinn', 'tempest'): dict(description='Behind Enemy Lines', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Quinn', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Rakan', 'evasion'): dict(description='Gleaming Quill', how_to_use='Q — tap to buff.'),
    ('Rakan', 'wind_arrow'): dict(description='Grand Entrance', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Rakan', 'swift_buff'): dict(description='Battle Dance', how_to_use='E — tap to buff.'),
    ('Rakan', 'tempest'): dict(description='The Quickness', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Rakan', "basic_attack"): dict(description="A vastaya's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Rammus', 'fire_summon'): dict(description='Powerball', how_to_use='Q — tap to summon (lasts several seconds).'),
    ('Rammus', 'fire_slash'): dict(description='Defensive Ball Curl', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Rammus', 'fire_bolt'): dict(description='Frenzying Taunt', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Rammus', 'meteor'): dict(description='Soaring Slam', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Rammus', "basic_attack"): dict(description="A construct's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('RekSai', 'shield_ward'): dict(description="Queen's Wrath", how_to_use='Q — tap to buff.'),
    ('RekSai', 'dark_bolt'): dict(description='Burrow', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('RekSai', 'dark_aoe'): dict(description='Furious Bite', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('RekSai', 'void_nova'): dict(description='Void Rush', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('RekSai', "basic_attack"): dict(description="A beast's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Rell', 'fire_summon'): dict(description='Shattering Strike', how_to_use='Q — tap to summon (lasts several seconds).'),
    ('Rell', 'fire_slash'): dict(description='Ferromancy: Crash Down', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Rell', 'phoenix'): dict(description='Full Tilt', how_to_use='E — tap to heal an ally.'),
    ('Rell', 'meteor'): dict(description='Magnet Storm', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Rell', "basic_attack"): dict(description="A construct's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Renata', 'dark_curse'): dict(description='Handshake', how_to_use='Q — tap to curse the nearest foe.'),
    ('Renata', 'soul_drain'): dict(description='Bailout', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Renata', 'shield_ward'): dict(description='Loyalty Program', how_to_use='E — tap to buff.'),
    ('Renata', 'void_nova'): dict(description='Hostile Takeover', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Renata', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Renekton', 'phoenix'): dict(description='Cull the Meek', how_to_use='Q — tap to heal an ally.'),
    ('Renekton', 'fire_summon'): dict(description='Ruthless Predator', how_to_use='W — tap to summon (lasts several seconds).'),
    ('Renekton', 'fire_strike'): dict(description='Slice', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Renekton', 'meteor'): dict(description='Dominus', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Renekton', "basic_attack"): dict(description="A brute's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Rengar', 'swift_buff'): dict(description='Savagery', how_to_use='Q — tap to buff.'),
    ('Rengar', 'evasion'): dict(description='Battle Roar', how_to_use='W — tap to buff.'),
    ('Rengar', 'wind_arrow'): dict(description='Bola Strike', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Rengar', 'tempest'): dict(description='Thrill of the Hunt', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Rengar', "basic_attack"): dict(description="A vastaya's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Riven', 'fire_curse'): dict(description='Broken Wings', how_to_use='Q — tap to curse the nearest foe.'),
    ('Riven', 'fire_slash'): dict(description='Ki Burst', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Riven', 'fire_summon'): dict(description='Valor', how_to_use='E — tap to summon (lasts several seconds).'),
    ('Riven', 'meteor'): dict(description='Blade of the Exile', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Riven', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Rumble', 'phoenix'): dict(description='Flamespitter', how_to_use='Q — tap to heal an ally.'),
    ('Rumble', 'fire_summon'): dict(description='Scrap Shield', how_to_use='W — tap to summon (lasts several seconds).'),
    ('Rumble', 'fire_curse'): dict(description='Electro Harpoon', how_to_use='E — tap to curse the nearest foe.'),
    ('Rumble', 'meteor'): dict(description='The Equalizer', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Rumble', "basic_attack"): dict(description="A yordle's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Ryze', 'shield_ward'): dict(description='Overload', how_to_use='Q — tap to buff.'),
    ('Ryze', 'dark_curse'): dict(description='Rune Prison', how_to_use='W — tap to curse the nearest foe.'),
    ('Ryze', 'dark_bolt'): dict(description='Spell Flux', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Ryze', 'void_nova'): dict(description='Realm Warp', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Ryze', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Samira', 'fire_slash'): dict(description='Flair', how_to_use='Q — tap to strike in facing; hold to aim.'),
    ('Samira', 'fire_strike'): dict(description='Blade Whirl', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Samira', 'fire_summon'): dict(description='Wild Rush', how_to_use='E — tap to summon (lasts several seconds).'),
    ('Samira', 'meteor'): dict(description='Inferno Trigger', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Samira', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Sejuani', 'dark_curse'): dict(description='Arctic Assault', how_to_use='Q — tap to curse the nearest foe.'),
    ('Sejuani', 'water_bolt'): dict(description="Winter's Wrath", how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Sejuani', 'tidal_wave'): dict(description='Permafrost', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Sejuani', 'tsunami'): dict(description='Glacial Prison', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Sejuani', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Senna', 'soul_drain'): dict(description='Piercing Darkness', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Senna', 'dark_curse'): dict(description='Last Embrace', how_to_use='W — tap to curse the nearest foe.'),
    ('Senna', 'shield_ward'): dict(description='Curse of the Black Mist', how_to_use='E — tap to buff.'),
    ('Senna', 'void_nova'): dict(description='Dawning Shadow', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Senna', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Seraphine', 'sanctuary'): dict(description='High Note', how_to_use='Q — tap to heal an ally.'),
    ('Seraphine', 'light_slash'): dict(description='Surround Sound', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Seraphine', 'taunt_skill'): dict(description='Beat Drop', how_to_use='E — tap to buff.'),
    ('Seraphine', 'light_hymn'): dict(description='Encore', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Seraphine', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Sett', 'swift_buff'): dict(description='Knuckle Down', how_to_use='Q — tap to buff.'),
    ('Sett', 'evasion'): dict(description='Haymaker', how_to_use='W — tap to buff.'),
    ('Sett', 'wind_arrow'): dict(description='Facebreaker', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Sett', 'tempest'): dict(description='The Show Stopper', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Sett', "basic_attack"): dict(description="A vastaya's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Shaco', 'shield_ward'): dict(description='Deceive', how_to_use='Q — tap to buff.'),
    ('Shaco', 'dark_bolt'): dict(description='Jack in the Box', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Shaco', 'soul_drain'): dict(description='Two-Shiv Poison', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Shaco', 'void_nova'): dict(description='Hallucinate', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Shaco', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Shen', 'swift_buff'): dict(description='Twilight Assault', how_to_use='Q — tap to buff.'),
    ('Shen', 'wind_arrow'): dict(description="Spirit's Refuge", how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Shen', 'evasion'): dict(description='Shadow Dash', how_to_use='E — tap to buff.'),
    ('Shen', 'tempest'): dict(description='Stand United', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Shen', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Shyvana', 'blessing'): dict(description='Twin Bite', how_to_use='Q — tap to buff.'),
    ('Shyvana', 'light_slash'): dict(description='Burnout', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Shyvana', 'sanctuary'): dict(description='Flame Breath', how_to_use='E — tap to heal an ally.'),
    ('Shyvana', 'light_hymn'): dict(description="Dragon's Descent", how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Shyvana', "basic_attack"): dict(description="A vastaya's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Singed', 'dark_aoe'): dict(description='Poison Trail', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Singed', 'dark_curse'): dict(description='Mega Adhesive', how_to_use='W — tap to curse the nearest foe.'),
    ('Singed', 'soul_drain'): dict(description='Fling', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Singed', 'void_nova'): dict(description='Insanity Potion', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Singed', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Sion', 'fire_summon'): dict(description='Decimating Smash', how_to_use='Q — tap to summon (lasts several seconds).'),
    ('Sion', 'phoenix'): dict(description='Soul Furnace', how_to_use='W — tap to heal an ally.'),
    ('Sion', 'fire_curse'): dict(description='Roar of the Slayer', how_to_use='E — tap to curse the nearest foe.'),
    ('Sion', 'meteor'): dict(description='Unstoppable Onslaught', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Sion', "basic_attack"): dict(description="A brute's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Sivir', 'fire_strike'): dict(description='Boomerang Blade', how_to_use='Q — tap to strike in facing; hold to aim.'),
    ('Sivir', 'phoenix'): dict(description='Ricochet', how_to_use='W — tap to heal an ally.'),
    ('Sivir', 'fire_slash'): dict(description='Spell Shield', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Sivir', 'meteor'): dict(description='On the Hunt', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Sivir', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Skarner', 'evasion'): dict(description='Shattered Earth', how_to_use='Q — tap to buff.'),
    ('Skarner', 'wind_arrow'): dict(description='Seismic Bastion', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Skarner', 'swift_buff'): dict(description="Ixtal's Impact", how_to_use='E — tap to buff.'),
    ('Skarner', 'tempest'): dict(description='Impale', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Skarner', "basic_attack"): dict(description="A construct's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Smolder', 'soul_drain'): dict(description='Super Scorcher Breath', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Smolder', 'dark_curse'): dict(description='Achooo!', how_to_use='W — tap to curse the nearest foe.'),
    ('Smolder', 'shield_ward'): dict(description='Flap, Flap, Flap', how_to_use='E — tap to buff.'),
    ('Smolder', 'void_nova'): dict(description='MMOOOMMMM!', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Smolder', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Sona', 'blessing'): dict(description='Hymn of Valor', how_to_use='Q — tap to buff.'),
    ('Sona', 'sanctuary'): dict(description='Aria of Perseverance', how_to_use='W — tap to heal an ally.'),
    ('Sona', 'light_slash'): dict(description='Song of Celerity', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Sona', 'light_hymn'): dict(description='Crescendo', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Sona', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Soraka', 'sanctuary'): dict(description='Starcall', how_to_use='Q — tap to heal an ally.'),
    ('Soraka', 'light_slash'): dict(description='Astral Infusion', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Soraka', 'taunt_skill'): dict(description='Equinox', how_to_use='E — tap to buff.'),
    ('Soraka', 'light_hymn'): dict(description='Wish', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Soraka', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Swain', 'fire_summon'): dict(description="Death's Hand", how_to_use='Q — tap to summon (lasts several seconds).'),
    ('Swain', 'fire_curse'): dict(description='Vision of Empire', how_to_use='W — tap to curse the nearest foe.'),
    ('Swain', 'fire_slash'): dict(description='Nevermove', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Swain', 'meteor'): dict(description='Demonic Ascension', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Swain', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Sylas', 'taunt_skill'): dict(description='Chain Lash', how_to_use='Q — tap to buff.'),
    ('Sylas', 'sanctuary'): dict(description='Kingslayer', how_to_use='W — tap to heal an ally.'),
    ('Sylas', 'light_beam'): dict(description='Abscond', how_to_use='E — tap to fire in facing; hold to aim the line.'),
    ('Sylas', 'light_hymn'): dict(description='Hijack', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Sylas', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Syndra', 'wind_aoe'): dict(description='Dark Sphere', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Syndra', 'swift_buff'): dict(description='Force of Will', how_to_use='W — tap to buff.'),
    ('Syndra', 'evasion'): dict(description='Scatter the Weak', how_to_use='E — tap to buff.'),
    ('Syndra', 'tempest'): dict(description='Unleashed Power', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Syndra', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('TahmKench', 'soul_drain'): dict(description='Tongue Lash', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('TahmKench', 'dark_curse'): dict(description='Abyssal Dive', how_to_use='W — tap to curse the nearest foe.'),
    ('TahmKench', 'dark_bolt'): dict(description='Thick Skin', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('TahmKench', 'void_nova'): dict(description='Devour', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('TahmKench', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Taliyah', 'fire_summon'): dict(description='Threaded Volley', how_to_use='Q — tap to summon (lasts several seconds).'),
    ('Taliyah', 'fire_curse'): dict(description='Seismic Shove', how_to_use='W — tap to curse the nearest foe.'),
    ('Taliyah', 'fire_slash'): dict(description='Unraveled Earth', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Taliyah', 'meteor'): dict(description="Weaver's Wall", how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Taliyah', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Talon', 'phoenix'): dict(description='Noxian Diplomacy', how_to_use='Q — tap to heal an ally.'),
    ('Talon', 'fire_curse'): dict(description='Rake', how_to_use='W — tap to curse the nearest foe.'),
    ('Talon', 'fire_bolt'): dict(description="Assassin's Path", how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Talon', 'meteor'): dict(description='Shadow Assault', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Talon', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Taric', 'sanctuary'): dict(description="Starlight's Touch", how_to_use='Q — tap to heal an ally.'),
    ('Taric', 'blessing'): dict(description='Bastion', how_to_use='W — tap to buff.'),
    ('Taric', 'taunt_skill'): dict(description='Dazzle', how_to_use='E — tap to buff.'),
    ('Taric', 'light_hymn'): dict(description='Cosmic Radiance', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Taric', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Teemo', 'wind_arrow'): dict(description='Blinding Dart', how_to_use='Q — tap to strike in facing; hold to aim.'),
    ('Teemo', 'swift_buff'): dict(description='Move Quick', how_to_use='W — tap to buff.'),
    ('Teemo', 'wind_aoe'): dict(description='Toxic Shot', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Teemo', 'tempest'): dict(description='Noxious Trap', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Teemo', "basic_attack"): dict(description="A yordle's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Thresh', 'dark_curse'): dict(description='Death Sentence', how_to_use='Q — tap to curse the nearest foe.'),
    ('Thresh', 'shield_ward'): dict(description='Dark Passage', how_to_use='W — tap to buff.'),
    ('Thresh', 'dark_bolt'): dict(description='Flay', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Thresh', 'void_nova'): dict(description='The Box', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Thresh', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Tristana', 'swift_buff'): dict(description='Rapid Fire', how_to_use='Q — tap to buff.'),
    ('Tristana', 'evasion'): dict(description='Rocket Jump', how_to_use='W — tap to buff.'),
    ('Tristana', 'wind_arrow'): dict(description='Explosive Charge', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Tristana', 'tempest'): dict(description='Buster Shot', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Tristana', "basic_attack"): dict(description="A yordle's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Trundle', 'tide_shield'): dict(description='Chomp', how_to_use='Q — tap to buff.'),
    ('Trundle', 'water_heal'): dict(description='Frozen Domain', how_to_use='W — tap to heal an ally.'),
    ('Trundle', 'dark_curse'): dict(description='Pillar of Ice', how_to_use='E — tap to curse the nearest foe.'),
    ('Trundle', 'tsunami'): dict(description='Subjugate', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Trundle', "basic_attack"): dict(description="A brute's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Tryndamere', 'water_heal'): dict(description='Bloodlust', how_to_use='Q — tap to heal an ally.'),
    ('Tryndamere', 'tide_shield'): dict(description='Mocking Shout', how_to_use='W — tap to buff.'),
    ('Tryndamere', 'frost_nova'): dict(description='Spinning Slash', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Tryndamere', 'tsunami'): dict(description='Undying Rage', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Tryndamere', "basic_attack"): dict(description="A brute's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('TwistedFate', 'tidal_wave'): dict(description='Wild Cards', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('TwistedFate', 'water_heal'): dict(description='Pick a Card', how_to_use='W — tap to heal an ally.'),
    ('TwistedFate', 'tide_shield'): dict(description='Stacked Deck', how_to_use='E — tap to buff.'),
    ('TwistedFate', 'tsunami'): dict(description='Destiny', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('TwistedFate', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Twitch', 'shield_ward'): dict(description='Ambush', how_to_use='Q — tap to buff.'),
    ('Twitch', 'dark_curse'): dict(description='Venom Cask', how_to_use='W — tap to curse the nearest foe.'),
    ('Twitch', 'dark_bolt'): dict(description='Contaminate', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Twitch', 'void_nova'): dict(description='Spray and Pray', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Twitch', "basic_attack"): dict(description="A beast's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Udyr', 'water_heal'): dict(description='Wilding Claw', how_to_use='Q — tap to heal an ally.'),
    ('Udyr', 'water_bolt'): dict(description='Iron Mantle', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Udyr', 'tide_shield'): dict(description='Blazing Stampede', how_to_use='E — tap to buff.'),
    ('Udyr', 'tsunami'): dict(description='Wingborne Storm', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Udyr', "basic_attack"): dict(description="A beast's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Urgot', 'dark_curse'): dict(description='Corrosive Charge', how_to_use='Q — tap to curse the nearest foe.'),
    ('Urgot', 'dark_bolt'): dict(description='Purge', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Urgot', 'shield_ward'): dict(description='Disdain', how_to_use='E — tap to buff.'),
    ('Urgot', 'void_nova'): dict(description='Fear Beyond Death', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Urgot', "basic_attack"): dict(description="A brute's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Varus', 'evasion'): dict(description='Piercing Arrow', how_to_use='Q — tap to buff.'),
    ('Varus', 'swift_buff'): dict(description='Blighted Quiver', how_to_use='W — tap to buff.'),
    ('Varus', 'wind_arrow'): dict(description='Hail of Arrows', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Varus', 'tempest'): dict(description='Chain of Corruption', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Varus', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Vayne', 'blessing'): dict(description='Tumble', how_to_use='Q — tap to buff.'),
    ('Vayne', 'light_slash'): dict(description='Silver Bolts', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Vayne', 'light_beam'): dict(description='Condemn', how_to_use='E — tap to fire in facing; hold to aim the line.'),
    ('Vayne', 'light_hymn'): dict(description='Final Hour', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Vayne', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Veigar', 'wind_aoe'): dict(description='Baleful Strike', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Veigar', 'wind_arrow'): dict(description='Dark Matter', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Veigar', 'evasion'): dict(description='Event Horizon', how_to_use='E — tap to buff.'),
    ('Veigar', 'tempest'): dict(description='Primordial Burst', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Veigar', "basic_attack"): dict(description="A yordle's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Velkoz', 'soul_drain'): dict(description='Plasma Fission', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Velkoz', 'dark_aoe'): dict(description='Void Rift', how_to_use='W — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Velkoz', 'dark_curse'): dict(description='Tectonic Disruption', how_to_use='E — tap to curse the nearest foe.'),
    ('Velkoz', 'void_nova'): dict(description='Life Form Disintegration Ray', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Velkoz', "basic_attack"): dict(description="A construct's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Vex', 'dark_aoe'): dict(description='Mistral Bolt', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Vex', 'shield_ward'): dict(description='Personal Space', how_to_use='W — tap to buff.'),
    ('Vex', 'dark_curse'): dict(description='Looming Darkness', how_to_use='E — tap to curse the nearest foe.'),
    ('Vex', 'void_nova'): dict(description='Shadow Surge', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Vex', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Vi', 'taunt_skill'): dict(description='Vault Breaker', how_to_use='Q — tap to buff.'),
    ('Vi', 'blessing'): dict(description='Denting Blows', how_to_use='W — tap to buff.'),
    ('Vi', 'light_slash'): dict(description='Relentless Force', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Vi', 'light_hymn'): dict(description='Cease and Desist', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Vi', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Viego', 'soul_drain'): dict(description='Blade of the Ruined King', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Viego', 'dark_curse'): dict(description='Spectral Maw', how_to_use='W — tap to curse the nearest foe.'),
    ('Viego', 'shield_ward'): dict(description='Harrowed Path', how_to_use='E — tap to buff.'),
    ('Viego', 'void_nova'): dict(description='Heartbreaker', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Viego', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Viktor', 'shield_ward'): dict(description='Siphon Power', how_to_use='Q — tap to buff.'),
    ('Viktor', 'dark_curse'): dict(description='Gravity Field', how_to_use='W — tap to curse the nearest foe.'),
    ('Viktor', 'dark_aoe'): dict(description='Hextech Ray', how_to_use='E — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Viktor', 'void_nova'): dict(description='Arcane Storm', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Viktor', "basic_attack"): dict(description="A construct's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Vladimir', 'phoenix'): dict(description='Transfusion', how_to_use='Q — tap to heal an ally.'),
    ('Vladimir', 'fire_slash'): dict(description='Sanguine Pool', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Vladimir', 'fire_bolt'): dict(description='Tides of Blood', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Vladimir', 'meteor'): dict(description='Hemoplague', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Vladimir', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Volibear', 'tide_shield'): dict(description='Thundering Smash', how_to_use='Q — tap to buff.'),
    ('Volibear', 'water_heal'): dict(description='Frenzied Maul', how_to_use='W — tap to heal an ally.'),
    ('Volibear', 'water_bolt'): dict(description='Sky Splitter', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Volibear', 'tsunami'): dict(description='Stormbringer', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Volibear', "basic_attack"): dict(description="A beast's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Warwick', 'soul_drain'): dict(description='Jaws of the Beast', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Warwick', 'dark_bolt'): dict(description='Blood Hunt', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Warwick', 'shield_ward'): dict(description='Primal Howl', how_to_use='E — tap to buff.'),
    ('Warwick', 'void_nova'): dict(description='Infinite Duress', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Warwick', "basic_attack"): dict(description="A beast's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Xayah', 'gust'): dict(description='Double Daggers', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Xayah', 'swift_buff'): dict(description='Deadly Plumage', how_to_use='W — tap to buff.'),
    ('Xayah', 'evasion'): dict(description='Bladecaller', how_to_use='E — tap to buff.'),
    ('Xayah', 'tempest'): dict(description='Featherstorm', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Xayah', "basic_attack"): dict(description="A vastaya's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Xerath', 'fire_curse'): dict(description='Arcanopulse', how_to_use='Q — tap to curse the nearest foe.'),
    ('Xerath', 'fire_slash'): dict(description='Eye of Destruction', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Xerath', 'fire_bolt'): dict(description='Shocking Orb', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Xerath', 'meteor'): dict(description='Rite of the Arcane', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Xerath', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('XinZhao', 'blessing'): dict(description='Three Talon Strike', how_to_use='Q — tap to buff.'),
    ('XinZhao', 'sanctuary'): dict(description='Wind Becomes Lightning', how_to_use='W — tap to heal an ally.'),
    ('XinZhao', 'light_slash'): dict(description='Audacious Charge', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('XinZhao', 'light_hymn'): dict(description='Crescent Guard', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('XinZhao', "basic_attack"): dict(description="A knight's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Yasuo', 'evasion'): dict(description='Steel Tempest', how_to_use='Q — tap to buff.'),
    ('Yasuo', 'wind_arrow'): dict(description='Wind Wall', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Yasuo', 'swift_buff'): dict(description='Sweeping Blade', how_to_use='E — tap to buff.'),
    ('Yasuo', 'tempest'): dict(description='Last Breath', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Yasuo', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Yone', 'evasion'): dict(description='Mortal Steel', how_to_use='Q — tap to buff.'),
    ('Yone', 'swift_buff'): dict(description='Spirit Cleave', how_to_use='W — tap to buff.'),
    ('Yone', 'wind_arrow'): dict(description='Soul Unbound', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Yone', 'tempest'): dict(description='Fate Sealed', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Yone', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Yorick', 'soul_drain'): dict(description='Last Rites', how_to_use='Q — tap to cast in facing; hold to aim.'),
    ('Yorick', 'dark_curse'): dict(description='Dark Procession', how_to_use='W — tap to curse the nearest foe.'),
    ('Yorick', 'shield_ward'): dict(description='Mourning Mist', how_to_use='E — tap to buff.'),
    ('Yorick', 'void_nova'): dict(description='Eulogy of the Isles', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Yorick', "basic_attack"): dict(description="A undead's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Yuumi', 'swift_buff'): dict(description='Prowling Projectile', how_to_use='Q — tap to buff.'),
    ('Yuumi', 'evasion'): dict(description='You and Me!', how_to_use='W — tap to buff.'),
    ('Yuumi', 'wind_arrow'): dict(description='Zoomies', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Yuumi', 'tempest'): dict(description='Final Chapter', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Yuumi', "basic_attack"): dict(description="A yordle's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Zac', 'shield_ward'): dict(description='Stretching Strikes', how_to_use='Q — tap to buff.'),
    ('Zac', 'dark_aoe'): dict(description='Unstable Matter', how_to_use='W — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Zac', 'soul_drain'): dict(description='Elastic Slingshot', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Zac', 'void_nova'): dict(description="Let's Bounce!", how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Zac', "basic_attack"): dict(description="A construct's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Zed', 'gust'): dict(description='Razor Shuriken', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Zed', 'evasion'): dict(description='Living Shadow', how_to_use='W — tap to buff.'),
    ('Zed', 'wind_arrow'): dict(description='Shadow Slash', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Zed', 'tempest'): dict(description='Death Mark', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Zed', "basic_attack"): dict(description="A rogue's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Zeri', 'shield_ward'): dict(description='Burst Fire', how_to_use='Q — tap to buff.'),
    ('Zeri', 'dark_curse'): dict(description='Ultrashock Laser', how_to_use='W — tap to curse the nearest foe.'),
    ('Zeri', 'dark_bolt'): dict(description='Spark Surge', how_to_use='E — tap to cast in facing; hold to aim.'),
    ('Zeri', 'void_nova'): dict(description='Lightning Crash', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Zeri', "basic_attack"): dict(description="A archer's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Ziggs', 'dark_aoe'): dict(description='Bouncing Bomb', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Ziggs', 'soul_drain'): dict(description='Satchel Charge', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Ziggs', 'dark_curse'): dict(description='Hexplosive Minefield', how_to_use='E — tap to curse the nearest foe.'),
    ('Ziggs', 'void_nova'): dict(description='Mega Inferno Bomb', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Ziggs', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Zilean', 'dark_curse'): dict(description='Time Bomb', how_to_use='Q — tap to curse the nearest foe.'),
    ('Zilean', 'dark_bolt'): dict(description='Rewind', how_to_use='W — tap to cast in facing; hold to aim.'),
    ('Zilean', 'shield_ward'): dict(description='Time Warp', how_to_use='E — tap to buff.'),
    ('Zilean', 'void_nova'): dict(description='Chronoshift', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Zilean', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Zoe', 'judgement_aoe'): dict(description='Paddle Star', how_to_use='Q — full energy; hits all enemies on screen.'),
    ('Zoe', 'blessing'): dict(description='Spell Thief', how_to_use='W — tap to buff.'),
    ('Zoe', 'light_slash'): dict(description='Sleepy Trouble Bubble', how_to_use='E — tap to strike in facing; hold to aim.'),
    ('Zoe', 'light_hymn'): dict(description='Portal Jump', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Zoe', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
    ('Zyra', 'wind_aoe'): dict(description='Deadly Spines', how_to_use='Q — tap to cast (AoE all enemies); hold to aim the radius.'),
    ('Zyra', 'wind_arrow'): dict(description='Rampant Growth', how_to_use='W — tap to strike in facing; hold to aim.'),
    ('Zyra', 'evasion'): dict(description='Grasping Roots', how_to_use='E — tap to buff.'),
    ('Zyra', 'tempest'): dict(description='Stranglethorns', how_to_use='U/Space — full energy; hits all enemies on screen.'),
    ('Zyra', "basic_attack"): dict(description="A mage's strike.", how_to_use='J — tap to strike in facing; hold to aim.'),
}


def _build_hero_assets():
    """Assemble HERO_ASSETS from the combat dicts + the per-hero text above.
    References — does not duplicate — SKILLS_DB / ULTIMATE_VARIANTS /
    HERO_SIGNATURE / CONSTELLATION_PERKS / HERO_LORE / PASSIVES_DB."""
    assets = {}
    for h in HEROES_DB:
        hid = h["id"]
        active = [s for s in h["skills"] if s != "basic_attack"]   # 2-3 ids
        ult = h.get("ultimate")
        # skills list = 3 active + ultimate + basic_attack (real skills only)
        skill_ids = list(active) + ([ult] if ult else []) + ["basic_attack"]
        skills_list = []
        for sid in skill_ids:
            if not sid or sid not in SKILLS_DB:
                continue
            sk = SKILLS_DB[sid]
            entry = {
                "id": sid,
                "name": sk["name"],
                "type": sk["type"],
                # read the post-processed `category` field (single source — the
                # _SKILL_TYPE_CATEGORY post-process at line ~643 sets it on every
                # skill; don't re-derive from a second map, which disagreed on
                # `revive`).
                "category": sk.get("category") or _SKILL_CATEGORY.get(sk["type"], sk["type"].title()),
                "cost": sk.get("cost", 0),
            }
            txt = _HERO_SKILL_TEXT.get((hid, sid))
            if txt:
                entry["description"] = txt["description"]
                entry["how_to_use"] = txt["how_to_use"]
            else:
                entry["description"] = sk.get("desc", "")
                entry["how_to_use"] = ""
            skills_list.append(entry)
        # signature passive (name + desc from PASSIVES_DB via HERO_SIGNATURE)
        sig_id = HERO_SIGNATURE.get(hid)
        sig = None
        if sig_id and sig_id in PASSIVES_DB:
            sp = PASSIVES_DB[sig_id]
            sig = {"name": sp["name"], "desc": sp["desc"]}
        # constellation: 6 perks (name + desc) from the role/hero template
        const = [{"name": p["name"], "desc": p["desc"]}
                 for p in hero_constellation_perks(h)]
        assets[hid] = {
            "name": h["name"], "title": h["title"],
            "element": h["element"], "role": h["role"],
            "lore": HERO_LORE.get(hid, {}),
            "skills": skills_list,
            "signature": sig,
            "constellation": const,
            "ultimate": ULTIMATE_VARIANTS.get(hid),
        }
    return assets


HERO_ASSETS = _build_hero_assets()


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
# Equipment
#   slot: weapon, armor, accessory
#   stat bonuses added to hero base stats
# ---------------------------------------------------------------------------
EQUIPMENT_DB = {
    # weapons -> atk
    "rusty_sword":  dict(name="Rusty Sword",   slot="weapon",    rarity="R",  stats=dict(atk=6),  price=120, sell=40),
    "steel_blade":  dict(name="Steel Blade",   slot="weapon",    rarity="SR", stats=dict(atk=14), price=400, sell=140),
    "dragon_fang":  dict(name="Dragon Fang",   slot="weapon",    rarity="SSR",stats=dict(atk=24), price=1800, sell=480),
    "mage_rod":     dict(name="Mage Rod",      slot="weapon",    rarity="SR", stats=dict(atk=10, mp=10), price=450, sell=160),
    # armor -> hp, defn
    "leather_armor":dict(name="Leather Armor", slot="armor",     rarity="R",  stats=dict(hp=20, defn=4), price=120, sell=40),
    "plate_mail":   dict(name="Plate Mail",    slot="armor",     rarity="SR", stats=dict(hp=40, defn=10), price=420, sell=150),
    "aether_vest":  dict(name="Aether Vest",   slot="armor",     rarity="SSR",stats=dict(hp=70, defn=18), price=1900, sell=520),
    # accessory -> spd / mp / misc
    "swift_boots":  dict(name="Swift Boots",   slot="accessory", rarity="R",  stats=dict(spd=4), price=120, sell=40),
    "mana_pendant": dict(name="Mana Pendant",  slot="accessory", rarity="SR", stats=dict(mp=14, atk=4), price=440, sell=160),
    "hero_crest":   dict(name="Hero Crest",    slot="accessory", rarity="SSR",stats=dict(spd=5, atk=8, hp=30), price=2000, sell=560),
    # --- new equipment (Phase B) ---
    "inferno_blade":dict(name="Inferno Blade", slot="weapon",    rarity="SSR",stats=dict(atk=28, hp=20), price=2400, sell=640),
    "frost_staff":  dict(name="Frost Staff",   slot="weapon",    rarity="SR", stats=dict(atk=12, mp=12), price=480, sell=170),
    "void_blade":   dict(name="Void Blade",    slot="weapon",    rarity="SSR",stats=dict(atk=26, spd=4), price=2200, sell=600),
    "guardian_aegis":dict(name="Guardian Aegis",slot="armor",    rarity="SSR",stats=dict(hp=90, defn=22), price=2500, sell=680),
    "shadow_cloak": dict(name="Shadow Cloak",  slot="armor",     rarity="SR", stats=dict(hp=30, defn=12, spd=3), price=520, sell=190),
    "berserker_ring":dict(name="Berserker Ring",slot="accessory",rarity="SR", stats=dict(atk=10, spd=3), price=560, sell=200),
    "sage_amulet":  dict(name="Sage Amulet",   slot="accessory", rarity="SSR",stats=dict(mp=20, atk=6, hp=40), price=2500, sell=680),
}

# Equipment set bonuses: equip a matching set across the 3 slots for a bonus.
# A "set" is keyed by a prefix on the item id. Bonuses stack onto the hero.
EQUIPMENT_SETS = {
    "ember":  dict(name="Ember Warden",  items=("inferno_blade", "aether_vest", "berserker_ring"),
                  bonus=dict(atk_pct=0.10, hp=30, crit_dmg=0.15), desc="+10% ATK, +30 HP, +15% crit dmg",
                  bonus2=dict(atk_pct=0.05)),
    "frost":  dict(name="Aegis Sovereign", items=("frost_staff", "guardian_aegis", "sage_amulet"),
                  bonus=dict(defn_pct=0.12, hp=60), desc="+12% DEF, +60 HP",
                  bonus2=dict(defn_pct=0.05)),
    "void":   dict(name="Voidwalker",   items=("void_blade", "shadow_cloak", "mana_pendant"),
                  bonus=dict(atk_pct=0.06, crit=0.10, crit_dmg=0.20), desc="+6% ATK, +10% crit, +20% crit dmg",
                  bonus2=dict(atk_pct=0.03)),
    "hero":   dict(name="Hero's Valor", items=("dragon_fang", "plate_mail", "hero_crest"),
                  bonus=dict(atk_pct=0.06, hp=40, defn=8), desc="+6% ATK, +40 HP, +8 DEF",
                  bonus2=dict(hp=20)),
}

def equipment_set_bonus(equipped_ids):
    """Return (set_name, bonus_dict) for a complete set (3/3) or a 2-piece
    partial bonus, or (None, {})."""
    eqset = set(equipped_ids)
    for sid, sdef in EQUIPMENT_SETS.items():
        items = set(sdef["items"])
        if items.issubset(eqset):
            return sdef["name"], dict(sdef["bonus"])
        if len(items & eqset) >= 2 and sdef.get("bonus2"):
            return sdef["name"] + " (2/3)", dict(sdef["bonus2"])
    return None, {}

# ---------------------------------------------------------------------------
# Consumables (inventory items)
# ---------------------------------------------------------------------------
CONSUMABLES_DB = {
    "hp_potion":    dict(name="HP Potion",     type="heal_hp",   power=60,  price=40,  sell=8,  desc="Restore 60 HP to one hero."),
    "mp_potion":    dict(name="MP Potion",     type="heal_mp",   power=40,  price=30,  sell=10, desc="Restore 40 MP to one hero."),
    "full_elixir":  dict(name="Full Elixir",   type="heal_full", power=0,   price=200, sell=40, desc="Fully restore HP & MP of one hero."),
    "revive_scroll":dict(name="Revive Scroll", type="revive",    power=0.5, price=300, sell=60, desc="Revive a fallen ally at 50% HP."),
    "bomb":         dict(name="Bomb",          type="damage",    power=80,  price=80,  sell=16, desc="Deal 80 damage to one enemy."),
    # --- new consumables (Phase B) ---
    "mega_potion":  dict(name="Mega Potion",   type="heal_hp",   power=200, price=100, sell=24, desc="Restore 200 HP to one hero."),
    "ether":        dict(name="Ether",         type="heal_mp",   power=80,  price=120, sell=28, desc="Restore 80 MP to one hero."),
    "mega_bomb":    dict(name="Mega Bomb",     type="damage",    power=240, price=220, sell=44, desc="Deal 240 damage to one enemy."),
}

# ---------------------------------------------------------------------------
# Shop offers (gems for gold, equipment, consumables)
# ---------------------------------------------------------------------------
SHOP_GEMS = [
    dict(id="gems_small",  name="100 Gems",  gems=100,  price=800),
    dict(id="gems_medium", name="600 Gems",  gems=600,  price=4200),
    dict(id="gems_large",  name="1500 Gems", gems=1500, price=9500),
]

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
        "name": "Elder Mira",
        "quest_id": "plains_boss",
        "dialogue": [
            "Welcome, traveler. The meadows were once at peace.",
            "Then the Goblin King rose in the east, crowned in rust.",
            "He drives his kin to burn the farms each new moon.",
            "Slay him, and I will open my shard-vault to you.",
        ],
    },
    "forest": {
        "name": "Ranger Thorne",
        "quest_id": "forest_boss",
        "dialogue": [
            "Stay quiet. The Woods have ears, and they bite.",
            "The Hydra coils where the old watchtower fell.",
            "Each head it grows spreads the rot a league further.",
            "Cut all its heads, and the green may yet return.",
        ],
    },
    "cave": {
        "name": "Keeper Vesh",
        "quest_id": "cave_boss",
        "dialogue": [
            "Mind the dark. The crystals used to sing, once.",
            "Now the Frost Titan sleeps in the deep gallery.",
            "Its breath froze the river solid, then the keepers.",
            "Melt its heart, and the caverns will breathe again.",
        ],
    },
    "castle": {
        "name": "Sir Caelan",
        "quest_id": "castle_boss",
        "dialogue": [
            "Halt. The citadel is no place for the living now.",
            "The Dragon claimed the throne the day the king fell.",
            "Its flames guard the banner no one dares to raise.",
            "Put it down, and I will name you the rightful heir.",
        ],
    },
    "void": {
        "name": "Oracle Lyra",
        "quest_id": "void_boss",
        "dialogue": [
            "You came. Few do. Fewer leave with their name intact.",
            "The Demon King waits where the world's edge frays.",
            "He was a hero once - the rifts were his last mercy.",
            "End him, and the Cycle may turn at last. Or break.",
        ],
    },
}

# ---------------------------------------------------------------------------
# Story quest chain (Task E2) — the main quest: 5 biome-boss quests + 1
# final-boss quest, chained plains -> forest -> cave -> castle -> void ->
# demon_king. Each quest's `giver` is the biome whose NPC offers it (matches
# NPCS[biome]["quest_id"]); `objective` is the boss it asks the player to
# defeat; `reward` is the payout on completion (gems + shards); `lore` is a
# one-line flavour beat. The chain order is the list order: a quest is
# "available" when the previous quest in the list is "complete" (the first
# quest, plains_boss, is available from the start). The boss cell for a biome
# (column 9 of that row) is SEALED until the biome's quest is "active"
# (accepted via the NPC dialogue — see world_scene._advance_dialogue); the
# final boss (demon_king at 9,4) is sealed until all 5 biome-boss quests are
# complete (the chain). The boss-defeat handler
# (world_scene._on_enemy_death) marks the biome-boss quest "complete" + the
# next quest becomes available (the next NPC can now give it).
# ---------------------------------------------------------------------------
STORY_QUESTS = [
    {"id": "plains_boss", "name": "The Goblin King", "giver": "plains",
     "objective": "Defeat the Goblin King in the plains (row 0, east edge).",
     "reward": {"gems": 50, "shards": 5},
     "lore": "The farms burn each new moon. Break the crown that lights them."},
    {"id": "forest_boss", "name": "The Forest Warden", "giver": "forest",
     "objective": "Defeat the Hydra where the old watchtower fell (row 1, east edge).",
     "reward": {"gems": 80, "shards": 8},
     "lore": "Each head it grows spreads the rot a league further. Cut them all."},
    {"id": "cave_boss", "name": "The Frost Titan", "giver": "cave",
     "objective": "Defeat the Frost Titan in the deep gallery (row 2, east edge).",
     "reward": {"gems": 120, "shards": 12},
     "lore": "Its breath froze the river solid, then the keepers. Melt its heart."},
    {"id": "castle_boss", "name": "The Dragon", "giver": "castle",
     "objective": "Defeat the Dragon on the fallen throne (row 3, east edge).",
     "reward": {"gems": 160, "shards": 16},
     "lore": "Its flames guard the banner no one dares to raise. Put it down."},
    {"id": "void_boss", "name": "The Riftbreaker", "giver": "void",
     "objective": "Defeat the Demon King's herald at the world's edge (row 4, east edge).",
     "reward": {"gems": 200, "shards": 20},
     "lore": "He was a hero once. The rifts were his last mercy. End him."},
    {"id": "demon_king", "name": "The Demon King", "giver": "void",
     "objective": "Defeat the Demon King at the world's end (9,4).",
     "reward": {"gems": 400, "shards": 40},
     "lore": "End him, and the Cycle may turn at last. Or break."},
]

# Fast lookups derived from STORY_QUESTS so callers don't re-derive on every
# _load_map / boss-defeat. STORY_QUEST_BY_ID is the dict {id -> quest};
# STORY_QUEST_ORDER is the chain order (the list of ids, plains -> demon_king)
# so the "next quest" is the one at index+1. STORY_BIOME_QUEST maps a biome
# (the giver) to its biome-boss quest id (the 5 biome-boss quests only; the
# final demon_king quest shares the void giver but is gated on the chain, not
# on the void NPC). The final-boss quest id is exported as STORY_FINAL_QUEST
# so the boss-defeat handler can detect it without a magic string.
STORY_QUEST_BY_ID = {q["id"]: q for q in STORY_QUESTS}
STORY_QUEST_ORDER = [q["id"] for q in STORY_QUESTS]
STORY_BIOME_QUEST = {q["giver"]: q["id"]
                     for q in STORY_QUESTS
                     if q["id"] in {v["quest_id"] for v in NPCS.values()}}
STORY_FINAL_QUEST = "demon_king"
