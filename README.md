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
pip install -r requirements.txt
python3 generate_assets.py     # (re)generate all PNG assets into assets/
python3 main.py                # play
```

From the title screen, pick **Enter World** for the open-world 2D mode.

## Open World controls (LoL-style)

- `WASD` / arrows — move
- `RMB` — click-to-move (League of Legends style; the hero auto-walks to the
  click point until WASD overrides it)
- `J` — basic attack
- `Q` / `W` / `E` — skill 1 / skill 2 / skill 3 (LoL-style; each has a cooldown
  + energy cost, shown in the bottom skill bar)
- `U` or `Space` — ultimate (R slot; needs full energy)
- `1` `2` `3` `4` — swap the active hero (Genshin-style; HP/energy persist)
- `R` — use the best HP potion on the active hero
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
  A slow **day/night cycle** tints the world and makes enemies tougher at night.
- **4-hero party, Genshin-style** — carry 4 heroes; press 1-4 to swap the
  active one in place (HP & energy persist across swaps and maps), with a
  swap-in burst and brief i-frames.
- **Real-time action combat** — basic attacks, **three mapped skills (Q/W/E)**,
  a **passive**, and an **ultimate (R)** per hero (LoL-style), with an energy
  gauge, cooldown sweeps, crits, elemental weakness, hit-stop, screen shake,
  knockback, particles, and a **combo system** that ramps damage on
  consecutive hits.
- **Elemental reactions** — hitting an enemy with a different element shortly
  after another triggers a reaction (Steam, Spread, Freeze, Rupture) for
  bonus damage + a distinct VFX. Rewards swapping heroes mid-fight.
- **Perfect-dash parry** — a brief window after moving where passing through
  an enemy attack grants a "perfect dodge" (slow-mo + a damage buff).
- **Boss phase patterns** — bosses get 2-3 phases with telegraphed patterns
  (charge dash, ring slam) that escalate as their HP drops, plus an intro
  cinematic and a defeat celebration.
- **Treasure chests** — 0-2 per map, with rewards scaling by depth (gold,
  gems, shards, equipment). Persisted so a chest stays opened on revisit.
- **Progression** — hero leveling & XP, **ascension** (limit-break from gacha
  duplicates), **equipment** (weapon/armor/accessory + set bonuses), **evolve**
  (spend soul shards to ascend a hero through tiers), and a **branching
  evolution tree** per hero (root + two 3-node branches: offensive + defensive).
- **Gacha / Summoning** — single & 10-pull, SSR/SR/R rates, soft + hard pity
  (honest — the hard pity is the true guarantee), per-banner pity, duplicate-to-
  ascension, a polished rarity-scaled reveal (SSR gets a multi-stage dramatic
  reveal; R is quick), and 5 themed banners.
- **25 heroes** across 5 elements and 7 combat paths, each with a unique
  skill kit, ultimate, and passive. Per-hero eye colors, expressions, hair
  styles, and skin tones so each hero looks distinct.
- **Shop**, **inventory**, **codex**, **records** (stats + achievements +
  daily quests with a board-clear capstone bonus).
- **7-day+ login streak** with escalating daily gem bonuses.
- **Procedural audio** — per-biome ambience beds, a low-HP heartbeat, and full
  combat SFX (numpy; no audio files).
- **Settings menu** — Audio/Display/Gameplay/Accessibility/Data tabs with
  toggles + sliders (sound, volume, fullscreen, FPS cap, screen shake, particle
  quality, reduce motion, high contrast, text speed). All settings persist and
  apply live. Fullscreen defaults on.
- **Save/load** (JSON, with migration) — heroes, levels, currency, discovered
  maps, opened chests, cleared bosses, world time, and settings all persist.

## Files

| File | Purpose |
|------|---------|
| `main.py` | Game loop + scene manager + menu scenes (title, roster, hero detail, gacha, shop, inventory, codex, stats, settings) |
| `world_scene.py` | Open-world scene: input, update, edge transitions, combat, HUD, teleport, evolve, pause hub, boss cinematics, day/night |
| `world_entities.py` | Camera, particles, projectiles, real-time WorldCharacter & WorldEnemy (AI, boss phases, enemy archetypes) |
| `world_data.py` | 10x5 grid, biomes, per-biome map generation, teleport graph, boss arenas |
| `data.py` | Static data: heroes, enemies, skills, gacha pool, items, equipment, evolve tree, achievements, quests, tuning |
| `entities.py` | Hero/Enemy runtime objects, stats, leveling, ascension, evolve, equipment, set bonuses |
| `gacha.py` | Summoning system with pity + rate-up |
| `player.py` | Player state, inventory, shop, evolve, achievements, quests, save/load |
| `audio.py` | Procedural sound synthesis (per-biome ambience, combat SFX, heartbeat) |
| `generate_assets.py` | Procedural PNG asset generator (characters, enemies, skills, items, ui, backgrounds, portraits) |
| `verify_assets.py` | Headless asset verifier (renders every sprite, reports size/coverage) |
| `assets/` | Generated PNGs (characters, enemies, skills, items, ui, backgrounds, portraits) |
| `saves/save.json` | Save file (auto-created, gitignored) |

## Verification

The game is verified headless (no window needed):

```bash
xvfb-run -a python3 verify_assets.py    # render every sprite, report sizes
SDL_VIDEODRIVER=dummy python3 main.py    # boot + play headless
```

## License

Personal project. All art and audio are procedurally generated.
