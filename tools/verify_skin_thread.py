"""Headless test: Hero.skin threads from record -> Hero -> ChampionRef."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))
if os.path.exists("saves/save.json"): os.remove("saves/save.json")

from src.entities.combatant import Hero
from src.data.heroes import HERO_BY_ID
from src.entities.components import ChampionRef

def test_hero_skin_default_and_set():
    hd = HERO_BY_ID["Ahri"]
    assert Hero(hd).skin == 0
    assert Hero(hd, skin=14).skin == 14

def test_get_hero_instance_threads_skin():
    import main
    g = main.Game()
    g.player.owned["Ahri"] = dict(level=1, xp=0, dupes=0, ascension=0, equipment={},
                                  evolve=0, evo_nodes=[], skin=14)
    h = g.player.get_hero_instance("Ahri")
    assert h is not None and h.skin == 14

def test_spawn_hero_threads_skin():
    from src.core.world import World
    from src.entities.hero import spawn_hero
    w = World()
    e = spawn_hero(w, "Ahri", skin=14, x=100, y=100)
    assert e.get(ChampionRef).skin == 14
    e2 = spawn_hero(World(), "Ahri", x=0, y=0)
    assert e2.get(ChampionRef).skin == 0

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("SKIN THREAD OK")

if __name__ == "__main__":
    run()
