"""AISystem — per-enemy AI driving entity Transform/AI components.

Extracted from WorldEnemy.update (the per-id AI branches). The system iterates
world.enemies(), finds the nearest hero, and applies movement per AI.kind
(hop/pounce/kite/rush/melee/ranged/boss). Runs IN PARALLEL with the legacy
WorldEnemy.update path during Phase 4 — the legacy path stays the source of
truth until Task 20 (full takeover). The system writes entity Transform/AI
only; it does not deal damage (that's Task 20's CombatSystem integration).

Constants mirror the legacy WorldEnemy:
  aggro_range = (240 + spd*10) non-boss, 460 boss
  atk_range   = 50 non-boss, 70 boss
  speed       = (55 + spd*5 + level*2) non-boss, (70 + level) boss
  pounce lunge = 90px after 0.22s telegraph, atk_cd 1.4s
  hop lunge    = 70px after telegraph, atk_cd 1.6s
  chase        = vx = dx/d * speed; x += vx*dt
  kite         = back off (vx = -dx/d * speed) when dist < 150
"""
import math
import random

import pygame

from src.data.skills import boss_patterns
from src.entities.components import Transform, AI, Combat, Identity


class AISystem:
    def __init__(self, world, scene=None):
        self.world = world
        self.scene = scene

    def _pick_hero(self, heroes):
        """Pick the active hero: the scene's active party slot if available,
        else the first hero entity."""
        if self.scene is not None:
            idx = getattr(self.scene, "active", 0)
            party = getattr(self.scene, "party", [])
            if 0 <= idx < len(party) and party[idx] is not None:
                wc = party[idx]
                hid = wc.hero.id
                for h in heroes:
                    from src.entities.components import ChampionRef
                    ref = h.get(ChampionRef)
                    if ref is not None and ref.hero_id == hid:
                        return h
        return heroes[0] if heroes else None

    def update(self, dt):
        heroes = self.world.heroes()
        if not heroes:
            return
        hero = self._pick_hero(heroes)
        if hero is None:
            return
        ht = hero.get(Transform)
        if ht is None:
            return
        for en in self.world.enemies():
            self._update_enemy(en, dt, ht)

    def _update_enemy(self, en, dt, ht):
        t = en.get(Transform)
        ai = en.get(AI)
        if t is None or ai is None:
            return
        ident = en.get(Identity)
        combat = en.get(Combat)
        is_boss = ident.is_boss if ident else False
        spd = combat.spd if combat else 10
        aggro_range = 460 if is_boss else (240 + spd * 10)
        atk_range = 50 if not is_boss else 70
        # level: read from the stat_obj if available, else 1
        level = 1
        if combat is not None and combat.stat_obj is not None:
            level = getattr(combat.stat_obj, "level", 1)
        speed = (70 + level) if is_boss else (55 + spd * 5 + level * 2)

        dx = ht.x - t.x
        dy = ht.y - t.y
        dist = math.hypot(dx, dy) or 1

        # tick the multipurpose timer (aggro_t doubles as telegraph countdown
        # and attack cooldown depending on state)
        ai.aggro_t = max(0.0, ai.aggro_t - dt)

        if ai.state == "idle":
            if dist < aggro_range:
                ai.state = "aggro"
            return

        if ai.state == "aggro":
            if dist > aggro_range * 1.4:
                ai.state = "idle"
                return
            # pounce: MurkWolves/CrimsonRaptor — telegraph then 90px lunge
            if ai.kind == "pounce" and dist < 200 and ai.aggro_t <= 0:
                ai.state = "telegraph"
                ai.aggro_t = 0.22  # telegraph time
                return
            # hop: Krugs/Gromp — telegraph then 70px lunge
            if ai.kind == "hop" and dist < 240 and ai.aggro_t <= 0:
                ai.state = "telegraph"
                ai.aggro_t = 0.22
                return
            # generic melee telegraph when in atk_range
            if ai.kind in ("melee", "boss") and dist < atk_range and ai.aggro_t <= 0:
                ai.state = "telegraph"
                ai.aggro_t = 0.4
                return
            # ranged: telegraph at a distance
            if ai.kind == "ranged" and dist < 360 and ai.aggro_t <= 0:
                ai.state = "telegraph"
                ai.aggro_t = 0.5
                return
            # otherwise: chase (or kite for kiters)
            self._chase(en, t, dx, dy, dist, speed, ai.kind)
            return

        if ai.state == "telegraph":
            # face the hero, hold still
            if ai.aggro_t <= 0:
                # resolve the telegraph
                if ai.kind == "pounce":
                    # 90px lunge toward hero
                    t.x += dx / dist * 90
                    t.y += dy / dist * 90
                    ai.aggro_t = 1.4  # atk_cd
                elif ai.kind == "hop":
                    # 70px lunge toward hero
                    t.x += dx / dist * 70
                    t.y += dy / dist * 70
                    ai.aggro_t = 1.6
                else:
                    # melee/ranged: no lunge (damage is Task 20), just cooldown
                    ai.aggro_t = 1.4 if not is_boss else (2.2 if True else 1.5)
                ai.state = "aggro"
            return

    def _chase(self, en, t, dx, dy, dist, speed, kind):
        """Move toward (or away from, for kiters) the hero."""
        if kind == "kite" and dist < 150:
            # back off to maintain distance (VoidHound/Razorbeaks skirmisher)
            t.x -= dx / dist * speed * 0.016
            t.y -= dy / dist * speed * 0.016
        elif kind == "ranged":
            # ranged: keep distance ~280; move away if too close, toward if too far
            if dist < 250:
                t.x -= dx / dist * speed * 0.016
                t.y -= dy / dist * speed * 0.016
            elif dist > 320:
                t.x += dx / dist * speed * 0.016
                t.y += dy / dist * speed * 0.016
        else:
            # rush/melee/boss/hop/pounce: chase toward hero
            t.x += dx / dist * speed * 0.016
            t.y += dy / dist * speed * 0.016

    # -----------------------------------------------------------------------
    # Task 20d — full-fidelity verbatim port of WorldEnemy.update.
    # The body below is copied verbatim from src/entities/_legacy_world_entities.py
    # (the `update` method on WorldEnemy, starting at line 1027). The only
    # rewire is `self` (the WorldEnemy) -> `en` (the WorldEnemy passed as the
    # first arg). The method operates on the en's OWN fields (x, vx, state,
    # enemy, etc.) + the params (target, obstacles, projectiles, particles,
    # on_attack). Helper method calls `self._do_attack`/`self._collide`/
    # `self.take_damage` -> `en._do_attack`/`en._collide`/`en.take_damage`
    # (WorldEnemy methods, unchanged). WorldEnemy.update becomes a 1-line
    # delegate to this staticmethod (see _legacy_world_entities.py). The
    # Projectile class is imported lazily from the legacy module to avoid a
    # circular import at module load time (the legacy module imports Camera
    # from this module's sibling physics.py).
    # -----------------------------------------------------------------------
    @staticmethod
    def update_enemy(en, dt, target, obstacles, projectiles, particles, on_attack):
        if not en.alive:
            return
        # knockback
        if abs(en.kb_x) > 1 or abs(en.kb_y) > 1:
            en.x += en.kb_x * dt
            en.y += en.kb_y * dt
            en.kb_x *= 0.8
            en.kb_y *= 0.8
        en.hit_flash = max(0, en.hit_flash - dt)
        en.invuln_t = max(0, en.invuln_t - dt)
        en.atk_cd = max(0, en.atk_cd - dt)
        en.atk_cd2 = max(0, en.atk_cd2 - dt)
        en.state_t -= dt
        # reaction timers: the element-hit window counts down; a freeze stun
        # skips the enemy's AI while it lasts
        en._element_hit_t = max(0, en._element_hit_t - dt)
        en._react_stun = max(0, en._react_stun - dt)
        # HSR toughness break recovery: count down the 2s window set on break;
        # when it elapses + the bar is still broken, refill it so the fight
        # reopens (the +50% break window ends). Mirrors recover_toughness()
        # end-of-round semantics but in real time (see take_damage).
        if en._broken_recover_t > 0:
            en._broken_recover_t = max(0, en._broken_recover_t - dt)
            if en._broken_recover_t == 0 and en.enemy.broken:
                en.enemy.recover_toughness()
                en._broke_flag = False

        # boss ultimate below 50%
        if en.is_boss and not en.ult_used and en.enemy.hp < en.enemy.max_hp * 0.5:
            en.ult_used = True
            on_attack("boss_ult", en)

        # boss phase progression: 66% and 33% HP thresholds advance the phase,
        # unlocking new telegraphed attack patterns (see data.BOSS_PATTERNS).
        if en.is_boss:
            frac = en.enemy.hp / max(1, en.enemy.max_hp)
            new_phase = 1 if frac > 0.66 else (2 if frac > 0.33 else 3)
            if new_phase > en._boss_phase:
                en._boss_phase = new_phase
                # entering a new phase: brief telegraph + a warning sound so the
                # player feels the fight escalate
                on_attack("boss_phase", en)

        # frozen by a Freeze reaction: skip the AI this frame (the enemy is
        # encased in ice and can't act; still takes damage / knockback)
        if en._react_stun > 0:
            return

        dist = math.hypot(target.x - en.x, target.y - en.y) if target else 9999

        if en.state == "hurt":
            if en.state_t <= 0:
                en.state = "aggro"
        elif en.state == "idle":
            # wander
            en.roam_t -= dt
            if en.roam_t <= 0:
                en.roam_t = 1.5 + random.random() * 2
                en.roam_target = (en.x + random.uniform(-120, 120),
                                    en.y + random.uniform(-120, 120))
            if dist < en.aggro_range:
                en.state = "aggro"
        elif en.state == "aggro":
            if dist > en.aggro_range * 1.4:
                en.state = "idle"
                en.moving = False
                return
            # Krugs: a slow waddler that telegraphed hop-lunges instead of a flat
            # chase+strike. It leaps in a predictable, dodgeable arc — the
            # textbook "kite the blob" starter enemy (distinct from a flat chaser).
            if en.id == "Krugs":
                en.hop_t = getattr(en, "hop_t", 0) - dt
                if en.hop_t <= 0 and dist < 240:
                    en.hop_t = 1.6
                    dx = target.x - en.x; dy = target.y - en.y
                    dd = math.hypot(dx, dy) or 1
                    en.x += dx / dd * 70
                    en.y += dy / dd * 70
                    en._collide(obstacles)
                    on_attack("enemy_strike", en)
                    if math.hypot(target.x - en.x, target.y - en.y) < en.atk_range + 20:
                        res = target.take_damage(en.enemy.atk * 1.2, en.x, en.y, is_melee=True)
                        if isinstance(res, tuple) and res[1] > 0:
                            en.take_damage(res[1], target.x, target.y)
                    en.atk_cd = 1.6
                    en.moving = False
                    return
            # bosses in phase 2+ weave special telegraphed patterns (charge /
            # slam) between their basic strikes, on their own cooldown. The
            # pattern telegraphs first, then resolves in the "pattern" state.
            # The trigger chance + pattern selection scale with the phase so the
            # fight visibly escalates (phase 3 favors the newly-unlocked slam).
            if (en.is_boss and en._boss_phase >= 2 and en._boss_pattern is None
                    and en.atk_cd <= 0 and en._boss_pat_t <= 0):
                patterns = boss_patterns(en.id, en._boss_phase)
                trigger_p = {1: 0.0, 2: 0.5, 3: 0.75}.get(en._boss_phase, 0.6)
                if patterns and random.random() < trigger_p:
                    if en._boss_phase >= 3 and len(patterns) > 1:
                        # phase 3: favor the newly-unlocked (last) pattern
                        pat = random.choice(patterns[-1:] + patterns[:-1])
                    else:
                        pat = random.choice(patterns)
                    en._boss_pattern = pat
                    en._boss_pat_t = 0.8 if pat == "charge" else 0.6
                    if pat == "charge" and target:
                        # lock the charge target at the player's current pos so
                        # the boss commits to the line (dodgeable by sidestepping)
                        en._boss_charge_target = (target.x, target.y)
                    on_attack("boss_warn", en)
                    en.moving = False
                    return
            # MurkWolves: a fast stalker that pounces — a short windup then a long
            # lunge at atk*1.4 (a real predator archetype, distinct from the blob
            # and the skirmisher). Only when the basic attack is off cooldown.
            if en.id == "MurkWolves" and dist < 200 and en.atk_cd <= 0:
                en.state = "telegraph"
                en.telegraph_t = 0.22
                en._pounce = True
            elif dist < en.atk_range and en.atk_cd <= 0 and not en.ranged:
                en.state = "telegraph"
                en.telegraph_t = 0.4
            elif en.ranged and en.atk_cd <= 0 and dist < 360:
                en.state = "telegraph"
                en.telegraph_t = 0.5
            else:
                # chase
                dx = target.x - en.x
                dy = target.y - en.y
                d = math.hypot(dx, dy) or 1
                # VoidHound kiter: back off when the hero closes in so it keeps its
                # distance and throws dark_bolt from range (a skirmisher that
                # feels distinct from a plain melee chaser).
                if en.id == "VoidHound" and dist < 150:
                    en.vx = -dx / d * en.speed
                    en.vy = -dy / d * en.speed
                else:
                    en.vx = dx / d * en.speed
                    en.vy = dy / d * en.speed
                en.x += en.vx * dt
                en.y += en.vy * dt
                en.facing = 1 if dx > 0 else -1
                en._collide(obstacles)
                en.moving = True
        elif en.state == "telegraph":
            # face target, hold still, then strike
            if target:
                en.facing = 1 if target.x > en.x else -1
            if en.telegraph_t <= 0:
                en._do_attack(target, projectiles, particles, on_attack)
                # phase 3 bosses attack faster (the fight escalates)
                en.atk_cd = (1.4 if not en.is_boss
                               else (2.2 if en._boss_phase < 3 else 1.5))
                en.state = "aggro"

        # active boss pattern: telegraph then resolve. The charge is a sustained
        # multi-frame dash along the telegraphed line (so sidestepping is the real
        # dodge), not a single-frame hop — the boss travels until it reaches (or
        # overshoots) the locked target, then resolves the hit on overlap.
        if en._boss_pattern is not None:
            en._boss_pat_t -= dt
            if en._boss_pattern == "charge":
                if en._boss_pat_t <= 0:
                    tx, ty = en._boss_charge_target
                    dx, dy = tx - en.x, ty - en.y
                    d = math.hypot(dx, dy)
                    if d is None or d < 12:
                        # reached the target -> resolve the charge hit
                        on_attack("boss_charge", en)
                        en._boss_pattern = None
                        en.atk_cd = 2.5
                        en.state = "aggro"
                    else:
                        # sustained dash toward the locked target (~300px/s);
                        # the scene's boss_charge handler damages on overlap.
                        step = min(d, en.speed * 3.0 * dt)
                        en.x += dx / d * step
                        en.y += dy / d * step
                        en.facing = 1 if dx > 0 else -1
                        en.moving = True
            elif en._boss_pattern == "slam":
                if en._boss_pat_t <= 0:
                    # resolve: an expanding burst at the boss's feet; damage in a
                    # radius is applied by _on_enemy_event("boss_slam", ...).
                    on_attack("boss_slam", en)
                    en._boss_pattern = None
                    en.atk_cd = 2.0
                    en.state = "aggro"

        # animation: walk bob while chasing, idle breathing otherwise
        if en.moving:
            en.walk_t += dt * 9
        else:
            en.walk_t = 0.0
            en.idle_t += dt * 2.0

        # flip sprite cache
        if en._sprite is not None and en._sprite_face != en.facing:
            en._sprite = pygame.transform.flip(en._sprite, True, False)
            en._sprite_face = en.facing
