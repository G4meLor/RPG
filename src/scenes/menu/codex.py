"""Codex scene."""
import pygame

from src.core.scene import Scene
from src.ui import (WIDTH, HEIGHT, WHITE, GOLD, BG_DARK, Button, draw_panel,
                    draw_stars, text, f, get_font, scratch as _scratch)
from src.entities import load_char_sprite, load_portrait, load_ui
from src.data.heroes import HEROES_DB, HERO_ASSETS, HERO_LORE
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
            # doesn't smoothscale 170 portraits every frame. The default-skin
            # splash (skin 0) is the codex headshot.
            try:
                pr = pygame.transform.smoothscale(load_portrait(hid, 0, 160), (130, 130))
            except Exception:
                pr = pygame.transform.smoothscale(load_char_sprite(hid, 160), (130, 130))
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
                rows = (len(HEROES_DB) + 6) // 7
                content_h = rows * (200 + 16)
                max_scroll = max(0, content_h - (HEIGHT - 130 - 40))
                self.scroll = max(0, min(self.scroll - e.y * 40, max_scroll))

    def draw(self, surf):
        surf.fill(BG_DARK)
        p = self.game.player
        text(surf, "Codex", 40, WHITE, (WIDTH // 2, 40), center=True)
        text(surf, f"Collected {len(p.owned)}/{len(HEROES_DB)} heroes", 20, GOLD,
             (WIDTH // 2, 80), center=True)
        all_heroes = HEROES_DB
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
        # (Task A2) read the bio from HERO_ASSETS — the single source of truth —
        # falling back to HERO_LORE only if the manifest is somehow missing.
        if hovered_id is not None and hovered_rect is not None and hovered_id in p.owned:
            ha = HERO_ASSETS.get(hovered_id)
            lore = ha["lore"] if ha else HERO_LORE.get(hovered_id)
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
