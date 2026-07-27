"""
Aetheria Gacha - Asset Generator
Procedurally draws and saves all game assets (characters, enemies, skills,
backgrounds, UI) as PNG files so the game never depends on external art.

Run:  python3 generate_assets.py
"""
import os
import math
import random
import numpy as np
import pygame

SEED = 1337
random.seed(SEED)

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
for sub in ["characters", "enemies", "skills", "backgrounds", "ui", "portraits", "effects", "items"]:
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

def vgrad(surface, top, bottom):
    w, h = surface.get_size()
    for y in range(h):
        t = y / max(1, h - 1)
        pygame.draw.line(surface, lerp_color(top, bottom, t), (0, y), (w, y))

def rgrad(surface, center, inner, outer, max_r):
    w, h = surface.get_size()
    cx, cy = center
    for r in range(int(max_r), 0, -1):
        t = r / max_r
        pygame.draw.circle(surface, lerp_color(inner, outer, t), (cx, cy), r)

def aa_circle(surf, color, pos, radius):
    pygame.draw.circle(surf, color, pos, radius)

def aa_polygon(surf, color, points):
    pygame.draw.polygon(surf, color, points)

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

def hgrad_surf(w, h, left, right, a_left=255, a_right=255):
    """Horizontal RGBA gradient (left->right)."""
    t = np.linspace(0.0, 1.0, max(2, w))[None, :]
    arr = np.empty((h, w, 4), np.uint8)
    arr[..., 0] = (left[0] + (right[0] - left[0]) * t)
    arr[..., 1] = (left[1] + (right[1] - left[1]) * t)
    arr[..., 2] = (left[2] + (right[2] - left[2]) * t)
    arr[..., 3] = (a_left + (a_right - a_left) * t)
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

def add_blit(surf, src, pos):
    """Blit a surface additively (great for glows/highlights over art)."""
    surf.blit(src, pos, special_flags=pygame.BLEND_RGBA_ADD)

# ---------------------------------------------------------------------------
# Chibi character sprite
# ---------------------------------------------------------------------------
HAIR_STYLES = ["spiky", "long", "short", "twin", "hood",
               "ponytail", "bob", "curly", "mohawk", "braided"]

def draw_chibi(surf, element, body_color, hair_color, accent,
               weapon="sword", hair_style="spiky", eye_color=(40, 40, 60),
               expression="neutral", eye_shape="round", skin=None):
    """Draw a polished chibi hero centered on surf (256x256)."""
    cx, cy = 128, 150
    outline = (30, 26, 40)
    body_light = shade(body_color, 1.22)
    body_dark = shade(body_color, 0.62)
    body_vdark = shade(body_color, 0.42)
    accent_dark = shade(accent, 0.65)
    accent_light = shade(accent, 1.25)
    hair_light = shade(hair_color, 1.28)
    hair_dark = shade(hair_color, 0.55)
    if skin is None:
        skin = (255, 226, 200)
        skin_light = (255, 240, 222)
        skin_dark = (224, 178, 158)
    else:
        skin_light = shade(skin, 1.08)
        skin_dark = shade(skin, 0.78)
    main_el, light_el, dark_el = ELEMENT_COLORS[element]

    # ground shadow (soft, elongated)
    shadow = pygame.Surface((190, 50), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
    surf.blit(shadow, (cx - 95, 234))

    # element aura glow behind the body (three-layer: outer halo + mid glow + tight core)
    aura = soft_glow(200, 200, light_el, 48, center=(100, 100), radius=100, falloff=1.6)
    surf.blit(aura, (cx - 100, 62))
    aura2 = soft_glow(144, 144, light_el, 64, center=(72, 72), radius=72, falloff=1.35)
    surf.blit(aura2, (cx - 72, 94))
    aura3 = soft_glow(96, 96, light_el, 45, center=(48, 48), radius=48, falloff=1.2)
    surf.blit(aura3, (cx - 48, 114))
    # element-specific particles in the aura (fire=embers, water=bubbles, wind=leaves, light=sparkles, dark=motes)
    # NOTE: use a stable, salt-free hash so the particle layout is reproducible
    # across runs (Python's built-in hash() is salted per process via PYTHONHASHSEED).
    rng = random.Random(sum(ord(c) for c in element) * 1000003 + 17)
    for _ in range(6 if element in ("fire", "light") else (5 if element == "dark" else 4)):
        px = cx + rng.uniform(-50, 50)
        py = cy + rng.uniform(-30, 60)
        pr = rng.uniform(1.5, 4.0)
        if element == "fire":
            pa = rng.randint(120, 200)
            pygame.draw.circle(surf, (*light_el, pa), (int(px), int(py)), int(pr))
        elif element == "water":
            pa = rng.randint(100, 180)
            pygame.draw.circle(surf, (*light_el, pa), (int(px), int(py)), int(pr))
            pygame.draw.circle(surf, (255, 255, 255, pa // 2), (int(px - pr * 0.3), int(py - pr * 0.3)), max(1, int(pr * 0.4)))
        elif element == "wind":
            pa = rng.randint(80, 160)
            lx = px + rng.uniform(-6, 6)
            ly = py + rng.uniform(-3, 3)
            pygame.draw.line(surf, (*light_el, pa), (int(px), int(py)), (int(lx), int(ly)), max(1, int(pr)))
        elif element == "light":
            pa = rng.randint(130, 220)
            pygame.draw.circle(surf, (255, 255, 255, pa), (int(px), int(py)), max(1, int(pr * 0.6)))
            # 4-point star sparkle
            for ang2 in (0, math.pi / 2, math.pi, 3 * math.pi / 2):
                ex2 = px + math.cos(ang2) * pr * 2
                ey2 = py + math.sin(ang2) * pr * 2
                pygame.draw.line(surf, (255, 255, 255, pa // 2), (int(px), int(py)), (int(ex2), int(ey2)), 1)
        elif element == "dark":
            pa = rng.randint(60, 140)
            pygame.draw.circle(surf, (*light_el, pa), (int(px), int(py)), int(pr))

    # cape/cloak flowing behind the body (shaded, with a center highlight fold)
    cape_dark = shade(body_color, 0.48)
    cape = [(cx - 34, 150), (cx - 60, 252), (cx - 44, 232),
            (cx - 30, 248), (cx - 16, 236), (cx, 248),
            (cx + 16, 236), (cx + 30, 248), (cx + 44, 232),
            (cx + 60, 252), (cx + 34, 150)]
    pygame.draw.polygon(surf, cape_dark, cape)
    # cape gradient (top lighter -> bottom darker) clipped to the cape shape
    cg = vgrad_surf(120, 110, shade(body_color, 0.92), cape_dark)
    cg2 = pygame.Surface((120, 110), pygame.SRCALPHA)
    pygame.draw.polygon(cg2, (255, 255, 255, 255),
                        [(p[0] - (cx - 60), p[1] - 142) for p in cape])
    cg.blit(cg2, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(cg, (cx - 60, 142))
    pygame.draw.polygon(surf, outline, cape, 2)
    # cape inner highlight streak
    cape_hi = [(cx - 8, 152), (cx - 6, 240), (cx + 6, 240), (cx + 8, 152)]
    pygame.draw.polygon(surf, shade(body_color, 0.75), cape_hi)

    # legs (shaded) + boots
    leg_y = 210
    for sx in (-26, 6):
        lg = diag_grad_surf(20, 30, body_light, body_dark)
        clip_to_rect(lg, pygame.Rect(0, 0, 20, 30))
        surf.blit(lg, (cx + sx, leg_y))
        pygame.draw.rect(surf, outline, (cx + sx, leg_y, 20, 30), 2, border_radius=8)
    for sx in (-28, 4):
        bg = vgrad_surf(24, 12, accent_light, accent_dark)
        clip_to_rect(bg, pygame.Rect(0, 0, 24, 12))
        surf.blit(bg, (cx + sx, leg_y + 22))
        pygame.draw.rect(surf, outline, (cx + sx, leg_y + 22, 24, 12), 2, border_radius=6)
        pygame.draw.rect(surf, accent_dark, (cx + sx, leg_y + 30, 24, 4), border_radius=3)

    # body / torso with diagonal shading (left-lit, right-shaded) + fabric fold lines
    torso = pygame.Rect(cx - 36, 150, 72, 70)
    bodyg = diag_grad_surf(72, 70, body_light, body_dark)
    clip_to_rect(bodyg, pygame.Rect(0, 0, 72, 70), border_radius=18)
    surf.blit(bodyg, torso.topleft)
    # fabric fold lines (subtle vertical curves for cloth drape)
    for fx in (-16, -2, 12):
        fold_alpha = 35 if fx < 0 else 25
        fold = pygame.Surface((4, 62), pygame.SRCALPHA)
        pygame.draw.line(fold, (*body_vdark, fold_alpha), (2, 0), (2, 62), 3)
        surf.blit(fold, (cx + fx, 154))
    # collar (accent triangle at the neck, with layered depth)
    pygame.draw.polygon(surf, shade(accent, 0.8), [(cx - 14, 150), (cx + 14, 150), (cx, 170)])
    pygame.draw.polygon(surf, accent, [(cx - 12, 151), (cx + 12, 151), (cx, 168)])
    pygame.draw.polygon(surf, accent_light, [(cx - 10, 152), (cx - 2, 152), (cx - 6, 163)])
    pygame.draw.polygon(surf, outline, [(cx - 14, 150), (cx + 14, 150), (cx, 170)], 2)
    # right-side core shadow (ambient occlusion feel)
    sh = pygame.Surface((28, 66), pygame.SRCALPHA)
    pygame.draw.rect(sh, (*body_vdark, 130), sh.get_rect(), border_radius=14)
    surf.blit(sh, (cx + 8, 152))
    # left rim light (warm edge light, wider and softer)
    rim = soft_glow(20, 70, body_light, 100, center=(10, 8), radius=11, falloff=1.25)
    surf.blit(rim, (cx - 36, 152))
    # subtle under-shadow (ambient occlusion at the bottom of the torso)
    us = pygame.Surface((64, 10), pygame.SRCALPHA)
    pygame.draw.rect(us, (*body_vdark, 80), us.get_rect(), border_radius=6)
    surf.blit(us, (cx - 32, 210))
    pygame.draw.rect(surf, outline, torso, 3, border_radius=18)
    # belt (shaded)
    beltg = hgrad_surf(72, 10, accent_dark, shade(accent_dark, 0.6))
    clip_to_rect(beltg, pygame.Rect(0, 0, 72, 10))
    surf.blit(beltg, (cx - 36, 198))
    pygame.draw.rect(surf, outline, (cx - 36, 198, 72, 10), 2)
    # belt buckle
    pygame.draw.rect(surf, accent_light, (cx - 6, 199, 12, 8), border_radius=2)
    pygame.draw.rect(surf, outline, (cx - 6, 199, 12, 8), 1, border_radius=2)
    # chest emblem (element gem with depth)
    gemg = radial_grad_surf(26, 26, light_el, dark_el, center=(11, 9), radius=13)
    clip_to_circle(gemg, (13, 13), 13)
    surf.blit(gemg, (cx - 13, 165))
    pygame.draw.circle(surf, accent, (cx, 178), 11)
    pygame.draw.circle(surf, light_el, (cx - 3, 175), 4)
    pygame.draw.circle(surf, (255, 255, 255), (cx - 5, 173), 2)
    pygame.draw.circle(surf, outline, (cx, 178), 13, 2)

    # arms (shaded)
    # back arm (darker)
    bg_arm = vgrad_surf(18, 50, body_dark, body_vdark)
    clip_to_rect(bg_arm, pygame.Rect(0, 0, 18, 50))
    surf.blit(bg_arm, (cx - 50, 156))
    pygame.draw.rect(surf, outline, (cx - 50, 156, 18, 50), 2, border_radius=9)
    # front arm
    fg_arm = diag_grad_surf(18, 50, body_light, body_dark)
    clip_to_rect(fg_arm, pygame.Rect(0, 0, 18, 50))
    surf.blit(fg_arm, (cx + 32, 156))
    pygame.draw.rect(surf, outline, (cx + 32, 156, 18, 50), 2, border_radius=9)
    # hands (with soft shading)
    for hx, base in ((cx - 41, skin_dark), (cx + 41, skin)):
        hg = radial_grad_surf(22, 22, skin_light, base, center=(8, 8), radius=11)
        clip_to_circle(hg, (11, 11), 11)
        surf.blit(hg, (hx - 11, 197))
        pygame.draw.circle(surf, outline, (hx, 208), 10, 2)

    # head (skin with soft spherical shading + subsurface-approximation rim)
    head_r = 46
    # base skin with warm offset lighting from upper-left (per-hero skin tone)
    headg = radial_grad_surf(head_r * 2, head_r * 2, skin_light, skin_dark,
                             center=(head_r - 18, head_r - 18), radius=head_r + 3)
    clip_to_circle(headg, (head_r, head_r), head_r)
    surf.blit(headg, (cx - head_r, 110 - head_r))
    # warm subsurface glow on the left edge (light passes through the skin edge)
    subsurf = soft_glow(head_r * 2, head_r * 2, (255, 200, 170), 70,
                        center=(head_r + 8, head_r), radius=head_r - 6, falloff=1.8)
    clip_to_circle(subsurf, (head_r, head_r), head_r)
    surf.blit(subsurf, (cx - head_r, 110 - head_r))
    # face core shadow (right side, cool ambient)
    fshade = pygame.Surface((head_r * 2, head_r * 2), pygame.SRCALPHA)
    pygame.draw.circle(fshade, (30, 40, 60, 55), (head_r, head_r), head_r)
    pygame.draw.circle(fshade, (0, 0, 0, 0), (head_r - 16, head_r), head_r - 4)
    surf.blit(fshade, (cx - head_r, 110 - head_r))
    # warm nose/cheek tint
    nose_warm = pygame.Surface((20, 14), pygame.SRCALPHA)
    pygame.draw.ellipse(nose_warm, (255, 180, 160, 45), nose_warm.get_rect())
    surf.blit(nose_warm, (cx - 10, 120))
    # cheek blush (soft, on both sides)
    blush = pygame.Surface((20, 12), pygame.SRCALPHA)
    pygame.draw.ellipse(blush, (255, 148, 165, 100), blush.get_rect())
    surf.blit(blush, (cx - 32, 120))
    surf.blit(blush, (cx + 12, 120))
    # small nose dot
    pygame.draw.circle(surf, (210, 160, 145), (cx, 122), 3)
    pygame.draw.circle(surf, outline, (cx, 122), 3, 1)
    pygame.draw.circle(surf, outline, (cx, 110), head_r, 3)

    # hair
    draw_hair(surf, cx, 110, head_r, hair_color, outline, hair_style, hair_light)

    # eyes (per-hero expression + eye shape for facial variety)
    draw_eyes(surf, cx, 112, eye_color, outline, element, expression, eye_shape)

    # weapon
    draw_weapon(surf, cx, cy, weapon, accent, outline, element)

def draw_hair(surf, cx, cy, r, color, outline, style, highlight=None):
    """Premium hair with specular band, strand texture, root shadow, tip highlights."""
    if highlight is None:
        highlight = shade(color, 1.2)
    shadow_col = shade(color, 0.65)
    dark_col = shade(color, 0.45)
    spec_col = shade(color, 1.45)  # bright specular for the hair shine band
    if style == "spiky":
        pts = []
        for i in range(11):  # more points for smoother silhouette
            ang = math.pi + math.pi * (i / 10)
            rr = r + (14 if i % 2 == 0 else -1)
            pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr * 0.92))
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, outline, pts, 3)
        # radial cap shading (light upper-left, darker lower-right)
        crown = radial_grad_surf(2 * r, 2 * r, highlight, dark_col,
                                 center=(r - 14, r - 14), radius=r + 6)
        clip_to_circle(crown, (r, r), r - 1)
        surf.blit(crown, (cx - r, cy - r))
        # specular band (a bright arc near the top-left of the hair)
        spec_band = pygame.Surface((2 * r, int(r * 0.5)), pygame.SRCALPHA)
        pygame.draw.arc(spec_band, (*spec_col, 130), (4, 0, 2 * r - 8, int(r * 0.5)), 0.4, 2.0, 5)
        pygame.draw.arc(spec_band, (*spec_col, 200), (4, 0, 2 * r - 8, int(r * 0.5)), 0.6, 1.8, 2)
        surf.blit(spec_band, (cx - r, cy - r + 4))
        # spiky strand highlights
        for i in (1, 3, 5, 7):
            ang = math.pi + math.pi * (i / 10)
            ex = cx + math.cos(ang) * (r + 8)
            ey = cy + math.sin(ang) * (r + 8) * 0.92
            sx2 = cx + math.cos(ang) * (r - 12)
            sy2 = cy + math.sin(ang) * (r - 12) * 0.92
            pygame.draw.line(surf, highlight, (sx2, sy2), (ex, ey), 2)
        # hairline fringe (a soft dark arc at the hairline)
        pygame.draw.arc(surf, (*dark_col, 100), (cx - r, cy - r, 2 * r, 2 * r), 0.2, math.pi - 0.2, 2)
        pygame.draw.arc(surf, outline, (cx - r, cy - r, 2 * r, 2 * r), 0.2, math.pi - 0.2, 3)
    elif style == "long":
        pygame.draw.circle(surf, color, (cx, cy - 6), r + 2)
        pygame.draw.rect(surf, color, (cx - r, cy - 10, 2 * r, 70), border_radius=24)
        # diagonal shading (light upper-left -> dark lower-right)
        lg = diag_grad_surf(2 * r, 70, highlight, dark_col)
        m = pygame.Surface((2 * r, 70), pygame.SRCALPHA)
        pygame.draw.rect(m, (255, 255, 255, 255), m.get_rect(), border_radius=24)
        lg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(lg, (cx - r, cy - 10))
        # specular band across the top/crown area
        spec = pygame.Surface((2 * r, int(r * 0.45)), pygame.SRCALPHA)
        pygame.draw.arc(spec, (*spec_col, 140), (4, 4, 2 * r - 8, int(r * 0.5) - 4), 0.5, 2.2, 5)
        pygame.draw.arc(spec, (*spec_col, 220), (4, 4, 2 * r - 8, int(r * 0.5) - 4), 0.7, 1.9, 2)
        surf.blit(spec, (cx - r, cy - r))
        pygame.draw.circle(surf, outline, (cx, cy - 6), r + 2, 3)
        pygame.draw.rect(surf, outline, (cx - r, cy - 10, 2 * r, 70), 3, border_radius=24)
        # tips with subtle gradient
        tips = pygame.Surface((2 * r, 28), pygame.SRCALPHA)
        for ty in range(28):
            ta = int(180 * (1 - ty / 28))
            pygame.draw.line(tips, (*dark_col, ta), (0, ty), (2 * r, ty))
        pygame.draw.rect(tips, (0, 0, 0, 0), tips.get_rect())
        surf.blit(tips, (cx - r, cy + 36))
        # more strand lines (varying thickness and opacity)
        for dx, s_alpha in ((-20, 60), (-12, 80), (-4, 70), (4, 55), (12, 65)):
            s = pygame.Surface((2, 56), pygame.SRCALPHA)
            pygame.draw.line(s, (*shade(color, 0.85), s_alpha), (1, 0), (1, 56), 1)
            surf.blit(s, (cx + dx, cy - 4))
    elif style == "short":
        pygame.draw.circle(surf, color, (cx, cy - 8), r)
        pygame.draw.rect(surf, color, (cx - r, cy - 8, 2 * r, 26), border_radius=18)
        # radial cap shading with specular band
        cap = radial_grad_surf(2 * r, 2 * r, highlight, dark_col,
                               center=(r - 14, r - 14), radius=r + 5)
        clip_to_circle(cap, (r, r), r)
        surf.blit(cap, (cx - r, cy - 8))
        # specular shine arc
        spec_short = pygame.Surface((2 * r, r), pygame.SRCALPHA)
        pygame.draw.arc(spec_short, (*spec_col, 150), (4, 2, 2 * r - 8, r - 4), 0.5, 2.0, 4)
        surf.blit(spec_short, (cx - r, cy - r + 4))
        # short strand lines (texture)
        for dx2 in (-14, -4, 6):
            s = pygame.Surface((1, 22), pygame.SRCALPHA)
            pygame.draw.line(s, (*shade(color, 0.85), 70), (0, 0), (0, 22), 1)
            surf.blit(s, (cx + dx2, cy - 6))
        # hairline shadow
        pygame.draw.arc(surf, (*dark_col, 90), (cx - r, cy - r, 2 * r, 2 * r), 0.3, math.pi - 0.3, 2)
        pygame.draw.circle(surf, outline, (cx, cy - 8), r, 3)
    elif style == "twin":
        pygame.draw.circle(surf, color, (cx, cy - 6), r)
        # specular on top
        pygame.draw.arc(surf, (*spec_col, 160), (cx - r, cy - r - 4, 2 * r, int(r * 0.7)), 0.4, 2.4, 4)
        pygame.draw.circle(surf, highlight, (cx - 8, cy - 12), r // 3)
        pygame.draw.circle(surf, outline, (cx, cy - 6), r, 3)
        for sx in (-1, 1):
            tx = cx + sx * (r + 6)
            # tail with gradient + specular band
            tailg = vgrad_surf(24, 44, highlight, dark_col)
            m = pygame.Surface((24, 44), pygame.SRCALPHA)
            pygame.draw.ellipse(m, (255, 255, 255, 255), m.get_rect())
            tailg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(tailg, (tx - 12, cy))
            # specular streak along the tail
            pygame.draw.line(surf, (*spec_col, 140), (tx, cy + 4), (tx, cy + 36), 2)
            pygame.draw.ellipse(surf, outline, (tx - 12, cy, 24, 44), 3)
            pygame.draw.circle(surf, color, (tx, cy + 4), 16)
            pygame.draw.circle(surf, outline, (tx, cy + 4), 16, 3)
            # ribbon tie with specular
            pygame.draw.circle(surf, shadow_col, (tx, cy + 2), 7)
            pygame.draw.circle(surf, highlight, (tx - 2, cy), 3)
            pygame.draw.circle(surf, (255, 255, 255), (tx - 3, cy - 1), 2)
            pygame.draw.circle(surf, outline, (tx, cy + 2), 7, 2)
    elif style == "hood":
        pygame.draw.circle(surf, color, (cx, cy - 4), r + 8)
        pygame.draw.polygon(surf, color, [(cx - r - 10, cy - 4), (cx + r + 10, cy - 4),
                                         (cx + r, cy + 40), (cx - r, cy + 40)])
        pygame.draw.circle(surf, outline, (cx, cy - 4), r + 8, 3)
        # hood diagonal shading (light upper-left -> dark lower-right) with texture folds
        hoodg = diag_grad_surf(2 * r + 20, 2 * r + 10, highlight, dark_col)
        m = pygame.Surface(hoodg.get_size(), pygame.SRCALPHA)
        pygame.draw.circle(m, (255, 255, 255, 255), (r + 10, r + 4), r + 8)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(0, r), (2 * r + 20, r), (2 * r + 10, 2 * r + 4 + 6), (10, 2 * r + 4 + 6)])
        hoodg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(hoodg, (cx - r - 10, cy - r - 4))
        # specular rim along the top arc of the hood
        pygame.draw.arc(surf, (*spec_col, 130), (cx - r - 6, cy - r - 4, 2 * r + 12, 2 * r), 0.3, 2.6, 3)
        # hood fold shading on the right (deeper)
        pygame.draw.polygon(surf, shadow_col, [(cx + r - 6, cy - 4), (cx + r + 10, cy - 4),
                                               (cx + r, cy + 40), (cx + r - 16, cy + 40)])
        # hood fabric folds (vertical cloth drape lines)
        for hfx in (-10, 0, 10):
            fold_a = 60 if hfx < 0 else 40
            fold_l = pygame.Surface((3, 46), pygame.SRCALPHA)
            pygame.draw.line(fold_l, (*dark_col, fold_a), (1, 0), (1, 46), 2)
            surf.blit(fold_l, (cx + hfx + 6, cy - 2))
        # inner hood shadow on the face (darker, deeper)
        hood_shadow = pygame.Surface((2 * r, r), pygame.SRCALPHA)
        pygame.draw.ellipse(hood_shadow, (0, 0, 0, 100), hood_shadow.get_rect())
        surf.blit(hood_shadow, (cx - r, cy - 10))
    elif style == "ponytail":
        # base cap + a single tail high on the back of the head
        pygame.draw.circle(surf, color, (cx, cy - 6), r)
        cap = radial_grad_surf(2 * r, 2 * r, highlight, dark_col,
                               center=(r - 14, r - 14), radius=r + 5)
        clip_to_circle(cap, (r, r), r)
        surf.blit(cap, (cx - r, cy - 6))
        pygame.draw.arc(surf, (*spec_col, 150), (cx - r, cy - r - 6, 2 * r, int(r * 0.7)), 0.4, 2.0, 4)
        # the tail (a rounded strand hanging from the top-back)
        tx = cx + r - 6
        ty = cy - r
        tailg = vgrad_surf(22, 64, highlight, dark_col)
        m = pygame.Surface((22, 64), pygame.SRCALPHA)
        pygame.draw.rect(m, (255, 255, 255, 255), m.get_rect(), border_radius=11)
        tailg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(tailg, (tx - 11, ty))
        pygame.draw.rect(surf, outline, (tx - 11, ty, 22, 64), 3, border_radius=11)
        # hair tie band
        pygame.draw.rect(surf, shadow_col, (tx - 13, ty + 4, 26, 8), border_radius=4)
        pygame.draw.rect(surf, highlight, (tx - 12, ty + 5, 24, 3), border_radius=2)
        pygame.draw.circle(surf, outline, (cx, cy - 6), r, 3)
    elif style == "bob":
        # rounded cap that frames the face, chin-length blunt cut
        pygame.draw.circle(surf, color, (cx, cy - 4), r + 2)
        pygame.draw.rect(surf, color, (cx - r - 2, cy - 6, 2 * r + 4, 40), border_radius=20)
        bg = diag_grad_surf(2 * r + 4, 40, highlight, dark_col)
        m = pygame.Surface((2 * r + 4, 40), pygame.SRCALPHA)
        pygame.draw.rect(m, (255, 255, 255, 255), m.get_rect(), border_radius=20)
        bg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(bg, (cx - r - 2, cy - 6))
        spec = pygame.Surface((2 * r, int(r * 0.4)), pygame.SRCALPHA)
        pygame.draw.arc(spec, (*spec_col, 150), (4, 2, 2 * r - 8, int(r * 0.4) - 4), 0.5, 2.0, 4)
        surf.blit(spec, (cx - r, cy - r))
        # blunt-cut bottom edge highlight
        pygame.draw.line(surf, (*spec_col, 120), (cx - r, cy + 32), (cx + r, cy + 32), 2)
        for dx in (-r + 2, r - 4):
            s = pygame.Surface((3, 36), pygame.SRCALPHA)
            pygame.draw.line(s, (*shade(color, 0.85), 70), (1, 0), (1, 36), 2)
            surf.blit(s, (cx + dx, cy - 4))
        pygame.draw.circle(surf, outline, (cx, cy - 4), r + 2, 3)
        pygame.draw.rect(surf, outline, (cx - r - 2, cy - 6, 2 * r + 4, 40), 3, border_radius=20)
    elif style == "curly":
        # cloud-like rounded silhouette with curl bumps
        pygame.draw.circle(surf, color, (cx, cy - 4), r + 2)
        for bx, by, br in ((-r + 2, -r + 4, 14), (r - 4, -r + 6, 13),
                           (-r + 14, -r - 4, 12), (r - 14, -r - 2, 13),
                           (0, -r - 6, 13)):
            pygame.draw.circle(surf, color, (cx + bx, cy + by), br)
        cap = radial_grad_surf(2 * r, 2 * r, highlight, dark_col,
                               center=(r - 14, r - 14), radius=r + 6)
        clip_to_circle(cap, (r, r), r)
        surf.blit(cap, (cx - r, cy - 4))
        pygame.draw.arc(surf, (*spec_col, 140), (cx - r, cy - r - 4, 2 * r, int(r * 0.6)), 0.4, 2.0, 4)
        pygame.draw.circle(surf, outline, (cx, cy - 4), r + 2, 3)
    elif style == "mohawk":
        # shaved sides + central spiky ridge
        pygame.draw.circle(surf, shade(color, 0.72), (cx, cy - 2), r - 6)
        pts = [(cx - 12, cy - 4)]
        for i in range(7):
            x = cx - 12 + i * 4
            pts.append((x, cy - r - 4 if i % 2 == 0 else cy - 8))
        pts.append((cx + 12, cy - 4))
        pygame.draw.polygon(surf, color, pts)
        # lighter band down the center of the ridge
        pygame.draw.polygon(surf, shade(color, 1.25), [(p[0], p[1] + 1) for p in pts])
        for i in range(7):
            x = cx - 12 + i * 4
            if i % 2 == 0:
                pygame.draw.line(surf, (*spec_col, 170), (x, cy - r - 4), (x, cy - 6), 1)
        pygame.draw.polygon(surf, outline, pts, 2)
        pygame.draw.circle(surf, outline, (cx, cy - 2), r - 6, 2)
    elif style == "braided":
        # base cap + two braids hanging on the sides
        pygame.draw.circle(surf, color, (cx, cy - 6), r)
        cap = radial_grad_surf(2 * r, 2 * r, highlight, dark_col,
                               center=(r - 14, r - 14), radius=r + 5)
        clip_to_circle(cap, (r, r), r)
        surf.blit(cap, (cx - r, cy - 6))
        pygame.draw.arc(surf, (*spec_col, 150), (cx - r, cy - r - 4, 2 * r, int(r * 0.6)), 0.4, 2.0, 4)
        pygame.draw.circle(surf, outline, (cx, cy - 6), r, 3)
        # two side braids: a stack of rounded segments
        for sx in (-1, 1):
            bx = cx + sx * (r - 2)
            for seg in range(4):
                by = cy - 2 + seg * 12
                pygame.draw.circle(surf, color, (bx, by), 8)
                pygame.draw.line(surf, shade(color, 0.6), (bx - 7, by), (bx + 7, by), 2)
            # tail tie + tip
            pygame.draw.circle(surf, shadow_col, (bx, cy - 4), 6)
            pygame.draw.circle(surf, highlight, (bx - 2, cy - 6), 3)
            pygame.draw.circle(surf, outline, (bx, cy - 4), 6, 2)

def draw_eyes(surf, cx, cy, color, outline, element, expression="neutral", eye_shape="round"):
    # Premium anime eyes with upper eyelid shadow, bottom lid, catchlights + lashes.
    # eye_shape varies the eye geometry (round/sharp/wide/half) so heroes of the
    # same element no longer share identical eyes; expression drives eyebrows + mouth.
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
        # white sclera with soft shading
        scl = radial_grad_surf(sw, sh, (252, 252, 255), (218, 222, 235),
                               center=(sw // 2 - 2, sh // 2 - 3), radius=max(8, sw // 2))
        m = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(m, (255, 255, 255, 255), m.get_rect())
        scl.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(scl, (cx + sx - sw // 2, cy - sh // 2))
        # upper eyelid shadow (dark gradient at top of eye)
        lid_shadow = pygame.Surface((sw, 8), pygame.SRCALPHA)
        for yy in range(8):
            a = int(80 * (1 - yy / 8))
            pygame.draw.line(lid_shadow, (0, 0, 0, a), (0, yy), (sw, yy))
        surf.blit(lid_shadow, (cx + sx - sw // 2, cy - sh // 2))
        # iris: the hero's personal eye color drives the bright center; the
        # element shows only as a faint outer rim (was: element-tinted center).
        iris = radial_grad_surf(iw, ih, shade(color, 1.25), shade(color, 0.4),
                                center=(iw // 2 - 1, ih // 2 - 2), radius=max(6, iw // 2))
        m2 = pygame.Surface((iw, ih), pygame.SRCALPHA)
        pygame.draw.ellipse(m2, (255, 255, 255, 255), m2.get_rect())
        iris.blit(m2, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(iris, (cx + sx - iw // 2, cy - ih // 2 + lid_off))
        # faint element-tinted outer ring (keeps the elemental theme)
        pygame.draw.ellipse(surf, shade(light_el, 0.9),
                            (cx + sx - iw // 2 - 1, cy - ih // 2 + lid_off - 1, iw + 2, ih + 2), 1)
        # iris texture rings (subtle concentric arcs, kept within the iris)
        for ir in (3, 5):
            if ir * 2 + 2 <= iw:
                pygame.draw.ellipse(surf, shade(color, 0.35),
                                    (cx + sx - ir, cy - 2 - ir // 2 + lid_off, ir * 2, ir * 2 + 2), 1)
        # pupil (dark)
        pygame.draw.ellipse(surf, (10, 8, 18),
                            (cx + sx - pw // 2, cy - ph // 2 + lid_off, pw, ph))
        # bottom eyelid line
        pygame.draw.arc(surf, shade(outline, 0.7),
                        (cx + sx - sw // 2 - 1, cy - 4 + lid_off, sw + 2, 12), 0.6, 2.5, 1)
        # upper eyelid thick line + lashes
        pygame.draw.arc(surf, outline,
                        (cx + sx - sw // 2, cy - 9 + lid_off, sw, 8), 3.1, 5.9, 3)
        # eyelash strokes on outer corner
        for la in (0.3, 0.5, 0.7):
            lx = cx + sx + 7 + la * 4
            ly = cy - 7 - la * 6 + lid_off
            pygame.draw.line(surf, outline, (int(lx), int(ly)), (int(lx - 4), int(ly + 4)), 1)
        # catchlights vary by eye_shape (breaks the identical-glare look)
        if eye_shape == "sharp":
            pygame.draw.circle(surf, (255, 255, 255), (cx + sx - 4, cy - 5 + lid_off), 3)
        elif eye_shape == "wide":
            pygame.draw.circle(surf, (255, 255, 255), (cx + sx - 4, cy - 5 + lid_off), 5)
            pygame.draw.circle(surf, (255, 255, 255), (cx + sx + 3, cy + 2 + lid_off), 3)
        else:
            pygame.draw.circle(surf, (255, 255, 255), (cx + sx - 4, cy - 5 + lid_off), 4)
            pygame.draw.circle(surf, (255, 255, 255), (cx + sx + 3, cy + 2 + lid_off), 2)
            pygame.draw.circle(surf, (255, 255, 255), (cx + sx + 1, cy - 3 + lid_off), 1)
    # eyebrows + mouth vary by expression (the most memorable part of a face)
    if expression == "fierce":
        # angled up-outward eyebrows + slightly open mouth
        pygame.draw.line(surf, outline, (cx - 20, cy - 16), (cx - 7, cy - 12), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx - 18, cy - 16), (cx - 9, cy - 12), 1)
        pygame.draw.line(surf, outline, (cx + 7, cy - 12), (cx + 20, cy - 16), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx + 9, cy - 12), (cx + 18, cy - 16), 1)
        pygame.draw.arc(surf, (175, 65, 75), (cx - 8, cy + 15, 16, 10), 3.0, 6.2, 2)
        pygame.draw.arc(surf, (255, 180, 180), (cx - 6, cy + 16, 12, 4), 3.2, 5.6, 1)
    elif expression == "gentle":
        # flat eyebrows + small smile
        pygame.draw.line(surf, outline, (cx - 20, cy - 14), (cx - 7, cy - 14), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx - 18, cy - 14), (cx - 9, cy - 14), 1)
        pygame.draw.line(surf, outline, (cx + 7, cy - 14), (cx + 20, cy - 14), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx + 9, cy - 14), (cx + 18, cy - 14), 1)
        pygame.draw.arc(surf, (175, 65, 75), (cx - 6, cy + 16, 12, 8), 3.6, 5.9, 2)
        pygame.draw.arc(surf, (255, 180, 180), (cx - 4, cy + 17, 8, 4), 3.7, 5.5, 1)
    elif expression == "stoic":
        # straight horizontal eyebrows + tiny straight mouth line
        pygame.draw.line(surf, outline, (cx - 20, cy - 14), (cx - 7, cy - 14), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx - 18, cy - 14), (cx - 9, cy - 14), 1)
        pygame.draw.line(surf, outline, (cx + 7, cy - 14), (cx + 20, cy - 14), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx + 9, cy - 14), (cx + 18, cy - 14), 1)
        pygame.draw.line(surf, (175, 65, 75), (cx - 4, cy + 18), (cx + 4, cy + 18), 2)
    elif expression == "sad":
        # downward eyebrows + downturned mouth
        pygame.draw.line(surf, outline, (cx - 20, cy - 12), (cx - 7, cy - 16), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx - 18, cy - 12), (cx - 9, cy - 16), 1)
        pygame.draw.line(surf, outline, (cx + 7, cy - 16), (cx + 20, cy - 12), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx + 9, cy - 16), (cx + 18, cy - 12), 1)
        pygame.draw.arc(surf, (175, 65, 75), (cx - 7, cy + 16, 14, 9), 4.6, 6.0, 2)
    else:  # neutral (current behavior, backward compatible)
        pygame.draw.line(surf, outline, (cx - 20, cy - 13), (cx - 7, cy - 15), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx - 18, cy - 13), (cx - 9, cy - 15), 1)
        pygame.draw.line(surf, outline, (cx + 7, cy - 15), (cx + 20, cy - 13), 3)
        pygame.draw.line(surf, shade(outline, 0.6), (cx + 9, cy - 15), (cx + 18, cy - 13), 1)
        pygame.draw.arc(surf, (175, 65, 75), (cx - 7, cy + 16, 14, 9), 3.4, 6.0, 2)
        pygame.draw.arc(surf, (255, 180, 180), (cx - 5, cy + 17, 10, 4), 3.5, 5.5, 1)

def draw_weapon(surf, cx, cy, weapon, accent, outline, element):
    _, light_el, _ = ELEMENT_COLORS[element]
    if weapon == "sword":
        # sword in right hand — premium metal with reflection bands + edge + fuller
        bx, by = cx + 50, 120
        bw, bh = 12, 82
        # metal base: alternating light/dark bands for realistic reflection
        blade = hgrad_surf(bw, bh, (225, 228, 240), (140, 145, 165))
        clip_to_rect(blade, pygame.Rect(0, 0, bw, bh))
        surf.blit(blade, (bx - 1, by - 72))
        # reflection bands (horizontal, simulating environment reflection)
        for ry, ra in ((8, 120), (28, 80), (48, 140), (62, 90)):
            rband = pygame.Surface((bw - 2, 4), pygame.SRCALPHA)
            rband.fill((255, 255, 255, ra))
            surf.blit(rband, (bx, by - 72 + ry))
        # dark band for contrast at base
        pygame.draw.rect(surf, (90, 95, 115), (bx, by - 72 + 74, bw, 6))
        # bright edge (left, the sharpened side)
        pygame.draw.rect(surf, (250, 252, 255), (bx - 1, by - 72, 3, bh))
        # fuller (center groove line)
        pygame.draw.line(surf, (180, 185, 200), (bx + bw // 2, by - 72), (bx + bw // 2, by + 6), 1)
        pygame.draw.rect(surf, outline, (bx - 1, by - 72, bw, bh), 2)
        # crossguard (shaded metal)
        cg = vgrad_surf(24, 8, shade(accent, 1.3), shade(accent, 0.65))
        clip_to_rect(cg, pygame.Rect(0, 0, 24, 8))
        surf.blit(cg, (bx - 7, by + 8))
        # crossguard specular
        pygame.draw.rect(surf, (255, 255, 255), (bx - 7, by + 8, 22, 2))
        pygame.draw.rect(surf, outline, (bx - 7, by + 8, 24, 8), 2)
        # grip (leather-wrapped, with cross-wrap lines)
        pygame.draw.rect(surf, (130, 85, 50), (bx + 2, by + 16, 8, 20))
        for gy in (20, 24, 28, 32):
            pygame.draw.line(surf, (100, 65, 35), (bx + 2, by + gy), (bx + 10, by + gy), 1)
        pygame.draw.rect(surf, outline, (bx + 2, by + 16, 8, 20), 1)
        # pommel (radial gem)
        pommel = radial_grad_surf(10, 10, shade(accent, 1.3), shade(accent, 0.5), center=(4, 3), radius=5)
        clip_to_circle(pommel, (5, 5), 4)
        surf.blit(pommel, (bx + 1, by + 34))
        pygame.draw.circle(surf, (255, 255, 255), (bx + 4, by + 36), 2)
        pygame.draw.circle(surf, outline, (bx + 5, by + 38), 4, 2)
    elif weapon == "staff":
        bx, by = cx + 52, 110
        # staff shaft with wood grain texture
        shaft = vgrad_surf(8, 120, (150, 105, 60), (85, 55, 30))
        clip_to_rect(shaft, pygame.Rect(0, 0, 8, 120))
        surf.blit(shaft, (bx, by - 60))
        # wood grain lines
        for gx in (2, 5):
            pygame.draw.line(surf, (120, 80, 40), (bx + gx, by - 58), (bx + gx, by + 58), 1)
        pygame.draw.rect(surf, outline, (bx, by - 60, 8, 120), 2)
        # metal ferrule at top
        pygame.draw.rect(surf, (200, 200, 215), (bx - 2, by - 62, 12, 6))
        pygame.draw.rect(surf, outline, (bx - 2, by - 62, 12, 6), 1)
        # glowing crystal head (three-layer: outer halo + mid glow + core)
        glow = soft_glow(66, 66, light_el, 120, radius=30, falloff=1.3)
        surf.blit(glow, (bx - 27, by - 96))
        glow2 = soft_glow(42, 42, (255, 255, 255), 80, radius=20, falloff=1.5)
        surf.blit(glow2, (bx - 15, by - 84))
        # faceted crystal (pointy hexagon shape)
        crystal_pts = [(bx + 4, by - 82), (bx + 18, by - 62), (bx + 10, by - 52), (bx - 2, by - 52), (bx - 14, by - 62)]
        cg = radial_grad_surf(36, 34, shade(light_el, 1.2), shade(accent, 0.45), center=(12, 8), radius=18)
        m = pygame.Surface((36, 34), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - (bx - 14), p[1] - (by - 82)) for p in crystal_pts])
        cg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(cg, (bx - 14, by - 82))
        # crystal facets (inner lines)
        pygame.draw.line(surf, shade(light_el, 0.6), (bx + 4, by - 82), (bx - 2, by - 56), 1)
        pygame.draw.line(surf, shade(light_el, 0.6), (bx + 4, by - 82), (bx + 8, by - 56), 1)
        pygame.draw.polygon(surf, outline, crystal_pts, 2)
        # specular on top point
        pygame.draw.circle(surf, (255, 255, 255), (bx + 2, by - 78), 3)
    elif weapon == "bow":
        bx, by = cx + 54, 150
        # bow limbs with compound curve look (outer dark wood, inner light)
        pygame.draw.arc(surf, shade(accent, 0.5), (bx - 14, by - 54, 48, 108), -1.2, 1.2, 8)
        pygame.draw.arc(surf, shade(accent, 0.75), (bx - 12, by - 52, 44, 104), -1.2, 1.2, 5)
        pygame.draw.arc(surf, accent, (bx - 10, by - 50, 40, 100), -1.2, 1.2, 3)
        # inner highlight (the lit edge)
        pygame.draw.arc(surf, shade(accent, 1.3), (bx - 9, by - 49, 38, 98), -1.15, 1.15, 1)
        # grip section (wrapped leather)
        pygame.draw.rect(surf, (90, 65, 40), (bx + 2, by - 6, 16, 12))
        for gw in (bx + 4, bx + 10):
            pygame.draw.line(surf, (70, 50, 30), (gw, by - 6), (gw, by + 5), 1)
        pygame.draw.rect(surf, outline, (bx + 2, by - 6, 16, 12), 1)
        # string
        pygame.draw.line(surf, (235, 235, 245), (bx + 10, by - 48), (bx + 10, by + 48), 1)
        # nocked arrow with fletching
        pygame.draw.line(surf, (210, 210, 220), (bx - 22, by), (bx + 12, by), 2)
        # arrowhead
        pygame.draw.polygon(surf, (220, 220, 235), [(bx + 12, by), (bx + 20, by - 5), (bx + 20, by + 5)])
        # fletching
        pygame.draw.polygon(surf, shade(light_el, 0.8), [(bx - 22, by), (bx - 28, by - 7), (bx - 24, by)])
        pygame.draw.polygon(surf, shade(light_el, 0.8), [(bx - 22, by), (bx - 28, by + 7), (bx - 24, by)])
        pygame.draw.polygon(surf, outline, [(bx + 12, by), (bx + 20, by - 5), (bx + 20, by + 5)])
    elif weapon == "dagger":
        bx, by = cx + 48, 150
        # blade triangle with premium metal + reflection
        bw2, bh2 = 10, 48
        blade = hgrad_surf(bw2, bh2, (230, 232, 242), (140, 145, 165))
        m = pygame.Surface((bw2, bh2), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255), [(0, 0), (bw2, 0), (bw2 // 2, bh2 - 2)])
        blade.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(blade, (bx - 1, by - 42))
        # reflection bands
        for ry2, ra2 in ((6, 100), (20, 70), (34, 120)):
            rb = pygame.Surface((8, 3), pygame.SRCALPHA)
            rb.fill((255, 255, 255, ra2))
            surf.blit(rb, (bx + 1, by - 42 + ry2))
        pygame.draw.rect(surf, (250, 252, 255), (bx - 1, by - 42, 2, bh2 - 2))
        pygame.draw.polygon(surf, outline, [(bx - 1, by - 42), (bx + bw2 - 1, by - 42), (bx + bw2 // 2 - 1, by + 4)], 2)
        # crossguard (metal, curved)
        cg = vgrad_surf(22, 6, shade(accent, 1.3), shade(accent, 0.65))
        clip_to_rect(cg, pygame.Rect(0, 0, 22, 6))
        surf.blit(cg, (bx - 5, by + 2))
        pygame.draw.rect(surf, (255, 255, 255), (bx - 5, by + 2, 20, 2))
        pygame.draw.rect(surf, outline, (bx - 5, by + 2, 22, 6), 2)
        # grip wrap
        pygame.draw.rect(surf, (110, 80, 50), (bx, by + 8, 6, 14))
        for gy2 in (10, 13, 16, 19):
            pygame.draw.line(surf, (85, 60, 35), (bx, by + gy2), (bx + 6, by + gy2), 1)
    elif weapon == "shield":
        bx, by = cx + 44, 170
        pts = [(bx - 6, by - 30), (bx + 22, by - 30), (bx + 22, by + 10), (bx + 8, by + 30), (bx - 6, by + 10)]
        # shield body with metallic diagonal shading + rim highlight
        shg = diag_grad_surf(30, 62, shade(accent, 1.25), shade(accent, 0.5))
        m = pygame.Surface((30, 62), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - (bx - 6), p[1] - (by - 30)) for p in pts])
        shg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(shg, (bx - 6, by - 30))
        # left rim highlight
        rim3 = pygame.Surface((4, 62), pygame.SRCALPHA)
        pygame.draw.polygon(rim3, (255, 255, 255, 90),
                            [(4, 0), (4, 60), (0, 50), (0, 8)])
        surf.blit(rim3, (bx - 6, by - 30))
        # metal rivets around the edge
        for rv_y in (-26, -10, 6, 20):
            pygame.draw.circle(surf, shade(accent, 0.6), (bx - 2, by + rv_y), 2)
            pygame.draw.circle(surf, (255, 255, 255), (bx - 3, by + rv_y - 1), 1)
        pygame.draw.polygon(surf, outline, pts, 3)
        # central boss (raised metal dome with radial gradient)
        boss_base = radial_grad_surf(24, 24, shade(accent, 1.4), shade(accent, 0.45), center=(8, 6), radius=12)
        clip_to_circle(boss_base, (12, 12), 11)
        surf.blit(boss_base, (bx, by - 16))
        # element gem inset
        gem = radial_grad_surf(14, 14, light_el, shade(accent, 0.35), center=(5, 4), radius=7)
        clip_to_circle(gem, (7, 7), 6)
        surf.blit(gem, (bx + 3, by - 12))
        pygame.draw.circle(surf, (255, 255, 255), (bx + 7, by - 9), 2)
        pygame.draw.circle(surf, outline, (bx + 8, by - 6), 12, 2)
        # bottom edge reinforcement bar
        pygame.draw.rect(surf, shade(accent, 0.55), (bx - 2, by + 26, 24, 5), border_radius=2)
        pygame.draw.rect(surf, outline, (bx - 2, by + 26, 24, 5), 1, border_radius=2)
    elif weapon == "orb":
        bx, by = cx + 50, 160
        # floating orb — three-layer glow + glassy orb + inner fire + orbiting motes
        glow = soft_glow(64, 64, light_el, 100, radius=30, falloff=1.35)
        surf.blit(glow, (bx - 32, by - 32))
        glow2 = soft_glow(42, 42, (255, 255, 255), 70, radius=20, falloff=1.5)
        surf.blit(glow2, (bx - 21, by - 21))
        # glassy orb body (concentric: dark edge -> bright rim -> light center)
        orb = radial_grad_surf(36, 36, shade(light_el, 1.4), shade(accent, 0.3), center=(14, 12), radius=18)
        clip_to_circle(orb, (18, 18), 16)
        surf.blit(orb, (bx - 18, by - 18))
        # inner core (brighter, smaller)
        core = radial_grad_surf(20, 20, (255, 255, 255), light_el, center=(8, 6), radius=10)
        clip_to_circle(core, (10, 10), 8)
        surf.blit(core, (bx - 10, by - 10))
        # glass rim highlight
        pygame.draw.circle(surf, (255, 255, 255), (bx - 7, by - 8), 4)
        pygame.draw.circle(surf, (255, 255, 255), (bx - 3, by - 4), 2)
        # secondary reflections on the bottom
        pygame.draw.circle(surf, (255, 255, 255), (bx + 6, by + 8), 1)
        pygame.draw.circle(surf, outline, (bx, by), 16, 2)
        # orbiting motes (with glow trails)
        for i in range(3):
            ang = -math.pi / 2 + (i - 1) * 0.5
            mx = int(bx + math.cos(ang) * 22)
            my = int(by + math.sin(ang) * 22)
            mote_glow = soft_glow(10, 10, light_el, 100, radius=5, falloff=1.4)
            surf.blit(mote_glow, (mx - 5, my - 5))
            pygame.draw.circle(surf, (255, 255, 255), (mx, my), 3)

# ---------------------------------------------------------------------------
# Enemy sprites
# ---------------------------------------------------------------------------
def _grad_ellipse(surf, rect, inner, outer, center=None, falloff=1.0):
    """Fill an ellipse with a radial gradient (inner at center, outer at edge)."""
    x, y, w, h = rect
    g = radial_grad_surf(w, h, inner, outer, center=center, radius=max(w, h) / 2.0, falloff=falloff)
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(m, (255, 255, 255, 255), m.get_rect())
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(g, (x, y))

def _grad_round_rect(surf, rect, top_left, bot_right, border_radius=0):
    """Fill a (rounded) rect with a diagonal gradient."""
    x, y, w, h = rect
    g = diag_grad_surf(w, h, top_left, bot_right)
    clip_to_rect(g, pygame.Rect(0, 0, w, h), border_radius=border_radius)
    surf.blit(g, (x, y))

def _glowing_eye(surf, pos, core, glow_col, r_core=5, r_glow=14):
    """A glowing eye: soft halo + bright core + dark pupil."""
    gx, gy = pos
    halo = soft_glow(r_glow * 2, r_glow * 2, glow_col, 150, radius=r_glow, falloff=1.6)
    surf.blit(halo, (gx - r_glow, gy - r_glow))
    pygame.draw.circle(surf, core, (gx, gy), r_core)
    pygame.draw.circle(surf, (255, 255, 255), (gx - r_core // 3, gy - r_core // 3), max(1, r_core // 3))
    pygame.draw.circle(surf, (30, 26, 40), (gx, gy), r_core, 1)

def draw_enemy(surf, kind, palette):
    cx, cy = 128, 140
    outline = (30, 26, 40)
    main, accent, dark = palette
    main_light = shade(main, 1.28)
    main_dark = shade(main, 0.62)
    accent_light = shade(accent, 1.25)
    dark_light = shade(dark, 1.3)

    # soft ground shadow
    shadow = pygame.Surface((180, 44), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 80), shadow.get_rect())
    surf.blit(shadow, (cx - 90, 222))

    if kind == "slime":
        # gelatinous body with radial gradient + glossy highlight
        body_r = pygame.Rect(cx - 60, cy - 30, 120, 90)
        _grad_ellipse(surf, body_r, main_light, main_dark, center=(40, 24), falloff=1.3)
        pygame.draw.ellipse(surf, outline, body_r, 4)
        # glossy highlight blob
        hl = soft_glow(44, 30, (255, 255, 255), 150, center=(14, 10), radius=20, falloff=1.4)
        surf.blit(hl, (cx - 40, cy - 22))
        # a second smaller shine
        pygame.draw.ellipse(surf, (255, 255, 255, 200), (cx - 30, cy - 14, 16, 10))
        draw_eyes(surf, cx, cy + 8, (20, 20, 30), outline, "dark")
    elif kind == "goblin":
        # body with diagonal shading
        body_r = pygame.Rect(cx - 30, cy, 60, 70)
        _grad_round_rect(surf, body_r, main_light, main_dark, border_radius=16)
        pygame.draw.rect(surf, outline, body_r, 3, border_radius=16)
        # head with radial shading
        head_g = radial_grad_surf(68, 68, main_light, main_dark, center=(24, 20), radius=36)
        clip_to_circle(head_g, (34, 34), 34)
        surf.blit(head_g, (cx - 34, cy - 54))
        pygame.draw.circle(surf, outline, (cx, cy - 20), 34, 3)
        # ears (shaded)
        for sx in (-1, 1):
            ear = [(cx + sx * 34, cy - 22), (cx + sx * 56, cy - 36), (cx + sx * 30, cy - 8)]
            pygame.draw.polygon(surf, main, ear)
            pygame.draw.polygon(surf, main_dark, [(cx + sx * 34, cy - 22), (cx + sx * 50, cy - 32), (cx + sx * 36, cy - 18)])
            pygame.draw.polygon(surf, outline, ear, 3)
        for sx in (-12, 12):
            _glowing_eye(surf, (cx + sx, cy - 22), (255, 230, 60), (255, 200, 40), r_core=4, r_glow=10)
        # club (shaded wood + knob)
        club_shaft = vgrad_surf(10, 60, (140, 95, 55), (90, 60, 35))
        clip_to_rect(club_shaft, pygame.Rect(0, 0, 10, 60))
        surf.blit(club_shaft, (cx + 36, cy - 10))
        knob = radial_grad_surf(32, 32, (150, 100, 60), (80, 50, 28), center=(12, 10), radius=16)
        clip_to_circle(knob, (16, 16), 16)
        surf.blit(knob, (cx + 25, cy - 26))
        pygame.draw.rect(surf, outline, (cx + 36, cy - 10, 10, 60), 2)
        pygame.draw.circle(surf, outline, (cx + 41, cy - 10), 16, 3)
    elif kind == "bat":
        # body with radial shading
        body_g = radial_grad_surf(60, 60, shade(dark, 1.3), dark, center=(20, 18), radius=32)
        clip_to_circle(body_g, (30, 30), 30)
        surf.blit(body_g, (cx - 30, cy - 30))
        pygame.draw.circle(surf, outline, (cx, cy), 30, 3)
        # wings with membrane gradient + finger bones
        for sx in (-1, 1):
            pts = [(cx, cy - 6), (cx + sx * 70, cy - 40), (cx + sx * 80, cy), (cx + sx * 50, cy + 6), (cx + sx * 30, cy - 6)]
            wg = diag_grad_surf(90, 50, main, shade(main, 0.6))
            m = pygame.Surface((90, 50), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255),
                                [(p[0] - (cx - 10), p[1] - (cy - 40)) if sx > 0 else (p[0] - (cx - 80), p[1] - (cy - 40)) for p in pts])
            wg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(wg, (cx - 10 if sx > 0 else cx - 80, cy - 40))
            pygame.draw.polygon(surf, outline, pts, 3)
            # wing finger bones
            pygame.draw.line(surf, dark, (cx, cy - 6), (cx + sx * 70, cy - 40), 2)
            pygame.draw.line(surf, dark, (cx, cy - 6), (cx + sx * 78, cy - 4), 2)
            pygame.draw.line(surf, dark, (cx, cy - 6), (cx + sx * 50, cy + 6), 2)
        for sx in (-10, 10):
            _glowing_eye(surf, (cx + sx, cy - 4), (255, 70, 70), (255, 40, 40), r_core=4, r_glow=10)
        # fangs
        pygame.draw.polygon(surf, (240, 240, 230), [(cx - 6, cy + 14), (cx - 8, cy + 22), (cx - 4, cy + 16)])
        pygame.draw.polygon(surf, (240, 240, 230), [(cx + 6, cy + 14), (cx + 8, cy + 22), (cx + 4, cy + 16)])
        pygame.draw.polygon(surf, outline, [(cx - 6, cy + 14), (cx, cy + 22), (cx + 6, cy + 14)], 2)
    elif kind == "skeleton":
        bone = (240, 240, 232)
        bone_dark = (200, 200, 192)
        # skull with radial shading
        skull = radial_grad_surf(64, 64, (255, 255, 250), bone_dark, center=(22, 20), radius=34)
        clip_to_circle(skull, (32, 32), 32)
        surf.blit(skull, (cx - 32, cy - 56))
        pygame.draw.circle(surf, outline, (cx, cy - 24), 32, 3)
        # eye sockets (dark voids with faint glow)
        for sx in (-12, 12):
            pygame.draw.circle(surf, (20, 20, 30), (cx + sx, cy - 22), 8)
            pygame.draw.circle(surf, (60, 60, 80), (cx + sx - 2, cy - 24), 3)
        # nose
        pygame.draw.polygon(surf, (20, 20, 30), [(cx - 3, cy - 14), (cx + 3, cy - 14), (cx, cy - 8)])
        # ribcage (shaded)
        rib_r = pygame.Rect(cx - 22, cy + 8, 44, 50)
        _grad_round_rect(surf, rib_r, bone, bone_dark, border_radius=10)
        pygame.draw.rect(surf, outline, rib_r, 3, border_radius=10)
        for i in range(4):
            yy = cy + 16 + i * 10
            pygame.draw.line(surf, shade(outline, 0.8), (cx - 18, yy), (cx + 18, yy), 2)
        # spine
        pygame.draw.line(surf, bone_dark, (cx, cy + 8), (cx, cy + 56), 2)
        # sword (metal gradient)
        blade = hgrad_surf(8, 70, (220, 222, 235), (160, 165, 180))
        clip_to_rect(blade, pygame.Rect(0, 0, 8, 70))
        surf.blit(blade, (cx + 30, cy - 50))
        pygame.draw.rect(surf, (245, 248, 255), (cx + 30, cy - 50, 2, 70))
        pygame.draw.rect(surf, outline, (cx + 30, cy - 50, 8, 70), 2)
    elif kind == "wolf":
        # body with radial shading
        body_r = pygame.Rect(cx - 50, cy - 10, 100, 60)
        _grad_ellipse(surf, body_r, main_light, main_dark, center=(34, 18), falloff=1.2)
        pygame.draw.ellipse(surf, outline, body_r, 3)
        # head snout
        snout = [(cx - 40, cy - 6), (cx - 70, cy - 30), (cx - 30, cy - 30)]
        sg = diag_grad_surf(50, 30, main_light, main_dark)
        m = pygame.Surface((50, 30), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - (cx - 70), p[1] - (cy - 30)) for p in snout])
        sg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(sg, (cx - 70, cy - 30))
        pygame.draw.polygon(surf, outline, snout, 3)
        # ears
        for ex in ((cx - 56, cy - 26), (cx - 44, cy - 28)):
            pygame.draw.polygon(surf, main, [(ex[0], ex[1]), (ex[0] - 8, ex[1] - 18), (ex[0] + 6, ex[1] - 6)])
            pygame.draw.polygon(surf, outline, [(ex[0], ex[1]), (ex[0] - 8, ex[1] - 18), (ex[0] + 6, ex[1] - 6)], 2)
        for sx in (-12, 4):
            _glowing_eye(surf, (cx + sx, cy - 4), (255, 230, 60), (255, 200, 40), r_core=4, r_glow=9)
        pygame.draw.polygon(surf, (40, 30, 30), [(cx - 18, cy + 10), (cx - 10, cy + 18), (cx - 2, cy + 10)])
        pygame.draw.polygon(surf, outline, [(cx - 18, cy + 10), (cx - 10, cy + 18), (cx - 2, cy + 10)], 2)
    elif kind == "orc":
        # body with diagonal shading
        body_r = pygame.Rect(cx - 36, cy - 10, 72, 80)
        _grad_round_rect(surf, body_r, main_light, main_dark, border_radius=18)
        pygame.draw.rect(surf, outline, body_r, 3, border_radius=18)
        # head with radial shading
        head_g = radial_grad_surf(80, 80, main_light, main_dark, center=(28, 24), radius=42)
        clip_to_circle(head_g, (40, 40), 40)
        surf.blit(head_g, (cx - 40, cy - 70))
        pygame.draw.circle(surf, outline, (cx, cy - 30), 40, 3)
        # tusks (shaded)
        for sx in (-1, 1):
            tusk = [(cx + sx * 12, cy - 18), (cx + sx * 16, cy - 2), (cx + sx * 8, cy - 8)]
            pygame.draw.polygon(surf, (245, 245, 235), tusk)
            pygame.draw.polygon(surf, (200, 200, 190), [(cx + sx * 12, cy - 18), (cx + sx * 14, cy - 6), (cx + sx * 10, cy - 10)])
            pygame.draw.polygon(surf, outline, tusk, 2)
        for sx in (-14, 14):
            _glowing_eye(surf, (cx + sx, cy - 34), (255, 60, 60), (255, 30, 30), r_core=5, r_glow=11)
        # axe (wood shaft + metal head with gradient)
        shaft = vgrad_surf(8, 90, (140, 95, 55), (90, 60, 35))
        clip_to_rect(shaft, pygame.Rect(0, 0, 8, 90))
        surf.blit(shaft, (cx + 40, cy - 40))
        pygame.draw.rect(surf, outline, (cx + 40, cy - 40, 8, 90), 2)
        head_pts = [(cx + 30, cy - 50), (cx + 70, cy - 50), (cx + 64, cy - 10), (cx + 36, cy - 10)]
        hg = diag_grad_surf(44, 44, accent_light, shade(accent, 0.6))
        m = pygame.Surface((44, 44), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - (cx + 26), p[1] - (cy - 54)) for p in head_pts])
        hg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(hg, (cx + 26, cy - 54))
        pygame.draw.polygon(surf, outline, head_pts, 3)
        pygame.draw.line(surf, (255, 255, 255), (cx + 32, cy - 48), (cx + 38, cy - 14), 2)
    elif kind == "golem":
        # body (rocky, diagonal shaded)
        body_r = pygame.Rect(cx - 44, cy - 40, 88, 110)
        _grad_round_rect(surf, body_r, main_light, main_dark, border_radius=12)
        pygame.draw.rect(surf, outline, body_r, 4, border_radius=12)
        # head (rocky block)
        head_r = pygame.Rect(cx - 34, cy - 70, 68, 40)
        _grad_round_rect(surf, head_r, main_light, main_dark, border_radius=10)
        pygame.draw.rect(surf, outline, head_r, 4, border_radius=10)
        for sx in (-16, 16):
            # glowing crystal eyes
            _glowing_eye(surf, (cx + sx, cy - 52), (255, 230, 90), (255, 200, 60), r_core=5, r_glow=12)
        # rocky cracks (darker, branching)
        pygame.draw.line(surf, dark, (cx - 20, cy - 10), (cx - 4, cy + 20), 3)
        pygame.draw.line(surf, dark, (cx - 4, cy + 20), (cx + 16, cy + 6), 3)
        pygame.draw.line(surf, dark, (cx + 18, cy - 20), (cx + 28, cy + 10), 2)
        # mossy accent at the base
        pygame.draw.rect(surf, shade(accent, 0.9), (cx - 40, cy + 60, 80, 10), border_radius=4)
    elif kind == "wraith":
        # ghostly robe with vertical gradient (ethereal)
        pts = [(cx - 40, cy - 30), (cx + 40, cy - 30), (cx + 50, cy + 70),
               (cx + 30, cy + 50), (cx + 10, cy + 80), (cx - 10, cy + 50), (cx - 50, cy + 70)]
        rg = vgrad_surf(110, 120, main_light, shade(main, 0.5))
        m = pygame.Surface((110, 120), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - (cx - 55), p[1] - (cy - 30)) for p in pts])
        rg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(rg, (cx - 55, cy - 30))
        pygame.draw.polygon(surf, outline, pts, 3)
        # tattered hem glow at the bottom
        for sx in (-30, -10, 10, 30):
            halo = soft_glow(20, 20, (120, 255, 200), 80, radius=10, falloff=1.5)
            surf.blit(halo, (cx + sx - 10, cy + 60))
        # hood/head
        head_g = radial_grad_surf(70, 70, main_light, shade(main, 0.5), center=(24, 22), radius=36)
        clip_to_circle(head_g, (35, 35), 34)
        surf.blit(head_g, (cx - 35, cy - 64))
        pygame.draw.circle(surf, outline, (cx, cy - 30), 34, 3)
        for sx in (-12, 12):
            _glowing_eye(surf, (cx + sx, cy - 30), (140, 255, 210), (80, 255, 200), r_core=5, r_glow=11)
    elif kind == "dragon":
        # body with radial shading
        body_r = pygame.Rect(cx - 70, cy - 30, 140, 110)
        _grad_ellipse(surf, body_r, main_light, main_dark, center=(50, 30), falloff=1.25)
        pygame.draw.ellipse(surf, outline, body_r, 4)
        # belly (lighter, scaled)
        belly_r = pygame.Rect(cx - 50, cy, 100, 70)
        _grad_ellipse(surf, belly_r, accent_light, accent, center=(36, 24), falloff=1.2)
        # scale texture lines on belly (proper overlapping scales)
        for i in range(6):
            yy = cy + 6 + i * 13
            pygame.draw.arc(surf, shade(accent, 0.65), (cx - 44, yy, 88, 14), 0.2, math.pi - 0.2, 1)
        # body scale texture (subtle diamond pattern on the back)
        for si in range(8):
            sx2 = cx - 40 + si * 16
            sy3 = cy - 20 + (si % 3) * 8
            pygame.draw.polygon(surf, shade(main, 0.55),
                                [(sx2, sy3), (sx2 + 8, sy3 - 4), (sx2 + 16, sy3), (sx2 + 8, sy3 + 4)])
            pygame.draw.polygon(surf, shade(main, 0.7),
                                [(sx2, sy3), (sx2 + 8, sy3 - 4), (sx2 + 16, sy3), (sx2 + 8, sy3 + 4)], 1)
        # fire breath glow near the mouth
        breath_glow = soft_glow(44, 30, (255, 200, 80), 90, center=(22, 10), radius=24, falloff=1.5)
        surf.blit(breath_glow, (cx + 80, cy - 58))
        # head with radial shading
        head_g = radial_grad_surf(80, 80, main_light, main_dark, center=(28, 24), radius=42)
        clip_to_circle(head_g, (40, 40), 40)
        surf.blit(head_g, (cx + 20, cy - 80))
        pygame.draw.circle(surf, outline, (cx + 60, cy - 40), 40, 4)
        # horns (shaded)
        for sx in (-7, 7):
            horn = [(cx + 57 + sx, cy - 70), (cx + 47 + sx, cy - 100), (cx + 64 + sx, cy - 70)]
            pygame.draw.polygon(surf, dark, horn)
            pygame.draw.polygon(surf, shade(dark, 1.2), [(cx + 57 + sx, cy - 70), (cx + 50 + sx, cy - 92), (cx + 56 + sx, cy - 70)])
            pygame.draw.polygon(surf, outline, horn, 3)
        # glowing eye
        _glowing_eye(surf, (cx + 70, cy - 44), (255, 230, 60), (255, 200, 40), r_core=7, r_glow=14)
        # wings (membrane gradient + finger bones)
        for i in range(3):
            bx = cx - 30 - i * 20
            wpts = [(cx - 20, cy - 20), (bx, cy - 80), (bx + 20, cy - 30)]
            wg = diag_grad_surf(60, 70, dark, shade(dark, 0.6))
            m = pygame.Surface((60, 70), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255),
                                [(p[0] - (bx - 10), p[1] - (cy - 80)) for p in wpts])
            wg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(wg, (bx - 10, cy - 80))
            pygame.draw.polygon(surf, outline, wpts, 3)
            pygame.draw.line(surf, shade(dark, 1.2), (cx - 20, cy - 20), (bx + 10, cy - 75), 2)
        # tail (tapered)
        tail = [(cx - 70, cy + 20), (cx - 110, cy), (cx - 100, cy + 40)]
        tg = diag_grad_surf(50, 50, main, shade(main, 0.6))
        m = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - (cx - 110), p[1] - cy) for p in tail])
        tg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(tg, (cx - 110, cy))
        pygame.draw.polygon(surf, outline, tail, 3)
        # tail spade
        pygame.draw.polygon(surf, dark, [(cx - 110, cy + 4), (cx - 120, cy - 6), (cx - 118, cy + 18), (cx - 108, cy + 12)])
        pygame.draw.polygon(surf, outline, [(cx - 110, cy + 4), (cx - 120, cy - 6), (cx - 118, cy + 18), (cx - 108, cy + 12)], 2)
    elif kind == "demonking":
        # big menacing figure (dark, with rim light)
        body_r = pygame.Rect(cx - 50, cy - 10, 100, 90)
        _grad_round_rect(surf, body_r, shade(dark, 1.15), shade(dark, 0.5), border_radius=20)
        pygame.draw.rect(surf, outline, body_r, 4, border_radius=20)
        # rim light on the left edge
        rim = soft_glow(14, 90, dark_light, 90, center=(7, 45), radius=8, falloff=1.3)
        surf.blit(rim, (cx - 50, cy - 10))
        # head with radial shading
        head_g = radial_grad_surf(92, 92, main, shade(main, 0.5), center=(32, 28), radius=48)
        clip_to_circle(head_g, (46, 46), 46)
        surf.blit(head_g, (cx - 46, cy - 86))
        pygame.draw.circle(surf, outline, (cx, cy - 40), 46, 4)
        # crown of horns (shaded)
        for sx in (-30, -10, 10, 30):
            horn = [(cx + sx, cy - 70), (cx + sx - 8, cy - 100), (cx + sx + 8, cy - 70)]
            pygame.draw.polygon(surf, dark, horn)
            pygame.draw.polygon(surf, shade(dark, 1.3), [(cx + sx, cy - 70), (cx + sx - 6, cy - 92), (cx + sx - 2, cy - 70)])
            pygame.draw.polygon(surf, outline, horn, 3)
        # glowing eyes
        for sx in (-16, 16):
            _glowing_eye(surf, (cx + sx, cy - 42), (255, 70, 70), (255, 30, 30), r_core=8, r_glow=15)
            pygame.draw.circle(surf, (255, 210, 210), (cx + sx - 2, cy - 44), 3)
        # cape (flowing, with fabric fold lines for depth)
        cape_pts = [(cx - 50, cy - 10), (cx - 80, cy + 80), (cx, cy + 50), (cx + 80, cy + 80), (cx + 50, cy - 10)]
        cg = vgrad_surf(170, 100, accent, shade(accent, 0.45))
        m = pygame.Surface((170, 100), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255),
                            [(p[0] - (cx - 80), p[1] - (cy - 10)) for p in cape_pts])
        cg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(cg, (cx - 80, cy - 10))
        # cape fold lines (darker vertical curves on the cape for fabric drape)
        for cfx in (-20, 0, 20):
            fold = pygame.Surface((4, 90), pygame.SRCALPHA)
            pygame.draw.line(fold, (*shade(accent, 0.6), 80), (2, 0), (2, 90), 3)
            surf.blit(fold, (cx + cfx, cy + 4))
        # dark void aura behind the demonking (menacing)
        dark_aura = soft_glow(180, 180, shade(dark, 1.05), 40, center=(90, 100), radius=92, falloff=1.6)
        surf.blit(dark_aura, (cx - 90, cy - 30))
        pygame.draw.polygon(surf, outline, cape_pts, 3)
    elif kind == "imp":
        # small horned fiend (shaded body)
        body_r = pygame.Rect(cx - 22, cy - 6, 44, 60)
        _grad_round_rect(surf, body_r, main_light, main_dark, border_radius=14)
        pygame.draw.rect(surf, outline, body_r, 3, border_radius=14)
        # head with radial shading
        head_g = radial_grad_surf(56, 56, main_light, main_dark, center=(20, 18), radius=30)
        clip_to_circle(head_g, (28, 28), 28)
        surf.blit(head_g, (cx - 28, cy - 52))
        pygame.draw.circle(surf, outline, (cx, cy - 24), 28, 3)
        # horns (shaded)
        for sx in (-12, 12):
            horn = [(cx + sx, cy - 44), (cx + sx - 6, cy - 64), (cx + sx + 6, cy - 44)]
            pygame.draw.polygon(surf, dark, horn)
            pygame.draw.polygon(surf, shade(dark, 1.3), [(cx + sx, cy - 44), (cx + sx - 4, cy - 60), (cx + sx - 2, cy - 44)])
            pygame.draw.polygon(surf, outline, horn, 2)
        for sx in (-9, 9):
            _glowing_eye(surf, (cx + sx, cy - 24), (255, 230, 70), (255, 200, 50), r_core=4, r_glow=9)
    elif kind == "harpy":
        # winged bird-woman
        body_r = pygame.Rect(cx - 30, cy - 10, 60, 70)
        _grad_ellipse(surf, body_r, main_light, main_dark, center=(22, 18), falloff=1.2)
        pygame.draw.ellipse(surf, outline, body_r, 3)
        # head with radial shading
        head_g = radial_grad_surf(52, 52, main_light, main_dark, center=(18, 16), radius=28)
        clip_to_circle(head_g, (26, 26), 26)
        surf.blit(head_g, (cx - 26, cy - 56))
        pygame.draw.circle(surf, outline, (cx, cy - 30), 26, 3)
        # feathered wings with gradient + feather lines
        for sx in (-1, 1):
            pts = [(cx, cy), (cx + sx * 70, cy - 50), (cx + sx * 90, cy + 10), (cx + sx * 40, cy + 10)]
            wg = diag_grad_surf(100, 70, accent, shade(accent, 0.6))
            m = pygame.Surface((100, 70), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255),
                                [(p[0] - (cx - 10 if sx > 0 else cx - 90), p[1] - (cy - 50)) for p in pts])
            wg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(wg, (cx - 10 if sx > 0 else cx - 90, cy - 50))
            pygame.draw.polygon(surf, outline, pts, 3)
            # feather ridges
            for fy in (-30, -10, 10):
                pygame.draw.line(surf, shade(accent, 0.7),
                                 (cx + sx * 8, cy + fy), (cx + sx * 60, cy + fy - 8), 1)
        for sx in (-8, 8):
            _glowing_eye(surf, (cx + sx, cy - 30), (255, 230, 50), (255, 200, 40), r_core=3, r_glow=8)
        # beak
        pygame.draw.polygon(surf, (240, 200, 80), [(cx - 4, cy - 22), (cx + 4, cy - 22), (cx, cy - 14)])
        pygame.draw.polygon(surf, outline, [(cx - 4, cy - 22), (cx + 4, cy - 22), (cx, cy - 14)], 1)
    elif kind == "ghoul":
        # hunched undead (sickly, desaturated shading)
        body_r = pygame.Rect(cx - 26, cy - 4, 52, 64)
        _grad_round_rect(surf, body_r, main_light, main_dark, border_radius=12)
        pygame.draw.rect(surf, outline, body_r, 3, border_radius=12)
        # head with radial shading
        head_g = radial_grad_surf(56, 56, main_light, main_dark, center=(20, 18), radius=30)
        clip_to_circle(head_g, (28, 28), 28)
        surf.blit(head_g, (cx - 28, cy - 54))
        pygame.draw.circle(surf, outline, (cx, cy - 26), 28, 3)
        for sx in (-10, 10):
            _glowing_eye(surf, (cx + sx, cy - 26), (190, 255, 190), (120, 255, 160), r_core=5, r_glow=11)
        # mouth (toothy)
        pygame.draw.rect(surf, (30, 26, 40), (cx - 9, cy - 14, 18, 6))
        for tx in (-6, -2, 2, 6):
            pygame.draw.rect(surf, (235, 235, 225), (cx + tx, cy - 14, 3, 6))
        # claws (shaded)
        for sx in (-30, 22):
            cl = vgrad_surf(8, 24, accent_light, accent)
            clip_to_rect(cl, pygame.Rect(0, 0, 8, 24))
            surf.blit(cl, (cx + sx, cy + 20))
            pygame.draw.rect(surf, outline, (cx + sx, cy + 20, 8, 24), 2)
            # claw tips
            pygame.draw.polygon(surf, shade(accent, 0.7), [(cx + sx, cy + 44), (cx + sx + 8, cy + 44), (cx + sx + 4, cy + 50)])
    elif kind == "paladin":
        # armored fallen knight (metallic)
        body_r = pygame.Rect(cx - 30, cy - 6, 60, 76)
        _grad_round_rect(surf, body_r, shade(main, 1.2), shade(main, 0.6), border_radius=16)
        pygame.draw.rect(surf, outline, body_r, 3, border_radius=16)
        # armor plate highlights
        pygame.draw.rect(surf, (255, 255, 255), (cx - 26, cy - 2, 8, 60), border_radius=4)
        pygame.draw.rect(surf, shade(main, 0.7), (cx + 18, cy - 2, 8, 60), border_radius=4)
        # helmet with radial shading
        head_g = radial_grad_surf(60, 60, shade(main, 1.25), shade(main, 0.55), center=(20, 18), radius=32)
        clip_to_circle(head_g, (30, 30), 30)
        surf.blit(head_g, (cx - 30, cy - 58))
        pygame.draw.circle(surf, outline, (cx, cy - 28), 30, 3)
        # visor slit (glowing)
        pygame.draw.rect(surf, (20, 20, 30), (cx - 17, cy - 31, 34, 9))
        visor_glow = soft_glow(40, 14, (255, 80, 80), 120, radius=18, falloff=1.4)
        surf.blit(visor_glow, (cx - 20, cy - 34))
        # emblem (radial gem)
        gem = radial_grad_surf(22, 22, accent_light, shade(accent, 0.4), center=(8, 7), radius=11)
        clip_to_circle(gem, (11, 11), 10)
        surf.blit(gem, (cx - 11, cy + 5))
        pygame.draw.circle(surf, outline, (cx, cy + 16), 10, 2)
        # sword (metal gradient + edge)
        blade = hgrad_surf(8, 80, (220, 222, 235), (160, 165, 180))
        clip_to_rect(blade, pygame.Rect(0, 0, 8, 80))
        surf.blit(blade, (cx + 30, cy - 50))
        pygame.draw.rect(surf, (245, 248, 255), (cx + 30, cy - 50, 2, 80))
        pygame.draw.rect(surf, outline, (cx + 30, cy - 50, 8, 80), 2)
        # crossguard
        pygame.draw.rect(surf, accent, (cx + 24, cy + 28, 20, 6))
        pygame.draw.rect(surf, outline, (cx + 24, cy + 28, 20, 6), 1)
    elif kind == "hydra":
        # multi-headed serpent (scaled body)
        body_r = pygame.Rect(cx - 60, cy, 120, 70)
        _grad_ellipse(surf, body_r, main_light, main_dark, center=(42, 22), falloff=1.2)
        pygame.draw.ellipse(surf, outline, body_r, 4)
        # scale texture
        for i in range(4):
            yy = cy + 10 + i * 14
            pygame.draw.arc(surf, shade(main, 0.7), (cx - 54, yy, 108, 16), 0.2, math.pi - 0.2, 1)
        for i, sx in enumerate((-36, 0, 36)):
            hy = cy - 30 - (10 if i == 1 else 0)
            # head with radial shading
            hg = radial_grad_surf(44, 44, main_light, main_dark, center=(15, 13), radius=23)
            clip_to_circle(hg, (22, 22), 22)
            surf.blit(hg, (cx + sx - 22, hy - 22))
            pygame.draw.circle(surf, outline, (cx + sx, hy), 22, 3)
            # glowing eye
            _glowing_eye(surf, (cx + sx + 6, hy - 4), (255, 90, 90), (255, 50, 50), r_core=4, r_glow=9)
            # forked tongue on the middle head
            if i == 1:
                pygame.draw.line(surf, (180, 40, 50), (cx + sx, hy + 18), (cx + sx - 6, hy + 26), 2)
                pygame.draw.line(surf, (180, 40, 50), (cx + sx, hy + 18), (cx + sx + 6, hy + 26), 2)
    elif kind == "frosttitan":
        # towering ice giant (crystalline)
        body_r = pygame.Rect(cx - 48, cy - 40, 96, 120)
        _grad_round_rect(surf, body_r, main_light, main_dark, border_radius=14)
        pygame.draw.rect(surf, outline, body_r, 4, border_radius=14)
        # ice crystal facets (lighter shards on the body, more varied)
        for fx, fy, fw, fh in ((-32, -28, 20, 42), (10, -22, 18, 52), (26, 12, 16, 42), (-24, 10, 14, 36)):
            fc = diag_grad_surf(fw, fh, (245, 252, 255), shade(main, 1.15))
            clip_to_rect(fc, pygame.Rect(0, 0, fw, fh), border_radius=3)
            surf.blit(fc, (cx + fx, cy + fy))
            pygame.draw.rect(surf, shade(main, 0.65), (cx + fx, cy + fy, fw, fh), 1, border_radius=3)
            # specular glint on each facet
            pygame.draw.rect(surf, (255, 255, 255), (cx + fx + 2, cy + fy + 2, fw - 4, 2))
        # frost mist aura around the body
        frost_aura = soft_glow(180, 180, (200, 240, 255), 50, center=(90, 110), radius=92, falloff=1.5)
        surf.blit(frost_aura, (cx - 90, cy - 50))
        # head with radial shading
        head_g = radial_grad_surf(76, 76, main_light, main_dark, center=(26, 22), radius=40)
        clip_to_circle(head_g, (38, 38), 38)
        surf.blit(head_g, (cx - 38, cy - 102))
        pygame.draw.circle(surf, outline, (cx, cy - 64), 38, 4)
        for sx in (-14, 14):
            _glowing_eye(surf, (cx + sx, cy - 64), (210, 245, 255), (140, 210, 255), r_core=6, r_glow=12)
        # ice shards (sharper crystal spires, with specular edges)
        for sx in (-30, 0, 30):
            sh_pts = [(cx + sx - 6, cy + 80), (cx + sx, cy + 34), (cx + sx + 6, cy + 80)]
            sg = vgrad_surf(16, 48, (255, 255, 255), shade(accent, 0.8))
            m = pygame.Surface((16, 48), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255),
                                [(p[0] - (cx + sx - 8), p[1] - (cy + 34)) for p in sh_pts])
            sg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(sg, (cx + sx - 8, cy + 34))
            # bright edge on the left side of each shard
            pygame.draw.line(surf, (255, 255, 255), (cx + sx - 5, cy + 78), (cx + sx - 1, cy + 36), 2)
            pygame.draw.polygon(surf, outline, sh_pts, 2)
        # frost breath glow (wider, more dramatic)
        breath = soft_glow(56, 36, (200, 245, 255), 100, center=(28, 16), radius=26, falloff=1.5)
        surf.blit(breath, (cx + 28, cy - 56))
        # few floating ice motes near the giant
        for im in range(4):
            mx = cx + random.uniform(-40, 40)
            my = cy + random.uniform(-60, 20)
            mr = random.uniform(2, 5)
            moteg = soft_glow(int(mr * 4), int(mr * 4), (210, 240, 255), 120, radius=int(mr * 2), falloff=1.5)
            surf.blit(moteg, (int(mx - mr * 2), int(my - mr * 2)))
            pygame.draw.circle(surf, (255, 255, 255), (int(mx), int(my)), int(mr))
    elif kind == "embertyrant":
        # roaring flame warlord
        body_r = pygame.Rect(cx - 52, cy - 8, 104, 92)
        _grad_round_rect(surf, body_r, shade(dark, 1.2), shade(dark, 0.5), border_radius=20)
        pygame.draw.rect(surf, outline, body_r, 4, border_radius=20)
        # ember cracks glowing on the body (branching, lava-like)
        for ey in (8, 38, 62):
            crack_glow = soft_glow(52, 10, (255, 180, 60), 180, center=(26, 5), radius=24, falloff=1.4)
            surf.blit(crack_glow, (cx - 26, cy + ey - 5))
            # main crack line + branches
            pygame.draw.line(surf, (255, 220, 120), (cx - 22, cy + ey), (cx + 22, cy + ey), 3)
            pygame.draw.line(surf, (255, 255, 200), (cx - 22, cy + ey), (cx, cy + ey), 1)
            # branch cracks going up and down
            for bx2 in (-8, 8):
                pygame.draw.line(surf, (255, 140, 60), (cx + bx2, cy + ey), (cx + bx2 + 6, cy + ey - 8), 2)
        # molten core glow at chest center
        core_glow = soft_glow(36, 36, (255, 200, 80), 140, center=(18, 18), radius=18, falloff=1.3)
        surf.blit(core_glow, (cx - 18, cy + 20))
        pygame.draw.circle(surf, (255, 240, 120), (cx, cy + 38), 8)
        pygame.draw.circle(surf, (255, 255, 200), (cx - 2, cy + 36), 3)
        # head with radial shading
        head_g = radial_grad_surf(96, 96, main, shade(main, 0.5), center=(32, 28), radius=50)
        clip_to_circle(head_g, (48, 48), 48)
        surf.blit(head_g, (cx - 48, cy - 88))
        pygame.draw.circle(surf, outline, (cx, cy - 40), 48, 4)
        # blazing crown (larger, taller, with inner glow core)
        for sx in (-30, -10, 10, 30):
            flame = [(cx + sx, cy - 72), (cx + sx - 8, cy - 110), (cx + sx + 8, cy - 72)]
            fg = vgrad_surf(20, 40, (255, 240, 140), shade(accent, 0.9))
            m = pygame.Surface((20, 40), pygame.SRCALPHA)
            pygame.draw.polygon(m, (255, 255, 255, 255),
                                [(p[0] - (cx + sx - 10), p[1] - (cy - 72)) for p in flame])
            fg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surf.blit(fg, (cx + sx - 10, cy - 72))
            # inner bright streak in each flame
            pygame.draw.line(surf, (255, 255, 200), (cx + sx, cy - 70), (cx + sx, cy - 106), 2)
            pygame.draw.polygon(surf, outline, flame, 3)
        for sx in (-18, 18):
            _glowing_eye(surf, (cx + sx, cy - 42), (255, 240, 120), (255, 200, 60), r_core=9, r_glow=16)
        # flame aura (orbiting embers with glow + smoke wisps)
        for i in range(8):
            ang = i * math.pi / 4
            ex = int(cx + math.cos(ang) * 72)
            ey2 = int(cy + math.sin(ang) * 52)
            halo = soft_glow(24, 24, (255, 180, 80), 140, center=(12, 12), radius=12, falloff=1.45)
            surf.blit(halo, (ex - 12, ey2 - 12))
            pygame.draw.circle(surf, (255, 240, 160), (ex, ey2), 5)
            pygame.draw.circle(surf, (255, 255, 255), (ex - 2, ey2 - 2), 2)
            # smoke trail behind each ember
            smoke = pygame.Surface((10, 6), pygame.SRCALPHA)
            pygame.draw.ellipse(smoke, (40, 20, 20, 60), smoke.get_rect())
            surf.blit(smoke, (ex - 14, ey2))

# ---------------------------------------------------------------------------
# Skill icons
# ---------------------------------------------------------------------------
def draw_skill_icon(surf, element, kind):
    cx, cy = 64, 64
    outline = (30, 26, 40)
    main, light, dark = ELEMENT_COLORS[element]
    # base disc — radial gradient for depth (light upper-left -> dark edge)
    disc = radial_grad_surf(112, 112, shade(main, 1.15), shade(dark, 0.7),
                            center=(40, 38), radius=58)
    clip_to_circle(disc, (56, 56), 56)
    surf.blit(disc, (8, 8))
    pygame.draw.circle(surf, outline, (cx, cy), 56, 3)
    # inner ring highlight
    pygame.draw.circle(surf, light, (cx, cy), 50, 2)
    # soft inner glow
    inner = soft_glow(96, 96, light, 50, center=(48, 44), radius=48, falloff=1.6)
    surf.blit(inner, (16, 16))

    if kind == "slash":
        # curved slash with a bright edge + motion trail
        pygame.draw.polygon(surf, light, [(cx - 24, cy + 20), (cx + 24, cy - 20), (cx + 30, cy - 10), (cx - 18, cy + 30)])
        pygame.draw.polygon(surf, (255, 255, 255), [(cx - 20, cy + 16), (cx + 20, cy - 16), (cx + 24, cy - 8), (cx - 14, cy + 26)])
        pygame.draw.polygon(surf, outline, [(cx - 24, cy + 20), (cx + 24, cy - 20), (cx + 30, cy - 10), (cx - 18, cy + 30)], 3)
    elif kind == "bolt":
        # lightning bolt with a glow + bright core
        bolt_pts = [(cx - 6, cy - 28), (cx + 14, cy - 6), (cx + 2, cy - 4), (cx + 12, cy + 28), (cx - 12, cy + 4), (cx + 2, cy + 2)]
        bg = soft_glow(60, 60, light, 90, center=(30, 30), radius=28, falloff=1.5)
        surf.blit(bg, (34, 34))
        pygame.draw.polygon(surf, light, bolt_pts)
        pygame.draw.polygon(surf, (255, 255, 230),
                            [(cx - 4, cy - 24), (cx + 10, cy - 6), (cx, cy - 4), (cx + 8, cy + 24), (cx - 8, cy + 4), (cx + 2, cy + 2)])
        pygame.draw.polygon(surf, outline, bolt_pts, 2)
    elif kind == "arrow":
        # arrow shaft + fletching with a gradient
        pygame.draw.line(surf, light, (cx - 26, cy + 22), (cx + 22, cy - 22), 6)
        pygame.draw.line(surf, (255, 255, 255), (cx - 26, cy + 22), (cx + 22, cy - 22), 2)
        pygame.draw.polygon(surf, (255, 255, 255), [(cx + 22, cy - 22), (cx + 6, cy - 30), (cx + 30, cy - 6)])
        # fletching (back fins)
        pygame.draw.polygon(surf, shade(light, 0.7), [(cx - 26, cy + 22), (cx - 30, cy + 16), (cx - 22, cy + 18)])
        pygame.draw.line(surf, outline, (cx - 26, cy + 22), (cx + 22, cy - 22), 2)
    elif kind == "heal":
        # plus sign with a soft glow
        heal_glow = soft_glow(56, 56, light, 80, center=(28, 28), radius=26, falloff=1.6)
        surf.blit(heal_glow, (36, 36))
        pygame.draw.rect(surf, (255, 255, 255), (cx - 8, cy - 24, 16, 48), border_radius=4)
        pygame.draw.rect(surf, (255, 255, 255), (cx - 24, cy - 8, 48, 16), border_radius=4)
        pygame.draw.rect(surf, outline, (cx - 8, cy - 24, 16, 48), 2, border_radius=4)
        pygame.draw.rect(surf, outline, (cx - 24, cy - 8, 48, 16), 2, border_radius=4)
    elif kind == "shield":
        # shield with a radial gradient + emblem
        sh_pts = [(cx, cy - 26), (cx + 22, cy - 14), (cx + 22, cy + 10), (cx, cy + 28), (cx - 22, cy + 10), (cx - 22, cy - 14)]
        shg = diag_grad_surf(48, 56, (255, 255, 255), shade(light, 0.7))
        m = pygame.Surface((48, 56), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - (cx - 24), p[1] - (cy - 26)) for p in sh_pts])
        shg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(shg, (cx - 24, cy - 26))
        pygame.draw.polygon(surf, outline, sh_pts, 3)
        pygame.draw.circle(surf, light, (cx, cy), 6)
        pygame.draw.circle(surf, (255, 255, 255), (cx - 2, cy - 2), 3)
    elif kind == "orb":
        # orb with radial gradient + specular shine + glow
        og = soft_glow(56, 56, light, 90, center=(28, 28), radius=26, falloff=1.5)
        surf.blit(og, (36, 36))
        orb = radial_grad_surf(44, 44, light, shade(dark, 0.6), center=(16, 14), radius=22)
        clip_to_circle(orb, (22, 22), 22)
        surf.blit(orb, (cx - 22, cy - 22))
        pygame.draw.circle(surf, (255, 255, 255), (cx - 7, cy - 7), 7)
        pygame.draw.circle(surf, (255, 255, 255), (cx - 3, cy - 3), 3)
        pygame.draw.circle(surf, outline, (cx, cy), 22, 3)
    elif kind == "aoe":
        # concentric rings with a soft glow center
        center_glow = soft_glow(60, 60, light, 110, center=(30, 30), radius=28, falloff=1.5)
        surf.blit(center_glow, (34, 34))
        for r, a in [(28, 255), (20, 255), (12, 255)]:
            s = pygame.Surface((2 * r + 4, 2 * r + 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (*light, a), (r + 2, r + 2), r, 4)
            surf.blit(s, (cx - r - 2, cy - r - 2))
        pygame.draw.circle(surf, outline, (cx, cy), 28, 2)
    elif kind == "curse":
        # dark curse sigil — outer ring with an inner void
        cg = soft_glow(56, 56, dark, 90, center=(28, 28), radius=26, falloff=1.5)
        surf.blit(cg, (36, 36))
        pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 24)
        pygame.draw.circle(surf, outline, (cx, cy), 24, 3)
        # inner void with a radial gradient
        void = radial_grad_surf(26, 26, shade(dark, 1.2), dark, center=(10, 9), radius=13)
        clip_to_circle(void, (13, 13), 12)
        surf.blit(void, (cx - 13, cy - 13))
        pygame.draw.circle(surf, outline, (cx, cy), 12, 2)
    elif kind == "buff":
        # upward triangle (buff) with a gradient + glow
        bg_glow = soft_glow(56, 56, light, 80, center=(28, 28), radius=26, falloff=1.6)
        surf.blit(bg_glow, (36, 36))
        tri = [(cx, cy - 26), (cx + 22, cy + 18), (cx - 22, cy + 18)]
        tg = vgrad_surf(48, 46, (255, 255, 255), shade(light, 0.7))
        m = pygame.Surface((48, 46), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - (cx - 24), p[1] - (cy - 26)) for p in tri])
        tg.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(tg, (cx - 24, cy - 26))
        pygame.draw.polygon(surf, outline, tri, 3)
        pygame.draw.line(surf, outline, (cx, cy - 14), (cx, cy + 8), 3)
        pygame.draw.circle(surf, outline, (cx, cy + 14), 3)


# ---------------------------------------------------------------------------
# Backgrounds
# ---------------------------------------------------------------------------
def make_title_bg(path):
    surf = pygame.Surface((1280, 720))
    vgrad(surf, SKY_TOP, SKY_BOTTOM)
    # stars
    for _ in range(120):
        x = random.randint(0, 1280)
        y = random.randint(0, 420)
        b = random.randint(120, 255)
        pygame.draw.circle(surf, (b, b, b), (x, y), random.choice([1, 1, 2]))
    # moon
    rgrad(surf, (960, 160), (255, 250, 220), (240, 220, 170), 120)
    pygame.draw.circle(surf, (255, 250, 230), (960, 160), 90)
    # distant mountains
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
    # foreground silhouette castle
    pygame.draw.rect(surf, (28, 24, 44), (520, 380, 240, 200))
    for tx in (540, 620, 700):
        pygame.draw.rect(surf, (28, 24, 44), (tx, 340, 40, 240))
        pygame.draw.polygon(surf, (28, 24, 44), [(tx, 340), (tx + 20, 300), (tx + 40, 340)])
    pygame.draw.rect(surf, (28, 24, 44), (620, 300, 40, 60))
    pygame.draw.polygon(surf, (40, 34, 60), [(620, 300), (640, 270), (660, 300)])
    # logo glow handled in code
    pygame.image.save(surf, path)

def make_battle_bg(path, theme):
    surf = pygame.Surface((1280, 720))
    if theme == "plains":
        vgrad(surf, (120, 180, 220), (200, 230, 240), target_h=420)
        grass = pygame.Rect(0, 420, 1280, 300)
        pygame.draw.rect(surf, (90, 170, 90), grass)
        for x in range(0, 1280, 40):
            pygame.draw.polygon(surf, (60, 140, 70), [(x, 420), (x + 20, 400), (x + 40, 420)])
        # distant hills
        pygame.draw.ellipse(surf, (120, 170, 120), (-100, 360, 500, 160))
        pygame.draw.ellipse(surf, (110, 160, 110), (800, 360, 600, 160))
        # sun
        rgrad(surf, (200, 120), (255, 240, 200), (255, 200, 120), 90)
    elif theme == "forest":
        vgrad(surf, (90, 150, 120), (140, 180, 150), target_h=420)
        pygame.draw.rect(surf, (50, 90, 60), (0, 420, 1280, 300))
        for x in range(-40, 1280, 90):
            pygame.draw.rect(surf, (60, 40, 30), (x, 300, 20, 200))
            pygame.draw.circle(surf, (40, 90, 60), (x + 10, 300), 60)
            pygame.draw.circle(surf, (50, 110, 70), (x - 10, 280), 50)
            pygame.draw.circle(surf, (60, 130, 80), (x + 30, 290), 50)
    elif theme == "cave":
        vgrad(surf, (40, 30, 50), (70, 50, 80))
        pygame.draw.rect(surf, (30, 24, 36), (0, 480, 1280, 240))
        for x in range(0, 1280, 120):
            pygame.draw.polygon(surf, (50, 40, 60), [(x, 480), (x + 60, 420), (x + 120, 480)])
        # crystals
        for cx, col in [(200, (120, 200, 255)), (1080, (200, 120, 255)), (640, (120, 255, 200))]:
            pygame.draw.polygon(surf, col, [(cx, 480), (cx - 20, 420), (cx, 360), (cx + 20, 420)])
            pygame.draw.polygon(surf, (255, 255, 255), [(cx, 480), (cx - 6, 440), (cx, 400)])
    elif theme == "castle":
        vgrad(surf, (60, 40, 80), (120, 60, 100))
        pygame.draw.rect(surf, (40, 30, 50), (0, 460, 1280, 260))
        # castle silhouette
        pygame.draw.rect(surf, (30, 24, 40), (440, 280, 400, 220))
        for tx in (440, 560, 680, 800):
            pygame.draw.rect(surf, (30, 24, 40), (tx, 240, 80, 260))
            pygame.draw.polygon(surf, (30, 24, 40), [(tx, 240), (tx + 40, 200), (tx + 80, 240)])
        # windows
        for wx in (480, 720):
            pygame.draw.rect(surf, (255, 180, 80), (wx, 360, 40, 60))
        # moon
        rgrad(surf, (980, 140), (255, 250, 220), (220, 200, 160), 70)
    elif theme == "void":
        vgrad(surf, (20, 10, 30), (60, 20, 70))
        for _ in range(80):
            x = random.randint(0, 1280); y = random.randint(0, 720)
            pygame.draw.circle(surf, (random.randint(120, 200), 80, 160), (x, y), random.choice([1, 2]))
        # swirling portal
        rgrad(surf, (640, 380), (180, 80, 200), (40, 10, 60), 300)
        pygame.draw.circle(surf, (20, 0, 30), (640, 380), 80)
    pygame.image.save(surf, path)

def make_map_bg(path):
    surf = pygame.Surface((1280, 720))
    vgrad(surf, (44, 60, 90), (28, 36, 60))
    # parchment overlay
    parch = pygame.Surface((1080, 600), pygame.SRCALPHA)
    parch.fill((236, 220, 180, 230))
    pygame.draw.rect(parch, (120, 90, 50), parch.get_rect(), 6, border_radius=20)
    # subtle stains
    for _ in range(40):
        x = random.randint(0, 1080); y = random.randint(0, 600)
        pygame.draw.circle(parch, (210, 190, 150, 60), (x, y), random.randint(8, 30))
    surf.blit(parch, (100, 60))
    # decorative compass
    cx, cy = 160, 620
    pygame.draw.circle(surf, (120, 90, 50), (cx, cy), 34, 3)
    for a in range(0, 360, 45):
        rad = math.radians(a)
        pygame.draw.line(surf, (120, 90, 50), (cx, cy), (cx + math.cos(rad) * 34, cy + math.sin(rad) * 34), 2)
    pygame.image.save(surf, path)

# helper for partial gradient height
def vgrad(surface, top, bottom, target_h=None):
    w, h = surface.get_size()
    hh = target_h or h
    for y in range(hh):
        t = y / max(1, hh - 1)
        pygame.draw.line(surface, lerp_color(top, bottom, t), (0, y), (w, y))

# ---------------------------------------------------------------------------
# UI elements
# ---------------------------------------------------------------------------
def make_ui():
    # button (normal + hover) 240x64 — gradient fill + top gloss + rim light
    for state, col in [("normal", (60, 70, 110)), ("hover", (90, 110, 170))]:
        s = pygame.Surface((240, 64), pygame.SRCALPHA)
        bg = vgrad_surf(240, 64, shade(col, 1.18), shade(col, 0.7))
        clip_to_rect(bg, pygame.Rect(0, 0, 240, 64), border_radius=16)
        s.blit(bg, (0, 0))
        # top-edge highlight (lit from above)
        hi = soft_glow(232, 20, (255, 255, 255), 120, center=(116, 10), radius=120, falloff=1.4)
        s.blit(hi, (4, 4))
        pygame.draw.rect(s, (200, 220, 255), s.get_rect(), 3, border_radius=16)
        pygame.image.save(s, os.path.join(ASSET_DIR, "ui", f"button_{state}.png"))

    # panel — dark glass with a soft top sheen
    s = pygame.Surface((400, 300), pygame.SRCALPHA)
    pg = diag_grad_surf(400, 300, (50, 48, 76), (24, 22, 42))
    clip_to_rect(pg, pygame.Rect(0, 0, 400, 300), border_radius=18)
    s.blit(pg, (0, 0))
    sheen = soft_glow(392, 60, (255, 255, 255), 50, center=(196, 26), radius=200, falloff=1.6)
    s.blit(sheen, (4, 4))
    pygame.draw.rect(s, (200, 200, 255), s.get_rect(), 3, border_radius=18)
    pygame.image.save(s, os.path.join(ASSET_DIR, "ui", "panel.png"))

    # rarity frames 220x280 — gradient fill + colored rim + inner shine + corner gems
    for rar, col in RARITY_COLORS.items():
        s = pygame.Surface((220, 280), pygame.SRCALPHA)
        fg = diag_grad_surf(220, 280, shade(col, 1.2), shade(col, 0.4))
        clip_to_rect(fg, pygame.Rect(0, 0, 220, 280), border_radius=16)
        s.blit(fg, (0, 0))
        # dark inner panel for contrast
        ip = pygame.Surface((208, 268), pygame.SRCALPHA)
        pygame.draw.rect(ip, (20, 20, 30, 210), ip.get_rect(), border_radius=12)
        s.blit(ip, (6, 6))
        # top sheen
        sheen = soft_glow(200, 26, (255, 255, 255), 70, center=(100, 12), radius=110, falloff=1.6)
        s.blit(sheen, (10, 8))
        pygame.draw.rect(s, col, s.get_rect(), 5, border_radius=16)
        pygame.draw.rect(s, shade(col, 1.3), (8, 8, 204, 24), border_radius=12)
        # corner accent gems
        for cx2, cy2 in ((14, 14), (206, 14), (14, 266), (206, 266)):
            cg = radial_grad_surf(12, 12, shade(col, 1.3), shade(col, 0.4), center=(5, 4), radius=6)
            clip_to_circle(cg, (6, 6), 5)
            s.blit(cg, (cx2 - 6, cy2 - 6))
        pygame.image.save(s, os.path.join(ASSET_DIR, "ui", f"frame_{rar}.png"))

    # gem icon — faceted crystal with specular
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    gem = radial_grad_surf(56, 56, (220, 245, 255), (40, 90, 150), center=(22, 18), radius=28)
    clip_to_polygon(gem, [(32, 6), (56, 28), (32, 58), (8, 28)])
    s.blit(gem, (0, 0))
    pygame.draw.polygon(s, (220, 245, 255), [(32, 6), (44, 28), (32, 30), (20, 28)])
    pygame.draw.polygon(s, (40, 90, 140), [(32, 6), (56, 28), (32, 58), (8, 28)], 3)
    pygame.draw.circle(s, (255, 255, 255), (24, 20), 4)
    pygame.image.save(s, os.path.join(ASSET_DIR, "ui", "gem.png"))

    # gold icon — coin with radial sheen + edge
    s = pygame.Surface((64, 64), pygame.SRCALPHA)
    coin = radial_grad_surf(56, 56, (255, 240, 160), (180, 140, 40), center=(22, 18), radius=28)
    clip_to_circle(coin, (28, 28), 26)
    s.blit(coin, (6, 6))
    pygame.draw.circle(s, (255, 230, 120), (32, 32), 26, 3)
    pygame.draw.circle(s, (200, 160, 40), (32, 32), 18, 0)
    pygame.draw.circle(s, (255, 250, 200), (24, 24), 6)
    pygame.image.save(s, os.path.join(ASSET_DIR, "ui", "gold.png"))

    # star (rarity marker) — radial-tinted star + specular dot
    for rar, col in RARITY_COLORS.items():
        s = pygame.Surface((48, 48), pygame.SRCALPHA)
        draw_star(s, 24, 24, 20, 9, shade(col, 1.15), (255, 255, 255))
        # specular highlight on the upper point
        pygame.draw.circle(s, (255, 255, 255), (24, 16), 3)
        pygame.image.save(s, os.path.join(ASSET_DIR, "ui", f"star_{rar}.png"))

    # element badge 64x64 — radial element disc + glyph + specular
    for el, (main, light, dark) in ELEMENT_COLORS.items():
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        disc = radial_grad_surf(60, 60, shade(main, 1.25), shade(dark, 0.6), center=(22, 18), radius=32)
        clip_to_circle(disc, (30, 30), 30)
        s.blit(disc, (2, 2))
        pygame.draw.circle(s, (255, 255, 255), (32, 32), 30, 2)
        draw_element_glyph(s, 32, 32, el, light)
        pygame.draw.circle(s, (255, 255, 255), (24, 22), 4)
        pygame.image.save(s, os.path.join(ASSET_DIR, "ui", f"element_{el}.png"))

    # cursor / selector arrow — gradient fill + edge
    s = pygame.Surface((48, 48), pygame.SRCALPHA)
    cur = diag_grad_surf(40, 40, (255, 240, 120), (180, 130, 30))
    clip_to_polygon(cur, [(8, 8), (8, 34), (18, 26), (28, 40), (34, 36), (24, 22), (36, 22)])
    s.blit(cur, (0, 0))
    pygame.draw.polygon(s, (120, 90, 30), [(8, 8), (8, 34), (18, 26), (28, 40), (34, 36), (24, 22), (36, 22)], 2)
    pygame.image.save(s, os.path.join(ASSET_DIR, "ui", "cursor.png"))

    # victory / defeat banners — gradient + rim + sheen
    for name, col in [("victory", (255, 210, 80)), ("defeat", (200, 60, 80))]:
        s = pygame.Surface((600, 120), pygame.SRCALPHA)
        bg = diag_grad_surf(600, 120, shade(col, 1.15), shade(col, 0.4))
        clip_to_rect(bg, pygame.Rect(0, 0, 600, 120), border_radius=20)
        s.blit(bg, (0, 0))
        sheen = soft_glow(580, 40, (255, 255, 255), 60, center=(290, 18), radius=300, falloff=1.6)
        s.blit(sheen, (10, 8))
        pygame.draw.rect(s, col, s.get_rect(), 5, border_radius=20)
        pygame.image.save(s, os.path.join(ASSET_DIR, "ui", f"banner_{name}.png"))

def make_shop_bg(path):
    surf = pygame.Surface((1280, 720))
    vgrad(surf, (60, 40, 70), (30, 20, 40))
    # wooden counter
    pygame.draw.rect(surf, (80, 50, 30), (0, 520, 1280, 200))
    for x in range(0, 1280, 60):
        pygame.draw.line(surf, (60, 38, 22), (x, 520), (x, 720), 2)
    # hanging lanterns
    for x in (200, 640, 1080):
        pygame.draw.line(surf, (40, 30, 20), (x, 0), (x, 120), 2)
        pygame.draw.circle(surf, (255, 180, 80), (x, 130), 22)
        pygame.draw.circle(surf, (255, 220, 140), (x, 130), 22, 2)
        # glow
        glow = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 200, 100, 60), (60, 60), 60)
        surf.blit(glow, (x - 60, 70))
    # shelves with bottles
    for sy in (240, 360):
        pygame.draw.rect(surf, (50, 34, 22), (120, sy, 1040, 12))
        for bx in range(160, 1120, 120):
            pygame.draw.rect(surf, (60, 90, 140), (bx, sy - 50, 26, 50), border_radius=6)
            pygame.draw.rect(surf, (120, 160, 220), (bx + 4, sy - 46, 18, 30))
            pygame.draw.rect(surf, (40, 30, 20), (bx + 6, sy - 56, 14, 8))
    pygame.image.save(surf, path)

def _flask(liquid_top, liquid_bot, cap_col=(200, 200, 210), body_rect=(44, 44, 40, 56),
           cap_pts=((44, 30), (84, 30), (80, 44), (48, 44))):
    """A potion flask with a gradient liquid + cork + specular shine."""
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    # cork
    pygame.draw.polygon(s, cap_col, list(cap_pts))
    pygame.draw.polygon(s, (30, 20, 30), list(cap_pts), 2)
    # liquid body with vertical gradient
    bx, by, bw, bh = body_rect
    liq = vgrad_surf(bw, bh, liquid_top, liquid_bot)
    clip_to_rect(liq, pygame.Rect(0, 0, bw, bh), border_radius=10)
    s.blit(liq, (bx, by))
    # specular highlight streak
    hl = pygame.Surface((10, bh - 8), pygame.SRCALPHA)
    pygame.draw.rect(hl, (255, 255, 255, 120), hl.get_rect(), border_radius=5)
    s.blit(hl, (bx + 5, by + 4))
    pygame.draw.rect(s, (30, 20, 30), (bx, by, bw, bh), 3, border_radius=10)
    # bubble
    pygame.draw.circle(s, shade(liquid_top, 1.3), (bx + 8, by + 10), 4)
    return s

def _blade_poly(pts, edge=(255, 255, 255), base=(200, 200, 215), dark=(150, 150, 170)):
    """A sword blade polygon with a horizontal metal gradient + bright edge."""
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    # bounding box of the blade for the gradient
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx = min(xs), max(xs); miny, maxy = min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = hgrad_surf(w, h, base, dark)
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (30, 26, 40), pts, 2)
    # bright edge (left side)
    pygame.draw.line(s, edge, (minx + 1, miny + 2), (minx + 1, maxy - 2), 2)
    return s

def make_items():
    """Generate item icons (consumables + equipment) with gradient shading."""
    items = []

    # --- Consumables ---
    # HP Potion - red flask
    s = _flask((220, 80, 90), (160, 30, 50))
    items.append(("hp_potion", s))

    # MP Potion - blue flask
    s = _flask((90, 160, 240), (40, 90, 200))
    pygame.draw.circle(s, (200, 230, 255), (52, 52), 3)
    items.append(("mp_potion", s))

    # Full Elixir - golden flask
    s = _flask((255, 220, 90), (200, 150, 30), cap_col=(220, 220, 230),
               body_rect=(42, 42, 44, 60), cap_pts=((40, 26), (88, 26), (82, 42), (46, 42)))
    # sparkle
    pygame.draw.line(s, (255, 255, 220), (64, 56), (64, 70), 2)
    pygame.draw.line(s, (255, 255, 220), (58, 63), (70, 63), 2)
    # soft glow
    g = soft_glow(40, 40, (255, 230, 120), 80, radius=18, falloff=1.5)
    s.blit(g, (44, 50))
    items.append(("full_elixir", s))

    # Revive Scroll
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    scroll = vgrad_surf(52, 80, (245, 235, 200), (200, 180, 140))
    clip_to_rect(scroll, pygame.Rect(0, 0, 52, 80), border_radius=6)
    s.blit(scroll, (38, 24))
    pygame.draw.rect(s, (180, 150, 100), (38, 24, 52, 80), 3, border_radius=6)
    # seal (radial gradient)
    seal = radial_grad_surf(26, 26, (255, 100, 100), (160, 30, 30), center=(10, 9), radius=13)
    clip_to_circle(seal, (13, 13), 12)
    s.blit(seal, (51, 37))
    pygame.draw.circle(s, (30, 20, 30), (64, 50), 12, 2)
    # cross
    pygame.draw.rect(s, (255, 245, 245), (61, 42, 6, 16))
    pygame.draw.rect(s, (255, 245, 245), (55, 47, 18, 6))
    items.append(("revive_scroll", s))

    # Bomb
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    bomb = radial_grad_surf(60, 60, (90, 90, 110), (30, 30, 45), center=(22, 20), radius=32)
    clip_to_circle(bomb, (30, 30), 30)
    s.blit(bomb, (34, 44))
    pygame.draw.circle(s, (70, 70, 90), (64, 74), 30, 3)
    pygame.draw.rect(s, (140, 95, 50), (60, 40, 8, 16))
    pygame.draw.rect(s, (30, 26, 30), (60, 40, 8, 16), 1)
    # spark glow
    sg = soft_glow(28, 28, (255, 220, 80), 130, radius=12, falloff=1.4)
    s.blit(sg, (50, 24))
    pygame.draw.circle(s, (255, 220, 80), (64, 38), 6)
    pygame.draw.circle(s, (255, 255, 200), (64, 38), 3)
    # shine
    pygame.draw.circle(s, (160, 160, 180), (54, 64), 7)
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
    g = hgrad_surf(w, h, (255, 130, 70), (170, 50, 30))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (255, 160, 60), pts, 2)
    # serrations
    for i in range(4):
        y = 30 + i * 14
        pygame.draw.polygon(s, (255, 200, 80), [(54, y), (48, y + 6), (54, y + 10)])
        pygame.draw.polygon(s, (255, 200, 80), [(74, y), (80, y + 6), (74, y + 10)])
    pygame.draw.rect(s, (140, 95, 50), (48, 92, 32, 8))
    pygame.draw.rect(s, (30, 26, 40), (48, 92, 32, 8), 1)
    items.append(("dragon_fang", s))

    # Mage Rod
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    shaft = vgrad_surf(8, 80, (150, 100, 60), (90, 60, 35))
    clip_to_rect(shaft, pygame.Rect(0, 0, 8, 80))
    s.blit(shaft, (60, 30))
    pygame.draw.rect(s, (30, 26, 30), (60, 30, 8, 80), 2)
    # orb (radial + glow)
    og = soft_glow(40, 40, (120, 180, 255), 100, radius=18, falloff=1.5)
    s.blit(og, (44, 8))
    orb = radial_grad_surf(36, 36, (200, 230, 255), (60, 120, 200), center=(14, 12), radius=18)
    clip_to_circle(orb, (18, 18), 18)
    s.blit(orb, (46, 10))
    pygame.draw.circle(s, (255, 255, 255), (58, 22), 6)
    pygame.draw.circle(s, (255, 255, 255), (60, 24), 3)
    pygame.draw.circle(s, (30, 26, 40), (64, 28), 18, 2)
    items.append(("mage_rod", s))

    # Leather Armor
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(40, 40), (88, 40), (96, 96), (32, 96)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = diag_grad_surf(w, h, (150, 100, 60), (90, 60, 30))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (30, 26, 30), pts, 3)
    # straps
    pygame.draw.rect(s, (90, 60, 30), (58, 40, 12, 56))
    pygame.draw.rect(s, (70, 45, 25), (44, 60, 40, 8))
    # buckle gem
    bgem = radial_grad_surf(14, 14, (255, 220, 100), (180, 140, 40), center=(5, 4), radius=7)
    clip_to_circle(bgem, (7, 7), 6)
    s.blit(bgem, (57, 49))
    pygame.draw.circle(s, (30, 26, 30), (64, 56), 6, 1)
    items.append(("leather_armor", s))

    # Plate Mail
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(38, 38), (90, 38), (98, 100), (30, 100)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = diag_grad_surf(w, h, (200, 210, 230), (110, 120, 145))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (30, 30, 40), pts, 3)
    for i in range(4):
        y = 44 + i * 14
        pygame.draw.line(s, (220, 230, 245), (36, y), (92, y), 2)
    # chest gem
    cgem = radial_grad_surf(18, 18, (255, 255, 255), (120, 130, 150), center=(7, 6), radius=9)
    clip_to_circle(cgem, (9, 9), 8)
    s.blit(cgem, (55, 43))
    pygame.draw.circle(s, (120, 130, 150), (64, 52), 8, 2)
    items.append(("plate_mail", s))

    # Aether Vest
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(36, 38), (92, 38), (100, 102), (28, 102)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = diag_grad_surf(w, h, (180, 130, 240), (90, 60, 140))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (220, 160, 255), pts, 3)
    # glowing runes
    for ry in (56, 76):
        rg = soft_glow(20, 20, (255, 240, 180), 120, radius=9, falloff=1.5)
        s.blit(rg, (54, ry - 9))
        pygame.draw.circle(s, (255, 240, 180), (64, ry), 5)
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
        g = diag_grad_surf(w, h, (150, 100, 60), (90, 60, 30))
        m = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
        g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        s.blit(g, (minx, miny))
        pygame.draw.polygon(s, (30, 26, 30), pts, 2)
    # wing (with gradient + glow)
    wg = diag_grad_surf(34, 18, (255, 255, 255), (180, 200, 240))
    m = pygame.Surface((34, 18), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(50, 48), (74, 40), (80, 56), (54, 56)])
    pygame.draw.polygon(m, (0, 0, 0, 0), [(50, 48), (74, 40), (80, 56), (54, 56)])
    # simpler: just draw the wing with a gradient via a clip
    wpts = [(50, 48), (74, 40), (80, 56), (54, 56)]
    wxs = [p[0] for p in wpts]; wys = [p[1] for p in wpts]
    wminx, wmaxx, wminy, wmaxy = min(wxs), max(wxs), min(wys), max(wys)
    ww, whh = wmaxx - wminx, wmaxy - wminy
    wg2 = diag_grad_surf(ww, whh, (255, 255, 255), (180, 200, 240))
    wm = pygame.Surface((ww, whh), pygame.SRCALPHA)
    pygame.draw.polygon(wm, (255, 255, 255, 255), [(p[0] - wminx, p[1] - wminy) for p in wpts])
    wg2.blit(wm, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(wg2, (wminx, wminy))
    items.append(("swift_boots", s))

    # Mana Pendant
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pygame.draw.line(s, (210, 190, 90), (64, 24), (40, 56), 4)
    pygame.draw.line(s, (210, 190, 90), (64, 24), (88, 56), 4)
    # gem (radial + glow)
    pg = soft_glow(48, 48, (120, 180, 255), 110, radius=22, falloff=1.5)
    s.blit(pg, (40, 46))
    gem = radial_grad_surf(44, 44, (200, 230, 255), (40, 90, 200), center=(16, 14), radius=22)
    clip_to_circle(gem, (22, 22), 22)
    s.blit(gem, (42, 48))
    pygame.draw.circle(s, (255, 255, 255), (56, 62), 7)
    pygame.draw.circle(s, (255, 255, 255), (58, 64), 3)
    pygame.draw.circle(s, (30, 26, 50), (64, 70), 22, 2)
    items.append(("mana_pendant", s))

    # Hero Crest
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(64, 24), (88, 48), (80, 92), (48, 92), (40, 48)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = diag_grad_surf(w, h, (255, 220, 120), (200, 150, 40))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (255, 220, 120), pts, 3)
    # emblem star
    draw_star(s, 64, 58, 14, 5, (255, 255, 255), (255, 255, 255))
    pygame.draw.circle(s, (180, 140, 40), (64, 58), 14, 2)
    items.append(("hero_crest", s))

    # --- new consumables (Phase B) ---
    # Mega Potion - big red flask
    s = _flask((240, 70, 80), (180, 30, 40), cap_col=(200, 200, 210),
               body_rect=(42, 42, 44, 60), cap_pts=((40, 26), (88, 26), (82, 42), (46, 42)))
    pygame.draw.circle(s, (255, 220, 220), (52, 52), 4)
    items.append(("mega_potion", s))

    # Ether - blue bottle
    s = _flask((70, 150, 250), (30, 80, 200), cap_col=(200, 200, 210),
               body_rect=(42, 42, 44, 60), cap_pts=((40, 26), (88, 26), (82, 42), (46, 42)))
    pygame.draw.circle(s, (200, 230, 255), (52, 52), 4)
    items.append(("ether", s))

    # Mega Bomb - bigger bomb
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    bomb = radial_grad_surf(72, 72, (100, 100, 120), (30, 30, 45), center=(26, 24), radius=38)
    clip_to_circle(bomb, (36, 36), 36)
    s.blit(bomb, (28, 40))
    pygame.draw.circle(s, (70, 70, 90), (64, 76), 36, 3)
    pygame.draw.rect(s, (140, 95, 50), (60, 36, 8, 20))
    pygame.draw.rect(s, (30, 26, 30), (60, 36, 8, 20), 1)
    sg = soft_glow(32, 32, (255, 200, 80), 140, radius=14, falloff=1.4)
    s.blit(sg, (48, 16))
    pygame.draw.circle(s, (255, 200, 80), (64, 32), 8)
    pygame.draw.circle(s, (255, 255, 200), (64, 32), 4)
    pygame.draw.circle(s, (160, 160, 180), (52, 66), 9)
    items.append(("mega_bomb", s))

    # --- new equipment (Phase B) ---
    # Inferno Blade - fiery sword
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(64, 10), (72, 14), (72, 82), (64, 96), (56, 82), (56, 14)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = vgrad_surf(w, h, (255, 220, 120), (220, 90, 40))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (255, 200, 80), pts, 2)
    # ember glow along the blade
    eg = soft_glow(20, 80, (255, 180, 80), 90, center=(10, 40), radius=10, falloff=1.5)
    s.blit(eg, (54, 14))
    for i in range(5):
        y = 22 + i * 12
        pygame.draw.polygon(s, (255, 220, 120), [(56, y), (50, y + 6), (56, y + 8)])
        pygame.draw.polygon(s, (255, 220, 120), [(72, y), (78, y + 6), (72, y + 8)])
    pygame.draw.rect(s, (140, 95, 50), (48, 92, 32, 8))
    pygame.draw.rect(s, (30, 26, 40), (48, 92, 32, 8), 1)
    items.append(("inferno_blade", s))

    # Frost Staff - icy staff
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    shaft = vgrad_surf(8, 80, (150, 180, 210), (90, 120, 160))
    clip_to_rect(shaft, pygame.Rect(0, 0, 8, 80))
    s.blit(shaft, (60, 30))
    pygame.draw.rect(s, (30, 30, 50), (60, 30, 8, 80), 2)
    # crystal head (radial + glow)
    cg = soft_glow(48, 48, (180, 220, 255), 110, radius=22, falloff=1.5)
    s.blit(cg, (40, 2))
    cryst = radial_grad_surf(40, 40, (230, 245, 255), (90, 150, 210), center=(16, 14), radius=20)
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
    g = hgrad_surf(w, h, (180, 120, 240), (90, 50, 150))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (200, 140, 255), pts, 2)
    # void glow down the center
    vg = soft_glow(16, 80, (200, 160, 255), 100, center=(8, 40), radius=8, falloff=1.5)
    s.blit(vg, (56, 14))
    pygame.draw.rect(s, (100, 70, 150), (60, 92, 8, 24))
    pygame.draw.rect(s, (30, 26, 50), (60, 92, 8, 24), 1)
    items.append(("void_blade", s))

    # Guardian Aegis - big shield
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(64, 18), (96, 36), (96, 70), (64, 100), (32, 70), (32, 36)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = diag_grad_surf(w, h, (220, 235, 250), (120, 150, 190))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (30, 30, 50), pts, 3)
    # boss gem (radial + glow)
    bg = soft_glow(36, 36, (255, 240, 120), 110, radius=16, falloff=1.5)
    s.blit(bg, (46, 38))
    gem = radial_grad_surf(30, 30, (255, 250, 180), (180, 150, 40), center=(12, 10), radius=15)
    clip_to_circle(gem, (15, 15), 14)
    s.blit(gem, (49, 41))
    pygame.draw.circle(s, (255, 255, 255), (60, 50), 4)
    pygame.draw.circle(s, (180, 160, 60), (64, 58), 14, 2)
    items.append(("guardian_aegis", s))

    # Shadow Cloak - hooded cloak
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pts = [(40, 56), (88, 56), (96, 104), (32, 104)]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, h = maxx - minx, maxy - miny
    g = vgrad_surf(w, h, (100, 80, 140), (40, 30, 70))
    m = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.polygon(m, (255, 255, 255, 255), [(p[0] - minx, p[1] - miny) for p in pts])
    g.blit(m, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    s.blit(g, (minx, miny))
    pygame.draw.polygon(s, (40, 30, 70), pts, 3)
    # hood (radial)
    hood = radial_grad_surf(36, 36, (90, 70, 130), (30, 20, 50), center=(14, 12), radius=18)
    clip_to_circle(hood, (18, 18), 18)
    s.blit(hood, (46, 22))
    pygame.draw.circle(s, (30, 20, 50), (64, 40), 18, 2)
    items.append(("shadow_cloak", s))

    # Berserker Ring - red ring
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    ring = radial_grad_surf(68, 68, (255, 100, 100), (140, 30, 30), center=(26, 24), radius=34)
    clip_to_circle(ring, (34, 34), 34)
    s.blit(ring, (30, 30))
    pygame.draw.circle(s, (255, 220, 120), (64, 64), 34, 3)
    pygame.draw.circle(s, (30, 20, 30), (64, 64), 34, 2)
    pygame.draw.circle(s, (30, 20, 30), (64, 64), 18)
    # gem (radial + glow)
    gg = soft_glow(24, 24, (255, 220, 120), 120, radius=11, falloff=1.5)
    s.blit(gg, (52, 42))
    gem = radial_grad_surf(16, 16, (255, 250, 200), (200, 150, 40), center=(6, 5), radius=8)
    clip_to_circle(gem, (8, 8), 7)
    s.blit(gem, (56, 46))
    items.append(("berserker_ring", s))

    # Sage Amulet - purple amulet
    s = pygame.Surface((128, 128), pygame.SRCALPHA)
    pygame.draw.line(s, (210, 170, 90), (64, 24), (40, 56), 4)
    pygame.draw.line(s, (210, 170, 90), (64, 24), (88, 56), 4)
    # gem (radial + glow)
    pg = soft_glow(52, 52, (180, 120, 240), 110, radius=24, falloff=1.5)
    s.blit(pg, (38, 44))
    gem = radial_grad_surf(48, 48, (230, 190, 255), (90, 50, 150), center=(18, 15), radius=24)
    clip_to_circle(gem, (24, 24), 24)
    s.blit(gem, (40, 46))
    pygame.draw.circle(s, (255, 255, 255), (56, 62), 7)
    pygame.draw.circle(s, (255, 255, 255), (58, 64), 3)
    pygame.draw.circle(s, (60, 30, 90), (64, 70), 24, 2)
    items.append(("sage_amulet", s))

    for name, surf in items:
        pygame.image.save(surf, os.path.join(ASSET_DIR, "items", f"{name}.png"))

def draw_star(surf, cx, cy, r, points, color, inner_color):
    pts = []
    for i in range(points * 2):
        ang = -math.pi / 2 + math.pi * i / points
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, (40, 30, 20), pts, 2)

def draw_element_glyph(surf, cx, cy, element, color):
    if element == "fire":
        pygame.draw.polygon(surf, color, [(cx, cy - 14), (cx + 8, cy), (cx + 4, cy + 2), (cx + 12, cy + 12), (cx, cy + 6), (cx - 4, cy + 10), (cx - 8, cy), (cx - 4, cy - 4)])
    elif element == "water":
        pygame.draw.polygon(surf, color, [(cx, cy - 14), (cx + 12, cy + 6), (cx + 6, cy + 12), (cx - 6, cy + 12), (cx - 12, cy + 6)])
    elif element == "wind":
        for i, dy in enumerate([-10, 0, 10]):
            pygame.draw.arc(surf, color, (cx - 14, cy + dy - 6, 28, 12), 0.1, math.pi - 0.1, 3)
    elif element == "light":
        for i in range(8):
            a = math.pi * i / 4
            pygame.draw.line(surf, color, (cx, cy), (cx + math.cos(a) * 14, cy + math.sin(a) * 14), 3)
        pygame.draw.circle(surf, color, (cx, cy), 5)
    elif element == "dark":
        pygame.draw.circle(surf, color, (cx, cy), 12)
        pygame.draw.circle(surf, (30, 20, 40), (cx, cy), 12, 2)
        pygame.draw.circle(surf, (30, 20, 40), (cx + 4, cy - 4), 4)

# ---------------------------------------------------------------------------
# Portraits (larger, framed headshots)
# ---------------------------------------------------------------------------
def make_portrait(element, body, hair, accent, hair_style, weapon, path,
                  eye=(40, 40, 60), expression="neutral", eye_shape="round", skin=None):
    s = pygame.Surface((512, 512), pygame.SRCALPHA)
    main, light, dark = ELEMENT_COLORS[element]
    # bg: rich diagonal gradient (deep dark top-left -> element-tinted bottom-right)
    bg = diag_grad_surf(512, 512, lerp_color(dark, (0, 0, 0), 0.45),
                        lerp_color(main, (0, 0, 0), 0.55))
    s.blit(bg, (0, 0))
    # large soft radial glow behind the character (element-tinted)
    glow = soft_glow(520, 520, light, 95, center=(260, 230), radius=280, falloff=1.4)
    s.blit(glow, (-4, -4))
    # a secondary, tighter glow near the chest for depth
    glow2 = soft_glow(300, 300, light, 60, center=(150, 150), radius=150, falloff=1.6)
    s.blit(glow2, (110, 150))
    # element particles / motes scattered in the bg (deterministic positions)
    for i in range(26):
        sx = 30 + (hash((element, i, "x")) % 452)
        sy = 30 + (hash((element, i, "y")) % 452)
        sr = 1 + (hash((element, i, "r")) % 3)
        sa = 90 + (hash((element, i, "a")) % 120)
        # soft mote (glow) + bright core
        mote = soft_glow(sr * 6, sr * 6, light, sa, radius=sr * 3, falloff=1.5)
        s.blit(mote, (sx - sr * 3, sy - sr * 3))
        pygame.draw.circle(s, (255, 255, 255), (sx, sy), 1)
    # a few trailing wisps (element-tinted arcs) for atmosphere
    for i in range(4):
        wx = 60 + (hash((element, i, "w")) % 392)
        wy = 80 + (hash((element, i, "h")) % 300)
        pygame.draw.arc(s, (*light, 60), (wx, wy, 120, 60), 0.3, 2.5, 2)
    # big character (scaled up, soft) — rendered on an opaque-free surface
    big = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi(big, element, body, hair, accent, weapon, hair_style, eye,
               expression, eye_shape, skin)
    big = pygame.transform.smoothscale(big, (470, 470))
    # subtle ground glow under the character
    gground = soft_glow(360, 60, light, 70, center=(180, 30), radius=180, falloff=1.5)
    s.blit(gground, (76, 430))
    s.blit(big, (21, 50))
    # vignette (dark edges) for focus
    vig = radial_grad_surf(512, 512, (0, 0, 0, 0), (0, 0, 0, 150),
                           center=(256, 256), radius=320, falloff=1.8)
    s.blit(vig, (0, 0))
    # frame: dark border + element-colored ring + thin inner highlight
    pygame.draw.rect(s, (18, 16, 28), s.get_rect(), 12, border_radius=30)
    pygame.draw.rect(s, light, s.get_rect(), 6, border_radius=30)
    pygame.draw.rect(s, (255, 255, 255), (24, 24, 464, 464), 2, border_radius=24)
    # corner accents (element gems)
    for cx2, cy2 in ((34, 34), (478, 34), (34, 478), (478, 478)):
        cg = radial_grad_surf(20, 20, light, dark, center=(8, 7), radius=10)
        clip_to_circle(cg, (10, 10), 9)
        s.blit(cg, (cx2 - 10, cy2 - 10))
        pygame.draw.circle(s, (255, 255, 255), (cx2 - 3, cy2 - 3), 2)
    pygame.image.save(s, path)

# ---------------------------------------------------------------------------
# Master build
# ---------------------------------------------------------------------------
HEROES = [
    # name, element, weapon, hair_style, hair_color, body_color, accent
    # (per-hero eye color / expression / eye shape / skin tone live in the
    #  HERO_EYE_COLORS / HERO_EXPRESSIONS / HERO_EYE_SHAPES / HERO_SKIN_TONES
    #  dicts below, so this tuple stays 7 fields and existing unpacks work.)
    ("aria",   "light", "sword",  "long",  (250, 230, 180), (240, 230, 250), (220, 180, 60)),
    ("kael",   "fire",  "sword",  "spiky", (200, 60, 40),   (220, 90, 60),    (255, 180, 80)),
    ("mira",   "water", "staff",  "long",  (90, 130, 220),  (120, 180, 230),  (180, 230, 255)),
    ("zephyr", "wind",  "bow",    "twin",  (120, 200, 120), (140, 210, 150),  (200, 240, 180)),
    ("luna",   "dark",  "dagger", "hood",  (160, 120, 200), (90, 70, 120),    (200, 160, 240)),
    ("pyra",   "fire",  "staff",  "twin",  (220, 80, 60),   (200, 70, 60),    (255, 180, 120)),
    ("lyra",   "light", "orb",    "long",  (240, 230, 200), (230, 220, 240),  (255, 240, 180)),
    ("thorne", "wind",  "shield", "short", (90, 70, 50),    (120, 100, 80),   (180, 150, 110)),
    ("sera",   "light", "staff",  "long",  (240, 220, 160), (240, 220, 200),  (255, 240, 180)),
    ("rune",   "dark",  "orb",    "spiky", (140, 80, 180),  (90, 60, 130),    (200, 140, 240)),
    ("blaze",  "fire",  "sword",  "curly", (220, 100, 40),  (200, 80, 50),    (255, 160, 60)),
    ("nami",   "water", "orb",    "twin",  (120, 180, 220), (140, 200, 230),  (200, 240, 255)),
    ("gale",   "wind",  "bow",    "short", (160, 200, 120), (140, 190, 130),  (200, 240, 160)),
    ("vex",    "dark",  "dagger", "braided", (120, 90, 150),  (80, 60, 110),    (180, 140, 220)),
    # --- new heroes (Phase B) ---
    ("ember",  "fire",  "sword",  "mohawk", (180, 50, 40),  (200, 80, 60),    (255, 180, 80)),
    ("tide",   "water", "shield", "short", (90, 150, 220), (120, 180, 220),  (200, 240, 255)),
    ("zephyra","wind",  "bow",    "ponytail", (140, 220, 200), (150, 220, 200),  (220, 250, 230)),
    ("selene", "light", "sword",  "ponytail", (250, 240, 200), (240, 230, 200), (255, 220, 120)),
    ("nox",    "dark",  "orb",    "hood",  (140, 60, 200),  (90, 50, 130),    (200, 140, 255)),
    ("cinder", "fire",  "sword",  "short", (200, 80, 40),   (190, 90, 60),    (255, 160, 80)),
    ("mist",   "wind",  "dagger", "bob",  (160, 200, 200), (140, 190, 190),  (220, 250, 240)),
    ("sol",    "light", "orb",    "bob",  (250, 230, 160), (240, 220, 180),  (255, 240, 180)),
    # --- new heroes (Phase C) ---
    ("gaia",  "wind",  "shield", "bob", (120, 160, 90),  (110, 150, 90),   (180, 220, 120)),
    ("echo",  "water", "orb",    "twin",  (160, 200, 220), (150, 200, 220),  (220, 240, 255)),
    ("raven", "dark",  "dagger", "hood",  (90, 30, 30),    (70, 30, 40),     (200, 60, 80)),
]

# Per-hero facial features (keyed by hero name). Together with the new hair
# styles above, these give each of the 25 heroes a distinct face so heroes of
# the same element are no longer near-identical clones. (Audit: chibi face
# variety.) The HEROES tuple stays 7 fields; these are looked up by name in
# main() so existing 7-field unpacks (e.g. verify_assets.py) keep working.
HERO_EYE_COLORS = {
    "aria": (180, 140, 60), "kael": (220, 80, 40), "mira": (120, 200, 230),
    "zephyr": (120, 200, 120), "luna": (180, 120, 220), "pyra": (240, 120, 50),
    "lyra": (220, 180, 90), "thorne": (90, 140, 80), "sera": (200, 170, 80),
    "rune": (160, 90, 210), "blaze": (230, 100, 40), "nami": (100, 180, 240),
    "gale": (140, 220, 110), "vex": (140, 80, 180), "ember": (210, 60, 50),
    "tide": (80, 140, 220), "zephyra": (160, 220, 180), "selene": (160, 180, 220),
    "nox": (120, 70, 200), "cinder": (180, 50, 40), "mist": (180, 220, 200),
    "sol": (240, 200, 80), "gaia": (100, 170, 90), "echo": (140, 210, 230),
    "raven": (200, 40, 60),
}
HERO_EXPRESSIONS = {
    "aria": "stoic", "kael": "fierce", "mira": "gentle", "zephyr": "fierce",
    "luna": "sad", "pyra": "fierce", "lyra": "gentle", "thorne": "stoic",
    "sera": "gentle", "rune": "stoic", "blaze": "fierce", "nami": "gentle",
    "gale": "fierce", "vex": "fierce", "ember": "fierce", "tide": "stoic",
    "zephyra": "gentle", "selene": "stoic", "nox": "stoic", "cinder": "stoic",
    "mist": "sad", "sol": "gentle", "gaia": "stoic", "echo": "gentle",
    "raven": "fierce",
}
HERO_EYE_SHAPES = {
    "aria": "half", "kael": "sharp", "mira": "wide", "zephyr": "sharp",
    "luna": "round", "pyra": "sharp", "lyra": "wide", "thorne": "half",
    "sera": "wide", "rune": "half", "blaze": "sharp", "nami": "wide",
    "gale": "sharp", "vex": "sharp", "ember": "sharp", "tide": "half",
    "zephyra": "wide", "selene": "half", "nox": "half", "cinder": "half",
    "mist": "round", "sol": "wide", "gaia": "half", "echo": "wide",
    "raven": "sharp",
}
HERO_SKIN_TONES = {
    "raven": (230, 210, 215), "gaia": (210, 170, 130), "tide": (220, 210, 225),
    "sol": (255, 215, 170), "luna": (235, 215, 220), "nox": (225, 210, 230),
    "ember": (235, 200, 170), "cinder": (240, 210, 180),
}

ENEMIES = [
    ("slime",     "wind",   ((120, 220, 140), (200, 255, 200), (40, 120, 60))),
    ("goblin",    "fire",   ((120, 160, 80),  (180, 220, 120), (40, 80, 30))),
    ("bat",       "dark",   ((90, 60, 120),   (160, 120, 200), (30, 20, 40))),
    ("skeleton",  "light",  ((230, 230, 220), (255, 255, 250), (80, 80, 90))),
    ("wolf",      "wind",   ((120, 120, 130), (180, 180, 190), (40, 40, 50))),
    ("orc",       "fire",   ((140, 100, 70),  (200, 160, 100), (60, 40, 30))),
    ("golem",     "wind",   ((150, 140, 110), (200, 190, 160), (70, 60, 50))),
    ("wraith",    "dark",   ((120, 130, 180), (180, 200, 240), (40, 50, 80))),
    ("dragon",    "fire",   ((180, 80, 60),   (240, 180, 120), (90, 30, 20))),
    ("demonking", "dark",   ((120, 40, 60),   (200, 80, 120),  (40, 10, 20))),
    # --- new enemies (Phase B) ---
    ("imp",         "fire",   ((200, 80, 50),   (255, 160, 90),  (80, 20, 10))),
    ("harpy",       "wind",   ((160, 130, 90),  (220, 200, 160), (80, 60, 40))),
    ("ghoul",       "dark",   ((120, 160, 110), (180, 220, 170), (40, 70, 50))),
    ("paladin",     "light",  ((180, 180, 200), (230, 230, 245), (80, 80, 100))),
    ("hydra",       "water",  ((80, 160, 180),  (140, 220, 230), (20, 60, 80))),
    ("frosttitan",  "water",  ((140, 200, 240), (200, 230, 255), (40, 90, 140))),
    ("embertyrant", "fire",   ((180, 60, 40),   (255, 180, 80),  (90, 20, 10))),
]

SKILLS = [
    ("fire_slash", "fire", "slash"), ("fire_bolt", "fire", "bolt"),
    ("inferno", "fire", "aoe"), ("meteor", "fire", "aoe"),
    ("water_bolt", "water", "bolt"), ("water_heal", "water", "heal"),
    ("tidal_wave", "water", "aoe"),
    ("wind_arrow", "wind", "arrow"), ("wind_aoe", "wind", "aoe"),
    ("swift_buff", "wind", "buff"),
    ("light_slash", "light", "slash"), ("light_heal", "light", "heal"),
    ("light_aoe", "light", "aoe"), ("blessing", "light", "shield"),
    ("revive", "light", "heal"), ("light_hymn", "light", "heal"),
    ("dark_bolt", "dark", "bolt"), ("dark_curse", "dark", "curse"),
    ("dark_aoe", "dark", "aoe"), ("shield_ward", "dark", "shield"),
    ("void_nova", "dark", "aoe"),
    ("buff_atk", "light", "buff"), ("buff_def", "wind", "shield"),
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
    # boss ultimates
    ("hellfire", "fire", "aoe"), ("abyssal_wave", "dark", "aoe"),
    ("frost_cataclysm", "water", "aoe"), ("storm_of_embers", "fire", "aoe"),
]

def main():
    print("Generating Aetheria assets...")
    # characters
    for name, element, weapon, hair_style, hair, body, accent in HEROES:
        # per-hero facial variety (eye color / expression / eye shape / skin)
        eye = HERO_EYE_COLORS.get(name, (40, 40, 60))
        expr = HERO_EXPRESSIONS.get(name, "neutral")
        eshape = HERO_EYE_SHAPES.get(name, "round")
        skin = HERO_SKIN_TONES.get(name)
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        draw_chibi(s, element, body, hair, accent, weapon, hair_style,
                   eye, expr, eshape, skin)
        pygame.image.save(s, os.path.join(ASSET_DIR, "characters", f"{name}.png"))
        make_portrait(element, body, hair, accent, hair_style, weapon,
                      os.path.join(ASSET_DIR, "portraits", f"{name}.png"),
                      eye, expr, eshape, skin)
    print(f"  {len(HEROES)} characters + portraits")

    # enemies
    for name, el, pal in ENEMIES:
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        draw_enemy(s, name, pal)
        pygame.image.save(s, os.path.join(ASSET_DIR, "enemies", f"{name}.png"))
    print(f"  {len(ENEMIES)} enemies")

    # skills
    for name, el, kind in SKILLS:
        s = pygame.Surface((128, 128), pygame.SRCALPHA)
        draw_skill_icon(s, el, kind)
        pygame.image.save(s, os.path.join(ASSET_DIR, "skills", f"{name}.png"))
    print(f"  {len(SKILLS)} skill icons")

    # backgrounds
    make_title_bg(os.path.join(ASSET_DIR, "backgrounds", "title.png"))
    make_map_bg(os.path.join(ASSET_DIR, "backgrounds", "map.png"))
    make_shop_bg(os.path.join(ASSET_DIR, "backgrounds", "shop.png"))
    for theme in ["plains", "forest", "cave", "castle", "void"]:
        make_battle_bg(os.path.join(ASSET_DIR, "backgrounds", f"battle_{theme}.png"), theme)
    print("  backgrounds")

    # items
    make_items()
    print("  item icons")

    # ui
    make_ui()
    print("  UI elements")
    print("Done. Assets saved to", ASSET_DIR)

if __name__ == "__main__":
    main()
