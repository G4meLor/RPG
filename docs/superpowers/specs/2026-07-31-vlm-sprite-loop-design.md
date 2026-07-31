# VLM-in-the-Loop Pixel Sprite Improvement — Design Spec

**Date:** 2026-07-31
**Status:** Approved (brainstorm sections 1-5)
**Author:** design session

## Goal

Drastically improve the quality of the procedural per-champion **world sprite**
(`assets/characters/{id}/sprite.png`) by putting a **VLM (vision-language
model) in the loop as an art director** at build time. The renderer stays
pixel-art; the VLM only *describes* and *critiques*, never draws. Extend the
system to **per-skin sprites** so changing a hero's equipped skin in-game also
changes their world sprite.

## Background — what exists today

- `assets/characters/{id}/sprite.png` is a 256×256 procedural pixel sprite,
  drawn by `src/assets_gen/generate.py:draw_chibi_descriptor` from a
  **descriptor** baked into `src/build/champions.py` (one per champion, for the
  Original skin only). The descriptor drives: archetype (10), weapon (8),
  palette (3 RGB), features (≤3 from 7), build (5), motif/element-aura (8).
- `WorldCharacter._load_sprite` (`src/entities/world_actors.py`) calls
  `load_char_sprite(self.hero.id, size)` (`src/entities/combatant.py`), which
  loads `characters/{id}/sprite.png` and **ignores the equipped skin entirely**.
- Skins already exist as data: `rec["skin"]` (index, default 0) is persisted on
  the player's hero record, switched in `hero_detail.py`, and used by
  `load_portrait(hero_id, skin_idx)` to pick `skins/{idx}.jpg`. But the *world
  sprite* never changes with skin — that is the gap this spec closes.
- Skin splash references live at `assets/characters/{id}/skins/{idx}.jpg`
  (~1780 total, ~10.5/champ). These are the VLM's reference images.
- The VLM endpoint is an OpenAI-compatible chat/completions API (vLLM,
  misa-gemma-4-31b-it), reachable with a self-signed cert (`verify=False`),
  ~0.8s / ~1000 tokens per vision critique. Verified working for both
  describe-from-image and critique-two-images tasks.

## Architecture

**Core idea:** the VLM is a build-time art director; the existing pixel
renderer is the brush; runtime only loads baked PNGs. The VLM never runs while
playing.

```
BUILD TIME (offline, run once)                  RUNTIME (game)
┌──────────────────────────────────────┐      ┌───────────────────────────┐
│ ref: characters/{id}/skins/{idx}.jpg │      │ load_char_sprite(          │
│            ↓                         │      │   hero_id, size, skin_idx) │
│  VLM.describe(ref) → descriptor      │      │   → sprites/{idx}.png      │
│            ↓                         │ bake │     (or sprite.png fallback)│
│  renderer.draw(descriptor) → PNG     │ ───▶ │                           │
│            ↓                         │ PNGs │ WorldCharacter blit +      │
│  VLM.critique(ref, PNG) → {ok?}      │      │ squash/tilt/lunge/walk-bob │
│   ├─ ok   → SAVE PNG + descriptor    │      └───────────────────────────┘
│   └─ !ok  → descriptor = suggested   │
│             → loop (max 10)          │
└──────────────────────────────────────┘
```

**Fixed renderer vocabulary** (the VLM only adjusts within this; it cannot
invent drawing primitives — that is Phase 2):

| Field | Values |
|-------|--------|
| archetype | knight, mage, archer, brute, rogue, undead, yordle, vastaya, construct, beast |
| weapon | sword, bow, staff, orb, scythe, spear, gauntlet, none |
| features | cape, hood, horns, wings, mask, halo, spikes (≤3) |
| build | slender, average, bulky, tall, short |
| motif | flame, ice, wind, lightning, shadow, light, void, nature |
| palette | {primary, secondary, accent} each [r,g,b] 0-255 |

## The VLM loop

```
def vlm_sprite_loop(hero_id, skin_idx, ref_jpg, max_iters=10):
    desc = VLM.describe(ref_jpg)              # round 0: initial description
    history = []                              # (descriptor, match, ok) per round
    for i in range(max_iters):
        png = renderer.draw(desc)             # pixel render (under render-lock)
        crit = VLM.critique(ref_jpg, png)     # {match:0-10, ok:bool, problems:[], suggested_descriptor:{}}
        history.append((desc, crit.match, crit.ok))
        if crit.ok: break                     # VLM says good → stop
        desc = crit.suggested_descriptor      # not good → take suggested
    best_desc = max(history, key=lambda h: h[1])[0]  # never converged → best-scoring desc
    best_png = renderer.draw(best_desc)       # re-render the chosen descriptor once
    return best_desc, best_png, history
```

- **Convergence:** the VLM's own `ok` field is `true` (the VLM decides "ảnh đã
  ổn"; it typically returns `ok` when `match ≥ 7`, but we trust its `ok`, not a
  hardcoded threshold). **Cap:** 10 critique rounds. If it never converges,
  keep the highest-`match` descriptor and re-render it once — the loop can only
  improve, never make a sprite worse than round 0.
- **Per round cost:** round 0 = 1 describe + 1 critique; rounds 1+ = 1 critique
  each. Typical convergence ~3-5 rounds → ~4-6 VLM calls per skin.

### Concurrency (configurable, default 1)

- Config: `--concurrency N` CLI flag (default **1 = serial**) plus a default in
  the config module. Env-var override for the endpoint/key.
- **Parallelism granularity = skin:** N skins processed concurrently, each
  running its own sequential loop (round N depends on round N-1).
- **Render lock:** pygame `Surface.draw` is not thread-safe, so rendering is
  serialized under one `threading.Lock`. Rendering is ~ms (not the bottleneck);
  the VLM HTTP call is ~1s (the bottleneck) → parallelize VLM, serialize render.
- Implementation: `concurrent.futures.ThreadPoolExecutor(max_workers=N)` for
  skins + `threading.Lock` around `renderer.draw`. VLM calls are plain HTTP,
  thread-safe by nature.

### Caching & resumability (essential for ~1780 skins)

- Sidecar `assets/characters/{id}/descriptors.json`:
  `{"0": {descriptor, match, iters, ok}, "14": {...}, ...}`.
- Re-run skips any skin already cached with `ok == true` (or match ≥ threshold)
  unless `--force`. A crash mid-bake → re-run resumes without redoing finished
  skins.
- Baked PNGs are committed → deterministic runtime regardless of VLM
  stochasticity. Re-bake only on `--force`.

### Vocab contract & output validation

- The VLM returns JSON (gemma sometimes wraps it in ```json fences → strip).
- Validate every field against the fixed vocab above. On invalid JSON: retry
  once, then fall back to the last valid descriptor. An invalid descriptor
  never reaches the renderer.

### Config surface

```python
# src/build/vlm_client.py — defaults, env override
DEFAULT_MODEL    = "misa-gemma-4-31b-it"
DEFAULT_BASE_URL = "https://runai.misaonline.vpnlocal/prod-llm/misa-gemma4-31b-it-api/v1"
DEFAULT_API_KEY  = "sk-proj-..."   # or env VLM_API_KEY
```
CLI:
- `--concurrency N` — max concurrent VLM calls (default 1).
- `--max-iters N` — round cap (default 10).
- `--champs Ahri,Garen` / `--skins 0,14` — incremental filter.
- `--force` — ignore cache.

### Cost estimate

- P1 (170 Original) × ~5 rounds × ~1000 tokens ≈ 850k tokens, ~15 min at
  concurrency 1.
- P3 (~1780 skins) ≈ 9M tokens, ~3-5 h at concurrency 1; concurrency 4 → ~1 h
  (GPU-dependent).

## Per-skin file layout & game wiring

### File layout (Phase 3)

```
assets/characters/{id}/
├── sprite.png              # Original fallback (back-compat; P1 overwrites)
├── skins/                  # splash references — UNTOUCHED (jpg)
│   ├── 0.jpg
│   └── 14.jpg
├── sprites/                # NEW: per-skin world sprites (png)
│   ├── 0.png               # == sprite.png (Original)
│   └── 14.png
└── descriptors.json        # NEW: {idx: {descriptor, match, iters, ok}}
```

- `skins/` = splash references (jpg); `sprites/` = rendered world sprites (png).
  Clean separation — a new dir, no rename of existing splash files.
- Naming inside `sprites/` = `{idx}.png` (no `.sprite` infix; the dir name
  already says sprites).

### Runtime wiring (3 small edits)

1. **`Hero` carries skin** — `Hero.__init__` gains `skin=0`, stores
   `self.skin`. `player.get_hero_instance` passes `rec.get("skin", 0)`.
2. **`load_char_sprite(hero_id, size, skin_idx=0)`** — if `skin_idx > 0` and
   `sprites/{skin_idx}.png` exists → load it; else fall back to `sprite.png`
   (back-compat for old saves + champs not yet per-skin-baked).
3. **`WorldCharacter._load_sprite`** — call
   `load_char_sprite(self.hero.id, self.sprite_size, skin_idx=getattr(self.hero, "skin", 0))`.

### Skin change → sprite change

`hero_detail.py` sets `rec["skin"]` and saves. Returning to the world,
`_build_party` rebuilds `WorldCharacter` via `get_hero_instance` (now passing
the new skin) → loads the correct skin's sprite. No mid-scene hot-swap needed
(kept simple).

### Backward compatibility

- Old saves: `rec["skin"]` defaults to 0 (migration already exists at
  `player.py:474`). `Hero.skin` defaults to 0.
- Champs not yet per-skin-baked: `sprites/{idx}.png` absent → fall back to
  `sprite.png`. Game still runs; skin just doesn't change the world sprite for
  that champ — no crash.
- `verify_assets.py` + the 21-test acceptance suite must stay green (only an
  optional file + a defaulted arg are added; no game-logic change).

## Phase plan (each phase ships independently)

| Phase | What | Output | Risk |
|-------|------|--------|------|
| **P1: Re-tune Original** | VLM loop on skin index 0 for all 170 champs, current vocab. Fixes obvious mismatches (e.g. Ahri rendered as a green robot). | Better `sprite.png` for 170 champs. Game unchanged. | Low — asset-only, logic untouched. |
| **P2: Expand vocab** | Gap-analysis: ask the VLM "what distinct visual feature can the renderer NOT express?" across skins. Implement top-N new primitives (fox_ears, nine_tails, shield, dual_pistols, huge_hammer, scythe, gun, …). Re-run P1 loop. | Wider renderer vocab + better P1 sprites. | Medium — new draw code, must test pixel coverage. |
| **P3: Per-skin + switching** | Extend loop to ~1780 skins. Save `sprites/{idx}.png` + `descriptors.json`. Wire `skin_idx` through Hero → WorldCharacter → `load_char_sprite`. | Each skin has its own sprite; changing skin changes the world sprite in-game. | Highest — 1780 sprites + runtime wiring, but combat logic untouched. |

**Ordering rationale:** validate the loop cheaply (170) → expand vocab so P3
bakes only once with the full vocabulary → scale to 1780. Baking P3 before P2
would force re-baking 1780 sprites twice.

### P2 — vocab expansion detail

**Gap-analysis (cheap, no rendering):** one different VLM prompt over a sample
of splash refs:
> "Look at this splash. Name the 1-2 MOST distinct visual features of this
> character's world appearance that a pixel sprite MUST capture (e.g. 'nine
> tails', 'shield', 'dual pistols', 'huge hammer', 'fox ears'). Output JSON
> {features:[...], weapon:[...]} — free-form, not from a fixed vocab."

Aggregate across champs → count frequency of features/weapons the renderer
lacks. Pick top-N (~8-12) most common + most important → implement.

**Implement new primitives** in `src/assets_gen/generate.py`: each is one new
draw function + an entry in the dispatch map (`_FEATURE_DRAW`, `_WEAPON_DRAW`).
Pixel-art, scaled to 256×256, coverage-tested via `verify_assets.py`. Update
the vocab list in `vlm_client.py` + the system prompt so the VLM can request
the new primitives. Re-run the P1 loop and compare match scores before/after.

**Risk control:** each new primitive is small (~30-60 lines). Implement + test
pixel coverage one at a time before re-running the loop. A broken primitive is
dropped — it cannot corrupt already-baked sprites (committed PNGs don't depend
on runtime vocab).

## Verification strategy

Three layers; each phase must be green before the next.

**1. Build-time — VLM match-score log.** Every skin writes
`{match, iters, ok}` into `descriptors.json`. End-of-run aggregate: mean match
before (round 0) vs after (best), % converged < 10 rounds, # skins ok.
- **P1 gate:** mean match ≥ 6 and no skin worse than its round 0 (loop only
  improves). (Convergence itself is gated on the VLM's own `ok`; the match
  threshold is an aggregate quality bar, not a per-skin stop condition.)
- **P2 gate:** mean match after-expand > before-expand (new vocab must help).

**2. Asset verify (`tools/verify_assets.py`, headless, no image reading).**
Currently checks `sprite.png` exists + 256×256 + archetype distinctness (mean
coverage differs). P1 overwrites `sprite.png` → must still pass. P3 extends
the checker: `sprites/{idx}.png` (if present) = 256×256 + alpha-bbox in bounds
+ coverage > 0 (not blank); `descriptors.json` parseable.
Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets`.

**3. Game acceptance (`/tmp/verify_complete.py`, 21 tests).** Game logic is
untouched (only assets + 3 small wiring edits). Must stay green: boot, 9 scene
renders, combat, edge transitions, teleport, save, gacha, audio, boss, 600-frame
long-run. **P3 adds a test:** set `rec["skin"]` → `get_hero_instance` →
`WorldCharacter._sprite` loads the right `sprites/{idx}.png` (assert the load
path, not pixels). Add to `tools/verify_ecs.py` or a dedicated suite.

**Per-phase smoke:**
```bash
SDL_VIDEODRIVER=dummy python3 -c "
import main; from src.scenes.world import WorldScene
g=main.Game(); g.goto('world'); sc=g.scene
[sc.update(0.016,[]) or sc.draw(g.screen) for _ in range(120)]
print('boot+play ok')"
```

## Risk fences

- **Stochastic loop** → baked PNGs committed (deterministic runtime). Re-bake
  only on `--force`.
- **VLM endpoint down** → build fails gracefully (skip that skin, keep old
  sprite, log error). Never crashes the game.
- **Broken new primitive** → `verify_assets` catches it (coverage 0 / wrong
  size) before merge.
- **HARD CONSTRAINT preserved:** never Read a PNG/JPG via the Read tool. The
  VLM reads images over HTTP base64 (outside the Claude session); the build
  script uses headless `pygame.image.load`. The session-crash constraint from
  `AGENTS.md` / memory `gacha-no-image-reading` is not violated.

## Out of scope

- Replacing the pixel renderer with the VLM drawing directly (the VLM cannot
  draw; it only describes/critiques).
- Mid-scene hot-swap of the world sprite on skin change (deferred — re-entering
  the world is sufficient and simpler).
- Re-baking non-sprite assets (portraits/icons/skill icons are real LoL art;
  unchanged).
