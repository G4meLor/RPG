"""RenderSystem (Phase 4, Task 20a of the ECS restructure) — world renderer.

Full-fidelity port: the legacy ``WorldScene.draw`` + ~25 ``_draw_*`` helper
methods + the atmosphere helpers (``_biome_atmos`` / ``_rain_overlay`` /
``_fog_overlay`` / ``_sky_for_phase`` / ``_night_level`` / ``_night_overlay`` /
``_torch_sprite`` / ``_draw_chevron`` / ``_draw_edge_hints``) are moved VERBATIM
into this system. The method BODIES are copied exactly — only the ``self.X``
references to scene-level state are rewired to ``self.scene.X``; the
``_draw_*`` / atmosphere helper calls stay ``self.X`` (they are now sibling
methods in RenderSystem). ``WorldScene.draw`` becomes a 1-line delegate to
``self.render.draw(surf, self.map_ctrl)`` so the legacy draw path + the 21-test
suite keep working (the rendered output is pixel-identical — the port is
verbatim).

The HUD methods (``_draw_hud`` / ``_draw_skill_bar`` / ``_draw_skill_tooltip``
``_draw_minimap`` / ``_hud_portrait`` / ``_skill_icon``) were Task 20b
(HudSystem) — they are now ported verbatim into ``HudSystem`` and
``RenderSystem.draw`` delegates the HUD layer to ``self.scene.hud.draw(surf)``.

``_draw_tick`` (the per-frame particles/camera tick under overlays) STAYS in
WorldScene — it mutates particles/floats/camera (simulation, not rendering),
so it belongs on the scene until the physics/particle systems take over.
"""
import math
import random

import pygame

import src.fx as fx
import src.world.data as WD
from src.data.elements import ELEMENT_COLORS
from src.data.skills import SKILLS_DB
from src.entities import (WEAPON_STYLE, scratch,
                            load_drop, load_terrain, load_landmark, load_village)
from src.ui import get_font as _font, text


# ---------------------------------------------------------------------------
# Aim-preview thresholds (Task B2) — copied verbatim from world.py so this
# module is self-contained (no circular import on src.scenes.world). The
# values MUST stay in sync with world.py's module-level constants.
# ---------------------------------------------------------------------------
AIM_HOLD_THRESHOLD = 0.12
AIM_MAX_RANGE = 300.0
AIM_AOE_RADIUS = 200


# ---------------------------------------------------------------------------
# Weapon style lookup (champion id -> weapon) — copied verbatim from the
# bottom of world.py so render.py doesn't import src.scenes.world (circular).
# Cached per hero_id; the descriptor is static (baked at build time).
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


class RenderSystem:
    """ECS world renderer — full-fidelity port of the legacy ``WorldScene.draw``
    pipeline (ground + water/bridges + depth-sorted drawables + projectiles +
    aim preview + chests + breakables + rift portal + particles/floats +
    atmosphere + edge hints + banners + dialogue box + modal overlays).

    The method bodies are copied VERBATIM from ``WorldScene``; only ``self.X``
    references to scene-level state are rewired to ``self.scene.X``. The
    ``_draw_*`` / atmosphere helper methods stay ``self.X`` (sibling methods
    in this system). ``WorldScene.draw`` delegates to
    ``self.render.draw(surf, self.map_ctrl)``.

    Parameters
    ----------
    world : World
        The ECS entity world (kept for API parity with the other systems; the
        verbatim port reads the legacy ``scene.party`` / ``scene.enemies``
        lists, not the entity world, so the rendered output is pixel-identical
        to the legacy draw).
    scene : WorldScene or None
        The owning scene. All scene-level state (party, enemies, camera,
        particles, projectiles, floats, map state, atmosphere caches, etc.)
        is read via ``self.scene.X``. May be None for headless tests.
    """

    def __init__(self, world, scene=None):
        self.world = world
        self.scene = scene

    def _camera_offset(self):
        """Return the (ox, oy) camera offset for the world->screen transform.

        Reads ``self.scene.camera.offset()`` (mirrors the legacy
        ``WorldScene.draw`` line ``ox, oy = self.camera.offset()``). Falls
        back to (0, 0) when there is no scene/camera so the system never
        raises in a headless test.
        """
        if self.scene is None:
            return 0, 0
        cam = getattr(self.scene, "camera", None)
        if cam is None:
            return 0, 0
        try:
            return cam.offset()
        except Exception:
            return 0, 0

    def draw(self, surf, map_ctrl=None):
        # map background
        if self.scene._map_cell != (self.scene.c, self.scene.r):
            self.scene._map_surf = self.scene.map_renderer.get(self.scene.c, self.scene.r)
            self.scene._map_cell = (self.scene.c, self.scene.r)
        ox, oy = self.scene.camera.offset()
        surf.blit(self.scene._map_surf, (-ox, -oy))

        # water + bridges (Task C3) — drawn BEFORE the drawables so they're
        # ground (under the hero/enemies/breakables). Water is a dithered
        # shimmer (a slow sine on the alpha) blitted tiled over each water rect;
        # bridges are a passable tile blitted over each bridge rect. Both are
        # cached by load_terrain so this is a single blit per tile per frame.
        # Biome-tinted: the water sprite is re-tinted toward the biome's ground
        # color at load time (load_terrain returns the neutral sprite; the
        # shimmer is a global alpha pulse so the water reads as wet).
        if self.scene._water or self.scene._bridges:
            self._draw_water_bridges(surf, ox, oy)

        # depth-sorted drawables: enemies + active hero + projectiles
        # the boss aura reads the night level (expanded at night) — set it once
        # per frame on each enemy so WorldEnemy.draw doesn't re-derive it per
        # enemy (the boss aura + the hero torch + the vignette all share one
        # quantized night level, no cache thrash).
        night_level = self._night_level()
        drawables = []
        for en in self.scene.enemies:
            if en.alive:
                en._night_level = night_level
                drawables.append((en.y, "enemy", en))
        # breakable props — sorted with the rest so they occlude correctly
        # against the hero/enemies (a pot behind the hero is drawn first).
        for b in self.scene.breakables:
            if not b["broken"]:
                drawables.append((b["y"], "breakable", b))
        # summon allies (Task A3) — sorted with the rest so they occlude correctly
        for s in self.scene._summons:
            drawables.append((s.y, "summon", s))
        # traps (Task A3) — drawn under the entities (ground hazards, low y-sort
        # weight so they sit beneath the hero/enemies)
        for t in self.scene._traps:
            drawables.append((t.y - 1, "trap", t))
        # ground loot drops (Task C2) — sorted with the rest so they occlude
        # correctly against the hero/enemies (a drop behind the hero is drawn
        # first). y-sort weight is the drop's y so they sit on the ground at
        # their actual position (a drop at the hero's feet is drawn before the
        # hero, a drop behind the hero is drawn first — same rule as breakables).
        for d in self.scene._drops_legacy:
            drawables.append((d["y"], "drop", d))
        # landmark + village buildings (Task C3) — sorted with the rest so they
        # occlude correctly against the hero/enemies (a landmark behind the hero
        # is drawn first). Landmarks are decorative (no collision); village
        # buildings are decorative (no collision — the NPC entity is Task E1).
        if self.scene._landmark is not None:
            drawables.append((self.scene._landmark["y"], "landmark", self.scene._landmark))
        if self.scene._village is not None:
            for (bx, by, bkind) in self.scene._village["buildings"]:
                drawables.append((by, "village", (bx, by, bkind)))
        # NPC (Task E1) — sorted with the rest so the NPC occludes correctly
        # against the hero/enemies (an NPC behind the hero is drawn first). Drawn
        # as a small sprite + a name tag (see _draw_npc).
        if self.scene._npc is not None:
            drawables.append((self.scene._npc["y"], "npc", self.scene._npc))
        wc = self.scene.party[self.scene.active]
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
                obj.draw(surf, ox, oy, self.scene.font_sm)

        # projectiles
        for p in self.scene.projectiles:
            p.draw(surf, ox, oy)

        # hold-to-aim preview (Task B2): while a skill key is held past the
        # threshold, draw a category-specific aim preview at the mouse (clamped
        # to AIM_MAX_RANGE from the hero). AoE = a circle (the burst radius),
        # beam = a line, ranged = a trajectory line, melee = an arc in the
        # facing, summon/trap = a marker at the spawn point. Element-tinted;
        # the pulse is gated on reduce_motion (static reticle under RM).
        if wc and self.scene._aim_skill is not None and self.scene._aim_t > AIM_HOLD_THRESHOLD:
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
                el_col = ELEMENT_COLORS.get(wc.element, ((200, 200, 220),))[0]
                fade = max(0.0, 1.0 - wc.move_target_t / 0.5)
                if fade > 0:
                    pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.01)
                    a_ring = int(180 * pulse * fade)
                    ring = scratch(24, 24)
                    pygame.draw.circle(ring, (*el_col, a_ring), (12, 12), 8, 2)
                    surf.blit(ring, (sx - 12, sy - 12))
                    pygame.draw.circle(surf, el_col, (sx, sy), 2)

        # treasure chests — a glowing crate with a soft pulse; dimmed once opened
        for ch in self.scene.chests:
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
        for b in self.scene.breakables:
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
        # draws) using the draw_rift_portal helper from fx. Skipped once the
        # rift is cleared (_rift_done) so a cleared rift doesn't keep glowing
        # on the map (it's gone — the player solved it).
        if self.scene._rift_secret is not None and not self.scene._rift_done:
            rx, ry, _, _ = self.scene._rift_secret
            sx = int(rx - ox)
            sy = int(ry - oy)
            if -60 < sx < 1340 and -60 < sy < 780:
                fx.draw_rift_portal(surf, sx, sy, float(pygame.time.get_ticks()))

        # particles + floats
        self.scene.particles.draw(surf, ox, oy)
        for f in self.scene.floats:
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
        # Task 20b: the verbatim HUD methods were ported into HudSystem; this
        # delegates the HUD draw to self.scene.hud (the legacy
        # WorldScene._draw_hud was removed in Task 20b).
        self.scene.hud.draw(surf)

        # transient center message
        if self.scene.message_t > 0:
            text(surf, self.scene.message, 26, (255, 240, 180), (640, 60), center=True)

        # boss intro cinematic banner — a full-width name plate that fades in/out
        # over the first ~1.6s on entering a boss arena
        if self.scene._boss_intro_t > 0:
            self._draw_boss_banner(surf, self.scene._boss_intro_name, self.scene._boss_intro_t,
                                   intro=True)
        # boss defeat celebration banner — "BOSS DEFEATED" + the boss name
        if self.scene._boss_defeat_t > 0:
            self._draw_boss_banner(surf, self.scene._boss_defeat_name, self.scene._boss_defeat_t,
                                   intro=False)
        # Aetheric Cycle "World Ascended!" banner — shown for ~3s after the
        # final boss (Demon King at 9,4) is defeated, signalling that the
        # player can now Ascend the World from the title screen.
        if self.scene._ascend_banner_t > 0:
            self._draw_ascend_banner(surf, self.scene._ascend_banner_t)

        # NPC dialogue box (Task E1) — a UI overlay drawn on top of the HUD (so
        # the box isn't covered by the skill bar) but under the modal overlays
        # (teleport/evolve/pause take over the screen). The world keeps simulating
        # behind it (the dialogue is a UI overlay, NOT a pause — update ran as
        # normal; only F/Space/Esc were intercepted to advance the line).
        if self.scene._dialogue is not None:
            self._draw_dialogue_box(surf)

        # modal overlays (teleport map, evolve, pause hub) on top of everything
        if self.scene.teleport:
            self.scene.teleport.draw(surf, self.scene.font_big, self.scene.font, self.scene.font_sm)
        if self.scene.evolve:
            self.scene.evolve.draw(surf, self.scene.font_big, self.scene.font, self.scene.font_sm)
        if self.scene.pause:
            self.scene.pause.draw(surf, self.scene.font_big)

    def _draw_aim_preview(self, surf, wc, ox, oy):
        """Draw the hold-to-aim preview (Task B2) for the currently-aimed skill.
        Called from draw() only when `_aim_skill is not None and _aim_t >
        AIM_HOLD_THRESHOLD`. Draws by skill category: AoE = a circle at the
        clamped mouse (the burst radius), beam = a line from hero to the clamped
        mouse, ranged (attack/magic with a projectile) = a trajectory line,
        melee (attack without a projectile) = an arc in the facing, summon/trap
        = a marker at the spawn/place point. Element-tinted; the pulse is gated
        on reduce_motion (static reticle, no pulse)."""
        idx = self.scene._aim_skill
        if idx is None or idx < 0 or idx >= 3:
            return
        sk_list = wc.skill_list()
        if idx >= len(sk_list):
            return
        sk_id = sk_list[idx]
        if sk_id is None:
            return
        skill = SKILLS_DB.get(sk_id)
        if not skill:
            return
        kind = skill["type"]
        col = ELEMENT_COLORS.get(skill["element"], ((200, 200, 200),))[0]
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
        if self.scene._reduce_motion:
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
            if not self.scene._reduce_motion:
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
        if not self.scene._reduce_motion:
            shimmer = int(40 * (0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.003)))
        else:
            shimmer = 0
        # water tiles — blit the water sprite tiled over each water rect, with
        # the shimmer applied as a global alpha on the sprite. The sprite is
        # cached per (path, scale); we set the alpha per frame on a copy so the
        # shimmer doesn't mutate the cached sprite (set_alpha on the cached
        # surface would persist across frames).
        water_sprite = load_terrain("water")
        for wr in self.scene._water:
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
        for br in self.scene._bridges:
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
            wc = self.scene.party[self.scene.active]
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
        dlg = self.scene._dialogue
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
            pulse = 1.0 if self.scene._reduce_motion else (
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
        if getattr(self.scene, "_reduce_motion", False):
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
        """A full-width cinematic banner shown after the final boss (Baron
        Nashor at 9,4) is defeated, signalling the player can Ascend the World
        to start a new Aetheric Cycle (NG+). Reuses the boss-banner fade shape."""
        dur = 3.0
        if t > dur * 0.8:
            a = max(0, 1 - (t - dur * 0.8) / (dur * 0.2))   # fading out
        elif t < dur * 0.2:
            a = max(0, 1 - (dur * 0.2 - t) / (dur * 0.2))   # fading in
        else:
            a = 1.0
        alpha = int(220 * a)
        if getattr(self.scene, "_reduce_motion", False):
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
        pal = WD.BIOMES[WD.cell_biome(self.scene.c, self.scene.r)]
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
        sky = self._sky_for_phase(sky, _qphase=round(self.scene._world_time * 16) / 16 % 1.0)
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
            wc = self.scene.party[self.scene.active]
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
        if not self.scene._reduce_motion:
            if self.scene._weather in ("rain", "storm"):
                rain_ov = self._rain_overlay()
                surf.blit(rain_ov, (0, 0))
            elif self.scene._weather == "fog":
                fog_ov = self._fog_overlay()
                surf.blit(fog_ov, (0, 0))

        # full-screen flashes (reuse one persistent overlay surface)
        if self.scene.map_enter_t > 0 or self.scene.swap_flash > 0 or self.scene.flash > 0:
            ov = self.scene._flash_surf
            ov.fill((0, 0, 0, 0))
            if self.scene.map_enter_t > 0:
                # a directional slide-wipe for edge transitions, a soft circle
                # wipe for teleports; falls back to a flat fade
                a = int(190 * (self.scene.map_enter_t / 0.45))
                if self.scene._reduce_motion:
                    a = min(a, 60)
                d = self.scene._enter_dir
                if d in ("left", "right", "top", "bottom"):
                    prog = 1 - (self.scene.map_enter_t / 0.45)   # 0..1 as it clears
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
            if self.scene.swap_flash > 0:
                a = int(120 * (self.scene.swap_flash / 0.3))
                ov.fill((180, 220, 255, a))
            if self.scene.flash > 0:
                a = int(120 * self.scene.flash)
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
        ov = self.scene._light_cache.get(key)
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
            self.scene._light_cache[key] = ov
        return ov

    def _rain_overlay(self):
        """A cached full-screen rain overlay — a field of diagonal alpha streaks
        drawn once into a 1280x720 surface and blitted as a single image per
        frame. The streaks are static (the rain 'moves' via the streak offsets
        baked into the sprite) so the overlay is one blit, not a per-frame
        redraw of ~80 lines. Cached in _light_cache so the 3.5MB surface is
        built once per scene, not per frame."""
        key = ("weather_rain",)
        ov = self.scene._light_cache.get(key)
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
            self.scene._light_cache[key] = ov
        return ov

    def _fog_overlay(self):
        """A cached full-screen fog overlay — a flat low-alpha grey-blue
        darkening so the world reads as hazy (a heavier version of the night
        overlay, tinted cool so it reads as fog, not night). One blit per
        frame; cached in _light_cache so the surface is built once."""
        key = ("weather_fog",)
        ov = self.scene._light_cache.get(key)
        if ov is None:
            ov = pygame.Surface((1280, 720), pygame.SRCALPHA)
            ov.fill((180, 200, 220, 60))
            self.scene._light_cache[key] = ov
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
        p = _qphase if _qphase is not None else self.scene._world_time
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
        p = self.scene._world_time
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
        ov = self.scene._light_cache.get(key)
        if ov is None:
            a = int(level * 11)   # up to ~88 alpha at the deepest night
            ov = pygame.Surface((1280, 720), pygame.SRCALPHA)
            ov.fill((6, 8, 24, a))
            self.scene._light_cache[key] = ov
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
        sp = self.scene._light_cache.get(key)
        if sp is None:
            R = 140
            sp = pygame.Surface((R * 2, R * 2), pygame.SRCALPHA)
            warm = (255, 220, 160)
            for k in range(R, 0, -8):
                a = int(10 * level * (1 - k / R))
                pygame.draw.circle(sp, (*warm, a), (R, R), k)
            self.scene._light_cache[key] = sp
        return sp

    def _draw_edge_hints(self, surf, ox, oy):
        # glowing chevron arrows at traversable map edges, pointing the way out
        c, r = self.scene.c, self.scene.r
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
