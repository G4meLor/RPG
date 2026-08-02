"""Render a 256x256 sprite PNG as an ANSI-colored ASCII grid in the terminal.

We cannot use the Read tool on PNGs in this repo (it crashes the session), so
this downsamples the sprite to a grid and prints colored blocks so a human
(or the coordinator) can actually SEE the sprite: shape, colors, face, weapon,
background issues.

Each cell = average of the block it covers. Cells with alpha < threshold are
blank (space). Cells with content are printed as '█' colored via 24-bit ANSI
truecolor using the average RGB. A brightness-based char ramp ( ░▒▓█ ) gives
shape even if color is stripped.

Usage:
  python3 exp/ascii_sprite.py <path> [cols] [rows]      # one sprite
  python3 exp/ascii_sprite.py --champ <id> [skin_idx]   # by champ id
  python3 exp/ascii_sprite.py --champs A,B,C             # several defaults
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
# use full block always, color carries the info; ramp only for non-color dumps
BLOCK = "█"


def _load_rgba(path):
    s = pygame.image.load(path)
    if s.get_flags() & pygame.SRCALPHA:
        rgb = sa.array3d(s)              # (W,H,3)
        pa = sa.pixels_alpha(s)          # locked surface array
        a = np.array(pa, copy=True)      # copy so we can release the lock
        del pa                           # release the surface lock
    else:
        rgb = sa.array3d(s)
        a = np.full(rgb.shape[:2], 255, dtype=np.uint8)
    # rgb is (W,H,3); transpose to (H,W,3) for natural row/col
    rgb = np.transpose(rgb, (1, 0, 2))
    a = np.transpose(a, (1, 0))
    return rgb, a


def render_grid(path, cols=48, rows=24, alpha_thresh=24, color=True, cell=None):
    """Print the sprite as a colored grid. cell=(row,col) prints only that cell
    with its avg color + alpha (debug)."""
    if not os.path.exists(path):
        print(f"(missing: {path})")
        return
    rgb, a = _load_rgba(path)
    H, W = rgb.shape[:2]
    # block size
    bx = W / cols
    by = H / rows
    if cell:
        r, c = cell
        y0 = int(r * by); y1 = int((r + 1) * by)
        x0 = int(c * bx); x1 = int((c + 1) * bx)
        blk_rgb = rgb[y0:y1, x0:x1].reshape(-1, 3)
        blk_a = a[y0:y1, x0:x1].reshape(-1)
        m = blk_a >= alpha_thresh
        if not m.any():
            print(f"cell({r},{c}): empty")
            return
        avg = blk_rgb[m].mean(axis=0).astype(int)
        print(f"cell({r},{c}): avg RGB={tuple(avg)} alpha~{int(blk_a[m].mean())} "
              f"fill={int(100*m.mean())}%")
        return
    lines = []
    for r in range(rows):
        y0 = int(r * by); y1 = int((r + 1) * by)
        row = []
        for c in range(cols):
            x0 = int(c * bx); x1 = int((c + 1) * bx)
            blk_rgb = rgb[y0:y1, x0:x1].reshape(-1, 3)
            blk_a = a[y0:y1, x0:x1].reshape(-1)
            m = blk_a >= alpha_thresh
            if not m.any() or m.mean() < 0.08:
                row.append(" ")
                continue
            avg = blk_rgb[m].mean(axis=0).astype(int)
            bright = int(avg.mean())
            if color:
                row.append(f"\x1b[38;2;{avg[0]};{avg[1]};{avg[2]}m{BLOCK}\x1b[0m")
            else:
                row.append(RAMP[min(9, bright * 10 // 256)])
        lines.append("".join(row))
    print(f"--- {path} ({cols}x{rows}) ---")
    print("\n".join(lines))


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
    ap.add_argument("--cols", type=int, default=48)
    ap.add_argument("--rows", type=int, default=24)
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument("--cell", nargs=2, type=int, metavar=("R", "C"))
    args = ap.parse_args()
    color = not args.no_color
    if args.champs:
        for cid in args.champs.split(","):
            cid = cid.strip()
            render_grid(_champ_path(cid, 0), args.cols, args.rows, color=color)
            print()
    elif args.champ:
        cell = tuple(args.cell) if args.cell else None
        render_grid(_champ_path(args.champ, args.idx), args.cols, args.rows,
                    color=color, cell=cell)
    elif args.path:
        cell = tuple(args.cell) if args.cell else None
        render_grid(args.path, args.cols, args.rows, color=color, cell=cell)
