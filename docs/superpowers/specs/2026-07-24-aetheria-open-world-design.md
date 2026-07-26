# Aetheria — Open World 2D Action (Design)

Date: 2026-07-24
Status: Approved (user authorized a no-loop build: "surprise me with the finished product")

## Goal

Convert Aetheria from a turn-based gacha RPG into a **2D open-world action
game** (Genshin Impact-style) while reusing the existing heroes, enemies,
skills, elements, gacha, equipment, and ascension systems.

## Non-goals

- Keep the old turn-based BattleScene as the primary mode. The open world
  becomes the main game; the turn-based scenes are retired from the main flow.
- Hand-authored map layouts. Maps are procedurally generated per-cell with a
  deterministic seed so all 50 are stable but cheap to produce.

## Player experience

- Launch → Title → **Enter World** at the starting map (grid cell 0,0).
- Move with WASD/arrows (smooth acceleration + dash dodge with i-frames).
- A party of **4 heroes**; press **1/2/3/4** to swap the active hero
  (Genshin-style). Only the active hero is on the field; the others are in
  reserve and keep their own HP/energy.
- Real-time combat: **J / left-click** normal attack, **K / L** skills,
  **U / Space** ultimate. Energy builds from landing hits; skills/ultimate
  cost energy (reuses `data.skill_energy_cost`).
- Each map is a fixed-size room. The camera follows the active hero and is
  clamped to the map. Walking off the **left/right/top/bottom** edge
  transitions to the neighboring map (player enters on the opposite edge).
  Grid edges with no neighbor are walled.
- **50 maps** in a 10×5 grid; 5 rows are 5 biomes with rising difficulty.
  Each row ends in a boss map; the final map (9,4) is the final boss.
- **Teleport**: press **M** to open the world map overlay and jump to any
  discovered map. Maps are discovered by entering them.
- Meta-progression: enemies drop XP (→ level up), gold, consumables,
  equipment, and **Soul Shards** (→ evolve/ascend). Pause menu (Esc) reaches
  Party/Character (stats, equip, evolve, use items), Gacha, Shop, Inventory,
  Settings, and Save & Quit to Title.

## Architecture

New modules (open-world engine) layered on top of the existing data/entities:

- `world_data.py` — constants (map size, tile), the 10×5 grid of map cells,
  biome definitions (palette, decorations, enemy pool, boss), deterministic
  per-cell map generation (obstacles + spawns + exits), the teleport graph
  (neighbor links), map naming, and difficulty/level scaling.
- `world_entities.py` — `Camera` (smooth lerp, clamp), `Particles`,
  `Projectiles`, `FloatText`, `WorldCharacter` (a real-time hero with
  movement, animation, skills, energy, HP, facing, dash, i-frames), and
  `WorldEnemy` (roam/aggro/chase/attack AI, telegraph, drops).
- `world_scene.py` — `WorldScene`: input handling, the update loop
  (movement, camera, enemy AI, combat resolution, edge transitions,
  pickups, deaths), drawing (cached map surface, depth-sorted entities,
  HUD, overlays), the teleport overlay, and the pause/hub menu.
- `player.py` — save/load extended with open-world state: `ow_current`
  (col,row), `ow_pos` (x,y), `ow_discovered` (list of "col,row"),
  `ow_party_hp` / `ow_party_energy` per active hero, `shards`, and a
  `version` bump with migration.
- `main.py` — register the `"world"` scene, add an **Enter World** button on
  the title, and wire the in-world pause menu to the existing Gacha/Shop/
  Roster/Inventory/Settings scenes (reused as-is).

## Map system

- Grid: 10 columns × 5 rows = 50 cells. Cell `(c, r)`.
- Map size: `MAP_TW=50 × MAP_TH=30` tiles, `TILE=40` px → 2000×1200 px.
  The 1280×720 viewport shows ~64% of a map, so the camera moves.
- Biomes by row:
  - r0 Sunlit Meadows (plains) — slime, goblin, bat; boss golem.
  - r1 Whispering Woods (forest) — wolf, goblin, harpy, imp; boss hydra.
  - r2 Crystal Caverns (cave) — bat, skeleton, ghoul, golem; boss frosttitan.
  - r3 Ruined Citadel (castle) — skeleton, orc, paladin, wraith; boss dragon.
  - r4 The Void (void) — wraith, paladin, hydra, demon; boss demonking (final).
- Generation: per-cell `random.Random(seed(c,r))`. Place ground tiles, a
  border, scattered obstacles (trees/rocks/pillars by biome) with collision
  rects, enemy spawn points (count scales with difficulty, capped at ~12),
  and one boss on boss cells. Exits link to existing neighbors.
- Difficulty: `level = 1 + r*6 + int(c*1.5)`; bosses +6 levels.
- Rendering: on map load, render ground + decorations to one cached
  `Surface` (2000×1200) and blit the visible slice each frame. Obstacles are
  baked into the surface; a separate rect list drives collision. This keeps
  per-frame work to a single blit + dynamic entities.

## Camera & movement

- Camera follows the active hero with an exponential lerp, clamped to
  `[0, MAP_W - VIEW_W]` / `[0, MAP_H - VIEW_H]`.
- Movement: target velocity = input_dir × max_speed; integrate with accel
  toward target and friction when no input. ~220 px/s, dash ~520 px/s for
  ~0.18s with ~0.3s i-frames, ~1s cooldown.
- 8-directional, normalized diagonals. Facing flips the sprite horizontally.

## Combat (real-time)

- Normal attack: melee arc (sword/dagger) or projectile (bow/staff/orb) by
  weapon; short cooldown; builds energy.
- Skills: interpreted from `SKILLS_DB` `type`/`element`:
  - attack/slash → melee arc; magic/bolt → projectile; aoe_* → burst around
    the hero; heal → heal active (+party share); buff/debuff → self/nearby;
    ultimate → large AoE or large heal, costs full energy.
- Damage reuses the element chart, crit, and defense from `data.py`/`entities`.
- Juice: hit flash, screen shake, hit-stop, element-tinted particles,
  floating damage numbers (crit larger).
- Enemy AI: idle (wander) → aggro (chase within ~300px) → attack (telegraph
  ~0.4s, strike, cooldown). Ranged enemies fire projectiles. Contact
  damage on melee. Knockback on hit.
- Bosses: more HP, multiple attack patterns, a telegraphed ultimate below
  50% HP (reuses `BOSS_ULTIMATES`), large drops + guaranteed shards.

## Party & switching

- 4 party slots from `player.team` (extended to 4). Press 1/2/3/4 to make
  that slot active. Swap is instant with a quick flash; the previous hero
  leaves the field, the new one enters at the same position.
- Each hero has independent HP/energy persisted across swaps and map
  transitions (saved). Full-party wipe → respawn at the hub (cell 0,0) with
  a small gold penalty; single deaths → switch to a living hero.
- HUD: active portrait + HP/energy bars, four party icons (1-4) with
  cooldown/energy hints, minimap, current map name, gold/gems/shards.

## Items, level, evolve

- Level: XP from kills → `Hero.gain_xp`; level raises stats (`STAT_GROWTH`).
- Gold: currency for shop/gacha.
- Consumables: drop from enemies; **Q** uses an HP potion on the active hero.
- Equipment: drops from elites/bosses; equip in the Character menu.
- Evolve (ascension): **Soul Shards** drop from bosses/elites; spend
  `shard_cost + gold` to ascend a hero (reuses `ASCENSION_BONUS` stages).
  Gacha duplicates also still convert to ascension.

## Teleport

- Press M → overlay draws the 10×5 grid; discovered cells are selectable,
  undiscovered are hidden/locked. Click (or arrow + Enter) to teleport.
  Teleporting preserves party HP/energy.

## Performance

- One cached map `Surface` per loaded map (regenerated only on map change).
- Camera culling for dynamic entities (skip off-screen).
- Capped particles (~200, recycled), capped enemies per map (~12).
- `convert_alpha` on all sprites; vsync on; `dt`-driven, capped at 1/30s.
- Sprite flip cached; walk animation via sine bob + leg shimmy, no per-frame
  asset work.

## Save/load

- Extend `Player.save`/`load` with `ow_*` fields + `shards`; bump version to
  4 with migration (missing fields default; old saves start at cell 0,0).

## Controls

- Move: WASD / Arrows. Dash: Shift / RMB.
- Attack: J / Left-click. Skills: K, L. Ultimate: U / Space.
- Switch hero: 1, 2, 3, 4. Use potion: Q.
- Character menu: C. Teleport: M. Inventory: I. Pause: Esc.

## Testing

- Headless smoke test: `SDL_VIDEODRIVER=dummy python3 main.py` runs N frames
  across several maps (walk off edges, switch heroes, fight, teleport) with
  no exceptions and a stable 60fps tick.
- Manual: `python3 main.py` → Enter World → explore, switch, fight, evolve,
  teleport.
