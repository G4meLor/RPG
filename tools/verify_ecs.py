"""ECS acceptance suite (grows each phase). Layer 1: component/entity/world unit tests."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1,1))

from src.entities.components import (Transform, Health, Combat, AI, Render,
    Identity, Statuses, ChampionRef)
from src.entities.entity import Entity
from src.core.world import World
from src.entities.hero import spawn_hero
from src.entities.enemy import spawn_enemy
from src.data.heroes import HERO_BY_ID

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

def test_spawn_hero():
    w = World()
    e = spawn_hero(w, "Ahri")
    assert e.has(Transform) and e.has(Health) and e.has(Combat) and e.has(AI) \
        and e.has(Render) and e.has(Identity) and e.has(Statuses) and e.has(ChampionRef)
    ident = e.get(Identity)
    assert ident.is_hero is True and ident.name == "Ahri"
    ref = e.get(ChampionRef)
    assert ref.hero_id == "Ahri" and ref.level == 1
    hp = e.get(Health)
    h = HERO_BY_ID["Ahri"]["stats"]
    assert hp.max_hp == h["hp"]  # level-1 base
    assert e.get(Combat).element == HERO_BY_ID["Ahri"]["element"]

def test_spawn_enemy():
    w = World()
    e = spawn_enemy(w, "Krugs", level=3)
    assert e.get(Identity).is_hero is False
    assert e.get(Combat).element is not None
    assert e.get(Health).max_hp > 0

def test_worldscene_entity_sync():
    """Integration test (Task 12): WorldScene builds a parallel World of
    entities (via the factories) that track the legacy WorldCharacter /
    WorldEnemy objects. After 60 frames, each hero entity's Transform.x
    matches its legacy WorldCharacter.x (±2) and the entity counts match
    the legacy party/enemy lists. The adapter is READ-ONLY on the legacy
    path — it must not change behavior."""
    import main as M
    g = M.Game()
    from src.scenes.world import WorldScene
    sc = WorldScene(g); g.scene = sc
    # the adapter must expose a World
    assert hasattr(sc, "world"), "WorldScene has no .world adapter"
    for _ in range(60):
        sc.update(0.016, []); sc.draw(g.screen)
    # 4 party heroes (the legacy party is a 4-slot list)
    heroes = sc.world.heroes()
    assert len(heroes) == 4, f"expected 4 hero entities, got {len(heroes)}"
    # each hero entity Transform matches its legacy WorldCharacter (±2 px)
    for wc in sc.party:
        if wc is None: continue
        e = next((e for e in heroes if e.get(ChampionRef).hero_id == wc.hero.id), None)
        assert e is not None, f"no entity for hero {wc.hero.id}"
        assert abs(e.get(Transform).x - wc.x) < 2, \
            f"{wc.hero.id} x drift: entity={e.get(Transform).x} legacy={wc.x}"
    # enemy entities: count should equal the legacy enemy list length
    # (the adapter spawns one entity per WorldEnemy append)
    assert len(sc.world.enemies()) == len(sc.enemies), \
        f"entity enemies {len(sc.world.enemies())} != legacy {len(sc.enemies)}"
    print("  worldscene entity sync OK")

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("Layer 1 OK")

if __name__ == "__main__":
    run()
