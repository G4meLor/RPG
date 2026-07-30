# Aetheria OOP + ECS-lite Restructure — Design

> **Status:** Approved design (2026-07-30). Next step: writing-plans skill creates the implementation plan.
> **Scope:** Full refactor — package `src/` layout + data migration (no shim) + ECS-lite entity/system architecture. 5 staged phases, each verified before the next.

## Goal

Restructure the Aetheria codebase from 14 flat top-level files (~20k lines, god-classes: `world_scene.py` 5451 lines / 70 methods, `data.py` 2563 lines / 104 tables / 416 `D.*` call sites, `main.py` 2330 lines / 13 scenes) into a `src/` package with an ECS-lite architecture (entity = component data bag, system = stateless-ish processor). The game stays runnable as `python3 main.py` throughout; behavior is preserved verbatim.

## Architecture

**Package layout** (`main.py` thin entry at root + `src/` package):

```
main.py                      # thin entry: pygame init, Game(), loop (adds src/ to sys.path)
src/
  __init__.py
  core/
    __init__.py
    game.py                  # class Game (scene manager, from main.py)
    scene.py                 # class Scene (base)
    world.py                 # class World (entity container + query)
    registry.py              # data registry (skills/heroes/enemies lookup API)
    config.py                # WIDTH/HEIGHT/FPS/SEED constants
  ui/
    __init__.py              # re-export text/Button/draw_bar/...
    primitives.py            # font cache, text, Button, draw_bar/panel/stars, dim_overlay, scratch
    colors.py                # element_color/rarity_color, palettes
    widgets.py               # Toggle/Slider
  data/
    __init__.py              # Phase 1: shim re-export; Phase 2: removed (no shim)
    tuning.py  elements.py  skills.py  roles.py  heroes.py  passives.py
    evolution.py  constellation.py  ascension.py  enemies.py  gacha_data.py
    equipment.py  consumables.py  shop.py  progression.py  story.py  resonance.py
  world/
    __init__.py
    data.py                  # world_data.py (map grid, biome, gen_map)
    map_renderer.py          # MapRenderer (from world_scene.py)
    overlays.py              # TeleportOverlay/PauseHub/EvolveOverlay
  entities/
    __init__.py
    components.py            # Component dataclasses (Transform/Health/Combat/AI/Render/Identity/Statuses/ChampionRef)
    entity.py                # Entity (eid + component dict, __slots__)
    combatant.py             # Combatant/Hero/Enemy stat logic (kept as class, from entities.py)
    hero.py  enemy.py        # entity factories (build entity + attach components)
  systems/
    __init__.py
    combat.py                # CombatSystem (basic_attack/use_skill/use_ultimate/on_hit/on_death)
    physics.py               # PhysicsSystem (movement, collision, camera)
    ai.py                    # AISystem (enemy AI: hop/pounce/kite, aggro)
    render.py                # RenderSystem (draw entities, VFX, atmosphere)
    hud.py                   # HudSystem (skill bar, party, boss bar)
    dialogue.py              # DialogueSystem (NPC talk, advance)
    drops.py                 # DropSystem (spawn/pickup)
    rift.py                  # RiftSystem
    map_ctrl.py              # MapController (load_map, transition, discover_neighbors)
  scenes/
    __init__.py
    world.py                 # WorldScene (thin: owns World + systems, delegates)
    adventure.py             # AdventureScene(WorldScene)
    menu/
      __init__.py
      title.py roster.py hero_detail.py gacha_scene.py shop.py
      inventory.py settings.py stats.py codex.py
  fx/
    __init__.py              # draw_rift_portal + runtime VFX
  assets_gen/
    __init__.py
    generate.py              # generate_assets.py (build-only pipeline)
    descriptors.py           # draw_chibi_descriptor + archetypes + feature-adders + weapon drawers
    enemies_art.py  items_art.py  ui_art.py  terrain_art.py  skills_art.py
  build/
    __init__.py
    champions.py             # champions.py (baked data)
    build_champions.py       # build pipeline
  audio.py
  player.py
  gacha.py
tools/
  verify_assets.py
  verify_ecs.py              # new ECS acceptance suite
```

**Run commands:**
- Play: `python3 main.py` (root thin entry; adds `src/` to `sys.path`, imports `from src.core.game import Game`).
- Regenerate shared art: `python3 -m src.assets_gen.generate`.
- Rebuild roster: `python3 -m src.build.build_champions --all`.
- Verify: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` / `... -m tools.verify_ecs`.

**ECS-lite core:**

Entity = data bag (component dict, `__slots__`):
```python
# src/entities/components.py
@dataclass(slots=True)
class Transform: x: float; y: float; vx: float = 0; vy: float = 0; r: float = 26
@dataclass(slots=True)
class Health: hp: float; max_hp: float; energy: float; max_energy: float
@dataclass(slots=True)
class Combat: element: str; atk: float; defn: float; spd: float; atk_cd: float = 0
@dataclass(slots=True)
class AI: kind: str; state: str = "idle"; target: int = -1; aggro_t: float = 0
@dataclass(slots=True)
class Render: sprite_id: str; weapon: str; facing: int = 1; anim_t: float = 0
@dataclass(slots=True)
class Identity: eid: int; name: str; is_hero: bool; is_boss: bool = False
@dataclass(slots=True)
class Statuses: effects: list  # [StatusEffect]
@dataclass(slots=True)
class ChampionRef: hero_id: str; skin: int = 0; level: int = 1; ascension: int = 0
```

```python
# src/entities/entity.py
class Entity:
    __slots__ = ("eid", "components")
    def __init__(self, eid): self.eid = eid; self.components = {}
    def add(self, comp): self.components[type(comp)] = comp; return self
    def get(self, comp_cls): return self.components.get(comp_cls)
    def has(self, comp_cls): return comp_cls in self.components
```

```python
# src/core/world.py
class World:
    def __init__(self): self.entities = {}; self._next_eid = 0
    def spawn(self) -> Entity: ...
    def destroy(self, eid): ...
    def query(self, *comp_classes) -> iterator[Entity]:  # yield entities having all comps
    def heroes(self) -> list[Entity]: ...   # convenience: Identity.is_hero
    def enemies(self) -> list[Entity]: ...  # convenience: not is_hero
```

System = stateless-ish processor (receives `World` + data registry, mutates entity components):
```python
# src/systems/combat.py
class CombatSystem:
    def __init__(self, world, data): self.world = world; self.skills = data.skills
    def basic_attack(self, attacker_eid, target_eid=None): ...
    def use_skill(self, eid, idx, target=None): ...
    def use_ultimate(self, eid): ...
    def on_hit(self, target_eid, attacker_eid, dmg, is_crit): ...
    def on_death(self, eid, killer_eid): ...
```

WorldScene becomes a thin coordinator:
```python
# src/scenes/world.py
class WorldScene(Scene):
    def __init__(self, game):
        self.world = World()
        self.combat = CombatSystem(self.world, game.data)
        self.physics = PhysicsSystem(self.world, game.data)
        self.ai = AISystem(self.world, game.data)
        self.render = RenderSystem(self.world, game.data)
        self.hud = HudSystem(self.world, game.data)
        self.dialogue = DialogueSystem(...)
        self.drops = DropSystem(...)
        self.rift = RiftSystem(...)
        self.map_ctrl = MapController(...)
    def update(self, dt, events):
        self.map_ctrl.update(dt, events, self)
        self.ai.update(dt)
        self.physics.update(dt)
        self.combat.update(dt)        # cooldowns, projectiles, reaction ticks
        self.drops.update(dt)
        self.rift.update(dt)
        self._handle_input(events)    # input -> combat/drop/dialogue calls
    def draw(self, surf):
        self.render.draw(surf, self.map_ctrl)
        self.hud.draw(surf)
        self.dialogue.draw(surf)
```

**Stat logic preservation:** `Combatant`/`Hero`/`Enemy` (leveling, ascension, equipment, passive bonuses — from `entities.py`) are kept as classes in `src/entities/combatant.py`. An entity's `Combat`/`ChampionRef` component references the `Hero`/`Enemy` object for stat reads; systems call the object's methods for leveling/equip. This avoids rewriting stable stat logic while the realtime world behavior (movement, AI, combat VFX) moves to systems.

## Data migration (416 call sites, no shim)

`data.py` → 18 files in `src/data/`, split by concern (table inventory in the package layout above). Migration strategy: a script scans all `D.SYMBOL` call sites and batch-rewrites them to `from src.data.<file> import SYMBOL`. Order: tuning/elements/skills first (fewest deps), heroes/enemies/gacha next (depend on skills), story/npc last.

- **Phase 1:** `src/data/__init__.py` is a shim re-exporting everything from the not-yet-split `data.py` so `import data as D; D.X` still works while files move.
- **Phase 2:** actually split `data.py` into the 18 files, migrate the 416 call sites to specific imports, then **remove the shim** — no `D.*` remains.

## Testing strategy — new ECS suite

Suite: `tools/verify_ecs.py`, run `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs`. Replaces `/tmp/verify_complete.py` (which tests the old `WorldScene`/`WorldEnemy` API and is dropped from Phase 3 onward).

**Layer 1 — Unit (component/entity/world):** Entity spawn → unique eid, add/get/has correct. World spawn/destroy/query/heroes/enemies: correct subset, no leak. Component dataclass slots + defaults. Combatant/Hero/Enemy stat logic (leveling, ascension, equip bonus).

**Layer 2 — System (stateless processor):** `CombatSystem.basic_attack` — HP reduction with element_mult, energy gain, atk_cd. `use_skill` — cooldown + energy cost, damage from SKILLS_DB, reaction trigger (fire+water→steam). `use_ultimate` — full-energy gate, extra effect (heal/shield/knockback) from ULTIMATE_VARIANTS. `on_hit`/`on_death` — drop spawn, combo milestone, signature passive. `PhysicsSystem` — movement (accel/friction), collision, camera follow. `AISystem` — mob hop/pounce/kite by AI.kind, aggro range, de-aggro. `DropSystem` — drift + pickup → gold/shard/item. `RiftSystem` — trigger → wave → clear. `MapController` — edge transition, discover_neighbors, teleport, boss-cell seal/unseal.

**Layer 3 — Integration (WorldScene + systems):** Boot title→world→adventure transitions. One frame `WorldScene.update(dt, [])` + `draw(surf)` no exception. Party 4 hero entities, swap 1/2/3/4 changes active, HP/energy persist. Save round-trip. Gacha 10-pull + 180-pull 0 error.

**Layer 4 — Stress + perf:** 1200-frame WorldScene update+draw, capture fps (gate: no regression >10% vs baseline ~152fps). 1200-frame adventure. `verify_assets.py` stays green (bundles unchanged).

**Layer 5 — Build:** `python3 -m src.assets_gen.generate` produces all art (16 enemies, 4 boss-ult, bg/items/ui/terrain/landmarks/villages/drops). `generate_sprites(champions)` → 170 descriptor sprites.

**Per-phase gates:** Layer 1-2 (unit+system) pass from Phase 3-4 onward; Layer 3-4 (integration+stress) pass every phase; Layer 5 passes Phase 1+5. The old `/tmp/verify_complete.py` runs in parallel during Phase 1-2 (old API), dropped from Phase 3.

## Migration plan — 5 staged phases

Each phase: implement → `verify_assets.py` green → acceptance suite pass → 1200-frame stress no fps regression → commit. Code stays runnable as `python3 main.py` between phases; can stop mid-way.

**Phase 1 — Package layout (move + re-import only, 0 logic change).** Create `src/` tree + `__init__.py` files. Move files to correct subdirs (rename `world_scene.py`→`src/scenes/world.py`, etc.), content unchanged. `src/data/__init__.py` = shim re-exporting old `data.py`. `main.py` thin: add `src/` to `sys.path`, import `from src.core.game import Game`. Verify: `python3 main.py` runs, 21/21 suite (update import paths), stress. Zero logic lines changed.

**Phase 2 — Data package + call-site migration (no shim).** Split `data.py` → 18 files in `src/data/`. Script scans 416 `D.*` call sites → batch rewrite to `from src.data.<file> import SYMBOL`. Remove the shim. Verify: imports green, 21/21, stress, gacha 180 pulls. Gate: no `import data as D` or `D.*` remains.

**Phase 3 — Entity → component data bag.** Create `src/entities/components.py` (dataclass slots) + `Entity` + `World`. Convert `WorldCharacter`/`WorldEnemy` to entity factories: spawn hero/enemy entity, attach Transform/Health/Combat/AI/Render/Statuses/ChampionRef. `Combatant`/`Hero`/`Enemy` stat classes kept, referenced by the `Combat`/`ChampionRef` component. WorldScene temporarily calls through an adapter (entity ↔ old WorldCharacter) so not-yet-extracted systems don't break. Verify: new suite (spawn entity + component, query heroes/enemies), stress. Combat still runs through the adapter.

**Phase 4 — Systems stateless (ECS core).** Split WorldScene's 70 methods into systems: CombatSystem, PhysicsSystem, AISystem, RenderSystem, HudSystem, DialogueSystem, DropSystem, RiftSystem, MapController. Each system receives `World` + data registry, mutates entity components. WorldScene becomes the thin coordinator. Delete the Phase-3 adapter (entities direct, no old object). Verify: full new suite (combat via system API, AI, drop, rift, map transition), stress, gacha.

**Phase 5 — Cleanup + docs + suite.** Delete dead adapter/old code, clean temporary `__init__.py` re-exports. Update README/AGENTS.md (package layout, ECS arch, run commands). Finalize `tools/verify_ecs.py` (full Layer 1-5). Update memory. Verify: full suite green, stress, build pipeline, boot smoke.

## User decisions (already made)

- **Scope:** Deep OOP refactor — package layout + composition + ECS-lite + class hierarchy redesign. (Highest risk.)
- **Data access:** Specific imports, no shim — migrate all 416 `D.*` call sites to `from src.data.<file> import SYMBOL`.
- **WorldScene:** ECS-lite — Entity = component data bag, System = stateless processor. `WorldCharacter`/`WorldEnemy` become entities.
- **Delivery:** Staged, 5 phases, each verified (verify_assets + acceptance suite + 1200-frame stress) before the next.
- **Verify gate:** Write a new suite for the ECS API (old `/tmp/verify_complete.py` dropped from Phase 3).
- **Package + run:** `main.py` thin at root + `src/` package; `python3 main.py` still runs.
- **Combatant/Hero/Enemy:** Kept as classes (stat logic preserved); referenced by entity components, not dissolved.

## Constraints (carry forward)

- **NEVER Read a PNG/JPG with the Read tool — it crashes the session.** Verify art headless via `pygame.image.load` under `SDL_VIDEODRIVER=dummy` / `xvfb-run`. (memory: gacha-no-image-reading)
- Behavior preserved verbatim across all phases — the 170-champion roster, combat/gacha/evo/constellation systems, controls, and assets are unchanged; only code organization + the entity/system internals change.
- `python3 main.py` must run at the end of every phase.
- `verify_assets.py` must stay green every phase (bundles untouched).
- pygame 2.6.x + numpy on Python 3.11.
