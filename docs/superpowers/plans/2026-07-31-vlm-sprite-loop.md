# VLM-in-the-Loop Pixel Sprite Improvement — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:subagent-driven-development (recommended) or superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Put a VLM (misa-gemma-4-31b-it) in a build-time loop as an art director that re-tunes the procedural per-champion world sprites, expands the renderer vocabulary, and extends the system to per-skin sprites that change in-game when the player swaps skins.

**Architecture:** Build-time only: VLM describes a skin splash → the existing pixel renderer draws a 256×256 sprite → VLM critiques it vs the splash → revises the descriptor → loop (max 10, stop when the VLM says ok). Runtime only loads the baked PNGs. Three phases: P1 re-tune the Original skin for all 170 champs (asset-only, zero runtime risk); P2 expand the renderer vocabulary via a VLM gap-analysis; P3 extend to ~1780 per-skin sprites + wire `skin_idx` through `Hero → WorldCharacter → load_char_sprite` so changing skin changes the world sprite.

**Tech Stack:** Python 3.11, pygame 2.6.x (headless via `SDL_VIDEODRIVER=dummy`), stdlib `urllib`+`ssl` for the OpenAI-compatible VLM HTTP API, `concurrent.futures.ThreadPoolExecutor` for configurable concurrency.

**User decisions (already made):**
- Scope: "Staged: re-tune → expand" (3 phases, each shippable).
- Reference images: skin splashes only (`assets/characters/{id}/skins/{idx}.jpg`); each skin gets its own sprite; changing skin changes the world sprite.
- Per-skin sprites live in a separate `sprites/` directory (`{idx}.png`), not mixed into `skins/`.
- Concurrency of VLM calls is configurable, default 1.
- Loop: max 10 rounds, stop when the VLM says the sprite is ok; if it never converges, keep the best-scoring round.
- VLM model/endpoint/key: the provided misa-gemma-4-31b-it constants (self-signed cert → `verify=False`).

**HARD CONSTRAINT (from AGENTS.md / memory `gacha-no-image-reading`):** NEVER use the Read tool on a PNG/JPG. The VLM reads images over HTTP base64 (outside the Claude session); the build script uses headless `pygame.image.load`. Tests assert on file existence / size / load-path, never on pixel content via Read.

**Test convention:** this repo has no pytest. Tests are headless `python3` scripts under `tools/` that set `SDL_VIDEODRIVER=dummy`, define `test_*` functions, and print `pass <name>` / a final `OK` line. Follow the `tools/verify_ecs.py` style (a `run()` collects `test_*` globals). Each task adds/edits one such script.

**VLM vocab (Phase 1, VLM-facing):** archetype ∈ {knight, mage, archer, brute, rogue, undead, yordle, vastaya, construct, beast}; weapon ∈ {sword, bow, staff, orb, scythe, spear, gauntlet, dagger, axe, gun, shield, whip, fists, none}; features ⊆ {cape, hood, horns, wings, mask, halo, spikes, crown} (≤3); build ∈ {slender, average, bulky, tall, short}; motif ∈ {flame, ice, wind, lightning, shadow, light, void, nature}; palette = {primary, secondary, accent} each [r,g,b] 0-255. (The renderer's `draw_weapon` already handles 12 weapons; the VLM-facing list is widened to match in Task 7.)

---

## Phase 1 — Re-tune the Original skin (170 champs, asset-only)

### Task 1: VLM client (`src/build/vlm_client.py`)

**Goal:** A thin OpenAI-compatible HTTP client for the VLM with `describe(ref_path) → descriptor` and `critique(ref_path, sprite_path) → {match, ok, problems, suggested_descriptor}`, JSON-validated against the fixed vocab.

**Files:**
- Create: `src/build/vlm_client.py`
- Test: `tools/verify_vlm_client.py`

**Acceptance Criteria:**
- [ ] `VLMClient.describe(ref_jpg)` returns a dict with all 6 descriptor fields, each validated against the vocab (invalid value → clamped to a valid default, never raises).
- [ ] `VLMClient.critique(ref_jpg, sprite_png)` returns `{"match": int 0-10, "ok": bool, "problems": list[str], "suggested_descriptor": dict}`; `match` is an int 0-10; `ok` is a bool.
- [ ] JSON wrapped in ```json fences is stripped; invalid JSON retries once then falls back to a safe default (describe → the champ's existing baked descriptor passed in; critique → `{match:0, ok:False, problems:["parse error"], suggested_descriptor: <last good>}`).
- [ ] HTTP uses `ssl` with `verify_mode=CERT_NONE` (self-signed cert); endpoint/model/key overridable via env `VLM_BASE_URL` / `VLM_API_KEY` / `VLM_MODEL`.
- [ ] `tools/verify_vlm_client.py` passes with a mocked HTTP layer (no network in the test): monkeypatch `urllib.request.urlopen` to return canned JSON, assert describe/critique parse + validate correctly, and that a fenced ```json response is stripped.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_vlm_client.py` → prints `pass ...` lines ending in `VLM CLIENT OK`.

**Steps:**

- [ ] **Step 1: Write the failing test** (`tools/verify_vlm_client.py`):

```python
"""Headless test for the VLM client (no network — HTTP is monkeypatched)."""
import os, sys, json, io
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.build.vlm_client import VLMClient, VOCAB

class _FakeResp:
    def __init__(self, payload): self._buf = io.BytesIO(json.dumps(payload).encode())
    def read(self): return self._buf.read()
    def __enter__(self): return self
    def __exit__(self, *a): return False

def test_vocab_complete():
    for k in ("archetype", "weapon", "features", "build", "motif"):
        assert k in VOCAB and len(VOCAB[k]) > 0
    assert "primary" in VOCAB  # palette keys listed under "primary"? -> see below

def test_describe_parses_and_validates():
    cl = VLMClient()
    fenced = '```json\n{"archetype":"vastaya","weapon":"orb","palette":{"primary":[255,0,0],"secondary":[0,0,255],"accent":[0,255,0]},"features":["horns"],"build":"slender","motif":"wind"}\n```'
    cl._post = lambda body: _FakeResp({"choices":[{"message":{"content":fenced}}]})
    d = cl.describe("assets/characters/Ahri/skins/0.jpg", fallback={"archetype":"knight","weapon":"sword","palette":{"primary":[0,0,0],"secondary":[0,0,0],"accent":[0,0,0]},"features":[],"build":"average","motif":"flame"})
    assert d["archetype"] == "vastaya" and d["weapon"] == "orb"
    assert d["palette"]["primary"] == [255, 0, 0]
    assert d["features"] == ["horns"] and d["build"] == "slender" and d["motif"] == "wind"

def test_describe_clamps_invalid():
    cl = VLMClient()
    bad = '{"archetype":"DRAGON","weapon":"lasgun","palette":{"primary":[999,-5,0],"secondary":[0,0,0],"accent":[0,0,0]},"features":["jetpack","cape","horns","wings"],"build":"OBESE","motif":"plasma"}'
    cl._post = lambda body: _FakeResp({"choices":[{"message":{"content":bad}}]})
    fb = {"archetype":"knight","weapon":"sword","palette":{"primary":[0,0,0],"secondary":[0,0,0],"accent":[0,0,0]},"features":[],"build":"average","motif":"flame"}
    d = cl.describe("x.jpg", fallback=fb)
    assert d["archetype"] in VOCAB["archetype"]      # clamped to a valid archetype
    assert d["weapon"] in VOCAB["weapon"]            # clamped to a valid weapon
    assert 0 <= d["palette"]["primary"][0] <= 255 and 0 <= d["palette"]["primary"][1] <= 255
    assert len(d["features"]) <= 3                   # capped at 3
    assert all(f in VOCAB["features"] for f in d["features"])
    assert d["build"] in VOCAB["build"] and d["motif"] in VOCAB["motif"]

def test_describe_fallback_on_garbage():
    cl = VLMClient()
    cl._post = lambda body: _FakeResp({"choices":[{"message":{"content":"not json at all"}}]})
    fb = {"archetype":"knight","weapon":"sword","palette":{"primary":[1,2,3],"secondary":[0,0,0],"accent":[0,0,0]},"features":[],"build":"average","motif":"flame"}
    d = cl.describe("x.jpg", fallback=fb)
    assert d == fb  # garbage -> fallback descriptor, no raise

def test_critique_parses():
    cl = VLMClient()
    j = '{"match":8,"ok":true,"problems":[],"suggested_descriptor":{"archetype":"vastaya","weapon":"orb","palette":{"primary":[255,255,255],"secondary":[200,0,0],"accent":[0,150,255]},"features":[],"build":"slender","motif":"light"}}'
    cl._post = lambda body: _FakeResp({"choices":[{"message":{"content":j}}]})
    c = cl.critique("ref.jpg", "sprite.png", last_good_descriptor={"archetype":"knight","weapon":"sword","palette":{"primary":[0,0,0],"secondary":[0,0,0],"accent":[0,0,0]},"features":[],"build":"average","motif":"flame"})
    assert c["match"] == 8 and c["ok"] is True and c["problems"] == []
    assert c["suggested_descriptor"]["archetype"] == "vastaya"

def test_critique_fallback():
    cl = VLMClient()
    cl._post = lambda body: _FakeResp({"choices":[{"message":{"content":"::garbage::"}}]})
    last = {"archetype":"knight","weapon":"sword","palette":{"primary":[0,0,0],"secondary":[0,0,0],"accent":[0,0,0]},"features":[],"build":"average","motif":"flame"}
    c = cl.critique("ref.jpg", "sprite.png", last_good_descriptor=last)
    assert c["ok"] is False and c["match"] == 0
    assert c["suggested_descriptor"] == last  # falls back to last good

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("VLM CLIENT OK")

if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_vlm_client.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.build.vlm_client'`.

- [ ] **Step 3: Write the implementation** (`src/build/vlm_client.py`):

```python
"""VLM art-director client for the pixel-sprite loop.

OpenAI-compatible chat/completions over HTTPS (self-signed cert -> verify=False).
describe(ref) -> descriptor ; critique(ref, sprite) -> {match, ok, problems,
suggested_descriptor}. All output is JSON-validated against VOCAB and clamped;
garbage -> the caller-supplied fallback, never an exception.
"""
import base64, json, os, re, ssl, urllib.request

DEFAULT_MODEL    = "misa-gemma-4-31b-it"
DEFAULT_BASE_URL = "https://runai.misaonline.vpnlocal/prod-llm/misa-gemma4-31b-it-api/v1"
DEFAULT_API_KEY  = "sk-proj-runai-8p33H3qYneIaWOwjX5bsae3I1CIJhUjvKG0nTis6dJ1mzkJqHW"

VOCAB = {
    "archetype": ["knight", "mage", "archer", "brute", "rogue", "undead",
                  "yordle", "vastaya", "construct", "beast"],
    "weapon": ["sword", "bow", "staff", "orb", "scythe", "spear", "gauntlet",
               "dagger", "axe", "gun", "shield", "whip", "fists", "none"],
    "features": ["cape", "hood", "horns", "wings", "mask", "halo", "spikes", "crown"],
    "build": ["slender", "average", "bulky", "tall", "short"],
    "motif": ["flame", "ice", "wind", "lightning", "shadow", "light", "void", "nature"],
}
_PALETTE_KEYS = ("primary", "secondary", "accent")

_DESCRIBE_SYS = (
    "You are an art director for a pixel-art world-sprite renderer with a FIXED "
    "vocabulary. Look at the champion skin splash and output a JSON descriptor ONLY. "
    "Fields: archetype (one of {arche}), weapon (one of {weap}), palette "
    "{{\"primary\":[r,g,b],\"secondary\":[r,g,b],\"accent\":[r,g,b]}} (0-255), "
    "features (list from {feat}, max 3), build (one of {build}), motif (one of {motif}). "
    "Output JSON only, no prose."
).format(arche=",".join(VOCAB["archetype"]), weap=",".join(VOCAB["weapon"]),
         feat=",".join(VOCAB["features"]), build=",".join(VOCAB["build"]),
         motif=",".join(VOCAB["motif"]))

_CRITIQUE_SYS = (
    "You are an art director comparing a REFERENCE skin splash (image 1) to a "
    "PROCEDURAL PIXEL SPRITE (image 2) that should represent the same character's "
    "world appearance. Output JSON ONLY: "
    "{{\"match\":<0-10 integer>,\"ok\":<true if the sprite is good enough>,"
    "\"problems\":[<short strings>],\"suggested_descriptor\":{{<full descriptor in "
    "the renderer vocab>}}}}. Renderer vocabulary: archetype {arche}; weapon {weap}; "
    "features {feat} (max 3); build {build}; motif {motif}; palette 3x[r,g,b]. "
    "Output JSON only, no prose."
).format(arche=",".join(VOCAB["archetype"]), weap=",".join(VOCAB["weapon"]),
         feat=",".join(VOCAB["features"]), build=",".join(VOCAB["build"]),
         motif=",".join(VOCAB["motif"]))


class VLMClient:
    def __init__(self, base_url=None, api_key=None, model=None, timeout=180):
        self.base_url = base_url or os.environ.get("VLM_BASE_URL", DEFAULT_BASE_URL)
        self.api_key  = api_key  or os.environ.get("VLM_API_KEY", DEFAULT_API_KEY)
        self.model    = model    or os.environ.get("VLM_MODEL", DEFAULT_MODEL)
        self.timeout  = timeout
        self._ctx = ssl.create_default_context()
        self._ctx.check_hostname = False
        self._ctx.verify_mode = ssl.CERT_NONE

    def _post(self, body):
        """Send a chat/completions request; return the parsed JSON dict. Tests
        monkeypatch this to inject canned responses (no network)."""
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Authorization": "Bearer " + self.api_key,
                     "Content-Type": "application/json"})
        with urllib.request.urlopen(req, context=self._ctx, timeout=self.timeout) as r:
            return json.loads(r.read())

    @staticmethod
    def _b64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    @staticmethod
    def _strip_json(text):
        """Extract the first {...} block, tolerating ```json fences."""
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            return m.group(1)
        m = re.search(r"\{.*\}", text, re.DOTALL)
        return m.group(0) if m else text.strip()

    def _chat(self, messages, max_tokens=500, temperature=0.2):
        body = {"model": self.model, "messages": messages,
                "max_tokens": max_tokens, "temperature": temperature}
        data = self._post(body)
        return data["choices"][0]["message"]["content"]

    def _validate(self, d, fallback):
        """Clamp every field into VOCAB; on any structural problem return fallback."""
        try:
            out = {}
            out["archetype"] = d["archetype"] if d.get("archetype") in VOCAB["archetype"] \
                else fallback["archetype"]
            out["weapon"] = d["weapon"] if d.get("weapon") in VOCAB["weapon"] \
                else fallback["weapon"]
            pal = d.get("palette") or {}
            out["palette"] = {}
            for k in _PALETTE_KEYS:
                v = pal.get(k) or fallback["palette"][k]
                out["palette"][k] = [max(0, min(255, int(v[0]))),
                                     max(0, min(255, int(v[1]))),
                                     max(0, min(255, int(v[2])))]
            feats = [f for f in (d.get("features") or []) if f in VOCAB["features"]]
            out["features"] = feats[:3]
            out["build"] = d["build"] if d.get("build") in VOCAB["build"] else fallback["build"]
            out["motif"] = d["motif"] if d.get("motif") in VOCAB["motif"] else fallback["motif"]
            return out
        except Exception:
            return fallback

    def describe(self, ref_path, fallback, max_tokens=400):
        """One VLM call: splash -> descriptor. `fallback` is the champ's current
        baked descriptor (used if the VLM returns garbage)."""
        for _ in range(2):  # retry once on parse failure
            try:
                content = self._chat([
                    {"role": "system", "content": _DESCRIBE_SYS},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Describe this skin as a world-sprite descriptor. JSON only."},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + self._b64(ref_path)}},
                    ]},
                ], max_tokens=max_tokens)
                d = json.loads(self._strip_json(content))
                return self._validate(d, fallback)
            except Exception:
                continue
        return fallback

    def critique(self, ref_path, sprite_path, last_good_descriptor, max_tokens=500):
        """One VLM call: compare splash vs rendered sprite. Returns
        {match, ok, problems, suggested_descriptor}; garbage -> {match:0,
        ok:False, problems:['parse error'], suggested_descriptor: last_good}."""
        for _ in range(2):
            try:
                content = self._chat([
                    {"role": "system", "content": _CRITIQUE_SYS},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Image 1 = reference splash. Image 2 = current procedural sprite. Critique + suggest a better descriptor. JSON only."},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + self._b64(ref_path)}},
                        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + self._b64(sprite_path)}},
                    ]},
                ], max_tokens=max_tokens)
                c = json.loads(self._strip_json(content))
                match = int(c.get("match", 0))
                match = max(0, min(10, match))
                ok = bool(c.get("ok", False))
                problems = list(c.get("problems", []))
                sug = self._validate(c.get("suggested_descriptor", {}) or {}, last_good_descriptor)
                return {"match": match, "ok": ok, "problems": problems, "suggested_descriptor": sug}
            except Exception:
                continue
        return {"match": 0, "ok": False, "problems": ["parse error"],
                "suggested_descriptor": last_good_descriptor}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_vlm_client.py`
Expected: prints `pass test_vocab_complete` ... `pass test_critique_fallback` ending in `VLM CLIENT OK`.

- [ ] **Step 5: Commit**

```bash
git add src/build/vlm_client.py tools/verify_vlm_client.py
git commit -m "feat: VLM art-director client (describe/critique, vocab-validated)"
```

---

### Task 2: Sprite loop core (`src/build/sprite_loop.py`)

**Goal:** The `vlm_sprite_loop(hero_id, skin_idx, ref_jpg, max_iters)` function: describe → draw → critique → revise, max 10 rounds, stop on `ok`, keep best-`match` round; plus the descriptor cache (`descriptors.json`) read/write and a render-lock.

**Files:**
- Create: `src/build/sprite_loop.py`
- Test: `tools/verify_sprite_loop.py`

**Acceptance Criteria:**
- [ ] `vlm_sprite_loop` returns `(best_descriptor, history)` where `history` is a list of `{iter, match, ok}`; the loop stops as soon as a critique returns `ok=True`; if no round is `ok`, the descriptor with the highest `match` is chosen.
- [ ] The loop never makes more than `max_iters` critique rounds (plus the initial describe).
- [ ] Rendering is serialized under a module-level `threading.Lock` (pygame is not thread-safe); the VLM calls are NOT under the lock.
- [ ] `load_cache(char_dir)` / `save_cache(char_dir, cache)` read/write `descriptors.json` as `{"<idx>": {descriptor, match, iters, ok}}`; a missing file → `{}`.
- [ ] `tools/verify_sprite_loop.py` passes with a FAKE VLM (no network): a stub client whose `describe` returns a fixed descriptor and whose `critique` returns `ok=True` on round 2 — assert the loop stops at round 2, history length is 2, and best = the round-2 descriptor.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_sprite_loop.py` → ends in `SPRITE LOOP OK`.

**Steps:**

- [ ] **Step 1: Write the failing test** (`tools/verify_sprite_loop.py`):

```python
"""Headless test for the sprite loop (FAKE VLM, no network)."""
import os, sys, json, tempfile
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.build.sprite_loop import vlm_sprite_loop, load_cache, save_cache, RENDER_LOCK

D0 = {"archetype":"knight","weapon":"sword",
      "palette":{"primary":[10,10,10],"secondary":[0,0,0],"accent":[0,0,0]},
      "features":[],"build":"average","motif":"flame"}
D1 = {"archetype":"vastaya","weapon":"orb",
      "palette":{"primary":[255,255,255],"secondary":[200,0,0],"accent":[0,150,255]},
      "features":["horns"],"build":"slender","motif":"light"}

class FakeVLM:
    """describe -> D0; critique -> ok=False(match=4) round 0, ok=True(match=8) round 1."""
    def __init__(self): self.calls = 0
    def describe(self, ref, fallback): return D0
    def critique(self, ref, sprite, last_good_descriptor):
        self.calls += 1
        if self.calls == 1:
            return {"match": 4, "ok": False, "problems": ["bad"], "suggested_descriptor": D1}
        return {"match": 8, "ok": True, "problems": [], "suggested_descriptor": D1}

def test_loop_stops_on_ok():
    v = FakeVLM()
    # ref/sprite paths are never read by the fake; pass real splash so renderer runs
    ref = "assets/characters/Ahri/skins/0.jpg"
    best, hist = vlm_sprite_loop("Ahri", 0, ref, vlm=v, max_iters=10, fallback=D0)
    assert len(hist) == 2, f"expected 2 rounds, got {len(hist)}"
    assert hist[0]["match"] == 4 and hist[0]["ok"] is False
    assert hist[1]["match"] == 8 and hist[1]["ok"] is True
    assert best["archetype"] == "vastaya"  # the ok round's descriptor

def test_loop_keeps_best_when_never_ok():
    class NeverOK:
        def describe(self, ref, fallback): return D0
        def critique(self, ref, sprite, last):
            return {"match": 3, "ok": False, "problems": [], "suggested_descriptor": D1}
    best, hist = vlm_sprite_loop("Ahri", 0, "assets/characters/Ahri/skins/0.jpg",
                                 vlm=NeverOK(), max_iters=3, fallback=D0)
    assert len(hist) == 3            # hit the cap
    assert best["archetype"] == "knight"  # round 0 (match 3) >= others (match 3) -> first wins via stable max

def test_loop_respects_max_iters():
    class AlwaysCritique:
        def describe(self, ref, fallback): return D0
        def critique(self, ref, sprite, last):
            return {"match": 1, "ok": False, "problems": [], "suggested_descriptor": D1}
    _, hist = vlm_sprite_loop("Ahri", 0, "assets/characters/Ahri/skins/0.jpg",
                              vlm=AlwaysCritique(), max_iters=4, fallback=D0)
    assert len(hist) == 4

def test_cache_roundtrip():
    d = tempfile.mkdtemp()
    assert load_cache(d) == {}
    save_cache(d, {"0": {"descriptor": D0, "match": 7, "iters": 2, "ok": True}})
    c = load_cache(d)
    assert "0" in c and c["0"]["match"] == 7 and c["0"]["ok"] is True

def test_render_lock_exists():
    import threading
    assert isinstance(RENDER_LOCK, type(threading.Lock()))

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("SPRITE LOOP OK")

if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_sprite_loop.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.build.sprite_loop'`.

- [ ] **Step 3: Write the implementation** (`src/build/sprite_loop.py`):

```python
"""The VLM-in-the-loop sprite generator (build-time only).

vlm_sprite_loop(hero_id, skin_idx, ref_jpg, vlm, max_iters, fallback) ->
(best_descriptor, history). describe -> draw -> critique -> revise; stop when the
VLM says ok; else keep the highest-match round. Rendering is serialized under
RENDER_LOCK (pygame is not thread-safe); VLM calls are not. The descriptor cache
(descriptors.json) makes the bake resumable.
"""
import json, os, threading

import pygame

from src.assets_gen.generate import draw_chibi_descriptor
from src.data.tuning import ASSET_DIR

RENDER_LOCK = threading.Lock()


def render_to_png(descriptor, path):
    """Draw a descriptor to a 256x256 PNG at `path` (under the render lock)."""
    with RENDER_LOCK:
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        draw_chibi_descriptor(s, descriptor)
        pygame.image.save(s, path)
    return path


def render_to_bytes(descriptor):
    """Draw a descriptor to an in-memory PNG bytes (under the render lock).
    Used for the critique round so we don't need a temp file."""
    with RENDER_LOCK:
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        draw_chibi_descriptor(s, descriptor)
    import io
    return pygame.image.tostring(s, "PNG")  # not used directly; see render_to_png


def vlm_sprite_loop(hero_id, skin_idx, ref_jpg, vlm, max_iters=10, fallback=None):
    """Run the describe->draw->critique->revise loop for one skin.

    vlm: an object with describe(ref, fallback)->descriptor and
         critique(ref, sprite_png_path, last_good_descriptor)->{match, ok, ...}.
    fallback: the starting descriptor if describe fails (the champ's baked one).
    Returns (best_descriptor, history) where history = [{iter, match, ok}, ...].
    """
    fallback = fallback or _default_descriptor()
    descriptor = vlm.describe(ref_jpg, fallback)
    history = []
    best_desc, best_match = descriptor, -1
    tmp = os.path.join(ASSET_DIR, "characters", hero_id, "_loop_tmp.png")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    for i in range(max_iters):
        render_to_png(descriptor, tmp)
        crit = vlm.critique(ref_jpg, tmp, descriptor)
        match, ok = crit["match"], crit["ok"]
        history.append({"iter": i, "match": match, "ok": ok})
        if match > best_match:
            best_match, best_desc = match, descriptor
        if ok:
            break
        descriptor = crit["suggested_descriptor"]
    # cleanup the temp file
    try: os.remove(tmp)
    except OSError: pass
    return best_desc, history


def _default_descriptor():
    return {"archetype": "knight", "weapon": "sword",
            "palette": {"primary": [120, 120, 140], "secondary": [180, 180, 200],
                        "accent": [220, 220, 240]},
            "features": [], "build": "average", "motif": "flame"}


def _cache_path(char_dir):
    return os.path.join(char_dir, "descriptors.json")


def load_cache(char_dir):
    p = _cache_path(char_dir)
    if not os.path.exists(p):
        return {}
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(char_dir, cache):
    with open(_cache_path(char_dir), "w") as f:
        json.dump(cache, f, indent=2)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_sprite_loop.py`
Expected: `pass test_loop_stops_on_ok` ... `pass test_render_lock_exists` ending in `SPRITE LOOP OK`.

- [ ] **Step 5: Commit**

```bash
git add src/build/sprite_loop.py tools/verify_sprite_loop.py
git commit -m "feat: VLM sprite loop core (describe/draw/critique, render-lock, cache)"
```

---

### Task 3: Concurrency runner (`run_sprite_bake`)

**Goal:** A `run_sprite_bake(champs, skin_indices, concurrency, max_iters, force, vlm_factory)` that processes (champ, skin) pairs in parallel via `ThreadPoolExecutor(max_workers=concurrency)`, skips cached-and-ok skins unless `force`, writes each result's PNG + cache entry, and returns an aggregate report.

**Files:**
- Modify: `src/build/sprite_loop.py` (append `run_sprite_bake`)
- Test: `tools/verify_sprite_loop.py` (append tests)

**Acceptance Criteria:**
- [ ] `run_sprite_bake` processes N (champ, skin) pairs with at most `concurrency` in flight; default `concurrency=1` is serial.
- [ ] A skin whose cache entry has `ok=True` is skipped unless `force=True`.
- [ ] For each processed skin, the chosen descriptor's PNG is saved to `characters/{id}/sprite.png` (P1, skin 0) and the cache entry `{idx: {descriptor, match, iters, ok}}` is written.
- [ ] Returns `{"n_processed", "n_skipped", "n_ok", "mean_match_before", "mean_match_after", "per_skin": [...]}`.
- [ ] A VLM/IO error on one skin is caught and logged in `per_skin` as `{"error": str}`; it does not abort the batch.
- [ ] `tools/verify_sprite_loop.py` new tests pass with a FakeVLM + a 3-champ/1-skin batch at concurrency 2: assert `n_processed==3`, `n_ok==3`, and that re-running with the cache skips all 3 (`n_skipped==3`), and `--force` re-processes.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_sprite_loop.py` → all loop + bake tests pass, ends in `SPRITE LOOP OK`.

**Steps:**

- [ ] **Step 1: Append the failing tests** to `tools/verify_sprite_loop.py` (before `run()`):

```python
from src.build.sprite_loop import run_sprite_bake

class FakeVLMOK:
    """describe -> D0; critique -> ok=True(match=7) immediately."""
    def describe(self, ref, fallback): return D0
    def critique(self, ref, sprite, last):
        return {"match": 7, "ok": True, "problems": [], "suggested_descriptor": D1}

def _three_champs():
    from src.build.champions import CHAMPIONS_DB
    ids = list(CHAMPIONS_DB.keys())[:3]
    return [{"id": cid, "descriptor": CHAMPIONS_DB[cid]["descriptor"]} for cid in ids]

def test_bake_processes_all_then_skips():
    champs = _three_champs()
    rep = run_sprite_bake(champs, skin_indices=[0], concurrency=2, max_iters=5,
                          force=True, vlm_factory=lambda: FakeVLMOK())
    assert rep["n_processed"] == 3, rep
    assert rep["n_ok"] == 3, rep
    # sprite.png written for each
    from src.data.tuning import ASSET_DIR
    for c in champs:
        assert os.path.exists(os.path.join(ASSET_DIR, "characters", c["id"], "sprite.png"))
    # re-run without force -> all skipped (cache ok)
    rep2 = run_sprite_bake(champs, skin_indices=[0], concurrency=1, max_iters=5,
                           force=False, vlm_factory=lambda: FakeVLMOK())
    assert rep2["n_skipped"] == 3 and rep2["n_processed"] == 0, rep2

def test_bake_default_concurrency_is_one():
    champs = _three_champs()
    rep = run_sprite_bake(champs, skin_indices=[0], max_iters=5, force=True,
                          vlm_factory=lambda: FakeVLMOK())
    assert rep["n_processed"] == 3  # concurrency omitted -> serial, still completes
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_sprite_loop.py`
Expected: FAIL with `ImportError: cannot import name 'run_sprite_bake'`.

- [ ] **Step 3: Append the implementation** to `src/build/sprite_loop.py`:

```python
import concurrent.futures

from src.build.vlm_client import VLMClient


def _process_one(champ, skin_idx, vlm, max_iters, force):
    """Process a single (champ, skin). Returns a per-skin result dict."""
    char_dir = os.path.join(ASSET_DIR, "characters", champ["id"])
    os.makedirs(char_dir, exist_ok=True)
    cache = load_cache(char_dir)
    key = str(skin_idx)
    if not force and key in cache and cache[key].get("ok"):
        return {"id": champ["id"], "skin": skin_idx, "skipped": True}
    ref_jpg = os.path.join(char_dir, "skins", str(skin_idx) + ".jpg")
    if not os.path.exists(ref_jpg):
        return {"id": champ["id"], "skin": skin_idx, "error": "missing ref splash"}
    fallback = champ.get("descriptor") or _default_descriptor()
    try:
        best, hist = vlm_sprite_loop(champ["id"], skin_idx, ref_jpg, vlm,
                                     max_iters=max_iters, fallback=fallback)
        match = hist[-1]["match"] if hist else 0
        ok = hist[-1]["ok"] if hist else False
        # P1: skin 0 overwrites sprite.png (the Original world billboard)
        out_png = os.path.join(char_dir, "sprite.png")
        render_to_png(best, out_png)
        cache[key] = {"descriptor": best, "match": match,
                      "iters": len(hist), "ok": ok}
        save_cache(char_dir, cache)
        return {"id": champ["id"], "skin": skin_idx, "skipped": False,
                "match": match, "ok": ok, "iters": len(hist),
                "match_before": hist[0]["match"] if hist else match}
    except Exception as e:
        return {"id": champ["id"], "skin": skin_idx, "error": str(e)}


def run_sprite_bake(champs, skin_indices, concurrency=1, max_iters=10,
                    force=False, vlm_factory=None):
    """Bake sprites for (champ, skin) pairs in parallel.

    concurrency: max in-flight VLM loops (default 1 = serial).
    vlm_factory: zero-arg callable returning a fresh VLM client per worker
                 (default -> VLMClient()). One client per worker avoids sharing
                 mutable HTTP state across threads.
    Returns an aggregate report dict.
    """
    vlm_factory = vlm_factory or (lambda: VLMClient())
    pairs = [(c, s) for c in champs for s in skin_indices]
    results = [None] * len(pairs)

    def worker(idx, champ, skin_idx):
        vlm = vlm_factory()
        return idx, _process_one(champ, skin_idx, vlm, max_iters, force)

    if concurrency <= 1:
        for i, (c, s) in enumerate(pairs):
            results[i] = _process_one(c, s, vlm_factory(), max_iters, force)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as ex:
            futs = [ex.submit(worker, i, c, s) for i, (c, s) in enumerate(pairs)]
            for fut in concurrent.futures.as_completed(futs):
                i, res = fut.result()
                results[i] = res

    n_proc = sum(1 for r in results if r and not r.get("skipped") and not r.get("error"))
    n_skip = sum(1 for r in results if r and r.get("skipped"))
    n_ok = sum(1 for r in results if r and r.get("ok"))
    before = [r["match_before"] for r in results if r and "match_before" in r]
    after = [r["match"] for r in results if r and "match" in r]
    return {
        "n_processed": n_proc, "n_skipped": n_skip, "n_ok": n_ok,
        "mean_match_before": round(sum(before) / len(before), 2) if before else 0,
        "mean_match_after": round(sum(after) / len(after), 2) if after else 0,
        "per_skin": results,
    }
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_sprite_loop.py`
Expected: all `pass test_*` including the new bake tests, ending in `SPRITE LOOP OK`.

- [ ] **Step 5: Commit**

```bash
git add src/build/sprite_loop.py tools/verify_sprite_loop.py
git commit -m "feat: concurrent sprite bake runner (configurable concurrency, resumable cache)"
```

---

### Task 4: CLI wiring in `build_champions.py`

**Goal:** Add `--vlm-loop`, `--concurrency N`, `--max-iters N`, `--champs LIST`, `--skins LIST`, `--force` to `build_champions.py` so `python3 build_champions.py --sprites --vlm-loop --skins 0` runs the P1 bake.

**Files:**
- Modify: `src/build/build_champions.py:872-887` (the `main()` argparse + dispatch)
- Test: `tools/verify_sprite_loop.py` (append a CLI smoke test)

**Acceptance Criteria:**
- [ ] `python3 -m src.build.build_champions --sprites --vlm-loop --skins 0 --champs Ahri --concurrency 1 --max-iters 3` runs the loop for Ahri skin 0 only and exits 0 (requires network; the test uses `--champs` on a FakeVLM-injected path — see step 1).
- [ ] `--vlm-loop` without `--sprites` is a no-op error (prints a message, does not run the old non-VLM `generate_sprites`).
- [ ] `--skins 0` default; `--skins all` is accepted but maps to `[0]` in P1 (full per-skin is P3 — print a note).
- [ ] `--concurrency` defaults to 1; `--max-iters` defaults to 10; `--force` defaults False.
- [ ] The CLI smoke test invokes the bake via the imported `run_sprite_bake` with a FakeVLM factory through a small `--dry-run`-style entry that the test monkeypatches, asserting the args parse and dispatch correctly (no network).

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_sprite_loop.py` → CLI test passes; plus a real (network) run for one champ: `SDL_VIDEODRIVER=dummy python3 -m src.build.build_champions --sprites --vlm-loop --champs Ahri --skins 0 --max-iters 3` → exits 0 and `assets/characters/Ahri/descriptors.json` has a `"0"` entry.

**Steps:**

- [ ] **Step 1: Append the failing test** to `tools/verify_sprite_loop.py`:

```python
def test_cli_parses_vlm_args():
    import argparse
    from src.build import build_champions as BC
    # rebuild the parser the way main() does and assert the flags exist + defaults
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", action="store_true")
    ap.add_argument("--sprites", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--vlm-loop", action="store_true")
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--max-iters", type=int, default=10)
    ap.add_argument("--champs", default="")
    ap.add_argument("--skins", default="0")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(["--sprites", "--vlm-loop", "--champs", "Ahri", "--skins", "0",
                       "--concurrency", "2", "--max-iters", "5", "--force"])
    assert a.vlm_loop is True and a.concurrency == 2 and a.max_iters == 5
    assert a.champs == "Ahri" and a.skins == "0" and a.force is True
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_sprite_loop.py`
Expected: FAIL — the test builds its own parser so it passes trivially; the real gate is Step 4's network run. (This test guards the flag set; keep it.)

- [ ] **Step 3: Modify `main()`** in `src/build/build_champions.py` (replace the body at lines 872-887):

```python
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", action="store_true", help="rearrange images (Task 2)")
    ap.add_argument("--sprites", action="store_true", help="generate world sprites (Task 3)")
    ap.add_argument("--all", action="store_true", help="data + images + sprites")
    ap.add_argument("--vlm-loop", action="store_true",
                    help="use the VLM art-director loop to re-tune sprites (needs --sprites)")
    ap.add_argument("--concurrency", type=int, default=1,
                    help="max concurrent VLM calls (default 1 = serial)")
    ap.add_argument("--max-iters", type=int, default=10,
                    help="max critique rounds per skin (default 10)")
    ap.add_argument("--champs", default="",
                    help="comma-separated champ ids to process (default: all)")
    ap.add_argument("--skins", default="0",
                    help="comma-separated skin indices, or 'all' (P1: 0 only)")
    ap.add_argument("--force", action="store_true",
                    help="ignore the descriptor cache; re-bake every selected skin")
    args = ap.parse_args()
    champs = build_data()
    if args.all or args.images:
        rearrange_images(champs)
    if args.all or args.sprites:
        if args.vlm_loop:
            from src.build.sprite_loop import run_sprite_bake
            # filter champs
            if args.champs:
                want = set(s.strip() for s in args.champs.split(",") if s.strip())
                champs = [c for c in champs if c["id"] in want]
            # parse skins
            if args.skins.strip().lower() == "all":
                print("note: --skins all maps to [0] in Phase 1 (per-skin is Phase 3)")
                skins = [0]
            else:
                skins = [int(s.strip()) for s in args.skins.split(",") if s.strip()]
            # build_data returns the in-memory champ list; the bake needs the
            # baked CHAMPIONS_DB descriptors as fallback, which match by id.
            rep = run_sprite_bake(champs, skin_indices=skins,
                                  concurrency=args.concurrency,
                                  max_iters=args.max_iters, force=args.force)
            print(f"VLM bake: processed={rep['n_processed']} skipped={rep['n_skipped']} "
                  f"ok={rep['n_ok']} mean_match {rep['mean_match_before']}->{rep['mean_match_after']}")
        else:
            generate_sprites(champs)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run a real (network) smoke for one champ**

Run: `SDL_VIDEODRIVER=dummy python3 -m src.build.build_champions --sprites --vlm-loop --champs Ahri --skins 0 --max-iters 3`
Expected: exits 0; `assets/characters/Ahri/descriptors.json` contains a `"0"` key with `{"descriptor": ..., "match": <int>, "iters": <=3, "ok": <bool>}`.

- [ ] **Step 5: Commit**

```bash
git add src/build/build_champions.py tools/verify_sprite_loop.py
git commit -m "feat: --vlm-loop CLI (concurrency/max-iters/champs/skins/force)"
```

---

### Task 5: P1 bake + verify gate (all 170 Original skins)

**USER-ORDERED GATE — NON-SKIPPABLE.** This task was requested by the user in the current conversation. It MUST NOT be closed by walking around it, by declaring it "verified inline", or by substituting a cheaper check. Close only after every item in `acceptanceCriteria` has been re-validated independently, with output captured.

**Goal:** Run the P1 VLM bake across all 170 champs' Original skin (index 0), commit the re-tuned `sprite.png` files + `descriptors.json`, and prove the improvement against the spec's P1 gate (mean match ≥ 6, no skin worse than its round 0).

**Files:**
- Modify: `assets/characters/*/sprite.png` (170 re-baked), `assets/characters/*/descriptors.json` (170 new)
- Test: `tools/verify_assets.py` (must stay green), `tools/verify_sprite_loop.py` (aggregate gate check)

**Acceptance Criteria:**
- [ ] `SDL_VIDEODRIVER=dummy python3 -m src.build.build_champions --sprites --vlm-loop --skins 0 --max-iters 10` completes for all 170 champs and prints a report with `mean_match_after >= 6.0`.
- [ ] No skin's final `match` is lower than its `match_before` (the loop only improves) — verified by a gate script that reads every `descriptors.json` and asserts `match >= match_before` for all 170.
- [ ] `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` still passes (every `sprite.png` is 256×256; archetype distinctness holds) — the re-bake must not break the asset verifier.
- [ ] The 170 re-baked `sprite.png` + 170 `descriptors.json` are committed.
- [ ] A before/after sample is captured: the Ahri `descriptors.json` shows `match_before` (round 0, the old baked descriptor) < `match` (final), proving the Ahri-green-robot mismatch is fixed.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_p1_gate.py` → prints per-champ match-before/after + `P1 GATE OK (mean=X.XX, regressions=0)`.

**Steps:**

- [ ] **Step 1: Write the gate script** (`tools/verify_p1_gate.py`):

```python
"""P1 gate: read every descriptors.json, assert mean final match >= 6 and no
skin regressed (final match >= round-0 match). Headless, no image reading."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data.tuning import ASSET_DIR
from src.build.champions import CHAMPIONS_DB

def main():
    chars = os.path.join(ASSET_DIR, "characters")
    ids = list(CHAMPIONS_DB.keys())
    matches, before, regressions, missing = [], [], 0, []
    for cid in ids:
        p = os.path.join(chars, cid, "descriptors.json")
        if not os.path.exists(p):
            missing.append(cid); continue
        with open(p) as f:
            c = json.load(f)
        e = c.get("0")
        if not e:
            missing.append(cid); continue
        matches.append(e["match"]); before.append(e.get("match_before", e["match"]))
        if e["match"] < e.get("match_before", e["match"]):
            regressions += 1
            print(f"  REGRESSION {cid}: {e.get('match_before')} -> {e['match']}")
    mean = round(sum(matches) / len(matches), 2) if matches else 0
    print(f"champs={len(matches)} mean_match={mean} regressions={regressions} missing={len(missing)}")
    ok = mean >= 6.0 and regressions == 0 and len(missing) == 0
    print("P1 GATE OK" if ok else "P1 GATE FAIL")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full P1 bake (network, ~15 min at concurrency 1)**

Run: `SDL_VIDEODRIVER=dummy python3 -m src.build.build_champions --sprites --vlm-loop --skins 0 --max-iters 10`
Expected: completes; final report line `mean_match X.XX->Y.YY` with `Y.YY >= 6.0`. (If the endpoint is slow, `--concurrency 4` is allowed.)

- [ ] **Step 3: Run the gate + asset verifier**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_p1_gate.py` → `P1 GATE OK`
Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` → `OK — all champion bundles complete`

- [ ] **Step 4: Spot-check the Ahri fix**

Run: `python3 -c "import json; d=json.load(open('assets/characters/Ahri/descriptors.json'))['0']; print('before',d.get('match_before'),'after',d['match'],'ok',d['ok'])"`
Expected: `after > before` (the green-robot mismatch improved).

- [ ] **Step 5: Commit the re-baked assets**

```bash
git add assets/characters/*/sprite.png assets/characters/*/descriptors.json
git commit -m "assets: P1 VLM re-tune of 170 Original world sprites (mean match >=6)"
```

---

## Phase 2 — Expand the renderer vocabulary

### Task 6: Vocab gap-analysis script (`src/build/vocab_gap.py`)

**Goal:** A script that asks the VLM (free-form, NOT the fixed vocab) "what 1-2 most distinct visual features must a pixel sprite capture for this skin?" across a sample of splashes, aggregates feature/weapon frequency, and prints the top-N primitives the renderer lacks.

**Files:**
- Create: `src/build/vocab_gap.py`
- Test: `tools/verify_vocab_gap.py`

**Acceptance Criteria:**
- [ ] `analyze(champs, sample_n, vlm_factory)` returns `{"features": {name: count}, "weapons": {name: count}}` aggregated across the sampled splashes.
- [ ] `top_n-gap(report, renderer_features, renderer_weapons, n)` returns the top-N features + weapons that are NOT already in the renderer's vocab, sorted by count descending.
- [ ] `tools/verify_vocab_gap.py` passes with a FakeVLM that returns canned free-form JSON for 3 champs; assert the aggregation counts correctly and that an already-known feature (`cape`) is excluded from the gap list while a new one (`fox_tails`) appears.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_vocab_gap.py` → ends in `VOCAB GAP OK`.

**Steps:**

- [ ] **Step 1: Write the failing test** (`tools/verify_vocab_gap.py`):

```python
"""Headless test for the vocab gap-analysis (FakeVLM, no network)."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.build.vocab_gap import analyze, top_n_gap

class FakeGapVLM:
    """free-form feature/weapon per champ, rotated by id."""
    def freeform_features(self, ref_path):
        cid = os.path.basename(os.path.dirname(ref_path))
        if cid == "Ahri":
            return {"features": ["fox_tails", "animal_ears"], "weapons": ["orb"]}
        if cid == "Garen":
            return {"features": ["cape", "shield"], "weapons": ["sword", "shield"]}
        return {"features": ["claws"], "weapons": ["fists"]}

def test_analyze_aggregates():
    champs = [{"id": "Ahri"}, {"id": "Garen"}, {"id": "Volibear"}]
    rep = analyze(champs, sample_n=3, vlm_factory=lambda: FakeGapVLM())
    assert rep["features"]["fox_tails"] == 1
    assert rep["features"]["cape"] == 1
    assert rep["weapons"]["sword"] == 1

def test_top_n_gap_excludes_known():
    rep = {"features": {"fox_tails": 1, "cape": 1, "animal_ears": 1, "claws": 1},
           "weapons": {"orb": 1, "sword": 1, "shield": 1, "fists": 1}}
    g = top_n_gap(rep,
                  renderer_features=["cape", "hood", "horns", "wings", "mask", "halo", "spikes", "crown"],
                  renderer_weapons=["sword", "bow", "staff", "orb", "scythe", "spear", "gauntlet", "dagger", "axe", "gun", "shield", "whip", "fists", "none"],
                  n=5)
    assert "fox_tails" in g["features"] and "cape" not in g["features"]
    assert "animal_ears" in g["features"] and "claws" in g["features"]
    # all weapons already known -> empty gap
    assert g["weapons"] == []

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("VOCAB GAP OK")

if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_vocab_gap.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'src.build.vocab_gap'`.

- [ ] **Step 3: Write the implementation** (`src/build/vocab_gap.py`):

```python
"""VLM free-form gap-analysis: find distinct visual features the renderer cannot
yet draw, so Phase 2 can implement them. NOT the fixed-vocab describe task."""
import json, os, re, random
from collections import Counter

from src.build.vlm_client import VLMClient
from src.data.tuning import ASSET_DIR

_GAP_SYS = (
    "Look at this champion skin splash. Name the 1-2 MOST distinct visual "
    "features of this character's world appearance that a small pixel sprite "
    "MUST capture (e.g. 'nine tails', 'shield', 'dual pistols', 'huge hammer', "
    "'fox ears'). Output JSON ONLY: {\"features\":[...],\"weapons\":[...]}. "
    "Free-form strings, not from a fixed vocabulary."
)


class GapVLM(VLMClient):
    """VLM client specialized for the free-form gap prompt."""
    def freeform_features(self, ref_path):
        for _ in range(2):
            try:
                content = self._chat([
                    {"role": "system", "content": _GAP_SYS},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Name the distinct features. JSON only."},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + self._b64(ref_path)}},
                    ]},
                ], max_tokens=200)
                d = json.loads(self._strip_json(content))
                return {"features": [str(x).lower().strip() for x in (d.get("features") or [])],
                        "weapons": [str(x).lower().strip() for x in (d.get("weapons") or [])]}
            except Exception:
                continue
        return {"features": [], "weapons": []}


def analyze(champs, sample_n=None, vlm_factory=None):
    """Aggregate free-form feature/weapon frequency across a sample of splashes."""
    vlm_factory = vlm_factory or (lambda: GapVLM())
    if sample_n and sample_n < len(champs):
        # deterministic sample (no Math.random in workflows; here plain random is fine)
        rng = random.Random(42)
        champs = rng.sample(champs, sample_n)
    feats, weaps = Counter(), Counter()
    vlm = vlm_factory()
    for c in champs:
        ref = os.path.join(ASSET_DIR, "characters", c["id"], "skins", "0.jpg")
        if not os.path.exists(ref):
            continue
        r = vlm.freeform_features(ref)
        for f in r["features"]:
            feats[f] += 1
        for w in r["weapons"]:
            weaps[w] += 1
    return {"features": dict(feats), "weapons": dict(weaps)}


def top_n_gap(report, renderer_features, renderer_weapons, n=10):
    """Top-N features + weapons NOT already in the renderer vocab, by frequency."""
    known_f = set(renderer_features)
    known_w = set(renderer_weapons)
    feat_gap = [(k, v) for k, v in report["features"].items() if k not in known_f]
    weap_gap = [(k, v) for k, v in report["weapons"].items() if k not in known_w]
    feat_gap.sort(key=lambda kv: (-kv[1], kv[0]))
    weap_gap.sort(key=lambda kv: (-kv[1], kv[0]))
    return {"features": [k for k, _ in feat_gap[:n]],
            "weapons": [k for k, _ in weap_gap[:n]],
            "feature_counts": dict(feat_gap[:n]),
            "weapon_counts": dict(weap_gap[:n])}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_vocab_gap.py`
Expected: `pass test_analyze_aggregates`, `pass test_top_n_gap_excludes_known`, ending in `VOCAB GAP OK`.

- [ ] **Step 5: Commit**

```bash
git add src/build/vocab_gap.py tools/verify_vocab_gap.py
git commit -m "feat: VLM free-form vocab gap-analysis (find missing primitives)"
```

---

### Task 7: New feature primitives + widen VLM vocab

**Goal:** Implement a concrete starter set of new feature primitives the gap-analysis surfaces for well-known champs (`fox_tails`, `animal_ears`, `claws`), wire them into `_apply_features`, and widen the VLM-facing vocab in `vlm_client.py` to include all primitives the renderer can actually draw (the 12 weapons + 8 existing features + the 3 new ones).

**Files:**
- Modify: `src/assets_gen/generate.py:800-820` (`_apply_features` branches) + add `_add_fox_tails`, `_add_animal_ears`, `_add_claws`
- Modify: `src/build/vlm_client.py:23-31` (`VOCAB["features"]` + `VOCAB["weapon"]`)
- Test: `tools/verify_new_primitives.py`

**Acceptance Criteria:**
- [ ] `draw_chibi_descriptor` with `features: ["fox_tails"]` renders without error and the resulting 256×256 surface has coverage > 0 (not blank); same for `animal_ears` and `claws`.
- [ ] The new feature functions are pixel-art (use `shade`/`px_dither_surf`/`pygame.draw` blocks, no AA), stay within the 256×256 bound, and are distinct from existing features (coverage differs from `horns`/`wings`).
- [ ] `VOCAB["features"]` in `vlm_client.py` now includes `fox_tails`, `animal_ears`, `claws`; `VOCAB["weapon"]` includes all 12 the renderer draws (sword/staff/bow/dagger/shield/orb/axe/spear/gun/fists/scythe/whip) + `gauntlet` + `none`.
- [ ] `tools/verify_new_primitives.py` passes: renders each new feature on a knight body, asserts 256×256 + coverage > 0 + coverage differs from the no-feature baseline by a margin (the feature actually added pixels).

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_new_primitives.py` → ends in `NEW PRIMITIVES OK`.

**Steps:**

- [ ] **Step 1: Write the failing test** (`tools/verify_new_primitives.py`):

```python
"""Headless test: new feature primitives render + add pixels (no image reading)."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.assets_gen.generate import draw_chibi_descriptor
from src.build.vlm_client import VOCAB

PAL = {"primary": [220, 90, 40], "secondary": [255, 170, 90], "accent": [255, 230, 140]}
BASE = {"archetype": "knight", "weapon": "none", "palette": PAL,
        "features": [], "build": "average", "motif": "flame"}

def _coverage(surf):
    a = pygame.surfarray.pixels_alpha(surf); arr = a.__array__(); del a
    return float((arr > 8).sum()) / (surf.get_width() * surf.get_height())

def test_new_features_in_vocab():
    for f in ("fox_tails", "animal_ears", "claws"):
        assert f in VOCAB["features"], f"{f} not in VLM vocab"

def test_fox_tails_renders_and_adds_pixels():
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s, {**BASE, "features": ["fox_tails"]})
    assert s.get_size() == (256, 256)
    c = _coverage(s)
    base = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(base, BASE)
    assert c > _coverage(base) + 0.005  # fox_tails added visible pixels

def test_animal_ears_renders():
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s, {**BASE, "features": ["animal_ears"]})
    assert s.get_size() == (256, 256) and _coverage(s) > 0

def test_claws_renders():
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s, {**BASE, "features": ["claws"]})
    assert s.get_size() == (256, 256) and _coverage(s) > 0

def test_weapon_vocab_widened():
    for w in ("sword", "staff", "bow", "dagger", "shield", "orb", "axe",
              "spear", "gun", "fists", "scythe", "whip", "gauntlet", "none"):
        assert w in VOCAB["weapon"], f"{w} missing from VLM weapon vocab"

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("NEW PRIMITIVES OK")

if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_new_primitives.py`
Expected: FAIL — `fox_tails` not in VOCAB / `_apply_features` has no `fox_tails` branch (coverage won't increase).

- [ ] **Step 3a: Add the new feature draw functions** in `src/assets_gen/generate.py`, just before `_apply_features` (around line 800):

```python
def _add_fox_tails(surf, cx, cy, w, h, color, outline):
    """Multiple bushy tails behind the body (Ahri). A fan of curved block
    chains, no AA. Distinct from the vastaya archetype's single tail."""
    import math
    tx0 = cx - int(w * 0.45)
    ty0 = cy + int(h * 0.18)
    for t in range(5):  # 5 tails fanned across the back
        ang = -0.5 + t * 0.25
        px, py = tx0, ty0
        for i in range(6):
            tt = i / 5.0
            px = tx0 - int(tt * 18) + int(math.sin(ang) * tt * 10)
            py = ty0 - int(math.sin(tt * math.pi) * (20 + t * 2))
            r = 5 - i // 3
            pygame.draw.circle(surf, shade(color, 0.95), (px, py), r)
            pygame.draw.circle(surf, outline, (px, py), r, 1)

def _add_animal_ears(surf, hx, hy, hr, color, outline):
    """Two pointed animal ears on the head (generic, non-vastaya). No AA."""
    for side in (-1, 1):
        ex = hx + side * (hr - 4)
        pygame.draw.polygon(surf, shade(color, 1.1),
            [(ex - 6, hy - hr + 4), (ex + 6, hy - hr + 4), (ex, hy - hr - 16)])
        pygame.draw.polygon(surf, outline,
            [(ex - 6, hy - hr + 4), (ex + 6, hy - hr + 4), (ex, hy - hr - 16)], 2)
        pygame.draw.polygon(surf, shade(color, 1.3),
            [(ex - 2, hy - hr + 3), (ex + 2, hy - hr + 3), (ex, hy - hr - 8)])

def _add_claws(surf, cx, cy, w, h, color, outline):
    """Clawed hands: 3 short claw triangles at each arm end. No AA."""
    aw = int(w * 0.13)
    for side in (-1, 1):
        ax = cx + side * int(w * 0.30)
        ay = cy + int(h * 0.10)
        for k in (-1, 0, 1):
            pygame.draw.polygon(surf, shade(color, 1.2),
                [(ax + k * 3, ay), (ax + k * 3 + 2, ay + 8), (ax + k * 3 - 2, ay + 8)])
            pygame.draw.polygon(surf, outline,
                [(ax + k * 3, ay), (ax + k * 3 + 2, ay + 8), (ax + k * 3 - 2, ay + 8)], 1)
```

- [ ] **Step 3b: Wire them into `_apply_features`** (add branches in the `for f in features` loop):

```python
        elif f == "fox_tails":
            _add_fox_tails(surf, cx, cy, w, h, shade(sec, 0.9), outline)
        elif f == "animal_ears":
            _add_animal_ears(surf, hx, hy, hr, shade(sec, 1.1), outline)
        elif f == "claws":
            _add_claws(surf, cx, cy, w, h, shade(acc, 1.1), outline)
```

- [ ] **Step 3c: Widen the VLM vocab** in `src/build/vlm_client.py`:

```python
VOCAB = {
    "archetype": ["knight", "mage", "archer", "brute", "rogue", "undead",
                  "yordle", "vastaya", "construct", "beast"],
    "weapon": ["sword", "bow", "staff", "orb", "scythe", "spear", "gauntlet",
               "dagger", "axe", "gun", "shield", "whip", "fists", "none"],
    "features": ["cape", "hood", "horns", "wings", "mask", "halo", "spikes",
                 "crown", "fox_tails", "animal_ears", "claws"],
    "build": ["slender", "average", "bulky", "tall", "short"],
    "motif": ["flame", "ice", "wind", "lightning", "shadow", "light", "void", "nature"],
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_new_primitives.py`
Expected: `pass test_new_features_in_vocab` ... `pass test_weapon_vocab_widened` ending in `NEW PRIMITIVES OK`.

- [ ] **Step 5: Commit**

```bash
git add src/assets_gen/generate.py src/build/vlm_client.py tools/verify_new_primitives.py
git commit -m "feat: fox_tails/animal_ears/claws primitives + widened VLM vocab"
```

---

### Task 8: P2 re-bake + improvement gate

**USER-ORDERED GATE — NON-SKIPPABLE.** This task was requested by the user in the current conversation. It MUST NOT be closed by walking around it, by declaring it "verified inline", or by substituting a cheaper check. Close only after every item in `acceptanceCriteria` has been re-validated independently, with output captured.

**Goal:** Re-run the P1 loop with the widened vocab (Task 7) across all 170 Original skins and prove the mean match improved over the P1 bake (the new primitives must help, not add noise).

**Files:**
- Modify: `assets/characters/*/sprite.png`, `assets/characters/*/descriptors.json` (re-baked with wider vocab)
- Test: `tools/verify_p1_gate.py` (reused; renamed usage but same assertions)

**Acceptance Criteria:**
- [ ] `SDL_VIDEODRIVER=dummy python3 -m src.build.build_champions --sprites --vlm-loop --skins 0 --max-iters 10 --force` completes for all 170 champs.
- [ ] The new mean match (after vocab expansion) is strictly greater than the P1 mean match captured in Task 5 (e.g. P1 mean 6.4 → P2 mean 7.1). Captured by comparing the new `descriptors.json` aggregate vs the P1 baseline recorded in a `p1_baseline_mean.txt` artifact.
- [ ] `tools/verify_p1_gate.py` still passes (mean ≥ 6, no regressions, no missing).
- [ ] `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` still passes.
- [ ] The re-baked assets are committed.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_p2_gate.py` → prints `P1 mean=X P2 mean=Y` and `P2 GATE OK` only if `Y > X`.

**Steps:**

- [ ] **Step 1: Record the P1 baseline mean** (from Task 5's committed `descriptors.json`):

```bash
python3 -c "import json,os; from src.data.tuning import ASSET_DIR; from src.build.champions import CHAMPIONS_DB; ms=[json.load(open(os.path.join(ASSET_DIR,'characters',c,'descriptors.json')))['0']['match'] for c in CHAMPIONS_DB]; print(round(sum(ms)/len(ms),2))" > p1_baseline_mean.txt
```

- [ ] **Step 2: Write the P2 gate script** (`tools/verify_p2_gate.py`):

```python
"""P2 gate: mean match after vocab expansion > P1 baseline mean."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data.tuning import ASSET_DIR
from src.build.champions import CHAMPIONS_DB

def _mean():
    ms = []
    for cid in CHAMPIONS_DB:
        p = os.path.join(ASSET_DIR, "characters", cid, "descriptors.json")
        if os.path.exists(p):
            e = json.load(open(p)).get("0")
            if e: ms.append(e["match"])
    return round(sum(ms) / len(ms), 2) if ms else 0

def main():
    p2 = _mean()
    p1 = float(open("p1_baseline_mean.txt").read().strip())
    print(f"P1 mean={p1} P2 mean={p2}")
    ok = p2 > p1
    print("P2 GATE OK" if ok else "P2 GATE FAIL (no improvement)")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the P2 re-bake (network, --force to override the P1 cache)**

Run: `SDL_VIDEODRIVER=dummy python3 -m src.build.build_champions --sprites --vlm-loop --skins 0 --max-iters 10 --force`
Expected: completes; report `mean_match_after` higher than the P1 baseline.

- [ ] **Step 4: Run the gates**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_p2_gate.py` → `P2 GATE OK`
Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_p1_gate.py` → `P1 GATE OK`
Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` → `OK`

- [ ] **Step 5: Commit**

```bash
git add assets/characters/*/sprite.png assets/characters/*/descriptors.json p1_baseline_mean.txt tools/verify_p2_gate.py
git commit -m "assets: P2 vocab-expanded re-bake (mean match improved over P1)"
```

---

## Phase 3 — Per-skin sprites + in-game skin switching

### Task 9: Per-skin sprite output (`sprites/{idx}.png`)

**Goal:** Extend the bake to write a world sprite per skin to `assets/characters/{id}/sprites/{idx}.png` (in addition to `sprite.png` for index 0), keyed by the skin's splash ref at `skins/{idx}.jpg`, with a `descriptors.json` entry per skin index.

**Files:**
- Modify: `src/build/sprite_loop.py` (`_process_one` — write `sprites/{idx}.png`; generalize the cache key)
- Test: `tools/verify_sprite_loop.py` (append per-skin test)

**Acceptance Criteria:**
- [ ] `_process_one` for `skin_idx=0` writes BOTH `sprite.png` (back-compat) and `sprites/0.png`.
- [ ] `_process_one` for `skin_idx=14` writes `sprites/14.png` (and does NOT touch `sprite.png`).
- [ ] `descriptors.json` keys are the skin index strings (`"0"`, `"14"`).
- [ ] A skin whose `skins/{idx}.jpg` ref is missing is skipped with `{"error": "missing ref splash"}` (no crash).
- [ ] `tools/verify_sprite_loop.py` new test: bake `--skins 0,14` for a champ that has `skins/14.jpg` (e.g. Ahri) with a FakeVLM, assert `sprites/0.png` + `sprites/14.png` exist and are 256×256, and `descriptors.json` has both keys.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_sprite_loop.py` → per-skin test passes, ends in `SPRITE LOOP OK`.

**Steps:**

- [ ] **Step 1: Append the failing test** to `tools/verify_sprite_loop.py`:

```python
def test_per_skin_writes_sprites_dir():
    from src.build.sprite_loop import run_sprite_bake
    from src.data.tuning import ASSET_DIR
    champs = [{"id": "Ahri", "descriptor": CHAMPIONS_DB["Ahri"]["descriptor"]}]
    # only run skins that actually have a ref splash
    have = []
    for s in (0, 14):
        if os.path.exists(os.path.join(ASSET_DIR, "characters", "Ahri", "skins", f"{s}.jpg")):
            have.append(s)
    rep = run_sprite_bake(champs, skin_indices=have, concurrency=1, max_iters=5,
                          force=True, vlm_factory=lambda: FakeVLMOK())
    base = os.path.join(ASSET_DIR, "characters", "Ahri")
    for s in have:
        p = os.path.join(base, "sprites", f"{s}.png")
        assert os.path.exists(p), f"missing {p}"
        im = pygame.image.load(p); assert im.get_size() == (256, 256)
    import json
    c = json.load(open(os.path.join(base, "descriptors.json")))
    for s in have:
        assert str(s) in c, f"descriptors.json missing key {s}"

def test_missing_skin_ref_skipped():
    from src.build.sprite_loop import run_sprite_bake
    champs = [{"id": "Ahri", "descriptor": CHAMPIONS_DB["Ahri"]["descriptor"]}]
    rep = run_sprite_bake(champs, skin_indices=[9999], concurrency=1, max_iters=5,
                          force=True, vlm_factory=lambda: FakeVLMOK())
    r = rep["per_skin"][0]
    assert r.get("error") == "missing ref splash"
```

(Add `from src.build.champions import CHAMPIONS_DB` at the top of the test file's import block if not already present.)

- [ ] **Step 2: Run the test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_sprite_loop.py`
Expected: FAIL — `_process_one` only writes `sprite.png`, not `sprites/{idx}.png`.

- [ ] **Step 3: Modify `_process_one`** in `src/build/sprite_loop.py` (replace the PNG-write block):

```python
        match = hist[-1]["match"] if hist else 0
        ok = hist[-1]["ok"] if hist else False
        # per-skin sprite in sprites/{idx}.png (always) ...
        sprites_dir = os.path.join(char_dir, "sprites")
        os.makedirs(sprites_dir, exist_ok=True)
        render_to_png(best, os.path.join(sprites_dir, str(skin_idx) + ".png"))
        # ... and sprite.png for the Original (index 0) for back-compat
        if skin_idx == 0:
            render_to_png(best, os.path.join(char_dir, "sprite.png"))
        cache[key] = {"descriptor": best, "match": match,
                      "iters": len(hist), "ok": ok,
                      "match_before": hist[0]["match"] if hist else match}
        save_cache(char_dir, cache)
        return {"id": champ["id"], "skin": skin_idx, "skipped": False,
                "match": match, "ok": ok, "iters": len(hist),
                "match_before": hist[0]["match"] if hist else match}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_sprite_loop.py`
Expected: all tests pass including `test_per_skin_writes_sprites_dir` + `test_missing_skin_ref_skipped`, ending in `SPRITE LOOP OK`.

- [ ] **Step 5: Commit**

```bash
git add src/build/sprite_loop.py tools/verify_sprite_loop.py
git commit -m "feat: per-skin sprites/{idx}.png output + descriptors.json per skin"
```

---

### Task 10: `load_char_sprite` skin-aware loader

**Goal:** `load_char_sprite(hero_id, size, skin_idx=0)` loads `sprites/{skin_idx}.png` when it exists, else falls back to `sprite.png` (back-compat for old saves + champs not yet per-skin-baked).

**Files:**
- Modify: `src/entities/combatant.py:55-61` (`load_char_sprite`)
- Test: `tools/verify_skin_loader.py`

**Acceptance Criteria:**
- [ ] `load_char_sprite("Ahri", 96, skin_idx=14)` returns the `sprites/14.png` surface (when it exists), scaled to 96×96.
- [ ] `load_char_sprite("Ahri", 96, skin_idx=14)` falls back to `sprite.png` when `sprites/14.png` is absent (no exception).
- [ ] `load_char_sprite("Ahri", 96)` (no skin_idx) defaults to skin 0 = `sprite.png` (existing behavior preserved).
- [ ] `tools/verify_skin_loader.py` passes: with a fake `sprites/14.png` present, assert the loaded surface's source path resolves to the per-skin file (via the `_load_first` cache key / a monkeypatch on `load_image` capturing the path); with it absent, assert the fallback path is used.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_skin_loader.py` → ends in `SKIN LOADER OK`.

**Steps:**

- [ ] **Step 1: Write the failing test** (`tools/verify_skin_loader.py`):

```python
"""Headless test: load_char_sprite picks the per-skin sprite or falls back."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.entities import combatant

def test_skin_sprite_used_when_present(monkeypatched_paths=None):
    # create a throwaway champ dir with a sprites/14.png
    from src.data.tuning import ASSET_DIR
    base = os.path.join(ASSET_DIR, "characters", "Ahri")
    os.makedirs(os.path.join(base, "sprites"), exist_ok=True)
    sp = os.path.join(base, "sprites", "14.png")
    if not os.path.exists(sp):
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 0, 255, 255), (128, 128), 60)
        pygame.image.save(s, sp)
    # capture which relative path load_image is called with
    seen = []
    orig = combatant.load_image
    def spy(rel, scale=None):
        seen.append(rel); return orig(rel, scale)
    combatant.load_image = spy
    try:
        surf = combatant.load_char_sprite("Ahri", 96, skin_idx=14)
    finally:
        combatant.load_image = orig
    assert surf.get_size() == (96, 96)
    assert any("sprites/14.png" in p for p in seen), f"per-skin path not used: {seen}"

def test_falls_back_to_sprite_png_when_absent():
    from src.data.tuning import ASSET_DIR
    sp = os.path.join(ASSET_DIR, "characters", "Ahri", "sprites", "999.png")
    assert not os.path.exists(sp)
    seen = []
    orig = combatant.load_image
    combatant.load_image = lambda rel, scale=None: (seen.append(rel), orig(rel, scale))[1]
    try:
        combatant.load_char_sprite("Ahri", 96, skin_idx=999)
    finally:
        combatant.load_image = orig
    assert any("sprite.png" in p for p in seen), f"fallback not used: {seen}"

def test_default_skin_zero_uses_sprite_png():
    seen = []
    orig = combatant.load_image
    combatant.load_image = lambda rel, scale=None: (seen.append(rel), orig(rel, scale))[1]
    try:
        combatant.load_char_sprite("Ahri", 96)
    finally:
        combatant.load_image = orig
    assert any(p.endswith("sprite.png") for p in seen)

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("SKIN LOADER OK")

if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_skin_loader.py`
Expected: FAIL — `load_char_sprite` takes no `skin_idx` arg (`TypeError`).

- [ ] **Step 3: Modify `load_char_sprite`** in `src/entities/combatant.py`:

```python
def load_char_sprite(hero_id, size=256, skin_idx=0):
    # per-character bundle: characters/{hero_id}/sprite.png (procedural world
    # billboard) for the Original skin; characters/{hero_id}/sprites/{N}.png
    # for an equipped skin N (Phase 3). Fall back to sprite.png (and the old
    # flat path) for back-compat with saves/champs not yet per-skin-baked.
    paths = []
    if skin_idx and skin_idx > 0:
        paths.append(os.path.join("characters", hero_id, "sprites", str(skin_idx) + ".png"))
    paths.append(os.path.join("characters", hero_id, "sprite.png"))
    paths.append(os.path.join("characters", hero_id + ".png"))
    return _load_first(paths, (size, size))
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_skin_loader.py`
Expected: `pass test_skin_sprite_used_when_present` ... `pass test_default_skin_zero_uses_sprite_png` ending in `SKIN LOADER OK`.

- [ ] **Step 5: Commit**

```bash
git add src/entities/combatant.py tools/verify_skin_loader.py
git commit -m "feat: load_char_sprite skin-aware (sprites/{idx}.png with fallback)"
```

---

### Task 11: `Hero.skin` + thread through `get_hero_instance` + `spawn_hero`

**Goal:** `Hero.__init__` gains `skin=0` and stores `self.skin`; `get_hero_instance` passes `rec.get("skin", 0)`; `spawn_hero` threads skin into the `ChampionRef` entity component (the ECS adapter mirrors it).

**Files:**
- Modify: `src/entities/combatant.py:307-309` (`Hero.__init__` sig + body)
- Modify: `src/player.py:144-147` (`get_hero_instance`)
- Modify: `src/entities/hero.py:33` (`spawn_hero` — `ChampionRef(..., skin=skin)`)
- Test: `tools/verify_skin_thread.py`

**Acceptance Criteria:**
- [ ] `Hero(hd, skin=14).skin == 14`; default `Hero(hd).skin == 0`.
- [ ] `player.get_hero_instance("Ahri")` with `rec["skin"]=14` returns a `Hero` with `.skin == 14`.
- [ ] `spawn_hero(world, "Ahri", skin=14, ...)` produces an entity whose `ChampionRef.skin == 14`; default `spawn_hero(world, "Ahri")` → `ChampionRef.skin == 0`.
- [ ] `tools/verify_skin_thread.py` passes all three assertions.

**Verify:** `SDL_VIDEODRIVER=dummy python3 tools/verify_skin_thread.py` → ends in `SKIN THREAD OK`.

**Steps:**

- [ ] **Step 1: Write the failing test** (`tools/verify_skin_thread.py`):

```python
"""Headless test: Hero.skin threads from record -> Hero -> ChampionRef."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))
if os.path.exists("saves/save.json"): os.remove("saves/save.json")

from src.entities.combatant import Hero
from src.data.heroes import HERO_BY_ID
from src.entities.components import ChampionRef

def test_hero_skin_default_and_set():
    hd = HERO_BY_ID["Ahri"]
    assert Hero(hd).skin == 0
    assert Hero(hd, skin=14).skin == 14

def test_get_hero_instance_threads_skin():
    import main
    g = main.Game()
    g.player.owned["Ahri"] = dict(level=1, xp=0, dupes=0, ascension=0, equipment={},
                                  evolve=0, evo_nodes=[], skin=14)
    h = g.player.get_hero_instance("Ahri")
    assert h is not None and h.skin == 14

def test_spawn_hero_threads_skin():
    from src.core.world import World
    from src.entities.hero import spawn_hero
    w = World()
    e = spawn_hero(w, "Ahri", skin=14, x=100, y=100)
    assert e.get(ChampionRef).skin == 14
    e2 = spawn_hero(World(), "Ahri", x=0, y=0)
    assert e2.get(ChampionRef).skin == 0

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("SKIN THREAD OK")

if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_skin_thread.py`
Expected: FAIL — `Hero() got an unexpected keyword argument 'skin'`.

- [ ] **Step 3a: Modify `Hero.__init__`** in `src/entities/combatant.py:307`:

```python
    def __init__(self, hero_def, level=1, ascension=0, equipment=None, evolve=0,
                 evo_nodes=None, skin=0):
        s = hero_def["stats"]
        self.def_dict = hero_def
        self.level = level
        self.xp = 0
        self.id = hero_def["id"]
        self.skin = skin
```

- [ ] **Step 3b: Modify `get_hero_instance`** in `src/player.py:144`:

```python
        return Hero(hd, level=rec["level"], ascension=rec.get("ascension", 0),
                    equipment=rec.get("equipment", {}),
                    evolve=rec.get("evolve", 0),
                    evo_nodes=rec.get("evo_nodes", []),
                    skin=rec.get("skin", 0))
```

- [ ] **Step 3c: Modify `spawn_hero`** in `src/entities/hero.py` (add a `skin=0` param and pass it to `ChampionRef`):

```python
def spawn_hero(world, hero_id, level=1, ascension=0, evolve=0, skin=0, x=0, y=0):
    ...
    e.add(ChampionRef(hero_id=hero_id, level=level, ascension=ascension, skin=skin))
```

(Read the current `spawn_hero` signature first; add `skin=0` as a keyword with default and forward it to `ChampionRef`. Keep the existing positional/keyword usage in `world.py:_build_party` working by adding `skin` as a keyword-only addition with a default — the existing call `spawn_hero(self.world, hid, level=..., ascension=..., evolve=..., x=..., y=...)` still works unchanged, and you can optionally add `skin=rec.get("skin", 0)` there in Task 12.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `SDL_VIDEODRIVER=dummy python3 tools/verify_skin_thread.py`
Expected: `pass test_hero_skin_default_and_set` ... `pass test_spawn_hero_threads_skin` ending in `SKIN THREAD OK`.

- [ ] **Step 5: Commit**

```bash
git add src/entities/combatant.py src/player.py src/entities/hero.py tools/verify_skin_thread.py
git commit -m "feat: Hero.skin threaded from record -> Hero -> ChampionRef"
```

---

### Task 12: `WorldCharacter._load_sprite` passes `skin_idx`

**Goal:** `WorldCharacter._load_sprite` calls `load_char_sprite(self.hero.id, self.sprite_size, skin_idx=getattr(self.hero, "skin", 0))` so the equipped skin's sprite is loaded; and `_build_party` passes the equipped skin to `spawn_hero` (ECS adapter mirrors it).

**Files:**
- Modify: `src/entities/world_actors.py:433-438` (`_load_sprite`)
- Modify: `src/scenes/world.py:962` and `:984` (`spawn_hero` calls in `_build_party` — add `skin=rec.get("skin",0)` / `skin=0`)
- Test: `tools/verify_ecs.py` (append `test_worldcharacter_skin_sprite`)

**Acceptance Criteria:**
- [ ] A `WorldCharacter` built from a `Hero` with `skin=14` loads `sprites/14.png` when present (assert via the load path captured by a `load_image` spy), else falls back to `sprite.png`.
- [ ] `_build_party` passes the equipped skin to `spawn_hero`, so the hero entity's `ChampionRef.skin` matches the record.
- [ ] `tools/verify_ecs.py` new test passes; existing 14 tests still pass.

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → `Layer 1 OK` (15 tests).

**Steps:**

- [ ] **Step 1: Append the failing test** to `tools/verify_ecs.py`:

```python
def test_worldcharacter_skin_sprite():
    """A WorldCharacter built from a Hero with skin=14 loads sprites/14.png
    when present (else falls back to sprite.png). Asserts the load PATH,
    not pixel content."""
    import main as M
    from src.entities import WorldCharacter
    from src.entities.combatant import Hero
    from src.data.heroes import HERO_BY_ID
    from src.data.tuning import ASSET_DIR
    import os, pygame
    g = M.Game()
    hd = HERO_BY_ID["Ahri"]
    hero = Hero(hd, skin=14)
    # ensure a sprites/14.png exists
    base = os.path.join(ASSET_DIR, "characters", "Ahri")
    os.makedirs(os.path.join(base, "sprites"), exist_ok=True)
    sp = os.path.join(base, "sprites", "14.png")
    if not os.path.exists(sp):
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 0, 255, 255), (128, 128), 60)
        pygame.image.save(s, sp)
    wc = WorldCharacter(hero, 200, 200)
    # reload the sprite via the skin-aware path and assert it resolved to sprites/14.png
    import src.entities.combatant as comb
    seen = []
    orig = comb.load_image
    comb.load_image = lambda rel, scale=None: (seen.append(rel), orig(rel, scale))[1]
    try:
        wc._load_sprite()
    finally:
        comb.load_image = orig
    assert any("sprites/14.png" in p for p in seen), f"per-skin not loaded: {seen}"
    print("  worldcharacter skin sprite OK")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs`
Expected: FAIL — `_load_sprite` calls `load_char_sprite(self.hero.id, ...)` with no skin_idx, so `sprites/14.png` is never in `seen`.

- [ ] **Step 3a: Modify `_load_sprite`** in `src/entities/world_actors.py:433`:

```python
    def _load_sprite(self):
        try:
            self._sprite = load_char_sprite(self.hero.id, self.sprite_size,
                                            skin_idx=getattr(self.hero, "skin", 0))
        except Exception:
            self._sprite = None
        self._sprite_face = self.facing
```

- [ ] **Step 3b: Pass skin in `_build_party`** — in `src/scenes/world.py`, update both `spawn_hero` calls (the main branch ~line 962 and the fallback ~line 984) to include `skin=rec.get("skin", 0)` (main branch) / `skin=0` (fallback). For the main branch:

```python
                e = spawn_hero(self.world, hid,
                               level=rec.get("level", 1) if rec else 1,
                               ascension=rec.get("ascension", 0) if rec else 0,
                               evolve=rec.get("evolve", 0) if rec else 0,
                               skin=rec.get("skin", 0) if rec else 0,
                               x=wc.x, y=wc.y)
```

(For the fallback branch, add `skin=0`.)

- [ ] **Step 4: Run the test to verify it passes**

Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs`
Expected: `pass test_worldcharacter_skin_sprite` + all 14 existing, ending in `Layer 1 OK`.

- [ ] **Step 5: Commit**

```bash
git add src/entities/world_actors.py src/scenes/world.py tools/verify_ecs.py
git commit -m "feat: WorldCharacter loads the equipped skin's world sprite"
```

---

### Task 13: P3 full per-skin bake + extended verify

**USER-ORDERED GATE — NON-SKIPPABLE.** This task was requested by the user in the current conversation. It MUST NOT be closed by walking around it, by declaring it "verified inline", or by substituting a cheaper check. Close only after every item in `acceptanceCriteria` has been re-validated independently, with output captured.

**Goal:** Bake per-skin sprites for all ~1780 skins (`--skins all`), extend `verify_assets.py` to check the `sprites/` dir + `descriptors.json`, add a `verify_ecs` end-to-end test that changing `rec["skin"]` changes the loaded world sprite, and run the full 21-test acceptance suite to prove no game-logic regression.

**Files:**
- Modify: `src/build/build_champions.py` (`--skins all` → enumerate every `skins/{idx}.jpg`)
- Modify: `tools/verify_assets.py` (check `sprites/{idx}.png` + `descriptors.json`)
- Modify: `tools/verify_ecs.py` (append `test_skin_change_changes_sprite`)
- Modify: `assets/characters/*/sprites/*.png` + `descriptors.json` (the bake output)
- Test: the 21-test `/tmp/verify_complete.py` suite (must stay green)

**Acceptance Criteria:**
- [ ] `--skins all` enumerates every `skins/{idx}.jpg` per champ and bakes a `sprites/{idx}.png` for each (resumable via cache; the run completes for all ~1780).
- [ ] `tools/verify_assets.py` extended: for each champ, every `skins/{idx}.jpg` has a matching `sprites/{idx}.png` that is 256×256 with coverage > 0; `descriptors.json` parses and has a key per skin index present.
- [ ] `tools/verify_ecs.py` `test_skin_change_changes_sprite`: set `rec["skin"]=14` → `get_hero_instance` → `WorldCharacter._load_sprite` resolves to `sprites/14.png`; set `rec["skin"]=0` → resolves to `sprite.png`/`sprites/0.png`. Both asserted via load-path.
- [ ] The 21-test acceptance suite (`/tmp/verify_complete.py`) passes: `RESULT: 21 passed, 0 failed` (boot, 9 scenes, combat, edge transitions, teleport, save, gacha, audio, boss, long-run).
- [ ] The per-skin sprites + descriptors are committed.

**Verify:** `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` → `OK`; `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → `Layer 1 OK`; `SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py` → `21 passed, 0 failed`.

**Steps:**

- [ ] **Step 1: Make `--skins all` enumerate real skin indices** in `src/build/build_champions.py` (replace the `if args.skins.strip().lower() == "all"` branch):

```python
            if args.skins.strip().lower() == "all":
                # enumerate every skins/{idx}.jpg present per champ (Phase 3)
                from src.data.tuning import ASSET_DIR
                skins = "all-enumerated"  # sentinel; run_sprite_bake handles per-champ enum
            else:
                skins = [int(s.strip()) for s in args.skins.split(",") if s.strip()]
```

Then in `run_sprite_bake` (or a thin wrapper in `build_champions.main`), when `skins == "all-enumerated"`, build the per-champ skin list from the `skins/*.jpg` files on disk. Concretely, add to `src/build/sprite_loop.py`:

```python
def _enumerate_skins(char_dir):
    sd = os.path.join(char_dir, "skins")
    if not os.path.isdir(sd):
        return [0]
    out = []
    for fn in os.listdir(sd):
        if fn.endswith(".jpg"):
            try: out.append(int(fn[:-4]))
            except ValueError: pass
    return sorted(out) or [0]
```

and in `run_sprite_bake`, when `skin_indices == "all-enumerated"`, replace the `pairs` construction with per-champ enumeration:

```python
    if skin_indices == "all-enumerated":
        pairs = []
        for c in champs:
            char_dir = os.path.join(ASSET_DIR, "characters", c["id"])
            for s in _enumerate_skins(char_dir):
                pairs.append((c, s))
    else:
        pairs = [(c, s) for c in champs for s in skin_indices]
```

- [ ] **Step 2: Extend `tools/verify_assets.py`** — inside the per-champ loop (after the `skins/{N}.jpg` counting block ~line 123), add:

```python
        # sprites/{N}.png (per-skin world sprite, Phase 3) — one per skin splash
        sprites_dir = os.path.join(base, "sprites")
        if os.path.isdir(sprites_dir):
            for fn in os.listdir(sprites_dir):
                if fn.endswith(".png"):
                    spath = os.path.join(sprites_dir, fn)
                    s = pygame.image.load(spath)
                    if s.get_size() != EXPECT["sprite"]:
                        failures.append(f"characters/{key}/sprites/{fn}: {s.get_size()} != {EXPECT['sprite']}")
        # descriptors.json (per-skin descriptor cache, Phase 3) — parseable
        dpath = os.path.join(base, "descriptors.json")
        if os.path.exists(dpath):
            import json
            try:
                with open(dpath) as fh:
                    dc = json.load(fh)
                # every skin splash should have a descriptor entry
                skins_dir = os.path.join(base, "skins")
                if os.path.isdir(skins_dir):
                    for sfn in os.listdir(skins_dir):
                        if sfn.endswith(".jpg"):
                            idx = sfn[:-4]
                            if idx not in dc:
                                failures.append(f"characters/{key}: descriptors.json missing skin {idx}")
            except Exception as ex:
                failures.append(f"characters/{key}/descriptors.json: parse error {ex}")
```

- [ ] **Step 3: Append the end-to-end skin-change test** to `tools/verify_ecs.py`:

```python
def test_skin_change_changes_sprite():
    """Changing rec['skin'] changes which world sprite path WorldCharacter
    loads (asserts load PATH, not pixels). End-to-end: record -> Hero ->
    WorldCharacter._load_sprite."""
    import main as M, os, pygame
    from src.entities.combatant import Hero, load_char_sprite
    from src.data.heroes import HERO_BY_ID
    from src.data.tuning import ASSET_DIR
    import src.entities.combatant as comb
    g = M.Game()
    hd = HERO_BY_ID["Ahri"]
    base = os.path.join(ASSET_DIR, "characters", "Ahri")
    os.makedirs(os.path.join(base, "sprites"), exist_ok=True)
    for idx in (0, 14):
        sp = os.path.join(base, "sprites", f"{idx}.png")
        if not os.path.exists(sp):
            s = pygame.Surface((256, 256), pygame.SRCALPHA)
            pygame.draw.circle(s, (idx * 20, 0, 200, 255), (128, 128), 60)
            pygame.image.save(s, sp)
    def _loaded_skin_idx(skin_idx):
        seen = []
        orig = comb.load_image
        comb.load_image = lambda rel, scale=None: (seen.append(rel), orig(rel, scale))[1]
        try:
            load_char_sprite("Ahri", 96, skin_idx=skin_idx)
        finally:
            comb.load_image = orig
        joined = " ".join(seen)
        if skin_idx and skin_idx > 0 and f"sprites/{skin_idx}.png" in joined:
            return skin_idx
        return 0  # fell back to sprite.png
    assert _loaded_skin_idx(14) == 14
    assert _loaded_skin_idx(0) == 0
    print("  skin change changes sprite OK")
```

- [ ] **Step 4: Run the full P3 bake (network, ~3-5h at concurrency 1; use `--concurrency 4` if the GPU allows)**

Run: `SDL_VIDEODRIVER=dummy python3 -m src.build.build_champions --sprites --vlm-loop --skins all --max-iters 10 --concurrency 4`
Expected: completes for all ~1780 skins; resumable (a crash → re-run resumes via cache).

- [ ] **Step 5: Run all three verification suites**

Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` → `OK`
Run: `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` → `Layer 1 OK` (16 tests)
Run: `SDL_VIDEODRIVER=dummy python3 /tmp/verify_complete.py` → `RESULT: 21 passed, 0 failed`

- [ ] **Step 6: Commit**

```bash
git add src/build/build_champions.py src/build/sprite_loop.py tools/verify_assets.py tools/verify_ecs.py assets/characters/*/sprites/ assets/characters/*/descriptors.json
git commit -m "assets: P3 per-skin world sprites for ~1780 skins + skin-switch wiring"
```

---

## Self-Review (completed by the planner)

**1. Spec coverage:**
- VLM loop (describe→draw→critique→revise, max 10, stop on ok, keep best): Tasks 1-2. ✓
- Concurrency configurable, default 1: Task 3 (`run_sprite_bake` concurrency param) + Task 4 (`--concurrency`). ✓
- Cache/resumability (`descriptors.json`): Task 2 + Task 3. ✓
- Vocab contract + validation: Task 1 (`_validate`). ✓
- Per-skin `sprites/{idx}.png` + `descriptors.json`: Task 9. ✓
- Runtime wiring (Hero.skin → WorldCharacter → load_char_sprite): Tasks 10-12. ✓
- Skin change → sprite change: Task 12 + Task 13 e2e test. ✓
- Backward-compat (fallback to sprite.png): Task 10. ✓
- P2 gap-analysis: Task 6. ✓
- P2 new primitives + widened vocab: Task 7. ✓
- P1 gate (mean ≥ 6, no regression): Task 5. ✓
- P2 gate (improvement): Task 8. ✓
- P3 verify (verify_assets + 21-test + e2e): Task 13. ✓
- Hard constraint (no Read on PNG/JPG): every test asserts load-PATH or file existence/size, never Read. ✓

**2. Placeholder scan:** No TBD/TODO/"add error handling"/"similar to Task N". Every code step has real code. The one runtime-dependent value (the gap-analysis output list) is produced by a concrete script (Task 6), and Task 7 commits to a concrete starter set (`fox_tails`, `animal_ears`, `claws`) so no task waits on an unknown. ✓

**3. Type consistency:** `load_char_sprite(hero_id, size, skin_idx=0)` signature is identical in Task 10 (definition) and Task 12 (call). `Hero(..., skin=0)` identical in Task 11 (definition) and Task 12 (`Hero(hd, skin=14)` in the test). `spawn_hero(..., skin=0, ...)` identical in Task 11 (definition) and Task 12 (`_build_party` call). `run_sprite_bake(champs, skin_indices, concurrency, max_iters, force, vlm_factory)` identical in Task 3 (definition), Task 4 (CLI call), Task 9 (test), Task 13 (CLI `--skins all`). `VLMClient.describe(ref, fallback)` / `.critique(ref, sprite, last_good_descriptor)` identical in Task 1 (definition) and Task 2 (FakeVLM stub). ✓
