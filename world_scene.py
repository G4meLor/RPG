"""
Aetheria Open World - World Scene
The real-time open-world scene: input, update loop, edge transitions, combat,
pickups, drawing, HUD, teleport overlay, and the in-world pause hub.
"""
import math
import random
import time

import pygame

import data as D
from entities import (Hero, load_char_sprite, load_enemy_sprite, load_skill_icon,
                      load_drop, load_terrain, load_landmark, load_village)
import audio
import generate_assets as GA
import world_data as WD
from world_entities import (Camera, Particles, Particle, Projectile, FloatText,
                            WorldCharacter, WorldEnemy, WEAPON_STYLE, scratch,
                            SummonAlly, Trap)


def _seg_hit(x1, y1, x2, y2, px, py, r):
    """Point-to-segment distance < r — the beam skill's line hit-scan test.
    Returns True if the point (px, py) is within r of the segment (x1,y1)-(x2,y2)."""
    dx, dy = x2 - x1, y2 - y1
    seg2 = dx * dx + dy * dy
    if seg2 <= 0:
        return math.hypot(px - x1, py - y1) < r
    t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / seg2))
    cx, cy = x1 + t * dx, y1 + t * dy
    return math.hypot(px - cx, py - cy) < r


def _wrap(s, width):
    """Word-wrap a string into a list of lines, each <= `width` chars. Splits
    on spaces; a word longer than `width` is hard-split. Used by the skill
    tooltip (Task B1) so the description/how_to_use don't overflow the panel."""
    if not s:
        return []
    words = s.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) <= width:
            cur = (cur + " " + w) if cur else w
        else:
            if cur:
                lines.append(cur)
            # hard-split an over-long word
            while len(w) > width:
                lines.append(w[:width]); w = w[width:]
            cur = w
    if cur:
        lines.append(cur)
    return lines


# Hold-to-aim threshold (Task B2): a skill key held longer than this enters aim
# mode (the preview draws + the release fires at the mouse). A quick tap (< this)
# fires instantly at the facing (legacy behavior). 0.12s is below a typical human
# tap duration (~0.15s) so a deliberate tap still fires instantly, while a
# deliberate hold enters aim mode.
AIM_HOLD_THRESHOLD = 0.12
# Max range (world px) a ground-targeted AoE can be placed from the hero. The
# preview + the cast clamp the target to this radius so a player can't AoE a
# target off-screen across the map.
AIM_MAX_RANGE = 300.0
# Default AoE preview radius (world px) — matches the AoE skill's aoe_r (200,
# 260 empowered) so the preview circle reads as the actual burst area.
AIM_AOE_RADIUS = 200

# ---------------------------------------------------------------------------
# Signature passive handlers (C6) — dict-lookup dispatch, NOT if/elif chains.
# These run in the world scene (where they need scene state: the enemy list,
# particles, audio, the camera). Each hook point has its own dict mapping
# kind -> handler, so only the relevant handler runs at that point. The
# signature is ADDITIONAL to the shared base passive — these run in addition to
# the lifesteal/thorns/shield_when_low/etc. handlers in _do_attack /
# _on_enemy_death, not instead of them.
# ---------------------------------------------------------------------------

def _sig_cleave(scene, wc, primary_x, primary_y, atk):
    """cleave: basic attacks splash to enemies within 60px of the primary
    target. val is the fraction of ATK dealt as splash (0.5 = 50%). Skips the
    primary target (already hit by the main arc) and dead enemies. The splash
    is a separate damage roll (not the main arc) so it doesn't double-dip with
    the combo multiplier that's already applied to the main hit."""
    sig = wc.hero.signature
    if not sig or sig.get("kind") != "cleave":
        return
    cleave_dmg = int(atk * sig.get("val", 0.5))
    col = D.ELEMENT_COLORS.get(wc.element, ((200, 200, 200),))[0]
    for en in scene.enemies:
        if not en.alive:
            continue
        # skip the primary target (already hit by the main arc)
        if math.hypot(en.x - primary_x, en.y - primary_y) < 5:
            continue
        if math.hypot(en.x - primary_x, en.y - primary_y) < 60 + en.r:
            dealt = en.take_damage(cleave_dmg, wc.x, wc.y, False,
                                   on_attack=scene._on_enemy_event)
            if dealt > 0:
                scene._on_enemy_hit(en, wc, dealt, False)
    # a subtle slash streak so the splash reads visually
    scene.particles.spark(primary_x, primary_y, col, n=6, speed=160, size=4, life=0.2)

def _sig_stacking_atk(scene, wc):
    """stacking_atk: +val ATK per kill (stacking). The stack is read in
    WorldCharacter.effective_atk (via _SIG_ATK_MOD) and decays out of combat
    (via _SIG_UPDATE in world_entities). Reset the decay timer here so a fresh
    kill restarts the out-of-combat countdown."""
    sig = wc.hero.signature
    if not sig or sig.get("kind") != "stacking_atk":
        return
    wc._kill_stack += 1
    wc._kill_stack_t = 0.0

# Dispatch dict for the _do_attack hook point (kind -> handler).
_SIG_ATTACK = {"cleave": _sig_cleave}
# Dispatch dict for the _on_enemy_death hook point (kind -> handler).
_SIG_ON_KILL = {"stacking_atk": _sig_stacking_atk}


# Reuse the main.py Button + draw_bar by importing them. main.py is the entry
# point so it is already loaded when the world scene is constructed.
from main import Button, draw_bar


# ---------------------------------------------------------------------------
# Map renderer - bakes a map's ground + decorations to one Surface
# ---------------------------------------------------------------------------
class MapRenderer:
    def __init__(self):
        self.cache = {}       # "c,r" -> full map Surface
        self._ground = {}     # biome -> base ground Surface (2000x1200), once

    def get(self, c, r):
        key = f"{c},{r}"
        s = self.cache.get(key)
        if s is None:
            s = self._render(c, r)
            self.cache[key] = s
        return s

    def get_locked(self, c, r, lock):
        """Thread-safe get used by the main loop during the background pre-warm.
        Tries to acquire the lock non-blocking: if free, render+cache the cell
        under the lock (the authoritative cached copy). If the worker holds it,
        we render a throwaway surface for this frame so the transition isn't
        blocked — the next frame picks up the cached one the worker produces."""
        key = f"{c},{r}"
        s = self.cache.get(key)
        if s is not None:
            return s
        if lock is None or lock.acquire(blocking=False):
            try:
                s = self.cache.get(key)
                if s is None:
                    s = self._render(c, r)
                    self.cache[key] = s
            finally:
                if lock is not None:
                    lock.release()
            return s
        # lock held by the worker: render a throwaway copy so the transition
        # frame isn't blocked (the next frame will pick up the cached one)
        return self._render(c, r)

    def _ground_base(self, biome, pal):
        """A per-biome ground surface (checker + speckles + vignette), rendered
        once and .convert()-ed once. Per-cell maps copy this cheap base and add
        their own winding path + portals + decorations — so the first visit to
        any map is a fast memcpy + a few cheap draws instead of 1500 rects.

        The pre-warm worker and the main thread can both reach here for the same
        biome; use setdefault so the first one to finish wins and the second
        build is discarded (no torn writes, no wasted cache slot)."""
        if biome in self._ground:
            return self._ground[biome]
        surf = pygame.Surface((WD.MAP_W, WD.MAP_H)).convert()
        g1 = pal["ground"]
        g2 = pal["ground2"]
        tile = WD.TILE
        # checker via a 2x2-tile pattern blitted across (25x15 = 375 blits of an
        # 80x80 surface, far cheaper than 1500 draw.rect calls)
        pat = pygame.Surface((tile * 2, tile * 2)).convert()
        pat.fill(g1)
        pygame.draw.rect(pat, g2, (tile, 0, tile, tile))
        pygame.draw.rect(pat, g2, (0, tile, tile, tile))
        for ty in range(0, WD.MAP_H, tile * 2):
            for tx in range(0, WD.MAP_W, tile * 2):
                surf.blit(pat, (tx, ty))
        # subtle shared speckles (deterministic by biome, not per-cell) so the
        # floor isn't a flat checkerboard. Salt-free str hash (sum of ords) so
        # the speckle layout is stable across reloads (Python's hash(str) is
        # PYTHONHASHSEED-salted per process — mirrors generate_assets.py).
        rng = random.Random(sum(ord(ch) for ch in biome) & 0xffff)
        speck = (max(0, g1[0] - 18), max(0, g1[1] - 18), max(0, g1[2] - 18))
        for _ in range(160):
            sx = rng.randint(0, WD.MAP_W - 4)
            sy = rng.randint(0, WD.MAP_H - 4)
            pygame.draw.ellipse(surf, speck, (sx, sy, 5, 3))
        light = (min(255, g1[0] + 22), min(255, g1[1] + 22), min(255, g1[2] + 22))
        for _ in range(90):
            sx = rng.randint(0, WD.MAP_W - 3)
            sy = rng.randint(0, WD.MAP_H - 3)
            pygame.draw.circle(surf, light, (sx, sy), 2)
        # subtle vignette darkening at borders (the wall area)
        dark = (max(0, g1[0] - 30), max(0, g1[1] - 30), max(0, g1[2] - 30))
        for i in range(WD.TILE):
            a = int(120 * (1 - i / WD.TILE))
            band = pygame.Surface((WD.MAP_W, 1), pygame.SRCALPHA)
            band.fill((*dark, a))
            surf.blit(band, (0, i))
            surf.blit(pygame.transform.flip(band, False, True), (0, WD.MAP_H - 1 - i))
        # setdefault: if another thread already cached this biome while we were
        # building, keep their (already-convert_alpha'd) surface and drop ours.
        existing = self._ground.setdefault(biome, surf)
        return existing

    def _render(self, c, r):
        m = WD.gen_map(c, r)
        pal = m["pal"]
        biome = m["biome"]
        # start from the shared per-biome ground base (a fast copy — same pixel
        # format, no .convert() needed) then layer the per-cell bits on top
        base = self._ground_base(biome, pal)
        surf = base.copy()
        g1 = pal["ground"]
        tile = WD.TILE
        # a winding path through the map so the world reads like a place you
        # walk through, not an empty field. The path shape varies per biome so
        # a plains road and a void road aren't the same winding ribbon: plains
        # = a wider brighter dirt road, forest = a narrow winding deer trail,
        # castle = a straight paved road, void = a thin glowing accent line.
        rng = random.Random(WD.cell_seed(c, r) + 99)
        accent = pal["accent"]
        if biome == "void":
            # a thin glowing accent rift line down the map
            px = WD.MAP_W // 2
            for step in range(WD.MAP_TH + 2):
                py = step * tile
                pygame.draw.line(surf, accent, (px, py), (px, py + tile + 2), 3)
                if rng.random() < 0.25:
                    px += rng.choice([-tile, tile])
                    px = max(tile, min(WD.MAP_W - tile, px))
        elif biome == "castle":
            # a straight paved road: alternating g1/g2 tiles down the middle
            px = WD.MAP_W // 2
            for step in range(WD.MAP_TH + 2):
                py = step * tile
                col = g1 if step % 2 == 0 else pal["ground2"]
                pygame.draw.rect(surf, col, (px - tile, py, tile * 2, tile + 2),
                                border_radius=4)
        elif biome == "forest":
            # a narrow winding deer trail, darker than the ground
            dark = (max(0, g1[0] - 12), max(0, g1[1] - 12), max(0, g1[2] - 12))
            px = rng.randint(4, WD.MAP_TW - 5) * tile
            for step in range(WD.MAP_TH + 6):
                py = step * tile - tile
                pw = tile
                pygame.draw.rect(surf, dark, (px - pw // 2, py, pw, tile + 2),
                                 border_radius=4)
                if rng.random() < 0.4:
                    px += rng.choice([-tile, tile])
                    px = max(tile, min(WD.MAP_W - tile, px))
        else:
            # plains / cave: the default wider winding road
            path_col = (min(255, g1[0] + 30), min(255, g1[1] + 30),
                        min(255, g1[2] + 26))
            px = rng.randint(4, WD.MAP_TW - 5) * tile
            for step in range(WD.MAP_TH + 6):
                py = step * tile - tile
                pw = tile * 2
                pygame.draw.rect(surf, path_col, (px - pw // 2, py, pw, tile + 2),
                                 border_radius=6)
                if rng.random() < 0.35:
                    px += rng.choice([-tile, tile])
                    px = max(tile, min(WD.MAP_W - tile, px))
        # left/right edge portals so the world reads as connected (a glowing
        # arch where you walk through to the next map)
        self._draw_edge_portal(surf, "left", pal)
        self._draw_edge_portal(surf, "right", pal)
        if r > 0:
            self._draw_edge_portal(surf, "top", pal)
        if r < WD.GRID_H - 1:
            self._draw_edge_portal(surf, "bottom", pal)
        # decorations
        for (dx, dy, kind, size) in m["deco"]:
            self._draw_deco(surf, dx, dy, kind, size, pal)
        return surf

    def _draw_edge_portal(self, surf, edge, pal):
        """A glowing arch at a traversable edge so the world reads connected.
        A biome-specific silhouette element is layered on the arch so a cave
        portal and a castle portal aren't the same glowing arch in a different
        hue (castle = iron portcullis bars, void = a spiral)."""
        accent = pal["accent"]
        obs = pal["obstacle"]
        glow = pygame.Surface((120, 120), pygame.SRCALPHA)
        for rr in range(54, 0, -4):
            a = int(40 * (1 - rr / 54))
            pygame.draw.circle(glow, (*accent, a), (60, 60), rr)
        if edge == "left":
            surf.blit(glow, (0, WD.MAP_H // 2 - 60))
            pygame.draw.arc(surf, accent, (6, WD.MAP_H // 2 - 50, 60, 100), -1.2, 1.2, 4)
        elif edge == "right":
            surf.blit(glow, (WD.MAP_W - 120, WD.MAP_H // 2 - 60))
            pygame.draw.arc(surf, accent, (WD.MAP_W - 66, WD.MAP_H // 2 - 50, 60, 100), 1.9, 4.4, 4)
        elif edge == "top":
            surf.blit(glow, (WD.MAP_W // 2 - 60, 0))
            pygame.draw.arc(surf, accent, (WD.MAP_W // 2 - 50, 6, 100, 60), 0.2, 2.4, 4)
        elif edge == "bottom":
            surf.blit(glow, (WD.MAP_W // 2 - 60, WD.MAP_H - 120))
            pygame.draw.arc(surf, accent, (WD.MAP_W // 2 - 50, WD.MAP_H - 66, 100, 60), 3.5, 6.0, 4)
        # biome-specific portal motif on top of the arch
        biome = pal.get("name", "")
        if "Citadel" in biome and edge in ("left", "right"):
            # castle: iron portcullis bars (vertical lines in obstacle color)
            bx0 = 6 if edge == "left" else WD.MAP_W - 66
            for k in range(4):
                pygame.draw.line(surf, obs,
                                 (bx0 + 8 + k * 12, WD.MAP_H // 2 - 40),
                                 (bx0 + 8 + k * 12, WD.MAP_H // 2 + 40), 3)
        elif "Void" in biome and edge in ("left", "right"):
            # void: a small spiral around the arch center
            cx0 = 30 if edge == "left" else WD.MAP_W - 30
            cy0 = WD.MAP_H // 2
            for k in range(5):
                ang = k * 0.9
                rr = 6 + k * 5
                pygame.draw.circle(surf, accent,
                                   (int(cx0 + math.cos(ang) * rr),
                                    int(cy0 + math.sin(ang) * rr)), 2)

    def _draw_deco(self, surf, x, y, kind, size, pal):
        if kind == "tree":
            # trunk — darkened from the biome's obstacle color so a cave tree
            # reads as petrified/blue, not a plains brown trunk
            obs = pal["obstacle"]
            trunk = (max(0, obs[0] - 10), max(0, obs[1] - 8), max(0, obs[2] - 6))
            trunk_d = (max(0, obs[0] - 18), max(0, obs[1] - 14), max(0, obs[2] - 12))
            pygame.draw.rect(surf, trunk, (x - 5, y - 4, 10, 18))
            pygame.draw.rect(surf, trunk_d, (x - 5, y - 4, 5, 18))
            # canopy with layered shading
            obs_dark = (max(0, obs[0] - 24), max(0, obs[1] - 24), max(0, obs[2] - 24))
            for rr in range(size, 6, -4):
                pygame.draw.circle(surf, obs, (x, y - 8), rr)
            pygame.draw.circle(surf, obs_dark, (x + 6, y - 4), max(3, size // 2))
            pygame.draw.circle(surf, pal["accent"], (x - 4, y - 12), max(3, size // 3))
        elif kind == "rock":
            obs = pal["obstacle"]
            obs_dark = (max(0, obs[0] - 24), max(0, obs[1] - 24), max(0, obs[2] - 24))
            pygame.draw.circle(surf, obs, (x, y), size // 2)
            pygame.draw.circle(surf, obs_dark, (x + 3, y + 3), size // 3)
            pygame.draw.circle(surf, obs, (x, y), size // 2, 2)
            pygame.draw.circle(surf, pal["accent"], (x - 4, y - 4), max(2, size // 5))
        elif kind == "pillar":
            obs = pal["obstacle"]
            obs_dark = (max(0, obs[0] - 25), max(0, obs[1] - 25), max(0, obs[2] - 25))
            pygame.draw.rect(surf, obs, (x - size // 2, y - size, size, size * 2))
            pygame.draw.rect(surf, obs_dark, (x - size // 2, y - size, size, size * 2), 2)
            # capital + base
            pygame.draw.rect(surf, pal["accent"], (x - size // 2 - 4, y - size - 4, size + 8, 6))
            pygame.draw.rect(surf, pal["accent"], (x - size // 2 - 4, y + size - 2, size + 8, 6))
        elif kind == "bush":
            obs = pal["obstacle"]
            pygame.draw.circle(surf, obs, (x, y), size // 2)
            pygame.draw.circle(surf, obs, (x - size // 3, y - 2), size // 3)
            pygame.draw.circle(surf, obs, (x + size // 3, y - 2), size // 3)
            pygame.draw.circle(surf, pal["accent"], (x - 3, y - 3), max(2, size // 4))
        elif kind == "crystal":
            # cave signature: a faceted accent-colored crystal with a white core
            acc = pal["accent"]
            pts = [(x, y - size), (x + size // 2, y - size // 4),
                   (x + size // 3, y + size // 2), (x - size // 3, y + size // 2),
                   (x - size // 2, y - size // 4)]
            pygame.draw.polygon(surf, acc, pts)
            pygame.draw.polygon(surf, (255, 255, 255), pts, 1)
            pygame.draw.circle(surf, (255, 255, 255), (x, y - size // 4),
                               max(2, size // 4))
        elif kind == "banner":
            # castle signature: a tall accent-colored flag on a pole
            obs = pal["obstacle"]
            pygame.draw.rect(surf, obs, (x - 2, y - size, 4, size * 2))
            pygame.draw.rect(surf, pal["accent"], (x + 2, y - size, size, size // 2 + 2))
        elif kind == "torch":
            # castle signature: a pillar + a flickering accent flame
            obs = pal["obstacle"]
            pygame.draw.rect(surf, obs, (x - 3, y - size, 6, size * 2))
            pygame.draw.circle(surf, pal["accent"], (x, y - size - 2), max(3, size // 3))
            pygame.draw.circle(surf, (255, 220, 120), (x, y - size - 2),
                               max(2, size // 5))
        elif kind == "rift":
            # void signature: a jagged accent-colored diagonal crack
            acc = pal["accent"]
            pts = [(x - size, y - size), (x - size // 3, y - size // 4),
                   (x + size // 3, y + size // 4), (x + size, y + size)]
            pygame.draw.lines(surf, acc, False, pts, 3)
            pygame.draw.circle(surf, acc, (x, y), max(2, size // 4))


# ---------------------------------------------------------------------------
# Teleport overlay
# ---------------------------------------------------------------------------
class TeleportOverlay:
    def __init__(self, game):
        self.game = game
        self.sel = list(game.player.ow_current) if game.player.ow_current else [0, 0]
        self.t = 0

    def update(self, dt, events, on_teleport, on_close):
        self.t += dt
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_m or e.key == pygame.K_ESCAPE:
                    on_close()
                elif e.key in (pygame.K_LEFT, pygame.K_a):
                    self.sel[0] = max(0, self.sel[0] - 1)
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    self.sel[0] = min(WD.GRID_W - 1, self.sel[0] + 1)
                elif e.key in (pygame.K_UP, pygame.K_w):
                    self.sel[1] = max(0, self.sel[1] - 1)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.sel[1] = min(WD.GRID_H - 1, self.sel[1] + 1)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    cid = WD.cell_id(self.sel[0], self.sel[1])
                    if cid in self.game.player.ow_discovered:
                        on_teleport(self.sel[0], self.sel[1])
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                cell = self._cell_at(e.pos)
                if cell:
                    cx, cy = cell
                    cid = WD.cell_id(cx, cy)
                    if cid in self.game.player.ow_discovered:
                        on_teleport(cx, cy)

    def _cell_at(self, pos):
        mx, my = pos
        ox, oy = self._origin()
        cw, ch = self._cell_size()
        if ox <= mx <= ox + cw * WD.GRID_W and oy <= my <= oy + ch * WD.GRID_H:
            cx = (mx - ox) // cw
            cy = (my - oy) // ch
            return int(cx), int(cy)
        return None

    def _origin(self):
        cw, ch = self._cell_size()
        ox = (1280 - cw * WD.GRID_W) // 2
        oy = (720 - ch * WD.GRID_H) // 2
        return ox, oy

    def _cell_size(self):
        # fit 10x5 in the viewport with padding
        cw = (1280 - 160) // WD.GRID_W
        ch = (720 - 200) // WD.GRID_H
        return cw, ch

    def draw(self, surf, font_big, font_med, font_sm):
        # dim (reused)
        dim = _overlay_dim()
        surf.blit(dim, (0, 0))
        text(surf, "WORLD MAP  -  Teleport", 40, (255, 240, 180), (640, 60), center=True)
        text(surf, "Arrow keys to move, Enter to teleport, M/Esc to close", 18, (200, 200, 230),
             (640, 100), center=True)
        ox, oy = self._origin()
        cw, ch = self._cell_size()
        discovered = self.game.player.ow_discovered
        cur = self.game.player.ow_current or [0, 0]
        for r in range(WD.GRID_H):
            for c in range(WD.GRID_W):
                x = ox + c * cw
                y = oy + r * ch
                rect = pygame.Rect(x + 4, y + 4, cw - 8, ch - 8)
                cid = WD.cell_id(c, r)
                if cid in discovered:
                    biome = WD.BIOMES[WD.cell_biome(c, r)]
                    col = biome["ground"]
                    pygame.draw.rect(surf, col, rect, border_radius=8)
                    pygame.draw.rect(surf, biome["accent"], rect, 2, border_radius=8)
                    if WD.is_boss_cell(c, r):
                        text(surf, "BOSS", 14, (255, 80, 80), rect.center, center=True)
                    if [c, r] == cur:
                        pygame.draw.circle(surf, (255, 240, 120), rect.center, 10)
                        pygame.draw.circle(surf, (0, 0, 0), rect.center, 10, 2)
                    if [c, r] == self.sel:
                        pulse = 3 + int(math.sin(self.t * 8) * 2)
                        pygame.draw.rect(surf, (255, 255, 255), rect.inflate(pulse * 2, pulse * 2),
                                         3, border_radius=8)
                else:
                    pygame.draw.rect(surf, (30, 30, 40), rect, border_radius=8)
                    pygame.draw.rect(surf, (60, 60, 80), rect, 2, border_radius=8)
                    text(surf, "?", 24, (90, 90, 110), rect.center, center=True)
        # selected-cell info line so the player knows the destination's name +
        # biome before committing to a teleport (was navigating blind)
        sc, sr = self.sel
        name = WD.cell_name(sc, sr)
        cid = WD.cell_id(sc, sr)
        tag = " (discovered)" if cid in discovered else " (undiscovered)"
        text(surf, f"{name}{tag}", 22, (255, 240, 180), (640, 660), center=True)


# ---------------------------------------------------------------------------
# Pause hub (in-world menu)
# ---------------------------------------------------------------------------
class PauseHub:
    def __init__(self, game):
        self.game = game
        self.buttons = [
            Button((1280 // 2 - 120, 220, 240, 50), "Resume", (60, 100, 70), (90, 160, 110)),
            Button((1280 // 2 - 120, 280, 240, 50), "Party / Characters", (90, 80, 50), (160, 130, 70)),
            Button((1280 // 2 - 120, 340, 240, 50), "Evolve Heroes", (110, 70, 150), (170, 110, 210)),
            Button((1280 // 2 - 120, 400, 240, 50), "Summon", (90, 60, 130), (140, 90, 200)),
            Button((1280 // 2 - 120, 460, 240, 50), "Shop", (70, 90, 130), (100, 130, 190)),
            Button((1280 // 2 - 120, 520, 240, 50), "Inventory", (90, 70, 120), (140, 100, 190)),
            Button((1280 // 2 - 120, 580, 240, 50), "Save & Quit to Title", (120, 60, 60), (190, 90, 90), size=18),
        ]

    def update(self, dt, events, on_resume, on_gacha, on_shop, on_inventory, on_quit, on_evolve=None):
        mp = pygame.mouse.get_pos()
        mdown = pygame.mouse.get_pressed()[0]
        for b in self.buttons:
            b.update(mp, mdown)
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                on_resume()
            if self.buttons[0].clicked(e):
                on_resume()
            if self.buttons[1].clicked(e):
                # go to roster; the world scene stays on the stack so back() returns
                self.game.goto("roster")
            if self.buttons[2].clicked(e):
                if on_evolve: on_evolve()
            if self.buttons[3].clicked(e):
                on_gacha()
            if self.buttons[4].clicked(e):
                on_shop()
            if self.buttons[5].clicked(e):
                on_inventory()
            if self.buttons[6].clicked(e):
                on_quit()

    def draw(self, surf, font_big):
        surf.blit(_overlay_dim(), (0, 0))
        text(surf, "PAUSED", 56, (255, 240, 180), (640, 150), center=True)
        # shard count so the player sees their evolve currency
        text(surf, f"Soul Shards: {self.game.player.shards}", 18, (200, 160, 255),
             (640, 196), center=True)
        for b in self.buttons:
            b.draw(surf)


# ---------------------------------------------------------------------------
# Evolve overlay — soul-shard ascension + a branching evolution tree per hero
# ---------------------------------------------------------------------------
class EvolveOverlay:
    """Two-panel evolve screen.
    Left: a grid of owned heroes (select one). Right: that hero's evolution tree
    (root + two branches, each 3 nodes). Click a node to unlock it with shards.
    A separate 'Ascend Tier' button spends shards for the flat evolve tier
    (the big stat jump). Both share the shard pool."""
    def __init__(self, game):
        self.game = game
        p = game.player
        self.order = list(p.owned.keys())
        self.sel = 0
        self.t = 0.0
        self.flash = ""
        self.flash_t = 0.0
        # tree interaction: which node is hovered (for tooltips)
        self._node_rects = []   # list of (node_id, rect) rebuilt each draw
        self._ascend_rect = None

    # --- layout ---
    def _hero_rect(self, i):
        cols = 4
        cw, ch = 130, 160
        gx = 60
        gy = 150
        cx = i % cols
        cy = i // cols
        return pygame.Rect(gx + cx * (cw + 10), gy + cy * (ch + 12), cw, ch)

    def _tree_origin(self):
        # tree panel on the right
        return 620, 140

    def _node_center(self, node_id):
        col, row = D.EVO_NODE_POS.get(node_id, (1, 0))
        ox, oy = self._tree_origin()
        # 3 columns spaced 180px, 3 rows spaced 150px
        cx = ox + 90 + col * 180
        cy = oy + 70 + row * 150
        return cx, cy

    def update(self, dt, events, on_close):
        self.t += dt
        self.flash_t = max(0, self.flash_t - dt)
        for e in events:
            if e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_e, pygame.K_g):
                    on_close()
                elif e.key in (pygame.K_LEFT, pygame.K_a):
                    self.sel = max(0, self.sel - 1)
                elif e.key in (pygame.K_RIGHT, pygame.K_d):
                    self.sel = min(max(0, len(self.order) - 1), self.sel + 1)
                elif e.key in (pygame.K_UP, pygame.K_w):
                    self.sel = max(0, self.sel - 4)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.sel = min(max(0, len(self.order) - 1), self.sel + 4)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._try_ascend()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # hero select
                for i in range(len(self.order)):
                    if self._hero_rect(i).collidepoint(e.pos):
                        self.sel = i
                        audio.play("menu_click", 0.2)
                        return
                # tree node click
                for nid, r in self._node_rects:
                    if r.collidepoint(e.pos):
                        self._try_unlock_node(nid)
                        return
                # ascend button
                if self._ascend_rect and self._ascend_rect.collidepoint(e.pos):
                    self._try_ascend()
                    return

    def _selected_hid(self):
        if not self.order:
            return None
        return self.order[self.sel]

    def _try_ascend(self):
        hid = self._selected_hid()
        if not hid:
            return
        p = self.game.player
        if p.can_evolve(hid):
            p.evolve_hero(hid)
            h = p.get_hero_instance(hid)
            self.flash = f"{h.name} ascended to {h.evolve_title()}!"
            self.flash_t = 2.5
            audio.play("ultimate", 0.6)
        else:
            cost = p.evolve_cost(hid)
            if cost is None:
                self.flash = "Already at max tier."
            else:
                self.flash = f"Need {cost} shards (have {p.shards})."
            self.flash_t = 2.0
            audio.play("hit", 0.2)
        p.save()

    def _try_unlock_node(self, node_id):
        hid = self._selected_hid()
        if not hid:
            return
        p = self.game.player
        if node_id in p.owned[hid].get("evo_nodes", []):
            self.flash = "Already unlocked."
            self.flash_t = 1.5
            return
        if p.can_unlock_evo_node(hid, node_id):
            p.unlock_evo_node(hid, node_id)
            hd = D.HERO_BY_ID[hid]
            tree = D.hero_evo_tree(hd)
            node = next((n for n in tree if n["id"] == node_id), None)
            name = node["name"] if node else node_id
            self.flash = f"Unlocked: {name}!"
            self.flash_t = 2.5
            audio.play("buff", 0.6)
        else:
            # figure out why not
            hd = D.HERO_BY_ID[hid]
            tree = D.hero_evo_tree(hd)
            node = next((n for n in tree if n["id"] == node_id), None)
            unlocked = set(p.owned[hid].get("evo_nodes", []))
            if node and not D.evo_node_prereq_met(node, unlocked):
                req = node.get("req")
                self.flash = f"Unlock '{req}' first."
            else:
                cost = node.get("cost", 20) if node else 20
                self.flash = f"Need {cost} shards (have {p.shards})."
            self.flash_t = 2.0
            audio.play("hit", 0.2)
        p.save()

    def draw(self, surf, font_big, font_med, font_sm):
        surf.blit(_overlay_dim(), (0, 0))
        text(surf, "EVOLVE  -  Soul Shard Ascension", 30, (220, 180, 255), (640, 50), center=True)
        text(surf, f"Shards: {self.game.player.shards}   |   Click a node to unlock | G/Esc close",
             15, (200, 200, 230), (640, 84), center=True)
        from entities import load_char_sprite
        # --- left: hero selector ---
        text(surf, "Heroes", 20, (255, 240, 180), (60, 120))
        for i, hid in enumerate(self.order):
            r = self._hero_rect(i)
            rec = self.game.player.owned[hid]
            h = self.game.player.get_hero_instance(hid)
            sel = (i == self.sel)
            col = (50, 40, 70) if sel else (30, 26, 44)
            pygame.draw.rect(surf, col, r, border_radius=10)
            border = h.evolve_color() if sel else (90, 90, 110)
            pygame.draw.rect(surf, border, r, 2 if sel else 1, border_radius=10)
            try:
                port = load_char_sprite(hid, 80)
                surf.blit(port, (r.x + (r.width - 80) // 2, r.y + 6))
            except Exception:
                pass
            text(surf, h.name, 13, (255, 255, 255), (r.centerx, r.y + 92), center=True)
            text(surf, h.evolve_title(), 11, h.evolve_color(), (r.centerx, r.y + 110), center=True)
            # node count
            nn = len(rec.get("evo_nodes", []))
            text(surf, f"Tree {nn}/5", 11, (200, 220, 255), (r.centerx, r.y + 126), center=True)
            text(surf, f"Lv {h.level}", 11, (220, 220, 240), (r.centerx, r.y + 142), center=True)

        # --- right: evolution tree for the selected hero ---
        hid = self._selected_hid()
        if hid:
            self._draw_tree(surf, hid)

        # flash message
        if self.flash_t > 0:
            text(surf, self.flash, 20, (255, 240, 180), (640, 680), center=True)

    def _draw_tree(self, surf, hid):
        p = self.game.player
        hd = D.HERO_BY_ID[hid]
        h = p.get_hero_instance(hid)
        tree = D.hero_evo_tree(hd)
        unlocked = set(p.owned[hid].get("evo_nodes", []))
        ox, oy = self._tree_origin()
        # panel
        panel = pygame.Rect(ox - 20, oy - 30, 620, 470)
        pygame.draw.rect(surf, (24, 20, 40), panel, border_radius=14)
        pygame.draw.rect(surf, (150, 130, 200), panel, 2, border_radius=14)
        text(surf, f"{h.name} - {D.ROLES.get(h.role, {}).get('name', h.role)} Tree",
             20, (255, 240, 180), (panel.centerx, oy - 12), center=True)
        # links
        for a, b in D.EVO_LINKS:
            ax, ay = self._node_center(a)
            bx, by = self._node_center(b)
            both = (a in unlocked) and (b in unlocked)
            col = (120, 220, 140) if both else (80, 80, 110)
            pygame.draw.line(surf, col, (ax, ay), (bx, by), 3)
        # nodes
        self._node_rects = []
        mp = pygame.mouse.get_pos()
        for node in tree:
            nid = node["id"]
            cx, cy = self._node_center(nid)
            is_unlocked = nid in unlocked
            can_unlock = p.can_unlock_evo_node(hid, nid)
            r = pygame.Rect(cx - 70, cy - 32, 140, 64)
            self._node_rects.append((nid, r))
            hover = r.collidepoint(mp)
            # node card
            if is_unlocked:
                bg = (40, 70, 50); bd = (120, 220, 140)
            elif can_unlock:
                bg = (60, 50, 30); bd = (255, 220, 120) if hover else (200, 170, 80)
            else:
                bg = (30, 28, 42); bd = (70, 70, 90)
            pygame.draw.rect(surf, bg, r, border_radius=8)
            pygame.draw.rect(surf, bd, r, 2, border_radius=8)
            text(surf, node["name"], 13, (255, 255, 255), (cx, cy - 18), center=True)
            # short desc (first ~22 chars)
            desc = node["desc"]
            text(surf, desc[:24], 10, (220, 220, 240), (cx, cy - 2), center=True)
            # show the passive the node grants + a dead-upgrade warning (when the
            # node's passive duplicates the hero's base passive) so the player
            # can see a waste before spending shards
            pid = node.get("passive")
            if pid:
                pname = D.PASSIVES_DB.get(pid, {}).get("name", pid)
                base_pid = D.HERO_PASSIVES.get(hid)
                dead = (pid == base_pid)
                pcol = (220, 140, 140) if dead else (140, 240, 160)
                tag = f"{pname} (have)" if dead else pname
                text(surf, tag, 9, pcol, (cx, cy + 12), center=True)
            if is_unlocked:
                text(surf, "UNLOCKED", 10, (140, 240, 160), (cx, cy + 26), center=True)
            else:
                cost = node.get("cost", 20)
                ccol = (120, 220, 140) if can_unlock else (220, 140, 140)
                text(surf, f"{cost} shards", 10, ccol, (cx, cy + 26), center=True)
        # ascend tier button (flat evolve)
        ar = pygame.Rect(panel.centerx - 110, panel.bottom - 56, 220, 40)
        self._ascend_rect = ar
        can_ascend = p.can_evolve(hid)
        cost = p.evolve_cost(hid)
        col = (90, 150, 110) if can_ascend else (70, 60, 80)
        if ar.collidepoint(mp):
            col = (max(0, col[0]+20), max(0, col[1]+20), max(0, col[2]+20))
        pygame.draw.rect(surf, col, ar, border_radius=8)
        pygame.draw.rect(surf, (220, 220, 240), ar, 2, border_radius=8)
        if cost is None:
            label = "MAX TIER"
        else:
            label = f"Ascend Tier ({cost} shards)"
        text(surf, label, 14, (255, 255, 255) if can_ascend else (180, 180, 200),
             ar.center, center=True)
        # current bonuses summary (from the hero's computed bonus)
        eb = h._evo_bonus
        by = panel.bottom - 110
        text(surf, "Current bonuses:", 12, (200, 200, 230), (panel.x + 16, by))
        parts = []
        if eb.get("atk_pct"): parts.append(f"ATK +{int(eb['atk_pct']*100)}%")
        if eb.get("hp_pct"):  parts.append(f"HP +{int(eb['hp_pct']*100)}%")
        if eb.get("def_pct"): parts.append(f"DEF +{int(eb['def_pct']*100)}%")
        if eb.get("crit"):    parts.append(f"CRIT +{int(eb['crit']*100)}%")
        if eb.get("energy_pct"): parts.append(f"Energy +{int(eb['energy_pct']*100)}%")
        if eb.get("crit_dmg"): parts.append(f"CRIT DMG +{int(eb['crit_dmg']*100)}%")
        cm = eb.get("skill_cost_mult", 1.0)
        if cm and cm < 1.0:
            parts.append(f"Skill cost -{int((1 - cm) * 100)}%")
        text(surf, "  ".join(parts) if parts else "none yet", 12, (160, 240, 200),
             (panel.x + 16, by + 18))
        # name the granted passive so the player sees the passive they paid for
        pid = eb.get("passive")
        if pid:
            pname = D.PASSIVES_DB.get(pid, {}).get("name", pid)
            text(surf, f"Passive: {pname}", 12, (180, 220, 255),
                 (panel.x + 16, by + 34))


# Reusable dim overlay for modal screens (teleport/pause). Allocated once and
# cached so we don't build a 1280x720 SRCALPHA surface every frame a modal is
# open.
_DIM_OVERLAY = None
def _overlay_dim():
    global _DIM_OVERLAY
    if _DIM_OVERLAY is None:
        _DIM_OVERLAY = pygame.Surface((1280, 720), pygame.SRCALPHA)
        _DIM_OVERLAY.fill((0, 0, 0, 170))
    return _DIM_OVERLAY


# Cached fonts so we never call SysFont in the hot path. SysFont construction
# is the #1 cost in the profile (>half the frame time under load) because it
# scans the system font list; cache one Font per size, reused forever.
_FONT_CACHE = {}
def _font(size):
    f = _FONT_CACHE.get(size)
    if f is None:
        f = pygame.font.SysFont("dejavusans,arial", size, bold=True)
        _FONT_CACHE[size] = f
    return f

# Rendered-text surface cache. font.render() is the #2 cost after SysFont; the
# HUD draws ~40 text elements/frame, most static (hero names, slot numbers, key
# hints, map name, controls hint). Cache the (text, shadow) Surfaces keyed by
# (string, size, color) so a repeated string is one dict lookup + 2 blits, not
# 2 font.render() calls. Capped; evicted wholesale when it grows too large so
# dynamic strings (HP numbers, cooldown timers) don't balloon memory.
_TEXT_CACHE = {}
_TEXT_CACHE_CAP = 300
# Cached "BROKEN — +50% DMG" label for the boss bar — rendered once and reused
# so a broken boss doesn't re-render the string every frame (font.render is a
# top profile cost). Lazily filled on first broken-boss draw.
_BOKEN_DMG_LABEL_SURF = None
def text(surf, txt, size, color, pos, center=False, shadow=True):
    key = (str(txt), size, color)
    cached = _TEXT_CACHE.get(key)
    if cached is None:
        f = _font(size)
        t = f.render(str(txt), True, color)
        sh = f.render(str(txt), True, (0, 0, 0)) if shadow else None
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
# World Scene
# ---------------------------------------------------------------------------
class WorldScene:
    def __init__(self, game):
        self.game = game
        p = game.player
        # ensure a valid current cell
        if not p.ow_current:
            p.ow_current = [0, 0]
        self.c, self.r = p.ow_current[0], p.ow_current[1]
        # ensure discovered
        if WD.cell_id(self.c, self.r) not in p.ow_discovered:
            p.ow_discovered.append(WD.cell_id(self.c, self.r))

        self.map_renderer = MapRenderer()
        self.particles = Particles(cap=260,
                                   quality=p.settings.get("particle_quality", 1.0))
        self.projectiles = []
        self.floats = []
        self.chests = []            # [{x,y,kind,opened}] per current map
        self.breakables = []        # [{x,y,kind,loot,broken}] per current map
        # hidden rift mini-dungeon state for the current map. _rift_active is
        # True while the player is sealed inside a triggered rift (the exits are
        # suppressed + the wave is alive); _rift_done is True once the wave has
        # been cleared this visit so the rift doesn't re-trigger. _rift_enemies
        # holds the ids of the rift-spawned WorldEnemies so we can detect the
        # wave-clear (all dead) and fire the reward. _rift_secret is the
        # (x, y, wave_level, wave_size) tuple from gen_map (or None).
        # Declared BEFORE _load_map (the same init-order trap as _world_time /
        # the boss intro timer — _load_map reads these on the first call).
        self._rift_active = False
        self._rift_done = False
        self._rift_enemies = []     # list of WorldEnemy the rift spawned
        self._rift_secret = None    # (x, y, wave_level, wave_size) or None
        self.camera = Camera(1280, 720)
        self.shake = 0
        self.flash = 0
        self.hit_stop = 0
        # direction of the most recent edge transition (for slide fade) or None
        self._enter_dir = None
        # background pre-warm: render all 50 maps once on a worker thread so the
        # first visit to any cell is a cache hit (no transition stall). The
        # worker only touches the MapRenderer cache (no shared mutable state with
        # the main loop), so it's safe to run while the title/world draws.
        self._warm_thread = None
        self._start_prewarm()
        # cached settings snapshot (refreshed each frame) so combat helpers can
        # scale shake/particles by the user's accessibility preferences without
        # re-reading the settings dict in every hot path
        self._shake_mul = 1.0
        self._reduce_motion = False
        # boss phase-transition flash timer: set to 0.5 on a "boss_phase" event,
        # decays in the update tick; the boss bar draws a white alpha overlay
        # while >0 (skipped under reduce_motion — see _on_enemy_event).
        self._boss_phase_flash_t = 0.0

        # build the party of WorldCharacters
        self.party = []          # list of WorldCharacter (4 slots)
        self.active = 0
        self._resonances = []   # active elemental resonance buffs (see _build_party)
        self._build_party()

        # boss intro/defeat cinematic state. _boss_intro_t counts down from the
        # intro duration on entering a boss cell (a name banner + brief slow-mo);
        # _boss_defeat_t counts down from the defeat banner duration on a boss kill.
        # Declared BEFORE _load_map so the boss-arena branch can set the intro
        # timer without it being clobbered by a later field default.
        self._boss_intro_t = 0.0
        self._boss_intro_name = ""
        self._boss_defeat_t = 0.0
        self._boss_defeat_name = ""
        # Aetheric Cycle: a "World Ascended!" banner shown for ~3s after the
        # final boss (Demon King at 9,4) is defeated, telling the player they
        # can now Ascend the World from the title screen.
        self._ascend_banner_t = 0.0

        # day/night cycle: a slow global phase (0..1, 4-minute full cycle) that
        # tints the biome atmosphere + scales enemy level at night. Loaded from
        # the save so the time of day persists across sessions. Declared BEFORE
        # _load_map so the night enemy-level bonus can read it.
        self._world_time = float(p.ow_time or 0.0)
        self._day_cycle = 240.0   # seconds for a full 0..1 cycle (4 minutes)

        # dynamic weather: a deterministic per-cell state (clear/rain/fog/storm)
        # re-evaluated on each _load_map from WD.weather_for so the same cell can
        # read different weather across a long session as the day phase advances.
        # Declared BEFORE _load_map (the same init-order trap as _world_time /
        # the boss intro timer — fields used in _load_map must be declared in
        # __init__ first so the first _load_map call doesn't AttributeError).
        self._weather = "clear"
        # storm strike timer: counts down; when it elapses, a telegraphed strike
        # spawns at a near-hero tile (see the per-frame update). Reset on each
        # _load_map so a fresh map's storm cadence is independent of the last.
        self._storm_strike_t = 0.0

        # load map content
        self.enemies = []
        self.drops = []          # list of {x,y,kind,value}
        # summon/trap entities (Task A3): temporary, cleared on _load_map so they
        # don't persist across maps. Declared before _load_map (init-order).
        self._summons = []
        self._traps = []
        # water/bridges/landmark/village (Task C3) — STATIC gen_map features read
        # in _load_map. Declared BEFORE _load_map (the same init-order trap as
        # _world_time / the boss intro timer — _load_map reads these on the first
        # call). Water rects are appended to the obstacles list in _load_map so
        # the existing collision check treats them as walls (impassable); bridges
        # are passable (NOT added to obstacles). Landmarks are decorative (no
        # collision); villages are decorative (no collision — buildings are drawn,
        # not walled; the NPC entity + interact is Task E1).
        self._water = []
        self._bridges = []
        self._landmark = None
        self._village = None
        # NPC + dialogue (Task E1) — the village NPC entity (spawned in _load_map
        # at the village's npc_spawn) + the active dialogue overlay state. The
        # dialogue is a UI overlay, NOT a pause: the world keeps simulating behind
        # it (update runs as normal; the dialogue box just draws on top in draw).
        # Declared BEFORE _load_map (the same init-order trap as _world_time /
        # the boss intro timer — _load_map reads these on the first call).
        self._npc = None            # {x, y, biome, name, quest_id, dialogue} or None
        self._dialogue = None       # {name, lines, idx} active overlay, or None
        self._load_map(enter_edge=None)

        # input state
        self.input_dir = (0, 0)
        self.want_dash = False
        # hold-to-aim (Task B2): while a skill key (Q/W/E) is held, _aim_held_key
        # tracks the pygame key constant + _aim_t accumulates the hold time. Once
        # _aim_t > AIM_HOLD_THRESHOLD the scene is in aim mode (_aim_skill = idx)
        # and the draw loop renders a category-specific preview at the mouse. On
        # KEYUP, a quick tap (< threshold) fires instantly at the facing (legacy);
        # a hold fires at the mouse world pos (ground-targeted AoE). Cleared on
        # map enter / party swap so a stale aim doesn't carry across transitions.
        self._aim_skill = None       # idx of the skill currently being aimed, or None
        self._aim_t = 0.0            # seconds the current skill key has been held
        self._aim_held_key = None     # the pygame key constant currently held, or None

        # overlays
        self.teleport = None
        self.pause = None
        self.evolve = None
        self.message = ""
        self.message_t = 0
        self.swap_flash = 0
        self.map_enter_t = 0.4
        # cached map surface for the current cell
        self._map_surf = self.map_renderer.get(self.c, self.r)
        self._map_cell = (self.c, self.r)

        # reusable full-screen overlay for flashes (avoids allocating a 1280x720
        # SRCALPHA surface every frame whenever a flash/transition is active)
        self._flash_surf = pygame.Surface((1280, 720), pygame.SRCALPHA)
        # reusable HUD panel surface
        self._hud_panel = pygame.Surface((300, 90), pygame.SRCALPHA)
        # (the fog motes — 7 big soft drifting circles, additive blend — were
        # removed in Task C1: they read as unexplained "stray white circles" on
        # screen. The fog weather darkening (_fog_overlay, a flat low-alpha
        # darkening) stays; the rain overlay + storm strikes stay.)
        # cached per-biome atmosphere overlays (base = vignette + sky gradient,
        # fog = soft mote sprite), keyed in _light_cache and built lazily
        self._light_cache = {}
        # baked minimap cell overlay, keyed by the discovery set (rebuilt only
        # when the player discovers a new cell, blitted as one image otherwise)
        self._minimap_cache = {}
        # HUD portrait cache: (hero_id, size) -> Surface. load_char_sprite is
        # already cached in entities._cache, but the HUD calls it every frame for
        # the active panel (64px) + each party slot (48px) = 5 lookups/frame that
        # are dict hits but still redundant; cache the Surface once per scene so
        # the HUD hot path is 5 dict lookups on this local cache instead.
        self._hud_portraits = {}
        # skill-icon cache for the skill bar (one load per (skill,size) per scene)
        self._skill_icons = {}
        # skill-tooltip cache (Task B1): keyed by (hero_id, slot_idx, affordable)
        # so the hover tooltip doesn't re-render text every frame while hovered.
        self._tooltip_cache = {}

        # fonts (cached globally via _font(); keep refs for convenience)
        self.font = _font(18)
        self.font_sm = _font(14)
        self.font_big = _font(28)

        # combo system: consecutive hits within a short window stack a damage
        # multiplier (data.py COMBO_BONUS_PER / COMBO_MAX) and a visible combo
        # counter. Resets after _combo_t seconds with no hits.
        self._combo_count = 0
        self._combo_t = 0.0
        self._combo_window = 2.0   # seconds before the combo resets
        # the last combo milestone we pitched the hit sound up for (so we only
        # bump the pitch every 5 combo, not every hit)
        self._combo_pitch_tier = 0
        # combo climax: at milestone counts the next skill/ult is empowered
        # (a bonus effect — wider AoE + a 2nd ring / 2nd projectile for skills,
        # a free debuff on every enemy hit for ults). The flag is consumed on
        # use and cleared on a party swap so it can't be banked across heroes.
        self._skill_empowered = False
        self._ult_empowered = False
        # one-shot max-combo celebration guard: a chord + brief hit-stop fires
        # the first time the streak hits COMBO_MAX, then resets when the combo
        # window expires so the next max streak celebrates again.
        self._combo_max_celebrated = False
        # party-swap leitmotif spam guard: _switch plays the per-element
        # leitmotif but skips it if the last swap sound was <0.25s ago so a
        # frantic 1/2/3/4 mash doesn't stack 4 stings on top of each other.
        self._last_swap_sound_t = -1.0

        # discover neighbors of the current cell so the map shows reachable ones
        # _discover_neighbors is now run inside _load_map on every map enter
        # (walk or teleport), so the standalone __init__ call is redundant —
        # _load_map already ran it for the initial cell. Kept as a no-op safety
        # net for any code path that constructs the scene without _load_map.
        # (No call here: _load_map above already discovered the start cell's
        # neighbors.)

    # -----------------------------------------------------------------
    # Background pre-warm of all 50 maps (so first visit = cache hit)
    # -----------------------------------------------------------------
    def _start_prewarm(self):
        """Pre-render all 50 maps on a background thread so the first visit to
        any cell is a cache hit. The worker renders one cell at a time under a
        lock and yields between cells, so a transition can grab the lock and
        render its destination first (no long stall even mid-pre-warm)."""
        import threading
        self._warm_lock = threading.Lock()
        self._warm_done = 0
        def warm():
            try:
                for rr in range(WD.GRID_H):
                    for cc in range(WD.GRID_W):
                        with self._warm_lock:
                            self.map_renderer.get(cc, rr)
                        self._warm_done += 1
                        time.sleep(0.001)   # yield so transitions can preempt
            except Exception:
                pass
        self._warm_thread = threading.Thread(target=warm, daemon=True)
        self._warm_thread.start()

    # -----------------------------------------------------------------
    # Party
    # -----------------------------------------------------------------
    def _build_party(self):
        p = self.game.player
        team = list(p.team)
        # ensure 4 slots
        while len(team) < 4:
            team.append(None)
        self.party = []
        for i, hid in enumerate(team):
            if hid and hid in p.owned:
                hero = p.get_hero_instance(hid)
                # restore persisted hp/energy if present
                rec = p.ow_party_state.get(hid)
                if rec:
                    hero.hp = rec.get("hp", hero.max_hp)
                    hero.energy = rec.get("energy", D.ENERGY_START)
                # a hero saved with hp<=0 (downed when the save was written)
                # would otherwise reload as alive with 0 HP and die to the next
                # tick. Revive at half HP instead so the run isn't bricked.
                if hero.hp <= 0:
                    hero.hp = max(1, hero.max_hp // 2)
                wc = WorldCharacter(hero, WD.MAP_W // 2, WD.MAP_H // 2)
                # C6: reset revive_once per combat here (NOT in WorldCharacter.__init__)
                # to avoid the init-order trap — _build_party runs after the wc is
                # fully constructed so the reset can't be clobbered by a later field
                # default. A fresh party starts with revive available.
                wc._revive_used = False
                self.party.append(wc)
            else:
                self.party.append(None)
        # ensure at least the first owned hero is active
        if not any(self.party):
            # fallback: load first owned
            for hid in p.owned:
                hero = p.get_hero_instance(hid)
                wc = WorldCharacter(hero, WD.MAP_W // 2, WD.MAP_H // 2)
                wc._revive_used = False
                self.party[0] = wc
                p.team[0] = hid
                break
        # active index
        self.active = 0
        # place the active hero at the saved position or map center
        pos = p.ow_pos or [WD.MAP_W // 2, WD.MAP_H // 2]
        a = self.party[self.active]
        if a:
            a.x, a.y = pos[0], pos[1]
        # elemental resonance: 2+ of the same element in the 4-hero party grants
        # a themed buff (fire +ATK, water +heal, wind +move, light +energy regen,
        # dark +crit dmg). Capped at 2-of-a-kind (no 3x/4x scaling). Recomputed on
        # every party swap (see _switch) so the active buffs track the live team.
        self._compute_resonances()

    def _compute_resonances(self):
        """Recompute self._resonances from the current party's elements and push
        the per-hero resonance bonuses onto each WorldCharacter. Stores a list of
        active resonance dicts (buff kind + val). Only heroes actually present
        in a slot count; None slots are skipped. The per-hero _res_* fields are
        read by effective_atk / move_speed / heal / add_energy, so the buffs apply
        to every hero in the party (not just the active one) — resonance is a
        party-wide buff."""
        team_ids = []
        for wc in self.party:
            team_ids.append(wc.hero.id if wc else None)
        self._resonances = D.team_resonances(team_ids)
        # flatten into a kind -> val map for the per-hero fields
        rmap = {}
        for r in self._resonances:
            rmap[r["buff"]] = r.get("val", 0)
        for wc in self.party:
            if wc is None:
                continue
            wc._res_atk_pct = rmap.get("atk_pct", 0)
            wc._res_heal_amp = rmap.get("heal_amp", 0)
            wc._res_move_speed = rmap.get("move_speed", 0)
            wc._res_energy_regen = rmap.get("energy_regen", 0)
            wc._res_crit_dmg = rmap.get("crit_dmg", 0)

    def _resonance(self, buff_kind):
        """Return the total resonance bonus for a buff kind, or 0 if inactive.
        Multiple resonances of the same kind don't stack (capped at 2-of-a-kind
        per element, and each element maps to a distinct kind), so this is a
        simple lookup. Used by combat helpers that need the scene-level value
        (e.g. crit_dmg, which is applied in the damage roll, not on the hero)."""
        for r in self._resonances:
            if r.get("buff") == buff_kind:
                return r.get("val", 0)
        return 0

    def _persist_party(self):
        p = self.game.player
        p.ow_party_state = {}
        for wc in self.party:
            if wc:
                p.ow_party_state[wc.hero.id] = dict(hp=wc.hero.hp, energy=wc.hero.energy)

    # -----------------------------------------------------------------
    # Map loading + transitions
    # -----------------------------------------------------------------
    def _load_map(self, enter_edge=None, target_cell=None):
        if target_cell:
            self.c, self.r = target_cell
        m = WD.gen_map(self.c, self.r)
        self._map_data = m
        self.enemies = []
        self.drops = []
        # clear summon/trap entities on map enter so a stale summon from the last
        # cell doesn't follow the player (Task A3).
        self._summons = []
        self._traps = []
        # clear hold-to-aim state on map enter (Task B2) so a stale aim from the
        # previous cell doesn't carry across the transition (the held key is
        # released by the player, but the state is defensive-cleared anyway).
        self._aim_skill = None
        self._aim_held_key = None
        self._aim_t = 0.0
        # clear AA targets on map enter (Task B3) so a stale AA target from the
        # previous cell's enemies doesn't carry across the transition (the
        # target enemy belongs to the old map — a ref to it would be invalid).
        for p in self.party:
            if p is not None:
                p.aa_target = None
        # dynamic weather: re-evaluate the per-cell weather state from the current
        # day phase on every map enter. Stored on the scene (NOT in gen_map — the
        # MapRenderer cache is keyed on (c,r) only, and weather is a live overlay
        # + combat modifier, not a baked map property). Reset the storm strike
        # timer so a fresh map's storm cadence is independent of the last.
        self._weather = WD.weather_for(self.c, self.r, self._world_time)
        self._storm_strike_t = 6.0   # first storm strike ~6s after entering a storm map
        # reset any stale boss intro/defeat banner timers on a non-boss map so a
        # cinematic from a previous boss arena doesn't bleed onto the wrong map
        if not m["is_boss"]:
            self._boss_intro_t = 0.0
            self._boss_intro_name = ""
            self._boss_defeat_t = 0.0
            self._boss_defeat_name = ""
        # treasure chests on this map (open on walk-over): a reward pickup that
        # gives exploration a point beyond killing enemies. Chests the player
        # already opened on a prior visit are restored as opened (persisted in
        # ow_chests_opened) so they can't be re-looted on revisit.
        cid = WD.cell_id(self.c, self.r)
        opened_idx = set(self.game.player.ow_chests_opened.get(cid, []))
        self.chests = [dict(x=x, y=y, kind=kind, opened=(i in opened_idx))
                       for i, (x, y, kind) in enumerate(m.get("chests", []))]
        # breakable props on this map (shatter on attack/dash, drop loot). They
        # are not persisted — a fresh map regenerates them, so a player can
        # re-break them on revisit (the loot is small, so this is fine).
        self.breakables = [dict(x=x, y=y, kind=kind, loot=loot, broken=False)
                           for (x, y, kind, loot) in m.get("breakables", [])]
        # water/bridges/landmark/village (Task C3) — read the STATIC gen_map
        # features. Water rects are appended to the obstacles list so the existing
        # collision check (self._map_data["obstacles"]) treats them as walls
        # (impassable, like obstacles); bridges are passable (NOT appended). The
        # water/bridge rects are also kept on the scene for the draw loop. A copy
        # of the obstacles list is NOT needed — gen_map returns a fresh list per
        # cell, so appending water to it doesn't mutate a cached map (the
        # MapRenderer cache stores a rendered Surface, not the dict).
        self._water = list(m.get("water", []))
        self._bridges = list(m.get("bridges", []))
        self._landmark = m.get("landmark")
        self._village = m.get("village")
        # NPC (Task E1) — spawn the village NPC at the village's npc_spawn (from
        # C3's gen_map). The NPC is a simple entity: a name + quest_id + dialogue
        # (from NPCS[biome]) + the x/y pos. Drawn in the drawables (a small sprite
        # + a name tag); interact on walk-up + F (see the event loop in update).
        # The dialogue is a UI overlay (NOT a pause — the world keeps updating
        # behind it; the dialogue box just draws on top in draw).
        self._npc = None
        self._dialogue = None
        if self._village is not None:
            biome = self._village.get("biome", WD.cell_biome(self.c, self.r))
            npc_data = D.NPCS.get(biome)
            if npc_data is not None:
                nx, ny = self._village["npc_spawn"]
                self._npc = {"x": float(nx), "y": float(ny),
                             "biome": biome,
                             "name": npc_data["name"],
                             "quest_id": npc_data["quest_id"],
                             "dialogue": list(npc_data["dialogue"])}
        # append the water rects to the obstacles list so the existing collision
        # check treats them as walls (impassable). The bridges are passable, so
        # they are NOT appended (the hero walks through them).
        if self._water:
            m["obstacles"].extend(self._water)
        # lore float on the first visit to this cell's landmark — fired in
        # _load_map (not in _draw_landmark) so the player sees it on cell entry
        # even if the landmark is off-screen on the first draw frame (the float
        # is at the landmark's world pos; if fired in draw, an off-screen
        # landmark would spawn an off-screen float that fades unseen + the
        # ow_landmarks_seen gate would prevent a re-fire). Tracked per cell id
        # in ow_landmarks_seen so revisiting a cell doesn't re-show the lore.
        if self._landmark is not None:
            cid = WD.cell_id(self.c, self.r)
            if cid not in self.game.player.ow_landmarks_seen:
                self.game.player.ow_landmarks_seen.append(cid)
                biome = self._landmark.get("biome", WD.cell_biome(self.c, self.r))
                lore = D.LANDMARK_LORE.get(biome, "")
                if lore:
                    pal = WD.BIOMES.get(biome, {})
                    col = pal.get("accent", (230, 220, 180))
                    self.floats.append(FloatText(self._landmark["x"],
                                                self._landmark["y"] - 50,
                                                lore, col, size=18, life=2.5))
            m["obstacles"].extend(self._water)
        # hidden rift mini-dungeon: read the per-cell secret from gen_map. A
        # cleared rift stays cleared (persisted in ow_secrets_done) so the
        # player can't re-trigger the wave for infinite SR/SSR chests. Reset
        # the active seal + wave state on every map enter so a stale seal from
        # a previous map doesn't bleed onto the new one (the wipe-respawn
        # teleport_to(0,0) hits this path too, so the seal breaks on a wipe).
        self._rift_secret = m.get("secret")
        cid = WD.cell_id(self.c, self.r)
        if self._rift_secret is not None and cid in self.game.player.ow_secrets_done:
            self._rift_done = True     # already cleared this visit
        else:
            self._rift_done = False
        self._rift_active = False
        self._rift_enemies = []
        level = WD.cell_level(self.c, self.r, ng_cycle=self.game.player.ng_cycle)
        # the active hero entry point (offset slightly inward from the edge so
        # the hero slides into the new map instead of snapping)
        ep = WD.entry_point(enter_edge) if enter_edge else (WD.MAP_W // 2, WD.MAP_H // 2)
        # place the active hero
        if self.party[self.active]:
            self.party[self.active].x = ep[0]
            self.party[self.active].y = ep[1]
            self.party[self.active].vx = 0
            self.party[self.active].vy = 0
            # snap the camera onto the hero immediately so the transition is a
            # clean slide rather than a flying pan from the previous map
            self.camera.x = max(0, min(WD.MAP_W - self.camera.vw, ep[0] - self.camera.vw / 2))
            self.camera.y = max(0, min(WD.MAP_H - self.camera.vh, ep[1] - self.camera.vh / 2))
            self.map_enter_t = 0.45
            # ensure the active hero starts a map with usable energy (the
            # "skills don't recover" fix: a hero loaded from save with stale low
            # energy should top up to ENERGY_START on map enter)
            a = self.party[self.active]
            if a and a.hero.energy < D.ENERGY_START:
                a.hero.energy = min(D.ENERGY_START, a.hero.max_energy)
        # pre-render the new map's surface on a background thread so the first
        # visit doesn't stall the frame (the render is ~10ms but a fresh map's
        # ground-base build can spike). We render synchronously here but the
        # MapRenderer caches the result, so revisits are instant.
        self._map_surf = self.map_renderer.get_locked(self.c, self.r,
                                                      getattr(self, "_warm_lock", None))
        self._map_cell = (self.c, self.r)
        # spawn enemies
        if not m["is_boss"]:
            pool, _ = WD.ROW_ENEMIES[self.r]
            # at night (day phase 0.4..0.95) enemies are tougher: +1 level so
            # the world feels more dangerous after dark (better drops follow from
            # the higher-level enemy gold/xp scaling). The window matches the
            # _night_overlay visual-darkening window so the danger cue and the
            # visual cue agree (was 0.5, leaving a 0.4-0.5 slice where the world
            # looked dark but enemies weren't tougher).
            night_bonus = 1 if 0.4 <= self._world_time <= 0.95 else 0
            for (sx, sy) in m["spawns"]:
                eid = random.choice(pool)
                self.enemies.append(WorldEnemy(eid, sx, sy, level + night_bonus, is_boss=False))
        else:
            _, boss_id = WD.ROW_ENEMIES[self.r]
            bx, by = m["boss"]
            self.enemies.append(WorldEnemy(boss_id, bx, by, level + 6, is_boss=True))
            # boss intro cinematic: a name banner + a brief slow-mo the first time
            # the player enters this boss arena. Skips on a revisit (re-entering a
            # cleared arena shouldn't replay the intro).
            boss_name = D.ENEMIES_DB.get(boss_id, {}).get("name", "Boss")
            self._boss_intro_t = 1.6
            self._boss_intro_name = boss_name
            audio.play("boss_intro", 0.7)
        # reset camera to the active hero (clamped; the edge-entry case already
        # snapped it above, this covers teleport-to and initial load)
        a = self.party[self.active]
        if a:
            self.camera.x = max(0, min(WD.MAP_W - self.camera.vw, a.x - self.camera.vw / 2))
            self.camera.y = max(0, min(WD.MAP_H - self.camera.vh, a.y - self.camera.vh / 2))
        # (map surface already rendered + cached above; keep the cell ref current)
        self._map_surf = self.map_renderer.get_locked(self.c, self.r,
                                                      getattr(self, "_warm_lock", None))
        self._map_cell = (self.c, self.r)
        # discover: a NEW cell advances the 'explore' quest; any map enter
        # (walk or teleport) reveals the neighbors so the frontier grows and
        # the teleport overlay shows reachable cells (was only run once in
        # __init__, capping the discoverable world at ~3 cells).
        cid = WD.cell_id(self.c, self.r)
        if cid not in self.game.player.ow_discovered:
            self.game.player.ow_discovered.append(cid)
            self.game.player.quest_progress("explore", 1)
        # 'explore' also counts revisits so the daily quest stays completable for
        # a mid/late-game player who has already discovered all 50 maps
        self.game.player.quest_progress("explore", 1)
        # reveal the neighbors of the new cell so the minimap shows the
        # reachable frontier (not just cells the player has physically stood in)
        self._discover_neighbors()
        self._persist_party()
        self.game.player.ow_current = [self.c, self.r]
        if self.game.player.settings.get("auto_save", True):
            self.game.player.save()
        # start the looping biome ambience on map enter (a quiet bed so the
        # world isn't silent between hits). Respects the master sound toggle.
        # When the weather is rain/storm, switch the ambience bed to the rain
        # loop so the world sounds wet; thunder one-shots fire from the per-frame
        # storm-strike path (see update).
        if self.game.player.settings.get("sound", True):
            biome = WD.cell_biome(self.c, self.r)
            if self._weather == "rain" or self._weather == "storm":
                audio.set_ambience(True, volume=0.30, biome=biome, weather="rain")
            else:
                audio.set_ambience(True, volume=0.22, biome=biome)

    def _discover_neighbors(self):
        for (nc, nr) in WD.neighbors(self.c, self.r):
            cid = WD.cell_id(nc, nr)
            if cid not in self.game.player.ow_discovered:
                self.game.player.ow_discovered.append(cid)

    def _transition(self, edge):
        # find the neighbor in that direction
        c, r = self.c, self.r
        if edge == "right" and c < WD.GRID_W - 1:   nc, nr = c + 1, r
        elif edge == "left" and c > 0:              nc, nr = c - 1, r
        elif edge == "bottom" and r < WD.GRID_H - 1: nc, nr = c, r + 1
        elif edge == "top" and r > 0:               nc, nr = c, r - 1
        else:
            return  # walled edge
        # opposite entry edge
        opp = {"left": "right", "right": "left", "top": "bottom", "bottom": "top"}[edge]
        # direction of travel — used to slide the fade in the same direction
        self._enter_dir = edge
        self._persist_party()
        # pre-warm the destination map's surface so the transition frame doesn't
        # stall on the first visit. Use the lock-aware get so we never block on
        # the background pre-warm worker (worst case: a throwaway render this
        # frame, cached one next frame).
        self.map_renderer.get_locked(nc, nr, getattr(self, "_warm_lock", None))
        self._load_map(enter_edge=opp, target_cell=(nc, nr))
        # a soft whoosh on edge transitions so a map change has an audible cue
        audio.play("skill", 0.25)
        self.set_message(f"Entering {WD.cell_name(nc, nr)}")

    def teleport_to(self, c, r):
        self._persist_party()
        self.teleport = None
        self._enter_dir = None
        self._load_map(enter_edge=None, target_cell=(c, r))
        # center the hero
        if self.party[self.active]:
            self.party[self.active].x = WD.MAP_W // 2
            self.party[self.active].y = WD.MAP_H // 2
        # a UI warp-confirm cue so the teleport isn't silent
        audio.play("menu_click", 0.4)
        self.set_message(f"Teleported to {WD.cell_name(c, r)}")

    # -----------------------------------------------------------------
    # Treasure chests
    # -----------------------------------------------------------------
    def _open_chest(self, ch, wc):
        """Open a treasure chest: spawn a reward + a celebratory burst."""
        ch["opened"] = True
        p = self.game.player
        # persist the opened chest so it doesn't respawn on a revisit
        cid = WD.cell_id(self.c, self.r)
        idx = self.chests.index(ch)
        p.ow_chests_opened.setdefault(cid, []).append(idx)
        kind = ch["kind"]
        cx, cy = ch["x"], ch["y"]
        if kind == "gold":
            amt = 40 + WD.cell_level(self.c, self.r) * 10
            p.gold += amt
            p.stats["gold_earned"] = p.stats.get("gold_earned", 0) + amt
            label, col = f"+{amt} gold", (255, 220, 120)
        elif kind == "gems":
            amt = 20 + WD.cell_level(self.c, self.r) * 5
            p.gems += amt
            p.stats["gems_earned"] = p.stats.get("gems_earned", 0) + amt
            label, col = f"+{amt} gems", (120, 200, 255)
        elif kind == "shards":
            amt = 2 + WD.cell_level(self.c, self.r) // 3
            p.shards += amt
            label, col = f"+{amt} shards", (200, 160, 255)
        else:  # equipment
            pool = [k for k, v in D.EQUIPMENT_DB.items() if v["rarity"] in ("SR", "SSR")]
            if pool:
                eid = random.choice(pool)
                p.add_equipment(eid)
                label, col = f"+{D.EQUIPMENT_DB[eid]['name']}!", (255, 200, 120)
            else:
                p.gold += 100
                label, col = "+100 gold", (255, 220, 120)
        p.stats["treasures_opened"] = p.stats.get("treasures_opened", 0) + 1
        p.quest_progress("open_chests", 1)
        for aid in p.check_achievements():
            ach = D.ACHIEVEMENTS.get(aid, {})
            self.set_message(
                f"Achievement: {ach.get('name', '?')}! +{ach.get('reward_gems', 0)} gems",
                3.0)
        self.floats.append(FloatText(cx, cy - 20, label, col, size=22))
        # a gold sparkle burst + ring so the open feels rewarding
        self.particles.burst(cx, cy, (255, 220, 120), n=24, speed=240, size=6, life=0.6, grav=-60)
        self.particles.ring(cx, cy, (255, 240, 160), n=20, speed=300, size=5, life=0.5)
        # vary the cue by reward tier: equipment gets the reveal chime, shards
        # the buff hum, gold/gems a small pickup tick
        if kind == "equipment":
            audio.play("gacha_reveal", 0.6)
        elif kind == "shards":
            audio.play("buff", 0.6)
        else:
            audio.play("menu_click", 0.3)
        if p.settings.get("auto_save", True):
            p.save()

    def _break_breakable(self, b):
        """Shatter a breakable prop: mark broken, drop its loot as a visible
        ground drop (Task C2) + a shatter particle burst. Loot is small (a few
        gold, a potion, or 1 shard) so breakables are a nice-to-find, not a
        farm target. The loot spawns as a drop at the breakable's pos so the
        player walks over to collect it (the shatter VFX still fires here)."""
        b["broken"] = True
        p = self.game.player
        bx, by = b["x"], b["y"]
        kind = b["kind"]
        loot = b["loot"]
        level = WD.cell_level(self.c, self.r, ng_cycle=p.ng_cycle)
        if loot == "gold":
            amt = 8 + level * 2
            self._spawn_drop(bx, by, "gold", amt)
            # gold_earned tallied at pickup (in _pickup_drop), not here — the
            # stat tracks gold actually collected, not gold spawned on the ground.
            label, col = f"+{amt}g", (255, 220, 120)
        elif loot == "hp_potion":
            self._spawn_drop(bx, by, "hp_potion", 1)
            label, col = "+Potion", (140, 240, 160)
        else:  # shard
            self._spawn_drop(bx, by, "shard", 1)
            label, col = "+1 shard", (200, 160, 255)
        self.floats.append(FloatText(bx, by - 18, label, col, size=16))
        # a shatter burst: the prop's body color + a few white shards so it
        # reads as the prop breaking (not a generic hit spark)
        body_col = {"pot": (180, 120, 80), "crate": (140, 90, 50),
                    "barrel": (120, 70, 40)}.get(kind, (150, 100, 60))
        self.particles.burst(bx, by, body_col, n=14, speed=200, size=5, life=0.4, grav=120)
        self.particles.spark(bx, by, (255, 255, 255), n=6, speed=240, size=4, life=0.22)
        audio.play("hit", 0.18)

    # -----------------------------------------------------------------
    # Hidden rift mini-dungeon
    #   Walking into the rift seals the exits (suppress _transition while
    #   _rift_active) + spawns a wave of WorldEnemies from the row pool at
    #   level + wave_level. Clearing the wave (all rift enemies dead) breaks
    #   the seal, drops a guaranteed SR/SSR chest + a lore float, and marks
    #   the cell's secret done in ow_secrets_done so it can't re-trigger.
    #   The party-wipe respawn (teleport_to(0,0)) goes through _load_map,
    #   which resets _rift_active=False on the new map — so a wipe breaks the
    #   seal (the player respawns at the hub with no active rift).
    # -----------------------------------------------------------------
    def _enter_rift(self):
        """Seal the exits + spawn the rift wave. Called from the walk-over
        check in update() when the active hero steps onto the rift tile."""
        rx, ry, wave_level, wave_size = self._rift_secret
        self._rift_active = True
        self._rift_enemies = []
        # spawn the wave: wave_size enemies from the row's enemy pool at the
        # cell's level + the rift's wave_level bump. Spread around the rift
        # tile so the wave reads as an ambush ring, not a stack on one point.
        pool, _ = WD.ROW_ENEMIES[self.r]
        level = WD.cell_level(self.c, self.r, ng_cycle=self.game.player.ng_cycle)
        rng = random.Random(WD.cell_seed(self.c, self.r) + 99)
        for i in range(wave_size):
            ang = 2 * math.pi * i / max(1, wave_size) + rng.uniform(0, 1.0)
            dist = rng.randint(60, 120)
            sx = int(rx + math.cos(ang) * dist)
            sy = int(ry + math.sin(ang) * dist)
            # clamp inside the map (away from the walls so they don't spawn
            # on top of a border tile)
            sx = max(WD.TILE * 2, min(WD.MAP_W - WD.TILE * 2, sx))
            sy = max(WD.TILE * 2, min(WD.MAP_H - WD.TILE * 2, sy))
            eid = random.choice(pool)
            en = WorldEnemy(eid, sx, sy, level + wave_level, is_boss=False)
            self.enemies.append(en)
            self._rift_enemies.append(en)
        # a sealing burst at the rift tile so the trigger reads as a real event
        self.particles.burst(rx, ry, (180, 80, 220), n=30, speed=300, size=7, life=0.7)
        self.particles.ring(rx, ry, (200, 120, 240), n=24, speed=360, size=6, life=0.6)
        self.camera.add_shake(6, self._shake_mul)
        audio.play("boss_intro", 0.5)
        self.set_message("A rift opens! Clear the wave to escape.", 2.5)

    def _clear_rift(self):
        """Wave cleared: break the seal, drop a guaranteed SR/SSR chest + a
        lore float, and mark the cell's secret done so it can't re-trigger."""
        rx, ry, _, _ = self._rift_secret
        self._rift_active = False
        self._rift_done = True
        # persist the cleared secret so a revisit doesn't re-trigger the wave
        cid = WD.cell_id(self.c, self.r)
        if cid not in self.game.player.ow_secrets_done:
            self.game.player.ow_secrets_done.append(cid)
        # guaranteed SR/SSR equipment drop (reuse the chest equipment pool).
        # Weight toward SSR on deeper rows so the rift reward scales with the
        # row's difficulty (a row-4 rift should pay better than a row-0 rift).
        p = self.game.player
        rar = "SSR" if (self.r >= 3 and random.random() < 0.5) else "SR"
        pool = [k for k, v in D.EQUIPMENT_DB.items() if v["rarity"] == rar]
        if pool:
            eid = random.choice(pool)
            p.add_equipment(eid)
            label = f"+{D.EQUIPMENT_DB[eid]['name']}!"
            col = (255, 200, 120)
        else:
            # fallback: a gem bonus if the equipment pool is somehow empty
            amt = 50 + WD.cell_level(self.c, self.r) * 5
            p.gems += amt
            p.stats["gems_earned"] = p.stats.get("gems_earned", 0) + amt
            label, col = f"+{amt} gems", (120, 200, 255)
        self.floats.append(FloatText(rx, ry - 30, label, col, size=24))
        # a lore fragment float so the rift reads as a story beat, not just a
        # loot pinata. Pick deterministically from the cell so the same rift
        # always drops the same fragment (a stable piece of worldbuilding).
        if D.LORE_FRAGMENTS:
            frag_rng = random.Random(WD.cell_seed(self.c, self.r) + 4242)
            frag = frag_rng.choice(D.LORE_FRAGMENTS)
            self.floats.append(FloatText(rx, ry - 56, frag, (200, 200, 255), size=18))
        # a victory burst + ring at the rift tile so the clear feels rewarding
        self.particles.burst(rx, ry, (255, 220, 120), n=40, speed=320, size=8, life=0.8, grav=0)
        self.particles.ring(rx, ry, (255, 240, 160), n=28, speed=440, size=7, life=0.7)
        self.camera.add_shake(8, self._shake_mul)
        audio.play("gacha_reveal", 0.6)
        self.set_message("Rift cleared! The way is open.", 2.5)
        if p.settings.get("auto_save", True):
            p.save()

    # -----------------------------------------------------------------
    # Messaging
    # -----------------------------------------------------------------
    def set_message(self, msg, dur=2.0):
        self.message = msg
        # text_speed (0.5..2.0) scales how long a message stays: faster text
        # speed -> shorter display, so the Gameplay slider does something.
        text_speed = self.game.player.settings.get("text_speed", 1.0)
        self.message_t = dur / max(0.5, min(2.0, float(text_speed)))

    # -----------------------------------------------------------------
    # NPC dialogue (Task E1) — the village NPC + a dialogue text-box overlay.
    # The dialogue is a UI overlay, NOT a pause: the world keeps updating behind
    # it (update runs as normal; only F/Space/Esc are intercepted to advance the
    # line). Dismiss on the last line so the player isn't stuck in the box.
    # -----------------------------------------------------------------
    def _handle_npc_talk(self, wc):
        """F key: open or advance the village NPC dialogue. If a dialogue is
        already open, this is not reached (the KEYDOWN interceptor in update
        routes F/Space/Esc to _advance_dialogue when a dialogue is open). Here we
        only open a new dialogue when the active hero is within ~60px of the NPC.
        The dialogue is a UI overlay (NOT a pause — the world keeps simulating)."""
        if self._dialogue is not None:
            # an overlay is already open but F slipped through (e.g. the hero was
            # out of range when the box opened, then walked up) — advance instead
            # of re-opening so the player doesn't get a second box stacked.
            self._advance_dialogue()
            return
        if self._npc is None or wc is None or not wc.alive:
            return
        d = math.hypot(wc.x - self._npc["x"], wc.y - self._npc["y"])
        if d <= 60:
            self._dialogue = {"name": self._npc["name"],
                              "lines": list(self._npc["dialogue"]),
                              "idx": 0}
            audio.play("hit", 0.15)
        else:
            self.set_message("No one nearby to talk to", 1.0)

    def _advance_dialogue(self):
        """Advance the dialogue to the next line, or dismiss when the lines run
        out. Called from the KEYDOWN interceptor in update on F/Space/Esc when a
        dialogue is open. Dismiss (set _dialogue=None) on the last line so the
        player isn't stuck in the box — the world kept simulating behind it, so
        there's no 'resume' step (the overlay just stops drawing)."""
        if self._dialogue is None:
            return
        self._dialogue["idx"] += 1
        if self._dialogue["idx"] >= len(self._dialogue["lines"]):
            self._dialogue = None
        else:
            audio.play("hit", 0.12)

    # -----------------------------------------------------------------
    # Combat helpers
    # -----------------------------------------------------------------
    def _element_mult(self, atk_el, def_el):
        return D.element_mult(atk_el, def_el)

    def _do_attack(self, wc, target=None):
        if wc.atk_cd > 0:
            return
        wc.atk_cd = D.AA_CD
        wc.atk_anim = 0.2
        wc._last_combat_t = 0
        style = WEAPON_STYLE.get(WEAPON_STYLE_KEY(wc.hero.id), "melee")
        col = D.ELEMENT_COLORS.get(wc.element, ((200, 200, 200),))[0]
        a = wc.hero
        # crit chance includes the keen-eye passive and the tree's crit bonus
        crit_chance = a.crit_chance
        if a.passive and a.passive.get("kind") == "crit_up":
            crit_chance += a.passive.get("val", 0.1)
        atk = wc.effective_atk()
        # crit damage multiplier: base 1.6 + tree crit_dmg bonus + dark elemental
        # resonance (+crit_dmg when 2+ dark heroes in party). Additive on the
        # crit multiplier's bonus term so it stacks with the tree/set crit-dmg,
        # not multiplicatively on the whole crit.
        crit_mul = 1.6 + getattr(a, "crit_dmg_bonus", 0) + wc._res_crit_dmg
        if style == "ranged":
            # projectile toward the nearest enemy in the facing direction, or a
            # straight shot in the facing dir if no target — so ranged heroes
            # actually hit enemies that aren't at exactly the same y. If an AA
            # target (Task B3) is provided, aim directly at it instead of the
            # nearest-enemy search (the AA target is the player's intent).
            if target is not None:
                tx, ty = target.x, target.y
            else:
                tx, ty = wc.x + wc.facing * 400, wc.y
                best_d = 1e9
                for en in self.enemies:
                    if not en.alive:
                        continue
                    dx = en.x - wc.x
                    # only aim at enemies roughly in the facing half-plane
                    if wc.facing > 0 and dx < -40:
                        continue
                    if wc.facing < 0 and dx > 40:
                        continue
                    dd = math.hypot(dx, en.y - wc.y)
                    if dd < best_d:
                        best_d = dd; tx, ty = en.x, en.y
            dx, dy = tx - wc.x, ty - wc.y
            d = math.hypot(dx, dy) or 1
            sp = 560
            p = Projectile(wc.x + wc.facing * 20, wc.y, dx / d * sp, dy / d * sp,
                           1.4, 8, col, wc.element, wc, atk, kind="hero")
            self.projectiles.append(p)
            # muzzle flash
            self.particles.spark(wc.x + wc.facing * 24, wc.y, col, n=5, speed=200, size=4, life=0.18)
            audio.play("hit", 0.2)
        else:
            # melee arc - hit enemies in front. If an AA target (Task B3) is
            # provided, center the arc on the target so the melee swing actually
            # hits it (the default facing arc could miss a target slightly
            # above/below the hero). Falls back to the facing arc if no target.
            if target is not None:
                arc_x = target.x
                arc_y = target.y
            else:
                arc_x = wc.x + wc.facing * 40
                arc_y = wc.y
            ar = 60
            hit_any = False
            total_dmg = 0
            primary_x, primary_y = None, None  # for the cleave signature
            for en in self.enemies:
                if not en.alive:
                    continue
                if math.hypot(en.x - arc_x, en.y - arc_y) < ar + en.r:
                    mult = self._element_mult(wc.element, en.element)
                    is_crit = random.random() < crit_chance
                    combo_mul = 1.0 + max(0, self._combo_count) * D.COMBO_BONUS_PER
                    dmg = int(atk * (1.0 + random.uniform(-0.1, 0.2)) * mult
                              * (crit_mul if is_crit else 1.0) * combo_mul)
                    dealt = en.take_damage(dmg, wc.x, wc.y, is_crit,
                                            on_attack=self._on_enemy_event)
                    if dealt > 0:
                        self._on_enemy_hit(en, wc, dealt, is_crit)
                        total_dmg += dealt
                        hit_any = True
                        if primary_x is None:
                            primary_x, primary_y = en.x, en.y
            if hit_any:
                # routed through wc.add_energy so the light resonance
                # (energy_regen) and the p_energy (Flow State) passive add
                # instead of both multiplying the base.
                wc.add_energy(D.ENERGY_GAIN_BASIC)
                audio.play("hit", 0.3)
                self.camera.add_shake(3, self._shake_mul)
                # impact shockwave ring on a clean hit
                self.particles.ring(arc_x, arc_y, col, n=14, speed=260, size=4, life=0.3)
                # lifesteal passive: heal a fraction of basic-attack damage dealt
                if a.passive and a.passive.get("kind") == "lifesteal" and total_dmg > 0:
                    heal = max(1, int(total_dmg * a.passive.get("val", 0.12)))
                    wc.heal(heal)
                    if self.game.player.settings.get("damage_numbers", True):
                        self.floats.append(FloatText(wc.x, wc.y - 30, f"+{heal}",
                                                     (140, 240, 160), size=16))
            else:
                audio.play("hit", 0.12)
            # signature passive: cleave (dict-lookup dispatch — basic attacks
            # splash to enemies within 60px of the primary target). val is the
            # fraction of ATK dealt as splash (0.5 = 50%). Skips the primary
            # target (already hit by the main arc) and dead enemies.
            _sig = _SIG_ATTACK.get(wc._signature_kind)
            if _sig and primary_x is not None:
                _sig(self, wc, primary_x, primary_y, atk)
            # melee swing arc (a brighter slash streak)
            self.particles.spark(arc_x, arc_y, col, n=8, speed=180, size=4, life=0.22)
        # breakables: a melee arc or a dash both shatter any breakable props in
        # range. The arc covers the same hit area as the melee swing; the dash
        # covers the hero's current position (the dash passes *through* props,
        # so the endpoint check is enough). Each breakable drops its loot once.
        # Use the hero's facing arc for melee; for a ranged attack, fall back
        # to the hero's position so a ranged shot still shatters a prop the
        # hero dashes into (the projectile itself doesn't carry the shatter).
        if style == "ranged":
            br_x, br_y, br_r = wc.x, wc.y, 48
        else:
            br_x, br_y, br_r = arc_x, arc_y, ar
        if wc.dash_t > 0:
            # a dash widens the reach a bit so a dash-through reliably shatters
            # props the hero passes through (the dash moves fast; a tight arc
            # could miss between frames).
            br_x, br_y, br_r = wc.x, wc.y, 56
        for b in self.breakables:
            if b["broken"]:
                continue
            if math.hypot(b["x"] - br_x, b["y"] - br_y) < br_r + 20:
                self._break_breakable(b)

    def _do_skill(self, wc, idx, target=None):
        # Task B3: casting a skill interrupts the AA (the skill's targeting
        # shouldn't fight the AA target). Clear the AA target on a skill cast.
        wc.aa_target = None
        if not wc.can_skill(idx):
            # soft denied buzz on a rejected skill (on cooldown / no energy) so
            # the player gets audible feedback that the input was rejected
            audio.play("weak", 0.15)
            return
        sk = wc.skill_list()[idx]
        if sk is None:
            return
        skill = D.SKILLS_DB[sk]
        col = D.ELEMENT_COLORS.get(skill["element"], ((200, 200, 200),))[0]
        wc.spend_skill(idx)
        wc._last_combat_t = 0
        # constellation cd_reduction perk: shave the skill's cooldown by the hero's
        # accumulated perk fraction (applied after spend_skill sets the cd). The
        # perk is stored on the Hero as _perk_cd_reduction (a fraction 0..1).
        perk_cd = getattr(wc.hero, "_perk_cd_reduction", 0.0)
        if perk_cd > 0:
            wc.skill_cd[idx] = max(0.0, wc.skill_cd[idx] * (1.0 - perk_cd))
            wc.skill_cd_max[idx] = wc.skill_cd[idx]
        kind = skill["type"]
        a = wc.hero
        atk = wc.effective_atk()
        # combo climax: if the skill is empowered (armed at combo milestone 5),
        # widen the effect — AoE skills get a bigger radius + a second ring;
        # single-target skills get a second piercing projectile. Consumed on
        # use so the empowerment is a one-shot finisher, not a persistent buff.
        empowered = self._skill_empowered
        if empowered:
            self._skill_empowered = False
        # ground-targeted AoE (Task B2): if `target` (a world-space (x,y)) is
        # provided for an aoe_attack/aoe_magic skill, center the burst on the
        # clamped target instead of the hero. Clamp to AIM_MAX_RANGE so a player
        # can't AoE a target off-screen across the map. Other skill types ignore
        # `target` (melee/beam use the facing; ranged auto-targets the nearest
        # enemy; summon/trap place at the hero's side).
        aoe_cx, aoe_cy = wc.x, wc.y
        if target is not None and kind in ("aoe_attack", "aoe_magic"):
            tx, ty = target
            d = math.hypot(tx - wc.x, ty - wc.y)
            if d > AIM_MAX_RANGE:
                # clamp to the max range along the aim line
                tx = wc.x + (tx - wc.x) * (AIM_MAX_RANGE / d)
                ty = wc.y + (ty - wc.y) * (AIM_MAX_RANGE / d)
            aoe_cx, aoe_cy = tx, ty
        # most skills: a burst around the hero or a projectile
        if kind in ("attack", "magic") or (kind == "aoe_attack" and "arrow" in sk) or (kind == "magic" and "bolt" in sk):
            # single-target projectile or melee nuke
            style = WEAPON_STYLE.get(WEAPON_STYLE_KEY(wc.hero.id), "melee")
            if style == "ranged":
                # aim at the nearest enemy in the facing half-plane (same fix as
                # the basic attack — a straight horizontal shot misses anything
                # not at the hero's y)
                tx, ty = wc.x + wc.facing * 500, wc.y
                best_d = 1e9
                for en in self.enemies:
                    if not en.alive:
                        continue
                    dx = en.x - wc.x
                    if wc.facing > 0 and dx < -40:
                        continue
                    if wc.facing < 0 and dx > 40:
                        continue
                    dd = math.hypot(dx, en.y - wc.y)
                    if dd < best_d:
                        best_d = dd; tx, ty = en.x, en.y
                dx, dy = tx - wc.x, ty - wc.y
                d = math.hypot(dx, dy) or 1
                sp = 660
                p = Projectile(wc.x + wc.facing * 20, wc.y, dx / d * sp, dy / d * sp,
                               1.6, 12, col, skill["element"], wc,
                               atk * skill["power"], is_crit=False, kind="hero")
                self.projectiles.append(p)
                # empowered single-target: a second piercing projectile offset
                # perpendicular to the aim line so it hits a different arc of
                # the enemy cluster (a free second shot, not a damage multiplier).
                if empowered:
                    # perpendicular offset for the 2nd projectile's start
                    px = -dy / d * 24
                    py = dx / d * 24
                    p2 = Projectile(wc.x + wc.facing * 20 + px, wc.y + py,
                                    dx / d * sp, dy / d * sp,
                                    1.6, 12, col, skill["element"], wc,
                                    atk * skill["power"], is_crit=False, kind="hero")
                    self.projectiles.append(p2)
            else:
                # big melee arc
                arc_x = wc.x + wc.facing * 50
                # empowered melee: widen the arc radius so the nuke reaches a
                # wider cluster (a radius bump, not a damage multiplier).
                arc_r = 130 if empowered else 90
                combo_mul = 1.0 + max(0, self._combo_count) * D.COMBO_BONUS_PER
                for en in self.enemies:
                    if en.alive and math.hypot(en.x - arc_x, en.y - wc.y) < arc_r:
                        mult = self._element_mult(skill["element"], en.element)
                        dmg = int(atk * skill["power"] * mult * 1.3 * combo_mul)
                        dealt = en.take_damage(dmg, wc.x, wc.y,
                                                on_attack=self._on_enemy_event)
                        if dealt:
                            self._on_enemy_hit(en, wc, dealt, False)
                self.particles.burst(arc_x, wc.y, col, n=16, speed=240, size=6, life=0.4)
                # empowered melee: a second shockwave ring so the wider nuke
                # reads visually as a bigger impact.
                if empowered:
                    self.particles.ring(arc_x, wc.y, col, n=20, speed=360, size=6, life=0.45)
                self.camera.add_shake(5, self._shake_mul)
            audio.play("skill", 0.4)
        elif kind in ("aoe_attack", "aoe_magic"):
            # burst around the hero (or the clamped ground target — Task B2) + an
            # expanding shockwave ring. aoe_cx/aoe_cy default to the hero; a held
            # aim shifts the center to the mouse world pos (clamped to max range).
            self.particles.burst(aoe_cx, aoe_cy, col, n=30, speed=320, size=7, life=0.6, grav=0)
            self.particles.ring(aoe_cx, aoe_cy, col, n=28, speed=420, size=6, life=0.5)
            # empowered AoE: widen the radius (200 -> 260) + a second ring so
            # the burst covers a bigger cluster and reads as a bigger impact.
            aoe_r = 260 if empowered else 200
            if empowered:
                self.particles.ring(aoe_cx, aoe_cy, (255, 255, 255),
                                    n=24, speed=380, size=6, life=0.45)
            combo_mul = 1.0 + max(0, self._combo_count) * D.COMBO_BONUS_PER
            for en in self.enemies:
                if en.alive and math.hypot(en.x - aoe_cx, en.y - aoe_cy) < aoe_r:
                    mult = self._element_mult(skill["element"], en.element)
                    dmg = int(atk * skill["power"] * mult * combo_mul)
                    dealt = en.take_damage(dmg, aoe_cx, aoe_cy,
                                            on_attack=self._on_enemy_event)
                    if dealt:
                        self._on_enemy_hit(en, wc, dealt, False)
            self.camera.add_shake(8, self._shake_mul)
            self.flash = 0.2
            audio.play("skill", 0.5)
        elif kind == "heal":
            # heal active + share a bit with party
            amt = int(atk * skill["power"] * 0.8) + 30
            wc.heal(amt)
            if self.game.player.settings.get("damage_numbers", True):
                self.floats.append(FloatText(wc.x, wc.y - 30, f"+{amt}", (140, 240, 160), size=24))
            for other in self.party:
                if other and other is not wc and other.alive:
                    other.heal(amt // 2)
            self.particles.burst(wc.x, wc.y, (140, 240, 160), n=20, speed=160, size=6, life=0.5, grav=-60)
            # rising heal motes
            for _ in range(10):
                self.particles.list.append(Particle(
                    wc.x + random.uniform(-20, 20), wc.y + 20,
                    random.uniform(-10, 10), random.uniform(-90, -50),
                    0.7, (180, 255, 200), 4, -30))
            audio.play("heal", 0.5)
        elif kind in ("buff", "debuff"):
            # self buff visual — orbiting motes
            self.particles.burst(wc.x, wc.y, col, n=18, speed=180, size=5, life=0.5, grav=-80)
            audio.play("buff", 0.5)
            # actually apply the status effect (the skill dict carries buff/debuff
            # keys + potency + dur — wire them into the hero's effect list so
            # shield/atk_up/def_up/poison/etc. do something instead of just VFX)
            if skill.get("buff"):
                wc.hero.add_effect(skill["buff"], skill.get("dur", 3),
                                   skill.get("potency", 0.3))
                # a small heal for support buffs so they feel helpful immediately
                if skill["buff"] in ("shield", "def_up", "atk_up"):
                    wc.heal(20)
            if skill.get("debuff"):
                # debuffs are single-target in this real-time model — apply to the
                # nearest alive enemy in the facing arc so curse/rupture land
                nearest = None
                for en in self.enemies:
                    if not en.alive:
                        continue
                    if (en.x - wc.x) * wc.facing > 0 and math.hypot(en.x - wc.x, en.y - wc.y) < 200:
                        nearest = en
                        break
                if nearest:
                    # apply a short stun as the debuff's tangible effect (the
                    # real-time combat has no per-enemy effect list, so a brief
                    # telegraph-stun is the readable outcome)
                    nearest._react_stun = max(nearest._react_stun, 1.5)
                    # apply each debuff in the skill's debuff list (e.g.
                    # ["burn", "atk_down"]) so DoTs actually tick + stat debuffs
                    # land. DoT types (burn/bleed/poison) use the skill's
                    # dot_potency (distinct per debuff skill); stat debuffs use
                    # the generic potency. add_effect dedupes by type so
                    # re-application refreshes duration instead of double-stacking.
                    dur = skill.get("dur", 3)
                    dot_pot = skill.get("dot_potency", 0.3)
                    stat_pot = skill.get("potency", 0.3)
                    for db in skill["debuff"]:
                        pot = dot_pot if db in ("burn", "bleed", "poison") else stat_pot
                        nearest.enemy.add_effect(db, dur, pot)
                    self.particles.burst(nearest.x, nearest.y, col, n=12, speed=160, size=5, life=0.4)
        elif kind == "revive":
            # revive a downed party member at half HP; if none downed, big heal
            # on the active hero so the skill isn't wasted
            downed = [o for o in self.party if o and not o.alive]
            if downed:
                target = downed[0]
                target.alive = True
                target.hero.hp = target.hero.max_hp // 2
                target.hero.energy = D.ENERGY_START
                target.invuln_t = 0.5
                self.particles.burst(target.x, target.y, (140, 240, 160),
                                     n=30, speed=240, size=7, life=0.7, grav=-60)
                self.particles.ring(target.x, target.y, (180, 255, 200),
                                    n=24, speed=300, size=6, life=0.6)
                self.floats.append(FloatText(target.x, target.y - 40,
                                             f"REVIVED {target.hero.name}!",
                                             (140, 240, 160), size=20))
                audio.play("revive", 0.6)
            else:
                # nobody to revive — big heal on the active hero instead
                wc.heal(int(wc.hero.max_hp * 0.5))
                self.particles.burst(wc.x, wc.y, (140, 240, 160),
                                     n=24, speed=200, size=6, life=0.6, grav=-60)
                audio.play("heal", 0.5)
        elif kind == "summon":
            # spawn a temporary ally at the hero's side that auto-attacks nearby
            # enemies for `dur` seconds. A separate entity (SummonAlly) so the
            # 4-slot party is untouched. Water summon heals the party instead.
            sx = wc.x + wc.facing * 40
            sy = wc.y + 20
            ally = SummonAlly(sx, sy, skill["element"], col,
                              int(atk * skill["power"]), skill.get("dur", 6),
                              skill.get("potency", 1.0), wc)
            self._summons.append(ally)
            self.particles.burst(sx, sy, col, n=16, speed=180, size=6, life=0.5, grav=-60)
            audio.play("skill", 0.5)
        elif kind == "beam":
            # line hit-scan from hero toward the facing/aim — damage all enemies
            # along the line within `range`. Aim at the nearest enemy in the
            # facing half-plane (like the ranged attack) so the beam actually
            # hits a target, not a straight horizontal miss.
            bx = wc.x + wc.facing * 20
            by = wc.y
            ex = bx + wc.facing * skill.get("range", 420)
            ey = by
            best_d = 1e9
            for en in self.enemies:
                if not en.alive:
                    continue
                if (en.x - wc.x) * wc.facing < -40:
                    continue
                dd = math.hypot(en.x - wc.x, en.y - wc.y)
                if dd < best_d:
                    best_d = dd; ex, ey = en.x + wc.facing * 60, en.y
            combo_mul = 1.0 + max(0, self._combo_count) * D.COMBO_BONUS_PER
            for en in self.enemies:
                if not en.alive:
                    continue
                if _seg_hit(bx, by, ex, ey, en.x, en.y, en.r + 22):
                    mult = self._element_mult(skill["element"], en.element)
                    dmg = int(atk * skill["power"] * mult * combo_mul)
                    dealt = en.take_damage(dmg, wc.x, wc.y,
                                            on_attack=self._on_enemy_event)
                    if dealt:
                        self._on_enemy_hit(en, wc, dealt, False)
            # beam visual: a bright line + a sparkle at the endpoint
            self.particles.beam(bx, by, ex, ey, col)
            self.camera.add_shake(4, self._shake_mul)
            audio.play("skill", 0.5)
        elif kind == "trap":
            # place a trap on the ground at the facing that triggers when an
            # enemy steps within its radius — a delayed hazard. The trap stores
            # the summoning hero (source) so a trap kill fires the death/reward
            # path via the on_enemy_hit callback (no silent kills).
            tx = wc.x + wc.facing * 60
            ty = wc.y
            tr = Trap(tx, ty, skill["element"], col,
                      int(atk * skill["power"]), skill.get("radius", 70),
                      skill.get("dur", 8), wc)
            self._traps.append(tr)
            self.particles.burst(tx, ty, col, n=10, speed=120, size=4, life=0.4, grav=-30)
            audio.play("skill", 0.4)
        else:
            # fallback: small burst
            self.particles.burst(wc.x, wc.y, col, n=14, speed=200, size=5, life=0.4)
            audio.play("skill", 0.4)
        # variable hit-stop: heavier skills (higher cost tier) freeze the screen
        # longer than a basic attack so a cost-5 nuke lands with more weight than
        # a cost-2 poke. Capped at 0.4s; halved under reduce_motion. Uses max()
        # so multi-hit AoE doesn't stack the freeze.
        _hs = min(0.4, 0.06 + skill.get("cost", 2) * 0.03)
        if self._reduce_motion:
            _hs *= 0.5
        self.hit_stop = max(self.hit_stop, _hs)
        # energy gain for using a skill (small); flow-state passive + light
        # elemental resonance boost it. Routed through wc.add_energy so the
        # resonance (energy_regen) and the passive (energy_gen) add rather than
        # both multiplying the base (the old inline code only applied the
        # passive; add_energy now sums them).
        gain = D.ENERGY_GAIN_DEAL
        wc.add_energy(gain)

    def _do_ultimate(self, wc):
        # Task B3: casting an ult interrupts the AA (same as a skill cast).
        wc.aa_target = None
        if not wc.can_ultimate():
            # soft denied buzz so a rejected ult isn't silent
            audio.play("weak", 0.15)
            return
        skill = D.SKILLS_DB[wc.hero.ultimate]
        col = D.ELEMENT_COLORS.get(skill["element"], ((255, 255, 200),))[0]
        wc.spend_ultimate()
        wc._last_combat_t = 0
        a = wc.hero
        atk = wc.effective_atk()
        kind = skill["type"]
        # combo climax: if the ult is empowered (armed at combo milestone 10,
        # which coincides with COMBO_MAX), apply a free debuff to every enemy
        # hit by the ult — a status, not raw damage, so it doesn't double-dip
        # with the combo multiplier. Consumed on use; cleared on a party swap.
        empowered = self._ult_empowered
        if empowered:
            self._ult_empowered = False
        self.flash = 0.5
        if self._reduce_motion:
            self.flash *= 0.4
        self.camera.add_shake(16, self._shake_mul)
        # ultimates are the heaviest hit — a long hit-stop that scales with the
        # ult's cost tier (an ult with cost 8-9 -> 0.30-0.33s, capped at 0.4).
        # Halved under reduce_motion; uses max() so AoE doesn't stack the freeze.
        _hs = min(0.4, 0.06 + skill.get("cost", 8) * 0.03)
        if self._reduce_motion:
            _hs *= 0.5
        self.hit_stop = max(self.hit_stop, _hs)
        combo_mul = 1.0 + max(0, self._combo_count) * D.COMBO_BONUS_PER
        # total damage dealt by the ultimate — used by the per-hero variant's
        # self_heal effect (a fraction of damage dealt). Heal ults deal 0 damage
        # so their variants never pick self_heal (see ULTIMATE_VARIANTS).
        total_dmg = 0
        # heal ults (e.g. light_hymn) — the skill dict may carry heal=True even
        # though its type is "ultimate"; route to the heal branch so it actually
        # heals the party instead of falling through to the forward-beam else.
        if skill.get("heal") or kind == "heal":
            amt = a.max_hp
            for other in self.party:
                if other and other.alive:
                    other.heal(amt)
            self.particles.burst(wc.x, wc.y, (140, 240, 160), n=40, speed=260, size=8, life=0.8, grav=-80)
            self.particles.ring(wc.x, wc.y, (180, 255, 200), n=36, speed=300, size=6, life=0.7)
            audio.play("heal", 0.6)
        elif kind in ("aoe_attack", "aoe_magic"):
            # huge burst + double shockwave ring
            self.particles.burst(wc.x, wc.y, col, n=60, speed=420, size=9, life=0.9, grav=0)
            self.particles.ring(wc.x, wc.y, col, n=40, speed=560, size=7, life=0.6)
            self.particles.ring(wc.x, wc.y, (255, 255, 255), n=32, speed=360, size=5, life=0.5)
            for en in self.enemies:
                if en.alive and math.hypot(en.x - wc.x, en.y - wc.y) < 320:
                    mult = self._element_mult(skill["element"], en.element)
                    dmg = int(atk * skill["power"] * mult * 1.4 * combo_mul)
                    dealt = en.take_damage(dmg, wc.x, wc.y,
                                            on_attack=self._on_enemy_event)
                    if dealt:
                        total_dmg += dealt
                        self._on_enemy_hit(en, wc, dealt, True)
        else:
            # big forward beam — a streaking column of particles in the facing dir
            arc_x = wc.x + wc.facing * 60
            for step in range(6):
                bx = wc.x + wc.facing * (40 + step * 40)
                self.particles.burst(bx, wc.y, col, n=10, speed=120, size=7, life=0.4, grav=0)
            self.particles.ring(arc_x, wc.y, col, n=30, speed=400, size=7, life=0.5)
            for en in self.enemies:
                if en.alive and (en.x - wc.x) * wc.facing > 0 and math.hypot(en.x - wc.x, en.y - wc.y) < 300:
                    mult = self._element_mult(skill["element"], en.element)
                    dmg = int(atk * skill["power"] * mult * 1.5 * combo_mul)
                    dealt = en.take_damage(dmg, wc.x, wc.y,
                                            on_attack=self._on_enemy_event)
                    if dealt:
                        total_dmg += dealt
                        self._on_enemy_hit(en, wc, dealt, True)
        # --- B5: per-hero ultimate variant — a secondary effect on top of the
        # base ultimate. Read the variant (if any) and apply its extra. Only the
        # one-liner effects are wired (burn/freeze deferred until the DoT engine).
        # --- C5: empowered-ult free debuff — apply a short atk_down to every
        # enemy the ult actually hit (collected in _ult_hit_targets above) so
        # the climax is a status payoff, not a second damage roll. Skipped for
        # heal ults (they hit no enemies).
        if empowered:
            for en in self.enemies:
                if not en.alive:
                    continue
                # only enemies within the ult's effect radius (320 for AoE, 300
                # for the forward beam) — matches the damage loops above.
                if math.hypot(en.x - wc.x, en.y - wc.y) < 320:
                    en.enemy.add_effect("atk_down", 4, 0.3)
                    self.particles.burst(en.x, en.y, (255, 120, 180),
                                         n=10, speed=160, size=5, life=0.5)
            self.floats.append(FloatText(wc.x, wc.y - 50, "EMPOWERED!",
                                         (255, 180, 240), size=22))
        var = D.ULTIMATE_VARIANTS.get(wc.hero.id)
        if var:
            eff = var["extra_effect"]
            pot = var.get("potency", 0)
            if eff == "self_heal" and total_dmg > 0:
                # heal the caster a modest fraction of the damage dealt
                wc.heal(int(total_dmg * pot))
                self.particles.burst(wc.x, wc.y, (140, 240, 160),
                                     n=14, speed=160, size=5, life=0.5, grav=-60)
            elif eff == "party_shield":
                # shield each alive party member (potency = shield strength)
                for other in self.party:
                    if other and other.alive:
                        other.hero.add_effect("shield", 3, pot)
                self.particles.ring(wc.x, wc.y, (180, 220, 255),
                                    n=24, speed=260, size=5, life=0.5)
            elif eff == "knockback":
                # push enemies back away from the hero (potency = push speed)
                for en in self.enemies:
                    if not en.alive:
                        continue
                    if math.hypot(en.x - wc.x, en.y - wc.y) < 360:
                        dx = en.x - wc.x
                        dy = en.y - wc.y
                        d = math.hypot(dx, dy) or 1
                        en.kb_x = dx / d * pot
                        en.kb_y = dy / d * pot
            elif eff == "energy_refund":
                # refund a modest fraction of the active hero's max energy
                wc.add_energy(int(wc.hero.max_energy * pot))
            elif eff == "atk_buff_self":
                # buff the active hero's ATK for a few seconds
                wc.hero.add_effect("atk_up", 4, pot)
                self.particles.burst(wc.x, wc.y, (255, 200, 120),
                                     n=16, speed=180, size=5, life=0.5, grav=-40)
        # constellation ult_extra perks — applied after the ult's main effect so
        # the perk layer adds on top of the base ult. Variants shipped now:
        #   self_heal  - heal the active hero for val * max_hp
        #   party_buff - a temporary atk_up on each party member (3s, val potency)
        #   atk_buff   - a temporary atk_up on the active hero (3s, val potency)
        # Burn/freeze DoT variants are wired through the DoT engine (tick_effects
        # is now driven in the real-time world loop — see the enemy update loop).
        ux = getattr(a, "ult_extra", {}) or {}
        if ux:
            if ux.get("self_heal"):
                heal_amt = int(a.max_hp * ux["self_heal"])
                wc.heal(heal_amt)
                if self.game.player.settings.get("damage_numbers", True):
                    self.floats.append(FloatText(wc.x, wc.y - 30, f"+{heal_amt}",
                                                 (140, 240, 160), size=22))
            if ux.get("party_buff"):
                pot = ux["party_buff"]
                for other in self.party:
                    if other and other.alive:
                        other.hero.add_effect("atk_up", 3, pot)
            if ux.get("atk_buff"):
                pot = ux["atk_buff"]
                wc.hero.add_effect("atk_up", 3, pot)
        audio.play("ultimate", 0.6)

    def _on_enemy_hit(self, en, wc, dmg, is_crit):
        # combo system: each hit within the combo window stacks a damage
        # multiplier (capped at COMBO_MAX) and a visible combo counter. The
        # window refreshes on every hit; the counter resets when it expires.
        # The multiplier itself is applied at the damage source (see _do_attack /
        # _do_skill / _do_ultimate) using the pre-increment count, so the first
        # hit of a streak gets 0% bonus and the ramp builds from there.
        self._combo_count = min(D.COMBO_MAX, self._combo_count + 1)
        self._combo_t = self._combo_window
        # combo climax milestones: arm the next skill/ult with a bonus effect.
        # The skill milestone (5) arms _skill_empowered; the ult milestone (10)
        # coincides with COMBO_MAX and arms _ult_empowered. Re-hitting the
        # milestone while already empowered is a no-op (the flag is set, not
        # toggled) so the player keeps the empowerment until they spend it.
        if self._combo_count == D.COMBO_MILESTONE_SKILL:
            self._skill_empowered = True
        if self._combo_count == D.COMBO_MILESTONE_ULT:
            self._ult_empowered = True
        # max-combo one-shot celebration: the first time the streak hits
        # COMBO_MAX in this window, fire a chord + a brief hit-stop. Gated by
        # _combo_max_celebrated so it only fires once per window (reset on
        # window expiry below). The hit-stop uses max() so it doesn't stack
        # with a crit's freeze on the same frame.
        if self._combo_count >= D.COMBO_MAX and not self._combo_max_celebrated:
            self._combo_max_celebrated = True
            audio.play("combo_max", 0.5)
            _hs = 0.18
            if self._reduce_motion:
                _hs *= 0.5
            self.hit_stop = max(self.hit_stop, _hs)
            self.camera.add_shake(8, self._shake_mul)
            self.particles.ring(wc.x, wc.y, (255, 220, 120),
                                n=32, speed=420, size=7, life=0.6)
        # per-enemy weakness: a hero whose element matches the enemy's listed
        # weakness deals +50% (the Genshin-style break). Surfaced as a "WEAK!"
        # tag on the float so the player sees the counter-element pay off.
        weak_hit = bool(getattr(en.enemy, "weakness", None)) and en.enemy.weakness == wc.element
        if self.game.player.settings.get("damage_numbers", True):
            col = (255, 220, 80) if is_crit else (255, 255, 255)
            # crits get a "!" suffix and a bigger font
            label = f"{dmg}!" if is_crit else str(dmg)
            self.floats.append(FloatText(en.x, en.y - 20, label, col,
                                         size=30 if is_crit else 20))
            if weak_hit:
                self.floats.append(FloatText(en.x, en.y - 8, "WEAK!",
                                            (255, 180, 80), size=16))
        el_col = D.ELEMENT_COLORS.get(wc.element, ((200, 200, 200),))[0]
        self.particles.burst(en.x, en.y, el_col, n=8, speed=200, size=4, life=0.3)
        # wet effect: when the current map's weather is rain (or storm), the
        # wet multiplier (D.WET_EFFECT) extends the reaction window (+50%) and
        # scales the reaction bonus (water x1.2, fire x0.8). Gated to the
        # reaction window ONLY — the wet effect extends the reaction window,
        # not the Freeze stun duration (en._react_stun stays at its base 1.5s,
        # not 1.5 * 1.5, so the wet effect doesn't stack with the Freeze stun).
        wet = self._weather in ("rain", "storm")
        # elemental reaction: if this hit's element differs from the last one
        # that hit this enemy within the reaction window, trigger a reaction
        # (bonus damage + a named float + a distinct particle). This rewards
        # swapping the active hero mid-fight (the Genshin-style 4-hero party).
        rxn = D.reaction_for(en._last_element_hit, wc.element) if en._last_element_hit else None
        if rxn and en._element_hit_t > 0:
            name, bonus_frac, effect, rcol = rxn
            # wet scales the reaction bonus: water +20%, fire -20% (the wet
            # effect amplifies water reactions and dampens fire ones)
            if wet:
                if wc.element == "water":
                    bonus_frac *= D.WET_EFFECT["water"]
                elif wc.element == "fire":
                    bonus_frac *= D.WET_EFFECT["fire"]
            bonus = int(dmg * bonus_frac)
            if bonus > 0:
                en.enemy.hp -= bonus
                if en.enemy.hp <= 0:
                    en.enemy.hp = 0
                    en.alive = False
            # a reaction-named float above the target so the player sees the proc
            self.floats.append(FloatText(en.x, en.y - 44, name.upper() + "!",
                                         rcol, size=24))
            if effect == "aoe":
                # steam: bonus damage to nearby enemies + a cloud burst
                for other in self.enemies:
                    if other is en or not other.alive:
                        continue
                    if math.hypot(other.x - en.x, other.y - en.y) < 120:
                        odmg = int(bonus * 0.5)
                        other.enemy.hp -= odmg
                        if other.enemy.hp <= 0:
                            other.enemy.hp = 0
                            other.alive = False
                self.particles.burst(en.x, en.y, rcol, n=28, speed=260, size=7, life=0.6)
                self.particles.ring(en.x, en.y, rcol, n=22, speed=320, size=6, life=0.5)
            elif effect == "stun":
                # freeze: a brief stun + an ice shard burst. The wet effect
                # does NOT extend the stun duration (only the reaction window).
                en._react_stun = 1.5
                self.particles.burst(en.x, en.y, rcol, n=24, speed=180, size=6, life=0.7, grav=-40)
            else:  # burst
                self.particles.burst(en.x, en.y, rcol, n=30, speed=340, size=7, life=0.6)
                self.particles.ring(en.x, en.y, rcol, n=20, speed=380, size=6, life=0.5)
            self.camera.add_shake(6, self._shake_mul)
            audio.play("react_" + name.lower(), 0.45)
        # record this hit's element + refresh the reaction window for the next hit
        en._last_element_hit = wc.element
        # wet extends the reaction window (+50%) so the next element swap has a
        # longer window to trigger a reaction in the rain (the wet effect).
        en._element_hit_t = D.REACTION_WINDOW * (D.WET_EFFECT["reaction_window"] if wet else 1.0)
        if is_crit:
            # crits get a sharper white spark + a small ring + bigger hit-stop
            self.particles.ring(en.x, en.y, (255, 240, 180), n=14, speed=300, size=4, life=0.28)
            self.particles.spark(en.x, en.y, (255, 255, 255), n=6, speed=260, size=4, life=0.22)
            # crit hit-stop: base 0.11 + a small extra for combo tier >=2 so a
            # streak of crits feels heavier. Halved under reduce_motion; uses
            # max() so multi-hit AoE doesn't stack.
            _hs = 0.11 + (0.03 if self._combo_count >= 2 else 0.0)
            if self._reduce_motion:
                _hs *= 0.5
            self.hit_stop = max(self.hit_stop, _hs)
            self.camera.add_shake(5, self._shake_mul)
            audio.play("crit", 0.4)
        else:
            self.hit_stop = max(self.hit_stop, 0.05)
            self.camera.add_shake(2, self._shake_mul)
            # pitch the hit sound up every 5 combo so a streak feels escalating.
            # On a tier increase also fire the combo stinger (an ascending
            # arpeggio cached as combo_1/combo_2) so the milestone is heard,
            # not just the pitched hit. The stinger only plays on a tier
            # increase (not every hit at that tier) so it doesn't spam.
            tier = self._combo_count // 5
            if tier > self._combo_pitch_tier:
                self._combo_pitch_tier = tier
                if tier in (1, 2):
                    audio.play("combo_1" if tier == 1 else "combo_2", 0.3)
                audio.play("crit", 0.18)
            else:
                audio.play("hit", 0.2)
        if not en.alive:
            self._on_enemy_death(en, wc)

    def _on_enemy_death(self, en, wc):
        # drops: xp (instant party-wide), gold/shards/potion/equipment (visible
        # ground drops the player walks over — Task C2). XP stays instant because
        # it's party-wide and shouldn't require walking over a sprite. The
        # gold/shard/potion/equipment rewards spawn as drop entities on the
        # ground at the enemy's pos; the pickup/magnet/expire logic is in update.
        p = self.game.player
        hero = wc.hero
        # xp to whole party (with level-up pop) — stays instant (not a drop)
        xp = en.enemy.xp
        for other in self.party:
            if other and other.alive:
                before = other.hero.level
                other.hero.gain_xp(xp)
                if other.hero.level > before:
                    self._on_hero_levelup(other)
        # gold — spawn as a ground drop (visible loot). Bosses drop more (the
        # enemy.gold is already level-scaled in entities.py). The gold_earned
        # stat is tallied at pickup (in _pickup_drop), not here — the stat
        # tracks gold actually collected, not gold spawned on the ground.
        gold = en.enemy.gold
        if gold > 0:
            self._spawn_drop(en.x, en.y, "gold", gold)
        # shards from bosses / elites — bosses scale by row so deeper bosses
        # are worth more (row0=3 ... row4=19); elites rarely drop 1. Non-boss
        # shard drop rate is 15% (was 8%, near-zero sustained shard income).
        # Spawned as a ground drop (visible loot) instead of straight to inventory.
        shards = 0
        if en.is_boss:
            shards = 3 + self.r * 4
        elif random.random() < 0.15:
            shards = 1
        if shards:
            self._spawn_drop(en.x, en.y, "shard", shards)
        # potion drop — 12% chance, spawned as a ground drop (visible loot).
        if random.random() < 0.12:
            self._spawn_drop(en.x, en.y, "hp_potion", 1)
        # equipment drop from bosses — only on the first clear of the cell (gated
        # by ow_bosses_cleared) so the drop can't be farm-grounded; weight the
        # rarity by row so deeper bosses drop better gear. Spawned as a ground
        # drop (visible loot) so the player walks over to pick it up.
        cid = WD.cell_id(self.c, self.r)
        first_clear = en.is_boss and cid not in set(p.ow_bosses_cleared)
        if first_clear and random.random() < 0.6:
            rar = "SSR" if (self.r >= 3 and random.random() < 0.5) else "SR"
            pool = [k for k, v in D.EQUIPMENT_DB.items() if v["rarity"] == rar]
            if pool:
                eid = random.choice(pool)
                self._spawn_drop(en.x, en.y, "equipment", eid)
        # boss cleared -> mark + row-scaled bonus gems (only the first clear per
        # cell pays out, so bosses can't be farm-grounded for infinite gems).
        if en.is_boss:
            cleared = set(p.ow_bosses_cleared)
            cid = WD.cell_id(self.c, self.r)
            first_clear = cid not in cleared
            boss_gem = (20 + self.r * 50) if first_clear else 10
            p.gems += boss_gem
            p.stats["gems_earned"] = p.stats.get("gems_earned", 0) + boss_gem
            p.stats["bosses_defeated"] = p.stats.get("bosses_defeated", 0) + 1
            if first_clear:
                p.ow_bosses_cleared = sorted(cleared | {cid})
            self.set_message(f"Boss defeated! +{boss_gem} gems, +{shards} shards")
            # defeat celebration: a long hit-stop, a big flash, a victory burst,
            # and a "BOSS DEFEATED" banner with the boss name for ~2.5s
            self.hit_stop = max(self.hit_stop, 0.5)
            self.flash = 0.6
            if self._reduce_motion:
                self.flash *= 0.4
            self.particles.burst(en.x, en.y, (255, 220, 120), n=80, speed=420, size=9, life=1.0, grav=0)
            self.particles.ring(en.x, en.y, (255, 240, 160), n=40, speed=560, size=8, life=0.8)
            self.camera.add_shake(14, self._shake_mul)
            audio.play("victory", 0.7)
            self._boss_defeat_name = en.enemy.name
            self._boss_defeat_t = 2.5
            # Aetheric Cycle: when the FINAL boss (the Demon King at 9,4) is
            # defeated for the first time this cycle, show a "World Ascended!"
            # banner so the player knows they can now Ascend the World from
            # the title screen to start NG+. The cell is (9,4) and the boss id
            # for row 4 is "demonking" — check both so a non-final boss on the
            # same row (none currently, but defensive) can't trigger this.
            if (WD.is_boss_cell(self.c, self.r) and self.c == WD.GRID_W - 1
                    and self.r == WD.GRID_H - 1
                    and getattr(en, "id", None) == "demonking"):
                self._ascend_banner_t = 3.0
                self.set_message(
                    "World Ascended! Return to the title to start a new cycle.",
                    4.0)
        # particles
        self.particles.burst(en.x, en.y, (200, 80, 80), n=20, speed=240, size=6, life=0.5)
        # stats + quests + achievements
        p.stats["enemies_defeated"] = p.stats.get("enemies_defeated", 0) + 1
        p.quest_progress("defeat_enemies", 1)
        p.quest_progress("win_battles", 1)
        # surface newly-unlocked achievements as real-time toasts (the return
        # value was discarded, so unlocks were invisible until the Records tab)
        for aid in p.check_achievements():
            ach = D.ACHIEVEMENTS.get(aid, {})
            self.set_message(
                f"Achievement: {ach.get('name', '?')}! +{ach.get('reward_gems', 0)} gems",
                3.0)
        # save hero levels back
        for other in self.party:
            if other:
                hid = other.hero.id
                if hid in p.owned:
                    p.owned[hid]["level"] = other.hero.level
                    p.owned[hid]["xp"] = other.hero.xp
        p.save()
        # signature passive: stacking_atk (dict-lookup dispatch — +val ATK per
        # kill, decaying out of combat). The stack is read in effective_atk and
        # decays in update; here we just increment + reset the decay timer.
        _sig = _SIG_ON_KILL.get(wc._signature_kind)
        if _sig:
            _sig(self, wc)

    def _spawn_drop(self, x, y, kind, value, count=1):
        """Spawn one (or `count`) ground loot drop(s) at (x, y). Each drop is a
        visible sprite the player walks over to collect (Task C2). A small random
        offset per drop so a multi-drop doesn't stack on one pixel (reads as a
        scatter of loot, not a single sprite). Kinds: gold / hp_potion / shard /
        equipment — each rendered by load_drop(kind) (Task A4). `value` is the
        amount (gold count, shard count, 1 for potion, the equipment id for
        equipment). Capped at a sane per-call count so a huge gold value doesn't
        spawn hundreds of sprites — gold aggregates into one drop with the total
        value, the other kinds are 1-drop-per-call."""
        if kind == "gold":
            # gold aggregates into one drop carrying the total value (a 200g
            # drop is one coin sprite worth 200, not 200 coin sprites).
            self.drops.append({"x": float(x), "y": float(y),
                               "kind": "gold", "value": int(value),
                               "t": 0.0, "sprite_id": "gold"})
            return
        n = max(1, min(int(count), 4))  # cap so a stray high count doesn't flood
        for _ in range(n):
            ox = x + random.uniform(-10, 10)
            oy = y + random.uniform(-10, 10)
            self.drops.append({"x": float(ox), "y": float(oy),
                               "kind": kind, "value": value,
                               "t": 0.0, "sprite_id": kind})

    def _pickup_drop(self, drop, wc):
        """Collect a ground loot drop: add its value to the player's inventory
        by kind, a gold sparkle burst, and remove it from self.drops. Called
        from the walk-over check in update when the active hero is within the
        pickup radius. gold -> player.gold; hp_potion -> inventory; shard ->
        player.shards; equipment -> equipment_inv (via add_equipment)."""
        p = self.game.player
        kind = drop["kind"]
        value = drop["value"]
        if kind == "gold":
            p.gold += value
            p.stats["gold_earned"] = p.stats.get("gold_earned", 0) + value
            col = (255, 220, 120)
        elif kind == "hp_potion":
            p.add_item("hp_potion", 1)
            col = (140, 240, 160)
        elif kind == "shard":
            p.shards += value
            col = (200, 160, 255)
        elif kind == "equipment":
            p.add_equipment(value)
            col = (255, 200, 120)
        else:
            return  # unknown kind — don't collect (defensive)
        # a gold sparkle burst so the pickup reads as loot collected, not a
        # silent vanish. Reuses the chest-open burst shape (a burst + a ring).
        self.particles.burst(drop["x"], drop["y"], col, n=8, speed=180, size=5, life=0.4)
        self.floats.append(FloatText(drop["x"], drop["y"] - 18,
                                     f"+{value}{'g' if kind == 'gold' else ''}",
                                     col, size=16))
        audio.play("menu_click", 0.2)

    def _on_hero_levelup(self, wc):
        """Celebrate a level-up with a burst + a banner float."""
        h = wc.hero
        self.floats.append(FloatText(wc.x, wc.y - 50, f"LV {h.level}!", (255, 230, 120), size=26))
        self.particles.burst(wc.x, wc.y, (255, 220, 120), n=24, speed=220, size=6, life=0.6, grav=-60)
        # the ascending arpeggio fits a milestone better than the generic buff hum
        audio.play("revive", 0.5)

    def _hero_damaged(self, wc, dmg):
        if self.game.player.settings.get("damage_numbers", True):
            self.floats.append(FloatText(wc.x, wc.y - 30, str(dmg), (255, 100, 100), size=22))
        shake_mul = self.game.player.settings.get("screen_shake", 1.0)
        self.camera.add_shake(4 * shake_mul)
        self.flash = 0.15
        if self.game.player.settings.get("reduce_motion", False):
            self.flash *= 0.4
        audio.play("hit", 0.3)
        if not wc.alive:
            self._on_hero_down()

    def _on_perfect_dodge(self, wc):
        """A perfect dodge: the hero dashed through an attack in the reward
        window. Negate the hit, slow time briefly, a white ring + a 'PERFECT!'
        float, and grant a 2s 1.5x damage buff (set in take_damage)."""
        self.hit_stop = max(self.hit_stop, 0.15)
        self.camera.add_shake(3, self._shake_mul)
        self.particles.ring(wc.x, wc.y, (255, 255, 255), n=24, speed=360, size=5, life=0.4)
        self.particles.spark(wc.x, wc.y, (255, 255, 255), n=10, speed=300, size=4, life=0.3)
        if self.game.player.settings.get("damage_numbers", True):
            self.floats.append(FloatText(wc.x, wc.y - 40, "PERFECT!", (255, 240, 180), size=22))
        audio.play("perfect", 0.5)

    def _on_hero_revive(self, wc):
        """A signature passive (revive_once) brought the hero back from a lethal
        blow. Celebrate with a bright burst + a 'REVIVE!' float so the player
        sees the proc. The brief invuln window is already set in take_damage
        (invuln_t = 1.0); here we just fire the VFX so the proc is visible."""
        self.floats.append(FloatText(wc.x, wc.y - 50, "REVIVE!", (255, 240, 120), size=26))
        self.particles.burst(wc.x, wc.y, (255, 240, 160), n=30, speed=300, size=7, life=0.8, grav=-40)
        self.particles.ring(wc.x, wc.y, (255, 240, 120), n=24, speed=360, size=6, life=0.5)
        audio.play("revive", 0.6)
        self.camera.add_shake(6, self._shake_mul)

    def _on_hero_down(self):
        # try to switch to a living hero
        for i, wc in enumerate(self.party):
            if wc and wc.alive:
                self.active = i
                self.swap_flash = 0.3
                self.set_message(f"{wc.hero.name} is up!")
                # a hero-downed sting so the auto-swap isn't silent (only the
                # full-party-wipe case below plays 'defeat')
                audio.play("weak", 0.4)
                return
        # all down -> respawn at hub
        self.set_message("Party defeated... reviving at hub")
        audio.play("defeat", 0.6)
        # revive all at half HP + clear all transient combat state so a hero
        # who died mid-knockback / mid-i-frames doesn't re-enter the hub with
        # stale velocity or no protection. Give a brief swap-in invuln window.
        for wc in self.party:
            if wc:
                wc.alive = True
                wc.hero.hp = wc.hero.max_hp // 2
                wc.hero.energy = D.ENERGY_START
                wc.kb_x = wc.kb_y = 0.0
                wc.iframes = 0.5
                wc.invuln_t = 0.5
                wc.hit_flash = 0.0
                wc.dash_t = 0.0
                wc.dash_cd = 0.0
                wc._shield_hp = 0.0
                wc._perfect_dodge_t = 0.0
                wc._dmg_buff_t = 0.0
                # C6: reset revive_once on a full-party-wipe revive so the next
                # combat has revive available again (mirrors the _build_party reset).
                wc._revive_used = False
                for i in range(3):
                    wc.skill_cd[i] = 0.0
                wc.ult_cd = 0.0
        # gold penalty scaled by progress so late-game deaths matter (was a flat
        # 50, trivial at row 3+ where one kill yields ~180-260 gold), plus a
        # small gem/shard sting so dying isn't free.
        penalty_gold = 50 + self.r * 30
        self.game.player.gold = max(0, self.game.player.gold - penalty_gold)
        self.game.player.gems = max(0, self.game.player.gems - 10)
        self.game.player.shards = max(0, self.game.player.shards - 2)
        self.teleport_to(0, 0)

    # -----------------------------------------------------------------
    # Switching (Genshin-style: 1-4 swap the active hero in-place)
    # -----------------------------------------------------------------
    def _switch(self, idx):
        if idx >= len(self.party) or self.party[idx] is None:
            return
        if idx == self.active:
            return
        if not self.party[idx].alive:
            return
        old = self.party[self.active]
        new = self.party[idx]
        # carry position + facing (the new hero materializes where the old one stood)
        new.x, new.y = old.x, old.y
        new.vx, new.vy = 0, 0
        new.facing = old.facing
        # brief swap-in i-frames so the swap can't get you killed on entry
        new.iframes = 0.4
        new.invuln_t = 0.3
        self.active = idx
        self.swap_flash = 0.35
        # element-tinted swap burst (outgoing) + ring (incoming)
        el_col = D.ELEMENT_COLORS.get(new.element, ((180, 220, 255),))[0]
        self.particles.burst(old.x, old.y, (180, 220, 255), n=18, speed=240, size=5, life=0.4)
        self.particles.burst(new.x, new.y, el_col, n=24, speed=300, size=6, life=0.5, grav=-40)
        self.camera.add_shake(2)
        # a party swap is a combat action (elemental-reaction setup + i-frames),
        # not a menu click — play the per-element leitmotif so each of the 5
        # elements has its own identity on swap (Genshin-style), with a quieter
        # skill whoosh layered under the motif so the swap still reads as a
        # combat action. A 0.25s spam guard keeps a frantic 1/2/3/4 mash from
        # stacking 4 stings on top of each other (the motif is skipped, not the
        # swap itself — the i-frames/resonances still fire).
        now = time.time()
        if now - self._last_swap_sound_t >= 0.25:
            audio.play("leit_" + new.element, 0.4)
            audio.play("skill", 0.15)
            self._last_swap_sound_t = now
        # combo climax: clear the empowered flags on a swap so a player can't
        # bank a milestone bonus on one hero and spend it on another. The combo
        # counter itself stays (the streak is a party-wide resource), but the
        # finisher must be spent by the hero who earned it.
        self._skill_empowered = False
        self._ult_empowered = False
        # clear hold-to-aim state on a swap (Task B2) so an aim started on the
        # outgoing hero doesn't carry to the incoming hero (the new hero's skill
        # idx may map to a different skill/category).
        self._aim_skill = None
        self._aim_held_key = None
        self._aim_t = 0.0
        # clear AA targets on a swap (Task B3): the outgoing hero's AA target
        # belongs to it (the new hero didn't pick it), and the incoming hero's
        # stale aa_target (if any) shouldn't fire on entry.
        old.aa_target = None
        new.aa_target = None
        # recompute elemental resonances — the active buffs track the live party,
        # so swapping in a 2nd hero of an element enables its resonance live.
        self._compute_resonances()

    # -----------------------------------------------------------------
    # Update
    # -----------------------------------------------------------------
    def update(self, dt, events):
        # hit-stop pauses world sim but not input
        if self.hit_stop > 0:
            self.hit_stop -= dt
            sim_dt = 0
        else:
            sim_dt = dt
        # refresh the cached settings snapshot for this frame
        s = self.game.player.settings
        self._shake_mul = s.get("screen_shake", 1.0)
        self._reduce_motion = s.get("reduce_motion", False)
        if self._reduce_motion:
            self._shake_mul = 0.0
        # apply the particle-quality setting live so the Display slider works
        self.particles.quality = max(0.1, float(s.get("particle_quality", 1.0)))

        # overlays consume input
        if self.teleport:
            self.teleport.update(dt, events, self.teleport_to, lambda: setattr(self, "teleport", None))
            self._draw_tick(dt)
            return
        if self.evolve:
            self.evolve.update(dt, events, lambda: setattr(self, "evolve", None))
            self._draw_tick(dt)
            return
        if self.pause:
            self.pause.update(dt, events,
                              on_resume=lambda: setattr(self, "pause", None),
                              on_gacha=lambda: self.game.goto("gacha"),
                              on_shop=lambda: self.game.goto("shop"),
                              on_inventory=lambda: self.game.goto("inventory"),
                              on_quit=self._quit_to_title,
                              on_evolve=lambda: setattr(self, "evolve", EvolveOverlay(self.game)))
            self._draw_tick(dt)
            return

        # input
        keys = pygame.key.get_pressed()
        ix = (1 if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0) - \
             (1 if keys[pygame.K_a] or keys[pygame.K_LEFT] else 0)
        iy = (1 if keys[pygame.K_s] or keys[pygame.K_DOWN] else 0) - \
             (1 if keys[pygame.K_w] or keys[pygame.K_UP] else 0)
        self.input_dir = (ix, iy)
        want_dash = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        wc = self.party[self.active]
        # LoL-style auto-attack (Task B3): if an AA target is set, drive the AA
        # BEFORE the wc.update so the synthesized move-toward-target input + the
        # auto-fire run in the same frame. If the target is dead/None, clear it.
        # This runs before wc.update so the AA-driven move_target / facing is
        # picked up by the movement code in the same frame (no 1-frame lag).
        if wc and wc.alive and wc.aa_target is not None:
            if not wc.aa_target.alive:
                wc.aa_target = None
            else:
                d = math.hypot(wc.aa_target.x - wc.x, wc.aa_target.y - wc.y)
                if d < D.AA_RANGE:
                    # in range: face the target + auto-fire at the AA cd (reuse
                    # wc.atk_cd so the AA + the manual J attack share a cd). Clear
                    # any stale move_target so the hero stops + attacks (otherwise
                    # wc.update keeps walking toward the enemy's last-frame pos).
                    wc.facing = 1 if wc.aa_target.x > wc.x else -1
                    wc.move_target = None
                    if wc.atk_cd <= 0:
                        self._do_attack(wc, target=wc.aa_target)
                else:
                    # out of range: walk toward the target (the existing
                    # move_target auto-walk in wc.update handles the pathing).
                    wc.move_target = (wc.aa_target.x, wc.aa_target.y)
                    wc.move_target_t = 0.0
                    wc._last_mt_dist = 0.0
                    wc._mt_stall_t = 0.0
        if wc and wc.alive:
            wc.update(sim_dt, self.input_dir, self._map_data["obstacles"], want_dash)

        # edge transition check — suppressed while a rift is active (the exits
        # are sealed: the player must clear the wave before they can leave).
        if wc and not self._rift_active:
            if wc.x < 8:
                self._transition("left"); return
            elif wc.x > WD.MAP_W - 8:
                self._transition("right"); return
            elif wc.y < 8:
                self._transition("top"); return
            elif wc.y > WD.MAP_H - 8:
                self._transition("bottom"); return

        # hidden rift: walking into the rift tile seals the exits + spawns the
        # wave (only the first time this visit — _rift_done blocks a re-trigger
        # after the wave is cleared). The rift is the secret tuple from gen_map.
        if wc and self._rift_secret is not None and not self._rift_done and not self._rift_active:
            rx, ry, r_lvl, r_size = self._rift_secret
            if math.hypot(wc.x - rx, wc.y - ry) < wc.r + 24:
                self._enter_rift()

        # treasure chest pickup: the active hero opens a chest by walking over it
        if wc:
            for ch in self.chests:
                if ch["opened"]:
                    continue
                if math.hypot(wc.x - ch["x"], wc.y - ch["y"]) < wc.r + 22:
                    self._open_chest(ch, wc)
                    break

        # ground loot drops (Task C2): magnet + pickup. The active hero pulls
        # nearby drops toward them within the magnet radius (80px) and collects
        # them within the pickup radius (40px). Collecting adds the drop's value
        # to the inventory by kind (gold/hp_potion/shard/equipment) + a gold
        # sparkle burst (see _pickup_drop). Iterate over a copy so we can mutate
        # self.drops in place on pickup (the list comp filters the collected
        # ones out at the end so we don't skip a drop after a mid-loop removal).
        if wc and self.drops:
            picked = []
            for d in self.drops:
                dx = wc.x - d["x"]
                dy = wc.y - d["y"]
                dist = math.hypot(dx, dy)
                if dist < 40:
                    # within pickup radius — collect (add to inventory + sparkle)
                    self._pickup_drop(d, wc)
                    picked.append(d)
                elif dist < 80:
                    # within magnet radius — pull toward the hero (not collect).
                    # The pull is a fraction of the distance per frame so the
                    # drop accelerates as it gets closer (reads as a magnet).
                    pull = min(1.0, sim_dt * 8)
                    d["x"] += dx * pull
                    d["y"] += dy * pull
            if picked:
                self.drops = [d for d in self.drops if d not in picked]

        # events: attacks, skills, ult, switch, menus
        # Q/W/E use a hold-to-aim model (Task B2): KEYDOWN starts the hold timer
        # (no immediate cast); KEYUP fires — a quick tap (< AIM_HOLD_THRESHOLD)
        # fires instantly at the facing (legacy), a hold fires at the mouse world
        # pos for ground-targeted AoE. J (basic attack), U/Space (ult), 1-4
        # (swap), R/M/G/Esc stay instant (unchanged). Aim mode does not block
        # movement (RMB still moves) — the hold timer runs in parallel with the
        # normal input_dir update above.
        # F (Task E1): talk to the village NPC. If a dialogue is open, F/Space/Esc
        # advances the line; when the lines run out, dismiss (set _dialogue=None).
        # If no dialogue is open + the active hero is within ~60px of the NPC,
        # open the dialogue. The dialogue is a UI overlay (NOT a pause — the world
        # keeps updating behind it; this event handler only toggles the overlay).
        for e in events:
            if e.type == pygame.KEYDOWN:
                # dialogue overlay (Task E1): while a dialogue is open, F/Space/Esc
                # advance the line (and dismiss when the lines run out) INSTEAD of
                # their normal actions (Space=ult, Esc=pause). The dialogue is a UI
                # overlay (NOT a pause — the world keeps updating behind it; this
                # only intercepts these keys so the player can read at their own
                # pace without accidentally firing an ult into the NPC's face).
                if self._dialogue is not None and e.key in (pygame.K_f, pygame.K_SPACE, pygame.K_ESCAPE):
                    self._advance_dialogue()
                    continue
                if e.key in (pygame.K_j,):
                    if wc and wc.alive: self._do_attack(wc)
                elif e.key == pygame.K_q:
                    # hold-to-aim: start the hold timer (don't fire yet). The
                    # KEYUP handler below fires on release.
                    if wc and wc.alive:
                        self._aim_held_key = e.key
                        self._aim_skill = 0
                        self._aim_t = 0.0
                elif e.key == pygame.K_w:
                    if wc and wc.alive:
                        self._aim_held_key = e.key
                        self._aim_skill = 1
                        self._aim_t = 0.0
                elif e.key == pygame.K_e:
                    # E is the third ability (LoL-style). Evolve is on a different
                    # key (G) so E stays a combat key in the world.
                    if wc and wc.alive:
                        self._aim_held_key = e.key
                        self._aim_skill = 2
                        self._aim_t = 0.0
                elif e.key in (pygame.K_u, pygame.K_SPACE):
                    if wc and wc.alive: self._do_ultimate(wc)
                elif e.key == pygame.K_1:
                    self._switch(0)
                elif e.key == pygame.K_2:
                    self._switch(1)
                elif e.key == pygame.K_3:
                    self._switch(2)
                elif e.key == pygame.K_4:
                    self._switch(3)
                elif e.key == pygame.K_r:
                    # use the strongest heal potion the player owns on the active
                    # hero (R = recovery item). Picks mega_potion (>hp_potion) so
                    # the upgrade tiers matter, and heals by the item's actual
                    # power (was a hardcoded 120, 3x the hp_potion's listed 60).
                    if wc and wc.alive:
                        used = None
                        for pid in ("mega_potion", "hp_potion"):
                            if self.game.player.has_item(pid):
                                used = pid
                                break
                        if used is not None:
                            item = D.CONSUMABLES_DB[used]
                            amt = item.get("power", 60)
                            self.game.player.use_item(used)
                            wc.heal(amt)
                            self.floats.append(FloatText(wc.x, wc.y - 30, f"+{amt}",
                                                         (140, 240, 160), size=22))
                            audio.play("heal", 0.4)
                        else:
                            self.set_message("No potions left", 0.8)
                            audio.play("hit", 0.15)
                    else:
                        self.set_message("Hero is down", 0.8)
                        audio.play("hit", 0.15)
                elif e.key == pygame.K_m:
                    self.teleport = TeleportOverlay(self.game)
                elif e.key == pygame.K_g:
                    self.evolve = EvolveOverlay(self.game)
                elif e.key == pygame.K_f:
                    # F (Task E1): talk to the village NPC. If a dialogue is open,
                    # advance the line; when the lines run out, dismiss. If no
                    # dialogue is open + the active hero is within ~60px of the NPC,
                    # open the dialogue. The dialogue is a UI overlay (NOT a pause
                    # — the world keeps updating; this only toggles the overlay).
                    self._handle_npc_talk(wc)
                elif e.key == pygame.K_ESCAPE:
                    self.pause = PauseHub(self.game)
            elif e.type == pygame.KEYUP:
                # hold-to-aim release (Task B2): on KEYUP of the held skill key,
                # fire — a quick tap (< threshold) fires at the facing (legacy),
                # a hold fires at the mouse world pos (ground-targeted AoE). Only
                # fires if the released key matches the one we started the hold
                # with (so a stray KEYUP of another key doesn't misfire). Clear
                # the aim state whenever the held key is released — even if the
                # hero died mid-hold (otherwise the timer keeps accumulating +
                # the preview keeps drawing on a dead hero until the next
                # swap/map-load/KEYDOWN).
                if (self._aim_held_key is not None
                        and e.key == self._aim_held_key):
                    if wc and wc.alive:
                        idx = self._aim_skill
                        if idx is not None and 0 <= idx < 3:
                            if self._aim_t > AIM_HOLD_THRESHOLD:
                                # held long enough → fire at the mouse world pos
                                # (clamped to AIM_MAX_RANGE in _do_skill).
                                ox, oy = self.camera.offset()
                                mp = pygame.mouse.get_pos()
                                target = (mp[0] + ox, mp[1] + oy)
                                self._do_skill(wc, idx, target=target)
                            else:
                                # quick tap → fire instantly at the facing (legacy)
                                self._do_skill(wc, idx)
                    # clear the aim state regardless (the hold is over)
                    self._aim_skill = None
                    self._aim_held_key = None
                    self._aim_t = 0.0
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # LMB: LoL-style — no-op on its own (the player uses WASD +
                # abilities). Kept as a no-op so a stray click doesn't fire a
                # free attack; the basic attack stays on J / LMB-during-combat
                # is intentionally disabled to match the LoL control scheme.
                pass
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                # RMB: LoL-style — if the click lands on an enemy, set it as the
                # auto-attack target (the hero AA's it continuously until it dies
                # or a new command is given); otherwise (ground) set the
                # click-to-move target + clear any AA target. Use the event's own
                # pos (not pygame.mouse.get_pos) so the target is the click
                # location, not wherever the cursor drifted to by next frame.
                # Aim mode does not block RMB (the player can reposition while
                # aiming a ground-targeted skill).
                if wc and wc.alive:
                    ox, oy = self.camera.offset()
                    wx, wy = e.pos[0] + ox, e.pos[1] + oy
                    # hit-test enemies at the click world pos (Task B3)
                    hit_enemy = None
                    for en in self.enemies:
                        if en.alive and math.hypot(en.x - wx, en.y - wy) < en.r + 12:
                            hit_enemy = en
                            break
                    if hit_enemy is not None:
                        # RMB on an enemy -> AA target (the hero walks toward it
                        # when out of range, auto-attacks when in range; the
                        # update loop drives the AA). Clear any stale move_target
                        # so the hero doesn't keep walking to an old ground point
                        # while attacking the enemy.
                        wc.aa_target = hit_enemy
                        wc.move_target = None
                    else:
                        # RMB on ground -> click-to-move + clear the AA target
                        wc.aa_target = None
                        wc.move_target = (wx, wy)
                        wc.move_target_t = 0.0
                        wc._last_mt_dist = 0.0
                        wc._mt_stall_t = 0.0

        # hold-to-aim timer (Task B2): while a skill key is held, accumulate the
        # hold time so the KEYUP handler can distinguish a tap from a hold. The
        # preview draws once _aim_t > AIM_HOLD_THRESHOLD (see _draw_aim_preview).
        if self._aim_held_key is not None:
            self._aim_t += dt

        # enemies
        for en in self.enemies:
            if en.alive:
                en.update(sim_dt, wc, self._map_data["obstacles"], self.projectiles,
                          self.particles, self._on_enemy_event)
                # drive the DoT/status engine: burn/bleed/poison/regen tick in
                # real time and surface as a FloatText over the enemy. The tick
                # applies damage directly to the Combatant (en.enemy) via
                # take_damage on the base class, so the HP move is real and the
                # death path below fires when a DoT kills the enemy.
                if en.enemy.effects:
                    for res in en.enemy.tick_effects(sim_dt):
                        text, col = res
                        if self.game.player.settings.get("damage_numbers", True):
                            self.floats.append(FloatText(
                                en.x, en.y - 20, text, col, size=18))
                        # a DoT kill: take_damage already set hp=0 + alive=False
                        # on the Combatant; mirror to the WorldEnemy so the
                        # death/drops path fires on the next pass.
                        if en.enemy.hp <= 0:
                            en.alive = False
                            self._on_enemy_death(en, wc)
                            break

        # projectiles
        new_proj = []
        for p in self.projectiles:
            if not p.update(sim_dt, self._map_data["obstacles"]):
                continue          # projectile expired or hit a wall
            # collision with targets
            if p.kind == "hero":
                hit_one = False
                for en in self.enemies:
                    if en.alive and id(en) not in p.hit_set:
                        if math.hypot(en.x - p.x, en.y - p.y) < en.r + p.radius:
                            p.hit_set.add(id(en))
                            mult = self._element_mult(p.element, en.element)
                            is_crit = random.random() < p.source.hero.crit_chance
                            dmg = int(p.power * mult * (1.6 if is_crit else 1.0))
                            dealt = en.take_damage(dmg, p.x, p.y, is_crit,
                                                    on_attack=self._on_enemy_event)
                            if dealt:
                                self._on_enemy_hit(en, p.source, dealt, is_crit)
                                # ranged basic-attack energy: the melee branch grants
                                # ENERGY_GAIN_BASIC on a hit; do the same for the
                                # projectile source so ranged heroes charge energy + ult.
                                # Routed through add_energy so the light resonance
                                # (energy_regen) and the p_energy passive add.
                                p.source.add_energy(D.ENERGY_GAIN_BASIC)
                                # lifesteal passive for ranged heroes (the melee branch
                                # has its own lifesteal block; mirror it here so pyra /
                                # cinder / ranged staffs actually heal on basic hits)
                                a = p.source.hero
                                if (a.passive and a.passive.get("kind") == "lifesteal"
                                        and dealt > 0):
                                    heal = max(1, int(dealt * a.passive.get("val", 0.12)))
                                    p.source.heal(heal)
                                    if self.game.player.settings.get("damage_numbers", True):
                                        self.floats.append(FloatText(
                                            p.source.x, p.source.y - 30, f"+{heal}",
                                            (140, 240, 160), size=16))
                            hit_one = True
                            if not p.pierce:
                                break
                # a non-piercing projectile that hit anything is consumed; a
                # piercing one (or one that missed everything) keeps flying
                if p.pierce or not hit_one:
                    new_proj.append(p)
            else:  # enemy projectile
                if wc and wc.alive and id(wc) not in p.hit_set:
                    if math.hypot(wc.x - p.x, wc.y - p.y) < wc.r + p.radius:
                        p.hit_set.add(id(wc))
                        dmg = p.power
                        res = wc.take_damage(dmg, p.x, p.y)
                        if res == "perfect_dodge":
                            self._on_perfect_dodge(wc)
                        elif res == "revive":
                            self._on_hero_revive(wc)
                            self._hero_damaged(wc, dmg)
                        else:
                            dealt, reflected = res
                            if dealt:
                                self._hero_damaged(wc, dealt)
                                # thorns / reflect: send the reflected damage back
                                # to the projectile's owner (the source enemy) so
                                # the passive isn't silently discarded.
                                if reflected > 0:
                                    en = p.source
                                    if en is not None and en.alive:
                                        en.enemy.hp -= reflected
                                        if en.enemy.hp <= 0:
                                            en.enemy.hp = 0
                                            en.alive = False
                                        self.floats.append(FloatText(
                                            en.x, en.y - 20, str(reflected),
                                            (180, 220, 255), size=18))
                        continue
                    new_proj.append(p)
        self.projectiles = new_proj

        # summon + trap entities (Task A3): drive the temporary allies + ground
        # hazards. Summons auto-attack (or heal, for water) + despawn on expiry;
        # traps trigger on contact + despawn. Filtered in place so expired ones
        # drop out (the same pattern as projectiles/floats).
        if self._summons:
            self._summons = [s for s in self._summons
                             if s.update(sim_dt, self.enemies, self.particles,
                                         self._on_enemy_hit, self.party)]
        if self._traps:
            self._traps = [t for t in self._traps
                           if t.update(sim_dt, self.enemies, self.particles,
                                       self._on_enemy_hit, self._element_mult)]

        # ground loot drops (Task C2): expire old drops so the list doesn't
        # pile up. Drops older than 30s are removed (the player had plenty of
        # time to collect them; a stale drop shouldn't linger forever). The
        # magnet + pickup are driven in the walk-over check above; here we just
        # age + expire, after the pickup so a drop picked up this frame isn't
        # aged (it's already gone).
        if self.drops:
            for d in self.drops:
                d["t"] += sim_dt
            self.drops = [d for d in self.drops if d["t"] < 30.0]

        # particles + floats
        self.particles.update(sim_dt)
        self.floats = [f for f in self.floats if f.update(sim_dt)]

        # rift wave-clear check: if the rift is active and all the rift-spawned
        # enemies are dead, the wave is cleared -> break the seal, spawn a
        # guaranteed SR/SSR chest + a lore float, and mark the cell's secret
        # done so it can't re-trigger (persisted in ow_secrets_done). The
        # check is gated on _rift_active so it only fires once per trigger.
        if self._rift_active and self._rift_enemies:
            if all(not en.alive for en in self._rift_enemies):
                self._clear_rift()

        # camera
        if wc:
            lax = wc.vx * 0.1
            lay = wc.vy * 0.1
            self.camera.follow(wc.x, wc.y, WD.MAP_W, WD.MAP_H, sim_dt, (lax, lay))

        # timers
        self.message_t = max(0, self.message_t - dt)
        self.swap_flash = max(0, self.swap_flash - dt)
        self.map_enter_t = max(0, self.map_enter_t - dt)
        self.flash = max(0, self.flash - dt * 3)
        # day/night cycle: advance the world time (wraps 0..1) + persist it
        self._world_time = (self._world_time + dt / self._day_cycle) % 1.0
        self.game.player.ow_time = self._world_time
        # boss intro/defeat banner timers
        if self._boss_intro_t > 0:
            self._boss_intro_t = max(0, self._boss_intro_t - dt)
        if self._boss_defeat_t > 0:
            self._boss_defeat_t = max(0, self._boss_defeat_t - dt)
        if self._ascend_banner_t > 0:
            self._ascend_banner_t = max(0, self._ascend_banner_t - dt)
        # boss phase-transition flash decays over 0.5s (set on boss_phase event)
        if self._boss_phase_flash_t > 0:
            self._boss_phase_flash_t = max(0, self._boss_phase_flash_t - dt)
        # combo window: count down; reset the streak when it expires
        if self._combo_t > 0:
            self._combo_t -= dt
            if self._combo_t <= 0:
                self._combo_count = 0
                self._combo_pitch_tier = 0
                # combo climax: reset the max-combo celebration guard so the
                # next streak to hit COMBO_MAX celebrates again, and drop any
                # unspent empowered flags (the window that earned them expired).
                self._combo_max_celebrated = False
                self._skill_empowered = False
                self._ult_empowered = False

        # low-HP heartbeat: tick the procedural heartbeat while the active hero
        # is below 30% HP so the player feels the danger (silenced above 35%)
        if wc and wc.alive and self.game.player.settings.get("sound", True):
            low_hp = wc.hero.hp / max(1, wc.hero.max_hp) < 0.3
            audio.heartbeat_tick(dt, low_hp=low_hp)

        # storm strikes: every ~6s a storm map spawns a telegraphed lightning
        # strike at a random near-hero tile. Reuses the boss_slam telegraph
        # pattern (an expanding ring + a damage check at the strike point) so the
        # storm is a real hazard, not just a visual. Skipped under reduce_motion
        # (the strike still deals damage but the telegraph flash is dropped).
        if self._weather == "storm" and wc and wc.alive:
            self._storm_strike_t -= dt
            if self._storm_strike_t <= 0:
                self._storm_strike_t = 6.0
                # pick a strike point near the hero (within ~160px) so the strike
                # is a real threat the player must react to, not a distant flash
                ang = random.random() * math.tau
                dist = random.uniform(40, 160)
                sx = int(max(WD.TILE, min(WD.MAP_W - WD.TILE, wc.x + math.cos(ang) * dist)))
                sy = int(max(WD.TILE, min(WD.MAP_H - WD.TILE, wc.y + math.sin(ang) * dist)))
                # telegraph: an expanding ring + a brief flash so the player sees
                # the strike coming (reuses the boss_slam telegraph shape)
                self.particles.ring(sx, sy, (255, 240, 200), n=28, speed=360, size=6, life=0.5)
                self.particles.burst(sx, sy, (255, 240, 180), n=20, speed=300, size=6, life=0.5, grav=0)
                # damage check: hit the active hero if they're inside the strike
                # radius (the player should dash out during the telegraph)
                strike_r = 90
                if math.hypot(wc.x - sx, wc.y - sy) < strike_r:
                    dmg = int(40 + self.r * 8)  # scales with row depth
                    res = wc.take_damage(dmg, sx, sy, is_melee=False)
                    if res == "perfect_dodge":
                        self._on_perfect_dodge(wc)
                    elif res == "revive":
                        self._on_hero_revive(wc)
                        self._hero_damaged(wc, dmg)
                    else:
                        dealt, reflected = res
                        if dealt:
                            self._hero_damaged(wc, dealt)
                # thunder one-shot on each strike so the storm reads audibly
                if self.game.player.settings.get("sound", True):
                    audio.play_thunder(0.5)
                self.camera.add_shake(6, self._shake_mul)
                if not self._reduce_motion:
                    self.flash = max(self.flash, 0.18)

        # auto-save position periodically
        if wc:
            self.game.player.ow_pos = [int(wc.x), int(wc.y)]
        self._persist_party()
        # light save every ~2s? we save on map changes and deaths already; skip per-frame save

    def _on_enemy_event(self, name, en):
        if name == "enemy_strike":
            # melee already applied in _do_attack of enemy; just sfx + shake
            self.camera.add_shake(2, self._shake_mul)
            audio.play("hit", 0.2)
        elif name == "enemy_shoot":
            audio.play("skill", 0.2)
        elif name == "boss_ult":
            # boss ultimate: big AoE around boss. The radius/damage scale with the
            # mapped BOSS_ULT skill so the 6 bosses differ (frost = wider+freeze,
            # storm = wider high-damage, abyssal = lingering, hellfire = big).
            ult_id = D.BOSS_ULT.get(en.id)
            usk = D.SKILLS_DB.get(ult_id, {}) if ult_id else {}
            upower = usk.get("power", 1.8)
            radius = 260
            if ult_id in ("frost_cataclysm", "storm_of_embers"):
                radius = 320
            col = D.ELEMENT_COLORS.get(en.element, ((255, 80, 80),))[0]
            self.particles.burst(en.x, en.y, col, n=50, speed=360, size=8, life=0.8, grav=0)
            self.particles.ring(en.x, en.y, col, n=36, speed=440, size=7, life=0.6)
            self.camera.add_shake(12, self._shake_mul)
            self.flash = 0.35
            if self._reduce_motion:
                self.flash *= 0.4
            audio.play("boss_ult", 0.7)
            # damage active hero if close
            wc = self.party[self.active]
            if wc and wc.alive and math.hypot(wc.x - en.x, wc.y - en.y) < radius:
                dmg = int(en.enemy.atk * upower * self._element_mult(en.element, wc.element))
                res = wc.take_damage(dmg, en.x, en.y, is_melee=False)
                if res == "perfect_dodge":
                    self._on_perfect_dodge(wc)
                elif res == "revive":
                    self._on_hero_revive(wc)
                    self._hero_damaged(wc, dmg)
                else:
                    dealt, reflected = res
                    if dealt:
                        self._hero_damaged(wc, dealt)
                        # thorns/reflect: send reflected damage back to the boss
                        if reflected > 0 and en.alive:
                            en.enemy.hp -= reflected
                            if en.enemy.hp <= 0:
                                en.enemy.hp = 0
                                en.alive = False
                            self.floats.append(FloatText(
                                en.x, en.y - 20, str(reflected),
                                (180, 220, 255), size=18))
                # frost cataclysm also briefly freezes a hero caught in the blast
                if ult_id == "frost_cataclysm" and wc.alive:
                    wc._react_stun = max(getattr(wc, "_react_stun", 0.0), 1.2)
        elif name == "boss_phase":
            # boss advanced a phase: a telegraph flash + a warning sound so the
            # player feels the fight escalate (the new patterns start next)
            self.flash = 0.3
            if self._reduce_motion:
                self.flash *= 0.4
            # phase-transition flash on the boss bar: a 0.5s white alpha overlay
            # that fades out, drawn over the boss HP bar (see the boss bar draw).
            # Skipped under reduce_motion (the tick marks still show the phase
            # boundaries; only the flashy overlay is skipped).
            if not self._reduce_motion:
                self._boss_phase_flash_t = 0.5
            self.camera.add_shake(6, self._shake_mul)
            audio.play("boss_intro", 0.5)
            self.set_message(f"{en.enemy.name} — Phase {en._boss_phase}!", 1.5)
        elif name == "boss_warn":
            # a boss pattern is telegraphing: a distinct low warning ping (was
            # the boss_ult sound at 0.25 — a quieted version of the BIG boss
            # ult sound, easy to miss and confusing). Use 'weak' as the tell.
            audio.play("weak", 0.3)
        elif name == "boss_charge":
            # the boss finished its charge dash: damage the active hero if the
            # boss overlaps them (the dash is dodgeable by sidestepping the line)
            wc = self.party[self.active]
            if wc and wc.alive and math.hypot(wc.x - en.x, wc.y - en.y) < en.r + wc.r + 8:
                dmg = int(en.enemy.atk * 1.6 * self._element_mult(en.element, wc.element))
                res = wc.take_damage(dmg, en.x, en.y, is_melee=True)
                if res == "perfect_dodge":
                    self._on_perfect_dodge(wc)
                elif res == "revive":
                    self._on_hero_revive(wc)
                    self._hero_damaged(wc, dmg)
                else:
                    dealt, reflected = res
                    if dealt:
                        self._hero_damaged(wc, dealt)
                        if reflected > 0 and en.alive:
                            en.enemy.hp -= reflected
                            if en.enemy.hp <= 0:
                                en.enemy.hp = 0
                                en.alive = False
                            self.floats.append(FloatText(
                                en.x, en.y - 20, str(reflected),
                                (180, 220, 255), size=18))
            col = D.ELEMENT_COLORS.get(en.element, ((255, 80, 80),))[0]
            self.particles.burst(en.x, en.y, col, n=24, speed=300, size=6, life=0.5)
            self.camera.add_shake(8, self._shake_mul)
        elif name == "boss_slam":
            # the boss's ring-slam burst: damage the active hero if they're still
            # inside the slam radius (they should have dashed out during the telegraph)
            wc = self.party[self.active]
            slam_r = 160
            if wc and wc.alive and math.hypot(wc.x - en.x, wc.y - en.y) < slam_r:
                dmg = int(en.enemy.atk * 1.4 * self._element_mult(en.element, wc.element))
                res = wc.take_damage(dmg, en.x, en.y, is_melee=False)
                if res == "perfect_dodge":
                    self._on_perfect_dodge(wc)
                elif res == "revive":
                    self._on_hero_revive(wc)
                    self._hero_damaged(wc, dmg)
                else:
                    dealt, reflected = res
                    if dealt:
                        self._hero_damaged(wc, dealt)
                        if reflected > 0 and en.alive:
                            en.enemy.hp -= reflected
                            if en.enemy.hp <= 0:
                                en.enemy.hp = 0
                                en.alive = False
                            self.floats.append(FloatText(
                                en.x, en.y - 20, str(reflected),
                                (180, 220, 255), size=18))
            col = D.ELEMENT_COLORS.get(en.element, ((255, 80, 80),))[0]
            # a big expanding ring + burst so the slam reads as a shockwave
            self.particles.ring(en.x, en.y, col, n=40, speed=500, size=8, life=0.6)
            self.particles.burst(en.x, en.y, col, n=30, speed=360, size=7, life=0.6, grav=0)
            self.camera.add_shake(10, self._shake_mul)
            self.flash = 0.25
            if self._reduce_motion:
                self.flash *= 0.4
        elif name == "boss_break":
            # the boss's toughness bar shattered: a big ring + a "BROKEN!"
            # float + a longer hit-stop so the player feels the break land and
            # gets a clear window to pour damage in (the +50% multiplier is
            # applied inside WorldEnemy.take_damage while enemy.broken is true).
            col = D.ELEMENT_COLORS.get(en.element, ((255, 80, 80),))[0]
            # a white-tinged ring so the break reads distinctly from the
            # element-colored boss_ult/slam bursts
            self.particles.ring(en.x, en.y, (255, 240, 200), n=44, speed=520, size=8, life=0.7)
            self.particles.burst(en.x, en.y, col, n=36, speed=380, size=7, life=0.7, grav=0)
            self.floats.append(FloatText(en.x, en.y - 50, "BROKEN!",
                                         (255, 200, 120), size=28))
            self.hit_stop = max(self.hit_stop, 0.15)
            self.camera.add_shake(10, self._shake_mul)
            self.flash = 0.3
            if self._reduce_motion:
                self.flash *= 0.4
            audio.play("boss_intro", 0.6)

    def _draw_tick(self, dt):
        # keep particles/camera updating under overlays so the world looks alive
        self.particles.update(dt)
        self.floats = [f for f in self.floats if f.update(dt)]
        if self.party[self.active]:
            self.camera.follow(self.party[self.active].x, self.party[self.active].y,
                               WD.MAP_W, WD.MAP_H, dt, (0, 0))

    def _quit_to_title(self):
        self._persist_party()
        if self.party[self.active]:
            self.game.player.ow_pos = [int(self.party[self.active].x), int(self.party[self.active].y)]
        self.game.player.save()
        # stop the looping biome ambience when leaving the world scene (otherwise
        # it keeps playing under the title/menu music)
        audio.set_ambience(False)
        self.pause = None
        self.game.goto("title")

    # -----------------------------------------------------------------
    # Draw
    # -----------------------------------------------------------------
    def draw(self, surf):
        # map background
        if self._map_cell != (self.c, self.r):
            self._map_surf = self.map_renderer.get(self.c, self.r)
            self._map_cell = (self.c, self.r)
        ox, oy = self.camera.offset()
        surf.blit(self._map_surf, (-ox, -oy))

        # water + bridges (Task C3) — drawn BEFORE the drawables so they're
        # ground (under the hero/enemies/breakables). Water is a dithered
        # shimmer (a slow sine on the alpha) blitted tiled over each water rect;
        # bridges are a passable tile blitted over each bridge rect. Both are
        # cached by load_terrain so this is a single blit per tile per frame.
        # Biome-tinted: the water sprite is re-tinted toward the biome's ground
        # color at load time (load_terrain returns the neutral sprite; the
        # shimmer is a global alpha pulse so the water reads as wet).
        if self._water or self._bridges:
            self._draw_water_bridges(surf, ox, oy)

        # depth-sorted drawables: enemies + active hero + projectiles
        # the boss aura reads the night level (expanded at night) — set it once
        # per frame on each enemy so WorldEnemy.draw doesn't re-derive it per
        # enemy (the boss aura + the hero torch + the vignette all share one
        # quantized night level, no cache thrash).
        night_level = self._night_level()
        drawables = []
        for en in self.enemies:
            if en.alive:
                en._night_level = night_level
                drawables.append((en.y, "enemy", en))
        # breakable props — sorted with the rest so they occlude correctly
        # against the hero/enemies (a pot behind the hero is drawn first).
        for b in self.breakables:
            if not b["broken"]:
                drawables.append((b["y"], "breakable", b))
        # summon allies (Task A3) — sorted with the rest so they occlude correctly
        for s in self._summons:
            drawables.append((s.y, "summon", s))
        # traps (Task A3) — drawn under the entities (ground hazards, low y-sort
        # weight so they sit beneath the hero/enemies)
        for t in self._traps:
            drawables.append((t.y - 1, "trap", t))
        # ground loot drops (Task C2) — sorted with the rest so they occlude
        # correctly against the hero/enemies (a drop behind the hero is drawn
        # first). y-sort weight is the drop's y so they sit on the ground at
        # their actual position (a drop at the hero's feet is drawn before the
        # hero, a drop behind the hero is drawn first — same rule as breakables).
        for d in self.drops:
            drawables.append((d["y"], "drop", d))
        # landmark + village buildings (Task C3) — sorted with the rest so they
        # occlude correctly against the hero/enemies (a landmark behind the hero
        # is drawn first). Landmarks are decorative (no collision); village
        # buildings are decorative (no collision — the NPC entity is Task E1).
        if self._landmark is not None:
            drawables.append((self._landmark["y"], "landmark", self._landmark))
        if self._village is not None:
            for (bx, by, bkind) in self._village["buildings"]:
                drawables.append((by, "village", (bx, by, bkind)))
        # NPC (Task E1) — sorted with the rest so the NPC occludes correctly
        # against the hero/enemies (an NPC behind the hero is drawn first). Drawn
        # as a small sprite + a name tag (see _draw_npc).
        if self._npc is not None:
            drawables.append((self._npc["y"], "npc", self._npc))
        wc = self.party[self.active]
        if wc:
            drawables.append((wc.y, "hero", wc))
        drawables.sort(key=lambda d: d[0])
        for _, kind, obj in drawables:
            if kind == "breakable":
                self._draw_breakable(surf, obj, ox, oy)
            elif kind == "drop":
                self._draw_drop(surf, obj, ox, oy)
            elif kind == "landmark":
                self._draw_landmark(surf, obj, ox, oy)
            elif kind == "village":
                bx, by, bkind = obj
                self._draw_village_building(surf, bx, by, bkind, ox, oy)
            elif kind == "npc":
                self._draw_npc(surf, obj, ox, oy)
            elif kind in ("summon", "trap"):
                obj.draw(surf, ox, oy)
            else:
                obj.draw(surf, ox, oy, self.font_sm)

        # projectiles
        for p in self.projectiles:
            p.draw(surf, ox, oy)

        # hold-to-aim preview (Task B2): while a skill key is held past the
        # threshold, draw a category-specific aim preview at the mouse (clamped
        # to AIM_MAX_RANGE from the hero). AoE = a circle (the burst radius),
        # beam = a line, ranged = a trajectory line, melee = an arc in the
        # facing, summon/trap = a marker at the spawn point. Element-tinted;
        # the pulse is gated on reduce_motion (static reticle under RM).
        if wc and self._aim_skill is not None and self._aim_t > AIM_HOLD_THRESHOLD:
            self._draw_aim_preview(surf, wc, ox, oy)

        # RMB click-to-move ground marker — a pulsing reticle at the auto-walk
        # target so the player sees where the click registered and where the
        # hero is heading (was invisible: the hero just started walking).
        if wc and getattr(wc, "move_target", None):
            tx, ty = wc.move_target
            sx, sy = int(tx - ox), int(ty - oy)
            if -60 < sx < 1340 and -60 < sy < 780:
                # element-tinted (not pure white) + fading over 0.5s so the
                # reticle reads as a soft target marker, not a stray circle
                el_col = D.ELEMENT_COLORS.get(wc.element, ((200, 200, 220),))[0]
                fade = max(0.0, 1.0 - wc.move_target_t / 0.5)
                if fade > 0:
                    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.01)
                    a_ring = int(180 * pulse * fade)
                    ring = scratch(24, 24)
                    pygame.draw.circle(ring, (*el_col, a_ring), (12, 12), 8, 2)
                    surf.blit(ring, (sx - 12, sy - 12))
                    pygame.draw.circle(surf, el_col, (sx, sy), 2)

        # treasure chests — a glowing crate with a soft pulse; dimmed once opened
        for ch in self.chests:
            cx = int(ch["x"] - ox)
            cy = int(ch["y"] - oy)
            if -40 < cx < 1320 and -40 < cy < 760:
                if ch["opened"]:
                    # opened: a flat empty lid, no glow
                    pygame.draw.rect(surf, (60, 50, 30), (cx - 18, cy - 12, 36, 24), border_radius=4)
                    pygame.draw.rect(surf, (90, 70, 40), (cx - 18, cy - 12, 36, 24), 2, border_radius=4)
                else:
                    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.005)
                    # soft glow under the chest (reused scratch surface)
                    gw = 60
                    g = scratch(gw, gw)
                    ec = (255, 220, 120)
                    for rr in range(28, 12, -3):
                        a = int(40 * pulse * (1 - (rr - 12) / 16))
                        pygame.draw.circle(g, (*ec, a), (gw // 2, gw // 2), rr)
                    surf.blit(g, (cx - gw // 2, cy - gw // 2))
                    # the chest body: a wooden crate with a gold band + lid
                    pygame.draw.rect(surf, (90, 60, 30), (cx - 18, cy - 12, 36, 24), border_radius=4)
                    pygame.draw.rect(surf, (140, 90, 40), (cx - 18, cy - 12, 36, 8), border_radius=4)
                    pygame.draw.rect(surf, (255, 200, 90), (cx - 20, cy - 2, 40, 4))
                    pygame.draw.rect(surf, (60, 40, 20), (cx - 18, cy - 12, 36, 24), 2, border_radius=4)
                    # a little sparkle on top so it reads as loot
                    sp = int(pulse * 3)
                    pygame.draw.circle(surf, (255, 240, 180), (cx, cy - 14), 2 + sp)

        # broken breakables: a small dark shard pile so the broken prop leaves a
        # visible mark (not just vanishing). Drawn after the drawables loop so
        # it sits under the hero/enemies but above the chest layer.
        for b in self.breakables:
            if not b["broken"]:
                continue
            bx = int(b["x"] - ox)
            by = int(b["y"] - oy)
            if -30 < bx < 1310 and -30 < by < 750:
                body_col = {"pot": (110, 75, 50), "crate": (90, 60, 35),
                            "barrel": (80, 50, 30)}.get(b["kind"], (90, 60, 40))
                pygame.draw.ellipse(surf, body_col, (bx - 14, by + 4, 28, 10))
                pygame.draw.ellipse(surf, (40, 25, 15), (bx - 14, by + 4, 28, 10), 2)

        # hidden rift portal — a pulsing violet vortex at the rift tile so the
        # player can see where the rift is (and, once triggered, where the wave
        # is coming from). Drawn inline (the same pattern as the chest/breakable
        # draws) using the draw_rift_portal helper from generate_assets. Skipped
        # once the rift is cleared (_rift_done) so a cleared rift doesn't keep
        # glowing on the map (it's gone — the player solved it).
        if self._rift_secret is not None and not self._rift_done:
            rx, ry, _, _ = self._rift_secret
            sx = int(rx - ox)
            sy = int(ry - oy)
            if -60 < sx < 1340 and -60 < sy < 780:
                GA.draw_rift_portal(surf, sx, sy, float(pygame.time.get_ticks()))

        # particles + floats
        self.particles.draw(surf, ox, oy)
        for f in self.floats:
            x = int(f.x - ox)
            y = int(f.y - oy)
            if -50 < x < 1330 and -50 < y < 770:
                col = f.color
                # scale + fade the float by its remaining life for a nicer pop
                life_frac = max(0, f.life / f.max_life)
                size = f.size
                if life_frac < 0.4:
                    size = max(10, int(size * (0.6 + 0.4 * (life_frac / 0.4))))
                t = _font(size).render(f.text, True, col)
                sh = _font(size).render(f.text, True, (0, 0, 0))
                # alpha fade in the last 30% of life
                if life_frac < 0.3:
                    t.set_alpha(int(255 * (life_frac / 0.3)))
                    sh.set_alpha(int(255 * (life_frac / 0.3)))
                surf.blit(sh, (x + 2, y + 2))
                surf.blit(t, (x, y))

        # ambient biome fog + a soft vignette around the viewport edges for depth
        self._draw_atmosphere(surf, ox, oy)

        # edge transition arrows (subtle hint where exits are)
        self._draw_edge_hints(surf, ox, oy)

        # HUD on top of the world (party, skill bar, minimap, boss bar, etc.)
        self._draw_hud(surf)

        # transient center message
        if self.message_t > 0:
            text(surf, self.message, 26, (255, 240, 180), (640, 60), center=True)

        # boss intro cinematic banner — a full-width name plate that fades in/out
        # over the first ~1.6s on entering a boss arena
        if self._boss_intro_t > 0:
            self._draw_boss_banner(surf, self._boss_intro_name, self._boss_intro_t,
                                   intro=True)
        # boss defeat celebration banner — "BOSS DEFEATED" + the boss name
        if self._boss_defeat_t > 0:
            self._draw_boss_banner(surf, self._boss_defeat_name, self._boss_defeat_t,
                                   intro=False)
        # Aetheric Cycle "World Ascended!" banner — shown for ~3s after the
        # final boss (Demon King at 9,4) is defeated, signalling that the
        # player can now Ascend the World from the title screen.
        if self._ascend_banner_t > 0:
            self._draw_ascend_banner(surf, self._ascend_banner_t)

        # NPC dialogue box (Task E1) — a UI overlay drawn on top of the HUD (so
        # the box isn't covered by the skill bar) but under the modal overlays
        # (teleport/evolve/pause take over the screen). The world keeps simulating
        # behind it (the dialogue is a UI overlay, NOT a pause — update ran as
        # normal; only F/Space/Esc were intercepted to advance the line).
        if self._dialogue is not None:
            self._draw_dialogue_box(surf)

        # modal overlays (teleport map, evolve, pause hub) on top of everything
        if self.teleport:
            self.teleport.draw(surf, self.font_big, self.font, self.font_sm)
        if self.evolve:
            self.evolve.draw(surf, self.font_big, self.font, self.font_sm)
        if self.pause:
            self.pause.draw(surf, self.font_big)

    def _draw_aim_preview(self, surf, wc, ox, oy):
        """Draw the hold-to-aim preview (Task B2) for the currently-aimed skill.
        Called from draw() only when `_aim_skill is not None and _aim_t >
        AIM_HOLD_THRESHOLD`. Draws by skill category: AoE = a circle at the
        clamped mouse (the burst radius), beam = a line from hero to the clamped
        mouse, ranged (attack/magic with a projectile) = a trajectory line,
        melee (attack without a projectile) = an arc in the facing, summon/trap
        = a marker at the spawn/place point. Element-tinted; the pulse is gated
        on reduce_motion (static reticle, no pulse)."""
        idx = self._aim_skill
        if idx is None or idx < 0 or idx >= 3:
            return
        sk_list = wc.skill_list()
        if idx >= len(sk_list):
            return
        sk_id = sk_list[idx]
        if sk_id is None:
            return
        skill = D.SKILLS_DB.get(sk_id)
        if not skill:
            return
        kind = skill["type"]
        col = D.ELEMENT_COLORS.get(skill["element"], ((200, 200, 200),))[0]
        # mouse → world space, clamped to AIM_MAX_RANGE from the hero
        mp = pygame.mouse.get_pos()
        mx, my = mp[0] + ox, mp[1] + oy
        d = math.hypot(mx - wc.x, my - wc.y)
        if d > AIM_MAX_RANGE:
            # clamp along the aim line so the preview stays in range
            mx = wc.x + (mx - wc.x) * (AIM_MAX_RANGE / d)
            my = wc.y + (my - wc.y) * (AIM_MAX_RANGE / d)
        # screen-space coords for drawing
        hx, hy = int(wc.x - ox), int(wc.y - oy)
        tx, ty = int(mx - ox), int(my - oy)
        # pulse (gated on reduce_motion — static reticle under RM)
        if self._reduce_motion:
            pulse = 1.0
        else:
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.012)
        # category-specific preview
        if kind in ("aoe_attack", "aoe_magic"):
            # AoE: a circle at the clamped target (the burst radius). Element-
            # tinted, pulsing alpha (unless reduce_motion). A dashed outer ring
            # + a solid inner fill so the area reads clearly.
            r = AIM_AOE_RADIUS
            ring = scratch(r * 2 + 8, r * 2 + 8)
            cx, cy = r + 4, r + 4
            a_fill = int(40 + 30 * pulse)
            pygame.draw.circle(ring, (*col, a_fill), (cx, cy), r)
            pygame.draw.circle(ring, (*col, int(160 + 60 * pulse)), (cx, cy), r, 2)
            # crosshair ticks at the center so the target point is readable
            pygame.draw.line(ring, (*col, 220), (cx - 6, cy), (cx + 6, cy), 1)
            pygame.draw.line(ring, (*col, 220), (cx, cy - 6), (cx, cy + 6), 1)
            surf.blit(ring, (tx - cx, ty - cy))
        elif kind == "beam":
            # beam: a line from hero to the clamped target, element-tinted. A
            # bright core + a soft halo so the beam reads as a directed shot.
            halo = scratch(max(abs(tx - hx) + 16, 8), max(abs(ty - hy) + 16, 8))
            # draw the halo relative to the hero endpoint
            x0, y0 = min(hx, tx) - 8, min(hy, ty) - 8
            pygame.draw.line(halo, (*col, int(80 * pulse)),
                             (hx - x0, hy - y0), (tx - x0, ty - y0), 6)
            pygame.draw.line(halo, (*col, 240),
                             (hx - x0, hy - y0), (tx - x0, ty - y0), 2)
            surf.blit(halo, (x0, y0))
            # endpoint marker so the beam's terminus is readable
            pygame.draw.circle(surf, col, (tx, ty), 4)
        elif kind in ("attack", "magic"):
            # ranged vs melee: a ranged hero (bow/staff/orb) gets a trajectory
            # line to the clamped target; a melee hero (sword/dagger/shield)
            # gets an arc in the facing (melee doesn't aim at the mouse — the
            # swing is in the facing direction, so the preview shows the arc).
            style = WEAPON_STYLE.get(WEAPON_STYLE_KEY(wc.hero.id), "melee")
            if style == "ranged":
                # trajectory: a thin line + a reticle at the target
                pygame.draw.line(surf, (*col, 180), (hx, hy), (tx, ty), 2)
                pygame.draw.circle(surf, col, (tx, ty), 5, 2)
                pygame.draw.circle(surf, col, (tx, ty), 2)
            else:
                # melee arc in the facing: an arc at the hero's facing (not the
                # mouse — melee doesn't aim). The arc radius matches the melee
                # nuke's arc_r (~90). Drawn as a thick arc + a reticle at the
                # arc center so the swing area is readable.
                arc_cx = hx + wc.facing * 50
                arc_cy = hy
                arc_r = 90
                # a thick arc (drawn as a filled wedge outline) — use pygame.draw
                # arc with a bounding rect; element-tinted, pulsing alpha.
                arc_surf = scratch(arc_r * 2 + 4, arc_r * 2 + 4)
                ar_rect = pygame.Rect(2, 2, arc_r * 2, arc_r * 2)
                # draw a thick arc (the facing half) — pygame.draw.arc draws an
                # outline; use width=3 for a readable swing arc.
                pygame.draw.arc(arc_surf, (*col, int(160 + 60 * pulse)),
                                ar_rect, 0, math.pi, 3)
                # flip the arc to the facing direction (facing>0 = right side)
                if wc.facing < 0:
                    arc_surf = pygame.transform.flip(arc_surf, True, False)
                surf.blit(arc_surf, (arc_cx - arc_r - 2, arc_cy - arc_r - 2))
                # reticle at the arc center so the target point is readable
                pygame.draw.circle(surf, col, (arc_cx, arc_cy), 3)
        elif kind in ("summon", "trap"):
            # summon/trap: a marker at the spawn/place point (the hero's side /
            # facing, not the mouse — these skills place at the hero). A small
            # ring + a crosshair so the placement point is readable.
            sx = hx + wc.facing * 40 if kind == "summon" else hx + wc.facing * 60
            sy = hy
            r = 18 if kind == "summon" else 24
            ring = scratch(r * 2 + 6, r * 2 + 6)
            cx, cy = r + 3, r + 3
            pygame.draw.circle(ring, (*col, int(120 + 60 * pulse)), (cx, cy), r, 2)
            pygame.draw.line(ring, (*col, 200), (cx - 5, cy), (cx + 5, cy), 1)
            pygame.draw.line(ring, (*col, 200), (cx, cy - 5), (cx, cy + 5), 1)
            surf.blit(ring, (sx - cx, sy - cy))
        # for heal/buff/debuff/ultimate/revive, no preview (these are self/
        # facing-targeted; the aim doesn't change the effect). The aim mode
        # still runs (the hold timer + KEYUP), but the preview is empty.

    def _draw_breakable(self, surf, b, ox, oy):
        """Draw a breakable prop (pot/crate/barrel) — a simple procedural shape
        inline (like the chest at ~line 2734), cued by the kind. Small (~24px)
        so it reads as a ground prop, not an obstacle."""
        bx = int(b["x"] - ox)
        by = int(b["y"] - oy)
        if -30 < bx < 1310 and -30 < by < 750:
            kind = b["kind"]
            if kind == "pot":
                # a small clay pot: rounded body + a rim + a tiny mouth
                pygame.draw.ellipse(surf, (150, 100, 70), (bx - 12, by - 14, 24, 24))
                pygame.draw.ellipse(surf, (90, 60, 40), (bx - 12, by - 14, 24, 24), 2)
                pygame.draw.rect(surf, (110, 75, 50), (bx - 7, by - 18, 14, 6), border_radius=2)
                pygame.draw.rect(surf, (60, 40, 25), (bx - 7, by - 18, 14, 6), 2, border_radius=2)
            elif kind == "crate":
                # a wooden crate: a square with plank lines + iron corners
                pygame.draw.rect(surf, (140, 95, 55), (bx - 13, by - 13, 26, 26), border_radius=2)
                pygame.draw.rect(surf, (180, 130, 80), (bx - 13, by - 13, 26, 6), border_radius=2)
                pygame.draw.line(surf, (90, 60, 35), (bx - 13, by - 13), (bx + 13, by + 13), 2)
                pygame.draw.line(surf, (90, 60, 35), (bx + 13, by - 13), (bx - 13, by + 13), 2)
                pygame.draw.rect(surf, (60, 40, 20), (bx - 13, by - 13, 26, 26), 2, border_radius=2)
                # iron corner studs
                for cx2, cy2 in ((bx - 10, by - 10), (bx + 8, by - 10),
                                 (bx - 10, by + 8), (bx + 8, by + 8)):
                    pygame.draw.circle(surf, (70, 70, 80), (cx2, cy2), 2)
            else:  # barrel
                # a wooden barrel: a wider body + iron bands + top ellipse
                pygame.draw.ellipse(surf, (120, 80, 45), (bx - 14, by - 14, 28, 28))
                pygame.draw.ellipse(surf, (80, 55, 30), (bx - 14, by - 14, 28, 28), 2)
                # iron bands
                pygame.draw.rect(surf, (70, 70, 80), (bx - 14, by - 6, 28, 3))
                pygame.draw.rect(surf, (70, 70, 80), (bx - 14, by + 4, 28, 3))
                # top opening
                pygame.draw.ellipse(surf, (60, 40, 25), (bx - 10, by - 16, 20, 8))

    def _draw_drop(self, surf, drop, ox, oy):
        """Draw a ground loot drop (Task C2) — a pixel-art sprite (load_drop
        from Task A4) at the drop's screen pos, scaled to ~24px, with a small
        bob so it reads as loot (not a static tile). The bob is a vertical
        sinusoid (amplitude 2px, ~2s period) gated on reduce_motion (static
        under RM). The sprite is cached by load_drop so this is a single blit
        per drop per frame. A soft glow under the drop so it reads as loot
        against the ground (reused scratch surface, the same pattern as the
        chest glow)."""
        dx = int(drop["x"] - ox)
        dy = int(drop["y"] - oy)
        if -40 < dx < 1320 and -40 < dy < 760:
            kind = drop["kind"]
            # bob: a vertical sinusoid so the drop reads as loot, not a static
            # tile. Gated on reduce_motion (static under RM).
            if not self._reduce_motion:
                bob = int(2 * math.sin(pygame.time.get_ticks() * 0.005 + drop["x"] * 0.1))
            else:
                bob = 0
            # soft glow under the drop so it reads as loot against the ground
            # (the same pattern as the chest glow — a reused scratch surface).
            gw = 28
            g = scratch(gw, gw)
            ec = {"gold": (255, 220, 120), "hp_potion": (140, 240, 160),
                  "shard": (200, 160, 255),
                  "equipment": (255, 200, 120)}.get(kind, (255, 220, 120))
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.005)
            for rr in range(14, 6, -2):
                a = int(36 * pulse * (1 - (rr - 6) / 8))
                pygame.draw.circle(g, (*ec, a), (gw // 2, gw // 2), rr)
            surf.blit(g, (dx - gw // 2, dy - gw // 2 + 8))
            # the drop sprite — load_drop returns a cached 16x16 surface scaled
            # to 24x24 (the size that reads as loot, not a tiny speck). The
            # hp_potion drop kind maps to the "potion" sprite (the asset is saved
            # as drops/potion.png by generate_assets.py; the inventory item is
            # "hp_potion" but the drop sprite id is "potion").
            sprite_kind = "potion" if kind == "hp_potion" else kind
            sprite = load_drop(sprite_kind, (24, 24))
            sw, sh = sprite.get_size()
            surf.blit(sprite, (dx - sw // 2, dy - sh // 2 + bob))

    # -----------------------------------------------------------------
    # Water / bridges / landmark / village (Task C3)
    # -----------------------------------------------------------------
    def _draw_water_bridges(self, surf, ox, oy):
        """Draw the water pools + bridges (Task C3). Water is a dithered
        shimmer (a slow sine on the alpha) blited tiled over each water rect;
        bridges are a passable tile blitted over each bridge rect. Both sprites
        are cached by load_terrain so this is a single blit per tile per frame.
        Drawn BEFORE the drawables so they're ground (under the hero/enemies).
        The shimmer is a global alpha pulse on the water tiles so the water
        reads as wet, not a static blue square. Gated on reduce_motion (static
        under RM — no shimmer, just the tile)."""
        # the water sprite is a 40x40 tile (TILE_PX); the bridge sprite is the
        # same size. Both are cached by load_terrain so this is a single blit per
        # tile per frame.
        tile = WD.TILE
        # shimmer: a slow sine on the alpha (amplitude 40, ~2s period). Gated on
        # reduce_motion (static under RM — no shimmer, full alpha).
        if not self._reduce_motion:
            shimmer = int(40 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.003)))
        else:
            shimmer = 0
        # water tiles — blit the water sprite tiled over each water rect, with
        # the shimmer applied as a global alpha on the sprite. The sprite is
        # cached per (path, scale); we set the alpha per frame on a copy so the
        # shimmer doesn't mutate the cached sprite (set_alpha on the cached
        # surface would persist across frames).
        water_sprite = load_terrain("water")
        for wr in self._water:
            # cull off-screen water rects (the rect is in world coords; the
            # camera offset is ox/oy)
            wx, wy = wr.x, wr.y
            if wx - ox > 1280 or wx + wr.w - ox < 0:
                continue
            if wy - oy > 720 or wy + wr.h - oy < 0:
                continue
            for ty in range(wr.y, wr.y + wr.h, tile):
                for tx in range(wr.x, wr.x + wr.w, tile):
                    sx = tx - ox
                    sy = ty - oy
                    if -tile < sx < 1280 and -tile < sy < 720:
                        if shimmer > 0:
                            # a copy so the shimmer alpha doesn't mutate the
                            # cached sprite (set_alpha on the cached surface
                            # would persist across frames + across cells).
                            ws = water_sprite.copy()
                            ws.set_alpha(255 - shimmer)
                            surf.blit(ws, (sx, sy))
                        else:
                            surf.blit(water_sprite, (sx, sy))
        # bridge tiles — blit the bridge sprite over each bridge rect. The bridge
        # is passable (NOT in the obstacles list), so the hero walks through it.
        bridge_sprite = load_terrain("bridge")
        for br in self._bridges:
            bx0, by0 = br.x, br.y
            if bx0 - ox > 1280 or bx0 + br.w - ox < 0:
                continue
            if by0 - oy > 720 or by0 + br.h - oy < 0:
                continue
            for ty in range(br.y, br.y + br.h, tile):
                for tx in range(br.x, br.x + br.w, tile):
                    sx = tx - ox
                    sy = ty - oy
                    if -tile < sx < 1280 and -tile < sy < 720:
                        surf.blit(bridge_sprite, (sx, sy))

    def _draw_landmark(self, surf, lm, ox, oy):
        """Draw a landmark (Task C3) — a pixel-art sprite (load_landmark from
        Task A4) at the landmark's screen pos. Decorative (no collision). The
        lore float on first visit is fired in _load_map (not here) so the player
        sees it on cell entry even if the landmark is off-screen on the first
        draw frame."""
        lx = int(lm["x"] - ox)
        ly = int(lm["y"] - oy)
        if -80 < lx < 1360 and -80 < ly < 800:
            kind = lm["kind"]
            sprite = load_landmark(kind)
            sw, sh = sprite.get_size()
            surf.blit(sprite, (lx - sw // 2, ly - sh // 2))

    def _draw_village_building(self, surf, bx, by, kind, ox, oy):
        """Draw a village building (Task C3) — a pixel-art sprite (load_village
        from Task A4) at the building's screen pos. Decorative (no collision —
        the NPC entity + interact is Task E1). The sprite is a 60x60 surface
        cached by load_village so this is a single blit per building per frame.
        Drawn depth-sorted with the hero/enemies so a building behind the hero
        is drawn first (occludes correctly)."""
        sx = int(bx - ox)
        sy = int(by - oy)
        if -60 < sx < 1340 and -60 < sy < 780:
            sprite = load_village(kind)
            sw, sh = sprite.get_size()
            surf.blit(sprite, (sx - sw // 2, sy - sh // 2))

    def _draw_npc(self, surf, npc, ox, oy):
        """Draw the village NPC (Task E1) — a small figure + a name tag at the
        NPC's screen pos. The NPC reuses a village building sprite (the temple
        sprite, which reads as a robed figure at this scale) as the body so no
        new asset is needed, tinted toward the biome's accent so a plains NPC
        and a void NPC read differently. A name tag floats above so the player
        can see who to walk up to. Decorative (no collision); interact on F
        (see the event loop in update + _handle_npc_talk)."""
        sx = int(npc["x"] - ox)
        sy = int(npc["y"] - oy)
        if -60 < sx < 1340 and -60 < sy < 780:
            # body: a temple sprite tinted toward the biome accent (so the NPC
            # reads as a person, not a building — the temple has a figure shape).
            pal = WD.BIOMES.get(npc["biome"], {})
            accent = pal.get("accent", (230, 220, 180))
            sprite = load_village("temple")
            sw, sh = sprite.get_size()
            # tint by blitting a translucent accent rect over the sprite (cheap,
            # no per-pixel work) so the NPC picks up the biome's mood.
            surf.blit(sprite, (sx - sw // 2, sy - sh // 2))
            tint = scratch(sw, sh)
            pygame.draw.rect(tint, (*accent, 70), tint.get_rect())
            surf.blit(tint, (sx - sw // 2, sy - sh // 2))
            # a soft ground shadow so the NPC sits on the ground (not floating)
            shadow = scratch(34, 10)
            pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
            surf.blit(shadow, (sx - 17, sy + sh // 2 - 4))
            # name tag above the NPC (a small label so the player sees who to talk
            # to). Drawn with the cached text() helper so it doesn't re-render the
            # string every frame.
            text(surf, npc["name"], 18, (255, 240, 200),
                 (sx, sy - sh // 2 - 14), center=True)
            # an "F to talk" hint when the active hero is in range (so the player
            # learns the interact key without a tutorial). Pulses softly so it
            # reads as a prompt, not a static label.
            wc = self.party[self.active]
            if wc and math.hypot(wc.x - npc["x"], wc.y - npc["y"]) <= 60:
                pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.006)
                col = (int(220 + 35 * pulse), int(220 + 20 * pulse), int(160 + 40 * pulse))
                text(surf, "[F] Talk", 16, col, (sx, sy - sh // 2 - 34), center=True)

    def _draw_dialogue_box(self, surf):
        """Draw the NPC dialogue box (Task E1) — a rounded rect at the bottom of
        the screen with the NPC name + the current line + a '>' advance marker.
        A UI overlay (NOT a pause — the world keeps simulating behind it; update
        ran as normal, only F/Space/Esc were intercepted to advance the line).
        Advance on F/Space/Esc; dismiss when the lines run out (see
        _advance_dialogue). The box sits above the HUD (so the skill bar doesn't
        cover it) but under the modal overlays (teleport/evolve/pause)."""
        dlg = self._dialogue
        if dlg is None:
            return
        # box geometry — a wide rounded rect at the bottom, above the skill bar
        bw, bh = 960, 150
        bx = (1280 - bw) // 2
        by = 720 - bh - 90           # 90px above the bottom so the skill bar shows
        # a dark translucent panel with a light border (reads as a text box)
        panel = scratch(bw, bh)
        pygame.draw.rect(panel, (16, 14, 24, 220), panel.get_rect(), border_radius=12)
        pygame.draw.rect(panel, (220, 200, 140, 220), panel.get_rect(), 3, border_radius=12)
        surf.blit(panel, (bx, by))
        # NPC name (top-left, in the accent color so it reads as a speaker label)
        text(surf, dlg["name"], 22, (255, 230, 160), (bx + 24, by + 16))
        # the current line (centered in the box, wrapped if needed — the lines are
        # <=80 chars so a single line fits at font size 24 in a 960px box)
        lines = dlg["lines"]
        idx = dlg["idx"]
        if 0 <= idx < len(lines):
            text(surf, lines[idx], 24, (240, 240, 250),
                 (bx + bw // 2, by + bh // 2 - 6), center=True)
        # advance marker — a '>' in the bottom-right that pulses so the player
        # knows to press F/Space/Esc to advance. Gated on reduce_motion (static
        # under RM). On the last line, show "[end]" so the player knows the next
        # press dismisses the box (not advances to another line).
        if idx < len(lines) - 1:
            pulse = 1.0 if self._reduce_motion else (
                0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.008))
            col = (int(180 + 75 * pulse), int(180 + 60 * pulse), int(120 + 40 * pulse))
            text(surf, ">", 26, col, (bx + bw - 28, by + bh - 28))
        else:
            text(surf, "[end]", 18, (200, 200, 220),
                 (bx + bw - 48, by + bh - 26))
        # a controls hint at the bottom-left so the player learns the advance keys
        text(surf, "F/Space/Esc: continue", 15, (180, 180, 200),
             (bx + 24, by + bh - 24))

    def _draw_boss_banner(self, surf, name, t, intro):
        """A full-width cinematic banner for the boss intro / defeat. Fades in
        at the start and out at the end of its duration; intro shows the boss
        name + a 'BOSS' tag, defeat shows 'BOSS DEFEATED' + the name."""
        # total duration drives the fade (intro 1.6s, defeat 2.5s)
        dur = 1.6 if intro else 2.5
        # fade in over the first 20%, out over the last 25%
        if t > dur * 0.8:
            a = max(0, 1 - (t - dur * 0.8) / (dur * 0.2))   # fading out
        elif t < dur * 0.2:
            a = max(0, 1 - (dur * 0.2 - t) / (dur * 0.2))   # fading in
        else:
            a = 1.0
        alpha = int(220 * a)
        # honor reduce_motion: keep the banner a subtle low-contrast notification
        if getattr(self, "_reduce_motion", False):
            alpha = min(alpha, 80)
            a = min(a, 0.4)
        # a dark band across the upper-middle of the screen
        band = pygame.Surface((1280, 140), pygame.SRCALPHA)
        pygame.draw.rect(band, (10, 8, 16, int(180 * a)), band.get_rect())
        pygame.draw.rect(band, (200, 60, 60, alpha), (0, 60, 1280, 4))
        pygame.draw.rect(band, (200, 60, 60, alpha), (0, 76, 1280, 4))
        surf.blit(band, (0, 200))
        if intro:
            text(surf, "BOSS", 28, (255, 80, 80), (640, 232), center=True)
            text(surf, name, 48, (255, 240, 220), (640, 286), center=True)
        else:
            text(surf, "BOSS DEFEATED", 48, (255, 220, 120), (640, 250), center=True)
            text(surf, name, 28, (255, 240, 200), (640, 300), center=True)

    def _draw_ascend_banner(self, surf, t):
        """A full-width cinematic banner shown after the final boss (Demon King
        at 9,4) is defeated, signalling the player can Ascend the World to
        start a new Aetheric Cycle (NG+). Reuses the boss-banner fade shape."""
        dur = 3.0
        if t > dur * 0.8:
            a = max(0, 1 - (t - dur * 0.8) / (dur * 0.2))   # fading out
        elif t < dur * 0.2:
            a = max(0, 1 - (dur * 0.2 - t) / (dur * 0.2))   # fading in
        else:
            a = 1.0
        alpha = int(220 * a)
        if getattr(self, "_reduce_motion", False):
            alpha = min(alpha, 80)
            a = min(a, 0.4)
        # a golden band (vs the boss banner's red) so the ascend cue reads as a
        # world-tier milestone, not another boss kill
        band = pygame.Surface((1280, 160), pygame.SRCALPHA)
        pygame.draw.rect(band, (16, 12, 8, int(180 * a)), band.get_rect())
        pygame.draw.rect(band, (255, 200, 80, alpha), (0, 60, 1280, 4))
        pygame.draw.rect(band, (255, 200, 80, alpha), (0, 96, 1280, 4))
        surf.blit(band, (0, 360))
        text(surf, "WORLD ASCENDED!", 56, (255, 230, 140), (640, 410), center=True)
        text(surf, "Return to the title to Ascend the World (NG+)",
             24, (255, 240, 200), (640, 470), center=True)

    def _draw_atmosphere(self, surf, ox, oy):
        """Biome-tinted drifting fog motes + a soft vignette for depth.

        The vignette + sky gradient are baked once per biome+day-phase into one
        overlay (cached in _light_cache) and blitted as a single image. The fog
        motes are a handful of pre-rendered soft circles (one blit each) whose
        positions parallax with the camera — no per-frame full-screen fill and
        no ~15-draws-per-mote concentric circle build."""
        pal = WD.BIOMES[WD.cell_biome(self.c, self.r)]
        sky = pal.get("sky", (40, 40, 60))
        # modulate the sky color by the day/night phase so the world has a
        # time-of-day glow: phase 0 = dawn (cool), 0.25 = noon (warm/bright),
        # 0.5 = dusk (orange), 0.75 = night (dark blue). The biome's base sky is
        # the anchor; the phase shifts it. Quantize the phase to 1/16 so the
        # _biome_atmos cache key stays stable (otherwise the continuous phase
        # would allocate a fresh 3.5MB overlay every frame — a memory leak).
        # quantize the phase to 1/16 so the _biome_atmos cache key stays stable
        # (otherwise the continuous phase would allocate a fresh 3.5MB overlay
        # every frame — a memory leak). 16 buckets per biome is ~56MB total.
        sky = self._sky_for_phase(sky, _qphase=round(self._world_time * 16) / 16 % 1.0)
        # night level (0 = day, 1..8 = night depth) — the single quantized value
        # the atmosphere base + the darkening overlay + the torch pool + the
        # boss aura all read so they share one quantization (no cache thrash).
        night_level = self._night_level()
        # base atmosphere (vignette + sky gradient) — one cached blit per
        # biome+phase+night. The vignette is stronger at night (multiplied by a
        # night factor) so the world reads as a deeper, more enclosed space.
        base = self._biome_atmos(sky, night_level)
        surf.blit(base, (0, 0))
        # a darkening overlay at night so the world reads as night-time (a flat
        # low-alpha blue-black over everything below phase 0.5..1.0 night)
        night = self._night_overlay()
        if night is not None:
            surf.blit(night, (0, 0))
            # torchlight: a warm radial light pool follows the active hero so the
            # night reads as torch-lit, not just uniformly dark. The pool is
            # warm-tinted (255,220,160) + BLEND_RGBA_ADD so it brightens the night
            # overlay without erasing it (a torch glow, not a white-out). The pool
            # is positioned at the hero's screen pos (camera-adjusted, so it
            # tracks the hero under camera shake too — the shake is in ox/oy).
            wc = self.party[self.active]
            if wc is not None:
                torch_sp = self._torch_sprite(night_level)
                tw, th = torch_sp.get_size()
                tx = int(wc.x - ox - tw // 2)
                ty = int(wc.y - oy - th // 2)
                surf.blit(torch_sp, (tx, ty),
                          special_flags=pygame.BLEND_RGBA_ADD)
        # (the drifting fog motes were removed in Task C1 — they read as stray
        # white circles. The fog weather darkening below stays.)

        # weather overlays — rain (diagonal alpha streaks) + fog (a flat
        # darkening). Both are cached in _light_cache and blitted as a single
        # image so the per-frame cost is one blit, not a full-screen fill.
        # Skipped under reduce_motion (the wet multiplier + storm strikes still
        # apply; only the visual overlay is dropped so the accessibility mode
        # isn't overwhelmed by a moving rain layer).
        if not self._reduce_motion:
            if self._weather in ("rain", "storm"):
                rain_ov = self._rain_overlay()
                surf.blit(rain_ov, (0, 0))
            elif self._weather == "fog":
                fog_ov = self._fog_overlay()
                surf.blit(fog_ov, (0, 0))

        # full-screen flashes (reuse one persistent overlay surface)
        if self.map_enter_t > 0 or self.swap_flash > 0 or self.flash > 0:
            ov = self._flash_surf
            ov.fill((0, 0, 0, 0))
            if self.map_enter_t > 0:
                # a directional slide-wipe for edge transitions, a soft circle
                # wipe for teleports; falls back to a flat fade
                a = int(190 * (self.map_enter_t / 0.45))
                if self._reduce_motion:
                    a = min(a, 60)
                d = self._enter_dir
                if d in ("left", "right", "top", "bottom"):
                    prog = 1 - (self.map_enter_t / 0.45)   # 0..1 as it clears
                    # the wipe band retreats in the direction of travel so the
                    # hero's entry edge is uncovered first (was inverted: the
                    # band sat on the entry edge and hid the hero until the end)
                    if d == "right":
                        wband = int((1 - prog) * 1280)
                        ov.fill((0, 0, 0, a), (1280 - wband, 0, wband, 720))
                    elif d == "left":
                        wband = int((1 - prog) * 1280)
                        ov.fill((0, 0, 0, a), (0, 0, wband, 720))
                    elif d == "bottom":
                        hband = int((1 - prog) * 720)
                        ov.fill((0, 0, 0, a), (0, 720 - hband, 1280, hband))
                    elif d == "top":
                        hband = int((1 - prog) * 720)
                        ov.fill((0, 0, 0, a), (0, 0, 1280, hband))
                else:
                    ov.fill((0, 0, 0, a))
            if self.swap_flash > 0:
                a = int(120 * (self.swap_flash / 0.3))
                ov.fill((180, 220, 255, a))
            if self.flash > 0:
                a = int(120 * self.flash)
                ov.fill((255, 255, 255, a))
            surf.blit(ov, (0, 0))

    def _biome_atmos(self, sky, night_level=0):
        """Cached per-biome atmosphere base: a soft vignette + a top-down sky
        gradient, baked into one 1280x720 overlay. Built once per biome +
        night level (the vignette is stronger at night — multiply the vignette
        alpha by a night factor — so the night reads as a deeper, more
        claustrophobic space). Reuses the quantized night levels as part of the
        cache key so the cache doesn't thrash (8 night buckets per biome +
        16 day-phase buckets per biome = ~128 cached overlays total)."""
        key = ("atmos", sky, night_level)
        ov = self._light_cache.get(key)
        if ov is None:
            ov = pygame.Surface((1280, 720), pygame.SRCALPHA)
            # gentle top-to-bottom gradient of the sky color at low alpha —
            # gives the world a time-of-day glow that shifts per biome
            for y in range(0, 720, 4):
                t = y / 720
                a = int(22 * (1 - t))
                pygame.draw.rect(ov, (*sky, a), (0, y, 1280, 4))
            # vignette — darker corners (the inset grows outward, so the alpha
            # is highest at the outermost ring = the corners, not the center).
            # Tint the vignette with a darkened sky color so the depth shading
            # reads as the biome's own (cave = deep-blue, castle = warm-brown)
            # rather than pure black in every biome. At night the vignette is
            # stronger (multiply the alpha by a night factor up to 1.6x at the
            # deepest night) so the world reads as a deeper, more enclosed space
            # — the lit pool in the center reads brighter by contrast.
            vign_mul = 1.0 + 0.075 * night_level   # 1.0 day, ~1.6 at deepest night
            sky_dark = (sky[0] // 4, sky[1] // 4, sky[2] // 4)
            for i in range(0, 220, 6):
                a = int(min(255, 80 * (1 - i / 220) ** 2 * vign_mul))
                pygame.draw.rect(ov, (*sky_dark, a),
                                 (i, i, 1280 - 2 * i, 720 - 2 * i), 6)
            self._light_cache[key] = ov
        return ov

    def _rain_overlay(self):
        """A cached full-screen rain overlay — a field of diagonal alpha streaks
        drawn once into a 1280x720 surface and blitted as a single image per
        frame. The streaks are static (the rain 'moves' via the streak offsets
        baked into the sprite) so the overlay is one blit, not a per-frame
        redraw of ~80 lines. Cached in _light_cache so the 3.5MB surface is
        built once per scene, not per frame."""
        key = ("weather_rain",)
        ov = self._light_cache.get(key)
        if ov is None:
            ov = pygame.Surface((1280, 720), pygame.SRCALPHA)
            rng = random.Random(4242)   # deterministic streak field
            # ~80 diagonal streaks across the screen; each is a short line with
            # a low alpha so the overlay reads as rain, not a solid sheet
            for _ in range(80):
                x = rng.randint(0, 1280)
                y = rng.randint(0, 720)
                length = rng.randint(14, 26)
                a = rng.randint(60, 110)
                # diagonal down-right (the wind-driven slant)
                pygame.draw.line(ov, (200, 220, 255, a),
                                 (x, y), (x + length // 2, y + length), 2)
            self._light_cache[key] = ov
        return ov

    def _fog_overlay(self):
        """A cached full-screen fog overlay — a flat low-alpha grey-blue
        darkening so the world reads as hazy (a heavier version of the night
        overlay, tinted cool so it reads as fog, not night). One blit per
        frame; cached in _light_cache so the surface is built once."""
        key = ("weather_fog",)
        ov = self._light_cache.get(key)
        if ov is None:
            ov = pygame.Surface((1280, 720), pygame.SRCALPHA)
            ov.fill((180, 200, 220, 60))
            self._light_cache[key] = ov
        return ov

    def _sky_for_phase(self, base_sky, _qphase=None):
        """Shift a biome's base sky color by the day/night phase (0..1).
        0   = dawn  — bright (start of day)
        0.25= midday — brightest + warm
        0.5 = dusk  — dimming, warm
        0.75= night — darkest + blue
        Returns a new RGB tuple; the base sky is the anchor (treated as the
        midday value). The phase is quantized to 1/16 by the caller (passed as
        _qphase) so the downstream _biome_atmos cache key stays stable — without
        quantization, the continuous phase would allocate a fresh 3.5MB overlay
        every frame (a memory leak)."""
        p = _qphase if _qphase is not None else self._world_time
        r, g, b = base_sky
        # brightness curve: full (1.0) near p=0.25 (midday), dim (~0.45) at
        # p=0.75 (night). cos(2*pi*(p-0.25)) is +1 at midday, -1 at night.
        bright = 0.72 + 0.28 * math.cos(2 * math.pi * (p - 0.25))
        # a single continuous warm/cool model across the whole cycle (no branch
        # at p=0.5 — the old day/night halves used different multipliers and
        # kicked the color by ~24 R-units in one frame at dusk). Warmth flares
        # at the two horizons (dawn ~0.0, dusk ~0.5) and is ~0 at noon, so the
        # warm hue reads as dawn/dusk, not midday. Cool grows as brightness
        # falls so night skews blue.
        warm = 0.9 * math.exp(-((p - 0.0) / 0.10) ** 2) + \
               0.9 * math.exp(-((p - 0.5) / 0.10) ** 2)
        warm = min(1.0, warm)
        cool = max(0, 1 - bright)
        r = min(255, int(r * bright + 22 * warm))
        g = min(255, int(g * bright + 4 * warm))
        b = min(255, max(10, int(b * bright + 16 * cool - 10 * warm)))
        return (r, g, b)

    def _night_level(self):
        """Quantized night level (0 = day, 1..8 = night depth). The single
        source of truth for night-scaled effects: the darkening overlay, the
        hero torchlight, the boss aura, and the vignette boost all read this so
        they share one quantization (8 buckets — no per-frame cache thrash).
        The active window ramps up after dusk (p >= 0.4), peaks near midnight
        (0.75), and ramps back down through pre-dawn with no hard snap."""
        p = self._world_time
        # distance from midnight (0.75) along the wrapped cycle; 0 at midnight,
        # 0.5 at noon. Only darken once we're past dusk (p >= 0.4).
        dp = abs(((p - 0.75) + 0.5) % 1.0 - 0.5)   # 0 at 0.75, 0.5 at 0.25
        if p < 0.4 or dp > 0.35:
            return 0
        # 8 at midnight (dp=0), fading to 0 at the edges of the window (dp=0.35)
        level = int(8 * (1 - dp / 0.35))
        return max(1, min(8, level))

    def _night_overlay(self):
        """A cached full-screen darkening overlay whose strength follows the day
        phase — strongest near midnight, none during the day. Quantized to 8
        steps (via _night_level) so the cache key stays stable (one overlay per
        night level)."""
        level = self._night_level()
        if level == 0:
            return None
        key = ("night", level)
        ov = self._light_cache.get(key)
        if ov is None:
            a = int(level * 11)   # up to ~88 alpha at the deepest night
            ov = pygame.Surface((1280, 720), pygame.SRCALPHA)
            ov.fill((6, 8, 24, a))
            self._light_cache[key] = ov
        return ov

    def _torch_sprite(self, level):
        """A cached warm radial light pool for the hero torchlight — one per
        night level (reuses the quantized night levels as the cache key so the
        cache doesn't thrash: 8 buckets, built once). A ~280px warm-tinted
        (255,220,160) radial gradient, blitted with BLEND_RGBA_ADD so the pool
        brightens the night overlay without erasing it (a torch glow, not a
        white-out). Intensity scales with the night level (deeper night =
        stronger torch)."""
        key = ("torch", level)
        sp = self._light_cache.get(key)
        if sp is None:
            R = 140
            sp = pygame.Surface((R * 2, R * 2), pygame.SRCALPHA)
            warm = (255, 220, 160)
            for k in range(R, 0, -8):
                a = int(10 * level * (1 - k / R))
                pygame.draw.circle(sp, (*warm, a), (R, R), k)
            self._light_cache[key] = sp
        return sp

    def _draw_edge_hints(self, surf, ox, oy):
        # glowing chevron arrows at traversable map edges, pointing the way out
        c, r = self.c, self.r
        edges = []
        if c > 0:              edges.append((24 - ox, WD.MAP_H // 2 - oy, "left"))
        if c < WD.GRID_W - 1:   edges.append((WD.MAP_W - 24 - ox, WD.MAP_H // 2 - oy, "right"))
        if r > 0:              edges.append((WD.MAP_W // 2 - ox, 24 - oy, "top"))
        if r < WD.GRID_H - 1:   edges.append((WD.MAP_W // 2 - ox, WD.MAP_H - 24 - oy, "bottom"))
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.005)
        col = (int(160 * pulse + 80), int(170 * pulse + 80), 255)
        for (x, y, d) in edges:
            if -60 < x < 1340 and -60 < y < 780:
                self._draw_chevron(surf, int(x), int(y), d, col, pulse)

    def _draw_chevron(self, surf, x, y, d, col, pulse):
        sz = 10 + int(pulse * 4)
        # double chevron for a clearer "exit this way" arrow
        def chev(dx):
            if d == "right":
                pts = [(x - sz + dx, y - sz), (x + sz + dx, y), (x - sz + dx, y + sz)]
            elif d == "left":
                pts = [(x + sz - dx, y - sz), (x - sz - dx, y), (x + sz - dx, y + sz)]
            elif d == "top":
                pts = [(x - sz, y + sz - dx), (x, y - sz - dx), (x + sz, y + sz - dx)]
            else:  # bottom
                pts = [(x - sz, y - sz + dx), (x, y + sz + dx), (x + sz, y - sz + dx)]
            return pts
        pygame.draw.polygon(surf, col, chev(0), 3)
        pygame.draw.polygon(surf, col, chev(sz + 2), 3)

    def _hud_portrait(self, hid, size):
        """Cached HUD portrait — one load per (hero,size) per scene lifetime."""
        key = (hid, size)
        p = self._hud_portraits.get(key)
        if p is None:
            try:
                p = load_char_sprite(hid, size)
            except Exception:
                p = None
            self._hud_portraits[key] = p
        return p

    def _skill_icon(self, sid, size):
        """Cached skill icon — one load per (skill,size) per scene lifetime."""
        key = (sid, size)
        ic = self._skill_icons.get(key)
        if ic is None:
            try:
                ic = load_skill_icon(sid, size)
            except Exception:
                ic = None
            self._skill_icons[key] = ic
        return ic

    def _nearest_objective(self):
        """Return (tc, tr, label, color) for the nearest un-cleared boss cell,
        or the nearest undiscovered cell if all bosses are cleared. O(50) per
        frame (scans the 5 boss cells in the right-most column + up to 50 cells
        for undiscovered ones). Returns None when every boss is cleared and
        every cell is discovered, so the compass hides in the endgame."""
        p = self.game.player
        cleared = set(p.ow_bosses_cleared)
        discovered = set(p.ow_discovered)
        best = None
        best_d2 = None
        # 1. nearest un-cleared boss cell (right-most column, all rows) — gold
        bc = WD.GRID_W - 1
        for r in range(WD.GRID_H):
            cid = WD.cell_id(bc, r)
            if cid in cleared:
                continue
            d2 = (bc - self.c) ** 2 + (r - self.r) ** 2
            if best_d2 is None or d2 < best_d2:
                best_d2 = d2
                best = (bc, r, "Boss", (255, 200, 80))
        if best is not None:
            return best
        # 2. all bosses cleared — fall back to nearest undiscovered cell — cyan
        for r in range(WD.GRID_H):
            for c in range(WD.GRID_W):
                cid = WD.cell_id(c, r)
                if cid in discovered:
                    continue
                d2 = (c - self.c) ** 2 + (r - self.r) ** 2
                if best_d2 is None or d2 < best_d2:
                    best_d2 = d2
                    best = (c, r, "Unexplored", (120, 220, 255))
        return best

    def _draw_hud(self, surf):
        p = self.game.player
        wc = self.party[self.active]
        # active hero panel (top-left) — reuse a persistent panel surface
        if wc:
            hero = wc.hero
            # portrait (cached per-scene so the HUD hot path is one dict lookup)
            port = self._hud_portrait(hero.id, 64)
            panel = self._hud_panel
            panel.fill((0, 0, 0, 0))
            pygame.draw.rect(panel, (20, 20, 40, 200), panel.get_rect(), border_radius=12)
            pygame.draw.rect(panel, (180, 180, 220), panel.get_rect(), 2, border_radius=12)
            surf.blit(panel, (16, 16))
            if port:
                surf.blit(port, (24, 24))
            text(surf, hero.name, 18, (255, 255, 255), (96, 26))
            el_col = D.ELEMENT_COLORS.get(hero.element, ((200, 200, 200),))[0]
            ev_col = hero.evolve_color() if hero.evolve > 0 else el_col
            tier = f"  {hero.evolve_title()}" if hero.evolve > 0 else ""
            text(surf, f"Lv {hero.level}  {hero.element}{tier}", 13, ev_col, (96, 48))
            # HP bar
            draw_bar(surf, (96, 68, 200, 14), hero.hp / max(1, hero.max_hp), (220, 70, 80))
            # energy bar
            draw_bar(surf, (96, 86, 200, 10), hero.energy / max(1, hero.max_energy), (90, 150, 240))
            # HP + energy numerics, right-aligned inside their bars so a 999/999
            # doesn't overflow the 300px panel (was left-aligned at x=302)
            hp_txt = f"{int(hero.hp)}/{hero.max_hp}"
            hp_w = _font(12).size(hp_txt)[0]
            text(surf, hp_txt, 12, (255, 255, 255), (96 + 200 - hp_w - 2, 66), center=False)
            en_txt = f"{int(hero.energy)}/{hero.max_energy}"
            en_w = _font(12).size(en_txt)[0]
            text(surf, en_txt, 10, (200, 220, 255), (96 + 200 - en_w - 2, 84), center=False)
            # low-HP warning pulse on the panel border
            if hero.hp / max(1, hero.max_hp) < 0.3:
                pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.012)
                pygame.draw.rect(surf, (int(220 * pulse), 40, 50),
                                 (16, 16, 300, 90), 3, border_radius=12)

        # party icons (1-4) — Genshin-style slot row with portrait, HP, energy,
        # and a pulsing highlight on the active slot
        for i, wc2 in enumerate(self.party):
            x = 16 + i * 64
            y = 116
            r2 = pygame.Rect(x, y, 56, 56)
            if wc2 is None:
                pygame.draw.rect(surf, (30, 30, 40), r2, border_radius=10)
                pygame.draw.rect(surf, (60, 60, 80), r2, 2, border_radius=10)
                text(surf, str(i + 1), 16, (90, 90, 110), r2.center, center=True)
                continue
            el_col2 = D.ELEMENT_COLORS.get(wc2.hero.element, ((180, 200, 220),))[0]
            is_active = (i == self.active)
            # active slot glows with the element color
            col = el_col2 if is_active else (46, 50, 70)
            pygame.draw.rect(surf, col, r2, border_radius=10)
            border = (240, 240, 255) if is_active else (90, 90, 120)
            bw = 3 if is_active else 1
            pygame.draw.rect(surf, border, r2, bw, border_radius=10)
            try:
                port = self._hud_portrait(wc2.hero.id, 48)
                if port:
                    surf.blit(port, (x + 4, y + 4))
            except Exception:
                pass
            # evolve tier pip (small dot, colored by tier) top-right of the slot
            if wc2.hero.evolve > 0:
                ec = wc2.hero.evolve_color()
                pygame.draw.circle(surf, ec, (x + r2.width - 8, y + 8), 5)
                pygame.draw.circle(surf, (20, 20, 30), (x + r2.width - 8, y + 8), 5, 1)
            # hp mini bar
            draw_bar(surf, (x + 4, y + r2.height - 10, r2.width - 8, 6),
                     wc2.hero.hp / max(1, wc2.hero.max_hp),
                     (220, 70, 80) if wc2.alive else (60, 60, 60))
            text(surf, str(i + 1), 14, (255, 255, 255), (x + 6, y + 2))
            # a thin energy bar under the hp bar so you can see ult readiness
            draw_bar(surf, (x + 4, y + r2.height - 18, r2.width - 8, 4),
                     wc2.hero.energy / max(1, wc2.hero.max_energy), (90, 150, 240))
            if not wc2.alive:
                # dim the slot and mark it down (reused scratch surface)
                dim2 = scratch(r2.width, r2.height)
                dim2.fill((0, 0, 0, 120))
                surf.blit(dim2, r2.topleft)
                text(surf, "DOWN", 12, (255, 80, 80), r2.center, center=True)

        # elemental resonance badges — a row under the party icons showing each
        # active resonance (2+ of the same element). Each badge is a small
        # element-colored pill with the buff short-name + value, so the player
        # sees what their party composition is granting. Hidden when no
        # resonance is active (a rainbow team shows nothing, which is the point —
        # resonance is a reward for committing to an element).
        if self._resonances:
            bx = 16
            by = 178
            for r in self._resonances:
                el = next((e for e, d in D.ELEMENTAL_RESONANCE.items()
                           if d.get("buff") == r.get("buff")), None)
                col = D.ELEMENT_COLORS.get(el, ((180, 200, 220),))[0]
                val_pct = int(r.get("val", 0) * 100)
                # short label per buff kind (kept terse so the row fits 2-3 badges)
                short = {"atk_pct": "ATK", "heal_amp": "HEAL",
                         "move_speed": "SPD", "energy_regen": "ENER",
                         "crit_dmg": "CRIT"}.get(r.get("buff"), "BUFF")
                label = f"{r.get('name', 'Resonance')}  +{val_pct}% {short}"
                fnt_r = _font(12)
                lw = fnt_r.size(label)[0] + 16
                pill = pygame.Rect(bx, by, lw, 22)
                pygame.draw.rect(surf, (20, 20, 30, 200), pill, border_radius=8)
                pygame.draw.rect(surf, col, pill, 2, border_radius=8)
                text(surf, label, 12, col, (bx + 8, by + 4))
                bx += lw + 6

        # top-right: map name (right-aligned to the screen edge so long boss-cell
        # names like "Whispering Woods - Sanctum" don't overflow off-screen)
        fnt = _font(20)
        name = WD.cell_name(self.c, self.r)
        nrt = fnt.render(name, True, (255, 240, 180))
        surf.blit(nrt, (1276 - nrt.get_width(), 20))
        # resources — each currency in its own color (gems blue, gold yellow,
        # shards purple) so the player can glance and distinguish them, stacked
        # right-aligned under the map name
        parts = [(f"Gems {p.gems}", (120, 200, 255)),
                 (f"Gold {p.gold}", (255, 210, 90)),
                 (f"Shards {p.shards}", (200, 160, 255))]
        yy = 44
        for txt, col in parts:
            rt = fnt.render(txt, True, col)
            surf.blit(rt, (1264 - rt.get_width(), yy))
            yy += 22

        # combo counter — only show once a streak is building (>= 2 hits), with
        # a shrinking timer bar so the player feels the window closing. The
        # label shows the damage bonus (count * COMBO_BONUS_PER) so the streak's
        # point is legible, not just a number.
        if self._combo_count >= 2:
            cx = 640
            cy = 120
            bonus = int(self._combo_count * D.COMBO_BONUS_PER * 100)
            label = f"x{self._combo_count}  +{bonus}% DMG"
            col = (255, 220, 80) if self._combo_count < 10 else (255, 120, 120)
            text(surf, label, 26, col, (cx, cy), center=True)
            # timer bar
            bw = 120
            frac = max(0, self._combo_t / self._combo_window)
            bx = cx - bw // 2
            by = cy + 16
            pygame.draw.rect(surf, (30, 30, 40), (bx, by, bw, 6), border_radius=3)
            if frac > 0:
                pygame.draw.rect(surf, col, (bx, by, int(bw * frac), 6), border_radius=3)
            # combo climax: an "EMPOWERED" tag under the combo counter when a
            # milestone flag is active, so the player sees the finisher is armed
            # and knows to spend it before the window expires. Pulses so it
            # reads as an active buff, not a static label.
            if self._skill_empowered or self._ult_empowered:
                pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.01)
                ecol = (int(180 * pulse + 75), int(120 * pulse + 60), int(200 * pulse + 40))
                etag = "EMPOWERED SKILL!" if self._skill_empowered else "EMPOWERED ULT!"
                text(surf, etag, 16, ecol, (cx, by + 14), center=True)

        # boss HP bar at top center if a boss is alive — a dramatic framed bar
        boss = next((e for e in self.enemies if e.is_boss and e.alive), None)
        if boss:
            bw = 640
            bx = (1280 - bw) // 2
            by = 18
            # frame
            pygame.draw.rect(surf, (10, 8, 16), (bx - 6, by - 6, bw + 12, 30), border_radius=8)
            pygame.draw.rect(surf, (60, 20, 30), (bx - 6, by - 6, bw + 12, 30), 2, border_radius=8)
            # segmented HP bar
            frac = boss.enemy.hp / max(1, boss.enemy.max_hp)
            pygame.draw.rect(surf, (30, 14, 22), (bx, by, bw, 18), border_radius=4)
            fw = int(bw * max(0, min(1, frac)))
            if fw > 0:
                pygame.draw.rect(surf, (220, 60, 70), (bx, by, fw, 18), border_radius=4)
                # top gloss (a thin alpha rect, cheaper than a Surface)
                gloss = scratch(fw, 6)
                gloss.fill((255, 255, 255, 50))
                surf.blit(gloss, (bx, by))
            # phase threshold tick marks at 66% and 33% — the same thresholds the
            # WorldEnemy.update phase progression uses (0.66 / 0.33). Drawn as
            # 2px vertical lines in a dim color so the player can read where the
            # next phase transition lands. Drawn over the HP fill so they stay
            # visible at any HP level.
            for t_frac in (0.66, 0.33):
                tx = bx + int(bw * t_frac)
                pygame.draw.line(surf, (40, 40, 50),
                                 (tx, by + 1), (tx, by + 17), 2)
            # phase-transition flash: a white alpha overlay over the boss bar that
            # fades over 0.5s, set in _on_enemy_event on "boss_phase". Gated on
            # reduce_motion (skip the flash, keep the tick marks above).
            if self._boss_phase_flash_t > 0:
                fa = int(140 * (self._boss_phase_flash_t / 0.5))
                fov = scratch(bw, 18)
                fov.fill((255, 255, 255, fa))
                surf.blit(fov, (bx, by))
            # boss name + level, centered over the bar
            text(surf, f"{boss.enemy.name}  Lv {boss.enemy.level}", 18, (255, 230, 230),
                 (640, by + 1), center=True)
            # phase number (right-aligned inside the frame) + numeric HP, so the
            # player can tell which phase the boss is in and how close to death
            ph_txt = f"Phase {boss._boss_phase}/3"
            ph_w = _font(11).size(ph_txt)[0]
            text(surf, ph_txt, 11, (255, 200, 200), (bx + bw - ph_w - 4, by + 2),
                 center=False)
            text(surf, f"{int(boss.enemy.hp)}/{boss.enemy.max_hp} ({int(frac*100)}%)",
                 12, (255, 230, 230), (640, by + 22), center=True)
            # boss toughness bar: a thin 4px white bar under the boss HP frame,
            # shown only after first hit (toughness < max) so an untouched boss
            # doesn't carry visual clutter. When broken, the bar empties and a
            # "BROKEN — +50% DMG" label tells the player the bonus window is open.
            if boss.enemy.has_toughness() and boss.enemy.toughness < boss.enemy.max_toughness:
                tby = by + 24
                tf = max(0, boss.enemy.toughness / max(1, boss.enemy.max_toughness))
                pygame.draw.rect(surf, (20, 20, 30), (bx, tby, bw, 4), border_radius=2)
                if tf > 0 and not boss.enemy.broken:
                    pygame.draw.rect(surf, (235, 235, 245),
                                     (bx, tby, int(bw * tf), 4), border_radius=2)
                if boss.enemy.broken:
                    # cache the label surface (rendered once, reused) so the
                    # per-frame font.render on a broken boss is a dict lookup
                    global _BOKEN_DMG_LABEL_SURF
                    if _BOKEN_DMG_LABEL_SURF is None:
                        _BOKEN_DMG_LABEL_SURF = _font(12).render(
                            "BROKEN — +50% DMG", True, (255, 200, 120))
                    lbl = _BOKEN_DMG_LABEL_SURF
                    surf.blit(lbl, (640 - lbl.get_width() // 2, tby + 6))
            # enraged tag — centered UNDER the boss name so it doesn't collide
            # with the right-aligned resources line (was at bx+bw+14 = 974)
            if getattr(boss, "ult_used", False):
                pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.01)
                col = (int(200 * pulse + 55), 40, 50)
                text(surf, "ENRAGED", 12, col, (640, by + 40), center=True)

        # controls hint (bottom)
        if self.game.player.settings.get("show_hints", True):
            hint = "WASD move | RMB enemy=auto-attack / ground=move | J attack | Q/W/E skills | U/Space ult | 1-4 switch | R potion | M map | G evolve | Esc menu"
            text(surf, hint, 12, (200, 200, 220), (640, 704), center=True)

        # skill bar (bottom-center): Q/W/E + R(ult) with icons + cooldown sweeps
        self._draw_skill_bar(surf)

        # quest tracker (top-right, under the resource counters — y~110, x>900
        # so it clears the boss HP bar at top-center x=320..960). Shows the top
        # daily quest's name + a progress bar + N/goal so the player always sees
        # their active objective. Skipped when no quests are loaded yet (the
        # quest tab calls reset_quests_if_needed; the world scene reads the
        # in-memory dict, which may be empty on a fresh load before the quest
        # tab is opened — guard with .get).
        try:
            p.reset_quests_if_needed()
        except Exception:
            pass
        first_qid = next(iter(D.DAILY_QUESTS), None)
        if first_qid is not None:
            qd = D.DAILY_QUESTS[first_qid]
            st = p.quests.get(first_qid)
            if st is None:
                st = dict(progress=0, claimed=False, goal=qd["goal"])
            prog = st.get("progress", 0)
            goal = st.get("goal", qd["goal"])
            claimed = st.get("claimed", False)
            qx = 1276
            qy = 110
            # panel: right-aligned, ~220 wide so it fits under the resources
            qpanel_w = 220
            qpanel_h = 56
            qpanel = pygame.Rect(qx - qpanel_w, qy, qpanel_w, qpanel_h)
            qp = scratch(qpanel_w, qpanel_h)
            pygame.draw.rect(qp, (20, 20, 36, 200), qp.get_rect(), border_radius=8)
            qcol = (140, 200, 250) if not claimed else (120, 180, 140)
            pygame.draw.rect(qp, qcol, qp.get_rect(), 2, border_radius=8)
            surf.blit(qp, qpanel.topleft)
            text(surf, "QUEST", 10, (160, 160, 200), (qpanel.x + 8, qpanel.y + 4))
            name_col = (200, 220, 180) if claimed else (255, 240, 220)
            text(surf, qd["name"], 13, name_col, (qpanel.x + 8, qpanel.y + 18))
            # progress bar + N/goal
            bar_rect = (qpanel.x + 8, qpanel.y + 36, qpanel_w - 60, 10)
            frac = prog / max(1, goal)
            draw_bar(surf, bar_rect, frac, qcol)
            ng_txt = f"{prog}/{goal}"
            text(surf, ng_txt, 12, (240, 240, 255),
                 (qpanel.x + qpanel_w - 50, qpanel.y + 33), center=False)

        # compass to the nearest objective — a screen-edge arrow pointing toward
        # the nearest un-cleared boss cell (gold) or undiscovered cell (cyan).
        # Reuses _draw_chevron (the same double-chevron the edge hints use).
        # Handles the on-screen case (target in the viewport -> a marker at the
        # target, not an edge arrow) and the all-cleared case (no objective ->
        # hide the compass).
        obj = self._nearest_objective()
        if obj is not None:
            tc, tr, olabel, ocol = obj
            # target world coords = cell center (c*MAP_W + MAP_W/2, r*MAP_H + MAP_H/2)
            tx = tc * WD.MAP_W + WD.MAP_W // 2
            ty = tr * WD.MAP_H + WD.MAP_H // 2
            ox, oy = self.camera.offset()
            sx = tx - ox
            sy = ty - oy
            vw, vh = 1280, 720
            on_screen = (0 <= sx < vw) and (0 <= sy < vh)
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.005)
            if on_screen:
                # target is in the viewport: a pulsing marker ring at the target
                # (not an edge arrow) so the player sees exactly where it is.
                ring = scratch(44, 44)
                a_ring = int(180 * pulse)
                pygame.draw.circle(ring, (*ocol, a_ring), (22, 22), 18, 3)
                surf.blit(ring, (sx - 22, sy - 22))
                pygame.draw.circle(surf, ocol, (int(sx), int(sy)), 4)
            else:
                # target off-screen: a screen-edge arrow pointing toward it.
                # Compute the direction from the screen center to the target's
                # screen pos, then clamp the arrow to the nearest edge.
                cx = vw / 2
                cy = vh / 2
                dx = sx - cx
                dy = sy - cy
                # pick the dominant axis (the edge the arrow sits on) + the
                # chevron direction (left/right/top/bottom) the arrow points.
                margin = 36
                if abs(dx) >= abs(dy):
                    # left or right edge
                    ex = margin if dx < 0 else vw - margin
                    ey = int(cy + dy * (margin / max(1, abs(dx))))
                    ey = max(margin, min(vh - margin, ey))
                    d = "left" if dx < 0 else "right"
                else:
                    # top or bottom edge
                    ey = margin if dy < 0 else vh - margin
                    ex = int(cx + dx * (margin / max(1, abs(dy))))
                    ex = max(margin, min(vw - margin, ex))
                    d = "top" if dy < 0 else "bottom"
                self._draw_chevron(surf, int(ex), int(ey), d, ocol, pulse)
                # a small label under the arrow so the player knows what it points to
                text(surf, olabel, 12, ocol, (int(ex), int(ey) + 22), center=True)

        # minimap (bottom-right) - show current grid position
        self._draw_minimap(surf)

    def _draw_minimap(self, surf):
        """Bottom-right grid minimap. The discovered/undiscovered cells are baked
        into one overlay whenever the discovery set changes (rare) and blitted as
        a single image each frame; only the pulsing current-cell marker is drawn
        live on top."""
        gw, gh = WD.GRID_W, WD.GRID_H
        cell = 16
        ox = 1280 - gw * cell - 28
        oy = 720 - gh * cell - 44
        # frame
        pygame.draw.rect(surf, (20, 20, 36), (ox - 6, oy - 6, gw * cell + 12, gh * cell + 12), border_radius=8)
        pygame.draw.rect(surf, (120, 120, 160), (ox - 6, oy - 6, gw * cell + 12, gh * cell + 12), 2, border_radius=8)
        discovered = self.game.player.ow_discovered
        # rebuild the baked cell overlay only when the discovery set changes
        key = tuple(sorted(discovered))
        base = self._minimap_cache.get(key)
        if base is None:
            base = pygame.Surface((gw * cell, gh * cell), pygame.SRCALPHA)
            for r in range(gh):
                for c in range(gw):
                    x = c * cell
                    y = r * cell
                    cid = WD.cell_id(c, r)
                    if cid in discovered:
                        biome = WD.BIOMES[WD.cell_biome(c, r)]
                        col = biome["ground"]
                        if WD.is_boss_cell(c, r):
                            col = (200, 80, 80)
                        pygame.draw.rect(base, col, (x, y, cell - 2, cell - 2))
                    else:
                        pygame.draw.rect(base, (40, 40, 50), (x, y, cell - 2, cell - 2))
            self._minimap_cache[key] = base
        surf.blit(base, (ox, oy))
        # pulsing current-position marker (drawn live, one cell)
        cx = ox + self.c * cell
        cy = oy + self.r * cell
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.006)
        pygame.draw.rect(surf, (255, 255, 120), (cx - 1, cy - 1, cell, cell), 2)
        pygame.draw.circle(surf, (255, 240, 120),
                           (cx + cell // 2 - 1, cy + cell // 2 - 1),
                           2 + int(pulse * 2))

    def _draw_skill_bar(self, surf):
        """Bottom-center LoL-style skill bar: Q/W/E + R (ultimate).
        Each slot shows the skill icon, a key hint, and a radial/wedge cooldown
        sweep. R glows when the ultimate is ready; Q/W/E dim when out of energy."""
        wc = self.party[self.active]
        if not wc:
            return
        slot = 56
        gap = 10
        # 4 slots: Q, W, E, R  (R is the ultimate, separated by a bigger gap)
        n = 4
        total = n * slot + (n - 1) * gap + 8  # +8 for the R-separator gap
        ux = (1280 - total) // 2
        uy = 720 - slot - 56
        keys = ["Q", "W", "E", "R"]
        # gather skill ids: Q/W/E from ability list, R = ultimate
        abilities = wc.skill_list()
        ult_id = wc.hero.ultimate
        ids = [abilities[0] if len(abilities) > 0 else None,
               abilities[1] if len(abilities) > 1 else None,
               abilities[2] if len(abilities) > 2 else None,
               ult_id]
        # back panel behind the whole bar for readability (covers passive chip too)
        pad = 12
        panel = pygame.Rect(ux - pad - 170, uy - pad, total + 2 * pad + 170,
                            slot + 2 * pad)
        ppanel = scratch(panel.width, panel.height)
        pygame.draw.rect(ppanel, (16, 14, 28, 190), ppanel.get_rect(), border_radius=12)
        pygame.draw.rect(ppanel, (90, 90, 130), ppanel.get_rect(), 2, border_radius=12)
        surf.blit(ppanel, panel.topleft)
        for i, sid in enumerate(ids):
            x = ux + i * (slot + gap) + (8 if i == 3 else 0)
            r = pygame.Rect(x, uy, slot, slot)
            is_ult = (i == 3)
            # slot background
            pygame.draw.rect(surf, (18, 18, 30), r, border_radius=10)
            # readiness
            if is_ult:
                ready = wc.can_ultimate()
            else:
                ready = wc.can_skill(i) if sid else False
            border = (255, 220, 120) if (ready and is_ult) else \
                     (140, 200, 250) if ready else (80, 80, 100)
            pygame.draw.rect(surf, border, r, 2, border_radius=10)
            # icon (cached per-scene so the bar hot path is one dict lookup)
            if sid:
                ic = self._skill_icon(sid, slot - 10)
                if ic is not None:
                    surf.blit(ic, (r.x + 5, r.y + 5))
                else:
                    text(surf, "?", 20, (200, 200, 220), r.center, center=True)
            else:
                text(surf, "-", 20, (90, 90, 110), r.center, center=True)
            # cooldown sweep: a dark wedge that shrinks as the cd counts down
            cd = wc.skill_cd[i] if not is_ult else wc.ult_cd
            cd_max = wc.skill_cd_max[i] if not is_ult else 1.0
            if cd > 0 and cd_max > 0:
                frac = cd / cd_max
                # overlay a dark rect covering the top fraction, shrinking down
                ch = int(slot * frac)
                ov = scratch(slot, ch)
                ov.fill((0, 0, 0, 160))
                surf.blit(ov, (r.x, r.y))
                # big cd number
                text(surf, f"{cd:.1f}", 18, (255, 255, 255), r.center, center=True)
            elif not is_ult and sid and not wc.hero.can_use_skill(sid):
                # not enough energy: a blue tint + the energy cost hint
                ov = scratch(slot, slot)
                ov.fill((20, 30, 70, 120))
                surf.blit(ov, r.topleft)
                cost = wc.hero.skill_energy_cost(sid)
                text(surf, f"{cost}", 12, (160, 200, 255), r.center, center=True)
            # key hint badge (bottom-left of the slot)
            kx, ky = r.x + 3, r.bottom - 18
            pygame.draw.rect(surf, (30, 30, 46), (kx, ky, 16, 15), border_radius=4)
            pygame.draw.rect(surf, (160, 160, 200), (kx, ky, 16, 15), 1, border_radius=4)
            text(surf, keys[i], 12, (240, 240, 255), (kx + 8, ky + 1))
            # ultimate ready glow pulse
            if is_ult and ready:
                pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.008)
                glow = scratch(slot + 16, slot + 16)
                pygame.draw.rect(glow, (255, 220, 120, int(60 * pulse)),
                                 glow.get_rect(), border_radius=12)
                surf.blit(glow, (r.x - 8, r.y - 8))
            # hover tooltip (Task B1): when the mouse is over a skill slot, draw a
            # tooltip panel above the slot with the skill's name/category/cost/cd/
            # description/how_to_use — read from the HERO_ASSETS manifest. Cached
            # per (hero_id, idx, affordable) so the panel isn't re-rendered every
            # frame while hovered. Grows upward from the skill bar (bottom) so it
            # never overlaps the boss HP bar at top-center. Display only — does
            # not block clicks. Instant under reduce_motion (no fade).
            if r.collidepoint(pygame.mouse.get_pos()):
                self._draw_skill_tooltip(surf, wc, i, sid, r, ready)
        # passive indicator (a small labeled chip to the left of the bar)
        pv = wc.hero.passive
        if pv:
            chip_w = 150
            cx0 = ux - chip_w - 14
            cy0 = uy + 6
            cr = pygame.Rect(cx0, cy0, chip_w, slot - 2)
            pygame.draw.rect(surf, (24, 22, 40), cr, border_radius=8)
            pygame.draw.rect(surf, (140, 200, 160), cr, 1, border_radius=8)
            text(surf, "PASSIVE", 10, (160, 220, 180), (cr.x + 6, cr.y + 3))
            text(surf, pv["name"], 12, (220, 240, 220), (cr.x + 6, cr.y + 18))
            # word-wrap the desc into 2 lines so the meaning isn't cut mid-word
            # (was [:20] which yielded 'Heal for 12% of basi')
            desc = pv["desc"]
            text(surf, desc[:24], 9, (170, 190, 170), (cr.x + 6, cr.y + 33))
            if len(desc) > 24:
                text(surf, desc[24:48], 9, (170, 190, 170), (cr.x + 6, cr.y + 44))

    def _draw_skill_tooltip(self, surf, wc, idx, sid, slot_rect, ready):
        """Hover tooltip for one skill slot (Task B1). Reads the skill's
        name/category/element/cost/cd/description/how_to_use from the HERO_ASSETS
        manifest (the single source — Task A2). Cached per (hero_id, idx,
        affordable, cd_bucket) so the panel isn't re-rendered every frame while
        hovered (the cd line changes each second, so bucket the cd to 0.5s).
        Grows upward from the skill bar so it never overlaps the boss HP bar."""
        if not sid:
            return
        # resolve the skill's presentation from the manifest (fallback to
        # SKILLS_DB if the hero isn't in HERO_ASSETS — graceful, no crash)
        ha = D.HERO_ASSETS.get(wc.hero.id)
        entry = None
        if ha:
            for s in ha["skills"]:
                if s["id"] == sid:
                    entry = s; break
        if entry is None:
            sk = D.SKILLS_DB.get(sid, {})
            entry = {"id": sid, "name": sk.get("name", sid),
                     "category": sk.get("category", sk.get("type", "").title()),
                     "type": sk.get("type", ""), "cost": sk.get("cost", 0),
                     "element": sk.get("element", wc.hero.element),
                     "description": sk.get("desc", ""), "how_to_use": ""}
        else:
            # the manifest entry doesn't carry element/cd (they're hero-level /
            # runtime) — add them so the tooltip can show element + cooldown.
            entry = dict(entry)
            entry.setdefault("element", wc.hero.element)
        # the runtime cooldown for this slot (Q/W/E = skill_cd, R = ult_cd)
        is_ult = (idx == 3)
        cd = wc.ult_cd if is_ult else wc.skill_cd[idx]
        entry["cd"] = cd
        # cache key: (hero_id, idx, affordable, cd_bucket) — re-render only when
        # the affordability flips OR the cd crosses a 0.5s bucket (the cd line
        # text changes each 0.5s, not every frame). Cap the cache so a long
        # session doesn't grow it unbounded.
        ck = (wc.hero.id, idx, bool(ready), int(cd * 2))
        cached = self._tooltip_cache.get(ck)
        if cached is None:
            panel = self._build_skill_tooltip_surf(entry, ready)
            self._tooltip_cache[ck] = panel
            if len(self._tooltip_cache) > 128:
                self._tooltip_cache.clear()
            cached = panel
        pw, ph = cached.get_size()
        # place above the slot, centered on the slot's x, clamped to the screen
        px = max(8, min(1280 - pw - 8, slot_rect.centerx - pw // 2))
        py = max(8, slot_rect.y - ph - 8)
        surf.blit(cached, (px, py))

    def _build_skill_tooltip_surf(self, entry, ready):
        """Build (once per cache key) the tooltip surface for one skill."""
        pw, pad = 230, 10
        # measure the content height: name(20) + cat/element/cost line(14) +
        # cd line(14) + description (word-wrapped, 12) + how_to_use (12) + spacing
        name = entry.get("name", "")
        cat = entry.get("category", "")
        desc = entry.get("description", "")
        how = entry.get("how_to_use", "")
        cost = entry.get("cost", 0)
        element = entry.get("element", "")
        cd = entry.get("cd", None)
        # word-wrap the description at ~30 chars (the panel inner width)
        desc_lines = _wrap(desc, 30) if desc else []
        how_lines = _wrap(how, 30) if how else []
        # height: header(24) + cat/element/cost(18) + cd(18) + desc + how + pads
        ph = (pad * 2 + 24 + 18 + 18
              + max(1, len(desc_lines)) * 16
              + max(1, len(how_lines)) * 16 + 8)
        s = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(s, (16, 14, 28, 225), s.get_rect(), border_radius=10)
        border = (255, 220, 120) if ready else (140, 160, 200)
        pygame.draw.rect(s, border, s.get_rect(), 2, border_radius=10)
        y = pad
        text(s, name, 18, (245, 240, 220), (pad, y))
        y += 24
        # category badge (left) + cost (right-aligned) on one line
        cat_col = (180, 200, 255)
        text(s, f"[{cat}]", 13, cat_col, (pad, y))
        cost_col = (160, 220, 255) if ready else (220, 160, 160)
        cost_txt = f"cost {cost}"
        cost_w = _font(13).size(cost_txt)[0]
        text(s, cost_txt, 13, cost_col, (pw - pad - cost_w, y))
        y += 18
        # element (left) + cooldown (right-aligned) on one line
        el_col = D.ELEMENT_COLORS.get(element, ((200, 200, 220),))[0] if element else (160, 160, 180)
        text(s, element.title() if element else "-", 13, el_col, (pad, y))
        if cd is not None and cd > 0:
            cd_txt = f"cd {cd:.1f}s"
            cd_w = _font(13).size(cd_txt)[0]
            text(s, cd_txt, 13, (220, 200, 180), (pw - pad - cd_w, y))
        else:
            ready_txt = "ready" if ready else "charging"
            rw = _font(13).size(ready_txt)[0]
            text(s, ready_txt, 13, (180, 220, 200) if ready else (200, 180, 160),
                 (pw - pad - rw, y))
        y += 18
        for line in desc_lines or [""]:
            text(s, line, 12, (210, 210, 230), (pad, y))
            y += 16
        y += 4
        for line in how_lines or [""]:
            text(s, line, 12, (180, 220, 200), (pad, y))
            y += 16
        return s


# ---------------------------------------------------------------------------
# Weapon style lookup (hero id -> weapon) from generate_assets HEROES list
# ---------------------------------------------------------------------------
def WEAPON_STYLE_KEY(hero_id):
    # mirror of generate_assets.HEROES weapon field
    weapons = {
        "aria": "sword", "kael": "sword", "mira": "staff", "zephyr": "bow",
        "luna": "dagger", "pyra": "staff", "lyra": "orb", "thorne": "shield",
        "sera": "staff", "rune": "orb", "blaze": "sword", "nami": "orb",
        "gale": "bow", "vex": "dagger", "ember": "sword", "tide": "shield",
        "zephyra": "bow", "selene": "sword", "nox": "orb", "cinder": "sword",
        "mist": "dagger", "sol": "orb", "gaia": "shield", "echo": "orb",
        "raven": "dagger",
    }
    return weapons.get(hero_id, "sword")
