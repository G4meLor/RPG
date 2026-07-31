"""
Aetheria Gacha - Asset Generator (build-only)

Procedurally draws and saves the SHARED game art: enemy sprites, the 4 boss-ult
skill icons, backgrounds, item icons, UI frames, terrain tiles, landmarks,
village buildings, and ground-loot drops. Also exposes generate_sprites() for
build_champions.py, which draws the descriptor-driven world sprite for each
champion.

Per-champion bundles (splash art, icons, ability icons, skins) are built by
build_champions.py from crawled LoL data — NOT by this module. Runtime VFX
(drawn every frame) live in fx.py.

Run:  python3 generate_assets.py
"""
import os
import math
import random
import numpy as np
import pygame

SEED = 1337
random.seed(SEED)

# Repo root = parent of src/ = two levels up from this file (src/assets_gen/generate.py).
# Assets live at <repo-root>/assets regardless of where this module sits, so the
# path is repo-root-relative (not __file__-relative) to stay correct after the
# move into src/assets_gen/ without a symlink.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ASSET_DIR = os.path.join(_REPO_ROOT, "assets")
for sub in ["characters", "enemies", "skills", "backgrounds", "ui",
            "items", "terrain", "landmarks", "villages", "drops"]:
    os.makedirs(os.path.join(ASSET_DIR, sub), exist_ok=True)

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
ELEMENT_COLORS = {
    "fire":  ( (232, 86, 60),  (255,168, 90), (120, 24, 18) ),
    "water": ( ( 64,150,230),  (140,220,255), ( 18, 48, 96) ),
    "wind":  ( ( 96,200,140),  (180,240,190), ( 24, 84, 56) ),
    "light": ( (245,210, 90),  (255,245,200), (140,110, 30) ),
    "dark":  ( (150, 90,200),  (210,170,240), ( 56, 28, 84) ),
}

# pixel-art scale: each logical pixel is rendered as a PIXEL×PIXEL block so the
# art reads as chunky pixel-art at higher density than Stardew (Stardew tiles are
# 16x16; a 256px sprite at PIXEL=5 -> ~51 logical pixels, 3x Stardew). Palette is
# locked per element (base/light/shadow/outline/accent) so gradients dither
# instead of smoothing. Re-exported from data.py so the rest of the codebase can
# import a single source of truth.
from src.data.elements import PIXEL, PIXEL_PALETTE

RARITY_COLORS = {
    "R":   (140, 150, 165),
    "SR":  (220, 150, 60),
    "SSR": (220, 80, 150),
}

SKY_TOP    = ( 38, 34, 70)
SKY_BOTTOM = (110, 86, 150)

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)),
            int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))

def shade(c, factor):
    """Multiply a color toward black (factor<1) or white (factor>1)."""
    if factor >= 1:
        return (min(255, int(c[0] * factor)),
                min(255, int(c[1] * factor)),
                min(255, int(c[2] * factor)))
    return (max(0, int(c[0] * factor)),
            max(0, int(c[1] * factor)),
            max(0, int(c[2] * factor)))


def _hue_shift(c, deg):
    """Rotate a color's hue by `deg` degrees (a per-hero tint so same-accent
    heroes still differ). Uses colorsys so the rotation is a true hue shift,
    not a flat channel add (which could clip or desaturate). Returns an RGB
    tuple. A no-op if colorsys isn't available (it's stdlib)."""
    import colorsys
    r, g, b = c[0] / 255.0, c[1] / 255.0, c[2] / 255.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    h = (h + deg / 360.0) % 1.0
    r2, g2, b2 = colorsys.hsv_to_rgb(h, s, v)
    return (int(r2 * 255), int(g2 * 255), int(b2 * 255))

# ---------------------------------------------------------------------------
# Pixel-art primitives (chunky pixels, limited palette, dithered gradients, no
# anti-aliasing). Every "logical pixel" below is a PIXEL×PIXEL block so the art
# reads as pixel-art at ~48-logical-pixel density (3x Stardew's 16x16). Gradients
# are 2-color checker dithers (px_dither) instead of smooth lerp_color ramps.
# ---------------------------------------------------------------------------
def px_fill(surf, color, rect):
    """Fill a rect with a single solid color (pixel-art: no anti-aliasing)."""
    pygame.draw.rect(surf, color, rect)

def px_dither(surf, c1, c2, rect, step=None):
    """A 2-color checker dither over a rect (replaces smooth gradients with a
    pixel-art gradient). step is the checker size in px (defaults to PIXEL so the
    dither matches the chunky-pixel grid)."""
    if step is None:
        step = PIXEL
    x, y, w, h = rect
    for yy in range(y, y + h, step):
        for xx in range(x, x + w, step):
            c = c1 if ((xx + yy) // step) % 2 == 0 else c2
            pygame.draw.rect(surf, c, (xx, yy, step, step))

def px_dither_surf(w, h, c1, c2, step=None):
    """Build a small SRCALPHA surface filled with a 2-color checker dither, then
    return it (so it can be clipped to a shape with BLEND_RGBA_MIN)."""
    if step is None:
        step = PIXEL
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for yy in range(0, h, step):
        for xx in range(0, w, step):
            c = c1 if ((xx + yy) // step) % 2 == 0 else c2
            pygame.draw.rect(s, c, (xx, yy, step, step))
    return s

def px_snap(v, step=None):
    """Snap a coordinate to the nearest pixel-grid boundary (so shapes align to
    the chunky-pixel grid)."""
    if step is None:
        step = PIXEL
    return int(round(v / step) * step)

# ---------------------------------------------------------------------------
# High-quality vector helpers (numpy-backed gradients + soft glows)
# ---------------------------------------------------------------------------
def _display_ready():
    """True once a display mode exists, so convert_alpha() is safe to call."""
    return pygame.display.get_init() and pygame.display.get_surface() is not None

def vgrad_surf(w, h, top, bottom, a_top=255, a_bot=255):
    """Vertical RGBA gradient surface (bottom-up). Fast numpy construction."""
    t = np.linspace(0.0, 1.0, max(2, h))[:, None]
    arr = np.empty((h, w, 4), np.uint8)
    arr[..., 0] = (top[0] + (bottom[0] - top[0]) * t)
    arr[..., 1] = (top[1] + (bottom[1] - top[1]) * t)
    arr[..., 2] = (top[2] + (bottom[2] - top[2]) * t)
    arr[..., 3] = (a_top + (a_bot - a_top) * t)
    s = pygame.image.frombuffer(arr.tobytes(), (w, h), "RGBA")
    return s.convert_alpha() if _display_ready() else s

def diag_grad_surf(w, h, top_left, bot_right, a_top=255, a_bot=255):
    """Diagonal gradient (top-left light -> bottom-right dark); gives a soft,
    directional shading useful for bodies/fabric lit from the upper-left."""
    yy, xx = np.ogrid[:h, :w]
    t = (xx / max(1, w - 1) + yy / max(1, h - 1)) * 0.5
    arr = np.empty((h, w, 4), np.uint8)
    arr[..., 0] = (top_left[0] + (bot_right[0] - top_left[0]) * t)
    arr[..., 1] = (top_left[1] + (bot_right[1] - top_left[1]) * t)
    arr[..., 2] = (top_left[2] + (bot_right[2] - top_left[2]) * t)
    arr[..., 3] = (a_top + (a_bot - a_top) * t)
    s = pygame.image.frombuffer(arr.tobytes(), (w, h), "RGBA")
    return s.convert_alpha() if _display_ready() else s

def radial_grad_surf(w, h, inner, outer, center=None, radius=None,
                     a_inner=255, a_outer=0, falloff=1.0):
    """Radial gradient (inner color at center fading to outer at radius)."""
    yy, xx = np.ogrid[:h, :w]
    cx, cy = center if center else ((w - 1) / 2.0, (h - 1) / 2.0)
    rad = radius if radius else max(w, h) / 2.0
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(1e-6, rad)
    t = np.clip(d, 0.0, 1.0) ** falloff
    arr = np.empty((h, w, 4), np.uint8)
    arr[..., 0] = (inner[0] + (outer[0] - inner[0]) * t)
    arr[..., 1] = (inner[1] + (outer[1] - inner[1]) * t)
    arr[..., 2] = (inner[2] + (outer[2] - inner[2]) * t)
    arr[..., 3] = (a_inner + (a_outer - a_inner) * t)
    s = pygame.image.frombuffer(arr.tobytes(), (w, h), "RGBA")
    return s.convert_alpha() if _display_ready() else s

def soft_glow(w, h, color, max_alpha, center=None, radius=None, falloff=1.4):
    """A soft additive-feeling glow disc (alpha falls off from center)."""
    yy, xx = np.ogrid[:h, :w]
    cx, cy = center if center else ((w - 1) / 2.0, (h - 1) / 2.0)
    rad = radius if radius else max(w, h) / 2.0
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / max(1e-6, rad)
    a = np.clip(1.0 - d, 0.0, 1.0) ** falloff * max_alpha
    arr = np.empty((h, w, 4), np.uint8)
    arr[..., 0] = color[0]
    arr[..., 1] = color[1]
    arr[..., 2] = color[2]
    arr[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
    s = pygame.image.frombuffer(arr.tobytes(), (w, h), "RGBA")
    return s.convert_alpha() if _display_ready() else s

def clip_to_rect(surf, rect, border_radius=0):
    """Clip a gradient surface to a (rounded) rectangle shape (alpha-mask)."""
    m = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(m, (255, 255, 255, 255), rect, border_radius=border_radius)
    surf.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

def clip_to_circle(surf, center, radius):
    """Clip a gradient surface to a circle (alpha-mask)."""
    m = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(m, (255, 255, 255, 255), center, radius)
    surf.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

def clip_to_polygon(surf, points):
    """Clip a gradient surface to a polygon (alpha-mask)."""
    m = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), points)
    surf.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

def draw_eyes(surf, cx, cy, color, outline, element, expression="neutral", eye_shape="round"):
    # Pixel-art anime eyes: 2-tone dithered sclera + iris, solid lid blocks,
    # catchlights + lashes. eye_shape varies the eye geometry
    # (round/sharp/wide/half) so heroes of the same element no longer share
    # identical eyes; expression drives eyebrows + mouth. No smooth gradients,
    # no anti-aliased arcs.
    _, light_el, _ = ELEMENT_COLORS[element]
    if eye_shape == "sharp":
        sw, sh, iw, ih, pw, ph, lid_off = 14, 18, 12, 14, 7, 9, -2
    elif eye_shape == "wide":
        sw, sh, iw, ih, pw, ph, lid_off = 20, 22, 16, 18, 9, 11, 1
    elif eye_shape == "half":  # hooded
        sw, sh, iw, ih, pw, ph, lid_off = 18, 12, 14, 12, 8, 9, 3
    else:  # round (default)
        sw, sh, iw, ih, pw, ph, lid_off = 18, 20, 14, 16, 8, 10, 0
    for sx in (-14, 14):
        # white sclera — 2-tone dithered fill clipped to the eye ellipse (no AA)
        scl = px_dither_surf(sw, sh, (252, 252, 255), (218, 222, 235))
        m = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(m, (255, 255, 255, 255), m.get_rect())
        scl.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(scl, (cx + sx - sw // 2, cy - sh // 2))
        # upper eyelid shadow (solid dark block at the top of the eye, no AA)
        pygame.draw.rect(surf, (0, 0, 0), (cx + sx - sw // 2, cy - sh // 2, sw, 4))
        # iris: the hero's personal eye color drives the bright center; the
        # element shows only as a faint outer rim. 2-tone dithered fill clipped
        # to the iris ellipse (no AA radial gradient).
        iris = px_dither_surf(iw, ih, shade(color, 1.25), shade(color, 0.4))
        m2 = pygame.Surface((iw, ih), pygame.SRCALPHA)
        pygame.draw.ellipse(m2, (255, 255, 255, 255), m2.get_rect())
        iris.blit(m2, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(iris, (cx + sx - iw // 2, cy - ih // 2 + lid_off))
        # faint element-tinted outer ring (solid ellipse outline, no AA)
        pygame.draw.ellipse(surf, shade(light_el, 0.9),
                            (cx + sx - iw // 2 - 1, cy - ih // 2 + lid_off - 1, iw + 2, ih + 2), 1)
        # iris texture rings (solid concentric ellipse outlines, no AA arcs)
        for ir in (3, 5):
            if ir * 2 + 2 <= iw:
                pygame.draw.ellipse(surf, shade(color, 0.35),
                                    (cx + sx - ir, cy - 2 - ir // 2 + lid_off, ir * 2, ir * 2 + 2), 1)
        # pupil (dark solid block, no AA)
        pygame.draw.rect(surf, (10, 8, 18),
                         (cx + sx - pw // 2, cy - ph // 2 + lid_off, pw, ph))
        # bottom eyelid line (solid line, no AA arc)
        pygame.draw.line(surf, shade(outline, 0.7),
                         (cx + sx - sw // 2, cy + 4 + lid_off),
                         (cx + sx + sw // 2, cy + 4 + lid_off), 1)
        # upper eyelid thick line + lashes (solid line, no AA arc)
        pygame.draw.line(surf, outline,
                         (cx + sx - sw // 2, cy - 4 + lid_off),
                         (cx + sx + sw // 2, cy - 4 + lid_off), 3)
        # eyelash strokes on outer corner (solid lines, no AA)
        for la in (0.3, 0.5, 0.7):
            lx = cx + sx + 7 + la * 4
            ly = cy - 7 - la * 6 + lid_off
            pygame.draw.line(surf, outline, (int(lx), int(ly)), (int(lx - 4), int(ly + 4)), 1)
        # catchlights vary by eye_shape (solid blocks, no AA)
        if eye_shape == "sharp":
            pygame.draw.rect(surf, (255, 255, 255), (cx + sx - 6, cy - 7 + lid_off, 5, 5))
        elif eye_shape == "wide":
            pygame.draw.rect(surf, (255, 255, 255), (cx + sx - 8, cy - 9 + lid_off, 9, 9))
            pygame.draw.rect(surf, (255, 255, 255), (cx + sx + 2, cy + 1 + lid_off, 5, 5))
        else:
            pygame.draw.rect(surf, (255, 255, 255), (cx + sx - 8, cy - 8 + lid_off, 7, 7))
            pygame.draw.rect(surf, (255, 255, 255), (cx + sx + 2, cy + 1 + lid_off, 3, 3))
            pygame.draw.rect(surf, (255, 255, 255), (cx + sx, cy - 4 + lid_off, 2, 2))
    # eyebrows + mouth vary by expression (solid lines + blocks, no AA arcs)
    if expression == "fierce":
        # angled up-outward eyebrows + slightly open mouth (solid blocks, no AA)
        pygame.draw.line(surf, outline, (cx - 20, cy - 16), (cx - 7, cy - 12), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx - 18, cy - 16), (cx - 9, cy - 12), 1)
        pygame.draw.line(surf, outline, (cx + 7, cy - 12), (cx + 20, cy - 16), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx + 9, cy - 12), (cx + 18, cy - 16), 1)
        # open mouth (solid block, no AA arc)
        pygame.draw.rect(surf, (175, 65, 75), (cx - 8, cy + 15, 16, 8))
        pygame.draw.rect(surf, (255, 180, 180), (cx - 6, cy + 16, 12, 3))
    elif expression == "gentle":
        # flat eyebrows + small smile (solid lines + block, no AA)
        pygame.draw.line(surf, outline, (cx - 20, cy - 14), (cx - 7, cy - 14), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx - 18, cy - 14), (cx - 9, cy - 14), 1)
        pygame.draw.line(surf, outline, (cx + 7, cy - 14), (cx + 20, cy - 14), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx + 9, cy - 14), (cx + 18, cy - 14), 1)
        # smile (a solid block, no AA arc)
        pygame.draw.rect(surf, (175, 65, 75), (cx - 6, cy + 16, 12, 6))
        pygame.draw.rect(surf, (255, 180, 180), (cx - 4, cy + 17, 8, 3))
    elif expression == "stoic":
        # straight horizontal eyebrows + tiny straight mouth line (solid, no AA)
        pygame.draw.line(surf, outline, (cx - 20, cy - 14), (cx - 7, cy - 14), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx - 18, cy - 14), (cx - 9, cy - 14), 1)
        pygame.draw.line(surf, outline, (cx + 7, cy - 14), (cx + 20, cy - 14), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx + 9, cy - 14), (cx + 18, cy - 14), 1)
        pygame.draw.line(surf, (175, 65, 75), (cx - 4, cy + 18), (cx + 4, cy + 18), 2)
    elif expression == "sad":
        # downward eyebrows + downturned mouth (solid, no AA)
        pygame.draw.line(surf, outline, (cx - 20, cy - 12), (cx - 7, cy - 16), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx - 18, cy - 12), (cx - 9, cy - 16), 1)
        pygame.draw.line(surf, outline, (cx + 7, cy - 16), (cx + 20, cy - 12), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx + 9, cy - 16), (cx + 18, cy - 12), 1)
        # downturned mouth (a solid block, no AA arc)
        pygame.draw.rect(surf, (175, 65, 75), (cx - 7, cy + 18, 14, 5))
    else:  # neutral (current behavior, backward compatible)
        pygame.draw.line(surf, outline, (cx - 20, cy - 13), (cx - 7, cy - 15), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx - 18, cy - 13), (cx - 9, cy - 15), 1)
        pygame.draw.line(surf, outline, (cx + 7, cy - 15), (cx + 20, cy - 13), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx + 9, cy - 15), (cx + 18, cy - 13), 1)
        # neutral mouth (a solid block, no AA arc)
        pygame.draw.rect(surf, (175, 65, 75), (cx - 7, cy + 16, 14, 6))
        pygame.draw.rect(surf, (255, 180, 180), (cx - 5, cy + 17, 10, 3))

def draw_weapon(surf, cx, cy, weapon, accent, outline, element):
    """Pixel-art weapons: 2-tone dithered fills + solid blocks, no smooth
    gradients, no anti-aliased arcs. All 6 weapons (sword/staff/bow/dagger/
    shield/orb) preserved so per-hero variety stays intact."""
    _, light_el, _ = ELEMENT_COLORS[element]
    if weapon == "sword":
        # sword in right hand — 2-tone dithered metal + solid reflection bands
        bx, by = cx + 50, 120
        bw, bh = 12, 82
        # metal base — 2-tone dithered fill clipped to the blade rect (no AA)
        blade = px_dither_surf(bw, bh, (225, 228, 240), (140, 145, 165))
        clip_to_rect(blade, pygame.Rect(0, 0, bw, bh))
        surf.blit(blade, (bx - 1, by - 72))
        # reflection bands (solid horizontal blocks, no AA)
        for ry in (8, 28, 48, 62):
            pygame.draw.rect(surf, (255, 255, 255), (bx, by - 72 + ry, bw - 2, 4))
        # dark band for contrast at base (solid block, no AA)
        pygame.draw.rect(surf, (90, 95, 115), (bx, by - 72 + 74, bw, 6))
        # bright edge (left, the sharpened side, solid block, no AA)
        pygame.draw.rect(surf, (250, 252, 255), (bx - 1, by - 72, 3, bh))
        # fuller (center groove line, solid line, no AA)
        pygame.draw.line(surf, (180, 185, 200), (bx + bw // 2, by - 72), (bx + bw // 2, by + 6), 1)
        pygame.draw.rect(surf, outline, (bx - 1, by - 72, bw, bh), 2)
        # crossguard — 2-tone dithered fill clipped to the guard rect (no AA)
        cg = px_dither_surf(24, 8, shade(accent, 1.3), shade(accent, 0.65))
        clip_to_rect(cg, pygame.Rect(0, 0, 24, 8))
        surf.blit(cg, (bx - 7, by + 8))
        # crossguard specular (solid block, no AA)
        pygame.draw.rect(surf, (255, 255, 255), (bx - 7, by + 8, 22, 2))
        pygame.draw.rect(surf, outline, (bx - 7, by + 8, 24, 8), 2)
        # grip (leather-wrapped, solid block + cross-wrap lines, no AA)
        pygame.draw.rect(surf, (130, 85, 50), (bx + 2, by + 16, 8, 20))
        for gy in (20, 24, 28, 32):
            pygame.draw.line(surf, (100, 65, 35), (bx + 2, by + gy), (bx + 10, by + gy), 1)
        pygame.draw.rect(surf, outline, (bx + 2, by + 16, 8, 20), 1)
        # pommel — 2-tone dithered fill clipped to a circle (no AA radial gem)
        pommel = px_dither_surf(10, 10, shade(accent, 1.3), shade(accent, 0.5))
        clip_to_circle(pommel, (5, 5), 4)
        surf.blit(pommel, (bx + 1, by + 34))
        pygame.draw.rect(surf, (255, 255, 255), (bx + 3, by + 35, 3, 3))
        pygame.draw.circle(surf, outline, (bx + 5, by + 38), 4, 2)
    elif weapon == "staff":
        bx, by = cx + 52, 110
        # staff shaft — 2-tone dithered fill clipped to the shaft rect (no AA)
        shaft = px_dither_surf(8, 120, (150, 105, 60), (85, 55, 30))
        clip_to_rect(shaft, pygame.Rect(0, 0, 8, 120))
        surf.blit(shaft, (bx, by - 60))
        # wood grain lines (solid lines, no AA)
        for gx in (2, 5):
            pygame.draw.line(surf, (120, 80, 40), (bx + gx, by - 58), (bx + gx, by + 58), 1)
        pygame.draw.rect(surf, outline, (bx, by - 60, 8, 120), 2)
        # metal ferrule at top (solid block, no AA)
        pygame.draw.rect(surf, (200, 200, 215), (bx - 2, by - 62, 12, 6))
        pygame.draw.rect(surf, outline, (bx - 2, by - 62, 12, 6), 1)
        # glowing crystal head — chunky block halo (no AA soft-glow)
        pygame.draw.circle(surf, light_el, (bx, by - 66), 30)
        pygame.draw.circle(surf, (255, 255, 255), (bx, by - 66), 20)
        # faceted crystal — 2-tone dithered fill clipped to the crystal polygon (no AA)
        crystal_pts = [(bx + 4, by - 82), (bx + 18, by - 62), (bx + 10, by - 52), (bx - 2, by - 52), (bx - 14, by - 62)]
        cg = px_dither_surf(36, 34, shade(light_el, 1.2), shade(accent, 0.45))
        m = pygame.Surface((36, 34), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - (bx - 14), p[1] - (by - 82)) for p in crystal_pts])
        cg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(cg, (bx - 14, by - 82))
        # crystal facets (inner lines, solid, no AA)
        pygame.draw.line(surf, shade(light_el, 0.6), (bx + 4, by - 82), (bx - 2, by - 56), 1)
        pygame.draw.line(surf, shade(light_el, 0.6), (bx + 4, by - 82), (bx + 8, by - 56), 1)
        pygame.draw.polygon(surf, outline, crystal_pts, 2)
        # specular on top point (solid block, no AA)
        pygame.draw.rect(surf, (255, 255, 255), (bx, by - 80, 4, 4))
    elif weapon == "bow":
        bx, by = cx + 54, 150
        # bow limbs — pixel-art: a solid block limb with dithered shading (no AA
        # arcs). The old code drew 4 nested arcs for a compound-curve look; the
        # pixel-art version is a thick solid block with 2-tone dithered shading
        # and a brighter inner block for the lit edge.
        # outer dark wood limb (solid block, no AA)
        pygame.draw.rect(surf, shade(accent, 0.5), (bx - 14, by - 54, 8, 108))
        # mid wood (solid block, no AA)
        pygame.draw.rect(surf, shade(accent, 0.75), (bx - 12, by - 52, 6, 104))
        # inner light wood (solid block, no AA)
        pygame.draw.rect(surf, accent, (bx - 10, by - 50, 4, 100))
        # inner highlight (the lit edge, solid block, no AA)
        pygame.draw.rect(surf, shade(accent, 1.3), (bx - 9, by - 49, 2, 98))
        # grip section (wrapped leather, solid block + wrap lines, no AA)
        pygame.draw.rect(surf, (90, 65, 40), (bx + 2, by - 6, 16, 12))
        for gw in (bx + 4, bx + 10):
            pygame.draw.line(surf, (70, 50, 30), (gw, by - 6), (gw, by + 5), 1)
        pygame.draw.rect(surf, outline, (bx + 2, by - 6, 16, 12), 1)
        # string (solid line, no AA)
        pygame.draw.line(surf, (235, 235, 245), (bx + 10, by - 48), (bx + 10, by + 48), 1)
        # nocked arrow with fletching (solid lines + blocks, no AA)
        pygame.draw.line(surf, (210, 210, 220), (bx - 22, by), (bx + 12, by), 2)
        # arrowhead (solid polygon, no AA)
        pygame.draw.polygon(surf, (220, 220, 235), [(bx + 12, by), (bx + 20, by - 5), (bx + 20, by + 5)])
        # fletching (solid polygons, no AA)
        pygame.draw.polygon(surf, shade(light_el, 0.8), [(bx - 22, by), (bx - 28, by - 7), (bx - 24, by)])
        pygame.draw.polygon(surf, shade(light_el, 0.8), [(bx - 22, by), (bx - 28, by + 7), (bx - 24, by)])
        pygame.draw.polygon(surf, outline, [(bx + 12, by), (bx + 20, by - 5), (bx + 20, by + 5)])
    elif weapon == "dagger":
        bx, by = cx + 48, 150
        # blade triangle — 2-tone dithered fill clipped to the blade polygon (no AA)
        bw2, bh2 = 10, 48
        blade = px_dither_surf(bw2, bh2, (230, 232, 242), (140, 145, 165))
        m = pygame.Surface((bw2, bh2), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255), [(0, 0), (bw2, 0), (bw2 // 2, bh2 - 2)])
        blade.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(blade, (bx - 1, by - 42))
        # reflection bands (solid horizontal blocks, no AA)
        for ry2 in (6, 20, 34):
            pygame.draw.rect(surf, (255, 255, 255), (bx + 1, by - 42 + ry2, 8, 3))
        pygame.draw.rect(surf, (250, 252, 255), (bx - 1, by - 42, 2, bh2 - 2))
        pygame.draw.polygon(surf, outline, [(bx - 1, by - 42), (bx + bw2 - 1, by - 42), (bx + bw2 // 2 - 1, by + 4)], 2)
        # crossguard — 2-tone dithered fill clipped to the guard rect (no AA)
        cg = px_dither_surf(22, 6, shade(accent, 1.3), shade(accent, 0.65))
        clip_to_rect(cg, pygame.Rect(0, 0, 22, 6))
        surf.blit(cg, (bx - 5, by + 2))
        pygame.draw.rect(surf, (255, 255, 255), (bx - 5, by + 2, 20, 2))
        pygame.draw.rect(surf, outline, (bx - 5, by + 2, 22, 6), 2)
        # grip wrap (solid block + cross-wrap lines, no AA)
        pygame.draw.rect(surf, (110, 80, 50), (bx, by + 8, 6, 14))
        for gy2 in (10, 13, 16, 19):
            pygame.draw.line(surf, (85, 60, 35), (bx, by + gy2), (bx + 6, by + gy2), 1)
    elif weapon == "shield":
        bx, by = cx + 44, 170
        pts = [(bx - 6, by - 30), (bx + 22, by - 30), (bx + 22, by + 10), (bx + 8, by + 30), (bx - 6, by + 10)]
        # shield body — 2-tone dithered fill clipped to the shield polygon (no AA)
        shg = px_dither_surf(30, 62, shade(accent, 1.25), shade(accent, 0.5))
        m = pygame.Surface((30, 62), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - (bx - 6), p[1] - (by - 30)) for p in pts])
        shg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(shg, (bx - 6, by - 30))
        # left rim highlight (solid block, no AA)
        pygame.draw.rect(surf, (255, 255, 255), (bx - 6, by - 30, 4, 62))
        # metal rivets around the edge (solid discs, no AA)
        for rv_y in (-26, -10, 6, 20):
            pygame.draw.circle(surf, shade(accent, 0.6), (bx - 2, by + rv_y), 2)
            pygame.draw.rect(surf, (255, 255, 255), (bx - 4, by + rv_y - 1, 2, 2))
        pygame.draw.polygon(surf, outline, pts, 3)
        # central boss — 2-tone dithered fill clipped to a circle (no AA radial)
        boss_base = px_dither_surf(24, 24, shade(accent, 1.4), shade(accent, 0.45))
        clip_to_circle(boss_base, (12, 12), 11)
        surf.blit(boss_base, (bx, by - 16))
        # element gem inset — 2-tone dithered fill clipped to a circle (no AA)
        gem = px_dither_surf(14, 14, light_el, shade(accent, 0.35))
        clip_to_circle(gem, (7, 7), 6)
        surf.blit(gem, (bx + 3, by - 12))
        pygame.draw.rect(surf, (255, 255, 255), (bx + 6, by - 11, 3, 3))
        pygame.draw.circle(surf, outline, (bx + 8, by - 6), 12, 2)
        # bottom edge reinforcement bar (solid block, no AA)
        pygame.draw.rect(surf, shade(accent, 0.55), (bx - 2, by + 26, 24, 5), border_radius=2)
        pygame.draw.rect(surf, outline, (bx - 2, by + 26, 24, 5), 1, border_radius=2)
    elif weapon == "orb":
        bx, by = cx + 50, 160
        # floating orb — chunky block halo (no AA soft-glow)
        pygame.draw.circle(surf, light_el, (bx, by), 30)
        pygame.draw.circle(surf, (255, 255, 255), (bx, by), 20)
        # glassy orb body — 2-tone dithered fill clipped to a circle (no AA)
        orb = px_dither_surf(36, 36, shade(light_el, 1.4), shade(accent, 0.3))
        clip_to_circle(orb, (18, 18), 16)
        surf.blit(orb, (bx - 18, by - 18))
        # inner core — 2-tone dithered fill clipped to a circle (no AA)
        core = px_dither_surf(20, 20, (255, 255, 255), light_el)
        clip_to_circle(core, (10, 10), 8)
        surf.blit(core, (bx - 10, by - 10))
        # glass rim highlight (solid blocks, no AA)
        pygame.draw.rect(surf, (255, 255, 255), (bx - 9, by - 10, 5, 5))
        pygame.draw.rect(surf, (255, 255, 255), (bx - 5, by - 6, 3, 3))
        # secondary reflections on the bottom (solid block, no AA)
        pygame.draw.rect(surf, (255, 255, 255), (bx + 5, by + 7, 2, 2))
        pygame.draw.circle(surf, outline, (bx, by), 16, 2)
        # orbiting motes (solid blocks, no AA)
        for i in range(3):
            ang = -math.pi / 2 + (i - 1) * 0.5
            mx = int(bx + math.cos(ang) * 22)
            my = int(by + math.sin(ang) * 22)
            pygame.draw.circle(surf, light_el, (mx, my), 5)
            pygame.draw.rect(surf, (255, 255, 255), (mx - 2, my - 2, 4, 4))
    elif weapon == "axe":
        bx, by = cx + 50, 140
        # haft — 2-tone dithered wood (solid block, no AA)
        haft = px_dither_surf(7, 110, (150, 105, 60), (85, 55, 30))
        clip_to_rect(haft, pygame.Rect(0, 0, 7, 110))
        surf.blit(haft, (bx, by - 55))
        pygame.draw.rect(surf, outline, (bx, by - 55, 7, 110), 2)
        # axe head — 2-tone dithered fill clipped to a crescent polygon (no AA)
        head_pts = [(bx + 6, by - 40), (bx + 30, by - 48), (bx + 34, by - 30),
                    (bx + 30, by - 12), (bx + 6, by - 20)]
        head = px_dither_surf(30, 40, (200, 205, 220), (110, 115, 135))
        m = pygame.Surface((30, 40), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - bx - 6, p[1] - by + 48) for p in head_pts])
        head.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(head, (bx + 6, by - 48))
        pygame.draw.rect(surf, (255, 255, 255), (bx + 8, by - 44, 4, 4))
        pygame.draw.polygon(surf, outline, head_pts, 2)
    elif weapon == "spear":
        bx, by = cx + 52, 130
        # shaft — 2-tone dithered wood (solid block, no AA)
        shaft = px_dither_surf(6, 130, (150, 105, 60), (85, 55, 30))
        clip_to_rect(shaft, pygame.Rect(0, 0, 6, 130))
        surf.blit(shaft, (bx, by - 70))
        pygame.draw.rect(surf, outline, (bx, by - 70, 6, 130), 2)
        # spearhead — 2-tone dithered fill clipped to a leaf polygon (no AA)
        head_pts = [(bx + 3, by - 86), (bx + 12, by - 74), (bx + 3, by - 62),
                    (bx - 6, by - 74)]
        head = px_dither_surf(18, 24, (225, 228, 240), (140, 145, 165))
        m = pygame.Surface((18, 24), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - bx + 6, p[1] - by + 86) for p in head_pts])
        head.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(head, (bx - 6, by - 86))
        pygame.draw.line(surf, (255, 255, 255), (bx + 2, by - 80), (bx + 2, by - 68), 1)
        pygame.draw.polygon(surf, outline, head_pts, 2)
        # butt spike (solid block, no AA)
        pygame.draw.polygon(surf, (180, 185, 200), [(bx, by + 60), (bx + 6, by + 60), (bx + 3, by + 72)])
    elif weapon == "gun":
        bx, by = cx + 48, 150
        # barrel — 2-tone dithered metal (solid block, no AA)
        barrel = px_dither_surf(46, 10, (90, 95, 115), (50, 55, 70))
        clip_to_rect(barrel, pygame.Rect(0, 0, 46, 10))
        surf.blit(barrel, (bx - 8, by - 5))
        pygame.draw.rect(surf, outline, (bx - 8, by - 5, 46, 10), 2)
        # muzzle (solid block, no AA)
        pygame.draw.rect(surf, (40, 45, 60), (bx + 34, by - 6, 6, 12))
        # sight (solid block, no AA)
        pygame.draw.rect(surf, (60, 65, 80), (bx + 10, by - 12, 4, 8))
        # grip/stock — 2-tone dithered fill (solid block, no AA)
        stock = px_dither_surf(12, 30, shade(accent, 0.8), shade(accent, 0.4))
        clip_to_rect(stock, pygame.Rect(0, 0, 12, 30))
        surf.blit(stock, (bx - 4, by + 4))
        pygame.draw.rect(surf, outline, (bx - 4, by + 4, 12, 30), 2)
        # trigger guard (solid arc-line, no AA)
        pygame.draw.arc(surf, outline, (bx + 2, by + 6, 10, 12), math.pi, 2 * math.pi, 2)
    elif weapon == "fists":
        # big gauntleted fists flanking the body (solid blocks, no AA)
        for side in (-1, 1):
            fx = cx + side * 46
            fy = 168
            fist = px_dither_surf(26, 26, shade(accent, 1.2), shade(accent, 0.5))
            clip_to_circle(fist, (13, 13), 12)
            surf.blit(fist, (fx - 13, fy - 13))
            # knuckle plates (solid blocks, no AA)
            for kx in (-7, -1, 5):
                pygame.draw.rect(surf, (255, 255, 255), (fx + kx, fy - 9, 3, 3))
            pygame.draw.circle(surf, outline, (fx, fy), 12, 2)
    elif weapon == "scythe":
        bx, by = cx + 50, 130
        # shaft — 2-tone dithered wood (solid block, no AA)
        shaft = px_dither_surf(6, 120, (120, 80, 40), (70, 45, 25))
        clip_to_rect(shaft, pygame.Rect(0, 0, 6, 120))
        surf.blit(shaft, (bx, by - 60))
        pygame.draw.rect(surf, outline, (bx, by - 60, 6, 120), 2)
        # curved blade — a thick arc approximated by stacked blocks (no AA arc)
        for i in range(9):
            t = i / 8.0
            ang = math.pi * (0.9 - t * 1.3)
            r = 34
            px_ = int(bx + 3 + math.cos(ang) * r)
            py_ = int(by - 64 + math.sin(ang) * r * 0.55 - t * 6)
            pygame.draw.rect(surf, (220, 225, 240) if i < 5 else (150, 155, 175),
                             (px_ - 2, py_ - 3, 5, 7))
        pygame.draw.circle(surf, outline, (bx + 3, by - 64), 4, 2)
    elif weapon == "whip":
        # a coiled/extended whip — a chain of blocks forming a curve (no AA)
        bx, by = cx + 48, 150
        pts = []
        for i in range(14):
            t = i / 13.0
            x = bx + t * 36
            y = by - 30 + math.sin(t * math.pi * 1.4) * 40 + t * 20
            pts.append((x, y))
        for i, (x, y) in enumerate(pts):
            r = 5 - i // 5
            pygame.draw.circle(surf, shade(accent, 0.6), (int(x), int(y)), r)
            pygame.draw.circle(surf, outline, (int(x), int(y)), r, 1)
        # handle (solid block, no AA)
        pygame.draw.rect(surf, (110, 80, 50), (bx - 2, by - 4, 8, 14))
        pygame.draw.rect(surf, outline, (bx - 2, by - 4, 8, 14), 1)
    # weapon == "none": draw nothing (the archetype's bare hands/body)


# ---------------------------------------------------------------------------
# Descriptor-driven world sprite (Task 3) — 10 archetypes, each a distinct
# silhouette, + shared feature-adders. The descriptor drives the palette +
# motif + features + weapon. This replaces the single-chibi-body approach so
# 170 champions read as visually distinct at the 96px world-billboard scale.
# ---------------------------------------------------------------------------

# Motif -> the element-aura color + a particle kind. Drives the aura disc
# behind the body + the floating particles.
MOTIF_COLOR = {
    "flame":     (255, 140, 60),
    "ice":       (150, 220, 255),
    "wind":      (180, 240, 190),
    "lightning": (255, 240, 150),
    "shadow":    (180, 120, 220),
    "light":     (255, 240, 180),
    "void":      (200, 120, 240),
    "nature":    (140, 220, 130),
}

# Build -> vertical/horizontal scale multipliers on the base silhouette.
BUILD_SCALE = {
    "slender": (0.92, 1.08),
    "average": (1.00, 1.00),
    "bulky":   (1.18, 0.94),
    "tall":    (0.96, 1.12),
    "short":   (1.06, 0.84),
}


def _motif_aura(surf, cx, cy, motif):
    """Draw a small element-aura disc behind the head + a few chunky particles.
    Kept tight (radius 46, alpha-bounded) so it does NOT dominate the sprite's
    coverage/bbox — the archetype silhouette must read as the distinct part."""
    col = MOTIF_COLOR.get(motif, (200, 200, 220))
    dark = shade(col, 0.5)
    aura_r = 46
    aura = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(aura, (*dark, 60), (aura_r, aura_r), aura_r)
    pygame.draw.circle(aura, (*col, 90), (aura_r, aura_r), aura_r - 12)
    pygame.draw.circle(aura, (*shade(col, 1.25), 110), (aura_r, aura_r), aura_r - 24)
    surf.blit(aura, (cx - aura_r, cy - 96))
    # a few chunky particles (stable layout: seeded from the motif string)
    rng = random.Random(sum(ord(c) for c in motif) * 100003 + 7)
    for _ in range(4):
        px = cx + rng.randint(-36, 36)
        py = cy + rng.randint(-30, 40)
        ps = rng.randint(2, 3) * PIXEL // 2
        pygame.draw.rect(surf, col, (int(px), int(py), ps, ps))


def _body_outline(surf, cx, cy, w, h, primary, outline):
    """A chunky pixel-art humanoid body silhouette: torso + head + legs + arms.
    w/h are the scaled body box. Returns the head center (for features)."""
    light = shade(primary, 1.22)
    dark = shade(primary, 0.58)
    # torso — 2-tone dithered fill clipped to a rounded rect (no AA)
    tw, th = int(w * 0.5), int(h * 0.34)
    tx = cx - tw // 2
    ty = cy - th // 2 - int(h * 0.04)
    torso = px_dither_surf(tw, th, light, dark)
    clip_to_rect(torso, pygame.Rect(0, 0, tw, th), border_radius=6)
    surf.blit(torso, (tx, ty))
    pygame.draw.rect(surf, outline, (tx, ty, tw, th), 2, border_radius=6)
    # legs — two solid blocks (no AA)
    lw, lh = int(tw * 0.34), int(h * 0.30)
    ly = ty + th - 2
    for lx in (tx + 3, tx + tw - lw - 3):
        leg = px_dither_surf(lw, lh, shade(primary, 0.7), shade(primary, 0.45))
        clip_to_rect(leg, pygame.Rect(0, 0, lw, lh), border_radius=3)
        surf.blit(leg, (lx, ly))
        pygame.draw.rect(surf, outline, (lx, ly, lw, lh), 2, border_radius=3)
    # arms — two solid blocks flanking the torso (no AA)
    aw, ah = int(tw * 0.26), int(th * 0.92)
    ay = ty + 3
    for ax in (tx - aw - 1, tx + tw + 1):
        arm = px_dither_surf(aw, ah, shade(primary, 0.85), shade(primary, 0.5))
        clip_to_rect(arm, pygame.Rect(0, 0, aw, ah), border_radius=4)
        surf.blit(arm, (ax, ay))
        pygame.draw.rect(surf, outline, (ax, ay, aw, ah), 2, border_radius=4)
    # head — 2-tone dithered fill clipped to a circle (no AA)
    hr = int(w * 0.20)
    hx, hy = cx, ty - hr - 2
    head = px_dither_surf(hr * 2, hr * 2, shade(primary, 1.15), shade(primary, 0.62))
    clip_to_circle(head, (hr, hr), hr - 1)
    surf.blit(head, (hx - hr, hy - hr))
    pygame.draw.circle(surf, outline, (hx, hy), hr, 2)
    # eyes (two chunky blocks, no AA)
    ey = hy - 1
    pygame.draw.rect(surf, (40, 40, 60), (hx - hr // 2 - 1, ey, 3, 3))
    pygame.draw.rect(surf, (40, 40, 60), (hx + hr // 2 - 2, ey, 3, 3))
    return (hx, hy, hr)


def _add_cape(surf, cx, cy, w, h, color, outline):
    """A cape behind the torso — a dithered polygon (no AA)."""
    pts = [(cx - int(w * 0.30), cy - int(h * 0.18)),
           (cx + int(w * 0.30), cy - int(h * 0.18)),
           (cx + int(w * 0.36), cy + int(h * 0.34)),
           (cx - int(w * 0.36), cy + int(h * 0.34))]
    cape = px_dither_surf(int(w * 0.72), int(h * 0.52), shade(color, 1.15), shade(color, 0.5))
    m = pygame.Surface((int(w * 0.72), int(h * 0.52)), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255),
                        [(p[0] - (cx - int(w * 0.36)), p[1] - (cy - int(h * 0.18))) for p in pts])
    cape.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(cape, (cx - int(w * 0.36), cy - int(h * 0.18)))
    pygame.draw.polygon(surf, outline, pts, 2)


def _add_horns(surf, hx, hy, hr, color, outline):
    """Two curved horns above the head (stacked blocks, no AA arc)."""
    for side in (-1, 1):
        bx = hx + side * (hr - 4)
        for i in range(5):
            t = i / 4.0
            x = bx + side * int(t * 10)
            y = hy - hr - int(t * 14)
            r = 5 - i
            pygame.draw.circle(surf, color, (x, y), r)
            pygame.draw.circle(surf, outline, (x, y), r, 1)


def _add_wings(surf, cx, cy, w, h, color, outline):
    """Two bat/feather wings behind the torso (dithered polygons, no AA)."""
    for side in (-1, 1):
        pts = [(cx + side * int(w * 0.28), cy - int(h * 0.16)),
               (cx + side * int(w * 0.62), cy - int(h * 0.08)),
               (cx + side * int(w * 0.58), cy + int(h * 0.20)),
               (cx + side * int(w * 0.28), cy + int(h * 0.10))]
        wing = px_dither_surf(int(w * 0.40), int(h * 0.40), shade(color, 1.1), shade(color, 0.45))
        m = pygame.Surface((int(w * 0.40), int(h * 0.40)), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - min(p[0] for p in pts), p[1] - min(p[1] for p in pts)) for p in pts])
        wing.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(wing, (min(p[0] for p in pts), min(p[1] for p in pts)))
        pygame.draw.polygon(surf, outline, pts, 2)


def _add_hood(surf, hx, hy, hr, color, outline):
    """A hood over the head — a dithered arc (no AA)."""
    hood = pygame.Surface((hr * 2 + 8, hr * 2 + 4), pygame.SRCALPHA)
    pygame.draw.ellipse(hood, (*shade(color, 0.7), 255),
                        (0, 0, hr * 2 + 8, hr * 2 + 4))
    # cut the lower half so the face shows (zero-alpha the lower band)
    sub = pygame.Surface((hr * 2 + 8, hr + 4), pygame.SRCALPHA)
    hood.blit(sub, (0, hr), special_flags=pygame.BLEND_RGBA_SUB)
    surf.blit(hood, (hx - hr - 4, hy - hr - 6))
    pygame.draw.arc(surf, outline, (hx - hr - 4, hy - hr - 6, hr * 2 + 8, hr * 2), math.pi, 2 * math.pi, 2)


def _add_mask(surf, hx, hy, hr, color, outline):
    """A face mask — a dithered band across the eyes (no AA)."""
    band = px_dither_surf(hr * 2, hr // 2 + 2, shade(color, 1.1), shade(color, 0.5))
    clip_to_rect(band, pygame.Rect(0, 0, hr * 2, hr // 2 + 2), border_radius=3)
    surf.blit(band, (hx - hr, hy - hr // 4))
    pygame.draw.rect(surf, outline, (hx - hr, hy - hr // 4, hr * 2, hr // 2 + 2), 2, border_radius=3)
    # eye-slits (solid dark blocks, no AA)
    pygame.draw.rect(surf, (20, 20, 30), (hx - hr // 2 - 1, hy - 1, 3, 3))
    pygame.draw.rect(surf, (20, 20, 30), (hx + hr // 2 - 2, hy - 1, 3, 3))


def _add_crown(surf, hx, hy, hr, color, outline):
    """A crown above the head — a dithered zigzag (no AA)."""
    cy = hy - hr - 2
    pts = [(hx - hr, cy + 8), (hx - hr, cy), (hx - hr // 2, cy + 4),
           (hx - hr // 4, cy - 4), (hx, cy + 2), (hx + hr // 4, cy - 4),
           (hx + hr // 2, cy + 4), (hx + hr, cy), (hx + hr, cy + 8)]
    crown = px_dither_surf(hr * 2, 12, shade(color, 1.3), shade(color, 0.6))
    m = pygame.Surface((hr * 2, 12), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255),
                        [(p[0] - (hx - hr), p[1] - (cy - 4)) for p in pts])
    crown.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(crown, (hx - hr, cy - 4))
    pygame.draw.polygon(surf, outline, pts, 2)


def _add_halo(surf, hx, hy, hr, color, outline):
    """A glowing halo ring above the head (no AA)."""
    pygame.draw.circle(surf, color, (hx, hy - hr - 8), hr // 2 + 2, 3)
    pygame.draw.circle(surf, shade(color, 1.3), (hx, hy - hr - 8), hr // 2 + 2, 1)


def _add_spikes(surf, cx, cy, w, h, color, outline):
    """Spikes along the shoulders (solid triangles, no AA)."""
    ty = cy - int(h * 0.18)
    for i in range(4):
        sx = cx - int(w * 0.30) + i * int(w * 0.20)
        pygame.draw.polygon(surf, color,
                            [(sx, ty), (sx + 4, ty - 10), (sx + 8, ty)])
        pygame.draw.polygon(surf, outline,
                            [(sx, ty), (sx + 4, ty - 10), (sx + 8, ty)], 1)


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


def _apply_features(surf, cx, cy, w, h, hx, hy, hr, features, pal, outline):
    """Apply 0-3 features from the descriptor."""
    sec = pal["secondary"]
    acc = pal["accent"]
    for f in features:
        if f == "cape":
            _add_cape(surf, cx, cy, w, h, sec, outline)
        elif f == "horns":
            _add_horns(surf, hx, hy, hr, shade(acc, 0.85), outline)
        elif f == "wings":
            _add_wings(surf, cx, cy, w, h, shade(sec, 0.8), outline)
        elif f == "hood":
            _add_hood(surf, hx, hy, hr, shade(sec, 0.6), outline)
        elif f == "mask":
            _add_mask(surf, hx, hy, hr, acc, outline)
        elif f == "crown":
            _add_crown(surf, hx, hy, hr, acc, outline)
        elif f == "halo":
            _add_halo(surf, hx, hy, hr, acc, outline)
        elif f == "spikes":
            _add_spikes(surf, cx, cy, w, h, shade(sec, 0.7), outline)
        elif f == "fox_tails":
            _add_fox_tails(surf, cx, cy, w, h, shade(sec, 0.9), outline)
        elif f == "animal_ears":
            _add_animal_ears(surf, hx, hy, hr, shade(sec, 1.1), outline)
        elif f == "claws":
            _add_claws(surf, cx, cy, w, h, shade(acc, 1.1), outline)


# --- per-archetype silhouettes ---------------------------------------------
# Each draws its distinct body onto surf (256x256), returns (hx, hy, hr, w, h)
# so _apply_features + draw_weapon can place features/weapon consistently.
# Anchor: cx,cy = 128,150.

def _arch_knight(surf, cx, cy, pal, outline, build):
    """Armored knight: broad shoulders, plate torso, helmet."""
    sx, sy = BUILD_SCALE.get(build, (1.0, 1.0))
    w, h = int(96 * sx), int(120 * sy)
    primary = pal["primary"]
    sec = pal["secondary"]
    # ground shadow
    sh = pygame.Surface((int(w * 1.6), 16), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 70), sh.get_rect())
    surf.blit(sh, (cx - int(w * 0.8), cy + h // 2 - 2))
    _motif_aura(surf, cx, cy, "light")
    # plate torso — wide, dithered steel (no AA)
    tw, th = int(w * 0.56), int(h * 0.36)
    tx, ty = cx - tw // 2, cy - th // 2 - int(h * 0.04)
    torso = px_dither_surf(tw, th, shade(sec, 1.15), shade(primary, 0.55))
    clip_to_rect(torso, pygame.Rect(0, 0, tw, th), border_radius=6)
    surf.blit(torso, (tx, ty))
    # pauldrons (broad shoulders) — two dithered discs (no AA)
    for side in (-1, 1):
        pd = px_dither_surf(20, 20, shade(sec, 1.2), shade(primary, 0.5))
        clip_to_circle(pd, (10, 10), 9)
        surf.blit(pd, (cx + side * (tw // 2 + 2) - 10, ty - 4))
        pygame.draw.circle(surf, outline, (cx + side * (tw // 2 + 2), ty + 6), 9, 2)
    pygame.draw.rect(surf, outline, (tx, ty, tw, th), 2, border_radius=6)
    # chest emblem (solid block, no AA)
    pygame.draw.rect(surf, pal["accent"], (cx - 6, ty + 6, 12, 12))
    pygame.draw.rect(surf, outline, (cx - 6, ty + 6, 12, 12), 1)
    # legs — armored greaves (solid blocks, no AA)
    lw, lh = int(tw * 0.36), int(h * 0.30)
    ly = ty + th - 2
    for lx in (tx + 3, tx + tw - lw - 3):
        leg = px_dither_surf(lw, lh, shade(primary, 0.75), shade(primary, 0.45))
        clip_to_rect(leg, pygame.Rect(0, 0, lw, lh), border_radius=3)
        surf.blit(leg, (lx, ly))
        pygame.draw.rect(surf, outline, (lx, ly, lw, lh), 2, border_radius=3)
    # arms — gauntlets flanking the torso (solid blocks, no AA)
    aw, ah = int(tw * 0.26), int(th * 0.9)
    ay = ty + 4
    for ax in (tx - aw - 1, tx + tw + 1):
        arm = px_dither_surf(aw, ah, shade(sec, 0.9), shade(primary, 0.5))
        clip_to_rect(arm, pygame.Rect(0, 0, aw, ah), border_radius=4)
        surf.blit(arm, (ax, ay))
        pygame.draw.rect(surf, outline, (ax, ay, aw, ah), 2, border_radius=4)
    # helmet — full helm with a T-visor (no AA)
    hr = int(w * 0.22)
    hx, hy = cx, ty - hr - 2
    helm = px_dither_surf(hr * 2, hr * 2, shade(sec, 1.1), shade(primary, 0.5))
    clip_to_circle(helm, (hr, hr), hr - 1)
    surf.blit(helm, (hx - hr, hy - hr))
    pygame.draw.circle(surf, outline, (hx, hy), hr, 2)
    # T-visor (solid dark blocks, no AA)
    pygame.draw.rect(surf, (30, 30, 40), (hx - hr + 3, hy - 2, hr * 2 - 6, 4))
    pygame.draw.rect(surf, (30, 30, 40), (hx - 2, hy - 2, 4, hr))
    return (hx, hy, hr, w, h)


def _arch_mage(surf, cx, cy, pal, outline, build):
    """Robed mage: floating, no legs visible, hooded robe."""
    sx, sy = BUILD_SCALE.get(build, (1.0, 1.0))
    w, h = int(88 * sx), int(124 * sy)
    primary = pal["primary"]
    sec = pal["secondary"]
    sh = pygame.Surface((int(w * 1.5), 16), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 60), sh.get_rect())
    surf.blit(sh, (cx - int(w * 0.75), cy + h // 2 - 2))
    _motif_aura(surf, cx, cy, "light")
    # robe — a flaring dithered polygon (no AA): narrow at top, wide at bottom
    rtop = int(w * 0.22)
    rbot = int(w * 0.48)
    rty = cy - int(h * 0.20)
    rby = cy + int(h * 0.34)
    pts = [(cx - rtop, rty), (cx + rtop, rty),
           (cx + rbot, rby), (cx - rbot, rby)]
    robe = px_dither_surf(rbot * 2, rby - rty, shade(primary, 1.15), shade(primary, 0.5))
    m = pygame.Surface((rbot * 2, rby - rty), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255),
                        [(p[0] - (cx - rbot), p[1] - rty) for p in pts])
    robe.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(robe, (cx - rbot, rty))
    pygame.draw.polygon(surf, outline, pts, 2)
    # robe trim (solid accent band, no AA)
    pygame.draw.rect(surf, pal["accent"], (cx - rbot, rby - 5, rbot * 2, 5))
    # sleeves — two dithered polygons (no AA)
    for side in (-1, 1):
        spts = [(cx + side * rtop, rty + 2),
                (cx + side * (rtop + 18), rty + 18),
                (cx + side * (rtop + 6), rty + 30),
                (cx + side * (rtop - 4), rty + 16)]
        sl = px_dither_surf(24, 30, shade(primary, 0.95), shade(primary, 0.45))
        m2 = pygame.Surface((24, 30), pygame.SRCALPHA)
        pygame.draw.polygon(m2, (255, 255, 255, 255),
                            [(p[0] - min(p[0] for p in spts), p[1] - min(p[1] for p in spts)) for p in spts])
        sl.blit(m2, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(sl, (min(p[0] for p in spts), min(p[1] for p in spts)))
        pygame.draw.polygon(surf, outline, spts, 2)
    # head — smaller, with a hood (drawn as a feature below); bare here
    hr = int(w * 0.18)
    hx, hy = cx, rty - hr - 2
    head = px_dither_surf(hr * 2, hr * 2, shade(sec, 1.1), shade(primary, 0.6))
    clip_to_circle(head, (hr, hr), hr - 1)
    surf.blit(head, (hx - hr, hy - hr))
    pygame.draw.circle(surf, outline, (hx, hy), hr, 2)
    pygame.draw.rect(surf, (40, 40, 60), (hx - hr // 2 - 1, hy - 1, 3, 3))
    pygame.draw.rect(surf, (40, 40, 60), (hx + hr // 2 - 2, hy - 1, 3, 3))
    return (hx, hy, hr, w, h)


def _arch_archer(surf, cx, cy, pal, outline, build):
    """Lean archer: slim torso, quiver on the back, bow arm."""
    sx, sy = BUILD_SCALE.get(build, (1.0, 1.0))
    w, h = int(84 * sx), int(128 * sy)
    primary = pal["primary"]
    sec = pal["secondary"]
    sh = pygame.Surface((int(w * 1.5), 16), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 65), sh.get_rect())
    surf.blit(sh, (cx - int(w * 0.75), cy + h // 2 - 2))
    _motif_aura(surf, cx, cy, "wind")
    # slim torso — dithered tunic (no AA)
    tw, th = int(w * 0.42), int(h * 0.32)
    tx, ty = cx - tw // 2, cy - th // 2 - int(h * 0.06)
    torso = px_dither_surf(tw, th, shade(sec, 1.12), shade(primary, 0.55))
    clip_to_rect(torso, pygame.Rect(0, 0, tw, th), border_radius=5)
    surf.blit(torso, (tx, ty))
    pygame.draw.rect(surf, outline, (tx, ty, tw, th), 2, border_radius=5)
    # quiver on the back (solid block + arrow fletching, no AA)
    qx = cx + tw // 2 - 2
    pygame.draw.rect(surf, shade(sec, 0.6), (qx, ty - 8, 8, 26), border_radius=2)
    pygame.draw.rect(surf, outline, (qx, ty - 8, 8, 26), 1, border_radius=2)
    for fy in (ty - 14, ty - 10, ty - 6):
        pygame.draw.rect(surf, pal["accent"], (qx + 1, fy, 6, 2))
    # legs — slim, two blocks (no AA)
    lw, lh = int(tw * 0.40), int(h * 0.34)
    ly = ty + th - 2
    for lx in (tx + 2, tx + tw - lw - 2):
        leg = px_dither_surf(lw, lh, shade(primary, 0.7), shade(primary, 0.45))
        clip_to_rect(leg, pygame.Rect(0, 0, lw, lh), border_radius=3)
        surf.blit(leg, (lx, ly))
        pygame.draw.rect(surf, outline, (lx, ly, lw, lh), 2, border_radius=3)
    # bow arm — extended forward (solid block, no AA)
    aw, ah = int(tw * 0.30), int(th * 0.7)
    pygame.draw.rect(surf, shade(sec, 0.8), (tx - aw - 2, ty + 6, aw, ah), border_radius=4)
    pygame.draw.rect(surf, outline, (tx - aw - 2, ty + 6, aw, ah), 1, border_radius=4)
    # head — lean, with a headband (no AA)
    hr = int(w * 0.19)
    hx, hy = cx, ty - hr - 2
    head = px_dither_surf(hr * 2, hr * 2, shade(sec, 1.12), shade(primary, 0.6))
    clip_to_circle(head, (hr, hr), hr - 1)
    surf.blit(head, (hx - hr, hy - hr))
    pygame.draw.circle(surf, outline, (hx, hy), hr, 2)
    pygame.draw.rect(surf, pal["accent"], (hx - hr, hy - hr // 2, hr * 2, 4))
    pygame.draw.rect(surf, (40, 40, 60), (hx - hr // 2 - 1, hy + 1, 3, 3))
    pygame.draw.rect(surf, (40, 40, 60), (hx + hr // 2 - 2, hy + 1, 3, 3))
    return (hx, hy, hr, w, h)


def _arch_brute(surf, cx, cy, pal, outline, build):
    """Huge brute: hunched, massive torso, tiny head, big fists."""
    sx, sy = BUILD_SCALE.get(build, (1.18, 0.94))
    w, h = int(112 * sx), int(116 * sy)
    primary = pal["primary"]
    sec = pal["secondary"]
    sh = pygame.Surface((int(w * 1.5), 18), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 80), sh.get_rect())
    surf.blit(sh, (cx - int(w * 0.75), cy + h // 2 - 2))
    _motif_aura(surf, cx, cy, "flame")
    # massive hunched torso — dithered, wide + short (no AA)
    tw, th = int(w * 0.62), int(h * 0.40)
    tx, ty = cx - tw // 2, cy - th // 2 + int(h * 0.02)
    torso = px_dither_surf(tw, th, shade(sec, 1.1), shade(primary, 0.5))
    clip_to_rect(torso, pygame.Rect(0, 0, tw, th), border_radius=8)
    surf.blit(torso, (tx, ty))
    pygame.draw.rect(surf, outline, (tx, ty, tw, th), 2, border_radius=8)
    # belt (solid accent band, no AA)
    pygame.draw.rect(surf, pal["accent"], (tx, ty + th - 8, tw, 8))
    # legs — thick stumps (solid blocks, no AA)
    lw, lh = int(tw * 0.36), int(h * 0.26)
    ly = ty + th - 4
    for lx in (tx + 4, tx + tw - lw - 4):
        leg = px_dither_surf(lw, lh, shade(primary, 0.7), shade(primary, 0.42))
        clip_to_rect(leg, pygame.Rect(0, 0, lw, lh), border_radius=3)
        surf.blit(leg, (lx, ly))
        pygame.draw.rect(surf, outline, (lx, ly, lw, lh), 2, border_radius=3)
    # massive arms — thick, hanging forward (solid blocks, no AA)
    aw, ah = int(tw * 0.32), int(th * 1.05)
    ay = ty - 2
    for ax in (tx - aw - 2, tx + tw + 2):
        arm = px_dither_surf(aw, ah, shade(sec, 0.95), shade(primary, 0.45))
        clip_to_rect(arm, pygame.Rect(0, 0, aw, ah), border_radius=5)
        surf.blit(arm, (ax, ay))
        pygame.draw.rect(surf, outline, (ax, ay, aw, ah), 2, border_radius=5)
        # big fist at the end (dithered disc, no AA)
        fx = ax + aw // 2
        fy = ay + ah - 2
        fist = px_dither_surf(24, 24, shade(sec, 1.1), shade(primary, 0.5))
        clip_to_circle(fist, (12, 12), 11)
        surf.blit(fist, (fx - 12, fy - 12))
        pygame.draw.circle(surf, outline, (fx, fy), 11, 2)
    # tiny head (hunched forward, low) (no AA)
    hr = int(w * 0.14)
    hx, hy = cx, ty - hr + 2
    head = px_dither_surf(hr * 2, hr * 2, shade(sec, 1.1), shade(primary, 0.6))
    clip_to_circle(head, (hr, hr), hr - 1)
    surf.blit(head, (hx - hr, hy - hr))
    pygame.draw.circle(surf, outline, (hx, hy), hr, 2)
    pygame.draw.rect(surf, (40, 30, 30), (hx - hr // 2, hy, 3, 3))
    pygame.draw.rect(surf, (40, 30, 30), (hx + hr // 2 - 2, hy, 3, 3))
    return (hx, hy, hr, w, h)


def _arch_rogue(surf, cx, cy, pal, outline, build):
    """Crouched rogue: low stance, hood, daggers."""
    sx, sy = BUILD_SCALE.get(build, (0.94, 1.06))
    w, h = int(84 * sx), int(116 * sy)
    primary = pal["primary"]
    sec = pal["secondary"]
    sh = pygame.Surface((int(w * 1.5), 14), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 65), sh.get_rect())
    surf.blit(sh, (cx - int(w * 0.75), cy + h // 2 + 4))
    _motif_aura(surf, cx, cy, "shadow")
    # crouched torso — low + leaning forward (dithered, no AA)
    tw, th = int(w * 0.46), int(h * 0.28)
    tx, ty = cx - tw // 2 + 4, cy - th // 2 + int(h * 0.06)
    torso = px_dither_surf(tw, th, shade(sec, 1.1), shade(primary, 0.5))
    clip_to_rect(torso, pygame.Rect(0, 0, tw, th), border_radius=5)
    surf.blit(torso, (tx, ty))
    pygame.draw.rect(surf, outline, (tx, ty, tw, th), 2, border_radius=5)
    # bent legs — two angled blocks (no AA)
    lw, lh = int(tw * 0.42), int(h * 0.26)
    ly = ty + th - 2
    for lx, lean in ((tx + 2, 6), (tx + tw - lw - 2, -6)):
        leg = px_dither_surf(lw, lh, shade(primary, 0.7), shade(primary, 0.42))
        clip_to_rect(leg, pygame.Rect(0, 0, lw, lh), border_radius=3)
        surf.blit(leg, (lx + lean, ly))
        pygame.draw.rect(surf, outline, (lx + lean, ly, lw, lh), 2, border_radius=3)
    # arms — crossed forward (solid blocks, no AA)
    aw, ah = int(tw * 0.30), int(th * 0.8)
    ay = ty + 4
    for ax in (tx - aw, tx + tw):
        pygame.draw.rect(surf, shade(sec, 0.85), (ax, ay, aw, ah), border_radius=4)
        pygame.draw.rect(surf, outline, (ax, ay, aw, ah), 1, border_radius=4)
    # head — small, hooded (hood added as a feature below)
    hr = int(w * 0.17)
    hx, hy = cx + 4, ty - hr
    head = px_dither_surf(hr * 2, hr * 2, shade(sec, 1.1), shade(primary, 0.6))
    clip_to_circle(head, (hr, hr), hr - 1)
    surf.blit(head, (hx - hr, hy - hr))
    pygame.draw.circle(surf, outline, (hx, hy), hr, 2)
    pygame.draw.rect(surf, (40, 40, 60), (hx - hr // 2, hy - 1, 3, 3))
    pygame.draw.rect(surf, (40, 40, 60), (hx + hr // 2 - 2, hy - 1, 3, 3))
    return (hx, hy, hr, w, h)


def _arch_undead(surf, cx, cy, pal, outline, build):
    """Wraith-like undead: floating, tattered lower body, glowing eyes."""
    sx, sy = BUILD_SCALE.get(build, (0.96, 1.12))
    w, h = int(88 * sx), int(128 * sy)
    primary = pal["primary"]
    sec = pal["secondary"]
    sh = pygame.Surface((int(w * 1.4), 14), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 50), sh.get_rect())
    surf.blit(sh, (cx - int(w * 0.7), cy + h // 2 - 2))
    _motif_aura(surf, cx, cy, "shadow")
    # tattered robe — a jagged-bottom dithered polygon (no AA)
    rtop = int(w * 0.24)
    rbot = int(w * 0.42)
    rty = cy - int(h * 0.22)
    rby = cy + int(h * 0.30)
    # jagged bottom hem
    hem = []
    steps = 6
    for i in range(steps + 1):
        t = i / steps
        x = cx - rbot + t * rbot * 2
        y = rby + (8 if i % 2 else 0)
        hem.append((x, y))
    pts = [(cx - rtop, rty), (cx + rtop, rty)] + hem[::-1]
    robe = px_dither_surf(rbot * 2, rby - rty + 10, shade(primary, 0.85), shade(primary, 0.35))
    m = pygame.Surface((rbot * 2, rby - rty + 10), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255),
                        [(p[0] - (cx - rbot), p[1] - rty) for p in pts])
    robe.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(robe, (cx - rbot, rty))
    pygame.draw.polygon(surf, outline, pts, 2)
    # spectral arms — thin, fading (solid blocks, no AA)
    aw, ah = int(rtop * 0.5), int(h * 0.30)
    ay = rty + 4
    for ax in (cx - rtop - aw - 2, cx + rtop + 2):
        arm = pygame.Surface((aw, ah), pygame.SRCALPHA)
        pygame.draw.rect(arm, (*shade(primary, 0.7), 180), (0, 0, aw, ah), border_radius=3)
        surf.blit(arm, (ax, ay))
        pygame.draw.rect(surf, outline, (ax, ay, aw, ah), 1, border_radius=3)
    # head — skull-like, with glowing eyes (no AA)
    hr = int(w * 0.19)
    hx, hy = cx, rty - hr - 2
    head = px_dither_surf(hr * 2, hr * 2, shade(sec, 0.9), shade(primary, 0.4))
    clip_to_circle(head, (hr, hr), hr - 1)
    surf.blit(head, (hx - hr, hy - hr))
    pygame.draw.circle(surf, outline, (hx, hy), hr, 2)
    # glowing eyes (solid bright blocks, no AA)
    glow = pal["accent"]
    pygame.draw.rect(surf, glow, (hx - hr // 2 - 1, hy - 1, 4, 4))
    pygame.draw.rect(surf, glow, (hx + hr // 2 - 3, hy - 1, 4, 4))
    pygame.draw.rect(surf, shade(glow, 1.3), (hx - hr // 2, hy, 2, 2))
    pygame.draw.rect(surf, shade(glow, 1.3), (hx + hr // 2 - 2, hy, 2, 2))
    return (hx, hy, hr, w, h)


def _arch_yordle(surf, cx, cy, pal, outline, build):
    """Tiny yordle: big head, small body, big ears."""
    sx, sy = BUILD_SCALE.get(build, (1.06, 0.84))
    w, h = int(76 * sx), int(96 * sy)
    primary = pal["primary"]
    sec = pal["secondary"]
    sh = pygame.Surface((int(w * 1.5), 12), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 60), sh.get_rect())
    surf.blit(sh, (cx - int(w * 0.75), cy + h // 2 + 4))
    _motif_aura(surf, cx, cy, "nature")
    # tiny body — small dithered torso (no AA)
    tw, th = int(w * 0.40), int(h * 0.30)
    tx, ty = cx - tw // 2, cy + int(h * 0.06)
    torso = px_dither_surf(tw, th, shade(sec, 1.12), shade(primary, 0.55))
    clip_to_rect(torso, pygame.Rect(0, 0, tw, th), border_radius=5)
    surf.blit(torso, (tx, ty))
    pygame.draw.rect(surf, outline, (tx, ty, tw, th), 2, border_radius=5)
    # little legs (solid blocks, no AA)
    lw, lh = int(tw * 0.40), int(h * 0.18)
    ly = ty + th - 2
    for lx in (tx + 2, tx + tw - lw - 2):
        pygame.draw.rect(surf, shade(primary, 0.6), (lx, ly, lw, lh), border_radius=3)
        pygame.draw.rect(surf, outline, (lx, ly, lw, lh), 1, border_radius=3)
    # little arms (solid blocks, no AA)
    aw, ah = int(tw * 0.26), int(th * 0.8)
    ay = ty + 2
    for ax in (tx - aw, tx + tw):
        pygame.draw.rect(surf, shade(sec, 0.85), (ax, ay, aw, ah), border_radius=4)
        pygame.draw.rect(surf, outline, (ax, ay, aw, ah), 1, border_radius=4)
    # BIG head — oversized for the yordle look (no AA)
    hr = int(w * 0.30)
    hx, hy = cx, ty - hr + 2
    head = px_dither_surf(hr * 2, hr * 2, shade(sec, 1.12), shade(primary, 0.6))
    clip_to_circle(head, (hr, hr), hr - 1)
    surf.blit(head, (hx - hr, hy - hr))
    pygame.draw.circle(surf, outline, (hx, hy), hr, 2)
    # big ears (two dithered ellipses, no AA)
    for side in (-1, 1):
        ear = pygame.Surface((hr, hr), pygame.SRCALPHA)
        pygame.draw.ellipse(ear, (*shade(sec, 1.05), 255), (0, 0, hr, hr))
        surf.blit(ear, (hx + side * hr - hr // 2, hy - hr // 4))
        pygame.draw.ellipse(surf, outline, (hx + side * hr - hr // 2, hy - hr // 4, hr, hr), 2)
    # big eyes (no AA)
    pygame.draw.rect(surf, (40, 40, 60), (hx - hr // 2, hy - 2, 5, 5))
    pygame.draw.rect(surf, (40, 40, 60), (hx + hr // 2 - 4, hy - 2, 5, 5))
    pygame.draw.rect(surf, (255, 255, 255), (hx - hr // 2 + 1, hy - 1, 2, 2))
    pygame.draw.rect(surf, (255, 255, 255), (hx + hr // 2 - 3, hy - 1, 2, 2))
    return (hx, hy, hr, w, h)


def _arch_vastaya(surf, cx, cy, pal, outline, build):
    """Vastaya: humanoid with animal ears + a tail."""
    sx, sy = BUILD_SCALE.get(build, (1.0, 1.04))
    w, h = int(90 * sx), int(122 * sy)
    primary = pal["primary"]
    sec = pal["secondary"]
    sh = pygame.Surface((int(w * 1.5), 16), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 65), sh.get_rect())
    surf.blit(sh, (cx - int(w * 0.75), cy + h // 2 - 2))
    _motif_aura(surf, cx, cy, "wind")
    # humanoid body (reuse the base silhouette)
    hx, hy, hr = _body_outline(surf, cx, cy, w, h, primary, outline)
    # animal ears — two pointed triangles on the head (no AA)
    for side in (-1, 1):
        ex = hx + side * (hr - 2)
        pygame.draw.polygon(surf, shade(sec, 1.1),
                            [(ex - 5, hy - hr + 2), (ex + 5, hy - hr + 2), (ex, hy - hr - 12)])
        pygame.draw.polygon(surf, outline,
                            [(ex - 5, hy - hr + 2), (ex + 5, hy - hr + 2), (ex, hy - hr - 12)], 2)
        pygame.draw.polygon(surf, shade(pal["accent"], 1.2),
                            [(ex - 2, hy - hr + 1), (ex + 2, hy - hr + 1), (ex, hy - hr - 6)])
    # tail — a curved block chain behind the body (no AA)
    tx0 = cx - int(w * 0.30)
    ty0 = cy + int(h * 0.20)
    for i in range(7):
        t = i / 6.0
        x = tx0 - int(t * 14)
        y = ty0 - int(math.sin(t * math.pi) * 18)
        r = 5 - i // 3
        pygame.draw.circle(surf, shade(sec, 0.9), (x, y), r)
        pygame.draw.circle(surf, outline, (x, y), r, 1)
    return (hx, hy, hr, w, h)


def _arch_construct(surf, cx, cy, pal, outline, build):
    """Construct: angular, rocky/metallic, segmented joints."""
    sx, sy = BUILD_SCALE.get(build, (1.18, 0.96))
    w, h = int(104 * sx), int(118 * sy)
    primary = pal["primary"]
    sec = pal["secondary"]
    sh = pygame.Surface((int(w * 1.5), 18), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 75), sh.get_rect())
    surf.blit(sh, (cx - int(w * 0.75), cy + h // 2 - 2))
    _motif_aura(surf, cx, cy, "lightning")
    # angular torso — a dithered hexagon (no AA)
    tw, th = int(w * 0.56), int(h * 0.38)
    tx, ty = cx - tw // 2, cy - th // 2 - int(h * 0.04)
    pts = [(cx, ty - 6), (cx + tw // 2, ty + 6), (cx + tw // 2, ty + th - 6),
           (cx, ty + th), (cx - tw // 2, ty + th - 6), (cx - tw // 2, ty + 6)]
    torso = px_dither_surf(tw, th, shade(sec, 1.1), shade(primary, 0.5))
    m = pygame.Surface((tw, th), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255),
                        [(p[0] - (cx - tw // 2), p[1] - ty) for p in pts])
    torso.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(torso, (cx - tw // 2, ty))
    # core gem in the chest (dithered disc, no AA)
    gem = px_dither_surf(20, 20, pal["accent"], shade(pal["accent"], 0.4))
    clip_to_circle(gem, (10, 10), 9)
    surf.blit(gem, (cx - 10, ty + th // 2 - 10))
    pygame.draw.circle(surf, outline, (cx, ty + th // 2), 9, 2)
    pygame.draw.polygon(surf, outline, pts, 2)
    # segmented legs — blocky (solid blocks, no AA)
    lw, lh = int(tw * 0.34), int(h * 0.28)
    ly = ty + th - 4
    for lx in (tx + 4, tx + tw - lw - 4):
        pygame.draw.rect(surf, shade(primary, 0.7), (lx, ly, lw, lh), border_radius=2)
        pygame.draw.rect(surf, shade(primary, 0.5), (lx, ly + lh // 2, lw, 4))
        pygame.draw.rect(surf, outline, (lx, ly, lw, lh), 2, border_radius=2)
    # blocky arms (solid blocks, no AA)
    aw, ah = int(tw * 0.28), int(th * 0.95)
    ay = ty + 2
    for ax in (tx - aw - 2, tx + tw + 2):
        pygame.draw.rect(surf, shade(sec, 0.9), (ax, ay, aw, ah), border_radius=3)
        pygame.draw.rect(surf, shade(primary, 0.5), (ax, ay + ah // 2, aw, 4))
        pygame.draw.rect(surf, outline, (ax, ay, aw, ah), 2, border_radius=3)
    # head — a rectangular helm (no AA)
    hr = int(w * 0.18)
    hx, hy = cx, ty - hr - 4
    pygame.draw.rect(surf, shade(sec, 1.1), (hx - hr, hy - hr, hr * 2, hr * 2), border_radius=3)
    pygame.draw.rect(surf, outline, (hx - hr, hy - hr, hr * 2, hr * 2), 2, border_radius=3)
    # visor slit (solid dark block, no AA)
    pygame.draw.rect(surf, pal["accent"], (hx - hr + 3, hy - 2, hr * 2 - 6, 4))
    pygame.draw.rect(surf, (30, 30, 40), (hx - hr + 4, hy - 1, hr * 2 - 8, 2))
    return (hx, hy, hr, 0, 0)  # w,h unused for construct features


def _arch_beast(surf, cx, cy, pal, outline, build):
    """Beast: feral, hunched-forward, clawed, bestial head."""
    sx, sy = BUILD_SCALE.get(build, (1.10, 0.92))
    w, h = int(108 * sx), int(112 * sy)
    primary = pal["primary"]
    sec = pal["secondary"]
    sh = pygame.Surface((int(w * 1.6), 16), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 75), sh.get_rect())
    surf.blit(sh, (cx - int(w * 0.8), cy + h // 2 - 2))
    _motif_aura(surf, cx, cy, "nature")
    # hunched feral torso — dithered, leaning forward (no AA)
    tw, th = int(w * 0.58), int(h * 0.36)
    tx, ty = cx - tw // 2 + 6, cy - th // 2 + int(h * 0.04)
    torso = px_dither_surf(tw, th, shade(sec, 1.05), shade(primary, 0.45))
    clip_to_rect(torso, pygame.Rect(0, 0, tw, th), border_radius=8)
    surf.blit(torso, (tx, ty))
    pygame.draw.rect(surf, outline, (tx, ty, tw, th), 2, border_radius=8)
    # fur tufts along the back (solid triangles, no AA)
    for i in range(5):
        fx = tx + i * (tw // 4)
        pygame.draw.polygon(surf, shade(primary, 0.6),
                            [(fx, ty + 2), (fx + 4, ty - 8), (fx + 8, ty + 2)])
    # bent legs — digitigrade (angled blocks, no AA)
    lw, lh = int(tw * 0.34), int(h * 0.30)
    ly = ty + th - 2
    for lx, lean in ((tx + 4, 8), (tx + tw - lw - 4, -8)):
        leg = px_dither_surf(lw, lh, shade(primary, 0.7), shade(primary, 0.42))
        clip_to_rect(leg, pygame.Rect(0, 0, lw, lh), border_radius=3)
        surf.blit(leg, (lx + lean, ly))
        pygame.draw.rect(surf, outline, (lx + lean, ly, lw, lh), 2, border_radius=3)
        # claws at the foot (solid triangles, no AA)
        pygame.draw.polygon(surf, shade(sec, 1.1),
                            [(lx + lean, ly + lh), (lx + lean + 4, ly + lh + 6), (lx + lean + 8, ly + lh)])
    # long arms reaching forward (solid blocks, no AA)
    aw, ah = int(tw * 0.32), int(th * 1.0)
    ay = ty
    for ax in (tx - aw - 2, tx + tw + 2):
        pygame.draw.rect(surf, shade(sec, 0.9), (ax, ay, aw, ah), border_radius=5)
        pygame.draw.rect(surf, outline, (ax, ay, aw, ah), 2, border_radius=5)
        # claws (solid triangles, no AA)
        for ci in range(3):
            pygame.draw.polygon(surf, shade(sec, 1.2),
                                [(ax + ci * 4, ay + ah), (ax + ci * 4 + 2, ay + ah + 7), (ax + ci * 4 + 4, ay + ah)])
    # bestial head — elongated, with a snout (no AA)
    hr = int(w * 0.16)
    hx, hy = cx + 8, ty - hr - 2
    head = px_dither_surf(hr * 2 + 10, hr * 2, shade(sec, 1.05), shade(primary, 0.5))
    clip_to_rect(head, pygame.Rect(0, 0, hr * 2 + 10, hr * 2), border_radius=6)
    surf.blit(head, (hx - hr, hy - hr))
    pygame.draw.rect(surf, outline, (hx - hr, hy - hr, hr * 2 + 10, hr * 2), 2, border_radius=6)
    # snout (solid block, no AA)
    pygame.draw.rect(surf, shade(primary, 0.7), (hx + hr - 2, hy + 2, 12, 8), border_radius=3)
    # pointed ears (solid triangles, no AA)
    for side in (-1, 1):
        pygame.draw.polygon(surf, shade(sec, 1.1),
                            [(hx + side * (hr - 4), hy - hr + 2), (hx + side * (hr + 2), hy - hr + 2), (hx + side * hr, hy - hr - 10)])
    # glowing eyes (solid bright blocks, no AA)
    pygame.draw.rect(surf, pal["accent"], (hx - hr // 2, hy - 1, 4, 4))
    pygame.draw.rect(surf, pal["accent"], (hx + 2, hy - 1, 4, 4))
    return (hx, hy, hr, w, h)


# archetype dispatcher
_ARCH_DRAW = {
    "knight": _arch_knight, "mage": _arch_mage, "archer": _arch_archer,
    "brute": _arch_brute, "rogue": _arch_rogue, "undead": _arch_undead,
    "yordle": _arch_yordle, "vastaya": _arch_vastaya,
    "construct": _arch_construct, "beast": _arch_beast,
}


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


def generate_sprites(champs):
    """Generate the descriptor-driven world sprite for every champion."""
    pygame.init()
    pygame.display.set_mode((1, 1))
    n = 0
    for c in champs:
        key = c["id"]
        desc = c["descriptor"]
        hero_dir = os.path.join(ASSET_DIR, "characters", key)
        os.makedirs(hero_dir, exist_ok=True)
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        draw_chibi_descriptor(s, desc)
        pygame.image.save(s, os.path.join(hero_dir, "sprite.png"))
        n += 1
    print(f"Generated {n} descriptor-driven world sprites")



def _grad_ellipse(surf, rect, inner, outer, center=None, falloff=1.0):
    """Fill an ellipse with a 2-tone dithered fill (pixel-art: no AA radial
    gradient). inner at center, outer at edge, clipped to the ellipse shape."""
    x, y, w, h = rect
    g = px_dither_surf(w, h, inner, outer)
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(m, (255, 255, 255, 255), m.get_rect())
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(g, (x, y))

def _grad_round_rect(surf, rect, top_left, bot_right, border_radius=0):
    """Fill a (rounded) rect with a 2-tone dithered fill (pixel-art: no AA
    diagonal gradient)."""
    x, y, w, h = rect
    g = px_dither_surf(w, h, top_left, bot_right)
    clip_to_rect(g, pygame.Rect(0, 0, w, h), border_radius=border_radius)
    surf.blit(g, (x, y))

def _glowing_eye(surf, pos, core, glow_col, r_core=5, r_glow=14):
    """A glowing eye: a chunky block halo + bright core + dark pupil (pixel-art:
    no soft-glow AA)."""
    gx, gy = pos
    # chunky block halo (a filled disc of the glow color, no AA falloff)
    halo = pygame.Surface((r_glow * 2, r_glow * 2), pygame.SRCALPHA)
    pygame.draw.circle(halo, (*glow_col, 120), (r_glow, r_glow), r_glow)
    surf.blit(halo, (gx - r_glow, gy - r_glow))
    pygame.draw.circle(surf, core, (gx, gy), r_core)
    pygame.draw.circle(surf, shade(core, 1.3), (gx - r_core // 3, gy - r_core // 3), max(1, r_core // 3))
    pygame.draw.circle(surf, (30, 26, 40), (gx, gy), r_core, 1)

def draw_enemy(surf, kind, palette):
    cx, cy = 128, 140
    outline = (30, 26, 40)
    main, accent, dark = palette
    main_light = shade(main, 1.22)
    main_dark = shade(main, 0.62)
    accent_light = shade(accent, 1.22)
    dark_light = shade(dark, 1.25)
    # The LoL mob/boss ids alias to the closest-fitting legacy silhouette so the
    # existing per-kind art is reused without rewriting 16 sprites. Unknown ids
    # fall through to the default branch (shadow + body block).
    _ALIAS = {
        "Razorbeaks": "harpy", "Krugs": "golem", "Voidlings": "imp",
        "FallenKnight": "paladin", "MurkWolves": "wolf",
        "CrimsonRaptor": "orc", "Gromp": "slime", "Wraiths": "wraith",
        "Raptors": "harpy", "VoidHound": "ghoul",
        "Sylas": "demonking", "Swain": "dragon", "Lissandra": "frosttitan",
        "Mordekaiser": "demonking", "Viego": "wraith", "Baron": "embertyrant",
    }
    kind = _ALIAS.get(kind, kind)

    # ground shadow (chunky ellipse, no AA)
    shadow = pygame.Surface((180, 44), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 80), shadow.get_rect())
    surf.blit(shadow, (cx - 90, 222))

    if kind == "slime":
        # gelatinous body — 2-tone dithered fill clipped to an ellipse (no AA)
        body_r = pygame.Rect(cx - 60, cy - 30, 120, 90)
        _grad_ellipse(surf, body_r, main_light, main_dark, center=(40, 24), falloff=1.3)
        pygame.draw.ellipse(surf, outline, body_r, 4)
        # glossy highlight (solid blocks, no AA)
        pygame.draw.rect(surf, (255, 255, 255), (cx - 40, cy - 22, 16, 10))
        pygame.draw.rect(surf, shade(main_light, 1.1), (cx - 30, cy - 14, 16, 10))
        draw_eyes(surf, cx, cy + 8, (20, 20, 30), outline, "dark")
    elif kind == "goblin":
        # body — 2-tone dithered fill (no AA diagonal gradient)
        body_r = pygame.Rect(cx - 30, cy, 60, 70)
        _grad_round_rect(surf, body_r, main_light, main_dark, border_radius=16)
        pygame.draw.rect(surf, outline, body_r, 3, border_radius=16)
        # head — 2-tone dithered fill clipped to a circle (no AA radial gradient)
        head_g = px_dither_surf(68, 68, main_light, main_dark)
        clip_to_circle(head_g, (34, 34), 34)
        surf.blit(head_g, (cx - 34, cy - 54))
        pygame.draw.circle(surf, outline, (cx, cy - 20), 34, 3)
        # ears (solid palette fills, no AA)
        for sx in (-1, 1):
            ear = [(cx + sx * 34, cy - 22), (cx + sx * 56, cy - 36), (cx + sx * 30, cy - 8)]
            pygame.draw.polygon(surf, main, ear)
            pygame.draw.polygon(surf, main_dark, [(cx + sx * 34, cy - 22), (cx + sx * 50, cy - 32), (cx + sx * 36, cy - 18)])
            pygame.draw.polygon(surf, outline, ear, 3)
        for sx in (-12, 12):
            _glowing_eye(surf, (cx + sx, cy - 22), (255, 230, 60), (255, 200, 40), r_core=4, r_glow=10)
        # club (solid wood block + dithered knob, no AA)
        pygame.draw.rect(surf, (140, 95, 55), (cx + 36, cy - 10, 10, 60))
        pygame.draw.rect(surf, (90, 60, 35), (cx + 36, cy - 10, 5, 60))
        knob = px_dither_surf(32, 32, (150, 100, 60), (80, 50, 28))
        clip_to_circle(knob, (16, 16), 16)
        surf.blit(knob, (cx + 25, cy - 26))
        pygame.draw.rect(surf, outline, (cx + 36, cy - 10, 10, 60), 2)
        pygame.draw.circle(surf, outline, (cx + 41, cy - 10), 16, 3)
    elif kind == "bat":
        # body — 2-tone dithered fill clipped to a circle (no AA)
        body_g = px_dither_surf(60, 60, shade(dark, 1.25), dark)
        clip_to_circle(body_g, (30, 30), 30)
        surf.blit(body_g, (cx - 30, cy - 30))
        pygame.draw.circle(surf, outline, (cx, cy), 30, 3)
        # wings — 2-tone dithered fill clipped to the wing polygon (no AA)
        for sx in (-1, 1):
            pts = [(cx, cy - 6), (cx + sx * 70, cy - 40), (cx + sx * 80, cy), (cx + sx * 50, cy + 6), (cx + sx * 30, cy - 6)]
            wg = px_dither_surf(90, 50, main, shade(main, 0.6))
            m = pygame.Surface((90, 50), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255),
                                [(p[0] - (cx - 10), p[1] - (cy - 40)) if sx > 0 else (p[0] - (cx - 80), p[1] - (cy - 40)) for p in pts])
            wg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(wg, (cx - 10 if sx > 0 else cx - 80, cy - 40))
            pygame.draw.polygon(surf, outline, pts, 3)
            # wing finger bones (solid lines, no AA)
            pygame.draw.line(surf, dark, (cx, cy - 6), (cx + sx * 70, cy - 40), 2)
            pygame.draw.line(surf, dark, (cx, cy - 6), (cx + sx * 78, cy - 4), 2)
            pygame.draw.line(surf, dark, (cx, cy - 6), (cx + sx * 50, cy + 6), 2)
        for sx in (-10, 10):
            _glowing_eye(surf, (cx + sx, cy - 4), (255, 70, 70), (255, 40, 40), r_core=4, r_glow=10)
        # fangs (solid blocks, no AA)
        pygame.draw.polygon(surf, (240, 240, 230), [(cx - 6, cy + 14), (cx - 8, cy + 22), (cx - 4, cy + 16)])
        pygame.draw.polygon(surf, (240, 240, 230), [(cx + 6, cy + 14), (cx + 8, cy + 22), (cx + 4, cy + 16)])
        pygame.draw.polygon(surf, outline, [(cx - 6, cy + 14), (cx, cy + 22), (cx + 6, cy + 14)], 2)
    elif kind == "skeleton":
        bone = (240, 240, 232)
        bone_dark = (200, 200, 192)
        # skull — 2-tone dithered fill clipped to a circle (no AA)
        skull = px_dither_surf(64, 64, (255, 255, 250), bone_dark)
        clip_to_circle(skull, (32, 32), 32)
        surf.blit(skull, (cx - 32, cy - 56))
        pygame.draw.circle(surf, outline, (cx, cy - 24), 32, 3)
        # eye sockets (solid dark voids, no AA)
        for sx in (-12, 12):
            pygame.draw.rect(surf, (20, 20, 30), (cx + sx - 6, cy - 26, 12, 12))
            pygame.draw.rect(surf, (60, 60, 80), (cx + sx - 6, cy - 26, 4, 4))
        # nose (solid triangle, no AA)
        pygame.draw.polygon(surf, (20, 20, 30), [(cx - 3, cy - 14), (cx + 3, cy - 14), (cx, cy - 8)])
        # ribcage — 2-tone dithered fill (no AA)
        rib_r = pygame.Rect(cx - 22, cy + 8, 44, 50)
        _grad_round_rect(surf, rib_r, bone, bone_dark, border_radius=10)
        pygame.draw.rect(surf, outline, rib_r, 3, border_radius=10)
        for i in range(4):
            yy = cy + 16 + i * 10
            pygame.draw.line(surf, shade(outline, 0.8), (cx - 18, yy), (cx + 18, yy), 2)
        # spine (solid line, no AA)
        pygame.draw.line(surf, bone_dark, (cx, cy + 8), (cx, cy + 56), 2)
        # sword (solid metal block + edge, no AA)
        pygame.draw.rect(surf, (220, 222, 235), (cx + 30, cy - 50, 8, 70))
        pygame.draw.rect(surf, (160, 165, 180), (cx + 30, cy - 50, 4, 70))
        pygame.draw.rect(surf, (245, 248, 255), (cx + 30, cy - 50, 2, 70))
        pygame.draw.rect(surf, outline, (cx + 30, cy - 50, 8, 70), 2)
    elif kind == "wolf":
        # body — 2-tone dithered fill clipped to an ellipse (no AA)
        body_r = pygame.Rect(cx - 50, cy - 10, 100, 60)
        _grad_ellipse(surf, body_r, main_light, main_dark, center=(34, 18), falloff=1.2)
        pygame.draw.ellipse(surf, outline, body_r, 3)
        # head snout — 2-tone dithered fill clipped to the snout polygon (no AA)
        snout = [(cx - 40, cy - 6), (cx - 70, cy - 30), (cx - 30, cy - 30)]
        sg = px_dither_surf(50, 30, main_light, main_dark)
        m = pygame.Surface((50, 30), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - (cx - 70), p[1] - (cy - 30)) for p in snout])
        sg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(sg, (cx - 70, cy - 30))
        pygame.draw.polygon(surf, outline, snout, 3)
        # ears (solid palette fills, no AA)
        for ex in ((cx - 56, cy - 26), (cx - 44, cy - 28)):
            pygame.draw.polygon(surf, main, [(ex[0], ex[1]), (ex[0] - 8, ex[1] - 18), (ex[0] + 6, ex[1] - 6)])
            pygame.draw.polygon(surf, outline, [(ex[0], ex[1]), (ex[0] - 8, ex[1] - 18), (ex[0] + 6, ex[1] - 6)], 2)
        for sx in (-12, 4):
            _glowing_eye(surf, (cx + sx, cy - 4), (255, 230, 60), (255, 200, 40), r_core=4, r_glow=9)
        pygame.draw.polygon(surf, (40, 30, 30), [(cx - 18, cy + 10), (cx - 10, cy + 18), (cx - 2, cy + 10)])
        pygame.draw.polygon(surf, outline, [(cx - 18, cy + 10), (cx - 10, cy + 18), (cx - 2, cy + 10)], 2)
    elif kind == "orc":
        # body — 2-tone dithered fill (no AA)
        body_r = pygame.Rect(cx - 36, cy - 10, 72, 80)
        _grad_round_rect(surf, body_r, main_light, main_dark, border_radius=18)
        pygame.draw.rect(surf, outline, body_r, 3, border_radius=18)
        # head — 2-tone dithered fill clipped to a circle (no AA)
        head_g = px_dither_surf(80, 80, main_light, main_dark)
        clip_to_circle(head_g, (40, 40), 40)
        surf.blit(head_g, (cx - 40, cy - 70))
        pygame.draw.circle(surf, outline, (cx, cy - 30), 40, 3)
        # tusks (solid palette fills, no AA)
        for sx in (-1, 1):
            tusk = [(cx + sx * 12, cy - 18), (cx + sx * 16, cy - 2), (cx + sx * 8, cy - 8)]
            pygame.draw.polygon(surf, (245, 245, 235), tusk)
            pygame.draw.polygon(surf, (200, 200, 190), [(cx + sx * 12, cy - 18), (cx + sx * 14, cy - 6), (cx + sx * 10, cy - 10)])
            pygame.draw.polygon(surf, outline, tusk, 2)
        for sx in (-14, 14):
            _glowing_eye(surf, (cx + sx, cy - 34), (255, 60, 60), (255, 30, 30), r_core=5, r_glow=11)
        # axe (solid wood shaft + dithered metal head, no AA)
        pygame.draw.rect(surf, (140, 95, 55), (cx + 40, cy - 40, 8, 90))
        pygame.draw.rect(surf, (90, 60, 35), (cx + 40, cy - 40, 4, 90))
        pygame.draw.rect(surf, outline, (cx + 40, cy - 40, 8, 90), 2)
        head_pts = [(cx + 30, cy - 50), (cx + 70, cy - 50), (cx + 64, cy - 10), (cx + 36, cy - 10)]
        hg = px_dither_surf(44, 44, accent_light, shade(accent, 0.6))
        m = pygame.Surface((44, 44), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - (cx + 26), p[1] - (cy - 54)) for p in head_pts])
        hg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(hg, (cx + 26, cy - 54))
        pygame.draw.polygon(surf, outline, head_pts, 3)
        pygame.draw.line(surf, (255, 255, 255), (cx + 32, cy - 48), (cx + 38, cy - 14), 2)
    elif kind == "golem":
        # body (rocky, 2-tone dithered fill, no AA)
        body_r = pygame.Rect(cx - 44, cy - 40, 88, 110)
        _grad_round_rect(surf, body_r, main_light, main_dark, border_radius=12)
        pygame.draw.rect(surf, outline, body_r, 4, border_radius=12)
        # head (rocky block, 2-tone dithered fill, no AA)
        head_r = pygame.Rect(cx - 34, cy - 70, 68, 40)
        _grad_round_rect(surf, head_r, main_light, main_dark, border_radius=10)
        pygame.draw.rect(surf, outline, head_r, 4, border_radius=10)
        for sx in (-16, 16):
            # glowing crystal eyes (chunky block halo, no AA)
            _glowing_eye(surf, (cx + sx, cy - 52), (255, 230, 90), (255, 200, 60), r_core=5, r_glow=12)
        # rocky cracks (solid lines, no AA)
        pygame.draw.line(surf, dark, (cx - 20, cy - 10), (cx - 4, cy + 20), 3)
        pygame.draw.line(surf, dark, (cx - 4, cy + 20), (cx + 16, cy + 6), 3)
        pygame.draw.line(surf, dark, (cx + 18, cy - 20), (cx + 28, cy + 10), 2)
        # mossy accent at the base (solid block, no AA)
        pygame.draw.rect(surf, shade(accent, 0.9), (cx - 40, cy + 60, 80, 10), border_radius=4)
    elif kind == "wraith":
        # ghostly robe — 2-tone dithered fill clipped to the robe polygon (no AA)
        pts = [(cx - 40, cy - 30), (cx + 40, cy - 30), (cx + 50, cy + 70),
               (cx + 30, cy + 50), (cx + 10, cy + 80), (cx - 10, cy + 50), (cx - 50, cy + 70)]
        rg = px_dither_surf(110, 120, main_light, shade(main, 0.5))
        m = pygame.Surface((110, 120), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - (cx - 55), p[1] - (cy - 30)) for p in pts])
        rg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(rg, (cx - 55, cy - 30))
        pygame.draw.polygon(surf, outline, pts, 3)
        # tattered hem glow at the bottom (chunky blocks, no AA)
        for sx in (-30, -10, 10, 30):
            pygame.draw.rect(surf, (120, 255, 200), (cx + sx - 10, cy + 60, 20, 20))
        # hood/head — 2-tone dithered fill clipped to a circle (no AA)
        head_g = px_dither_surf(70, 70, main_light, shade(main, 0.5))
        clip_to_circle(head_g, (35, 35), 34)
        surf.blit(head_g, (cx - 35, cy - 64))
        pygame.draw.circle(surf, outline, (cx, cy - 30), 34, 3)
        for sx in (-12, 12):
            _glowing_eye(surf, (cx + sx, cy - 30), (140, 255, 210), (80, 255, 200), r_core=5, r_glow=11)
    elif kind == "dragon":
        # body — 2-tone dithered fill clipped to an ellipse (no AA)
        body_r = pygame.Rect(cx - 70, cy - 30, 140, 110)
        _grad_ellipse(surf, body_r, main_light, main_dark, center=(50, 30), falloff=1.25)
        pygame.draw.ellipse(surf, outline, body_r, 4)
        # belly (lighter, scaled) — 2-tone dithered fill (no AA)
        belly_r = pygame.Rect(cx - 50, cy, 100, 70)
        _grad_ellipse(surf, belly_r, accent_light, accent, center=(36, 24), falloff=1.2)
        # scale texture lines on belly (solid lines, no AA)
        for i in range(6):
            yy = cy + 6 + i * 13
            pygame.draw.line(surf, shade(accent, 0.65), (cx - 44, yy), (cx + 44, yy), 1)
        # body scale texture (subtle diamond pattern on the back, solid blocks)
        for si in range(8):
            sx2 = cx - 40 + si * 16
            sy3 = cy - 20 + (si % 3) * 8
            pygame.draw.polygon(surf, shade(main, 0.55),
                                [(sx2, sy3), (sx2 + 8, sy3 - 4), (sx2 + 16, sy3), (sx2 + 8, sy3 + 4)])
            pygame.draw.polygon(surf, shade(main, 0.7),
                                [(sx2, sy3), (sx2 + 8, sy3 - 4), (sx2 + 16, sy3), (sx2 + 8, sy3 + 4)], 1)
        # fire breath glow near the mouth (chunky block, no AA)
        pygame.draw.circle(surf, (255, 200, 80), (cx + 90, cy - 50), 18)
        pygame.draw.circle(surf, (255, 240, 140), (cx + 90, cy - 50), 10)
        # head — 2-tone dithered fill clipped to a circle (no AA)
        head_g = px_dither_surf(80, 80, main_light, main_dark)
        clip_to_circle(head_g, (40, 40), 40)
        surf.blit(head_g, (cx + 20, cy - 80))
        pygame.draw.circle(surf, outline, (cx + 60, cy - 40), 40, 4)
        # horns (solid palette fills, no AA)
        for sx in (-7, 7):
            horn = [(cx + 57 + sx, cy - 70), (cx + 47 + sx, cy - 100), (cx + 64 + sx, cy - 70)]
            pygame.draw.polygon(surf, dark, horn)
            pygame.draw.polygon(surf, shade(dark, 1.2), [(cx + 57 + sx, cy - 70), (cx + 50 + sx, cy - 92), (cx + 56 + sx, cy - 70)])
            pygame.draw.polygon(surf, outline, horn, 3)
        # glowing eye
        _glowing_eye(surf, (cx + 70, cy - 44), (255, 230, 60), (255, 200, 40), r_core=7, r_glow=14)
        # wings — 2-tone dithered fill clipped to the wing polygon (no AA)
        for i in range(3):
            bx = cx - 30 - i * 20
            wpts = [(cx - 20, cy - 20), (bx, cy - 80), (bx + 20, cy - 30)]
            wg = px_dither_surf(60, 70, dark, shade(dark, 0.6))
            m = pygame.Surface((60, 70), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255),
                                [(p[0] - (bx - 10), p[1] - (cy - 80)) for p in wpts])
            wg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(wg, (bx - 10, cy - 80))
            pygame.draw.polygon(surf, outline, wpts, 3)
            pygame.draw.line(surf, shade(dark, 1.2), (cx - 20, cy - 20), (bx + 10, cy - 75), 2)
        # tail — 2-tone dithered fill clipped to the tail polygon (no AA)
        tail = [(cx - 70, cy + 20), (cx - 110, cy), (cx - 100, cy + 40)]
        tg = px_dither_surf(50, 50, main, shade(main, 0.6))
        m = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - (cx - 110), p[1] - cy) for p in tail])
        tg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(tg, (cx - 110, cy))
        pygame.draw.polygon(surf, outline, tail, 3)
        # tail spade (solid block, no AA)
        pygame.draw.polygon(surf, dark, [(cx - 110, cy + 4), (cx - 120, cy - 6), (cx - 118, cy + 18), (cx - 108, cy + 12)])
        pygame.draw.polygon(surf, outline, [(cx - 110, cy + 4), (cx - 120, cy - 6), (cx - 118, cy + 18), (cx - 108, cy + 12)], 2)
    elif kind == "demonking":
        # big menacing figure (dark, with rim light) — 2-tone dithered fill (no AA)
        body_r = pygame.Rect(cx - 50, cy - 10, 100, 90)
        _grad_round_rect(surf, body_r, shade(dark, 1.15), shade(dark, 0.5), border_radius=20)
        pygame.draw.rect(surf, outline, body_r, 4, border_radius=20)
        # rim light on the left edge (solid block, no AA)
        pygame.draw.rect(surf, dark_light, (cx - 50, cy - 10, 4, 90))
        # head — 2-tone dithered fill clipped to a circle (no AA)
        head_g = px_dither_surf(92, 92, main, shade(main, 0.5))
        clip_to_circle(head_g, (46, 46), 46)
        surf.blit(head_g, (cx - 46, cy - 86))
        pygame.draw.circle(surf, outline, (cx, cy - 40), 46, 4)
        # crown of horns (solid palette fills, no AA)
        for sx in (-30, -10, 10, 30):
            horn = [(cx + sx, cy - 70), (cx + sx - 8, cy - 100), (cx + sx + 8, cy - 70)]
            pygame.draw.polygon(surf, dark, horn)
            pygame.draw.polygon(surf, shade(dark, 1.3), [(cx + sx, cy - 70), (cx + sx - 6, cy - 92), (cx + sx - 2, cy - 70)])
            pygame.draw.polygon(surf, outline, horn, 3)
        # glowing eyes
        for sx in (-16, 16):
            _glowing_eye(surf, (cx + sx, cy - 42), (255, 70, 70), (255, 30, 30), r_core=8, r_glow=15)
            pygame.draw.circle(surf, (255, 210, 210), (cx + sx - 2, cy - 44), 3)
        # cape — 2-tone dithered fill clipped to the cape polygon (no AA)
        cape_pts = [(cx - 50, cy - 10), (cx - 80, cy + 80), (cx, cy + 50), (cx + 80, cy + 80), (cx + 50, cy - 10)]
        cg = px_dither_surf(170, 100, accent, shade(accent, 0.45))
        m = pygame.Surface((170, 100), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - (cx - 80), p[1] - (cy - 10)) for p in cape_pts])
        cg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(cg, (cx - 80, cy - 10))
        # cape fold lines (solid vertical blocks, no AA)
        for cfx in (-20, 0, 20):
            pygame.draw.rect(surf, shade(accent, 0.6), (cx + cfx, cy + 4, 3, 90))
        # dark void aura behind the demonking (chunky block, no AA)
        pygame.draw.circle(surf, shade(dark, 1.05), (cx, cy + 40), 90)
        pygame.draw.polygon(surf, outline, cape_pts, 3)
    elif kind == "imp":
        # small horned fiend — 2-tone dithered fill (no AA)
        body_r = pygame.Rect(cx - 22, cy - 6, 44, 60)
        _grad_round_rect(surf, body_r, main_light, main_dark, border_radius=14)
        pygame.draw.rect(surf, outline, body_r, 3, border_radius=14)
        # head — 2-tone dithered fill clipped to a circle (no AA)
        head_g = px_dither_surf(56, 56, main_light, main_dark)
        clip_to_circle(head_g, (28, 28), 28)
        surf.blit(head_g, (cx - 28, cy - 52))
        pygame.draw.circle(surf, outline, (cx, cy - 24), 28, 3)
        # horns (solid palette fills, no AA)
        for sx in (-12, 12):
            horn = [(cx + sx, cy - 44), (cx + sx - 6, cy - 64), (cx + sx + 6, cy - 44)]
            pygame.draw.polygon(surf, dark, horn)
            pygame.draw.polygon(surf, shade(dark, 1.3), [(cx + sx, cy - 44), (cx + sx - 4, cy - 60), (cx + sx - 2, cy - 44)])
            pygame.draw.polygon(surf, outline, horn, 2)
        for sx in (-9, 9):
            _glowing_eye(surf, (cx + sx, cy - 24), (255, 230, 70), (255, 200, 50), r_core=4, r_glow=9)
    elif kind == "harpy":
        # winged bird-woman — 2-tone dithered fill (no AA)
        body_r = pygame.Rect(cx - 30, cy - 10, 60, 70)
        _grad_ellipse(surf, body_r, main_light, main_dark, center=(22, 18), falloff=1.2)
        pygame.draw.ellipse(surf, outline, body_r, 3)
        # head — 2-tone dithered fill clipped to a circle (no AA)
        head_g = px_dither_surf(52, 52, main_light, main_dark)
        clip_to_circle(head_g, (26, 26), 26)
        surf.blit(head_g, (cx - 26, cy - 56))
        pygame.draw.circle(surf, outline, (cx, cy - 30), 26, 3)
        # feathered wings — 2-tone dithered fill clipped to the wing polygon (no AA)
        for sx in (-1, 1):
            pts = [(cx, cy), (cx + sx * 70, cy - 50), (cx + sx * 90, cy + 10), (cx + sx * 40, cy + 10)]
            wg = px_dither_surf(100, 70, accent, shade(accent, 0.6))
            m = pygame.Surface((100, 70), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255),
                                [(p[0] - (cx - 10 if sx > 0 else cx - 90), p[1] - (cy - 50)) for p in pts])
            wg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(wg, (cx - 10 if sx > 0 else cx - 90, cy - 50))
            pygame.draw.polygon(surf, outline, pts, 3)
            # feather ridges (solid lines, no AA)
            for fy in (-30, -10, 10):
                pygame.draw.line(surf, shade(accent, 0.7),
                                 (cx + sx * 8, cy + fy), (cx + sx * 60, cy + fy - 8), 1)
        for sx in (-8, 8):
            _glowing_eye(surf, (cx + sx, cy - 30), (255, 230, 50), (255, 200, 40), r_core=3, r_glow=8)
        # beak (solid block, no AA)
        pygame.draw.polygon(surf, (240, 200, 80), [(cx - 4, cy - 22), (cx + 4, cy - 22), (cx, cy - 14)])
        pygame.draw.polygon(surf, outline, [(cx - 4, cy - 22), (cx + 4, cy - 22), (cx, cy - 14)], 1)
    elif kind == "ghoul":
        # hunched undead — 2-tone dithered fill (no AA)
        body_r = pygame.Rect(cx - 26, cy - 4, 52, 64)
        _grad_round_rect(surf, body_r, main_light, main_dark, border_radius=12)
        pygame.draw.rect(surf, outline, body_r, 3, border_radius=12)
        # head — 2-tone dithered fill clipped to a circle (no AA)
        head_g = px_dither_surf(56, 56, main_light, main_dark)
        clip_to_circle(head_g, (28, 28), 28)
        surf.blit(head_g, (cx - 28, cy - 54))
        pygame.draw.circle(surf, outline, (cx, cy - 26), 28, 3)
        for sx in (-10, 10):
            _glowing_eye(surf, (cx + sx, cy - 26), (190, 255, 190), (120, 255, 160), r_core=5, r_glow=11)
        # mouth (toothy, solid blocks, no AA)
        pygame.draw.rect(surf, (30, 26, 40), (cx - 9, cy - 14, 18, 6))
        for tx in (-6, -2, 2, 6):
            pygame.draw.rect(surf, (235, 235, 225), (cx + tx, cy - 14, 3, 6))
        # claws (solid blocks + tips, no AA)
        for sx in (-30, 22):
            pygame.draw.rect(surf, accent_light, (cx + sx, cy + 20, 8, 24))
            pygame.draw.rect(surf, accent, (cx + sx, cy + 20, 4, 24))
            pygame.draw.rect(surf, outline, (cx + sx, cy + 20, 8, 24), 2)
            # claw tips
            pygame.draw.polygon(surf, shade(accent, 0.7), [(cx + sx, cy + 44), (cx + sx + 8, cy + 44), (cx + sx + 4, cy + 50)])
    elif kind == "paladin":
        # armored fallen knight (metallic) — 2-tone dithered fill (no AA)
        body_r = pygame.Rect(cx - 30, cy - 6, 60, 76)
        _grad_round_rect(surf, body_r, shade(main, 1.2), shade(main, 0.6), border_radius=16)
        pygame.draw.rect(surf, outline, body_r, 3, border_radius=16)
        # armor plate highlights (solid blocks, no AA)
        pygame.draw.rect(surf, (255, 255, 255), (cx - 26, cy - 2, 8, 60), border_radius=4)
        pygame.draw.rect(surf, shade(main, 0.7), (cx + 18, cy - 2, 8, 60), border_radius=4)
        # helmet — 2-tone dithered fill clipped to a circle (no AA)
        head_g = px_dither_surf(60, 60, shade(main, 1.25), shade(main, 0.55))
        clip_to_circle(head_g, (30, 30), 30)
        surf.blit(head_g, (cx - 30, cy - 58))
        pygame.draw.circle(surf, outline, (cx, cy - 28), 30, 3)
        # visor slit (solid block, no AA)
        pygame.draw.rect(surf, (20, 20, 30), (cx - 17, cy - 31, 34, 9))
        pygame.draw.rect(surf, (255, 80, 80), (cx - 17, cy - 31, 34, 4))
        # emblem (solid gem, no AA)
        pygame.draw.circle(surf, accent_light, (cx, cy + 16), 10)
        pygame.draw.circle(surf, shade(accent, 0.4), (cx, cy + 16), 6)
        pygame.draw.circle(surf, outline, (cx, cy + 16), 10, 2)
        # sword (solid metal block + edge, no AA)
        pygame.draw.rect(surf, (220, 222, 235), (cx + 30, cy - 50, 8, 80))
        pygame.draw.rect(surf, (160, 165, 180), (cx + 30, cy - 50, 4, 80))
        pygame.draw.rect(surf, (245, 248, 255), (cx + 30, cy - 50, 2, 80))
        pygame.draw.rect(surf, outline, (cx + 30, cy - 50, 8, 80), 2)
        # crossguard (solid block, no AA)
        pygame.draw.rect(surf, accent, (cx + 24, cy + 28, 20, 6))
        pygame.draw.rect(surf, outline, (cx + 24, cy + 28, 20, 6), 1)
    elif kind == "hydra":
        # multi-headed serpent — 2-tone dithered fill (no AA)
        body_r = pygame.Rect(cx - 60, cy, 120, 70)
        _grad_ellipse(surf, body_r, main_light, main_dark, center=(42, 22), falloff=1.2)
        pygame.draw.ellipse(surf, outline, body_r, 4)
        # scale texture (solid lines, no AA)
        for i in range(4):
            yy = cy + 10 + i * 14
            pygame.draw.line(surf, shade(main, 0.7), (cx - 54, yy), (cx + 54, yy), 1)
        for i, sx in enumerate((-36, 0, 36)):
            hy = cy - 30 - (10 if i == 1 else 0)
            # head — 2-tone dithered fill clipped to a circle (no AA)
            hg = px_dither_surf(44, 44, main_light, main_dark)
            clip_to_circle(hg, (22, 22), 22)
            surf.blit(hg, (cx + sx - 22, hy - 22))
            pygame.draw.circle(surf, outline, (cx + sx, hy), 22, 3)
            # glowing eye
            _glowing_eye(surf, (cx + sx + 6, hy - 4), (255, 90, 90), (255, 50, 50), r_core=4, r_glow=9)
            # forked tongue on the middle head (solid lines, no AA)
            if i == 1:
                pygame.draw.line(surf, (180, 40, 50), (cx + sx, hy + 18), (cx + sx - 6, hy + 26), 2)
                pygame.draw.line(surf, (180, 40, 50), (cx + sx, hy + 18), (cx + sx + 6, hy + 26), 2)
    elif kind == "frosttitan":
        # towering ice giant — 2-tone dithered fill (no AA)
        body_r = pygame.Rect(cx - 48, cy - 40, 96, 120)
        _grad_round_rect(surf, body_r, main_light, main_dark, border_radius=14)
        pygame.draw.rect(surf, outline, body_r, 4, border_radius=14)
        # ice crystal facets (2-tone dithered fill, no AA)
        for fx, fy, fw, fh in ((-32, -28, 20, 42), (10, -22, 18, 52), (26, 12, 16, 42), (-24, 10, 14, 36)):
            fc = px_dither_surf(fw, fh, (245, 252, 255), shade(main, 1.15))
            clip_to_rect(fc, pygame.Rect(0, 0, fw, fh), border_radius=3)
            surf.blit(fc, (cx + fx, cy + fy))
            pygame.draw.rect(surf, shade(main, 0.65), (cx + fx, cy + fy, fw, fh), 1, border_radius=3)
            # specular glint on each facet (solid block, no AA)
            pygame.draw.rect(surf, (255, 255, 255), (cx + fx + 2, cy + fy + 2, fw - 4, 2))
        # frost mist aura around the body (chunky block, no AA)
        pygame.draw.circle(surf, (200, 240, 255), (cx, cy + 50), 90)
        # head — 2-tone dithered fill clipped to a circle (no AA)
        head_g = px_dither_surf(76, 76, main_light, main_dark)
        clip_to_circle(head_g, (38, 38), 38)
        surf.blit(head_g, (cx - 38, cy - 102))
        pygame.draw.circle(surf, outline, (cx, cy - 64), 38, 4)
        for sx in (-14, 14):
            _glowing_eye(surf, (cx + sx, cy - 64), (210, 245, 255), (140, 210, 255), r_core=6, r_glow=12)
        # ice shards — 2-tone dithered fill clipped to the shard polygon (no AA)
        for sx in (-30, 0, 30):
            sh_pts = [(cx + sx - 6, cy + 80), (cx + sx, cy + 34), (cx + sx + 6, cy + 80)]
            sg = px_dither_surf(16, 48, (255, 255, 255), shade(accent, 0.8))
            m = pygame.Surface((16, 48), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255),
                                [(p[0] - (cx + sx - 8), p[1] - (cy + 34)) for p in sh_pts])
            sg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(sg, (cx + sx - 8, cy + 34))
            # bright edge on the left side of each shard (solid line, no AA)
            pygame.draw.line(surf, (255, 255, 255), (cx + sx - 5, cy + 78), (cx + sx - 1, cy + 36), 2)
            pygame.draw.polygon(surf, outline, sh_pts, 2)
        # frost breath glow (chunky block, no AA)
        pygame.draw.circle(surf, (200, 245, 255), (cx + 50, cy - 40), 26)
        # few floating ice motes near the giant (solid blocks, no AA)
        for im in range(4):
            mx = cx + random.uniform(-40, 40)
            my = cy + random.uniform(-60, 20)
            pygame.draw.rect(surf, (210, 240, 255), (px_snap(mx), px_snap(my), 5, 5))
            pygame.draw.rect(surf, (255, 255, 255), (px_snap(mx) + 1, px_snap(my) + 1, 2, 2))
    elif kind == "embertyrant":
        # roaring flame warlord — 2-tone dithered fill (no AA)
        body_r = pygame.Rect(cx - 52, cy - 8, 104, 92)
        _grad_round_rect(surf, body_r, shade(dark, 1.2), shade(dark, 0.5), border_radius=20)
        pygame.draw.rect(surf, outline, body_r, 4, border_radius=20)
        # ember cracks glowing on the body (solid lines, no AA)
        for ey in (8, 38, 62):
            pygame.draw.rect(surf, (255, 180, 60), (cx - 26, cy + ey - 5, 52, 6))
            pygame.draw.line(surf, (255, 220, 120), (cx - 22, cy + ey), (cx + 22, cy + ey), 3)
            pygame.draw.line(surf, (255, 255, 200), (cx - 22, cy + ey), (cx, cy + ey), 1)
            # branch cracks going up and down
            for bx2 in (-8, 8):
                pygame.draw.line(surf, (255, 140, 60), (cx + bx2, cy + ey), (cx + bx2 + 6, cy + ey - 8), 2)
        # molten core glow at chest center (solid block, no AA)
        pygame.draw.circle(surf, (255, 200, 80), (cx, cy + 38), 18)
        pygame.draw.circle(surf, (255, 240, 120), (cx, cy + 38), 8)
        pygame.draw.circle(surf, (255, 255, 200), (cx - 2, cy + 36), 3)
        # head — 2-tone dithered fill clipped to a circle (no AA)
        head_g = px_dither_surf(96, 96, main, shade(main, 0.5))
        clip_to_circle(head_g, (48, 48), 48)
        surf.blit(head_g, (cx - 48, cy - 88))
        pygame.draw.circle(surf, outline, (cx, cy - 40), 48, 4)
        # blazing crown — 2-tone dithered fill clipped to each flame polygon (no AA)
        for sx in (-30, -10, 10, 30):
            flame = [(cx + sx, cy - 72), (cx + sx - 8, cy - 110), (cx + sx + 8, cy - 72)]
            fg = px_dither_surf(20, 40, (255, 240, 140), shade(accent, 0.9))
            m = pygame.Surface((20, 40), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255),
                                [(p[0] - (cx + sx - 10), p[1] - (cy - 72)) for p in flame])
            fg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(fg, (cx + sx - 10, cy - 72))
            # inner bright streak in each flame (solid line, no AA)
            pygame.draw.line(surf, (255, 255, 200), (cx + sx, cy - 70), (cx + sx, cy - 106), 2)
            pygame.draw.polygon(surf, outline, flame, 3)
        for sx in (-18, 18):
            _glowing_eye(surf, (cx + sx, cy - 42), (255, 240, 120), (255, 200, 60), r_core=9, r_glow=16)
        # flame aura (orbiting embers, solid blocks, no AA)
        for i in range(8):
            ang = i * math.pi / 4
            ex = int(cx + math.cos(ang) * 72)
            ey2 = int(cy + math.sin(ang) * 52)
            pygame.draw.rect(surf, (255, 180, 80), (ex - 6, ey2 - 6, 12, 12))
            pygame.draw.rect(surf, (255, 240, 160), (ex - 4, ey2 - 4, 8, 8))
            pygame.draw.rect(surf, (255, 255, 255), (ex - 2, ey2 - 2, 4, 4))
            # smoke trail behind each ember (solid block, no AA)
            pygame.draw.rect(surf, (40, 20, 20), (ex - 14, ey2, 10, 6))

# ---------------------------------------------------------------------------
# Skill icons
# ---------------------------------------------------------------------------
def _skill_variant(skill_name):
    """Deterministic variant index (0-3) from the skill name.

    Uses sum(ord(c)) — NOT hash() (which is PYTHONHASHSEED-salted and so would
    produce a different variant across regenerations). Stable across runs so
    the per-skill art is reproducible."""
    return sum(ord(c) for c in skill_name) % 4


def draw_skill_icon(surf, skill_name, element, kind, hero_accent=None,
                   hero_tint=None):
    """Draw a skill icon with per-skill distinct art.

    The `kind` (slash/bolt/arrow/heal/shield/orb/aoe/curse/buff/summon/beam/
    trap) is the visual family; within each family, a deterministic variant
    (derived from the skill name via sum(ord(c))%4) picks one of 3-4 distinct
    drawings so fire_slash and light_slash no longer look the same shape.

    If `hero_accent` is given, the glyph's light color is tinted toward it
    (lerp 0.3) so each hero's copy of a shared skill is accent-colored. A
    per-hero hue shift (derived from `hero_tint` via sum(ord(c))) is also
    applied to the light color so two heroes with the same palette accent
    still get a distinct tint (the accent palette has duplicates — kael/
    ember, lyra/sera — so the accent alone isn't unique per hero)."""
    cx, cy = 64, 64
    outline = (30, 26, 40)
    main, light, dark = ELEMENT_COLORS[element]
    # per-hero accent tinting: shift the light color toward the hero's accent.
    if hero_accent is not None:
        light = lerp_color(light, hero_accent, 0.3)
    # per-hero hue shift: rotate the light color's hue by a per-hero offset
    # (derived from the hero_id) so two heroes with the same accent still get a
    # distinct tint. The offset is a small hue rotation (±20°) via an additive
    # per-hero color blend, deterministic from sum(ord(c)) (NOT hash()).
    if hero_tint is not None:
        hoff = (sum(ord(c) for c in hero_tint) % 40) - 20  # -20..+19
        light = _hue_shift(light, hoff)
    v = _skill_variant(skill_name)

    # base disc — 2-tone dithered fill clipped to a circle (pixel-art: no AA
    # radial gradient). Light upper-left, dark edge.
    disc = px_dither_surf(112, 112, shade(main, 1.15), shade(dark, 0.7))
    clip_to_circle(disc, (56, 56), 56)
    surf.blit(disc, (8, 8))
    pygame.draw.circle(surf, outline, (cx, cy), 56, 3)
    # inner ring highlight (solid line, no AA)
    pygame.draw.circle(surf, light, (cx, cy), 50, 2)
    # soft inner glow (a chunky block disc, no AA soft-glow)
    inner = pygame.Surface((96, 96), pygame.SRCALPHA)
    pygame.draw.circle(inner, (*light, 90), (48, 48), 40)
    pygame.draw.circle(inner, (*light, 50), (48, 48), 48)
    surf.blit(inner, (16, 16))

    if kind == "slash":
        if v == 0:
            # v0: single diagonal slash (the original)
            pygame.draw.polygon(surf, light, [(cx - 24, cy + 20), (cx + 24, cy - 20), (cx + 30, cy - 10), (cx - 18, cy + 30)])
            pygame.draw.polygon(surf, (255, 255, 255), [(cx - 20, cy + 16), (cx + 20, cy - 16), (cx + 24, cy - 8), (cx - 14, cy + 26)])
            pygame.draw.polygon(surf, outline, [(cx - 24, cy + 20), (cx + 24, cy - 20), (cx + 30, cy - 10), (cx - 18, cy + 30)], 3)
        elif v == 1:
            # v1: cross (X) slash — two crossing blades
            pygame.draw.line(surf, light, (cx - 24, cy + 24), (cx + 24, cy - 24), 8)
            pygame.draw.line(surf, light, (cx + 24, cy + 24), (cx - 24, cy - 24), 8)
            pygame.draw.line(surf, (255, 255, 255), (cx - 22, cy + 22), (cx + 22, cy - 22), 3)
            pygame.draw.line(surf, (255, 255, 255), (cx + 22, cy + 22), (cx - 22, cy - 22), 3)
            pygame.draw.line(surf, outline, (cx - 24, cy + 24), (cx + 24, cy - 24), 2)
            pygame.draw.line(surf, outline, (cx + 24, cy + 24), (cx - 24, cy - 24), 2)
            pygame.draw.circle(surf, outline, (cx, cy), 6, 2)
        elif v == 2:
            # v2: triple parallel slashes
            for dy in (-16, 0, 16):
                pygame.draw.polygon(surf, light,
                    [(cx - 24, cy + dy + 8), (cx + 24, cy + dy - 8),
                     (cx + 28, cy + dy - 4), (cx - 20, cy + dy + 12)])
                pygame.draw.line(surf, outline,
                    (cx - 24, cy + dy + 8), (cx + 28, cy + dy - 8), 2)
        else:
            # v3: crescent slash — an arc
            pygame.draw.arc(surf, light, pygame.Rect(cx - 28, cy - 28, 56, 56), 0.4, 2.7, 8)
            pygame.draw.arc(surf, (255, 255, 255), pygame.Rect(cx - 26, cy - 26, 52, 52), 0.4, 2.7, 3)
            pygame.draw.arc(surf, outline, pygame.Rect(cx - 28, cy - 28, 56, 56), 0.4, 2.7, 2)

    elif kind == "bolt":
        if v == 0:
            # v0: lightning bolt (the original)
            bolt_pts = [(cx - 6, cy - 28), (cx + 14, cy - 6), (cx + 2, cy - 4), (cx + 12, cy + 28), (cx - 12, cy + 4), (cx + 2, cy + 2)]
            pygame.draw.polygon(surf, light, bolt_pts)
            pygame.draw.polygon(surf, (255, 255, 230),
                                [(cx - 4, cy - 24), (cx + 10, cy - 6), (cx, cy - 4), (cx + 8, cy + 24), (cx - 8, cy + 4), (cx + 2, cy + 2)])
            pygame.draw.polygon(surf, outline, bolt_pts, 2)
        elif v == 1:
            # v1: forked lightning — 2 prongs
            pygame.draw.polygon(surf, light,
                [(cx - 8, cy - 28), (cx + 8, cy - 8), (cx, cy - 6), (cx + 6, cy + 6),
                 (cx + 14, cy + 28), (cx + 2, cy + 4), (cx + 8, cy + 2), (cx - 4, cy - 6)])
            pygame.draw.line(surf, light, (cx, cy - 4), (cx - 14, cy + 28), 5)
            pygame.draw.line(surf, (255, 255, 230), (cx - 2, cy - 4), (cx - 12, cy + 26), 2)
            pygame.draw.line(surf, outline, (cx - 8, cy - 28), (cx + 8, cy - 8), 2)
            pygame.draw.line(surf, outline, (cx, cy - 4), (cx - 14, cy + 28), 2)
            pygame.draw.line(surf, outline, (cx, cy - 4), (cx + 6, cy + 28), 2)
        elif v == 2:
            # v2: ball lightning — circle + radial sparks
            pygame.draw.circle(surf, light, (cx, cy), 18)
            pygame.draw.circle(surf, (255, 255, 230), (cx - 4, cy - 4), 12)
            pygame.draw.circle(surf, outline, (cx, cy), 18, 3)
            for ang in range(0, 360, 45):
                rad = math.radians(ang)
                x1 = cx + int(math.cos(rad) * 20)
                y1 = cy + int(math.sin(rad) * 20)
                x2 = cx + int(math.cos(rad) * 30)
                y2 = cy + int(math.sin(rad) * 30)
                pygame.draw.line(surf, light, (x1, y1), (x2, y2), 3)
        else:
            # v3: zigzag bolt
            pts = [(cx - 20, cy - 24), (cx + 8, cy - 8), (cx - 8, cy + 4),
                   (cx + 20, cy + 24)]
            pygame.draw.lines(surf, light, False, pts, 6)
            pygame.draw.lines(surf, (255, 255, 230), False, pts, 2)
            pygame.draw.lines(surf, outline, False, pts, 2)
            # end caps
            pygame.draw.circle(surf, light, pts[0], 4)
            pygame.draw.circle(surf, light, pts[-1], 4)

    elif kind == "arrow":
        if v == 0:
            # v0: single arrow (the original)
            pygame.draw.line(surf, light, (cx - 26, cy + 22), (cx + 22, cy - 22), 6)
            pygame.draw.line(surf, (255, 255, 255), (cx - 26, cy + 22), (cx + 22, cy - 22), 2)
            pygame.draw.polygon(surf, (255, 255, 255), [(cx + 22, cy - 22), (cx + 6, cy - 30), (cx + 30, cy - 6)])
            # fletching (back fins)
            pygame.draw.polygon(surf, shade(light, 0.7), [(cx - 26, cy + 22), (cx - 30, cy + 16), (cx - 22, cy + 18)])
            pygame.draw.line(surf, outline, (cx - 26, cy + 22), (cx + 22, cy - 22), 2)
        elif v == 1:
            # v1: triple arrow (3 arrows fan)
            for ang in (-20, 0, 20):
                rad = math.radians(ang - 45)
                ex = cx + int(math.cos(rad) * 26)
                ey = cy + int(math.sin(rad) * 26)
                sx = cx - int(math.cos(rad) * 26)
                sy = cy - int(math.sin(rad) * 26)
                pygame.draw.line(surf, light, (sx, sy), (ex, ey), 4)
                pygame.draw.line(surf, (255, 255, 255), (sx, sy), (ex, ey), 1)
                # arrowhead
                ax = ex - int(math.cos(rad) * 8)
                ay = ey - int(math.sin(rad) * 8)
                px = -int(math.sin(rad) * 5)
                py = int(math.cos(rad) * 5)
                pygame.draw.polygon(surf, (255, 255, 255), [(ex, ey), (ax + px, ay + py), (ax - px, ay - py)])
                pygame.draw.line(surf, outline, (sx, sy), (ex, ey), 1)
        elif v == 2:
            # v2: piercing arrow — arrow + trail line
            pygame.draw.line(surf, shade(light, 0.6), (cx - 30, cy + 26), (cx + 10, cy - 14), 3)
            pygame.draw.line(surf, light, (cx + 10, cy - 14), (cx + 28, cy - 26), 6)
            pygame.draw.polygon(surf, (255, 255, 255), [(cx + 28, cy - 26), (cx + 14, cy - 30), (cx + 30, cy - 14)])
            pygame.draw.line(surf, outline, (cx - 30, cy + 26), (cx + 28, cy - 26), 2)
        else:
            # v3: barbed arrow — arrow with barbs
            pygame.draw.line(surf, light, (cx - 26, cy + 22), (cx + 22, cy - 22), 6)
            pygame.draw.line(surf, (255, 255, 255), (cx - 26, cy + 22), (cx + 22, cy - 22), 2)
            pygame.draw.polygon(surf, (255, 255, 255), [(cx + 22, cy - 22), (cx + 6, cy - 30), (cx + 30, cy - 6)])
            # barbs (back-pointing spikes)
            pygame.draw.polygon(surf, shade(light, 0.7), [(cx - 10, cy + 6), (cx - 18, cy + 16), (cx - 4, cy + 14)])
            pygame.draw.polygon(surf, shade(light, 0.7), [(cx + 4, cy - 10), (cx + 14, cy - 2), (cx - 2, cy - 4)])
            pygame.draw.line(surf, outline, (cx - 26, cy + 22), (cx + 22, cy - 22), 2)

    elif kind == "heal":
        if v == 0:
            # v0: plus sign (the original)
            pygame.draw.rect(surf, (255, 255, 255), (cx - 8, cy - 24, 16, 48), border_radius=4)
            pygame.draw.rect(surf, (255, 255, 255), (cx - 24, cy - 8, 48, 16), border_radius=4)
            pygame.draw.rect(surf, outline, (cx - 8, cy - 24, 16, 48), 2, border_radius=4)
            pygame.draw.rect(surf, outline, (cx - 24, cy - 8, 48, 16), 2, border_radius=4)
        elif v == 1:
            # v1: cross (Christian) — longer vertical + shorter horizontal
            pygame.draw.rect(surf, (255, 255, 255), (cx - 6, cy - 28, 12, 56), border_radius=3)
            pygame.draw.rect(surf, (255, 255, 255), (cx - 18, cy - 4, 36, 12), border_radius=3)
            pygame.draw.rect(surf, outline, (cx - 6, cy - 28, 12, 56), 2, border_radius=3)
            pygame.draw.rect(surf, outline, (cx - 18, cy - 4, 36, 12), 2, border_radius=3)
        elif v == 2:
            # v2: heart
            pygame.draw.circle(surf, (255, 255, 255), (cx - 10, cy - 6), 12)
            pygame.draw.circle(surf, (255, 255, 255), (cx + 10, cy - 6), 12)
            pygame.draw.polygon(surf, (255, 255, 255), [(cx - 22, cy - 4), (cx, cy + 24), (cx + 22, cy - 4)])
            pygame.draw.polygon(surf, outline, [(cx - 22, cy - 4), (cx - 10, cy - 18), (cx + 10, cy - 18), (cx + 22, cy - 4), (cx, cy + 24)], 2)
        else:
            # v3: leaf
            pygame.draw.polygon(surf, light, [(cx - 4, cy - 24), (cx + 24, cy + 4), (cx + 4, cy + 24), (cx - 24, cy + 4)])
            pygame.draw.polygon(surf, (255, 255, 255), [(cx - 2, cy - 20), (cx + 20, cy + 2), (cx + 2, cy + 20), (cx - 20, cy + 2)])
            pygame.draw.line(surf, outline, (cx - 4, cy - 24), (cx + 4, cy + 24), 2)
            pygame.draw.polygon(surf, outline, [(cx - 4, cy - 24), (cx + 24, cy + 4), (cx + 4, cy + 24), (cx - 24, cy + 4)], 2)

    elif kind == "shield":
        if v == 0:
            # v0: round shield (the original)
            sh_pts = [(cx, cy - 26), (cx + 22, cy - 14), (cx + 22, cy + 10), (cx, cy + 28), (cx - 22, cy + 10), (cx - 22, cy - 14)]
            shg = px_dither_surf(48, 56, (255, 255, 255), shade(light, 0.7))
            m = pygame.Surface((48, 56), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - (cx - 24), p[1] - (cy - 26)) for p in sh_pts])
            shg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(shg, (cx - 24, cy - 26))
            pygame.draw.polygon(surf, outline, sh_pts, 3)
            pygame.draw.circle(surf, light, (cx, cy), 6)
            pygame.draw.circle(surf, (255, 255, 255), (cx - 2, cy - 2), 3)
        elif v == 1:
            # v1: kite shield — tall + pointed bottom
            sh_pts = [(cx, cy - 30), (cx + 18, cy - 16), (cx + 14, cy + 8), (cx, cy + 30), (cx - 14, cy + 8), (cx - 18, cy - 16)]
            shg = px_dither_surf(40, 64, (255, 255, 255), shade(light, 0.7))
            m = pygame.Surface((40, 64), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - (cx - 20), p[1] - (cy - 30)) for p in sh_pts])
            shg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(shg, (cx - 20, cy - 30))
            pygame.draw.polygon(surf, outline, sh_pts, 3)
            pygame.draw.line(surf, light, (cx, cy - 20), (cx, cy + 20), 3)
        elif v == 2:
            # v2: tower shield — rectangular
            sh_pts = [(cx - 20, cy - 28), (cx + 20, cy - 28), (cx + 20, cy + 20), (cx, cy + 28), (cx - 20, cy + 20)]
            shg = px_dither_surf(44, 60, (255, 255, 255), shade(light, 0.7))
            m = pygame.Surface((44, 60), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - (cx - 22), p[1] - (cy - 28)) for p in sh_pts])
            shg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(shg, (cx - 22, cy - 28))
            pygame.draw.polygon(surf, outline, sh_pts, 3)
            pygame.draw.line(surf, light, (cx, cy - 20), (cx, cy + 16), 3)
        else:
            # v3: buckler — small round
            shg = px_dither_surf(36, 36, (255, 255, 255), shade(light, 0.7))
            clip_to_circle(shg, (18, 18), 18)
            surf.blit(shg, (cx - 18, cy - 18))
            pygame.draw.circle(surf, outline, (cx, cy), 18, 3)
            pygame.draw.circle(surf, light, (cx, cy), 10, 2)
            pygame.draw.circle(surf, (255, 255, 255), (cx - 3, cy - 3), 4)

    elif kind == "orb":
        if v == 0:
            # v0: plain orb (the original)
            orb = px_dither_surf(44, 44, light, shade(dark, 0.6))
            clip_to_circle(orb, (22, 22), 22)
            surf.blit(orb, (cx - 22, cy - 22))
            pygame.draw.circle(surf, (255, 255, 255), (cx - 7, cy - 7), 7)
            pygame.draw.circle(surf, (255, 255, 255), (cx - 3, cy - 3), 3)
            pygame.draw.circle(surf, outline, (cx, cy), 22, 3)
        elif v == 1:
            # v1: crystal (faceted) — diamond shape
            pts = [(cx, cy - 26), (cx + 20, cy - 6), (cx + 14, cy + 22), (cx - 14, cy + 22), (cx - 20, cy - 6)]
            pygame.draw.polygon(surf, light, pts)
            pygame.draw.polygon(surf, (255, 255, 255), [(cx, cy - 26), (cx + 20, cy - 6), (cx, cy - 6)])
            pygame.draw.polygon(surf, shade(light, 0.6), [(cx, cy - 6), (cx + 20, cy - 6), (cx + 14, cy + 22)])
            pygame.draw.polygon(surf, outline, pts, 3)
        elif v == 2:
            # v2: pearl — orb with strong shine
            orb = px_dither_surf(44, 44, (255, 255, 255), shade(light, 0.5))
            clip_to_circle(orb, (22, 22), 22)
            surf.blit(orb, (cx - 22, cy - 22))
            pygame.draw.circle(surf, (255, 255, 255), (cx - 8, cy - 8), 10)
            pygame.draw.circle(surf, (255, 255, 255), (cx - 4, cy - 4), 5)
            pygame.draw.circle(surf, outline, (cx, cy), 22, 3)
        else:
            # v3: runic orb — orb with rune marks
            orb = px_dither_surf(44, 44, light, shade(dark, 0.6))
            clip_to_circle(orb, (22, 22), 22)
            surf.blit(orb, (cx - 22, cy - 22))
            pygame.draw.circle(surf, (255, 255, 255), (cx - 7, cy - 7), 5)
            # rune marks (3 small dots in a triangle)
            for ry in (-8, 8):
                for rx in (-8, 8):
                    pygame.draw.circle(surf, outline, (cx + rx, cy + ry), 3, 1)
            pygame.draw.circle(surf, outline, (cx, cy), 22, 3)

    elif kind == "aoe":
        if v == 0:
            # v0: concentric rings (the original)
            for r in (28, 20, 12):
                pygame.draw.circle(surf, light, (cx, cy), r, 4)
            pygame.draw.circle(surf, outline, (cx, cy), 28, 2)
        elif v == 1:
            # v1: spiral
            pts = []
            for i in range(0, 80, 3):
                rad = i * 0.1
                r = 4 + i * 0.3
                if r > 30:
                    break
                pts.append((cx + int(math.cos(rad) * r), cy + int(math.sin(rad) * r)))
            if len(pts) > 1:
                pygame.draw.lines(surf, light, False, pts, 3)
                pygame.draw.lines(surf, (255, 255, 255), False, pts, 1)
            pygame.draw.circle(surf, outline, (cx, cy), 30, 2)
        elif v == 2:
            # v2: star burst — a small star + radial lines
            for ang in range(0, 360, 30):
                rad = math.radians(ang)
                pygame.draw.line(surf, light,
                    (cx + int(math.cos(rad) * 8), cy + int(math.sin(rad) * 8)),
                    (cx + int(math.cos(rad) * 28), cy + int(math.sin(rad) * 28)), 3)
            draw_star(surf, cx, cy, 10, 5, light, (255, 255, 255))
        else:
            # v3: explosion — radial lines from center
            for ang in range(0, 360, 45):
                rad = math.radians(ang)
                x1 = cx + int(math.cos(rad) * 6)
                y1 = cy + int(math.sin(rad) * 6)
                x2 = cx + int(math.cos(rad) * 28)
                y2 = cy + int(math.sin(rad) * 28)
                pygame.draw.line(surf, light, (x1, y1), (x2, y2), 5)
                pygame.draw.line(surf, (255, 255, 255), (x1, y1), (x2, y2), 2)
            pygame.draw.circle(surf, light, (cx, cy), 8)
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 4)
            pygame.draw.circle(surf, outline, (cx, cy), 30, 2)

    elif kind == "curse":
        if v == 0:
            # v0: sigil — circle + void (the original)
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 24)
            pygame.draw.circle(surf, outline, (cx, cy), 24, 3)
            void = px_dither_surf(26, 26, shade(dark, 1.2), dark)
            clip_to_circle(void, (13, 13), 12)
            surf.blit(void, (cx - 13, cy - 13))
            pygame.draw.circle(surf, outline, (cx, cy), 12, 2)
        elif v == 1:
            # v1: skull
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy - 4), 20)
            pygame.draw.rect(surf, (255, 255, 255), (cx - 12, cy + 4, 24, 12), border_radius=4)
            pygame.draw.circle(surf, outline, (cx - 8, cy - 4), 6, 2)
            pygame.draw.circle(surf, outline, (cx + 8, cy - 4), 6, 2)
            pygame.draw.rect(surf, outline, (cx - 2, cy + 8, 4, 8))
            pygame.draw.circle(surf, outline, (cx, cy - 4), 20, 2)
        elif v == 2:
            # v2: hex — triangle + circle
            pygame.draw.polygon(surf, (255, 255, 255), [(cx, cy - 24), (cx + 22, cy + 12), (cx - 22, cy + 12)])
            pygame.draw.polygon(surf, outline, [(cx, cy - 24), (cx + 22, cy + 12), (cx - 22, cy + 12)], 3)
            pygame.draw.circle(surf, shade(dark, 1.2), (cx, cy), 10)
            pygame.draw.circle(surf, outline, (cx, cy), 10, 2)
        else:
            # v3: eye
            pygame.draw.ellipse(surf, (255, 255, 255), (cx - 24, cy - 12, 48, 24))
            pygame.draw.ellipse(surf, outline, (cx - 24, cy - 12, 48, 24), 3)
            pygame.draw.circle(surf, shade(dark, 1.2), (cx, cy), 9)
            pygame.draw.circle(surf, outline, (cx, cy), 9, 2)
            pygame.draw.circle(surf, (255, 255, 255), (cx - 3, cy - 3), 3)

    elif kind == "buff":
        if v == 0:
            # v0: upward triangle (the original)
            tri = [(cx, cy - 26), (cx + 22, cy + 18), (cx - 22, cy + 18)]
            tg = px_dither_surf(48, 46, (255, 255, 255), shade(light, 0.7))
            m = pygame.Surface((48, 46), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - (cx - 24), p[1] - (cy - 26)) for p in tri])
            tg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(tg, (cx - 24, cy - 26))
            pygame.draw.polygon(surf, outline, tri, 3)
            pygame.draw.line(surf, outline, (cx, cy - 14), (cx, cy + 8), 3)
            pygame.draw.circle(surf, outline, (cx, cy + 14), 3)
        elif v == 1:
            # v1: star
            draw_star(surf, cx, cy, 26, 11, light, (255, 255, 255))
            pygame.draw.rect(surf, (255, 255, 255), (cx - 4, cy - 16, 6, 6))
        elif v == 2:
            # v2: banner — flag shape
            pygame.draw.rect(surf, light, (cx - 3, cy - 28, 6, 56))
            pygame.draw.polygon(surf, (255, 255, 255), [(cx + 3, cy - 28), (cx + 24, cy - 18), (cx + 3, cy - 8)])
            pygame.draw.polygon(surf, outline, [(cx + 3, cy - 28), (cx + 24, cy - 18), (cx + 3, cy - 8)], 2)
            pygame.draw.line(surf, outline, (cx - 3, cy - 28), (cx - 3, cy + 28), 2)
            pygame.draw.line(surf, outline, (cx + 3, cy - 28), (cx + 3, cy + 28), 2)
        else:
            # v3: chevron — upward V
            pygame.draw.lines(surf, light, False, [(cx - 22, cy + 16), (cx, cy - 22), (cx + 22, cy + 16)], 6)
            pygame.draw.lines(surf, (255, 255, 255), False, [(cx - 22, cy + 16), (cx, cy - 22), (cx + 22, cy + 16)], 2)
            pygame.draw.lines(surf, outline, False, [(cx - 22, cy + 16), (cx, cy - 22), (cx + 22, cy + 16)], 2)

    elif kind == "summon":
        if v == 0:
            # v0: portal — concentric rings + center glow
            for r in (28, 20, 12):
                pygame.draw.circle(surf, light, (cx, cy), r, 3)
            pygame.draw.circle(surf, shade(dark, 1.3), (cx, cy), 8)
            pygame.draw.circle(surf, light, (cx, cy), 4)
            pygame.draw.circle(surf, outline, (cx, cy), 28, 2)
        elif v == 1:
            # v1: crystal cluster — multiple small crystals
            for ox, oy, sz in [(-12, -8, 10), (10, -12, 8), (4, 12, 12)]:
                pts = [(cx + ox, cy + oy - sz), (cx + ox + sz, cy + oy),
                       (cx + ox, cy + oy + sz), (cx + ox - sz, cy + oy)]
                pygame.draw.polygon(surf, light, pts)
                pygame.draw.polygon(surf, (255, 255, 255),
                    [(cx + ox, cy + oy - sz), (cx + ox + sz, cy + oy), (cx + ox, cy + oy)])
                pygame.draw.polygon(surf, outline, pts, 2)
        elif v == 2:
            # v2: rune circle — circle with rune marks around
            pygame.draw.circle(surf, light, (cx, cy), 22, 3)
            for ang in range(0, 360, 60):
                rad = math.radians(ang)
                rx = cx + int(math.cos(rad) * 22)
                ry = cy + int(math.sin(rad) * 22)
                pygame.draw.circle(surf, (255, 255, 255), (rx, ry), 4)
                pygame.draw.circle(surf, outline, (rx, ry), 4, 1)
            pygame.draw.circle(surf, shade(dark, 1.3), (cx, cy), 8)
            pygame.draw.circle(surf, outline, (cx, cy), 22, 2)
        else:
            # v3: spirit flame — wisp shape
            pts = [(cx - 8, cy + 24), (cx - 14, cy + 4), (cx - 6, cy - 14),
                   (cx, cy - 28), (cx + 6, cy - 14), (cx + 14, cy + 4), (cx + 8, cy + 24)]
            pygame.draw.polygon(surf, light, pts)
            pygame.draw.polygon(surf, (255, 255, 255),
                [(cx - 4, cy + 20), (cx - 8, cy + 2), (cx, cy - 10), (cx + 8, cy + 2), (cx + 4, cy + 20)])
            pygame.draw.polygon(surf, outline, pts, 2)

    elif kind == "beam":
        if v == 0:
            # v0: horizontal beam — thick line + burst caps
            pygame.draw.rect(surf, light, (cx - 28, cy - 6, 56, 12))
            pygame.draw.rect(surf, (255, 255, 255), (cx - 26, cy - 3, 52, 6))
            pygame.draw.circle(surf, light, (cx - 28, cy), 8)
            pygame.draw.circle(surf, light, (cx + 28, cy), 8)
            pygame.draw.rect(surf, outline, (cx - 28, cy - 6, 56, 12), 2)
        elif v == 1:
            # v1: vertical beam
            pygame.draw.rect(surf, light, (cx - 6, cy - 28, 12, 56))
            pygame.draw.rect(surf, (255, 255, 255), (cx - 3, cy - 26, 6, 52))
            pygame.draw.circle(surf, light, (cx, cy - 28), 8)
            pygame.draw.circle(surf, light, (cx, cy + 28), 8)
            pygame.draw.rect(surf, outline, (cx - 6, cy - 28, 12, 56), 2)
        elif v == 2:
            # v2: diagonal beam
            pygame.draw.line(surf, light, (cx - 24, cy + 24), (cx + 24, cy - 24), 12)
            pygame.draw.line(surf, (255, 255, 255), (cx - 22, cy + 22), (cx + 22, cy - 22), 5)
            pygame.draw.circle(surf, light, (cx - 24, cy + 24), 8)
            pygame.draw.circle(surf, light, (cx + 24, cy - 24), 8)
            pygame.draw.line(surf, outline, (cx - 24, cy + 24), (cx + 24, cy - 24), 2)
        else:
            # v3: converging beams — 3 beams meeting at center
            for ang in (0, 120, 240):
                rad = math.radians(ang)
                sx = cx - int(math.cos(rad) * 28)
                sy = cy - int(math.sin(rad) * 28)
                pygame.draw.line(surf, light, (sx, sy), (cx, cy), 6)
                pygame.draw.line(surf, (255, 255, 255), (sx, sy), (cx, cy), 2)
                pygame.draw.circle(surf, light, (sx, sy), 6)
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 10)
            pygame.draw.circle(surf, outline, (cx, cy), 10, 2)

    elif kind == "trap":
        if v == 0:
            # v0: spiked trap — circle with spikes
            pygame.draw.circle(surf, light, (cx, cy), 16)
            pygame.draw.circle(surf, (255, 255, 255), (cx - 4, cy - 4), 8)
            for ang in range(0, 360, 45):
                rad = math.radians(ang)
                x1 = cx + int(math.cos(rad) * 16)
                y1 = cy + int(math.sin(rad) * 16)
                x2 = cx + int(math.cos(rad) * 28)
                y2 = cy + int(math.sin(rad) * 28)
                pygame.draw.line(surf, light, (x1, y1), (x2, y2), 3)
                pygame.draw.polygon(surf, outline, [(x1, y1), (x2, y2), (cx + int(math.cos(rad + 0.3) * 16), cy + int(math.sin(rad + 0.3) * 16))], 1)
            pygame.draw.circle(surf, outline, (cx, cy), 16, 2)
        elif v == 1:
            # v1: web/net — radial lines + concentric
            for ang in range(0, 360, 60):
                rad = math.radians(ang)
                pygame.draw.line(surf, light,
                    (cx, cy),
                    (cx + int(math.cos(rad) * 28), cy + int(math.sin(rad) * 28)), 2)
            for r in (10, 20, 28):
                pygame.draw.circle(surf, light, (cx, cy), r, 1)
            pygame.draw.circle(surf, outline, (cx, cy), 28, 2)
        elif v == 2:
            # v2: rune trap — square with rune
            pygame.draw.rect(surf, light, (cx - 22, cy - 22, 44, 44), 3)
            pygame.draw.rect(surf, shade(dark, 1.3), (cx - 18, cy - 18, 36, 36))
            # inner rune (X)
            pygame.draw.line(surf, light, (cx - 12, cy - 12), (cx + 12, cy + 12), 2)
            pygame.draw.line(surf, light, (cx + 12, cy - 12), (cx - 12, cy + 12), 2)
            pygame.draw.circle(surf, light, (cx, cy), 6)
        else:
            # v3: spike pit — ground spikes
            for ox in (-20, -6, 8, 20):
                pygame.draw.polygon(surf, light,
                    [(cx + ox - 4, cy + 22), (cx + ox, cy - 18), (cx + ox + 4, cy + 22)])
                pygame.draw.polygon(surf, (255, 255, 255),
                    [(cx + ox - 2, cy + 20), (cx + ox, cy - 14), (cx + ox + 2, cy + 20)])
                pygame.draw.polygon(surf, outline,
                    [(cx + ox - 4, cy + 22), (cx + ox, cy - 18), (cx + ox + 4, cy + 22)], 1)
            pygame.draw.line(surf, outline, (cx - 24, cy + 22), (cx + 24, cy + 22), 2)


# ---------------------------------------------------------------------------
# Backgrounds
# ---------------------------------------------------------------------------
def make_title_bg(path):
    surf = pygame.Surface((1280, 720))
    # pixel-art sky: 2-tone dithered vertical gradient (no AA lerp_color ramp)
    px_dither(surf, SKY_TOP, SKY_BOTTOM, (0, 0, 1280, 720))
    # stars (chunky blocks, no AA)
    for _ in range(120):
        x = random.randint(0, 1280)
        y = random.randint(0, 420)
        b = random.randint(120, 255)
        pygame.draw.rect(surf, (b, b, b), (x, y, 2, 2))
    # moon (solid disc + dithered shading, no AA)
    pygame.draw.circle(surf, (240, 220, 170), (960, 160), 120)
    pygame.draw.circle(surf, (255, 250, 220), (960, 160), 90)
    pygame.draw.circle(surf, (255, 250, 230), (960, 160), 60)
    # distant mountains (solid palette fills, no AA)
    for layer, col in [(0, (70, 60, 100)), (1, (54, 46, 84)), (2, (40, 34, 66))]:
        base_y = 460 + layer * 40
        pts = [(0, 720)]
        x = 0
        while x < 1280:
            h = random.randint(80, 200) - layer * 20
            pts.append((x, base_y - h))
            x += random.randint(120, 220)
        pts.append((1280, 720))
        pygame.draw.polygon(surf, col, pts)
    # foreground silhouette castle (solid blocks, no AA)
    pygame.draw.rect(surf, (28, 24, 44), (520, 380, 240, 200))
    for tx in (540, 620, 700):
        pygame.draw.rect(surf, (28, 24, 44), (tx, 340, 40, 240))
        pygame.draw.polygon(surf, (28, 24, 44), [(tx, 340), (tx + 20, 300), (tx + 40, 340)])
    pygame.draw.rect(surf, (28, 24, 44), (620, 300, 40, 60))
    pygame.draw.polygon(surf, (40, 34, 60), [(620, 300), (640, 270), (660, 300)])
    pygame.image.save(surf, path)

# ---------------------------------------------------------------------------
# UI elements
# ---------------------------------------------------------------------------
def make_ui():
    # Only the rarity frames are loaded by load_ui (frame_R/SR/SSR). The
    # button / panel / gem / gold / star / element / cursor / banner sprites
    # were all drawn programmatically by the scenes and never reached by a
    # loader, so they are no longer generated.
    # rarity frames 220x280 — 2-tone dithered fill + colored rim + corner gems (pixel-art, no AA)
    for rar, col in RARITY_COLORS.items():
        s = pygame.Surface((220, 280), pygame.SRCALPHA)
        fg = px_dither_surf(220, 280, shade(col, 1.2), shade(col, 0.4))
        clip_to_rect(fg, pygame.Rect(0, 0, 220, 280), border_radius=16)
        s.blit(fg, (0, 0))
        # dark inner panel for contrast (solid block, no AA)
        ip = pygame.Surface((208, 268), pygame.SRCALPHA)
        pygame.draw.rect(ip, (20, 20, 30, 210), ip.get_rect(), border_radius=12)
        s.blit(ip, (6, 6))
        # top sheen (solid block, no AA)
        pygame.draw.rect(s, (255, 255, 255), (10, 8, 200, 8), border_radius=4)
        pygame.draw.rect(s, col, s.get_rect(), 5, border_radius=16)
        pygame.draw.rect(s, shade(col, 1.3), (8, 8, 204, 24), border_radius=12)
        # corner accent gems (solid discs, no AA)
        for cx2, cy2 in ((14, 14), (206, 14), (14, 266), (206, 266)):
            pygame.draw.circle(s, shade(col, 1.3), (cx2, cy2), 5)
            pygame.draw.circle(s, shade(col, 0.4), (cx2, cy2), 3)
        pygame.image.save(s, os.path.join(ASSET_DIR, "ui", f"frame_{rar}.png"))

def make_shop_bg(path):
    surf = pygame.Surface((1280, 720))
    # pixel-art shop: 2-tone dithered vertical gradient (no AA)
    px_dither(surf, (60, 40, 70), (30, 20, 40), (0, 0, 1280, 720))
    # wooden counter (solid block, no AA)
    pygame.draw.rect(surf, (80, 50, 30), (0, 520, 1280, 200))
    for x in range(0, 1280, 60):
        pygame.draw.line(surf, (60, 38, 22), (x, 520), (x, 720), 2)
    # hanging lanterns (solid blocks, no AA)
    for x in (200, 640, 1080):
        pygame.draw.line(surf, (40, 30, 20), (x, 0), (x, 120), 2)
        pygame.draw.circle(surf, (255, 180, 80), (x, 130), 22)
        pygame.draw.circle(surf, (255, 220, 140), (x, 130), 22, 2)
        # glow (chunky block, no AA)
        glow = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 200, 100, 60), (60, 60), 60)
        surf.blit(glow, (x - 60, 70))
    # shelves with bottles (solid blocks, no AA)
    for sy in (240, 360):
        pygame.draw.rect(surf, (50, 34, 22), (120, sy, 1040, 12))
        for bx in range(160, 1120, 120):
            pygame.draw.rect(surf, (60, 90, 140), (bx, sy - 50, 26, 50), border_radius=6)
            pygame.draw.rect(surf, (120, 160, 220), (bx + 4, sy - 46, 18, 30))
            pygame.draw.rect(surf, (40, 30, 20), (bx + 6, sy - 56, 14, 8))
    pygame.image.save(surf, path)

def _flask(liquid_top, liquid_bot, cap_col=(200, 200, 210), body_rect=(44, 44, 40, 56),
           cap_pts=((44, 30), (84, 30), (80, 44), (48, 44))):
    """A potion flask with a 2-tone dithered liquid + cork + specular shine
    (pixel-art: no AA gradient)."""
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    # cork (solid polygon, no AA)
    pygame.draw.polygon(s, cap_col, list(cap_pts))
    pygame.draw.polygon(s, (30, 20, 30), list(cap_pts), 2)
    # liquid body — 2-tone dithered fill (no AA vertical gradient)
    bx, by, bw, bh = body_rect
    liq = px_dither_surf(bw, bh, liquid_top, liquid_bot)
    clip_to_rect(liq, pygame.Rect(0, 0, bw, bh), border_radius=10)
    s.blit(liq, (bx, by))
    # specular highlight streak (solid block, no AA)
    pygame.draw.rect(s, (255, 255, 255), (bx + 5, by + 4, 6, bh - 8), border_radius=3)
    pygame.draw.rect(s, (30, 20, 30), (bx, by, bw, bh), 3, border_radius=10)
    # bubble (solid block, no AA)
    pygame.draw.rect(s, shade(liquid_top, 1.3), (bx + 6, by + 8, 6, 6))
    return s

def _blade_poly(pts, edge=(255, 255, 255), base=(200, 200, 215), dark=(150, 150, 170)):
    """A sword blade polygon with a 2-tone dithered metal fill + bright edge
    (pixel-art: no AA horizontal gradient)."""
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    # bounding box of the blade for the dithered fill
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = px_dither_surf(w, h, base, dark)
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (30, 26, 40), pts, 2)
    # bright edge (left side, solid line, no AA)
    pygame.draw.line(s, edge, (minx + 1, miny + 2), (minx + 1, maxy - 2), 2)
    return s

def make_items():
    """Generate item icons (consumables + equipment) with 2-tone dithered fills
    (pixel-art: no AA gradients)."""
    items = []

    # --- Consumables ---
    # HP Potion - red flask
    s = _flask((220, 80, 90), (160, 30, 50))
    items.append(("hp_potion", s))

    # MP Potion - blue flask
    s = _flask((90, 160, 240), (40, 90, 200))
    pygame.draw.rect(s, (200, 230, 255), (50, 50, 6, 6))
    items.append(("mp_potion", s))

    # Full Elixir - golden flask
    s = _flask((255, 220, 90), (200, 150, 30), cap_col=(220, 220, 230),
               body_rect=(42, 42, 44, 60), cap_pts=((40, 26), (88, 26), (82, 42), (46, 42)))
    # sparkle (solid cross, no AA)
    pygame.draw.line(s, (255, 255, 220), (64, 56), (64, 70), 2)
    pygame.draw.line(s, (255, 255, 220), (58, 63), (70, 63), 2)
    # glow (chunky block, no AA)
    pygame.draw.circle(s, (255, 230, 120), (64, 70), 18)
    pygame.draw.circle(s, (255, 255, 200), (64, 70), 10)
    items.append(("full_elixir", s))

    # Revive Scroll
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    scroll = px_dither_surf(52, 80, (245, 235, 200), (200, 180, 140))
    clip_to_rect(scroll, pygame.Rect(0, 0, 52, 80), border_radius=6)
    s.blit(scroll, (38, 24))
    pygame.draw.rect(s, (180, 150, 100), (38, 24, 52, 80), 3, border_radius=6)
    # seal — 2-tone dithered fill clipped to a circle (no AA)
    seal = px_dither_surf(26, 26, (255, 100, 100), (160, 30, 30))
    clip_to_circle(seal, (13, 13), 12)
    s.blit(seal, (51, 37))
    pygame.draw.circle(s, (30, 20, 30), (64, 50), 12, 2)
    # cross (solid blocks, no AA)
    pygame.draw.rect(s, (255, 245, 245), (61, 42, 6, 16))
    pygame.draw.rect(s, (255, 245, 245), (55, 47, 18, 6))
    items.append(("revive_scroll", s))

    # Bomb
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    bomb = px_dither_surf(60, 60, (90, 90, 110), (30, 30, 45))
    clip_to_circle(bomb, (30, 30), 30)
    s.blit(bomb, (34, 44))
    pygame.draw.circle(s, (70, 70, 90), (64, 74), 30, 3)
    pygame.draw.rect(s, (140, 95, 50), (60, 40, 8, 16))
    pygame.draw.rect(s, (30, 26, 30), (60, 40, 8, 16), 1)
    # spark glow (chunky block, no AA)
    pygame.draw.circle(s, (255, 220, 80), (64, 38), 12)
    pygame.draw.circle(s, (255, 255, 200), (64, 38), 6)
    # shine (solid block, no AA)
    pygame.draw.rect(s, (160, 160, 180), (50, 60, 8, 8))
    items.append(("bomb", s))

    # --- Equipment ---
    # Rusty Sword
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(64, 16), (72, 16), (72, 80), (64, 90), (56, 80), (56, 16)]
    blade = _blade_poly(pts, edge=(220, 200, 180), base=(190, 170, 150), dark=(130, 110, 90))
    s.blit(blade, (0, 0))
    pygame.draw.rect(s, (140, 100, 55), (48, 80, 32, 8))
    pygame.draw.rect(s, (30, 26, 30), (48, 80, 32, 8), 1)
    pygame.draw.rect(s, (90, 65, 35), (60, 88, 8, 22))
    pygame.draw.rect(s, (30, 26, 30), (60, 88, 8, 22), 1)
    items.append(("rusty_sword", s))

    # Steel Blade
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(64, 12), (70, 12), (70, 84), (64, 96), (58, 84), (58, 12)]
    blade = _blade_poly(pts, edge=(255, 255, 255), base=(225, 228, 240), dark=(150, 155, 175))
    s.blit(blade, (0, 0))
    pygame.draw.rect(s, (190, 150, 65), (46, 84, 36, 8), border_radius=3)
    pygame.draw.rect(s, (30, 30, 40), (46, 84, 36, 8), 1, border_radius=3)
    pygame.draw.rect(s, (90, 65, 35), (60, 92, 8, 24))
    pygame.draw.rect(s, (30, 30, 40), (60, 92, 8, 24), 1)
    items.append(("steel_blade", s))

    # Dragon Fang
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(64, 8), (74, 18), (74, 80), (64, 100), (54, 80), (54, 18)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = px_dither_surf(w, h, (255, 130, 70), (170, 50, 30))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (255, 160, 60), pts, 2)
    # serrations (solid blocks, no AA)
    for i in range(4):
        y = 30 + i * 14
        pygame.draw.polygon(s, (255, 200, 80), [(54, y), (48, y + 6), (54, y + 10)])
        pygame.draw.polygon(s, (255, 200, 80), [(74, y), (80, y + 6), (74, y + 10)])
    pygame.draw.rect(s, (140, 95, 50), (48, 92, 32, 8))
    pygame.draw.rect(s, (30, 26, 40), (48, 92, 32, 8), 1)
    items.append(("dragon_fang", s))

    # Mage Rod
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    shaft = px_dither_surf(8, 80, (150, 100, 60), (90, 60, 35))
    clip_to_rect(shaft, pygame.Rect(0, 0, 8, 80))
    s.blit(shaft, (60, 30))
    pygame.draw.rect(s, (30, 26, 30), (60, 30, 8, 80), 2)
    # orb — 2-tone dithered fill clipped to a circle + glow (chunky block, no AA)
    orb = px_dither_surf(36, 36, (200, 230, 255), (60, 120, 200))
    clip_to_circle(orb, (18, 18), 18)
    s.blit(orb, (46, 10))
    pygame.draw.circle(s, (120, 180, 255), (64, 28), 20)
    pygame.draw.rect(s, (255, 255, 255), (56, 20, 6, 6))
    pygame.draw.rect(s, (255, 255, 255), (58, 22, 3, 3))
    pygame.draw.circle(s, (30, 26, 40), (64, 28), 18, 2)
    items.append(("mage_rod", s))

    # Leather Armor
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(40, 40), (88, 40), (96, 96), (32, 96)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = px_dither_surf(w, h, (150, 100, 60), (90, 60, 30))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (30, 26, 30), pts, 3)
    # straps (solid blocks, no AA)
    pygame.draw.rect(s, (90, 60, 30), (58, 40, 12, 56))
    pygame.draw.rect(s, (70, 45, 25), (44, 60, 40, 8))
    # buckle gem (solid discs, no AA)
    pygame.draw.circle(s, (255, 220, 100), (64, 56), 6)
    pygame.draw.circle(s, (180, 140, 40), (64, 56), 4)
    pygame.draw.circle(s, (30, 26, 30), (64, 56), 6, 1)
    items.append(("leather_armor", s))

    # Plate Mail
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(38, 38), (90, 38), (98, 100), (30, 100)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = px_dither_surf(w, h, (200, 210, 230), (110, 120, 145))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (30, 30, 40), pts, 3)
    for i in range(4):
        y = 44 + i * 14
        pygame.draw.line(s, (220, 230, 245), (36, y), (92, y), 2)
    # chest gem (solid discs, no AA)
    pygame.draw.circle(s, (255, 255, 255), (64, 52), 8)
    pygame.draw.circle(s, (120, 130, 150), (64, 52), 6)
    pygame.draw.circle(s, (120, 130, 150), (64, 52), 8, 2)
    items.append(("plate_mail", s))

    # Aether Vest
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(36, 38), (92, 38), (100, 102), (28, 102)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = px_dither_surf(w, h, (180, 130, 240), (90, 60, 140))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (220, 160, 255), pts, 3)
    # glowing runes (solid blocks, no AA)
    for ry in (56, 76):
        pygame.draw.circle(s, (255, 240, 180), (64, ry), 8)
        pygame.draw.circle(s, (255, 255, 200), (64, ry), 5)
        pygame.draw.circle(s, (30, 26, 40), (64, ry), 6, 1)
    pygame.draw.line(s, (255, 240, 180), (64, 50), (64, 82), 2)
    items.append(("aether_vest", s))

    # Swift Boots
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    for bx in (40, 70):
        pts = [(bx, 60), (bx + 26, 60), (bx + 30, 84), (bx, 84)]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        w, h = maxx - minx, maxy - miny
        g = px_dither_surf(w, h, (150, 100, 60), (90, 60, 30))
        m = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
        g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        s.blit(g, (minx, miny))
        pygame.draw.polygon(s, (30, 26, 30), pts, 2)
    # wing — 2-tone dithered fill clipped to the wing polygon (no AA)
    wpts = [(50, 48), (74, 40), (80, 56), (54, 56)]
    wxs = [p[0] for p in wpts]; wys = [p[1] for p in wpts]
    wminx, wmaxx, wminy, wmaxy = min(wxs), max(wxs), min(wys), max(wys)
    ww, whh = wmaxx - wminx, wmaxy - wminy
    wg2 = px_dither_surf(ww, whh, (255, 255, 255), (180, 200, 240))
    wm = pygame.Surface((ww, whh), pygame.SRCALPHA)
    pygame.draw.polygon(wm, (255, 255, 255, 255), [(p[0] - wminx, p[1] - wminy) for p in wpts])
    wg2.blit(wm, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(wg2, (wminx, wminy))
    items.append(("swift_boots", s))

    # Mana Pendant
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pygame.draw.line(s, (210, 190, 90), (64, 24), (40, 56), 4)
    pygame.draw.line(s, (210, 190, 90), (64, 24), (88, 56), 4)
    # gem — 2-tone dithered fill clipped to a circle + glow (chunky block, no AA)
    pygame.draw.circle(s, (120, 180, 255), (64, 70), 22)
    gem = px_dither_surf(44, 44, (200, 230, 255), (40, 90, 200))
    clip_to_circle(gem, (22, 22), 22)
    s.blit(gem, (42, 48))
    pygame.draw.rect(s, (255, 255, 255), (54, 60, 6, 6))
    pygame.draw.rect(s, (255, 255, 255), (56, 62, 3, 3))
    pygame.draw.circle(s, (30, 26, 50), (64, 70), 22, 2)
    items.append(("mana_pendant", s))

    # Hero Crest
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(64, 24), (88, 48), (80, 92), (48, 92), (40, 48)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = px_dither_surf(w, h, (255, 220, 120), (200, 150, 40))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (255, 220, 120), pts, 3)
    # emblem star (solid palette fills, no AA)
    draw_star(s, 64, 58, 14, 5, (255, 255, 255), (255, 255, 255))
    pygame.draw.circle(s, (180, 140, 40), (64, 58), 14, 2)
    items.append(("hero_crest", s))

    # --- new consumables (Phase B) ---
    # Mega Potion - big red flask
    s = _flask((240, 70, 80), (180, 30, 40), cap_col=(200, 200, 210),
               body_rect=(42, 42, 44, 60), cap_pts=((40, 26), (88, 26), (82, 42), (46, 42)))
    pygame.draw.rect(s, (255, 220, 220), (50, 50, 6, 6))
    items.append(("mega_potion", s))

    # Ether - blue bottle
    s = _flask((70, 150, 250), (30, 80, 200), cap_col=(200, 200, 210),
               body_rect=(42, 42, 44, 60), cap_pts=((40, 26), (88, 26), (82, 42), (46, 42)))
    pygame.draw.rect(s, (200, 230, 255), (50, 50, 6, 6))
    items.append(("ether", s))

    # Mega Bomb - bigger bomb
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    bomb = px_dither_surf(72, 72, (100, 100, 120), (30, 30, 45))
    clip_to_circle(bomb, (36, 36), 36)
    s.blit(bomb, (28, 40))
    pygame.draw.circle(s, (70, 70, 90), (64, 76), 36, 3)
    pygame.draw.rect(s, (140, 95, 50), (60, 36, 8, 20))
    pygame.draw.rect(s, (30, 26, 30), (60, 36, 8, 20), 1)
    # spark glow (chunky block, no AA)
    pygame.draw.circle(s, (255, 200, 80), (64, 32), 14)
    pygame.draw.circle(s, (255, 255, 200), (64, 32), 8)
    pygame.draw.circle(s, (255, 255, 200), (64, 32), 4)
    pygame.draw.rect(s, (160, 160, 180), (50, 64, 8, 8))
    items.append(("mega_bomb", s))

    # --- new equipment (Phase B) ---
    # Inferno Blade - fiery sword
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(64, 10), (72, 14), (72, 82), (64, 96), (56, 82), (56, 14)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = px_dither_surf(w, h, (255, 220, 120), (220, 90, 40))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (255, 200, 80), pts, 2)
    # ember glow along the blade (chunky block, no AA)
    pygame.draw.rect(s, (255, 180, 80), (54, 14, 20, 80))
    for i in range(5):
        y = 22 + i * 12
        pygame.draw.polygon(s, (255, 220, 120), [(56, y), (50, y + 6), (56, y + 8)])
        pygame.draw.polygon(s, (255, 220, 120), [(72, y), (78, y + 6), (72, y + 8)])
    pygame.draw.rect(s, (140, 95, 50), (48, 92, 32, 8))
    pygame.draw.rect(s, (30, 26, 40), (48, 92, 32, 8), 1)
    items.append(("inferno_blade", s))

    # Frost Staff - icy staff
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    shaft = px_dither_surf(8, 80, (150, 180, 210), (90, 120, 160))
    clip_to_rect(shaft, pygame.Rect(0, 0, 8, 80))
    s.blit(shaft, (60, 30))
    pygame.draw.rect(s, (30, 30, 50), (60, 30, 8, 80), 2)
    # crystal head — 2-tone dithered fill clipped to a diamond + glow (no AA)
    pygame.draw.circle(s, (180, 220, 255), (64, 26), 22)
    cryst = px_dither_surf(40, 40, (230, 245, 255), (90, 150, 210))
    cm = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.polygon(cm, (255, 255, 255, 255), [(20, 0), (38, 20), (20, 40), (2, 20)])
    cryst.blit(cm, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(cryst, (44, 6))
    pygame.draw.polygon(s, (30, 30, 60), [(64, 8), (78, 26), (64, 44), (50, 26)], 2)
    items.append(("frost_staff", s))

    # Void Blade - dark sword
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(64, 12), (70, 12), (70, 84), (64, 96), (58, 84), (58, 12)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = px_dither_surf(w, h, (180, 120, 240), (90, 50, 150))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (200, 140, 255), pts, 2)
    # void glow down the center (chunky block, no AA)
    pygame.draw.rect(s, (200, 160, 255), (56, 14, 16, 80))
    pygame.draw.rect(s, (100, 70, 150), (60, 92, 8, 24))
    pygame.draw.rect(s, (30, 26, 50), (60, 92, 8, 24), 1)
    items.append(("void_blade", s))

    # Guardian Aegis - big shield
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(64, 18), (96, 36), (96, 70), (64, 100), (32, 70), (32, 36)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = px_dither_surf(w, h, (220, 235, 250), (120, 150, 190))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (30, 30, 50), pts, 3)
    # boss gem — 2-tone dithered fill clipped to a circle + glow (no AA)
    pygame.draw.circle(s, (255, 240, 120), (64, 56), 16)
    gem = px_dither_surf(30, 30, (255, 250, 180), (180, 150, 40))
    clip_to_circle(gem, (15, 15), 14)
    s.blit(gem, (49, 41))
    pygame.draw.rect(s, (255, 255, 255), (58, 48, 6, 6))
    pygame.draw.circle(s, (180, 160, 60), (64, 58), 14, 2)
    items.append(("guardian_aegis", s))

    # Shadow Cloak - hooded cloak
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(40, 56), (88, 56), (96, 104), (32, 104)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = px_dither_surf(w, h, (100, 80, 140), (40, 30, 70))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (40, 30, 70), pts, 3)
    # hood — 2-tone dithered fill clipped to a circle (no AA)
    hood = px_dither_surf(36, 36, (90, 70, 130), (30, 20, 50))
    clip_to_circle(hood, (18, 18), 18)
    s.blit(hood, (46, 22))
    pygame.draw.circle(s, (30, 20, 50), (64, 40), 18, 2)
    items.append(("shadow_cloak", s))

    # Berserker Ring - red ring
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    ring = px_dither_surf(68, 68, (255, 100, 100), (140, 30, 30))
    clip_to_circle(ring, (34, 34), 34)
    s.blit(ring, (30, 30))
    pygame.draw.circle(s, (255, 220, 120), (64, 64), 34, 3)
    pygame.draw.circle(s, (30, 20, 30), (64, 64), 34, 2)
    pygame.draw.circle(s, (30, 20, 30), (64, 64), 18)
    # gem — 2-tone dithered fill clipped to a circle + glow (no AA)
    pygame.draw.circle(s, (255, 220, 120), (64, 52), 11)
    gem = px_dither_surf(16, 16, (255, 250, 200), (200, 150, 40))
    clip_to_circle(gem, (8, 8), 7)
    s.blit(gem, (56, 46))
    items.append(("berserker_ring", s))

    # Sage Amulet - purple amulet
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pygame.draw.line(s, (210, 170, 90), (64, 24), (40, 56), 4)
    pygame.draw.line(s, (210, 170, 90), (64, 24), (88, 56), 4)
    # gem — 2-tone dithered fill clipped to a circle + glow (no AA)
    pygame.draw.circle(s, (180, 120, 240), (64, 70), 24)
    gem = px_dither_surf(48, 48, (230, 190, 255), (90, 50, 150))
    clip_to_circle(gem, (24, 24), 24)
    s.blit(gem, (40, 46))
    pygame.draw.rect(s, (255, 255, 255), (54, 60, 6, 6))
    pygame.draw.rect(s, (255, 255, 255), (56, 62, 3, 3))
    pygame.draw.circle(s, (60, 30, 90), (64, 70), 24, 2)
    items.append(("sage_amulet", s))

    for name, surf in items:
        pygame.image.save(surf, os.path.join(ASSET_DIR, "items", f"{name}.png"))

# ---------------------------------------------------------------------------
# v2 world sprites — terrain tiles + landmarks + village buildings + ground
# loot drops (Task A4). Each is pixel-art: palette-locked solid fills, 2-color
# checker dithers for gradients (px_dither/px_dither_surf), no anti-aliasing,
# no smoothscale. Sizes match the v2 world enrichment: water/bridge 40x40
# (one TILE), landmarks ~80x80, village buildings ~60x60, drops ~16x16.
# Biome tinting happens at draw time in C3, so a single neutral water/bridge
# tile is shipped (the biome variants are produced by tint+blend there).
# ---------------------------------------------------------------------------
# water/bridge tile size matches WD.TILE (40). Imported lazily so the asset
# generator stays runnable without the world module (the constant is fixed).
TILE_PX = 40

def draw_water_tile(surf, biome_pal=None):
    """A 40x40 water tile — a 2-tone dithered blue fill with a few dithered
    ripple lines so it reads as water, not a flat blue square (pixel-art: no
    AA gradient). biome_pal is the optional biome palette dict; when given the
    base tints toward the biome's ground color so the same water sprite can be
    re-tinted per biome by C3 (we ship a single neutral tile here).
    """
    w = h = TILE_PX
    # base water blues (palette-locked, 2-tone checker dither, no AA gradient)
    c1 = ( 70, 130, 210)
    c2 = ( 36,  78, 150)
    if biome_pal is not None:
        # tint toward the biome ground so plains water reads greener, void
        # water reads purpler, etc. A single lerp step keeps it chunky.
        gnd = biome_pal.get("ground", (90, 130, 180))
        c1 = lerp_color(c1, gnd, 0.30)
        c2 = lerp_color(c2, gnd, 0.45)
    px_dither(surf, c1, c2, (0, 0, w, h))
    # dithered ripple lines — two horizontal bands of the light tone so the
    # surface reads as a ripple pattern, not a flat fill (solid blocks, no AA)
    ripple = (180, 215, 245)
    for ry in (8, 22):
        for xx in range(0, w, PIXEL):
            # checker-stagger the ripple so it shimmers, not a straight line
            off = PIXEL if ((ry // PIXEL) % 2) else 0
            if (xx + off) % (PIXEL * 2) < PIXEL:
                pygame.draw.rect(surf, ripple, (xx, ry, PIXEL, PIXEL))
    # a couple of bright sparkles (solid blocks, no AA)
    pygame.draw.rect(surf, (220, 235, 255), (5, 5, PIXEL, PIXEL))
    pygame.draw.rect(surf, (220, 235, 255), (28, 18, PIXEL, PIXEL))
    # outline (solid, no AA)
    pygame.draw.rect(surf, (20, 40, 80), (0, 0, w, h), 1)

def draw_bridge_tile(surf, biome_pal=None):
    """A 40x40 bridge tile — wood planks laid over water (pixel-art: no AA).
    Two plank rows of dithered wood over a dithered water underlay, with a
    dark plank-gap line between them and iron studs at the corners.
    """
    w = h = TILE_PX
    # water underlay (a thin strip top + bottom so the bridge reads as over
    # water, not a wood raft). Same dithered fill as draw_water_tile.
    water_c1, water_c2 = ( 70, 130, 210), ( 36,  78, 150)
    if biome_pal is not None:
        gnd = biome_pal.get("ground", (90, 130, 180))
        water_c1 = lerp_color(water_c1, gnd, 0.30)
        water_c2 = lerp_color(water_c2, gnd, 0.45)
    px_dither(surf, water_c1, water_c2, (0, 0, w, 4))
    px_dither(surf, water_c1, water_c2, (0, h - 4, w, 4))
    # plank wood — 2-tone dithered fill (no AA horizontal gradient)
    wood_l, wood_d = (150, 100, 60), (90, 60, 30)
    px_dither(surf, wood_l, wood_d, (0, 4, w, h - 8))
    # plank-gap line (solid dark, no AA) splitting the two plank rows
    pygame.draw.rect(surf, (60, 40, 20), (0, h // 2 - 1, w, 2))
    # wood grain lines (solid, no AA) — a couple of staggered lines per row
    for gy in (10, 24):
        for xx in range(0, w, PIXEL * 2):
            pygame.draw.rect(surf, shade(wood_d, 0.8), (xx + (gy % 8), gy, PIXEL, 1))
    # iron corner studs (solid blocks, no AA)
    for cx, cy in ((4, 7), (w - 7, 7), (4, h - 7), (w - 7, h - 7)):
        pygame.draw.rect(surf, (90, 90, 100), (cx, cy, 3, 3))
        pygame.draw.rect(surf, (40, 40, 50), (cx, cy, 3, 3), 1)
    # outline (solid, no AA)
    pygame.draw.rect(surf, (40, 25, 15), (0, 4, w, h - 8), 1)

def draw_landmark(surf, kind, element_color=None):
    """A ~80x80 landmark sprite, per-kind. Pixel-art: dithered fills clipped
    to shape, solid palette fills, no AA. kind is one of:
    statue / ruin / shrine / obelisk / rift_anchor. element_color is an
    optional (r,g,b) accent so the same landmark can be re-tinted per biome.
    The sprite is drawn on a 80x80 surface; the caller blits it at the tile.
    """
    cx, cy = 40, 44
    outline = (30, 26, 40)
    accent = element_color if element_color is not None else (200, 170, 90)
    accent_l = shade(accent, 1.25)
    accent_d = shade(accent, 0.65)

    # ground shadow (chunky ellipse, no AA) under every landmark
    shadow = pygame.Surface((72, 22), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
    surf.blit(shadow, (cx - 36, 70))

    if kind == "statue":
        # a robed figure on a pedestal. Pedestal — 2-tone dithered stone fill
        # clipped to a rounded rect (no AA).
        ped = px_dither_surf(56, 18, (200, 200, 200), (140, 140, 150))
        clip_to_rect(ped, pygame.Rect(0, 0, 56, 18), border_radius=3)
        surf.blit(ped, (cx - 28, 56))
        pygame.draw.rect(surf, outline, (cx - 28, 56, 56, 18), 2, border_radius=3)
        # robe body — 2-tone dithered fill clipped to a trapezoid (no AA)
        robe_pts = [(cx - 20, 22), (cx + 20, 22), (cx + 26, 58), (cx - 26, 58)]
        xs = [p[0] for p in robe_pts]; ys = [p[1] for p in robe_pts]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        rg = px_dither_surf(maxx - minx, maxy - miny, accent_l, accent_d)
        m = pygame.Surface((maxx - minx, maxy - miny), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - minx, p[1] - miny) for p in robe_pts])
        rg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(rg, (minx, miny))
        pygame.draw.polygon(surf, outline, robe_pts, 2)
        # head — 2-tone dithered fill clipped to a circle (no AA)
        head = px_dither_surf(28, 28, (235, 215, 180), (180, 150, 120))
        clip_to_circle(head, (14, 14), 14)
        surf.blit(head, (cx - 14, 8))
        pygame.draw.circle(surf, outline, (cx, 22), 14, 2)
        # halo — a thin accent ring (solid, no AA)
        pygame.draw.circle(surf, accent_l, (cx, 22), 18, 2)
    elif kind == "ruin":
        # a broken pillar — a tall shaft with a jagged top + a fallen chunk.
        # Shaft — 2-tone dithered stone fill (no AA vertical gradient).
        shaft = px_dither_surf(28, 60, (200, 195, 188), (130, 125, 120))
        clip_to_rect(shaft, pygame.Rect(0, 0, 28, 60), border_radius=2)
        surf.blit(shaft, (cx - 14, 14))
        pygame.draw.rect(surf, outline, (cx - 14, 14, 28, 60), 2, border_radius=2)
        # jagged top — a chunky block broken at an angle (solid, no AA)
        pygame.draw.polygon(surf, (160, 155, 148),
                            [(cx - 14, 14), (cx + 14, 14), (cx + 10, 6), (cx + 2, 12), (cx - 6, 8)])
        pygame.draw.polygon(surf, outline,
                            [(cx - 14, 14), (cx + 14, 14), (cx + 10, 6), (cx + 2, 12), (cx - 6, 8)], 2)
        # capital block on top (solid, no AA)
        pygame.draw.rect(surf, (180, 175, 168), (cx - 18, 8, 36, 6), border_radius=2)
        pygame.draw.rect(surf, outline, (cx - 18, 8, 36, 6), 2, border_radius=2)
        # fallen chunk at the base (solid dithered block, no AA)
        chunk = px_dither_surf(22, 14, (190, 185, 178), (130, 125, 120))
        clip_to_rect(chunk, pygame.Rect(0, 0, 22, 14), border_radius=2)
        surf.blit(chunk, (cx + 16, 58))
        pygame.draw.rect(surf, outline, (cx + 16, 58, 22, 14), 2, border_radius=2)
        # crack lines (solid, no AA)
        pygame.draw.line(surf, shade(outline, 0.8), (cx - 8, 30), (cx + 6, 44), 2)
        pygame.draw.line(surf, shade(outline, 0.8), (cx + 4, 22), (cx - 2, 34), 1)
    elif kind == "shrine":
        # a small shrine — a peaked roof on four posts over a stone base.
        # Stone base — 2-tone dithered fill (no AA).
        base = px_dither_surf(56, 12, (190, 185, 178), (130, 125, 120))
        clip_to_rect(base, pygame.Rect(0, 0, 56, 12), border_radius=2)
        surf.blit(base, (cx - 28, 58))
        pygame.draw.rect(surf, outline, (cx - 28, 58, 56, 12), 2, border_radius=2)
        # four posts (solid dithered blocks, no AA)
        for px in (cx - 22, cx - 6, cx + 10):
            post = px_dither_surf(8, 26, (180, 140, 90), (110, 80, 50))
            clip_to_rect(post, pygame.Rect(0, 0, 8, 26))
            surf.blit(post, (px, 32))
            pygame.draw.rect(surf, outline, (px, 32, 8, 26), 2)
        # peaked roof — 2-tone dithered fill clipped to a triangle (no AA)
        roof_pts = [(cx - 32, 32), (cx + 32, 32), (cx, 8)]
        xs = [p[0] for p in roof_pts]; ys = [p[1] for p in roof_pts]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        rg = px_dither_surf(maxx - minx, maxy - miny, accent_l, accent_d)
        m = pygame.Surface((maxx - minx, maxy - miny), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - minx, p[1] - miny) for p in roof_pts])
        rg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(rg, (minx, miny))
        pygame.draw.polygon(surf, outline, roof_pts, 2)
        # offering bowl on the base (solid dithered disc, no AA)
        bowl = px_dither_surf(14, 8, accent_l, accent_d)
        clip_to_rect(bowl, pygame.Rect(0, 0, 14, 8), border_radius=3)
        surf.blit(bowl, (cx - 7, 54))
        pygame.draw.rect(surf, outline, (cx - 7, 54, 14, 8), 1, border_radius=3)
    elif kind == "obelisk":
        # a tall obelisk — a tapered shaft with a pyramid cap.
        # Shaft — 2-tone dithered fill clipped to a tapered trapezoid (no AA).
        shaft_pts = [(cx - 14, 18), (cx + 14, 18), (cx + 10, 64), (cx - 10, 64)]
        xs = [p[0] for p in shaft_pts]; ys = [p[1] for p in shaft_pts]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        sg = px_dither_surf(maxx - minx, maxy - miny, (200, 195, 188), (120, 115, 110))
        m = pygame.Surface((maxx - minx, maxy - miny), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - minx, p[1] - miny) for p in shaft_pts])
        sg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(sg, (minx, miny))
        pygame.draw.polygon(surf, outline, shaft_pts, 2)
        # pyramid cap — 2-tone dithered fill clipped to a triangle (no AA)
        cap_pts = [(cx - 14, 18), (cx + 14, 18), (cx, 2)]
        cx2 = [p[0] for p in cap_pts]; cy2 = [p[1] for p in cap_pts]
        minx2, maxx2, miny2, maxy2 = min(cx2), max(cx2), min(cy2), max(cy2)
        cg = px_dither_surf(maxx2 - minx2, maxy2 - miny2, accent_l, accent_d)
        cm = pygame.Surface((maxx2 - minx2, maxy2 - miny2), pygame.SRCALPHA)
        pygame.draw.polygon(cm, (255, 255, 255, 255),
                            [(p[0] - minx2, p[1] - miny2) for p in cap_pts])
        cg.blit(cm, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(cg, (minx2, miny2))
        pygame.draw.polygon(surf, outline, cap_pts, 2)
        # base block (solid, no AA)
        pygame.draw.rect(surf, (160, 155, 148), (cx - 18, 64, 36, 8), border_radius=2)
        pygame.draw.rect(surf, outline, (cx - 18, 64, 36, 8), 2, border_radius=2)
        # glyph runes (solid accent blocks, no AA)
        for ry in (28, 42, 54):
            pygame.draw.rect(surf, accent_l, (cx - 4, ry, 8, 4))
    elif kind == "rift_anchor":
        # a glowing rift anchor — a floating crystal over a cracked base with
        # a violet glow. The crystal — 2-tone dithered fill clipped to a
        # diamond + a violet glow (chunky block, no AA soft-glow).
        glow = pygame.Surface((80, 80), pygame.SRCALPHA)
        for rr in range(34, 8, -4):
            a = int(70 * (1 - (rr - 8) / 26))
            pygame.draw.circle(glow, (180, 80, 220, a), (40, 36), rr)
        surf.blit(glow, (0, 0))
        # cracked base — 2-tone dithered fill (no AA)
        base = px_dither_surf(52, 12, (120, 90, 150), (60, 40, 90))
        clip_to_rect(base, pygame.Rect(0, 0, 52, 12), border_radius=2)
        surf.blit(base, (cx - 26, 58))
        pygame.draw.rect(surf, outline, (cx - 26, 58, 52, 12), 2, border_radius=2)
        # crack lines across the base (solid, no AA)
        pygame.draw.line(surf, (200, 120, 240), (cx - 20, 62), (cx + 20, 66), 2)
        pygame.draw.line(surf, (200, 120, 240), (cx - 12, 66), (cx + 12, 62), 1)
        # crystal — 2-tone dithered fill clipped to a diamond (no AA)
        cryst_pts = [(cx, 12), (cx + 18, 36), (cx, 58), (cx - 18, 36)]
        xs = [p[0] for p in cryst_pts]; ys = [p[1] for p in cryst_pts]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        cg2 = px_dither_surf(maxx - minx, maxy - miny, (230, 190, 255), (120, 60, 180))
        cm2 = pygame.Surface((maxx - minx, maxy - miny), pygame.SRCALPHA)
        pygame.draw.polygon(cm2, (255, 255, 255, 255),
                           [(p[0] - minx, p[1] - miny) for p in cryst_pts])
        cg2.blit(cm2, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(cg2, (minx, miny))
        pygame.draw.polygon(surf, (220, 160, 255), cryst_pts, 2)
        # core shine (solid block, no AA)
        pygame.draw.rect(surf, (255, 240, 255), (cx - 3, 30, 6, 10))
        # anchor chains — two short violet lines from the crystal to the base
        pygame.draw.line(surf, (200, 120, 240), (cx - 14, 44), (cx - 14, 58), 2)
        pygame.draw.line(surf, (200, 120, 240), (cx + 14, 44), (cx + 14, 58), 2)
    else:
        # unknown kind — a plain dithered stone block (solid, no AA) so the
        # caller never gets a blank surface
        blk = px_dither_surf(56, 56, (190, 185, 178), (120, 115, 110))
        clip_to_rect(blk, pygame.Rect(0, 0, 56, 56), border_radius=4)
        surf.blit(blk, (cx - 28, 12))
        pygame.draw.rect(surf, outline, (cx - 28, 12, 56, 56), 2, border_radius=4)

def draw_village_building(surf, kind, color=None):
    """A ~60x60 village building sprite, per-kind. Pixel-art: dithered fills
    clipped to shape, solid palette fills, no AA. kind is one of:
    house / shop / temple. color is an optional (r,g,b) tint so the same
    building can be re-tinted per village; default is a warm thatch tone.
    """
    cx, cy = 30, 36
    outline = (30, 26, 30)
    base = color if color is not None else (170, 120, 70)
    base_l = shade(base, 1.25)
    base_d = shade(base, 0.65)
    roof_l = shade(base, 1.05)
    roof_d = shade(base, 0.55)

    # ground shadow (chunky ellipse, no AA)
    shadow = pygame.Surface((56, 16), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
    surf.blit(shadow, (cx - 28, 50))

    if kind == "house":
        # peaked-roof house. Walls — 2-tone dithered fill (no AA).
        wall = px_dither_surf(44, 28, base_l, base_d)
        clip_to_rect(wall, pygame.Rect(0, 0, 44, 28))
        surf.blit(wall, (cx - 22, 28))
        pygame.draw.rect(surf, outline, (cx - 22, 28, 44, 28), 2)
        # door (solid, no AA)
        pygame.draw.rect(surf, (90, 60, 30), (cx - 6, 36, 12, 20))
        pygame.draw.rect(surf, outline, (cx - 6, 36, 12, 20), 2)
        pygame.draw.circle(surf, (255, 220, 120), (cx + 3, 46), 2)
        # window (solid dithered block, no AA)
        win = px_dither_surf(10, 10, (220, 230, 240), (120, 140, 170))
        clip_to_rect(win, pygame.Rect(0, 0, 10, 10))
        surf.blit(win, (cx - 18, 32))
        pygame.draw.rect(surf, outline, (cx - 18, 32, 10, 10), 2)
        # peaked roof — 2-tone dithered fill clipped to a triangle (no AA)
        roof_pts = [(cx - 28, 28), (cx + 28, 28), (cx, 4)]
        xs = [p[0] for p in roof_pts]; ys = [p[1] for p in roof_pts]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        rg = px_dither_surf(maxx - minx, maxy - miny, roof_l, roof_d)
        m = pygame.Surface((maxx - minx, maxy - miny), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - minx, p[1] - miny) for p in roof_pts])
        rg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(rg, (minx, miny))
        pygame.draw.polygon(surf, outline, roof_pts, 2)
        # chimney (solid, no AA)
        pygame.draw.rect(surf, (140, 100, 60), (cx + 8, 8, 6, 14))
        pygame.draw.rect(surf, outline, (cx + 8, 8, 6, 14), 2)
    elif kind == "shop":
        # shop with a sign — wider walls + a hanging sign + a flat awning.
        # Walls — 2-tone dithered fill (no AA).
        wall = px_dither_surf(48, 26, base_l, base_d)
        clip_to_rect(wall, pygame.Rect(0, 0, 48, 26))
        surf.blit(wall, (cx - 24, 30))
        pygame.draw.rect(surf, outline, (cx - 24, 30, 48, 26), 2)
        # door (solid, no AA)
        pygame.draw.rect(surf, (90, 60, 30), (cx - 6, 36, 12, 20))
        pygame.draw.rect(surf, outline, (cx - 6, 36, 12, 20), 2)
        # awning — 2-tone dithered fill clipped to a trapezoid (no AA)
        awn_pts = [(cx - 26, 28), (cx + 26, 28), (cx + 22, 38), (cx - 22, 38)]
        xs = [p[0] for p in awn_pts]; ys = [p[1] for p in awn_pts]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        ag = px_dither_surf(maxx - minx, maxy - miny, (220, 80, 80), (150, 40, 40))
        m = pygame.Surface((maxx - minx, maxy - miny), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - minx, p[1] - miny) for p in awn_pts])
        ag.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(ag, (minx, miny))
        pygame.draw.polygon(surf, outline, awn_pts, 2)
        # awning stripes (solid, no AA)
        for sx in range(cx - 22, cx + 22, 8):
            pygame.draw.line(surf, (255, 220, 200), (sx, 30), (sx - 2, 38), 2)
        # hanging sign (solid dithered block, no AA)
        sign = px_dither_surf(20, 12, (180, 140, 70), (120, 90, 40))
        clip_to_rect(sign, pygame.Rect(0, 0, 20, 12), border_radius=2)
        surf.blit(sign, (cx - 10, 14))
        pygame.draw.rect(surf, outline, (cx - 10, 14, 20, 12), 2, border_radius=2)
        # sign post (solid, no AA)
        pygame.draw.line(surf, outline, (cx, 10), (cx, 14), 2)
        # window (solid dithered block, no AA)
        win = px_dither_surf(10, 10, (220, 230, 240), (120, 140, 170))
        clip_to_rect(win, pygame.Rect(0, 0, 10, 10))
        surf.blit(win, (cx + 14, 34))
        pygame.draw.rect(surf, outline, (cx + 14, 34, 10, 10), 2)
        # flat roof (solid, no AA)
        pygame.draw.rect(surf, roof_d, (cx - 26, 28, 52, 4))
        pygame.draw.rect(surf, outline, (cx - 26, 28, 52, 4), 1)
    elif kind == "temple":
        # temple with a spire — a tall spire over a pillared hall.
        # Hall walls — 2-tone dithered fill (no AA).
        wall = px_dither_surf(48, 24, base_l, base_d)
        clip_to_rect(wall, pygame.Rect(0, 0, 48, 24))
        surf.blit(wall, (cx - 24, 36))
        pygame.draw.rect(surf, outline, (cx - 24, 36, 48, 24), 2)
        # four pillars (solid dithered blocks, no AA)
        for px in (cx - 20, cx - 8, cx + 4):
            pillar = px_dither_surf(6, 22, (220, 215, 210), (150, 145, 140))
            clip_to_rect(pillar, pygame.Rect(0, 0, 6, 22))
            surf.blit(pillar, (px, 36))
            pygame.draw.rect(surf, outline, (px, 36, 6, 22), 2)
        # door (solid, no AA)
        pygame.draw.rect(surf, (60, 40, 20), (cx - 6, 42, 12, 18))
        pygame.draw.rect(surf, outline, (cx - 6, 42, 12, 18), 2)
        # spire — 2-tone dithered fill clipped to a tall triangle (no AA)
        spire_pts = [(cx - 10, 36), (cx + 10, 36), (cx, 4)]
        xs = [p[0] for p in spire_pts]; ys = [p[1] for p in spire_pts]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        sg2 = px_dither_surf(maxx - minx, maxy - miny, (240, 230, 200), (170, 140, 90))
        m = pygame.Surface((maxx - minx, maxy - miny), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                           [(p[0] - minx, p[1] - miny) for p in spire_pts])
        sg2.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(sg2, (minx, miny))
        pygame.draw.polygon(surf, outline, spire_pts, 2)
        # spire cap orb — 2-tone dithered fill clipped to a circle (no AA)
        orb = px_dither_surf(12, 12, (255, 240, 180), (200, 150, 40))
        clip_to_circle(orb, (6, 6), 5)
        surf.blit(orb, (cx - 6, 0))
        pygame.draw.circle(surf, outline, (cx, 6), 5, 2)
        # step base (solid, no AA)
        pygame.draw.rect(surf, shade(base_d, 0.8), (cx - 26, 58, 52, 4))
        pygame.draw.rect(surf, outline, (cx - 26, 58, 52, 4), 1)
    else:
        # unknown kind — a plain dithered block (solid, no AA) so the caller
        # never gets a blank surface
        blk = px_dither_surf(44, 36, base_l, base_d)
        clip_to_rect(blk, pygame.Rect(0, 0, 44, 36))
        surf.blit(blk, (cx - 22, 24))
        pygame.draw.rect(surf, outline, (cx - 22, 24, 44, 36), 2)

def draw_drop(surf, kind, color=None):
    """A ~16x16 ground loot drop sprite, per-kind. Pixel-art: dithered fills
    clipped to shape, solid palette fills, no AA. kind is one of:
    gold / potion / shard / equipment. color is an optional (r,g,b) tint so
    the same drop can be re-tinted per rarity; defaults per kind below.
    """
    cx, cy = 8, 8
    outline = (30, 26, 30)

    if kind == "gold":
        # a coin — 2-tone dithered fill clipped to a circle + a $ sheen (no AA)
        gold_l = color if color is not None else (255, 220, 90)
        gold_d = shade(gold_l, 0.55)
        coin = px_dither_surf(14, 14, gold_l, gold_d)
        clip_to_circle(coin, (7, 7), 7)
        surf.blit(coin, (1, 1))
        pygame.draw.circle(surf, outline, (cx, cy), 7, 2)
        # $ sheen (solid block, no AA)
        pygame.draw.rect(surf, (255, 250, 200), (cx - 1, cy - 4, 2, 8))
        pygame.draw.rect(surf, (255, 250, 200), (cx - 3, cy - 2, 6, 2))
        pygame.draw.rect(surf, (255, 250, 200), (cx - 3, cy + 2, 6, 2))
    elif kind == "potion":
        # a small bottle — dithered liquid body + cork + shine (no AA)
        pot_l = color if color is not None else (220, 80, 90)
        pot_d = shade(pot_l, 0.55)
        # cork (solid, no AA)
        pygame.draw.rect(surf, (180, 130, 70), (cx - 2, 0, 4, 3))
        pygame.draw.rect(surf, outline, (cx - 2, 0, 4, 3), 1)
        # body — 2-tone dithered fill clipped to a rounded rect (no AA)
        body = px_dither_surf(10, 12, pot_l, pot_d)
        clip_to_rect(body, pygame.Rect(0, 0, 10, 12), border_radius=3)
        surf.blit(body, (cx - 5, 3))
        pygame.draw.rect(surf, outline, (cx - 5, 3, 10, 12), 2, border_radius=3)
        # shine (solid block, no AA)
        pygame.draw.rect(surf, (255, 255, 255), (cx - 3, 5, 2, 4))
    elif kind == "shard":
        # a crystal shard — 2-tone dithered fill clipped to a diamond + glow (no AA)
        shard_l = color if color is not None else (180, 220, 255)
        shard_d = shade(shard_l, 0.45)
        # glow (chunky block, no AA soft-glow)
        pygame.draw.circle(surf, (*shade(shard_l, 1.1), 0), (cx, cy), 8)
        glow = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*shard_l, 70), (8, 8), 8)
        surf.blit(glow, (0, 0))
        # diamond — 2-tone dithered fill clipped to a diamond (no AA)
        diam_pts = [(cx, 1), (cx + 6, cy), (cx, 15), (cx - 6, cy)]
        xs = [p[0] for p in diam_pts]; ys = [p[1] for p in diam_pts]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        dg = px_dither_surf(maxx - minx, maxy - miny, shard_l, shard_d)
        m = pygame.Surface((maxx - minx, maxy - miny), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                           [(p[0] - minx, p[1] - miny) for p in diam_pts])
        dg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(dg, (minx, miny))
        pygame.draw.polygon(surf, outline, diam_pts, 2)
        # core shine (solid block, no AA)
        pygame.draw.rect(surf, (255, 255, 255), (cx - 1, cy - 3, 2, 6))
    elif kind == "equipment":
        # a gear/sword — a small sword icon (solid + dithered, no AA)
        eq_l = color if color is not None else (220, 225, 240)
        eq_d = shade(eq_l, 0.6)
        # blade — 2-tone dithered fill clipped to a blade polygon (no AA)
        blade_pts = [(cx, 1), (cx + 2, 1), (cx + 2, 11), (cx, 14), (cx - 2, 11)]
        xs = [p[0] for p in blade_pts]; ys = [p[1] for p in blade_pts]
        minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
        bg2 = px_dither_surf(maxx - minx, maxy - miny, eq_l, eq_d)
        m = pygame.Surface((maxx - minx, maxy - miny), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                           [(p[0] - minx, p[1] - miny) for p in blade_pts])
        bg2.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(bg2, (minx, miny))
        pygame.draw.polygon(surf, outline, blade_pts, 1)
        # crossguard (solid, no AA)
        pygame.draw.rect(surf, (140, 100, 50), (cx - 4, 10, 8, 2))
        pygame.draw.rect(surf, outline, (cx - 4, 10, 8, 2), 1)
        # grip (solid, no AA)
        pygame.draw.rect(surf, (90, 60, 30), (cx - 1, 12, 2, 4))
        pygame.draw.rect(surf, outline, (cx - 1, 12, 2, 4), 1)
    else:
        # unknown kind — a plain dithered disc (solid, no AA) so the caller
        # never gets a blank surface
        disc = px_dither_surf(12, 12, (200, 200, 200), (120, 120, 120))
        clip_to_circle(disc, (6, 6), 6)
        surf.blit(disc, (cx - 6, cy - 6))
        pygame.draw.circle(surf, outline, (cx, cy), 6, 2)

def draw_star(surf, cx, cy, r, points, color, inner_color):
    pts = []
    for i in range(points * 2):
        ang = -math.pi / 2 + math.pi * i / points
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, (40, 30, 20), pts, 2)

# ---------------------------------------------------------------------------
# Master build
# ---------------------------------------------------------------------------
ENEMIES = [
    # LoL jungle mobs (open-world trash) — palette = (main, accent, dark)
    ("Razorbeaks",    "wind",   ((120, 220, 140), (200, 255, 200), (40, 120, 60))),
    ("Krugs",         "fire",   ((120, 160, 80),  (180, 220, 120), (40, 80, 30))),
    ("Voidlings",     "dark",   ((90, 60, 120),   (160, 120, 200), (30, 20, 40))),
    ("FallenKnight",  "light",  ((230, 230, 220), (255, 255, 250), (80, 80, 90))),
    ("MurkWolves",    "wind",   ((120, 120, 130), (180, 180, 190), (40, 40, 50))),
    ("CrimsonRaptor", "fire",   ((140, 100, 70),  (200, 160, 100), (60, 40, 30))),
    ("Gromp",         "water",  ((150, 140, 110), (200, 190, 160), (70, 60, 50))),
    ("Wraiths",       "dark",   ((120, 130, 180), (180, 200, 240), (40, 50, 80))),
    ("Raptors",       "fire",   ((200, 80, 50),   (255, 160, 90),  (80, 20, 10))),
    ("VoidHound",     "dark",   ((120, 160, 110), (180, 220, 170), (40, 70, 50))),
    # LoL villain bosses
    ("Sylas",         "dark",   ((120, 130, 180), (180, 200, 240), (40, 50, 80))),
    ("Swain",         "fire",   ((180, 80, 60),   (240, 180, 120), (90, 30, 20))),
    ("Lissandra",     "water",  ((140, 200, 240), (200, 230, 255), (40, 90, 140))),
    ("Mordekaiser",   "dark",   ((120, 40, 60),   (200, 80, 120),  (40, 10, 20))),
    ("Viego",         "dark",   ((120, 160, 110), (180, 220, 170), (40, 70, 50))),
    ("Baron",         "dark",   ((180, 60, 40),   (255, 180, 80),  (90, 20, 10))),
]

SKILLS = [
    ("fire_slash", "fire", "slash"), ("fire_bolt", "fire", "bolt"),
    ("inferno", "fire", "aoe"), ("meteor", "fire", "aoe"),
    ("water_bolt", "water", "bolt"), ("water_heal", "water", "heal"),
    ("tidal_wave", "water", "aoe"),
    ("wind_arrow", "wind", "arrow"), ("wind_aoe", "wind", "aoe"),
    ("swift_buff", "wind", "buff"),
    ("light_slash", "light", "slash"), ("light_heal", "light", "heal"),
    ("blessing", "light", "shield"),
    ("revive", "light", "heal"), ("light_hymn", "light", "heal"),
    ("dark_bolt", "dark", "bolt"), ("dark_curse", "dark", "curse"),
    ("dark_aoe", "dark", "aoe"), ("shield_ward", "dark", "shield"),
    ("void_nova", "dark", "aoe"),
    ("basic_attack", "fire", "slash"),
    # --- new skills (Phase B) ---
    ("fire_strike", "fire", "slash"), ("phoenix", "fire", "heal"),
    ("frost_nova", "water", "aoe"), ("tide_shield", "water", "shield"),
    ("gust", "wind", "aoe"), ("evasion", "wind", "buff"),
    ("sanctuary", "light", "heal"), ("judgement_aoe", "light", "aoe"),
    ("soul_drain", "dark", "bolt"), ("death_coil", "dark", "aoe"),
    # --- new skills (Phase C) ---
    ("rupture", "dark", "curse"), ("taunt_skill", "light", "shield"),
    ("reflect_ward", "water", "shield"),
    # --- new skill kinds (v2 A3: summon / beam / trap) — added here so the
    # global assets/skills/{id}.png is generated for skills that appear in a
    # hero's kit but were missing from the SKILLS list (the per-hero bundle
    # loop uses SKILL_KIND below to look up the kind).
    ("fire_summon", "fire", "summon"),
    ("light_beam", "light", "beam"), ("dark_trap", "dark", "trap"),
    ("fire_curse", "fire", "curse"), ("tsunami", "water", "aoe"),
    ("tempest", "wind", "aoe"),
    # boss ultimates
    ("hellfire", "fire", "aoe"), ("abyssal_wave", "dark", "aoe"),
    ("frost_cataclysm", "water", "aoe"), ("storm_of_embers", "fire", "aoe"),
]

# SKILL_KIND — a {skill_id: kind} map for the per-hero bundle loop. The
# SKILLS list is the canonical (id, element, kind) for the global icons; this
# map lets the per-hero loop look up the visual kind for a skill id from
# SKILLS_DB without a `kind` field. Fallback to "orb" for skills not listed.
SKILL_KIND = {name: kind for name, el, kind in SKILLS}

def main():
    print("Generating Aetheria assets...")
    # NOTE: per-champion character bundles (sprite.png / portrait.jpg / icon.png
    # / skills/*.png / skins/*.jpg) are built by build_champions.py from the
    # crawled LoL data, NOT by this loop. This main() generates only the shared
    # non-champion art: enemy sprites, the 4 boss-ult skill icons, backgrounds,
    # item icons, UI frames, terrain tiles, landmarks, village buildings, and
    # ground-loot drops.
    # enemies
    for name, el, pal in ENEMIES:
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        draw_enemy(s, name, pal)
        pygame.image.save(s, os.path.join(ASSET_DIR, "enemies", f"{name}.png"))
    print(f"  {len(ENEMIES)} enemies")

    # global skill icons — ONLY boss ultimates (the 4 skills no hero has in
    # their kit). Per-hero bundle copies are generated above; these neutral
    # globals are the fallback load_skill_icon reaches for boss ultimates.
    boss_ults = [s for s in SKILLS if s[0] in
                 ("hellfire", "abyssal_wave", "frost_cataclysm", "storm_of_embers")]
    for name, el, kind in boss_ults:
        s = pygame.Surface((128, 128), pygame.SRCALPHA)
        draw_skill_icon(s, name, el, kind)
        pygame.image.save(s, os.path.join(ASSET_DIR, "skills", f"{name}.png"))
    print(f"  {len(boss_ults)} boss-ult skill icons")

    # backgrounds — only the two that the game actually loads (title + shop).
    # The battle_* and map backgrounds were drawn programmatically by the
    # scenes and never reached by load_bg, so they are no longer generated.
    make_title_bg(os.path.join(ASSET_DIR, "backgrounds", "title.png"))
    make_shop_bg(os.path.join(ASSET_DIR, "backgrounds", "shop.png"))
    print("  backgrounds")

    # items
    make_items()
    print("  item icons")

    # ui — only the rarity frames are loaded by load_ui; the banner / button /
    # cursor / element / gem / gold / panel / star sprites were all drawn
    # programmatically by the scenes and never reached by load_ui, so they are
    # no longer generated.
    make_ui()
    print("  UI elements")

    # v2 terrain tiles — one neutral water + one bridge (biome tinting happens
    # at draw time in C3, so a single tile per kind is shipped here).
    for name in ("water", "bridge"):
        s = pygame.Surface((TILE_PX, TILE_PX), pygame.SRCALPHA)
        if name == "water":
            draw_water_tile(s)
        else:
            draw_bridge_tile(s)
        pygame.image.save(s, os.path.join(ASSET_DIR, "terrain", f"{name}.png"))
    print("  terrain tiles")

    # v2 landmarks — one sprite per kind (statue / ruin / shrine / obelisk /
    # rift_anchor). The accent is a neutral gold so the same sprite reads in
    # any biome; C3 re-tints by passing an element color to draw_landmark.
    for kind in ("statue", "ruin", "shrine", "obelisk", "rift_anchor"):
        s = pygame.Surface((80, 80), pygame.SRCALPHA)
        draw_landmark(s, kind)
        pygame.image.save(s, os.path.join(ASSET_DIR, "landmarks", f"{kind}.png"))
    print("  landmarks")

    # v2 village buildings — one sprite per kind (house / shop / temple).
    for kind in ("house", "shop", "temple"):
        s = pygame.Surface((60, 60), pygame.SRCALPHA)
        draw_village_building(s, kind)
        pygame.image.save(s, os.path.join(ASSET_DIR, "villages", f"{kind}.png"))
    print("  village buildings")

    # v2 ground loot drops — one sprite per kind (gold / potion / shard /
    # equipment). C2 re-tints by passing a rarity color to draw_drop.
    for kind in ("gold", "potion", "shard", "equipment"):
        s = pygame.Surface((16, 16), pygame.SRCALPHA)
        draw_drop(s, kind)
        pygame.image.save(s, os.path.join(ASSET_DIR, "drops", f"{kind}.png"))
    print("  drop sprites")

    print("Done. Assets saved to", ASSET_DIR)

if __name__ == "__main__":
    main()
