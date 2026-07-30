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
