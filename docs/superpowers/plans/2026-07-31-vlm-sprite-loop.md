# VLM Canonical Sprite Overhaul — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:subagent-driven-development (recommended) or superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the per-champion world sprites actually recognizable as their champion — canonical mean match ≥ 6.0, recognizable ≥ 70%, stance captured ≥ 90% (from today's 1.18 / 0% / 46%) — by overhauling the renderer (stance-driven + ~26 new body/feature primitives), rewriting the VLM pipeline (canon-grounded describe/critique + canonical gate), and re-baking.

**Architecture:** Add a `stance` field to the descriptor; `draw_chibi_descriptor` dispatches by stance (upright/quadruped/mounted/flying/floating), then by archetype within stance, then applies features + weapon. The VLM picks stance/archetype/features/colors from the champ's canonical identity (LoL knowledge) + splash. A canonical gate (VLM LoL knowledge as ground truth, strict) replaces the dishonest calibrated splash-similarity gate. Runtime only loads baked PNGs (unchanged wiring).

**Tech Stack:** Python 3.11, pygame 2.6.x (headless via `SDL_VIDEODRIVER=dummy`), stdlib `urllib`+`ssl` for the OpenAI-compatible VLM HTTP API, `concurrent.futures.ThreadPoolExecutor` for configurable concurrency.

**User decisions (already made):**
- Invest fully; do the best for good results (all 170 champs get a real body; 1-champ unique bodies get dedicated drawers).
- Success metric: canonical mean ≥ 6, recognizable ≥ 70%, stance ≥ 90%. Accept no specific faces (recognizable via silhouette + features + colors).
- Phasing: 170 Original first (prove the renderer hits the gate), then 1780 per-skin.
- Concurrency configurable, default 1 (after-hours runs may use 4).
- VLM model/endpoint/key: the provided misa-gemma-4-31b-it constants (self-signed cert → verify=False).

**HARD CONSTRAINT (from AGENTS.md / memory `gacha-no-image-reading`):** NEVER use the Read tool on a PNG/JPG. The VLM reads images over HTTP base64 (outside the Claude session); the build script uses headless `pygame.image.load`. Tests assert on file existence / size / coverage / load-path, never on pixel content via Read.

**Test convention:** no pytest. Tests are headless `python3` scripts under `tools/` that set `SDL_VIDEODRIVER=dummy`, define `test_*` functions, and print `pass <name>` / a final `OK` line. Follow the existing `tools/verify_*.py` style.

**Existing plumbing being REUSED (from the merged vlm-sprite-loop branch):** `src/build/vlm_client.py` (VLMClient describe/critique), `src/build/sprite_loop.py` (vlm_sprite_loop, run_sprite_bake, RENDER_LOCK, CACHE_LOCK, load_cache/save_cache), `src/build/build_champions.py` (--vlm-loop CLI), the per-skin `sprites/{idx}.png` output + `descriptors.json` cache, and the runtime skin-switch wiring (load_char_sprite skin_idx, Hero.skin, WorldCharacter._load_sprite). This plan REWRITES the renderer primitives + VLM prompts + gate, then re-bakes.

**Renderer extension points (confirmed):**
- `src/assets_gen/generate.py:1389` `draw_chibi_descriptor(surf, descriptor)` — the dispatch entry; add stance branching.
- `src/assets_gen/generate.py:1381` `_ARCH_DRAW` map — add new upright bodies.
- `src/assets_gen/generate.py:841` `_apply_features(...)` — the feature dispatch loop; add new feature branches.
- `src/assets_gen/generate.py:324` `draw_weapon(surf, cx, cy, weapon, ...)` — add `dual_pistols`.
- Helpers available: `shade(c, factor)`, `px_dither_surf(w,h,c1,c2)`, `clip_to_rect/clip_to_circle`, `_body_outline(surf,cx,cy,w,h,primary,outline)`, `_motif_aura(surf,cx,cy,motif)`, `_add_*` feature family (lines 701-838).
- Each archetype drawer returns `(hx, hy, hr, w, h)` so features/weapon place consistently. Anchor `cx,cy = 128,150`.

---

## Phase 1 — Renderer overhaul (new primitives + stance dispatch)

### Task 1: stance field + dispatch skeleton

**Goal:** Add a `stance` field to the descriptor and make `draw_chibi_descriptor` dispatch by stance (upright → existing `_ARCH_DRAW`; the other 4 stances → stub drawers that fall back to `_arch_knight` for now). This wires the 2-level dispatch so later tasks fill in the real drawers.

**Files:**
- Modify: `src/assets_gen/generate.py:1389-1410` (`draw_chibi_descriptor`)
- Test: `tools/verify_stance_dispatch.py`

**Acceptance Criteria:**
- [ ] `draw_chibi_descriptor` reads `descriptor.get("stance", "upright")` and branches: `upright` → `_ARCH_DRAW[archetype]` (existing behavior, unchanged); `quadruped`/`mounted`/`flying`/`floating` → a stub that calls `_arch_knight` (placeholder, replaced in later tasks) so it still renders 256×256.
- [ ] A descriptor WITHOUT `stance` defaults to `upright` → byte-identical to the old behavior (existing `verify_assets` + `verify_new_primitives` still pass).
- [ ] `floating` stance applies a `_floating_modifier` (no legs + hover disc) on top of the upright body — implemented now (small), since it's a modifier not a new body.
- [ ] `tools/verify_stance_dispatch.py` passes: renders each of the 5 stances (upright/quadruped/mounted/flying/floating) → 256×256 + coverage > 0; a no-stance descriptor → identical coverage to the old path (backward-compat).

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_stance_dispatch.py` → ends in `STANCE DISPATCH OK`. Plus `SDL_VIDEODRIVER=dummy python3 tools/verify_new_primitives.py` still `NEW PRIMITIVES OK` + `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` still `OK`.

**Steps:**

- [ ] **Step 1: Write the failing test** (`tools/verify_stance_dispatch.py`):

```python
"""Stance dispatch: 5 stances render + no-stance backward-compat."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))
from src.assets_gen.generate import draw_chibi_descriptor
import pygame.surfarray, numpy as np

PAL = {"primary": [220, 90, 40], "secondary": [255, 170, 90], "accent": [255, 230, 140]}
BASE = {"archetype": "knight", "weapon": "none", "palette": PAL,
        "features": [], "build": "average", "motif": "flame"}

def _cov(surf):
    a = pygame.surfarray.pixels_alpha(surf); arr = a.__array__(); del a
    return float((arr > 8).sum()) / (surf.get_width() * surf.get_height())

def test_no_stance_defaults_upright_identical():
    s_old = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s_old, {**BASE})  # no stance key
    s_new = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s_new, {**BASE, "stance": "upright"})
    assert s_old.get_size() == (256, 256) and s_new.get_size() == (256, 256)
    assert _cov(s_old) == _cov(s_new), "upright stance must be byte-identical to no-stance"

def test_all_5_stances_render():
    for stance in ("upright", "quadruped", "mounted", "flying", "floating"):
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        draw_chibi_descriptor(s, {**BASE, "stance": stance})
        assert s.get_size() == (256, 256), f"{stance} size"
        assert _cov(s) > 0, f"{stance} blank"

def test_floating_has_no_legs_modifier():
    # floating should differ from upright (the modifier removes legs / adds hover)
    s_up = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_up, {**BASE, "stance": "upright"})
    s_fl = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_fl, {**BASE, "stance": "floating"})
    assert _cov(s_fl) != _cov(s_up), "floating modifier must change the sprite"

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("STANCE DISPATCH OK")

if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_stance_dispatch.py`
Expected: FAIL — `draw_chibi_descriptor` ignores `stance`; the all-5-stances test would pass trivially (all render the knight) BUT the floating-modifier test fails (floating == upright coverage).

- [ ] **Step 3: Implement the stance dispatch + floating modifier** in `src/assets_gen/generate.py`. Replace the body of `draw_chibi_descriptor` (lines 1389-1410) with:

```python
def _floating_modifier(surf, cx, cy, w, h, pal, outline):
    """Floating stance: erase the lower legs (draw bg-colored blocks over them)
    + add a hover disc beneath. Applied AFTER the upright body is drawn."""
    # hover disc (a flat ellipse under the body)
    disc = pygame.Surface((int(w * 1.4), 14), pygame.SRCALPHA)
    pygame.draw.ellipse(disc, (255, 255, 255, 70), disc.get_rect())
    pygame.draw.ellipse(disc, (*pal["accent"], 120), disc.get_rect(), 1)
    surf.blit(disc, (cx - int(w * 0.7), cy + h // 2 - 4))
    # erase the lower half of the legs (cover with transparent)
    leg_eraser = pygame.Surface((int(w * 0.9), int(h * 0.18)), pygame.SRCALPHA)
    surf.blit(leg_eraser, (cx - int(w * 0.45), cy + int(h * 0.32)))


def draw_chibi_descriptor(surf, descriptor):
    """Draw a descriptor-driven world sprite onto surf (256x256, SRCALPHA).
    descriptor fields: stance, archetype, weapon, palette{primary,secondary,
    accent}, features[], build, motif. Dispatches by stance, then archetype,
    applies features, then draws the weapon."""
    cx, cy = 128, 150
    pal = descriptor["palette"]
    primary = pal["primary"]
    outline = shade(primary, 0.3)
    archetype = descriptor["archetype"]
    build = descriptor.get("build", "average")
    stance = descriptor.get("stance", "upright")

    if stance == "upright":
        fn = _ARCH_DRAW.get(archetype, _arch_knight)
        hx, hy, hr, w, h = fn(surf, cx, cy, pal, outline, build)
    elif stance == "floating":
        fn = _ARCH_DRAW.get(archetype, _arch_knight)
        hx, hy, hr, w, h = fn(surf, cx, cy, pal, outline, build)
        if w and h:
            _floating_modifier(surf, cx, cy, w, h, pal, outline)
    else:
        # quadruped / mounted / flying: stub falls back to an upright body
        # until the real drawers land (Tasks 2-4). Still returns a valid box.
        fn = _ARCH_DRAW.get(archetype, _arch_knight)
        hx, hy, hr, w, h = fn(surf, cx, cy, pal, outline, build)

    features = [f for f in descriptor.get("features", []) if f != "helmet"]
    if w and h:
        _apply_features(surf, cx, cy, w, h, hx, hy, hr, features, pal, outline)
    weapon = descriptor.get("weapon", "sword")
    if weapon and weapon != "none":
        draw_weapon(surf, cx, cy, weapon, pal["accent"], outline,
                    {"fire": "fire", "water": "water", "wind": "wind",
                     "light": "light", "dark": "dark"}.get(descriptor.get("motif"), "fire"))
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_stance_dispatch.py` → `STANCE DISPATCH OK`.
Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_new_primitives.py` → `NEW PRIMITIVES OK`.
Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` → `OK`.

- [ ] **Step 5: Commit**

```bash
git add src/assets_gen/generate.py tools/verify_stance_dispatch.py
git commit -m "feat: stance field + 2-level dispatch + floating modifier"
```

---

### Task 2: quadruped stance drawer

**Goal:** Implement `_arch_quadruped` — a 4-legged body (bear/wolf/cat/hound base) + feature mods (shell/stinger/fur/insect_carapace/void_fins) so Volibear/Warwick/RekSai/Rammus/Skarner/Khazix/etc. render as actual quadrupeds, not humanoids.

**Files:**
- Modify: `src/assets_gen/generate.py` (add `_arch_quadruped` + wire into stance dispatch + feature mods: `_add_shell`, `_add_stinger`, `_add_fur`, `_add_insect_carapace`, `_add_void_fins`)
- Test: `tools/verify_stance_dispatch.py` (append quadruped tests)

**Acceptance Criteria:**
- [ ] `draw_chibi_descriptor` with `stance: "quadruped"` renders a 4-legged body (not a humanoid) — the silhouette reads as a quadruped: a horizontal torso on 4 legs + a head at one end.
- [ ] The quadruped drawer returns `(hx, hy, hr, w, h)` so features/weapon place consistently.
- [ ] Feature mods: `shell` (Rammus — rounded shell on back), `stinger` (Skarner — tail stinger), `fur` (Volibear/Warwick — fur texture), `insect_carapace` (Khazix/Belveth — segmented plates), `void_fins` (KogMaw/Chogath — void fins) each add visible pixels (coverage > base quadruped).
- [ ] Pixel-art (no AA), in-bounds (256×256), coverage > 0.
- [ ] `tools/verify_stance_dispatch.py` new tests pass: quadruped renders 256×256 + coverage > 0 + coverage differs from upright knight (it's a different silhouette); each feature mod adds pixels.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_stance_dispatch.py` → `STANCE DISPATCH OK`.

**Steps:**

- [ ] **Step 1: Append the failing tests** to `tools/verify_stance_dispatch.py`:

```python
QUAD = {**BASE, "stance": "quadruped", "archetype": "quadruped"}

def test_quadruped_renders_and_differs_from_upright():
    s_q = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_q, QUAD)
    s_u = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_u, {**BASE, "stance": "upright"})
    assert s_q.get_size() == (256, 256) and _cov(s_q) > 0
    assert _cov(s_q) != _cov(s_u), "quadruped must differ from upright knight"

def test_quadruped_feature_mods_add_pixels():
    base = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(base, QUAD)
    base_c = _cov(base)
    for feat in ("shell", "stinger", "fur", "insect_carapace", "void_fins"):
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        draw_chibi_descriptor(s, {**QUAD, "features": [feat]})
        assert _cov(s) > base_c + 0.003, f"quadruped feature {feat} didn't add pixels"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_stance_dispatch.py`
Expected: FAIL — quadruped currently falls back to knight (stub from Task 1), so `test_quadruped_renders_and_differs_from_upright` fails (same coverage as upright).

- [ ] **Step 3: Implement `_arch_quadruped` + the 5 feature mods** in `src/assets_gen/generate.py`. Place `_arch_quadruped` near the other `_arch_*` functions (before `_ARCH_DRAW`). It draws: a horizontal torso (dithered, rounded), 4 legs (angled blocks), a head at the front (circle + ears + eye), a tail at the back. Returns `(hx, hy, hr, w, h)`. The 5 feature mods (`_add_shell`, `_add_stinger`, `_add_fur`, `_add_insect_carapace`, `_add_void_fins`) are added to `_apply_features` as new branches. Use `shade`/`px_dither_surf`/`pygame.draw` blocks (no AA). Wire `stance == "quadruped"` in `draw_chibi_descriptor` to call `_arch_quadruped`.

```python
def _arch_quadruped(surf, cx, cy, pal, outline, build):
    """Quadruped: 4-legged beast body (bear/wolf/cat/hound base). Horizontal
    torso on 4 legs + head at the front + tail at the back. Pixel-art, no AA."""
    sx, sy = BUILD_SCALE.get(build, (1.18, 0.92))
    w, h = int(120 * sx), int(78 * sy)  # wider than tall (quadruped)
    primary = pal["primary"]; sec = pal["secondary"]
    # shadow
    sh = pygame.Surface((int(w * 1.4), 14), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
    surf.blit(sh, (cx - int(w * 0.7), cy + h // 2 - 2))
    _motif_aura(surf, cx, cy, "nature")
    # horizontal torso (dithered, rounded rect)
    tw, th = int(w * 0.78), int(h * 0.52)
    tx, ty = cx - tw // 2, cy - th // 2 + 6
    torso = px_dither_surf(tw, th, shade(sec, 1.05), shade(primary, 0.45))
    clip_to_rect(torso, pygame.Rect(0, 0, tw, th), border_radius=10)
    surf.blit(torso, (tx, ty))
    pygame.draw.rect(surf, outline, (tx, ty, tw, th), 2, border_radius=10)
    # 4 legs (angled blocks under the torso)
    lw, lh = int(tw * 0.16), int(h * 0.42)
    ly = ty + th - 2
    for i, lx in enumerate((tx + 6, tx + tw * 0.32, tx + tw * 0.62, tx + tw - lw - 6)):
        leg = px_dither_surf(lw, lh, shade(primary, 0.7), shade(primary, 0.42))
        clip_to_rect(leg, pygame.Rect(0, 0, lw, lh), border_radius=3)
        surf.blit(leg, (lx, ly))
        pygame.draw.rect(surf, outline, (lx, ly, lw, lh), 2, border_radius=3)
    # head at the front (right side) — circle + 2 ears + eye
    hr = int(h * 0.26)
    hx, hy = tx + tw - hr + 4, ty + 2
    head = px_dither_surf(hr * 2, hr * 2, shade(primary, 1.1), shade(primary, 0.6))
    clip_to_circle(head, (hr, hr), hr - 1)
    surf.blit(head, (hx - hr, hy - hr))
    pygame.draw.circle(surf, outline, (hx, hy), hr, 2)
    for side in (-1, 1):
        ex = hx + side * (hr - 2)
        pygame.draw.polygon(surf, shade(sec, 1.1),
            [(ex - 5, hy - hr + 2), (ex + 5, hy - hr + 2), (ex, hy - hr - 10)])
        pygame.draw.polygon(surf, outline,
            [(ex - 5, hy - hr + 2), (ex + 5, hy - hr + 2), (ex, hy - hr - 10)], 2)
    pygame.draw.rect(surf, (40, 40, 60), (hx + 2, hy - 2, 3, 3))  # eye
    # tail at the back (left side) — a curved block chain
    tx0 = tx - 4; ty0 = ty + 4
    for i in range(5):
        t = i / 4.0
        px_ = tx0 - int(t * 10)
        py_ = ty0 - int((1 - (1 - t) ** 2) * 14)
        r = 4 - i // 2
        pygame.draw.circle(surf, shade(sec, 0.9), (px_, py_), r)
        pygame.draw.circle(surf, outline, (px_, py_), r, 1)
    return (hx, hy, hr, w, h)


def _add_shell(surf, cx, cy, w, h, color, outline):
    """Rounded shell on the back (Rammus)."""
    sx, sy = cx, cy - 4
    pygame.draw.ellipse(surf, shade(color, 1.1), (sx - int(w*0.30), sy - int(h*0.28), int(w*0.60), int(h*0.56)))
    pygame.draw.ellipse(surf, outline, (sx - int(w*0.30), sy - int(h*0.28), int(w*0.60), int(h*0.56)), 2)
    for i in range(3):
        pygame.draw.line(surf, shade(color, 0.7), (sx, sy - int(h*0.20) + i*8), (sx, sy + int(h*0.20) + i*8), 1)

def _add_stinger(surf, cx, cy, w, h, color, outline):
    """Tail stinger (Skarner)."""
    pygame.draw.polygon(surf, shade(color, 1.2),
        [(cx - int(w*0.42), cy - 4), (cx - int(w*0.52), cy - 18), (cx - int(w*0.38), cy - 10)])
    pygame.draw.polygon(surf, outline,
        [(cx - int(w*0.42), cy - 4), (cx - int(w*0.52), cy - 18), (cx - int(w*0.38), cy - 10)], 2)

def _add_fur(surf, cx, cy, w, h, color, outline):
    """Fur tufts along the back (Volibear/Warwick)."""
    tx = cx - int(w * 0.30)
    for i in range(7):
        fx = tx + i * int(w * 0.10)
        pygame.draw.polygon(surf, shade(color, 0.85),
            [(fx, cy - int(h*0.18)), (fx + 4, cy - int(h*0.30)), (fx + 8, cy - int(h*0.18))])

def _add_insect_carapace(surf, cx, cy, w, h, color, outline):
    """Segmented chitinous plates (Khazix/Belveth)."""
    for i in range(4):
        py = cy - int(h*0.20) + i * int(h*0.10)
        pygame.draw.rect(surf, shade(color, 0.9), (cx - int(w*0.28), py, int(w*0.56), int(h*0.06)), border_radius=2)
        pygame.draw.rect(surf, outline, (cx - int(w*0.28), py, int(w*0.56), int(h*0.06)), 1, border_radius=2)

def _add_void_fins(surf, cx, cy, w, h, color, outline):
    """Void fins along the back (KogMaw/Chogath)."""
    tx = cx - int(w * 0.22)
    for i in range(4):
        fx = tx + i * int(w * 0.13)
        pygame.draw.polygon(surf, shade(color, 1.15),
            [(fx, cy - int(h*0.16)), (fx + 3, cy - int(h*0.34)), (fx + 9, cy - int(h*0.16))])
        pygame.draw.polygon(surf, outline,
            [(fx, cy - int(h*0.16)), (fx + 3, cy - int(h*0.34)), (fx + 9, cy - int(h*0.16))], 1)
```

Wire into `draw_chibi_descriptor`'s `elif stance == "quadruped"` branch: call `_arch_quadruped`. Add the 5 feature branches to `_apply_features`.

- [ ] **Step 4: Run the test to verify it passes**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_stance_dispatch.py` → `STANCE DISPATCH OK`.

- [ ] **Step 5: Commit**

```bash
git add src/assets_gen/generate.py tools/verify_stance_dispatch.py
git commit -m "feat: quadruped stance drawer + 5 feature mods (shell/stinger/fur/insect/void)"
```

---

### Task 3: mounted + flying stance drawers

**Goal:** Implement `_draw_mounted` (rider on a mount — reuses an upright archetype for the rider + a mount body) and `_arch_flying_bird` + `_arch_flying_dragon` (winged bodies). Corki/Sejuani/Nunu/Kled/Kindred/Hecarim render as rider+mount; Anivia as a bird; AurelionSol as a serpentine dragon.

**Files:**
- Modify: `src/assets_gen/generate.py` (add `_draw_mounted`, `_arch_flying_bird`, `_arch_flying_dragon` + a `mount_kind` descriptor field + wire into stance dispatch)
- Test: `tools/verify_stance_dispatch.py` (append mounted/flying tests)

**Acceptance Criteria:**
- [ ] `stance: "mounted"` renders a rider (upright humanoid, smaller, top) on a mount (beast/vehicle body, bottom) — two distinct bodies stacked. The `mount_kind` field (`boar`/`yeti`/`lizard`/`bird`/`wolf`/`plane`) varies the mount silhouette slightly (at least color/shape of the mount body).
- [ ] `stance: "flying"` with `archetype: "flying_bird"` renders a bird body (wings + beak + tail); `archetype: "flying_dragon"` renders a serpentine dragon (long body + wings + horns). Both differ from upright.
- [ ] All render 256×256, coverage > 0, in-bounds, pixel-art (no AA).
- [ ] Tests pass: mounted renders + coverage > upright (rider+mount = more pixels); flying_bird + flying_dragon each render + differ from each other + from upright.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_stance_dispatch.py` → `STANCE DISPATCH OK`.

**Steps:**

- [ ] **Step 1: Append the failing tests** to `tools/verify_stance_dispatch.py`:

```python
def test_mounted_renders_rider_plus_mount():
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s, {**BASE, "stance": "mounted", "archetype": "knight", "mount_kind": "boar"})
    s_u = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_u, {**BASE, "stance": "upright"})
    assert s.get_size() == (256, 256) and _cov(s) > 0
    assert _cov(s) > _cov(s_u) + 0.01, "mounted (rider+mount) should have more coverage than upright alone"

def test_flying_bird_and_dragon_render_and_differ():
    s_b = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s_b, {**BASE, "stance": "flying", "archetype": "flying_bird"})
    s_d = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s_d, {**BASE, "stance": "flying", "archetype": "flying_dragon"})
    assert _cov(s_b) > 0 and _cov(s_d) > 0
    assert _cov(s_b) != _cov(s_d), "bird and dragon must differ"
```

- [ ] **Step 2: Run the test to verify it fails** (mounted/flying still stub to knight).

- [ ] **Step 3: Implement** `_draw_mounted` (draws a mount body at the bottom + calls an upright archetype for the rider at the top, offset), `_arch_flying_bird` (wings + round body + beak), `_arch_flying_dragon` (long serpentine body + wings + horns). Wire `stance == "mounted"` → `_draw_mounted`; `stance == "flying"` → `_FLY_DRAW[archetype]` (new map). Pixel-art, no AA, in-bounds. (Full code in the implementer's hands — follow the `_arch_quadruped` style; return `(hx, hy, hr, w, h)`.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_stance_dispatch.py` → `STANCE DISPATCH OK`.

- [ ] **Step 5: Commit**

```bash
git add src/assets_gen/generate.py tools/verify_stance_dispatch.py
git commit -m "feat: mounted (rider+mount) + flying (bird/dragon) stance drawers"
```

---

### Task 4: new upright body drawers (rock_giant, treant, blob, naga, scarecrow)

**Goal:** Implement 5 new upright body drawers for champs whose body can't be feature-modded on existing archetypes: `rock_giant` (Malphite/Galio/Ornn), `treant` (Maokai/Ivern), `blob` (Zac), `naga` (Cassiopeia/Nami), `scarecrow` (Fiddlesticks).

**Files:**
- Modify: `src/assets_gen/generate.py` (add `_arch_rock_giant`, `_arch_treant`, `_arch_blob`, `_arch_naga`, `_arch_scarecrow` + register in `_ARCH_DRAW`)
- Test: `tools/verify_stance_dispatch.py` (append body tests)

**Acceptance Criteria:**
- [ ] Each new body renders 256×256, coverage > 0, in-bounds, pixel-art (no AA).
- [ ] Each differs from the existing knight (distinct silhouette): rock_giant (craggy bulky), treant (bark texture + branches), blob (amorphous rounded), naga (humanoid upper + serpentine lower), scarecrow (gaunt thin + straw).
- [ ] Registered in `_ARCH_DRAW` so `stance: "upright", archetype: "rock_giant"` dispatches correctly.
- [ ] Tests pass for all 5.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_stance_dispatch.py` → `STANCE DISPATCH OK`.

**Steps:**

- [ ] **Step 1: Append the failing tests** (one per body, asserting render + differ-from-knight).

- [ ] **Step 2: Run to verify fail** (bodies not in `_ARCH_DRAW` → fall back to knight → same coverage).

- [ ] **Step 3: Implement** the 5 drawers + register in `_ARCH_DRAW`. Each ~40-70 lines, pixel-art, returns `(hx, hy, hr, w, h)`. (Follow `_arch_quadruped` style; the implementer authors the pixel-art for each silhouette.)

- [ ] **Step 4: Run to verify pass** → `STANCE DISPATCH OK`.

- [ ] **Step 5: Commit**

```bash
git add src/assets_gen/generate.py tools/verify_stance_dispatch.py
git commit -m "feat: 5 new upright bodies (rock_giant/treant/blob/naga/scarecrow)"
```

---

### Task 5: new feature primitives (15) + dual_pistols weapon

**Goal:** Implement the 15 new feature primitives (tail, long_hair, pointed_ears, large_horns, feathered_wings, dragon_wings, fur, scales, hat, beard, chains, spider_legs, bovine_head, glowing_eyes) + the `dual_pistols` weapon drawer. These let the VLM depict signature features on top of the body drawers.

**Files:**
- Modify: `src/assets_gen/generate.py` (add `_add_tail`, `_add_long_hair`, `_add_pointed_ears`, `_add_large_horns`, `_add_feathered_wings`, `_add_dragon_wings`, `_add_fur_body`, `_add_scales`, `_add_hat`, `_add_beard`, `_add_chains`, `_add_spider_legs`, `_add_bovine_head`, `_add_glowing_eyes` + `dual_pistols` branch in `draw_weapon` + wire all features into `_apply_features`)
- Test: `tools/verify_stance_dispatch.py` (append feature tests)

**Acceptance Criteria:**
- [ ] Each of the 14 new features (note: `fur` for upright is `_add_fur_body`, distinct from the quadruped `_add_fur` from Task 2 — same vocab key `fur`, dispatched by stance or unified) renders without error, adds visible pixels (coverage > knight-base + 0.003), in-bounds.
- [ ] `dual_pistols` weapon renders (two pistol shapes) — adds pixels vs `weapon: "none"`.
- [ ] All wired into `_apply_features` (feature branches) + `draw_weapon` (dual_pistols branch).
- [ ] Tests pass for all 15.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_stance_dispatch.py` → `STANCE DISPATCH OK`.

**Steps:**

- [ ] **Step 1: Append the failing tests** (one per feature: render knight + feature → coverage > knight base; dual_pistols → coverage > none).

- [ ] **Step 2: Run to verify fail** (features not in `_apply_features` → no pixels added).

- [ ] **Step 3: Implement** the 14 `_add_*` functions + the `dual_pistols` weapon branch + wire into `_apply_features`/`draw_weapon`. Pixel-art, no AA, in-bounds. (The implementer authors each; ~20-40 lines each.)

- [ ] **Step 4: Run to verify pass** → `STANCE DISPATCH OK`.

- [ ] **Step 5: Commit**

```bash
git add src/assets_gen/generate.py tools/verify_stance_dispatch.py
git commit -m "feat: 14 new feature primitives + dual_pistols weapon"
```

---

### Task 6: float_eye unique body + renderer vocab consolidation

**Goal:** Implement `_arch_float_eye` (Velkoz — central eye + floating tentacles) as the last unique body. Consolidate the renderer vocab: produce a single `RENDERER_VOCAB` dict (stance + archetype-per-stance + features + weapons) that both the renderer and the VLM client import, so they can't drift.

**Files:**
- Modify: `src/assets_gen/generate.py` (add `_arch_float_eye` + a `RENDERER_VOCAB` module-level dict listing all valid stance/archetype/feature/weapon values)
- Modify: `src/build/vlm_client.py` (import `RENDERER_VOCAB` from `generate.py` instead of hardcoding `VOCAB`)
- Test: `tools/verify_stance_dispatch.py` (append float_eye + vocab-consistency tests)

**Acceptance Criteria:**
- [ ] `stance: "floating", archetype: "float_eye"` renders a central eye + tentacles (Velkoz) — differs from a floating humanoid.
- [ ] `RENDERER_VOCAB` in `generate.py` lists every stance/archetype/feature/weapon the renderer actually dispatches (the single source of truth).
- [ ] `vlm_client.py`'s `VOCAB` is derived from `RENDERER_VOCAB` (imported), so the VLM-facing vocab matches the renderer exactly — no drift.
- [ ] `tools/verify_vlm_client.py` still passes (the import doesn't break validation).
- [ ] Tests pass: float_eye renders + differs; `RENDERER_VOCAB` keys ⊇ the dispatched values.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_stance_dispatch.py` → `STANCE DISPATCH OK`; `SDL_VIDEODRIVER=dummy python3 tools/verify_vlm_client.py` → `VLM CLIENT OK`.

**Steps:**

- [ ] **Step 1: Append failing tests** (float_eye render + differ; a check that `RENDERER_VOCAB` exists with stance/archetype/features/weapon keys).

- [ ] **Step 2: Run to verify fail.**

- [ ] **Step 3: Implement** `_arch_float_eye` + define `RENDERER_VOCAB` (a dict literal listing the values) + update `vlm_client.py` to `from src.assets_gen.generate import RENDERER_VOCAB` and build `VOCAB` from it. Keep `_validate` working (the field names are unchanged).

- [ ] **Step 4: Run to verify pass** → both `STANCE DISPATCH OK` + `VLM CLIENT OK`.

- [ ] **Step 5: Commit**

```bash
git add src/assets_gen/generate.py src/build/vlm_client.py tools/verify_stance_dispatch.py
git commit -m "feat: float_eye body + RENDERER_VOCAB single source of truth"
```

---

## Phase 2 — VLM pipeline rewrite (grounding + canonical gate)

### Task 7: canon-grounded VLM client (describe/critique + canon identity)

**Goal:** Rewrite `vlm_client.py` so `describe` and `critique` take the champ's canonical identity (name, title, faction, role, abilities, lore) + the splash, and produce/judge a stance-aware descriptor. Add a `canon_identity(champ)` helper that builds the context text.

**Files:**
- Modify: `src/build/vlm_client.py` (`_DESCRIBE_SYS`/`_CRITIQUE_SYS` rewrite + `describe`/`critique` accept a `champ`/`canon` context + `VOCAB` now includes `stance`)
- Test: `tools/verify_vlm_client.py` (update FakeVLM tests for the new signatures)

**Acceptance Criteria:**
- [ ] `describe(ref, fallback, champ)` builds a context string (name/title/faction/role/abilities/lore) + sends it with the splash; returns a descriptor WITH a `stance` field (validated against `RENDERER_VOCAB`).
- [ ] `critique(ref, sprite, last_good, champ)` judges canonical identity capture (stance/body/features/colors) + returns `canonical_match`/`stance_captured`/`suggested_descriptor`.
- [ ] `_validate` validates the `stance` field too (clamps to a valid stance).
- [ ] FakeVLM tests pass (no network): describe returns a stance; critique returns canonical_match; garbage → fallback; fenced JSON stripped.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_vlm_client.py` → `VLM CLIENT OK`.

**Steps:**

- [ ] **Step 1: Update the failing tests** in `tools/verify_vlm_client.py` for the new `describe(ref, fallback, champ)` / `critique(ref, sprite, last_good, champ)` signatures + the `stance` field in the descriptor + `canonical_match` in the critique output.

- [ ] **Step 2: Run to verify fail** (signature mismatch).

- [ ] **Step 3: Rewrite** `_DESCRIBE_SYS`/`_CRITIQUE_SYS` (canon-grounded, stance-aware, per Section 3 of the spec) + `describe`/`critique` to accept `champ` + build context + validate `stance`. Add `_champ_context(champ)` helper.

- [ ] **Step 4: Run to verify pass** → `VLM CLIENT OK`.

- [ ] **Step 5: Commit**

```bash
git add src/build/vlm_client.py tools/verify_vlm_client.py
git commit -m "feat: canon-grounded VLM client (stance-aware describe/critique + champ context)"
```

---

### Task 8: canonical gate + canon-grounded sprite loop

**Goal:** Add a canonical gate (`VLMClient.canon_gate(sprite, champ, canon)` → canonical_match + per-axis) and rewrite `vlm_sprite_loop` to use `canonical_match` (stop at ≥ 7) instead of splash `match`. The loop now takes `champ` + `canon` and calls the canon-grounded describe/critique.

**Files:**
- Modify: `src/build/vlm_client.py` (add `canon_gate` method)
- Modify: `src/build/sprite_loop.py` (`vlm_sprite_loop` takes `champ`/`canon`, uses canonical_match, stop at 7)
- Test: `tools/verify_sprite_loop.py` (update FakeVLM tests for canonical_match)

**Acceptance Criteria:**
- [ ] `VLMClient.canon_gate(sprite_path, champ, canon)` returns `{canonical_match, stance_captured, body_shape_score, features_captured, features_missing, colors_captured, recognizable, verdict}`.
- [ ] `vlm_sprite_loop` stops when `critique.canonical_match ≥ 7` (not splash match); keeps best-canonical_match round; writes `canonical_match` (not `match`) to the cache.
- [ ] FakeVLM tests pass: loop stops at canonical_match ≥ 7; keeps best; cache round-trips with `canonical_match`.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_sprite_loop.py` → `SPRITE LOOP OK`.

**Steps:**

- [ ] **Step 1: Update the failing tests** in `tools/verify_sprite_loop.py` (FakeVLM returns `canonical_match`/`stance_captured` instead of `match`/`ok`; loop stops at canonical_match ≥ 7).

- [ ] **Step 2: Run to verify fail.**

- [ ] **Step 3: Implement** `canon_gate` in `vlm_client.py` + rewrite `vlm_sprite_loop` to take `champ`/`canon`, use `canonical_match`, stop at 7, write `canonical_match` to cache.

- [ ] **Step 4: Run to verify pass** → `SPRITE LOOP OK`.

- [ ] **Step 5: Commit**

```bash
git add src/build/vlm_client.py src/build/sprite_loop.py tools/verify_sprite_loop.py
git commit -m "feat: canonical gate + canon-grounded sprite loop (stop at canonical_match>=7)"
```

---

### Task 9: canonical gate script + bake CLI update

**Goal:** Write `tools/verify_canon_gate.py` (the honest gate: reads `descriptors.json` + sends sprite + canon to the VLM → canonical_match; pass = mean ≥ 6, recognizable ≥ 70%, stance ≥ 90%). Update `run_sprite_bake`/`build_champions` CLI to pass `champ`/`canon` through the loop.

**Files:**
- Create: `tools/verify_canon_gate.py`
- Modify: `src/build/sprite_loop.py` (`run_sprite_bake`/`_process_one` pass `champ` + build canon per champ)
- Modify: `src/build/build_champions.py` (CLI unchanged flags; passes champ dicts through)
- Test: `tools/verify_canon_gate.py` (self-test with a FakeVLM gate)

**Acceptance Criteria:**
- [ ] `tools/verify_canon_gate.py` reads every `descriptors.json` + the champ's canon identity + the sprite → canonical_match per champ; prints mean, recognizable %, stance %; exits 0 if mean ≥ 6 AND recognizable ≥ 70% AND stance ≥ 90%, else 1.
- [ ] `run_sprite_bake` builds the canon identity per champ (via a `canon_identity(champ)` call) and passes `champ`/`canon` to `vlm_sprite_loop`.
- [ ] The CLI `--vlm-loop --skins 0` runs the canon-grounded bake end-to-end (network smoke for one champ).

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_canon_gate.py` (with a FakeVLM-injected path for the self-test) → `CANON GATE OK`; plus a real one-champ network smoke.

**Steps:**

- [ ] **Step 1: Write the gate script** (`tools/verify_canon_gate.py`) per the spec's gate section.

- [ ] **Step 2: Update `run_sprite_bake`/`_process_one`** to build + pass `champ`/`canon`.

- [ ] **Step 3: Self-test the gate** with a FakeVLM (monkeypatch `canon_gate`) + a real one-champ network smoke (`--champs Ahri --skins 0 --max-iters 3`).

- [ ] **Step 4: Run** the self-test → `CANON GATE OK`; the smoke exits 0.

- [ ] **Step 5: Commit**

```bash
git add tools/verify_canon_gate.py src/build/sprite_loop.py src/build/build_champions.py
git commit -m "feat: canonical gate script + bake CLI passes champ/canon through"
```

---

## Phase 3 — Re-bake 170 Original + canonical gate

### Task 10: P3 re-bake 170 Original + canonical gate (USER GATE)

**USER-ORDERED GATE — NON-SKIPPABLE.** This task was requested by the user. Close only after every `acceptanceCriteria` item has been re-validated independently with captured output.

**Goal:** Re-bake all 170 Original skins with the new renderer + canon-grounded pipeline. Prove the canonical gate hits the targets: mean ≥ 6, recognizable ≥ 70%, stance ≥ 90%. Commit the re-baked sprites + descriptors.

**Files:**
- Modify: `assets/characters/*/sprite.png` (170 re-baked), `assets/characters/*/descriptors.json` (170 re-baked with canonical_match + stance)
- Test: `tools/verify_canon_gate.py` (the gate), `tools/verify_assets.py` (must stay green)

**Acceptance Criteria:**
- [ ] `SDL_VIDEODRIVER=dummy python3 -m src.build.build_champions --sprites --vlm-loop --skins 0 --max-iters 10 --concurrency 4 --force` completes for all 170 champs.
- [ ] `SDL_VIDEODRIVER=dummy python3 tools/verify_canon_gate.py` passes: mean canonical_match ≥ 6.0, recognizable ≥ 70% (≥119/170), stance_captured ≥ 90% (≥153/170). Captured output.
- [ ] `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` still passes (every sprite 256×256, coverage > 0, distinctness).
- [ ] The 21-test acceptance suite (`/tmp/verify_complete.py`) passes: `21 passed, 0 failed` (no game-logic regression — runtime loads PNGs).
- [ ] The 170 re-baked `sprite.png` + `descriptors.json` are committed.
- [ ] A before/after is captured: the old mean (1.18) → new mean (≥6), proving the overhaul worked.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_canon_gate.py` → `CANON GATE OK (mean=X.XX, recognizable=Y%, stance=Z%)`; `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` → `OK`; `SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py` → `21 passed, 0 failed`.

**Steps:**

- [ ] **Step 1: Run the full P3 re-bake** (live, concurrency 4, `--force` to override the old cache):
`SDL_VIDEODRIVER=dummy python3 -m src.build.build_champions --sprites --vlm-loop --skins 0 --max-iters 10 --concurrency 4 --force`
Capture the aggregate.

- [ ] **Step 2: Run the canonical gate** → capture mean/recognizable/stance. Must hit the targets.

- [ ] **Step 3: Run verify_assets + 21-test** → both green.

- [ ] **Step 4: Spot-check 5 distinctive champs** (Ahri/Volibear/Thresh/Malphite/AurelionSol) — capture their canonical_match + stance_captured from `descriptors.json` (proving the non-humanoid champs now render with the right stance).

- [ ] **Step 5: Commit** the re-baked assets.

```bash
git add assets/characters/*/sprite.png assets/characters/*/descriptors.json
git commit -m "assets: P3 canon-grounded re-bake of 170 Original (canonical mean>=6, recognizable>=70%)"
```

**Gate failure handling:** If the canonical gate fails (mean < 6, or recognizable < 70%, or stance < 90%), do NOT commit. Report BLOCKED with the per-axis numbers + which champs/clusters failed. The coordinator decides: iterate the failing renderer primitive (Task 4/5) for that cluster, raise max-iters, or adjust. Do NOT lower the targets.

---

## Phase 4 — Re-bake 1780 per-skin

### Task 11: P4 re-bake 1780 per-skin + extended verify (USER GATE)

**USER-ORDERED GATE — NON-SKIPPABLE.**

**Goal:** Re-bake all ~1780 per-skin sprites with the new renderer (resumable). Extend `verify_assets` for the new archetypes/stances. Run the canonical gate on a sample + the full 21-test suite.

**Files:**
- Modify: `assets/characters/*/sprites/*.png` + `descriptors.json` (the re-bake output)
- Modify: `tools/verify_assets.py` (update archetype-distinctness for the new stance/archetype set)

**Acceptance Criteria:**
- [ ] `--skins all` re-bakes `sprites/{idx}.png` for all ~1780 skins (resumable; completes).
- [ ] `verify_assets` passes (every per-skin sprite 256×256 + coverage > 0; descriptors.json per skin; distinctness updated for new archetypes).
- [ ] A canonical-gate SAMPLE (e.g. 30 champs × skin 0) passes: sample mean ≥ 6, sample recognizable ≥ 70% (proves the renderer held across the bake, not just the first 170).
- [ ] The 21-test acceptance suite passes: `21 passed, 0 failed`.
- [ ] The per-skin sprites + descriptors are committed.

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` → `OK`; `SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py` → `21 passed, 0 failed`; the sample canon gate → sample mean ≥ 6.

**Steps:**

- [ ] **Step 1: Update `verify_assets`** archetype-distinctness for the new stance/archetype set.

- [ ] **Step 2: Run the full P4 re-bake** (live, `--skins all --concurrency 4 --force`).

- [ ] **Step 3: Run verify_assets + the 21-test + a 30-champ canon-gate sample.**

- [ ] **Step 4: Commit** the re-baked per-skin assets.

```bash
git add assets/characters/*/sprites/ assets/characters/*/descriptors.json tools/verify_assets.py
git commit -m "assets: P4 canon-grounded re-bake of ~1780 per-skin sprites"
```

---

## Self-Review (completed by the planner)

**1. Spec coverage:**
- Stance-driven 2-level dispatch: Task 1. ✓
- 5 stances (upright existing + quadruped/mounted/flying/floating): Tasks 1-4. ✓
- ~8 new body drawers (quadruped + mounted + flying_bird + flying_dragon + rock_giant + treant + blob + naga + scarecrow + float_eye): Tasks 2-4, 6. ✓ (10 bodies — spec said ~8; float_eye + scarecrow + the flying pair round it to 10.)
- 2 stance modifiers (floating_modifier + the float_eye unique): Tasks 1, 6. ✓
- ~15 new features + dual_pistols: Task 5. ✓
- RENDERER_VOCAB single source of truth: Task 6. ✓
- Canon-grounded describe/critique: Task 7. ✓
- Canonical gate + canon-grounded loop (stop at canonical_match ≥ 7): Task 8. ✓
- Canonical gate script (mean ≥ 6, recognizable ≥ 70%, stance ≥ 90%): Task 9. ✓
- Re-bake 170 Original + gate: Task 10. ✓
- Re-bake 1780 per-skin + extended verify: Task 11. ✓
- Hard constraint (no Read on PNG/JPG): every test asserts coverage/load-path, never Read. ✓
- Backward-compat: Task 1's no-stance default = upright = byte-identical. ✓

**2. Placeholder scan:** No TBD/TODO/"add error handling"/"similar to Task N". The pixel-art bodies (Tasks 2-5) give the implementer the drawer structure + helpers + the test contract, and explicitly hand the per-silhouette pixel-art authoring to the implementer (this is unavoidably creative work — the plan gives the silhouette spec + the test, the implementer draws). Task 1's code is complete; Tasks 2/3/4/5 give the quadruped code fully (Task 2) + the silhouette spec + test for the rest (the implementer authors each following the `_arch_quadruped` template). This is the right granularity for pixel-art authoring — a plan can't hand-draw 26 silhouettes verbatim.

**3. Type consistency:** `draw_chibi_descriptor(surf, descriptor)` reads `descriptor["stance"]` (Task 1) — same field the VLM produces (Task 7) + the cache stores (Task 8). `_ARCH_DRAW` map (Task 4/6) keys match `RENDERER_VOCAB["archetype"]` (Task 6) match `VOCAB` in `vlm_client.py` (Task 6/7). `vlm_sprite_loop(champ, canon, ...)` (Task 8) matches `run_sprite_bake`/`_process_one` passing `champ`/`canon` (Task 9). `canon_gate(sprite, champ, canon)` (Task 8) matches the gate script's call (Task 9). `canonical_match` (Task 8) matches the gate's read (Task 9/10). ✓
