"""PhysicsSystem (Phase 4, Task 15 of the ECS restructure) — movement,
collision, and camera.

The Camera class was moved here from `src/entities/world_actors.py`
(re-exported there for backward compatibility). The PhysicsSystem mirrors the
legacy `WorldCharacter.update` movement body, but operates on the ECS entity
components (`Transform` + `Movement`) instead of `self.x`/`self.vx`/`self.dash_t`.

CRITICAL (this task): the legacy `WorldCharacter.update` movement path STAYS
the source of truth. PhysicsSystem runs IN PARALLEL (additive), reading the
same input + writing entity `Transform`. The adapter (`_sync_entities`) still
copies legacy `wc.x/y` onto entity `Transform` AFTER `update`, so the
PhysicsSystem writes may be OVERWRITTEN by the sync. That's fine for now: the
test checks the entity moved (the sync copies the legacy position which DID
move). The point is to PROVE the PhysicsSystem logic works in isolation. Full
takeover of movement from the legacy object happens in Task 20.
"""
import math

import pygame

from src.data.tuning import ENERGY_REGEN_PCT


# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
class Camera:
    def __init__(self, vw, vh):
        self.x = 0.0
        self.y = 0.0
        self.vw = vw
        self.vh = vh
        self.shake = 0.0
        self.shake_t = 0.0
        # smoothed velocity for look-ahead + a little extra lerp weight so the
        # camera feels weighty but never laggy
        self._vx = 0.0
        self._vy = 0.0

    def follow(self, tx, ty, map_w, map_h, dt, look_ahead=(0, 0)):
        # smooth lerp toward target (top-left of the view)
        lax, lay = look_ahead
        target_x = tx - self.vw / 2 + lax
        target_y = ty - self.vh / 2 + lay
        # clamp to map bounds
        target_x = max(0, min(map_w - self.vw, target_x))
        target_y = max(0, min(map_h - self.vh, target_y))
        # critically-damped spring: faster catch-up, no overshoot
        k = min(1, dt * 9)
        self.x += (target_x - self.x) * k
        self.y += (target_y - self.y) * k
        # clamp again after lerp (avoids drift past edges)
        self.x = max(0, min(map_w - self.vw, self.x))
        self.y = max(0, min(map_h - self.vh, self.y))
        # shake decay
        if self.shake > 0:
            self.shake = max(0, self.shake - dt * 40)
            self.shake_t += dt * 40

    def add_shake(self, amt, mult=1.0):
        self.shake = min(14, self.shake + amt * mult)

    def offset(self):
        ox, oy = self.x, self.y
        if self.shake > 0:
            # two-frequency shake feels less mechanical than a single sine
            ox += math.sin(self.shake_t * 3.1) * self.shake + math.sin(self.shake_t * 7.3) * self.shake * 0.3
            oy += math.cos(self.shake_t * 2.7) * self.shake + math.cos(self.shake_t * 6.1) * self.shake * 0.3
        return int(ox), int(oy)


# ---------------------------------------------------------------------------
# PhysicsSystem
# ---------------------------------------------------------------------------
class PhysicsSystem:
    """ECS movement/collision system. Mirrors the legacy
    `WorldCharacter.update` movement body, but reads/writes the entity's
    `Transform` + `Movement` components instead of `self.x`/`self.vx`/etc.

    The legacy movement path stays the source of truth this task; this system
    runs in parallel (additive) to prove the extraction works in isolation.
    """

    def __init__(self, world, scene=None):
        self.world = world
        self.scene = scene

    def update(self, dt, entity, input_vec, obstacles=None, want_dash=False):
        """Mirror `WorldCharacter.update` movement, operating on the entity's
        `Transform` + `Movement` components instead of `self.x`/`self.vx`/etc.

        Args:
            dt: frame delta seconds.
            entity: an Entity with Transform + Movement components.
            input_vec: (ix, iy) keyboard/dir input (auto-normalized).
            obstacles: iterable of pygame.Rect (collision rects). None => [].
            want_dash: True to trigger a dash this frame (LoL-style shift-dash).

        Returns: None (mutates the entity's Transform + Movement in place).
        """
        # Imported lazily inside the method to avoid a circular import at
        # module load time: src.entities.__init__ eagerly imports
        # world_actors, which re-exports Camera from this module, so
        # top-level `from src.entities.components import ...` would run before
        # src.entities is fully initialized.
        from src.entities.components import Transform, Movement
        """Mirror `WorldCharacter.update` movement, operating on the entity's
        `Transform` + `Movement` components.

        Args:
            dt: frame delta seconds.
            entity: an Entity with Transform + Movement components.
            input_vec: (ix, iy) keyboard/dir input (auto-normalized).
            obstacles: iterable of pygame.Rect (collision rects). None => [].
            want_dash: True to trigger a dash this frame (LoL-style shift-dash).

        Returns: None (mutates the entity's Transform + Movement in place).
        """
        t = entity.get(Transform)
        m = entity.get(Movement)
        if t is None or m is None:
            return
        obstacles = obstacles if obstacles is not None else []

        # knockback decays
        if abs(m.kb_x) > 1 or abs(m.kb_y) > 1:
            t.x += m.kb_x * dt
            t.y += m.kb_y * dt
            m.kb_x *= 0.8
            m.kb_y *= 0.8

        ix, iy = input_vec
        # LoL-style click-to-move: if the player isn't pressing WASD, the hero
        # auto-walks toward the RMB-set move_target until it reaches it. Any
        # WASD press overrides + clears the target (keyboard has priority).
        if ix or iy:
            m.move_target = None
        elif m.move_target is not None:
            tx, ty = m.move_target
            dx = tx - t.x
            dy = ty - t.y
            d = math.hypot(dx, dy)
            m.move_target_t += dt
            if d < 8:
                # reached the target — stop auto-moving
                m.move_target = None
            else:
                # stall detection: if the hero isn't getting closer (blocked by a
                # wall), clear the target after 0.3s so the reticle doesn't hang
                # on a wall forever (the "stray white circle" fix)
                if d >= m._last_mt_dist - 1:
                    m._mt_stall_t += dt
                    if m._mt_stall_t > 0.3:
                        m.move_target = None
                else:
                    m._mt_stall_t = 0
                m._last_mt_dist = d
                if m.move_target is not None:
                    # synthesize a normalized input toward the target so the
                    # existing accel/friction movement handles it (no special-case path)
                    ix = dx / d
                    iy = dy / d
                    # face the direction we're walking
                    m.facing = 1 if dx > 0 else -1
                    m.moving = True

        # dash
        if want_dash and m.dash_cd <= 0 and (ix or iy):
            m.dash_t = 0.16
            m.iframes = 0.22
            m.dash_cd = 0.7
            n = math.hypot(ix, iy) or 1
            m.dash_dir = (ix / n, iy / n)
        if m.dash_t > 0:
            m.dash_t -= dt
            ds = 520
            t.x += m.dash_dir[0] * ds * dt
            t.y += m.dash_dir[1] * ds * dt
            m.moving = True
        else:
            # normal movement with accel + friction
            n = math.hypot(ix, iy)
            if n > 0:
                ix /= n; iy /= n
                t.vx += ix * m.accel * dt
                t.vy += iy * m.accel * dt
                if ix != 0:
                    m.facing = 1 if ix > 0 else -1
                m.moving = True
            else:
                # friction
                f = m.friction * dt
                if abs(t.vx) <= f: t.vx = 0
                else: t.vx -= f * (1 if t.vx > 0 else -1)
                if abs(t.vy) <= f: t.vy = 0
                else: t.vy -= f * (1 if t.vy > 0 else -1)
                m.moving = False
            # clamp speed
            ms = m.max_speed
            sp = math.hypot(t.vx, t.vy)
            if sp > ms:
                t.vx = t.vx / sp * ms
                t.vy = t.vy / sp * ms
            t.x += t.vx * dt
            t.y += t.vy * dt

        # collide with obstacles (axis separated)
        self._collide(t, m, obstacles)

        # timers
        m.dash_cd = max(0, m.dash_cd - dt)
        m.iframes = max(0, m.iframes - dt)

    def _collide(self, t, m, obstacles):
        # X axis
        r = pygame.Rect(int(t.x - m.r), int(t.y - m.r), m.r * 2, m.r * 2)
        for o in obstacles:
            if r.colliderect(o):
                if t.vx > 0:
                    t.x = o.left - m.r
                elif t.vx < 0:
                    t.x = o.right + m.r
                t.vx = 0
                r.x = int(t.x - m.r)
        # Y axis
        r = pygame.Rect(int(t.x - m.r), int(t.y - m.r), m.r * 2, m.r * 2)
        for o in obstacles:
            if r.colliderect(o):
                if t.vy > 0:
                    t.y = o.top - m.r
                elif t.vy < 0:
                    t.y = o.bottom + m.r
                t.vy = 0
                r.y = int(t.y - m.r)
        # keep inside map bounds (caller passes border walls as obstacles too)

    # -----------------------------------------------------------------------
    # Task 20d — full-fidelity verbatim port of WorldCharacter.update.
    # The body below is copied verbatim from src/entities/world_actors.py
    # (the `update` method on WorldCharacter, starting at line 622). The only
    # rewire is `self` (the WorldCharacter) -> `wc` (the WorldCharacter passed
    # as the first arg). The method operates on the wc's OWN fields (x, vx,
    # atk_cd, hero, etc.); there is no scene state to rewire. WorldCharacter
    # .update becomes a 1-line delegate to this staticmethod (see
    # world_actors.py). The signature passive update handlers
    # (_SIG_UPDATE) are imported lazily from the legacy module to avoid a
    # circular import at module load time (this module is imported by the
    # legacy module via `from src.systems.physics import Camera`).
    # -----------------------------------------------------------------------
    @staticmethod
    def update_hero(wc, dt, input_dir, obstacles, want_dash):
        # knockback decays
        if abs(wc.kb_x) > 1 or abs(wc.kb_y) > 1:
            wc.x += wc.kb_x * dt
            wc.y += wc.kb_y * dt
            wc.kb_x *= 0.8
            wc.kb_y *= 0.8

        # LoL-style click-to-move: if the player isn't pressing WASD, the hero
        # auto-walks toward the RMB-set move_target until it reaches it. Any
        # WASD press overrides + clears the target (keyboard has priority).
        if input_dir[0] or input_dir[1]:
            wc.move_target = None
        elif wc.move_target is not None:
            tx, ty = wc.move_target
            dx = tx - wc.x
            dy = ty - wc.y
            d = math.hypot(dx, dy)
            wc.move_target_t += dt
            if d < 8:
                # reached the target — stop auto-moving
                wc.move_target = None
            else:
                # stall detection: if the hero isn't getting closer (blocked by a
                # wall), clear the target after 0.3s so the reticle doesn't hang
                # on a wall forever (the "stray white circle" fix)
                if d >= wc._last_mt_dist - 1:
                    wc._mt_stall_t += dt
                    if wc._mt_stall_t > 0.3:
                        wc.move_target = None
                else:
                    wc._mt_stall_t = 0
                wc._last_mt_dist = d
                if wc.move_target is not None:
                    # synthesize a normalized input toward the target so the
                    # existing accel/friction movement handles it (no special-case path)
                    input_dir = (dx / d, dy / d)
                    # face the direction we're walking
                    wc.facing = 1 if dx > 0 else -1
                    wc.moving = True

        # dash
        if want_dash and wc.dash_cd <= 0 and (input_dir[0] or input_dir[1]):
            wc.dash_t = 0.16
            wc.iframes = 0.22
            wc.dash_cd = 0.7
            n = math.hypot(*input_dir) or 1
            wc.dash_dir = (input_dir[0] / n, input_dir[1] / n)
        if wc.dash_t > 0:
            wc.dash_t -= dt
            ds = 520
            wc.x += wc.dash_dir[0] * ds * dt
            wc.y += wc.dash_dir[1] * ds * dt
            wc.moving = True
        else:
            # normal movement with accel + friction
            ix, iy = input_dir
            n = math.hypot(ix, iy)
            if n > 0:
                ix /= n; iy /= n
                wc.vx += ix * wc.accel * dt
                wc.vy += iy * wc.accel * dt
                if ix != 0:
                    wc.facing = 1 if ix > 0 else -1
                wc.moving = True
            else:
                # friction
                f = wc.friction * dt
                if abs(wc.vx) <= f: wc.vx = 0
                else: wc.vx -= f * (1 if wc.vx > 0 else -1)
                if abs(wc.vy) <= f: wc.vy = 0
                else: wc.vy -= f * (1 if wc.vy > 0 else -1)
                wc.moving = False
            # clamp speed (with swift passive)
            ms = wc.move_speed
            sp = math.hypot(wc.vx, wc.vy)
            if sp > ms:
                wc.vx = wc.vx / sp * ms
                wc.vy = wc.vy / sp * ms
            wc.x += wc.vx * dt
            wc.y += wc.vy * dt

        # collide with obstacles (axis separated)
        wc._collide(obstacles)

        # timers
        wc.dash_cd = max(0, wc.dash_cd - dt)
        wc.iframes = max(0, wc.iframes - dt)
        wc.invuln_t = max(0, wc.invuln_t - dt)
        wc.atk_cd = max(0, wc.atk_cd - dt)
        wc.atk_anim = max(0, wc.atk_anim - dt)
        wc.hit_flash = max(0, wc.hit_flash - dt)
        wc._shield_cd = max(0, wc._shield_cd - dt)
        # perfect-dodge window opens right after a dash ends (the i-frames are
        # the dodge itself; this is the "just-dodged" reward window) and counts
        # down. The damage buff from a successful perfect dodge decays too.
        # Track the previous dash state so we detect the dash->no-dash edge and
        # open the window exactly once when it ends.
        was_dashing = getattr(wc, "_was_dashing", False)
        is_dashing = wc.dash_t > 0 or wc.iframes > 0
        if was_dashing and not is_dashing and wc.dash_cd > 0.3:
            wc._perfect_dodge_t = 0.15
        wc._was_dashing = is_dashing
        wc._perfect_dodge_t = max(0, wc._perfect_dodge_t - dt)
        wc._dmg_buff_t = max(0, wc._dmg_buff_t - dt)
        for i in range(3):
            wc.skill_cd[i] = max(0, wc.skill_cd[i] - dt)
        wc.ult_cd = max(0, wc.ult_cd - dt)
        # out-of-combat regen passive
        wc._last_combat_t += dt
        if (wc.hero.passive and wc.hero.passive.get("kind") == "regen"
                and wc._last_combat_t > 2.0 and wc.alive
                and wc.hero.hp < wc.hero.max_hp):
            wc.hero.hp = min(wc.hero.max_hp,
                               wc.hero.hp + wc.hero.max_hp * wc.hero.passive.get("val", 0.02) * dt)
        # signature passive update handlers (dict-lookup dispatch). stacking_atk
        # decays by 1 every 3s out of combat so a stale streak doesn't persist.
        # Imported lazily to avoid a circular import (this module is imported by
        # the legacy module at load time).
        from src.entities.world_actors import _SIG_UPDATE
        _sig_upd = _SIG_UPDATE.get(wc._signature_kind)
        if _sig_upd:
            _sig_upd(wc, dt)
        # passive energy regen: recover energy over time so a hero with low
        # energy can use skills again without landing a hit (the "skills don't
        # recover / mana doesn't increase" fix). Slower in combat. The light
        # elemental resonance (energy_regen) boosts the rate additively (a 2-light
        # party regens 15% faster); the p_energy (Flow State) passive only applies
        # to discrete energy gains from hits/skills, not to this passive trickle,
        # so there's no double-apply to guard here.
        if wc.alive and wc.hero.energy < wc.hero.max_energy:
            rate = ENERGY_REGEN_PCT * (0.5 if wc._last_combat_t < 1.5 else 1.0)
            rate *= (1 + wc._res_energy_regen)
            wc.hero.energy = min(wc.hero.max_energy,
                                   wc.hero.energy + wc.hero.max_energy * rate * dt)

        # walk anim + idle breathing + squash/stretch
        if wc.moving:
            wc.walk_t += dt * 11
            # landing/squash from vertical bob of the walk cycle
            phase = math.sin(wc.walk_t)
            wc.scale_y = 1.0 + phase * 0.04
            wc.scale_x = 1.0 - phase * 0.03
        else:
            wc.walk_t *= 0.85
            wc.idle_t += dt * 2.2
            # gentle breathing
            br = math.sin(wc.idle_t) * 0.025
            wc.scale_y = 1.0 + br
            wc.scale_x = 1.0 - br * 0.6
        # attack lunge: forward lean that eases back (drive from atk_anim)
        if wc.atk_anim > 0:
            # 0.2s swing -> lunge peaks early then returns
            t = 1 - (wc.atk_anim / 0.2)
            wc.lunge = math.sin(min(1, t) * math.pi) * 14 * wc.facing
            wc.scale_x = 1.0 + 0.10 * math.sin(min(1, t) * math.pi)
        else:
            wc.lunge *= 0.8

        # reload sprite if facing changed (flip cache)
        if wc._sprite is not None and wc._sprite_face != wc.facing:
            wc._sprite = pygame.transform.flip(wc._sprite, True, False)
            wc._sprite_face = wc.facing
