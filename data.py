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
ELEMENTS = ["fire", "water", "wind", "light", "dark"]

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
EFFECT_NAMES = {
    "poison":   ("Poison",  (120, 200, 80)),
    "burn":     ("Burn",    (255, 140, 60)),
    "regen":    ("Regen",   (120, 240, 160)),
    "atk_up":   ("ATK Up",  (255, 200, 80)),
    "def_up":   ("DEF Up",  (140, 180, 255)),
    "atk_down": ("ATK Dn",  (200, 120, 200)),
    "def_down": ("DEF Dn",  (180, 120, 160)),
    "spd_up":   ("SPD Up",  (180, 240, 220)),
    "stun":     ("Stun",    (255, 230, 90)),
    "shield":   ("Shield",  (200, 230, 255)),
    "freeze":   ("Freeze",  (160, 220, 255)),
    "bleed":    ("Bleed",   (200, 60, 80)),
    "taunt":    ("Taunt",   (255, 180, 80)),
    "reflect":  ("Reflect", (180, 220, 255)),
    "broken":   ("Broken",  (255, 200, 90)),
}

# ---------------------------------------------------------------------------
# Combat tuning
# ---------------------------------------------------------------------------
BASE_CRIT_CHANCE = 0.08      # base chance any hit can crit
CRIT_MULT = 1.6              # crit damage multiplier
COMBO_BONUS_PER = 0.04       # +4% damage per combo step
COMBO_MAX = 10
DEFEND_MITIGATION = 0.45     # defending reduces incoming damage by this fraction

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
ENERGY_REGEN_PCT = 0.04   # passive energy regen: 4% of max per second out of
                          # combat (~4.8/s at max 120 -> full bar in ~25s out of
                          # combat, ~2.4/s in combat). Skills recover + mana
                          # increases without needing to land a hit.

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
ABILITY_KEYS = ["Q", "W", "E", "R"]

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
}

# Per-hero passive assignment (one each, flavored to their role/element).
# destruction -> lifesteal/adrenaline, hunt -> crit, erudition -> energy,
# harmony -> regen, nihility -> thorns, preservation -> shield, abundance -> regen.
HERO_PASSIVES = {
    "aria": "p_adrenaline", "kael": "p_lifesteal", "mira": "p_energy",
    "zephyr": "p_crit", "luna": "p_thorns", "pyra": "p_energy",
    "lyra": "p_regen", "thorne": "p_shield_low", "sera": "p_regen",
    "rune": "p_energy", "blaze": "p_adrenaline", "nami": "p_regen",
    "gale": "p_energy", "vex": "p_crit", "ember": "p_lifesteal",
    "tide": "p_shield_low", "zephyra": "p_crit", "selene": "p_adrenaline",
    "nox": "p_lifesteal", "cinder": "p_lifesteal", "mist": "p_swift",
    "sol": "p_regen", "gaia": "p_thorns", "echo": "p_energy", "raven": "p_crit",
}

def hero_passive(hero_id):
    pid = HERO_PASSIVES.get(hero_id)
    if not pid:
        return None
    return PASSIVES_DB.get(pid)

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
TOUGHNESS_HIT_BASE = 10            # every hit shaves this much toughness
TOUGHNESS_HIT_WEAK = 30            # a weakness-element hit shaves this much

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
                        desc="Curse an enemy: burn + ATK down.", debuff=["burn", "atk_down"], dur=3),
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
                        desc="Curse an enemy: poison + ATK down.", debuff=["poison", "atk_down"], dur=3),
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
                        desc="Inflict bleed + DEF down.", debuff=["bleed", "def_down"], dur=3),
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
}

# Boss enemies (the big arena fights in the open world). Maps a boss id to the
# ultimate skill it unleashes below 50% HP. Also the canonical set of boss ids.
BOSS_ULT = {
    "dragon":      "hellfire",
    "demonking":   "abyssal_wave",
    "frosttitan":  "frost_cataclysm",
    "embertyrant": "storm_of_embers",
    "hydra":       "frost_cataclysm",
    "golem":       "abyssal_wave",
}
BOSS_IDS = set(BOSS_ULT.keys())
BOSS_ULT_HP_FRAC = 0.5   # boss uses ultimate when HP drops below this

# Boss phase patterns — which telegraphed patterns a boss uses at each phase.
# Phase 1 (100-66% HP): no special pattern (just the basic strike + the 50% ult).
# Phase 2 (66-33% HP): "charge" — telegraph a line to the player, then dash.
# Phase 3 (33-0% HP): adds "slam" — an expanding ring burst the player dodges.
# Keyed per boss id so each boss fights differently; bosses without an entry
# fall back to the default pattern set for their phase.
BOSS_PATTERNS = {
    "dragon":      {2: ["charge"],            3: ["charge", "slam"]},
    "demonking":   {2: ["charge", "slam"],    3: ["charge", "slam"]},
    "frosttitan":  {2: ["slam"],              3: ["charge", "slam"]},
    "embertyrant": {2: ["charge"],            3: ["charge", "slam"]},
    "hydra":       {2: ["slam"],              3: ["charge", "slam"]},
    "golem":       {2: ["charge"],            3: ["charge", "slam"]},
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
# Hero definitions
#   id, name, title, element, rarity, role, base stats, skills, ultimate
# Stats: hp, atk, defn, spd, mp
# ---------------------------------------------------------------------------
HEROES_DB = [
    dict(id="aria",   name="Aria",   title="Knight of Dawn",  element="light", rarity="SSR", role="destruction",
         stats={"hp": 120, "atk": 24, "defn": 18, "spd": 14, "mp": 30},
         skills=["light_slash", "light_heal", "blessing", "basic_attack"],
         ultimate="light_hymn"),
    dict(id="kael",   name="Kael",   title="Ember Warrior",    element="fire", rarity="SSR", role="destruction",
         stats={"hp": 130, "atk": 26, "defn": 16, "spd": 13, "mp": 28},
         skills=["fire_slash", "inferno", "fire_bolt", "basic_attack"],
         ultimate="meteor"),
    dict(id="mira",   name="Mira",   title="Tide Caller",      element="water", rarity="SSR", role="erudition",
         stats={"hp": 110, "atk": 22, "defn": 15, "spd": 15, "mp": 36},
         skills=["water_bolt", "water_heal", "tidal_wave", "basic_attack"],
         ultimate="tsunami"),
    dict(id="zephyr", name="Zephyr", title="Sky Ranger",       element="wind", rarity="SSR", role="hunt",
         stats={"hp": 108, "atk": 25, "defn": 13, "spd": 18, "mp": 28},
         skills=["wind_arrow", "wind_aoe", "swift_buff", "basic_attack"],
         ultimate="tempest"),
    dict(id="luna",   name="Luna",   title="Nightshade",       element="dark", rarity="SSR", role="nihility",
         stats={"hp": 112, "atk": 27, "defn": 14, "spd": 16, "mp": 30},
         skills=["dark_bolt", "dark_curse", "dark_aoe", "basic_attack"],
         ultimate="void_nova"),
    dict(id="pyra",   name="Pyra",   title="Crimson Empress",  element="fire", rarity="SSR", role="nihility",
         stats={"hp": 122, "atk": 27, "defn": 15, "spd": 16, "mp": 32},
         skills=["fire_curse", "fire_bolt", "inferno", "basic_attack"],
         ultimate="meteor"),
    dict(id="lyra",   name="Lyra",   title="Moon Oracle",      element="light", rarity="SSR", role="abundance",
         stats={"hp": 108, "atk": 21, "defn": 15, "spd": 16, "mp": 42},
         skills=["light_heal", "blessing", "revive", "basic_attack"],
         ultimate="light_hymn"),
    dict(id="thorne", name="Thorne", title="Stoneguard",       element="wind", rarity="SR", role="preservation",
         stats={"hp": 150, "atk": 20, "defn": 24, "spd": 9, "mp": 24},
         skills=["wind_arrow", "shield_ward", "basic_attack"],
         ultimate="tempest"),
    dict(id="sera",   name="Sera",   title="Cleric of Light",  element="light", rarity="SR", role="abundance",
         stats={"hp": 102, "atk": 18, "defn": 16, "spd": 13, "mp": 40},
         skills=["sanctuary", "blessing", "revive", "basic_attack"],
         ultimate="light_hymn"),
    dict(id="rune",   name="Rune",   title="Void Mage",        element="dark", rarity="SR", role="erudition",
         stats={"hp": 98, "atk": 24, "defn": 12, "spd": 15, "mp": 38},
         skills=["dark_bolt", "dark_curse", "dark_aoe", "basic_attack"],
         ultimate="void_nova"),
    dict(id="blaze",  name="Blaze",  title="Flame Berserker",  element="fire", rarity="SR", role="destruction",
         stats={"hp": 125, "atk": 25, "defn": 14, "spd": 14, "mp": 24},
         skills=["fire_slash", "fire_bolt", "basic_attack"],
         ultimate="meteor"),
    dict(id="nami",   name="Nami",   title="Sea Oracle",       element="water", rarity="SR", role="harmony",
         stats={"hp": 105, "atk": 18, "defn": 17, "spd": 14, "mp": 38},
         skills=["water_bolt", "water_heal", "tidal_wave", "basic_attack"],
         ultimate="tsunami"),
    dict(id="gale",   name="Gale",   title="Wind Dancer",      element="wind", rarity="R", role="erudition",
         stats={"hp": 100, "atk": 21, "defn": 12, "spd": 16, "mp": 30},
         skills=["gust", "wind_aoe", "evasion", "basic_attack"],
         ultimate="tempest"),
    dict(id="vex",    name="Vex",    title="Shade Rogue",      element="dark", rarity="R", role="hunt",
         stats={"hp": 102, "atk": 22, "defn": 11, "spd": 17, "mp": 26},
         skills=["dark_bolt", "dark_curse", "basic_attack"],
         ultimate="void_nova"),
    # --- new heroes (Phase B) ---
    dict(id="ember",  name="Ember",  title="Ashen Revenant",   element="fire", rarity="SSR", role="destruction",
         stats={"hp": 135, "atk": 27, "defn": 17, "spd": 14, "mp": 30},
         skills=["fire_strike", "inferno", "phoenix", "basic_attack"],
         ultimate="meteor"),
    dict(id="tide",   name="Tide",   title="Glacier Warden",   element="water", rarity="SSR", role="preservation",
         stats={"hp": 140, "atk": 23, "defn": 20, "spd": 12, "mp": 34},
         skills=["water_bolt", "frost_nova", "tide_shield", "basic_attack"],
         ultimate="tsunami"),
    dict(id="zephyra",name="Zephyra",title="Storm Herald",     element="wind", rarity="SSR", role="hunt",
         stats={"hp": 112, "atk": 26, "defn": 14, "spd": 19, "mp": 30},
         skills=["wind_arrow", "gust", "evasion", "basic_attack"],
         ultimate="tempest"),
    dict(id="selene", name="Selene", title="Dawnbringer",      element="light", rarity="SSR", role="hunt",
         stats={"hp": 118, "atk": 25, "defn": 17, "spd": 15, "mp": 38},
         skills=["light_slash", "sanctuary", "blessing", "basic_attack"],
         ultimate="judgement_aoe"),
    dict(id="nox",    name="Nox",    title="Eclipse Lord",     element="dark", rarity="SSR", role="destruction",
         stats={"hp": 118, "atk": 29, "defn": 15, "spd": 16, "mp": 30},
         skills=["soul_drain", "dark_bolt", "dark_aoe", "basic_attack"],
         ultimate="death_coil"),
    dict(id="cinder", name="Cinder", title="Cinder Knight",    element="fire", rarity="SR", role="destruction",
         stats={"hp": 128, "atk": 24, "defn": 16, "spd": 13, "mp": 26},
         skills=["fire_strike", "fire_bolt", "basic_attack"],
         ultimate="meteor"),
    dict(id="mist",   name="Mist",   title="Veil Dancer",     element="wind", rarity="SR", role="harmony",
         stats={"hp": 104, "atk": 22, "defn": 14, "spd": 18, "mp": 30},
         skills=["wind_arrow", "evasion", "shield_ward", "basic_attack"],
         ultimate="tempest"),
    dict(id="sol",    name="Sol",    title="Sun Priest",       element="light", rarity="R", role="abundance",
         stats={"hp": 98,  "atk": 18, "defn": 14, "spd": 14, "mp": 32},
         skills=["light_heal", "blessing", "basic_attack"],
         ultimate="light_hymn"),
    # --- new heroes (Phase C: status-oriented kits) ---
    dict(id="gaia",  name="Gaia",  title="Earthwarden",      element="wind", rarity="SR", role="preservation",
         stats={"hp": 160, "atk": 19, "defn": 26, "spd": 8,  "mp": 26},
         skills=["taunt_skill", "shield_ward", "gust", "basic_attack"],
         ultimate="tempest"),
    dict(id="echo",  name="Echo",  title="Mirror Sage",      element="water", rarity="SR", role="harmony",
         stats={"hp": 110, "atk": 22, "defn": 16, "spd": 14, "mp": 36},
         skills=["water_bolt", "reflect_ward", "tide_shield", "basic_attack"],
         ultimate="tsunami"),
    dict(id="raven", name="Raven", title="Blood Reaper",     element="dark", rarity="SSR", role="nihility",
         stats={"hp": 118, "atk": 30, "defn": 14, "spd": 17, "mp": 30},
         skills=["rupture", "soul_drain", "dark_aoe", "basic_attack"],
         ultimate="death_coil"),
]

# Quick lookup
HERO_BY_ID = {h["id"]: h for h in HEROES_DB}

# ---------------------------------------------------------------------------
# Hero lore: bio (<=120 chars), quote (<=80 chars), personality (one word).
# Pure data shown in the codex tooltip + hero-detail screen.
# ---------------------------------------------------------------------------
HERO_LORE = {
    "aria":    {"bio": "A knight of the fallen dawn, sworn to the light after her order's ruin.",
                "quote": "Dawn breaks for everyone. Even you.",
                "personality": "stoic"},
    "kael":    {"bio": "A warrior of the ember wars who carries the fire that burned his city.",
                "quote": "Stand in my fire and we'll see who burns first.",
                "personality": "fierce"},
    "mira":    {"bio": "A scholar of drowned empires who reads the tides like open books.",
                "quote": "The tide remembers everything. So do I.",
                "personality": "contemplative"},
    "zephyr":  {"bio": "A ranger of the open sky who never touches the ground if he can help it.",
                "quote": "The sky has no ceiling. Neither do I.",
                "personality": "restless"},
    "luna":    {"bio": "An assassin of the night court who poisons dreams and silences kings.",
                "quote": "Dream of me. I'll be the last thing you see.",
                "personality": "cold"},
    "pyra":    {"bio": "A tyrant burned alive who returned as flame, crowned in living fire.",
                "quote": "I was crowned in fire. Bow or burn.",
                "personality": "proud"},
    "lyra":    {"bio": "An oracle who reads the moon's face and speaks for the silent dead.",
                "quote": "The moon has already spoken. Listen.",
                "personality": "serene"},
    "thorne":  {"bio": "A wall of stone and patience who stood for a thousand years.",
                "quote": "I have stood for centuries. I can stand for you.",
                "personality": "steadfast"},
    "sera":    {"bio": "A healer who mends wounds with light and never asks the price.",
                "quote": "Let the light mend what you cannot.",
                "personality": "gentle"},
    "rune":    {"bio": "A scholar of the void who counts the spaces between the stars.",
                "quote": "I have counted the void. It is patient.",
                "personality": "curious"},
    "blaze":   {"bio": "A berserker who burns hotter with every wound he takes.",
                "quote": "The hotter I burn, the less I feel.",
                "personality": "reckless"},
    "nami":    {"bio": "A tide-reader who sings the sea to sleep and wakes it again.",
                "quote": "Sleep now. The tide will wake you when it's time.",
                "personality": "calm"},
    "gale":    {"bio": "A wanderer who speaks the wind's language and forgets to land.",
                "quote": "The wind doesn't wait. Neither do I.",
                "personality": "flighty"},
    "vex":     {"bio": "A rogue of the shade courts who slips through locked doors.",
                "quote": "You didn't see me. You never do.",
                "personality": "sly"},
    "ember":   {"bio": "A revenant who crawled out of the ash, still burning, still owed.",
                "quote": "I crawled out of the ash. I'm still owed.",
                "personality": "unyielding"},
    "tide":    {"bio": "A warden of the frozen deep who guards what the sea forgot.",
                "quote": "The deep keeps its own. I keep the deep.",
                "personality": "glacial"},
    "zephyra": {"bio": "A herald of storms who runs ahead of the lightning.",
                "quote": "Outrun the storm. I am the storm.",
                "personality": "swift"},
    "selene":  {"bio": "A hunter who chases the dawn across the edge of the world.",
                "quote": "The dawn runs. I run faster.",
                "personality": "relentless"},
    "nox":     {"bio": "A lord of eclipses who rules the hour the sun forgets.",
                "quote": "The sun forgets this hour. I do not.",
                "personality": "imperious"},
    "cinder":  {"bio": "A knight of the cinder wars who kept burning after the truce.",
                "quote": "The truce is ash. So are you.",
                "personality": "grim"},
    "mist":    {"bio": "A dancer of the veils who is never where the eye believes.",
                "quote": "You saw me. You were mistaken.",
                "personality": "elusive"},
    "sol":     {"bio": "A priest of the noon sun who gives light and asks nothing.",
                "quote": "Take the light. I have enough to spare.",
                "personality": "warm"},
    "gaia":    {"bio": "The earthwarden who holds the land together when it wants to break.",
                "quote": "The land breaks. I hold it. I hold you.",
                "personality": "patient"},
    "echo":    {"bio": "A sage of mirrors who remembers what you have not yet said.",
                "quote": "I said what you were about to. I always do.",
                "personality": "cryptic"},
    "raven":   {"bio": "A reaper cursed to take a soul for every one he saves.",
                "quote": "One soul saved, one soul taken. The ledger balances.",
                "personality": "morbid"},
}

# ---------------------------------------------------------------------------
# Enemy definitions
# ---------------------------------------------------------------------------
ENEMIES_DB = {
    "slime":    dict(name="Slime",     element="wind",   hp=60,  atk=14, defn=6,  spd=8,  xp=20, gold=15,
                    skills=["basic_attack"], weakness="fire", toughness=40),
    "goblin":   dict(name="Goblin",    element="fire",   hp=80,  atk=18, defn=8,  spd=11, xp=28, gold=22,
                    skills=["basic_attack", "fire_bolt"], weakness="water", toughness=50),
    "bat":      dict(name="Cave Bat",  element="dark",   hp=55,  atk=16, defn=5,  spd=16, xp=24, gold=18,
                    skills=["basic_attack", "dark_bolt"], weakness="light", toughness=35),
    "skeleton": dict(name="Skeleton", element="light",  hp=90,  atk=20, defn=10, spd=9,  xp=32, gold=26,
                    skills=["basic_attack", "light_slash"], weakness="dark", toughness=55),
    "wolf":     dict(name="Dire Wolf", element="wind",   hp=100, atk=22, defn=9,  spd=15, xp=36, gold=30,
                    skills=["basic_attack", "wind_arrow"], weakness="fire", toughness=60),
    "orc":      dict(name="Orc Brute", element="fire",   hp=140, atk=26, defn=14, spd=8,  xp=48, gold=40,
                    skills=["basic_attack", "fire_slash"], weakness="water", toughness=80),
    "golem":    dict(name="Stone Golem", element="wind", hp=180, atk=24, defn=22, spd=6,  xp=60, gold=50,
                    skills=["basic_attack", "wind_aoe"], weakness="fire", toughness=100),
    "wraith":   dict(name="Wraith",    element="dark",   hp=120, atk=28, defn=12, spd=14, xp=55, gold=45,
                    skills=["basic_attack", "dark_bolt", "dark_curse"], weakness="light", toughness=70),
    "dragon":   dict(name="Flame Dragon", element="fire", hp=340, atk=34, defn=20, spd=12, xp=120, gold=120,
                    skills=["basic_attack", "fire_bolt", "inferno"], weakness="water", toughness=160),
    "demonking":dict(name="Demon King", element="dark",  hp=520, atk=38, defn=24, spd=13, xp=300, gold=300,
                    skills=["basic_attack", "dark_bolt", "dark_aoe", "dark_curse"], weakness="light", toughness=220),
    # --- new enemies (Phase B) ---
    "imp":      dict(name="Imp",         element="fire",   hp=70,  atk=20, defn=6,  spd=14, xp=30, gold=24,
                    skills=["basic_attack", "fire_bolt"], weakness="water", toughness=45),
    "harpy":    dict(name="Harpy",       element="wind",   hp=85,  atk=22, defn=7,  spd=18, xp=34, gold=28,
                    skills=["basic_attack", "wind_arrow"], weakness="fire", toughness=50),
    "ghoul":    dict(name="Ghoul",       element="dark",   hp=110, atk=24, defn=10, spd=12, xp=40, gold=32,
                    skills=["basic_attack", "dark_bolt"], weakness="light", toughness=65),
    "paladin":  dict(name="Fallen Paladin", element="light", hp=160, atk=26, defn=18, spd=10, xp=60, gold=48,
                    skills=["basic_attack", "light_slash"], weakness="dark", toughness=90),
    "hydra":    dict(name="Hydra",       element="water",  hp=200, atk=26, defn=16, spd=11, xp=80, gold=60,
                    skills=["basic_attack", "water_bolt", "tidal_wave"], weakness="wind", toughness=110),
    "frosttitan": dict(name="Frost Titan", element="water", hp=440, atk=36, defn=26, spd=10, xp=260, gold=260,
                      skills=["basic_attack", "water_bolt", "frost_nova"], weakness="fire", toughness=200),
    "embertyrant": dict(name="Ember Tyrant", element="fire", hp=620, atk=42, defn=26, spd=14, xp=360, gold=360,
                      skills=["basic_attack", "fire_bolt", "inferno", "fire_slash"], weakness="water", toughness=260),
}

# ---------------------------------------------------------------------------
# Stages / map nodes — REMOVED.
# The turn-based adventure campaign was deleted in favor of the open-world
# mode. STAGES_DB is kept as an empty list so any stray references (and the
# save migration) degrade gracefully instead of NameError-ing.
# ---------------------------------------------------------------------------
STAGES_DB = []

# ---------------------------------------------------------------------------
# Gacha pool
# ---------------------------------------------------------------------------
GACHA_RATES = {"SSR": 0.06, "SR": 0.34, "R": 0.60}
GACHA_POOL = {"SSR": ["aria", "kael", "mira", "zephyr", "luna", "pyra", "lyra",
                      "ember", "tide", "zephyra", "selene", "nox", "raven"],
              "SR":  ["thorne", "sera", "rune", "blaze", "nami", "cinder", "mist", "gaia", "echo"],
              "R":   ["gale", "vex", "sol"]}

GACHA_COST = dict(single=dict(gems=10, gold=0), multi=dict(gems=90, gold=0))

# --- Banners (multi-banner summoning) --------------------------------------
#   Each banner has its own pool + featured rate-up + its own pity counter.
#   - Standard: every hero, no rate-up, the "permanent" banner.
#   - Featured banners: a rate-up SSR (50% of SSR pulls land on the featured
#     hero) + a rate-up SR; smaller pool so the featured hero is more likely.
#   Pity rules (per banner):
#     - Hard pity: guaranteed SSR at PITY_HARD pulls since the last SSR.
#     - Soft pity: SSR chance ramps up after SOFT_PITY pulls.
#     - Guaranteed SR+ in every 10-pull (the 10th pull is at least SR).
GACHA_BANNERS = [
    dict(id="standard", name="Eternal Gate",
         desc="All heroes. No rate-up.",
         pool=GACHA_POOL,
         featured_ssr=None, featured_sr=None,
         color=(120, 180, 255)),
    dict(id="dawn", name="Dawn Covenant",
         desc="Rate-up: Aria & Selene (Light).",
         pool={"SSR": ["aria", "selene", "lyra", "kael", "mira"],
               "SR":  ["sera", "thorne", "nami", "rune", "echo"],
               "R":   ["gale", "vex", "sol"]},
         featured_ssr="aria", featured_sr="sera",
         color=(255, 220, 120)),
    dict(id="ember", name="Crimson Pact",
         desc="Rate-up: Kael & Pyra (Fire).",
         pool={"SSR": ["kael", "pyra", "ember", "aria", "raven"],
               "SR":  ["blaze", "cinder", "gaia", "mist", "sera"],
               "R":   ["gale", "vex", "sol"]},
         featured_ssr="kael", featured_sr="blaze",
         color=(255, 120, 90)),
    dict(id="abyss", name="Abyssal Veil",
         desc="Rate-up: Luna & Nox (Dark).",
         pool={"SSR": ["luna", "nox", "raven", "kael", "zephyr"],
               "SR":  ["rune", "nami", "cinder", "mist", "gaia"],
               "R":   ["gale", "sol", "vex"]},
         featured_ssr="luna", featured_sr="rune",
         color=(190, 120, 240)),
    dict(id="gale", name="Tempest Call",
         desc="Rate-up: Zephyr & Zephyra (Wind).",
         pool={"SSR": ["zephyr", "zephyra", "tide", "aria", "luna"],
               "SR":  ["thorne", "sera", "gaia", "echo", "mist"],
               "R":   ["vex", "sol", "gale"]},
         featured_ssr="zephyr", featured_sr="gaia",
         color=(140, 230, 170)),
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
ASCENSION_STARS_PER_DUPE = 1
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
# weakness-break system from the start: Aria (light), Kael (fire), Mira (water),
# Zephyr (wind) - a 4-hero open-world party.
STARTING_TEAM = ["aria", "kael", "mira", "zephyr"]
STARTING_OWNED = ["aria", "kael", "mira", "zephyr", "sera", "gale"]
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
