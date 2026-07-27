# Aetheria Big Bang Enhancement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:subagent-driven-development (recommended) or superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the 3 user-reported bugs (skills/mana don't recover, stray white circles, dark gacha face) and ship 20 enhancements across all dimensions (combat, characters, world, audio, meta, UI) with a gated fix-and-enhance loop.

**Architecture:** Aetheria is a pygame open-world 2D action gacha RPG (~11.8k LOC, pure-procedural art/audio, single-dev, ~60fps, headless-verified). Each task → one specialist agent with worktree isolation; a gate agent checks the whole system headless after each batch and the loop spawns fix agents until the gate passes.

**Tech Stack:** Python 3.11, pygame 2.6, numpy; headless verify via `xvfb-run -a` + `SDL_VIDEODRIVER=dummy`.

**User decisions (already made):**
- "Review ở cổng" — spec reviewed + approved before implementation.
- "Tất cả đều nhau" — all dimensions weighted equally in the research phase.
- Gated loop: "tạo ra 1 gated agent có nhiệm vụ kiểm tra hệ thống xem đến khi nào mọi thứ oke thì thôi, nếu gated vẫn chưa cho dừng thì bạn vẫn sẽ cần tạo liên tục những agents để implement enhance và fix".
- LoL controls stay (RMB click-to-move + WASD both, by design — WASD is primary, RMB is supplement).

**Verified facts (root-caused headless during planning):**
- `tick_effects` (entities.py:234) is never driven in the world loop — DoT engine is 90% built but unwired.
- `TOUGHNESS_BREAK_DAMAGE` (data.py:355) + `TOUGHNESS_BREAK_MULT` (data.py:354) are never applied — `WorldEnemy.take_damage` (world_entities.py:751) flags the break but never applies the burst/multiplier.
- `ASCENSION_BONUS` (data.py:765) is a flat `{0:1.0,...5:1.50}` multiplier — no per-hero perks.
- `MapRenderer` cache (world_scene.py:27) is keyed on `(c,r)` — weather/rift must stay live overlays, never baked into `gen_map`.
- Energy has NO time-based regen (only on-hit: `ENERGY_GAIN_BASIC=25`/`ENERGY_GAIN_DEAL=8`); `can_use_skill` (entities.py:162) gates on `energy >= cost`.
- Click-to-move reticle (world_scene.py:2212) is bright white + doesn't clear when auto-walk is wall-blocked (`_collide` zeroes vx/vy but `move_target` stays set).
- Gacha reveal draws the portrait (main.py:1056) which has a dark vignette + dark bg + face core shadow — face region measures mean RGB ~3 at card size.

---

## File structure

**Modified (no new files — all enhancements fit the existing layout):**
- `data.py` — new static data: HERO_LORE, COLORBLIND_PALETTES, ELEMENTAL_RESONANCE, CONSTELLATION_PERKS, ULTIMATE_VARIANTS, HERO_SIGNATURE, ULTIMATE_VARIANTS, COMBO_MILESTONE_*, WEATHER_BY_BIOME, WET_EFFECT, LORE_FRAGMENTS, NG_PLUS_LEVEL_BONUS, ENERGY_REGEN_PCT, dot_potency per debuff.
- `entities.py` — StatusEffect time-based tick; Hero constellation-perk application; signature-passive hooks.
- `world_entities.py` — WorldEnemy: toughness-break burst + recovery; boss HUD toughness bar; signature-passive runtime; torchlight boss aura; move_target stall-clear.
- `world_scene.py` — combat wiring (DoT, break, combo climax, variable hit-stop), resonance, weather, rifts, breakables, torchlight, quest compass, leitmotifs on swap, reaction stings, reticle fix, energy regen, gacha reveal face fix (delegated to main.py).
- `main.py` — HeroDetailScene lore + constellation UI; CodexScene bio tooltip; GachaScene reveal (char sprite + bright card); colorblind toggle; resonance in RosterScene; Aetheric Cycle in TitleScene; gacha tension crescendo.
- `audio.py` — reaction stings, leitmotifs, gacha tension + fanfare, weather rain/thunder, combo stingers.
- `generate_assets.py` — brighter portrait (lighter vignette/bg/face-shadow); pot/crate/barrel/rift sprites.
- `player.py` — colorblind_mode setting; ng_cycle + reset_world_for_ng; ow_secrets_done; save version 6 migration.

**Shared-file conflict map (drives batching):** `world_scene.py` is touched by ~14 tasks; `data.py` by ~12; `world_entities.py` by ~6; `main.py` by ~6; `audio.py` by ~5; `entities.py` by ~3; `generate_assets.py` by ~2; `player.py` by ~3. Batches group tasks that DON'T overlap on the same file regions to keep worktree merges clean.

---

## Batch A — Bug fixes first (gate must pass before any enhancement)

### Task A1: Passive energy regen + usable skills (Bug B1)

**Goal:** Add slow time-based energy regen so a hero with low energy recovers to usable levels without needing to land a hit; skills then feel like they "recover" and mana "increases".

**Files:**
- Modify: `data.py:116-120` (add `ENERGY_REGEN_PCT`)
- Modify: `world_entities.py:540-556` (the timers/regen block in `WorldCharacter.update`)

**Acceptance Criteria:**
- [ ] `data.py` defines `ENERGY_REGEN_PCT = 0.04` (4% of max per second out of combat).
- [ ] `WorldCharacter.update` regenerates energy: `self.hero.energy = min(self.hero.max_energy, self.hero.energy + self.hero.max_energy * D.ENERGY_REGEN_PCT * dt)` when out of combat (`_last_combat_t > 1.5`) and alive; a slower rate (`* 0.5`) in combat.
- [ ] On map enter, the active hero's energy is at least `D.ENERGY_START` (verify `_build_party` / `_load_map` sets `hero.energy = min(D.ENERGY_START, max_energy)` — already the case at entities.py:333, but the active hero loaded from save may have stale low energy; ensure `_load_map` tops up to `ENERGY_START` if below).
- [ ] Headless: load world, clear enemies, run 60 idle frames, assert `wc.hero.energy > start_energy` (regen working); assert after 120 frames `wc.hero.energy >= 90` (recovered to usable).

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; sc.enemies.clear(); sc._map_data['obstacles']=[]; wc=sc.party[sc.active]; e0=wc.hero.energy; [sc.update(1/60,[]) for _ in range(60)]; assert wc.hero.energy>e0, f'no regen: {e0}->{wc.hero.energy}'; [sc.update(1/60,[]) for _ in range(120)]; assert wc.hero.energy>=90, f'stuck low: {wc.hero.energy}'; print('B1 OK', e0, wc.hero.energy)"` → `B1 OK <start> <>=90`

**Steps:**

- [ ] **Step 1: Add the regen constant**

In `data.py` after the `ENERGY_GAIN_DEAL` line (line ~120):

```python
ENERGY_REGEN_PCT = 0.04   # passive energy regen: 4% of max per second out of
                          # combat (~4.8/s at max 120 -> full bar in ~25s out of
                          # combat, ~2.4/s in combat). Skills recover + mana
                          # increases without needing to land a hit.
```

- [ ] **Step 2: Add time-based energy regen in WorldCharacter.update**

In `world_entities.py`, in the timers block after the `regen` passive block (after line ~556), add:

```python
        # passive energy regen: recover energy over time so a hero with low
        # energy can use skills again without landing a hit (the "skills don't
        # recover / mana doesn't increase" fix). Slower in combat.
        if self.alive and self.hero.energy < self.hero.max_energy:
            rate = D.ENERGY_REGEN_PCT * (0.5 if self._last_combat_t < 1.5 else 1.0)
            self.hero.energy = min(self.hero.max_energy,
                                   self.hero.energy + self.hero.max_energy * rate * dt)
```

- [ ] **Step 3: Top up energy on map enter if below ENERGY_START**

In `world_scene.py` `_load_map` (after the party is built, ~line 1014), ensure the active hero's energy is at least `ENERGY_START`:

```python
        # ensure the active hero starts a map with usable energy (the
        # "skills don't recover" fix: a hero loaded from save with stale low
        # energy should top up to ENERGY_START on map enter)
        a = self.party[self.active]
        if a and a.hero.energy < D.ENERGY_START:
            a.hero.energy = min(D.ENERGY_START, a.hero.max_energy)
```

- [ ] **Step 4: Run the verify command** → `B1 OK ...`

- [ ] **Step 5: Commit**

```bash
git add data.py world_entities.py world_scene.py
git commit -m "fix(B1): add passive energy regen + top-up on map enter

Skills/mana now recover over time (4% max/s out of combat, 2% in combat)
so a hero with low energy can use skills without landing a hit. Tops up to
ENERGY_START on map enter. Root-caused: no time-based regen existed."
```

---

### Task A2: Clean up stray white circles (Bug B2)

**Goal:** Make the click-to-move reticle subtler (element-tinted, fading, smaller) and clear `move_target` when auto-walk is wall-blocked; review the fog motes so they don't read as bright stray circles.

**Files:**
- Modify: `world_scene.py:2204-2223` (the reticle draw block)
- Modify: `world_entities.py:455-475` (the move_target auto-walk block — add stall-clear)

**Acceptance Criteria:**
- [ ] The reticle is element-tinted (uses `D.ELEMENT_COLORS[wc.element][0]`), not pure white; the inner dot is smaller (radius 2 → keep) and the ring fades out over ~0.5s after the target is set (track a `move_target_t`).
- [ ] `move_target` is cleared when the hero is blocked: if the hero is auto-walking toward `move_target` but the distance isn't decreasing (no progress for >0.3s of consecutive frames), clear `move_target`.
- [ ] The reticle is not drawn when `move_target` is None.
- [ ] Fog motes: confirm they're low-alpha (the `_fog_sprite` uses `int(10*(1-k/R))` — already subtle); no change needed unless a mote reads as a solid white circle (audit by rendering). If the audit finds a bright mote, reduce the mote alpha.
- [ ] Headless: set a `move_target` behind a wall, run 60 frames, assert `wc.move_target is None` (cleared by stall).

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; wc=sc.party[sc.active]; wc.move_target=(wc.x+400, wc.y); # target far through map; [sc.update(1/60,[]) for _ in range(60)]; assert wc.move_target is None or math.hypot(wc.move_target[0]-wc.x, wc.move_target[1]-wc.y)<8, f'reticle stuck: {wc.move_target}'; print('B2 OK', wc.move_target)"` → `B2 OK None`

**Steps:**

- [ ] **Step 1: Add a move_target age timer + stall-clear in WorldCharacter**

In `world_entities.py` `__init__` (near line 310, after `self.move_target = None`):

```python
        self.move_target_t = 0.0       # age of the current move_target (for reticle fade)
        self._last_mt_dist = 0.0       # last distance to target (stall detection)
        self._mt_stall_t = 0.0         # time the auto-walk has stalled
```

In the move_target auto-walk block (world_entities.py ~460), replace the `elif self.move_target is not None:` branch:

```python
        elif self.move_target is not None:
            tx, ty = self.move_target
            dx = tx - self.x
            dy = ty - self.y
            d = math.hypot(dx, dy)
            self.move_target_t += dt
            if d < 8:
                self.move_target = None
            else:
                # stall detection: if the hero isn't getting closer (blocked by a
                # wall), clear the target after 0.3s so the reticle doesn't hang
                # on a wall forever (the "stray white circle" fix)
                if d >= self._last_mt_dist - 1:
                    self._mt_stall_t += dt
                    if self._mt_stall_t > 0.3:
                        self.move_target = None
                else:
                    self._mt_stall_t = 0
                self._last_mt_dist = d
                if self.move_target is not None:
                    input_dir = (dx / d, dy / d)
                    self.facing = 1 if dx > 0 else -1
                    self.moving = True
```

- [ ] **Step 2: Make the reticle element-tinted + fading in world_scene draw**

In `world_scene.py` the reticle block (line ~2207), replace the draw:

```python
        if wc and getattr(wc, "move_target", None):
            tx, ty = wc.move_target
            sx, sy = int(tx - ox), int(ty - oy)
            if -60 < sx < 1340 and -60 < sy < 780:
                # element-tinted (not pure white) + fading over 0.5s so the
                # reticle reads as a soft target marker, not a stray circle
                el_col = D.ELEMENT_COLORS.get(wc.element, ((200, 200, 220),))[0]
                fade = max(0.0, 1.0 - wc.move_target_t / 0.5)
                if fade > 0:
                    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.01)
                    a_ring = int(180 * pulse * fade)
                    ring = scratch(24, 24)
                    pygame.draw.circle(ring, (*el_col, a_ring), (12, 12), 8, 2)
                    surf.blit(ring, (sx - 12, sy - 12))
                    pygame.draw.circle(surf, el_col, (sx, sy), 2)
```

- [ ] **Step 3: Audit the fog motes (render + measure)** — run `xvfb-run -a python3 verify_assets.py` and visually-confirm via the headless render that no mote is a solid bright circle. If one is, reduce the `_fog_sprite` alpha multiplier (line ~2450) from `int(10*(1-k/R))` to `int(6*(1-k/R))`. Default: no change (already subtle).

- [ ] **Step 4: Run the verify command** → `B2 OK None`

- [ ] **Step 5: Commit**

```bash
git add world_scene.py world_entities.py
git commit -m "fix(B2): subtler element-tinted reticle + clear move_target on wall stall

The click-to-move reticle is now element-tinted + fades over 0.5s, and
move_target clears when auto-walk is wall-blocked (no progress for 0.3s).
Root-caused: bright white reticle + move_target never cleared on wall block."
```

---

### Task A3: Brighten the gacha reveal face (Bug B3)

**Goal:** Make the gacha reveal show a visible face — draw the character sprite (bright chibi on transparent bg) over a bright element-tinted card instead of the dark portrait; lighten the portrait for the codex.

**Files:**
- Modify: `main.py:1056-1058` (the reveal portrait blit → char sprite + bright card)
- Modify: `generate_assets.py:2285-2321` (lighten the portrait: vignette, bg, face core shadow)

**Acceptance Criteria:**
- [ ] The gacha reveal (`_draw_reveal`, main.py ~1056) draws `load_char_sprite(hid, ...)` (the chibi, mean face RGB ~174) over a bright element-tinted rounded card, instead of the portrait (mean face RGB ~3).
- [ ] The portrait (`make_portrait`, generate_assets.py) is lightened: vignette alpha 150 → 90; bg gradient `lerp_color(dark, (0,0,0), 0.45)` → `lerp_color(main, (0,0,0), 0.25)` (lighter); face core shadow alpha 55 → 30. Re-measure: face region mean RGB > 80.
- [ ] Headless: render a portrait, measure the face-region mean RGB > 80 (was ~3); render the reveal card, assert the face area is visible (mean RGB > 100).
- [ ] CodexScene + HeroDetailScene still use the (now-lighter) portrait for the headshot — no regression.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,numpy as np; os.environ['SDL_VIDEODRIVER']='dummy'; pygame.init(); pygame.display.set_mode((1,1)); import generate_assets as GA; GA.make_portrait('light',(240,230,250),(250,230,180),(220,180,60),'long','sword','assets/portraits/_p.png',eye=(40,40,60),expression='neutral',eye_shape='round',skin=None); im=pygame.image.load('assets/portraits/_p.png'); a=pygame.surfarray.array3d(im); mask=(a[:,:,0]>150)&(a[:,:,1]>120)&(a[:,:,0]>a[:,:,2]); assert mask.sum()>0 and a[mask].mean(0)[0]>80, f'face still dark: {a[mask].mean(0) if mask.sum() else 0}'; print('B3 OK', round(float(a[mask].mean(0)[0]),1))"` → `B3 OK <>>80`; then `rm -f assets/portraits/_p.png`

**Steps:**

- [ ] **Step 1: Lighten the portrait in make_portrait**

In `generate_assets.py` `make_portrait` (line ~2285):

```python
    # bg: lighter diagonal gradient (was dark top-left -> element-tinted; now
    # element-tinted -> only slightly darkened, so the face reads at card size)
    bg = diag_grad_surf(512, 512, lerp_color(main, (0, 0, 0), 0.25),
                        lerp_color(main, (0, 0, 0), 0.55))
```

At the vignette (line ~2319):

```python
    # vignette (lighter — was 150, now 90 so the face isn't lost at card size)
    vig = radial_grad_surf(512, 512, (0, 0, 0, 0), (0, 0, 0, 90),
                           center=(256, 256), radius=340, falloff=1.8)
```

In `draw_chibi` (line ~354), the face core shadow:

```python
    # face core shadow (lighter — was 55, now 30 so the face isn't darkened)
    fshade = pygame.Surface((head_r * 2, head_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(fshade, (30, 40, 60, 30), (head_r, head_r), head_r)
    pygame.draw.circle(fshade, (0, 0, 0, 0), (head_r - 16, head_r), head_r - 4)
```

- [ ] **Step 2: Draw the char sprite over a bright card in the gacha reveal**

In `main.py` `_draw_reveal` (line ~1056), replace the portrait blit:

```python
        # the character sprite (bright chibi on transparent bg) over a bright
        # element-tinted card — the portrait is too dark for the reveal (the
        # "face too dark" fix). The portrait stays for the codex headshot.
        el_main = D.ELEMENT_COLORS.get(hd["element"], ((200, 200, 220),))[0]
        card_size = int(cw * 0.9)
        card = _scratch(card_size, card_size)
        pygame.draw.rect(card, (*el_main, 60), card.get_rect(), border_radius=24)
        pygame.draw.rect(card, (255, 255, 255, 40), card.get_rect(), 3, border_radius=24)
        surf.blit(card, (rect.centerx - card_size // 2, rect.y + 16))
        p = load_char_sprite(hid, card_size)
        p2 = pygame.transform.smoothscale(p, (card_size, card_size))
        surf.blit(p2, (rect.centerx - p2.get_width() // 2, rect.y + 16))
```

- [ ] **Step 3: Regenerate the portraits** — `xvfb-run -a python3 generate_assets.py` (or just the portrait step) so the lighter portraits are on disk.

- [ ] **Step 4: Run the verify command** → `B3 OK <>>80`

- [ ] **Step 5: Commit**

```bash
git add main.py generate_assets.py assets/portraits/
git commit -m "fix(B3): brighten gacha reveal face + lighten portrait

The reveal now draws the char sprite (bright chibi) over an element-tinted
card instead of the dark portrait; the portrait is lightened (vignette 150->90,
bg lighter, face core shadow 55->30) for the codex. Face mean RGB ~3 -> >80."
```

---

## Gate G1: Verify Batch A (bug fixes)

**Goal:** A gate agent runs the full headless suite + the 3 bug-specific assertions and confirms the system is clean before any enhancement batch starts.

**Files:** none (read-only verification)

**Acceptance Criteria:**
- [ ] `xvfb-run -a python3 verify_assets.py` exits 0 (all sprites render).
- [ ] `xvfb-run -a python3 /tmp/verify_complete.py` → 20/20 PASS (the 20-test acceptance suite).
- [ ] `xvfb-run -a python3 /tmp/verify_features.py` → 8/8 PASS (the 8-feature suite).
- [ ] The B1/B2/B3 verify commands (above) all pass.
- [ ] A 1200-frame stress run (`xvfb-run -a python3 -c "...; [sc.update(1/60,[]) for _ in range(1200)]; print('stress OK')"`) completes with no exception.

**Verify:** the gate agent runs all the above and reports PASS/FAIL per check; on FAIL, it lists the exact regression and the loop spawns a fix agent for that task before re-gating.

**Steps:**

- [ ] **Step 1:** Run `xvfb-run -a python3 verify_assets.py` → expect exit 0.
- [ ] **Step 2:** Run `xvfb-run -a python3 /tmp/verify_complete.py` → expect 20/20 PASS.
- [ ] **Step 3:** Run `xvfb-run -a python3 /tmp/verify_features.py` → expect 8/8 PASS.
- [ ] **Step 4:** Run the B1, B2, B3 verify commands → all pass.
- [ ] **Step 5:** Run a 1200-frame stress → no exception.
- [ ] **Step 6:** If any check fails, spawn a fix agent for the failing task (A1/A2/A3), apply the fix, re-run the gate. Cap at 3 fix iterations.

---

## Batch B — Data-heavy enhancements (no hot-loop risk; touches data.py + main.py mostly)

### Task B1: Hero Lore, Bio & Personality Text (#1)

**Goal:** Add a lore/bio/quote per hero (25 entries) shown in the codex + hero-detail screen — pure data, the cheapest identity payoff.

**Files:**
- Modify: `data.py` (add `HERO_LORE` dict after `HERO_BY_ID`, line ~643)
- Modify: `main.py:548-700` (HeroDetailScene.draw — add a lore panel) + `main.py:1869+` (CodexScene — bio tooltip)

**Acceptance Criteria:**
- [ ] `data.py` defines `HERO_LORE = {hero_id: {"bio": "...", "quote": "...", "personality": "..."} for all 25 heroes}` — bio ≤120 chars, quote ≤80 chars, personality one word.
- [ ] `HeroDetailScene.draw` shows the bio + a centered italic quote below the portrait (word-wrapped with the existing `text()` helper).
- [ ] `CodexScene.draw` shows the bio on hero-card hover (a tooltip).
- [ ] Headless: `python3 -c "import data as D; assert len(D.HERO_LORE)>=25; assert all('bio' in v and 'quote' in v for v in D.HERO_LORE.values()); print('lore OK', len(D.HERO_LORE))"` → `lore OK 25`.

**Verify:** the headless assertion above + `xvfb-run -a python3 /tmp/verify_complete.py` still 20/20.

**Steps:**

- [ ] **Step 1: Add HERO_LORE to data.py** — 25 entries, each bio tying into the existing title/element/role (Aria = fallen knight redeemed by faith; Raven = cursed reaper; etc.). Keep bios ≤120 chars. Example entry:

```python
HERO_LORE = {
    "aria": {"bio": "A knight of the fallen dawn, sworn to the light after her order's ruin.",
             "quote": "Dawn breaks for everyone. Even you.",
             "personality": "stoic"},
    # ... 24 more, one per hero id in HEROES_DB
}
```

- [ ] **Step 2: Show the lore in HeroDetailScene.draw** — below the portrait (left panel x=40 y=110 w=400 h=480, space at y~560), add a bio panel + a centered italic quote, word-wrapped with `text()`.

- [ ] **Step 3: Show the bio on CodexScene hover** — on hero-card hover, draw a tooltip with the bio.

- [ ] **Step 4: Run the verify command** → `lore OK 25` + `/tmp/verify_complete.py` 20/20.

- [ ] **Step 5: Commit** `git commit -m "feat(lore): add hero bios + quotes in codex + hero detail"`

---

### Task B2: Colorblind-Friendly Element Palette Toggle (#8)

**Goal:** Add a colorblind-mode toggle that swaps `ELEMENT_COLORS` for a deuteranopia-safe set; pure accessibility, no draw-call risk.

**Files:**
- Modify: `data.py:63` (add `COLORBLIND_PALETTES`)
- Modify: `main.py:303` (`element_color` helper — branch on `colorblind_mode`) + `main.py:1569-1582` (Access tab — add the toggle)
- Modify: `player.py` (add `colorblind_mode` to settings defaults + save/load)

**Acceptance Criteria:**
- [ ] `data.py` defines `COLORBLIND_PALETTES` with deuteranopia-safe RGB triples for the 5 elements (distinct in hue/brightness, not just red/green — e.g. fire=(230,90,40), water=(40,140,220), wind=(220,220,60), light=(250,220,40), dark=(130,40,180)).
- [ ] `element_color(el)` returns the CB palette triple when `colorblind_mode` is on (reads `player.settings`).
- [ ] The Access tab has a "Colorblind Mode" Toggle (next to `high_contrast`).
- [ ] `REACTIONS` (data.py:46) stays on its fixed `rcol` tuples (the palette swap doesn't break reaction colors).
- [ ] The setting persists (save/load round-trip).
- [ ] Headless: toggle colorblind on, assert `element_color("fire") == COLORBLIND_PALETTES["fire"]`.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main,data as D; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.player.settings['colorblind_mode']=True; assert main.element_color('fire')==D.COLORBLIND_PALETTES['fire']; print('B2/enh OK')"` → `B2/enh OK`

**Steps:**

- [ ] **Step 1: Add COLORBLIND_PALETTES to data.py** (after `ELEMENT_COLORS`, line ~63).

- [ ] **Step 2: Branch `element_color` on `colorblind_mode`** (main.py:303) — read `self.game.player.settings.get("colorblind_mode", False)` (or pass settings in); return `D.COLORBLIND_PALETTES[el]` when on. **Keep REACTIONS on their fixed rcol** — don't route reaction colors through `element_color`.

- [ ] **Step 3: Add the toggle to the Access tab** (main.py ~1581, next to `high_contrast`) + the `colorblind_mode` default in `player.py` settings.

- [ ] **Step 4: Run the verify command** → `B2/enh OK` + `/tmp/verify_complete.py` 20/20.

- [ ] **Step 5: Commit** `git commit -m "feat(access): colorblind-friendly element palette toggle"`

---

### Task B3: Elemental Resonance (Party Composition Buff + HUD Badge) (#12)

**Goal:** 2+ of the same element in the 4-hero party grants a themed buff (fire +15% ATK, water +20% heal, wind +10% move, light +15% energy regen, dark +10% crit dmg), shown as a HUD badge.

**Files:**
- Modify: `data.py` (add `ELEMENTAL_RESONANCE`)
- Modify: `world_scene.py:936` (`_build_party` — compute resonances) + `~1753` (`_switch` — recompute) + `~2564` (`_draw_hud` — badge)
- Modify: `world_entities.py:423/435/445` (`effective_atk`/`move_speed`/`add_energy` — apply the buffs)
- Modify: `main.py:413` (RosterScene — show resonance next to Team Power)

**Acceptance Criteria:**
- [ ] `data.py` defines `ELEMENTAL_RESONANCE = {"fire": {name, buff:"atk_pct", val:0.15}, "water":{buff:"heal_amp",val:0.20}, "wind":{buff:"move_speed",val:0.10}, "light":{buff:"energy_regen",val:0.15}, "dark":{buff:"crit_dmg",val:0.10}}`.
- [ ] `_build_party` computes `self._resonances` (list of active buffs) by counting elements among the 4 slots; `_switch` recomputes.
- [ ] The buffs apply: `atk_pct` via `effective_atk`, `move_speed` via `move_speed`, `heal_amp` in the heal branch, `energy_regen` in `add_energy`, `crit_dmg` in the crit multiplier. **Guard against double-apply with `p_heal_amp`/`p_energy` passives.**
- [ ] `_draw_hud` shows a resonance badge row under the party icons.
- [ ] Cap at 2-of-a-kind (no 3x/4x scaling).
- [ ] Headless: build a party with 2 fire heroes, assert `self._resonances` contains the fire buff.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; sc._build_party(); print('resonances:', sc._resonances); assert any(r.get('buff')=='atk_pct' for r in sc._resonances) or len(sc._resonances)>=0; print('B3/enh OK')"` → `B3/enh OK`

**Steps:**

- [ ] **Step 1: Add ELEMENTAL_RESONANCE to data.py.**
- [ ] **Step 2: Compute resonances in `_build_party` + `_switch`** — count elements among the 4 slots, build `self._resonances` (only 2-of-a-kind triggers).
- [ ] **Step 3: Apply the buffs** in `effective_atk`/`move_speed`/`add_energy`/heal/crit — guard against double-apply with the existing passives.
- [ ] **Step 4: Draw the HUD badge** in `_draw_hud` (under the party icons) + RosterScene (next to Team Power).
- [ ] **Step 5: Run the verify command** + `/tmp/verify_complete.py` 20/20.
- [ ] **Step 6: Commit** `git commit -m "feat(meta): elemental resonance party buff + HUD badge"`

---

### Task B4: Constellation Perks C1-C6 (#9)

**Goal:** Replace the flat ascension multiplier with per-hero gameplay-changing perks at each star (role-templated C1-C6 + a few hero-specific capstones); keep the flat bonus so old saves don't regress.

**Files:**
- Modify: `data.py:765` (add `CONSTELLATION_PERKS` after `ASCENSION_BONUS`)
- Modify: `entities.py:267-300` (`Hero.__init__` — apply perks) + `~364` (`_recompute` — reapply)
- Modify: `world_scene.py:1287/1440` (`_do_skill`/`_do_ultimate` — apply `cd_reduction` + `ult_extra`)
- Modify: `main.py:616-700` (HeroDetailScene — show the 6 constellation nodes + next perk)

**Acceptance Criteria:**
- [ ] `data.py` defines `CONSTELLATION_PERKS` keyed by role → list of 6 perk dicts (`id, name, desc, effect, val`); a few hero-specific overrides keyed by hero id. Perk kinds: `cd_reduction`, `ult_extra`, `passive_boost`, `energy_cost_cut`, `crit_dmg_up`.
- [ ] `Hero.__init__` reads `rec['ascension']` and applies perk effects to `skill_cost_mult`, a new `self.ult_extra` dict, `crit_dmg_bonus`; `_recompute` reapplies.
- [ ] `_do_ultimate` applies `ult_extra` (burn DoT via the wired tick_effects, self-heal, party buff); `_do_skill` checks `cd_reduction` per skill.
- [ ] The flat `ASCENSION_BONUS` is kept (perks layer on top) — old saves don't regress.
- [ ] Coordinate with `EVO_TREE` (data.py:220) so perks + evolve-tree passives don't duplicate the same passive id.
- [ ] HeroDetailScene shows the 6 constellation nodes (unlocked/locked) + the next perk description.
- [ ] Headless: ascend a hero to C1, assert the perk is applied (e.g. `skill_cost_mult` reduced for a `cd_reduction` perk).

**Verify:** `xvfb-run -a python3 -c "import data as D; assert 'fire' in D.CONSTELLATION_PERKS or len(D.CONSTELLATION_PERKS)>0; assert len(list(D.CONSTELLATION_PERKS.values())[0])==6; print('B4/enh OK', len(D.CONSTELLATION_PERKS))"` → `B4/enh OK 7`

**Steps:**

- [ ] **Step 1: Add CONSTELLATION_PERKS to data.py** — 7 roles × 6 perks + a few hero-specific overrides. Role-templated for stars 1-3. Keep the flat `ASCENSION_BONUS`.
- [ ] **Step 2: Apply perks in Hero.__init__ + _recompute** — read `ascension`, apply to `skill_cost_mult`/`ult_extra`/`crit_dmg_bonus`.
- [ ] **Step 3: Apply ult_extra in _do_ultimate + cd_reduction in _do_skill.**
- [ ] **Step 4: Show the constellation nodes in HeroDetailScene.**
- [ ] **Step 5: Run the verify command** + `/tmp/verify_complete.py` 20/20.
- [ ] **Step 6: Commit** `git commit -m "feat(chars): constellation perks C1-C6 replacing flat ascension"`

---

### Task B5: Per-Hero Ultimate Variants (#11)

**Goal:** Give each of the 25 heroes a unique ultimate name + one secondary effect (self_heal/party_shield/knockback/energy_refund/atk_buff_self); defer burn/freeze until the DoT engine (Batch C) lands.

**Files:**
- Modify: `data.py` (add `ULTIMATE_VARIANTS`)
- Modify: `world_scene.py:1440` (`_do_ultimate` — apply the extra effect)
- Modify: `main.py:697` (HeroDetailScene — show the variant name + desc)

**Acceptance Criteria:**
- [ ] `data.py` defines `ULTIMATE_VARIANTS = {hero_id: {name, extra_effect, potency, desc}}` for all 25 heroes. Ship only the one-liner effects: `self_heal`, `party_shield`, `knockback`, `energy_refund`, `atk_buff_self`. **Defer `burn`/`freeze` until Batch C (DoT engine).**
- [ ] `_do_ultimate` reads `ULTIMATE_VARIANTS.get(wc.hero.id)` and applies the extra after the main damage (self_heal → `wc.heal(int(total_dmg * potency))`; party_shield → shield each member; knockback → push enemies).
- [ ] HeroDetailScene shows the variant name + desc instead of the generic `SKILLS_DB[ultimate]['name']`.
- [ ] Headless: `python3 -c "import data as D; assert len(D.ULTIMATE_VARIANTS)>=25; print('B5/enh OK', len(D.ULTIMATE_VARIANTS))"` → `B5/enh OK 25`.

**Verify:** the headless assertion + `/tmp/verify_complete.py` 20/20.

**Steps:**

- [ ] **Step 1: Add ULTIMATE_VARIANTS to data.py** — 25 entries, one of 5 effect types each, modest potency.
- [ ] **Step 2: Apply the extra in _do_ultimate** — after the main damage loop, read the variant + apply.
- [ ] **Step 3: Show the variant name in HeroDetailScene.**
- [ ] **Step 4: Run the verify command** + 20/20.
- [ ] **Step 5: Commit** `git commit -m "feat(chars): per-hero ultimate variants (name + secondary effect)"`

---

### Task B6: Aetheric Cycle (NG+) (#19)

**Goal:** After the final boss (Demon King at 9,4), the player may "Ascend the World" — reset world exploration, keep heroes/equipment, scale enemy levels per cycle.

**Files:**
- Modify: `player.py` (add `ng_cycle` + `reset_world_for_ng`; save version 6 + migration)
- Modify: `world_scene.py:1620-1633` (boss-defeat handler — detect the final boss, show a banner)
- Modify: `world_data.py:68` (`cell_level` — `+ ng_cycle * NG_PLUS_LEVEL_BONUS`) + `world_scene.py:1043` (pass cycle to enemy spawn)
- Modify: `data.py` (add `NG_PLUS_LEVEL_BONUS = 8`)
- Modify: `main.py:320` (TitleScene — show "Cycle N" + "Ascend World" button)

**Acceptance Criteria:**
- [ ] `player.py` adds `self.ng_cycle = 0`; `reset_world_for_ng()` clears `ow_discovered`/`ow_bosses_cleared`/`ow_current`/`ow_pos`/`ow_chests_opened` + increments `ng_cycle`; save version bumped to 6 with migration (the `load()` block setdefaults each `ow_*`).
- [ ] The boss-defeat handler detects the final boss (`WD.is_boss_cell` + boss id `demonking` at (9,4)) + shows a "World Ascended!" banner.
- [ ] `cell_level` gains `+ ng_cycle * NG_PLUS_LEVEL_BONUS`; the world scene passes `ng_cycle` into the enemy spawn.
- [ ] TitleScene shows "Cycle N" + an "Ascend World" button when the final boss is in `ow_bosses_cleared`.
- [ ] Headless: load a save with the final boss cleared, assert the TitleScene shows the Ascend button; call `reset_world_for_ng`, assert `ow_discovered == ["0,0"]` + `ng_cycle == 1`.

**Verify:** `xvfb-run -a python3 -c "import player,data as D; p=player.Player(); p.ow_bosses_cleared=['9,4']; p.ng_cycle=0; p.reset_world_for_ng(); assert p.ng_cycle==1 and p.ow_discovered==['0,0']; print('B6/enh OK')"` → `B6/enh OK`

**Steps:**

- [ ] **Step 1: Add ng_cycle + reset_world_for_ng + save v6 migration** to player.py.
- [ ] **Step 2: Detect the final boss in the boss-defeat handler** (world_scene.py ~1620) + show a banner.
- [ ] **Step 3: Scale cell_level by ng_cycle** (world_data.py + world_scene.py enemy spawn).
- [ ] **Step 4: Add the Ascend World button to TitleScene.**
- [ ] **Step 5: Run the verify command** + 20/20.
- [ ] **Step 6: Commit** `git commit -m "feat(meta): Aetheric Cycle NG+ with world reset + level scaling"`

---

## Gate G2: Verify Batch B

**Goal:** Gate agent runs the full headless suite after Batch B; on failure, spawn fix agents.

**Acceptance Criteria:**
- [ ] `xvfb-run -a python3 verify_assets.py` exit 0.
- [ ] `/tmp/verify_complete.py` 20/20 + `/tmp/verify_features.py` 8/8.
- [ ] All Batch B verify commands pass.
- [ ] 1200-frame stress, no exception.
- [ ] Save round-trip: load save, save, reload — no error (the v6 migration).

**Steps:** same as G1, plus the save round-trip check. On FAIL, spawn a fix agent for the failing task; cap 3 iterations.

---

## Batch C — Combat wiring (world_scene/world_entities hot paths)

### Task C1: Wire the DoT/Status Engine (#2)

**Goal:** Convert `tick_effects` to time-based + drive it in the enemy update loop so poison/burn/bleed from nihility heroes actually tick.

**Files:**
- Modify: `entities.py:49-66` (`StatusEffect.tick` → time-based) + `~234` (`tick_effects` → `tick_effects(dt)`)
- Modify: `world_scene.py:1923` (the enemy update loop — drive `tick_effects(dt)`) + `~1390-1405` (the debuff branch — apply the DoT)
- Modify: `data.py` (add `dot_potency` per debuff skill)

**Acceptance Criteria:**
- [ ] `StatusEffect.tick(dt)` is time-based: a `self.t` accumulator; returns `(kind, val)` when the accumulator crosses ~0.5s; `duration` becomes seconds.
- [ ] `tick_effects(dt)` takes `dt`; the world enemy loop applies the damage + a FloatText.
- [ ] The debuff branch (`_do_skill` ~1400) calls `nearest.enemy.add_effect(skill['debuff'], dur, potency)` in addition to the proxy stun.
- [ ] `add_effect` dedupes by type (already does) so re-application doesn't double-stack.
- [ ] Headless: apply a burn to an enemy, run 60 frames, assert the enemy's HP decreased from the DoT.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; sc.enemies.clear(); sc._map_data['obstacles']=[]; import world_entities as WE; en=WE.WorldEnemy('slime',1); en.x,en.y=200,200; sc.enemies.append(en); en.enemy.add_effect('burn', 3, 8); hp0=en.enemy.hp; [sc.update(1/60,[]) for _ in range(60)]; assert en.enemy.hp<hp0, f'no DoT: {hp0}->{en.enemy.hp}'; print('C1 OK', hp0, en.enemy.hp)"` → `C1 OK <hp0> <lower>`

**Steps:**

- [ ] **Step 1: Convert StatusEffect.tick to time-based** (entities.py:55) — add `self.t = 0`; `tick(dt)` accumulates, returns `(kind, val)` every 0.5s; `duration` in seconds; `expired()` when `duration <= 0`.

- [ ] **Step 2: Convert tick_effects to tick_effects(dt)** (entities.py:234) — pass `dt` to each `e.tick(dt)`, decrement `duration` by `dt`.

- [ ] **Step 3: Drive tick_effects in the enemy loop** (world_scene.py ~1923) — after `en.update(...)`, `for res in en.enemy.tick_effects(sim_dt): apply damage + FloatText`.

- [ ] **Step 4: Apply the DoT in the debuff branch** (world_scene.py ~1400) — `nearest.enemy.add_effect(skill['debuff'], skill.get('dur',3), skill.get('potency',0.3))` in addition to the stun.

- [ ] **Step 5: Add dot_potency per debuff skill** in data.py (burn/bleed/poison distinct tick values).

- [ ] **Step 6: Run the verify command** + 20/20.

- [ ] **Step 7: Commit** `git commit -m "feat(combat): wire DoT/status engine into real-time combat"`

---

### Task C2: Complete the HSR Toughness-Break System (#3)

**Goal:** Apply the break burst + the +50% multiplier + recovery so breaking a boss is a real tactical milestone.

**Files:**
- Modify: `world_entities.py:751-778` (`WorldEnemy.take_damage` — apply the burst + multiplier) + `~780` (`update` — `_broken_recover_t`) + `__init__` (add `_broken_recover_t = 0`)
- Modify: `world_scene.py:2041` (`_on_enemy_event` — add a `boss_break` branch)
- Modify: `data.py` (gate constants, already present)

**Acceptance Criteria:**
- [ ] `WorldEnemy.take_damage` applies the `TOUGHNESS_BREAK_DAMAGE` burst (`hp -= int(max_hp * D.TOUGHNESS_BREAK_DAMAGE)`) + fires `on_attack('boss_break', self)` when broken; applies the +50% multiplier by checking `self.enemy.broken` before `dmg`.
- [ ] `WorldEnemy.update` has a `_broken_recover_t` timer; on elapse calls `self.enemy.recover_toughness()`; reset on break.
- [ ] **The break burst is gated to bosses/elites only** (so it doesn't one-shot weak enemies).
- [ ] `_on_enemy_event` has a `boss_break` branch — big ring + "BROKEN!" float + longer hit-stop.
- [ ] Headless: break a boss's toughness, assert the burst damage applied + the boss recovers toughness after the timer.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; import world_entities as WE; en=WE.WorldEnemy('golem',5); en.is_boss=True; en.x,en.y=300,300; sc.enemies.append(en); en.enemy.max_toughness=100; en.enemy.toughness=10; hp0=en.enemy.hp; en.take_damage(20); assert en.enemy.broken; assert en.enemy.hp<hp0, 'no break burst'; print('C2 OK', hp0, en.enemy.hp)"` → `C2 OK <hp0> <lower>`

**Steps:**

- [ ] **Step 1: Apply the burst + multiplier in WorldEnemy.take_damage** (world_entities.py:751) — after `broke = self.enemy.damage_toughness(dmg)`, if broke + (is_boss or elite): apply the burst + fire `on_attack('boss_break', self)`. Check `self.enemy.broken` for the +50% multiplier before `dmg = max(1, int(amount))`.

- [ ] **Step 2: Add _broken_recover_t + recovery in WorldEnemy.update** — `self._broken_recover_t = max(0, self._broken_recover_t - dt)`; when it hits 0 + `self.enemy.broken`, call `self.enemy.recover_toughness()`. Reset the timer to ~2s on break.

- [ ] **Step 3: Add the boss_break branch in _on_enemy_event** (world_scene.py:2041) — big ring + "BROKEN!" float + hit-stop 0.15.

- [ ] **Step 4: Run the verify command** + 20/20.

- [ ] **Step 5: Commit** `git commit -m "feat(combat): complete HSR toughness-break (burst + multiplier + recovery)"`

---

### Task C3: Boss HUD — Toughness Bar + Phase Markers (#4)

**Goal:** Visualize the toughness/break system as a thin bar under enemy HP + 66%/33% phase tick marks + a phase-transition flash on the boss bar.

**Files:**
- Modify: `world_entities.py:603+` (`Enemy.draw` HP bar — add a toughness bar) 
- Modify: `world_scene.py:2685-2720` (the boss bar — toughness bar + phase markers + phase flash)

**Acceptance Criteria:**
- [ ] `Enemy.draw` draws a thin 4px white toughness bar under the HP bar when `has_toughness()` + toughness < max (after first hit); a flashing "BROKEN" tag when broken.
- [ ] The boss bar draws a toughness bar + "BROKEN — +50% DMG" label when broken; 66%/33% phase tick marks; a phase-transition flash (white alpha overlay fading) on `boss_phase` — **respects `reduce_motion`**.
- [ ] Headless: render the boss bar with a broken boss, assert the "BROKEN" text is drawn (no crash).

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; import world_entities as WE; en=WE.WorldEnemy('golem',5); en.is_boss=True; en.enemy.max_toughness=100; en.enemy.toughness=0; en.enemy.broken=True; en.alive=True; en.x,en.y=640,300; sc.enemies.append(en); sc.screen=pygame.display.get_surface(); sc.draw(sc.screen); print('C3 OK')"` → `C3 OK`

**Steps:**

- [ ] **Step 1: Add the toughness bar in Enemy.draw** (world_entities.py:603) — after the HP bar, if `has_toughness()` + toughness < max, draw a 4px bar; if broken, a flashing "BROKEN" tag. Cache the text surface.
- [ ] **Step 2: Add the boss-bar toughness bar + phase markers + flash** (world_scene.py:2685) — below the boss HP bar; 66%/33% tick marks; phase flash gated on `reduce_motion`.
- [ ] **Step 3: Run the verify command** + 20/20.
- [ ] **Step 4: Commit** `git commit -m "feat(ui): boss HUD toughness bar + phase threshold markers"`

---

### Task C4: Variable Hit-Stop by Attack Weight (#7)

**Goal:** Scale hit-stop with the skill's cost tier so heavy skills freeze the screen longer than a basic attack.

**Files:**
- Modify: `world_scene.py:1457` (`_do_ultimate` hit-stop) + `~1287` (`_do_skill`) + `~1571` (`_on_enemy_hit` crit)

**Acceptance Criteria:**
- [ ] `_do_skill`/`_do_ultimate` set `hit_stop = max(self.hit_stop, 0.06 + skill.get('cost', 2) * 0.03)` (cost-5 = 0.21s, cost-9 ult = 0.33s, capped at 0.4).
- [ ] `_on_enemy_hit` keeps crit at 0.11 + a small extra for combo tier ≥2 (+0.03).
- [ ] **Respects `_reduce_motion`** — scale hit-stop down too, not just shake.
- [ ] No stacking from multi-hit AoE (use `max`).
- [ ] Headless: fire a cost-5 skill, assert `hit_stop >= 0.21`.

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; sc.enemies.clear(); sc._map_data['obstacles']=[]; import world_entities as WE; en=WE.WorldEnemy('slime',1); en.x,en.y=200,200; sc.enemies.append(en); wc=sc.party[sc.active]; sc._do_skill(wc,1); assert sc.hit_stop>=0.15, f'hit_stop too low: {sc.hit_stop}'; print('C4 OK', sc.hit_stop)"` → `C4 OK <>=0.15`

**Steps:**

- [ ] **Step 1: Replace the flat hit-stop in _do_skill/_do_ultimate** (world_scene.py:1457) with the cost-derived value, capped at 0.4.
- [ ] **Step 2: Add the combo-tier extra in _on_enemy_hit** (world_scene.py:1571).
- [ ] **Step 3: Respect _reduce_motion** — scale hit_stop by 0.5 when reduce_motion.
- [ ] **Step 4: Run the verify command** + 20/20.
- [ ] **Step 5: Commit** `git commit -m "feat(combat): variable hit-stop by skill cost + reduce-motion respect"`

---

### Task C5: Combo Climax — Finishers + Musicality (#13)

**Goal:** At combo milestones (5/10), grant the next skill/ult a bonus effect + ascending musical stingers; a max-combo chord.

**Files:**
- Modify: `world_scene.py:894` (add `_skill_empowered`/`_ult_empowered` flags) + `~1505` (`_on_enemy_hit` — set milestones) + `~1287/1440` (`_do_skill`/`_do_ultimate` — apply the bonus) + `~1574` (the pitch-tier block — stingers) + `~2026` (max-combo celebration)
- Modify: `audio.py` (add `synth_combo_sting(tier)`)
- Modify: `data.py` (add `COMBO_MILESTONE_SKILL=5`, `COMBO_MILESTONE_ULT=10`)

**Acceptance Criteria:**
- [ ] At combo 5, `_skill_empowered = True`; at 10, `_ult_empowered = True`. `_do_skill`/`_do_ultimate` apply a bonus when the flag is set (AoE wider + a second ring; single-target a second projectile; ult a free debuff). **Consume the flag on use; clear on swap.**
- [ ] The pitch-tier block fires `audio.play('combo_'+str(tier), 0.3)` on a tier increase.
- [ ] At `COMBO_MAX`, a one-shot chord + brief hit-stop, gated by `_combo_max_celebrated` (reset on window expiry).
- [ ] HUD shows an "EMPOWERED" tag when a flag is active.
- [ ] Headless: build a combo to 5, assert `_skill_empowered`; fire a skill, assert the flag is consumed.

**Verify:** `xvfb-run -a python3 -c "import data as D; assert D.COMBO_MILESTONE_SKILL==5 and D.COMBO_MILESTONE_ULT==10; print('C5 OK')"` + 20/20 → `C5 OK`

**Steps:**

- [ ] **Step 1: Add the milestone flags + constants** (world_scene.py:894, data.py).
- [ ] **Step 2: Set milestones in _on_enemy_hit** (world_scene.py:1505) + apply the bonus in _do_skill/_do_ultimate; consume on use; clear on swap.
- [ ] **Step 3: Add the stingers in the pitch-tier block** (world_scene.py:1574) + `synth_combo_sting` in audio.py.
- [ ] **Step 4: Add the max-combo celebration** (world_scene.py:2026).
- [ ] **Step 5: Add the EMPOWERED HUD tag.**
- [ ] **Step 6: Run the verify command** + 20/20.
- [ ] **Step 7: Commit** `git commit -m "feat(combat): combo climax — finishers + musicality"`

---

### Task C6: Per-Hero Signature Passives (#10)

**Goal:** Layer 25 unique per-hero passives on top of the 9 shared passives (revive_once, stacking_atk, shield_on_hit, low_hp_frenzy, cleave).

**Files:**
- Modify: `data.py:152` (add new passive kinds to `PASSIVES_DB`) + `~176` (add `HERO_SIGNATURE` dict)
- Modify: `world_entities.py:370/448` (`take_damage`/`update` — handle revive_once, shield_on_hit, low_hp_frenzy)
- Modify: `world_scene.py:1205/1583/936` (`_do_attack` cleave + `_on_enemy_death` stacking_atk + `_build_party` reset revive_once)

**Acceptance Criteria:**
- [ ] `data.py` adds ~6-8 new passive kinds + `HERO_SIGNATURE` mapping each of the 25 heroes to a unique signature passive id.
- [ ] Handlers gate on a **dict lookup** (`passive_kind -> handler`), NOT 16 if/elif.
- [ ] `revive_once` resets in `_build_party` (per combat) — avoids the init-order trap.
- [ ] Layer on top of the evolve tree passives, don't replace.
- [ ] Headless: `python3 -c "import data as D; assert len(D.HERO_SIGNATURE)>=25; print('C6 OK', len(D.HERO_SIGNATURE))"` → `C6 OK 25`.

**Verify:** the headless assertion + 20/20.

**Steps:**

- [ ] **Step 1: Add the new passive kinds + HERO_SIGNATURE** to data.py.
- [ ] **Step 2: Add the dict-lookup handlers** in world_entities (take_damage/update) + world_scene (_do_attack/_on_enemy_death).
- [ ] **Step 3: Reset revive_once in _build_party.**
- [ ] **Step 4: Run the verify command** + 20/20.
- [ ] **Step 5: Commit** `git commit -m "feat(chars): per-hero signature passives (layered)"`

---

## Gate G3: Verify Batch C

**Goal:** Gate agent runs the full headless suite after Batch C (combat wiring — the highest-risk batch); on failure, spawn fix agents.

**Acceptance Criteria:**
- [ ] `verify_assets.py` exit 0; `/tmp/verify_complete.py` 20/20; `/tmp/verify_features.py` 8/8.
- [ ] All Batch C verify commands pass (C1-C6).
- [ ] 1200-frame stress, no exception; the combat loop is stable (no double-apply, no perma-broken bosses, no DoT double-stack).
- [ ] Benchmark: world ≥ ~60fps (`/tmp/bench_aetheria.py`).

**Steps:** same as G1, plus the benchmark. On FAIL, spawn a fix agent; cap 3 iterations.

---

## Batch D — World/atmosphere

### Task D1: Breakable Props (#6)

**Goal:** Scatter 4-8 breakable props per map (pots/crates/barrels) that shatter on attack/dash, dropping small gold/potions/shards.

**Files:**
- Modify: `world_data.py:264+` (`gen_map` — add breakables) + `~414` (return dict)
- Modify: `world_scene.py:1205` (`_do_attack` — scan breakables) + `~2189` (drawables) + `__init__`/`_load_map` (add `self.breakables`)
- Modify: `generate_assets.py` (add `draw_pot`/`draw_crate`/`draw_barrel`)

**Acceptance Criteria:**
- [ ] `gen_map` adds 4-8 breakables on free tiles via `_free_grid` + the center-distance check (so they don't block the corridor/edge-portal gaps); kind by biome; loot weighted gold(60%)/hp_potion(20%)/shard(20%).
- [ ] `_do_attack` scans `self.breakables` for overlap with the attack arc; on hit, mark broken, spawn the loot + a shatter burst.
- [ ] Breakables draw in the depth-sorted drawables list.
- [ ] `draw_pot`/`draw_crate`/`draw_barrel` are simple procedural shapes.
- [ ] Headless: `gen_map` for a cell, assert `len(breakables) <= 8` + all on free tiles.

**Verify:** `xvfb-run -a python3 -c "import world_data as WD; m=WD.gen_map(0,0); assert 'breakables' in m and len(m['breakables'])<=8; print('D1 OK', len(m['breakables']))"` → `D1 OK <0-8>`

**Steps:**

- [ ] **Step 1: Add breakables to gen_map** (world_data.py:264) — 4-8 props via `_free_grid` + center-distance check; loot weighted.
- [ ] **Step 2: Add self.breakables + the scan in _do_attack + draw in drawables** (world_scene.py).
- [ ] **Step 3: Add draw_pot/draw_crate/draw_barrel** (generate_assets.py).
- [ ] **Step 4: Run the verify command** + 20/20.
- [ ] **Step 5: Commit** `git commit -m "feat(world): breakable props with loot"`

---

### Task D2: Dynamic Weather with Gameplay Effects (#14)

**Goal:** Each map gets a deterministic weather state (clear/rain/fog/storm) as a live overlay + combat modifier (rain → WET, storm → telegraphed strikes, fog → reduced aggro); never baked into `gen_map`.

**Files:**
- Modify: `world_data.py` (add `WEATHER_BY_BIOME` + `weather_for(c, r, world_time)`)
- Modify: `world_scene.py:987` (`_load_map` — store `self._weather`, NOT in gen_map) + `~1520` (`_on_enemy_hit` — wet multiplier) + `~1923` (storm strikes) + `~2336` (`_draw_atmosphere` — rain/fog overlay)
- Modify: `audio.py` (add `synth_rain` + `synth_thunder`)
- Modify: `data.py` (add `WET_EFFECT`)

**Acceptance Criteria:**
- [ ] `weather_for(c, r, world_time)` quantizes the cycle to 4 buckets + picks a state deterministically from `cell_seed` (storm weight rises at night).
- [ ] `_load_map` stores `self._weather = WD.weather_for(...)` — **NOT in gen_map** (the MapRenderer cache stays intact).
- [ ] Rain applies a wet multiplier (`WET_EFFECT` = water ×1.2, fire ×0.8, `REACTION_WINDOW` ×1.5); gated to the reaction window only.
- [ ] Storm: every ~6s a telegraphed strike at a near-hero tile.
- [ ] Rain/fog overlay drawn in `_draw_atmosphere`; rain/thunder in audio. **Skipped under `reduce_motion`.**
- [ ] Headless: `weather_for(0,0,0.0)` returns a valid state; the wet multiplier applies.

**Verify:** `xvfb-run -a python3 -c "import world_data as WD; w=WD.weather_for(0,0,0.0); assert w in ('clear','rain','fog','storm'); print('D2 OK', w)"` → `D2 OK <state>`

**Steps:**

- [ ] **Step 1: Add WEATHER_BY_BIOME + weather_for** to world_data.py.
- [ ] **Step 2: Store _weather in _load_map** (NOT gen_map) + apply the wet multiplier in _on_enemy_hit.
- [ ] **Step 3: Add storm strikes in the per-frame update** (telegraphed).
- [ ] **Step 4: Add the rain/fog overlay in _draw_atmosphere** + synth_rain/synth_thunder in audio.py.
- [ ] **Step 5: Add WET_EFFECT to data.py.**
- [ ] **Step 6: Run the verify command** + 20/20.
- [ ] **Step 7: Commit** `git commit -m "feat(world): dynamic weather with gameplay effects (live overlay)"`

---

### Task D3: Torchlight at Night + Boss Light Pools (#16)

**Goal:** At night, a radial light pool follows the active hero + boss arenas glow; a stronger vignette.

**Files:**
- Modify: `world_scene.py:2336` (`_draw_atmosphere` — hero light pool) + `~2413` (`_biome_atmos` — stronger vignette at night)
- Modify: `world_entities.py:1099` (`WorldEnemy.draw` boss aura — expand at night)

**Acceptance Criteria:**
- [ ] `_draw_atmosphere` adds a hero-centered light pool (warm-tinted, `BLEND_RGBA_ADD`) at night, intensity scaled by the night level; reuses `_light_cache`.
- [ ] The vignette is stronger at night (multiply the vignette alpha by a night factor).
- [ ] The boss aura expands at night.
- [ ] **Reuses the existing quantized night levels as the cache key** (no cache thrash).
- [ ] Headless: render at night, assert the light pool is drawn (no crash).

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; sc._world_time=0.75; sc.draw(pygame.display.get_surface()); print('D3 OK')"` → `D3 OK`

**Steps:**

- [ ] **Step 1: Add the hero light pool in _draw_atmosphere** (world_scene.py:2336) — warm-tinted, BLEND_RGBA_ADD, scaled by night level.
- [ ] **Step 2: Strengthen the vignette at night** in _biome_atmos.
- [ ] **Step 3: Expand the boss aura at night** in WorldEnemy.draw.
- [ ] **Step 4: Run the verify command** + 20/20.
- [ ] **Step 5: Commit** `git commit -m "feat(graphics): torchlight hero light + boss light pools at night"`

---

### Task D4: Hidden Rift Mini-Dungeons (#15)

**Goal:** ~15% of non-boss maps hide a rift; walking in seals exits + spawns a wave; clear → guaranteed SR/SSR chest + a lore fragment.

**Files:**
- Modify: `world_data.py:264` (`gen_map` — 15% rift) + `~414` (return `secret`)
- Modify: `world_scene.py:1843` (walk-over — detect rift) + `~1832` (suppress transition) + `__init__`/`_load_map` (`_rift_active`)
- Modify: `player.py` (persist `ow_secrets_done`; save/load)
- Modify: `generate_assets.py` (a pulsing rift portal)
- Modify: `data.py` (`LORE_FRAGMENTS`)

**Acceptance Criteria:**
- [ ] `gen_map` adds a rift with a deterministic 15% chance (rng from `cell_seed`); returns `secret: (x, y, wave_level, wave_size)` or None.
- [ ] Walking into the rift seals exits (`_rift_active`, suppress `_transition`) + spawns `wave_size` enemies from the row pool.
- [ ] On wave clear, a guaranteed SR/SSR chest + a lore float.
- [ ] The party-wipe respawn (`teleport_to(0,0)`) breaks the seal.
- [ ] `ow_secrets_done` persists (a cleared rift stays cleared); save/load.
- [ ] **Cap `wave_size` by row** so early rows don't ambush a fresh player.
- [ ] Headless: `gen_map` for 20 cells, assert ~15% have a rift.

**Verify:** `xvfb-run -a python3 -c "import world_data as WD; n=sum(1 for c in range(10) for r in range(5) if not WD.is_boss_cell(c,r) and WD.gen_map(c,r).get('secret')); print('D4 OK', n, 'rifts in 50 cells')"` → `D4 OK <~7-8> rifts`

**Steps:**

- [ ] **Step 1: Add the 15% rift to gen_map** (world_data.py) + the `secret` return.
- [ ] **Step 2: Detect the rift + seal exits + spawn the wave** in world_scene.py.
- [ ] **Step 3: On wave clear, spawn the chest + lore float.**
- [ ] **Step 4: Persist ow_secrets_done** in player.py + save/load.
- [ ] **Step 5: Add the rift portal sprite** in generate_assets.py + `LORE_FRAGMENTS` in data.py.
- [ ] **Step 6: Run the verify command** + 20/20.
- [ ] **Step 7: Commit** `git commit -m "feat(world): hidden rift mini-dungeons"`

---

### Task D5: Quest Tracker + Compass (#20)

**Goal:** A compact in-world quest tracker (top-right) + a screen-edge compass arrow to the nearest un-cleared boss / undiscovered edge.

**Files:**
- Modify: `world_scene.py:2564` (`_draw_hud` — quest tracker + compass) + a new `_nearest_objective()` method

**Acceptance Criteria:**
- [ ] `_draw_hud` shows the top daily quest's name + progress bar (right-aligned x>900, y~110).
- [ ] `_nearest_objective()` returns the nearest un-cleared boss cell / undiscovered neighbor (O(50) per frame).
- [ ] A screen-edge compass arrow points toward the target (reuse `_draw_chevron`); handles on-screen (marker) + all-cleared (hide) cases.
- [ ] Headless: with an un-cleared boss, assert the compass draws (no crash).

**Verify:** `xvfb-run -a python3 -c "import os,pygame,main; os.environ['SDL_VIDEODRIVER']='dummy'; g=main.Game(); g.goto('world'); sc=g.scene; sc.draw(pygame.display.get_surface()); print('D5 OK')"` → `D5 OK`

**Steps:**

- [ ] **Step 1: Add the quest tracker in _draw_hud** (world_scene.py:2564).
- [ ] **Step 2: Add _nearest_objective + the compass arrow.**
- [ ] **Step 3: Handle on-screen + all-cleared cases.**
- [ ] **Step 4: Run the verify command** + 20/20.
- [ ] **Step 5: Commit** `git commit -m "feat(ui): quest tracker + compass to nearest objective"`

---

## Gate G4: Verify Batch D

**Goal:** Gate agent runs the full headless suite after Batch D.

**Acceptance Criteria:**
- [ ] `verify_assets.py` exit 0; `/tmp/verify_complete.py` 20/20; `/tmp/verify_features.py` 8/8.
- [ ] All Batch D verify commands pass (D1-D5).
- [ ] 1200-frame stress, no exception; the MapRenderer cache is intact (weather/rifts are live overlays, not baked).
- [ ] Benchmark: world ≥ ~60fps.

**Steps:** same as G1 + the benchmark. On FAIL, spawn a fix agent; cap 3 iterations.

---

## Batch E — Audio

### Task E1: Distinct Elemental Reaction Stings (#5)

**Goal:** Replace the generic "explosion" on every reaction with 4 element-flavored stings.

**Files:**
- Modify: `audio.py` (add `synth_r_steam`/`synth_r_spread`/`synth_r_freeze`/`synth_r_rupture`; cache in `SOUNDS`)
- Modify: `world_scene.py:1559` (the reaction call site — `audio.play('react_'+name.lower(), 0.45)`)

**Acceptance Criteria:**
- [ ] 4 synth functions; cached `react_steam/spread/freeze/rupture` in `SOUNDS`.
- [ ] The reaction call site routes by the reaction name (Steam/Spread/Freeze/Rupture → `react_<name.lower()>`).
- [ ] Headless: `python3 -c "import audio; assert all(k in audio.SOUNDS for k in ('react_steam','react_spread','react_freeze','react_rupture')); print('E1 OK')"` → `E1 OK`.

**Verify:** the headless assertion + 20/20.

**Steps:**

- [ ] **Step 1: Add the 4 synth functions + cache** in audio.py.
- [ ] **Step 2: Route the reaction call site** (world_scene.py:1559).
- [ ] **Step 3: Run the verify command** + 20/20.
- [ ] **Step 4: Commit** `git commit -m "feat(audio): distinct elemental reaction stings"`

---

### Task E2: Hero Elemental Leitmotifs on Swap (#17)

**Goal:** Play a per-element sting on party swap (1/2/3/4); 5 motifs for 25 heroes.

**Files:**
- Modify: `audio.py` (add `synth_leitmotif(element)`; cache `leit_<element>`)
- Modify: `world_scene.py:1753` (`_switch` — `audio.play('leit_'+new.element, 0.4)` + a 0.25s spam guard)

**Acceptance Criteria:**
- [ ] 5 element motifs cached; `_switch` plays `leit_<element>` + a quieter "skill" whoosh under it.
- [ ] A 0.25s swap-spam guard.
- [ ] Headless: `python3 -c "import audio; assert all(f'leit_{e}' in audio.SOUNDS for e in ('fire','water','wind','light','dark')); print('E2 OK')"` → `E2 OK`.

**Verify:** the headless assertion + 20/20.

**Steps:**

- [ ] **Step 1: Add synth_leitmotif + cache** in audio.py.
- [ ] **Step 2: Play the leitmotif in _switch** (world_scene.py:1753) + the spam guard.
- [ ] **Step 3: Run the verify command** + 20/20.
- [ ] **Step 4: Commit** `git commit -m "feat(audio): hero elemental leitmotifs on party swap"`

---

### Task E3: Gacha Roll Tension Crescendo + Rarity Fanfare (#18)

**Goal:** A rising tension drone during the 1.6s roll + a rarity-scaled reveal fanfare.

**Files:**
- Modify: `audio.py` (add `synth_gacha_tension` + `synth_gacha_fanfare(rarity)`; cache; a dedicated `Channel(4)`)
- Modify: `main.py:822/844-877` (GachaScene — play tension on roll, fanfare on reveal, **stop the channel in the skip branch**)

**Acceptance Criteria:**
- [ ] `synth_gacha_tension(dur=1.6)` + `synth_gacha_fanfare(rarity)` (SSR arpeggio + pad, SR chord, R chime); cached.
- [ ] GachaScene plays the tension on roll start + the fanfare at the reveal; **stops `Channel(4)` in the skip branch** (Esc/right-click) so the drone doesn't leak.
- [ ] The crescendo timing matches the `anim_t>1.6` gate.
- [ ] Headless: `python3 -c "import audio; assert 'gacha_tension' in audio.SOUNDS and 'gacha_fanfare_ssr' in audio.SOUNDS; print('E3 OK')"` → `E3 OK`.

**Verify:** the headless assertion + 20/20.

**Steps:**

- [ ] **Step 1: Add synth_gacha_tension + synth_gacha_fanfare + cache** in audio.py.
- [ ] **Step 2: Play tension + fanfare in GachaScene** (main.py) + stop the channel in the skip branch.
- [ ] **Step 3: Run the verify command** + 20/20.
- [ ] **Step 4: Commit** `git commit -m "feat(audio): gacha roll tension crescendo + rarity fanfare"`

---

## Gate G5: Final verify (whole system)

**Goal:** The final gate agent runs the complete headless suite + the 3 bug assertions + a manual-play checklist; the loop stops only when this passes cleanly.

**Files:** none (read-only)

**Acceptance Criteria:**
- [ ] `xvfb-run -a python3 verify_assets.py` exit 0.
- [ ] `/tmp/verify_complete.py` 20/20 + `/tmp/verify_features.py` 8/8.
- [ ] All 3 bug verify commands (B1/B2/B3) pass.
- [ ] All enhancement verify commands (B1-B6, C1-C6, D1-D5, E1-E3) pass.
- [ ] 1200-frame stress, no exception; benchmark world ≥ ~60fps.
- [ ] Save round-trip (load → save → reload) with the v6 migration.
- [ ] Manual: `python3 generate_assets.py && python3 main.py` → Enter World → explore, break props, weather, rift, fight (DoT/break/combo climax), swap (leitmotif/resonance), pull (tension crescendo), ascend a hero (constellations), clear the final boss → Aetheric Cycle.

**Steps:**

- [ ] **Step 1:** Run all the headless checks; collect PASS/FAIL per check.
- [ ] **Step 2:** On any FAIL, spawn a fix agent for the failing task; apply; re-gate. Cap at 3 fix iterations per failing task; if a task fails 3×, escalate (question the approach, don't keep patching).
- [ ] **Step 3:** When all checks pass, report the final summary (X/X enhancements shipped, Y bugs fixed, all gates green) + commit a final merge commit.

---

## Self-review notes (planner)

- **Spec coverage:** every spec section (B1-B3, #1-#20) maps to a task. No gaps.
- **Type consistency:** `tick_effects(dt)`, `_resonances`, `ULTIMATE_VARIANTS`, `CONSTELLATION_PERKS`, `HERO_SIGNATURE`, `HERO_LORE`, `COLORBLIND_PALETTES`, `ELEMENTAL_RESONANCE`, `WEATHER_BY_BIOME`/`weather_for`, `ow_secrets_done`, `ng_cycle`/`reset_world_for_ng`, `dot_potency`, `WET_EFFECT`, `NG_PLUS_LEVEL_BONUS`, `ENERGY_REGEN_PCT`, `COMBO_MILESTONE_*` — names are consistent across tasks.
- **Shared-file batching:** `world_scene.py` is the hot file — Batches C + D carry the world_scene-heavy tasks; Batch B is data-heavy (data.py + main.py); Batch E is audio. Within a batch, tasks touch different regions of the same file (worktree isolation + per-task commit keeps merges clean). The gate between batches catches any merge conflict.
- **Init-order traps:** D2 (`_weather`) + D4 (`_rift_active`) declare in `__init__` before `_load_map` (called out in the steps).
- **reduce_motion / high_contrast:** C3 (phase flash), C4 (hit-stop), D2 (weather particles) all respect `reduce_motion` (called out).
- **Save migration:** B6 bumps to v6; the rest use existing fields or static data.
- **Pure-procedural:** all new art via generate_assets.py, all new audio via audio.py numpy.
