"""PhysicsSystem (Phase 4, Task 15 of the ECS restructure) — movement,
collision, and camera.

The Camera class was moved here from `src/entities/_legacy_world_entities.py`
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
        # _legacy_world_entities, which re-exports Camera from this module, so
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
