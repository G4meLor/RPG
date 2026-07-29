# LoL Roster Redesign — Design Spec

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:subagent-driven-development (recommended) or superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 25 generic procedural heroes with 170 real League of Legends champions — real splash art for all UI, real ability icons for skills, a per-champion skin system, faction-linked story, and LoL-ified enemies/bosses — while preserving the entire combat/gacha/evo/constellation runtime.

**Architecture:** A one-shot build script (`build_champions.py`) reads the three crawled LoL data dirs, maps each champion to the game's data model (element/role/rarity/stats/skills/lore/descriptor), bakes the result into a new `champions.py`, rearranges the real images into the per-champion bundle layout, generates the one remaining procedural asset (the world sprite) via a descriptor-driven rewrite of `generate_assets.py`, updates every cross-reference in `data.py` and the scene/runtime, then deletes the three source dirs. The game's combat, gacha, evo, constellation, and story systems are preserved verbatim — only the roster contents and the art sources change.

**Tech Stack:** Python 3.11, pygame 2.6, numpy; pure-procedural art for the world sprite only; real LoL PNG/JPG assets (loaded via pygame, never via the Read tool).

**User decisions (already made):**
- Use all 170 LoL champions (data crawled into `assets/champions/`, `assets/champions_images/`, `assets/champions_ability_icons/`).
- Use LoL champion names directly (display `name` from JSON; `key` as the id).
- LoL-ify both enemies and bosses.
- Do all 170 at once (no 12→170 phasing) — real art removes the "is the art distinct?" risk.
- Use the real splash_tile images directly for portrait/roll/skins.
- Use the real ability icons for skill icons (fuzzy-matched per slot).
- User delegated all remaining decisions: "bạn tự quyết toàn bộ các bước còn lại… tự viết spec, tự review, tự viết plan, tự review rồi implement luôn theo đúng chuẩn của skill superpowers mà không cần hỏi lại… Bạn có thể dùng workflows."

---

## 1. The three crawled data sources

All keyed by the LoL `key` field (sanitized name: `Ahri`, `MissFortune`, `KSante`, `Chogath`). Verified: 170 JSONs ↔ 170 image dirs ↔ 170 non-jade ability-icon dirs, all 1:1 by lowercased key.

### `assets/champions/{Key}.json` — the data source
Fields used: `id`(int), `key`(str, the id), `name`(str, display, may have spaces/apostrophes), `title`(str), `faction`(str: demacia/noxus/ionia/freljord/shurima/void/shadow-isles/piltover/zaun/bilgewater/ixtal/mount-targon/bandle-city/unaffiliated), `lore`(str, full bio), `stats`(dict: health/mana/armor/magicResistance/attackDamage/movespeed/attackRange/attackSpeed, each `{flat, perLevel}`), `positions`([TOP/JUNGLE/MIDDLE/BOTTOM/SUPPORT]), `roles`([MAGE/FIGHTER/ASSASSIN/TANK/SUPPORT/MARKSMAN/DIVER/JUGGERNAUT/SKIRMISHER/ARTILLERY/BATTLEMAGE/BURST/VANGUARD/WARDEN/ENCHANTER/CATCHER/SPECIALIST]), `adaptiveType`(PHYSICAL_DAMAGE/MAGIC_DAMAGE), `attackType`(MELEE/RANGED), `attributeRatings`(dict: damage/toughness/control/mobility/utility/difficulty, each 1-3), `abilities`(dict: P/Q/W/E/R, each a list of one ability `{name, effects, cost, cooldown, damageType, spellEffects}`), `skins`(list of `{name, id, isBase, rarity, cost}`).

### `assets/champions_images/{Key}/` — splash art
- `{Key}.png` — 128×128, NO alpha, dark bg ~(0,0,5). The champion icon. → `icon.png`.
- `{key_lower}_splash_tile_{N}.jpg` — 380×380 square, champ-centered, ~18/champ. **The usable one.** `N = skin_id % 1000` (verified: Ahri skin 103014 → splash_tile_14.jpg). `_0` = Original skin. → `portrait.jpg` (for N=0) and `skins/{N}.jpg` (for each skin).
- `{key_lower}_splash_centered_{N}.jpg` (1280×720), `_uncentered_{N}.jpg` (~1215×717), `{key}loadscreen_{N}.jpg` (308×560), `{skinId}.png` (270×303) — all DELETE.

### `assets/champions_ability_icons/{key.lower()}/` — ability icons
- 64×64 PNG per ability. Naming inconsistent (`aatrox_q`, `icons_ahri_q`, `garen_q`, `jinx_q1`). Multi-variant per slot (aatrox 3 Q, jinx 2 Q). Fuzzy match by slot keyword (passive/q/w/e/r), pick base variant (no digit suffix, or lowest digit). → `skills/{skill_id}.png` for the skill_id that fills that slot.
- Ignore `jade_*` (skin-specific) + extras (`locke`, `zaahen`, `yunara`).

## 2. Target bundle layout (per champion)

```
assets/characters/{Key}/
  sprite.png      procedural 256×256 (world billboard, descriptor-driven, ~10 archetypes)
  portrait.jpg    real splash_tile_0 (380×380, default skin)
  icon.png        real {Key}.png (128×128, HUD/codex thumbnail)
  skills/
    {skill_id}.png  real ability icon (64×64) for the slot that skill_id fills
  skins/
    {N}.jpg       real splash_tile_{N} (skin art; N = skin_id % 1000; 0 = Original)
```

The loader signatures are unchanged: `load_char_sprite(hero_id)` → `characters/{Key}/sprite.png`; `load_portrait(hero_id)` → `characters/{Key}/portrait.jpg` (updated to try `.jpg`); `load_skill_icon(hero_id, skill_id)` → `characters/{Key}/skills/{skill_id}.png`. Each champion's skill icons are the real LoL ability icons for that champion's slots, so the same `skill_id` on two champions has different (real) icons — the existing per-skill distinctness is preserved and strengthened.

## 3. Champion descriptor (the world sprite)

The procedural world sprite is the only remaining procedural art. The current `draw_chibi`/`make_portrait` uses one chibi silhouette + a color swap, which is why "characters all look alike." The rewrite drives the sprite from a rich descriptor so each champion's 96px billboard is visually distinct.

Descriptor fields (derived from the JSON by the build script):
- `archetype`: one of `knight`, `mage`, `archer`, `brute`, `rogue`, `undead`, `yordle`, `vastaya`, `construct`, `beast` — derived from roles + attackType + faction theme.
- `weapon`: one of `sword`, `axe`, `bow`, `dagger`, `staff`, `spear`, `gun`, `fists`, `scythe`, `whip`, `orb`, `shield`, `none` — derived from abilities + theme.
- `palette`: `(primary, secondary, accent)` RGB — derived from faction + adaptiveType + the champion's icon mean color.
- `features`: 0-3 of `horns`, `wings`, `cape`, `mask`, `crown`, `halo`, `veil`, `hood`, `spikes`, `helmet` — derived from theme.
- `build`: `slender`/`average`/`bulky`/`tall`/`short` — derived from stats (health/size).
- `motif`: `flame`/`ice`/`wind`/`lightning`/`shadow`/`light`/`void`/`nature` — derived from element + signature ability.

`generate_assets.py` gains one draw function per archetype (`draw_knight`, `draw_mage`, `draw_archer`, `draw_brute`, `draw_rogue`, `draw_undead`, `draw_yordle`, `draw_vastaya`, `draw_construct`, `draw_beast`), each a distinct silhouette; shared feature-adders (`add_horns`, `add_wings`, `add_cape`, `add_mask`, ...); shared weapon-drawers (`draw_sword`, `draw_bow`, ...); the palette + motif drive colors + an aura. `make_portrait` (the procedural 512×512) is removed — real splash replaces it.

## 4. Stat / skill / lore / skin mapping

### Stats (LoL → game, scaled)
- `hp` ← `stats.health.flat` scaled to ~100-160 by `build` (bulky→160, slender→100, linear in between).
- `atk` ← `stats.attackDamage.flat` scaled to ~18-30.
- `defn` ← `(stats.armor.flat + stats.magicResistance.flat) / 2` scaled to ~10-26.
- `spd` ← `stats.movespeed.flat` scaled to ~8-19.
- `mp` ← `stats.mana.flat` scaled to ~24-42 (non-mana resources → fixed 30).

Scaling: `game_val = min + (lol_val - lol_min) / (lol_max - lol_min) * (game_max - game_min)`, with `lol_min`/`lol_max` the observed min/max across all 170 champions (computed once by the build script).

### Skills (Q/W/E → 3 active, R → ult, P → passive, + basic_attack)
The game's combat is tuned around ~40 skill ids in `SKILLS_DB`. Each champion's Q/W/E/R map to shared skill ids by `(element, type)`; the **displayed name is the LoL ability name**; the **icon is the real LoL ability icon** for that slot. So the same `skill_id` on two champions has different name + icon but the same tuned mechanics — balanced combat, per-champion flavor + art.

Mapping by LoL ability `spellEffects`/`damageType`:
- single-target + physical → `attack` (e.g. `fire_slash`, `wind_arrow`).
- single-target + magic → `magic` (e.g. `fire_bolt`, `water_bolt`).
- aoe + physical → `aoe_attack`; aoe + magic → `aoe_magic` (e.g. `inferno`, `tidal_wave`).
- buff/shield → `buff`; heal → `heal`; debuff/cc → `debuff`.
- R → `ultimate` (e.g. `meteor`, `tsunami`, `void_nova`, `light_hymn`).
- P → `HERO_PASSIVES` (signature passive, ~15-20 templates by role/theme).
- basic_attack → from `attackType` (melee → `basic_attack`, ranged → `basic_attack` with a projectile flag).

The build script picks, for each champion, 3 active skill ids from `SKILLS_DB` matching `(element, type)` derived from the champion's Q/W/E abilities; if an ability's type isn't represented for the element, fall back to the element's default attack/magic. The ultimate is the element's ultimate. This guarantees every champion has a valid, tuned kit.

### Lore (from JSON)
- `bio` ← `lore` (truncated to ~120 chars at a sentence boundary).
- `quote` ← a flavor line: for the curated flagship set, hand-picked; for the rest, derived from the lore's first sentence or the champion's `title`.
- `personality` ← from `attributeRatings` (damage≥3→fierce, utility≥3→gentle, mobility≥3→restless, else stoic) or `roles` (assassin→cold, support→gentle).
- `faction` ← the LoL faction (for story grouping).

### Skins (new feature)
Each champion has N skins (the `splash_tile` variants). Skin metadata (name, rarity) from the JSON `skins` array, indexed by `skin_id % 1000`. The equipped skin changes the portrait + roll art + (optionally) a palette tint on the world sprite. Stored on the hero record (`rec["skin"]`, default 0). `load_portrait(hero_id, skin_idx)` loads `skins/{skin_idx}.jpg` (default 0 → `portrait.jpg`). The gacha roll reveal shows the rolled skin's splash. The hero-detail screen has a skin selector.

## 5. Element + role + rarity mapping

### Element (5: fire/water/wind/light/dark — chart + reactions preserved)
Default by faction: fire = noxus/shurima; water = freljord/bilgewater; wind = ionia/ixtal/bandle-city; light = demacia/piltover/mount-targon; dark = zaun/void/shadow-isles/unaffiliated. A theme-override table (~30-40 entries) fixes obviously-mismatched champions (Brand→fire, Annie→fire, Aatrox→fire, Anivia→water, AurelionSol→light, Nami→water, etc.). The override table lives in the build script's hand-tunable section.

### Role (7 HSR roles — preserved; stat profiles + evo trees + constellations)
Map LoL roles → game roles: JUGGERNAUT/DIVER → destruction; ASSASSIN/MARKSMAN/SKIRMISHER → hunt; MAGE/ARTILLERY/BATTLEMAGE/BURST/SPECIALIST → erudition; SUPPORT/CATCHER → harmony (or nihility for debuff-heavy catchers); TANK/VANGUARD/WARDEN → preservation; ENCHANTER → abundance. First matching LoL role wins; fallback by primary position (TOP→preservation, JUNGLE→hunt, MIDDLE→erudition, BOTTOM→hunt, SUPPORT→abundance). `role_mult`, `EVO_TREE`, `CONSTELLATION_PERKS` handle unknown roles gracefully (1.0 / default tree / destruction perks).

### Rarity (SSR/SR/R — gacha pool + UI)
A curated SSR set (~30 iconic champions: Ahri, Yasuo, Jinx, Lux, Garen, Thresh, Lee Sin, Jhin, Kai'Sa, Ezreal, Zed, Darius, Ashe, Lissandra, Brand, Veigar, Teemo, Riven, Syndra, Aurelion Sol, Mordekaiser, Swain, Sylas, Viego, Volibear, Ornn, Kindred, Bard, Pyke, Shaco). The rest by `price.blueEssence` tier: 480/1350 → R, 3150 → SR, 4800/6300/7800 → SSR; or by `attributeRatings.difficulty` (3→SSR, 2→SR, 1→R) if price is missing. The build script's override section holds the curated SSR list.

## 6. Story (faction-linked)

Six story quests, each a faction conflict ending in a LoL villain boss:
1. Demacia (light) → boss Sylas (the traitor).
2. Noxus (fire) → boss Swain (the noxian general).
3. Freljord (water) → boss Lissandra (the ice witch).
4. Ionia (wind) → boss the Noxus invasion (cross-faction; a noxian brute).
5. Shadow Isles (dark) → boss Mordekaiser (the Ruined King).
6. Void (dark) → boss Baron Nashor (the final).

Each champion's lore references its faction + the conflict. The codex groups champions by faction. `STORY_QUESTS`, `STORY_QUEST_BY_ID`, `STORY_BIOME_QUEST`, `STORY_FINAL_QUEST` are regenerated from the faction set. Boss intro/defeat cinematics use the boss's `name` from `ENEMIES_DB`.

## 7. Enemies + bosses (LoL-ified)

### Enemies (replace slime/goblin/wolf/orc/bat/skeleton/golem)
LoL jungle mobs + faction mobs: Razorbeaks (wind), Krugs (fire), Murk Wolves (wind), Raptors (fire), Voidlings (void/dark), Wraiths (shadow-isles/dark), Gromp (water), Crimson Raptor (fire). `ENEMIES_DB` rewritten with LoL mob stats + skills + weakness + toughness. `ROW_ENEMIES` (world_data.py) rewritten to map biomes → LoL mob pools + faction bosses. The hardcoded ranged-id list (`world_entities.py:983`) and per-id AI quirks (slime hop, wolf pounce, goblin kite) are updated to the new mob ids.

### Bosses (keep the 4 boss ults, LoL-ify the boss ids)
`BOSS_ULT` maps the new boss ids → the 4 boss-ult skill ids (hellfire/abyssal_wave/frost_cataclysm/storm_of_embers). Boss ids: Dragon, Baron, RiftHerald, Vilemaw (or the faction villains Sylas/Swain/Lissandra/Mordekaiser as open-world bosses, with the 4 ults mapped onto them). `BOSS_PATTERNS` per boss id. The boss sprite uses the real art where available (a boss splash) or a procedural boss sprite.

## 8. Cross-references to update (the audit's safety checklist)

Every one of these is regenerated/updated by the build script in lockstep with `HEROES_DB`:
1. `HEROES_DB` (data.py:715) — the list of champion dicts.
2. `HERO_BY_ID` — auto-derived.
3. `HERO_PASSIVES` (data.py:257) — champion_id → passive_id (auto by role + flagship overrides).
4. `HERO_SIGNATURE` (data.py:280) — champion_id → signature_id (auto by role + flagship).
5. `ULTIMATE_VARIANTS` (data.py:837) — champion_id → variant (auto by role + flagship).
6. `CONSTELLATION_PERK_OVERRIDES` (data.py:1216) — flagship only.
7. `GACHA_POOL` (data.py:1017) + every `GACHA_BANNERS[i]["pool"]` (data.py:1033) — champion ids by rarity per banner (auto by element-themed banners).
8. `STARTING_TEAM` (data.py:1741) — 4 iconic champion ids (Ahri, Lux, Garen, Darius — or a balanced 4-element starter).
9. `_HERO_SKILL_TEXT` (data.py:1309) — (champion_id, skill_id) → the LoL ability description.
10. `HERO_LORE` (data.py:894) — champion_id → bio/quote/personality (from JSON).
11. `WEAPON_STYLE_KEY` (world_scene.py:5458) — champion_id → weapon (from the descriptor's weapon).
12. `SKILLS_DB` — any new skill ids must exist; the build reuses existing ids so no new ids are needed (except possibly enemy skills).
13. `assets/characters/{Key}/` bundle — sprite.png, portrait.jpg, icon.png, skills/*.png, skins/*.jpg.
14. `ENEMIES_DB`, `ROW_ENEMIES`, `BOSS_ULT`, `BOSS_PATTERNS`, `BOSS_IDS` — LoL-ified.
15. `STORY_QUESTS`, `STORY_QUEST_BY_ID`, `STORY_BIOME_QUEST`, `STORY_FINAL_QUEST`, `NPCS` — faction-based.

Graceful fallbacks (from the audit) protect against partial mismatches: `hero_abilities` pads to 3; `WEAPON_STYLE_KEY` defaults to sword; `HERO_ASSETS`/`HERO_LORE` fall back; `role_mult` returns 1.0; `EVO_TREE`/`CONSTELLATION_PERKS` fall back. Hard failure points (KeyErrors on `HERO_BY_ID`/`SKILLS_DB`/`ENEMIES_DB`, IndexError on empty gacha pools, FileNotFoundError on missing portraits) are covered by the build script generating every entry + the verifier.

## 9. Build pipeline (`build_champions.py`)

1. Read all 170 `assets/champions/{Key}.json` → extract fields.
2. Map → game fields (element/role/rarity/stats/skills/passive/weapon/descriptor/lore/skins) using the mapping tables + override section.
3. Write `champions.py` (`CHAMPIONS_DB` list, `CHAMPION_BY_KEY` dict, skin metadata, the descriptor per champion). The override section (element/role/rarity/signature/weapon/archetype overrides) is hand-tunable at the top.
4. Rearrange images: for each champion, copy `splash_tile_{N}.jpg` → `skins/{N}.jpg` + `portrait.jpg` (N=0); `{Key}.png` → `icon.png`; fuzzy-match the ability icons → `skills/{skill_id}.png`. Delete the rest of each image dir.
5. Generate the procedural world sprite: `generate_assets.py` (descriptor-driven rewrite) → `sprite.png` per champion.
6. Update `data.py`: `HEROES_DB` ← from `champions.py`; regenerate `GACHA_POOL`/`GACHA_BANNERS`; `STARTING_TEAM`; `HERO_PASSIVES`/`HERO_SIGNATURE`/`ULTIMATE_VARIANTS`/`CONSTELLATION_PERK_OVERRIDES`; `HERO_LORE`; `_HERO_SKILL_TEXT`; `WEAPON_STYLE_KEY`; story quests; `ENEMIES_DB`/`ROW_ENEMIES`/`BOSS_ULT`/`BOSS_PATTERNS`.
7. Update `entities.py` loaders: `load_portrait` tries `.jpg` + `skins/{skin_idx}.jpg`; `load_skill_icon` unchanged (per-hero path).
8. Update `verify_assets.py` for the new bundle layout (`.jpg` portrait, `skins/`, `icon.png`, real skill icons).
9. Delete the three source dirs (`assets/champions/`, `assets/champions_images/`, `assets/champions_ability_icons/`).
10. Verify: `verify_assets.py` (headless), the acceptance suite, 1200-frame stress both modes.

## 10. Verification

- `verify_assets.py` (updated): every champion has `sprite.png` (256×256), `portrait.jpg` (380×380), `icon.png` (128×128), `skills/{skill_id}.png` (64×64) for each skill in the kit, `skins/{N}.jpg` for each skin. No missing files. Real skill icons are distinct across champions (per-skill distinctness check). The procedural sprites are distinct across archetypes.
- The acceptance suite (21 tests) passes.
- 1200-frame headless stress, both endless and adventure modes, ≥60 fps.
- The gacha pulls a valid champion from every banner at every rarity (no IndexError).
- `STARTING_TEAM` champions all exist in `HEROES_DB` + have bundles.

## 11. Scope/decomposition

This is a large change touching data.py, generate_assets.py, entities.py, world_scene.py, world_entities.py, world_data.py, main.py, gacha.py, verify_assets.py, + a new build_champions.py + champions.py. It decomposes into:
- **A. Build script + data bake** (build_champions.py, champions.py): the mapping + data generation.
- **B. Image rearrange** (the bundle layout + delete sources): the asset pipeline.
- **C. Procedural sprite rewrite** (generate_assets.py descriptor system): the world sprite.
- **D. Runtime cross-reference update** (data.py, entities.py, world_scene.py, world_entities.py, world_data.py, gacha.py, main.py): wire the new roster in.
- **E. Enemy/boss LoL-ify** (data.py, world_data.py, world_entities.py): the mobs + bosses.
- **F. Skin system** (entities.py, main.py, world_scene.py): the skin selector + roll reveal.
- **G. Verify + cleanup** (verify_assets.py, acceptance suite, delete source dirs).

Each is a testable, committable unit. The build script (A) is the foundation; B-F depend on it; G is last.

## 12. Non-goals

- No new combat mechanics, no new skill types, no new elements, no new roles. The combat/gacha/evo/constellation systems are preserved verbatim.
- No new game scenes. The existing scenes are updated to read the new roster.
- No real art for the world sprite (procedural descriptor-driven only).
- No ability-icon download (the crawled icons are used as-is; missing icons fall back to procedural).
