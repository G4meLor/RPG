"""Gacha scene."""
import math
import random

import pygame

from src.core.scene import Scene
from src.ui import (WIDTH, HEIGHT, WHITE, DIM, GOLD, Button, draw_panel, draw_stars,
                    text, f, dim_overlay as _dim_overlay, scratch as _scratch)
from src.entities import load_char_sprite, load_portrait, load_ui
from gacha import GachaSystem
import data as D
import audio
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
                # start the 1.6s rising tension drone on its dedicated channel
                # so it crescendos toward the reveal and can be stopped cleanly
                # at the reveal (or the skip branch) without leaking.
                audio.play_gacha_tension(0.5)
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
                # stop the tension drone the moment the reveal fires (the
                # crescendo peaks at exactly 1.6s to match this gate) so the
                # drone resolves into the fanfare instead of overlapping it.
                audio.stop_gacha_tension()
                # opening reveal fanfare scaled to the BEST rarity in the batch
                # (not the first card) so an SSR buried later still triggers the
                # strong cue. Replaces the generic gacha_reveal+victory reuse
                # with a dedicated rarity-scaled fanfare cue.
                _rank = {"SSR": 3, "SR": 2, "R": 1}
                best = max(self.results, key=lambda r: _rank.get(r[1], 1))[1] if self.results else "R"
                audio.play("gacha_fanfare_" + best.lower(), 0.8)
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
                            audio.play("gacha_fanfare_ssr", 0.8)
                        elif nrar == "SR":
                            audio.play("gacha_fanfare_sr", 0.5)
                        else:
                            audio.play("gacha_fanfare_r", 0.3)
                        self._seed_reveal_burst(nrar)
                    else:
                        self.state = "idle"; self.results = []
                    return
                # Esc / right-click skips the whole reveal (summary is retained)
                if (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE) or \
                   (e.type == pygame.MOUSEBUTTONDOWN and e.button == 3):
                    # stop the tension drone so the drone doesn't leak past the
                    # skip (the reveal branch already stops it, but the skip
                    # branch bypasses the reveal so it must stop here too).
                    audio.stop_gacha_tension()
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
            try:
                fp = load_portrait(feat, 0, 200)
            except Exception:
                fp = load_char_sprite(feat, 200)
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
        # the real LoL splash art (the default skin's 380x380 square) fills the
        # reveal card — the "wow" moment with the champion's actual splash.
        # The procedural world sprite stays for the in-game billboard; the
        # splash is the reveal + codex + hero-detail art.
        card_size = int(cw * 0.9)
        try:
            p = load_portrait(hid, 0, card_size)
        except Exception:
            p = load_char_sprite(hid, card_size)
        p2 = pygame.transform.smoothscale(p, (card_size, int(card_size * p.get_height() / p.get_width())))
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



