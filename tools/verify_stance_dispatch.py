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
    # the lower-leg region must have fewer opaque pixels than upright
    # (the eraser must actually clear pixels, not be a no-op blit)
    cx, cy = 128, 150
    w, h = 96, 120  # knight average build box
    lx0 = max(0, cx - int(w * 0.45)); lx1 = min(256, cx + int(w * 0.45))
    ly0 = max(0, cy + int(h * 0.32)); ly1 = min(256, ly0 + int(h * 0.18))
    up_a = pygame.surfarray.pixels_alpha(s_up); up_arr = up_a.__array__(); del up_a
    fl_a = pygame.surfarray.pixels_alpha(s_fl); fl_arr = fl_a.__array__(); del fl_a
    up_legs = int((up_arr[lx0:lx1, ly0:ly1] > 8).sum())
    fl_legs = int((fl_arr[lx0:lx1, ly0:ly1] > 8).sum())
    assert fl_legs < up_legs, f"floating lower-leg region must have fewer opaque pixels (fl={fl_legs}, up={up_legs})"

QUAD = {**BASE, "stance": "quadruped", "archetype": "quadruped"}

def test_quadruped_renders_and_differs_from_upright():
    s_q = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_q, QUAD)
    s_u = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_u, {**BASE, "stance": "upright"})
    assert s_q.get_size() == (256, 256) and _cov(s_q) > 0
    assert _cov(s_q) != _cov(s_u), "quadruped must differ from upright knight"

def test_quadruped_feature_mods_add_pixels():
    base = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(base, QUAD)
    base_c = _cov(base)
    for feat in ("shell", "stinger", "fur", "insect_carapace", "void_fins"):
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        draw_chibi_descriptor(s, {**QUAD, "features": [feat]})
        assert _cov(s) > base_c + 0.003, f"quadruped feature {feat} didn't add pixels"

def test_mounted_renders_rider_plus_mount():
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s, {**BASE, "stance": "mounted", "archetype": "knight", "mount_kind": "boar"})
    s_u = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_u, {**BASE, "stance": "upright"})
    assert s.get_size() == (256, 256) and _cov(s) > 0
    assert _cov(s) > _cov(s_u) + 0.01, "mounted (rider+mount) should have more coverage than upright alone"

def test_flying_bird_and_dragon_render_and_differ():
    s_b = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s_b, {**BASE, "stance": "flying", "archetype": "flying_bird"})
    s_d = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s_d, {**BASE, "stance": "flying", "archetype": "flying_dragon"})
    assert _cov(s_b) > 0 and _cov(s_d) > 0
    assert _cov(s_b) != _cov(s_d), "bird and dragon must differ"

def test_rock_giant_renders_and_differs():
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s, {**BASE, "stance": "upright", "archetype": "rock_giant"})
    s_k = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_k, {**BASE, "stance": "upright", "archetype": "knight"})
    assert s.get_size() == (256, 256) and _cov(s) > 0
    assert _cov(s) != _cov(s_k), "rock_giant must differ from knight"

def test_treant_renders_and_differs():
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s, {**BASE, "stance": "upright", "archetype": "treant"})
    s_k = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_k, {**BASE, "stance": "upright", "archetype": "knight"})
    assert s.get_size() == (256, 256) and _cov(s) > 0
    assert _cov(s) != _cov(s_k), "treant must differ from knight"

def test_blob_renders_and_differs():
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s, {**BASE, "stance": "upright", "archetype": "blob"})
    s_k = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_k, {**BASE, "stance": "upright", "archetype": "knight"})
    assert s.get_size() == (256, 256) and _cov(s) > 0
    assert _cov(s) != _cov(s_k), "blob must differ from knight"

def test_naga_renders_and_differs():
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s, {**BASE, "stance": "upright", "archetype": "naga"})
    s_k = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_k, {**BASE, "stance": "upright", "archetype": "knight"})
    assert s.get_size() == (256, 256) and _cov(s) > 0
    assert _cov(s) != _cov(s_k), "naga must differ from knight"

def test_scarecrow_renders_and_differs():
    s = pygame.Surface((256, 256), pygame.SRCALPHA)
    draw_chibi_descriptor(s, {**BASE, "stance": "upright", "archetype": "scarecrow"})
    s_k = pygame.Surface((256, 256), pygame.SRCALPHA); draw_chibi_descriptor(s_k, {**BASE, "stance": "upright", "archetype": "knight"})
    assert s.get_size() == (256, 256) and _cov(s) > 0
    assert _cov(s) != _cov(s_k), "scarecrow must differ from knight"

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("STANCE DISPATCH OK")

if __name__ == "__main__":
    run()
