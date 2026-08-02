"""Scan all 170 default sprites for SIZE / TRUNCATION problems:

  - TOO BIG: bounding box fills most of canvas AND touches edges (clipped)
  - MISSING BODY: content touches one edge but NOT the opposite (asymmetric =
    truncated on one side), or bounding box is tiny (undersized), or no
    content in expected body regions (head/torso/legs).

For each champ report: bbox (x0,y0,x1,y1), w, h, touches edges (T/B/L/R),
fill%, center-of-mass (cx,cy), and a flag for each problem class.

Usage: python3 exp/sprite_geometry_scan.py [--threshold N]
"""
import os, sys, json
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame  # noqa: E402
import pygame.surfarray as sa  # noqa: E402
import numpy as np  # noqa: E402
pygame.init(); pygame.display.set_mode((1, 1))

from src.data.tuning import ASSET_DIR  # noqa: E402

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
TH = 24  # alpha threshold for "opaque"


def analyze(path):
    s = pygame.image.load(path)
    rgb = sa.array3d(s)
    if s.get_flags() & pygame.SRCALPHA:
        pa = sa.pixels_alpha(s)
        a = np.array(pa, copy=True); del pa
    else:
        a = np.full(rgb.shape[:2], 255, dtype=np.uint8)
    a = np.transpose(a, (1, 0))  # (H, W)
    mask = a >= TH
    H, W = mask.shape
    if not mask.any():
        return None
    ys, xs = np.where(mask)
    y0, y1 = int(ys.min()), int(ys.max())
    x0, x1 = int(xs.min()), int(xs.max())
    bw, bh = x1 - x0 + 1, y1 - y0 + 1
    # touches edges (within 4px of canvas border)
    touch_t = y0 <= 4
    touch_b = y1 >= H - 5
    touch_l = x0 <= 4
    touch_r = x1 >= W - 5
    fill = float(mask.mean())
    # center of mass
    cy = float(ys.mean()); cx = float(xs.mean())
    # region fills
    def reg_fill(ya, yb, xa, xb):
        m = mask[max(0, ya):min(H, yb), max(0, xa):min(W, xb)]
        return float(m.mean()) if m.size else 0.0
    head = reg_fill(30, 95, 80, 176)
    torso = reg_fill(95, 175, 70, 186)
    legs = reg_fill(175, 240, 80, 176)
    return dict(y0=y0, y1=y1, x0=x0, x1=x1, bw=bw, bh=bh,
                touch_t=touch_t, touch_b=touch_b, touch_l=touch_l, touch_r=touch_r,
                fill=fill, cx=cx, cy=cy, head=head, torso=torso, legs=legs,
                W=W, H=H)


def classify(r):
    """Return list of problem flags."""
    flags = []
    if r is None:
        return ["empty"]
    W, H = r["W"], r["H"]
    # TOO BIG: bbox >= 90% of canvas in both dims AND touches >=3 edges (clipped)
    n_touch = sum([r["touch_t"], r["touch_b"], r["touch_l"], r["touch_r"]])
    if r["bw"] >= 0.92 * W and r["bh"] >= 0.92 * H and n_touch >= 3:
        flags.append("TOO_BIG_CLIPPED")
    elif r["bw"] >= 0.95 * W and r["touch_l"] and r["touch_r"]:
        flags.append("TOO_WIDE")
    elif r["bh"] >= 0.95 * H and r["touch_t"] and r["touch_b"]:
        flags.append("TOO_TALL")
    # TRUNCATED: touches one edge but not the opposite (asymmetric), AND big shift
    if r["touch_t"] and not r["touch_b"] and r["bh"] < 0.80 * H:
        flags.append("TRUNC_BOT")
    if r["touch_b"] and not r["touch_t"] and r["bh"] < 0.80 * H:
        flags.append("TRUNC_TOP")
    if r["touch_l"] and not r["touch_r"] and r["bw"] < 0.80 * W:
        flags.append("TRUNC_RIGHT")
    if r["touch_r"] and not r["touch_l"] and r["bw"] < 0.80 * W:
        flags.append("TRUNC_LEFT")
    # OFF-CENTER: center of mass far from canvas center
    if abs(r["cx"] - W / 2) > 0.18 * W:
        flags.append("OFF_CENTER_X")
    if abs(r["cy"] - H / 2) > 0.18 * H:
        flags.append("OFF_CENTER_Y")
    # UNDERSIZED: bbox small
    if r["bw"] < 0.45 * W and r["bh"] < 0.55 * H:
        flags.append("UNDERSIZED")
    # MISSING region (very low fill in an expected body region for a humanoid)
    # only flag if torso is also low (otherwise it's a creature w/o legs etc)
    if r["torso"] < 0.05:
        flags.append("NO_TORSO")
    return flags


def main():
    champs = sorted(os.listdir(os.path.join(ASSET_DIR, "characters")))
    rows = []
    for cid in champs:
        p = os.path.join(ASSET_DIR, "characters", cid, "sprite.png")
        if not os.path.exists(p):
            continue
        try:
            r = analyze(p)
        except Exception:
            continue
        if r is None:
            rows.append((cid, ["empty"], r)); continue
        flags = classify(r)
        rows.append((cid, flags, r))
    # report problems
    prob = [(cid, fl, r) for cid, fl, r in rows if fl]
    print(f"=== {len(prob)} champs with geometry flags (of {len(rows)}) ===\n")
    # group by flag
    from collections import defaultdict
    byflag = defaultdict(list)
    for cid, fl, r in prob:
        for f in fl:
            byflag[f].append((cid, r))
    for f in sorted(byflag, key=lambda k: -len(byflag[k])):
        print(f"--- {f} ({len(byflag[f])}) ---")
        for cid, r in byflag[f]:
            print(f"  {cid:14s} bbox=({r['x0']},{r['y0']})-({r['x1']},{r['y1']}) "
                  f"{r['bw']}x{r['bh']} fill={r['fill']*100:.0f}% "
                  f"com=({r['cx']:.0f},{r['cy']:.0f}) head={r['head']*100:.0f}% "
                  f"torso={r['torso']*100:.0f}% legs={r['legs']*100:.0f}%")
        print()


if __name__ == "__main__":
    main()
