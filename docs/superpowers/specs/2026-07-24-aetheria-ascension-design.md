# Aetheria: Ascension — Design Spec

**Date:** 2026-07-24
**Status:** Approved (user: "ok", "cực đại", "chạy tới cùng")
**Goal:** Fix all crashes + maximally expand the gacha RPG across breadth, depth,
and polish. User wants to be surprised by the finished product; run to
completion, report per-phase with a smoke test.

## Root cause of the three crashes

All three crashes share one systemic cause: `Game.goto()` swaps `self.scene`
mid-frame (a button click inside `update()` calls `goto`), and the same frame
then calls `self.scene.draw()` before the new scene's `update()` has run once,
so the draw-state attributes the scene caches in `update()` do not exist yet.

- `MapScene`: `nodes[i]["unlocked"]` only set in `update()` (main.py:248).
- `RosterScene`: `self.cards` only assigned in `update()` (main.py:331).
- `ShopScene`: `self.consumable_rects` only assigned in `update()` (main.py:724).

Hidden bugs of the same family: `HeroDetailScene._item_rects`,
`BattleScene.hero_panel_rects` / `item_rects` follow the same
draw-before-update pattern.

**Fix (idiomatic + testable):** every scene initializes its full draw-state in
`__init__` so `draw()` is safe even if called before `update()` (this also
makes scenes directly testable). Defense-in-depth: `Game.goto()` calls
`self.scene.update(0.0, [])` once after construction so a freshly-swapped scene
always has cached state before the first `draw()`.

## Architecture

Keep the existing file layout: `data.py`, `entities.py`, `combat.py`,
`gacha.py`, `player.py`, `audio.py`, `main.py`, `generate_assets.py`. Each
scene owns and initializes its draw-state. New data goes in `data.py`; new
procedural art is added to `generate_assets.py` and regenerated.

New shared infrastructure:
- A small navigation back-stack on `Game` so Back returns to the previous scene
  instead of a hardcoded target.
- A `Scene` base helper hook (`on_enter`) for first-frame setup where needed.
- Save-file version bump with migration.

## Phase A — Foundation & robustness

**Files:** main.py, player.py, data.py

Scope:
1. Fix all three crashes + every hidden draw-before-update bug by initializing
   draw-state in each scene's `__init__`. Add `Game.goto` defensive
   `self.scene.update(0.0, [])`.
2. Navigation back-stack: `Game.goto(name, **kw)` pushes the current scene;
   `Game.back()` pops. Scenes use `back()` for Back/Esc where a previous scene
   exists; fall back to a sensible default (title) when the stack is empty.
3. **Settings scene** (reached from title): sound on/off, text speed slider,
   reset-save with confirmation. `player.settings` already holds `sound` and
   `text_speed`; wire them to `audio.set_enabled` and the `text` helper.
4. **Stats screen** (reached from title): battles won/lost, total pulls,
   enemies defeated, gold/gems earned, stages cleared, tower floor. Uses
   `player.stats`.
5. Shop: render `SHOP_GEMS` packs (data exists, UI omits them). Fix battle item
   menu so revive/bomb items either enter targeting or are visually disabled,
   not silently no-op.
6. Save migration: bump `version` to 3; ensure all new fields default safely.

Acceptance:
- Headless smoke test: construct Title/Map/Roster/Shop/Inventory/HeroDetail
  scenes and call `draw()` without `update()` — no crash.
- Real run: navigate title → map → roster → hero detail → back, and title →
  shop, with no crash; Esc/Back returns to the previous scene.
- Settings toggles sound; stats screen shows correct numbers; gem packs
  purchasable in shop.

## Phase B — Content breadth

**Files:** data.py, generate_assets.py, main.py, combat.py, entities.py

Scope:
1. Add ~6 new heroes across the existing elements (mix of SSR/SR/R) with
   distinct skill kits and ultimates. Update `GACHA_POOL`.
2. Add 5-6 new enemies (including a new mid-boss and a second boss with an
   ultimate). Update `BOSS_ULTIMATES`.
3. Add new skills (a couple per element) to `SKILLS_DB`.
4. Expand `STAGES_DB` to ~9-10 stages: extend the existing chapter and add a
   harder chapter 2 with higher power/rewards and the new boss.
5. **Endless Tower mode**: a new scene reached from the title. Climb floors;
   enemy level scales with floor; rewards gold/gems per floor; best floor saved
   to player state. Flee returns to title.
6. **Daily Dungeon mode**: a new scene, seeded by date, one clear per day for
   bonus rewards; completion tracked in player state.
7. Expand equipment (`EQUIPMENT_DB`) with a few more pieces and add the new
   item/equipment icons to `generate_assets.py`.

Acceptance:
- `generate_assets.py` runs clean and produces all new character/enemy/skill/
  item/background assets.
- Tower climbs at least 5 floors headlessly; daily dungeon is enterable and
  winnable; rewards persist.
- New heroes appear in gacha pool and roster; new stages unlock sequentially.

## Phase C — Combat depth & juice

**Files:** combat.py, main.py, data.py, audio.py

Scope:
1. Tune hit-stop, screen shake, and particles; add KO fade-out and entry
  animations; improve damage-number readability.
2. Add an **auto-battle / turbo** toggle in battle: auto picks a basic attack
  on a sensible target and speeds up action timing; toggle with a key/button.
3. New status effects (e.g. bleed, taunt, reflect) with icons in
  `EFFECT_NAMES`; wire into combat and the effect drawing.
4. Boss multi-phase behavior: a second threshold / enrage at low HP for the new
  boss; clearer boss-ultimate telegraph.
5. Improve turn-order preview and combo meter visuals.

Acceptance:
- Battle plays with and without auto/turbo; no softlocks across a full clear.
- New status effects apply, tick, display, and expire correctly.
- New boss enrages and telegraphs its ultimate.

## Phase D — Meta, progression & polish

**Files:** data.py, player.py, main.py, generate_assets.py

Scope:
1. **Achievements**: definitions in `data.py`, tracking in `player.py`, a panel
  in the stats screen; grant gem rewards on unlock.
2. **Daily quests**: a small rotating set (win N battles, summon once, clear a
  stage) with gem rewards; reset daily; shown in a quests panel.
3. **Codex/Collection scene**: view all heroes (owned/total) with portraits.
4. Daily login 7-day streak with escalating bonus.
5. Scene transitions (fade), title screen polish, gacha reveal polish.

Acceptance:
- Achievements unlock and grant rewards; quests reset daily and grant rewards.
- Codex shows owned vs total counts correctly.
- 7-day streak grants escalating bonuses; transitions fade cleanly.

## Cross-cutting

- Every scene initializes draw-state in `__init__`.
- `Game.goto` calls `self.scene.update(0.0, [])` after construction.
- Save version bumped with migration; old saves load without error.
- No new external dependencies; art/audio remain procedural.
- Smoke test after each phase: headless construct+draw of all scenes, then a
  real `python3 generate_assets.py && python3 main.py` launch.

## Out of scope (YAGNI)

- Online / server features, accounts, leaderboards (would require a backend).
- Rewriting the engine in a different framework.
- Real-money purchases (keep it gold/gem only).
