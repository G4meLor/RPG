"""Map renderer — bakes a map's ground + decorations to one Surface.

Extracted from src/scenes/world.py (Task 14, Phase 4 ECS restructure).
The renderer is a pure cache of per-cell Surfaces keyed by "c,r"; it owns no
scene state. MapRenderer is imported by both WorldScene (for the pre-warm +
the per-frame map blit) and MapController (which owns the renderer instance).
"""
import math
import random

import pygame

import src.world.data as WD


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
