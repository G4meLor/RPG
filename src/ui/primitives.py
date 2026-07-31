"""
Aetheria — shared UI primitives.

The low-level drawing helpers used by every scene: the font cache, the
rendered-text surface cache, the button/panel/bar/star widgets, the dim
overlay. Extracted from main.py so the world/adventure scenes can import
them without pulling in the whole game loop (which previously forced a
main <-> world_scene circular import).

The element/rarity color lookups + the color constants (WHITE/GOLD/PANEL/...)
live in src.ui.colors; the settings-menu widgets (Toggle/Slider) live in
src.ui.widgets. This module re-exports the color constants so callers that
import them from `ui` (the root shim or src.ui) still resolve them.

This module depends only on pygame + audio + world_entities.scratch, so it
is safe to import from any scene at module load time.
"""
import math

import pygame

import src.audio as audio

# Reusable scratch surfaces (mirrors world_entities.scratch) for menu scenes
# that allocate small SRCALPHA overlays each frame. Re-exported so callers
# that used to import `scratch` from main can import it from ui instead.
# The try/except keeps ui importable before pygame.display is init'd (the
# scratch surface factory needs a display mode set; under headless verify it
# would otherwise hard-fail at import time).
try:
    from src.entities.world_actors import scratch as _scratch
except Exception:  # pragma: no cover - world_entities needs an init'd pygame
    _scratch = None
scratch = _scratch

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 1280, 720
FPS = 60
TITLE = "Aetheria - Gacha RPG"
SEED = 1337

# Colors live in src.ui.colors now; import them so this module's callers can
# still reach WHITE/GOLD/PANEL/PANEL_BORDER via the package __init__ (and so
# Button/draw_panel/draw_stars/draw_bar below resolve them as names).
from src.ui.colors import (WHITE, DIM, GOLD, PANEL, PANEL_BORDER, HP_RED,  # noqa: F401
    HP_GREEN, MP_BLUE, XP_PURPLE, BG_DARK)

# ---------------------------------------------------------------------------
# Fonts + rendered-text cache
# ---------------------------------------------------------------------------
FONTS = {}

def init_fonts():
    sizes = [10, 11, 12, 13, 14, 16, 18, 20, 22, 24, 28, 32, 34, 36, 40, 48, 56, 72]
    for s in sizes:
        FONTS[s] = pygame.font.SysFont("dejavusans,arial", s, bold=True)
    FONTS["small"] = pygame.font.SysFont("dejavusans,arial", 14)
    FONTS["tiny"] = pygame.font.SysFont("dejavusans,arial", 12)
    # floats/particles use arbitrary float sizes; pre-fill a dense range so the
    # FONTS[sz] lookup in the battle float renderer never KeyErrors.
    for s in range(8, 73):
        if s not in FONTS:
            FONTS[s] = pygame.font.SysFont("dejavusans,arial", s, bold=True)

def get_font(size):
    if size not in FONTS:
        FONTS[size] = pygame.font.SysFont("dejavusans,arial", size, bold=True)
    return FONTS[size]

def f(size): return get_font(size)

# Rendered-text surface cache. font.render() is a top profile cost (the HUD
# draws ~40 text elements/frame, most static); cache the (text, shadow)
# Surfaces keyed by (string, size, color) so a repeated string is one dict
# lookup + 2 blits, not 2 font.render() calls. Capped; evicted wholesale when
# it grows too large so dynamic strings (HP numbers, cooldown timers) don't
# balloon memory. (Merged from world_scene's _TEXT_CACHE — one cache, not two.)
_TEXT_CACHE = {}
_TEXT_CACHE_CAP = 300

def text(surf, txt, size, color, pos, center=False, shadow=True):
    key = (str(txt), size, color)
    cached = _TEXT_CACHE.get(key)
    if cached is None:
        font = get_font(size)
        t = font.render(str(txt), True, color)
        sh = font.render(str(txt), True, (0, 0, 0)) if shadow else None
        if len(_TEXT_CACHE) >= _TEXT_CACHE_CAP:
            _TEXT_CACHE.clear()
        _TEXT_CACHE[key] = (t, sh)
        cached = (t, sh)
    t, sh = cached
    r = t.get_rect()
    if center:
        r.center = pos
    else:
        r.topleft = pos
    if sh:
        surf.blit(sh, (r.x + 2, r.y + 2))
    surf.blit(t, r)
    return r

# ---------------------------------------------------------------------------
# UI widgets
# ---------------------------------------------------------------------------
class Button:
    def __init__(self, rect, label, color=(60, 70, 110), hot=(90, 110, 170), text_color=WHITE, size=24):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color
        self.hot = hot
        self.text_color = text_color
        self.size = size
        self.hover = False
        self.pressed = False
        self.scale = 1.0
        self._was_hover = False

    def update(self, mp, mdown):
        self.hover = self.rect.collidepoint(mp)
        if self.hover and not self._was_hover:
            audio.play("hover", 0.2)
        self._was_hover = self.hover
        target = 1.06 if self.hover else 1.0
        self.scale += (target - self.scale) * 0.2
        self.pressed = self.hover and mdown

    def draw(self, surf):
        r = self.rect.copy()
        cx, cy = r.center
        r.width = int(r.width * self.scale); r.height = int(r.height * self.scale)
        r.center = (cx, cy)
        col = self.hot if self.hover else self.color
        # soft drop shadow under the button for depth (reused scratch surface)
        sh = _scratch(r.width + 8, r.height + 8)
        pygame.draw.rect(sh, (0, 0, 0, 90), sh.get_rect(), border_radius=16)
        surf.blit(sh, (r.x - 4, r.y + 4))
        pygame.draw.rect(surf, col, r, border_radius=14)
        # a brighter top-edge highlight gradient (reused scratch surface)
        hi = _scratch(r.width - 8, r.height // 2)
        pygame.draw.rect(hi, (255, 255, 255, 55), hi.get_rect(), border_radius=10)
        surf.blit(hi, (r.x + 4, r.y + 4))
        pygame.draw.rect(surf, (240, 240, 255), r, 3, border_radius=14)
        text(surf, self.label, self.size, self.text_color, r.center, center=True)

    def clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                audio.play("menu_click", 0.3)
                return True
        return False


def draw_panel(surf, rect, border=PANEL_BORDER, fill=PANEL, radius=18, border_w=3):
    r = pygame.Rect(rect)
    # draw directly to the destination: a filled rounded rect + a border. The
    # fill color has an alpha channel, so use a scratch surface only for that
    # one blit (cheaper than building the border on the scratch too).
    s = _scratch(r.width, r.height)
    pygame.draw.rect(s, fill, s.get_rect(), border_radius=radius)
    surf.blit(s, r.topleft)
    pygame.draw.rect(surf, border, r, border_w, border_radius=radius)

def draw_bar(surf, rect, frac, fg, bg=(40, 40, 60), border=(0, 0, 0)):
    r = pygame.Rect(rect)
    pygame.draw.rect(surf, bg, r, border_radius=4)
    if frac > 0:
        fr = r.copy(); fr.width = int(r.width * max(0, min(1, frac)))
        pygame.draw.rect(surf, fg, fr, border_radius=4)
    pygame.draw.rect(surf, border, r, 1, border_radius=4)

def draw_stars(surf, x, y, n, size=16):
    for i in range(n):
        cx = x + i * (size + 4)
        pts = []
        for k in range(10):
            ang = -math.pi / 2 + math.pi * k / 5
            rr = size if k % 2 == 0 else size * 0.45
            pts.append((cx + math.cos(ang) * rr, y + math.sin(ang) * rr))
        pygame.draw.polygon(surf, GOLD, pts)
        pygame.draw.polygon(surf, (120, 90, 30), pts, 1)

# ---------------------------------------------------------------------------
# Cached full-screen dim overlays (different alphas used by menu scenes).
# ---------------------------------------------------------------------------
_DIM_CACHE = {}
def dim_overlay(alpha=170, tint=(0, 0, 0)):
    key = (alpha, tint)
    s = _DIM_CACHE.get(key)
    if s is None:
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((*tint, alpha))
        _DIM_CACHE[key] = s
    return s

# element_color / rarity_color + the color constants live in src.ui.colors.
# element_color keeps its late `from main import Game` (colorblind-palette hook)
# so it lives next to the data lookups it depends on.

