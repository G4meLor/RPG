"""HudSystem (Phase 4, Task 20b of the ECS restructure) — HUD renderer.

Renders the HUD layer (party + boss bar + skill bar + minimap + quest tracker
+ compass + resonance badges) to a surface, reading the legacy
``WorldScene`` party / enemies / player / camera / map state via
``self.scene``. The methods are ported VERBATIM from ``WorldScene`` (Task 20b)
— only ``self.X`` → ``self.scene.X`` for scene-level state. The HUD helper
methods (``_hud_portrait`` / ``_skill_icon`` / ``_draw_skill_bar`` /
``_draw_skill_tooltip`` / ``_build_skill_tooltip_surf`` / ``_draw_minimap`` /
``_draw_chevron``) stayed as ``self.X`` (now HudSystem methods).
"""
import math

import pygame

from src.data.elements import ELEMENT_COLORS
from src.data.heroes import HERO_ASSETS
from src.data.progression import DAILY_QUESTS
from src.data.resonance import ELEMENTAL_RESONANCE
from src.data.skills import SKILLS_DB
from src.data.tuning import COMBO_BONUS_PER
from src.entities import load_char_sprite, load_skill_icon, scratch
import src.world.data as WD
from src.ui import draw_bar
from src.ui import get_font as _font, text

# Cached "BROKEN — +50% DMG" label for the boss bar — rendered once and reused
# so a broken boss doesn't re-render the string every frame (font.render is a
# top profile cost). Lazily filled on first broken-boss draw.
_BOKEN_DMG_LABEL_SURF = None


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


class HudSystem:
    """ECS HUD renderer — draws the HUD layer to a surface. The legacy
    ``WorldScene._draw_hud`` stayed the source of truth through Task 19; Task
    20b moves the verbatim HUD methods into this system so ``RenderSystem``
    delegates the HUD draw here.

    Parameters
    ----------
    world : World
        The ECS entity world (kept for API parity with the other systems; the
        verbatim HUD reads legacy party/enemies/player state via ``scene``).
    scene : WorldScene or None
        The owning scene. The ported HUD methods read ``scene.party`` /
        ``scene.active`` / ``scene.enemies`` / ``scene.game`` /
        ``scene.camera`` / ``scene.c`` / ``scene.r`` / ``scene._resonances`` /
        ``scene._combo_*`` / ``scene._hud_panel`` / ``scene._hud_portraits`` /
        ``scene._skill_icons`` / ``scene._minimap_cache`` /
        ``scene._tooltip_cache`` / ``scene._boss_phase_flash_t`` /
        ``scene._skill_empowered`` / ``scene._ult_empowered``. May be None for
        headless tests (``draw`` is a no-op then).
    """

    def __init__(self, world, scene=None):
        self.world = world
        self.scene = scene

    # ------------------------------------------------------------------
    # HUD helpers (ported verbatim from WorldScene, Task 20b)
    # ------------------------------------------------------------------
    def _hud_portrait(self, hid, size):
        """Cached HUD portrait — one load per (hero,size) per scene lifetime."""
        key = (hid, size)
        p = self.scene._hud_portraits.get(key)
        if p is None:
            try:
                p = load_char_sprite(hid, size)
            except Exception:
                p = None
            self.scene._hud_portraits[key] = p
        return p

    def _skill_icon(self, hero_id, sid, size):
        """Cached skill icon — one load per (hero,skill,size) per scene
        lifetime. Per-hero art means the cache key includes the hero id so
        switching the active hero re-loads that hero's accent-tinted icons."""
        key = (hero_id, sid, size)
        ic = self.scene._skill_icons.get(key)
        if ic is None:
            try:
                ic = load_skill_icon(hero_id, sid, size)
            except Exception:
                ic = None
            self.scene._skill_icons[key] = ic
        return ic

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

    def draw(self, surf):
        p = self.scene.game.player
        wc = self.scene.party[self.scene.active]
        # active hero panel (top-left) — reuse a persistent panel surface
        if wc:
            hero = wc.hero
            # portrait (cached per-scene so the HUD hot path is one dict lookup)
            port = self._hud_portrait(hero.id, 64)
            panel = self.scene._hud_panel
            panel.fill((0, 0, 0, 0))
            pygame.draw.rect(panel, (20, 20, 40, 200), panel.get_rect(), border_radius=12)
            pygame.draw.rect(panel, (180, 180, 220), panel.get_rect(), 2, border_radius=12)
            surf.blit(panel, (16, 16))
            if port:
                surf.blit(port, (24, 24))
            text(surf, hero.name, 18, (255, 255, 255), (96, 26))
            el_col = ELEMENT_COLORS.get(hero.element, ((200, 200, 200),))[0]
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
        for i, wc2 in enumerate(self.scene.party):
            x = 16 + i * 64
            y = 116
            r2 = pygame.Rect(x, y, 56, 56)
            if wc2 is None:
                pygame.draw.rect(surf, (30, 30, 40), r2, border_radius=10)
                pygame.draw.rect(surf, (60, 60, 80), r2, 2, border_radius=10)
                text(surf, str(i + 1), 16, (90, 90, 110), r2.center, center=True)
                continue
            el_col2 = ELEMENT_COLORS.get(wc2.hero.element, ((180, 200, 220),))[0]
            is_active = (i == self.scene.active)
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
        if self.scene._resonances:
            bx = 16
            by = 178
            for r in self.scene._resonances:
                el = next((e for e, d in ELEMENTAL_RESONANCE.items()
                           if d.get("buff") == r.get("buff")), None)
                col = ELEMENT_COLORS.get(el, ((180, 200, 220),))[0]
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
        name = WD.cell_name(self.scene.c, self.scene.r)
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
        if self.scene._combo_count >= 2:
            cx = 640
            cy = 120
            bonus = int(self.scene._combo_count * COMBO_BONUS_PER * 100)
            label = f"x{self.scene._combo_count}  +{bonus}% DMG"
            col = (255, 220, 80) if self.scene._combo_count < 10 else (255, 120, 120)
            text(surf, label, 26, col, (cx, cy), center=True)
            # timer bar
            bw = 120
            frac = max(0, self.scene._combo_t / self.scene._combo_window)
            bx = cx - bw // 2
            by = cy + 16
            pygame.draw.rect(surf, (30, 30, 40), (bx, by, bw, 6), border_radius=3)
            if frac > 0:
                pygame.draw.rect(surf, col, (bx, by, int(bw * frac), 6), border_radius=3)
            # combo climax: an "EMPOWERED" tag under the combo counter when a
            # milestone flag is active, so the player sees the finisher is armed
            # and knows to spend it before the window expires. Pulses so it
            # reads as an active buff, not a static label.
            if self.scene._skill_empowered or self.scene._ult_empowered:
                pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.01)
                ecol = (int(180 * pulse + 75), int(120 * pulse + 60), int(200 * pulse + 40))
                etag = "EMPOWERED SKILL!" if self.scene._skill_empowered else "EMPOWERED ULT!"
                text(surf, etag, 16, ecol, (cx, by + 14), center=True)

        # boss HP bar at top center if a boss is alive — a dramatic framed bar
        boss = next((e for e in self.scene.enemies if e.is_boss and e.alive), None)
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
            if self.scene._boss_phase_flash_t > 0:
                fa = int(140 * (self.scene._boss_phase_flash_t / 0.5))
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
        if self.scene.game.player.settings.get("show_hints", True):
            hint = "WASD move | RMB enemy=auto-attack / ground=move | J attack | Q/W/E skills | U/Space ult | 1-4 switch | R potion | M map | G evolve | Esc menu"
            text(surf, hint, 12, (200, 200, 220), (640, 704), center=True)

        # skill bar (bottom-center): Q/W/E + R(ult) with icons + cooldown sweeps
        self._draw_skill_bar(surf)

        # quest tracker (top-right, under the resource counters — y~110, x>900
        # so it clears the boss HP bar at top-center x=320..960). Two panels:
        # the story quest (Task E3, above) + the daily quest (v1 #20, below).
        # The story panel shows the active/next story quest's name + a short
        # hint ("seek the <biome> NPC" when not yet accepted, "defeat the boss
        # at the east edge" when active). The daily panel shows the top daily
        # quest's name + a progress bar + N/goal. Skipped when no quests are
        # loaded yet (the quest tab calls reset_quests_if_needed; the world
        # scene reads the in-memory dict, which may be empty on a fresh load
        # before the quest tab is opened — guard with .get).
        try:
            p.reset_quests_if_needed()
        except Exception:
            pass
        qx = 1276
        qy = 110
        # story quest panel (Task E3) — the active/next story quest. Shown
        # above the daily-quest panel so the main story reads as the primary
        # objective. The hint is "seek the <biome> NPC" when the quest isn't
        # accepted yet (the next available quest) or "defeat the boss at the
        # east edge" when the quest is active. Skipped only when the whole
        # chain is complete (the endgame — no story target).
        sq = self.scene._next_story_quest()
        if sq is not None:
            sp = p.story_progress
            sq_active = sp.get(sq["id"]) == "active"
            sq_done = sp.get(sq["id"]) == "complete"
            sq_w = 220
            sq_h = 64
            sq_panel = pygame.Rect(qx - sq_w, qy, sq_w, sq_h)
            sqp = scratch(sq_w, sq_h)
            pygame.draw.rect(sqp, (20, 20, 36, 200), sqp.get_rect(), border_radius=8)
            # gold border for an active quest, dim green for complete, cyan
            # for "seek the NPC" (the next available quest).
            if sq_active:
                sq_col = (255, 200, 80)
            elif sq_done:
                sq_col = (120, 180, 140)
            else:
                sq_col = (140, 200, 250)
            pygame.draw.rect(sqp, sq_col, sqp.get_rect(), 2, border_radius=8)
            surf.blit(sqp, sq_panel.topleft)
            text(surf, "STORY", 10, (160, 160, 200), (sq_panel.x + 8, sq_panel.y + 4))
            text(surf, sq["name"], 13, (255, 240, 220),
                 (sq_panel.x + 8, sq_panel.y + 18))
            # hint line: "seek the <biome> NPC" or "defeat the boss at the east edge"
            if sq_active:
                hint = "Defeat the boss at the east edge"
            else:
                hint = f"Seek the {sq['giver']} NPC"
            text(surf, hint, 11, sq_col, (sq_panel.x + 8, sq_panel.y + 38))
            # shift the daily-quest panel below the story panel
            qy += sq_h + 4
        first_qid = next(iter(DAILY_QUESTS), None)
        if first_qid is not None:
            qd = DAILY_QUESTS[first_qid]
            st = p.quests.get(first_qid)
            if st is None:
                st = dict(progress=0, claimed=False, goal=qd["goal"])
            prog = st.get("progress", 0)
            goal = st.get("goal", qd["goal"])
            claimed = st.get("claimed", False)
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
        obj = self.scene._nearest_objective()
        if obj is not None:
            tc, tr, olabel, ocol = obj
            # target world coords = cell center (c*MAP_W + MAP_W/2, r*MAP_H + MAP_H/2)
            tx = tc * WD.MAP_W + WD.MAP_W // 2
            ty = tr * WD.MAP_H + WD.MAP_H // 2
            ox, oy = self.scene.camera.offset()
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
        discovered = self.scene.game.player.ow_discovered
        # rebuild the baked cell overlay only when the discovery set changes
        key = tuple(sorted(discovered))
        base = self.scene._minimap_cache.get(key)
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
            self.scene._minimap_cache[key] = base
        surf.blit(base, (ox, oy))
        # pulsing current-position marker (drawn live, one cell)
        cx = ox + self.scene.c * cell
        cy = oy + self.scene.r * cell
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.006)
        pygame.draw.rect(surf, (255, 255, 120), (cx - 1, cy - 1, cell, cell), 2)
        pygame.draw.circle(surf, (255, 240, 120),
                           (cx + cell // 2 - 1, cy + cell // 2 - 1),
                           2 + int(pulse * 2))

    def _draw_skill_bar(self, surf):
        """Bottom-center LoL-style skill bar: Q/W/E + R (ultimate).
        Each slot shows the skill icon, a key hint, and a radial/wedge cooldown
        sweep. R glows when the ultimate is ready; Q/W/E dim when out of energy."""
        wc = self.scene.party[self.scene.active]
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
                ic = self._skill_icon(wc.hero.id, sid, slot - 10)
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
        ha = HERO_ASSETS.get(wc.hero.id)
        entry = None
        if ha:
            for s in ha["skills"]:
                if s["id"] == sid:
                    entry = s; break
        if entry is None:
            sk = SKILLS_DB.get(sid, {})
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
        cached = self.scene._tooltip_cache.get(ck)
        if cached is None:
            panel = self._build_skill_tooltip_surf(entry, ready)
            self.scene._tooltip_cache[ck] = panel
            if len(self.scene._tooltip_cache) > 128:
                self.scene._tooltip_cache.clear()
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
        el_col = ELEMENT_COLORS.get(element, ((200, 200, 220),))[0] if element else (160, 160, 180)
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
