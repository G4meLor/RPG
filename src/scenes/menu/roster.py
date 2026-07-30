"""Roster scene."""
import pygame

from src.core.scene import Scene
from src.ui import (WIDTH, HEIGHT, WHITE, DIM, GOLD, BG_DARK, Button, draw_panel,
                    draw_stars, text, f)
from src.entities import load_char_sprite, load_portrait, load_ui
import data as D
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
            try:
                self.portrait_cache[hid] = load_portrait(hid, 0, 220)
            except Exception:
                self.portrait_cache[hid] = load_char_sprite(hid, 220)
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
                try:
                    p = load_portrait(hid, 0, 44)
                except Exception:
                    p = load_char_sprite(hid, 44)
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


