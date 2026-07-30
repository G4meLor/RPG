"""DropSystem (Phase 4, Task 18 of the ECS restructure) — ground loot drops.

Mirrors the legacy ``_spawn_drop``/``_pickup_drop`` bodies from
``src/scenes/world.py`` (world.py:2381-2436), but operates on the ECS entity
layer + the player object instead of the legacy ``WorldCharacter``. Runs IN
PARALLEL with the legacy drop path (additive) — the legacy path stays the
source of truth until Task 20 (full takeover). The system owns ``self.drops``
(a list of drop dicts); the legacy ``WorldScene.drops`` list is UNTOUCHED and
keeps driving the 21-test suite.

Drop kinds (mirrors legacy ``_spawn_drop``):
  - ``gold``     -> aggregates into ONE drop carrying the total value
                    (a 200g drop is one coin sprite worth 200, not 200 sprites).
  - ``hp_potion``/``shard``/``equipment`` -> one drop per call, with a small
                    random scatter offset (±10px) so a multi-drop doesn't stack.

Pickup (mirrors legacy ``_pickup_drop``):
  - ``gold``       -> ``player.gold += value`` + ``stats["gold_earned"]``
  - ``hp_potion``  -> ``player.add_item("hp_potion", 1)``
  - ``shard``      -> ``player.shards += value``
  - ``equipment``  -> ``player.add_equipment(value)``
  - unknown kind   -> no-op (defensive, mirrors the legacy ``return``)

The sparkle burst / float text / audio cue are presentation-only and are
deferred to Task 20's full integration; this task proves the gold/shard/item
increment works on the entity/player layer self-containedly.

``update(dt)`` mirrors the legacy walk-over pickup (world.py:2735-2753) +
the magnet pull (world.py:2745-2751) + the age/expire (world.py:3042-3045):
  - within 40px of the active hero  -> pickup (add to inventory + remove drop)
  - within 80px                      -> magnet pull toward the hero
  - every drop ages ``t += dt``      -> expire at ``t >= 30.0``
"""
import random

from src.entities.components import Transform


# pickup radius (mirrors legacy world.py:2741: ``if dist < 40``)
_PICKUP_RADIUS = 40
# magnet radius (mirrors legacy world.py:2745: ``elif dist < 80``)
_MAGNET_RADIUS = 80
# drop lifetime in seconds (mirrors legacy world.py:3045: ``d["t"] < 30.0``)
_DROP_LIFETIME = 30.0
# per-call drop count cap (mirrors legacy world.py:2398: ``max(1, min(count, 4))``)
_MAX_DROP_COUNT = 4
# magnet pull rate per second (mirrors legacy world.py:2749: ``min(1.0, sim_dt*8)``)
_MAGNET_PULL_RATE = 8.0


class DropSystem:
    """ECS ground-loot system — spawn / pickup / drift+expire.

    Parameters
    ----------
    world : World
        The ECS entity world (used to read hero Transforms for the
        proximity-based pickup in ``update``).
    scene : WorldScene or None
        The owning scene. Used to read ``scene.game.player`` for the pickup
        increment + ``scene.active``/``scene.party`` to find the active hero
        entity. May be None for headless tests (callers pass the player
        explicitly via ``pickup``).
    """

    def __init__(self, world, scene=None):
        self.world = world
        self.scene = scene
        # the system-owned drop list (parallel to the legacy WorldScene.drops).
        # The legacy list is UNTOUCHED; this list is the system's own state.
        self.drops = []

    # ------------------------------------------------------------------
    # spawn (mirrors legacy _spawn_drop, world.py:2381-2404)
    # ------------------------------------------------------------------
    def spawn(self, x, y, kind, value, count=1):
        """Spawn one (or ``count``) ground loot drop(s) at (x, y).

        Gold aggregates into ONE drop carrying the total value; the other
        kinds are 1-drop-per-call (capped at ``_MAX_DROP_COUNT`` so a stray
        high count doesn't flood). Returns the first drop created (so callers
        can pass it straight to ``pickup`` for a headless test); further drops
        from a multi-drop call are appended to ``self.drops`` but not returned.

        Mirrors legacy ``_spawn_drop`` (world.py:2381-2404) verbatim, minus the
        ``self.drops`` -> ``self.drops`` rename (the system owns its own list).
        """
        first = None
        if kind == "gold":
            # gold aggregates into one drop carrying the total value (a 200g
            # drop is one coin sprite worth 200, not 200 coin sprites).
            d = {"x": float(x), "y": float(y),
                 "kind": "gold", "value": int(value),
                 "t": 0.0, "sprite_id": "gold"}
            self.drops.append(d)
            return d
        n = max(1, min(int(count), _MAX_DROP_COUNT))  # cap so a stray high count doesn't flood
        for _ in range(n):
            ox = x + random.uniform(-10, 10)
            oy = y + random.uniform(-10, 10)
            d = {"x": float(ox), "y": float(oy),
                 "kind": kind, "value": value,
                 "t": 0.0, "sprite_id": kind}
            self.drops.append(d)
            if first is None:
                first = d
        return first

    # ------------------------------------------------------------------
    # pickup (mirrors legacy _pickup_drop, world.py:2406-2436)
    # ------------------------------------------------------------------
    def pickup(self, drop, hero_entity=None):
        """Collect a ground loot drop: add its value to the player's inventory
        by kind + remove it from ``self.drops``.

        Reads the player from ``self.scene.game.player`` (mirrors legacy
        ``p = self.game.player``). The ``hero_entity`` arg is accepted for
        signature symmetry with the legacy ``_pickup_drop(drop, wc)`` but is
        not strictly required for the gold/shard/item increment (the legacy
        method only uses ``wc`` for the sparkle-burst position, which is
        presentation-only and deferred to Task 20).

        Mirrors legacy ``_pickup_drop`` (world.py:2406-2436) verbatim, minus
        the particles/floats/audio (presentation-only, deferred to Task 20).
        """
        if self.scene is None:
            return  # headless: caller should set scene, or skip pickup
        p = self.scene.game.player
        kind = drop["kind"]
        value = drop["value"]
        if kind == "gold":
            p.gold += value
            p.stats["gold_earned"] = p.stats.get("gold_earned", 0) + value
        elif kind == "hp_potion":
            p.add_item("hp_potion", 1)
        elif kind == "shard":
            p.shards += value
        elif kind == "equipment":
            p.add_equipment(value)
        else:
            return  # unknown kind — don't collect (defensive, mirrors legacy)
        # remove the drop from the system list (mirrors the legacy
        # ``self.drops = [d for d in self.drops if d not in picked]`` filter)
        if drop in self.drops:
            self.drops.remove(drop)

    # ------------------------------------------------------------------
    # update (mirrors legacy walk-over pickup + magnet + age/expire,
    # world.py:2735-2753 + 3042-3045)
    # ------------------------------------------------------------------
    def _active_hero_entity(self):
        """Find the active hero entity (the one the player controls). Mirrors
        the legacy ``wc = self.party[self.active]`` selection, but returns the
        ECS hero entity (so we can read its Transform for the proximity check).
        Falls back to the first hero entity if the active slot has no entity."""
        if self.scene is None:
            return None
        idx = getattr(self.scene, "active", 0)
        party = getattr(self.scene, "party", [])
        hero_map = getattr(self.scene, "_entity_for_hero", {})
        if 0 <= idx < len(party) and party[idx] is not None:
            wc = party[idx]
            hid = wc.hero.id
            e = hero_map.get(hid)
            if e is not None:
                return e
        heroes = self.world.heroes()
        return heroes[0] if heroes else None

    def update(self, dt):
        """Drift drops + on hero proximity pickup + age/expire.

        Mirrors the legacy walk-over check (world.py:2735-2753) + the
        age/expire (world.py:3042-3045). The pickup radius is 40px; the magnet
        radius is 80px (a drop within 80px is pulled toward the hero, not
        collected). Drops age ``t += dt`` and expire at ``t >= 30.0``.
        """
        if not self.drops:
            return
        hero = self._active_hero_entity()
        ht = hero.get(Transform) if hero is not None else None
        picked = []
        for d in self.drops:
            if ht is not None:
                dx = ht.x - d["x"]
                dy = ht.y - d["y"]
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < _PICKUP_RADIUS:
                    # within pickup radius — collect
                    self.pickup(d, hero)
                    picked.append(d)
                    continue
                elif dist < _MAGNET_RADIUS:
                    # within magnet radius — pull toward the hero (not collect).
                    # The pull is a fraction of the distance per frame so the
                    # drop accelerates as it gets closer (reads as a magnet).
                    pull = min(1.0, dt * _MAGNET_PULL_RATE)
                    d["x"] += dx * pull
                    d["y"] += dy * pull
            # age + expire (mirrors world.py:3042-3045)
            d["t"] += dt
        # filter out picked-up + expired drops
        self.drops = [d for d in self.drops
                      if d not in picked and d["t"] < _DROP_LIFETIME]
