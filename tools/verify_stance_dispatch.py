"""Stance dispatch: 5 stances render + no-stance backward-compat."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))
from src.assets_gen.generate import draw_chibi_descriptor
import pygame.surfarray, numpy as np

PAL = {"primary": [220, 90, 40], "secondary": [255, 170, 90], "accent": [255, 230, 140]}
BASE = {"archetype": "knight", "weapon": "none", "palette": PAL,
        "features": [], "build": "average", "motif": "flame"}

def _cov(surf):
    a = pygame.surfarray.pixels_alpha(surf); arr = a.__array__(); del a
    return float((arr > 8).sum()) / (surf.get_width() * surf.get_height())

def test_no_stance_defaults_upright_identical():
    s_old = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s_old, {**BASE})  # no stance key
    s_new = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s_new, {**BASE, "stance": "upright"})
    assert s_old.get_size() == (256, 256) and s_new.get_size() == (256, 256)
    assert _cov(s_old) == _cov(s_new), "upright stance must be byte-identical to no-stance"

def test_all_5_stances_render():
    for stance in ("upright", "quadruped", "mounted", "flying", "floating"):
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        draw_chibi_descriptor(s, {**BASE, "stance": stance})
        assert s.get_size() == (256, 256), f"{stance} size"
        assert _cov(s) > 0, f"{stance} blank"

def test_floating_has_no_legs_modifier():
    # floating should differ from upright (the modifier removes legs / adds hover)
    s_up = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_up, {**BASE, "stance": "upright"})
    s_fl = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_fl, {**BASE, "stance": "floating"})
    assert _cov(s_fl) != _cov(s_up), "floating modifier must change the sprite"

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("STANCE DISPATCH OK")

if __name__ == "__main__":
    run()
