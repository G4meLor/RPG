"""The VLM-in-the-loop sprite generator (build-time only).

vlm_sprite_loop(hero_id, skin_idx, ref_jpg, vlm, max_iters, fallback, champ, canon)
-> (best_descriptor, history). describe -> draw -> critique -> revise; stop when
the VLM's canonical_match >= 7; else keep the highest-canonical_match round.
Rendering is serialized under RENDER_LOCK (pygame is not thread-safe); VLM calls
are not. The descriptor cache (descriptors.json) makes the bake resumable.

The loop is canon-grounded: `champ` (the CHAMPIONS_DB dict) + `canon` (the
champ's canonical origin identity dict) are threaded into describe/critique so
the VLM judges against the champ's canonical body/features/colors, NOT mere
splash similarity. The critique returns {canonical_match, stance_captured, ...,
suggested_descriptor}; the loop stops at canonical_match >= 7 (NOT the old
splash `match`/`ok`).
"""
import json, os, threading

import pygame

from src.assets_gen.generate import draw_chibi_descriptor
from src.data.tuning import ASSET_DIR

RENDER_LOCK = threading.Lock()
# Serializes the descriptors.json read-modify-write so concurrent workers baking
# different skins of the SAME champ don't clobber each other's cache keys
# (load -> mutate -> save race -> lost entry -> silent re-bake on resume).
# Cache I/O is fast; a single global lock is simpler than a per-char-dir map.
CACHE_LOCK = threading.Lock()


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


def vlm_sprite_loop(hero_id, skin_idx, ref_jpg, vlm, max_iters=10, fallback=None,
                    champ=None, canon=None):
    """Run the describe->draw->critique->revise loop for one skin.

    vlm: an object with describe(ref, fallback, champ)->descriptor and
         critique(ref, sprite_png_path, last_good_descriptor, champ)->
         {canonical_match, stance_captured, ..., suggested_descriptor}.
    fallback: the starting descriptor if describe fails (the champ's baked one).
    champ: the champ dict from CHAMPIONS_DB (id/name/title/faction/role/
           ability_names/lore) — threaded into describe/critique for canon
           grounding. None = back-compat (no canon context; loses grounding).
    canon: the champ's canonical origin identity dict (stance/body_shape/
           signature_features/colors/weapon) — reserved for the canon_gate
           path (Task 9 wires the real canon through); the loop's describe/
           critique use `champ` for grounding. None = back-compat.
    Returns (best_descriptor, history) where history =
        [{iter, canonical_match, stance_captured}, ...].
    Stops when canonical_match >= 7; keeps the best-canonical_match round
    (strict `>` tie-break: the FIRST round wins on ties so a late equally-good
    round can't displace an earlier one) if never converges.
    """
    fallback = fallback or _default_descriptor()
    descriptor = vlm.describe(ref_jpg, fallback, champ)
    history = []
    best_desc, best_match = descriptor, -1
    tmp = os.path.join(ASSET_DIR, "characters", hero_id, f"_loop_tmp_{skin_idx}.png")
    os.makedirs(os.path.dirname(tmp), exist_ok=True)
    for i in range(max_iters):
        render_to_png(descriptor, tmp)
        crit = vlm.critique(ref_jpg, tmp, descriptor, champ)
        canonical_match = crit["canonical_match"]
        stance_captured = crit.get("stance_captured", False)
        history.append({"iter": i, "canonical_match": canonical_match,
                        "stance_captured": stance_captured})
        if canonical_match > best_match:
            best_match, best_desc = canonical_match, descriptor
        if canonical_match >= 7:
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


import concurrent.futures

from src.build.vlm_client import VLMClient


def _enumerate_skins(char_dir):
    """Phase 3: enumerate every skins/{idx}.jpg present for a champ. Returns
    a sorted list of skin indices (e.g. [0, 1, 7, 14]); falls back to [0] if
    the skins dir is missing or has no .jpg files."""
    sd = os.path.join(char_dir, "skins")
    if not os.path.isdir(sd):
        return [0]
    out = []
    for fn in os.listdir(sd):
        if fn.endswith(".jpg"):
            try:
                out.append(int(fn[:-4]))
            except ValueError:
                pass
    return sorted(out) or [0]


def _process_one(champ, skin_idx, vlm, max_iters, force):
    """Process a single (champ, skin). Returns a per-skin result dict."""
    char_dir = os.path.join(ASSET_DIR, "characters", champ["id"])
    os.makedirs(char_dir, exist_ok=True)
    cache = load_cache(char_dir)
    key = str(skin_idx)
    if not force and key in cache and cache[key].get("ok"):
        # Cache-skip: still ensure the per-skin sprite PNG exists on disk so the
        # verify_assets gate (every skins/{idx}.jpg has a sprites/{idx}.png)
        # passes for skins baked in an earlier phase that only wrote sprite.png
        # for index 0. Re-render from the cached descriptor (fast, no VLM call).
        sprites_dir = os.path.join(char_dir, "sprites")
        os.makedirs(sprites_dir, exist_ok=True)
        sp_path = os.path.join(sprites_dir, str(skin_idx) + ".png")
        if not os.path.exists(sp_path):
            cached_desc = cache[key].get("descriptor")
            if cached_desc:
                render_to_png(cached_desc, sp_path)
        return {"id": champ["id"], "skin": skin_idx, "skipped": True}
    ref_jpg = os.path.join(char_dir, "skins", str(skin_idx) + ".jpg")
    if not os.path.exists(ref_jpg):
        return {"id": champ["id"], "skin": skin_idx, "error": "missing ref splash"}
    fallback = champ.get("descriptor") or _default_descriptor()
    try:
        # The bake passes `champ` (the CHAMPIONS_DB dict) to vlm_sprite_loop so
        # describe/critique ground in the champ's canonical identity. `canon`
        # is None here — the loop's describe/critique use `champ` for grounding
        # (the separate canon dict is reserved for the canon_gate path; the
        # honest gate, tools/verify_canon_gate.py, builds canon via a text-only
        # VLM call). Task 9.
        best, hist = vlm_sprite_loop(champ["id"], skin_idx, ref_jpg, vlm,
                                     max_iters=max_iters, fallback=fallback,
                                     champ=champ, canon=None)
        # Use the BEST round (max canonical_match), not the last round, so a
        # late bad critique can't overwrite a good earlier sprite.
        # canonical_match_before is the first round's score (the describe()
        # baseline before any revision).
        canonical_match = max((h["canonical_match"] for h in hist), default=0)
        ok = any(h["canonical_match"] >= 7 for h in hist) if hist else False
        # P3: per-skin sprite in sprites/{idx}.png (always) ...
        sprites_dir = os.path.join(char_dir, "sprites")
        os.makedirs(sprites_dir, exist_ok=True)
        render_to_png(best, os.path.join(sprites_dir, str(skin_idx) + ".png"))
        # ... and sprite.png for the Original (index 0) for back-compat
        if skin_idx == 0:
            render_to_png(best, os.path.join(char_dir, "sprite.png"))
        # Cache update under CACHE_LOCK: render_to_png above is already under
        # RENDER_LOCK; the lock is released before we touch the cache, so the
        # two locks are NEVER nested (no deadlock risk). This makes the
        # load_cache -> mutate -> save_cache atomic per char dir, so two workers
        # baking skin 0 and skin 14 of the same champ can't lose each other's
        # cache entry.
        with CACHE_LOCK:
            cache = load_cache(char_dir)
            cache[key] = {"descriptor": best, "canonical_match": canonical_match,
                          "iters": len(hist), "ok": ok,
                          "canonical_match_before": hist[0]["canonical_match"]
                                                    if hist else canonical_match}
            save_cache(char_dir, cache)
        return {"id": champ["id"], "skin": skin_idx, "skipped": False,
                "canonical_match": canonical_match, "ok": ok,
                "iters": len(hist),
                "canonical_match_before": hist[0]["canonical_match"]
                                          if hist else canonical_match}
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
    if skin_indices == "all-enumerated":
        # Phase 3: build per-champ (champ, skin) pairs from the skins/*.jpg
        # files actually on disk for each champ (every skin splash present).
        pairs = []
        for c in champs:
            char_dir = os.path.join(ASSET_DIR, "characters", c["id"])
            for s in _enumerate_skins(char_dir):
                pairs.append((c, s))
    else:
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
    before = [r["canonical_match_before"] for r in results
              if r and "canonical_match_before" in r]
    after = [r["canonical_match"] for r in results
             if r and "canonical_match" in r]
    return {
        "n_processed": n_proc, "n_skipped": n_skip, "n_ok": n_ok,
        "mean_canonical_match_before": round(sum(before) / len(before), 2) if before else 0,
        "mean_canonical_match_after": round(sum(after) / len(after), 2) if after else 0,
        "per_skin": results,
    }
