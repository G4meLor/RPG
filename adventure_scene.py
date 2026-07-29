"""
Aetheria Adventure Mode - AdventureScene (Task D1)
A wave-survival mode distinct from the open world: a 10-min survival per stage,
continuous waves (scaling with stage level + elapsed time), a boss at the 5-min
mark, stage-clear on boss defeat (advance the stage ladder, +5 enemy levels, full
heal), run-end on party wipe.

Subclass of WorldScene — inherits the combat helpers (_do_attack / _do_skill /
_do_ultimate / _on_enemy_hit / _on_enemy_death / _on_enemy_event / _element_mult /
_compute_resonances / _switch / _build_party) and overrides __init__ / update /
draw with the stage/timer/wave/boss logic. This avoids touching WorldScene at all
(zero regression risk to the 20/20 + 8/8 suites, which test WorldScene).

The update override calls super().update() so the full WorldScene combat + input +
movement + drawables run unchanged. The open-world-only parts (edge transitions,
rift, chests, weather, day/night) also run, but in the fixed (0,0) plains arena
they are benign: the hero is centered (no edge-portal gaps reached), the rift is a
bonus wave if present, the chests are walk-over loot, the weather is a cosmetic
overlay. The adventure-specific logic (the stage timer, the wave spawner, the
boss-at-5-min, the stage-clear, the party-wipe) runs BEFORE super().update() so
the combat loop sees the freshly-spawned enemies this frame.
"""
import math
import random

import pygame

import data as D
import audio
import world_data as WD
from world_entities import WorldEnemy, scratch
from world_scene import WorldScene, _font, text


# Adventure HUD layout (top-center, above the boss bar at y=18).
# The timer + stage + wave counter sit in a slim panel so they read as a
# mode-specific HUD, not the open-world map name / resources.
_ADV_HUD_Y = 18
_ADV_HUD_H = 28


class AdventureScene(WorldScene):
    """Wave-survival scene: 10-min per stage, waves every 25s, boss at 5 min,
    stage-clear on boss defeat, party-wipe ends the run. Subclass of WorldScene
    so the combat engine (AA, hold-to-aim, skill taxonomy, reactions, combo,
    summons/traps, drops) is reused via inheritance — no duplication."""

    def __init__(self, game):
        # super().__init__ sets up the full WorldScene state (the party, the map,
        # the combat state) for ow_current (the open-world cell). Then we
        # OVERRIDE the open-world state with the stage state: force-load the
        # plains arena at (0,0), set the stage ladder from the save, reset the
        # stage timer + wave timer + boss flag + run-over flag.
        super().__init__(game)
        # the stage ladder: resume at the player's best stage so a returning
        # player picks up where they left off. _stage is the current stage
        # (0-indexed); adventure_best_stage is the highest stage reached.
        self._stage = int(self.game.player.adventure_best_stage)
        self._stage_t = 0.0          # seconds elapsed in the current stage
        self._wave_t = 0.0           # seconds since the last wave spawn
        self._boss_spawned = False    # has the 5-min boss spawned this stage?
        self._boss = None             # the WorldEnemy boss (for stage-clear check)
        self._run_over = False        # party-wipe flag (the run has ended)
        self._is_adventure = True     # flag for the overridden update/draw
        # force-load the plains arena at (0,0) so the adventure is always in a
        # fixed plains map (super().__init__ loaded ow_current, which may be a
        # non-plains cell for a player who last played the open world). Re-calling
        # _load_map re-runs the gen_map + the enemy spawns for (0,0); we then
        # clear the open-world spawns so the stage starts empty (the wave
        # spawner populates the arena).
        self.c, self.r = 0, 0
        self._load_map(target_cell=(0, 0))
        # clear the open-world enemy spawns so the stage starts with a clean
        # arena (the wave spawner populates it). Keep chests/breakables as
        # walk-over loot (they're benign in the fixed arena).
        self.enemies = []
        # place the active hero at the arena center so the player starts in the
        # middle of the plains (not at the edge entry point _load_map set).
        if self.party[self.active]:
            self.party[self.active].x = WD.MAP_W // 2
            self.party[self.active].y = WD.MAP_H // 2
            self.party[self.active].vx = 0
            self.party[self.active].vy = 0
            # snap the camera onto the hero so the first frame is centered
            self.camera.x = max(0, min(WD.MAP_W - self.camera.vw,
                                       self.party[self.active].x - self.camera.vw / 2))
            self.camera.y = max(0, min(WD.MAP_H - self.camera.vh,
                                       self.party[self.active].y - self.camera.vh / 2))
        # full-heal the party on stage entry so the player starts each stage at
        # full HP/energy (the stage is a fresh challenge, not a continuation of
        # the last stage's damage).
        for wc in self.party:
            if wc:
                wc.hero.hp = wc.hero.max_hp
                wc.hero.energy = wc.hero.max_energy
                wc.alive = True
        # a stage-entry banner so the player sees which stage they're on.
        self.set_message(f"Stage {self._stage + 1} — Survive!", 2.5)

    # -----------------------------------------------------------------
    # Wave spawner
    # -----------------------------------------------------------------
    def _spawn_wave(self):
        """Spawn a wave of enemies from the arena edges. Count + level scale
        with the stage level + the elapsed time so the waves ramp in difficulty
        over the 10-min stage. Enemies spawn at the arena edges (x near 0 or
        MAP_W, y random in the playable area) so the player sees them coming."""
        pool, _ = WD.ROW_ENEMIES[0]   # the plains row pool (slime/goblin/bat)
        # wave size: base 4 + the stage level + 1 per minute elapsed (capped so
        # a long stage doesn't flood the arena). The +1/min ramp makes the later
        # minutes of a stage feel more desperate than the opening.
        count = 4 + self._stage + int(self._stage_t / 60)
        count = max(3, min(count, 14))
        # enemy level: the stage level * the step + 1 per 2 min elapsed so the
        # enemies scale with both the stage ladder + the time spent in the stage.
        level = self._stage * D.ADVENTURE_STAGE_LEVEL_STEP + int(self._stage_t / 120)
        level = max(1, level)
        # spawn from the arena edges: alternate left/right edges, y random in
        # the playable area (TILE..MAP_H-TILE so they don't spawn on the border
        # wall). Spread along the edge so a wave reads as a line, not a stack.
        for i in range(count):
            edge = random.choice(("left", "right"))
            sx = WD.TILE + 8 if edge == "left" else WD.MAP_W - WD.TILE - 8
            sy = random.randint(WD.TILE * 2, WD.MAP_H - WD.TILE * 2)
            eid = random.choice(pool)
            en = WorldEnemy(eid, sx, sy, level, is_boss=False)
            self.enemies.append(en)
        # a wave-spawn burst at the edges so the spawn reads as an event (not a
        # silent pop). Reuses the rift-seal burst shape.
        self.particles.burst(WD.TILE + 8, WD.MAP_H // 2, (180, 80, 220),
                             n=18, speed=240, size=6, life=0.5)
        self.particles.burst(WD.MAP_W - WD.TILE - 8, WD.MAP_H // 2, (180, 80, 220),
                             n=18, speed=240, size=6, life=0.5)
        self.camera.add_shake(3, self._shake_mul)
        audio.play("boss_intro", 0.25)

    def _spawn_adventure_boss(self):
        """Spawn the stage boss at the arena center. A row boss from the plains
        row pool (golem), scaled to the stage level + 6 (the same +6 the
        open-world boss arenas use) so the boss is a real threat. is_boss=True
        so the boss AI (phases, telegraphs, ult) + the boss HP bar + the boss
        intro cinematic all fire via the inherited WorldScene paths."""
        _, boss_id = WD.ROW_ENEMIES[0]   # plains boss = golem
        level = self._stage * D.ADVENTURE_STAGE_LEVEL_STEP + 6
        bx, by = WD.MAP_W // 2, WD.MAP_H // 2
        boss = WorldEnemy(boss_id, bx, by, level, is_boss=True)
        self.enemies.append(boss)
        self._boss = boss
        # boss intro cinematic: reuse the WorldScene boss-intro path so the
        # adventure boss gets the same name banner + slow-mo as an open-world boss.
        boss_name = D.ENEMIES_DB.get(boss_id, {}).get("name", "Boss")
        self._boss_intro_t = 1.6
        self._boss_intro_name = boss_name
        audio.play("boss_intro", 0.7)
        self.set_message(f"BOSS INCOMING — {boss_name}!", 3.0)

    # -----------------------------------------------------------------
    # Update — the stage timer, the wave spawner, the boss, the stage-clear,
    # the party-wipe. Runs BEFORE super().update() so the combat loop sees the
    # freshly-spawned enemies this frame.
    # -----------------------------------------------------------------
    def update(self, dt, events):
        # if the run is over, the title transition is handled by the party-wipe
        # path below (game.goto('title')). Bail so we don't keep simulating a
        # dead run.
        if self._run_over:
            return
        # hit-stop pauses the world sim but not the stage timer's input handling.
        # Mirror WorldScene.update's hit-stop so the stage timer respects the
        # same freeze (a boss phase-transition hit-stop shouldn't advance the
        # stage timer).
        if self.hit_stop > 0:
            self.hit_stop = max(0, self.hit_stop - dt)
            sim_dt = 0
        else:
            sim_dt = dt
        # advance the stage timer (sim_dt, so hit-stop freezes the timer too).
        self._stage_t += sim_dt
        # wave spawner: every ADVENTURE_WAVE_INTERVAL seconds, spawn a wave.
        self._wave_t += sim_dt
        if self._wave_t >= D.ADVENTURE_WAVE_INTERVAL:
            self._wave_t = 0.0
            self._spawn_wave()
        # boss at the 5-min mark: spawn once per stage (gated on _boss_spawned
        # so the boss doesn't re-spawn every frame after 5 min).
        if self._stage_t >= D.ADVENTURE_BOSS_TIME and not self._boss_spawned:
            self._boss_spawned = True
            self._spawn_adventure_boss()
        # stage-clear: the boss was spawned + is now dead (no boss enemy alive).
        # Advance the stage ladder, full-heal the party, reset the timer + wave
        # timer + boss flag, clear the enemies, and persist the best stage.
        if self._boss_spawned and self._boss is not None and not self._boss.alive:
            self._stage += 1
            self.game.player.adventure_best_stage = max(
                self.game.player.adventure_best_stage, self._stage)
            self._stage_t = 0.0
            self._wave_t = 0.0
            self._boss_spawned = False
            self._boss = None
            # full-heal the party on a stage-clear so the next stage starts fresh.
            for wc in self.party:
                if wc:
                    wc.hero.hp = wc.hero.max_hp
                    wc.hero.energy = wc.hero.max_energy
                    wc.alive = True
                    wc.kb_x = wc.kb_y = 0.0
                    wc.iframes = 0.5
                    wc.invuln_t = 0.5
            # clear the enemies so the next stage starts with a clean arena.
            self.enemies = []
            self.projectiles = []
            self._summons = []
            self._traps = []
            # a stage-clear celebration: a burst + a banner so the clear feels
            # rewarding (reuses the rift-clear burst shape).
            cx, cy = WD.MAP_W // 2, WD.MAP_H // 2
            self.particles.burst(cx, cy, (255, 220, 120), n=40,
                                 speed=320, size=8, life=0.8, grav=0)
            self.particles.ring(cx, cy, (255, 240, 160), n=28,
                                speed=440, size=7, life=0.7)
            self.camera.add_shake(8, self._shake_mul)
            audio.play("gacha_reveal", 0.6)
            self.set_message(f"Stage {self._stage} Cleared! Advancing...", 3.0)
            if self.game.player.settings.get("auto_save", True):
                self.game.player.save()
        # run-end: party wipe (all 4 slots dead/None) -> end the run, return to
        # the title screen. The open-world _on_hero_down path revives the party
        # at the hub on a wipe, but in Adventure a wipe ends the run (the mode
        # is a roguelike stage ladder, not the open world). Check BEFORE
        # super().update() so the open-world revive-at-hub path doesn't fire
        # first (it would revive the party + teleport to (0,0), masking the
        # wipe). We set _run_over + goto title so the WorldScene revive path is
        # bypassed (the _on_hero_down path checks for a living hero; we've
        # already decided the run is over).
        if all(wc is None or not wc.alive for wc in self.party):
            self._run_over = True
            # persist the best stage so the player resumes at the right stage
            # next time (the stage-clear path already persisted it if the player
            # cleared a stage this run; this covers a run that ended mid-stage).
            if self.game.player.settings.get("auto_save", True):
                self.game.player.save()
            # stop the looping ambience on the run end (otherwise it keeps
            # playing under the title menu).
            audio.set_ambience(False)
            self.set_message("Party Wiped — Run Over", 3.0)
            audio.play("defeat", 0.7)
            self.game.goto("title")
            return
        # run the full WorldScene update (combat + input + movement + drawables
        # + the open-world logic). The open-world logic (edge transitions, rift,
        # chests, weather, day/night) is benign in the fixed (0,0) plains arena:
        # the hero is centered (no edge-portal gaps reached), the rift is a bonus
        # wave if present, the chests are walk-over loot, the weather is a
        # cosmetic overlay. This is the lower-risk option (the brief's
        # recommendation) — the 20/20 + 8/8 suites test WorldScene, not
        # AdventureScene, so inheriting the open-world logic is acceptable for
        # D1 (the user can refine later).
        super().update(dt, events)

    # -----------------------------------------------------------------
    # Draw — the WorldScene draw (map, drawables, HUD) + the adventure HUD on
    # top (the stage timer, the stage number, the wave counter, the boss
    # warning).
    # -----------------------------------------------------------------
    def draw(self, surf):
        super().draw(surf)
        # adventure HUD: a slim top-center panel with the stage timer (the
        # 10-min countdown), the stage number, and the wave counter. Drawn AFTER
        # the WorldScene HUD so it sits on top (the boss bar at y=18 is drawn in
        # _draw_hud; the adventure HUD is at y=18 too but the boss bar is hidden
        # until a boss spawns, so the timer panel occupies the top-center slot
        # until the boss arrives, then the boss bar takes over).
        self._draw_adventure_hud(surf)

    def _draw_adventure_hud(self, surf):
        """The adventure mode HUD: a top-center panel with the stage timer (a
        10-min countdown), the stage number, and the wave counter. A "BOSS
        INCOMING" warning pulses when the stage timer approaches the boss time
        (so the player knows the boss is near). Drawn AFTER the WorldScene HUD
        so it sits on top of the open-world HUD (the map name / resources at
        top-right stay visible; the adventure panel is top-center)."""
        # the panel: top-center, 360 wide so it fits the timer + stage + wave.
        pw = 360
        ph = _ADV_HUD_H
        px = (1280 - pw) // 2
        py = _ADV_HUD_Y
        # skip drawing the adventure timer panel when a boss is alive (the boss
        # HP bar at the same y takes precedence — the player is in the climax).
        boss_alive = any(e.is_boss and e.alive for e in self.enemies)
        if not boss_alive:
            panel = scratch(pw, ph)
            pygame.draw.rect(panel, (20, 20, 36, 210), panel.get_rect(), border_radius=8)
            pygame.draw.rect(panel, (140, 160, 200), panel.get_rect(), 2, border_radius=8)
            surf.blit(panel, (px, py))
            # the 10-min countdown: 10 min - elapsed (in minutes), so the player
            # sees the time remaining in the stage. Turns red in the last 2 min.
            mins_left = max(0, D.ADVENTURE_STAGE_TIME_LIMIT - self._stage_t) / 60.0
            timer_col = (255, 220, 120) if mins_left > 2.0 else (255, 120, 120)
            text(surf, f"{mins_left:4.1f}m", 20, timer_col, (px + 12, py + 4))
            # the stage number (left of center) so the player knows which stage.
            text(surf, f"Stage {self._stage + 1}", 16, (255, 240, 200),
                 (px + 120, py + 6))
            # the wave counter: the number of enemies currently in the arena
            # (a live threat count, not a waves-elapsed count — the player cares
            # about what's on screen right now).
            n_enemies = sum(1 for e in self.enemies if e.alive and not e.is_boss)
            text(surf, f"Enemies {n_enemies}", 14, (220, 220, 240),
                 (px + 230, py + 8))
        # "BOSS INCOMING" warning: pulses in the last 30s before the boss spawns
        # (so the player knows the boss is near + can prep). Drawn under the
        # timer panel so it reads as a subtitle, not a replacement.
        if not self._boss_spawned:
            t_to_boss = D.ADVENTURE_BOSS_TIME - self._stage_t
            if 0 < t_to_boss < 30:
                pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.012)
                col = (int(200 * pulse + 55), int(40 * pulse + 30), int(60 * pulse + 40))
                text(surf, f"BOSS INCOMING — {int(t_to_boss)}s", 18, col,
                     (640, py + ph + 6), center=True)
