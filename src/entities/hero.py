"""Hero entity factory — spawns an entity with components + a Combatant.Hero stat obj."""
from __future__ import annotations
from typing import TYPE_CHECKING
from src.entities.entity import Entity
from src.entities.components import (Transform, Health, Combat, AI, Render,
    Identity, Statuses, ChampionRef, Movement)
from src.entities.combatant import Hero
from src.data.heroes import HERO_BY_ID

if TYPE_CHECKING:
    from src.core.world import World  # noqa: F401  (annotation only — avoids cycle)


def spawn_hero(world: "World", hero_id: str, level: int = 1, ascension: int = 0,
               evolve: int = 0, skin: int = 0, x: float = 0.0, y: float = 0.0) -> Entity:
    hdef = HERO_BY_ID[hero_id]
    hero = Hero(hdef, level=level, ascension=ascension, evolve=evolve, skin=skin)
    e = world.spawn()
    e.add(Identity(e.eid, hero.name, is_hero=True))
    e.add(Transform(x, y))
    e.add(Health(hero.hp, hero.max_hp, hero.mp, hero.max_mp))
    # stat_obj holds the Hero instance for systems to read. Combat is
    # @dataclass(slots=True) but `stat_obj` is a declared field, so it can be
    # set in the constructor (preferred) or assigned after — both work.
    e.add(Combat(hero.element, hero.atk, hero.defn, hero.spd, stat_obj=hero))
    e.add(AI(kind="hero"))
    # weapon comes from the champion descriptor
    import src.build.champions as _CH
    c = _CH.CHAMPION_BY_KEY.get(hero_id)
    weapon = c["descriptor"]["weapon"] if c else "sword"
    e.add(Render(sprite_id=hero_id, weapon=weapon))
    e.add(Statuses())
    e.add(ChampionRef(hero_id=hero_id, level=level, ascension=ascension, skin=skin))
    # Movement component (Phase 4, Task 15): the PhysicsSystem reads/writes
    # this instead of the legacy WorldCharacter's movement fields. Defaults
    # match WorldCharacter.__init__ (max_speed=230, accel=2400, friction=1800,
    # r=20). The legacy wc stays the source of truth this task; the entity's
    # Movement is the parallel-prove path.
    e.add(Movement())
    return e
