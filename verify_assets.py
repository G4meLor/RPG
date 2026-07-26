"""
Headless asset verification — NO image reading.

Renders each character / enemy / portrait via the same code paths the game uses,
then reports metadata (size, alpha-bbox, mean color, per-channel stats, element
tint) so art quality can be checked without ever opening a PNG with the Read
tool. Safe to run under `SDL_VIDEODRIVER=dummy` or `xvfb-run`.

Run:
    SDL_VIDEODRIVER=dummy python3 verify_assets.py
"""
import os
import sys
import math
import statistics

import pygame

import generate_assets as GA

ASSET_DIR = GA.ASSET_DIR


def _stats(surf):
    """Return lightweight metadata about a Surface without 'reading' it as art."""
    w, h = surf.get_size()
    arr = pygame.surfarray.pixels_alpha(surf)  # (w,h) uint8 view
    alpha = arr.__array__()
    del arr
    # opaque bounding box
    ys, xs = (alpha > 8).nonzero()
    if len(xs) == 0:
        bbox = None
        coverage = 0.0
    else:
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
        coverage = float((alpha > 8).sum()) / (w * h)
    # mean RGB over opaque pixels (sample a small grid to stay cheap)
    mean_rgb = None
    try:
        rgb = pygame.surfarray.pixels3d(surf)
        mask = alpha > 8
        if mask.any():
            r = rgb[:, :, 0][mask].mean()
            g = rgb[:, :, 1][mask].mean()
            b = rgb[:, :, 2][mask].mean()
            mean_rgb = (round(float(r), 1), round(float(g), 1), round(float(b), 1))
        del rgb
    except Exception:
        pass
    return {
        "size": (w, h),
        "bbox": bbox,
        "coverage_pct": round(coverage * 100, 2),
        "mean_rgb_opaque": mean_rgb,
    }


def _hue_bucket(rgb):
    """Crude element guess from mean color for a sanity cross-check."""
    if rgb is None:
        return "?"
    r, g, b = rgb
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 18:
        return "neutral"
    if r >= g and r >= b:
        return "fire/light" if g > 120 else "fire/dark"
    if b >= r and b >= g:
        return "water/dark"
    if g >= r and g >= b:
        return "wind"
    return "light"


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))  # needed for some font/surface ops

    print("=" * 64)
    print("CHARACTERS (chibi 256x256)")
    print("=" * 64)
    rows = []
    for name, element, weapon, hair_style, hair, body, accent in GA.HEROES:
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        GA.draw_chibi(s, element, body, hair, accent, weapon, hair_style)
        st = _stats(s)
        rows.append((name, element, st))
        print(f"{name:9s} el={element:5s} {st['size']} cov={st['coverage_pct']:5.1f}% "
              f"bbox={st['bbox']} mean={st['mean_rgb_opaque']} hue~{_hue_bucket(st['mean_rgb_opaque'])}")

    # quick distinctness check: no two heroes should have identical mean color
    means = [r[2]["mean_rgb_opaque"] for r in rows]
    dups = [m for m in means if means.count(m) > 1]
    print(f"  duplicate mean colors: {len(dups)} (expect ~0)")

    print()
    print("=" * 64)
    print("PORTRAITS (512x512)")
    print("=" * 64)
    for name, element, weapon, hair_style, hair, body, accent in GA.HEROES:
        path = os.path.join(ASSET_DIR, "portraits", f"{name}.png")
        GA.make_portrait(element, body, hair, accent, hair_style, weapon, path)
        # load the saved portrait back to measure the actual saved pixels
        # (loading via pygame.image.load is fine — it is NOT the Read tool)
        s = pygame.image.load(path)
        st = _stats(s)
        print(f"{name:9s} el={element:5s} {st['size']} cov={st['coverage_pct']:5.1f}% "
              f"bbox={st['bbox']} mean={st['mean_rgb_opaque']}")

    print()
    print("=" * 64)
    print("ENEMIES (256x256)")
    print("=" * 64)
    for name, el, pal in GA.ENEMIES:
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        GA.draw_enemy(s, name, pal)
        st = _stats(s)
        print(f"{name:13s} el={el:5s} {st['size']} cov={st['coverage_pct']:5.1f}% "
              f"bbox={st['bbox']} mean={st['mean_rgb_opaque']}")

    print()
    print("OK — all rendered without error.")


if __name__ == "__main__":
    main()
