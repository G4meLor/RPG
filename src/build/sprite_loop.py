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
    tmp = os.path.join(ASSET_DIR, "characters", hero_id, f"_loop_tmp_{skin_idx}.png")
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
        # Use the BEST round (max match), not the last round, so a late bad
        # critique can't overwrite a good earlier sprite. match_before is the
        # first round's score (the describe() baseline before any revision).
        match = max((h["match"] for h in hist), default=0)
        ok = any(h["ok"] for h in hist) if hist else False
        # P1: skin 0 overwrites sprite.png (the Original world billboard)
        out_png = os.path.join(char_dir, "sprite.png")
        render_to_png(best, out_png)
        cache[key] = {"descriptor": best, "match": match,
                      "iters": len(hist), "ok": ok,
                      "match_before": hist[0]["match"] if hist else match}
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
