# Aetheria Big Bang v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:subagent-driven-development (recommended) or superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the game into Adventure (wave-survival) + Endless (open-world Zelda-like story) modes; overhaul art to procedural pixel-art with per-character asset bundles; make the skill system readable (taxonomy + hover tooltips + hold-to-aim); add LoL-style auto-attack; fix mana regen; ground loot as visible pickups; enrich terrain (water/bridges/landmarks/villages); remove the stray fog-mote circles. 14 enhancements, batched A-E with a gated fix-and-enhance loop.

**Architecture:** Aetheria is a pygame open-world 2D action gacha RPG (~14.8k LOC, pure-procedural art/audio, single-dev, ~60fps, headless-verified). v2 builds on v1 (28 commits, 23 tasks, 5 gates — all green on branch `worktree-big-bang`). Each task → one specialist agent with worktree isolation; a gate agent checks the whole system headless after each batch and the loop spawns fix agents until the gate passes.

**Tech Stack:** Python 3.11, pygame 2.6, numpy; headless verify via `xvfb-run -a` + `SDL_VIDEODRIVER=dummy`.

**User decisions (already made):**
- "làm hết đi" — full scope, all 14 enhancements; no trim.
- "apply kiểu của superpowers để viết spec và implement" — superpowers workflow (spec → plan → subagent-driven implementation).
- Asset strategy: "phân vân giữa 1 và 2 + thích pixel-art kiểu Stardew Valley nhưng nhiều pixel hơn" — stay pure-procedural BUT adopt a pixel-art aesthetic at higher pixel density than Stardew (no external PNGs).
- Adventure mode: "Separate dedicated scene" — Adventure is a new `AdventureScene`, not a flag in the world scene.
- Adventure party: "Fixed 4, swap allowed" — lock the 4-char roster for the run, 1-4 mid-fight swap stays.
- World enrichment: "Full enrichment" — ground loot drops + new terrain (water/bridges/landmarks/villages) + remove fog motes.
- Gated loop (from v1, carried forward): a gate agent checks the system until everything is OK; if the gate hasn't passed, keep spawning agents to implement/fix.

**Verified facts (from the 4-agent codebase survey during planning):**
- 25 heroes, each with a unique 256px chibi sprite + 512px portrait (`generate_assets.py:179` `draw_chibi`, `:2338` `make_portrait`); 17 enemies; 41 skill icons (9 shared kind-glyphs recolored by element, `:1453` `draw_skill_icon`). Asset tree: `assets/{characters,portraits,enemies,skills,backgrounds,items,ui}/`.
- The party is a 4-slot array, one `active` hero, Genshin-style 1-4 live swap with i-frames + resonance recompute (`world_scene.py:2348` `_switch`). Roster edits anytime in `RosterScene`.
- Skills: `SKILLS_DB` (`data.py:495`) with `type` field (attack/magic/aoe/heal/buff/debuff/ultimate — NO summon/innate/beam). 3 active skills (Q/W/E) + 1 ult (U/Space) + 1 basic attack (J). No hold-to-charge, no hover tooltip, no aim preview. Skill bar at `world_scene.py:3936` (`_draw_skill_bar`).
- Energy: per-hero, `ENERGY_REGEN_PCT=0.04` (4%/s out of combat, 2%/s in combat, `world_entities.py:756`). On-hit gains (+25 basic, +8 skill). The user still feels mana doesn't increase → root-cause + tune.
- RMB = click-to-move (`world_scene.py:2534`); LMB = no-op; J = manual basic attack (`_do_attack` `:1516`, 0.32s cd). No auto-attack.
- `self.drops` (`world_scene.py:934`) is declared but NEVER populated — drops go straight to inventory (`:2145`). No ground item sprites.
- Fog motes (`world_scene.py:958` init, `:3231` draw — 7 big soft circles, `BLEND_RGBA_ADD`) are the "stray white circles". Rain/storm/fog overlays are separate (`:3345`).
- World: 50 maps (GRID_W=10 × GRID_H=5), 5 biomes (one per row), bosses at column 9 (rightmost) per row, final boss Demon King at (9,4). `gen_map` (`world_data.py:358`) returns `{obstacles, deco, spawns, boss, is_boss, biome, pal, chests, breakables, secret}`. No water/impassable terrain, no villages, no NPCs, no story (sandbox + daily quests). `STAGES_DB=[]` (turn-based campaign deleted).
- Scenes routed in `main.py:2190` `_make_scene`; title at `:333` `TitleScene` with a single "Enter World" button (`:346`). Save version 7 (`player.py:437`).
- MapRenderer cache keyed on `(c,r)` — weather/rifts stay live overlays; water/landmarks/villages are static gen_map features (cache-safe).

---

## File structure

**New files:**
- `adventure_scene.py` — the `AdventureScene` (wave-survival mode), reusing the combat engine via a shared combat mixin.

**Modified:**
- `generate_assets.py` — pixel-art aesthetic rewrite of `draw_chibi`/`draw_enemy`/`draw_skill_icon`/`make_portrait`/`make_ui`/`make_items`/`make_battle_bg`/`make_map_bg`; new terrain/landmark/village/drop sprites; `PIXEL`/`PIXEL_PALETTE` constants.
- `data.py` — `HERO_ASSETS` manifest (consolidating lore/signature/constellation/ult-variant/skill descriptions); `PIXEL_PALETTE`; expanded skill taxonomy (`category`, new skill types summon/beam/trap/innate); `NPCS`/`STORY_QUESTS`/`DIALOGUE`; `ADVENTURE_*` constants; `AA_RANGE`/`AA_CD`; tune `ENERGY_REGEN_PCT`.
- `world_scene.py` — skill hover tooltips; hold-to-aim preview; AA (RMB-enemy); ground loot drops; remove fog motes; terrain water/bridges/landmarks/villages draw + collision; NPC spawn + interact + dialogue; boss gating; mode-aware routing.
- `world_entities.py` — `aa_target` + auto-attack in `WorldCharacter`; mana regen tune; summon/trap entities.
- `world_data.py` — `gen_map` adds `water`/`bridges`/`landmark`/`village`; `cell_level` unchanged (distance scaling already exists).
- `main.py` — title mode selector (Adventure/Endless); `_make_scene` routes to `AdventureScene`; `RosterScene` locks team in adventure; codex/hero-detail read `HERO_ASSETS`; quest tracker shows the story chain.
- `player.py` — `mode` field + `adventure_best_stage`; save version 8 migration.
- `verify_assets.py` — assert the new sprites render + sizes unchanged.

**Shared-file conflict map (drives batching):** `world_scene.py` is touched by ~10 tasks; `data.py` by ~7; `generate_assets.py` by ~3; `main.py` by ~5; `world_entities.py` by ~3; `world_data.py` by ~2; `player.py` by ~3. Batches group tasks that DON'T overlap on the same file regions. The hot file `world_scene.py` is split across B (skill/AA/loot), C (terrain/fog), E (NPC/story) — each batch owns a distinct region.

---

## Batch A — Asset overhaul (generate_assets.py + data.py manifest; no hot-loop risk)

### Task A1: Pixel-art aesthetic overhaul

**Goal:** Redraw all procedural art in a pixel-art aesthetic (chunky pixels, limited palette, dithering, no anti-aliased gradients) at higher pixel density than Stardew Valley, keeping sprite sizes + loader paths unchanged.

**Files:**
- Modify: `generate_assets.py:17` (`ASSET_DIR` — add `PIXEL`/`PIXEL_PALETTE` constants nearby) + `:179` (`draw_chibi`) + `:926` (`draw_enemy`) + `:1453` (`draw_skill_icon`) + `:2338` (`make_portrait`) + `:1675` (`make_ui`) + `:1841` (`make_items`) + `:1591`/`:1644` (`make_battle_bg`/`make_map_bg`)
- Modify: `data.py:24` (`ELEMENT_COLORS` — add `PIXEL_PALETTE` after it)
- Modify: `verify_assets.py` (assert sizes unchanged)

**Acceptance Criteria:**
- [ ] `generate_assets.py` defines `PIXEL = 5` (each logical pixel = 5px at the 256px world sprite) + a per-element `PIXEL_PALETTE` dict (5 colors each: base/light/shadow/outline/accent), re-exported from `data.py`.
- [ ] `draw_chibi`/`draw_enemy`/`draw_skill_icon`/`make_portrait`/`make_ui`/`make_items`/`make_battle_bg`/`make_map_bg` render on the coarse pixel grid: palette-locked fills, dithered gradients (a 2-color checker pattern instead of smooth `lerp_color` ramps), no `pygame.draw` anti-aliasing (no `aa=True` on circles/lines). Character sprites render at ~48×48 logical pixels, upscaled to 256px (world) / 512px (portrait).
- [ ] **Sprite sizes + file paths unchanged** — `characters/{id}.png` (256×256), `portraits/{id}.png` (512×512), `enemies/{id}.png` (256×256), `skills/{id}.png` (128×128), backgrounds/UI/items same sizes. `load_char_sprite`/`load_portrait`/`load_skill_icon`/`load_enemy_sprite` + the scene caches work unchanged.
- [ ] The 5 elements stay visually distinct from each other AND from HP-red/crit-yellow/heal-green.
- [ ] Headless: `xvfb-run -a python3 verify_assets.py` exits 0 (every sprite renders, sizes unchanged).

**Verify:** `xvfb-run -a python3 verify_assets.py` → exit 0; then `xvfb-run -a python3 -c "import os,pygame; os.environ['SDL_VIDEODRIVER']='dummy'; pygame.init(); pygame.display.set_mode((1,1)); import generate_assets as GA; GA.main(); from entities import load_char_sprite; s=load_char_sprite('aria'); assert s.get_size()==(256,256), s.get_size(); p=__import__('entities').load_portrait('aria'); assert p.get_size()==(512,512), p.get_size(); print('A1 OK', s.get_size(), p.get_size())"` → `A1 OK (256, 256) (512, 512)`

**Steps:**

- [ ] **Step 1: Add `PIXEL` + `PIXEL_PALETTE` to data.py** (after `ELEMENT_COLORS`, line ~24):

```python
# pixel-art scale: each logical pixel is rendered as a PIXEL×PIXEL block so the
# art reads as chunky pixel-art at higher density than Stardew (Stardew tiles are
# 16x16; a 256px sprite at PIXEL=5 -> ~51 logical pixels, 3x Stardew). Palette is
# locked per element (base/light/shadow/outline/accent) so gradients dither
# instead of smoothing.
PIXEL = 5
PIXEL_PALETTE = {
    "fire":   {"base": (220, 90, 40), "light": (255, 170, 90), "shadow": (130, 40, 20),
               "outline": (60, 20, 10), "accent": (255, 230, 140)},
    "water":  {"base": (40, 120, 210), "light": (120, 200, 255), "shadow": (20, 60, 120),
               "outline": (10, 30, 60), "accent": (200, 240, 255)},
    "wind":   {"base": (120, 220, 160), "light": (200, 255, 220), "shadow": (60, 130, 90),
               "outline": (20, 50, 40), "accent": (240, 255, 200)},
    "light":  {"base": (250, 220, 90), "light": (255, 250, 200), "shadow": (180, 140, 40),
               "outline": (80, 60, 20), "accent": (255, 255, 240)},
    "dark":   {"base": (110, 50, 150), "light": (180, 110, 220), "shadow": (60, 20, 90),
               "outline": (30, 10, 50), "accent": (200, 160, 255)},
}
```

- [ ] **Step 2: Add a pixel-fill helper in generate_assets.py** (near the top, after the imports):

```python
def px_fill(surf, color, rect):
    """Fill a rect with a single solid color (pixel-art: no anti-aliasing)."""
    pygame.draw.rect(surf, color, rect)

def px_dither(surf, c1, c2, rect, step=10):
    """A 2-color checker dither over a rect (replaces smooth gradients with a
    pixel-art gradient). step is the checker size in px (match PIXEL)."""
    x, y, w, h = rect
    for yy in range(y, y + h, step):
        for xx in range(x, x + w, step):
            c = c1 if ((xx + yy) // step) % 2 == 0 else c2
            pygame.draw.rect(surf, c, (xx, yy, step, step))
```

- [ ] **Step 3: Rewrite `draw_chibi` (line 179)** to use palette-locked fills + dithered gradients from `PIXEL_PALETTE[element]` instead of smooth `lerp_color` gradients. Render the body/hair/weapon/eyes as solid palette colors with a 2-tone dither for shading. No `aa=True`. Keep the 256×256 size + the per-hero parameter signature (`element, weapon, hair_style, hair_color, body_color, accent, eye, expression, eye_shape, skin`).

- [ ] **Step 4: Rewrite `draw_enemy` (line 926), `draw_skill_icon` (line 1453), `make_portrait` (line 2338), `make_ui` (line 1675), `make_items` (line 1841), `make_battle_bg`/`make_map_bg` (lines 1591/1644)** the same way: palette-locked fills, dithered gradients, no anti-aliasing. Keep all output sizes + file paths unchanged.

- [ ] **Step 5: Regenerate all assets** — `xvfb-run -a python3 generate_assets.py` so the pixel-art sprites are on disk.

- [ ] **Step 6: Run the verify command** → `A1 OK (256, 256) (512, 512)` + `verify_assets.py` exit 0.

- [ ] **Step 7: Commit**

```bash
git add generate_assets.py data.py assets/ verify_assets.py
git commit -m "feat(art): pixel-art aesthetic overhaul (chunky pixels, dithering, no AA)

Redraws all procedural art in a pixel-art style at ~48-logical-pixel density
(3x Stardew's 16), palette-locked per element + dithered gradients instead
of smooth anti-aliased ramps. Sprite sizes + loader paths unchanged."
```

---

### Task A2: Per-character HERO_ASSETS manifest

**Goal:** Consolidate the scattered per-hero data (lore, signature, constellation, ultimate variant, skills) into one `HERO_ASSETS` manifest keyed by hero id — the single source of truth for the codex, hero-detail screen, and skill tooltips. Each entry carries skill descriptions + how-to-use.

**Files:**
- Modify: `data.py` (add `HERO_ASSETS` after `HERO_BY_ID`, line ~773; consolidate `HERO_LORE`/`HERO_SIGNATURE`/`CONSTELLATION_PERKS`/`ULTIMATE_VARIANTS` references)
- Modify: `main.py:667` (`HeroDetailScene.draw` — read from `HERO_ASSETS`) + `:1869` (`CodexScene` — read from `HERO_ASSETS`)
- Modify: `world_scene.py:3936` (`_draw_skill_bar` — read `how_to_use`/`description` from the manifest; wired in Task B1)

**Acceptance Criteria:**
- [ ] `data.py` defines `HERO_ASSETS = {hero_id: {name, title, element, role, lore{bio, quote, personality}, skills[{id, name, type, category, cost, description, how_to_use}], signature{name, desc}, constellation[6 × {name, desc}], ultimate{name, desc, extra_effect}}}` for all 25 heroes.
- [ ] Each skill entry's `id` matches `HEROES_DB[id].skills` + `ultimate`; `description` is a human-readable ≤100-char sentence; `how_to_use` names the key + hold-to-aim note + AoE/range.
- [ ] The manifest references the combat dicts (`SKILLS_DB`/`ULTIMATE_VARIANTS`/`HERO_SIGNATURE`/`CONSTELLATION_PERKS`) for mechanics — it does NOT duplicate the combat data (presentation + descriptions only).
- [ ] `HeroDetailScene.draw` + `CodexScene` read from `HERO_ASSETS` instead of the scattered dicts (no regression — the displayed content is the same or richer).
- [ ] Headless: `python3 -c "import data as D; assert len(D.HERO_ASSETS)>=25; a=D.HERO_ASSETS['aria']; assert 'skills' in a and len(a['skills'])>=4; assert all('description' in s and 'how_to_use' in s for s in a['skills']); print('A2 OK', len(D.HERO_ASSETS))"` → `A2 OK 25`.

**Verify:** the headless assertion + `xvfb-run -a python3 /tmp/verify_complete.py` → 20/20.

**Steps:**

- [ ] **Step 1: Add `HERO_ASSETS` to data.py** (after `HERO_BY_ID`, line ~773). 25 entries, one per hero id in `HEROES_DB`. Each entry's `skills` list = the 3 active skills + ultimate + basic_attack, each `{id, name, type, category, cost, description, how_to_use}`. Reuse `HERO_LORE[hero_id]` for `lore`, `HERO_SIGNATURE[hero_id]` for `signature`, `CONSTELLATION_PERKS[role]` for `constellation`, `ULTIMATE_VARIANTS[hero_id]` for `ultimate`. Example:

```python
HERO_ASSETS = {
    "aria": {
        "name": "Aria", "title": "Knight of Dawn", "element": "light", "role": "guardian",
        "lore": HERO_LORE["aria"],
        "skills": [
            {"id": "light_slash", "name": "Dawn Slash", "type": "attack", "category": "Attack",
             "cost": 2, "description": "A radiant sword strike. Hits one enemy in front.",
             "how_to_use": "Q — tap to cast in facing; hold to aim the arc."},
            {"id": "light_bolt", "name": "Light Bolt", "type": "magic", "category": "Magic",
             "cost": 3, "description": "A bolt of light. Ranged single-target.",
             "how_to_use": "W — tap to cast at nearest enemy; hold to aim the trajectory."},
            {"id": "light_heal", "name": "Mending Light", "type": "heal", "category": "Heal",
             "cost": 4, "description": "Heal the party for a modest amount.",
             "how_to_use": "E — tap to cast (self-centered)."},
            {"id": "light_hymn", "name": "Hymn of Dawn", "type": "ultimate", "category": "Ultimate",
             "cost": 8, "description": "A radiant hymn damaging all enemies + self-heal.",
             "how_to_use": "U/Space — full energy; hits all enemies on screen."},
        ],
        "signature": {"name": HERO_SIGNATURE["aria"], "desc": "..."},
        "constellation": [{"name": p["name"], "desc": p["desc"]} for p in CONSTELLATION_PERKS["guardian"]],
        "ultimate": ULTIMATE_VARIANTS["aria"],
    },
    # ... 24 more
}
```

- [ ] **Step 2: Route `HeroDetailScene.draw` (main.py:667) + `CodexScene` (main.py:1869) through `HERO_ASSETS`** — read the lore/skills/signature/constellation/ultimate from the manifest instead of the scattered dicts. Keep the displayed content the same or richer (add the `how_to_use` line under each skill).

- [ ] **Step 3: Run the verify command** → `A2 OK 25` + 20/20.

- [ ] **Step 4: Commit** `git commit -m "feat(chars): per-character HERO_ASSETS manifest (skills+lore+descriptions)"`

---

### Task A3: Skill taxonomy expansion

**Goal:** Expand the skill type taxonomy with `summon`/`beam`/`trap`/`innate` (plus existing attack/magic/aoe/heal/buff/debuff/ultimate), add a `category` field for UI grouping, and add a few new skills of the new types so the taxonomy is real.

**Files:**
- Modify: `data.py:495` (`SKILLS_DB` — add `category` to each skill + ~4-6 new skills of new types) + `:667` (`HEROES_DB` — give 2-3 heroes a new-type skill in their kit)
- Modify: `world_scene.py:1636` (`_do_skill` — add dispatch branches for `summon`/`beam`/`trap`)
- Modify: `world_entities.py` (a `SummonAlly`/`Trap` entity, or reuse the projectile pattern)

**Acceptance Criteria:**
- [ ] `SKILLS_DB` has a `category` field on every skill. New skill types added: `summon` (spawn a temporary ally/construct), `beam` (line hit-scan), `trap` (place a delayed hazard), `innate` (display-only tag for signature passives).
- [ ] ~4-6 new skills of the new types are added to `SKILLS_DB` (e.g. `fire_summon`, `light_beam`, `dark_trap`, `water_summon`) with `power`/`cost`/`desc`/`potency`/`dur` as appropriate.
- [ ] 2-3 heroes get a new-type skill in their `HEROES_DB[id].skills` kit (e.g. a summoner hero, a beam mage), reflected in their `HERO_ASSETS` manifest (Task A2).
- [ ] `_do_skill` dispatches `summon` (spawn a temporary `WorldEntity` ally at the hero's side that auto-attacks nearby enemies for a duration — NOT a party member, don't break the 4-slot party), `beam` (a line hit-scan from hero toward the aim/facing, damages all enemies along the line), `trap` (place a trap entity on the ground that triggers when an enemy steps on it).
- [ ] The new skills are balanced (don't trivialize combat) + respect the existing hit-scan/collision.
- [ ] Headless: `python3 -c "import data as D; cats=set(s.get('category') for s in D.SKILLS_DB.values()); assert {'Summon','Beam','Trap'} <= cats or {'summon','beam','trap'} <= set(s.get('type') for s in D.SKILLS_DB.values()); print('A3 OK', cats)"` → `A3 OK ...`.

**Verify:** the headless assertion + `xvfb-run -a python3 /tmp/verify_complete.py` → 20/20.

**Steps:**

- [ ] **Step 1: Add `category` + the new skill types to `SKILLS_DB` (data.py:495)** — add a `category` field to each existing skill (Attack/Magic/AoE/Heal/Buff/Debuff/Ultimate). Add ~4-6 new skills: `fire_summon` (summon, fire, cost 5, spawns a fire construct), `light_beam` (beam, light, cost 4, line hit-scan), `dark_trap` (trap, dark, cost 3, delayed hazard), `water_summon` (summon, water, cost 5). Each with `power`/`cost`/`desc`/`potency`/`dur`.

- [ ] **Step 2: Give 2-3 heroes a new-type skill** in `HEROES_DB[id].skills` (data.py:667) — replace one of their 3 active skills with a new-type skill. Reflect in `HERO_ASSETS` (Task A2's manifest).

- [ ] **Step 3: Add the `summon`/`beam`/`trap` dispatch in `_do_skill` (world_scene.py:1636)** — after the existing `kind in ("attack","magic")`/`aoe_*`/heal/buff/debuff branches, add:

```python
        elif kind == "summon":
            # spawn a temporary ally (a WorldEntity construct) at the hero's side
            # that auto-attacks nearby enemies for `dur` seconds. NOT a party
            # member — a separate entity so the 4-slot party is untouched.
            ally = SummonAlly(wc, skill, self.particles)
            self._summons.append(ally)
            audio.play("skill", 0.3)
        elif kind == "beam":
            # line hit-scan from hero toward facing/aim — damage all enemies along
            # the line within `range`.
            bx, by = wc.x + wc.facing * 20, wc.y
            ex, ey = bx + wc.facing * skill.get("range", 400), by
            for en in self.enemies:
                if en.alive and _line_hit(bx, by, ex, ey, en.x, en.y, en.r):
                    dmg = int(atk * skill["power"] * self._element_mult(wc.element, en.element))
                    dealt = en.take_damage(dmg, wc.x, wc.y, False, on_attack=self._on_enemy_event)
                    if dealt > 0: self._on_enemy_hit(en, wc, dealt, False)
            self.particles.spark(bx, by, col, n=8, speed=300, size=5, life=0.2)
            audio.play("skill", 0.3)
        elif kind == "trap":
            # place a trap on the ground at the aim (or facing) that triggers when
            # an enemy steps on it — delayed hazard.
            tx, ty = (wc.x + wc.facing * 60, wc.y)
            self._traps.append(Trap(tx, ty, skill, wc, self.particles))
            audio.play("skill", 0.3)
```

- [ ] **Step 4: Add the `SummonAlly` + `Trap` entity classes in `world_entities.py`** (or reuse the projectile pattern if simpler). `SummonAlly`: a temporary entity with a `dur` timer, auto-attacks nearby enemies at the AA cd, despawns on expiry. `Trap`: a ground entity that triggers (AoE damage + a particle burst) when an enemy enters its radius, then despawns. Add `self._summons = []` + `self._traps = []` to `WorldScene.__init__` + drive them in the update loop + draw them in the drawables.

- [ ] **Step 5: Run the verify command** → `A3 OK ...` + 20/20.

- [ ] **Step 6: Commit** `git commit -m "feat(skills): expand taxonomy (summon/beam/trap/innate) + new skills"`

---

### Task A4: Terrain + landmark + village + drop sprites

**Goal:** Add the pixel-art sprites for the new terrain (water, bridge), landmarks (statue/ruin/shrine/obelisk/rift-anchor), village buildings, and ground loot drops — used by Tasks C2 (ground loot) + C3 (terrain).

**Files:**
- Modify: `generate_assets.py` (add `draw_water_tile`/`draw_bridge_tile`/`draw_landmark`/`draw_village_building`/`draw_drop` — pixel-art) + the `main()` save loop (save the new sprites)
- Modify: `verify_assets.py` (assert the new sprites render)

**Acceptance Criteria:**
- [ ] `generate_assets.py` adds `draw_water_tile` (40×40, animated-tile-ready, biome-tinted blue with dithered ripples), `draw_bridge_tile` (40×40, wood planks over water), `draw_landmark` (per-kind: statue/ruin/shrine/obelisk/rift-anchor, ~80×80, pixel-art), `draw_village_building` (per-kind: house/shop/temple, ~60×60, pixel-art), `draw_drop` (per-kind: gold/potion/shard/equipment, ~16×16, pixel-art).
- [ ] The `main()` save loop writes the new sprites to `assets/` (water/bridge/landmark/village/drop subdirs or namespaced names — the implementer picks, but the loader paths in C2/C3 must match).
- [ ] All sprites render pixel-art (palette-locked, dithered, no AA), matching Task A1's aesthetic.
- [ ] Headless: `xvfb-run -a python3 verify_assets.py` exit 0 + the new sprite files exist.

**Verify:** `xvfb-run -a python3 -c "import os,pygame; os.environ['SDL_VIDEODRIVER']='dummy'; pygame.init(); pygame.display.set_mode((1,1)); import generate_assets as GA; GA.main(); from entities import load_image; import os.path as P; d='assets'; assert P.exists(P.join(d,'water.png')) or P.exists(P.join(d,'terrain','water.png')); print('A4 OK')"` → `A4 OK`

**Steps:**

- [ ] **Step 1: Add the draw helpers in generate_assets.py** — `draw_water_tile`, `draw_bridge_tile`, `draw_landmark(kind)`, `draw_village_building(kind)`, `draw_drop(kind)`. Each pixel-art (palette-locked, dithered, no AA), matching Task A1.

- [ ] **Step 2: Save the new sprites in `main()` (generate_assets.py:2520)** — add save calls for the water/bridge tiles (per biome tint), the 5 landmark kinds, the 3-4 village building kinds, the 4 drop kinds. Use a consistent path scheme (e.g. `assets/terrain/{name}.png`, `assets/landmarks/{kind}.png`, `assets/villages/{kind}.png`, `assets/drops/{kind}.png`).

- [ ] **Step 3: Add loaders in `entities.py`** — `load_terrain(name)`/`load_landmark(kind)`/`load_village(kind)`/`load_drop(kind)` routing through `load_image` (the existing cache pattern).

- [ ] **Step 4: Run the verify command** → `A4 OK` + `verify_assets.py` exit 0.

- [ ] **Step 5: Commit** `git commit -m "feat(art): pixel-art terrain/landmark/village/drop sprites"`

---

## Gate G1: Verify Batch A (asset overhaul)

**Goal:** A gate agent runs the full headless suite + the Batch A assertions and confirms the system is clean before the skill/combat batch.

**Files:** none (read-only verification)

**Acceptance Criteria:**
- [ ] `xvfb-run -a python3 verify_assets.py` exits 0 (all sprites render, sizes unchanged).
- [ ] `xvfb-run -a python3 /tmp/verify_complete.py` → 20/20 PASS.
- [ ] `xvfb-run -a python3 /tmp/verify_features.py` → 8/8 PASS.
- [ ] The A1/A2/A3/A4 verify commands all pass.
- [ ] A 1200-frame stress run completes with no exception.
- [ ] The pixel-art sprites render without crashing the world scene (boot → world → draw).

**Verify:** the gate agent runs all the above and reports PASS/FAIL per check; on FAIL, it lists the exact regression and the loop spawns a fix agent for that task before re-gating.

**Steps:**

- [ ] **Step 1:** Run `xvfb-run -a python3 verify_assets.py` → expect exit 0.
- [ ] **Step 2:** Run `xvfb-run -a python3 /tmp/verify_complete.py` → expect 20/20.
- [ ] **Step 3:** Run `xvfb-run -a python3 /tmp/verify_features.py` → expect 8/8.
- [ ] **Step 4:** Run the A1/A2/A3/A4 verify commands → all pass.
- [ ] **Step 5:** Run a 1200-frame stress (`xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); [g.scene.update(1/60,[]) for _ in range(1200)]; print('stress OK')"`) → no exception.
- [ ] **Step 6:** If any check fails, spawn a fix agent for the failing task, apply, re-run the gate. Cap at 3 fix iterations.

---

## Batch B — Skill system + combat fixes (world_scene.py hot paths)

### Task B1: Skill hover tooltips

**Goal:** On the world skill bar, hovering a skill slot shows a tooltip panel with the skill's name, type/category, element, energy cost, cooldown, description, and how-to-use — read from the `HERO_ASSETS` manifest.

**Files:**
- Modify: `world_scene.py:3936` (`_draw_skill_bar` — add hover detection + tooltip) + `__init__` (a `_tooltip_cache`)

**Acceptance Criteria:**
- [ ] `_draw_skill_bar` (world_scene.py:3936) detects hover on each skill slot (Q/W/E/R) via `collidepoint` with `pygame.mouse.get_pos()`.
- [ ] On hover, a tooltip panel draws above the slot: name, category badge, element, energy cost, cooldown, `description`, `how_to_use` — read from `HERO_ASSETS[wc.hero.id].skills[idx]`.
- [ ] The tooltip surface is cached per `(hero_id, idx, affordable)` to avoid per-frame text re-render; word-wrapped with the existing `text()` helper.
- [ ] The tooltip shows only when the slot is hovered + the player is idle (not mid-cast); it does not block clicks (display only).
- [ ] The tooltip does not overlap the boss HP bar (top-center) — draw it above the skill bar (bottom), growing upward.
- [ ] **Respects `reduce_motion`** — instant show, no fade.
- [ ] Headless: hover a skill slot, assert the tooltip panel is drawn (no crash); `HERO_ASSETS[hero].skills[idx]['description']` is non-empty.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main,data as D; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; wc=sc.party[sc.active]; a=D.HERO_ASSETS[wc.hero.id]; assert len(a['skills'])>=4 and all(s.get('description') for s in a['skills']); sc.draw(pygame.display.get_surface()); print('B1 OK', a['skills'][0]['name'])"` → `B1 OK <name>`

**Steps:**

- [ ] **Step 1: Add a `_tooltip_cache` to `WorldScene.__init__`** (world_scene.py ~894) — `self._tooltip_cache = {}` keyed by `(hero_id, idx, affordable)`.

- [ ] **Step 2: Add hover detection + tooltip draw in `_draw_skill_bar` (world_scene.py:3936)** — after drawing each slot, `mp = pygame.mouse.get_pos()`; if the slot rect `collidepoint(mp)`, build (or fetch from cache) the tooltip panel: a rounded rect above the slot with the name (bold), category badge, element dot, `cost` / `cd`, `description` (word-wrapped), `how_to_use`. Draw it above the slot (growing upward from the skill bar at the bottom). Cache by `(hero_id, idx, wc.can_skill(idx))`.

- [ ] **Step 3: Gate the tooltip on `reduce_motion`** — instant show (no fade) when `self._reduce_motion`.

- [ ] **Step 4: Run the verify command** → `B1 OK <name>` + 20/20.

- [ ] **Step 5: Commit** `git commit -m "feat(ui): skill hover tooltips (name/category/cost/desc/how-to-use)"`

---

### Task B2: Hold-to-aim preview

**Goal:** When holding a skill key (Q/W/E), show an aim reticle / AoE area preview before releasing. A quick tap fires instantly at the facing (legacy). Release fires at the aimed target.

**Files:**
- Modify: `world_scene.py:1636` (`_do_skill` — accept an optional `target=(x,y)` for ground-targeted AoE) + the event loop (line ~2477 — KEYDOWN/KEYUP Q/W/E → hold timer + aim mode) + the draw loop (draw the aim preview) + `__init__` (`_aim_skill`/`_aim_t`)

**Acceptance Criteria:**
- [ ] On KEYDOWN Q/W/E, start a hold timer; if held > 0.12s, enter aim mode (`_aim_skill = idx`, draw the preview). On KEYUP, fire the skill at the aimed target (mouse pos for ground-target AoE, facing for melee/beam).
- [ ] If held < 0.12s (tap), fire instantly at the facing (legacy behavior preserved).
- [ ] The preview draws by skill category: AoE = a circle at the mouse (clamped to the skill's max range from the hero), beam = a line from hero to mouse, ranged = a trajectory line, melee = an arc in the facing.
- [ ] `_do_skill` gains an optional `target=(x,y)` param for ground-targeted AoE (the AoE centers on `target` instead of the hero).
- [ ] **Aim mode does not block movement** (RMB still moves while aiming) + does not block skill cast.
- [ ] **Gate the preview animation on `reduce_motion`** — static reticle, no pulse.
- [ ] Headless: hold Q > 0.12s → `_aim_skill` is set + the preview draws; release → the skill fires at the target.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; sc._aim_skill=1; sc._aim_t=0.2; sc.draw(pygame.display.get_surface()); assert sc._aim_skill==1; print('B2 OK')"` → `B2 OK`

**Steps:**

- [ ] **Step 1: Add `_aim_skill`/`_aim_t` to `WorldScene.__init__`** (world_scene.py ~894) — `self._aim_skill = None; self._aim_t = 0.0`.

- [ ] **Step 2: In the event loop (world_scene.py ~2477)**, on KEYDOWN Q/W/E start the hold timer (don't fire yet); on KEYUP, if `_aim_t > 0.12` fire `_do_skill(wc, idx, target=mouse_world)` else fire `_do_skill(wc, idx)` (instant at facing). Track the hold in the update loop (`_aim_t += dt` while the key is held).

- [ ] **Step 3: Add the `target` param to `_do_skill` (world_scene.py:1636)** — `def _do_skill(self, wc, idx, target=None)`. For AoE skills, center the effect on `target` (clamped to max range) if provided, else the hero. For melee/beam, the facing (ignore `target`).

- [ ] **Step 4: Draw the aim preview in the draw loop** — if `_aim_skill is not None`, draw by the skill's category: AoE = circle at the mouse (clamped), beam = line, ranged = trajectory, melee = arc. Element-tinted. Gate the pulse on `reduce_motion`.

- [ ] **Step 5: Run the verify command** → `B2 OK` + 20/20.

- [ ] **Step 6: Commit** `git commit -m "feat(combat): hold-to-aim preview (tap=instant, hold=aim+release)"`

---

### Task B3: Auto-attack (AA) LoL-style

**Goal:** RMB on an enemy targets it and the hero auto-attacks continuously at the AA cooldown until the target dies or a new command is given; RMB on ground click-to-moves (clears the AA target). Keep J as a manual attack.

**Files:**
- Modify: `world_scene.py:2534` (the RMB handler — hit-test enemies; set `aa_target` or `move_target`) + the update loop (drive the AA) + `~1516` (`_do_attack` — accept an optional target enemy)
- Modify: `world_entities.py` (`WorldCharacter.__init__` — add `aa_target = None`; the update loop — move toward `aa_target` if out of range)

**Acceptance Criteria:**
- [ ] `WorldCharacter` has an `aa_target` field (a WorldEnemy ref or None).
- [ ] The RMB handler (world_scene.py:2534) hit-tests enemies at the click pos; if an enemy is hit, sets `wc.aa_target = enemy` (and moves toward it if out of range); else (ground) sets `wc.move_target` + clears `wc.aa_target` (existing click-to-move).
- [ ] In the update loop, if `wc.aa_target` is set, alive, and in range, auto-fire `_do_attack(wc, target=aa_target)` at the AA cooldown (0.32s); if out of range, move toward it (set `move_target` to the enemy's pos).
- [ ] `aa_target` clears when the target dies, the player issues a move (RMB ground), a skill cast, or a transition.
- [ ] J manual attack does not set `aa_target` (fires at facing, legacy).
- [ ] Headless: set `wc.aa_target` to an enemy in range, run 60 frames, assert `_do_attack` fired (the enemy took damage); RMB on ground clears `aa_target`.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; sc.enemies.clear(); sc._map_data['obstacles']=[]; import world_entities as WE; en=WE.WorldEnemy('slime',1); en.x,en.y=sc.party[sc.active].x+60,sc.party[sc.active].y; sc.enemies.append(en); hp0=en.enemy.hp; sc.party[sc.active].aa_target=en; [sc.update(1/60,[]) for _ in range(60)]; assert en.enemy.hp<hp0, f'no AA: {hp0}->{en.enemy.hp}'; print('B3 OK', hp0, en.enemy.hp)"` → `B3 OK <hp0> <lower>`

**Steps:**

- [ ] **Step 1: Add `aa_target` to `WorldCharacter.__init__`** (world_entities.py) — `self.aa_target = None`.

- [ ] **Step 2: Modify the RMB handler (world_scene.py:2534)** — on RMB, hit-test enemies at the click world-pos; if an enemy is hit, `wc.aa_target = en` (+ move toward it if out of range); else `wc.move_target = (world_x, world_y)` + `wc.aa_target = None` (existing click-to-move). Example:

```python
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                if wc and wc.alive:
                    ox, oy = self.camera.offset()
                    wx, wy = e.pos[0] + ox, e.pos[1] + oy
                    # LoL-style AA: RMB on an enemy targets it (auto-attack);
                    # RMB on ground click-to-moves (clears aa_target).
                    hit_en = None
                    for en in self.enemies:
                        if en.alive and math.hypot(en.x - wx, en.y - wy) < en.r + 12:
                            hit_en = en; break
                    if hit_en is not None:
                        wc.aa_target = hit_en
                    else:
                        wc.aa_target = None
                        wc.move_target = (wx, wy)
                        wc.move_target_t = 0.0; wc._last_mt_dist = 0.0; wc._mt_stall_t = 0.0
```

- [ ] **Step 3: Drive the AA in the update loop** (world_scene.py, the per-frame `wc` update) — if `wc.aa_target` is set + alive: if in range (`hypot < AA_RANGE`), auto-fire `_do_attack(wc, target=wc.aa_target)` at the AA cd (reuse `wc.atk_cd`); else move toward it (`wc.move_target = (aa_target.x, aa_target.y)`). If `aa_target` is dead/None, clear it.

- [ ] **Step 4: Add the `target` param to `_do_attack` (world_scene.py:1516)** — `def _do_attack(self, wc, target=None)`. For melee, if `target` is provided, aim the arc at `target.x/target.y` instead of `wc.x + wc.facing*40`. For ranged, aim the projectile at `target`. If `target` is None, legacy (facing).

- [ ] **Step 5: Clear `aa_target` on move (RMB ground — done in step 2), skill cast (in `_do_skill`/`_do_ultimate` set `wc.aa_target = None`), and transition (`_load_map` clears it).**

- [ ] **Step 6: Add `AA_RANGE` + `AA_CD` to data.py** — `AA_RANGE = 120; AA_CD = 0.32` (reuse the existing 0.32s `atk_cd`).

- [ ] **Step 7: Run the verify command** → `B3 OK <hp0> <lower>` + 20/20.

- [ ] **Step 8: Commit** `git commit -m "feat(combat): LoL-style auto-attack (RMB enemy=AA, RMB ground=move)"`

---

### Task B4: Mana regen fix + tune

**Goal:** Root-cause why the user still feels mana doesn't increase, then tune so mana visibly recovers. v1 added `ENERGY_REGEN_PCT=0.04` (4%/s out of combat, 2%/s in combat); the user reports it's still not felt.

**Files:**
- Modify: `world_entities.py:756` (the regen block — verify + tune) + `__init__` (the `_last_combat_t`/`_res_energy_regen` fields)
- Modify: `data.py:155` (`ENERGY_REGEN_PCT` — bump)

**Acceptance Criteria:**
- [ ] **Root cause found + documented** (systematic debugging): verify the regen runs every frame when `alive` + `energy < max_energy`; check the in-combat 0.5x multiplier (`_last_combat_t < 1.5`) isn't making it too slow; check the energy bar HUD animates the fill visibly. If there's a bug (the regen not called, or the combat-state gate too aggressive), fix it.
- [ ] `ENERGY_REGEN_PCT` is tuned to ~0.08 (8%/s out of combat, 4%/s in combat — full bar in ~12s out of combat) so mana visibly recovers.
- [ ] The energy bar HUD animates the fill (the fill width tracks `energy/max_energy`).
- [ ] The on-hit gains (`ENERGY_GAIN_BASIC=25`, `ENERGY_GAIN_DEAL=8`) stay (they reward aggression).
- [ ] Headless: load world, clear enemies, run 60 idle frames, assert `wc.hero.energy` increased from the start value; after 120 frames, assert `wc.hero.energy >= 90` (recovered to usable).

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; sc.enemies.clear(); sc._map_data['obstacles']=[]; wc=sc.party[sc.active]; wc.hero.energy=20; e0=wc.hero.energy; [sc.update(1/60,[]) for _ in range(60)]; assert wc.hero.energy>e0, f'no regen: {e0}->{wc.hero.energy}'; [sc.update(1/60,[]) for _ in range(120)]; assert wc.hero.energy>=90, f'stuck low: {wc.hero.energy}'; print('B4 OK', e0, round(wc.hero.energy,1))"` → `B4 OK <start> <>=90>`

**Steps:**

- [ ] **Step 1: Root-cause (systematic debugging)** — read the regen block (world_entities.py:756); confirm `self.alive` + `self.hero.energy < self.hero.max_energy` + the `rate` computation. Check `_last_combat_t` is updated on combat events (so the 0.5x in-combat multiplier clears after 1.5s). Reproduce headless: set `energy=20`, idle 60 frames, measure `energy`. If it doesn't increase, find the bug (e.g. the regen gated on a wrong field, or `_last_combat_t` never decays). Document the root cause.

- [ ] **Step 2: Tune `ENERGY_REGEN_PCT` (data.py:155)** — bump from 0.04 to 0.08 (8%/s out of combat, 4%/s in combat — full bar in ~12s out of combat). Keep the in-combat 0.5x multiplier but with the higher base it's still felt.

- [ ] **Step 3: Verify the energy bar HUD animates** — in `_draw_hud`/the skill bar, the energy fill width tracks `wc.hero.energy / wc.hero.max_energy`. If it doesn't animate (a static bar), fix it.

- [ ] **Step 4: Run the verify command** → `B4 OK <start> <>=90>` + 20/20.

- [ ] **Step 5: Commit** `git commit -m "fix(mana): tune energy regen to 8%/s + verify HUD animates the fill"`

---

## Gate G2: Verify Batch B (skill system + combat)

**Goal:** Gate agent runs the full headless suite after Batch B; on failure, spawn fix agents.

**Acceptance Criteria:**
- [ ] `xvfb-run -a python3 verify_assets.py` exit 0.
- [ ] `/tmp/verify_complete.py` 20/20 + `/tmp/verify_features.py` 8/8.
- [ ] All Batch B verify commands pass (B1-B4).
- [ ] 1200-frame stress, no exception; the combat loop is stable (AA doesn't double-fire, hold-to-aim doesn't block movement, mana regens).
- [ ] Benchmark: world ≥ ~60fps (`/tmp/bench_aetheria.py`).

**Steps:** same as G1, plus the benchmark. On FAIL, spawn a fix agent for the failing task; cap 3 iterations.

---

## Batch C — World enrichment (world_data.py + world_scene.py)

### Task C1: Remove fog motes (stray white circles)

**Goal:** Delete the `_fog_motes` (7 big soft circles, additive blend — the "stray white circles"). Keep the fog weather darkening (subtle flat overlay), remove the bright drifting circles.

**Files:**
- Modify: `world_scene.py:958` (`_fog_motes` init — remove) + `:3231` (the mote draw — remove)

**Acceptance Criteria:**
- [ ] `_fog_motes` init (world_scene.py:958) + draw (world_scene.py:3231) are removed.
- [ ] The fog weather darkening (`_fog_overlay`, line ~3370) stays — fog weather still darkens without the motes.
- [ ] The rain overlay + storm strikes stay (they're weather, not stray circles).
- [ ] Headless: boot → world → draw with fog weather, no crash, no bright mote circles.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; assert not hasattr(sc,'_fog_motes') or sc._fog_motes is None or len(sc._fog_motes)==0; sc._weather='fog'; sc.draw(pygame.display.get_surface()); print('C1 OK')"` → `C1 OK`

**Steps:**

- [ ] **Step 1: Remove the `_fog_motes` init (world_scene.py:958)** — delete the `self._fog_motes = [...]` block.

- [ ] **Step 2: Remove the mote draw (world_scene.py:3231)** — delete the `for fm in self._fog_motes: ...` draw block. Keep the `_fog_overlay` call (the flat darkening).

- [ ] **Step 3: Run the verify command** → `C1 OK` + 20/20.

- [ ] **Step 4: Commit** `git commit -m "fix(ui): remove stray fog-mote white circles"`

---

### Task C2: Ground loot drops

**Goal:** Enemy deaths + breakables drop loot as visible sprites on the ground (gold/potions/shards/equipment), walk over (magnet pickup radius) to collect. Replaces the "drops straight to inventory" with visible ground items.

**Files:**
- Modify: `world_scene.py:934` (`self.drops` — populate it) + `:2145` (enemy death — spawn drops) + `:1383` (breakable shatter — spawn drops) + the walk-over check (line ~2465 — pickup) + the draw loop (draw drops) + the update loop (magnet + expire)
- Modify: `generate_assets.py` (drop sprites — Task A4)

**Acceptance Criteria:**
- [ ] `self.drops` (world_scene.py:934) is populated on enemy death (line ~2145) + breakable shatter (line ~1383) with drop entities `{x, y, kind, value, t, sprite_id}`. Kinds: `gold`, `hp_potion`, `shard`, `equipment` — each a pixel-art sprite (Task A4).
- [ ] Drops draw in the depth-sorted drawables.
- [ ] Pickup: in the walk-over check, if `hypot(wc - drop) < 40` (magnet radius), collect (add to inventory) + a sparkle. Magnet: if the hero is within ~80px, pull the drop toward the hero.
- [ ] The drops list is capped (expire old drops after ~30s) so it doesn't pile up.
- [ ] Boss/elite drops richer (more gold, guaranteed shard/equipment).
- [ ] Headless: kill an enemy, assert a drop entity spawns; walk over it, assert it's collected + removed from `self.drops`.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; sc.enemies.clear(); sc._map_data['obstacles']=[]; import world_entities as WE; en=WE.WorldEnemy('slime',1); en.x,en.y=200,200; sc.enemies.append(en); en.enemy.hp=1; en.take_damage(999,0,0,False,on_attack=sc._on_enemy_event); assert len(sc.drops)>0, 'no drops'; d=sc.drops[0]; wc=sc.party[sc.active]; wc.x,wc.y=d['x'],d['y']; [sc.update(1/60,[]) for _ in range(5)]; assert len(sc.drops)==0, 'not picked up'; print('C2 OK', len(sc.drops))"` → `C2 OK 0`

**Steps:**

- [ ] **Step 1: Populate `self.drops` on enemy death (world_scene.py:2145)** — replace the "add gold/xp/shards directly to inventory" with: spawn drop entities on the ground at the enemy's pos (gold coins always; hp_potion 12%; shard 15% non-boss / 3+r*4 boss; equipment 60% boss first-clear). Keep the xp/gold add to inventory (xp is party-wide, instant) but spawn the visible gold/shard/potion/equipment drops. Each drop: `{x, y, kind, value, t: 0, sprite_id}`.

- [ ] **Step 2: Populate `self.drops` on breakable shatter (world_scene.py:1383)** — same pattern (the breakable loot spawns as drops).

- [ ] **Step 3: Add the pickup in the walk-over check (world_scene.py ~2465)** — for each drop, if `hypot(wc - drop) < 40`, collect (add `value` to inventory by `kind`) + a sparkle + remove from `self.drops`. Add a magnet: if `hypot < 80`, pull the drop toward the hero (`drop.x += (wc.x - drop.x) * dt * 8`).

- [ ] **Step 4: Draw the drops in the depth-sorted drawables** — blit the drop sprite (Task A4) at the drop's screen pos.

- [ ] **Step 5: Expire old drops** — in the update loop, `drop['t'] += dt`; if `drop['t'] > 30`, remove it (so the list doesn't pile up).

- [ ] **Step 6: Run the verify command** → `C2 OK 0` + 20/20.

- [ ] **Step 7: Commit** `git commit -m "feat(world): ground loot drops (walk-over pickup + magnet)"`

---

### Task C3: Terrain — water + bridges + landmarks + villages

**Goal:** Add water bodies (impassable, with bridges), named landmarks (one per biome), and villages (a small hub per biome with an NPC spawn point). Evaluate the 5 biomes + add what's missing.

**Files:**
- Modify: `world_data.py:358` (`gen_map` — add `water`/`bridges`/`landmark`/`village` to the return dict) + `~577` (the return dict)
- Modify: `world_scene.py` (water collision, bridge passable, landmark draw + lore float on first visit, village buildings draw + NPC spawn) + `__init__`/`_load_map` (the new fields)
- Modify: `generate_assets.py` (terrain/landmark/village sprites — Task A4)
- Modify: `data.py` (landmark lore lines, NPC data — Task E1)

**Acceptance Criteria:**
- [ ] `gen_map` (world_data.py:358) adds `water` (an impassable pool per map, biome-tinted) + `bridges` (passable tiles over water) + `landmark` (one per biome: statue/ruin/shrine/obelisk/rift-anchor) + `village` (a cluster of 3-5 buildings + an NPC spawn point) — all placed via `_free_grid` + the center-distance check so they don't block the corridor/edge-portal gaps. All included in the return dict (line ~577).
- [ ] Water is impassable (collision, like obstacles); bridges are passable.
- [ ] Landmarks are decorative (no collision) + show a lore float on first visit.
- [ ] Villages draw the buildings + spawn an NPC (Task E1 wires the NPC interact).
- [ ] **Water/landmarks/villages are static gen_map features** — the MapRenderer cache (keyed on (c,r)) stays intact.
- [ ] Headless: `gen_map` for a cell, assert `water`/`landmark`/`village` keys present; water rects don't overlap the edge-portal gaps.

**Verify:** `xvfb-run -a python3 -c "import world_data as WD; m=WD.gen_map(0,0); assert 'water' in m and 'landmark' in m and 'village' in m; assert 'bridges' in m; print('C3 OK', bool(m['water']), bool(m['landmark']), bool(m['village']))"` → `C3 OK ...`

**Steps:**

- [ ] **Step 1: Add `water`/`bridges`/`landmark`/`village` to `gen_map` (world_data.py:358)** — after the breakables (line ~509), add: a water pool (1-2 rects on free tiles, biome-tinted), bridges (passable tiles over the water), a landmark (one per biome kind, on a free tile), a village (a cluster of 3-5 buildings + an NPC spawn point on a free tile cluster). Gate all with `_free_grid` + `_dist(x, y, cx_mid, cy_mid) > TILE * 3` so they don't block the corridor/edge-portal gaps. Add to the return dict (line ~577): `water=water, bridges=bridges, landmark=landmark, village=village`.

- [ ] **Step 2: Add water collision + bridge passable in `world_scene.py`** — water rects go into the collision list (impassable, like obstacles); bridges are passable (excluded from collision). In `_load_map`, add the water rects to `self._map_data["obstacles"]` (or a separate `water` list the collision check reads).

- [ ] **Step 3: Draw the water/bridges/landmark/village in `world_scene.py`** — water (the tile sprite, Task A4, with a dithered shimmer), bridges (the plank sprite), landmark (the biome-kind sprite + a lore float on first visit — track visited landmarks in `p.ow_discovered` or a new set), village buildings (the building sprites). Draw in the depth-sorted drawables.

- [ ] **Step 4: Add the landmark lore lines to `data.py`** — `LANDMARK_LORE = {biome: "..."}` (5 entries, one per biome landmark).

- [ ] **Step 5: Run the verify command** → `C3 OK ...` + 20/20.

- [ ] **Step 6: Commit** `git commit -m "feat(world): water+bridges+landmarks+villages terrain"`

---

## Gate G3: Verify Batch C (world enrichment)

**Goal:** Gate agent runs the full headless suite after Batch C.

**Acceptance Criteria:**
- [ ] `verify_assets.py` exit 0; `/tmp/verify_complete.py` 20/20; `/tmp/verify_features.py` 8/8.
- [ ] All Batch C verify commands pass (C1-C3).
- [ ] 1200-frame stress, no exception; the MapRenderer cache is intact (water/landmarks/villages are static gen_map features; weather/rifts stay live overlays).
- [ ] Benchmark: world ≥ ~60fps.

**Steps:** same as G1 + the benchmark. On FAIL, spawn a fix agent; cap 3 iterations.

---

## Batch D — Adventure mode (new adventure_scene.py + main.py + player.py)

### Task D1: AdventureScene (wave-survival)

**Goal:** A new `AdventureScene`: select 4 chars, 10-min survival per stage, continuous waves (scaling with stage level), boss at 5 min, defeat the boss to advance to the next stage. Party wipe ends the run. Reuse the combat engine via a shared combat mixin.

**Files:**
- Create: `adventure_scene.py` (the `AdventureScene` + a `CombatMixin` extracting the combat methods from `WorldScene`)
- Modify: `world_scene.py` (extract `_do_attack`/`_do_skill`/`_do_ultimate`/`_on_enemy_hit`/`_on_enemy_death`/`_on_enemy_event` into the `CombatMixin`; `WorldScene` inherits it)
- Modify: `main.py:2190` (`_make_scene` — route to `AdventureScene` when `player.mode == "adventure"`)
- Modify: `player.py` (`adventure_best_stage`; save version 8)
- Modify: `data.py` (`ADVENTURE_WAVE_INTERVAL`, `ADVENTURE_BOSS_TIME`, `ADVENTURE_STAGE_LEVEL_STEP`)

**Acceptance Criteria:**
- [ ] `adventure_scene.py` defines `AdventureScene` with: a stage-start party select (pick 4 from roster, locked for the run — Task D2), a 10-min timer HUD, a wave spawner (enemies spawn from arena edges every ~25s, count + level scale with stage level + elapsed time), a boss at the 5-min mark (a row boss scaled to stage level), stage-clear on boss defeat (advance to next stage, level +5, full heal party), run-end on party wipe.
- [ ] The combat methods (`_do_attack`/`_do_skill`/`_do_ultimate`/`_on_enemy_hit`/`_on_enemy_death`/`_on_enemy_event`) are extracted into a `CombatMixin` that both `WorldScene` and `AdventureScene` inherit — no duplication.
- [ ] `_make_scene` (main.py:2190) routes to `AdventureScene` when `player.mode == "adventure"`.
- [ ] `player.py` adds `adventure_best_stage = 0`; save version bumped to 8 with migration.
- [ ] `data.py` adds `ADVENTURE_WAVE_INTERVAL=25`, `ADVENTURE_BOSS_TIME=300`, `ADVENTURE_STAGE_LEVEL_STEP=5`.
- [ ] Headless: enter adventure, run 60 frames, assert the timer ticks + waves spawn; fast-forward to 5 min, assert the boss spawns; defeat the boss, assert stage advances.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.player.mode='adventure'; g.goto('world'); sc=g.scene; assert sc.__class__.__name__=='AdventureScene'; t0=sc._stage_t; [sc.update(1/60,[]) for _ in range(60)]; assert sc._stage_t>t0; print('D1 OK', sc.__class__.__name__, round(sc._stage_t,1))"` → `D1 OK AdventureScene <t>`

**Steps:**

- [ ] **Step 1: Extract the combat methods into a `CombatMixin`** in `world_scene.py` — move `_do_attack`/`_do_skill`/`_do_ultimate`/`_on_enemy_hit`/`_on_enemy_death`/`_on_enemy_event`/`_element_mult`/`_compute_resonances` into a `class CombatMixin:` that `WorldScene` inherits. Keep the `WorldScene` behavior unchanged (no regression — the 20/20 suite stays green).

- [ ] **Step 2: Create `adventure_scene.py`** — `class AdventureScene(CombatMixin, Scene)` with: `__init__` (the stage state: `_stage_t=0`, `_stage=player.adventure_best_stage`, `_wave_t=0`, `_boss_spawned=False`, the party from `player.team`), a 10-min timer, a wave spawner (every `ADVENTURE_WAVE_INTERVAL`s, spawn `4 + stage + elapsed/60` enemies from the arena edges at level `stage * ADVENTURE_STAGE_LEVEL_STEP + elapsed/120`), a boss at `_stage_t >= ADVENTURE_BOSS_TIME` (a row boss scaled to stage level), stage-clear on boss defeat (advance + full heal + `player.adventure_best_stage = max(..., stage+1)`), run-end on party wipe (return to title). Reuse the arena map (a fixed biome layout via `gen_map(0,0)`). Draw the timer + wave counter HUD.

- [ ] **Step 3: Route `_make_scene` (main.py:2190)** — `elif name == "world": if self.player.mode == "adventure": return AdventureScene(self) else: return _get_world_scene_cls()(self)`.

- [ ] **Step 4: Add `adventure_best_stage` + save v8 to `player.py`** — `self.adventure_best_stage = 0`; add to the save dict (line ~414) + load (`d.get("adventure_best_stage", 0)`); bump `version` to 8.

- [ ] **Step 5: Add the `ADVENTURE_*` constants to `data.py`** — `ADVENTURE_WAVE_INTERVAL=25`, `ADVENTURE_BOSS_TIME=300`, `ADVENTURE_STAGE_LEVEL_STEP=5`.

- [ ] **Step 6: Run the verify command** → `D1 OK AdventureScene <t>` + 20/20.

- [ ] **Step 7: Commit** `git commit -m "feat(mode): AdventureScene (10-min wave-survival, boss at 5 min, stage ladder)"`

---

### Task D2: Party system (adventure fixed-4, endless live-swap)

**Goal:** Adventure locks the 4-char party at stage start (no roster changes mid-run), 1-4 swap allowed. Endless keeps full live swap + roster changes.

**Files:**
- Modify: `player.py` (`mode` field — `"adventure"`/`"endless"`, default `"endless"`; save v8)
- Modify: `main.py:413` (`RosterScene` — disable team add/remove when `player.mode == "adventure"`)
- Modify: `adventure_scene.py` (the stage-start party select — lock the 4 ids)

**Acceptance Criteria:**
- [ ] `player.py` adds `self.mode = "endless"` (default); `mode` persists in the save (v8).
- [ ] `AdventureScene` (D1) locks the 4-char team at stage start (the player picks 4 from the roster; the team is fixed for the run).
- [ ] `RosterScene` (main.py:413) disables team add/remove (the "Team Full!" / add/remove buttons) when `player.mode == "adventure"`; shows "locked for the run".
- [ ] The 1-4 swap in adventure changes only the active index (the existing `_switch`), not the roster.
- [ ] Endless stays unchanged (full live swap + roster changes).
- [ ] Headless: set `mode="adventure"`, assert `RosterScene` refuses team edits; the 1-4 swap still works.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.player.mode='adventure'; g.goto('roster'); sc=g.scene; assert g.player.mode=='adventure'; print('D2 OK', g.player.mode)"` → `D2 OK adventure`

**Steps:**

- [ ] **Step 1: Add the `mode` field to `player.py`** — `self.mode = "endless"` (default); add to the save dict + load (`d.get("mode", "endless")`); save v8 (with D1).

- [ ] **Step 2: Lock the team in `AdventureScene` (adventure_scene.py)** — at stage start, `self.player.set_team(chosen_4)`; store the locked ids; refuse roster changes mid-run.

- [ ] **Step 3: Disable team edits in `RosterScene` (main.py:413)** — when `self.game.player.mode == "adventure"`, the add/remove hero buttons are disabled (greyed + "locked for the run"); the 1-4 swap is not in the roster (it's in-world).

- [ ] **Step 4: Run the verify command** → `D2 OK adventure` + 20/20.

- [ ] **Step 5: Commit** `git commit -m "feat(meta): party system (adventure fixed-4, endless live-swap)"`

---

### Task D3: Title screen mode selector

**Goal:** Replace the single "Enter World" button with a mode selector: "Adventure" / "Endless". Sets `player.mode` and routes to the right scene.

**Files:**
- Modify: `main.py:333` (`TitleScene` — replace "Enter World" with two buttons) + `:383` (the click handlers)
- Modify: `player.py` (`mode` — set on click; persist)

**Acceptance Criteria:**
- [ ] `TitleScene` (main.py:333) replaces the "Enter World" button (line ~346) with two buttons: "Adventure" (with a one-line description "10-min wave survival") + "Endless" ("open world + story").
- [ ] On click, set `player.mode` + route to `AdventureScene` or `WorldScene` (via `goto("world")` which routes by `mode`).
- [ ] The meta menus (Heroes/Summon/Shop/Codex/Records/Settings) stay accessible from both modes.
- [ ] `player.mode` persists in the save.
- [ ] Headless: click "Adventure" → `mode == "adventure"` + `AdventureScene`; click "Endless" → `mode == "endless"` + `WorldScene`.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('title'); sc=g.scene; assert any('Adventure' in (b.text if hasattr(b,'text') else '') for b in sc.buttons); print('D3 OK')"` → `D3 OK`

**Steps:**

- [ ] **Step 1: Replace the "Enter World" button in `TitleScene` (main.py:346)** with two buttons:

```python
        self.buttons = [
            Button((WIDTH // 2 - 240, 300, 220, 56), "Adventure", (120, 60, 40), (200, 100, 60)),
            Button((WIDTH // 2 + 20, 300, 220, 56), "Endless", (70, 120, 90), (110, 180, 130)),
            Button((WIDTH // 2 - 120, 364, 240, 56), "Heroes", (90, 80, 50), (160, 130, 70)),
            # ... rest unchanged (Summon/Shop/Codex/Records/Settings)
        ]
```

- [ ] **Step 2: Add the click handlers (main.py:383)** — `if self.buttons[0].clicked(e): self.game.player.mode = "adventure"; self.game.player.save(); self.game.goto("world")` + `if self.buttons[1].clicked(e): self.game.player.mode = "endless"; self.game.player.save(); self.game.goto("world")`. Shift the remaining button indices (Heroes→2, Summon→3, etc.).

- [ ] **Step 3: Draw the one-line descriptions under each mode button** (in `TitleScene.draw`) — "10-min wave survival" under Adventure, "Open world + story" under Endless.

- [ ] **Step 4: Run the verify command** → `D3 OK` + 20/20.

- [ ] **Step 5: Commit** `git commit -m "feat(ui): title screen Adventure/Endless mode selector"`

---

## Gate G4: Verify Batch D (adventure mode)

**Goal:** Gate agent runs the full headless suite after Batch D.

**Acceptance Criteria:**
- [ ] `verify_assets.py` exit 0; `/tmp/verify_complete.py` 20/20; `/tmp/verify_features.py` 8/8.
- [ ] All Batch D verify commands pass (D1-D3).
- [ ] 1200-frame stress in BOTH modes (adventure + endless), no exception.
- [ ] Save round-trip (load → save → reload) with the v8 migration.
- [ ] Benchmark: world ≥ ~60fps.

**Steps:** same as G1 + the dual-mode stress + save round-trip. On FAIL, spawn a fix agent; cap 3 iterations.

---

## Batch E — Endless story (data.py + world_scene.py + main.py)

### Task E1: NPCs + dialogue

**Goal:** Add NPCs in villages (one per biome) with dialogue text boxes. Walk up + press F to interact. The NPC gives the biome's quest (Task E2) + reveals lore.

**Files:**
- Modify: `data.py` (add `NPCS` dict — 1 per biome, `{name, village_cell, dialogue, quest_id}`; `DIALOGUE` trees)
- Modify: `world_scene.py` (NPC spawn at the village (from C3), interact on F, dialogue text box)
- Modify: `main.py` (the quest tracker — show the active NPC quest, Task E3)

**Acceptance Criteria:**
- [ ] `data.py` defines `NPCS = {biome: {name, village_cell, dialogue, quest_id}}` (5 NPCs, one per biome) + `DIALOGUE = {npc_id: [lines]}` (dialogue trees revealing the world's story).
- [ ] `world_scene.py` spawns the NPC at the village (from C3's `village` spawn point); on walk-up + F, shows a dialogue text box with the NPC's lines + a dismiss.
- [ ] The dialogue does not block the action (a text box with a dismiss key).
- [ ] Headless: `python3 -c "import data as D; assert len(D.NPCS)>=5; assert all('dialogue' in v for v in D.NPCS.values()); print('E1 OK', len(D.NPCS))"` → `E1 OK 5`.

**Verify:** the headless assertion + `xvfb-run -a python3 /tmp/verify_complete.py` → 20/20.

**Steps:**

- [ ] **Step 1: Add `NPCS` + `DIALOGUE` to `data.py`** — 5 NPCs (one per biome: plains/forest/cave/castle/void), each `{name, village_cell, dialogue, quest_id}`. `DIALOGUE` trees (3-5 lines per NPC revealing the world's story + the biome boss quest).

- [ ] **Step 2: Spawn the NPC + interact in `world_scene.py`** — in `_load_map`, if the cell has a village (from C3), spawn the NPC at the village's spawn point (a `WorldNPC` or a simple entity). On walk-up + F (a new key binding), show a dialogue text box with the NPC's `DIALOGUE` lines + a dismiss (F/Esc). The dialogue box is a rounded rect at the bottom with the NPC name + the current line + a "▶" advance.

- [ ] **Step 3: Run the verify command** → `E1 OK 5` + 20/20.

- [ ] **Step 4: Commit** `git commit -m "feat(story): NPCs in villages + dialogue text boxes"`

---

### Task E2: Main quest chain + boss gating

**Goal:** A main quest chain (5 biome bosses → Demon King) with quest givers (the NPCs from E1). Gate each biome boss behind its quest (the boss cell locks until the biome quest is accepted + the area explored) so the boss is not "at the start".

**Files:**
- Modify: `data.py` (add `STORY_QUESTS` — the main chain: 5 biome-boss quests + 1 final-boss quest, each `{id, name, giver, objective, reward, lore}`)
- Modify: `world_scene.py` (gate the boss cell on the biome quest; the boss-defeat handler advances the story quest) + `__init__`/`_load_map` (the story state)

**Acceptance Criteria:**
- [ ] `data.py` defines `STORY_QUESTS = [5 biome-boss quests + 1 final-boss quest]`, each `{id, name, giver (NPC biome), objective (defeat the biome boss), reward, lore}`.
- [ ] The boss cell (column 9 per row) locks until the biome's quest is accepted (the NPC gives it) + the area explored (the player has visited the biome). The boss doesn't spawn / the boss arena is sealed until the quest is active.
- [ ] The boss-defeat handler (world_scene.py ~2215) advances the story quest (marks the biome-boss quest complete, unlocks the next).
- [ ] The gate does not block exploration (gate on quest acceptance + area exploration, not completion).
- [ ] Headless: `python3 -c "import data as D; assert len(D.STORY_QUESTS)>=6; print('E2 OK', len(D.STORY_QUESTS))"` → `E2 OK 6`.

**Verify:** the headless assertion + 20/20.

**Steps:**

- [ ] **Step 1: Add `STORY_QUESTS` to `data.py`** — 6 quests (5 biome-boss + 1 final), each `{id, name, giver, objective, reward, lore}`. The giver is the biome's NPC (from E1).

- [ ] **Step 2: Gate the boss cell in `world_scene.py`** — in `_load_map`, if the cell is a boss cell (`is_boss_cell`) + the biome's story quest isn't active (not accepted via the NPC), seal the boss arena (don't spawn the boss; show a "sealed — seek the <biome> NPC" float). Once the quest is active + the area explored, spawn the boss.

- [ ] **Step 3: Advance the story quest on boss defeat (world_scene.py ~2215)** — when the biome boss dies, mark the biome-boss quest complete + unlock the next story quest.

- [ ] **Step 4: Track the story state in `player.py`** — `story_progress = {}` (quest_id → status); add to the save (v8) + load.

- [ ] **Step 5: Run the verify command** → `E2 OK 6` + 20/20.

- [ ] **Step 6: Commit** `git commit -m "feat(story): main quest chain + boss gating (not at the start)"`

---

### Task E3: Quest tracker enhancement (story chain)

**Goal:** Enhance the in-world quest tracker (v1 #20) to show the main story quest chain + the active NPC quest, so the player knows where to go next.

**Files:**
- Modify: `world_scene.py:2564` (`_draw_hud` — the quest tracker shows the active story quest + the NPC quest) + the `_nearest_objective` (point to the active story target)
- Modify: `main.py` (the quest tracker / quest tab — show the story chain)

**Acceptance Criteria:**
- [ ] The quest tracker (world_scene.py ~2564) shows the active story quest's name + objective (e.g. "Defeat the Forest Boss — seek the Forest NPC") + a progress hint.
- [ ] The compass (`_nearest_objective`) points to the active story target (the biome NPC's village, or the boss cell once the quest is active).
- [ ] The quest tab (main.py) shows the story chain (5 biome-boss quests + the final, with complete/active/locked state).
- [ ] Headless: with an active story quest, assert the tracker draws + the compass points to the target (no crash).

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; sc.draw(pygame.display.get_surface()); print('E3 OK')"` → `E3 OK`

**Steps:**

- [ ] **Step 1: Show the active story quest in the quest tracker (world_scene.py ~2564)** — the top-right panel shows the active `STORY_QUESTS` entry's name + objective + a "seek the <biome> NPC" hint when the quest is accepted but the boss isn't reachable yet.

- [ ] **Step 2: Point the compass to the story target (world_scene.py `_nearest_objective`)** — if a story quest is active, point to the biome NPC's village (or the boss cell once the quest is active + the area explored). Fall back to the existing (un-cleared boss / undiscovered edge) when no story quest is active.

- [ ] **Step 3: Show the story chain in the quest tab (main.py)** — the quest/records scene lists the 6 story quests with complete/active/locked state.

- [ ] **Step 4: Run the verify command** → `E3 OK` + 20/20.

- [ ] **Step 5: Commit** `git commit -m "feat(ui): quest tracker shows the story chain + compass to the story target"`

---

## Gate G5: Final verify (whole system, both modes)

**Goal:** The final gate agent runs the complete headless suite + the v2 assertions + a manual-play checklist for both modes; the loop stops only when this passes cleanly.

**Files:** none (read-only)

**Acceptance Criteria:**
- [ ] `xvfb-run -a python3 verify_assets.py` exit 0 (pixel-art sprites, new terrain/landmark/village/drop sprites).
- [ ] `/tmp/verify_complete.py` 20/20 + `/tmp/verify_features.py` 8/8.
- [ ] All Batch verify commands (A1-A4, B1-B4, C1-C3, D1-D3, E1-E3) pass.
- [ ] v2 assertions: mana regen (idle 60 frames, `hero.energy` increases), AA (RMB on enemy sets `aa_target`, auto-fires), hold-to-aim (hold Q > 0.12s shows preview, release fires), ground loot (enemy death spawns a drop, walk-over collects), adventure (10-min timer, waves, boss at 5 min), mode selector (title → adventure → AdventureScene; title → endless → WorldScene), skill tooltip (hover shows the panel).
- [ ] 1200-frame stress in BOTH modes, no exception; benchmark world ≥ ~60fps.
- [ ] Save round-trip (load → save → reload) with the v8 migration.
- [ ] Manual: `python3 generate_assets.py && python3 main.py` → title → pick Adventure / Endless → play (pixel-art, AA, hold-to-aim, tooltips, ground loot, water/landmarks/villages, NPCs/story, adventure waves).

**Steps:**

- [ ] **Step 1:** Run all the headless checks; collect PASS/FAIL per check.
- [ ] **Step 2:** On any FAIL, spawn a fix agent for the failing task; apply; re-gate. Cap at 3 fix iterations per failing task; if a task fails 3×, escalate (question the approach, don't keep patching).
- [ ] **Step 3:** When all checks pass, report the final summary (14 enhancements shipped, all gates green, both modes playable) + commit a final merge commit.

---

## Self-review notes (planner)

- **Spec coverage:** every spec enhancement (#1-#14) maps to a task. #1 pixel-art → A1; #2 manifest → A2; #3 taxonomy → A3; #4 tooltips → B1; #5 hold-to-aim → B2; #6 AA → B3; #7 mana → B4; #8 fog motes → C1; #9 ground loot → C2; #10 terrain → C3 (+ A4 sprites); #11 AdventureScene → D1; #12 endless story → E1/E2/E3; #13 party → D2; #14 title selector → D3. No gaps.
- **Type consistency:** `HERO_ASSETS`, `PIXEL`/`PIXEL_PALETTE`, `aa_target`, `AA_RANGE`/`AA_CD`, `_aim_skill`/`_aim_t`, `self.drops` (drop entities), `water`/`bridges`/`landmark`/`village` (gen_map keys), `NPCS`/`DIALOGUE`/`STORY_QUESTS`, `story_progress`, `mode`/`adventure_best_stage`, `ADVENTURE_WAVE_INTERVAL`/`ADVENTURE_BOSS_TIME`/`ADVENTURE_STAGE_LEVEL_STEP`, `SummonAlly`/`Trap`, `CombatMixin` — names are consistent across tasks.
- **Shared-file batching:** `world_scene.py` is the hot file — Batch B (skill/AA region ~1516-2564), Batch C (world/draw region ~934-3231), Batch E (NPC/story region ~2215-2564) each own a distinct region; Batch A is generate_assets.py + data.py; Batch D is the new adventure_scene.py + main.py routing. The gate between batches catches any merge conflict.
- **Init-order traps:** B1 (`_tooltip_cache`), B2 (`_aim_skill`/`_aim_t`), B3 (`aa_target`), C3 (water/village fields) declare in `__init__` before `_load_map` (called out in the steps).
- **reduce_motion / high_contrast:** B1 (tooltip instant), B2 (static reticle) respect `reduce_motion` (called out).
- **Save migration:** D1/D2 bump to v8; the rest use existing fields or static data.
- **Pure-procedural:** all new art via generate_assets.py (pixel-art), all new audio via audio.py numpy (no new audio in v2 — the v1 audio set ships).
- **Cached-map model:** C3 water/landmarks/villages are static gen_map features (cache-safe); weather/rifts stay live overlays.
- **Both modes:** D1/D2/D3 + G4/G5 verify BOTH modes (adventure + endless) so neither regresses.
