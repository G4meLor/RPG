"""Inspect a sprite as a human-readable report: shape ramp + named dominant
colors per region. We can't use the Read tool on PNGs (crashes session), so
this is how the coordinator "looks at" a sprite to judge it.

Regions (256x256, body center ~128,150):
  bg-tl / bg-tr / bg-bl / bg-br : the 4 corners (should be empty/transparent)
  head      : y 40-95,  x 100-156 (face lives here)
  torso     : y 95-175, x 90-166
  legs      : y 175-230, x 95-161
  l-weapon  : x 0-95,   y 80-200  (left-side weapon/wing zone)
  r-weapon  : x 161-256, y 80-200 (right-side weapon/wing zone)

For each region: fill% (opaque pixels / region area) and top-3 named colors.

Usage:
  python3 exp/sprite_inspect.py --champ <id> [skin_idx]
  python3 exp/sprite_inspect.py --champs A,B,C
  python3 exp/sprite_inspect.py <path>
"""
import os, sys
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame  # noqa: E402
import pygame.surfarray as sa  # noqa: E402
import numpy as np  # noqa: E402
pygame.init(); pygame.display.set_mode((1, 1))

from src.data.tuning import ASSET_DIR  # noqa: E402

RAMP = " .:-=+*#%@"

# named color palette (name -> RGB). Covers skin tones, common LoL colors.
_NAMED = [
    ("black",       (10, 10, 10)),
    ("dk-gray",     (60, 60, 60)),
    ("gray",        (120, 120, 120)),
    ("lt-gray",     (190, 190, 190)),
    ("white",       (245, 245, 245)),
    ("skin-lt",     (240, 200, 165)),
    ("skin",        (222, 175, 140)),
    ("skin-med",    (196, 145, 110)),
    ("skin-dark",   (150, 100, 70)),
    ("skin-brown",  (110, 70, 45)),
    ("red",         (220, 40, 40)),
    ("dk-red",      (140, 30, 30)),
    ("orange",      (240, 130, 30)),
    ("gold",        (240, 195, 60)),
    ("yellow",      (240, 220, 60)),
    ("brown",       (120, 75, 40)),
    ("dk-brown",    (70, 45, 25)),
    ("green",       (60, 170, 70)),
    ("dk-green",    (40, 110, 50)),
    ("lime",        (170, 230, 60)),
    ("teal",        (40, 170, 160)),
    ("cyan",        (60, 200, 220)),
    ("blue",        (50, 110, 220)),
    ("dk-blue",     (35, 60, 150)),
    ("lt-blue",     (150, 200, 240)),
    ("navy",        (25, 35, 80)),
    ("purple",      (140, 60, 180)),
    ("magenta",     (210, 60, 180)),
    ("pink",        (245, 130, 190)),
    ("hot-pink",    (255, 60, 160)),
]


def _name(rgb):
    r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
    best = "white"; bd = 1e9
    for nm, (pr, pg, pb) in _NAMED:
        d = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if d < bd:
            bd = d; best = nm
    return best


def _load(path):
    s = pygame.image.load(path)
    rgb = sa.array3d(s)                       # (W,H,3)
    if s.get_flags() & pygame.SRCALPHA:
        pa = sa.pixels_alpha(s)
        a = np.array(pa, copy=True); del pa
    else:
        a = np.full(rgb.shape[:2], 255, dtype=np.uint8)
    rgb = np.transpose(rgb, (1, 0, 2))        # (H,W,3)
    a = np.transpose(a, (1, 0))               # (H,W)
    return rgb, a


def _region_colors(rgb, a, y0, y1, x0, x1, thresh=24, topn=3):
    blk_rgb = rgb[y0:y1, x0:x1].reshape(-1, 3)
    blk_a = a[y0:y1, x0:x1].reshape(-1)
    m = blk_a >= thresh
    fill = float(m.mean())
    if fill == 0:
        return 0.0, []
    px = blk_rgb[m]
    # quantize to reduce near-duplicates (step 32)
    q = (px // 32) * 32
    from collections import Counter
    c = Counter(map(tuple, q.tolist()))
    out = []
    for col, n in c.most_common(topn):
        out.append((_name(col), round(100 * n / m.sum()), col))
    return fill, out


REGIONS = {
    "bg-tl": (0, 40, 0, 60),
    "bg-tr": (0, 40, 196, 256),
    "bg-bl": (216, 256, 0, 60),
    "bg-br": (216, 256, 196, 256),
    "head":  (40, 95, 100, 156),
    "torso": (95, 175, 90, 166),
    "legs":  (175, 230, 95, 161),
    "l-wpn": (80, 200, 0, 95),
    "r-wpn": (80, 200, 161, 256),
}


def report(path, ramp=True, cols=40, rows=20):
    if not os.path.exists(path):
        print(f"(missing: {path})"); return
    rgb, a = _load(path)
    H, W = rgb.shape[:2]
    print(f"=== {os.path.basename(os.path.dirname(path))} / {os.path.basename(path)} ===")
    # shape ramp
    if ramp:
        bx = W / cols; by = H / rows
        lines = []
        for r in range(rows):
            y0 = int(r * by); y1 = int((r + 1) * by)
            row = []
            for c in range(cols):
                x0 = int(c * bx); x1 = int((c + 1) * bx)
                ba = a[y0:y1, x0:x1].reshape(-1)
                m = ba >= 24
                if not m.any() or m.mean() < 0.08:
                    row.append(" "); continue
                br = int(rgb[y0:y1, x0:x1].reshape(-1, 3)[m].mean())
                row.append(RAMP[min(9, br * 10 // 256)])
            lines.append("".join(row))
        print("\n".join(lines))
    # regions
    print("\nregion        fill%  top colors (name, %, rgb)")
    for nm, (y0, y1, x0, x1) in REGIONS.items():
        fill, cols_ = _region_colors(rgb, a, y0, y1, x0, x1)
        if fill == 0:
            print(f"  {nm:8s}    0%   (empty)")
            continue
        desc = "  ".join(f"{n}({p}%)" for n, p, _ in cols_)
        print(f"  {nm:8s}  {fill*100:3.0f}%  {desc}")
    # overall dominant
    allm = a.flatten() >= 24
    if allm.any():
        q = (rgb.reshape(-1, 3)[allm] // 32) * 32
        from collections import Counter
        c = Counter(map(tuple, q.tolist()))
        top = ", ".join(f"{_name(col)}({round(100*n/allm.sum())}%)" for col, n in c.most_common(5))
        print(f"  overall   100%  {top}")
    print()


def _champ_path(cid, idx=0):
    if idx == 0:
        p = os.path.join(ASSET_DIR, "characters", cid, "sprite.png")
        if os.path.exists(p):
            return p
    return os.path.join(ASSET_DIR, "characters", cid, "sprites", f"{idx}.png")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("--champ")
    ap.add_argument("--champs")
    ap.add_argument("idx", nargs="?", type=int, default=0)
    ap.add_argument("--no-ramp", action="store_true")
    args = ap.parse_args()
    ramp = not args.no_ramp
    if args.champs:
        for cid in args.champs.split(","):
            report(_champ_path(cid.strip(), 0), ramp=ramp)
    elif args.champ:
        report(_champ_path(args.champ, args.idx), ramp=ramp)
    elif args.path:
        report(args.path, ramp=ramp)
