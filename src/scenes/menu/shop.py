"""Shop scene."""
import pygame

from src.core.scene import Scene
from src.ui import (WIDTH, HEIGHT, WHITE, DIM, GOLD, Button, draw_panel, text, f,
                    dim_overlay as _dim_overlay, rarity_color)
from src.entities import load_bg, load_item_icon
from src.data.consumables import CONSUMABLES_DB
from src.data.equipment import EQUIPMENT_DB
from src.data.shop import SHOP_GEMS
import audio
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
        for i, (iid, item) in enumerate(CONSUMABLES_DB.items()):
            col = i % 5
            row = i // 5
            r = pygame.Rect(80 + col * 220, 180 + row * 180, 200, 160)
            self.consumable_rects.append((iid, r))
        # equipment — offset by the scroll so all 17 items are reachable
        self.equip_rects = []
        for i, (iid, item) in enumerate(EQUIPMENT_DB.items()):
            col = i % 5
            row = i // 5
            r = pygame.Rect(80 + col * 220, 470 + row * 180 - self.equip_scroll, 200, 160)
            self.equip_rects.append((iid, r))
        # gem packs
        self.gem_rects = []
        for i, offer in enumerate(SHOP_GEMS):
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
                rows = (len(EQUIPMENT_DB) + 4) // 5
                max_scroll = max(0, 470 + (rows - 1) * 180 + 160 - HEIGHT)
                self.equip_scroll = max(0, min(max_scroll, self.equip_scroll - e.y * 40))
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for iid, r in self.consumable_rects:
                    if r.collidepoint(e.pos):
                        if self.game.player.buy_consumable(iid):
                            self.toast = f"Bought {CONSUMABLES_DB[iid]['name']}!"
                            self.toast_t = 1.5
                            audio.play("menu_click")
                        else:
                            self.toast = "Not enough gold!"
                            self.toast_t = 1.2
                        return
                for iid, r in self.equip_rects:
                    if r.collidepoint(e.pos):
                        if self.game.player.buy_equipment(iid):
                            self.toast = f"Bought {EQUIPMENT_DB[iid]['name']}!"
                            self.toast_t = 1.5
                            audio.play("menu_click")
                        else:
                            self.toast = "Not enough gold!"
                            self.toast_t = 1.2
                        return
                for oid, r in self.gem_rects:
                    if r.collidepoint(e.pos):
                        if self.game.player.buy_gems(oid):
                            offer = next(o for o in SHOP_GEMS if o["id"] == oid)
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
            item = CONSUMABLES_DB[iid]
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
            item = EQUIPMENT_DB[iid]
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
            offer = next(o for o in SHOP_GEMS if o["id"] == oid)
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


