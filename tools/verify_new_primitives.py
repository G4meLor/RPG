"""Headless test: new feature primitives render + add pixels (no image reading)."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.assets_gen.generate import draw_chibi_descriptor
from src.build.vlm_client import VOCAB

PAL = {"primary": [220, 90, 40], "secondary": [255, 170, 90], "accent": [255, 230, 140]}
BASE = {"archetype": "knight", "weapon": "none", "palette": PAL,
        "features": [], "build": "average", "motif": "flame"}

def _coverage(surf):
    a = pygame.surfarray.pixels_alpha(surf); arr = a.__array__(); del a
    return float((arr > 8).sum()) / (surf.get_width() * surf.get_height())

def test_new_features_in_vocab():
    for f in ("fox_tails", "animal_ears", "claws"):
        assert f in VOCAB["features"], f"{f} not in VLM vocab"

def test_fox_tails_renders_and_adds_pixels():
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s, {**BASE, "features": ["fox_tails"]})
    assert s.get_size() == (256, 256)
    c = _coverage(s)
    base = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(base, BASE)
    assert c > _coverage(base) + 0.005  # fox_tails added visible pixels

def test_animal_ears_renders():
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s, {**BASE, "features": ["animal_ears"]})
    assert s.get_size() == (256, 256) and _coverage(s) > 0

def test_claws_renders():
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s, {**BASE, "features": ["claws"]})
    assert s.get_size() == (256, 256) and _coverage(s) > 0

def test_weapon_vocab_widened():
    for w in ("sword", "staff", "bow", "dagger", "shield", "orb", "axe",
              "spear", "gun", "fists", "scythe", "whip", "gauntlet", "none"):
        assert w in VOCAB["weapon"], f"{w} missing from VLM weapon vocab"

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("NEW PRIMITIVES OK")

if __name__ == "__main__":
    run()
