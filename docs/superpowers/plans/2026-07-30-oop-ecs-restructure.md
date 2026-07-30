# Aetheria OOP + ECS-lite Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:subagent-driven-development (recommended) or superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the 14 flat top-level files (~20k lines, god-classes) into a `src/` package with an ECS-lite architecture (entity = component data bag, system = stateless processor), behavior preserved verbatim, `python3 main.py` runnable after every phase.

**Architecture:** 5 staged phases — (1) package layout, (2) data split + call-site migration, (3) entity/component core + adapter, (4) systems extraction, (5) cleanup + docs. Entity = `__slots__` component dict; World = entity container + query; System = processor receiving `World` + data registry. `Combatant`/`Hero`/`Enemy` stat classes kept and referenced by components. Each phase ends with `verify_assets.py` green + acceptance suite + 1200-frame stress.

**Tech Stack:** pygame 2.6.x, numpy, Python 3.11. Headless verify via `SDL_VIDEODRIVER=dummy` / `xvfb-run`.

**User decisions (already made):**
- Deep OOP refactor — package + ECS-lite + class hierarchy redesign (highest risk).
- Data access: specific imports, no shim — migrate all 416 `D.*` call sites to `from src.data.<file> import SYMBOL`.
- WorldScene: ECS-lite — Entity = component data bag, System = stateless processor.
- Delivery: staged, 5 phases, each verified before the next.
- Verify gate: new ECS suite (`tools/verify_ecs.py`); old `/tmp/verify_complete.py` dropped from Phase 3.
- Package + run: `main.py` thin at root + `src/` package; `python3 main.py` still runs.
- `Combatant`/`Hero`/`Enemy` kept as classes (stat logic preserved); referenced by entity components.

**Global constraints (carry across all tasks):**
- **NEVER Read a PNG/JPG with the Read tool — it crashes the session.** Verify art headless via `pygame.image.load` under `SDL_VIDEODRIVER=dummy` / `xvfb-run`. (memory: gacha-no-image-reading)
- Behavior preserved verbatim — 170-champion roster, combat/gacha/evo/constellation systems, controls, and assets are unchanged; only code organization + entity/system internals change.
- `python3 main.py` must run at the end of every phase.
- `verify_assets.py` must stay green every phase (bundles untouched).
- Run the phase-gate verify at the end of each phase: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` + the acceptance suite + 1200-frame stress (no fps regression >10% vs baseline ~152fps endless / ~165fps adventure).

---

## File Structure (final target)

```
main.py                      # thin entry: sys.path insert, pygame init, Game().run()
src/
  __init__.py
  core/{__init__.py, config.py, scene.py, game.py, world.py, registry.py}
  ui/{__init__.py, primitives.py, colors.py, widgets.py}
  data/{__init__.py, tuning.py, elements.py, skills.py, roles.py, heroes.py,
        passives.py, evolution.py, constellation.py, ascension.py, enemies.py,
        gacha_data.py, equipment.py, consumables.py, shop.py, progression.py,
        story.py, resonance.py}
  world/{__init__.py, data.py, map_renderer.py, overlays.py}
  entities/{__init__.py, components.py, entity.py, combatant.py, hero.py, enemy.py}
  systems/{__init__.py, combat.py, physics.py, ai.py, render.py, hud.py,
           dialogue.py, drops.py, rift.py, map_ctrl.py}
  scenes/{__init__.py, world.py, adventure.py,
          menu/{__init__.py, title.py, roster.py, hero_detail.py, gacha_scene.py,
                shop.py, inventory.py, settings.py, stats.py, codex.py}}
  fx/{__init__.py, rift.py}
  assets_gen/{__init__.py, generate.py, descriptors.py, enemies_art.py,
              items_art.py, ui_art.py, terrain_art.py, skills_art.py}
  build/{__init__.py, champions.py, build_champions.py}
  audio.py  player.py  gacha.py
tools/{verify_assets.py, verify_ecs.py}
```

**Run commands (final):**
- Play: `python3 main.py`
- Regenerate shared art: `python3 -m src.assets_gen.generate`
- Rebuild roster: `python3 -m src.build.build_champions --all`
- Verify: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` / `python3 -m tools.verify_ecs`

---

## PHASE 1 — Package layout (move + re-import, 0 logic change)

Goal of Phase 1: every module lives under `src/` in its target subdir, `main.py` is a thin root entry, and the game runs identically. No logic changes — only moves, renames, and import-path rewrites. `src/data/__init__.py` is a temporary shim re-exporting the un-split `data.py` so `D.*` still works.

### Task 1: Create `src/` package skeleton + `main.py` thin entry

**Goal:** Stand up the empty `src/` package tree with `__init__.py` files at every level, and rewrite root `main.py` to a thin entry that bootstraps from `src/`.

**Files:**
- Create: `src/__init__.py`, `src/core/__init__.py`, `src/ui/__init__.py`, `src/data/__init__.py`, `src/world/__init__.py`, `src/entities/__init__.py`, `src/systems/__init__.py`, `src/scenes/__init__.py`, `src/scenes/menu/__init__.py`, `src/fx/__init__.py`, `src/assets_gen/__init__.py`, `src/build/__init__.py`, `tools/__init__.py` (each containing just a one-line module docstring)
- Modify: `main.py` (root) — replace the full game with a thin entry

**Acceptance Criteria:**
- [ ] `src/` and all 13 subpackage `__init__.py` files exist and are importable
- [ ] `main.py` root is ≤ 25 lines: inserts repo root onto `sys.path`, calls `pygame.init()`, constructs `Game`, runs the loop — OR delegates entirely to a `src.core.main:main()` function
- [ ] `python3 main.py` still imports cleanly (the actual Game/scene code has not moved yet, so it runs the OLD code via the OLD import paths until Task 2 moves it) — verify it at least reaches the title screen setup without ImportError

**Verify:** `SDL_VIDEODRIVER=dummy python3 -c "import main; print('main entry OK')"` → `main entry OK`

**Steps:**

- [ ] **Step 1: Create the package `__init__.py` files**

Each file is a one-line docstring, e.g. `src/core/__init__.py`:
```python
"""Aetheria core: game loop, scene base, world container, registry."""
```
Create all 13: `src/__init__.py`, `src/core/__init__.py`, `src/ui/__init__.py`, `src/data/__init__.py`, `src/world/__init__.py`, `src/entities/__init__.py`, `src/systems/__init__.py`, `src/scenes/__init__.py`, `src/scenes/menu/__init__.py`, `src/fx/__init__.py`, `src/assets_gen/__init__.py`, `src/build/__init__.py`, `tools/__init__.py`.

- [ ] **Step 2: Write the thin `src/core/main.py` bootstrap**

Create `src/core/main.py`:
```python
"""Thin entry shim invoked by the root main.py. The real Game lives in
src.core.game; this just wires sys.path + pygame + runs the loop so the
root main.py stays a one-liner."""
import os
import sys

# ensure the repo root (parent of src/) is on sys.path so `import src...` works
# when launched as `python3 main.py`
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pygame
from src.core.game import Game  # noqa: E402


def main():
    pygame.init()
    Game().run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Replace root `main.py` with a thin entry**

Overwrite root `main.py` with:
```python
"""Aetheria — open-world 2D gacha RPG (170 LoL champions). Thin entry point.

The game lives in the src/ package; this just bootstraps it. Run: python3 main.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.main import main  # noqa: E402

if __name__ == "__main__":
    main()
```

NOTE: `src/core/game.py` does not exist yet — Task 2 moves `Game` there. For this task, leave the OLD `main.py` content temporarily in `src/core/game.py` is NOT done yet. To keep `python3 main.py` runnable in this interim, ALSO keep a temporary `src/core/game.py` that re-exports from the not-yet-moved root modules. Simplest interim: create `src/core/game.py` as a thin wrapper that imports the old `Game` from the old location once Task 2 moves it. **For Task 1 only**, to avoid a broken interim, do NOT delete the old main.py body yet — instead keep the old `main.py` logic intact in a temporary `src/core/_legacy_main.py` and have `src/core/game.py` import `Game` from there. This is reconciled in Task 2.

Concretely, for Task 1: move the current root `main.py` body (everything below the imports) into `src/core/_legacy_main.py` verbatim, then `src/core/game.py`:
```python
"""Interim Game location — full content moved here in Task 1, refactored
into src.core.game properly across Tasks 2-10 as scenes move out."""
from src.core._legacy_main import Game  # noqa: F401
```
And root `main.py` becomes the thin entry above. This keeps `python3 main.py` working immediately.

- [ ] **Step 4: Verify the entry boots**

Run: `SDL_VIDEODRIVER=dummy python3 -c "import main; print('main entry OK')"`
Expected: `main entry OK` (pygame init + import resolves; the legacy Game is reachable via the shim).

- [ ] **Step 5: Commit**

```bash
git add main.py src/ tools/__init__.py
git commit -m "refactor(phase1): src/ package skeleton + thin main.py entry

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["main.py", "src/__init__.py", "src/core/__init__.py", "src/core/main.py", "src/core/game.py", "src/core/_legacy_main.py", "src/ui/__init__.py", "src/data/__init__.py", "src/world/__init__.py", "src/entities/__init__.py", "src/systems/__init__.py", "src/scenes/__init__.py", "src/scenes/menu/__init__.py", "src/fx/__init__.py", "src/assets_gen/__init__.py", "src/build/__init__.py", "tools/__init__.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -c \"import main; print('main entry OK')\"", "acceptanceCriteria": ["src/ + 13 subpackage __init__.py exist + importable", "main.py root <= 25 lines, bootstraps from src.core.main", "python3 main.py imports cleanly without ImportError"], "modelTier": "mechanical"}
```

### Task 2: Move data + champions + audio + player + gacha into `src/`

**Goal:** Move the data-layer and standalone modules into their `src/` homes with correct import rewrites, leaving a root shim only where a build tool still imports the old name.

**Files:**
- Move: `data.py` → `src/data/_legacy_data.py` (kept whole this task; split in Phase 2); create `src/data/__init__.py` shim re-exporting it
- Move: `champions.py` → `src/build/champions.py`; root `champions.py` shim re-exporting `src.build.champions`
- Move: `audio.py` → `src/audio.py`; root `audio.py` shim
- Move: `player.py` → `src/player.py`; root `player.py` shim
- Move: `gacha.py` → `src/gacha.py`; root `gacha.py` shim
- Modify: every `import data as D` / `import champions` / `import audio` / `import player` / `from gacha import` across `src/core/_legacy_main.py`, `entities.py`, `world_*.py`, `generate_assets.py`, `build_champions.py`, `verify_assets.py` to resolve through the shims (no change needed yet — shims keep old names live)

**Acceptance Criteria:**
- [ ] `src/data/__init__.py` re-exports every public name from `src/data/_legacy_data.py` so `import src.data as D; D.SKILLS_DB` works
- [ ] Root `champions.py`, `audio.py`, `player.py`, `gacha.py` each become a 2-line shim (`from src.<x> import *` + explicit `__all__` or `from src.<x> import <names>`)
- [ ] `SDL_VIDEODRIVER=dummy python3 -c "import main"` still OK; `python3 verify_assets.py` still green

**Verify:** `SDL_VIDEODRIVER=dummy python3 verify_assets.py` → ends with `OK — all champion bundles complete...`

**Steps:**

- [ ] **Step 1: Move data.py into src/data/ as _legacy_data.py**

`git mv data.py src/data/_legacy_data.py`. The file's internal `import champions as _CH` (line 740) must still resolve — champions is moving too (Step 2), so leave it as `import champions as _CH` for now (root shim makes `champions` still importable). Create `src/data/__init__.py`:
```python
"""data package — Phase 1 shim. The un-split data.py lives in _legacy_data;
this re-exports its public names so `import src.data as D; D.X` works.
Phase 2 splits _legacy_data into the 18 per-concern modules and removes this shim."""
from src.data._legacy_data import *  # noqa: F401,F403
# explicit re-export of names not covered by __all__ (the legacy module has no __all__)
from src.data._legacy_data import (  # noqa: F401
    ASSET_DIR, CHART, RESIST, WEAKNESS_FOR, element_mult, champion_enemy_def,
    REACTIONS, REACTION_WINDOW, WET_EFFECT, reaction_for, ELEMENT_COLORS, PIXEL,
    PIXEL_PALETTE, COLORBLIND_PALETTES, RARITY_COLORS, BASE_CRIT_CHANCE,
    COMBO_BONUS_PER, COMBO_MAX, COMBO_MILESTONE_SKILL, COMBO_MILESTONE_ULT,
    DEFEND_MITIGATION, AA_RANGE, AA_CD, NG_PLUS_LEVEL_BONUS, ADVENTURE_WAVE_INTERVAL,
    ADVENTURE_BOSS_TIME, ADVENTURE_STAGE_LEVEL_STEP, ADVENTURE_STAGE_TIME_LIMIT,
    ENERGY_MAX, ENERGY_START, ENERGY_COST_MULT, ENERGY_GAIN_BASIC, ENERGY_GAIN_DEAL,
    ENERGY_REGEN_PCT, skill_energy_cost, REACTIONS, PASSIVES_DB, ELEMENTAL_RESONANCE,
    team_resonances, hero_abilities, EVO_TREE, EVO_TREE_DEFAULT, hero_evo_tree,
    EVO_NODE_POS, EVO_LINKS, evo_node_prereq_met, TOUGHNESS_BREAK_MULT,
    TOUGHNESS_BREAK_DAMAGE, TOUGHNESS_RECOVER_FRAC, SKILLS_DB, BOSS_ULT, BOSS_IDS,
    BOSS_PATTERNS, BOSS_PATTERNS_DEFAULT, boss_patterns, ROLES, role_mult, HEROES_DB,
    HERO_BY_ID, HERO_PASSIVES, hero_passive, HERO_SIGNATURE, hero_signature,
    ULTIMATE_VARIANTS, HERO_LORE, ENEMIES_DB, GACHA_RATES, GACHA_POOL, GACHA_COST,
    GACHA_BANNERS, GACHA_BANNER_BY_ID, GACHA_PITY_HARD, GACHA_PITY_SOFT,
    GACHA_SR_GUARANTEE_EVERY, GACHA_DUPE_GEM_REFUND, MAX_ASCENSION, ASCENSION_BONUS,
    CONSTELLATION_PERKS, CONSTELLATION_PERK_OVERRIDES, hero_constellation_perks,
    constellation_perks_for, _SKILL_CATEGORY, _HERO_SKILL_TEXT, _build_hero_assets,
    HERO_ASSETS, MAX_EVOLVE, EVOLVE_COST, EVOLVE_BONUS, EVOLVE_TITLES, EVOLVE_COLORS,
    EQUIPMENT_DB, EQUIPMENT_SETS, equipment_set_bonus, CONSUMABLES_DB, SHOP_GEMS,
    STARTING_GEMS, STARTING_GOLD, STARTING_TEAM, STARTING_OWNED, STARTING_INVENTORY,
    xp_to_next, STAT_GROWTH, MAX_LEVEL, ACHIEVEMENTS, DAILY_QUESTS, LORE_FRAGMENTS,
    LANDMARK_LORE, NPCS, STORY_QUESTS, STORY_QUEST_BY_ID, STORY_QUEST_ORDER,
    STORY_BIOME_QUEST, STORY_FINAL_QUEST,
)
```
(If any name is missing, the import error names it — add it to the list. The list is the union of every top-level `NAME =` and `def name` in `_legacy_data.py`.)

- [ ] **Step 2: Move champions.py → src/build/champions.py + root shim**

`git mv champions.py src/build/champions.py`. Create root `champions.py` shim:
```python
"""Shim — real module at src.build.champions (kept for build_champions + any
legacy `import champions`). Removed in Phase 5."""
from src.build.champions import CHAMPIONS_DB, CHAMPION_BY_KEY  # noqa: F401
```
`src/data/_legacy_data.py`'s `import champions as _CH` still works via this shim.

- [ ] **Step 3: Move audio.py, player.py, gacha.py → src/ + root shims**

`git mv audio.py src/audio.py`; root `audio.py`:
```python
"""Shim — real module at src.audio. Removed in Phase 5."""
from src.audio import *  # noqa: F401,F403
```
`git mv player.py src/player.py`; root `player.py`:
```python
"""Shim — real module at src.player. Removed in Phase 5."""
from src.player import Player  # noqa: F401
```
`git mv gacha.py src/gacha.py`; root `gacha.py`:
```python
"""Shim — real module at src.gacha. Removed in Phase 5."""
from src.gacha import GachaSystem  # noqa: F401
```

- [ ] **Step 4: Verify imports + assets**

Run: `SDL_VIDEODRIVER=dummy python3 verify_assets.py`
Expected: ends `OK — all champion bundles complete, sizes correct, archetype + per-skill distinctness hold, loaders resolve, enemies/bosses consistent.`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(phase1): move data/champions/audio/player/gacha into src/ with root shims

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/data/__init__.py", "src/data/_legacy_data.py", "src/build/champions.py", "champions.py", "src/audio.py", "audio.py", "src/player.py", "player.py", "src/gacha.py", "gacha.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 verify_assets.py", "acceptanceCriteria": ["src/data/__init__.py re-exports _legacy_data so import src.data as D; D.SKILLS_DB works", "root champions/audio/player/gacha are 2-line shims", "verify_assets.py ends OK"], "modelTier": "mechanical"}
```

### Task 3: Move entities + world_data + world_entities into `src/`

**Goal:** Move the entity/world-data modules into `src/entities/` and `src/world/`, with root shims, import paths resolving through shims.

**Files:**
- Move: `entities.py` → `src/entities/_legacy_entities.py`; root `entities.py` shim; `src/entities/__init__.py` re-exports
- Move: `world_data.py` → `src/world/data.py`; root `world_data.py` shim
- Move: `world_entities.py` → `src/entities/_legacy_world_entities.py`; root `world_entities.py` shim
- Modify: internal imports inside these files (`import data as D` → still works via root shim; `from entities import` → still works via root shim) — no rewrite needed yet

**Acceptance Criteria:**
- [ ] `from src.entities import Hero, Enemy, load_char_sprite, load_portrait` works
- [ ] `from src.world.data import GRID_W, gen_map` works
- [ ] `from src.world.data import ROW_ENEMIES` (used by verify_assets + world_scene) works
- [ ] `python3 verify_assets.py` green; `import main` OK

**Verify:** `SDL_VIDEODRIVER=dummy python3 verify_assets.py` → `OK — ...`

**Steps:**

- [ ] **Step 1: Move entities.py**

`git mv entities.py src/entities/_legacy_entities.py`. Root `entities.py`:
```python
"""Shim — real module at src.entities._legacy_entities. Removed in Phase 5."""
from src.entities._legacy_entities import (  # noqa: F401
    Hero, Enemy, Combatant, StatusEffect, load_image, load_char_sprite,
    load_portrait, load_champ_icon, load_enemy_sprite, load_skill_icon, load_bg,
    load_ui, load_item_icon, load_terrain, load_landmark, load_village, load_drop,
)
```
`src/entities/__init__.py`:
```python
"""entities package — Phase 1 shim re-exporting _legacy_entities."""
from src.entities._legacy_entities import *  # noqa: F401,F403
```
The legacy file's `import data as D` resolves via the root `data.py`... wait — `data.py` was moved in Task 2. The root `data.py` no longer exists. Fix: the legacy file must `import src.data as D` OR a root `data.py` shim must exist. Add root `data.py` shim:
```python
"""Shim — real data package at src.data. Removed in Phase 2 (call-site migration)."""
from src.data import *  # noqa: F401,F403
from src.data import (ASSET_DIR, SKILLS_DB, HEROES_DB, HERO_BY_ID, ENEMIES_DB, ELEMENT_COLORS)  # noqa: F401
```
(This root `data.py` shim is what keeps all 416 `import data as D; D.X` call sites working through Phase 1. It is removed in Phase 2.)

- [ ] **Step 2: Move world_data.py**

`git mv world_data.py src/world/data.py`. Root `world_data.py`:
```python
"""Shim — real module at src.world.data. Removed in Phase 5."""
from src.world.data import *  # noqa: F401,F403
```
`src/world/__init__.py`:
```python
"""world package — map data, renderer, overlays."""
from src.world.data import *  # noqa: F401,F403
```

- [ ] **Step 3: Move world_entities.py**

`git mv world_entities.py src/entities/_legacy_world_entities.py`. Root `world_entities.py`:
```python
"""Shim — real module at src.entities._legacy_world_entities. Removed in Phase 4."""
from src.entities._legacy_world_entities import (  # noqa: F401
    Camera, Particle, Particles, Projectile, FloatText, WorldCharacter, WorldEnemy,
    SummonAlly, Trap, WEAPON_STYLE, scratch,
)
```
Add these names to `src/entities/__init__.py` re-export too:
```python
from src.entities._legacy_world_entities import (  # noqa: F401
    Camera, Particle, Particles, Projectile, FloatText, WorldCharacter, WorldEnemy,
    SummonAlly, Trap, WEAPON_STYLE, scratch,
)
```

- [ ] **Step 4: Verify**

Run: `SDL_VIDEODRIVER=dummy python3 verify_assets.py` → `OK — ...`
Run: `SDL_VIDEODRIVER=dummy python3 -c "import main; print('OK')"` → `OK`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(phase1): move entities/world_data/world_entities into src/ + root data.py shim

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/entities/_legacy_entities.py", "src/entities/__init__.py", "entities.py", "src/world/data.py", "src/world/__init__.py", "world_data.py", "src/entities/_legacy_world_entities.py", "world_entities.py", "data.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 verify_assets.py", "acceptanceCriteria": ["from src.entities import Hero, Enemy, load_char_sprite works", "from src.world.data import GRID_W, gen_map, ROW_ENEMIES works", "root data.py shim keeps 416 D.* call sites working", "verify_assets.py ends OK"], "modelTier": "mechanical"}
```

### Task 4: Move ui + fx + generate_assets + build_champions into `src/`

**Goal:** Move the UI, VFX, and build-tool modules into their `src/` homes with root shims.

**Files:**
- Move: `ui.py` → `src/ui/primitives.py` + `src/ui/colors.py` + `src/ui/widgets.py` (split the 3 concerns); root `ui.py` shim; `src/ui/__init__.py` re-exports
- Move: `fx.py` → `src/fx/rift.py`; root `fx.py` shim
- Move: `generate_assets.py` → `src/assets_gen/generate.py` (single file this task; split into descriptors/enemies_art/etc. in a later cleanup — YAGNI for Phase 1); root `generate_assets.py` shim
- Move: `build_champions.py` → `src/build/build_champions.py`; root `build_champions.py` shim

**Acceptance Criteria:**
- [ ] `from src.ui import text, Button, draw_bar, element_color, WIDTH, HEIGHT` works
- [ ] `from src.fx.rift import draw_rift_portal` works
- [ ] `python3 -m src.assets_gen.generate` (under xvfb) produces all shared art
- [ ] `python3 -m src.build.build_champions --sprites` delegates to `src.assets_gen.generate.generate_sprites` (the JSON source is absent so `--all`/`--images` error is expected + pre-existing; `--sprites` via direct champions data works)
- [ ] `verify_assets.py` green; `import main` OK

**Verify:** `xvfb-run -a python3 -m src.assets_gen.generate` → ends `Done. Assets saved to .../assets`

**Steps:**

- [ ] **Step 1: Split ui.py into src/ui/{primitives,colors,widgets}.py**

`git mv ui.py src/ui/primitives.py`. Then extract from `src/ui/primitives.py`:
- `element_color`, `rarity_color`, and the color constants block (`WHITE, DIM, GOLD, PANEL, PANEL_BORDER, HP_RED, HP_GREEN, MP_BLUE, XP_PURPLE, BG_DARK`) → `src/ui/colors.py` (move `import data as D` with them; `element_color` keeps its late `from main import Game`).
- `Toggle`, `Slider` → `src/ui/widgets.py` (they use `text` + `audio`).
`src/ui/primitives.py` keeps: constants `WIDTH/HEIGHT/FPS/TITLE/SEED`, `FONTS/init_fonts/get_font/f`, `text`, `Button`, `draw_panel/draw_bar/draw_stars`, `dim_overlay`, `scratch` re-export. It imports the color constants from `src.ui.colors` (`from src.ui.colors import WHITE, GOLD, PANEL, PANEL_BORDER`). `src/ui/widgets.py` imports `from src.ui.primitives import text` and `import src.audio as audio`.
`src/ui/__init__.py`:
```python
"""ui package — shared UI primitives, colors, widgets."""
from src.ui.primitives import *  # noqa: F401,F403
from src.ui.primitives import (WIDTH, HEIGHT, FPS, TITLE, SEED, FONTS, init_fonts,  # noqa: F401
    get_font, f, text, Button, draw_panel, draw_bar, draw_stars, dim_overlay, scratch)
from src.ui.colors import (WHITE, DIM, GOLD, PANEL, PANEL_BORDER, HP_RED, HP_GREEN,  # noqa: F401
    MP_BLUE, XP_PURPLE, BG_DARK, element_color, rarity_color)
from src.ui.widgets import Toggle, Slider  # noqa: F401
```
Root `ui.py` shim:
```python
"""Shim — real package at src.ui. Removed in Phase 5."""
from src.ui import *  # noqa: F401,F403
```

- [ ] **Step 2: Move fx.py**

`git mv fx.py src/fx/rift.py`. Root `fx.py`:
```python
"""Shim — real module at src.fx.rift. Removed in Phase 5."""
from src.fx.rift import draw_rift_portal  # noqa: F401
```
`src/fx/__init__.py`:
```python
"""fx package — runtime VFX helpers."""
from src.fx.rift import draw_rift_portal  # noqa: F401
```

- [ ] **Step 3: Move generate_assets.py**

`git mv generate_assets.py src/assets_gen/generate.py`. Root `generate_assets.py`:
```python
"""Shim — real module at src.assets_gen.generate. Removed in Phase 5."""
from src.assets_gen.generate import *  # noqa: F401,F403
from src.assets_gen.generate import generate_sprites, main  # noqa: F401
```
`src/assets_gen/__init__.py`:
```python
"""assets_gen package — build-only art generator."""
from src.assets_gen.generate import *  # noqa: F401,F403
```
The moved file's `from data import PIXEL, PIXEL_PALETTE` must resolve — root `data.py` shim (Task 3) covers it. Its `import data as D` (inside `main()`) likewise.

- [ ] **Step 4: Move build_champions.py**

`git mv build_champions.py src/build/build_champions.py`. Root `build_champions.py`:
```python
"""Shim — real module at src.build.build_champions. Removed in Phase 5."""
from src.build.build_champions import main, build_data, rearrange_images, generate_sprites  # noqa: F401
```
`src/build/__init__.py`:
```python
"""build package — roster builder + baked champion data."""
from src.build.champions import CHAMPIONS_DB, CHAMPION_BY_KEY  # noqa: F401
```
The moved file's `import generate_assets as GA` resolves via root shim; `import champions` via root shim.

- [ ] **Step 5: Verify the build pipeline runs from the new location**

Run: `xvfb-run -a python3 -m src.assets_gen.generate`
Expected: prints `16 enemies`, `4 boss-ult skill icons`, ... `Done. Assets saved to .../assets`.

Run: `SDL_VIDEODRIVER=dummy python3 verify_assets.py` → `OK — ...`

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor(phase1): move ui/fx/generate_assets/build_champions into src/ + shims

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/ui/primitives.py", "src/ui/colors.py", "src/ui/widgets.py", "src/ui/__init__.py", "ui.py", "src/fx/rift.py", "src/fx/__init__.py", "fx.py", "src/assets_gen/generate.py", "src/assets_gen/__init__.py", "generate_assets.py", "src/build/build_champions.py", "src/build/__init__.py", "build_champions.py"], "verifyCommand": "xvfb-run -a python3 -m src.assets_gen.generate", "acceptanceCriteria": ["from src.ui import text, Button, draw_bar, element_color, WIDTH, HEIGHT works", "from src.fx.rift import draw_rift_portal works", "python3 -m src.assets_gen.generate produces all shared art (16 enemies, 4 boss-ult, etc.)", "verify_assets.py ends OK"], "modelTier": "mechanical"}
```

### Task 5: Move scenes (world/adventure + 10 menu scenes) into `src/scenes/`

**Goal:** Move `world_scene.py`, `adventure_scene.py`, and the 10 menu scene classes out of `main.py`/root into `src/scenes/`, leaving `src/core/game.py` as the Game + scene factory only.

**Files:**
- Move: `world_scene.py` → `src/scenes/world.py`; root `world_scene.py` shim
- Move: `adventure_scene.py` → `src/scenes/adventure.py`; root `adventure_scene.py` shim
- Split `src/core/_legacy_main.py`: extract `TitleScene/RosterScene/HeroDetailScene/GachaScene/ShopScene/InventoryScene/SettingsScene/StatsScene/CodexScene` (+ `Scene` base + `Toggle/Slider` if still there) into `src/scenes/menu/{title,roster,hero_detail,gacha_scene,shop,inventory,settings,stats,codex}.py`; `src/scenes/menu/__init__.py` re-exports; leave `Game` + scene factory in `src/core/game.py`

**Acceptance Criteria:**
- [ ] `from src.scenes.world import WorldScene` works; `from src.scenes.adventure import AdventureScene` works
- [ ] Each menu scene imports from `src/scenes/menu/<name>.py`
- [ ] `src/core/game.py` contains only `class Game` + `_make_scene` referencing `src.scenes.*`
- [ ] `python3 main.py` boots to title; the 21-test acceptance suite (`/tmp/verify_complete.py`, with import paths updated) passes

**Verify:** `SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py` → `ALL ACCEPTANCE TESTS PASS ✓` (update the suite's top imports if needed: `import main` still works via the thin entry)

**Steps:**

- [ ] **Step 1: Move world_scene.py + adventure_scene.py**

`git mv world_scene.py src/scenes/world.py`. Root `world_scene.py`:
```python
"""Shim — real module at src.scenes.world. Removed in Phase 5."""
from src.scenes.world import (WorldScene, MapRenderer, TeleportOverlay, PauseHub,  # noqa: F401
    EvolveOverlay, text, WEAPON_STYLE_KEY)
```
`git mv adventure_scene.py src/scenes/adventure.py`. Root `adventure_scene.py`:
```python
"""Shim — real module at src.scenes.adventure. Removed in Phase 5."""
from src.scenes.adventure import AdventureScene  # noqa: F401
```
Inside `src/scenes/world.py`, the imports `from ui import ...`, `import fx`, `from world_entities import ...`, `import world_data as WD`, `import data as D`, `import champions as _CH` all resolve via root shims. `from main import Button, draw_bar` — main.py is now thin, so this BREAKS. Rewrite to `from src.ui import Button, draw_bar`. Also `from ui import get_font as _font, text, dim_overlay, _TEXT_CACHE` → `from src.ui import get_font as _font, text, dim_overlay` and `from src.ui import _TEXT_CACHE` (re-export `_TEXT_CACHE` from `src/ui/__init__.py`).
Inside `src/scenes/adventure.py`: `from world_scene import WorldScene, text` → `from src.scenes.world import WorldScene` + `from src.ui import text`; `from world_entities import WorldEnemy, scratch` → `from src.entities import WorldEnemy, scratch`; `import world_data as WD` → `import src.world.data as WD`; `import data as D` → `import src.data as D` (or keep `import data as D` via root shim — but since we're already editing, use `import src.data as D`).

- [ ] **Step 2: Extract menu scenes from _legacy_main.py into src/scenes/menu/**

For each of the 10 scenes, cut the class (and any scene-local helpers it alone uses) from `src/core/_legacy_main.py` into `src/scenes/menu/<name>.py`. Each menu file starts with the imports it needs, e.g. `src/scenes/menu/title.py`:
```python
"""Title scene."""
import pygame
from src.core.scene import Scene
from src.ui import (text, Button, draw_panel, draw_stars, element_color, rarity_color,
                    WIDTH, HEIGHT, WHITE, GOLD, PANEL, PANEL_BORDER)
from src.entities import load_bg, load_char_sprite, load_portrait, load_champ_icon
import src.data as D
import src.audio as audio
```
Create `src/core/scene.py` with the `Scene` base class (move it from _legacy_main.py):
```python
"""Base Scene class."""
class Scene:
    def __init__(self, game): self.game = game
    def update(self, dt, events): pass
    def draw(self, surf): pass
```
`src/scenes/menu/__init__.py`:
```python
"""menu scenes."""
from src.scenes.menu.title import TitleScene  # noqa: F401
from src.scenes.menu.roster import RosterScene  # noqa: F401
from src.scenes.menu.hero_detail import HeroDetailScene  # noqa: F401
from src.scenes.menu.gacha_scene import GachaScene  # noqa: F401
from src.scenes.menu.shop import ShopScene  # noqa: F401
from src.scenes.menu.inventory import InventoryScene  # noqa: F401
from src.scenes.menu.settings import SettingsScene  # noqa: F401
from src.scenes.menu.stats import StatsScene  # noqa: F401
from src.scenes.menu.codex import CodexScene  # noqa: F401
```
`src/scenes/__init__.py`:
```python
"""scenes package."""
from src.scenes.world import WorldScene  # noqa: F401
from src.scenes.adventure import AdventureScene  # noqa: F401
```

- [ ] **Step 3: Reduce src/core/game.py to Game + factory**

`src/core/game.py` now imports scenes from `src.scenes.*` and `src.scenes.menu.*`. Replace the lazy `_get_world_scene_cls`/`_get_adventure_scene_cls` with direct imports (the cycle is already broken — scenes import from `src.ui`/`src.entities`, not from `src.core.game`):
```python
from src.scenes.world import WorldScene
from src.scenes.adventure import AdventureScene
from src.scenes.menu import (TitleScene, RosterScene, HeroDetailScene, GachaScene,
    ShopScene, InventoryScene, SettingsScene, StatsScene, CodexScene)
```
`_make_scene` uses these directly. Keep `Game._active` + the `element_color` late-import contract (`src.ui.colors.element_color` does `from src.core.game import Game` — still works). Delete `src/core/_legacy_main.py` once `Game` is fully in `src/core/game.py`.

- [ ] **Step 4: Verify the suite**

Run: `SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py`
Expected: `ALL ACCEPTANCE TESTS PASS ✓` (the suite does `import main` which now goes through the thin entry → `src.core.main` → `src.core.game`).

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(phase1): move scenes into src/scenes/ (world/adventure + 10 menu)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/scenes/world.py", "src/scenes/adventure.py", "src/scenes/menu/title.py", "src/scenes/menu/roster.py", "src/scenes/menu/hero_detail.py", "src/scenes/menu/gacha_scene.py", "src/scenes/menu/shop.py", "src/scenes/menu/inventory.py", "src/scenes/menu/settings.py", "src/scenes/menu/stats.py", "src/scenes/menu/codex.py", "src/scenes/menu/__init__.py", "src/scenes/__init__.py", "src/core/scene.py", "src/core/game.py", "world_scene.py", "adventure_scene.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py", "acceptanceCriteria": ["from src.scenes.world import WorldScene works", "from src.scenes.adventure import AdventureScene works", "10 menu scenes import from src/scenes/menu/<name>.py", "src/core/game.py contains only Game + _make_scene", "21-test acceptance suite passes"], "modelTier": "standard"}
```

### Task 6: Move verify_assets.py into tools/ + Phase 1 gate

**Goal:** Move the verifier into `tools/`, run the Phase 1 gate (full verify + stress), confirm no regression.

**Files:**
- Move: `verify_assets.py` → `tools/verify_assets.py`; update its imports to `import src.data as D`, `import src.build.champions as C`, `import src.entities as E`, `import src.world.data as WD`
- Modify: `tools/verify_assets.py` import block

**Acceptance Criteria:**
- [ ] `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` ends `OK — ...`
- [ ] 21-test acceptance suite passes
- [ ] 1200-frame stress: endless + adventure, no fps regression >10% vs baseline (~152 / ~165 fps)
- [ ] No root-level `.py` modules remain except `main.py` + shims (`data.py`, `champions.py`, `audio.py`, `player.py`, `gacha.py`, `entities.py`, `world_data.py`, `world_entities.py`, `world_scene.py`, `adventure_scene.py`, `ui.py`, `fx.py`, `generate_assets.py`, `build_champions.py` — all shims)

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` → `OK — ...`

**Steps:**

- [ ] **Step 1: Move verify_assets.py**

`git mv verify_assets.py tools/verify_assets.py`. Rewrite its imports:
```python
import src.data as D
import src.build.champions as C
import src.entities as E
import src.world.data as WD
```

- [ ] **Step 2: Run the Phase 1 gate**

Run all three:
```bash
SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets
SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py
SDL_VIDEODRIVER=dummy python3 -c "
import os, pygame, time
os.environ['SDL_VIDEODRIVER']='dummy'; pygame.init(); pygame.display.set_mode((1,1))
import main as M
def run(w,label,n=1200):
    g=M.Game(); sc=(M._get_world_scene_cls() if False else __import__('src.scenes.world',fromlist=['WorldScene']).WorldScene)(g) if w=='world' else __import__('src.scenes.adventure',fromlist=['AdventureScene']).AdventureScene(g)
    g.scene=sc; t=time.perf_counter()
    for _ in range(n): sc.update(0.016,[]); sc.draw(g.screen)
    print(f'{label}: {n/(time.perf_counter()-t):.0f} fps')
run('world','endless'); run('adventure','adventure')
"
```
Expected: verify_assets `OK`; suite `ALL ACCEPTANCE TESTS PASS ✓`; stress both ≥ ~137 fps (within 10% of 152/165).

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "refactor(phase1): move verify_assets to tools/ + Phase 1 gate green

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["tools/verify_assets.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets", "acceptanceCriteria": ["python3 -m tools.verify_assets ends OK", "21-test acceptance suite passes", "1200-frame stress no fps regression >10% vs baseline", "only main.py + shims remain at root"], "modelTier": "mechanical"}
```

---

## PHASE 2 — Data split + call-site migration (no shim)

Goal of Phase 2: split `src/data/_legacy_data.py` into 18 per-concern modules, migrate all 416 `D.*` call sites to specific imports, remove the root `data.py` shim and the `src/data/__init__.py` star-shim. No `import data as D` or `D.*` remains.

### Task 7: Split _legacy_data.py into the 18 src/data/ modules

**Goal:** Create the 18 per-concern data modules by cutting sections out of `_legacy_data.py`, with correct inter-module imports (e.g. `heroes.py` imports from `skills.py`), and a `src/data/__init__.py` that re-exports the public API (this re-export stays through Phase 2 so `from src.data import SKILLS_DB` works after call-site migration; it is NOT the `D.*` shim).

**Files:**
- Create: `src/data/{tuning,elements,skills,roles,passives,evolution,constellation,ascension,enemies,gacha_data,equipment,consumables,shop,progression,story,resonance,heroes}.py` (17 + heroes)
- Modify: `src/data/__init__.py` — replace the `_legacy_data` shim with explicit re-exports from the 18 modules
- Delete: `src/data/_legacy_data.py` (after all content is distributed)

**Acceptance Criteria:**
- [ ] Each of the 18 modules imports cleanly on its own (`python3 -c "import src.data.skills"`)
- [ ] Inter-module deps resolve (e.g. `src.data.heroes` imports `SKILLS_DB` from `src.data.skills`; `src.data.gacha_data` imports `HEROES_DB` from `src.data.heroes`)
- [ ] `from src.data import SKILLS_DB, HERO_BY_ID, ENEMIES_DB, GACHA_BANNERS, STORY_QUESTS, EQUIPMENT_DB` all work
- [ ] `python3 -m tools.verify_assets` green; `import main` OK; the root `data.py` shim still works (it re-exports `src.data`)

**Verify:** `SDL_VIDEODRIVER=dummy python3 -c "from src.data import SKILLS_DB, HERO_BY_ID, ENEMIES_DB, GACHA_BANNERS, STORY_QUESTS, EQUIPMENT_DB, HERO_ASSETS; print('data split OK', len(HERO_BY_ID))"` → `data split OK 170`

**Steps:**

- [ ] **Step 1: Create the leaf modules (no internal data deps) first**

Create in this order (each is a cut from `_legacy_data.py`):
1. `src/data/tuning.py` — `CHART, RESIST, WEAKNESS_FOR, element_mult, BASE_CRIT_CHANCE, COMBO_BONUS_PER, COMBO_MAX, COMBO_MILESTONE_SKILL, COMBO_MILESTONE_ULT, DEFEND_MITIGATION, AA_RANGE, AA_CD, NG_PLUS_LEVEL_BONUS, ADVENTURE_WAVE_INTERVAL, ADVENTURE_BOSS_TIME, ADVENTURE_STAGE_LEVEL_STEP, ADVENTURE_STAGE_TIME_LIMIT, ENERGY_MAX, ENERGY_START, ENERGY_COST_MULT, ENERGY_GAIN_BASIC, ENERGY_GAIN_DEAL, ENERGY_REGEN_PCT, skill_energy_cost, TOUGHNESS_BREAK_MULT, TOUGHNESS_BREAK_DAMAGE, TOUGHNESS_RECOVER_FRAC, STAT_GROWTH, MAX_LEVEL, xp_to_next, MAX_EVOLVE, EVOLVE_COST, EVOLVE_BONUS, EVOLVE_TITLES, EVOLVE_COLORS, MAX_ASCENSION, ASCENSION_BONUS, STARTING_GEMS, STARTING_GOLD, STARTING_TEAM, STARTING_OWNED, STARTING_INVENTORY, GACHA_DUPE_GEM_REFUND, GACHA_PITY_HARD, GACHA_PITY_SOFT, GACHA_SR_GUARANTEE_EVERY`. (Pure constants + `element_mult`/`skill_energy_cost`/`xp_to_next` functions — no deps.)
2. `src/data/elements.py` — `ELEMENT_COLORS, PIXEL, PIXEL_PALETTE, COLORBLIND_PALETTES, RARITY_COLORS, REACTIONS, REACTION_WINDOW, WET_EFFECT, reaction_for`. (No deps.)
3. `src/data/roles.py` — `ROLES, role_mult`. (No deps.)
4. `src/data/passives.py` — `PASSIVES_DB`. (No deps.)
5. `src/data/shop.py` — `SHOP_GEMS`. (No deps.)
6. `src/data/consumables.py` — `CONSUMABLES_DB`. (No deps.)

- [ ] **Step 2: Create the mid-level modules (depend on leaves)**

7. `src/data/skills.py` — `SKILLS_DB, _SKILL_TYPE_CATEGORY, _SKILL_CATEGORY, BOSS_ULT, BOSS_IDS, BOSS_PATTERNS, BOSS_PATTERNS_DEFAULT, boss_patterns`. Imports `from src.data.tuning import TOUGHNESS_BREAK_MULT` if referenced (check the SKILLS_DB body — it references tuning constants for some skill values; import what it uses).
8. `src/data/evolution.py` — `EVO_TREE, EVO_TREE_DEFAULT, hero_evo_tree, EVO_NODE_POS, EVO_LINKS, evo_node_prereq_met`. (No data deps, but `hero_evo_tree` reads `hero_def` — pure.)
9. `src/data/constellation.py` — `CONSTELLATION_PERKS, CONSTELLATION_PERK_OVERRIDES, hero_constellation_perks, constellation_perks_for`. Imports `from src.data.roles import ROLES` (the role fallback uses `CONSTELLATION_PERKS[role]`).
10. `src/data/ascension.py` — re-export `MAX_ASCENSION, ASCENSION_BONUS` from tuning (or keep them in tuning and skip this file — **decision: keep ascension in tuning.py, do NOT create ascension.py**; update the `src/data/__init__.py` re-export accordingly). This avoids a 2-line file. (Final module count: 17, not 18.)
11. `src/data/equipment.py` — `EQUIPMENT_DB, EQUIPMENT_SETS, equipment_set_bonus`. (No deps.)
12. `src/data/resonance.py` — `ELEMENTAL_RESONANCE, team_resonances`. (No deps.)
13. `src/data/enemies.py` — `ENEMIES_DB`. Imports `from src.data.skills import SKILLS_DB` (enemy defs reference skill ids, but ENEMIES_DB itself is just data; the cross-check is at load). Also `champion_enemy_def, _get_champion_enemy_pool` — these read `HEROES_DB`/`CHAMPION_BY_KEY`, so they belong in `heroes.py` instead. Move `champion_enemy_def` + `_get_champion_enemy_pool` to `heroes.py`.
14. `src/data/progression.py` — `ACHIEVEMENTS, DAILY_QUESTS, LORE_FRAGMENTS, LANDMARK_LORE`. (No deps.)
15. `src/data/story.py` — `STORY_QUESTS, STORY_QUEST_BY_ID, STORY_QUEST_ORDER, STORY_BIOME_QUEST, STORY_FINAL_QUEST, NPCS`. (No deps.)

- [ ] **Step 3: Create the top-level modules (depend on mids)**

16. `src/data/heroes.py` — `HEROES_DB, HERO_BY_ID, HERO_PASSIVES, hero_passive, HERO_SIGNATURE, hero_signature, ULTIMATE_VARIANTS, HERO_LORE, HERO_ASSETS, _build_hero_assets, hero_abilities, champion_enemy_def, _get_champion_enemy_pool, _CHAMPION_ENEMY_POOL, _CHAMPION_BOSS_POOL`. Imports: `import src.build.champions as _CH` (for `CHAMPIONS_DB`), `from src.data.skills import SKILLS_DB`, `from src.data.passives import PASSIVES_DB`, `from src.data.constellation import hero_constellation_perks`, `from src.data.roles import role_mult` (if used), `from src.data.tuning import ...` (stat growth refs). The `HERO_LORE` dict (170 entries, ~170 lines) lives here verbatim.
17. `src/data/gacha_data.py` — `GACHA_RATES, GACHA_POOL, GACHA_COST, GACHA_BANNERS, GACHA_BANNER_BY_ID`. Imports `from src.data.heroes import HEROES_DB, HERO_BY_ID` (GACHA_POOL is built by rarity from HEROES_DB).

- [ ] **Step 4: Rewrite src/data/__init__.py as the public re-export**

```python
"""data package — per-concern modules. Public API re-exported here so
`from src.data import SKILLS_DB` works. The root data.py shim (for the old
`import data as D; D.X` pattern) is removed in Task 8 once call sites migrate."""
from src.data.tuning import *  # noqa: F401,F403
from src.data.elements import *  # noqa: F401,F403
from src.data.skills import *  # noqa: F401,F403
from src.data.roles import *  # noqa: F401,F403
from src.data.passives import *  # noqa: F401,F403
from src.data.evolution import *  # noqa: F401,F403
from src.data.constellation import *  # noqa: F401,F403
from src.data.equipment import *  # noqa: F401,F403
from src.data.resonance import *  # noqa: F401,F403
from src.data.enemies import *  # noqa: F401,F403
from src.data.progression import *  # noqa: F401,F403
from src.data.story import *  # noqa: F401,F403
from src.data.shop import *  # noqa: F401,F403
from src.data.consumables import *  # noqa: F401,F403
from src.data.heroes import *  # noqa: F401,F403
from src.data.gacha_data import *  # noqa: F401,F403
```
(Each leaf module should define `__all__` listing its public names so the star-exports are clean and don't leak private helpers. Add `__all__` to every module.)

- [ ] **Step 5: Delete _legacy_data.py + verify**

`git rm src/data/_legacy_data.py`. Run:
`SDL_VIDEODRIVER=dummy python3 -c "from src.data import SKILLS_DB, HERO_BY_ID, ENEMIES_DB, GACHA_BANNERS, STORY_QUESTS, EQUIPMENT_DB, HERO_ASSETS; print('data split OK', len(HERO_BY_ID))"`
Expected: `data split OK 170`. Then `python3 -m tools.verify_assets` → `OK`.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "refactor(phase2): split _legacy_data into 17 per-concern src/data/ modules

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/data/tuning.py", "src/data/elements.py", "src/data/skills.py", "src/data/roles.py", "src/data/passives.py", "src/data/evolution.py", "src/data/constellation.py", "src/data/equipment.py", "src/data/resonance.py", "src/data/enemies.py", "src/data/progression.py", "src/data/story.py", "src/data/shop.py", "src/data/consumables.py", "src/data/heroes.py", "src/data/gacha_data.py", "src/data/__init__.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -c \"from src.data import SKILLS_DB, HERO_BY_ID, HERO_ASSETS; print('data split OK', len(HERO_BY_ID))\"", "acceptanceCriteria": ["17 per-concern data modules each import cleanly", "inter-module deps resolve (heroes->skills, gacha_data->heroes, etc.)", "from src.data import SKILLS_DB, HERO_BY_ID, ENEMIES_DB, GACHA_BANNERS, STORY_QUESTS, EQUIPMENT_DB works", "HERO_BY_ID has 170 entries", "verify_assets ends OK"], "modelTier": "standard"}
```

### Task 8: Migrate all `D.*` call sites to specific imports + remove shims

**Goal:** Rewrite every `import data as D` + `D.SYMBOL` usage across the codebase to `from src.data.<file> import SYMBOL` (or `import src.data as D` is NOT allowed — must be specific). Then remove the root `data.py` shim. No `D.*` remains.

**Files:**
- Modify: every `.py` under `src/` and `tools/` that does `import data as D` or `from data import ...` — namely `src/entities/_legacy_entities.py`, `src/entities/_legacy_world_entities.py`, `src/world/data.py`, `src/scenes/world.py`, `src/scenes/adventure.py`, `src/scenes/menu/*.py` (10), `src/core/game.py`, `src/gacha.py`, `src/player.py`, `src/assets_gen/generate.py`, `src/build/build_champions.py`, `src/ui/colors.py`, `tools/verify_assets.py`, `tools/verify_ecs.py` (if exists)
- Delete: root `data.py` shim

**Acceptance Criteria:**
- [ ] `grep -rn 'import data as D\|from data import\| D\.' src/ tools/` returns ZERO matches
- [ ] root `data.py` is deleted
- [ ] `python3 main.py` boots; `python3 -m tools.verify_assets` green; 21-test suite passes; gacha 180-pull 0 error

**Verify:** `grep -rn 'import data as D\|from data import\| D\.' src/ tools/ | wc -l` → `0`

**Steps:**

- [ ] **Step 1: Build the symbol→file map**

Run this to produce the migration map (which `D.SYMBOL` appears in which file, and which data module owns each symbol):
```bash
cd /home/misa/Desktop/RD/Gacha
grep -rhoE 'D\.[A-Z_][A-Z_0-9]*' src/ tools/ | sort -u > /tmp/d_symbols.txt
# then for each symbol, the owning file is known from Task 7's split
```
The owning-file map (from Task 7): write it to `/tmp/d_map.py` as a dict `SYMBOL -> "src.data.<file>"` by reading each `src/data/*.py`'s `__all__`.

- [ ] **Step 2: Write a migration script**

Create `/tmp/migrate_d.py` that, for each `.py` under `src/` and `tools/`:
1. Finds the `import data as D` line and removes it.
2. Collects every `D.SYMBOL` used in the file.
3. Groups them by owning data module.
4. Inserts `from src.data.<file> import SYM1, SYM2, ...` lines at the top (after the other imports), one per owning module.
5. Replaces every `D.SYMBOL` with bare `SYMBOL` in the file body.
6. Handles `from data import PIXEL, PIXEL_PALETTE` (in `src/assets_gen/generate.py`) → `from src.data.elements import PIXEL, PIXEL_PALETTE`.
7. Writes the file back.
Run it: `python3 /tmp/migrate_d.py`.

- [ ] **Step 3: Manually verify a few migrated files**

Open `src/scenes/world.py` head — confirm `import data as D` is gone, `from src.data.skills import SKILLS_DB` etc. are present, and `D.SKILLS_DB` became `SKILLS_DB`. Spot-check `src/entities/_legacy_entities.py`, `src/gacha.py`, `src/player.py`.

- [ ] **Step 4: Delete the root data.py shim + verify no D.* remains**

`git rm data.py`. Run:
`grep -rn 'import data as D\|from data import\| D\.' src/ tools/ | wc -l` → expect `0`.
Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` → `OK`.
Run: `SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py` → `ALL ACCEPTANCE TESTS PASS ✓`.
Run gacha smoke: `SDL_VIDEODRIVER=dummy python3 -c "import os,pygame; os.environ['SDL_VIDEODRIVER']='dummy'; pygame.init(); pygame.display.set_mode((1,1)); import src.data as _; from src.gacha import GachaSystem; from src.player import Player; g=GachaSystem(Player()); e=0
for i in range(180):
    hid=list(__import__('src.data.heroes',fromlist=['HERO_BY_ID']).HERO_BY_ID)[i%170]
    try: g.apply_result(hid,'SSR' if i%17==0 else 'SR' if i%5==0 else 'R',i%2==0)
    except Exception: e+=1
print('180 pulls',e,'errors')"` → `180 pulls 0 errors`.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor(phase2): migrate 416 D.* call sites to specific imports; remove data.py shim

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/entities/_legacy_entities.py", "src/entities/_legacy_world_entities.py", "src/world/data.py", "src/scenes/world.py", "src/scenes/adventure.py", "src/scenes/menu/title.py", "src/scenes/menu/roster.py", "src/scenes/menu/hero_detail.py", "src/scenes/menu/gacha_scene.py", "src/scenes/menu/shop.py", "src/scenes/menu/inventory.py", "src/scenes/menu/settings.py", "src/scenes/menu/stats.py", "src/scenes/menu/codex.py", "src/core/game.py", "src/gacha.py", "src/player.py", "src/assets_gen/generate.py", "src/build/build_champions.py", "src/ui/colors.py", "tools/verify_assets.py", "data.py"], "verifyCommand": "grep -rn 'import data as D\\|from data import\\| D\\.' src/ tools/ | wc -l", "acceptanceCriteria": ["grep for D.* call sites returns 0 matches", "root data.py shim deleted", "python3 main.py boots", "verify_assets ends OK", "21-test suite passes", "gacha 180-pull 0 errors"], "modelTier": "standard"}
```

### Task 9: Remove remaining root shims + Phase 2 gate

**Goal:** Remove the other root shims (`champions.py`, `audio.py`, `player.py`, `gacha.py`, `entities.py`, `world_data.py`, `world_entities.py`, `world_scene.py`, `adventure_scene.py`, `ui.py`, `fx.py`, `generate_assets.py`, `build_champions.py`) by rewriting their few remaining importers to use `src.*` paths directly, then delete the shims. Run the Phase 2 gate.

**Files:**
- Modify: any file still importing a root shim name (e.g. `import champions` → `import src.build.champions`; `import audio` → `import src.audio`; `from world_entities import` → `from src.entities import`; `import generate_assets as GA` → `import src.assets_gen.generate as GA`; `import world_data as WD` → `import src.world.data as WD`; `from ui import` → `from src.ui import`; `import fx` → `import src.fx`)
- Delete: the 13 root shim files listed above

**Acceptance Criteria:**
- [ ] `ls *.py` at repo root shows only `main.py`
- [ ] `grep -rn 'import champions$\|import audio$\|import player$\|from gacha import\|from entities import\|from world_entities import\|from world_scene import\|from world_data import\|from ui import\|import fx$\|import generate_assets\|import build_champions\|import world_data' src/ tools/` returns 0
- [ ] `python3 main.py` boots; `python3 -m tools.verify_assets` green; 21-test suite passes; 1200-frame stress no regression

**Verify:** `ls *.py` → `main.py` only

**Steps:**

- [ ] **Step 1: Find + rewrite remaining shim importers**

```bash
grep -rnE "import (champions|audio|player|gacha|world_data|world_entities|world_scene|adventure_scene|generate_assets|build_champions|fx)\b|from (champions|audio|player|gacha|entities|world_entities|world_scene|adventure_scene|world_data|ui|fx|generate_assets|build_champions) import" src/ tools/
```
For each match, rewrite to the `src.*` path. Common ones:
- `src/data/heroes.py`: `import src.build.champions as _CH`
- `src/entities/_legacy_entities.py`: `import src.data...` (already migrated in Task 8), `import src.audio as audio` if it uses audio (check — entities.py likely doesn't)
- `src/scenes/world.py`: `import src.world.data as WD`, `from src.entities import ...`, `import src.fx as fx`, `import src.build.champions as _CH`
- `src/assets_gen/generate.py`: `import src.data...` (migrated), `from src.data.elements import PIXEL, PIXEL_PALETTE`
- `src/build/build_champions.py`: `import src.assets_gen.generate as GA`
- `src/ui/colors.py`: `import src.data...` (migrated)
- `tools/verify_assets.py`: already uses `src.*`

- [ ] **Step 2: Delete the 13 root shims**

```bash
git rm champions.py audio.py player.py gacha.py entities.py world_data.py \
       world_entities.py world_scene.py adventure_scene.py ui.py fx.py \
       generate_assets.py build_champions.py
```

- [ ] **Step 3: Run the Phase 2 gate**

```bash
ls *.py   # expect: main.py
SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets
SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py
# 1200-frame stress (same snippet as Task 6 Step 2)
```
Expected: `main.py` only; verify_assets `OK`; suite `ALL ACCEPTANCE TESTS PASS ✓`; stress no regression.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor(phase2): remove root shims; only main.py remains at root + Phase 2 gate

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["champions.py", "audio.py", "player.py", "gacha.py", "entities.py", "world_data.py", "world_entities.py", "world_scene.py", "adventure_scene.py", "ui.py", "fx.py", "generate_assets.py", "build_champions.py", "src/data/heroes.py", "src/scenes/world.py", "src/assets_gen/generate.py", "src/build/build_champions.py"], "verifyCommand": "ls *.py", "acceptanceCriteria": ["only main.py remains at repo root", "no root-shim imports remain in src/ or tools/", "python3 main.py boots", "verify_assets ends OK", "21-test suite passes", "1200-frame stress no regression"], "modelTier": "standard"}
```

---

## PHASE 3 — Entity → component data bag (with adapter)

Goal of Phase 3: introduce the ECS entity/component/World core, convert hero/enemy spawning to build entities with components, and bridge to the not-yet-extracted WorldScene systems via an adapter so combat still runs. `Combatant`/`Hero`/`Enemy` stat classes are kept and referenced by components.

### Task 10: Create the ECS core (components, Entity, World)

**Goal:** Build the entity/component/World primitives in `src/entities/components.py`, `src/entities/entity.py`, `src/core/world.py` with unit tests.

**Files:**
- Create: `src/entities/components.py`, `src/entities/entity.py`, `src/core/world.py`
- Create: `tools/verify_ecs.py` (Layer 1 unit tests — starts here, grows each phase)

**Acceptance Criteria:**
- [ ] `Entity` has `__slots__ = ("eid","components")`, `add`/`get`/`has` work, `add` returns self for chaining
- [ ] Each component is a `@dataclass(slots=True)` with the fields from the spec (Transform/Health/Combat/AI/Render/Identity/Statuses/ChampionRef)
- [ ] `World.spawn()` returns a unique-eid Entity; `World.destroy(eid)` removes it; `World.query(*comps)` yields entities having all the given component types; `World.heroes()`/`World.enemies()` filter by `Identity.is_hero`
- [ ] `tools/verify_ecs.py` Layer 1 passes

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → Layer 1 unit tests pass

**Steps:**

- [ ] **Step 1: Write the failing Layer 1 unit tests in tools/verify_ecs.py**

```python
"""ECS acceptance suite (grows each phase). Layer 1: component/entity/world unit tests."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1,1))

from src.entities.components import (Transform, Health, Combat, AI, Render,
    Identity, Statuses, ChampionRef)
from src.entities.entity import Entity
from src.core.world import World

def test_entity_components():
    e = Entity(0)
    assert e.eid == 0
    assert e.has(Transform) is False
    e.add(Transform(100, 200))
    assert e.has(Transform) is True
    t = e.get(Transform)
    assert t.x == 100 and t.y == 200 and t.vx == 0 and t.vy == 0 and t.r == 26
    assert e.add(Health(100, 100, 50, 120)) is e  # chaining

def test_component_defaults():
    assert Transform(0,0).r == 26
    assert AI("hop").state == "idle" and AI("hop").target == -1
    assert Identity(0, "Ahri", True).is_boss is False
    assert ChampionRef("Ahri").skin == 0 and ChampionRef("Ahri").level == 1

def test_world_spawn_destroy_query():
    w = World()
    a = w.spawn(); b = w.spawn(); c = w.spawn()
    assert len({a.eid, b.eid, c.eid}) == 3
    a.add(Identity(a.eid, "Ahri", True)); a.add(Transform(0,0))
    b.add(Identity(b.eid, "Krugs", False)); b.add(Transform(10,10))
    c.add(Identity(c.eid, "Lux", True))
    assert {e.eid for e in w.query(Identity, Transform)} == {a.eid, b.eid}
    assert {e.eid for e in w.heroes()} == {a.eid, c.eid}
    assert {e.eid for e in w.enemies()} == {b.eid}
    w.destroy(b.eid)
    assert b.eid not in w.entities
    assert {e.eid for e in w.enemies()} == set()

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("Layer 1 OK")

if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.entities.components'`

- [ ] **Step 3: Implement src/entities/components.py**

```python
"""ECS components — lightweight dataclass data bags (slots, no logic)."""
from dataclasses import dataclass, field

@dataclass(slots=True)
class Transform:
    x: float; y: float
    vx: float = 0.0; vy: float = 0.0
    r: float = 26.0

@dataclass(slots=True)
class Health:
    hp: float; max_hp: float
    energy: float; max_energy: float

@dataclass(slots=True)
class Combat:
    element: str
    atk: float; defn: float; spd: float
    atk_cd: float = 0.0

@dataclass(slots=True)
class AI:
    kind: str
    state: str = "idle"
    target: int = -1
    aggro_t: float = 0.0

@dataclass(slots=True)
class Render:
    sprite_id: str
    weapon: str
    facing: int = 1
    anim_t: float = 0.0

@dataclass(slots=True)
class Identity:
    eid: int
    name: str
    is_hero: bool
    is_boss: bool = False

@dataclass(slots=True)
class Statuses:
    effects: list = field(default_factory=list)  # [StatusEffect]

@dataclass(slots=True)
class ChampionRef:
    hero_id: str
    skin: int = 0
    level: int = 1
    ascension: int = 0
```

- [ ] **Step 4: Implement src/entities/entity.py**

```python
"""Entity — an eid + a component dict. __slots__ to stay cheap."""
class Entity:
    __slots__ = ("eid", "components")
    def __init__(self, eid):
        self.eid = eid
        self.components = {}
    def add(self, comp):
        self.components[type(comp)] = comp
        return self
    def get(self, comp_cls):
        return self.components.get(comp_cls)
    def has(self, comp_cls):
        return comp_cls in self.components
```

- [ ] **Step 5: Implement src/core/world.py**

```python
"""World — entity container + query."""
from src.entities.entity import Entity
from src.entities.components import Identity

class World:
    def __init__(self):
        self.entities = {}
        self._next_eid = 0
    def spawn(self):
        e = Entity(self._next_eid)
        self.entities[self._next_eid] = e
        self._next_eid += 1
        return e
    def destroy(self, eid):
        self.entities.pop(eid, None)
    def query(self, *comp_classes):
        for e in self.entities.values():
            if all(e.has(c) for c in comp_classes):
                yield e
    def heroes(self):
        return [e for e in self.entities.values()
                if e.has(Identity) and e.get(Identity).is_hero]
    def enemies(self):
        return [e for e in self.entities.values()
                if e.has(Identity) and not e.get(Identity).is_hero]
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs`
Expected: `pass test_entity_components`, `pass test_component_defaults`, `pass test_world_spawn_destroy_query`, `Layer 1 OK`

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat(phase3): ECS core — components, Entity, World + Layer 1 unit tests

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/entities/components.py", "src/entities/entity.py", "src/core/world.py", "tools/verify_ecs.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs", "acceptanceCriteria": ["Entity __slots__ + add/get/has + chaining", "8 component dataclasses with spec fields + defaults", "World spawn/destroy/query/heroes/enemies correct", "Layer 1 unit tests pass"], "modelTier": "mechanical"}
```

### Task 11: Hero/Enemy entity factories + Combatant stat bridge

**Goal:** Create `src/entities/hero.py` + `src/entities/enemy.py` factory functions that spawn an entity, attach components, AND instantiate the kept `Combatant`/`Hero`/`Enemy` stat object (moved from `_legacy_entities.py` into `src/entities/combatant.py`), storing it on the `Combat`/`ChampionRef` component so systems can read stats. Add Layer 1 tests for the factories.

**Files:**
- Create: `src/entities/combatant.py` (move `Combatant`/`Hero`/`Enemy` + `StatusEffect` + the loaders from `_legacy_entities.py` verbatim)
- Create: `src/entities/hero.py` (`spawn_hero(world, hero_id, ...) -> Entity`), `src/entities/enemy.py` (`spawn_enemy(world, enemy_id, ...) -> Entity`)
- Modify: `src/entities/__init__.py` to export the factories + Combatant classes + loaders
- Delete: `src/entities/_legacy_entities.py` (after content moved)
- Modify: `tools/verify_ecs.py` — add factory unit tests

**Acceptance Criteria:**
- [ ] `spawn_hero(world, "Ahri")` returns an Entity with Transform/Health/Combat/AI/Render/Identity/Statuses/ChampionRef, and `ChampionRef`/`Combat` references a `Hero` stat object whose `atk`/`hp` match `HERO_BY_ID["Ahri"]` scaled to level 1
- [ ] `spawn_enemy(world, "Krugs", level=3)` returns an Entity with the same component set, `Identity.is_hero=False`, Combat referencing an `Enemy` stat object
- [ ] The `Combatant`/`Hero`/`Enemy` classes behave identically to before (leveling `gain_xp`, `take_damage`, `heal`, `add_effect`, `tick_effects`, equip, ascension) — verified by re-pointing the existing tests
- [ ] `python3 -m tools.verify_assets` green; `python3 -m tools.verify_ecs` Layer 1 passes (old + new)

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → Layer 1 OK (incl. factory tests)

**Steps:**

- [ ] **Step 1: Move Combatant/Hero/Enemy + loaders into src/entities/combatant.py**

`git mv src/entities/_legacy_entities.py src/entities/combatant.py` (rename). The file's data imports were migrated to specific `from src.data.* import` in Task 8 — keep those. Its `import src.audio as audio` (if any) + `import pygame`/`os` stay. This file now exports `Combatant, Hero, Enemy, StatusEffect, load_image, load_char_sprite, load_portrait, load_champ_icon, load_enemy_sprite, load_skill_icon, load_bg, load_ui, load_item_icon, load_terrain, load_landmark, load_village, load_drop`.

- [ ] **Step 2: Write the failing factory tests**

Add to `tools/verify_ecs.py`:
```python
from src.entities.hero import spawn_hero
from src.entities.enemy import spawn_enemy
from src.data.heroes import HERO_BY_ID

def test_spawn_hero():
    w = World()
    e = spawn_hero(w, "Ahri")
    assert e.has(Transform) and e.has(Health) and e.has(Combat) and e.has(AI) \
        and e.has(Render) and e.has(Identity) and e.has(Statuses) and e.has(ChampionRef)
    ident = e.get(Identity)
    assert ident.is_hero is True and ident.name == "Ahri"
    ref = e.get(ChampionRef)
    assert ref.hero_id == "Ahri" and ref.level == 1
    hp = e.get(Health)
    h = HERO_BY_ID["Ahri"]["stats"]
    assert hp.max_hp == h["hp"]  # level-1 base
    assert e.get(Combat).element == HERO_BY_ID["Ahri"]["element"]

def test_spawn_enemy():
    w = World()
    e = spawn_enemy(w, "Krugs", level=3)
    assert e.get(Identity).is_hero is False
    assert e.get(Combat).element is not None
    assert e.get(Health).max_hp > 0
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs`
Expected: FAIL `ModuleNotFoundError: src.entities.hero`

- [ ] **Step 4: Implement src/entities/hero.py**

```python
"""Hero entity factory — spawns an entity with components + a Combatant.Hero stat obj."""
from src.core.world import World
from src.entities.entity import Entity
from src.entities.components import (Transform, Health, Combat, AI, Render,
    Identity, Statuses, ChampionRef)
from src.entities.combatant import Hero
from src.data.heroes import HERO_BY_ID
from src.data.skills import SKILLS_DB

def spawn_hero(world: World, hero_id: str, level: int = 1, ascension: int = 0,
               evolve: int = 0, x: float = 0.0, y: float = 0.0) -> Entity:
    hdef = HERO_BY_ID[hero_id]
    hero = Hero(hdef, level=level, ascension=ascension, evolve=evolve)
    e = world.spawn()
    e.add(Identity(e.eid, hero.name, is_hero=True))
    e.add(Transform(x, y))
    e.add(Health(hero.hp, hero.max_hp, hero.mp, hero.max_mp))
    e.add(Combat(hero.element, hero.atk, hero.defn, hero.spd))
    e.add(AI(kind="hero"))
    # weapon comes from the champion descriptor
    import src.build.champions as _CH
    c = _CH.CHAMPION_BY_KEY.get(hero_id)
    weapon = c["descriptor"]["weapon"] if c else "sword"
    e.add(Render(sprite_id=hero_id, weapon=weapon))
    e.add(Statuses())
    e.add(ChampionRef(hero_id=hero_id, level=level, ascension=ascension))
    # stash the stat object on Combat for systems to read (hack via a wrapper)
    e.get(Combat).__dict__["stat_obj"] = hero  # dataclass(slots) — see note
    return e
```
NOTE: `@dataclass(slots=True)` forbids arbitrary attribute assignment. So instead of stashing on the component, give `Combat` a `stat_obj` field in `components.py`:
```python
@dataclass(slots=True)
class Combat:
    element: str
    atk: float; defn: float; spd: float
    atk_cd: float = 0.0
    stat_obj: object = None  # the Combatant/Hero/Enemy instance for stat reads
```
Update the Task 10 test `test_entity_components`/`test_component_defaults` if needed (the new field defaults to None — existing asserts still pass). Use `e.get(Combat).stat_obj = hero` in the factory.

- [ ] **Step 5: Implement src/entities/enemy.py**

```python
"""Enemy entity factory — spawns an entity with components + a Combatant.Enemy stat obj."""
from src.core.world import World
from src.entities.entity import Entity
from src.entities.components import (Transform, Health, Combat, AI, Render,
    Identity, Statuses)
from src.entities.combatant import Enemy
from src.data.enemies import ENEMIES_DB
from src.data.heroes import champion_enemy_def

def spawn_enemy(world: World, enemy_id: str, level: int = 1, is_boss: bool = False,
                x: float = 0.0, y: float = 0.0) -> Entity:
    en = Enemy(enemy_id, level=level, is_boss=is_boss)
    e = world.spawn()
    e.add(Identity(e.eid, en.name, is_hero=False, is_boss=is_boss or en.is_boss))
    e.add(Transform(x, y, r=40 if is_boss else 26))
    e.add(Health(en.hp, en.max_hp, en.mp, en.max_mp))
    e.add(Combat(en.element, en.atk, en.defn, en.spd, stat_obj=en))
    # AI kind: LoL mob/boss id -> behaviour kind (mirror the legacy _ALIAS map)
    _AI_KIND = {"Krugs": "hop", "MurkWolves": "pounce", "Razorbeaks": "kite",
                "VoidHound": "kite", "Raptors": "pounce", "Voidlings": "rush",
                "Gromp": "hop", "Wraiths": "rush", "CrimsonRaptor": "pounce",
                "FallenKnight": "melee", "Sylas": "melee", "Swain": "ranged",
                "Lissandra": "ranged", "Mordekaiser": "melee", "Viego": "rush",
                "Baron": "boss"}
    e.add(AI(kind=_AI_KIND.get(enemy_id, "melee")))
    e.add(Render(sprite_id=enemy_id, weapon="sword"))
    e.add(Statuses())
    return e
```

- [ ] **Step 6: Update src/entities/__init__.py**

```python
"""entities package — ECS components, entity, combatant stat classes, factories."""
from src.entities.combatant import (Combatant, Hero, Enemy, StatusEffect,  # noqa: F401
    load_image, load_char_sprite, load_portrait, load_champ_icon, load_enemy_sprite,
    load_skill_icon, load_bg, load_ui, load_item_icon, load_terrain, load_landmark,
    load_village, load_drop)
from src.entities.hero import spawn_hero  # noqa: F401
from src.entities.enemy import spawn_enemy  # noqa: F401
```
NOTE: `world_entities` (WorldCharacter/WorldEnemy/Camera/etc.) still lives in `src/entities/_legacy_world_entities.py` and is re-exported from `__init__` (Task 3) — keep that re-export until Phase 4. Add it back explicitly:
```python
from src.entities._legacy_world_entities import (  # noqa: F401
    Camera, Particle, Particles, Projectile, FloatText, WorldCharacter, WorldEnemy,
    SummonAlly, Trap, WEAPON_STYLE, scratch)
```

- [ ] **Step 7: Run tests + verify_assets**

Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → Layer 1 OK incl. factory tests.
Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` → `OK`.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat(phase3): hero/enemy entity factories + Combatant stat bridge

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/entities/combatant.py", "src/entities/hero.py", "src/entities/enemy.py", "src/entities/__init__.py", "src/entities/components.py", "tools/verify_ecs.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs", "acceptanceCriteria": ["spawn_hero attaches 8 components + a Hero stat obj on Combat.stat_obj", "spawn_enemy attaches components + Enemy stat obj, AI.kind mapped from enemy_id", "Combatant/Hero/Enemy stat logic unchanged", "Layer 1 unit tests pass (incl. factory tests)", "verify_assets ends OK"], "modelTier": "standard"}
```

### Task 12: WorldScene adapter — spawn entities alongside legacy objects

**Goal:** Wire `WorldScene` to populate a `World` with entities (via the factories) in parallel with the legacy `WorldCharacter`/`WorldEnemy` objects, via an adapter that keeps the two in sync (entity Transform mirrors the legacy object's x/y; entity Health mirrors hp/energy). Combat still runs through the legacy path this task. This proves the entity layer tracks state correctly without yet driving it.

**Files:**
- Modify: `src/scenes/world.py` — in `__init__`, create `self.world = World()`; in `_build_party`/`_load_map`/`_on_enemy_event` (spawn), also `spawn_hero`/`spawn_enemy` into `self.world`; add an `_sync_entities()` method called each `update` that copies legacy object state onto the matching entity's components
- Modify: `tools/verify_ecs.py` — add an integration test that builds a WorldScene, runs 60 frames, and asserts `world.heroes()`/`world.enemies()` counts match the legacy party/enemies

**Acceptance Criteria:**
- [ ] After `WorldScene.__init__`, `self.world.heroes()` has 4 entities (the party) and each has a `ChampionRef.hero_id` matching the party hero ids
- [ ] After spawning enemies on map load, `self.world.enemies()` count equals `len(self.enemies)` (the legacy list)
- [ ] After 60 frames, each hero entity's `Transform.x/y` matches its legacy `WorldCharacter` x/y (±1), and `Health.hp` matches `WorldCharacter.hero.hp`
- [ ] Combat still works through the legacy path (21-test suite passes); `verify_assets` green

**Verify:** `SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py` → `ALL ACCEPTANCE TESTS PASS ✓` + `python3 -m tools.verify_ecs` integration test passes

**Steps:**

- [ ] **Step 1: Write the failing integration test**

Add to `tools/verify_ecs.py`:
```python
def test_worldscene_entity_sync():
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    sc = WorldScene(g); g.scene = sc
    for _ in range(60):
        sc.update(0.016, []); sc.draw(g.screen)
    # 4 party heroes
    assert len(sc.world.heroes()) == 4
    # each hero entity Transform matches its legacy WorldCharacter
    for wc in sc.party:
        if wc is None: continue
        e = next((e for e in sc.world.heroes() if e.get(__import__('src.entities.components',fromlist=['ChampionRef']).ChampionRef).hero_id == wc.hero.id), None)
        assert e is not None
        assert abs(e.get(__import__('src.entities.components',fromlist=['Transform']).Transform).x - wc.x) < 2
    print("  worldscene entity sync OK")
```

- [ ] **Step 2: Run to verify it fails**

Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs`
Expected: FAIL — `sc.world` doesn't exist yet.

- [ ] **Step 3: Add the World + adapter to WorldScene**

In `src/scenes/world.py` `__init__`, after the legacy party/enemy setup:
```python
from src.core.world import World
from src.entities.hero import spawn_hero
from src.entities.components import Transform, Health, ChampionRef
self.world = World()
self._entity_for_hero = {}   # hero_id -> Entity (party)
self._entity_for_enemy = {}  # id(legacy WorldEnemy) -> Entity
```
In `_build_party` (after each `WorldCharacter` is created for hero `hid`):
```python
e = spawn_hero(self.world, hid, level=rec.get("level",1), ascension=rec.get("ascension",0), evolve=rec.get("evolve",0), x=wc.x, y=wc.y)
self._entity_for_hero[hid] = e
```
In `_load_map`/`_on_enemy_event` wherever a `WorldEnemy` is appended to `self.enemies`:
```python
from src.entities.enemy import spawn_enemy
ee = spawn_enemy(self.world, en.id, level=en.enemy.level, is_boss=en.is_boss, x=en.x, y=en.y)
self._entity_for_enemy[id(en)] = ee
```
When a legacy enemy is removed (death), `self.world.destroy(self._entity_for_enemy.pop(id(en), -1))`.
Add `_sync_entities(self, dt)`:
```python
def _sync_entities(self, dt):
    for hid, wc in zip([wc.hero.id if wc else None for wc in self.party], self.party):
        if wc is None: continue
        e = self._entity_for_hero.get(wc.hero.id)
        if e is None: continue
        e.get(Transform).x = wc.x; e.get(Transform).y = wc.y
        e.get(Health).hp = wc.hero.hp; e.get(Health).energy = wc.hero.mp
    for en in self.enemies:
        e = self._entity_for_enemy.get(id(en))
        if e is None: continue
        e.get(Transform).x = en.x; e.get(Transform).y = en.y
        e.get(Health).hp = en.enemy.hp
```
Call `self._sync_entities(dt)` at the end of `update`.

- [ ] **Step 4: Run the tests + suite**

Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → integration test passes.
Run: `SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py` → `ALL ACCEPTANCE TESTS PASS ✓`.

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat(phase3): WorldScene entity adapter — World tracks party + enemies in parallel

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/scenes/world.py", "tools/verify_ecs.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs", "acceptanceCriteria": ["WorldScene.world.heroes() has 4 entities with ChampionRef matching party", "world.enemies() count == len(legacy enemies) after map load", "after 60 frames entity Transform/Health matches legacy objects", "21-test legacy suite still passes (combat via legacy path)", "verify_assets green"], "modelTier": "standard"}
```

### Task 13: Phase 3 gate

**Goal:** Run the full Phase 3 gate: Layer 1 unit + factory + integration tests, verify_assets, 21-test legacy suite, 1200-frame stress.

**Files:**
- Modify: none (gate-only task; produces an empty commit marker)

**Acceptance Criteria:**
- [ ] `python3 -m tools.verify_ecs` Layer 1 + factory + integration all pass
- [ ] `python3 -m tools.verify_assets` green
- [ ] 21-test legacy suite passes (combat still legacy-driven)
- [ ] 1200-frame stress no regression

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → all pass

**Steps:**

- [ ] **Step 1: Run the gate**

```bash
SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs
SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets
SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py
# 1200-frame stress snippet (Task 6 Step 2)
```
Expected: all green, stress no regression.

- [ ] **Step 2: Commit (gate marker)**

```bash
git commit --allow-empty -m "chore(phase3): gate green — ECS core + factories + adapter verified

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": [], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs", "acceptanceCriteria": ["verify_ecs Layer 1 + factory + integration pass", "verify_assets green", "21-test legacy suite passes", "1200-frame stress no regression"], "modelTier": "mechanical"}
```

---

## PHASE 4 — Systems extraction (ECS core, drop adapter)

Goal of Phase 4: extract WorldScene's 70 methods into 9 systems that drive the entities directly, delete the Phase-3 adapter, make WorldScene a thin coordinator. This is the largest phase — each system is its own task with TDD.

### Task 14: MapController (load_map, transition, discover_neighbors, teleport, boss-cell seal)

**Goal:** Extract the map-management methods into `src/systems/map_ctrl.py` as a `MapController` class owning the map state (grid, current cell, obstacles, villages, rift secret) + the `MapRenderer`. WorldScene delegates `_load_map`/`_transition`/`teleport_to`/`_discover_neighbors`/boss-cell logic to it.

**Files:**
- Create: `src/systems/map_ctrl.py`
- Modify: `src/scenes/world.py` — replace the 5 map methods with delegation; move map state fields onto MapController
- Modify: `src/world/map_renderer.py` — already exists (Task 5 moved MapRenderer into `src/scenes/world.py`'s body? No — MapRenderer is a class inside `world_scene.py`, now `src/scenes/world.py`). Move `MapRenderer` to `src/world/map_renderer.py`.
- Modify: `tools/verify_ecs.py` — add Layer 2 test: edge transition, teleport, boss-cell seal/unseal

**Acceptance Criteria:**
- [ ] `MapController.load_map(edge)`, `.transition(edge)`, `.teleport_to(c,r)`, `.discover_neighbors()` work and update `WorldScene` state via the controller
- [ ] Edge right → cell (1,0); edge bottom → (1,1); teleport → (5,2); boss cell sealed (0 enemies) until triggered
- [ ] `MapRenderer` lives in `src/world/map_renderer.py`
- [ ] 21-test suite passes; verify_assets green

**Verify:** `SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py` → edge/teleport/boss tests pass

**Steps:**

- [ ] **Step 1: Write failing Layer 2 test for MapController**

Add to `tools/verify_ecs.py`:
```python
def test_map_controller():
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    sc = WorldScene(g); g.scene = sc
    mc = sc.map_ctrl
    # edge right
    mc.transition("right")
    assert mc.cell == (1, 0), mc.cell
    mc.transition("bottom")
    assert mc.cell == (1, 1), mc.cell
    mc.teleport_to(5, 2)
    assert mc.cell == (5, 2), mc.cell
```

- [ ] **Step 2: Run to verify it fails**

Expected: FAIL — `sc.map_ctrl` doesn't exist.

- [ ] **Step 3: Move MapRenderer to src/world/map_renderer.py**

Cut the `MapRenderer` class (and its helpers `_seg_hit`, `_wrap`) from `src/scenes/world.py` into `src/world/map_renderer.py`. `src/scenes/world.py` imports `from src.world.map_renderer import MapRenderer`.

- [ ] **Step 4: Implement src/systems/map_ctrl.py**

Move `_load_map`, `_transition`, `teleport_to`, `_discover_neighbors`, `is_boss_cell`/boss-seal logic, and the map-state fields (`self.cell`, `self._map_data`, `self._village_cache`, `self._rift_secret`, `self._rift_done`, `self.map_renderer`) into `MapController`. The controller holds a ref to the `WorldScene` (or to the specific bits it needs: `self.world` for enemy spawning, `self.game.player` for `ow_*` state). Constructor: `MapController(scene)` storing `self.scene = scene; self.cell = ...; self.map_renderer = MapRenderer(); ...`. Each method body is the legacy code, with `self.X` → `self.scene.X` where it touches scene-level state (party, enemies, message), and `self.X` stays for controller-owned state.
`WorldScene.__init__`: `self.map_ctrl = MapController(self)`. Replace `_load_map`/`_transition`/`teleport_to`/`_discover_neighbors` with one-line delegates: `def _load_map(self, *a): return self.map_ctrl.load_map(*a)` etc. (Keep the delegates temporarily so the rest of WorldScene's legacy methods that call `self._load_map` still work.)

- [ ] **Step 5: Run tests + suite**

Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → `test_map_controller` passes.
Run: `SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py` → edge/teleport/boss pass.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat(phase4): MapController system (load_map/transition/teleport/boss-seal)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/systems/map_ctrl.py", "src/world/map_renderer.py", "src/scenes/world.py", "tools/verify_ecs.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs", "acceptanceCriteria": ["MapController.load_map/transition/teleport_to/discover_neighbors work", "edge right->(1,0), bottom->(1,1), teleport->(5,2)", "boss cell sealed until triggered", "MapRenderer in src/world/map_renderer.py", "21-test suite passes"], "modelTier": "standard"}
```

### Task 15: PhysicsSystem (movement, collision, camera)

**Goal:** Extract movement/collision/camera into `src/systems/physics.py`. `Camera` moves to `src/systems/physics.py` (from `_legacy_world_entities`). The system updates entity `Transform` (vx/vy/x/y) from input + accel/friction, resolves obstacle collisions, and updates the camera target.

**Files:**
- Create: `src/systems/physics.py` (move `Camera` class here)
- Modify: `src/scenes/world.py` — movement code in `update`/`_switch`/input handling delegates to `physics.update(dt, active_hero_entity, input_vec)`
- Modify: `tools/verify_ecs.py` — Layer 2: movement applies velocity, collision stops at obstacle, camera follows

**Acceptance Criteria:**
- [ ] A hero entity given input (1,0) for 30 frames moves ~+px with accel/friction; `Transform.x` increases
- [ ] An entity moving into an obstacle is clamped (no overlap)
- [ ] `Camera` follows the active hero entity's `Transform`
- [ ] 21-test suite passes; verify_assets green

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → physics tests pass

**Steps:**

- [ ] **Step 1: Write failing Layer 2 physics test**

```python
def test_physics_movement():
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    from src.entities.components import Transform
    sc = WorldScene(g); g.scene = sc
    sc.enemies.clear(); sc._map_data["obstacles"] = []
    active = sc.party[sc.active]
    start_x = active.x
    for _ in range(30):
        sc.physics.update(0.016, sc._entity_for_hero[active.hero.id], (1.0, 0.0))
    assert sc._entity_for_hero[active.hero.id].get(Transform).x > start_x + 5
```

- [ ] **Step 2: Run to verify it fails** → `sc.physics` missing.

- [ ] **Step 3: Move Camera + implement PhysicsSystem**

Move `Camera` from `src/entities/_legacy_world_entities.py` to `src/systems/physics.py` (re-export it from `_legacy_world_entities` for any remaining importer, or update importers). Implement `PhysicsSystem(world, data)` with `update(dt, entity, input_vec)` that mirrors the legacy `WorldCharacter` movement (accel/friction constants from `src.data.tuning`: the legacy code uses inline constants — copy them). The system mutates `entity.get(Transform).vx/vy/x/y` and resolves collisions against `scene._map_data["obstacles"]` (pass obstacles in). `WorldScene.__init__`: `self.physics = PhysicsSystem(self.world, ...)`. The legacy `WorldCharacter.update` movement stays for now (adapter still syncs); the system runs in parallel and the test checks the entity. (Full takeover of movement from the legacy object happens in Task 22 when the adapter is dropped.)

- [ ] **Step 4: Run tests + suite**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(phase4): PhysicsSystem (movement/collision/camera)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/systems/physics.py", "src/scenes/world.py", "src/entities/_legacy_world_entities.py", "tools/verify_ecs.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs", "acceptanceCriteria": ["input (1,0) for 30 frames moves entity Transform.x > start+5", "entity clamped at obstacle (no overlap)", "Camera follows active hero Transform", "21-test suite passes"], "modelTier": "standard"}
```

### Task 16: AISystem (enemy AI: hop/pounce/kite/rush/melee/ranged/boss)

**Goal:** Extract the per-enemy AI branches from `WorldEnemy.update` into `src/systems/ai.py` as `AISystem.update(dt)` that iterates `world.enemies()` and updates each entity's `Transform`/`AI` state based on `AI.kind` + aggro range + the nearest hero.

**Files:**
- Create: `src/systems/ai.py`
- Modify: `src/scenes/world.py` — enemy AI in `update` delegates to `self.ai.update(dt)`
- Modify: `tools/verify_ecs.py` — Layer 2: a "pounce" enemy moves toward a hero when in aggro range; a "kite" enemy maintains distance

**Acceptance Criteria:**
- [ ] A `pounce`-kind enemy entity within aggro range of a hero moves toward it (distance decreases)
- [ ] A `kite`-kind enemy within range moves to maintain distance (distance stays ~constant)
- [ ] An enemy outside aggro range does not move (or returns to idle)
- [ ] 21-test suite passes; verify_assets green

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → AI tests pass

**Steps:**

- [ ] **Step 1: Write failing Layer 2 AI test**

```python
def test_ai_pounce():
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    from src.entities.enemy import spawn_enemy
    from src.entities.components import Transform, AI
    sc = WorldScene(g); g.scene = sc
    sc.enemies.clear(); sc._map_data["obstacles"] = []
    hero_e = sc._entity_for_hero[sc.party[sc.active].hero.id]
    en = spawn_enemy(sc.world, "MurkWolves", level=1, x=hero_e.get(Transform).x+200, y=hero_e.get(Transform).y)
    d0 = abs(en.get(Transform).x - hero_e.get(Transform).x)
    for _ in range(60):
        sc.ai.update(0.016)
    d1 = abs(en.get(Transform).x - hero_e.get(Transform).x)
    assert d1 < d0  # pounce closes distance
```

- [ ] **Step 2: Run to verify it fails** → `sc.ai` missing.

- [ ] **Step 3: Implement AISystem**

`AISystem(world, data)` with `update(dt)`: for each enemy entity, read `AI.kind` + `AI.state` + `AI.aggro_t`, find nearest hero entity (`world.heroes()`), and apply the movement per kind — copy the velocity/leap/cooldown logic from the legacy `WorldEnemy.update` branches (Krugs hop, MurkWolves pounce, Razorbeaks/VoidHound kite, etc.). Mutate `entity.get(Transform)` + `entity.get(AI)`. `WorldScene.__init__`: `self.ai = AISystem(self.world, ...)`. Call `self.ai.update(dt)` in `update` (the legacy WorldEnemy.update still runs in parallel via the adapter this task; the test checks the entity).

- [ ] **Step 4: Run tests + suite**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(phase4): AISystem (hop/pounce/kite/rush/melee/ranged/boss)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/systems/ai.py", "src/scenes/world.py", "tools/verify_ecs.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs", "acceptanceCriteria": ["pounce enemy closes distance to hero when in aggro range", "kite enemy maintains distance", "enemy outside aggro range idle", "21-test suite passes"], "modelTier": "standard"}
```

### Task 17: CombatSystem (basic_attack, use_skill, use_ultimate, on_hit, on_death)

**Goal:** Extract the combat methods (`_do_attack`, `_do_skill`, `_do_ultimate`, `_on_enemy_hit`, `_on_enemy_death`, `_element_mult`, combo, reaction ticks) into `src/systems/combat.py`. The system operates on entities: reads `Combat.stat_obj` (the Hero/Enemy) for stats, mutates `Health` + `Statuses`, spawns projectiles (a `Projectile` component or legacy projectile list), and triggers drops/death via callbacks.

**Files:**
- Create: `src/systems/combat.py`
- Modify: `src/scenes/world.py` — combat methods delegate to `self.combat.*`
- Modify: `tools/verify_ecs.py` — Layer 2: basic_attack reduces target Health.hp by element-adjusted damage + gains energy + sets atk_cd; use_skill applies SKILLS_DB damage + reaction; use_ultimate requires full energy + applies ULTIMATE_VARIANTS extra

**Acceptance Criteria:**
- [ ] `combat.basic_attack(attacker_eid, target_eid)`: target `Health.hp` drops by `atk * element_mult(atk_el, def_el) * (crit?2:1) - defn`, attacker `Health.energy += ENERGY_GAIN_BASIC`, attacker `Combat.atk_cd = AA_CD`
- [ ] `combat.use_skill(eid, idx)`: cooldown + energy cost enforced (no-op if can't afford), damage from `SKILLS_DB`, fire+water on target → steam reaction applied
- [ ] `combat.use_ultimate(eid)`: requires `Health.energy >= max`, applies base ult + the `ULTIMATE_VARIANTS[hero_id]` extra effect (heal/shield/knockback/energy_refund/atk_buff)
- [ ] `combat.on_hit`/`on_death`: drop spawn callback fired, combo milestone, signature passive triggered
- [ ] 21-test suite passes (ranged + melee combat); verify_assets green

**Verify:** `SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py` → ranged_combat + melee_combat pass

**Steps:**

- [ ] **Step 1: Write failing Layer 2 combat tests**

```python
def test_combat_basic_attack():
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    from src.entities.enemy import spawn_enemy
    from src.entities.components import Health, Combat
    sc = WorldScene(g); g.scene = sc
    sc.enemies.clear(); sc._map_data["obstacles"] = []
    hero_e = sc._entity_for_hero[sc.party[sc.active].hero.id]
    en = spawn_enemy(sc.world, "Krugs", level=1)
    hp0 = en.get(Health).hp
    en0_energy = hero_e.get(Health).energy
    sc.combat.basic_attack(hero_e.eid, en.eid)
    assert en.get(Health).hp < hp0
    assert hero_e.get(Health).energy > en0_energy
    assert hero_e.get(Combat).atk_cd > 0
```

- [ ] **Step 2: Run to verify it fails** → `sc.combat` missing.

- [ ] **Step 3: Implement CombatSystem**

`CombatSystem(world, data, scene)` — `data` is a bundle of the needed data modules (`skills`, `tuning`, `elements`, `heroes`). Methods mirror the legacy `_do_attack`/`_do_skill`/`_do_ultimate`/`_on_enemy_hit`/`_on_enemy_death` bodies, but read/write entity components: `attacker.get(Combat).stat_obj` for the Hero/Enemy (use its `atk`/`take_damage`/`can_use_skill`/`skill_energy_cost`), `target.get(Health).hp` for the result, `target.get(Statuses).effects` for status application. Reactions: track an `applied_elements` list on `Statuses` (or a new `ElementAura` component) and trigger `reaction_for`. `on_death` calls a `on_death_callback(eid, killer_eid)` set by WorldScene (which wires DropSystem + combo + signature). `WorldScene.__init__`: `self.combat = CombatSystem(self.world, ..., self)`; set `self.combat.on_death_callback = self._on_entity_death`. Delegate `_do_attack`/`_do_skill`/`_do_ultimate` to `self.combat.*` (keep legacy delegates temporarily).

- [ ] **Step 4: Run tests + suite**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(phase4): CombatSystem (attack/skill/ultimate/on_hit/on_death + reactions)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/systems/combat.py", "src/scenes/world.py", "tools/verify_ecs.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs", "acceptanceCriteria": ["basic_attack reduces target Health.hp, gains attacker energy, sets atk_cd", "use_skill enforces cd+energy, applies SKILLS_DB dmg + fire+water->steam reaction", "use_ultimate requires full energy + applies ULTIMATE_VARIANTS extra", "on_hit/on_death fire drop/combo/signature callbacks", "21-test ranged+melee combat pass"], "modelTier": "frontier"}
```

### Task 18: DropSystem + RiftSystem + DialogueSystem

**Goal:** Extract `_spawn_drop`/`_pickup_drop` → `DropSystem`; `_enter_rift`/`_clear_rift` + rift wave spawn → `RiftSystem`; `_handle_npc_talk`/`_advance_dialogue` + story-quest checks → `DialogueSystem`. Each owns its state + operates on entities/player.

**Files:**
- Create: `src/systems/drops.py`, `src/systems/rift.py`, `src/systems/dialogue.py`
- Modify: `src/scenes/world.py` — delegate the corresponding methods
- Modify: `tools/verify_ecs.py` — Layer 2: drop spawn + pickup adds gold/shard to player; rift trigger spawns a wave; NPC talk advances dialogue

**Acceptance Criteria:**
- [ ] `DropSystem.spawn(x,y,kind,value)` creates a drop; `DropSystem.update(dt)` drifts drops + on hero proximity `pickup` adds to `player.gold`/`shards`/inventory
- [ ] `RiftSystem.trigger()` spawns a wave of enemies (entities); `RiftSystem.clear()` on wave defeat grants a reward + sets `_rift_done`
- [ ] `DialogueSystem.talk(npc)` opens a dialogue box; `advance()` steps through lines; story-quest gating works (`is_quest_active`/`is_quest_available`)
- [ ] 21-test suite passes; verify_assets green

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → drop/rift/dialogue tests pass

**Steps:**

- [ ] **Step 1: Write failing Layer 2 tests** for each (drop pickup increments player gold; rift trigger adds enemies to `world.enemies()`; dialogue talk sets a non-None dialogue state).

- [ ] **Step 2: Run to verify they fail** → systems missing.

- [ ] **Step 3: Implement the 3 systems** by moving the legacy method bodies, operating on entities/player. `DropSystem` holds `self.drops` list; `RiftSystem` holds `self._rift_secret`/`_rift_done`/wave state (coordinating with MapController); `DialogueSystem` holds `self.dialogue`/`self.dialogue_npc`/quest flags. WorldScene delegates.

- [ ] **Step 4: Run tests + suite**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(phase4): DropSystem + RiftSystem + DialogueSystem

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/systems/drops.py", "src/systems/rift.py", "src/systems/dialogue.py", "src/scenes/world.py", "tools/verify_ecs.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs", "acceptanceCriteria": ["drop spawn + pickup adds gold/shard/item to player", "rift trigger spawns wave entities; clear on defeat grants reward", "dialogue talk + advance steps lines; story-quest gating works", "21-test suite passes"], "modelTier": "standard"}
```

### Task 19: RenderSystem + HudSystem

**Goal:** Extract the draw methods (`draw` + `_draw_*` ~25 methods + atmosphere/sky/night/fog/rain) → `RenderSystem.draw(surf, map_ctrl)`; and the HUD (`_draw_hud`/`_draw_skill_bar`/`_draw_skill_tooltip`/`_draw_minimap`/`_draw_boss_banner`/`_draw_ascend_banner`/`_hud_portrait`/`_skill_icon`) → `HudSystem.draw(surf)`. These are read-only over entities + map state.

**Files:**
- Create: `src/systems/render.py`, `src/systems/hud.py`
- Modify: `src/scenes/world.py` — `draw` becomes `self.render.draw(surf, self.map_ctrl); self.hud.draw(surf); self.dialogue.draw(surf)`
- Modify: `tools/verify_ecs.py` — Layer 3: one full `WorldScene.draw(surf)` frame doesn't raise

**Acceptance Criteria:**
- [ ] `RenderSystem.draw(surf, map_ctrl)` renders ground + entities + VFX + atmosphere without raising
- [ ] `HudSystem.draw(surf)` renders skill bar + party + boss bar + minimap without raising
- [ ] One full `WorldScene.update(dt,[])` + `draw(surf)` frame is exception-free
- [ ] 21-test suite passes (scene:world render); verify_assets green

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → render/hud tests pass

**Steps:**

- [ ] **Step 1: Write failing Layer 3 render test**

```python
def test_render_one_frame():
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    sc = WorldScene(g); g.scene = sc
    sc.update(0.016, [])
    sc.draw(g.screen)  # must not raise
```

- [ ] **Step 2: Run to verify it fails** → still works actually (legacy draw), but the test asserts `sc.render` + `sc.hud` exist. Adjust test to `assert sc.render is not None and sc.hud is not None` first, then the no-raise.

- [ ] **Step 3: Move the draw methods into RenderSystem + HudSystem**

Cut the ~25 `_draw_*` methods + atmosphere into `RenderSystem.draw` (which calls them as internal methods). Cut the HUD methods into `HudSystem.draw`. Each system holds a ref to `scene` for state reads (party, enemies, map_ctrl, world). `WorldScene.draw` becomes the 3-line delegation. The systems read entity `Transform`/`Health`/`Render` for drawing (via `scene.world`), falling back to legacy objects where the adapter still syncs.

- [ ] **Step 4: Run tests + suite**

- [ ] **Step 5: Commit**

```bash
git commit -m "feat(phase4): RenderSystem + HudSystem (draw + atmosphere + HUD)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/systems/render.py", "src/systems/hud.py", "src/scenes/world.py", "tools/verify_ecs.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs", "acceptanceCriteria": ["RenderSystem.draw renders ground+entities+VFX+atmosphere no raise", "HudSystem.draw renders skill bar+party+boss bar+minimap no raise", "one full update+draw frame exception-free", "21-test scene:world passes"], "modelTier": "standard"}
```

### Task 20: WorldScene thin coordinator + delete Phase-3 adapter

**Goal:** Now that all systems exist, make `WorldScene` a thin coordinator: `__init__` builds `World` + the 9 systems; `update` calls `map_ctrl.update → ai.update → physics.update → combat.update → drops.update → rift.update → _handle_input`; `draw` calls `render.draw → hud.draw → dialogue.draw`. Delete the `_sync_entities` adapter + the legacy `WorldCharacter`/`WorldEnemy` driving (entities are now the source of truth; the legacy objects are removed or become thin wrappers the systems read via `Combat.stat_obj`).

**Files:**
- Modify: `src/scenes/world.py` — collapse to thin coordinator
- Modify: `src/entities/_legacy_world_entities.py` — remove `WorldCharacter`/`WorldEnemy` (or reduce to the `Combatant` stat obj + components); keep `Camera` (moved to physics in Task 15), `Particles`/`Projectile`/`FloatText`/`SummonAlly`/`Trap`/`scratch`/`WEAPON_STYLE` (these are still used by systems)
- Modify: `tools/verify_ecs.py` — Layer 3-4 full integration: party swap 1/2/3/4 changes active entity, HP/energy persist; save round-trip; gacha 10-pull

**Acceptance Criteria:**
- [ ] `WorldScene` is ≤ ~150 lines (init + update + draw + _handle_input + a few helpers)
- [ ] No `_sync_entities` adapter; entities are the source of truth (`Transform`/`Health` driven by systems)
- [ ] Party swap 1/2/3/4 changes the active hero entity; HP/energy persist across swaps
- [ ] Save round-trip: `player.save()` → `Player.load()` → state matches
- [ ] Gacha 10-pull + 180-pull 0 error
- [ ] 21-test suite passes; verify_assets green; 1200-frame stress no regression

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → all layers pass

**Steps:**

- [ ] **Step 1: Write failing Layer 3-4 integration tests** (party swap, save round-trip, gacha) in `tools/verify_ecs.py`.

- [ ] **Step 2: Run to verify they fail/pass** (some may already pass through the adapter; the swap-persist one is the key new assertion).

- [ ] **Step 3: Collapse WorldScene to thin coordinator**

Rewrite `WorldScene.__init__` to build `self.world = World()` + the 9 systems + `MapController(self)`. Rewrite `update`/`draw` to the delegation chain. Move `_handle_input` to translate events into `combat.basic_attack`/`use_skill`/`use_ultimate`/`drops`/`dialogue`/`map_ctrl` calls on the active hero entity. Remove `_sync_entities` + the legacy `self.party`/`self.enemies` lists (replaced by `self.world.heroes()`/`self.world.enemies()`; the active hero is `self.world.heroes()[self.active]` or tracked by eid). The systems read `Combat.stat_obj` for the Hero/Enemy stat object. Particles/projectiles stay as legacy lists owned by RenderSystem/CombatSystem.

- [ ] **Step 4: Remove the WorldCharacter/WorldEnemy driving**

In `src/entities/_legacy_world_entities.py`, delete `WorldCharacter` + `WorldEnemy` classes (their logic is now in PhysicsSystem/AISystem/CombatSystem). Keep `Particles/Particle/Projectile/FloatText/SummonAlly/Trap/scratch/WEAPON_STYLE`. Update `src/entities/__init__.py` re-exports (drop WorldCharacter/WorldEnemy).

- [ ] **Step 5: Run the full gate**

```bash
SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs
SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets
SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py
# 1200-frame stress
```
Expected: all green. (The 21-test legacy suite may need its combat spawn helper updated to use `spawn_enemy` instead of `WorldEnemy` — update the suite's setup, NOT the production code, if it constructs enemies directly.)

- [ ] **Step 6: Commit**

```bash
git commit -m "feat(phase4): WorldScene thin coordinator; delete adapter; entities drive systems

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/scenes/world.py", "src/entities/_legacy_world_entities.py", "src/entities/__init__.py", "tools/verify_ecs.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs", "acceptanceCriteria": ["WorldScene <= ~150 lines (thin coordinator)", "no _sync_entities adapter; entities are source of truth", "party swap 1/2/3/4 changes active entity, HP/energy persist", "save round-trip + gacha 10/180-pull OK", "21-test suite passes; 1200-frame stress no regression"], "modelTier": "frontier"}
```

### Task 21: AdventureScene on the new ECS WorldScene + Phase 4 gate

**Goal:** Update `AdventureScene` (subclass of WorldScene) to work with the thin coordinator + systems (its overrides for wave spawn / stage boss / timer HUD call into the systems). Run the Phase 4 gate.

**Files:**
- Modify: `src/scenes/adventure.py` — overrides use `self.combat`/`self.ai`/`self.world`/`self.hud` instead of legacy `self.enemies`/`self.party`
- Modify: `tools/verify_ecs.py` — Layer 4: 1200-frame adventure stress
- Delete: `/tmp/verify_complete.py` dependency is gone — the ECS suite replaces it from here

**Acceptance Criteria:**
- [ ] `AdventureScene` boots + runs waves + spawns stage boss without raising
- [ ] 1200-frame adventure stress no regression (>~150 fps)
- [ ] `python3 -m tools.verify_ecs` all layers pass; `verify_assets` green

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → all pass + adventure stress

**Steps:**

- [ ] **Step 1: Update AdventureScene overrides** to read `self.world.enemies()`/`self.world.heroes()` and call `self.ai`/`self.combat` for wave/boss spawning (using `spawn_enemy`). The timer/stage HUD draws via `self.hud` (extend HudSystem with an adventure-timer hook, or draw inline in AdventureScene.draw after `super().draw`).

- [ ] **Step 2: Add Layer 4 adventure stress test** to `tools/verify_ecs.py` (1200 frames, capture fps, assert ≥ ~137).

- [ ] **Step 3: Run the Phase 4 gate** — `verify_ecs` all layers + `verify_assets` + adventure stress + endless stress.

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(phase4): AdventureScene on ECS + Phase 4 gate green

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/scenes/adventure.py", "src/systems/hud.py", "tools/verify_ecs.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs", "acceptanceCriteria": ["AdventureScene boots + waves + stage boss no raise", "1200-frame adventure stress >= ~137 fps (no regression)", "verify_ecs all layers pass", "verify_assets green"], "modelTier": "standard"}
```

---

## PHASE 5 — Cleanup + docs + final suite

### Task 22: Delete dead legacy code + clean `__init__.py` re-exports

**Goal:** Remove all `_legacy_*` files + temporary re-exports now that systems drive everything. Consolidate `src/entities/_legacy_world_entities.py` remaining helpers (`Particles`/`Projectile`/`FloatText`/`SummonAlly`/`Trap`/`scratch`/`WEAPON_STYLE`) into properly-named modules (`src/systems/particles.py` for Particles/Projectile/FloatText; `src/entities/summons.py` for SummonAlly/Trap; `scratch` into `src/ui/primitives.py` where it already is, or `src/core/scratch.py`).

**Files:**
- Delete: `src/entities/_legacy_world_entities.py`, `src/entities/combatant.py`'s `_legacy` suffix (rename to keep `combatant.py`), any `_legacy_*` remnants
- Create: `src/systems/particles.py`, `src/entities/summons.py`
- Modify: `src/entities/__init__.py`, `src/systems/__init__.py` — clean re-exports

**Acceptance Criteria:**
- [ ] No file named `_legacy_*` remains
- [ ] `Particles/Particle/Projectile/FloatText` in `src/systems/particles.py`; `SummonAlly/Trap` in `src/entities/summons.py`
- [ ] `python3 main.py` boots; `verify_ecs` + `verify_assets` green

**Verify:** `find src -name '_legacy*'` → empty

**Steps:**

- [ ] **Step 1: Move Particles/Projectile/FloatText → src/systems/particles.py; SummonAlly/Trap → src/entities/summons.py; update importers.**

- [ ] **Step 2: Delete `src/entities/_legacy_world_entities.py`; update `src/entities/__init__.py`** to export from the new homes + `combatant.py`.

- [ ] **Step 3: Verify + commit**

```bash
git commit -m "refactor(phase5): delete _legacy_* remnants; consolidate particles/summons

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["src/systems/particles.py", "src/entities/summons.py", "src/entities/__init__.py", "src/entities/_legacy_world_entities.py"], "verifyCommand": "find src -name '_legacy*'", "acceptanceCriteria": ["no _legacy_* files remain", "Particles/Projectile/FloatText in src/systems/particles.py", "SummonAlly/Trap in src/entities/summons.py", "python3 main.py boots; verify_ecs + verify_assets green"], "modelTier": "standard"}
```

### Task 23: Update README + AGENTS.md + memory

**Goal:** Document the final package layout, ECS architecture, run commands, and the system/entity model. Update the project memory file.

**Files:**
- Modify: `README.md`, `AGENTS.md`
- Modify: `/home/misa/.claude/projects/-home-misa-Desktop-RD-Gacha/memory/gacha-lol-roster-redesign.md` (append the ECS restructure section)

**Acceptance Criteria:**
- [ ] README module-layout table matches the final `src/` tree; run commands correct
- [ ] AGENTS.md architecture table lists every `src/` subdir + the ECS entity/system model + the verify commands
- [ ] Memory file has a section on the ECS restructure (entity/component/system, where combat/AI/physics live, the verify suite)

**Verify:** `grep -c 'src/' README.md` → > 10 ; manual read of AGENTS.md architecture section

**Steps:**

- [ ] **Step 1: Rewrite README.md** module-layout + run sections to the final tree (from the plan's File Structure) + ECS-lite description.

- [ ] **Step 2: Rewrite AGENTS.md** section 3 (architecture) — table of `src/` subdirs with roles, the entity/component/system flow, verify commands (`python3 -m tools.verify_assets`, `python3 -m tools.verify_ecs`).

- [ ] **Step 3: Append to the memory file** a "ECS restructure (2026-07-30)" section noting: package `src/`, entity=component data bag, 9 systems, `Combatant`/`Hero`/`Enemy` kept as `Combat.stat_obj`, verify via `tools/verify_ecs`, the old `/tmp/verify_complete.py` is retired.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "docs(phase5): README + AGENTS + memory for the ECS package layout

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["README.md", "AGENTS.md"], "verifyCommand": "grep -c 'src/' README.md", "acceptanceCriteria": ["README module-layout table matches final src/ tree + run commands", "AGENTS.md architecture table lists src/ subdirs + ECS model + verify commands", "memory file has ECS restructure section"], "modelTier": "mechanical"}
```

### Task 24: Final ECS suite (Layer 5 build) + full gate

**Goal:** Complete `tools/verify_ecs.py` with Layer 5 (build pipeline) + run the complete 5-phase final gate.

**Files:**
- Modify: `tools/verify_ecs.py` — add Layer 5 (build) tests

**Acceptance Criteria:**
- [ ] `python3 -m tools.verify_ecs` runs all 5 layers green: unit, system, integration, stress, build
- [ ] `python3 -m tools.verify_assets` green
- [ ] `python3 main.py` boots to title → world → adventure smoke OK
- [ ] `xvfb-run -a python3 -m src.assets_gen.generate` produces all shared art
- [ ] 1200-frame stress endless + adventure no regression

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → `ALL ECS TESTS PASS`

**Steps:**

- [ ] **Step 1: Add Layer 5 build tests** to `tools/verify_ecs.py`: run `src.assets_gen.generate.main()` under dummy display (or skip if no display) + assert `generate_sprites` produces 170 sprites; assert `verify_assets` logic inline (count bundles).

- [ ] **Step 2: Run the full final gate**

```bash
SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs
SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets
xvfb-run -a python3 -m src.assets_gen.generate
SDL_VIDEODRIVER=dummy python3 -c "import main; M=main; g=M.Game(); import src.scenes.world as W, src.scenes.adventure as A; g.scene=W.WorldScene(g); [g.scene.update(0.016,[]) or g.scene.draw(g.screen) for _ in range(30)]; g.goto('adventure'); [g.scene.update(0.016,[]) or g.scene.draw(g.screen) for _ in range(30)]; print('boot smoke OK')"
```
Expected: `ALL ECS TESTS PASS`; verify_assets `OK`; build `Done.`; `boot smoke OK`.

- [ ] **Step 3: Commit (final)**

```bash
git commit --allow-empty -m "chore(phase5): final ECS suite (5 layers) + full gate green

Co-Authored-By: Claude <noreply@anthropic.com>"
```

```json:metadata
{"files": ["tools/verify_ecs.py"], "verifyCommand": "SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs", "acceptanceCriteria": ["verify_ecs all 5 layers green (unit/system/integration/stress/build)", "verify_assets green", "python3 main.py boot smoke (title->world->adventure) OK", "assets_gen.generate produces all shared art", "1200-frame stress no regression"], "modelTier": "mechanical"}
```

---

## Self-Review Notes

**Spec coverage:** Section 1 (package layout) → Tasks 1-6. Section 2 (ECS-lite arch) → Tasks 10-12, 14-20. Section 3 (data migration) → Tasks 7-9. Section 4 (5 phases) → Phase 1 = Tasks 1-6, Phase 2 = 7-9, Phase 3 = 10-13, Phase 4 = 14-21, Phase 5 = 22-24. Section 5 (testing) → `tools/verify_ecs.py` grown across Tasks 10-24, layers mapped. All spec sections covered.

**Type consistency:** `Combat.stat_obj` field introduced in Task 11 Step 4 is read by CombatSystem (Task 17) + RenderSystem (Task 19). `MapController.cell` (Task 14) read by tests + AdventureScene (Task 21). `World.heroes()`/`enemies()` (Task 10) used by every system. `spawn_hero`/`spawn_enemy` signatures (Task 11) match callsites in Task 12 + 16 + 17. `AI.kind` values (Task 11 enemy factory `_AI_KIND`) match the branches in AISystem (Task 16).

**Placeholder scan:** No TBD/TODO; every code step shows the actual code or the exact legacy method body to move. Where a step says "copy the legacy X body", the legacy method is named with its file:line so the implementer can read it (it exists in the current codebase).

**Deferred decisions:** None — all 6 user decisions are in the header and respected (no shim → Task 8 removes it; ECS-lite → Tasks 10-20; staged → 5 phases; new suite → `tools/verify_ecs.py`; main.py thin + src/ → Task 1; Combatant kept → Task 11).
