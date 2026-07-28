# Aetheria — Big Bang v2 Enhancement (Design)

Date: 2026-07-28
Status: Drafted — awaiting user review
Origin: user playtest feedback + a 4-agent codebase survey (party/char system, skill system, world gen/loot/boss, asset structure). Builds on v1 (28 commits, 23 tasks, 5 gates — all green on branch `worktree-big-bang`).

## Vision

v1 shipped the combat engine (DoT, toughness-break, combo climax, hit-stop), hero identity (constellations, signature passives, ult variants, lore), world atmosphere (weather, breakables, rifts, torchlight), and the meta loop (NG+, resonance, gacha crescendo). v2 targets the **structural gaps the user flagged in the second playtest**:

1. **No mode structure** — the game is one flat open world; there is no Adventure (wave-survival) vs Endless (open-world) split.
2. **No auto-attack** — the LoL verb is missing; the player must press J for every basic attack, and RMB only moves.
3. **Skills fire blind** — no hover tooltip, no hold-to-aim preview; the player can't read what a skill does or see its range/AoE before casting.
4. **Mana doesn't visibly recover** — v1 added a regen but the user still feels it not increasing.
5. **Drops vanish into inventory** — no ground loot, no walk-over pickups; loot feels immaterial.
6. **Art is soft-gradient, not pixel-art** — the user wants a Stardew-like pixel-art aesthetic at higher pixel density, with per-character asset bundles.
7. **The open world has no story direction** — no NPCs, no quest chain, no narrative; bosses appear without buildup.
8. **Stray white circles** — the fog motes read as unexplained clouds on screen.

v2 splits the game into **Adventure** (wave-survival) + **Endless** (open-world with a Zelda-like story), overhauls the art to procedural pixel-art with per-character asset bundles, makes the skill system readable (taxonomy + tooltips + hold-to-aim), adds LoL-style auto-attack, fixes mana regen, grounds loot as visible pickups, enriches the terrain (water/bridges/landmarks/villages), and removes the fog motes.

## Architecture

Two modes selected from the title screen:
- **Adventure** — a new dedicated `AdventureScene`: 10-min survival per stage, continuous waves, boss at 5 min, defeat the boss to advance to the next stage (enemy power scales with stage level). Fixed 4-char party (1-4 mid-fight swap allowed, no roster changes mid-run).
- **Endless** — the existing open-world `WorldScene`, evolved: distance-based enemy scaling, per-area bosses, a Zelda-like narrative (NPCs, quest chain, dialogue, lore). Full Genshin-style live swap + roster changes.

Five cross-cutting overhauls apply to both modes:
1. **Pixel-art asset overhaul** — procedural pixel-art (higher density than Stardew) + per-character asset bundles.
2. **Skill system** — expanded taxonomy, hover tooltips, hold-to-aim preview, per-skill descriptions.
3. **Combat fixes** — LoL-style auto-attack, mana regen fix, hold-to-aim.
4. **World enrichment** — remove fog motes, ground loot drops, water/bridges/landmarks/villages.
5. **Party system** — adventure fixed-4, endless live-swap.

## Cross-cutting constraints (every enhancement)

- **Pure-procedural:** no external art/audio; all art via `generate_assets.py` (pixel-art), all audio via `audio.py` numpy synthesis.
- **Pixel-art aesthetic:** chunky pixels, limited per-element/biome palette, dithering, no anti-aliased gradients. Character sprites on a ~48×48 logical pixel grid (3× Stardew's 16), upscaled to the existing 256px world sprite / 512px portrait. Keep sprite sizes + loader paths unchanged so the world scene + caches work.
- **LoL control scheme:** RMB click-to-move (ground) / RMB auto-attack (enemy), J manual attack, Q/W/E skills (hold-to-aim), U/Space ult, 1-4 swap — extended, not replaced.
- **Cached-map model:** weather/rifts stay live overlays, never baked into `gen_map` (MapRenderer cache keyed on (c,r)). Water/landmarks/villages are static gen_map features (cache-safe).
- **Init-order traps:** fields used in `_load_map` declared in `__init__` before `_load_map`.
- **`reduce_motion` / `high_contrast`:** every new visual effect (tooltips, aim preview, drop sparkle, water shimmer) respects the existing accessibility settings.
- **Save migration:** v2 bumps save version to 8; all new fields (`mode`, `adventure_best_stage`, story flags) use `d.get(..., default)` so old saves load.
- **Build on v1:** v2 layers on v1's features. No v1 regression — the 20-test + 8-feature suites stay green.
- **PYTHONHASHSEED determinism:** use `sum(ord(c))` for stable-across-reloads hashes (v1 lesson).
- **No new external dependencies.**

---

## Enhancements

### 1. Pixel-art asset overhaul  *(graphics, L)*
Redraw all procedural art in a pixel-art aesthetic (chunky pixels, limited palette, dithering, no smooth gradients) at higher pixel density than Stardew Valley, so the game reads as a cohesive pixel-art game instead of soft-gradient circles.
- **Inspiration:** Stardew Valley (16×16 pixel-art) at 3× the density; Celeste (limited palette + dithering); GBA-era JRPG sprites.
- **Value:** The user wants a Stardew-like pixel-art look with more pixels for readability. The current art is soft-gradient circles — a cohesive pixel-art pass makes the game feel like a real pixel-art game.
- **Sketch:** `generate_assets.py`: add a `PIXEL = 5` scale factor (each logical pixel = 5px at the 256px world sprite) and a per-element `PIXEL_PALETTE` dict (5-8 colors each: base/light/shadow/outline/accent). Rewrite `draw_chibi`, `draw_enemy`, `draw_skill_icon`, `make_portrait`, `make_ui`, `make_items`, `make_battle_bg`/`make_map_bg` to render on the coarse pixel grid (palette-locked, dithered gradients, no anti-aliasing). Character sprites render at ~48×48 logical pixels, upscaled to 256px (world) / 512px (portrait). Enemies 48×48, skill icons 48×48, terrain tiles 40×40 (match TILE), UI pixel-art. **Keep the existing sprite sizes + file paths** so `load_char_sprite`/`load_portrait`/`load_skill_icon`/`load_enemy_sprite` and the scene caches work unchanged. `verify_assets.py`: assert every sprite renders + sizes unchanged.
- **Files:** generate_assets.py, data.py (PIXEL_PALETTE), verify_assets.py
- **Risk:** Large art rewrite. Must keep sprite sizes + loader paths unchanged. Pixel-art at 48-logical-pixel must be readable at 1280×720 fullscreen. Tune the per-element palettes so the 5 elements stay distinct from each other and from HP-red/crit-yellow/heal-green.

### 2. Per-character asset bundles (HERO_ASSETS manifest)  *(characters/data, M)*
Consolidate the per-hero data (lore, signature, constellation, ultimate variant, skills) into one `HERO_ASSETS` manifest keyed by hero id — the single source of truth for the codex, hero-detail screen, and skill tooltips. Each entry: `name, title, element, role, lore{bio, quote, personality}, skills[{id, name, type, category, cost, description, how_to_use}], signature{name, desc}, constellation[6 × {name, desc}], ultimate{name, desc, extra_effect}`.
- **Inspiration:** Genshin Impact character profiles (one page per character with skills + descriptions + lore); Fire Emblem Heroes hero data.
- **Value:** The user wants each character to include assets for skills, skill descriptions, skill types, lore, name — in one bundle. Today the per-hero data is scattered across `HERO_LORE`, `HERO_SIGNATURE`, `CONSTELLATION_PERKS`, `ULTIMATE_VARIANTS`, `HEROES_DB`. One manifest makes the codex + tooltips + hero-detail read from one place and makes each hero feel like a complete character.
- **Sketch:** `data.py`: add `HERO_ASSETS` dict (25 entries), consolidating the scattered dicts. Each skill entry carries a human-readable `description` (what it does) + `how_to_use` (key + hold-to-aim note + AoE/range). **Keep `SKILLS_DB`/`ULTIMATE_VARIANTS`/`HERO_SIGNATURE`/`CONSTELLATION_PERKS` as the combat-data source** — the manifest is presentation + descriptions, referencing the same skill ids. `main.py` `HeroDetailScene` (line ~667) + `CodexScene` (line ~1869): read from `HERO_ASSETS` instead of the scattered dicts. `world_scene.py` skill tooltip (enhancement #4): read `how_to_use`/`description` from the manifest.
- **Files:** data.py, main.py, world_scene.py
- **Risk:** 25 entries is data work. The manifest's skill ids must match `HEROES_DB[id].skills` + `ultimate`. The combat dicts stay the source of truth for mechanics; the manifest layers descriptions + presentation. Don't duplicate the combat data (reference, don't copy).

### 3. Skill taxonomy expansion  *(skills/data, M)*
Expand the skill type taxonomy so skills classify as innate/summon/curse/beam/trap (plus existing attack/magic/aoe/heal/debuff/ultimate), and add a `category` label for UI grouping. Add a few new skills of the new types so the taxonomy is real, not just labels.
- **Inspiration:** Genshin Impact (skill types: normal attack, elemental skill, elemental burst, passive); League of Legends (innate passives, summon, curse, buff).
- **Value:** The user wants skill diversity — "skills kiểu nội tại, các loại khác nhau kiểu summon, curse, buff, fire". Today `SKILLS_DB` has `type` but only attack/magic/aoe/heal/buff/debuff/ultimate. Adding innate/summon/curse/beam/trap makes the skill system read as diverse and gives the tooltip a meaningful category.
- **Sketch:** `data.py` `SKILLS_DB`: add a `category` field to each skill. Add ~4-6 new skills of new types: a `summon` (spawn a temporary ally/construct that fights for the hero), a `beam` (line AoE hit-scan), a `trap` (place a delayed hazard on the ground), an `innate` tag for the signature passives (display only). Give 2-3 heroes a new-type skill in their kit (e.g. a summoner hero, a beam mage). `world_scene.py` `_do_skill` (line ~1636): add dispatch branches for `summon` (spawn a temporary `WorldEntity` ally that auto-attacks nearby enemies for a duration), `beam` (a line hit-scan from hero toward aim, damages all enemies along the line), `trap` (place a trap entity that triggers when an enemy steps on it). `world_entities.py`: a `SummonAlly`/`Trap` entity class (or reuse the projectile pattern).
- **Files:** data.py, world_scene.py, world_entities.py
- **Risk:** New combat branches — keep each handler small. Summon ally must be a temporary entity (not a party member — don't break the 4-slot party). Beam/trap must respect the existing hit-scan + collision. Balance the new skills so they don't trivialize combat.

### 4. Skill hover tooltips  *(ui, S)*
On the world skill bar, hovering a skill slot shows a tooltip panel with: skill name, type/category, element, energy cost, cooldown, description (what it does), how-to-use (key + hold-to-aim). So the player can read what each skill does without opening the codex.
- **Inspiration:** League of Legends ability tooltips (name + cost + cooldown + description on hover); Genshin skill tooltips.
- **Value:** The user wants "khi hover có thể đọc skills dùng như nào, chức năng gì" — read how to use + what it does on hover. Today the skill bar (`world_scene.py:3936`) shows icon + cost + cooldown sweep, no tooltip. A hover tooltip makes the skill system readable in-world.
- **Sketch:** `world_scene.py` `_draw_skill_bar` (line ~3936): add `collidepoint` hover detection on each skill slot (Q/W/E/R). On hover, draw a tooltip panel above the slot: name, category badge, element, energy cost, cooldown, `description`, `how_to_use` — all read from `HERO_ASSETS[hero].skills[idx]`. Cache the tooltip surface per `(hero_id, idx, affordable)` to avoid per-frame text re-render. Word-wrap with the existing `text()` helper. Show the tooltip only when the slot is hovered + the player is idle (not mid-cast). Respect `reduce_motion` (instant show, no fade).
- **Files:** world_scene.py, data.py (manifest)
- **Risk:** Tooltip must not overlap the boss HP bar (top-center) or the action. Cache to avoid per-frame text render. The tooltip must not block clicks (display only).

### 5. Hold-to-aim preview  *(combat/ui, M)*
When holding a skill key (Q/W/E), show an aim reticle / AoE area preview before releasing: ranged skills show a line/trajectory, AoE skills show a circle on the ground at the target, beam shows a line, melee shows the arc. Release fires. A quick tap fires instantly at the facing direction (legacy behavior preserved).
- **Inspiration:** League of Legends (hold to aim, release to cast, smart-cast); Genshin (tap vs hold skill).
- **Value:** The user wants "skill khi giữ không hiện tầm hay vùng ảnh hưởng" fixed — show the range/AoE when holding. Today skills auto-target instantly with no preview. Hold-to-aim makes skill casting deliberate + readable.
- **Sketch:** `world_scene.py`: on KEYDOWN Q/W/E, start a hold timer; if held > 0.12s enter aim mode (`_aim_skill = idx`, draw the preview); on KEYUP, fire the skill at the aimed target (mouse pos for ground-target AoE, facing for melee/beam). If held < 0.12s (tap), fire instantly at facing (legacy). Draw the preview by skill category: AoE = circle at mouse (clamped to max range), beam = line from hero to mouse, ranged = trajectory line, melee = arc in facing. `_do_skill` gains an optional `target=(x,y)` param for ground-targeted AoE. **Aim mode must not block movement** (RMB still moves while aiming). Gate the preview animation on `reduce_motion` (show a static reticle, no pulse).
- **Files:** world_scene.py
- **Risk:** Must not break the instant-cast feel (tap = instant). AoE ground-target must clamp to the skill's max range. Aim must not block movement or skill cast. The hold timer must not trigger on a quick tap.

### 6. Auto-attack (AA) LoL-style  *(combat, M)*
Add LoL-style auto-attack: RMB on an enemy targets it and the hero auto-attacks continuously at the AA cooldown until the target dies or a new command is given; RMB on ground click-to-moves (clears the AA target). Keep J as a manual attack. This is the LoL verb the game is missing.
- **Inspiration:** League of Legends (right-click enemy to auto-attack; right-click ground to move).
- **Value:** The user wants "như LOL thì cần AA" — LoL needs auto-attack. Today J is a manual basic attack (press per swing) and RMB only moves. LoL-style AA (RMB on enemy = auto-attack target) is the core combat verb the control scheme implies but lacks.
- **Sketch:** `world_entities.py` `WorldCharacter`: add `aa_target = None` (a WorldEnemy ref or None). `world_scene.py` RMB handler (line ~2534): on RMB, hit-test enemies at the click pos; if an enemy is hit, set `wc.aa_target = enemy` (and move toward it if out of range); else (ground) set `move_target` + clear `aa_target` (existing click-to-move). In the update loop, if `wc.aa_target` is set, alive, and in range, auto-fire `_do_attack` at the AA cooldown (0.32s) auto-targeted at `aa_target`; if out of range, move toward it. Clear `aa_target` when the target dies, the player issues a move (RMB ground), a skill cast, or a transition. Keep J manual attack (does not set `aa_target`, fires at facing).
- **Files:** world_scene.py, world_entities.py
- **Risk:** AA must not override skill cast or movement commands. Auto-attack movement must respect collision. AA target must clear on death/transition. Must not double-fire with J. The AA must feel responsive (0.32s cd, same as the manual attack).

### 7. Mana regen fix + tune  *(combat, S)*
The user reports mana "doesn't increase". v1 added `ENERGY_REGEN_PCT=0.04` (4%/s out of combat, 2%/s in combat, `world_entities.py:756`). Root-cause why it's not felt, and tune so mana visibly recovers.
- **Root cause (to verify):** the regen gates on `alive` + `energy < max_energy` + a combat-state 0.5x multiplier. Possible causes: the in-combat 0.5x makes it too slow to feel; the regen isn't applied when the player expects; or the energy bar HUD doesn't animate the fill visibly. Root-cause with systematic debugging before tuning.
- **Fix:** `world_entities.py` (line ~756): verify the regen runs; tune `ENERGY_REGEN_PCT` to ~0.08 (8%/s out of combat, 4%/s in combat — full bar in ~12s out of combat) so it's felt. Ensure the energy bar HUD animates the fill. `data.py`: bump `ENERGY_REGEN_PCT`. Keep the on-hit gains (they reward aggression).
- **Files:** world_entities.py, data.py
- **Risk:** Must root-cause first (systematic debugging) — don't just raise the rate if there's a bug. Verify headless: idle 60 frames, assert `hero.energy` increased from the start value.

### 8. Remove fog motes (stray white circles)  *(ui, S)*
Delete the `_fog_motes` (7 big soft circles, additive blend — the "stray white circles" the user sees). Keep the fog weather darkening (subtle flat overlay), remove the bright drifting circles.
- **Root cause (verified):** `world_scene.py:958-964` seeds 7 fog motes (big soft circles, `BLEND_RGBA_ADD`); drawn at `world_scene.py:3231-3240` — they drift + parallax and read as unexplained bright white circles ("mây").
- **Fix:** `world_scene.py`: remove `_fog_motes` init (line ~958) + draw (line ~3231). Keep `_fog_overlay` (the flat darkening, line ~3370) for fog weather. The rain overlay + storm strikes stay (they're weather, not stray circles).
- **Files:** world_scene.py
- **Risk:** None — pure removal. Verify the fog weather still darkens without the motes; the rain/storm still render.

### 9. Ground loot drops  *(world, M)*
Enemy deaths + breakables drop loot as visible sprites on the ground (gold coins, potions, shards, equipment), walk over (magnet pickup radius) to collect. Replaces the "drops straight to inventory" with visible ground items, so loot feels real.
- **Inspiration:** Zelda (rupees drop + walk-over pickup); Genshin (drops spawn on the ground, magnet pickup); Hades (gem drops).
- **Value:** The user asks "vật phẩm trên mặt đất có nên xuất hiện không?" — should ground items appear? Yes: visible ground loot makes combat rewards feel tangible. Today drops go straight to inventory (`world_scene.py:2145`) with only a FloatText label; `self.drops` (line ~934) is declared but never populated.
- **Sketch:** `world_scene.py`: populate `self.drops` (line ~934) with drop entities `{x, y, kind, value, t, vy, sprite_id}` on enemy death (line ~2145) + breakable shatter (line ~1383). Kinds: `gold` (coins), `hp_potion`, `shard`, `equipment` — each a pixel-art sprite (reuse `make_items` icons, or add small drop sprites in `generate_assets.py`). Draw drops in the depth-sorted drawables. Pickup: in the walk-over check, if `hypot(wc - drop) < magnet_radius (40)`, collect (add to inventory) + sparkle. Magnet: if the hero is within ~80px, pull the drop toward the hero (respect collision). Cap the drops list (expire old drops after ~30s) so it doesn't pile up. Boss/elite drops richer (more gold, guaranteed shard/equipment).
- **Files:** world_scene.py, generate_assets.py
- **Risk:** Drops must not pile up (cap + expire). Pickup must not double-collect. The magnet must not yank drops through walls. The drops list must not break the depth-sorted draw order.

### 10. Terrain: water + bridges + landmarks + villages  *(world, L)*
Add water bodies (impassable, with bridges to cross), named landmarks (statue/ruin/shrine per biome), and villages (a small hub per biome with an NPC quest giver). Evaluate the 5 biomes and add what's missing for an open world.
- **Inspiration:** Zelda (water + bridges, landmarks, villages with NPCs); Stardew (water bodies, bridges); Genshin (landmarks, villages).
- **Value:** The user wants "đánh giá địa hình random, cái nào cần thiết, bổ sung thêm gì" + ground items. Today the 5 biomes (plains/forest/cave/castle/void) have distinct layouts but no water/impassable terrain, no villages, no named landmarks. Water + bridges + landmarks + villages make the open world read as a world.
- **Sketch:** `world_data.py` `gen_map`: add `water` rects (an impassable pool per map, biome-tinted) + `bridges` (passable tiles over water) — gate with `_free_grid` + center-distance so they don't block the corridor/edge-portal gaps. Add `landmark` (one per biome: statue in plains, ruin in forest, shrine in cave, obelisk in castle, rift-anchor in void) with a lore line. Add `village` (a cluster of 3-5 buildings + an NPC spawn point) per biome on a free tile cluster. Include all in the gen_map return dict. `world_scene.py`: water collision (impassable, like obstacles), bridge passable, landmark draw + lore float on first visit, village buildings draw + NPC spawn. `generate_assets.py`: pixel-art water tile, bridge tile, landmark sprites, village building sprites. `data.py`: landmark lore lines, NPC data (enhancement #12).
- **Files:** world_data.py, world_scene.py, generate_assets.py, data.py
- **Risk:** Water must not trap the player (bridges or walkable edges). Villages must not block the corridor/edge-portal gaps. Landmarks are decorative (no collision). Water/landmarks/villages are static gen_map features — the MapRenderer cache (keyed on (c,r)) stays intact.

### 11. Adventure mode (new dedicated scene)  *(mode, L)*
A new `AdventureScene`: select 4 chars, 10-min survival per stage, continuous waves (scaling with stage level), boss at 5 min, defeat the boss to advance to the next stage. Party wipe ends the run. Rewards per stage.
- **Inspiration:** Hades (room-to-room escalation); Dead Cells (wave survival + boss); Genshin Spiral Abyss (timed challenge floors).
- **Value:** The user wants Adventure mode: "sống sót trong 10 phút với các đợt quái tấn công liên tục, 5 phút gặp 1 boss, đánh thắng boss thì qua màn" — survive 10 min with continuous waves, boss at 5 min, defeat to pass. This is a structured challenge mode distinct from the open world.
- **Sketch:** `adventure_scene.py` (new file): `AdventureScene` with a stage-start party select (pick 4 from roster, locked for the run), a 10-min timer HUD, a wave spawner (enemies spawn from arena edges every ~25s, count + level scale with stage level + elapsed time), a boss at the 5-min mark (a row boss scaled to stage level), stage-clear on boss defeat (advance to next stage, level +5, full heal party), run-end on party wipe. **Reuse the combat engine** by extracting `_do_attack`/`_do_skill`/`_do_ultimate`/`_on_enemy_hit`/`_on_enemy_death` into a shared combat mixin, or subclass `WorldScene` with wave/timer overrides (the implementer picks the cleaner option). Arena: a single fixed map (reuse a biome layout). `main.py` `_make_scene` (line ~2190): route to `AdventureScene` when `player.mode == "adventure"`. `player.py`: `adventure_best_stage` (record), save v8.
- **Files:** adventure_scene.py (new), main.py, player.py, data.py
- **Risk:** Reusing the combat engine without a full extract risks duplication — extract the combat methods into a shared mixin or subclass WorldScene. The 10-min + 5-min-boss timing must be readable (a timer HUD + wave counter). Wave scaling must not wall the player early. The party-select at stage start must lock the 4 ids (enhancement #13).

### 12. Endless mode + Zelda-like story  *(mode/world, L)*
Evolve the open world with a Zelda-like narrative: NPCs in villages, a main quest chain (5 biome bosses → Demon King), dialogue, lore, quest givers. Story gives the open world direction. Bosses come after exploring the area (not at the start).
- **Inspiration:** Zelda (NPCs in villages, main quest chain, dialogue, lore); Genshin (quest tracker + story chapters); Stardew (NPC relationships + dialogue).
- **Value:** The user wants "làm câu chuyện ở endless mode đủ thú vị như zelda" + "màn đánh boss luôn đầu game không hợp lý" — make the endless story Zelda-like + bosses not at the start. Today the open world is sandbox with daily quests; no NPCs, no story, no quest direction. A Zelda-like story (NPCs + quest chain + dialogue) gives exploration purpose and gates bosses behind progression.
- **Sketch:** `data.py`: add `NPCS` dict (1 per biome, `{name, village_cell, dialogue, quest_id}`), `STORY_QUESTS` (main chain: 5 biome-boss quests → 1 final-boss quest, each `{id, name, giver, objective, reward, lore}`), `DIALOGUE` trees (NPC lines revealing the world's story). `world_scene.py`: NPC spawn at the village (from #10), interact (walk up + press F) → dialogue text box + quest assignment. Gate each biome boss behind its quest (the boss cell locks until the biome quest is accepted + the area explored) so the boss is not "at the start". `main.py`: enhance the quest tracker (v1 #20) to show the main story quest chain + the active NPC quest. `data.py`: expand `LORE_FRAGMENTS` + NPC dialogue.
- **Files:** data.py, world_scene.py, main.py
- **Risk:** A full Zelda story is huge — scope to: 5 NPCs (1 per biome), 5 biome-boss quests + 1 final, dialogue text boxes, a quest tracker. Not a branching open-world. The boss gate must not block exploration (gate on quest acceptance + area exploration, not completion). Dialogue must not block the action (text box with a dismiss).

### 13. Party system (adventure fixed-4, endless live-swap)  *(meta, S)*
Adventure: lock the 4-char party at stage start (no roster changes mid-run), 1-4 swap allowed. Endless: full live swap + roster changes (existing Genshin-style).
- **Value:** The user wants "khi vào adventures sẽ chọn 4 chars luôn còn endless có thể đổi chars liên tục như genshin" — adventure picks 4 fixed, endless swaps freely. Today the roster UI allows team edits anytime; adventure needs a lock.
- **Sketch:** `player.py`: add `mode` field (`"adventure"`/`"endless"`, default `"endless"`, save v8). `AdventureScene` (#11): at stage start, `set_team` locks the 4 ids; disable roster add/remove mid-run; 1-4 swap stays (existing `_switch`). `WorldScene` (endless): keep the existing live swap + roster changes. `main.py` `RosterScene`: disable team edits (add/remove hero) when `player.mode == "adventure"`; show "locked for the run" in adventure.
- **Files:** player.py, main.py, adventure_scene.py
- **Risk:** Adventure must lock the team without breaking the roster UI. The 1-4 swap in adventure must change only the active index, not the roster. Endless stays unchanged.

### 14. Title screen mode selector  *(ui, S)*
Replace the single "Enter World" button with a mode selector: "Adventure" / "Endless". Sets `player.mode` and routes to the right scene.
- **Value:** The user wants the mode split visible at the title. Today the title has one "Enter World" button; the mode split needs a selector.
- **Sketch:** `main.py` `TitleScene` (line ~333): replace "Enter World" with two buttons "Adventure" / "Endless", each with a one-line description. On click, set `player.mode` + route to `AdventureScene` or `WorldScene`. Keep the meta menus (gacha/shop/roster/inventory/codex) accessible from both modes. Persist `player.mode` in the save.
- **Files:** main.py, player.py
- **Risk:** Low — a UI branch. Persist `player.mode`. The meta menus must work in both modes.

---

## Verification plan (headless, per batch + final)

- `xvfb-run -a python3 verify_assets.py` — render every sprite (pixel-art, new terrain/landmark/village/drop sprites), report sizes.
- `SDL_VIDEODRIVER=dummy python3 main.py` — boot + exercise both modes headless after each batch.
- The 20-test acceptance suite (`/tmp/verify_complete.py`) + 8-feature suite (`/tmp/verify_features.py`) + a 1200-frame stress test + the per-scene benchmark (`/tmp/bench_aetheria.py`) — all PASS after the full set, world ≥ ~60fps.
- New v2 assertions (added to the suite): mana regen (idle 60 frames, `hero.energy` increases), AA (RMB on enemy sets `aa_target`, auto-fires at cd), hold-to-aim (hold Q > 0.12s shows preview, release fires), ground loot (enemy death spawns a drop entity, walk-over collects), adventure (10-min timer runs, waves spawn, boss at 5 min), mode selector (title → adventure → AdventureScene; title → endless → WorldScene), skill tooltip (hover skill slot shows the panel).
- Manual: `python3 generate_assets.py && python3 main.py` → title → pick Adventure / Endless → play.

## Implementation shape (after spec approved)

A **gated batch loop** (the v1 pattern that shipped clean): batches A→E, each batch = specialist agents with worktree isolation + a gate agent running the full headless suite after each batch; on failure the loop spawns fix agents until the gate passes.

- **Batch A — asset overhaul:** #1 pixel-art, #2 per-character bundles, #3 skill taxonomy, + terrain/landmark/village/drop sprites (part of #10).
- **Batch B — skill system + combat fixes:** #4 tooltips, #5 hold-to-aim, #6 AA, #7 mana.
- **Batch C — world enrichment:** #8 fog motes, #9 ground loot, #10 terrain water/bridges/landmarks/villages.
- **Batch D — adventure mode:** #11 AdventureScene, #13 party fixed-4, #14 title selector (the mode split).
- **Batch E — endless story:** #12 NPCs/quest chain/dialogue/boss timing.

Each batch: every enhancement → one specialist agent (worktree isolation, owns its files, runs a headless smoke test). Merge + headless verify + commit per batch. The gate agent runs the full suite + the v2 assertions after each batch; on failure, fix agents target the regressions, re-gate until clean.

## Out of scope (YAGNI)

- Full branching open-world story (scope to 5 NPCs + 6 quests).
- Real external art (stay pure-procedural pixel-art — no external PNGs).
- Per-hero fully unique skill mechanics (reuse archetypes; unique names/art/descriptions/category per the manifest).
- Adventure mode as a full separate game (reuse the combat engine).
- Per-hero voice stings (v1 dropped; 5 element leitmotifs ship instead).
- New external dependencies.
