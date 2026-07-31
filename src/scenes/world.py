"""
Aetheria Open World - World Scene
The real-time open-world scene: input, update loop, edge transitions, combat,
pickups, drawing, HUD, teleport overlay, and the in-world pause hub.
"""
import math
import random
import time

import pygame

from src.data.consumables import CONSUMABLES_DB
from src.data.elements import ELEMENT_COLORS, REACTION_WINDOW, WET_EFFECT, reaction_for
from src.data.enemies import ENEMIES_DB
from src.data.equipment import EQUIPMENT_DB
from src.data.evolution import EVO_LINKS, EVO_NODE_POS, evo_node_prereq_met, hero_evo_tree
from src.data.heroes import HERO_ASSETS, HERO_BY_ID, HERO_PASSIVES, ULTIMATE_VARIANTS, _get_champion_enemy_pool
from src.data.passives import PASSIVES_DB
from src.data.progression import ACHIEVEMENTS, DAILY_QUESTS, LANDMARK_LORE, LORE_FRAGMENTS
from src.data.resonance import ELEMENTAL_RESONANCE, team_resonances
from src.data.roles import ROLES
from src.data.skills import BOSS_ULT, SKILLS_DB
from src.data.story import NPCS, STORY_BIOME_QUEST, STORY_FINAL_QUEST, STORY_QUEST_BY_ID, STORY_QUEST_ORDER
from src.data.tuning import AA_CD, AA_RANGE, COMBO_BONUS_PER, COMBO_MAX, COMBO_MILESTONE_SKILL, COMBO_MILESTONE_ULT, ENERGY_GAIN_BASIC, ENERGY_GAIN_DEAL, ENERGY_START, element_mult
from src.entities import (load_char_sprite, load_skill_icon,
                      load_drop, load_terrain, load_landmark, load_village)
import src.audio as audio
import src.fx as fx
import src.world.data as WD
from src.entities import (Camera, Particles, Particle, Projectile, FloatText,
                            WorldCharacter, WorldEnemy, WEAPON_STYLE, scratch,
                            SummonAlly, Trap)
from src.world.map_renderer import MapRenderer
from src.systems.map_ctrl import MapController
from src.systems.physics import PhysicsSystem
# ECS entity layer (Task 12): the adapter keeps a parallel World of entities
# in sync with the legacy WorldCharacter/WorldEnemy objects. The legacy path
# stays the source of truth this phase; the entity layer only tracks state.
from src.core.world import World
from src.entities.hero import spawn_hero
from src.entities.enemy import spawn_enemy
from src.entities.components import Transform, Health, ChampionRef


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
    col = ELEMENT_COLORS.get(wc.element, ((200, 200, 200),))[0]
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


# Button + draw_bar come from ui.py (the shared UI-primitives module). This
# used to import from main, which forced a main <-> world_scene circular
# dependency; ui.py has no such cycle.
from src.ui import Button, draw_bar


# Sentinel for the village-cell cache (None is a valid cached value — "no
# village in this biome" — so the cache uses a distinct sentinel to tell
# "cached None" from "not yet cached"). Module-level so the id is stable.
_VILLAGE_SENTINEL = object()



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
        col, row = EVO_NODE_POS.get(node_id, (1, 0))
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
            hd = HERO_BY_ID[hid]
            tree = hero_evo_tree(hd)
            node = next((n for n in tree if n["id"] == node_id), None)
            name = node["name"] if node else node_id
            self.flash = f"Unlocked: {name}!"
            self.flash_t = 2.5
            audio.play("buff", 0.6)
        else:
            # figure out why not
            hd = HERO_BY_ID[hid]
            tree = hero_evo_tree(hd)
            node = next((n for n in tree if n["id"] == node_id), None)
            unlocked = set(p.owned[hid].get("evo_nodes", []))
            if node and not evo_node_prereq_met(node, unlocked):
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
        # load_char_sprite is imported at module top (entities).
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
        hd = HERO_BY_ID[hid]
        h = p.get_hero_instance(hid)
        tree = hero_evo_tree(hd)
        unlocked = set(p.owned[hid].get("evo_nodes", []))
        ox, oy = self._tree_origin()
        # panel
        panel = pygame.Rect(ox - 20, oy - 30, 620, 470)
        pygame.draw.rect(surf, (24, 20, 40), panel, border_radius=14)
        pygame.draw.rect(surf, (150, 130, 200), panel, 2, border_radius=14)
        text(surf, f"{h.name} - {ROLES.get(h.role, {}).get('name', h.role)} Tree",
             20, (255, 240, 180), (panel.centerx, oy - 12), center=True)
        # links
        for a, b in EVO_LINKS:
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
                pname = PASSIVES_DB.get(pid, {}).get("name", pid)
                base_pid = HERO_PASSIVES.get(hid)
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
            pname = PASSIVES_DB.get(pid, {}).get("name", pid)
            text(surf, f"Passive: {pname}", 12, (180, 220, 255),
                 (panel.x + 16, by + 34))


# Font + rendered-text + dim-overlay helpers live in ui.py now (one shared
# cache instead of a per-module copy). Alias them under the names this module
# already uses so the ~80 internal call sites stay unchanged.
from src.ui import get_font as _font, text, dim_overlay
from src.ui import _TEXT_CACHE  # noqa: F401 (shared cache; kept warm here too)

def _overlay_dim():
    """Back-compat wrapper: the world scene's modals want the fixed alpha-170
    1280x720 overlay. ui.dim_overlay(alpha=170) returns exactly that (cached)."""
    return dim_overlay(170)

# Cached "BROKEN — +50% DMG" label for the boss bar — rendered once and reused
# so a broken boss doesn't re-render the string every frame (font.render is a
# top profile cost). Lazily filled on first broken-boss draw.
_BOKEN_DMG_LABEL_SURF = None


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
        # MapController (Task 14, Phase 4) owns the map grid state (c, r,
        # _map_data, map_renderer, _village, _landmark, _rift_*) + the
        # load_map / transition / teleport_to / discover_neighbors methods.
        # Constructed BEFORE the rift/village/landmark field inits below +
        # BEFORE _load_map: the controller owns those fields now, but the rest
        # of WorldScene reads them via the settable delegate properties at the
        # bottom of this class (c / r / _map_data / map_renderer / _village /
        # _landmark / _rift_*). The controller's __init__ reads p.ow_current
        # + ensures discovered, so the legacy lines that did that are gone.
        self.map_ctrl = MapController(self)
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
        # NOTE: these are now owned by MapController; the lines below are kept
        # as no-op comments for the init-order audit trail. The delegate
        # properties at the bottom of this class read+write through to
        # self.map_ctrl.
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

        # ECS entity layer (Task 12): a parallel World of entities that tracks
        # the legacy WorldCharacter/WorldEnemy objects. The legacy path stays
        # the source of truth; the entity layer is ADDITIVE (parallel tracking).
        # _entity_for_hero maps hero_id -> Entity; _entity_for_enemy maps
        # id(legacy WorldEnemy) -> Entity. Initialized BEFORE _build_party so
        # _build_party can spawn hero entities into self.world.
        self.world = World()
        self._entity_for_hero = {}   # hero_id -> Entity (party)
        self._entity_for_enemy = {}  # id(legacy WorldEnemy) -> Entity
        # PhysicsSystem (Phase 4, Task 15): the ECS movement/collision system.
        # Runs IN PARALLEL with the legacy WorldCharacter.update movement path
        # (the legacy path stays the source of truth this task; the adapter's
        # _sync_entities still copies legacy wc.x/y onto entity Transform AFTER
        # update, so the PhysicsSystem writes may be overwritten by the sync).
        # The point is to PROVE the PhysicsSystem logic works in isolation.
        # Full takeover of movement from the legacy object happens in Task 20.
        self.physics = PhysicsSystem(self.world, self)

        # AISystem (Task 16): per-enemy AI driving entity Transform/AI. Runs IN
        # PARALLEL with legacy WorldEnemy.update (additive) — the legacy path
        # stays the source of truth until Task 20 (full takeover).
        from src.systems.ai import AISystem
        self.ai = AISystem(self.world, self)

        # CombatSystem (Task 17): ECS combat on entities — basic_attack,
        # use_skill, use_ultimate, on_hit, on_death. Runs IN PARALLEL with the
        # legacy _do_attack/_do_skill/_do_ultimate/_on_enemy_hit/_on_enemy_death
        # (additive) — the legacy path stays the source of truth until Task 20
        # (full takeover). The system does NOT spawn projectiles/particles/drops
        # (those are Task 20); it computes damage + energy + cooldowns on
        # entities self-containedly.
        from src.systems.combat import CombatSystem
        self.combat = CombatSystem(self.world, None, self)

        # DropSystem (Task 18): ECS ground-loot system — spawn / pickup /
        # drift+expire. Runs IN PARALLEL with the legacy _spawn_drop/
        # _pickup_drop path (additive) — the legacy path stays the source of
        # truth until Task 20 (full takeover). The system owns its own
        # self.drops.drops list; the legacy self._drops_legacy list is
        # UNTOUCHED and keeps driving the 21-test suite + the draw loop.
        from src.systems.drops import DropSystem
        self.drops = DropSystem(self.world, self)

        # RiftSystem (Task 18): ECS rift mini-dungeon — trigger / clear /
        # update. Runs IN PARALLEL with the legacy _enter_rift/_clear_rift
        # path (additive) — the legacy path stays the source of truth until
        # Task 20 (full takeover). The system owns its own active/done/wave
        # state; the legacy _rift_active/_rift_done/_rift_enemies (on
        # MapController) are UNTOUCHED.
        from src.systems.rift import RiftSystem
        self.rift = RiftSystem(self.world, self)

        # DialogueSystem (Task 18): ECS NPC dialogue + story-quest gating —
        # talk / advance / is_quest_active / is_quest_available. Runs IN
        # PARALLEL with the legacy _handle_npc_talk/_advance_dialogue/
        # _is_quest_active/_is_quest_available path (additive) — the legacy
        # path stays the source of truth until Task 20 (full takeover). The
        # system owns its own dialogue/dialogue_npc/dialogue_lines/dialogue_idx
        # state; the legacy _dialogue/_npc (on WorldScene) are UNTOUCHED.
        from src.systems.dialogue import DialogueSystem
        self.dialogue = DialogueSystem(self.world, self)

        # RenderSystem (Task 19): ECS world renderer — draws the world layer
        # (ground + entities + VFX + atmosphere) to a surface. Runs IN PARALLEL
        # with the legacy WorldScene.draw (additive) — the legacy draw STAYS
        # the source of truth this task; this system proves it can render
        # entities to a surface without raising. Full takeover (moving all ~25
        # _draw_* methods + atmosphere helpers verbatim into this system) is
        # Task 20. The minimal draw iterates world.heroes()/enemies() and
        # draws element-colored circles at each Transform (camera-offset).
        from src.systems.render import RenderSystem
        self.render = RenderSystem(self.world, self)

        # HudSystem (Task 19): ECS HUD renderer — draws the HUD layer (skill
        # bar + party + boss bar + minimap) to a surface. Runs IN PARALLEL
        # with the legacy _draw_hud/_draw_skill_bar/_draw_minimap (additive)
        # — the legacy HUD draw STAYS the source of truth this task; this
        # system proves it can render a HUD to a surface without raising.
        # Full takeover (moving all the _draw_hud/_draw_skill_bar/
        # _draw_skill_tooltip/_draw_minimap/_draw_boss_banner/
        # _draw_ascend_banner/_hud_portrait/_skill_icon methods verbatim into
        # this system) is Task 20. The minimal draw renders the active hero's
        # name + HP bar + energy bar via src.ui text/draw_bar.
        from src.systems.hud import HudSystem
        self.hud = HudSystem(self.world, self)

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
        self._drops_legacy = []  # list of {x,y,kind,value} — the legacy drop
        #   list (renamed from self.drops in Task 18 so self.drops can be the
        #   DropSystem. The legacy _spawn_drop/_pickup_drop/update/draw paths
        #   all use self._drops_legacy now; behavior is unchanged.)
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
        # NOTE: _landmark / _village are now owned by MapController (the
        # delegate properties at the bottom of this class read+write through to
        # self.map_ctrl). _water / _bridges stay on the scene (the draw loop +
        # collision check read them here).
        self._water = []
        self._bridges = []
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
        # skill-icon cache for the skill bar (one load per (hero,skill,size)
        # per scene — per-hero art means the cache key includes the hero id)
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
                    hero.energy = rec.get("energy", ENERGY_START)
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
                # ECS adapter (Task 12): spawn a parallel hero entity that tracks
                # this WorldCharacter. The legacy wc stays the source of truth;
                # the entity only mirrors its state each frame (_sync_entities).
                e = spawn_hero(self.world, hid,
                               level=rec.get("level", 1) if rec else 1,
                               ascension=rec.get("ascension", 0) if rec else 0,
                               evolve=rec.get("evolve", 0) if rec else 0,
                               skin=getattr(hero, "skin", 0),
                               x=wc.x, y=wc.y)
                self._entity_for_hero[hid] = e
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
                # ECS adapter (Task 12): spawn the fallback hero's entity too so
                # the entity layer tracks it (mirrors the main-loop branch above).
                if hid not in self._entity_for_hero:
                    self._entity_for_hero[hid] = spawn_hero(
                        self.world, hid, skin=getattr(hero, "skin", 0),
                        x=wc.x, y=wc.y)
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
        self._resonances = team_resonances(team_ids)
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
    # Map loading + transitions — delegated to MapController (Task 14, Phase 4).
    # The bodies live in src/systems/map_ctrl.py; these one-line delegates keep
    # the rest of WorldScene's legacy methods (which call self._load_map /
    # self._transition / self.teleport_to / self._discover_neighbors) working
    # unchanged. The controller owns c / r / _map_data / map_renderer / _village
    # / _landmark / _rift_*; WorldScene reads/writes them via the settable
    # delegate properties at the bottom of this class.
    # -----------------------------------------------------------------
    def _load_map(self, enter_edge=None, target_cell=None):
        return self.map_ctrl.load_map(enter_edge=enter_edge,
                                      target_cell=target_cell)

    def _discover_neighbors(self):
        return self.map_ctrl.discover_neighbors()

    def _transition(self, edge):
        return self.map_ctrl.transition(edge)

    def teleport_to(self, c, r):
        return self.map_ctrl.teleport_to(c, r)

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
            pool = [k for k, v in EQUIPMENT_DB.items() if v["rarity"] in ("SR", "SSR")]
            if pool:
                eid = random.choice(pool)
                p.add_equipment(eid)
                label, col = f"+{EQUIPMENT_DB[eid]['name']}!", (255, 200, 120)
            else:
                p.gold += 100
                label, col = "+100 gold", (255, 220, 120)
        p.stats["treasures_opened"] = p.stats.get("treasures_opened", 0) + 1
        p.quest_progress("open_chests", 1)
        for aid in p.check_achievements():
            ach = ACHIEVEMENTS.get(aid, {})
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
            # ECS adapter (Task 12): spawn a parallel enemy entity that tracks
            # this rift-spawned WorldEnemy. Match the level/is_boss args.
            ee = spawn_enemy(self.world, en.id,
                             level=level + wave_level, is_boss=False,
                             x=en.x, y=en.y)
            self._entity_for_enemy[id(en)] = ee
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
        pool = [k for k, v in EQUIPMENT_DB.items() if v["rarity"] == rar]
        if pool:
            eid = random.choice(pool)
            p.add_equipment(eid)
            label = f"+{EQUIPMENT_DB[eid]['name']}!"
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
        if LORE_FRAGMENTS:
            frag_rng = random.Random(WD.cell_seed(self.c, self.r) + 4242)
            frag = frag_rng.choice(LORE_FRAGMENTS)
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
    # Story quest chain (Task E2) — helpers for the boss gating + the
    # boss-defeat advance. A quest is "active" when the NPC gave it (the
    # dialogue acceptance in _advance_dialogue sets story_progress[id] to
    # "active"); "complete" when the boss dies (the boss-defeat handler sets
    # it). The final-boss quest (baron) is "active" only when all 5
    # faction-boss quests are "complete" (the chain - the player must clear all
    # 5 faction bosses before Baron's arena unseals). A quest is "available"
    # when the previous quest in the chain is "complete" (the first quest,
    # demacia_quest, is available from the start) - the NPC only offers a
    # quest that's available, so the player can't skip ahead.
    # -----------------------------------------------------------------
    def _is_quest_active(self, quest_id):
        """True if the quest is active (the NPC gave it) or complete (the boss
        died - the arena should stay open on a revisit). For the final-boss
        quest (baron), active requires all 5 faction-boss quests complete
        (the void NPC gives the baron quest, but the arena stays sealed
        until the chain is done - the void_quest quest is the void row's
        faction-boss gate; the baron quest is the chain's final gate)."""
        sp = self.game.player.story_progress
        if quest_id == STORY_FINAL_QUEST:
            # Baron's arena unseals only when all 5 faction-boss quests are
            # complete (the chain). The baron entry itself may also be "active"
            # (set by the void NPC) but the chain gate is the stricter
            # condition - both must hold for the boss to spawn.
            faction_quests = [q for q in STORY_QUEST_ORDER
                              if q != STORY_FINAL_QUEST]
            return all(sp.get(q) == "complete" for q in faction_quests)
        return sp.get(quest_id) in ("active", "complete")

    def _is_quest_available(self, quest_id):
        """True if the NPC can offer the quest (the previous quest in the chain
        is complete, or it's the first quest). The first quest (demacia_quest)
        is always available; the final quest (baron) is available when all 5
        faction-boss quests are complete."""
        order = STORY_QUEST_ORDER
        if quest_id not in order:
            return False
        idx = order.index(quest_id)
        if idx == 0:
            return True
        sp = self.game.player.story_progress
        # available when the previous quest is complete (the chain unlocks one
        # quest at a time). The final quest (baron) follows the same rule - it's
        # available when void_quest (the previous in the list) is complete,
        # which itself requires the 4 before it complete.
        prev = order[idx - 1]
        return sp.get(prev) == "complete"

    # -----------------------------------------------------------------
    # Story quest tracker helpers (Task E3) — the chain + the compass target.
    # The quest tracker (_draw_hud) shows the active story quest's name +
    # objective so the player knows where to go next; the compass
    # (_nearest_objective) points at the story target (the boss cell once the
    # quest is active, or the biome NPC's village when the next quest hasn't
    # been accepted yet). The chain reads from player.story_progress
    # (quest_id -> "active"/"complete"); a quest is "available" when the
    # previous quest in the chain is complete (see _is_quest_available). The
    # first quest (plains_boss) is available from the start, so at boot the
    # tracker shows "seek the plains NPC" + the compass points to the plains
    # village. Once the player accepts the quest (the NPC dialogue), the
    # tracker shows "defeat the boss at the east edge" + the compass points to
    # the boss cell (column 9 of the biome's row). The village cell for a biome
    # is found by scanning the row's gen_map (the village is a deterministic
    # gen_map feature — the same cell always has the village for that biome).
    # -----------------------------------------------------------------
    def _active_story_quest(self):
        """The active story quest (the first STORY_QUESTS entry whose status in
        player.story_progress is "active"), or None if no quest is active. The
        chain unlocks one quest at a time, so at most one quest is "active"
        (the next quest is "available" but not yet accepted). Returns the
        STORY_QUESTS dict (with id/name/giver/objective/...) or None."""
        sp = self.game.player.story_progress
        for qid in STORY_QUEST_ORDER:
            if sp.get(qid) == "active":
                return STORY_QUEST_BY_ID[qid]
        return None

    def _next_story_quest(self):
        """The next quest the player should pursue — the active quest if one
        is active, else the first available-but-not-yet-accepted quest (the
        quest whose NPC the player should seek). Returns the STORY_QUESTS dict
        or None when the whole chain is complete (the endgame)."""
        active = self._active_story_quest()
        if active is not None:
            return active
        for qid in STORY_QUEST_ORDER:
            if (self.game.player.story_progress.get(qid) != "complete"
                    and self._is_quest_available(qid)):
                return STORY_QUEST_BY_ID[qid]
        return None

    def _village_cell_for_biome(self, biome):
        """The (c, r) cell that holds the village for `biome`, or None if no
        cell in the biome's row generates a village. The village is a
        deterministic gen_map feature (seeded from cell_seed), so the same
        cell always has the village for that biome. Scans the biome's row
        (ROW_BIOME[r] == biome) for the first cell whose gen_map has a
        village. Cached per (biome) on the scene so the compass hot path is a
        dict lookup, not a gen_map scan, on every frame."""
        if not hasattr(self, "_village_cell_cache"):
            self._village_cell_cache = {}
        cached = self._village_cell_cache.get(biome, _VILLAGE_SENTINEL)
        if cached is not _VILLAGE_SENTINEL:
            return cached
        row = None
        for ridx, rb in enumerate(WD.ROW_BIOME):
            if rb == biome:
                row = ridx
                break
        if row is None:
            self._village_cell_cache[biome] = None
            return None
        # boss cells (column 9) don't generate villages (gen_map gates the
        # village on `not is_boss`), so scan columns 0..GRID_W-2.
        found = None
        for c in range(WD.GRID_W - 1):
            m = WD.gen_map(c, row)
            if m.get("village") is not None:
                found = (c, row)
                break
        self._village_cell_cache[biome] = found
        return found

    def _story_target(self):
        """The (c, r, label, color) the compass should point at for the story
        chain, or None if the chain is done (no story target). The active quest
        points to the boss cell (column 9 of the biome's row); the next
        available (not-yet-accepted) quest points to the biome NPC's village
        (the village cell for the biome). The boss cell is gold (same as the
        existing boss compass); the village cell is a warm cyan so the player
        can tell the two apart."""
        q = self._next_story_quest()
        if q is None:
            return None
        biome = q["giver"]
        row = WD.ROW_BIOME.index(biome) if biome in WD.ROW_BIOME else None
        if row is None:
            return None
        sp = self.game.player.story_progress
        if sp.get(q["id"]) == "active":
            # the quest is accepted — point to the boss cell (column 9)
            return (WD.GRID_W - 1, row, "Boss", (255, 200, 80))
        # the quest isn't accepted yet — point to the biome NPC's village
        vc = self._village_cell_for_biome(biome)
        if vc is None:
            return None
        return (vc[0], vc[1], "NPC", (120, 220, 255))

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
        player isn't stuck in the box - the world kept simulating behind it, so
        there's no 'resume' step (the overlay just stops drawing).

        Task E2: on the dismiss (the last line), accept the quest - set the
        NPC's quest_id to "active" in story_progress so the boss arena unseals.
        The NPC only offers a quest that's available (the previous quest in the
        chain is complete, or it's the first quest); if the quest is already
        active/complete, the dialogue still plays (the NPC re-tells the story)
        but doesn't re-accept (no double-accept). The quest is accepted even if
        the player hasn't explored the boss cell yet - the gate is on quest
        acceptance, not exploration; the boss spawns the moment the quest is
        active (the next visit to the boss cell)."""
        if self._dialogue is None:
            return
        self._dialogue["idx"] += 1
        if self._dialogue["idx"] >= len(self._dialogue["lines"]):
            # dismiss - the dialogue's last line is the quest hook; finishing
            # the dialogue accepts the quest (the NPC gives it). Only accept
            # if the quest is available (the chain) + not already active/
            # complete (no double-accept).
            if self._npc is not None:
                qid = self._npc.get("quest_id")
                if (qid is not None and qid in STORY_QUEST_BY_ID
                        and self._is_quest_available(qid)
                        and self.game.player.story_progress.get(qid) not in
                            ("active", "complete")):
                    self.game.player.story_progress[qid] = "active"
                    q = STORY_QUEST_BY_ID[qid]
                    self.set_message(
                        f"Quest accepted: {q['name']} - {q['objective']}", 3.0)
                    # the void NPC ALSO gives the final quest (the chain's
                    # final marker) when the void_quest quest is accepted - the
                    # void row's boss (9,4) IS Baron Nashor, so accepting the
                    # void_quest quest (the row's faction-boss) means the player
                    # is also on the baron quest. Mark it active too so the
                    # boss-defeat handler can complete the chain's final marker
                    # (the baron quest) on Baron's death. The void NPC's
                    # dialogue already foreshadows Baron ("Baron Nashor waits
                    # where the world's edge frays" + "End it, and the Cycle may
                    # turn at last"), so the player learns about Baron from the
                    # void NPC.
                    if (qid == "void_quest"
                            and self.game.player.story_progress.get(
                                STORY_FINAL_QUEST) not in ("active", "complete")):
                        self.game.player.story_progress[STORY_FINAL_QUEST] = "active"
                    self.game.player.save()
            self._dialogue = None
        else:
            audio.play("hit", 0.12)

    # -----------------------------------------------------------------
    # Combat helpers
    # -----------------------------------------------------------------
    def _element_mult(self, atk_el, def_el):
        return self.combat._element_mult(atk_el, def_el)

    def _do_attack(self, wc, target=None):
        return self.combat._do_attack(wc, target=target)

    def _do_skill(self, wc, idx, target=None):
        return self.combat._do_skill(wc, idx, target=target)

    def _do_ultimate(self, wc):
        return self.combat._do_ultimate(wc)

    def _on_enemy_hit(self, en, wc, dmg, is_crit):
        return self.combat._on_enemy_hit(en, wc, dmg, is_crit)

    def _on_enemy_death(self, en, wc):
        return self.combat._on_enemy_death(en, wc)

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
            self._drops_legacy.append({"x": float(x), "y": float(y),
                               "kind": "gold", "value": int(value),
                               "t": 0.0, "sprite_id": "gold"})
            return
        n = max(1, min(int(count), 4))  # cap so a stray high count doesn't flood
        for _ in range(n):
            ox = x + random.uniform(-10, 10)
            oy = y + random.uniform(-10, 10)
            self._drops_legacy.append({"x": float(ox), "y": float(oy),
                               "kind": kind, "value": value,
                               "t": 0.0, "sprite_id": kind})

    def _pickup_drop(self, drop, wc):
        """Collect a ground loot drop: add its value to the player's inventory
        by kind, a gold sparkle burst, and remove it from self._drops_legacy. Called
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
                wc.hero.energy = ENERGY_START
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
        el_col = ELEMENT_COLORS.get(new.element, ((180, 220, 255),))[0]
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
        # ECS adapter (Task 12): ensure the incoming hero has a parallel entity.
        # _switch only swaps the active index — the hero was already in the
        # party (and got an entity in _build_party), so the entity should exist.
        # Spawn defensively if it doesn't (e.g. a hero added to the party after
        # _build_party via some other path) so the entity layer never goes stale.
        hid = new.hero.id
        if hid not in self._entity_for_hero:
            self._entity_for_hero[hid] = spawn_hero(
                self.world, hid, x=new.x, y=new.y)
        # recompute elemental resonances — the active buffs track the live party,
        # so swapping in a 2nd hero of an element enables its resonance live.
        self._compute_resonances()

    # -----------------------------------------------------------------
    # ECS adapter (Task 12) — copy legacy state onto entity components each
    # frame. READ-ONLY on the legacy path: it never mutates wc.x, wc.hero.hp,
    # self.enemies, etc. It only WRITES to entity components in self.world.
    # -----------------------------------------------------------------
    def _sync_entities(self, dt):
        for wc in self.party:
            if wc is None:
                continue
            e = self._entity_for_hero.get(wc.hero.id)
            if e is None:
                continue
            e.get(Transform).x = wc.x
            e.get(Transform).y = wc.y
            e.get(Health).hp = wc.hero.hp
            e.get(Health).energy = wc.hero.mp
        for en in self.enemies:
            e = self._entity_for_enemy.get(id(en))
            if e is None:
                continue
            e.get(Transform).x = en.x
            e.get(Transform).y = en.y
            e.get(Health).hp = en.enemy.hp

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
                if d < AA_RANGE:
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
        # are sealed: the player must clear the wave before they can leave) OR
        # while in adventure mode (the stage is a fixed arena — the player must
        # not walk out of the stage into the open world).
        if wc and not self._rift_active and not getattr(self, "_is_adventure", False):
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
        # self._drops_legacy in place on pickup (the list comp filters the collected
        # ones out at the end so we don't skip a drop after a mid-loop removal).
        if wc and self._drops_legacy:
            picked = []
            for d in self._drops_legacy:
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
                self._drops_legacy = [d for d in self._drops_legacy if d not in picked]

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
                            item = CONSUMABLES_DB[used]
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
                                p.source.add_energy(ENERGY_GAIN_BASIC)
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
        if self._drops_legacy:
            for d in self._drops_legacy:
                d["t"] += sim_dt
            self._drops_legacy = [d for d in self._drops_legacy if d["t"] < 30.0]

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
        # ECS adapter (Task 12): copy legacy state onto entity components at the
        # END of update so the entity layer tracks the post-tick legacy state.
        # READ-ONLY on the legacy path — only writes to entity components.
        self._sync_entities(dt)

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
            ult_id = BOSS_ULT.get(en.id)
            usk = SKILLS_DB.get(ult_id, {}) if ult_id else {}
            upower = usk.get("power", 1.8)
            radius = 260
            if ult_id in ("frost_cataclysm", "storm_of_embers"):
                radius = 320
            col = ELEMENT_COLORS.get(en.element, ((255, 80, 80),))[0]
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
            col = ELEMENT_COLORS.get(en.element, ((255, 80, 80),))[0]
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
            col = ELEMENT_COLORS.get(en.element, ((255, 80, 80),))[0]
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
            col = ELEMENT_COLORS.get(en.element, ((255, 80, 80),))[0]
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
        # Task 20a: the full world draw pipeline (ground + water/bridges +
        # depth-sorted drawables + projectiles + aim preview + chests +
        # breakables + rift portal + particles/floats + atmosphere + edge
        # hints + banners + dialogue box + modal overlays) is ported VERBATIM
        # into RenderSystem.draw. This delegate hops into the system so the
        # legacy draw path + the 21-test suite keep working (the rendered
        # output is pixel-identical — the port is verbatim). The HUD layer
        # (Task 20b) is now drawn via self.scene.hud.draw inside
        # RenderSystem.draw (the verbatim HUD methods were ported into
        # HudSystem in Task 20b).
        return self.render.draw(surf, self.map_ctrl)

    def _nearest_objective(self):
        """Return (tc, tr, label, color) for the compass target. Priority:
        1. The story target (Task E3) — the boss cell for the active quest, or
           the biome NPC's village for the next available (not-yet-accepted)
           quest. This is the main story chain, so it takes priority over the
           generic nearest-boss fallback (the story target is the *right* boss
           to fight next, not just the nearest one).
        2. The nearest un-cleared boss cell (right-most column, all rows) —
           the v1 #20 fallback for non-story bosses / a pre-E2 save.
        3. The nearest undiscovered cell (cyan) when all bosses are cleared.
        Returns None when the chain is done + every boss is cleared + every
        cell is discovered, so the compass hides in the endgame."""
        # 1. story target (Task E3) — the active quest's boss cell, or the
        # next available quest's NPC village. Takes priority so the compass
        # points the player along the chain (not just to the nearest boss).
        st = self._story_target()
        if st is not None:
            return st
        p = self.game.player
        cleared = set(p.ow_bosses_cleared)
        discovered = set(p.ow_discovered)
        best = None
        best_d2 = None
        # 2. nearest un-cleared boss cell (right-most column, all rows) — gold
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
        # 3. all bosses cleared — fall back to nearest undiscovered cell — cyan
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

    # -----------------------------------------------------------------
    # MapController delegate properties (Task 14, Phase 4). The controller owns
    # the map grid state (c, r, _map_data, map_renderer, _village, _landmark,
    # _rift_*); these settable properties read+write through to self.map_ctrl so
    # the rest of WorldScene's legacy methods (which read self.c / self._map_data
    # / self.map_renderer / self._village / self._landmark / self._rift_*) keep
    # working unchanged. Reads route to the controller; writes route to the
    # controller too (load_map sets self.c / self._map_data / ... on the
    # controller; the setter is defensive scaffolding in case a future path
    # writes self.c = ... directly).
    # -----------------------------------------------------------------
    @property
    def c(self):
        return self.map_ctrl.c

    @c.setter
    def c(self, v):
        self.map_ctrl.c = v

    @property
    def r(self):
        return self.map_ctrl.r

    @r.setter
    def r(self, v):
        self.map_ctrl.r = v

    @property
    def _map_data(self):
        return self.map_ctrl._map_data

    @_map_data.setter
    def _map_data(self, v):
        self.map_ctrl._map_data = v

    @property
    def map_renderer(self):
        return self.map_ctrl.map_renderer

    @map_renderer.setter
    def map_renderer(self, v):
        self.map_ctrl.map_renderer = v

    @property
    def _village(self):
        return self.map_ctrl._village

    @_village.setter
    def _village(self, v):
        self.map_ctrl._village = v

    @property
    def _landmark(self):
        return self.map_ctrl._landmark

    @_landmark.setter
    def _landmark(self, v):
        self.map_ctrl._landmark = v

    @property
    def _rift_active(self):
        return self.map_ctrl._rift_active

    @_rift_active.setter
    def _rift_active(self, v):
        self.map_ctrl._rift_active = v

    @property
    def _rift_done(self):
        return self.map_ctrl._rift_done

    @_rift_done.setter
    def _rift_done(self, v):
        self.map_ctrl._rift_done = v

    @property
    def _rift_enemies(self):
        return self.map_ctrl._rift_enemies

    @_rift_enemies.setter
    def _rift_enemies(self, v):
        self.map_ctrl._rift_enemies = v

    @property
    def _rift_secret(self):
        return self.map_ctrl._rift_secret

    @_rift_secret.setter
    def _rift_secret(self, v):
        self.map_ctrl._rift_secret = v


# ---------------------------------------------------------------------------
# Weapon style lookup (champion id -> weapon) from the baked descriptor in
# champions.py. The descriptor's `weapon` field drives the attack VFX style.
# Cached per hero_id: the descriptor is static (baked at build time), and this
# is called on every basic attack + skill + aim preview (3 hot-path call
# sites), so a dict lookup beats re-walking CHAMPION_BY_KEY each time.
# ---------------------------------------------------------------------------
import src.build.champions as _CH
_WEAPON_STYLE_CACHE = {}
def WEAPON_STYLE_KEY(hero_id):
    w = _WEAPON_STYLE_CACHE.get(hero_id)
    if w is None:
        c = _CH.CHAMPION_BY_KEY.get(hero_id)
        w = c["descriptor"]["weapon"] if c is not None else "sword"
        _WEAPON_STYLE_CACHE[hero_id] = w
    return w
