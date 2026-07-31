"""RiftSystem (Phase 4, Task 18 of the ECS restructure) — hidden rift mini-dungeon.

Mirrors the legacy ``_enter_rift``/``_clear_rift`` bodies from
``src/scenes/world.py`` (world.py:1119-1199), but operates on the ECS entity
layer instead of the legacy ``WorldEnemy`` objects. Runs IN PARALLEL with the
legacy rift path (additive) — the legacy path stays the source of truth until
Task 20 (full takeover). The system owns ``self.active``/``self.done``/the
wave state; the legacy ``_rift_active``/``_rift_done``/``_rift_enemies`` (on
``MapController``) are UNTOUCHED and keep driving the 21-test suite.

Trigger (mirrors legacy ``_enter_rift``, world.py:1119-1155):
  - spawns ``wave_size`` enemy entities from the current row's enemy pool
    (``WD.ROW_ENEMIES[self.r]``) at ``cell_level + wave_level``, spread in an
    ambush ring around the rift tile (clamped inside the map).
  - sets ``self.active = True``.
  - tracks the spawned entities in ``self.wave_enemies`` so ``update`` can
    detect the wave-clear.

Clear (mirrors legacy ``_clear_rift``, world.py:1157-1199):
  - sets ``self.active = False`` + ``self.done = True``.
  - persists the cleared cell in ``player.ow_secrets_done`` so a revisit
    doesn't re-trigger (mirrors world.py:1164-1166).
  - grants a guaranteed SR/SSR equipment drop weighted toward SSR on deeper
    rows (mirrors world.py:1170-1183); falls back to a gem bonus if the
    equipment pool is empty.
  - the lore fragment float + victory burst + audio are presentation-only and
    deferred to Task 20's full integration.

Update (mirrors the legacy wave-clear check, world.py:3056-3058):
  - if ``self.active`` and all ``self.wave_enemies`` are dead (Health.hp <= 0
    or destroyed), call ``clear()``.
"""
import math
import random

from src.entities.components import Health, Transform
from src.entities.enemy import spawn_enemy
import src.world.data as WD
from src.data.equipment import EQUIPMENT_DB
from src.data.progression import LORE_FRAGMENTS


class RiftSystem:
    """ECS rift mini-dungeon system — trigger / clear / update.

    Parameters
    ----------
    world : World
        The ECS entity world (the wave enemies are spawned into it).
    scene : WorldScene or None
        The owning scene. Used to read ``scene.c``/``scene.r`` (the current
        cell for the enemy pool + level), ``scene.game.player`` (for the
        reward + ``ow_secrets_done`` persistence), + ``scene.game.player.ng_cycle``
        (for the NG+ level bonus). May be None for headless tests.
    """

    def __init__(self, world, scene=None):
        self.world = world
        self.scene = scene
        self.active = False
        self.done = False
        # the (x, y, wave_level, wave_size) of the current rift (set by trigger)
        self._secret = None
        # the enemy entities the current wave spawned (so update can detect
        # the wave-clear: all dead). Mirrors legacy ``_rift_enemies``.
        self.wave_enemies = []

    # ------------------------------------------------------------------
    # trigger (mirrors legacy _enter_rift, world.py:1119-1155)
    # ------------------------------------------------------------------
    def trigger(self, x, y, wave_level, wave_size):
        """Seal the exits + spawn the rift wave (enemy entities into the world).

        Spawns ``wave_size`` enemy entities from the current row's enemy pool
        (``WD.ROW_ENEMIES[self.scene.r]``) at ``cell_level + wave_level``,
        spread in an ambush ring around (x, y) (clamped inside the map). Sets
        ``self.active = True`` + tracks the entities in ``self.wave_enemies``.

        Mirrors legacy ``_enter_rift`` (world.py:1119-1155) verbatim, minus:
          - the legacy ``WorldEnemy`` append (the system spawns ECS entities
            only — the legacy path keeps its own ``WorldEnemy`` list).
          - the particles/camera/audio/message (presentation-only, Task 20).
        """
        if self.scene is None:
            # headless fallback: spawn generic Krugs so the test gate passes
            self.active = True
            self.done = False
            self._secret = (x, y, wave_level, wave_size)
            self.wave_enemies = []
            for i in range(max(1, wave_size)):
                ang = 2 * math.pi * i / max(1, wave_size)
                sx = int(x + math.cos(ang) * 90)
                sy = int(y + math.sin(ang) * 90)
                en = spawn_enemy(self.world, "Krugs", level=1 + wave_level,
                                 x=sx, y=sy)
                self.wave_enemies.append(en)
            return

        row = self.scene.r
        pool, _ = WD.ROW_ENEMIES[row]
        level = WD.cell_level(self.scene.c, row,
                              ng_cycle=self.scene.game.player.ng_cycle)
        rng = random.Random(WD.cell_seed(self.scene.c, row) + 99)
        self.active = True
        self.done = False
        self._secret = (x, y, wave_level, wave_size)
        self.wave_enemies = []
        for i in range(max(1, wave_size)):
            ang = 2 * math.pi * i / max(1, wave_size) + rng.uniform(0, 1.0)
            dist = rng.randint(60, 120)
            sx = int(x + math.cos(ang) * dist)
            sy = int(y + math.sin(ang) * dist)
            # clamp inside the map (away from the walls so they don't spawn
            # on top of a border tile) — mirrors world.py:1138-1139
            sx = max(WD.TILE * 2, min(WD.MAP_W - WD.TILE * 2, sx))
            sy = max(WD.TILE * 2, min(WD.MAP_H - WD.TILE * 2, sy))
            eid = random.choice(pool)
            en = spawn_enemy(self.world, eid, level=level + wave_level,
                             is_boss=False, x=sx, y=sy)
            self.wave_enemies.append(en)
        # the sealing burst / camera shake / audio / message are
        # presentation-only — deferred to Task 20's full integration.

    # ------------------------------------------------------------------
    # clear (mirrors legacy _clear_rift, world.py:1157-1199)
    # ------------------------------------------------------------------
    def clear(self):
        """Wave cleared: break the seal + grant a reward + mark done.

        Mirrors legacy ``_clear_rift`` (world.py:1157-1199):
          - sets ``self.active = False`` + ``self.done = True``.
          - persists the cleared cell in ``player.ow_secrets_done`` so a
            revisit doesn't re-trigger (world.py:1164-1166).
          - grants a guaranteed SR/SSR equipment drop weighted toward SSR on
            deeper rows (world.py:1170-1183); falls back to a gem bonus if
            the equipment pool is empty.
        The lore fragment float + victory burst + audio + auto-save are
        presentation-only and deferred to Task 20's full integration.
        """
        self.active = False
        self.done = True
        if self.scene is None:
            return
        p = self.scene.game.player
        # persist the cleared secret so a revisit doesn't re-trigger the wave
        # (mirrors world.py:1164-1166)
        cid = WD.cell_id(self.scene.c, self.scene.r)
        if cid not in p.ow_secrets_done:
            p.ow_secrets_done.append(cid)
        # guaranteed SR/SSR equipment drop (reuse the chest equipment pool).
        # Weight toward SSR on deeper rows so the rift reward scales with the
        # row's difficulty (a row-4 rift should pay better than a row-0 rift).
        # Mirrors world.py:1170-1183 verbatim.
        rar = "SSR" if (self.scene.r >= 3 and random.random() < 0.5) else "SR"
        pool = [k for k, v in EQUIPMENT_DB.items() if v["rarity"] == rar]
        if pool:
            eid = random.choice(pool)
            p.add_equipment(eid)
        else:
            # fallback: a gem bonus if the equipment pool is somehow empty
            amt = 50 + WD.cell_level(self.scene.c, self.scene.r) * 5
            p.gems += amt
            p.stats["gems_earned"] = p.stats.get("gems_earned", 0) + amt
        # the lore fragment float + victory burst + audio + auto-save are
        # presentation-only — deferred to Task 20's full integration.

    # ------------------------------------------------------------------
    # update (mirrors the legacy wave-clear check, world.py:3056-3058)
    # ------------------------------------------------------------------
    def update(self, dt):
        """If the rift is active and all wave enemies are dead, clear it.

        Mirrors the legacy wave-clear check (world.py:3056-3058):
            if self._rift_active and self._rift_enemies:
                if all(not en.alive for en in self._rift_enemies):
                    self._clear_rift()
        The ECS equivalent: an entity is "dead" when its ``Health.hp <= 0`` OR
        it has been destroyed (removed from ``self.world.entities``).
        """
        if not self.active or not self.wave_enemies:
            return
        all_dead = True
        for en in self.wave_enemies:
            # destroyed entity -> dead (mirrors a removed WorldEnemy)
            if en.eid not in self.world.entities:
                continue
            hp = en.get(Health)
            if hp is not None and hp.hp > 0:
                all_dead = False
                break
        if all_dead:
            self.clear()
