"""ECS acceptance suite (grows each phase). Layer 1: component/entity/world unit tests."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1,1))

from src.entities.components import (Transform, Health, Combat, AI, Render,
    Identity, Statuses, ChampionRef)
from src.entities.entity import Entity
from src.core.world import World

def test_entity_components():
    e = Entity(0)
    assert e.eid == 0
    assert e.has(Transform) is False
    e.add(Transform(100, 200))
    assert e.has(Transform) is True
    t = e.get(Transform)
    assert t.x == 100 and t.y == 200 and t.vx == 0 and t.vy == 0 and t.r == 26
    assert e.add(Health(100, 100, 50, 120)) is e  # chaining

def test_component_defaults():
    assert Transform(0,0).r == 26
    assert AI("hop").state == "idle" and AI("hop").target == -1
    assert Identity(0, "Ahri", True).is_boss is False
    assert ChampionRef("Ahri").skin == 0 and ChampionRef("Ahri").level == 1

def test_world_spawn_destroy_query():
    w = World()
    a = w.spawn(); b = w.spawn(); c = w.spawn()
    assert len({a.eid, b.eid, c.eid}) == 3
    a.add(Identity(a.eid, "Ahri", True)); a.add(Transform(0,0))
    b.add(Identity(b.eid, "Krugs", False)); b.add(Transform(10,10))
    c.add(Identity(c.eid, "Lux", True))
    assert {e.eid for e in w.query(Identity, Transform)} == {a.eid, b.eid}
    assert {e.eid for e in w.heroes()} == {a.eid, c.eid}
    assert {e.eid for e in w.enemies()} == {b.eid}
    w.destroy(b.eid)
    assert b.eid not in w.entities
    assert {e.eid for e in w.enemies()} == set()

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("Layer 1 OK")

if __name__ == "__main__":
    run()
