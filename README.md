# Aetheria — Open World 2D Gacha RPG

A complete **open-world 2D** gacha RPG built with **pygame**, with **zero
external art or audio dependencies**. All characters, enemies, skills, items,
UI, backgrounds and sound effects are generated procedurally by
`generate_assets.py` and `audio.py`.

The game is **open-world first**: a 10×5 grid of **50 hand-styled maps** with
real-time action combat, a 4-hero party you swap on the fly (Genshin-style),
edge transitions between maps, and a teleport world map. The old turn-based
campaign has been removed — the open world *is* the game.

## Run

```bash
pip install pygame numpy
python3 generate_assets.py     # (re)generate all PNG assets into assets/
python3 main.py                # play
```

From the title screen, pick **Enter World** for the open-world 2D mode.

## Open World controls

- `WASD` / arrows — move
- `Shift` or `RMB` — dash (i-frames)
- `J` or `LMB` — basic attack
- `Q` / `W` / `E` — skill 1 / skill 2 / skill 3 (LoL-style; each has a cooldown + energy cost, shown in the bottom skill bar)
- `U` or `Space` — ultimate (R slot; needs full energy)
- `1` `2` `3` `4` — swap the active hero (Genshin-style; HP/energy persist)
- `R` — use an HP potion on the active hero
- `M` — open the world map / teleport
- `G` — open the Evolve screen (spend soul shards to ascend a hero)
- `Esc` — pause hub (roster, evolve, summon, shop, inventory, quit)

Each hero also has a **passive** (always-on combat ability, shown next to the
skill bar) — e.g. lifesteal, thorns, crit-up, low-HP shield, out-of-combat regen.

## Features

- **Open world** — a 10x5 grid of **50 hand-styled maps** across 5 biomes
  (plains, forest, cave, castle, void). Walk to a map edge to slide into the
  neighbor; open the **teleport map** (M) to jump to any discovered cell.
  Each row scales in difficulty toward a **boss arena** on the right edge.
- **4-hero party, Genshin-style** — carry 4 heroes; press 1-4 to swap the
  active one in place (HP & energy persist across swaps and maps), with a
  swap-in burst and brief i-frames.
- **Real-time action combat** — basic attacks, **three mapped skills (Q/W/E)**,
  a **passive**, and an **ultimate (R)** per hero (LoL-style), with an energy
  gauge, cooldown sweeps, crits, elemental weakness, hit-stop, screen shake,
  knockback, dash i-frames, and particles.
- **Bosses** with telegraphed attacks and an ultimate below 50% HP.
- **Progression** — hero leveling & XP (with level-up pop), **ascension**
  (limit-break from gacha duplicates), **equipment** (weapon/armor/accessory),
  **evolve** (spend soul shards to ascend a hero through tiers:
  Awakened -> Divine, each a big stat jump), and a **branching evolution tree**
  per hero (root + two 3-node branches: an offensive and a defensive path).
  Tree nodes grant stat bonuses, crit, energy, and passives (lifesteal, thorns,
  regen, low-HP shield, etc.) — pick a build per hero.
- **Gacha / Summoning** — single & 10-pull, SSR/SR/R rates, soft + hard pity,
  duplicate-to-ascension, and a polished reveal.
- **25 heroes** across 5 elements and 7 combat paths, each with a unique
  skill kit and ultimate.
- **Shop**, **inventory**, **codex**, **records** (stats + achievements +
  daily quests).
- **7-day login streak** with escalating daily gem bonuses.
- **Save/load** (JSON, with migration) and **procedural sound** (numpy; no
  audio files).

## Files

| File | Purpose |
|------|---------|
| `main.py` | Game loop + scene manager + menu scenes (title, roster, hero detail, gacha, shop, inventory, codex, stats, settings) |
| `world_scene.py` | Open-world scene: input, update, edge transitions, combat, HUD, teleport, evolve, pause hub |
| `world_entities.py` | Camera, particles, projectiles, real-time WorldCharacter & WorldEnemy |
| `world_data.py` | 10x5 grid, biomes, deterministic per-cell generation, teleport graph |
| `data.py` | Static data: heroes, enemies, skills, gacha pool, items, equipment, evolve, achievements, quests, tuning |
| `entities.py` | Hero/Enemy runtime objects, stats, leveling, ascension, evolve, equipment |
| `gacha.py` | Summoning system with pity |
| `player.py` | Player state, inventory, shop, evolve, achievements, quests, save/load |
| `audio.py` | Procedural sound synthesis |
| `generate_assets.py` | Procedural PNG asset generator (run once) |
| `assets/` | Generated PNGs (characters, enemies, skills, items, ui, backgrounds, portraits) |
| `saves/save.json` | Save file (auto-created) |
