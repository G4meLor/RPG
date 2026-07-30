"""Enemy entity factory — spawns an entity with components + a Combatant.Enemy stat obj."""
from __future__ import annotations
from typing import TYPE_CHECKING
from src.entities.entity import Entity
from src.entities.components import (Transform, Health, Combat, AI, Render,
    Identity, Statuses, Movement)
from src.entities.combatant import Enemy

if TYPE_CHECKING:
    from src.core.world import World  # noqa: F401  (annotation only — avoids cycle)


def spawn_enemy(world: "World", enemy_id: str, level: int = 1, is_boss: bool = False,
                x: float = 0.0, y: float = 0.0) -> Entity:
    en = Enemy(enemy_id, level=level, is_boss=is_boss)
    e = world.spawn()
    e.add(Identity(e.eid, en.name, is_hero=False, is_boss=is_boss or en.is_boss))
    e.add(Transform(x, y, r=40 if is_boss else 26))
    e.add(Health(en.hp, en.max_hp, en.mp, en.max_mp))
    e.add(Combat(en.element, en.atk, en.defn, en.spd, stat_obj=en))
    # AI kind: LoL mob/boss id -> behaviour kind (mirror the legacy _ALIAS map)
    _AI_KIND = {"Krugs": "hop", "MurkWolves": "pounce", "Razorbeaks": "kite",
                "VoidHound": "kite", "Raptors": "pounce", "Voidlings": "rush",
                "Gromp": "hop", "Wraiths": "rush", "CrimsonRaptor": "pounce",
                "FallenKnight": "melee", "Sylas": "melee", "Swain": "ranged",
                "Lissandra": "ranged", "Mordekaiser": "melee", "Viego": "rush",
                "Baron": "boss"}
    e.add(AI(kind=_AI_KIND.get(enemy_id, "melee")))
    e.add(Render(sprite_id=enemy_id, weapon="sword"))
    e.add(Statuses())
    # Movement component (Phase 4, Task 15): mirrors the hero's so the
    # PhysicsSystem can drive enemy entities uniformly. Bosses use r=40 to
    # match their larger collision radius.
    e.add(Movement(r=40 if is_boss else 26))
    return e
