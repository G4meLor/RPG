"""Inventory scene."""
import pygame

from src.core.scene import Scene
from src.ui import (WIDTH, HEIGHT, WHITE, DIM, GOLD, BG_DARK, Button, draw_panel,
                    text, f, rarity_color)
from src.entities import load_item_icon
from src.data.consumables import CONSUMABLES_DB
from src.data.equipment import EQUIPMENT_DB
import audio
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
                            self.toast = f"Sold {CONSUMABLES_DB[iid]['name']}!"
                            self.toast_t = 1.4
                            audio.play("menu_click")
                        return

    def _use_consumable(self, iid):
        """Apply a consumable to the world party (heal/restore the active hero,
        or all for elixir). Returns a toast string."""
        p = self.game.player
        item = CONSUMABLES_DB.get(iid)
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
            item = CONSUMABLES_DB.get(iid)
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
                item = EQUIPMENT_DB.get(item_id)
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
