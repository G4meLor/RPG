"""Title scene."""
import math
import random

import pygame

from src.core.scene import Scene
from src.ui import (WIDTH, HEIGHT, GOLD, Button, draw_panel, text, f)
from src.ui import scratch as _scratch
from src.entities import load_bg
class TitleScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.bg = load_bg("title")
        self.bg = pygame.transform.smoothscale(self.bg, (WIDTH, HEIGHT))
        self.t = 0
        # Aetheric Cycle: when the final boss (Demon King at 9,4) is cleared,
        # show an "Ascend World" button so the player can reset the world for
        # NG+ (keeping heroes/equipment, scaling enemy levels per cycle). The
        # button is appended after the base 7 so the main menu stays familiar;
        # its index is stored because the list is rebuilt each __init__.
        self._ascend_idx = None
        # D3: the single "Enter World" button is split into two mode buttons —
        # "Adventure" (left, warm/fire tone; the 10-min wave-survival mode that
        # routes to AdventureScene) + "Endless" (right, green/world tone; the
        # open-world + story mode that routes to WorldScene). Both are 116x44 so
        # a one-line description fits in the 8px gap above the Heroes button; the
        # meta menus (Heroes/Summon/Shop/Codex/Records/Settings) keep their y
        # positions, so indices shift by +1 (they were 1-6, now 2-7).
        self.buttons = [
            Button((WIDTH // 2 - 120, 300, 116, 44), "Adventure", (130, 70, 50), (180, 100, 70), size=20),
            Button((WIDTH // 2 + 4, 300, 116, 44), "Endless", (70, 120, 90), (110, 180, 130), size=20),
            Button((WIDTH // 2 - 120, 364, 240, 56), "Heroes", (90, 80, 50), (160, 130, 70)),
            Button((WIDTH // 2 - 120, 428, 240, 56), "Summon", (90, 60, 130), (140, 90, 200)),
            Button((WIDTH // 2 - 120, 492, 240, 56), "Shop", (70, 90, 130), (100, 130, 190)),
            Button((WIDTH // 2 - 120, 556, 240, 56), "Codex", (70, 110, 90), (110, 170, 130)),
            Button((WIDTH // 2 - 120, 620, 240, 56), "Records", (60, 70, 110), (90, 110, 160), size=20),
            Button((WIDTH // 2 - 120, 676, 240, 40), "Settings", (110, 90, 60), (170, 140, 80), size=18),
        ]
        if self.game.player.can_ascend_world():
            # place it just under the Settings button so the base layout is
            # unchanged; a gold-toned button so it reads as a world-tier action
            self.buttons.append(
                Button((WIDTH // 2 - 120, 724, 240, 44), "Ascend World",
                       (130, 90, 40), (200, 150, 70), size=20))
            self._ascend_idx = len(self.buttons) - 1
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
            # D3: buttons[0] = Adventure, buttons[1] = Endless (each sets
            # player.mode + routes via goto("world"), which _make_scene routes
            # by mode to AdventureScene or WorldScene). The meta menus shift
            # by +1 (Heroes was buttons[1], now buttons[2], etc.).
            if self.buttons[0].clicked(e):
                self.game.player.mode = "adventure"; self.game.player.save()
                self.game.goto("world")
            if self.buttons[1].clicked(e):
                self.game.player.mode = "endless"; self.game.player.save()
                self.game.goto("world")
            if self.buttons[2].clicked(e):
                self.game.goto("roster")
            if self.buttons[3].clicked(e):
                self.game.goto("gacha")
            if self.buttons[4].clicked(e):
                self.game.goto("shop")
            if self.buttons[5].clicked(e):
                self.game.goto("codex")
            if self.buttons[6].clicked(e):
                self.game.goto("stats")
            if self.buttons[7].clicked(e):
                self.game.goto("settings")
            # Aetheric Cycle: "Ascend World" resets the world for NG+ and
            # drops the player into the fresh world at (0,0) on cycle N+1.
            if self._ascend_idx is not None and self.buttons[self._ascend_idx].clicked(e):
                self.game.player.reset_world_for_ng()
                self.game.player.save()
                # rebuild the title so the Ascend button hides itself (the
                # final boss is no longer cleared after the reset) and the
                # cycle label updates
                self.buttons = [b for i, b in enumerate(self.buttons)
                                if i != self._ascend_idx]
                self._ascend_idx = None
                self.game.goto("world")

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
        # D3: one-line mode descriptions under the two mode buttons (subtle, dim,
        # small) so the player sees what each mode is without a tooltip. The 20px
        # gap between the mode buttons (bottom y=344) and Heroes (top y=364) fits
        # a size-13 line centered at y=354.
        text(surf, "10-min wave survival", 13, (200, 170, 150),
             (WIDTH // 2 - 62, 354), center=True)
        text(surf, "Open world + story", 13, (170, 200, 180),
             (WIDTH // 2 + 62, 354), center=True)
        text(surf, f"Gems: {self.game.player.gems}   Gold: {self.game.player.gold}", 18, GOLD,
             (WIDTH // 2, 280), center=True)
        # Aetheric Cycle: show the current NG+ cycle under the gems/gold line
        # so the player sees their progress on the title screen (Cycle 1+ only;
        # a first play stays quiet so the label doesn't read as a regression).
        if self.game.player.ng_cycle > 0:
            text(surf, f"Cycle {self.game.player.ng_cycle}", 22, (255, 220, 140),
                 (WIDTH // 2, 768), center=True)
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


