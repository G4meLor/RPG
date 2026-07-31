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
