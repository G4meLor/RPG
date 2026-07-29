"""
Aetheria Open World - World Entities
Camera, particles, projectiles, the real-time WorldCharacter and WorldEnemy.
Reuses data.py (skills, elements, tuning) and entities.py (Hero stats).
"""
import math
import random

import pygame

import data as D
from entities import Hero, load_char_sprite, load_enemy_sprite


# ---------------------------------------------------------------------------
# Reusable scratch surfaces for per-entity draw effects (shadows, flashes,
# telegraph glows). Allocated once per (w,h) and cleared each use instead of
# creating a new SRCALPHA surface every frame per entity — the second-biggest
# cost in the profile after font rendering.
# ---------------------------------------------------------------------------
_SCRATCH = {}
def scratch(w, h):
    w = int(w); h = int(h)
    s = _SCRATCH.get((w, h))
    if s is None:
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        _SCRATCH[(w, h)] = s
    s.fill((0, 0, 0, 0))
    return s

# Cached "BROKEN" tag surface for WorldEnemy.draw — rendered once and reused
# so a broken enemy doesn't re-render the string every frame (font.render is a
# top profile cost). Lazily filled on first broken draw.
_BROKEN_TAG_SURF = None


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
# Particles
# ---------------------------------------------------------------------------
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "color", "size", "grav", "additive")

    def __init__(self, x, y, vx, vy, life, color, size=4, grav=120, additive=False):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.life = life; self.max_life = life
        self.color = color
        self.size = size
        self.grav = grav
        # additive blending makes magical energy (fire/inferno/void) glow and
        # saturate instead of blending like an opaque physical hit. Set True by
        # the burst/ring/spark emitters for magic/aoe_magic/ultimate particles.
        self.additive = additive

    def update(self, dt):
        self.life -= dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.grav * dt
        self.vx *= 0.96
        return self.life > 0

    def draw(self, surf, ox, oy):
        a = max(0, self.life / self.max_life)
        sz = max(1, int(self.size * a))
        c = self.color
        # alpha by life (reused scratch surface)
        s = scratch(sz * 2, sz * 2)
        pygame.draw.circle(s, (*c, int(220 * a)), (sz, sz), sz)
        if self.additive:
            surf.blit(s, (self.x - ox - sz, self.y - oy - sz),
                      special_flags=pygame.BLEND_RGBA_ADD)
        else:
            surf.blit(s, (self.x - ox - sz, self.y - oy - sz))


class Particles:
    def __init__(self, cap=240, quality=1.0):
        self.list = []
        self.cap = cap
        # particle_quality (0.4..1.0): scales the count of each burst/ring/spark
        # so the user's Display setting actually does something. Set by the world
        # scene each frame from the player's settings.
        self.quality = max(0.1, min(1.0, float(quality)))

    def _qn(self, n):
        """Scale a particle count by the quality setting (always >= 1)."""
        return max(1, int(n * self.quality))

    def burst(self, x, y, color, n=10, speed=160, size=4, life=0.4, grav=120, additive=False):
        n = self._qn(n)
        for _ in range(n):
            ang = random.random() * math.tau
            sp = speed * (0.4 + random.random() * 0.8)
            self.list.append(Particle(x, y, math.cos(ang) * sp, math.sin(ang) * sp,
                                      life * (0.7 + random.random() * 0.6),
                                      color, size, grav, additive))
        self._trim()

    def ring(self, x, y, color, n=24, speed=300, size=5, life=0.5, additive=False):
        """An expanding ring of particles — great for shockwaves/impacts."""
        n = self._qn(n)
        for i in range(n):
            ang = i / n * math.tau
            sp = speed * (0.9 + random.random() * 0.2)
            self.list.append(Particle(x, y, math.cos(ang) * sp, math.sin(ang) * sp,
                                      life, color, size, 0, additive))
        self._trim()

    def spark(self, x, y, color, n=8, speed=260, size=4, life=0.3, additive=False):
        """Streaky sparks for melee hits — biased outward with a little spread."""
        n = self._qn(n)
        for _ in range(n):
            ang = random.random() * math.tau
            sp = speed * (0.6 + random.random() * 0.8)
            self.list.append(Particle(x, y, math.cos(ang) * sp, math.sin(ang) * sp,
                                      life, color, size, 60, additive))
        self._trim()

    def _trim(self):
        if len(self.list) > self.cap:
            self.list = self.list[-self.cap:]

    def update(self, dt):
        self.list = [p for p in self.list if p.update(dt)]

    def draw(self, surf, ox, oy):
        for p in self.list:
            p.draw(surf, ox, oy)

    def beam(self, x1, y1, x2, y2, color):
        """A bright beam line + a sparkle at the endpoint — for the beam skill.
        Adds a few streaky sparks along the line so the beam reads as an energy
        lance, not a flat line. (Pixel-art: a thick line, no AA.)"""
        n = self._qn(14)
        for _ in range(n):
            t = random.random()
            cx = x1 + (x2 - x1) * t
            cy = y1 + (y2 - y1) * t
            ang = random.random() * math.tau
            sp = 120 * (0.5 + random.random())
            self.list.append(Particle(cx, cy, math.cos(ang) * sp, math.sin(ang) * sp,
                                      0.3, color, 4, 40))
        # a couple of bright sparks at the endpoint
        for _ in range(self._qn(8)):
            ang = random.random() * math.tau
            sp = 200 * (0.5 + random.random())
            self.list.append(Particle(x2, y2, math.cos(ang) * sp, math.sin(ang) * sp,
                                      0.35, color, 5, 50))
        self._trim()


# ---------------------------------------------------------------------------
# Projectiles
# ---------------------------------------------------------------------------
class Projectile:
    __slots__ = ("x", "y", "vx", "vy", "life", "radius", "color", "element",
                 "source", "power", "is_crit", "pierce", "hit_set", "kind")

    def __init__(self, x, y, vx, vy, life, radius, color, element, source,
                 power, is_crit=False, pierce=False, kind="enemy"):
        self.x = x; self.y = y
        self.vx = vx; self.vy = vy
        self.life = life
        self.radius = radius
        self.color = color
        self.element = element
        self.source = source
        self.power = power
        self.is_crit = is_crit
        self.pierce = pierce
        self.hit_set = set()
        self.kind = kind  # "enemy" projectile or "hero" projectile

    def update(self, dt, obstacles):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        # collide with obstacles -> die
        r = pygame.Rect(self.x - self.radius, self.y - self.radius,
                        self.radius * 2, self.radius * 2)
        for o in obstacles:
            if r.colliderect(o):
                return False
        return self.life > 0

    def draw(self, surf, ox, oy):
        x = int(self.x - ox)
        y = int(self.y - oy)
        # glow (reused scratch surface)
        sz = self.radius * 4
        g = scratch(sz, sz)
        c = self.radius * 2
        pygame.draw.circle(g, (*self.color, 60), (c, c), c)
        pygame.draw.circle(g, (*self.color, 200), (c, c), self.radius)
        surf.blit(g, (x - c, y - c))


# ---------------------------------------------------------------------------
# Floating combat text
# ---------------------------------------------------------------------------
class FloatText:
    __slots__ = ("x", "y", "text", "color", "life", "max_life", "vy", "size")

    def __init__(self, x, y, text, color, size=22, life=0.8):
        self.x = x; self.y = y
        self.text = text
        self.color = color
        self.life = life; self.max_life = life
        self.vy = -60
        self.size = size

    def update(self, dt):
        self.life -= dt
        self.y += self.vy * dt
        self.vy += 40 * dt
        return self.life > 0


# ---------------------------------------------------------------------------
# Weapon mapping for the active hero's attack style
# ---------------------------------------------------------------------------
WEAPON_STYLE = {
    "sword":  "melee",
    "dagger": "melee_fast",
    "bow":    "ranged",
    "staff":  "ranged",
    "orb":    "ranged",
    "shield": "melee",
    "axe":    "melee",
    "spear":  "melee",
    "gun":    "ranged",
    "fists":  "melee",
    "scythe": "melee",
    "whip":   "melee",
    "none":   "melee",
}


# ---------------------------------------------------------------------------
# Signature passive handlers (C6) — dict-lookup dispatch, NOT if/elif chains.
# Each hook point has its own dict mapping kind -> handler, so only the
# relevant handler runs at that point. A handler may return a sentinel
# ("revive") to short-circuit the caller (like the perfect-dodge sentinel).
# The signature is ADDITIONAL to the shared base passive — these run in
# addition to the lifesteal/thorns/shield_when_low/etc. handlers in take_damage
# / effective_atk / move_speed / update, not instead of them.
# ---------------------------------------------------------------------------

def _sig_revive_once(wc):
    """revive_once: on a lethal blow, revive at val fraction of max HP once.
    Returns "revive" so the caller fires the revive VFX instead of _on_hero_down.
    _revive_used is reset in WorldScene._build_party per combat."""
    if wc._revive_used:
        return None
    sig = wc.hero.signature
    if not sig or sig.get("kind") != "revive_once":
        return None
    wc._revive_used = True
    wc.hero.hp = int(wc.hero.max_hp * sig.get("val", 0.4))
    wc.alive = True
    wc.invuln_t = 1.0
    return "revive"

def _sig_shield_on_hit(wc, dmg):
    """shield_on_hit: gain a small shield when damaged (after the hit lands).
    The shield buffers the NEXT hit (checked at the top of take_damage), so a
    reactive ward protects against subsequent hits, not the triggering one."""
    sig = wc.hero.signature
    if not sig or sig.get("kind") != "shield_on_hit":
        return
    wc._shield_hp = max(wc._shield_hp, int(wc.hero.max_hp * sig.get("val", 0.15)))

def _sig_low_hp_frenzy_atk(wc, a):
    """low_hp_frenzy ATK: +val ATK below 30% HP (additive on the bonus term,
    stacking with adrenaline/dodge-buff/resonance rather than multiplying)."""
    if wc.hero.hp < wc.hero.max_hp * 0.3:
        sig = wc.hero.signature
        return int(a * (1 + sig.get("val", 0.25)))
    return a

def _sig_stacking_atk_atk(wc, a):
    """stacking_atk ATK: +val ATK per kill in the current streak. Decays out of
    combat (see _sig_stacking_atk_update). Additive on the bonus term."""
    if wc._kill_stack > 0:
        sig = wc.hero.signature
        return int(a * (1 + wc._kill_stack * sig.get("val", 0.05)))
    return a

def _sig_low_hp_frenzy_spd(wc, s):
    """low_hp_frenzy SPD: +20% move speed below 30% HP (a fixed +20%, not the
    val, so the speed bonus stays modest even at high val)."""
    if wc.hero.hp < wc.hero.max_hp * 0.3:
        return s * 1.2
    return s

def _sig_stacking_atk_update(wc, dt):
    """stacking_atk: out-of-combat decay — lose one stack every 3s idle so a
    stale streak doesn't persist forever. _kill_stack_t accumulates dt; when it
    crosses 3s, drop one stack and reset the timer. _last_combat_t is reset on
    every combat action, so 'out of combat' = _last_combat_t >= 3.0; while in
    combat the timer is reset so no decay happens mid-fight."""
    if wc._kill_stack <= 0:
        return
    # only decay when out of combat (the _last_combat_t gate)
    if wc._last_combat_t < 3.0:
        wc._kill_stack_t = 0.0
        return
    wc._kill_stack_t += dt
    if wc._kill_stack_t >= 3.0:
        wc._kill_stack = max(0, wc._kill_stack - 1)
        wc._kill_stack_t = 0.0

# Dispatch dicts per hook point (kind -> handler). Only the kind(s) relevant
# to each hook point appear, so an if/elif chain over 5 kinds is replaced by a
# single dict lookup at each point.
_SIG_ON_DEATH = {"revive_once": _sig_revive_once}
_SIG_AFTER_DAMAGE = {"shield_on_hit": _sig_shield_on_hit}
_SIG_ATK_MOD = {
    "low_hp_frenzy": _sig_low_hp_frenzy_atk,
    "stacking_atk": _sig_stacking_atk_atk,
}
_SIG_SPD_MOD = {"low_hp_frenzy": _sig_low_hp_frenzy_spd}
_SIG_UPDATE = {"stacking_atk": _sig_stacking_atk_update}


# ---------------------------------------------------------------------------
# WorldCharacter - a hero in the open world (real-time)
# ---------------------------------------------------------------------------
class WorldCharacter:
    def __init__(self, hero, x, y):
        self.hero = hero
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.facing = 1  # 1 right, -1 left
        self.r = 20  # collision radius
        self.alive = True

        # movement
        self.max_speed = 230.0
        self.accel = 2400.0
        self.friction = 1800.0

        # dash
        self.dash_cd = 0.0
        self.dash_t = 0.0
        self.iframes = 0.0
        self.dash_dir = (0, 0)

        # combat
        self.atk_cd = 0.0
        self.atk_anim = 0.0
        self.skill_cd = [0.0, 0.0, 0.0]   # Q/W/E cooldowns (3 LoL-style skills)
        self.skill_cd_max = [0.0, 0.0, 0.0]  # max cooldown (for HUD sweep)
        self.ult_cd = 0.0
        self.invuln_t = 0.0          # brief post-hit invuln
        self.hit_flash = 0.0
        self.kb_x = 0.0
        self.kb_y = 0.0
        # passive runtime state (e.g. shield-when-low cooldown)
        self._shield_cd = 0.0
        self._shield_hp = 0.0
        self._last_combat_t = 9.0    # time since last combat action (for regen);
        # start "out of combat" (>= 1.5s) so a fresh hero regens at the full
        # rate immediately on map enter, not the 0.5x in-combat rate for the
        # first 1.5s (the "mana doesn't increase" feel — the v1 0.0 start made
        # the first 1.5s feel stalled even with no enemies).
        # signature passive runtime state (C6). _revive_used is reset in
        # WorldScene._build_party per combat (NOT here) to avoid the init-order
        # trap — _build_party runs after the wc is fully constructed so the
        # reset can't be clobbered by a later field default. _kill_stack /
        # _kill_stack_t track the stacking_atk kill streak + its out-of-combat
        # decay (reset to 0 here since a fresh wc starts with no kills).
        self._revive_used = False
        self._kill_stack = 0
        self._kill_stack_t = 0.0
        # perfect-dash: a brief window after a dash where passing through an
        # enemy attack grants a "perfect dodge" (slow-mo + a damage buff). The
        # window opens when the dash ends and counts down.
        self._perfect_dodge_t = 0.0
        self._dmg_buff_t = 0.0        # 1.5x damage buff after a perfect dodge
        # elemental resonance bonuses (set by WorldScene._compute_resonances via
        # apply_resonances). Zero when no resonance of that kind is active. Kept
        # on the WorldCharacter (not the Hero) so swapping the party updates them
        # without rebuilding hero instances. Additive with the matching passive.
        self._res_atk_pct = 0.0
        self._res_heal_amp = 0.0
        self._res_move_speed = 0.0
        self._res_energy_regen = 0.0
        self._res_crit_dmg = 0.0
        # click-to-move target (LoL-style RMB): when set, the hero auto-walks
        # toward this point. Cleared on WASD input, reaching the target, or a
        # combat action. None = no auto-move target.
        self.move_target = None        # (x, y) or None
        self.move_target_t = 0.0       # age of the current move_target (for reticle fade)
        self._last_mt_dist = 0.0       # last distance to target (stall detection)
        self._mt_stall_t = 0.0         # time the auto-walk has stalled
        # auto-attack target (LoL-style RMB-on-enemy, Task B3): when set, the hero
        # continuously auto-attacks this enemy at the AA cd while in range, or
        # walks toward it when out of range. Cleared on RMB-ground, skill cast,
        # party swap, or a map transition. None = no AA target. A WorldEnemy ref.
        self.aa_target = None

        # animation
        self.walk_t = 0.0
        self.moving = False
        self.atk_swing = 0.0        # 0..1 attack swing progress
        self.idle_t = 0.0           # idle breathing phase
        self.scale_x = 1.0          # squash/stretch (x)
        self.scale_y = 1.0          # squash/stretch (y)
        self.lunge = 0.0            # attack forward lunge offset

        # sprite (cached at a fixed display size)
        self.sprite_size = 96
        self._sprite = None
        self._sprite_face = 0
        self._load_sprite()

    def _load_sprite(self):
        try:
            self._sprite = load_char_sprite(self.hero.id, self.sprite_size)
        except Exception:
            self._sprite = None
        self._sprite_face = self.facing

    @property
    def element(self):
        return self.hero.element

    def skill_list(self):
        """The three skills mapped to Q/W/E (skip basic_attack)."""
        return D.hero_abilities(self.hero.def_dict)

    def can_skill(self, idx):
        sk = self.skill_list()
        if idx >= len(sk) or sk[idx] is None:
            return False
        sid = sk[idx]
        return self.hero.can_use_skill(sid) and self.skill_cd[idx] <= 0

    def can_ultimate(self):
        return self.hero.can_ultimate() and self.ult_cd <= 0

    def spend_skill(self, idx):
        sk = self.skill_list()
        sid = sk[idx]
        cost = self.hero.skill_energy_cost(sid)
        self.hero.energy -= cost
        # cooldown scales with the skill's cost tier (heavier skills cool slower)
        cd = 0.6 + (D.SKILLS_DB[sid].get("cost", 2)) * 0.18
        self.skill_cd[idx] = cd
        self.skill_cd_max[idx] = cd

    def spend_ultimate(self):
        self.hero.energy = 0
        # ult cooldown scales with the ult's cost tier so heavier ults (e.g.
        # death_coil cost 9) cool slightly longer than light ones (cost 8) —
        # this gives the per-ult "cost" field in the data sheet real meaning,
        # since every ult otherwise costs the full energy bar + a flat cd.
        self.ult_cd = 1.0 + D.SKILLS_DB[self.hero.ultimate].get("cost", 8) * 0.05

    def take_damage(self, amount, src_x=0, src_y=0, is_melee=False):
        """Apply incoming damage to this hero. Always returns a 2-tuple
        (dealt, reflected) for a normal hit, or (0, 0) when negated by
        i-frames/invuln/shield. A perfect dodge returns the sentinel
        "perfect_dodge" so the caller can fire the dodge VFX + buff. A
        revive_once signature returns "revive" so the caller fires the revive
        VFX instead of _on_hero_down."""
        if self.iframes > 0 or self.invuln_t > 0 or not self.alive:
            return 0, 0
        # perfect-dodge: if a dash just ended (the perfect-dodge window is open),
        # an incoming attack is negated and the dodge is rewarded. Returns a
        # sentinel so the caller can fire the perfect-dodge VFX + buff.
        if self._perfect_dodge_t > 0:
            self._perfect_dodge_t = 0
            self._dmg_buff_t = 2.0   # 1.5x damage buff for 2s
            self.invuln_t = 0.2
            return "perfect_dodge"
        # defense
        dmg = max(1, int(amount - self.hero.defn * 0.5))
        # shield-when-low passive: absorb from a temporary shield buffer
        if self._shield_hp > 0:
            absorbed = min(self._shield_hp, dmg)
            self._shield_hp -= absorbed
            dmg -= absorbed
            if dmg <= 0:
                self.hit_flash = 0.15
                self.invuln_t = 0.2
                return 0, 0
        self.hero.hp -= dmg
        self.hit_flash = 0.25
        self.invuln_t = 0.4
        # knockback
        dx = self.x - src_x
        dy = self.y - src_y
        d = math.hypot(dx, dy) or 1
        self.kb_x = dx / d * 260
        self.kb_y = dy / d * 260
        # thorns passive: reflect a fraction of melee damage back to the source
        reflected = 0
        if is_melee and self.hero.passive and self.hero.passive.get("kind") == "thorns":
            reflected = max(1, int(dmg * self.hero.passive.get("val", 0.2)))
        # shield-when-low passive: gain a shield the first time HP drops low
        if (self.hero.passive and self.hero.passive.get("kind") == "shield_when_low"
                and self._shield_cd <= 0 and self.hero.hp < self.hero.max_hp * 0.3):
            self._shield_hp = int(self.hero.max_hp * 0.25)
            self._shield_cd = 12.0
        # signature passive: shield_on_hit (dict-lookup dispatch — gain a small
        # shield when damaged, buffering the next hit)
        _handler = _SIG_AFTER_DAMAGE.get(self._signature_kind)
        if _handler:
            _handler(self, dmg)
        # death + signature: revive_once (dict-lookup dispatch — on a lethal
        # blow, revive at val HP once per combat; returns "revive" so the caller
        # fires the revive VFX instead of _on_hero_down)
        if self.hero.hp <= 0:
            _handler = _SIG_ON_DEATH.get(self._signature_kind)
            if _handler:
                result = _handler(self)
                if result == "revive":
                    return "revive"
            self.hero.hp = 0
            self.alive = False
        return dmg, reflected

    @property
    def _signature_kind(self):
        """The hero's signature passive kind (C6), or None. The signature is
        ADDITIONAL to the shared base passive — handlers at each hook point
        dispatch on this via the _SIG_* dicts above (dict-lookup, not if/elif)."""
        sig = getattr(self.hero, "signature", None)
        return sig.get("kind") if sig else None

    @property
    def passive(self):
        return self.hero.passive

    def effective_atk(self):
        """ATK with the adrenaline passive + the perfect-dodge damage buff +
        the fire elemental resonance (+atk_pct when 2+ fire heroes in party)
        + the signature ATK modifiers (low_hp_frenzy / stacking_atk)."""
        a = self.hero.atk
        if self.hero.passive and self.hero.passive.get("kind") == "adrenaline":
            if self.hero.hp < self.hero.max_hp * 0.35:
                a = int(a * (1 + self.hero.passive.get("val", 0.3)))
        # perfect-dodge reward: a 1.5x damage buff for 2s after a perfect dodge
        if self._dmg_buff_t > 0:
            a = int(a * 1.5)
        # elemental resonance (fire -> atk_pct). Applied as a flat additive on
        # the base ATK so it stacks additively with adrenaline/dodge-buff rather
        # than multiplicatively (those are situational; resonance is always-on).
        if self._res_atk_pct:
            a = int(a * (1 + self._res_atk_pct))
        # signature ATK modifier (dict-lookup dispatch — low_hp_frenzy below 30%
        # HP, or stacking_atk per kill). Additive on the bonus term so it stacks
        # with adrenaline/dodge-buff/resonance rather than double-multiplying.
        _sig_atk = _SIG_ATK_MOD.get(self._signature_kind)
        if _sig_atk:
            a = _sig_atk(self, a)
        return a

    @property
    def move_speed(self):
        """Max speed with the swift passive + the wind elemental resonance +
        the signature SPD modifier (low_hp_frenzy)."""
        s = self.max_speed
        if self.hero.passive and self.hero.passive.get("kind") == "swift":
            s *= (1 + self.hero.passive.get("val", 0.15))
        # elemental resonance (wind -> move_speed). Additive with the swift
        # passive: a swift hero in a 2-wind party gets +(0.15 + 0.10) = +25%.
        if self._res_move_speed:
            s *= (1 + self._res_move_speed)
        # signature SPD modifier (dict-lookup dispatch — low_hp_frenzy +20% below
        # 30% HP). Additive with the swift passive + wind resonance.
        _sig_spd = _SIG_SPD_MOD.get(self._signature_kind)
        if _sig_spd:
            s = _sig_spd(self, s)
        return s

    def heal(self, amount):
        """Heal with the water elemental resonance (+heal_amp when 2+ water
        heroes in party). Additive with the p_heal_amp passive: the resonance
        bonus and the passive bonus sum (both are flat fractions of the heal
        amount), so a Mercy hero in a 2-water party heals +45% instead of the
        resonance * passive double-dipping the base."""
        amt = amount
        amp = self._res_heal_amp
        if self.hero.passive and self.hero.passive.get("kind") == "heal_amp":
            amp += self.hero.passive.get("val", 0.25)
        if amp:
            amt = int(round(amt * (1 + amp)))
        self.hero.hp = min(self.hero.max_hp, self.hero.hp + amt)

    def add_energy(self, n):
        """Energy gain with the light elemental resonance (+energy_regen when
        2+ light heroes in party). Additive with the p_energy (Flow State)
        passive: the resonance bonus and the passive bonus sum on the gain, so
        a Flow-State hero in a 2-light party gains +65% energy instead of the
        resonance * passive double-dipping."""
        gain = n
        regen = self._res_energy_regen
        if self.hero.passive and self.hero.passive.get("kind") == "energy_gen":
            regen += self.hero.passive.get("val", 0.5)
        if regen:
            gain = int(round(gain * (1 + regen)))
        self.hero.energy = min(self.hero.max_energy, self.hero.energy + gain)

    def update(self, dt, input_dir, obstacles, want_dash):
        # knockback decays
        if abs(self.kb_x) > 1 or abs(self.kb_y) > 1:
            self.x += self.kb_x * dt
            self.y += self.kb_y * dt
            self.kb_x *= 0.8
            self.kb_y *= 0.8

        # LoL-style click-to-move: if the player isn't pressing WASD, the hero
        # auto-walks toward the RMB-set move_target until it reaches it. Any
        # WASD press overrides + clears the target (keyboard has priority).
        if input_dir[0] or input_dir[1]:
            self.move_target = None
        elif self.move_target is not None:
            tx, ty = self.move_target
            dx = tx - self.x
            dy = ty - self.y
            d = math.hypot(dx, dy)
            self.move_target_t += dt
            if d < 8:
                # reached the target — stop auto-moving
                self.move_target = None
            else:
                # stall detection: if the hero isn't getting closer (blocked by a
                # wall), clear the target after 0.3s so the reticle doesn't hang
                # on a wall forever (the "stray white circle" fix)
                if d >= self._last_mt_dist - 1:
                    self._mt_stall_t += dt
                    if self._mt_stall_t > 0.3:
                        self.move_target = None
                else:
                    self._mt_stall_t = 0
                self._last_mt_dist = d
                if self.move_target is not None:
                    # synthesize a normalized input toward the target so the
                    # existing accel/friction movement handles it (no special-case path)
                    input_dir = (dx / d, dy / d)
                    # face the direction we're walking
                    self.facing = 1 if dx > 0 else -1
                    self.moving = True

        # dash
        if want_dash and self.dash_cd <= 0 and (input_dir[0] or input_dir[1]):
            self.dash_t = 0.16
            self.iframes = 0.22
            self.dash_cd = 0.7
            n = math.hypot(*input_dir) or 1
            self.dash_dir = (input_dir[0] / n, input_dir[1] / n)
        if self.dash_t > 0:
            self.dash_t -= dt
            ds = 520
            self.x += self.dash_dir[0] * ds * dt
            self.y += self.dash_dir[1] * ds * dt
            self.moving = True
        else:
            # normal movement with accel + friction
            ix, iy = input_dir
            n = math.hypot(ix, iy)
            if n > 0:
                ix /= n; iy /= n
                self.vx += ix * self.accel * dt
                self.vy += iy * self.accel * dt
                if ix != 0:
                    self.facing = 1 if ix > 0 else -1
                self.moving = True
            else:
                # friction
                f = self.friction * dt
                if abs(self.vx) <= f: self.vx = 0
                else: self.vx -= f * (1 if self.vx > 0 else -1)
                if abs(self.vy) <= f: self.vy = 0
                else: self.vy -= f * (1 if self.vy > 0 else -1)
                self.moving = False
            # clamp speed (with swift passive)
            ms = self.move_speed
            sp = math.hypot(self.vx, self.vy)
            if sp > ms:
                self.vx = self.vx / sp * ms
                self.vy = self.vy / sp * ms
            self.x += self.vx * dt
            self.y += self.vy * dt

        # collide with obstacles (axis separated)
        self._collide(obstacles)

        # timers
        self.dash_cd = max(0, self.dash_cd - dt)
        self.iframes = max(0, self.iframes - dt)
        self.invuln_t = max(0, self.invuln_t - dt)
        self.atk_cd = max(0, self.atk_cd - dt)
        self.atk_anim = max(0, self.atk_anim - dt)
        self.hit_flash = max(0, self.hit_flash - dt)
        self._shield_cd = max(0, self._shield_cd - dt)
        # perfect-dodge window opens right after a dash ends (the i-frames are
        # the dodge itself; this is the "just-dodged" reward window) and counts
        # down. The damage buff from a successful perfect dodge decays too.
        # Track the previous dash state so we detect the dash->no-dash edge and
        # open the window exactly once when it ends.
        was_dashing = getattr(self, "_was_dashing", False)
        is_dashing = self.dash_t > 0 or self.iframes > 0
        if was_dashing and not is_dashing and self.dash_cd > 0.3:
            self._perfect_dodge_t = 0.15
        self._was_dashing = is_dashing
        self._perfect_dodge_t = max(0, self._perfect_dodge_t - dt)
        self._dmg_buff_t = max(0, self._dmg_buff_t - dt)
        for i in range(3):
            self.skill_cd[i] = max(0, self.skill_cd[i] - dt)
        self.ult_cd = max(0, self.ult_cd - dt)
        # out-of-combat regen passive
        self._last_combat_t += dt
        if (self.hero.passive and self.hero.passive.get("kind") == "regen"
                and self._last_combat_t > 2.0 and self.alive
                and self.hero.hp < self.hero.max_hp):
            self.hero.hp = min(self.hero.max_hp,
                               self.hero.hp + self.hero.max_hp * self.hero.passive.get("val", 0.02) * dt)
        # signature passive update handlers (dict-lookup dispatch). stacking_atk
        # decays by 1 every 3s out of combat so a stale streak doesn't persist.
        _sig_upd = _SIG_UPDATE.get(self._signature_kind)
        if _sig_upd:
            _sig_upd(self, dt)
        # passive energy regen: recover energy over time so a hero with low
        # energy can use skills again without landing a hit (the "skills don't
        # recover / mana doesn't increase" fix). Slower in combat. The light
        # elemental resonance (energy_regen) boosts the rate additively (a 2-light
        # party regens 15% faster); the p_energy (Flow State) passive only applies
        # to discrete energy gains from hits/skills, not to this passive trickle,
        # so there's no double-apply to guard here.
        if self.alive and self.hero.energy < self.hero.max_energy:
            rate = D.ENERGY_REGEN_PCT * (0.5 if self._last_combat_t < 1.5 else 1.0)
            rate *= (1 + self._res_energy_regen)
            self.hero.energy = min(self.hero.max_energy,
                                   self.hero.energy + self.hero.max_energy * rate * dt)

        # walk anim + idle breathing + squash/stretch
        if self.moving:
            self.walk_t += dt * 11
            # landing/squash from vertical bob of the walk cycle
            phase = math.sin(self.walk_t)
            self.scale_y = 1.0 + phase * 0.04
            self.scale_x = 1.0 - phase * 0.03
        else:
            self.walk_t *= 0.85
            self.idle_t += dt * 2.2
            # gentle breathing
            br = math.sin(self.idle_t) * 0.025
            self.scale_y = 1.0 + br
            self.scale_x = 1.0 - br * 0.6
        # attack lunge: forward lean that eases back (drive from atk_anim)
        if self.atk_anim > 0:
            # 0.2s swing -> lunge peaks early then returns
            t = 1 - (self.atk_anim / 0.2)
            self.lunge = math.sin(min(1, t) * math.pi) * 14 * self.facing
            self.scale_x = 1.0 + 0.10 * math.sin(min(1, t) * math.pi)
        else:
            self.lunge *= 0.8

        # reload sprite if facing changed (flip cache)
        if self._sprite is not None and self._sprite_face != self.facing:
            self._sprite = pygame.transform.flip(self._sprite, True, False)
            self._sprite_face = self.facing

    def _collide(self, obstacles):
        # X axis
        r = pygame.Rect(int(self.x - self.r), int(self.y - self.r), self.r * 2, self.r * 2)
        for o in obstacles:
            if r.colliderect(o):
                if self.vx > 0:
                    self.x = o.left - self.r
                elif self.vx < 0:
                    self.x = o.right + self.r
                self.vx = 0
                r.x = int(self.x - self.r)
        # Y axis
        r = pygame.Rect(int(self.x - self.r), int(self.y - self.r), self.r * 2, self.r * 2)
        for o in obstacles:
            if r.colliderect(o):
                if self.vy > 0:
                    self.y = o.top - self.r
                elif self.vy < 0:
                    self.y = o.bottom + self.r
                self.vy = 0
                r.y = int(self.y - self.r)
        # keep inside map bounds (caller passes border walls as obstacles too)

    def draw(self, surf, ox, oy, font):
        x = int(self.x - ox)
        y = int(self.y - oy)
        moving = self.moving
        # shadow (reused scratch surface) — squashes with the walk cycle
        sh_w = int(self.r * 2 * (0.9 + 0.1 * (1 + math.cos(self.walk_t)) if moving else 1))
        sh = scratch(max(20, sh_w), 10)
        pygame.draw.ellipse(sh, (0, 0, 0, 90), sh.get_rect())
        surf.blit(sh, (x - sh.get_width() // 2, y + self.r - 2))
        # a subtle element-tinted ground glow under the active-feet (cheap)
        if self.dash_t > 0 or self.atk_anim > 0:
            gw = self.r * 2
            g = scratch(gw, 14)
            ec = D.ELEMENT_COLORS.get(self.element, ((200, 200, 220),))[0]
            pygame.draw.ellipse(g, (*ec, 60), g.get_rect())
            surf.blit(g, (x - gw // 2, y + self.r - 6))
        # walk bob (vertical hop) + idle breathing offset
        if moving:
            bob = int(abs(math.sin(self.walk_t)) * 4)
        else:
            bob = int(math.sin(self.idle_t) * 1.5)
        # i-frame blink
        if self.iframes > 0 and int(self.iframes * 20) % 2 == 0:
            pass  # skip drawing this frame for a blink
        else:
            if self._sprite is not None:
                sw = self._sprite
                # squash/stretch via scale (only when it deviates enough to
                # matter; skip the transform entirely when near 1.0 to save
                # the rotozoom allocation)
                sx, sy = self.scale_x, self.scale_y
                needs_scale = abs(sx - 1.0) > 0.02 or abs(sy - 1.0) > 0.02
                # attack swing tilt
                tilt = 0.0
                if self.atk_anim > 0:
                    tilt = math.sin((1 - self.atk_anim / 0.2) * math.pi) * 0.28
                if needs_scale or tilt != 0.0:
                    angle = math.degrees(tilt * self.facing)
                    sw = pygame.transform.rotozoom(sw, angle, max(sx, sy))
                    if abs(sx - sy) > 0.02:
                        # apply non-uniform squash by scaling the already-rotated
                        # sprite along x (cheap smoothscale on a small surface)
                        w0, h0 = sw.get_size()
                        sw = pygame.transform.smoothscale(sw, (max(2, int(w0 * sx / max(sx, sy))),
                                                              max(2, int(h0 * sy / max(sx, sy)))))
                # lunge shifts the sprite horizontally toward facing
                lx = int(self.lunge)
                rect = sw.get_rect(midbottom=(x + lx, y + self.r + 6 + bob))
                surf.blit(sw, rect)
            else:
                pygame.draw.circle(surf, (200, 200, 220), (x, y), self.r)
        # hit flash overlay
        if self.hit_flash > 0:
            f = scratch(self.r * 2, self.r * 2)
            pygame.draw.circle(f, (255, 80, 80, int(180 * self.hit_flash / 0.25)), (self.r, self.r), self.r)
            surf.blit(f, (x - self.r, y - self.r))
        # dash trail glow
        if self.dash_t > 0:
            r2 = self.r * 2
            for i in range(3):
                tx = x - int(self.dash_dir[0] * i * 10)
                ty = y - int(self.dash_dir[1] * i * 10)
                a = 60 - i * 18
                s = scratch(r2, r2)
                pygame.draw.circle(s, (255, 255, 255, a), (self.r, self.r), self.r)
                surf.blit(s, (tx - self.r, ty - self.r))


# ---------------------------------------------------------------------------
# WorldEnemy
# ---------------------------------------------------------------------------
class WorldEnemy:
    def __init__(self, enemy_id, x, y, level, is_boss=False):
        from entities import Enemy
        self.enemy = Enemy(enemy_id, level)
        self.id = enemy_id
        d = D.ENEMIES_DB[enemy_id]
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.r = 26 if not is_boss else 40
        self.facing = 1
        self.alive = True
        self.is_boss = is_boss

        # AI state
        self.state = "idle"   # idle, roam, aggro, attack, hurt, telegraph
        self.state_t = 0.0
        self.atk_cd = 1.0
        self.roam_target = (x, y)
        self.roam_t = 0.0
        self.aggro_range = (240 + d.get("spd", 10) * 10) if not is_boss else 460
        self.atk_range = 50 if not is_boss else 70
        # world speed is derived from the data-sheet spd so stat differences are
        # felt (a slime spd=6 waddles, a harpy spd=18 darts) — otherwise every
        # enemy moves at the same pace regardless of its stats.
        if is_boss:
            self.speed = 70 + level
        else:
            self.speed = 55 + d.get("spd", 10) * 5 + level * 2
        self.telegraph_t = 0.0
        self.hit_flash = 0.0
        self.kb_x = 0.0
        self.kb_y = 0.0
        self.invuln_t = 0.0
        self.ult_used = False
        # elemental reaction state: the last element that hit this enemy + a
        # window timer; a hit by a different element within the window triggers a
        # reaction (see world_scene._on_enemy_hit + data.REACTIONS)
        self._last_element_hit = None
        self._element_hit_t = 0.0
        # reaction stun: while > 0 the enemy skips its AI (frozen by a Freeze
        # reaction); decays each update
        self._react_stun = 0.0
        # HSR-style toughness break: a 2s recovery window after the toughness
        # bar shatters, after which recover_toughness() resets the bar (see
        # update). _broke_flag is set on the break hit so the scene can fire a
        # bonus-damage window + particle burst (see _on_enemy_event).
        self._broke_flag = False
        self._broken_recover_t = 0.0
        # boss phase state: which phase the boss is in (1..3) + the pattern it's
        # currently telegraphing (None | "charge" | "slam") + a telegraph timer
        # + the saved target position for the charge. See data.BOSS_PATTERNS.
        self._boss_phase = 1
        self._boss_pattern = None
        self._boss_pat_t = 0.0
        self._boss_charge_target = (0, 0)
        # secondary skill cooldown: non-boss enemies with a secondary skill
        # (fire_bolt/dark_curse/etc.) cast it on this slower timer so the
        # data sheet's per-enemy skill list is actually used in the open world.
        self.atk_cd2 = 0.0
        # animation
        self.walk_t = 0.0
        self.idle_t = random.random() * math.tau
        self.moving = False
        self.scale_y = 1.0

        # sprite
        self.sprite_size = 96 if not is_boss else 180
        try:
            self._sprite = load_enemy_sprite(enemy_id, self.sprite_size)
        except Exception:
            self._sprite = None
        self._sprite_face = 1

        # weapon style for ranged (goblin is a short-range kiter that throws
        # fire_bolt — distinct from the plain melee chaser archetype)
        self.ranged = self.id in ("bat", "imp", "harpy", "wraith", "hydra", "frosttitan", "goblin")

    @property
    def element(self):
        return self.enemy.element

    def take_damage(self, amount, src_x=0, src_y=0, is_crit=False, on_attack=None):
        if self.invuln_t > 0 or not self.alive:
            return 0
        # element weakness handled by caller; here pure amount
        # HSR-style toughness break: a broken target takes +50% damage from all
        # sources while its bar is down (TOUGHNESS_BREAK_MULT). Applied to the
        # raw amount before clamping so weakness/reaction bonuses (already
        # folded in by the caller) stack multiplicatively with the break
        # multiplier — they don't compound absurdly because each is a flat
        # factor on the pre-broken base, not a chain of +50%s.
        if self.enemy.broken:
            amount = int(amount * D.TOUGHNESS_BREAK_MULT)
        dmg = max(1, int(amount))
        self.enemy.hp -= dmg
        self.hit_flash = 0.2
        self.state = "hurt"
        self.state_t = 0.2
        # HSR-style toughness: shave the toughness bar and, if this hit breaks
        # it, freeze the enemy briefly (reuses the existing _react_stun path the
        # scene already reads). The break is flagged so the scene can fire a
        # bonus-damage window + particle burst (see _on_enemy_event).
        if self.enemy.has_toughness() and not self.enemy.broken:
            broke = self.enemy.damage_toughness(dmg)
            if broke:
                self._react_stun = max(self._react_stun, 1.2)
                self._broke_flag = True
                # break burst: a one-time chunk of max_hp damage so shattering
                # the bar is a real tactical milestone (TOUGHNESS_BREAK_DAMAGE).
                # Gated to bosses only — non-boss toughness enemies are too
                # squishy to absorb a 15%-max-hp nuke without being one-shot.
                if self.is_boss:
                    burst = int(self.enemy.max_hp * D.TOUGHNESS_BREAK_DAMAGE)
                    if burst > 0:
                        self.enemy.hp -= burst
                        if on_attack:
                            on_attack("boss_break", self)
                    # start the recovery window: after 2s the toughness bar
                    # refills (HSR-accurate — the break is consumed, then the
                    # bar comes back full). Timed so the +50% window + the
                    # stun overlap a meaningful damage window.
                    self._broken_recover_t = 2.0
        dx = self.x - src_x
        dy = self.y - src_y
        d = math.hypot(dx, dy) or 1
        kb = 180 if not self.is_boss else 80
        self.kb_x = dx / d * kb
        self.kb_y = dy / d * kb
        if self.enemy.hp <= 0:
            self.enemy.hp = 0
            self.alive = False
        return dmg

    def update(self, dt, target, obstacles, projectiles, particles, on_attack):
        if not self.alive:
            return
        # knockback
        if abs(self.kb_x) > 1 or abs(self.kb_y) > 1:
            self.x += self.kb_x * dt
            self.y += self.kb_y * dt
            self.kb_x *= 0.8
            self.kb_y *= 0.8
        self.hit_flash = max(0, self.hit_flash - dt)
        self.invuln_t = max(0, self.invuln_t - dt)
        self.atk_cd = max(0, self.atk_cd - dt)
        self.atk_cd2 = max(0, self.atk_cd2 - dt)
        self.state_t -= dt
        # reaction timers: the element-hit window counts down; a freeze stun
        # skips the enemy's AI while it lasts
        self._element_hit_t = max(0, self._element_hit_t - dt)
        self._react_stun = max(0, self._react_stun - dt)
        # HSR toughness break recovery: count down the 2s window set on break;
        # when it elapses + the bar is still broken, refill it so the fight
        # reopens (the +50% break window ends). Mirrors recover_toughness()
        # end-of-round semantics but in real time (see take_damage).
        if self._broken_recover_t > 0:
            self._broken_recover_t = max(0, self._broken_recover_t - dt)
            if self._broken_recover_t == 0 and self.enemy.broken:
                self.enemy.recover_toughness()
                self._broke_flag = False

        # boss ultimate below 50%
        if self.is_boss and not self.ult_used and self.enemy.hp < self.enemy.max_hp * 0.5:
            self.ult_used = True
            on_attack("boss_ult", self)

        # boss phase progression: 66% and 33% HP thresholds advance the phase,
        # unlocking new telegraphed attack patterns (see data.BOSS_PATTERNS).
        if self.is_boss:
            frac = self.enemy.hp / max(1, self.enemy.max_hp)
            new_phase = 1 if frac > 0.66 else (2 if frac > 0.33 else 3)
            if new_phase > self._boss_phase:
                self._boss_phase = new_phase
                # entering a new phase: brief telegraph + a warning sound so the
                # player feels the fight escalate
                on_attack("boss_phase", self)

        # frozen by a Freeze reaction: skip the AI this frame (the enemy is
        # encased in ice and can't act; still takes damage / knockback)
        if self._react_stun > 0:
            return

        dist = math.hypot(target.x - self.x, target.y - self.y) if target else 9999

        if self.state == "hurt":
            if self.state_t <= 0:
                self.state = "aggro"
        elif self.state == "idle":
            # wander
            self.roam_t -= dt
            if self.roam_t <= 0:
                self.roam_t = 1.5 + random.random() * 2
                self.roam_target = (self.x + random.uniform(-120, 120),
                                    self.y + random.uniform(-120, 120))
            if dist < self.aggro_range:
                self.state = "aggro"
        elif self.state == "aggro":
            if dist > self.aggro_range * 1.4:
                self.state = "idle"
                self.moving = False
                return
            # slime: a slow waddler that telegraphed hop-lunges instead of a flat
            # chase+strike. It leaps in a predictable, dodgeable arc — the
            # textbook "kite the blob" starter enemy (distinct from a flat chaser).
            if self.id == "slime":
                self.hop_t = getattr(self, "hop_t", 0) - dt
                if self.hop_t <= 0 and dist < 240:
                    self.hop_t = 1.6
                    dx = target.x - self.x; dy = target.y - self.y
                    dd = math.hypot(dx, dy) or 1
                    self.x += dx / dd * 70
                    self.y += dy / dd * 70
                    self._collide(obstacles)
                    on_attack("enemy_strike", self)
                    if math.hypot(target.x - self.x, target.y - self.y) < self.atk_range + 20:
                        res = target.take_damage(self.enemy.atk * 1.2, self.x, self.y, is_melee=True)
                        if isinstance(res, tuple) and res[1] > 0:
                            self.take_damage(res[1], target.x, target.y)
                    self.atk_cd = 1.6
                    self.moving = False
                    return
            # bosses in phase 2+ weave special telegraphed patterns (charge /
            # slam) between their basic strikes, on their own cooldown. The
            # pattern telegraphs first, then resolves in the "pattern" state.
            # The trigger chance + pattern selection scale with the phase so the
            # fight visibly escalates (phase 3 favors the newly-unlocked slam).
            if (self.is_boss and self._boss_phase >= 2 and self._boss_pattern is None
                    and self.atk_cd <= 0 and self._boss_pat_t <= 0):
                patterns = D.boss_patterns(self.id, self._boss_phase)
                trigger_p = {1: 0.0, 2: 0.5, 3: 0.75}.get(self._boss_phase, 0.6)
                if patterns and random.random() < trigger_p:
                    if self._boss_phase >= 3 and len(patterns) > 1:
                        # phase 3: favor the newly-unlocked (last) pattern
                        pat = random.choice(patterns[-1:] + patterns[:-1])
                    else:
                        pat = random.choice(patterns)
                    self._boss_pattern = pat
                    self._boss_pat_t = 0.8 if pat == "charge" else 0.6
                    if pat == "charge" and target:
                        # lock the charge target at the player's current pos so
                        # the boss commits to the line (dodgeable by sidestepping)
                        self._boss_charge_target = (target.x, target.y)
                    on_attack("boss_warn", self)
                    self.moving = False
                    return
            # wolf: a fast stalker that pounces — a short windup then a long
            # lunge at atk*1.4 (a real predator archetype, distinct from the blob
            # and the skirmisher). Only when the basic attack is off cooldown.
            if self.id == "wolf" and dist < 200 and self.atk_cd <= 0:
                self.state = "telegraph"
                self.telegraph_t = 0.22
                self._pounce = True
            elif dist < self.atk_range and self.atk_cd <= 0 and not self.ranged:
                self.state = "telegraph"
                self.telegraph_t = 0.4
            elif self.ranged and self.atk_cd <= 0 and dist < 360:
                self.state = "telegraph"
                self.telegraph_t = 0.5
            else:
                # chase
                dx = target.x - self.x
                dy = target.y - self.y
                d = math.hypot(dx, dy) or 1
                # goblin kiter: back off when the hero closes in so it keeps its
                # distance and throws fire_bolt from range (a skirmisher that
                # feels distinct from a plain melee chaser).
                if self.id == "goblin" and dist < 150:
                    self.vx = -dx / d * self.speed
                    self.vy = -dy / d * self.speed
                else:
                    self.vx = dx / d * self.speed
                    self.vy = dy / d * self.speed
                self.x += self.vx * dt
                self.y += self.vy * dt
                self.facing = 1 if dx > 0 else -1
                self._collide(obstacles)
                self.moving = True
        elif self.state == "telegraph":
            # face target, hold still, then strike
            if target:
                self.facing = 1 if target.x > self.x else -1
            if self.telegraph_t <= 0:
                self._do_attack(target, projectiles, particles, on_attack)
                # phase 3 bosses attack faster (the fight escalates)
                self.atk_cd = (1.4 if not self.is_boss
                               else (2.2 if self._boss_phase < 3 else 1.5))
                self.state = "aggro"

        # active boss pattern: telegraph then resolve. The charge is a sustained
        # multi-frame dash along the telegraphed line (so sidestepping is the real
        # dodge), not a single-frame hop — the boss travels until it reaches (or
        # overshoots) the locked target, then resolves the hit on overlap.
        if self._boss_pattern is not None:
            self._boss_pat_t -= dt
            if self._boss_pattern == "charge":
                if self._boss_pat_t <= 0:
                    tx, ty = self._boss_charge_target
                    dx, dy = tx - self.x, ty - self.y
                    d = math.hypot(dx, dy)
                    if d is None or d < 12:
                        # reached the target -> resolve the charge hit
                        on_attack("boss_charge", self)
                        self._boss_pattern = None
                        self.atk_cd = 2.5
                        self.state = "aggro"
                    else:
                        # sustained dash toward the locked target (~300px/s);
                        # the scene's boss_charge handler damages on overlap.
                        step = min(d, self.speed * 3.0 * dt)
                        self.x += dx / d * step
                        self.y += dy / d * step
                        self.facing = 1 if dx > 0 else -1
                        self.moving = True
            elif self._boss_pattern == "slam":
                if self._boss_pat_t <= 0:
                    # resolve: an expanding burst at the boss's feet; damage in a
                    # radius is applied by _on_enemy_event("boss_slam", ...).
                    on_attack("boss_slam", self)
                    self._boss_pattern = None
                    self.atk_cd = 2.0
                    self.state = "aggro"

        # animation: walk bob while chasing, idle breathing otherwise
        if self.moving:
            self.walk_t += dt * 9
        else:
            self.walk_t = 0.0
            self.idle_t += dt * 2.0

        # flip sprite cache
        if self._sprite is not None and self._sprite_face != self.facing:
            self._sprite = pygame.transform.flip(self._sprite, True, False)
            self._sprite_face = self.facing

    def _do_attack(self, target, projectiles, particles, on_attack):
        # guard: the telegraph can outlive the target (it died / swapped to None);
        # abort the strike rather than dereferencing a None target.
        if target is None:
            return
        col = D.ELEMENT_COLORS.get(self.element, ((200, 200, 200),))[0]
        # wolf pounce: a long lunge toward the target then a heavy strike — a
        # real predator archetype (distinct from the blob and the skirmisher).
        if getattr(self, "_pounce", False):
            self._pounce = False
            dx = target.x - self.x; dy = target.y - self.y
            d = math.hypot(dx, dy) or 1
            self.x += dx / d * 90
            self.y += dy / d * 90
            on_attack("enemy_strike", self)
            if math.hypot(target.x - self.x, target.y - self.y) < self.atk_range + 24:
                res = target.take_damage(self.enemy.atk * 1.4, self.x, self.y, is_melee=True)
                if isinstance(res, tuple) and res[1] > 0:
                    self.take_damage(res[1], target.x, target.y)
            self.atk_cd = 1.8
            return
        # secondary skill: non-boss enemies with a skill list cast it on a
        # slower secondary cooldown so the data sheet's per-enemy skills
        # (fire_bolt/dark_curse/tidal_wave/frost_nova) are actually used in
        # the open world, not just by bosses.
        if (not self.is_boss and self.atk_cd2 <= 0
                and len(self.enemy.skills) > 1):
            sid = self.enemy.skills[-1]
            sk = D.SKILLS_DB.get(sid)
            if sk and sk.get("type") in ("magic", "aoe_magic", "debuff"):
                self._cast_skill(sid, sk, target, projectiles, on_attack)
                self.atk_cd2 = 3.0
                return
        if self.ranged:
            dx = target.x - self.x
            dy = target.y - self.y
            d = math.hypot(dx, dy) or 1
            # per-enemy ranged params so a harpy shoots fast/short (a quick
            # skirmisher) and a frosttitan shoots slow/long/heavy (a sniper),
            # instead of every ranged enemy sharing identical projectile stats.
            ranged_cfg = {
                "bat": (420, 1.6, 7, 260), "imp": (340, 1.8, 9, 300),
                "harpy": (480, 1.4, 6, 320), "wraith": (300, 2.2, 11, 280),
                "hydra": (260, 2.4, 12, 240), "frosttitan": (220, 2.8, 14, 200),
                "goblin": (300, 1.4, 8, 320),
            }
            sp, life, rad, _reach = ranged_cfg.get(self.id, (360, 2.0, 10, 360))
            p = Projectile(self.x, self.y, dx / d * sp, dy / d * sp,
                           life, rad, col, self.element, self,
                           self.enemy.atk, kind="enemy")
            projectiles.append(p)
            on_attack("enemy_shoot", self)
        else:
            # melee strike - damage if target in range
            on_attack("enemy_strike", self)
            if math.hypot(target.x - self.x, target.y - self.y) < self.atk_range + 20:
                res = target.take_damage(self.enemy.atk * 1.2, self.x, self.y, is_melee=True)
                # thorns passive reflects a fraction back to this attacker
                if isinstance(res, tuple) and res[1] > 0:
                    self.take_damage(res[1], target.x, target.y)

    def _cast_skill(self, sid, sk, target, projectiles, on_attack):
        """Fire a skill-typed projectile from an enemy's data-sheet skill list.
        magic -> a single fast bolt at sk power; aoe_magic -> a ring of 8
        projectiles; debuff -> a slow bolt (the scene applies the debuff on
        hit via the element/skill type)."""
        col = D.ELEMENT_COLORS.get(sk.get("element", self.element), ((200, 200, 200),))[0]
        if target is None:
            return
        dx = target.x - self.x; dy = target.y - self.y
        d = math.hypot(dx, dy) or 1
        power = int(self.enemy.atk * sk.get("power", 1.5))
        stype = sk.get("type")
        if stype == "magic":
            sp = 360
            projectiles.append(Projectile(self.x, self.y, dx / d * sp, dy / d * sp,
                                          2.0, 10, col, sk.get("element", self.element),
                                          self, power, kind="enemy"))
        elif stype == "aoe_magic":
            # a ring of 8 projectiles spreading outward (an AoE volley)
            for i in range(8):
                ang = i / 8 * math.tau
                sp = 260
                projectiles.append(Projectile(self.x, self.y,
                                              math.cos(ang) * sp, math.sin(ang) * sp,
                                              1.6, 9, col, sk.get("element", self.element),
                                              self, power, kind="enemy"))
        elif stype == "debuff":
            # a slow bolt that applies a debuff on hit (poison/atk_down/etc.)
            sp = 220
            projectiles.append(Projectile(self.x, self.y, dx / d * sp, dy / d * sp,
                                          2.4, 11, col, sk.get("element", self.element),
                                          self, power, kind="enemy"))
        on_attack("enemy_shoot", self)

    def _collide(self, obstacles):
        r = pygame.Rect(int(self.x - self.r), int(self.y - self.r), self.r * 2, self.r * 2)
        for o in obstacles:
            if r.colliderect(o):
                if self.vx > 0:
                    self.x = o.left - self.r
                elif self.vx < 0:
                    self.x = o.right + self.r
                self.vx = 0
                r.x = int(self.x - self.r)
        r = pygame.Rect(int(self.x - self.r), int(self.y - self.r), self.r * 2, self.r * 2)
        for o in obstacles:
            if r.colliderect(o):
                if self.vy > 0:
                    self.y = o.top - self.r
                elif self.vy < 0:
                    self.y = o.bottom + self.r
                self.vy = 0
                r.y = int(self.y - self.r)

    def draw(self, surf, ox, oy, font):
        x = int(self.x - ox)
        y = int(self.y - oy)
        # bob: walk hop while moving, idle breathing while still
        if self.moving:
            bob = int(abs(math.sin(self.walk_t)) * 3)
        else:
            bob = int(math.sin(self.idle_t) * 1.5)
        # shadow (reused scratch surface) — shrinks slightly when airborne
        sh = scratch(self.r * 2, 12)
        pygame.draw.ellipse(sh, (0, 0, 0, max(50, 90 - bob * 8)), sh.get_rect())
        surf.blit(sh, (x - self.r, y + self.r - 4))
        # boss aura (a pulsing element-tinted glow around boss feet). At night
        # the aura expands + intensifies so the boss arena reads as a lit pool
        # (the hero's torch pool only covers the hero; the boss gets its own so
        # the arena reads as lit from within, not just dark). The night_level
        # (0..8) is set on the enemy by the scene each frame so the boss aura +
        # the hero torch + the vignette all share one quantization (no thrash).
        if self.is_boss:
            nl = max(0, min(8, int(getattr(self, "_night_level", 0))))
            # at night: +60% radius, +60% intensity (0.4..0.95 = night window)
            rad_mul = 1.0 + 0.6 * (nl / 8.0)
            int_mul = 1.0 + 0.6 * (nl / 8.0)
            gw = int(self.r * 3 * rad_mul)
            g = scratch(gw, gw)
            pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.005)
            ec = D.ELEMENT_COLORS.get(self.element, ((220, 60, 60),))[0]
            ring_w = int(18 * rad_mul)
            for rr in range(self.r + ring_w, self.r, -3):
                a = int(min(255, 50 * pulse * (1 - (rr - self.r) / max(1, ring_w)) * int_mul))
                pygame.draw.circle(g, (*ec, a), (gw // 2, gw // 2), rr)
            surf.blit(g, (x - gw // 2, y - gw // 2))
        # telegraph glow (a growing red ring that snaps to the strike)
        if self.state == "telegraph":
            gw = self.r * 3
            g = scratch(gw, gw)
            # ring grows as the telegraph counts down
            prog = 1 - (self.telegraph_t / 0.5)
            ring_r = int(self.r + 10 + prog * 18)
            a = int(160 * prog)
            pygame.draw.circle(g, (255, 70, 70, a), (gw // 2, gw // 2), ring_r, 4)
            # fill glow
            pygame.draw.circle(g, (255, 80, 80, a // 3), (gw // 2, gw // 2), self.r)
            surf.blit(g, (x - gw // 2, y - gw // 2))
        # boss pattern telegraphs: a red line for the charge (re-aimed along
        # the boss's current travel direction so it tracks the sustained dash,
        # not the stale locked target) and an expanding ring for the slam.
        if self.is_boss and self._boss_pattern is not None:
            if self._boss_pattern == "charge":
                # the line points from the boss to its charge target; while the
                # dash is in flight the boss moves along this line, so the line
                # always matches the actual strike path (no stale lie).
                tx, ty = self._boss_charge_target
                sx, sy = ox + int(tx), oy + int(ty)
                prog = 1 - (self._boss_pat_t / 0.8)
                a = int(120 + 100 * prog)
                # draw a thick line on a scratch surface for an alpha glow
                lw = 8 + int(4 * prog)
                pygame.draw.line(surf, (255, 60, 60), (x, y), (sx, sy), lw)
                pygame.draw.line(surf, (255, 200, 200), (x, y), (sx, sy), 2)
            elif self._boss_pattern == "slam":
                # an expanding ring at the boss's feet that grows to the slam
                # radius as the telegraph counts down — the player must dash out
                prog = 1 - (self._boss_pat_t / 0.6)
                ring_r = int(40 + prog * 120)
                a = int(160 * prog)
                pygame.draw.circle(surf, (255, 70, 70), (x, y), ring_r, 4)
                pygame.draw.circle(surf, (255, 80, 80, a // 3), (x, y), ring_r)
        # sprite (with bob) — flip handled in update; add a subtle squash on hit
        if self._sprite is not None:
            sw = self._sprite
            if self.hit_flash > 0:
                # brief stretch on hit for impact feedback
                k = self.hit_flash / 0.2
                sy = 1.0 + 0.12 * k
                sx = 1.0 - 0.08 * k
                sw = pygame.transform.smoothscale(sw, (max(2, int(sw.get_width() * sx)),
                                                       max(2, int(sw.get_height() * sy))))
            rect = sw.get_rect(midbottom=(x, y + self.r + 4 + bob))
            surf.blit(sw, rect)
        else:
            pygame.draw.circle(surf, (180, 80, 80), (x, y), self.r)
        # hit flash
        if self.hit_flash > 0:
            f = scratch(self.r * 2, self.r * 2)
            pygame.draw.circle(f, (255, 255, 255, int(180 * self.hit_flash / 0.2)), (self.r, self.r), self.r)
            surf.blit(f, (x - self.r, y - self.r))
        # boss tag with a crown
        if self.is_boss:
            tag = font.render("BOSS", True, (255, 80, 80))
            surf.blit(tag, (x - tag.get_width() // 2, y - self.r - 36))
            # little crown above the tag
            cy = y - self.r - 54
            pygame.draw.polygon(surf, (255, 200, 80),
                [(x - 14, cy + 8), (x - 14, cy - 4), (x - 7, cy + 2),
                 (x, cy - 8), (x + 7, cy + 2), (x + 14, cy - 4), (x + 14, cy + 8)])
            pygame.draw.polygon(surf, (120, 80, 30),
                [(x - 14, cy + 8), (x - 14, cy - 4), (x - 7, cy + 2),
                 (x, cy - 8), (x + 7, cy + 2), (x + 14, cy - 4), (x + 14, cy + 8)], 2)
        # enemy HP bar (a thin bar above the sprite) so damage is readable
        if self.alive and self.enemy.hp < self.enemy.max_hp:
            bw = self.r * 2
            bx = x - self.r
            by = y - self.r - 16
            frac = max(0, self.enemy.hp / max(1, self.enemy.max_hp))
            pygame.draw.rect(surf, (20, 20, 30), (bx, by, bw, 5), border_radius=2)
            if frac > 0:
                col = (220, 70, 80) if frac > 0.5 else ((255, 200, 80) if frac > 0.25 else (255, 120, 60))
                pygame.draw.rect(surf, col, (bx, by, int(bw * frac), 5), border_radius=2)
            # HSR-style toughness bar: a thin 4px white bar under the HP bar,
            # shown only after first hit (toughness < max) so an untouched enemy
            # doesn't carry visual clutter. When broken, the bar empties and a
            # flashing "BROKEN" tag tells the player the +50% window is open.
            if self.enemy.has_toughness() and self.enemy.toughness < self.enemy.max_toughness:
                tby = by + 6
                tf = max(0, self.enemy.toughness / max(1, self.enemy.max_toughness))
                pygame.draw.rect(surf, (20, 20, 30), (bx, tby, bw, 4), border_radius=2)
                if tf > 0 and not self.enemy.broken:
                    pygame.draw.rect(surf, (235, 235, 245),
                                     (bx, tby, int(bw * tf), 4), border_radius=2)
                if self.enemy.broken:
                    # cache the BROKEN text surface (rendered once, reused) so the
                    # per-frame font.render on every broken enemy is a dict lookup
                    global _BROKEN_TAG_SURF
                    if _BROKEN_TAG_SURF is None:
                        _BROKEN_TAG_SURF = font.render("BROKEN", True, (255, 200, 120))
                    tag = _BROKEN_TAG_SURF
                    # flash: blink ~6Hz so the tag reads as an active state, not a
                    # static label (skip every other ~83ms frame)
                    if (pygame.time.get_ticks() % 160) < 120:
                        surf.blit(tag, (x - tag.get_width() // 2, tby - 14))


# ---------------------------------------------------------------------------
# Summon ally + Trap (the new summon/beam/trap skill types — Task A3)
# ---------------------------------------------------------------------------
class SummonAlly:
    """A temporary ally spawned by a `summon` skill. Auto-attacks nearby enemies
    at a fixed cooldown for `dur` seconds, then despawns. NOT a party member — a
    separate entity so the 4-slot party is untouched. Water-summons heal the
    party instead of attacking (potency < 1.0 flags the heal role)."""
    __slots__ = ("x", "y", "element", "color", "atk", "dur", "potency",
                 "source", "atk_cd", "r", "t", "dur_max")

    def __init__(self, x, y, element, color, atk, dur, potency, source):
        self.x = float(x); self.y = float(y)
        self.element = element; self.color = color
        self.atk = atk; self.dur = dur; self.potency = potency
        self.source = source  # the WorldCharacter that summoned it
        self.atk_cd = 0.0
        self.r = 18
        self.t = 0.0
        self.dur_max = max(1.0, dur)  # for the timer-ring fraction (avoids /6 hardcode)

    def update(self, dt, enemies, particles, on_enemy_hit, party):
        self.t += dt
        self.dur -= dt
        self.atk_cd = max(0.0, self.atk_cd - dt)
        # water summon: heal the party over time instead of attacking
        if self.element == "water" and self.potency < 1.0:
            if self.atk_cd <= 0:
                self.atk_cd = 1.2
                for wc in party:
                    if wc and wc.alive:
                        wc.heal(int(self.atk * 0.4))
                particles.burst(self.x, self.y, (140, 240, 200),
                                n=8, speed=120, size=4, life=0.4, grav=-60)
            return self.dur > 0
        # fire/other summon: auto-attack the nearest enemy in range
        if self.atk_cd <= 0:
            best = None; best_d = 220
            for en in enemies:
                if not en.alive:
                    continue
                dd = math.hypot(en.x - self.x, en.y - self.y)
                if dd < best_d:
                    best_d = dd; best = en
            if best is not None:
                self.atk_cd = 0.5
                dmg = max(1, int(self.atk * 0.6))
                dealt = best.take_damage(dmg, self.x, self.y,
                                         on_attack=None)
                if dealt > 0 and on_enemy_hit is not None:
                    on_enemy_hit(best, self.source, dealt, False)
                particles.spark(self.x, self.y, self.color, n=6, speed=200, size=4, life=0.25)
        return self.dur > 0

    def draw(self, surf, ox, oy):
        x = int(self.x - ox); y = int(self.y - oy)
        if -40 < x < 1320 and -40 < y < 760:
            # a small element-tinted construct (pixel-art: solid fills, no AA)
            pygame.draw.circle(surf, self.color, (x, y), self.r)
            pygame.draw.circle(surf, (20, 20, 30), (x, y), self.r, 2)
            # a fading timer ring so the player sees the summon's remaining dur
            frac = max(0.0, min(1.0, self.dur / self.dur_max))
            if frac > 0:
                pygame.draw.arc(surf, (255, 255, 255),
                                (x - self.r - 4, y - self.r - 4,
                                 (self.r + 4) * 2, (self.r + 4) * 2),
                                0, frac * math.tau, 2)


class Trap:
    """A delayed ground hazard placed by a `trap` skill. Triggers (AoE damage +
    a particle burst) when an enemy steps within `radius`, then despawns. Also
    despawns after `dur` seconds if nothing triggers it."""
    __slots__ = ("x", "y", "element", "color", "power", "radius", "dur",
                 "source", "t", "triggered")

    def __init__(self, x, y, element, color, power, radius, dur, source):
        self.x = float(x); self.y = float(y)
        self.element = element; self.color = color
        self.power = power; self.radius = radius
        self.dur = dur; self.source = source
        self.t = 0.0; self.triggered = False

    def update(self, dt, enemies, particles, on_enemy_hit, element_mult):
        self.t += dt
        self.dur -= dt
        if self.dur <= 0:
            return False
        for en in enemies:
            if en.alive and math.hypot(en.x - self.x, en.y - self.y) < self.radius + en.r:
                # trigger: AoE damage to all enemies within the radius + a burst.
                # Route each hit through on_enemy_hit (passing the summoning hero
                # as source) so a trap kill fires the death/reward path (xp/gold/
                # shards/combo), not a silent death. element_mult scales the trap
                # to the enemy's element (a dark trap vs a water enemy, etc.).
                combo_mul = 1.0  # traps don't ride the live combo counter
                for en2 in enemies:
                    if en2.alive and math.hypot(en2.x - self.x, en2.y - self.y) < self.radius:
                        mult = element_mult(self.element, en2.element)
                        dmg = max(1, int(self.power * mult * combo_mul))
                        dealt = en2.take_damage(dmg, self.x, self.y, on_attack=None)
                        if dealt > 0 and on_enemy_hit is not None:
                            on_enemy_hit(en2, self.source, dealt, False)
                particles.burst(self.x, self.y, self.color,
                                n=24, speed=300, size=6, life=0.5)
                particles.ring(self.x, self.y, self.color,
                               n=20, speed=360, size=5, life=0.45)
                self.triggered = True
                return False
        return True

    def draw(self, surf, ox, oy):
        x = int(self.x - ox); y = int(self.y - oy)
        if -40 < x < 1320 and -40 < y < 760:
            # a pulsing element-tinted hazard ring on the ground (pixel-art)
            pulse = 0.5 + 0.5 * math.sin(self.t * 6)
            r = int(self.radius * (0.9 + 0.1 * pulse))
            pygame.draw.circle(surf, (*self.color, 80) if len(self.color) == 3 else self.color,
                               (x, y), r, 2)
            pygame.draw.circle(surf, self.color, (x, y), 4)
