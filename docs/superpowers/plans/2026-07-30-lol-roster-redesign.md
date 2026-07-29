# LoL Roster Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:subagent-driven-development (recommended) or superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 25 procedural heroes with 170 real LoL champions (real splash art for UI, real ability icons for skills, per-champion skins, faction story, LoL-ified enemies/bosses, descriptor-driven world sprites) via a one-shot build pipeline, preserving the combat/gacha/evo/constellation runtime.

**Architecture:** A build script (`build_champions.py`) is the foundation: it reads the three crawled LoL data dirs, maps each champion to the game model, bakes `champions.py`, rearranges real images into the per-champion bundle, generates the descriptor-driven world sprite, and updates every cross-reference in `data.py`/`entities.py`/`world_scene.py`/`world_entities.py`/`world_data.py`/`main.py`/`gacha.py`. The combat/gacha/evo/constellation systems are preserved verbatim — only roster contents + art sources change.

**Tech Stack:** Python 3.11, pygame 2.6, numpy; pure-procedural art for the world sprite only; real LoL PNG/JPG assets (loaded via pygame, never via the Read tool).

**User decisions (already made):** Use all 170 LoL champions; LoL names directly (`key` as id, `name` as display); LoL-ify enemies + bosses; do all 170 at once; use real splash_tile for portrait/roll/skins; use real ability icons for skills (fuzzy-matched); procedural descriptor-driven world sprite; user delegated all remaining decisions and pre-authorized implementation without further questions ("tự quyết toàn bộ các bước còn lại… implement luôn theo đúng chuẩn của skill superpowers mà không cần hỏi lại… Bạn có thể dùng workflows").

**Reference:** Full mapping tables + data-source structure are in the spec: `docs/superpowers/specs/2026-07-30-lol-roster-redesign-design.md`. The runtime-usage audit (every place that iterates HEROES_DB/SKILLS_DB or references hero id/name/element/role/skills) is the safety checklist — spec §8 reproduces it.

**Global Constraints (bind every task):**
- **NEVER Read a PNG/JPG with the Read tool — it crashes the session.** Use `ls`/`find`/`grep`/`Glob` + headless `pygame.image.load` (under `SDL_VIDEODRIVER=dummy`) for any image inspection. This is a hard constraint (see memory: gacha-no-image-reading).
- The 5 elements (fire/water/wind/light/dark), the `CHART`/`RESIST`/`REACTIONS`, the 7 roles, the `SKILLS_DB` skill ids, the evo/constellation/gacha mechanics are **preserved verbatim** — no new elements/roles/skill-types/combat-mechanics.
- Hero id = the LoL `key` (sanitized: `Ahri`, `MissFortune`, `KSante`, `Chogath`). Display name = LoL `name` (`Miss Fortune`, `K'Sante`).
- Every cross-reference in the audit's safety checklist (spec §8) must be updated in lockstep with `HEROES_DB` — a stale `GACHA_POOL`/`HERO_PASSIVES`/`WEAPON_STYLE_KEY`/`STARTING_TEAM`/`ENEMIES_DB` breaks the game.
- Verify headless: `SDL_VIDEODRIVER=dummy python3 verify_assets.py`; the acceptance suite; `xvfb-run -a` for the 1200-frame stress.
- Work on the `lol-roster` branch (already created). Commit per task.

---

## File Structure (what each task touches)

- **Create:** `build_champions.py` (the one-shot build pipeline), `champions.py` (the baked champion data).
- **Rewrite/extend:** `generate_assets.py` (descriptor system + per-archetype draw; drop `make_portrait`).
- **Update:** `data.py` (HEROES_DB + every cross-reference + enemies/bosses/story), `entities.py` (loaders: `.jpg` + skin), `world_scene.py` (WEAPON_STYLE_KEY from descriptor; skin in roll/HUD), `world_entities.py` (ranged-id list + per-id AI for new enemy ids), `world_data.py` (ROW_ENEMIES), `gacha.py` (skin in reveal), `main.py` (skin selector in hero-detail + codex), `verify_assets.py` (new bundle layout).
- **Delete (Task 9):** `assets/champions/`, `assets/champions_images/`, `assets/champions_ability_icons/` (the crawled sources, after the build bakes + rearranges).

---

## Mapping tables (the core IP — used by Tasks 1, 4, 5)

### Element (faction default + override)
```python
FAC2EL = {
    "noxus": "fire", "shurima": "fire",
    "freljord": "water", "bilgewater": "water",
    "ionia": "wind", "ixtal": "wind", "bandle-city": "wind",
    "demacia": "light", "piltover": "light", "mount-targon": "light",
    "zaun": "dark", "void": "dark", "shadow-isles": "dark", "unaffiliated": "dark",
}
# Theme overrides (champ key -> element) for obviously-mismatched champs:
EL_OVERRIDE = {
    "Brand": "fire", "Annie": "fire", "Aatrox": "fire", "Rumble": "fire",
    "Anivia": "water", "Nami": "water", "Illaoi": "water", "Nautilus": "water",
    "AurelionSol": "light", "Kayle": "light", "Leona": "light", "Diana": "light",
    "Rakan": "wind", "Xayah": "wind", "Quinn": "wind",
    "Mordekaiser": "dark", "Thresh": "dark", "Hecarim": "dark",
}  # extend as needed during the build; default is FAC2EL[faction]
```

### Role (LoL roles → 7 game roles; first match wins; fallback by primary position)
```python
ROLEMAP = [
    ("JUGGERNAUT", "destruction"), ("DIVER", "destruction"),
    ("ASSASSIN", "hunt"), ("MARKSMAN", "hunt"), ("SKIRMISHER", "hunt"),
    ("MAGE", "erudition"), ("ARTILLERY", "erudition"), ("BATTLEMAGE", "erudition"),
    ("BURST", "erudition"), ("SPECIALIST", "erudition"),
    ("ENCHANTER", "abundance"),
    ("CATCHER", "nihility"),
    ("VANGUARD", "preservation"), ("WARDEN", "preservation"), ("TANK", "preservation"),
    ("SUPPORT", "harmony"),
]
POS2ROLE = {"TOP": "preservation", "JUNGLE": "hunt", "MIDDLE": "erudition",
            "BOTTOM": "hunt", "SUPPORT": "abundance"}
# game_role(champ): for r in champ.roles: if r in ROLEMAP dict: return it; else POS2ROLE[champ.positions[0]]
```

### Rarity (curated SSR + price tier)
```python
SSR_CURATED = {"Ahri","Yasuo","Jinx","Lux","Garen","Thresh","LeeSin","Jhin","Kaisa",
    "Ezreal","Zed","Darius","Ashe","Lissandra","Brand","Veigar","Teemo","Riven",
    "Syndra","AurelionSol","Mordekaiser","Swain","Sylas","Viego","Volibear","Ornn",
    "Kindred","Bard","Pyke","Shaco"}
# rarity(champ): if key in SSR_CURATED: "SSR"; elif price.blueEssence >= 4800: "SSR";
#   elif price.blueEssence >= 3150: "SR"; elif difficulty == 3: "SSR";
#   elif difficulty == 2: "SR"; else "R"
```

### Stats (LoL flat → game, scaled by observed min/max across 170)
```python
# game_val = gmin + (lol_val - lmin) / (lmax - lmin) * (gmax - gmin)
STAT_RANGES = {  # (lol_min, lol_max, game_min, game_max) — computed once from all 170
    "hp":   (500, 700, 100, 160),    # health.flat
    "atk":  (50, 65, 18, 30),        # attackDamage.flat
    "defn": (15, 40, 10, 26),       # (armor.flat + magicResistance.flat)/2
    "spd":  (325, 355, 8, 19),       # movespeed.flat
    "mp":   (200, 500, 24, 42),      # mana.flat (non-mana resource -> 30)
}
# build: clamp + round to int; build bumps hp/defn by role_mult after scaling
```

### Skills (Q/W/E → 3 active shared skill ids by (element, type); R → element ult; P → passive)
```python
# For each element, the pool of shared skill ids by type:
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
# Map LoL ability spellEffects/damageType -> game type:
#   "Area of effect"/"aoe" + physical -> "aoe_attack"; + magic -> "aoe_magic"
#   "Single target" + physical -> "attack"; + magic -> "magic"
#   "spell" + buff/shield -> "buff"; heal keyword -> "heal"; cc/debuff -> "debuff"
# For each champ: Q/W/E -> pick 3 distinct skill ids from EL_SKILLS[element] by
#   the ability's mapped type (avoid duplicates; fall back to element's attack/magic).
# R -> EL_SKILLS[element]["ultimate"]. P -> passive by role (see PASSIVE_BY_ROLE).
PASSIVE_BY_ROLE = {
    "destruction": "p_adrenaline", "hunt": "p_crit", "erudition": "p_energy",
    "harmony": "p_regen", "nihility": "p_thorns", "preservation": "p_shield_low",
    "abundance": "p_regen",
}
SIGNATURE_BY_ROLE = {  # HERO_SIGNATURE, auto by role (flagship overrides in a separate table)
    "destruction": "s_kael_cleave", "hunt": "s_zephyr_stack", "erudition": "s_zephyr_stack",
    "harmony": "s_mira_shield", "nihility": "s_luna_revive", "preservation": "s_mira_shield",
    "abundance": "s_luna_revive",
}
```

### Descriptor (archetype/weapon/features/build/motif — drives the world sprite)
```python
# archetype from roles + attackType + faction theme:
ARCHETYPE_RULES = [
    # (predicate on champ, archetype)
    ("yordle", lambda c: c["faction"] == "bandle-city"),  # Lulu, Teemo, Tristana, Veigar...
    ("vastaya", lambda c: c["key"] in {"Ahri","Rakan","Xayah","Wukong","Sett","Rengar"}),
    ("construct", lambda c: c["key"] in {"Blitzcrank","Camille","Orianna","Velkoz","Malphite","Rammus","Zac","Galio"}),
    ("undead", lambda c: c["faction"] in {"shadow-isles"} or c["key"] in {"Mordekaiser","Hecarim","Yorick","Karthus","Thresh","Nocturne"}),
    ("beast", lambda c: c["key"] in {"Warwick","Nunu","Volibear","Udyr","RekSai","Belveth","Khazix","Rengar","Nidalee"}),
    ("brute", lambda c: "JUGGERNAUT" in c["roles"] or c["key"] in {"Darius","Garen","Sion","Urgot","DrMundo","Nasus","Renekton","Aatrox","Tryndamere","Olaf","Mordekaiser"}),
    ("mage", lambda c: "MAGE" in c["roles"] or c["key"] in {"Lux","Syndra","Veigar","Brand","Annie","Xerath","Ziggs","Orianna","Ahri"}),
    ("archer", lambda c: "MARKSMAN" in c["roles"] or c["key"] in {"Ashe","Jinx","Caitlyn","Ezreal","Varus","Vayne","Sivir","MissFortune","Tristana","Kaisa"}),
    ("rogue", lambda c: "ASSASSIN" in c["roles"] or c["key"] in {"Zed","Akali","Talon","Katarina","Khazix","Shaco","Ekko","Vex"}),
    ("knight", lambda c: True),  # fallback: armored melee (Garen, Leona, Poppy...)
]
# weapon from a keyword scan of the abilities' names + the champ's roles:
WEAPON_RULES = [  # (keyword in ability names or champ theme, weapon)
    ("bow", "bow"), ("arrow", "bow"), ("shot", "gun"), ("bullet", "gun"), ("cannon", "gun"),
    ("dagger", "dagger"), ("blade", "sword"), ("sword", "sword"), ("strike", "sword"),
    ("axe", "axe"), ("spear", "spear"), ("staff", "staff"), ("orb", "orb"),
    ("fist", "fists"), ("punch", "fists"), ("kick", "fists"), ("scythe", "scythe"),
    ("whip", "whip"), ("chain", "whip"), ("shield", "shield"), ("wand", "staff"),
    ("magic", "staff"), ("spell", "staff"), ("curse", "staff"),
]  # fallback: MELEE -> "sword", RANGED -> "bow", MAGE -> "staff"
# features/build/motif: derived from archetype + element + faction (see Task 3).
```

---

## Task 1: Build script — data extraction + champions.py

**Goal:** Write `build_champions.py` that reads all 170 `assets/champions/{Key}.json`, applies the mapping tables (element/role/rarity/stats/skills/passive/weapon/descriptor/lore/skins), and writes `champions.py` with `CHAMPIONS_DB` (list) + `CHAMPION_BY_KEY` (dict).

**Files:**
- Create: `build_champions.py`
- Create: `champions.py` (generated output)

**Acceptance Criteria:**
- [ ] `champions.py` has exactly 170 entries in `CHAMPIONS_DB`.
- [ ] Every entry has: `id, name, title, faction, element, rarity, role, stats{hp,atk,defn,spd,mp}, skills[3], ultimate, passive, weapon, archetype, descriptor{...}, lore{bio,quote,personality}, skins[{name,id}]`.
- [ ] Every `element` is one of fire/water/wind/light/dark.
- [ ] Every `role` is one of the 7 game roles.
- [ ] Every `rarity` is SSR/SR/R.
- [ ] Every `skills[i]` and `ultimate` is a key in `data.SKILLS_DB`.
- [ ] Every `passive` is a key in `data.PASSIVES_DB`.
- [ ] `stats` values are ints within the game ranges (hp 100-160, atk 18-30, defn 10-26, spd 8-19, mp 24-42).
- [ ] `skins` is a non-empty list (at least the Original skin, id 0).

**Verify:** `python3 build_champions.py && python3 -c "import champions; assert len(champions.CHAMPIONS_DB)==170; import data; [assert s in data.SKILLS_DB for c in champions.CHAMPIONS_DB for s in c['skills']+[c['ultimate']]]; print('OK')"` → `OK`

**Steps:**
- [ ] **Step 1:** Write `build_champions.py` with the mapping tables (element/role/rarity/stats/skills/passive/weapon/descriptor/lore) above + the JSON extraction. Compute the stat min/max across all 170 first, then scale. For each champ: extract fields, map element (FAC2EL + EL_OVERRIDE), role (ROLEMAP + POS2ROLE), rarity (SSR_CURATED + price), stats (scaled + role_mult), skills (Q/W/E → EL_SKILLS by ability type, R → ult, P → PASSIVE_BY_ROLE), weapon (WEAPON_RULES + fallback), archetype (ARCHETYPE_RULES), lore (bio=lore[:120] at sentence boundary, quote=title or first lore sentence, personality from attributeRatings), skins (from JSON skins, index = id % 1000, keep name + id).
- [ ] **Step 2:** Write `champions.py` output: `CHAMPIONS_DB = [...]`, `CHAMPION_BY_KEY = {c["id"]: c for c in CHAMPIONS_DB}`. Include a hand-tunable override section at the top (EL_OVERRIDE, SSR_CURATED, per-champ archetype/weapon/signature overrides).
- [ ] **Step 3:** Run + verify the AC. Commit.

## Task 2: Build script — image rearrange

**Goal:** Extend the build pipeline to rearrange the three source image dirs into `assets/characters/{Key}/` (portrait.jpg, icon.png, skins/*.jpg, skills/*.png via fuzzy ability-icon match), and delete the unused image files.

**Files:**
- Modify: `build_champions.py` (add the rearrange step)
- Create: `assets/characters/{Key}/portrait.jpg`, `icon.png`, `skins/{N}.jpg`, `skills/{skill_id}.png` for all 170

**Acceptance Criteria:**
- [ ] Every `assets/characters/{Key}/` has `portrait.jpg` (380×380), `icon.png` (128×128), `skins/0.jpg` (the Original), and `skills/{skill_id}.png` for each skill in the champ's kit (3 active + ult + basic_attack).
- [ ] `skills/{skill_id}.png` is the real LoL ability icon for the slot that skill_id fills (fuzzy-matched: passive/q/w/e/r keyword, base variant = no digit or lowest digit).
- [ ] No unused image files remain in `assets/champions_images/{Key}/` after rearrange (the source dirs are deleted in Task 9; this task only builds the bundle).
- [ ] Missing ability icons fall back to a placeholder (a solid 64×64 element-tinted square) so no `FileNotFoundError`.

**Verify:** `SDL_VIDEODRIVER=dummy python3 -c "import pygame,os; pygame.init(); pygame.display.set_mode((1,1)); import champions; [assert os.path.exists(f'assets/characters/{c[\"id\"]}/portrait.jpg') for c in champions.CHAMPIONS_DB]; print('OK', len(champions.CHAMPIONS_DB), 'portraits')"` → `OK 170 portraits`

**Steps:**
- [ ] **Step 1:** Add `rearrange_images(champ)` to `build_champions.py`: for each champ, `os.makedirs assets/characters/{Key}/{skills,skins}`; copy `{Key}.png` → `icon.png`; copy `splash_tile_0.jpg` → `portrait.jpg` + `skins/0.jpg`; for each skin N (splash_tile_{N}.jpg exists) → `skins/{N}.jpg`.
- [ ] **Step 2:** Add `match_ability_icon(champ, slot_keyword)` — glob `assets/champions_ability_icons/{key.lower()}/*.png`, filter by slot keyword (passive/q/w/e/r), pick base variant (no digit suffix, else lowest digit). Map: champ's Q/W/E/R skill_ids → the slots Q/W/E/R; basic_attack → no icon (or the P passive icon). Copy the matched icon → `skills/{skill_id}.png`. Fallback: generate a 64×64 element-tinted square if no match.
- [ ] **Step 3:** Run + verify the AC (headless pygame load of portrait.jpg for all 170). Commit.

## Task 3: Descriptor system + procedural world sprite

**Goal:** Rewrite `generate_assets.py` to drive the world sprite from the rich descriptor (archetype/weapon/palette/features/build/motif), with one distinct silhouette per archetype (10 archetypes), shared feature-adders + weapon-drawers, and generate `sprite.png` (256×256) per champ. Remove `make_portrait` (real splash replaces it). Keep `draw_skill_icon` as the fallback for missing ability icons.

**Files:**
- Modify: `generate_assets.py` (descriptor system + 10 archetype draw functions; drop `make_portrait`; keep `draw_skill_icon`)

**Acceptance Criteria:**
- [ ] `generate_assets.py` has `draw_chibi(surf, descriptor)` that dispatches to `draw_{archetype}` (knight/mage/archer/brute/rogue/undead/yordle/vastaya/construct/beast), each a distinct silhouette (different bbox/coverage).
- [ ] Shared helpers: `add_horns`, `add_wings`, `add_cape`, `add_mask`, `add_hood`, `add_crown`, `draw_weapon(surf, weapon, ...)` (sword/axe/bow/dagger/staff/spear/gun/fists/scythe/whip/orb/shield).
- [ ] The palette (primary/secondary/accent) + motif (flame/ice/wind/lightning/shadow/light/void/nature) drive the colors + an aura.
- [ ] Every champ's `sprite.png` is 256×256 with alpha; archetypes differ in coverage/bbox (a distinctness check: no two archetypes have identical coverage).
- [ ] `make_portrait` is removed (no caller — `verify_assets.py` was updated in the cleanup commit to not call it for the on-disk bundle; the real splash is the portrait now).

**Verify:** `SDL_VIDEODRIVER=dummy python3 -c "import pygame,generate_assets as GA; pygame.init(); pygame.display.set_mode((1,1)); s=pygame.Surface((256,256),pygame.SRCALPHA); GA.draw_chibi(s, {'archetype':'knight','weapon':'sword','palette':{'primary':(120,180,255),'secondary':(200,220,255),'accent':(255,255,255)},'features':['cape'],'build':'average','motif':'light'}); print('OK', s.get_size())"` → `OK (256, 256)`

**Steps:**
- [ ] **Step 1:** Define the descriptor schema + the `draw_chibi(surf, descriptor)` dispatcher. Define the palette/motif → color helpers (primary body, secondary trim, accent glow, motif aura).
- [ ] **Step 2:** Write the 10 archetype draw functions, each a distinct silhouette: `draw_knight` (armored, broad shoulders, helmet), `draw_mage` (robed, floating, staff), `draw_archer` (lean, bow arm), `draw_brute` (huge, hunched, big fists/weapon), `draw_rogue` (crouched, daggers, hood), `draw_undead` (tattered, wraith-like, floating), `draw_yordle` (tiny, big head), `draw_vastaya` (animal ears/tail + humanoid), `draw_construct` (angular, rocky/metallic), `draw_beast` (quadrupedal/feral posture). Each ~30-50 lines of pygame primitives (rects/ellipses/polygons) at PIXEL=5 chunky style.
- [ ] **Step 3:** Write the feature-adders (`add_horns`, `add_wings`, `add_cape`, `add_mask`, `add_hood`, `add_crown`) + `draw_weapon(surf, weapon, x, y, facing)` (one shape per weapon). Write the build scaler (slender/average/bulky/tall/short → vertical/horizontal scale).
- [ ] **Step 4:** Add `generate_sprites()` that iterates `champions.CHAMPIONS_DB`, builds the descriptor per champ (from the baked descriptor + the palette derived from the champ's icon mean color + element), calls `draw_chibi`, saves `assets/characters/{Key}/sprite.png`. Remove `make_portrait` + its callers.
- [ ] **Step 5:** Run + verify the AC (distinctness across archetypes). Commit.

## Task 4: Wire champions into data.py

**Goal:** Replace `HEROES_DB` with the 170 champions from `champions.py`; regenerate every cross-reference (GACHA_POOL/GACHA_BANNERS/STARTING_TEAM/HERO_PASSIVES/HERO_SIGNATURE/ULTIMATE_VARIANTS/CONSTELLATION_PERK_OVERRIDES/HERO_LORE/_HERO_SKILL_TEXT/WEAPON_STYLE_KEY) in lockstep.

**Files:**
- Modify: `data.py` (HEROES_DB + cross-references), `world_scene.py` (WEAPON_STYLE_KEY)

**Acceptance Criteria:**
- [ ] `HEROES_DB` has 170 entries built from `champions.CHAMPIONS_DB` (id/name/title/element/rarity/role/stats/skills/ultimate).
- [ ] `HERO_BY_ID` auto-derived (no KeyError for any STARTING_TEAM/gacha id).
- [ ] `GACHA_POOL` has every champ in the right rarity bucket; every `GACHA_BANNERS[i]["pool"][rarity]` is non-empty (no IndexError in `random.choice`).
- [ ] `STARTING_TEAM` = 4 iconic champs covering 4 elements (e.g. Ahri/wind, Lux/light, Garen/light... — pick a balanced 4: one fire, one water, one wind, one light). `STARTING_OWNED` = the 4 + 2 more.
- [ ] `HERO_PASSIVES`/`HERO_SIGNATURE`/`ULTIMATE_VARIANTS` cover every champ (auto by role + flagship overrides for ~12-30 iconic).
- [ ] `HERO_LORE` has bio/quote/personality for every champ (from champions.py).
- [ ] `_HERO_SKILL_TEXT` has (champ_id, skill_id) entries with the LoL ability name as description.
- [ ] `WEAPON_STYLE_KEY` (world_scene.py:5458) maps every champ id → the descriptor's weapon.
- [ ] `data.py` imports without error; `import data; len(data.HEROES_DB)` == 170.

**Verify:** `python3 -c "import data; assert len(data.HEROES_DB)==170; assert all(h['id'] in data.HERO_BY_ID for h in data.HEROES_DB); [data.GACHA_POOL[r] for r in 'SSR SR R'.split()]; print('OK')"` → `OK`

**Steps:**
- [ ] **Step 1:** In `data.py`, replace the `HEROES_DB` literal with a build from `champions.py`: `HEROES_DB = [dict(id=c["id"], name=c["name"], title=c["title"], element=c["element"], rarity=c["rarity"], role=c["role"], stats=c["stats"], skills=c["skills"], ultimate=c["ultimate"]) for c in champions.CHAMPIONS_DB]`. Keep `HERO_BY_ID = {h["id"]: h for h in HEROES_DB}`.
- [ ] **Step 2:** Regenerate `GACHA_POOL` from `HEROES_DB` grouped by rarity. Regenerate `GACHA_BANNERS`: standard (all), + 4 element-themed banners (fire/water/wind/light/dark — pick 5, each rate-ups an iconic SSR + SR of that element). Keep `GACHA_BANNER_BY_ID`.
- [ ] **Step 3:** Set `STARTING_TEAM` to 4 balanced iconic champs (e.g. `["Ahri","Lux","Garen","Ashe"]` — wind/light/light/water; or pick one per element). Set `STARTING_OWNED` = STARTING_TEAM + 2 more.
- [ ] **Step 4:** Build `HERO_PASSIVES` (auto by role via `PASSIVE_BY_ROLE` + flagship overrides), `HERO_SIGNATURE` (auto by role via `SIGNATURE_BY_ROLE` + flagship overrides), `ULTIMATE_VARIANTS` (auto by role: destruction→atk_buff_self, hunt→self_heal, erudition→knockback, harmony→energy_refund, nihility→self_heal, preservation→party_shield, abundance→energy_refund + flagship overrides), `CONSTELLATION_PERK_OVERRIDES` (flagship ~12). Build `HERO_LORE` from champions.py. Build `_HERO_SKILL_TEXT` from the LoL ability names.
- [ ] **Step 5:** In `world_scene.py`, replace `WEAPON_STYLE_KEY` with a dict built from `champions.CHAMPION_BY_KEY` (champ id → descriptor weapon), keeping the default "sword".
- [ ] **Step 6:** Run + verify the AC. Commit.

## Task 5: LoL-ify enemies + bosses

**Goal:** Replace `ENEMIES_DB` with LoL-themed mobs, `ROW_ENEMIES` with LoL mob pools + faction bosses, `BOSS_ULT`/`BOSS_PATTERNS`/`BOSS_IDS` with the new boss ids, and update the hardcoded ranged-id list + per-id AI in `world_entities.py`.

**Files:**
- Modify: `data.py` (ENEMIES_DB, BOSS_ULT, BOSS_PATTERNS, BOSS_IDS), `world_data.py` (ROW_ENEMIES), `world_entities.py` (ranged-id list at ~983, per-id AI quirks)

**Acceptance Criteria:**
- [ ] `ENEMIES_DB` has LoL mobs (Razorbeaks/Krugs/MurkWolves/Raptors/Voidlings/Wraiths/Gromp/CrimsonRaptor + the faction bosses) with valid stats/skills/weakness/toughness. Every skill id is in `SKILLS_DB`.
- [ ] `ROW_ENEMIES` maps rows 0-4 → (mob pool, boss id); every id is in `ENEMIES_DB`.
- [ ] `BOSS_ULT` maps the boss ids → the 4 boss-ult skill ids (hellfire/abyssal_wave/frost_cataclysm/storm_of_embers). `BOSS_IDS = set(BOSS_ULT)`.
- [ ] `BOSS_PATTERNS` per boss id (charge/slam by phase).
- [ ] The ranged-id list in `world_entities.py` (`self.ranged = self.id in (...)`) is updated to the new ranged mob ids.
- [ ] Per-id AI quirks (`self.id == "slime"` hop, `"wolf"` pounce, `"goblin"` kite) are updated to the new mob ids (or removed if no equivalent).
- [ ] Enemies spawn + fight in the world; boss ults fire below 50% HP; no KeyError.

**Verify:** `python3 -c "import data,world_data; assert all(e in data.ENEMIES_DB for row in world_data.ROW_ENEMIES.values() for e in row[0]+[row[1]]); assert all(b in data.BOSS_ULT for b in data.BOSS_IDS); print('OK')"` → `OK`

**Steps:**
- [ ] **Step 1:** Rewrite `ENEMIES_DB` with LoL mobs (keep the stat/toughness/weakness pattern; assign elements by mob theme: Razorbeaks=wind, Krugs=fire, MurkWolves=wind, Raptors=fire, Voidlings=dark, Wraiths=dark, Gromp=water). Add the faction bosses (Sylas/Swain/Lissandra/Mordekaiser/Baron) with boss-tier stats. Every skill id in `SKILLS_DB`.
- [ ] **Step 2:** Rewrite `ROW_ENEMIES` (world_data.py): row 0 plains → (Razorbeaks/Krugs/MurkWolves, Sylas); row 1 forest → (Raptors/MurkWolves/Krugs, Swain); row 2 cave → (Voidlings/Wraiths/Gromp, Lissandra); row 3 castle → (Wraiths/Voidlings, Mordekaiser); row 4 void → (Voidlings/Wraiths, Baron).
- [ ] **Step 3:** Rewrite `BOSS_ULT` (Sylas→abyssal_wave, Swain→abyssal_wave, Lissandra→frost_cataclysm, Mordekaiser→storm_of_embers, Baron→hellfire) + `BOSS_PATTERNS` + `BOSS_IDS`.
- [ ] **Step 4:** In `world_entities.py`, update the ranged-id list (`self.ranged = self.id in ("Razorbeaks","Wraiths","Voidlings","Baron",...)`) + the per-id AI quirks (map the old slime/wolf/goblin behaviors to the new mob ids, or generic).
- [ ] **Step 5:** Run + verify the AC. Commit.

## Task 6: Faction story

**Goal:** Rewrite `STORY_QUESTS`/`NPCS`/`STORY_*` lookups to be faction-based (6 faction conflicts, each ending in a LoL villain boss), aligned with the new boss ids from Task 5.

**Files:**
- Modify: `data.py` (STORY_QUESTS, NPCS, STORY_QUEST_BY_ID, STORY_QUEST_ORDER, STORY_BIOME_QUEST, STORY_FINAL_QUEST)

**Acceptance Criteria:**
- [ ] `STORY_QUESTS` has 6 quests (Demacia/Noxus/Freljord/Ionia/ShadowIsles/Void), each with a giver biome + a boss objective matching the Task-5 boss ids.
- [ ] `NPCS` has one NPC per biome with faction-flavored dialogue + the quest_id.
- [ ] `STORY_QUEST_BY_ID`/`STORY_QUEST_ORDER`/`STORY_BIOME_QUEST`/`STORY_FINAL_QUEST` are consistent with `STORY_QUESTS`.
- [ ] The story chain works: a quest is available when the previous is complete; the boss cell is sealed until the biome quest is active; the final boss is sealed until all 5 are done.

**Verify:** `python3 -c "import data; assert len(data.STORY_QUESTS)==6; assert all(q['id'] in data.STORY_QUEST_BY_ID for q in data.STORY_QUESTS); print('OK')"` → `OK`

**Steps:**
- [ ] **Step 1:** Rewrite `STORY_QUESTS` (6 faction quests, givers = the 5 biomes + void for the final). Boss objectives = the Task-5 boss ids. Lore = faction conflict one-liners.
- [ ] **Step 2:** Rewrite `NPCS` (one per biome, faction-flavored names + dialogue + quest_id matching STORY_QUESTS).
- [ ] **Step 3:** Regenerate `STORY_QUEST_BY_ID`/`STORY_QUEST_ORDER`/`STORY_BIOME_QUEST`/`STORY_FINAL_QUEST`.
- [ ] **Step 4:** Run + verify the AC. Commit.

## Task 7: Skin system

**Goal:** Add the per-champion skin system: `load_portrait(hero_id, skin_idx)` loads `skins/{skin_idx}.jpg` (default 0 → `portrait.jpg`); the hero-detail screen (`main.py`) has a skin selector; the gacha roll reveal (`main.py`/`gacha.py`) shows the rolled skin's splash.

**Files:**
- Modify: `entities.py` (`load_portrait` signature + `.jpg`), `main.py` (hero-detail skin selector + codex + roll reveal), `gacha.py` (roll reveal skin), `player.py` (skin on the hero record)

**Acceptance Criteria:**
- [ ] `load_portrait(hero_id, skin_idx=0, size=440)` loads `assets/characters/{Key}/skins/{skin_idx}.jpg` (skin_idx 0 → `portrait.jpg`), returns a converted surface. No `FileNotFoundError`.
- [ ] The hero record (`player.py`) has a `skin` field (default 0).
- [ ] The hero-detail screen (`main.py`) shows the equipped skin's portrait + a skin selector (left/right arrows cycle skins; shows the skin name).
- [ ] The gacha roll reveal shows the rolled skin's splash (the new pull's skin, default 0).
- [ ] The codex (`main.py`) shows the default-skin portrait per champ.

**Verify:** `SDL_VIDEODRIVER=dummy python3 -c "import pygame,entities; pygame.init(); pygame.display.set_mode((1,1)); s=entities.load_portrait('Ahri',0); print('OK', s.get_size())"` → `OK (440, 440)` (or the loaded size scaled)

**Steps:**
- [ ] **Step 1:** In `entities.py`, update `load_portrait(hero_id, skin_idx=0, size=440)`: path = `characters/{Key}/skins/{skin_idx}.jpg` (skin_idx 0 → `characters/{Key}/portrait.jpg`); `pygame.image.load` + `.convert()` (jpg has no alpha; `.convert()` is fine) + scale. Keep the `_load_first` fallback for the old flat layout (harmless).
- [ ] **Step 2:** In `player.py`, add `skin` to the hero record (default 0); load migration adds `skin=0` to old records.
- [ ] **Step 3:** In `main.py` hero-detail scene, add a skin selector (cycle `skins` via left/right; show the skin name + the equipped portrait). In the codex, show the default-skin portrait. In the roll reveal, show the rolled skin's splash.
- [ ] **Step 4:** In `gacha.py`, the roll reveal passes the skin to the reveal UI.
- [ ] **Step 5:** Run + verify the AC. Commit.

## Task 8: Loaders + verify_assets

**Goal:** Update `entities.py` loaders for the new bundle layout (`.jpg` portrait, `icon.png`, real skill icons) + rewrite `verify_assets.py` for the new bundle layout.

**Files:**
- Modify: `entities.py` (`load_char_sprite`, `load_portrait`, `load_skill_icon`, add `load_champ_icon`), `verify_assets.py`

**Acceptance Criteria:**
- [ ] `load_char_sprite(hero_id)` → `characters/{Key}/sprite.png` (256×256). No error.
- [ ] `load_portrait(hero_id, skin_idx=0)` → `characters/{Key}/skins/{skin_idx}.jpg` (or `portrait.jpg`). No error.
- [ ] `load_skill_icon(hero_id, skill_id)` → `characters/{Key}/skills/{skill_id}.png` (64×64). No error.
- [ ] `load_champ_icon(hero_id)` → `characters/{Key}/icon.png` (128×128) — new loader for the HUD/codex thumbnail.
- [ ] `verify_assets.py` checks every champ has sprite.png (256×256), portrait.jpg (380×380), icon.png (128×128), skills/{skill_id}.png (64×64) for each kit skill, skins/{N}.jpg. No missing files. Per-skill distinctness (real icons differ across champs). Procedural sprite distinctness across archetypes.
- [ ] `verify_assets.py` runs clean under `SDL_VIDEODRIVER=dummy`.

**Verify:** `SDL_VIDEODRIVER=dummy python3 verify_assets.py` → `OK — all rendered without error, sizes unchanged.` (no FAIL lines)

**Steps:**
- [ ] **Step 1:** In `entities.py`, update `load_char_sprite` (path `characters/{Key}/sprite.png`), `load_portrait` (Task 7), `load_skill_icon` (unchanged path, works for the real 64×64 icons), add `load_champ_icon(hero_id, size=128)` → `characters/{Key}/icon.png`.
- [ ] **Step 2:** Rewrite `verify_assets.py` for the new bundle: iterate `champions.CHAMPIONS_DB`; check sprite.png (256×256), portrait.jpg (380×380), icon.png (128×128), skills/{skill_id}.png (64×64) for each kit skill, skins/{N}.jpg exists. Distinctness: real skill icons differ across champs for a shared skill_id; procedural sprites differ across archetypes. Use headless pygame (no Read tool).
- [ ] **Step 3:** Run + verify the AC. Commit.

## Task 9: Verify + cleanup

**Goal:** Run the full verification (acceptance suite + 1200-frame headless stress both modes), then delete the three crawled source dirs.

**Files:**
- Delete: `assets/champions/`, `assets/champions_images/`, `assets/champions_ability_icons/`

**Acceptance Criteria:**
- [ ] `verify_assets.py` passes (no FAIL).
- [ ] The acceptance suite (21 tests) passes.
- [ ] 1200-frame headless stress, endless + adventure modes, ≥60 fps, no crash.
- [ ] The gacha pulls a valid champ from every banner at every rarity (no IndexError).
- [ ] `STARTING_TEAM` champs all exist + have bundles.
- [ ] The three source dirs are deleted; `git status` shows the deletions; the repo's tracked image count is sane (sprites + icons + skill icons + skins + portraits).

**Verify:**
- `SDL_VIDEODRIVER=dummy python3 verify_assets.py` → OK
- The acceptance suite (`/tmp` bench, 21 tests) → all pass
- `xvfb-run -a python3 <stress script>` both modes → ≥60 fps, no crash
- `python3 -c "import gacha,data,player; p=player.Player(); g=gacha.GachaSystem(); [g.apply_result(p, g.pull(b,1)[0]) for b in data.GACHA_BANNERS for _ in range(10)]; print('OK')"` → OK
- `rm -rf assets/champions assets/champions_images assets/champions_ability_icons` + `git status`

**Steps:**
- [ ] **Step 1:** Run `verify_assets.py` (headless). Fix any FAIL.
- [ ] **Step 2:** Run the acceptance suite (21 tests). Fix any failure.
- [ ] **Step 3:** Run the 1200-frame headless stress both modes. Fix any crash/fps regression.
- [ ] **Step 4:** Run the gacha smoke test (pull from every banner). Fix any IndexError.
- [ ] **Step 5:** Delete the three source dirs. Commit. Report the final tracked-image count.

---

## Self-Review (run after writing the plan)

**1. Spec coverage:** Every spec section (§1-§12) maps to a task: §1-2 (data sources) → Task 1-2; §3 (descriptor) → Task 3; §4 (mapping) → Tasks 1+4; §5 (element/role/rarity) → Task 1; §6 (story) → Task 6; §7 (enemies/boss) → Task 5; §8 (cross-refs) → Task 4; §9 (build pipeline) → Tasks 1-2; §10 (verify) → Task 9; §11 (decomposition) → the 9 tasks; §12 (non-goals) → preserved (no task adds new mechanics). ✓

**2. Placeholder scan:** No "TBD"/"TODO". The mapping tables are concrete. The archetype draw functions (Task 3 Step 2) list the 10 archetypes + their silhouette spec + the test — the pixel-drawing code is the implementer's mechanical work (the interface + silhouette spec + test are the spec, not a placeholder). ✓

**3. Type consistency:** `CHAMPIONS_DB`/`CHAMPION_BY_KEY` (Task 1) → consumed by Tasks 2,3,4,8. `descriptor` fields (archetype/weapon/palette/features/build/motif) consistent across Tasks 1,3,4. `load_portrait(hero_id, skin_idx=0)` consistent across Tasks 7,8. Boss ids (Task 5) consumed by Task 6. ✓

**4. Dependency order:** 1 → (2, 3, 4); 4 → (5, 6, 7); 5 → 6; (2, 7) → 8; all → 9. No cycle. ✓

**5. Risk:** The highest-risk task is Task 4 (wiring 170 champs into data.py without a stale cross-reference). The AC + verify catch every KeyError/IndexError. The graceful fallbacks (audit) protect against partial misses. Task 9 is the final gate. ✓
