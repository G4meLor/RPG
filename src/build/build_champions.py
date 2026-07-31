"""
build_champions.py — one-shot build pipeline for the LoL roster redesign.

Reads the three crawled LoL data dirs and produces:
  - champions.py  (Task 1)  — the baked champion data (CHAMPIONS_DB)
  - assets/characters/{Key}/  (Task 2)  — rearranged real images (portrait/icon/skins/skills)
  - assets/characters/{Key}/sprite.png  (Task 3)  — descriptor-driven procedural world sprite

Task 1 (this version) implements the data bake only. Tasks 2 and 3 fill in
rearrange_images() and generate_sprites().

CRITICAL: never Read a PNG/JPG with the Read tool — it crashes the session.
This script uses only json/os (+ pygame for the image steps, headless).

Run:
    python3 build_champions.py            # Task 1: data bake -> champions.py
    python3 build_champions.py --images    # Task 2: + rearrange images
    python3 build_champions.py --sprites   # Task 3: + generate world sprites
    python3 build_champions.py --all       # all three
"""
import json
import os

# Repo root = parent of src/ = two levels up from this file (src/build/build_champions.py).
# Asset dirs + the output champions.py live at <repo-root> regardless of where
# this module sits, so the path is repo-root-relative (not __file__-relative) to
# stay correct after the move into src/build/ without a symlink.
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHAMP_DIR = os.path.join(HERE, "assets", "champions")          # JSON source
IMG_DIR = os.path.join(HERE, "assets", "champions_images")     # splash source
ICON_DIR = os.path.join(HERE, "assets", "champions_ability_icons")  # ability icons
BUNDLE_DIR = os.path.join(HERE, "assets", "characters")         # target bundles

# ---------------------------------------------------------------------------
# Mapping tables — the core IP. Hand-tunable override sections are meant to be
# edited directly to retune the roster without rerunning the whole pipeline.
# ---------------------------------------------------------------------------

# Element: faction default + per-champ theme override.
FAC2EL = {
    "noxus": "fire", "shurima": "fire",
    "freljord": "water", "bilgewater": "water",
    "ionia": "wind", "ixtal": "wind", "bandle-city": "wind",
    "demacia": "light", "piltover": "light", "mount-targon": "light",
    "zaun": "dark", "void": "dark", "shadow-isles": "dark", "unaffiliated": "dark",
}
# Per-champ element overrides (champ key -> element) for obviously-mismatched
# champs whose faction default would misassign their theme.
EL_OVERRIDE = {
    "Brand": "fire", "Annie": "fire", "Aatrox": "fire", "Rumble": "fire",
    "Anivia": "water", "Nami": "water", "Illaoi": "water", "Nautilus": "water",
    "AurelionSol": "light", "Kayle": "light", "Leona": "light", "Diana": "light",
    "Rakan": "wind", "Xayah": "wind", "Quinn": "wind", "JarvanIV": "light",
    "Mordekaiser": "dark", "Thresh": "dark", "Hecarim": "dark", "Elise": "dark",
    "Karthus": "dark", "Nocturne": "dark", "Shaco": "dark", "Evelynn": "dark",
    "Nunu": "water", "Braum": "water", "Gragas": "water",
}

# Role: LoL roles -> 7 game roles (first match wins); fallback by primary
# position. Order matters — more specific tags first.
ROLEMAP = [
    ("JUGGERNAUT", "destruction"), ("DIVER", "destruction"),
    ("ASSASSIN", "hunt"), ("MARKSMAN", "hunt"), ("SKIRMISHER", "hunt"),
    ("ARTILLERY", "erudition"), ("BATTLEMAGE", "erudition"), ("BURST", "erudition"),
    ("MAGE", "erudition"), ("SPECIALIST", "erudition"),
    ("ENCHANTER", "abundance"),
    ("CATCHER", "nihility"),
    ("VANGUARD", "preservation"), ("WARDEN", "preservation"), ("TANK", "preservation"),
    ("SUPPORT", "harmony"),
    ("FIGHTER", "destruction"),
]
POS2ROLE = {"TOP": "preservation", "JUNGLE": "hunt", "MIDDLE": "erudition",
            "BOTTOM": "hunt", "SUPPORT": "abundance"}
GAME_ROLES = {"destruction", "hunt", "erudition", "harmony",
              "nihility", "preservation", "abundance"}

# Rarity: curated SSR set + price tier. The curated set is the iconic faces the
# gacha should feature; the rest fall by blueEssence price (or difficulty).
SSR_CURATED = {
    "Ahri", "Yasuo", "Jinx", "Lux", "Garen", "Thresh", "LeeSin", "Jhin",
    "Kaisa", "Ezreal", "Zed", "Darius", "Ashe", "Lissandra", "Brand",
    "Veigar", "Teemo", "Riven", "Syndra", "AurelionSol", "Mordekaiser",
    "Swain", "Sylas", "Viego", "Volibear", "Ornn", "Kindred", "Bard",
    "Pyke", "Shaco", "Akali", "Katarina", "Sett", "Irelia", "Camille",
}

# Stats: LoL flat -> game, scaled by observed min/max across all 170.
# (lol_min, lol_max, game_min, game_max) — refined after the min/max pass.
STAT_RANGES = {
    "hp":   (520, 680, 100, 160),     # health.flat
    "atk":  (52,  64,  18,  30),       # attackDamage.flat
    "defn": (18,  38,  10,  26),      # (armor.flat + magicResistance.flat) / 2
    "spd":  (325, 355, 8,   19),       # movespeed.flat
    "mp":   (235, 490, 24,  42),       # mana.flat (non-mana resource -> 30)
}

# Skills: per-element shared skill ids by game type. Q/W/E map to 3 of these by
# the LoL ability's type; R -> the element's ultimate. The displayed name is the
# LoL ability name; the icon is the real LoL ability icon (Task 2). The same
# skill_id on two champs has different name+icon but the same tuned mechanics.
EL_SKILLS = {
    "fire":  {"attack": "fire_slash", "magic": "fire_bolt", "aoe_magic": "inferno",
              "aoe_attack": "fire_strike", "buff": "fire_summon", "debuff": "fire_curse",
              "heal": "phoenix", "ultimate": "meteor"},
    "water": {"attack": "water_bolt", "magic": "water_bolt", "aoe_magic": "tidal_wave",
              "aoe_attack": "frost_nova", "buff": "tide_shield", "debuff": "dark_curse",
              "heal": "water_heal", "ultimate": "tsunami"},
    "wind":  {"attack": "wind_arrow", "magic": "wind_arrow", "aoe_magic": "wind_aoe",
              "aoe_attack": "gust", "buff": "swift_buff", "debuff": "evasion",
              "heal": "evasion", "ultimate": "tempest"},
    "light": {"attack": "light_slash", "magic": "light_beam", "aoe_magic": "judgement_aoe",
              "aoe_attack": "light_slash", "buff": "blessing", "debuff": "taunt_skill",
              "heal": "sanctuary", "ultimate": "light_hymn"},
    "dark":  {"attack": "dark_bolt", "magic": "dark_bolt", "aoe_magic": "dark_aoe",
              "aoe_attack": "dark_bolt", "buff": "shield_ward", "debuff": "dark_curse",
              "heal": "soul_drain", "ultimate": "void_nova"},
}

# Passive (P) by role — the shared base passive. Signatures (HERO_SIGNATURE) are
# assigned in Task 4 (auto by role + flagship overrides).
PASSIVE_BY_ROLE = {
    "destruction": "p_adrenaline", "hunt": "p_crit", "erudition": "p_energy",
    "harmony": "p_regen", "nihility": "p_thorns", "preservation": "p_shield_low",
    "abundance": "p_regen",
}

# Archetype: the world-sprite silhouette class. First matching predicate wins.
# Predicates take the raw champ dict (key, roles, faction, attackType, ...).
def _arch(c):
    key = c.get("key", "")
    roles = set(c.get("roles", []))
    fac = c.get("faction", "")
    atk = c.get("attackType", "")
    if fac == "bandle-city":
        return "yordle"
    if key in {"Ahri", "Rakan", "Xayah", "MonkeyKing", "Sett", "Rengar",
               "Wukong", "Neeko", "Shyvana"}:
        return "vastaya"
    if key in {"Blitzcrank", "Camille", "Orianna", "Velkoz", "Malphite",
               "Rammus", "Zac", "Galio", "Skarner", "Rell", "Viktor"}:
        return "construct"
    if fac == "shadow-isles" or key in {"Mordekaiser", "Hecarim", "Yorick",
                                        "Karthus", "Thresh", "Nocturne",
                                        "Elise", "Viego", "Kalista", "Gwen",
                                        "Maokai", "Senna", "Lucian"}:
        return "undead"
    if key in {"Warwick", "Nunu", "Volibear", "Udyr", "RekSai", "Belveth",
               "Khazix", "Rengar", "Nidalee", "Briar", "Twitch", "Rumble",
               "Gnar", "Wukong"}:
        return "beast"
    if "JUGGERNAUT" in roles or key in {"Darius", "Garen", "Sion", "Urgot",
                                        "DrMundo", "Nasus", "Renekton",
                                        "Aatrox", "Tryndamere", "Olaf",
                                        "Mordekaiser", "Illaoi", "Sett",
                                        "Trundle", "Volibear", "Udyr"}:
        return "brute"
    if "MAGE" in roles or key in {"Lux", "Syndra", "Veigar", "Brand", "Annie",
                                  "Xerath", "Ziggs", "Orianna", "Ahri",
                                  "Ryze", "Cassiopeia", "Vladimir", "Malzahar",
                                  "Karthus", "AurelionSol", "Zoe", "Syndra"}:
        return "mage"
    if "MARKSMAN" in roles or key in {"Ashe", "Jinx", "Caitlyn", "Ezreal",
                                      "Varus", "Vayne", "Sivir", "MissFortune",
                                      "Tristana", "Kaisa", "Draven", "Jhin",
                                      "Lucian", "Senna", "Zeri", "Aphelios"}:
        return "archer"
    if "ASSASSIN" in roles or key in {"Zed", "Akali", "Talon", "Katarina",
                                      "Khazix", "Shaco", "Ekko", "Vex",
                                      "Qiyana", "Kayn", "Nocturne", "Diana"}:
        return "rogue"
    # fallback: armored melee (Garen, Leona, Poppy, Braum, Taric, Shen...)
    return "knight"

# Weapon: keyword scan of the ability names + champ theme. Fallback by
# attackType/role. Returns one of sword/axe/bow/dagger/staff/spear/gun/
# fists/scythe/whip/orb/shield.
WEAPON_KEYWORDS = [
    ("bow", "bow"), ("arrow", "bow"), ("archer", "bow"),
    ("shot", "gun"), ("bullet", "gun"), ("cannon", "gun"), ("gun", "gun"),
    ("dagger", "dagger"), ("blade", "sword"), ("sword", "sword"),
    ("strike", "sword"), ("slash", "sword"), ("cut", "sword"),
    ("axe", "axe"), ("cleaver", "axe"),
    ("spear", "spear"), ("polearm", "spear"),
    ("staff", "staff"), ("wand", "staff"), ("rod", "staff"),
    ("orb", "orb"), ("sphere", "orb"),
    ("fist", "fists"), ("punch", "fists"), ("kick", "fists"),
    ("scythe", "scythe"), ("sickle", "scythe"),
    ("whip", "whip"), ("chain", "whip"), ("flail", "whip"),
    ("shield", "shield"), ("buckler", "shield"),
]
WEAPON_FALLBACK = {"MELEE": "sword", "RANGED": "bow"}

# Motif: the champ's signature visual element, from the game element.
MOTIF_BY_EL = {"fire": "flame", "water": "ice", "wind": "wind",
               "light": "light", "dark": "shadow"}

# Build: body proportions, from archetype (overridden by stats below).
ARCH_BUILD = {
    "knight": "average", "mage": "average", "archer": "slender", "brute": "bulky",
    "rogue": "slender", "undead": "tall", "yordle": "short", "vastaya": "average",
    "construct": "bulky", "beast": "average",
}

# Features: 0-3 distinctive features per archetype, + element-based extras.
ARCH_FEATURES = {
    "knight": ["cape"], "mage": ["hood"], "archer": [], "brute": [],
    "rogue": ["hood"], "undead": ["cape"], "yordle": [], "vastaya": ["horns"],
    "construct": ["spikes"], "beast": [],
}

# Palette: (primary, secondary, accent) from the element's pixel palette +
# a faction tint so two champs of the same element from different factions
# differ slightly. Faction tint added to the primary color (clamped).
EL_PALETTE = {
    "fire":   {"primary": (220, 90, 40),  "secondary": (255, 170, 90),  "accent": (255, 230, 140)},
    "water":  {"primary": (40, 120, 210), "secondary": (120, 200, 255), "accent": (200, 240, 255)},
    "wind":   {"primary": (120, 220, 160),"secondary": (200, 255, 220), "accent": (240, 255, 200)},
    "light":  {"primary": (250, 220, 90), "secondary": (255, 250, 200), "accent": (255, 255, 240)},
    "dark":   {"primary": (110, 50, 150),"secondary": (180, 110, 220), "accent": (200, 160, 255)},
}
FAC_TINT = {
    "noxus": (20, -10, -10), "shurima": (10, 5, -15), "demacia": (-15, 5, 5),
    "piltover": (-10, 10, 15), "ionia": (-5, 10, -5), "freljord": (-15, 0, 10),
    "zaun": (-5, 10, -15), "void": (-10, -5, 20), "shadow-isles": (-20, 5, 10),
    "bilgewater": (-5, 5, -10), "ixtal": (5, 10, -5), "mount-targon": (10, 5, 5),
    "bandle-city": (5, 5, 10), "unaffiliated": (0, 0, 0),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _scale(lol_val, lol_min, lol_max, g_min, g_max):
    """Scale a LoL flat stat to the game range, clamped."""
    if lol_max <= lol_min:
        return int(round((g_min + g_max) / 2))
    t = (lol_val - lol_min) / (lol_max - lol_min)
    return int(round(g_min + t * (g_max - g_min)))


def _truncate_bio(text, limit=120):
    """Truncate lore to ~limit chars at a sentence boundary."""
    if not text:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    # find the last sentence end within the limit
    cut = text.rfind(". ", 0, limit)
    if cut < 0:
        cut = limit
        # break at a word boundary
        sp = text.rfind(" ", 0, cut)
        if sp > limit // 2:
            cut = sp
        return text[:cut].rstrip() + "…"
    return text[:cut + 1].strip()


def _derive_quote(lore, title, limit=80):
    """Derive a short quote from the lore (last sentence) or the title."""
    if lore:
        sents = [s.strip() for s in lore.replace("—", " ").split(".") if s.strip()]
        if sents:
            q = sents[-1]
            if len(q) > limit:
                sp = q.rfind(" ", 0, limit)
                q = q[:sp if sp > limit // 2 else limit].rstrip() + "…"
            return q
    if title:
        return f"{title}."
    return ""


def _personality(c):
    """One-word personality from roles + attributeRatings."""
    roles = set(c.get("roles", []))
    ar = c.get("attributeRatings", {}) or {}
    if "ASSASSIN" in roles:
        return "cold"
    if "SUPPORT" in roles or "ENCHANTER" in roles:
        return "gentle"
    if "MAGE" in roles:
        return "curious"
    if "TANK" in roles or "VANGUARD" in roles or "WARDEN" in roles:
        return "steadfast"
    if "MARKSMAN" in roles:
        return "focused"
    if "JUGGERNAUT" in roles:
        return "fierce"
    if ar.get("mobility", 0) >= 3:
        return "restless"
    if ar.get("utility", 0) >= 3:
        return "gentle"
    return "stoic"


def _game_role(c):
    """Map a LoL champ to one of the 7 game roles."""
    roles = c.get("roles", [])
    for r, g in ROLEMAP:
        if r in roles:
            return g
    pos = c.get("positions", ["MIDDLE"])
    return POS2ROLE.get(pos[0] if pos else "MIDDLE", "erudition")


def _game_element(c):
    """Map a LoL champ to one of the 5 game elements."""
    key = c.get("key", "")
    if key in EL_OVERRIDE:
        return EL_OVERRIDE[key]
    fac = c.get("faction", "unaffiliated")
    return FAC2EL.get(fac, "dark")


def _rarity(c):
    """SSR/SR/R by curated set + price tier + difficulty."""
    if c.get("key", "") in SSR_CURATED:
        return "SSR"
    price = (c.get("price", {}) or {}).get("blueEssence", 0) or 0
    if price >= 4800:
        return "SSR"
    if price >= 3150:
        return "SR"
    diff = (c.get("attributeRatings", {}) or {}).get("difficulty", 1)
    if diff >= 3:
        return "SSR"
    if diff == 2:
        return "SR"
    return "R"


def _ability_type(ab, element):
    """Map a LoL ability (spellEffects/damageType/effects) to a game skill type."""
    se = (ab.get("spellEffects") or "").lower()
    dt = (ab.get("damageType") or "").lower()
    desc = " ".join(e.get("description", "") for e in ab.get("effects", []) or []).lower()
    # heal/shield/buff/cc keywords from the effect description take precedence
    # (the champ's kit flavor — a heal ability should be a heal skill).
    if ("heal" in desc or "restore" in desc) and "damage" not in desc[:40]:
        return "heal"
    if "shield" in desc:
        return "buff"
    if "buff" in desc or "bonus " in desc or "grant" in desc[:30]:
        return "buff"
    if any(k in desc for k in ("stun", "root", "charm", "slow", "knock",
                               "silence", "fear", "taunt", "disarm", "pull")):
        return "debuff"
    # AoE vs single by spellEffects
    if any(k in se for k in ("aoe", "area", "cone", "line")):
        return "aoe_attack" if "physical" in dt else "aoe_magic"
    if "single" in se:
        return "attack" if "physical" in dt else "magic"
    # fallback by damageType
    if "physical" in dt:
        return "attack"
    if "magic" in dt:
        return "magic"
    return "magic"


def _map_skills(c, element):
    """Map Q/W/E -> 3 distinct active skill ids; R -> the element ultimate."""
    pool = EL_SKILLS[element]
    types = []
    for slot in ("Q", "W", "E"):
        ablist = c.get("abilities", {}).get(slot, [])
        ab = ablist[0] if ablist else {}
        types.append(_ability_type(ab, element))
    chosen = []
    used = set()
    for t in types:
        sid = pool.get(t) or pool.get("attack") or pool.get("magic")
        if sid in used:
            # dedup: pick the next available type from a priority order
            for alt in ("attack", "magic", "aoe_magic", "aoe_attack",
                        "buff", "debuff", "heal"):
                alt_sid = pool.get(alt)
                if alt_sid and alt_sid not in used:
                    sid = alt_sid
                    break
        used.add(sid)
        chosen.append(sid)
    return chosen, pool["ultimate"]


def _weapon(c, archetype):
    """Derive the weapon from ability-name keywords + fallback."""
    names = []
    for slot in ("Q", "W", "E", "R"):
        ablist = c.get("abilities", {}).get(slot, [])
        if ablist:
            names.append(ablist[0].get("name", "").lower())
    blob = " ".join(names) + " " + " ".join(r.lower() for r in c.get("roles", []))
    for kw, w in WEAPON_KEYWORDS:
        if kw in blob:
            return w
    # fallback by archetype + attackType
    if archetype == "mage":
        return "staff"
    if archetype == "archer":
        return "bow"
    if archetype == "rogue":
        return "dagger"
    if archetype == "brute":
        return "fists"
    if archetype in ("undead", "construct"):
        return "sword"
    return WEAPON_FALLBACK.get(c.get("attackType", ""), "sword")


def _palette(element, faction):
    """(primary, secondary, accent) from the element palette + faction tint."""
    base = EL_PALETTE[element]
    tint = FAC_TINT.get(faction, (0, 0, 0))
    prim = tuple(_clamp(base["primary"][i] + tint[i], 0, 255) for i in range(3))
    return {"primary": prim, "secondary": base["secondary"], "accent": base["accent"]}


def _descriptor(c, element, archetype, stats):
    """Build the rich descriptor driving the procedural world sprite."""
    weapon = _weapon(c, archetype)
    features = list(ARCH_FEATURES.get(archetype, []))
    # element-based feature extras
    if element == "light" and archetype in ("mage",):
        features.append("halo")
    if element == "dark" and archetype in ("rogue", "undead", "mage"):
        features.append("mask")
    # build: archetype default, nudged by stats
    build = ARCH_BUILD.get(archetype, "average")
    if stats["hp"] >= 150 and build != "short":
        build = "bulky"
    elif stats["spd"] >= 17 and build not in ("short", "bulky"):
        build = "slender"
    return {
        "archetype": archetype,
        "weapon": weapon,
        "palette": _palette(element, c.get("faction", "unaffiliated")),
        "features": features[:3],
        "build": build,
        "motif": MOTIF_BY_EL[element],
    }


# ---------------------------------------------------------------------------
# Stat range computation (min/max across all 170, for scaling)
# ---------------------------------------------------------------------------

def _collect_stat_ranges(champs):
    """Walk all champs once to find the LoL min/max per stat. Returns the
    observed ranges so _scale can map them to the game ranges."""
    mins = {"hp": 1e9, "atk": 1e9, "defn": 1e9, "spd": 1e9, "mp": 1e9}
    maxs = {"hp": 0, "atk": 0, "defn": 0, "spd": 0, "mp": 0}
    for c in champs:
        st = c.get("stats", {}) or {}
        h = (st.get("health", {}) or {}).get("flat", 0) or 0
        a = (st.get("attackDamage", {}) or {}).get("flat", 0) or 0
        ar = (st.get("armor", {}) or {}).get("flat", 0) or 0
        mr = (st.get("magicResistance", {}) or {}).get("flat", 0) or 0
        ms = (st.get("movespeed", {}) or {}).get("flat", 0) or 0
        ma = (st.get("mana", {}) or {}).get("flat", 0) or 0
        defn = (ar + mr) / 2
        for k, v in (("hp", h), ("atk", a), ("defn", defn),
                     ("spd", ms), ("mp", ma)):
            if v < mins[k]:
                mins[k] = v
            if v > maxs[k]:
                maxs[k] = v
    return mins, maxs


# ---------------------------------------------------------------------------
# Task 1: data bake -> champions.py
# ---------------------------------------------------------------------------

def build_data():
    """Read all 170 JSONs, map to the game model, write champions.py."""
    files = sorted(f for f in os.listdir(CHAMP_DIR) if f.endswith(".json"))
    raw = []
    for f in files:
        with open(os.path.join(CHAMP_DIR, f)) as fh:
            raw.append(json.load(fh))
    print(f"Loaded {len(raw)} champion JSONs")

    # stat ranges across all 170 (for scaling)
    mins, maxs = _collect_stat_ranges(raw)
    print(f"Stat ranges: hp {mins['hp']}-{maxs['hp']}, atk {mins['atk']}-{maxs['atk']}, "
          f"defn {mins['defn']:.0f}-{maxs['defn']:.0f}, spd {mins['spd']}-{maxs['spd']}, "
          f"mp {mins['mp']}-{maxs['mp']}")

    champs = []
    for c in raw:
        key = c["key"]
        element = _game_element(c)
        role = _game_role(c)
        rarity = _rarity(c)
        archetype = _arch(c)

        # stats
        st = c.get("stats", {}) or {}
        h = (st.get("health", {}) or {}).get("flat", 0) or 0
        a = (st.get("attackDamage", {}) or {}).get("flat", 0) or 0
        ar = (st.get("armor", {}) or {}).get("flat", 0) or 0
        mr = (st.get("magicResistance", {}) or {}).get("flat", 0) or 0
        ms = (st.get("movespeed", {}) or {}).get("flat", 0) or 0
        ma = (st.get("mana", {}) or {}).get("flat", 0) or 0
        resource = c.get("resource", "MANA")
        defn_raw = (ar + mr) / 2
        stats = {
            "hp":   _scale(h, mins["hp"], maxs["hp"], *STAT_RANGES["hp"][2:]),
            "atk":  _scale(a, mins["atk"], maxs["atk"], *STAT_RANGES["atk"][2:]),
            "defn": _scale(defn_raw, mins["defn"], maxs["defn"], *STAT_RANGES["defn"][2:]),
            "spd":  _scale(ms, mins["spd"], maxs["spd"], *STAT_RANGES["spd"][2:]),
            "mp":   30 if (resource != "MANA" or ma == 0)
                    else _scale(ma, mins["mp"], maxs["mp"], *STAT_RANGES["mp"][2:]),
        }

        # skills
        skills, ultimate = _map_skills(c, element)
        passive = PASSIVE_BY_ROLE[role]

        # lore
        lore_text = c.get("lore", "") or ""
        bio = _truncate_bio(lore_text, 120)
        quote = _derive_quote(lore_text, c.get("title", ""))
        personality = _personality(c)

        # skins (metadata from JSON; index = id % 1000; Task 2 copies the ones
        # whose splash_tile_{index}.jpg exists on disk)
        skins = []
        for sk in c.get("skins", []) or []:
            sk_id = sk.get("id", 0)
            skins.append({"name": sk.get("name", "Skin"), "id": sk_id,
                          "index": sk_id % 1000})

        # ability names for _HERO_SKILL_TEXT (Task 4)
        ab_names = {}
        for slot in ("Q", "W", "E", "R"):
            ablist = c.get("abilities", {}).get(slot, [])
            if ablist:
                ab_names[slot] = ablist[0].get("name", "")

        champs.append({
            "id": key,
            "name": c.get("name", key),
            "title": c.get("title", ""),
            "faction": c.get("faction", "unaffiliated"),
            "element": element,
            "rarity": rarity,
            "role": role,
            "stats": stats,
            "skills": skills,
            "ultimate": ultimate,
            "passive": passive,
            "weapon": _weapon(c, archetype),
            "archetype": archetype,
            "descriptor": _descriptor(c, element, archetype, stats),
            "lore": {"bio": bio, "quote": quote, "personality": personality},
            "skins": skins,
            "ability_names": ab_names,
        })

    # sanity checks
    assert len(champs) == 170, f"expected 170 champs, got {len(champs)}"
    for ch in champs:
        assert ch["element"] in EL_PALETTE, f"{ch['id']} bad element {ch['element']}"
        assert ch["role"] in GAME_ROLES, f"{ch['id']} bad role {ch['role']}"
        assert ch["rarity"] in ("SSR", "SR", "R"), f"{ch['id']} bad rarity {ch['rarity']}"
        assert 100 <= ch["stats"]["hp"] <= 165
        assert 17 <= ch["stats"]["atk"] <= 31
        assert 9 <= ch["stats"]["defn"] <= 27
        assert 7 <= ch["stats"]["spd"] <= 20
        assert 23 <= ch["stats"]["mp"] <= 43
        assert ch["skills"] and len(ch["skills"]) == 3
        assert ch["ultimate"]
        assert ch["passive"]
        assert ch["skins"], f"{ch['id']} has no skins"

    _write_champions_py(champs)
    print(f"Wrote champions.py: {len(champs)} champions")

    # element/role/rarity distribution (sanity)
    from collections import Counter
    print("  elements:", dict(Counter(c["element"] for c in champs).most_common()))
    print("  roles:", dict(Counter(c["role"] for c in champs).most_common()))
    print("  rarities:", dict(Counter(c["rarity"] for c in champs).most_common()))
    print("  archetypes:", dict(Counter(c["archetype"] for c in champs).most_common()))
    return champs


def _write_champions_py(champs):
    """Write champions.py with CHAMPIONS_DB + CHAMPION_BY_KEY."""
    lines = [
        '"""',
        "champions.py — the baked LoL champion roster (170 champions).",
        "",
        "Auto-generated by build_champions.py from assets/champions/*.json.",
        "DO NOT edit by hand — edit build_champions.py (the mapping tables +",
        "override section) and rerun: python3 build_champions.py",
        '"""',
        "",
        "# Each champion dict fields:",
        "#   id, name, title, faction, element, rarity, role, stats{hp,atk,defn,spd,mp},",
        "#   skills[3], ultimate, passive, weapon, archetype, descriptor{...},",
        "#   lore{bio,quote,personality}, skins[{name,id,index}], ability_names{Q,W,E,R}",
        "",
        "CHAMPIONS_DB = [",
    ]
    for ch in champs:
        lines.append(f"    {repr(ch)},")
    lines.append("]")
    lines.append("")
    lines.append("CHAMPION_BY_KEY = {c[\"id\"]: c for c in CHAMPIONS_DB}")
    lines.append("")
    with open(os.path.join(HERE, "champions.py"), "w") as fh:
        fh.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Task 2: image rearrange — copy the real LoL art into the per-champion bundle.
#   For each champion:
#     {Key}.png              -> assets/characters/{Key}/icon.png        (128x128)
#     splash_tile_0.jpg      -> assets/characters/{Key}/portrait.jpg    (380x380)
#     splash_tile_{N}.jpg    -> assets/characters/{Key}/skins/{N}.jpg   (per skin)
#     ability icon (fuzzy)   -> assets/characters/{Key}/skills/{skill_id}.png (64x64)
#   Missing ability icons fall back to a 64x64 element-tinted placeholder so no
#   loader ever hits FileNotFoundError. The source dirs is NOT deleted here
#   (Task 9 deletes the three source dirs after the whole build verifies).
# ---------------------------------------------------------------------------

import shutil
import re

def _champ_img_dir(key):
    return os.path.join(IMG_DIR, key)

def _ability_icon_dir(key):
    return os.path.join(ICON_DIR, key.lower())

def _splash_tile_path(key, index):
    """The splash_tile_{index}.jpg path for a champion (key is the dir name)."""
    # filenames are lowercase: ahri_splash_tile_0.jpg
    return os.path.join(_champ_img_dir(key), f"{key.lower()}_splash_tile_{index}.jpg")

def _all_splash_tiles(key):
    """All splash_tile_{N}.jpg in the champ's image dir, as {index: path}."""
    d = _champ_img_dir(key)
    if not os.path.isdir(d):
        return {}
    out = {}
    for f in os.listdir(d):
        if f.lower().startswith(f"{key.lower()}_splash_tile_") and f.lower().endswith(".jpg"):
            try:
                idx = int(f.split("_tile_")[1].split(".")[0])
                out[idx] = os.path.join(d, f)
            except ValueError:
                pass
    return out

def _numeric_skin_png(key, skin_id):
    """The {skinId}.png numeric skin-tile path (270x303), if it exists."""
    p = os.path.join(_champ_img_dir(key), f"{skin_id}.png")
    return p if os.path.exists(p) else None

def _to_square_jpg(src_path, dst_path, size=380):
    """Center-crop + scale a source image to a size×size jpg (headless pygame)."""
    import pygame
    s = pygame.image.load(src_path).convert()
    w, h = s.get_size()
    side = min(w, h)
    cx, cy = (w - side) // 2, (h - side) // 2
    cropped = pygame.Surface((side, side))
    cropped.blit(s, (-cx, -cy))
    out = pygame.transform.smoothscale(cropped, (size, size))
    pygame.image.save(out, dst_path)

def _best_portrait_src(key, skins):
    """Pick the best real-image source for the default-skin portrait.
    Returns (path, needs_crop) — needs_crop True if the source isn't already
    a 380x380 square (so the caller should _to_square_jpg it). Preference:
      1. splash_tile_0 (already 380x380 square) — copy as-is
      2. the lowest-N splash_tile (380x380 square) — copy as-is
      3. the base skin's numeric {skinId}.png (270x303) — crop to square
      4. the lowest-id numeric png — crop to square
      5. {Key}.png (128x128 icon) — crop to square (last resort)
    """
    tiles = _all_splash_tiles(key)
    if 0 in tiles:
        return (tiles[0], False)
    if tiles:
        lowest = min(tiles)
        return (tiles[lowest], False)
    # numeric pngs (skin tiles, 270x303)
    img_dir = _champ_img_dir(key)
    if os.path.isdir(img_dir):
        # the base skin's numeric png
        base_id = skins[0]["id"] if skins else None
        if base_id is not None:
            p = _numeric_skin_png(key, base_id)
            if p:
                return (p, True)
        # lowest-id numeric png
        nums = []
        for f in os.listdir(img_dir):
            if f.lower().endswith(".png"):
                stem = f[:-4]
                if stem.isdigit():
                    nums.append(int(stem))
        if nums:
            return (os.path.join(img_dir, f"{min(nums)}.png"), True)
    # last resort: the champ icon
    icon = os.path.join(img_dir, f"{key}.png")
    if os.path.exists(icon):
        return (icon, True)
    return (None, False)

def _ensure_bundle_dirs(key):
    base = os.path.join(BUNDLE_DIR, key)
    os.makedirs(os.path.join(base, "skills"), exist_ok=True)
    os.makedirs(os.path.join(base, "skins"), exist_ok=True)
    return base

def _match_ability_icon(key, slot):
    """Find the real LoL ability icon for (champ, slot). slot in
    {passive,q,w,e,r}. Returns the source path or None.

    Naming is inconsistent across champs: aatrox_q, icons_ahri_q, garen_q,
    jinx_q1, leesinq1, luxprismawrap (no slot keyword at all). Strategy:
      1. glob the champ's ability-icon dir
      2. for files whose basename (lowercased, stripped of the champ name +
         'icons_' prefix + digits + .png) ends in the slot keyword -> candidates
      3. if none, fall back to the slot keyword anywhere in the basename
      4. pick the base variant (no trailing digit, else the lowest digit)
    The 'passive' slot also matches 'p' (leesinp.png) and 'passive' substring.
    """
    d = _ability_icon_dir(key)
    if not os.path.isdir(d):
        return None
    files = [f for f in os.listdir(d) if f.lower().endswith(".png")]
    if not files:
        return None
    kl = key.lower()
    slots = {"q": ["q"], "w": ["w"], "e": ["e"], "r": ["r"],
             "passive": ["passive", "p"]}[slot]

    def _score(fn):
        n = fn.lower()[:-4]  # strip .png
        # strip the champ name + icons_ prefix
        for prefix in (kl, "icons_" + kl):
            if n.startswith(prefix):
                n = n[len(prefix):]
                break
        n = n.lstrip("_")
        # exact-slot match: the whole remaining token is the slot (maybe +digit)
        m = re.match(r"^(passive|p|q|w|e|r)(\d*)$", n)
        if m and m.group(1) in slots:
            return (0, int(m.group(2) or 0))
        # slot keyword at the start of the remaining token (after champ strip)
        for s in slots:
            if n.startswith(s):
                return (1, 0)
        # slot keyword anywhere in the full basename
        for s in slots:
            if s in fn.lower():
                return (2, 0)
        return None

    scored = []
    for fn in files:
        sc = _score(fn)
        if sc is not None:
            scored.append((sc, fn))
    if not scored:
        return None
    # lowest (rank, digit) wins; rank 0 (exact-slot) beats rank 1/2
    scored.sort(key=lambda x: x[0])
    return os.path.join(d, scored[0][1])

def _placeholder_skill_icon(element, path):
    """Generate a 64x64 element-tinted square as a fallback skill icon."""
    import pygame
    pygame.init()
    pygame.display.set_mode((1, 1))
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    pal = EL_PALETTE[element]
    pygame.draw.rect(s, (*pal["primary"], 255), s.get_rect(), border_radius=10)
    pygame.draw.rect(s, (*pal["secondary"], 255), s.get_rect().inflate(-12, -12), border_radius=6)
    pygame.draw.circle(s, (*pal["accent"], 255), (32, 32), 10)
    pygame.image.save(s, path)

def rearrange_images(champs):
    """Copy the real LoL art into the per-champion bundle layout."""
    import pygame
    pygame.init()
    pygame.display.set_mode((1, 1))
    n_ok = n_icon_ok = n_skin_ok = n_skill_ok = n_skill_fallback = 0
    n_portrait_crop = 0
    for c in champs:
        key = c["id"]
        element = c["element"]
        base = _ensure_bundle_dirs(key)
        img_dir = _champ_img_dir(key)
        if not os.path.isdir(img_dir):
            print(f"  WARN: {key} image dir missing")
            continue
        # icon.png <- {Key}.png
        icon_src = os.path.join(img_dir, f"{key}.png")
        if os.path.exists(icon_src):
            shutil.copy(icon_src, os.path.join(base, "icon.png"))
            n_icon_ok += 1
        # portrait.jpg + skins/0.jpg <- best available real splash for skin 0
        src, needs_crop = _best_portrait_src(key, c["skins"])
        if src:
            portrait_dst = os.path.join(base, "portrait.jpg")
            skins0_dst = os.path.join(base, "skins", "0.jpg")
            if needs_crop:
                _to_square_jpg(src, portrait_dst, 380)
                _to_square_jpg(src, skins0_dst, 380)
                n_portrait_crop += 1
            else:
                shutil.copy(src, portrait_dst)
                shutil.copy(src, skins0_dst)
            n_ok += 1
        # skins/{N}.jpg <- splash_tile_{N}.jpg for each alt skin whose tile exists
        tiles = _all_splash_tiles(key)
        for sk in c["skins"]:
            idx = sk["index"]
            if idx == 0:
                continue  # already copied as portrait.jpg + skins/0.jpg
            if idx in tiles:
                shutil.copy(tiles[idx], os.path.join(base, "skins", f"{idx}.jpg"))
                n_skin_ok += 1
        # skills/{skill_id}.png <- real ability icon for the slot that skill fills
        # The skill_id is shared, but the icon is the real per-champ ability
        # icon for that slot. basic_attack has no icon (uses the champ's
        # attack VFX), so skip it.
        slot_for_skill = {}  # skill_id -> slot (Q/W/E/R) for this champ
        for i, sid in enumerate(c["skills"]):
            slot_for_skill[sid] = ["Q", "W", "E"][i]
        slot_for_skill[c["ultimate"]] = "R"
        for sid, slot in slot_for_skill.items():
            slot_kw = {"Q": "q", "W": "w", "E": "e", "R": "r"}[slot]
            src = _match_ability_icon(key, slot_kw)
            dst = os.path.join(base, "skills", f"{sid}.png")
            if src:
                shutil.copy(src, dst)
                n_skill_ok += 1
            else:
                _placeholder_skill_icon(element, dst)
                n_skill_fallback += 1
    print(f"Rearrange: {n_ok} portraits ({n_portrait_crop} cropped from "
          f"numeric/png), {n_icon_ok} icons, {n_skin_ok} alt skins, "
          f"{n_skill_ok} real skill icons, {n_skill_fallback} skill-icon fallbacks")



# ---------------------------------------------------------------------------
# Task 3: procedural world sprite — delegate to generate_assets.py, which has
# the descriptor system (10 archetypes + feature-adders + weapon-drawers).
# ---------------------------------------------------------------------------
def generate_sprites(champs):
    import src.assets_gen.generate as GA
    GA.generate_sprites(champs)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", action="store_true", help="rearrange images (Task 2)")
    ap.add_argument("--sprites", action="store_true", help="generate world sprites (Task 3)")
    ap.add_argument("--all", action="store_true", help="data + images + sprites")
    ap.add_argument("--vlm-loop", action="store_true",
                    help="use the VLM art-director loop to re-tune sprites (needs --sprites)")
    ap.add_argument("--concurrency", type=int, default=1,
                    help="max concurrent VLM calls (default 1 = serial)")
    ap.add_argument("--max-iters", type=int, default=10,
                    help="max critique rounds per skin (default 10)")
    ap.add_argument("--champs", default="",
                    help="comma-separated champ ids to process (default: all)")
    ap.add_argument("--skins", default="0",
                    help="comma-separated skin indices, or 'all' (P1: 0 only)")
    ap.add_argument("--force", action="store_true",
                    help="ignore the descriptor cache; re-bake every selected skin")
    args = ap.parse_args()
    if args.vlm_loop:
        # VLM bake path: skip build_data() (which needs assets/champions/*.json
        # that are not shipped) and load the already-baked CHAMPIONS_DB instead.
        # The descriptors in CHAMPIONS_DB have tuple palettes; normalize to lists
        # for sprite_loop's _validate.
        from src.build.champions import CHAMPIONS_DB as _DB
        champs = []
        for c in _DB:
            cc = dict(c)
            if "descriptor" in cc:
                pal = cc["descriptor"].get("palette", {})
                cc["descriptor"] = {
                    **cc["descriptor"],
                    "palette": {k: list(v) for k, v in pal.items()},
                }
            champs.append(cc)
    else:
        champs = build_data()
        if args.all or args.images:
            rearrange_images(champs)
    if args.all or args.sprites:
        if args.vlm_loop:
            from src.build.sprite_loop import run_sprite_bake
            # filter champs
            if args.champs:
                want = set(s.strip() for s in args.champs.split(",") if s.strip())
                champs = [c for c in champs if c["id"] in want]
            # parse skins
            if args.skins.strip().lower() == "all":
                # enumerate every skins/{idx}.jpg present per champ (Phase 3).
                # Sentinel: run_sprite_bake builds the per-champ skin lists from
                # the skins/*.jpg files on disk (via _enumerate_skins).
                skins = "all-enumerated"
            else:
                skins = [int(s.strip()) for s in args.skins.split(",") if s.strip()]
            # The baked CHAMPIONS_DB descriptors (already palette-normalized
            # above) are the fallback for the VLM describe call.
            rep = run_sprite_bake(champs, skin_indices=skins,
                                  concurrency=args.concurrency,
                                  max_iters=args.max_iters, force=args.force)
            print(f"VLM bake: processed={rep['n_processed']} skipped={rep['n_skipped']} "
                  f"ok={rep['n_ok']} mean_canonical_match "
                  f"{rep['mean_canonical_match_before']}->{rep['mean_canonical_match_after']}")
        else:
            generate_sprites(champs)


if __name__ == "__main__":
    main()
