"""
Aetheria Gacha - Main game
A complete turn-based gacha RPG built with pygame.
Run:  python3 main.py
"""
import os
import sys
import math
import random
import pygame

import data as D
from entities import (Hero, load_char_sprite, load_portrait,
                      load_skill_icon, load_bg, load_ui, load_item_icon)
from gacha import GachaSystem
from player import Player
import audio
# Reusable scratch surfaces (mirrors world_entities.scratch) for menu scenes
# that allocate small SRCALPHA overlays each frame.
try:
    from world_entities import scratch as _scratch
except Exception:
    _scratch = None

# Cached full-screen dim overlays (different alphas used by menu scenes).
_DIM_CACHE = {}
def _dim_overlay(alpha=170, tint=(0, 0, 0)):
    key = (alpha, tint)
    s = _DIM_CACHE.get(key)
    if s is None:
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill((*tint, alpha))
        _DIM_CACHE[key] = s
    return s
# Open-world scene: imported lazily to avoid a circular import (world_scene
# imports Button/draw_bar from main). Resolved the first time the world scene
# is created.
_world_scene_cls = None
def _get_world_scene_cls():
    global _world_scene_cls
    if _world_scene_cls is None:
        from world_scene import WorldScene as _WS
        _world_scene_cls = _WS
    return _world_scene_cls

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 1280, 720
FPS = 60
TITLE = "Aetheria - Gacha RPG"
SEED = 1337
random.seed(SEED)

# Colors
WHITE = (245, 245, 250)
DIM   = (180, 180, 200)
GOLD  = (255, 210, 90)
PANEL = (28, 26, 44, 220)
PANEL_BORDER = (180, 180, 220)
HP_RED = (220, 70, 80)
HP_GREEN = (90, 210, 110)
MP_BLUE = (90, 150, 240)
XP_PURPLE = (200, 120, 240)
BG_DARK = (20, 18, 32)

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
def text(surf, txt, size, color, pos, center=False, shadow=True):
    font = get_font(size)
    t = font.render(str(txt), True, color)
    r = t.get_rect()
    if center: r.center = pos
    else: r.topleft = pos
    if shadow:
        sh = font.render(str(txt), True, (0, 0, 0))
        surf.blit(sh, (r.x + 2, r.y + 2))
    surf.blit(t, r)
    return r

# ---------------------------------------------------------------------------
# UI helpers
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

def draw_hp_bar(surf, rect, frac):
    col = HP_GREEN if frac > 0.5 else (GOLD if frac > 0.25 else HP_RED)
    draw_bar(surf, rect, frac, col)

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
# Toggle + Slider widgets for the settings menu
# ---------------------------------------------------------------------------
class Toggle:
    """An on/off switch. Calls on_change(bool) when clicked."""
    def __init__(self, x, y, value=False, on_change=None, w=64, h=30):
        self.rect = pygame.Rect(x, y, w, h)
        self.value = bool(value)
        self.on_change = on_change
        self.hover = False
        self.knob = 1.0 if self.value else 0.0   # animated 0..1

    def set(self, v):
        self.value = bool(v)
        self.knob = 1.0 if self.value else 0.0

    def update(self, mp, mdown):
        self.hover = self.rect.collidepoint(mp)
        target = 1.0 if self.value else 0.0
        self.knob += (target - self.knob) * 0.25

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.value = not self.value
                audio.play("menu_click", 0.3)
                if self.on_change:
                    self.on_change(self.value)
                return True
        return False

    def draw(self, surf):
        r = self.rect
        # track
        on_col = (90, 200, 130)
        off_col = (70, 70, 90)
        col = on_col if self.value else off_col
        pygame.draw.rect(surf, (20, 20, 30), r, border_radius=r.height // 2)
        pygame.draw.rect(surf, col, r, border_radius=r.height // 2)
        pygame.draw.rect(surf, (220, 220, 240) if self.hover else (150, 150, 170),
                         r, 2, border_radius=r.height // 2)
        # knob
        kx = r.x + 4 + int(self.knob * (r.width - r.height))
        kr = r.height // 2 - 4
        pygame.draw.circle(surf, (245, 245, 250), (kx + kr, r.centery), kr)
        pygame.draw.circle(surf, (60, 60, 80), (kx + kr, r.centery), kr, 2)
        # tiny on/off label
        text(surf, "ON" if self.value else "OFF", 11,
             (240, 240, 250) if self.value else (160, 160, 180),
             (r.x - 30, r.centery - 8))


class Slider:
    """A horizontal slider for a 0..1 (or min..max) value.
    on_change(value) fires while dragging and on click."""
    def __init__(self, x, y, w, value=0.5, on_change=None,
                 vmin=0.0, vmax=1.0, step=None):
        self.rect = pygame.Rect(x, y, w, 16)
        self.value = float(value)
        self.vmin = float(vmin)
        self.vmax = float(vmax)
        self.step = step
        self.on_change = on_change
        self.hover = False
        self.dragging = False

    def _norm(self):
        return (self.value - self.vmin) / max(1e-6, self.vmax - self.vmin)

    def _set_from_x(self, mx):
        n = (mx - self.rect.x) / max(1, self.rect.width)
        n = max(0.0, min(1.0, n))
        v = self.vmin + n * (self.vmax - self.vmin)
        if self.step:
            v = round(v / self.step) * self.step
        v = max(self.vmin, min(self.vmax, v))
        if v != self.value:
            self.value = v
            if self.on_change:
                self.on_change(self.value)

    def update(self, mp, mdown):
        self.hover = self.rect.collidepoint(mp) or self.dragging
        if self.dragging and not mdown:
            self.dragging = False

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # grab if click on the track or near the knob
            hit = self.rect.inflate(0, 20).collidepoint(event.pos)
            if hit:
                self.dragging = True
                self._set_from_x(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_x(event.pos[0])
            return True
        return False

    def draw(self, surf):
        r = self.rect
        # track
        pygame.draw.rect(surf, (30, 30, 44), r, border_radius=8)
        pygame.draw.rect(surf, (70, 70, 100) if self.hover else (50, 50, 70),
                         r, 2, border_radius=8)
        # fill
        fw = int(r.width * self._norm())
        if fw > 0:
            pygame.draw.rect(surf, (120, 180, 240), (r.x, r.y, fw, r.height),
                             border_radius=8)
        # knob
        kx = r.x + fw
        pygame.draw.circle(surf, (240, 240, 250), (kx, r.centery), 9)
        pygame.draw.circle(surf, (60, 60, 90), (kx, r.centery), 9, 2)

def element_color(el):
    # Branch on the colorblind_mode setting to swap the element palette for a
    # deuteranopia-safe set. The function reads the active Game's player
    # settings; if no Game has been instantiated yet (e.g. early import-time
    # probes), fall back to the default palette. REACTIONS are NOT routed here.
    if el not in D.ELEMENT_COLORS:
        return (200, 200, 200)
    try:
        cb = Game._active.player.settings.get("colorblind_mode", False) \
            if Game._active is not None else False
    except Exception:
        cb = False
    if cb:
        return D.COLORBLIND_PALETTES[el]
    return D.ELEMENT_COLORS[el][0]

def rarity_color(rar):
    return D.RARITY_COLORS.get(rar, (200, 200, 200))

# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------
class Scene:
    def __init__(self, game):
        self.game = game

    def update(self, dt, events): pass
    def draw(self, surf): pass


class TitleScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.bg = load_bg("title")
        self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        self.t = 0
        self.buttons = [
            Button((WIDTH // 2 - 120, 300, 240, 56), "Enter World", (70, 120, 90), (110, 180, 130)),
            Button((WIDTH // 2 - 120, 364, 240, 56), "Heroes", (90, 80, 50), (160, 130, 70)),
            Button((WIDTH // 2 - 120, 428, 240, 56), "Summon", (90, 60, 130), (140, 90, 200)),
            Button((WIDTH // 2 - 120, 492, 240, 56), "Shop", (70, 90, 130), (100, 130, 190)),
            Button((WIDTH // 2 - 120, 556, 240, 56), "Codex", (70, 110, 90), (110, 170, 130)),
            Button((WIDTH // 2 - 120, 620, 240, 56), "Records", (60, 70, 110), (90, 110, 160), size=20),
            Button((WIDTH // 2 - 120, 676, 240, 40), "Settings", (110, 90, 60), (170, 140, 80), size=18),
        ]
        # shimmering embers rising from the bottom for atmosphere (cached colors)
        self.particles = []
        embers = [(255, 220, 140), (255, 180, 120), (200, 200, 255), (180, 220, 255)]
        for _ in range(70):
            self.particles.append([random.uniform(0, WIDTH), random.uniform(0, HEIGHT),
                                   random.uniform(-8, 8), random.uniform(-26, -8),
                                   random.uniform(3, 6), random.choice(embers)])

    def update(self, dt, events):
        self.t += dt
        mp = pygame.mouse.get_pos()
        mdown = pygame.mouse.get_pressed()[0]
        for b in self.buttons:
            b.update(mp, mdown)
        for p in self.particles:
            p[0] += p[2] * dt; p[1] += p[3] * dt; p[4] -= dt
            if p[4] <= 0:
                p[0] = random.uniform(0, WIDTH); p[1] = HEIGHT + 10
                p[4] = random.uniform(2, 5)
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
            if self.buttons[0].clicked(e):
                self.game.goto("world")
            if self.buttons[1].clicked(e):
                self.game.goto("roster")
            if self.buttons[2].clicked(e):
                self.game.goto("gacha")
            if self.buttons[3].clicked(e):
                self.game.goto("shop")
            if self.buttons[4].clicked(e):
                self.game.goto("codex")
            if self.buttons[5].clicked(e):
                self.game.goto("stats")
            if self.buttons[6].clicked(e):
                self.game.goto("settings")

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        # embers with a soft additive glow (two-pass: a faint halo then the core)
        for p in self.particles:
            x, y = int(p[0]), int(p[1])
            rad = int(p[4])
            halo = _scratch(rad * 6, rad * 6)
            pygame.draw.circle(halo, (*p[5], 40), (rad * 3, rad * 3), rad * 3)
            surf.blit(halo, (x - rad * 3, y - rad * 3))
            pygame.draw.circle(surf, p[5], (x, y), max(1, rad - 1))
        bob = math.sin(self.t * 2) * 6
        # title with a soft glow halo behind it (reused scratch surface)
        glow = _scratch(640, 160)
        for r in range(80, 0, -8):
            a = int(40 * (1 - r / 80))
            pygame.draw.rect(glow, (255, 220, 140, a), (320 - r, 80 - r // 2, 2 * r, r), border_radius=20)
        surf.blit(glow, (WIDTH // 2 - 320, 80 + bob))
        text(surf, "AETHERIA", 72, (255, 240, 180), (WIDTH // 2, 140 + bob), center=True)
        text(surf, "Open World", 32, (200, 255, 220), (WIDTH // 2, 208 + bob), center=True)
        # decorative divider with diamond accents
        pygame.draw.line(surf, (255, 220, 120), (WIDTH // 2 - 160, 258), (WIDTH // 2 + 160, 258), 3)
        for dx in (-160, 0, 160):
            pygame.draw.polygon(surf, (255, 220, 120),
                                [(WIDTH // 2 + dx, 252), (WIDTH // 2 + dx + 6, 258),
                                 (WIDTH // 2 + dx, 264), (WIDTH // 2 + dx - 6, 258)])
        for b in self.buttons:
            b.draw(surf)
        text(surf, f"Gems: {self.game.player.gems}   Gold: {self.game.player.gold}", 18, GOLD,
             (WIDTH // 2, 280), center=True)
        # login bonus popup — placed at the top so it stays on-screen and does
        # not overlap the Settings button (which sits at the bottom of the stack)
        bonus = getattr(self.game, "_login_bonus", None)
        if bonus:
            amt, streak = bonus
            draw_panel(surf, (WIDTH // 2 - 220, 60, 440, 40))
            text(surf, f"Daily login! Day {streak}: +{amt} gems", 18, (255, 240, 160),
                 (WIDTH // 2, 80), center=True)
            if self.t > 4.0:
                self.game._login_bonus = None


class RosterScene(Scene):
    """List all owned heroes; click to open hero detail."""
    def __init__(self, game):
        super().__init__(game)
        self.back_btn = Button((40, 40, 140, 48), "Back", (60, 60, 90), (90, 90, 130), size=20)
        self.scroll = 0
        self.t = 0
        self.cols = 4   # card columns (kept here so scroll clamping can reuse it)
        self.portrait_cache = {}
        # cached scaled card art: (hid) -> (frame_surf, portrait_surf) at the
        # fixed card size, built once so draw() doesn't smoothscale per frame.
        self._card_art = {}
        # cached draw-state; initialized here so draw() is safe even if it runs
        # before the first update() (goto swaps the scene mid-frame).
        self.cards = []
        self._build_cards()

    def get_portrait(self, hid):
        if hid not in self.portrait_cache:
            self.portrait_cache[hid] = load_portrait(hid, 220)
        return self.portrait_cache[hid]

    def _card_art_for(self, hid):
        """Cached (frame, portrait) surfaces at the card display size."""
        art = self._card_art.get(hid)
        if art is None:
            hd = D.HERO_BY_ID[hid]
            frame = pygame.transform.smoothscale(load_ui(f"frame_{hd['rarity']}"), (180, 240))
            p = pygame.transform.smoothscale(self.get_portrait(hid), (156, 156))
            art = (frame, p)
            self._card_art[hid] = art
        return art

    def _build_cards(self):
        owned_ids = list(self.game.player.owned.keys())
        card_w, card_h = 180, 240
        # 4 columns so the last column (x=60+3*196=648, right=828) clears the
        # Battle Team panel (x=920). 5 cols at x=844 still overlapped it by 104px.
        cols = 4
        gap = 16
        start_x = 60
        start_y = 110
        self.cards = []
        for i, hid in enumerate(owned_ids):
            col = i % cols
            row = i // cols
            x = start_x + col * (card_w + gap)
            y = start_y + row * (card_h + gap) - self.scroll
            rect = pygame.Rect(x, y, card_w, card_h)
            self.cards.append((hid, rect))

    def update(self, dt, events):
        self.t += dt
        mp = pygame.mouse.get_pos()
        mdown = pygame.mouse.get_pressed()[0]
        self.back_btn.update(mp, mdown)
        self._build_cards()
        for e in events:
            if self.back_btn.clicked(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                self.game.back("title")
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for hid, rect in self.cards:
                    if rect.collidepoint(e.pos):
                        self.game.goto("hero_detail", hero_id=hid)
                        return
            if e.type == pygame.MOUSEWHEEL:
                # clamp scroll to the content height so the roster can't scroll
                # past its end (which left a blank screen with no way back).
                n = len(self.game.player.owned)
                rows = (n + self.cols - 1) // self.cols
                content_h = rows * (256)   # card_h (240) + gap (16)
                max_scroll = max(0, content_h - (HEIGHT - 110 - 40))
                self.scroll = max(0, min(self.scroll - e.y * 40, max_scroll))

    def draw(self, surf):
        surf.fill(BG_DARK)
        text(surf, "Heroes", 40, WHITE, (WIDTH // 2, 40), center=True)
        text(surf, "Click a hero to view details & equip", 18, DIM, (WIDTH // 2, 80), center=True)
        # current team display
        tx = WIDTH - 360
        draw_panel(surf, (tx, 110, 300, 240))
        text(surf, "Battle Team", 22, GOLD, (tx + 16, 120))
        for i, hid in enumerate(self.game.player.team):
            slot_y = 160 + i * 56
            pygame.draw.rect(surf, (50, 50, 70), (tx + 16, slot_y, 268, 48), border_radius=10)
            pygame.draw.rect(surf, (200, 200, 240), (tx + 16, slot_y, 268, 48), 2, border_radius=10)
            if hid:
                hd = D.HERO_BY_ID[hid]
                p = load_portrait(hid, 44)
                surf.blit(p, (tx + 22, slot_y + 2))
                text(surf, f"{hd['name']} Lv.{self.game.player.owned[hid]['level']}", 18, WHITE, (tx + 76, slot_y + 6))
                text(surf, hd['title'], 14, DIM, (tx + 76, slot_y + 28))
            else:
                text(surf, "Empty", 18, DIM, (tx + 100, slot_y + 14))
        text(surf, f"Team Power: {self.game.player.team_power()}", 20, (140, 220, 160), (tx + 16, 300))
        # elemental resonance — show active resonance buffs under Team Power so
        # the player sees what their party composition grants before entering the
        # world. Each line is the resonance name + value in the element's color.
        resonances = D.team_resonances(self.game.player.team)
        ry = 326
        for r in resonances:
            el = next((e for e, d in D.ELEMENTAL_RESONANCE.items()
                       if d.get("buff") == r.get("buff")), None)
            col = D.ELEMENT_COLORS.get(el, ((180, 200, 220),))[0]
            val_pct = int(r.get("val", 0) * 100)
            text(surf, f"  {r['name']}  +{val_pct}%", 13, col, (tx + 16, ry))
            ry += 16
        # cards
        for hid, rect in self.cards:
            hd = D.HERO_BY_ID[hid]
            info = self.game.player.owned[hid]
            in_team = hid in self.game.player.team
            frame, p2 = self._card_art_for(hid)
            pw = p2.get_width()
            surf.blit(frame, rect.topleft)
            if in_team:
                pygame.draw.rect(surf, GOLD, rect, 4, border_radius=16)
                text(surf, "IN TEAM", 14, GOLD, (rect.centerx, rect.bottom - 18), center=True)
            surf.blit(p2, (rect.x + 12, rect.y + 12))
            text(surf, hd["name"], 18, WHITE, (rect.centerx, rect.y + pw + 18), center=True)
            text(surf, f"Lv.{info['level']}", 14, DIM, (rect.centerx, rect.y + pw + 40), center=True)
            nstars = 3 if hd['rarity'] == "SSR" else (2 if hd['rarity'] == "SR" else 1)
            draw_stars(surf, rect.centerx - 30, rect.y + pw + 58, nstars, size=10)
            # ascension pips
            asc = info.get("ascension", 0)
            for a in range(D.MAX_ASCENSION):
                col = (255, 120, 200) if a < asc else (70, 60, 80)
                pygame.draw.circle(surf, col, (rect.x + 24 + a * 16, rect.y + 12), 5)
            # equipment set-progress hint: nudge the player toward a set bonus by
            # showing the completed set name or a "2/3" in-progress line.
            eq = info.get("equipment", {})
            eq_ids = set(eq.values()) if eq else set()
            for sdef in D.EQUIPMENT_SETS.values():
                have = len(set(sdef["items"]) & eq_ids)
                if have == 3:
                    text(surf, sdef["name"], 10, (255, 220, 120),
                         (rect.centerx, rect.y + pw + 72), center=True)
                    break
                if have == 2:
                    text(surf, f"{sdef['name']} 2/3", 10, (200, 180, 120),
                         (rect.centerx, rect.y + pw + 72), center=True)
                    break
        self.back_btn.draw(surf)
        text(surf, f"Heroes owned: {len(self.game.player.owned)}  |  Scroll: mouse wheel", 16, DIM,
             (WIDTH // 2, HEIGHT - 30), center=True)


class HeroDetailScene(Scene):
    """View a hero, add/remove from team, ascend, equip items."""
    def __init__(self, game, hero_id):
        super().__init__(game)
        self.hero_id = hero_id
        self.back_btn = Button((40, 40, 140, 48), "Back", (60, 60, 90), (90, 90, 130), size=20)
        self.team_btn = Button((WIDTH - 260, 600, 220, 56), "Add to Team", (60, 120, 80), (90, 180, 110), size=20)
        self.ascend_btn = Button((WIDTH - 260, 520, 220, 56), "Ascend", (150, 60, 130), (200, 90, 170), size=20)
        self.evolve_btn = Button((WIDTH - 260, 460, 220, 50), "Evolution Tree",
                                 (110, 70, 150), (170, 110, 210), size=16)
        self.tab = "equip"   # equip | stats
        self.t = 0
        self.equip_slots = ["weapon", "armor", "accessory"]
        # cached draw-state; initialized here so update()/draw() are safe even
        # if called before the first full draw() (goto swaps mid-frame).
        self._item_rects = []
        # "Team Full!" flash timer: the Add-to-Team button briefly shows this
        # when the team is full instead of silently overwriting a slot.
        self._team_full_t = 0.0

    def update(self, dt, events):
        self.t += dt
        # the "Team Full!" flash reverts to the normal label after it expires
        if self._team_full_t > 0:
            self._team_full_t = max(0, self._team_full_t - dt)
            if self._team_full_t <= 0:
                in_team_now = self.hero_id in self.game.player.team
                self.team_btn.label = "Remove from Team" if in_team_now else "Add to Team"
        mp = pygame.mouse.get_pos()
        mdown = pygame.mouse.get_pressed()[0]
        self.back_btn.update(mp, mdown)
        self.team_btn.update(mp, mdown)
        self.ascend_btn.update(mp, mdown)
        self.evolve_btn.update(mp, mdown)
        hid = self.hero_id
        in_team = hid in self.game.player.team
        if self._team_full_t <= 0:
            self.team_btn.label = "Remove from Team" if in_team else "Add to Team"
        rec = self.game.player.owned[hid]
        asc = rec.get("ascension", 0)
        can_ascend = rec["dupes"] > 0 and asc < D.MAX_ASCENSION
        self.ascend_btn.text_color = WHITE if can_ascend else (150, 150, 150)
        # invalidate the cached stat instance when equipment/level changes
        self._stat_hid = None
        for e in events:
            if self.back_btn.clicked(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                self.game.back("roster")
            if self.team_btn.clicked(e):
                if in_team:
                    self.game.player.team = [t for t in self.game.player.team if t != hid]
                    if len(self.game.player.team) < 3:
                        self.game.player.team.append(None)
                else:
                    # add to the first empty slot; if the team is full (no None),
                    # refuse instead of silently overwriting a slot — that would
                    # evict the hero in that slot without telling the player.
                    if None in self.game.player.team:
                        idx = self.game.player.team.index(None)
                        self.game.player.team[idx] = hid
                    else:
                        # team full: flash the button label briefly so the player
                        # sees the team is full rather than losing a hero silently
                        self.team_btn.label = "Team Full!"
                        self._team_full_t = 1.2
                        audio.play("hit", 0.3)
                        return
                self.game.player.save()
                audio.play("menu_click")
            if self.ascend_btn.clicked(e) and can_ascend:
                rec["dupes"] -= 1
                rec["ascension"] = asc + 1
                self.game.player.save()
                audio.play("ultimate", 0.5)
            if self.evolve_btn.clicked(e):
                # jump to the world's evolve overlay for this hero
                self.game.goto("world")
                from world_scene import EvolveOverlay
                self.game.scene.evolve = EvolveOverlay(self.game)
                # select this hero in the overlay
                try:
                    self.game.scene.evolve.sel = self.game.scene.evolve.order.index(hid)
                except Exception:
                    pass
                audio.play("menu_click", 0.3)
            # equip item click: click a slot then an item
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # clicking an equipment slot
                for si, slot in enumerate(self.equip_slots):
                    sr = pygame.Rect(680 + si * 180, 200, 160, 160)
                    if sr.collidepoint(e.pos):
                        # unequip
                        if rec["equipment"].get(slot):
                            self.game.player.unequip(hid, slot)
                            self.game.player.save()
                            audio.play("menu_click")
                        return
                # clicking an inventory item to equip
                for it_rect, item_id in self._item_rects:
                    if it_rect.collidepoint(e.pos):
                        if item_id in self.game.player.equipment_inv:
                            self.game.player.equip(hid, item_id)
                            self.game.player.save()
                            audio.play("menu_click")
                        return

    def draw(self, surf):
        surf.fill(BG_DARK)
        hid = self.hero_id
        hd = D.HERO_BY_ID[hid]
        rec = self.game.player.owned[hid]
        # portrait big
        p = load_portrait(hid, 360)
        draw_panel(surf, (40, 110, 400, 480))
        surf.blit(p, (60, 130))
        text(surf, hd["name"], 36, WHITE, (240, 510), center=True)
        text(surf, hd["title"], 20, DIM, (240, 548), center=True)
        nstars = 3 if hd['rarity'] == "SSR" else (2 if hd['rarity'] == "SR" else 1)
        draw_stars(surf, 240 - 30, 576, nstars, size=12)
        # ascension pips
        asc = rec.get("ascension", 0)
        text(surf, f"Ascension {asc}/{D.MAX_ASCENSION}  (dupes: {rec['dupes']})", 16, (255, 180, 220), (240, 600), center=True)
        # constellation nodes (C1-C6) — 6 pips in a row, lit for each unlocked
        # star, with the NEXT perk's description under the Ascend button so the
        # player sees what the next star will do before spending a dupe.
        perks = D.hero_constellation_perks(hd)
        cx0 = 240 - 90   # center 6 pips of width ~30 each
        for i in range(6):
            cx = cx0 + i * 30
            unlocked = i < asc
            col = (255, 120, 200) if unlocked else (70, 60, 80)
            pygame.draw.circle(surf, col, (cx, 622), 7)
            if unlocked:
                pygame.draw.circle(surf, (255, 220, 240), (cx, 622), 7, 2)
        # next perk description (the one the next Ascend click will unlock)
        if asc < 6:
            np = perks[asc]
            text(surf, f"Next (C{asc+1}): {np['name']} - {np['desc']}", 12,
                 (200, 180, 220), (240, 640), center=True)
        else:
            text(surf, "Constellation MAX", 12, (255, 220, 240), (240, 640), center=True)
        # lore panel: bio + centered italic quote, below the portrait (space at y~620+)
        lore = D.HERO_LORE.get(hid)
        if lore:
            # "italic" via a SysFont with italic=True, cached so we don't rebuild it each frame.
            if not hasattr(self, "_lore_font"):
                self._lore_font = pygame.font.SysFont("dejavusans,arial", 16, italic=True)
            # bio, word-wrapped to the left panel width (x 40..440, ~400 px)
            bio = lore["bio"]
            words = bio.split(" ")
            lines = []
            cur = ""
            for w in words:
                trial = cur + " " + w if cur else w
                if self._lore_font.size(trial)[0] <= 380:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)
            by = 624
            for ln in lines[:3]:
                text(surf, ln, 14, DIM, (60, by))
                by += 18
            # centered italic quote (word-wrapped so long quotes don't overflow the panel)
            qt = lore["quote"]
            qwords = qt.split(" ")
            qlines = []
            qcur = ""
            for w in qwords:
                trial = qcur + " " + w if qcur else w
                if self._lore_font.size(trial)[0] <= 380:
                    qcur = trial
                else:
                    if qcur:
                        qlines.append(qcur)
                    qcur = w
            if qcur:
                qlines.append(qcur)
            qy = by + 8
            for ln in qlines:
                t = self._lore_font.render(ln, True, (220, 200, 160))
                r = t.get_rect(midtop=(240, qy))
                sh = self._lore_font.render(ln, True, (0, 0, 0))
                surf.blit(sh, (r.x + 2, r.y + 2))
                surf.blit(t, r)
                qy += 20
        # stats panel
        draw_panel(surf, (460, 110, 780, 360))
        # cache the hero instance per hero id so we don't rebuild it every frame
        if getattr(self, "_stat_hid", None) != hid:
            self._stat_hid = hid
            self._stat_inst = self.game.player.get_hero_instance(hid)
        h_inst = self._stat_inst
        text(surf, "Stats", 24, GOLD, (480, 124))
        stats = [("HP", h_inst.max_hp, HP_RED), ("ATK", h_inst.atk, (255, 120, 80)),
                 ("DEF", h_inst.defn, (140, 180, 255)), ("SPD", h_inst.spd, (180, 240, 220)),
                 ("MP", h_inst.max_mp, MP_BLUE), ("Crit", f"{int(h_inst.crit_chance*100)}%", (255, 220, 120))]
        # stat rows are kept in the LEFT of the panel (x 460..680) so the bars
        # and values are not obscured by the equipment slots on the right.
        for i, (lbl, val, col) in enumerate(stats):
            y = 160 + i * 36
            text(surf, lbl, 20, WHITE, (470, y))
            if isinstance(val, int):
                # stat bar (relative) — narrow so it stays clear of the slots
                frac = min(1, val / 400)
                draw_bar(surf, (540, y + 4, 110, 20), frac, col)
            text(surf, str(val), 20, col, (660, y))
        # level + xp (left zone, below the stat rows)
        text(surf, f"Level {rec['level']}", 22, WHITE, (470, 384))
        xp_need = D.xp_to_next(rec["level"])
        draw_bar(surf, (540, 390, 110, 18), rec["xp"] / max(1, xp_need), XP_PURPLE)
        text(surf, f"XP {rec['xp']}/{xp_need}", 13, DIM, (660, 386))
        # ultimate / passive / skills / evo — moved up inside the panel (which
        # ends at y=470) so they are no longer overlapped by the inventory list.
        # B5: show the per-hero variant name + desc when one is defined, falling
        # back to the generic SKILLS_DB name otherwise.
        ult_var = D.ULTIMATE_VARIANTS.get(hd["id"]) if hd.get("ultimate") else None
        if ult_var:
            ult_name = ult_var["name"]
            ult_desc = ult_var.get("desc", "")
        else:
            ult_name = D.SKILLS_DB[hd["ultimate"]]["name"] if hd.get("ultimate") else "None"
            ult_desc = ""
        text(surf, f"Ultimate: {ult_name}", 18, (255, 180, 120), (470, 412))
        if ult_desc:
            text(surf, ult_desc, 12, (200, 180, 150), (470, 430))
        pv = h_inst.passive
        if pv:
            text(surf, f"Passive: {pv['name']}", 14, (160, 220, 180), (470, 448))
        ab = D.hero_abilities(hd)
        ab_names = [D.SKILLS_DB[s]["name"] if s and s in D.SKILLS_DB else "-" for s in ab]
        text(surf, f"Q {ab_names[0]}  W {ab_names[1]}  E {ab_names[2]}",
             13, (200, 220, 255), (470, 466))
        # evolution tree progress
        nn = len(rec.get("evo_nodes", []))
        text(surf, f"Evo {nn}/5  Tier {h_inst.evolve_title()}",
             13, (220, 180, 255), (470, 482))
        # equipment slots
        text(surf, "Equipment", 22, GOLD, (680, 168))
        self._item_rects = []
        for si, slot in enumerate(self.equip_slots):
            sr = pygame.Rect(680 + si * 180, 200, 160, 160)
            # slot frame tinted by whether an item is equipped
            eq = rec["equipment"].get(slot)
            slot_col = (70, 60, 90) if eq else (50, 50, 70)
            pygame.draw.rect(surf, slot_col, sr, border_radius=12)
            pygame.draw.rect(surf, (180, 180, 220), sr, 2, border_radius=12)
            text(surf, slot.upper(), 14, DIM, (sr.centerx, sr.bottom + 6), center=True)
            if eq:
                ic = load_item_icon(eq, 120)
                surf.blit(ic, (sr.centerx - 60, sr.y + 20))
                text(surf, D.EQUIPMENT_DB[eq]["name"], 13, WHITE, (sr.centerx, sr.bottom + 24), center=True)
        # active set bonus indicator (below the equipment slots)
        set_name = h_inst.set_name()
        if set_name:
            set_def = next((v for v in D.EQUIPMENT_SETS.values() if v["name"] == set_name), None)
            if set_def:
                text(surf, f"Set: {set_name} ({set_def['desc']})", 13, (255, 220, 120), (680, 372))
        # equipment inventory list — moved below the stats panel (y=490+) so it
        # no longer overlaps the skills/evo text that sat at y=484/504.
        text(surf, "Inventory (click to equip)", 20, GOLD, (460, 484))
        ex, ey = 460, 504
        for i, item_id in enumerate(self.game.player.equipment_inv[:8]):
            col = i % 4
            row = i // 4
            r = pygame.Rect(ex + col * 100, ey + row * 100, 88, 88)
            item = D.EQUIPMENT_DB[item_id]
            pygame.draw.rect(surf, (40, 40, 60), r, border_radius=10)
            pygame.draw.rect(surf, rarity_color(item["rarity"]), r, 2, border_radius=10)
            ic = load_item_icon(item_id, 64)
            surf.blit(ic, (r.x + 12, r.y + 12))
            # stat string under the icon
            stat_str = " ".join(f"+{v}{k[0].upper()}" for k, v in item["stats"].items())
            text(surf, stat_str, 10, (200, 220, 255), (r.centerx, r.bottom - 12), center=True)
            self._item_rects.append((r, item_id))
        # buttons
        self.back_btn.draw(surf)
        self.team_btn.draw(surf)
        self.ascend_btn.draw(surf)
        self.evolve_btn.draw(surf)


class GachaScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.back_btn = Button((40, 40, 140, 48), "Back", (60, 60, 90), (90, 90, 130), size=20)
        self.pull1 = Button((WIDTH // 2 - 240, 600, 200, 64), "Summon x1 (10)", (60, 80, 130), (90, 130, 200))
        self.pull10 = Button((WIDTH // 2 + 40, 600, 200, 64), "Summon x10 (90)", (120, 60, 130), (200, 90, 200))
        self.gacha = GachaSystem(game.player)
        self.banner_id = D.GACHA_BANNERS[0]["id"]
        self.state = "idle"
        self.anim_t = 0
        self.results = []          # list of (hid, rar, is_featured, status, refund)
        self.reveal_idx = 0
        self.reveal_t = 0
        self.t = 0
        self.particles = []
        self.spark_t = 0
        self._rolled_sound = False
        # compact summary of the last batch so a skipped reveal still leaves an
        # at-a-glance record on the idle screen (list of (hid, rar)).
        self._last_summary = []
        # snapshot of owned hero ids before a pull, so the reveal can show NEW!
        self._pre_pull_owned = set(self.game.player.owned.keys())
        self._banner_rects = []    # (banner_id, rect) for the banner selector
        self._skip_hover = None

    def _banner(self):
        return self.gacha.banner(self.banner_id)

    def _build_banner_rects(self):
        self._banner_rects = []
        n = len(D.GACHA_BANNERS)
        bw, bh, gap = 170, 56, 12
        total = n * bw + (n - 1) * gap
        start_x = (WIDTH - total) // 2
        for i, b in enumerate(D.GACHA_BANNERS):
            r = pygame.Rect(start_x + i * (bw + gap), 100, bw, bh)
            self._banner_rects.append((b["id"], r))

    def update(self, dt, events):
        self.t += dt
        mp = pygame.mouse.get_pos()
        mdown = pygame.mouse.get_pressed()[0]
        self.back_btn.update(mp, mdown)
        self.pull1.update(mp, mdown)
        self.pull10.update(mp, mdown)
        self._build_banner_rects()
        if self.state == "idle":
            for e in events:
                if self.back_btn.clicked(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    self.game.back("title")
                # banner selector
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    for bid, r in self._banner_rects:
                        if r.collidepoint(e.pos):
                            if bid != self.banner_id:
                                self.banner_id = bid
                                audio.play("menu_click", 0.3)
                            break
                if self.pull1.clicked(e):
                    if self.gacha.can_pull(1):
                        self._do_pull(1)
                if self.pull10.clicked(e):
                    if self.gacha.can_pull(10):
                        self._do_pull(10)
        elif self.state == "animating":
            self.anim_t += dt
            if not self._rolled_sound and self.anim_t > 0.1:
                audio.play("gacha_roll", 0.5)
                self._rolled_sound = True
            self.spark_t += dt
            if self.spark_t > 0.05:
                self.spark_t = 0
                bcol = self._banner()["color"]
                for _ in range(3):
                    self.particles.append([WIDTH // 2 + random.uniform(-200, 200),
                                           HEIGHT // 2 + random.uniform(-100, 100),
                                           random.uniform(-30, 30), random.uniform(-60, -20),
                                           random.uniform(0.4, 0.8),
                                           random.choice([bcol, (255, 240, 180), (200, 220, 255)])])
            for p in self.particles:
                p[0] += p[2] * dt; p[1] += p[3] * dt; p[4] -= dt
            self.particles = [p for p in self.particles if p[4] > 0]
            if self.anim_t > 1.6:
                self.state = "reveal"; self.reveal_idx = 0; self.reveal_t = 0
                # opening reveal sound scaled to the BEST rarity in the batch
                # (not the first card) so an SSR buried later still triggers the
                # strong cue. Reuse 'victory' as the SSR fanfare.
                _rank = {"SSR": 3, "SR": 2, "R": 1}
                best = max(self.results, key=lambda r: _rank.get(r[1], 1))[1] if self.results else "R"
                if best == "SSR":
                    audio.play("gacha_reveal", 0.9)
                    audio.play("victory", 0.6)
                elif best == "SR":
                    audio.play("gacha_reveal", 0.6)
                else:
                    audio.play("gacha_reveal", 0.4)
                # seed a rarity-scaled radial burst for the first card shown
                if self.results:
                    self._seed_reveal_burst(self.results[0][1])
        elif self.state == "reveal":
            self.reveal_t += dt
            # update + cull the reveal burst particles
            for p in self.particles:
                p[0] += p[2] * dt; p[1] += p[3] * dt; p[4] -= dt
            self.particles = [p for p in self.particles if p[4] > 0]
            for e in events:
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 or \
                   (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE)):
                    # advance to the next card; play a per-card rarity sound
                    if self.reveal_idx < len(self.results) - 1:
                        self.reveal_idx += 1; self.reveal_t = 0
                        nrar = self.results[self.reveal_idx][1]
                        if nrar == "SSR":
                            audio.play("gacha_reveal", 0.8)
                        elif nrar == "SR":
                            audio.play("gacha_reveal", 0.5)
                        else:
                            audio.play("menu_click", 0.3)
                        self._seed_reveal_burst(nrar)
                    else:
                        self.state = "idle"; self.results = []
                    return
                # Esc / right-click skips the whole reveal (summary is retained)
                if (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE) or \
                   (e.type == pygame.MOUSEBUTTONDOWN and e.button == 3):
                    self.state = "idle"; self.results = []
                    return
            # auto-advance with a rarity-scaled dwell so SSR breathes and R
            # dismisses quickly (a 10-pull of mostly R cards does not drag).
            rar = self.results[self.reveal_idx][1] if self.results else "R"
            dwell = {"SSR": 3.2, "SR": 2.2, "R": 1.2}.get(rar, 2.0)
            if self.reveal_t > dwell:
                if self.reveal_idx < len(self.results) - 1:
                    self.reveal_idx += 1; self.reveal_t = 0
                    self._seed_reveal_burst(self.results[self.reveal_idx][1])
                else:
                    self.state = "idle"; self.results = []

    def _seed_reveal_burst(self, rar):
        """Seed a rarity-scaled radial particle burst for a revealed card."""
        n_burst = 50 if rar == "SSR" else (25 if rar == "SR" else 0)
        for _ in range(n_burst):
            ang = random.uniform(0, math.tau)
            spd = random.uniform(140, 380) if rar == "SSR" else random.uniform(90, 220)
            self.particles.append([WIDTH // 2, HEIGHT // 2 - 20,
                                  math.cos(ang) * spd, math.sin(ang) * spd,
                                  random.uniform(0.6, 1.2),
                                  D.RARITY_COLORS.get(rar, (255, 240, 180))])

    def _do_pull(self, count):
        self._pre_pull_owned = set(self.game.player.owned.keys())
        self.game.player.gems -= self.gacha.cost(count)
        self.game.player.record_pulls(count)
        self.game.player.quest_progress("summon", count)
        raw = self.gacha.pull(self.banner_id, count)
        # apply each result and record status + any gem refund
        self.results = []
        for hid, rar, is_feat in raw:
            status, refund = self.gacha.apply_result(hid, rar, is_feat)
            self.results.append((hid, rar, is_feat, status, refund))
        # sort worst-to-best so the reveal builds toward the rarest card
        # ("save the best for last") and the opening cue matches the best pull.
        _order = {"R": 0, "SR": 1, "SSR": 2}
        self.results.sort(key=lambda r: _order.get(r[1], 0))
        # keep a compact summary of the last batch so a skipped reveal still
        # leaves an at-a-glance record on the idle screen.
        self._last_summary = [(r[0], r[1]) for r in self.results]
        self.game.player.check_achievements()
        self.game.player.save()
        self.state = "animating"; self.anim_t = 0
        self._rolled_sound = False
        self.particles = []

    def draw(self, surf):
        bcol = self._banner()["color"]
        # banner-tinted vertical gradient background
        for y in range(0, HEIGHT, 4):
            t = y / HEIGHT
            col = (int(20 + bcol[0] * 0.18 * t), int(18 + bcol[1] * 0.18 * t),
                   int(34 + bcol[2] * 0.22 * t))
            pygame.draw.rect(surf, col, (0, y, WIDTH, 4))
        text(surf, "Summoning Gate", 40, (255, 220, 160), (WIDTH // 2, 40), center=True)
        text(surf, f"Gems: {self.game.player.gems}", 22, (120, 200, 255), (WIDTH - 220, 50))
        text(surf, f"Gold: {self.game.player.gold}", 22, GOLD, (WIDTH - 220, 80))
        # banner selector tabs
        for bid, r in self._banner_rects:
            b = self.gacha.banner(bid)
            sel = (bid == self.banner_id)
            col = b["color"] if sel else (50, 50, 70)
            pygame.draw.rect(surf, col, r, border_radius=10)
            pygame.draw.rect(surf, (240, 240, 255) if sel else (90, 90, 120), r, 2, border_radius=10)
            text(surf, b["name"], 14, WHITE if sel else (180, 180, 200), r.center, center=True)
        # banner info + pity meter
        b = self._banner()
        pity = self.gacha.pity(self.banner_id)
        to_hard = self.gacha.pity_to_hard(self.banner_id)
        draw_panel(surf, (40, 180, 360, 380))
        text(surf, b["name"], 26, b["color"], (220, 196), center=False)
        text(surf, b["desc"], 14, DIM, (60, 230))
        # featured hero portrait
        feat = b.get("featured_ssr")
        if feat:
            fp = load_portrait(feat, 200)
            surf.blit(fp, (70, 260))
            text(surf, "Featured", 14, (255, 220, 120), (170, 470), center=True)
            text(surf, D.HERO_BY_ID[feat]["name"], 18, WHITE, (170, 490), center=True)
            text(surf, "Rate-up 50% SSR", 12, (255, 200, 120), (170, 512), center=True)
        # pity meter
        text(surf, "Pity Meter", 16, (220, 220, 240), (60, 540))
        pm = pygame.Rect(60, 562, 320, 16)
        pygame.draw.rect(surf, (40, 40, 60), pm, border_radius=8)
        frac = pity / self.gacha.PITY_HARD
        fw = int(pm.width * frac)
        if fw > 0:
            pygame.draw.rect(surf, (255, 120, 180) if frac > 0.66 else (255, 200, 120),
                             (pm.x, pm.y, fw, pm.height), border_radius=8)
        pygame.draw.rect(surf, (200, 200, 230), pm, 1, border_radius=8)
        text(surf, f"{pity}/{self.gacha.PITY_HARD}  ({to_hard} to SSR)", 13, DIM, (220, 582), center=True)
        if self.state in ("idle", "animating"):
            cx, cy = WIDTH // 2 + 80, 360
            for r in range(180, 0, -10):
                t = r / 180
                col = (min(255, int(bcol[0] * (1 - t) + 60)),
                       min(255, int(bcol[1] * (1 - t) + 50)),
                       min(255, int(bcol[2] * (1 - t) + 90)))
                pygame.draw.circle(surf, col, (cx, cy), r)
            if self.state == "animating":
                rot = self.anim_t * 6
                pulse = 1 + math.sin(self.anim_t * 8) * 0.1
                pygame.draw.circle(surf, (255, 240, 180), (cx, cy), int(40 * pulse))
                for i in range(12):
                    a = rot + i * math.pi / 6
                    x = cx + math.cos(a) * (60 + 40 * math.sin(self.anim_t * 4))
                    y = cy + math.sin(a) * (60 + 40 * math.sin(self.anim_t * 4))
                    pygame.draw.circle(surf, (255, 240, 180), (int(x), int(y)), 6)
                text(surf, "Summoning...", 32, WHITE, (cx, cy + 220), center=True)
            else:
                text(surf, "Pull a hero!", 28, (220, 220, 240), (cx, cy + 220), center=True)
            for p in self.particles:
                pygame.draw.circle(surf, p[5], (int(p[0]), int(p[1])), int(p[4] * 6))
            can1 = self.gacha.can_pull(1)
            can10 = self.gacha.can_pull(10)
            self.pull1.text_color = WHITE if can1 else (150, 150, 150)
            self.pull10.text_color = WHITE if can10 else (150, 150, 150)
            self.pull1.draw(surf)
            self.pull10.draw(surf)
            text(surf, "SSR 6%  |  SR 30%  |  R 64%", 18, DIM, (WIDTH // 2, 670), center=True)
            text(surf, "Guaranteed SR+ every 10 pulls  |  Guaranteed SSR every 60 pulls",
                 14, (200, 160, 120), (WIDTH // 2, 694), center=True)
            # compact "Last pull" summary so a skipped reveal still leaves a
            # record of the most recent batch (shown on the idle screen).
            if self._last_summary:
                from collections import Counter
                cnt = Counter(r for _, r in self._last_summary)
                summary = "  ".join(f"{cnt[r]}{r}" for r in ("SSR", "SR", "R") if cnt.get(r))
                text(surf, f"Last pull: {summary}", 14, (200, 200, 220), (220, 612), center=True)
            self.back_btn.draw(surf)
        elif self.state == "reveal":
            self._draw_reveal(surf)

    def _draw_reveal(self, surf):
        hid, rar, is_feat, status, refund = self.results[self.reveal_idx]
        hd = D.HERO_BY_ID[hid]
        rcol = D.RARITY_COLORS.get(rar, (200, 200, 200))
        # dim backdrop (cached)
        surf.blit(_dim_overlay(180), (0, 0))
        # multi-stage scale keyed to rarity: SSR gets a slow zoom + overshoot,
        # SR a single pop, R a quick snap — so an SSR lands with more weight.
        if rar == "SSR":
            if self.reveal_t < 0.6:
                scale = 0.3 + 0.3 * (self.reveal_t / 0.6)
            elif self.reveal_t < 1.0:
                u = (self.reveal_t - 0.6) / 0.4
                scale = 0.6 + 0.4 * u + math.sin(u * math.pi) * 0.12
            else:
                scale = 1.0 + math.sin((self.reveal_t - 1.0) * 6) * 0.03
        elif rar == "SR":
            pop = min(1.0, self.reveal_t * 4)
            scale = 0.6 + 0.4 * pop
            if self.reveal_t < 0.3:
                scale *= 1 + math.sin(self.reveal_t * 20) * 0.05
        else:  # R - quick snap, no fanfare
            pop = min(1.0, self.reveal_t * 6)
            scale = 0.6 + 0.4 * pop
        cw, ch = int(360 * scale), int(460 * scale)
        cx, cy = WIDTH // 2, HEIGHT // 2 - 20
        # decaying screen shake for SSR on entry (first 0.5s only)
        shake_x = 0
        if rar == "SSR" and self.reveal_t < 0.5:
            shake_x = math.sin(self.reveal_t * 40) * 8 * (1 - self.reveal_t / 0.5)
        rect = pygame.Rect(0, 0, cw, ch); rect.center = (cx + int(shake_x), cy)
        # rarity glow behind the card (reused scratch surface)
        glow = _scratch(cw + 120, ch + 120)
        for r in range(60, 0, -6):
            a = int(120 * (1 - r / 60))
            pygame.draw.rect(glow, (*rcol, a), (60 - r, 60 - r, cw + 2 * r, ch + 2 * r),
                             border_radius=24 + r)
        surf.blit(glow, (rect.x - 60, rect.y - 60))
        frame = load_ui(f"frame_{rar}")
        frame = pygame.transform.smoothscale(frame, (cw, ch))
        surf.blit(frame, rect.topleft)
        # the character sprite (bright chibi on transparent bg) over a bright
        # element-tinted card — the portrait is too dark for the reveal (the
        # "face too dark" fix). The portrait stays for the codex headshot.
        el_main = D.ELEMENT_COLORS.get(hd["element"], ((200, 200, 220),))[0]
        card_size = int(cw * 0.9)
        card = _scratch(card_size, card_size)
        pygame.draw.rect(card, (*el_main, 60), card.get_rect(), border_radius=24)
        pygame.draw.rect(card, (255, 255, 255, 40), card.get_rect(), 3, border_radius=24)
        surf.blit(card, (rect.centerx - card_size // 2, rect.y + 16))
        p = load_char_sprite(hid, card_size)
        p2 = pygame.transform.smoothscale(p, (card_size, card_size))
        surf.blit(p2, (rect.centerx - p2.get_width() // 2, rect.y + 16))
        # rotating rays scaled by rarity (SSR denser + counter-rotating set)
        if rar == "SSR":
            ray = _scratch(WIDTH, HEIGHT)
            for i in range(16):
                a = self.reveal_t * 2 + i * math.pi / 8
                x1 = cx + math.cos(a) * 50; y1 = cy + math.sin(a) * 50
                x2 = cx + math.cos(a) * 700; y2 = cy + math.sin(a) * 700
                pygame.draw.line(ray, (255, 240, 180, 90), (x1, y1), (x2, y2), 10)
            for i in range(8):
                a = -self.reveal_t * 2 + i * math.pi / 4
                x1 = cx + math.cos(a) * 40; y1 = cy + math.sin(a) * 40
                x2 = cx + math.cos(a) * 400; y2 = cy + math.sin(a) * 400
                pygame.draw.line(ray, (255, 200, 240, 50), (x1, y1), (x2, y2), 4)
            surf.blit(ray, (0, 0))
        elif rar == "SR":
            ray = _scratch(WIDTH, HEIGHT)
            for i in range(8):
                a = self.reveal_t * 2 + i * math.pi / 4
                x1 = cx + math.cos(a) * 50; y1 = cy + math.sin(a) * 50
                x2 = cx + math.cos(a) * 500; y2 = cy + math.sin(a) * 500
                pygame.draw.line(ray, (255, 240, 180, 30), (x1, y1), (x2, y2), 6)
            surf.blit(ray, (0, 0))
        is_new = status == "new"
        text(surf, hd["name"], 36, WHITE, (cx, rect.bottom - 90), center=True)
        text(surf, hd["title"], 20, DIM, (cx, rect.bottom - 50), center=True)
        draw_stars(surf, cx - 60, rect.bottom - 24, 3 if rar == "SSR" else (2 if rar == "SR" else 1), size=14)
        # rarity label — SSR appears after the flash stage with a pulse; SR after
        # a short delay; R immediately, so the rarity itself is the climax.
        if rar == "SSR":
            if self.reveal_t > 0.6:
                c = (255, 120 + int(60 * math.sin(self.reveal_t * 8)), 180)
                text(surf, "SSR!", 56, c, (cx, 120), center=True)
        elif rar == "SR":
            if self.reveal_t > 0.3:
                text(surf, "SR!", 48, (255, 180, 80), (cx, 120), center=True)
        else:
            text(surf, "R", 40, (180, 200, 220), (cx, 120), center=True)
        if is_feat:
            text(surf, "RATE-UP!", 24, (255, 220, 120), (cx, 170), center=True)
        if is_new:
            text(surf, "NEW!", 28, (140, 240, 160), (cx, 200), center=True)
        else:
            text(surf, "DUPE", 24, (200, 180, 120), (cx, 200), center=True)
            if refund:
                text(surf, f"+{refund} gems (maxed)", 16, (255, 220, 120), (cx, 226), center=True)
        # reveal burst particles (drawn in the reveal state too)
        for p in self.particles:
            pygame.draw.circle(surf, p[5], (int(p[0]), int(p[1])), int(p[4] * 6))
        # multi-reveal progress dots: revealed full, current pulsing, future dim
        n = len(self.results)
        dot_y = HEIGHT - 70
        dot_w = 14
        total_w = n * dot_w + (n - 1) * 8
        dx = (WIDTH - total_w) // 2
        for i in range(n):
            r_i = self.results[i][1]
            c = D.RARITY_COLORS.get(r_i, (120, 120, 140))
            cx_d = dx + i * (dot_w + 8) + dot_w // 2
            if i < self.reveal_idx:
                pygame.draw.circle(surf, c, (cx_d, dot_y), dot_w // 2)
            elif i == self.reveal_idx:
                dr = dot_w // 2 + int(2 + 2 * math.sin(self.reveal_t * 8))
                pygame.draw.circle(surf, (255, 255, 255), (cx_d, dot_y), dr)
                pygame.draw.circle(surf, c, (cx_d, dot_y), dot_w // 2)
            else:
                # not-yet-revealed: dimmed, no spoiler
                dim_c = tuple(int(v * 0.4) for v in c)
                pygame.draw.circle(surf, dim_c, (cx_d, dot_y), dot_w // 2)
        text(surf, f"{self.reveal_idx + 1} / {n}  -  Click to continue  (Esc skip)",
             18, DIM, (WIDTH // 2, HEIGHT - 40), center=True)



class ShopScene(Scene):
    """Buy consumables, equipment and gems with gold."""
    def __init__(self, game):
        super().__init__(game)
        self.bg = load_bg("shop")
        self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        self.back_btn = Button((40, 40, 140, 48), "Back", (60, 60, 90), (90, 90, 130), size=20)
        self.t = 0
        self.toast = ""
        self.toast_t = 0
        # cached draw-state; initialized here so draw() is safe before the first
        # update() (goto swaps the scene mid-frame then calls draw()).
        self.consumable_rects = []
        self.equip_rects = []
        self.gem_rects = []
        # equipment list scroll — there are 17 equipment items in 5 columns, so
        # rows 2-3 fall off the bottom of the 720px screen without scrolling.
        self.equip_scroll = 0
        self._build_shop_rects()

    def _build_shop_rects(self):
        # consumables
        self.consumable_rects = []
        for i, (iid, item) in enumerate(D.CONSUMABLES_DB.items()):
            col = i % 5
            row = i // 5
            r = pygame.Rect(80 + col * 220, 180 + row * 180, 200, 160)
            self.consumable_rects.append((iid, r))
        # equipment — offset by the scroll so all 17 items are reachable
        self.equip_rects = []
        for i, (iid, item) in enumerate(D.EQUIPMENT_DB.items()):
            col = i % 5
            row = i // 5
            r = pygame.Rect(80 + col * 220, 470 + row * 180 - self.equip_scroll, 200, 160)
            self.equip_rects.append((iid, r))
        # gem packs
        self.gem_rects = []
        for i, offer in enumerate(D.SHOP_GEMS):
            r = pygame.Rect(WIDTH - 280, 180 + i * 90, 240, 78)
            self.gem_rects.append((offer["id"], r))

    def update(self, dt, events):
        self.t += dt
        if self.toast_t > 0:
            self.toast_t -= dt
        mp = pygame.mouse.get_pos()
        mdown = pygame.mouse.get_pressed()[0]
        self.back_btn.update(mp, mdown)
        self._build_shop_rects()
        for e in events:
            if self.back_btn.clicked(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                self.game.back("title")
            # equipment list scroll (mouse wheel) so all 17 items are reachable
            if e.type == pygame.MOUSEWHEEL:
                # Scroll enough to bring the last row fully into view. Clamped so
                # the list doesn't scroll past its end.
                rows = (len(D.EQUIPMENT_DB) + 4) // 5
                max_scroll = max(0, 470 + (rows - 1) * 180 + 160 - HEIGHT)
                self.equip_scroll = max(0, min(max_scroll, self.equip_scroll - e.y * 40))
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for iid, r in self.consumable_rects:
                    if r.collidepoint(e.pos):
                        if self.game.player.buy_consumable(iid):
                            self.toast = f"Bought {D.CONSUMABLES_DB[iid]['name']}!"
                            self.toast_t = 1.5
                            audio.play("menu_click")
                        else:
                            self.toast = "Not enough gold!"
                            self.toast_t = 1.2
                        return
                for iid, r in self.equip_rects:
                    if r.collidepoint(e.pos):
                        if self.game.player.buy_equipment(iid):
                            self.toast = f"Bought {D.EQUIPMENT_DB[iid]['name']}!"
                            self.toast_t = 1.5
                            audio.play("menu_click")
                        else:
                            self.toast = "Not enough gold!"
                            self.toast_t = 1.2
                        return
                for oid, r in self.gem_rects:
                    if r.collidepoint(e.pos):
                        if self.game.player.buy_gems(oid):
                            offer = next(o for o in D.SHOP_GEMS if o["id"] == oid)
                            self.toast = f"Bought {offer['name']}!"
                            self.toast_t = 1.5
                            audio.play("menu_click")
                        else:
                            self.toast = "Not enough gold!"
                            self.toast_t = 1.2
                        return

    def draw(self, surf):
        surf.blit(self.bg, (0, 0))
        # dim overlay for readability (cached)
        surf.blit(_dim_overlay(120, (10, 10, 20)), (0, 0))
        text(surf, "Shop", 40, GOLD, (WIDTH // 2, 40), center=True)
        text(surf, f"Gold: {self.game.player.gold}", 24, GOLD, (WIDTH - 200, 50))
        text(surf, f"Gems: {self.game.player.gems}", 24, (120, 200, 255), (WIDTH - 200, 80))
        # consumables
        text(surf, "Consumables", 24, WHITE, (80, 150))
        for iid, r in self.consumable_rects:
            item = D.CONSUMABLES_DB[iid]
            can = self.game.player.gold >= item["price"]
            pygame.draw.rect(surf, (40, 40, 60, 220), r, border_radius=12)
            pygame.draw.rect(surf, (140, 200, 120) if can else (80, 80, 90), r, 2, border_radius=12)
            ic = load_item_icon(iid, 80)
            surf.blit(ic, (r.centerx - 40, r.y + 10))
            text(surf, item["name"], 16, WHITE if can else (140, 140, 150), (r.centerx, r.y + 96), center=True)
            text(surf, item["desc"], 11, DIM, (r.centerx, r.y + 116), center=True)
            text(surf, f"{item['price']}G", 18, GOLD if can else (120, 100, 60), (r.centerx, r.y + 138), center=True)
        # equipment
        text(surf, "Equipment", 24, WHITE, (80, 440))
        # clip the equipment grid to the region below the header so scrolled rows
        # don't overlap the consumables above while the player reaches row 3.
        old_clip = surf.get_clip()
        surf.set_clip(pygame.Rect(0, 440, WIDTH, HEIGHT - 440))
        for iid, r in self.equip_rects:
            item = D.EQUIPMENT_DB[iid]
            can = self.game.player.gold >= item["price"]
            pygame.draw.rect(surf, (40, 40, 60, 220), r, border_radius=12)
            pygame.draw.rect(surf, rarity_color(item["rarity"]) if can else (80, 80, 90), r, 2, border_radius=12)
            ic = load_item_icon(iid, 80)
            surf.blit(ic, (r.centerx - 40, r.y + 10))
            text(surf, item["name"], 16, WHITE if can else (140, 140, 150), (r.centerx, r.y + 96), center=True)
            stat_str = " ".join(f"+{v} {k.upper()}" for k, v in item["stats"].items())
            text(surf, stat_str, 11, DIM, (r.centerx, r.y + 116), center=True)
            text(surf, f"{item['price']}G", 18, GOLD if can else (120, 100, 60), (r.centerx, r.y + 138), center=True)
        surf.set_clip(old_clip)
        # gem packs
        text(surf, "Gem Packs", 22, (120, 200, 255), (WIDTH - 160, 150), center=True)
        for oid, r in self.gem_rects:
            offer = next(o for o in D.SHOP_GEMS if o["id"] == oid)
            can = self.game.player.gold >= offer["price"]
            pygame.draw.rect(surf, (30, 40, 70, 220), r, border_radius=12)
            pygame.draw.rect(surf, (120, 200, 255) if can else (80, 80, 90), r, 2, border_radius=12)
            text(surf, offer["name"], 18, WHITE if can else (140, 140, 150), (r.x + 16, r.y + 10))
            text(surf, f"+{offer['gems']} gems", 14, (120, 200, 255), (r.x + 16, r.y + 34))
            text(surf, f"{offer['price']}G", 20, GOLD if can else (120, 100, 60), (r.right - 16, r.y + 26))
        self.back_btn.draw(surf)
        # toast
        if self.toast_t > 0:
            tw = 300
            draw_panel(surf, (WIDTH // 2 - tw // 2, HEIGHT - 100, tw, 50))
            text(surf, self.toast, 22, WHITE, (WIDTH // 2, HEIGHT - 75), center=True)


class InventoryScene(Scene):
    """View and use consumables; sell items for gold."""
    def __init__(self, game):
        super().__init__(game)
        self.back_btn = Button((40, 40, 140, 48), "Back", (60, 60, 90), (90, 90, 130), size=20)
        self.t = 0
        self.toast = ""
        self.toast_t = 0
        # cached draw-state so draw() is safe before the first update()
        self._item_rects = []        # (iid, use_rect, sell_rect)

    def update(self, dt, events):
        self.t += dt
        if self.toast_t > 0:
            self.toast_t -= dt
        mp = pygame.mouse.get_pos()
        mdown = pygame.mouse.get_pressed()[0]
        self.back_btn.update(mp, mdown)
        for e in events:
            if self.back_btn.clicked(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                self.game.back("title")
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for iid, use_r, sell_r in self._item_rects:
                    if use_r.collidepoint(e.pos) and self.game.player.has_item(iid):
                        used = self._use_consumable(iid)
                        self.toast = used
                        self.toast_t = 1.6
                        audio.play("menu_click")
                        return
                    if sell_r.collidepoint(e.pos) and self.game.player.has_item(iid):
                        if self.game.player.sell_item(iid):
                            self.toast = f"Sold {D.CONSUMABLES_DB[iid]['name']}!"
                            self.toast_t = 1.4
                            audio.play("menu_click")
                        return

    def _use_consumable(self, iid):
        """Apply a consumable to the world party (heal/restore the active hero,
        or all for elixir). Returns a toast string."""
        p = self.game.player
        item = D.CONSUMABLES_DB.get(iid)
        if not item or not p.has_item(iid):
            return "Nothing to use"
        # find the active hero from the world scene if present, else the team
        target = None
        ws = getattr(self.game, "scene", None)
        if ws and hasattr(ws, "party") and hasattr(ws, "active"):
            try:
                wc = ws.party[ws.active]
                if wc and wc.alive:
                    target = wc
            except Exception:
                target = None
        itype = item["type"]
        if itype in ("heal_hp", "heal_mp", "heal_full"):
            if target is None:
                return "Enter the world to use healing items"
            if itype == "heal_hp":
                target.heal(item["power"])
                msg = f"+{item['power']} HP"
            elif itype == "heal_mp":
                target.add_energy(item["power"])
                msg = f"+{item['power']} energy"
            else:
                target.heal(target.hero.max_hp)
                target.add_energy(target.hero.max_energy)
                msg = "Fully restored!"
            p.use_item(iid)
            audio.play("heal", 0.4)
            return msg
        if itype == "revive":
            # revive the first downed party member at 50% HP
            if ws and hasattr(ws, "party"):
                for wc in ws.party:
                    if wc and not wc.alive:
                        wc.alive = True
                        wc.hero.hp = int(wc.hero.max_hp * item.get("power", 0.5))
                        wc.hero.energy = wc.hero.max_energy // 2
                        p.use_item(iid)
                        audio.play("heal", 0.5)
                        return f"Revived {wc.hero.name}!"
                return "No fallen allies"
            return "Enter the world to revive"
        # damage items (bomb/mega_bomb) are used in the world on nearby enemies
        if itype == "damage":
            if ws and hasattr(ws, "enemies"):
                hit = 0
                for en in list(ws.enemies):
                    if en.alive:
                        en.enemy.hp -= item["power"]
                        hit += 1
                        if en.enemy.hp <= 0:
                            en.alive = False
                        if hit >= 3:
                            break
                if hit:
                    p.use_item(iid)
                    audio.play("explosion", 0.5)
                    return f"Bomb hit {hit} enemies!"
                return "No enemies in range"
            return "Enter the world to use bombs"
        return "Can't use that here"

    def draw(self, surf):
        surf.fill(BG_DARK)
        p = self.game.player
        text(surf, "Inventory", 40, WHITE, (WIDTH // 2, 40), center=True)
        text(surf, "Use consumables on your active hero  |  Sell for gold", 16, DIM,
             (WIDTH // 2, 76), center=True)
        text(surf, f"Gold: {p.gold}", 22, GOLD, (WIDTH - 200, 50))
        items = list(p.inventory.items())
        self._item_rects = []
        for i, (iid, count) in enumerate(items):
            col = i % 6
            row = i // 6
            r = pygame.Rect(120 + col * 180, 110 + row * 220, 160, 200)
            item = D.CONSUMABLES_DB.get(iid)
            if not item:
                continue
            pygame.draw.rect(surf, (40, 40, 60), r, border_radius=12)
            pygame.draw.rect(surf, (180, 180, 220), r, 2, border_radius=12)
            ic = load_item_icon(iid, 100)
            surf.blit(ic, (r.centerx - 50, r.y + 16))
            text(surf, item["name"], 16, WHITE, (r.centerx, r.y + 124), center=True)
            text(surf, item["desc"], 11, DIM, (r.centerx, r.y + 144), center=True)
            text(surf, f"x{count}", 22, GOLD, (r.centerx, r.y + 164), center=True)
            # use + sell buttons
            use_r = pygame.Rect(r.x + 10, r.bottom - 26, 70, 22)
            sell_r = pygame.Rect(r.right - 80, r.bottom - 26, 70, 22)
            pygame.draw.rect(surf, (60, 120, 90), use_r, border_radius=6)
            pygame.draw.rect(surf, (200, 200, 240), use_r, 1, border_radius=6)
            text(surf, "Use", 14, WHITE, use_r.center, center=True)
            pygame.draw.rect(surf, (120, 90, 50), sell_r, border_radius=6)
            pygame.draw.rect(surf, (200, 200, 240), sell_r, 1, border_radius=6)
            text(surf, f"Sell {item.get('sell', 0)}g", 11, WHITE, sell_r.center, center=True)
            self._item_rects.append((iid, use_r, sell_r))
        # equipment inventory (owned equipment not equipped)
        eq_items = list(p.equipment_inv)
        if eq_items:
            text(surf, "Equipment (equip in Heroes -> Details)", 20, GOLD, (120, 560))
            for i, item_id in enumerate(eq_items[:12]):
                col = i % 6
                r = pygame.Rect(120 + col * 90, 590, 80, 80)
                item = D.EQUIPMENT_DB.get(item_id)
                if not item:
                    continue
                pygame.draw.rect(surf, (40, 40, 60), r, border_radius=8)
                pygame.draw.rect(surf, rarity_color(item["rarity"]), r, 2, border_radius=8)
                ic = load_item_icon(item_id, 64)
                surf.blit(ic, (r.x + 8, r.y + 8))
        if self.toast_t > 0:
            draw_panel(surf, (WIDTH // 2 - 180, HEIGHT - 80, 360, 48))
            text(surf, self.toast, 22, WHITE, (WIDTH // 2, HEIGHT - 56), center=True)
        self.back_btn.draw(surf)


# ---------------------------------------------------------------------------
# Settings scene — a full, tabbed settings menu
# ---------------------------------------------------------------------------
class SettingsScene(Scene):
    """Full settings: Audio, Display, Gameplay, Accessibility, Data tabs."""
    TABS = ["Audio", "Display", "Gameplay", "Access", "Data"]

    def __init__(self, game):
        super().__init__(game)
        self.back_btn = Button((40, 40, 140, 48), "Back", (60, 60, 90), (90, 90, 130), size=20)
        self.tab = "Audio"
        self.t = 0
        self.confirming = False
        # tab buttons across the top
        tw = 150
        tx = WIDTH // 2 - (len(self.TABS) * tw) // 2
        self.tab_btns = []
        for i, name in enumerate(self.TABS):
            b = Button((tx + i * tw, 120, tw - 10, 44), name,
                       (60, 70, 110), (90, 120, 180), size=18)
            self.tab_btns.append((name, b))
        # panel area
        self.px, self.py = 220, 190
        self.pw, self.ph = WIDTH - 440, HEIGHT - 260
        # build widgets for the current tab (rebuilt on tab change)
        self._widgets = {}
        self._labels = []
        self._build_tab()

    # --- settings helpers ---
    def _s(self, key, default):
        return self.game.player.settings.get(key, default)

    def _set(self, key, value):
        self.game.player.settings[key] = value
        self.game.player.save()

    def _apply_runtime(self):
        """Push settings that have live runtime effects (audio, display)."""
        s = self.game.player.settings
        audio.set_enabled(s.get("sound", True))
        audio.set_master_volume(s.get("sfx_volume", 0.7))

    def _build_tab(self):
        self._widgets = {}
        self._labels = []
        s = self.game.player.settings
        x = self.px + 40
        y = self.py + 30
        row_h = 64

        def label(txt):
            self._labels.append((txt, x, y + 6))
            return y + 34   # widget y under the label

        if self.tab == "Audio":
            wy = label("Master Sound")
            t = Toggle(x, wy, value=s.get("sound", True),
                       on_change=lambda v: (self._set("sound", v), self._apply_runtime()))
            self._widgets["sound"] = t
            self._labels.append(("Enable all sound effects", x + 80, wy + 6))
            y += row_h
            wy = label("SFX Volume")
            sl = Slider(x, wy, 360, value=s.get("sfx_volume", 0.7),
                        on_change=lambda v: (self._set("sfx_volume", v), self._apply_runtime()))
            self._widgets["sfx_volume"] = sl
            self._labels.append((f"{int(s.get('sfx_volume',0.7)*100)}%", x + 380, wy - 2))
            y += row_h
            wy = label("Music Volume")
            sl2 = Slider(x, wy, 360, value=s.get("music_volume", 0.5),
                         on_change=lambda v: self._set("music_volume", v))
            self._widgets["music_volume"] = sl2
            self._labels.append((f"{int(s.get('music_volume',0.5)*100)}%", x + 380, wy - 2))
            y += row_h
            wy = label("Text Speed")
            sl3 = Slider(x, wy, 360, value=s.get("text_speed", 1.0),
                         vmin=0.5, vmax=2.0, step=0.05,
                         on_change=lambda v: self._set("text_speed", v))
            self._widgets["text_speed"] = sl3
            self._labels.append((f"x{s.get('text_speed',1.0):.2f}", x + 380, wy - 2))

        elif self.tab == "Display":
            wy = label("Fullscreen")
            t = Toggle(x, wy, value=s.get("fullscreen", False),
                       on_change=lambda v: (self._set("fullscreen", v), self._apply_display()))
            self._widgets["fullscreen"] = t
            self._labels.append(("Borderless fullscreen window", x + 80, wy + 6))
            y += row_h
            wy = label("Show FPS")
            t2 = Toggle(x, wy, value=s.get("show_fps", False),
                        on_change=lambda v: self._set("show_fps", v))
            self._widgets["show_fps"] = t2
            self._labels.append(("Show a frames-per-second counter", x + 80, wy + 6))
            y += row_h
            wy = label("Frame Rate Cap")
            sl = Slider(x, wy, 360, value=s.get("fps_cap", 60),
                        vmin=30, vmax=144, step=6,
                        on_change=lambda v: self._set("fps_cap", int(v)))
            self._widgets["fps_cap"] = sl
            self._labels.append((f"{int(s.get('fps_cap',60))} fps", x + 380, wy - 2))
            y += row_h
            wy = label("Particle Quality")
            sl2 = Slider(x, wy, 360, value=s.get("particle_quality", 1.0),
                         vmin=0.4, vmax=1.0, step=0.1,
                         on_change=lambda v: self._set("particle_quality", round(v, 2)))
            self._widgets["particle_quality"] = sl2
            self._labels.append((f"{int(s.get('particle_quality',1.0)*100)}%", x + 380, wy - 2))

        elif self.tab == "Gameplay":
            wy = label("Auto Save")
            t = Toggle(x, wy, value=s.get("auto_save", True),
                       on_change=lambda v: self._set("auto_save", v))
            self._widgets["auto_save"] = t
            self._labels.append(("Save on map changes and deaths", x + 80, wy + 6))
            y += row_h
            wy = label("Damage Numbers")
            t2 = Toggle(x, wy, value=s.get("damage_numbers", True),
                        on_change=lambda v: self._set("damage_numbers", v))
            self._widgets["damage_numbers"] = t2
            self._labels.append(("Show floating damage/heal text", x + 80, wy + 6))
            y += row_h
            wy = label("Controls Hints")
            t3 = Toggle(x, wy, value=s.get("show_hints", True),
                        on_change=lambda v: self._set("show_hints", v))
            self._widgets["show_hints"] = t3
            self._labels.append(("Show the controls bar in the world", x + 80, wy + 6))
            y += row_h
            wy = label("Screen Shake")
            sl = Slider(x, wy, 360, value=s.get("screen_shake", 1.0),
                        vmin=0.0, vmax=1.0, step=0.1,
                        on_change=lambda v: self._set("screen_shake", round(v, 2)))
            self._widgets["screen_shake"] = sl
            self._labels.append((f"{int(s.get('screen_shake',1.0)*100)}%", x + 380, wy - 2))

        elif self.tab == "Access":
            wy = label("Reduce Motion")
            t = Toggle(x, wy, value=s.get("reduce_motion", False),
                       on_change=lambda v: self._set("reduce_motion", v))
            self._widgets["reduce_motion"] = t
            self._labels.append(("Dampen screen shake, flashes, and wipes", x + 80, wy + 6))
            y += row_h
            # a friendly explanation block
            self._labels.append(("Reduce Motion overrides Shake and Particle", x, y + 6))
            self._labels.append(("settings for a calmer experience.", x, y + 30))
            y += row_h
            wy = label("High Contrast UI (auto)")
            t2 = Toggle(x, wy, value=s.get("high_contrast", False),
                        on_change=lambda v: self._set("high_contrast", v))
            self._widgets["high_contrast"] = t2
            self._labels.append(("Brighter text and panel borders", x + 80, wy + 6))
            y += row_h
            wy = label("Colorblind Mode")
            t3 = Toggle(x, wy, value=s.get("colorblind_mode", False),
                        on_change=lambda v: self._set("colorblind_mode", v))
            self._widgets["colorblind_mode"] = t3
            self._labels.append(("Use deuteranopia-safe element colors", x + 80, wy + 6))

        elif self.tab == "Data":
            wy = self.py + 40
            self._labels.append(("Save Data Management", x, wy))
            self._labels.append(("This permanently deletes all your progress:", x, wy + 36))
            self._labels.append(("heroes, levels, currency, and discovered maps.", x, wy + 60))
            self.reset_btn = Button((WIDTH // 2 - 120, wy + 120, 240, 56),
                                    "Reset Save", (120, 40, 60), (180, 60, 90), size=20)
            self.confirm_btn = Button((WIDTH // 2 - 220, wy + 220, 200, 56),
                                      "Confirm Reset", (160, 40, 50), (220, 60, 60), size=18)
            self.cancel_btn = Button((WIDTH // 2 + 20, wy + 220, 200, 56),
                                     "Cancel", (60, 80, 120), (90, 120, 180), size=20)

    def _apply_display(self):
        """Apply fullscreen/windowed mode to the running display."""
        try:
            s = self.game.player.settings
            if s.get("fullscreen", False):
                self.game.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)
            else:
                self.game.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
        except Exception:
            pass

    def update(self, dt, events):
        self.t += dt
        mp = pygame.mouse.get_pos()
        mdown = pygame.mouse.get_pressed()[0]
        self.back_btn.update(mp, mdown)
        for name, b in self.tab_btns:
            b.update(mp, mdown)
        for w in self._widgets.values():
            w.update(mp, mdown)
        if self.tab == "Data":
            self.reset_btn.update(mp, mdown)
            self.confirm_btn.update(mp, mdown)
            self.cancel_btn.update(mp, mdown)
        for e in events:
            if self.back_btn.clicked(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                self.game.back("title")
                return
            # keyboard tab switching (Left/Right arrows) for consistency with the
            # world scene's full keyboard control.
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                idx = self.TABS.index(self.tab) if self.tab in self.TABS else 0
                if e.key == pygame.K_LEFT:
                    self.tab = self.TABS[max(0, idx - 1)]
                else:
                    self.tab = self.TABS[min(len(self.TABS) - 1, idx + 1)]
                self.confirming = False
                self._build_tab()
                audio.play("menu_click", 0.3)
                return
            for name, b in self.tab_btns:
                if b.clicked(e):
                    self.tab = name
                    self.confirming = False
                    self._build_tab()
                    audio.play("menu_click", 0.3)
                    return
            for w in self._widgets.values():
                if w.handle(e):
                    self._refresh_labels()
                    return
            if self.tab == "Data":
                if not self.confirming and self.reset_btn.clicked(e):
                    self.confirming = True
                    return
                if self.confirming:
                    if self.confirm_btn.clicked(e):
                        self.game.reset_save()
                        return
                    if self.cancel_btn.clicked(e):
                        self.confirming = False
                        return

    def _refresh_labels(self):
        """Re-render the dynamic value labels (percentages) after a change."""
        s = self.game.player.settings
        # find labels by matching the known prefix text and rewriting them
        # (simplest: rebuild the tab so labels reflect current values)
        self._build_tab()

    def draw(self, surf):
        surf.fill(BG_DARK)
        # high_contrast: brighten the title + label text so the Accessibility
        # toggle actually does something (brighter text + panel borders)
        hc = self.game.player.settings.get("high_contrast", False)
        title_col = (255, 255, 255) if hc else WHITE
        label_col = (240, 240, 255) if hc else (200, 200, 220)
        text(surf, "Settings", 40, title_col, (WIDTH // 2, 80), center=True)
        # tabs
        for name, b in self.tab_btns:
            b.color = (90, 120, 180) if self.tab == name else (60, 70, 110)
            b.draw(surf)
        # panel — a brighter border when high_contrast is on
        draw_panel(surf, (self.px, self.py, self.pw, self.ph),
                   border=(255, 255, 255) if hc else PANEL_BORDER)
        # labels
        for item in self._labels:
            if len(item) == 3:
                txt, lx, ly = item
                text(surf, txt, 18, label_col, (lx, ly))
        # widgets
        for w in self._widgets.values():
            w.draw(surf)
        # data tab extras
        if self.tab == "Data":
            if self.confirming:
                text(surf, "Delete ALL progress?", 22, (255, 120, 120),
                     (WIDTH // 2, self.py + 180), center=True)
                self.confirm_btn.draw(surf)
                self.cancel_btn.draw(surf)
            else:
                self.reset_btn.draw(surf)
        self.back_btn.draw(surf)
        # a subtle footer hint
        text(surf, "Changes save automatically", 14, DIM, (WIDTH // 2, HEIGHT - 30), center=True)


# ---------------------------------------------------------------------------
# Stats scene
# ---------------------------------------------------------------------------
class StatsScene(Scene):
    """Show battle stats, achievements and daily quests."""
    def __init__(self, game):
        super().__init__(game)
        self.back_btn = Button((40, 40, 140, 48), "Back", (60, 60, 90), (90, 90, 130), size=20)
        self.tab = "stats"
        self.tab_stats = Button((WIDTH // 2 - 240, 100, 140, 44), "Stats", (60, 80, 120), (90, 120, 180), size=18)
        self.tab_ach = Button((WIDTH // 2 - 90, 100, 140, 44), "Awards", (60, 80, 120), (90, 120, 180), size=18)
        self.tab_quest = Button((WIDTH // 2 + 60, 100, 160, 44), "Daily Quests", (60, 80, 120), (90, 120, 180), size=16)
        # "Claim All" button for the Daily Quests tab (reduces the daily chore
        # from one click per quest to one click for the whole board).
        self.claim_all_btn = Button((WIDTH // 2 - 110, 158, 220, 34), "Claim All",
                                    (90, 160, 110), (120, 200, 130), size=16)
        self.scroll = 0
        self.quest_rects = []
        self.t = 0
        # reward toast (shown after claiming a quest or the whole board)
        self.toast = ""
        self.toast_t = 0

    def update(self, dt, events):
        self.t += dt
        if self.toast_t > 0:
            self.toast_t -= dt
        mp = pygame.mouse.get_pos()
        mdown = pygame.mouse.get_pressed()[0]
        self.back_btn.update(mp, mdown)
        self.tab_stats.update(mp, mdown)
        self.tab_ach.update(mp, mdown)
        self.tab_quest.update(mp, mdown)
        self.claim_all_btn.update(mp, mdown)
        self.game.player.reset_quests_if_needed()
        self.quest_rects = []
        for i, qid in enumerate(D.DAILY_QUESTS):
            r = pygame.Rect(WIDTH // 2 - 280, 200 + i * 80, 560, 70)
            self.quest_rects.append((qid, r))
        for e in events:
            if self.back_btn.clicked(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                self.game.back("title")
                return
            if self.tab_stats.clicked(e):
                self.tab = "stats"; self.scroll = 0
            if self.tab_ach.clicked(e):
                self.tab = "ach"; self.scroll = 0
            if self.tab_quest.clicked(e):
                self.tab = "quest"; self.scroll = 0
            # keyboard tab switching (Left/Right arrows) for consistency with the
            # world scene's full keyboard control.
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                order = ["stats", "ach", "quest"]
                idx = order.index(self.tab) if self.tab in order else 0
                if e.key == pygame.K_LEFT:
                    self.tab = order[max(0, idx - 1)]
                else:
                    self.tab = order[min(len(order) - 1, idx + 1)]
                self.scroll = 0
                audio.play("menu_click", 0.3)
                return
            if self.tab == "quest" and self.claim_all_btn.clicked(e):
                total = 0
                for qid in D.DAILY_QUESTS:
                    if self.game.player.claim_quest(qid):
                        total += D.DAILY_QUESTS[qid]["reward_gems"]
                if total > 0:
                    self.toast = f"Claimed all: +{total} gems!"
                    self.toast_t = 2.0
                    audio.play("menu_click", 0.5)
                return
            if self.tab == "quest" and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for qid, r in self.quest_rects:
                    if r.collidepoint(e.pos):
                        if self.game.player.claim_quest(qid):
                            q = D.DAILY_QUESTS[qid]
                            self.toast = f"+{q['reward_gems']} gems!"
                            self.toast_t = 1.6
                            audio.play("menu_click", 0.4)
                        return
            if e.type == pygame.MOUSEWHEEL:
                # clamp scroll to the active tab's content height so the list
                # can't scroll past its end (which left a blank screen).
                if self.tab == "stats":
                    content_h = 10 * 60
                elif self.tab == "ach":
                    content_h = len(D.ACHIEVEMENTS) * 72
                else:
                    content_h = len(D.DAILY_QUESTS) * 80
                max_scroll = max(0, content_h - (HEIGHT - 180 - 40))
                self.scroll = max(0, min(self.scroll - e.y * 40, max_scroll))

    def draw(self, surf):
        surf.fill(BG_DARK)
        text(surf, "Records", 40, WHITE, (WIDTH // 2, 40), center=True)
        # tab indicator
        for btn, key in [(self.tab_stats, "stats"), (self.tab_ach, "ach"), (self.tab_quest, "quest")]:
            btn.color = (90, 120, 180) if self.tab == key else (60, 80, 120)
            btn.draw(surf)
        p = self.game.player
        if self.tab == "stats":
            rows = [
                ("Enemies Defeated", p.stats.get("enemies_defeated", 0)),
                ("Bosses Defeated", p.stats.get("bosses_defeated", 0)),
                ("Maps Discovered", len(p.ow_discovered)),
                ("Total Pulls", p.stats.get("total_pulls", 0)),
                ("Gold Earned", p.stats.get("gold_earned", 0)),
                ("Gems Earned", p.stats.get("gems_earned", 0)),
                ("Soul Shards", p.shards),
                ("Heroes Owned", len(p.owned)),
                ("Daily Clears", p.stats.get("daily_clears", 0)),
                ("Login Streak", p.login_streak),
            ]
            y = 180 - self.scroll
            for label, val in rows:
                draw_panel(surf, (WIDTH // 2 - 280, y, 560, 48))
                text(surf, label, 22, WHITE, (WIDTH // 2 - 260, y + 12))
                text(surf, str(val), 22, GOLD, (WIDTH // 2 + 240, y + 12))
                y += 60
        elif self.tab == "ach":
            y = 180 - self.scroll
            for aid, ach in D.ACHIEVEMENTS.items():
                unlocked = aid in p.achievements
                draw_panel(surf, (WIDTH // 2 - 300, y, 600, 64))
                text(surf, ach["name"], 22, GOLD if unlocked else WHITE, (WIDTH // 2 - 280, y + 8))
                text(surf, ach["desc"], 16, DIM, (WIDTH // 2 - 280, y + 34))
                text(surf, f"+{ach['reward_gems']} gems", 18,
                     (120, 200, 255) if unlocked else (120, 100, 100),
                     (WIDTH // 2 + 260, y + 20))
                if unlocked:
                    text(surf, "DONE", 16, (140, 220, 160), (WIDTH // 2 + 260, y + 40), center=True)
                y += 72
        else:  # quest
            self.claim_all_btn.draw(surf)
            for qid, r in self.quest_rects:
                q = D.DAILY_QUESTS[qid]
                st = p.quests.get(qid, dict(progress=0, claimed=False, goal=q["goal"]))
                prog = st.get("progress", 0)
                goal = st.get("goal", q["goal"])
                claimed = st.get("claimed", False)
                done = prog >= goal
                draw_panel(surf, r)
                text(surf, q["name"], 20, WHITE, (r.x + 16, r.y + 8))
                text(surf, q["desc"], 14, DIM, (r.x + 16, r.y + 32))
                draw_bar(surf, (r.x + 16, r.y + 50, 360, 12), prog / max(1, goal), (120, 200, 255))
                text(surf, f"{prog}/{goal}", 16, WHITE, (r.x + 390, r.y + 44))
                mp = pygame.mouse.get_pos()
                claim_rect = pygame.Rect(r.right - 120, r.y + 20, 100, 34)
                if done and not claimed:
                    col = (90, 160, 110) if claim_rect.collidepoint(mp) else (60, 120, 80)
                    pygame.draw.rect(surf, col, claim_rect, border_radius=8)
                    text(surf, "Claim", 16, WHITE, claim_rect.center, center=True)
                elif claimed:
                    text(surf, "Claimed", 16, (140, 220, 160), claim_rect.center, center=True)
        # reward toast (claim feedback)
        if self.toast_t > 0:
            draw_panel(surf, (WIDTH // 2 - 150, HEIGHT - 80, 300, 48))
            text(surf, self.toast, 22, (120, 200, 255), (WIDTH // 2, HEIGHT - 56), center=True)
        self.back_btn.draw(surf)


# ---------------------------------------------------------------------------
# Codex scene
# ---------------------------------------------------------------------------
class CodexScene(Scene):
    """Show all heroes with owned/total counts."""
    def __init__(self, game):
        super().__init__(game)
        self.back_btn = Button((40, 40, 140, 48), "Back", (60, 60, 90), (90, 90, 130), size=20)
        self.scroll = 0
        self.t = 0
        self.portrait_cache = {}

    def _portrait(self, hid):
        if hid not in self.portrait_cache:
            # cache the already-scaled portrait at the display size so draw()
            # doesn't smoothscale 25 portraits every frame.
            pr = pygame.transform.smoothscale(load_portrait(hid, 160), (130, 130))
            self.portrait_cache[hid] = pr
        return self.portrait_cache[hid]

    def update(self, dt, events):
        self.t += dt
        mp = pygame.mouse.get_pos()
        mdown = pygame.mouse.get_pressed()[0]
        self.back_btn.update(mp, mdown)
        for e in events:
            if self.back_btn.clicked(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                self.game.back("title")
                return
            if e.type == pygame.MOUSEWHEEL:
                # clamp scroll to the codex content height so it can't scroll
                # past the last row (which left a blank screen with no way back).
                rows = (len(D.HEROES_DB) + 6) // 7
                content_h = rows * (200 + 16)
                max_scroll = max(0, content_h - (HEIGHT - 130 - 40))
                self.scroll = max(0, min(self.scroll - e.y * 40, max_scroll))

    def draw(self, surf):
        surf.fill(BG_DARK)
        p = self.game.player
        text(surf, "Codex", 40, WHITE, (WIDTH // 2, 40), center=True)
        text(surf, f"Collected {len(p.owned)}/{len(D.HEROES_DB)} heroes", 20, GOLD,
             (WIDTH // 2, 80), center=True)
        all_heroes = D.HEROES_DB
        cols = 7
        cw, ch = 150, 200
        gap = 16
        start_x = 60
        start_y = 130
        # cache the scaled frame per rarity (3 rarities) so we don't smoothscale
        # 25 frames every frame.
        if not hasattr(self, "_frame_cache"):
            self._frame_cache = {}
        # find the hovered hero card so we can draw a bio tooltip on top of it.
        mp = pygame.mouse.get_pos()
        hovered_id = None
        hovered_rect = None
        for i, hd in enumerate(all_heroes):
            col = i % cols
            row = i // cols
            x = start_x + col * (cw + gap)
            y = start_y + row * (ch + gap) - self.scroll
            r = pygame.Rect(x, y, cw, ch)
            if r.collidepoint(mp):
                hovered_id = hd["id"]
                hovered_rect = r
            owned = hd["id"] in p.owned
            fr = self._frame_cache.get(hd["rarity"])
            if fr is None:
                fr = pygame.transform.smoothscale(load_ui(f"frame_{hd['rarity']}"), (cw, ch))
                self._frame_cache[hd["rarity"]] = fr
            surf.blit(fr, r.topleft)
            if owned:
                pr = self._portrait(hd["id"])
                surf.blit(pr, (r.x + 10, r.y + 10))
                text(surf, hd["name"], 14, WHITE, (r.centerx, r.y + cw + 4), center=True)
                nstars = 3 if hd["rarity"] == "SSR" else (2 if hd["rarity"] == "SR" else 1)
                draw_stars(surf, r.centerx - 24, r.y + cw + 24, nstars, size=8)
            else:
                # silhouette: dark overlay (reused scratch surface)
                dim = _scratch(cw - 20, cw - 20)
                dim.fill((20, 20, 30, 200))
                surf.blit(dim, (r.x + 10, r.y + 10))
                text(surf, "???", 28, (120, 120, 140), (r.centerx, r.y + cw // 2), center=True)
                text(surf, hd["name"], 14, (120, 120, 140), (r.centerx, r.y + cw + 4), center=True)
        # bio tooltip on hover: a small panel under the hovered card with the bio.
        # Only for owned heroes (silhouettes have no identity to reveal yet).
        if hovered_id is not None and hovered_rect is not None and hovered_id in p.owned:
            lore = D.HERO_LORE.get(hovered_id)
            if lore:
                bio = lore["bio"]
                tt_w, tt_h = 360, 60
                tx = hovered_rect.centerx - tt_w // 2
                ty = hovered_rect.bottom + 6
                # keep the tooltip on-screen
                tx = max(8, min(tx, WIDTH - tt_w - 8))
                ty = min(ty, HEIGHT - tt_h - 8)
                draw_panel(surf, (tx, ty, tt_w, tt_h))
                # word-wrap the bio inside the tooltip (max width ~ tt_w - 24)
                font = get_font(13)
                words = bio.split(" ")
                lines = []
                cur = ""
                for w in words:
                    trial = cur + " " + w if cur else w
                    if font.size(trial)[0] <= tt_w - 24:
                        cur = trial
                    else:
                        if cur:
                            lines.append(cur)
                        cur = w
                if cur:
                    lines.append(cur)
                ly = ty + 8
                for ln in lines[:3]:
                    text(surf, ln, 13, WHITE, (tx + 12, ly))
                    ly += 16
        self.back_btn.draw(surf)


# ---------------------------------------------------------------------------
# Game controller
# ---------------------------------------------------------------------------
class Game:
    _active = None  # class-level ref to the most-recently-constructed Game so
                    # module-level helpers (element_color) can read player.settings
    def __init__(self):
        pygame.init()
        audio.init()
        flags = pygame.SCALED
        try:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags, vsync=1)
        except pygame.error:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        init_fonts()
        self.player = Player.load()
        Game._active = self  # register this instance for element_color() lookups
        # apply persisted settings to the live audio + display on boot
        audio.set_enabled(self.player.settings.get("sound", True))
        audio.set_master_volume(self.player.settings.get("sfx_volume", 0.7))
        # apply the persisted display mode (fullscreen) on boot
        if self.player.settings.get("fullscreen", False):
            try:
                self.screen = pygame.display.set_mode((WIDTH, HEIGHT),
                                                      pygame.SCALED | pygame.FULLSCREEN)
            except Exception:
                pass
        # daily login bonus (7-day streak)
        granted, amt, streak = self.player.check_daily()
        if granted:
            self.player.save()
            self._login_bonus = (amt, streak)
        else:
            self._login_bonus = None
        self.scene = None
        self.scenes = {}
        self.running = True
        # navigation back-stack of (name, kw) tuples; title is a root
        self.scene_stack = []
        self._current = None
        # scene transition fade
        self._fade = 0.0          # 1.0 = fully black; fades out on scene change
        self._fade_target = 0.0
        self._pending_scene = None
        self.goto("title")
        self._fade = 1.0          # fade in on first launch

    def _make_scene(self, name, **kw):
        if name == "title":
            return TitleScene(self)
        elif name == "roster":
            return RosterScene(self)
        elif name == "gacha":
            return GachaScene(self)
        elif name == "shop":
            return ShopScene(self)
        elif name == "inventory":
            return InventoryScene(self)
        elif name == "hero_detail":
            return HeroDetailScene(self, kw["hero_id"])
        elif name == "settings":
            return SettingsScene(self)
        elif name == "stats":
            return StatsScene(self)
        elif name == "codex":
            return CodexScene(self)
        elif name == "world":
            return _get_world_scene_cls()(self)
        return TitleScene(self)

    def goto(self, name, **kw):
        # title is a root: clear the back-stack when going home
        if name == "title":
            self.scene_stack = []
        elif self.scene is not None and self._current is not None:
            self.scene_stack.append(self._current)
        self._current = (name, kw)
        self.scene = self._make_scene(name, **kw)
        # trigger a fade-out -> fade-in transition on scene change
        self._fade_target = 1.0
        # defensive: initialize the scene's cached draw-state so draw() is safe
        # even if it is called before the first update() (happens because goto
        # swaps self.scene mid-frame, then the same frame calls draw()).
        self._safe_init_scene()

    def back(self, fallback="title"):
        if self.scene_stack:
            name, kw = self.scene_stack.pop()
            self._current = (name, kw)
            self.scene = self._make_scene(name, **kw)
            self._fade_target = 1.0
            self._safe_init_scene()
        else:
            self.goto(fallback)

    def _safe_init_scene(self):
        try:
            self.scene.update(0.0, [])
        except Exception:
            # a scene that needs real input to init is still protected by the
            # per-scene __init__ defaults; never let init break the frame.
            pass

    def reset_save(self):
        self.player = Player()
        self.player.save()
        self.scene_stack = []
        self._current = None
        self.goto("title")

    def run(self):
        while self.running:
            # respect the user's FPS cap setting (default 60)
            cap = self.player.settings.get("fps_cap", FPS)
            dt = self.clock.tick(int(cap)) / 1000.0
            dt = min(dt, 1 / 30)
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    self.running = False
            self.scene.update(dt, events)
            self.scene.draw(self.screen)
            # debug FPS overlay
            if self.player.settings.get("show_fps", False):
                fps = self.clock.get_fps()
                text(self.screen, f"{fps:4.0f} fps", 20, (120, 240, 160), (WIDTH - 90, HEIGHT - 30))
            # scene transition fade overlay
            if self._fade_target > 0 or self._fade > 0:
                # ease the fade toward its target
                self._fade += (self._fade_target - self._fade) * min(1, dt * 8)
                # once fully black, drop back to transparent (reveal new scene)
                if self._fade_target == 1.0 and self._fade > 0.9:
                    self._fade_target = 0.0
                if self._fade > 0.01:
                    fl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    fl.fill((0, 0, 0, int(255 * min(1, self._fade))))
                    self.screen.blit(fl, (0, 0))
            pygame.display.flip()
        self.player.save()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
