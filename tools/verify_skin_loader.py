"""Headless test: load_char_sprite picks the per-skin sprite or falls back."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.entities import combatant

def test_skin_sprite_used_when_present(monkeypatched_paths=None):
    # create a throwaway champ dir with a sprites/14.png
    from src.data.tuning import ASSET_DIR
    base = os.path.join(ASSET_DIR, "characters", "Ahri")
    os.makedirs(os.path.join(base, "sprites"), exist_ok=True)
    sp = os.path.join(base, "sprites", "14.png")
    if not os.path.exists(sp):
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 0, 255, 255), (128, 128), 60)
        pygame.image.save(s, sp)
    # capture which relative path load_image is called with
    seen = []
    orig = combatant.load_image
    def spy(rel, scale=None):
        seen.append(rel); return orig(rel, scale)
    combatant.load_image = spy
    try:
        surf = combatant.load_char_sprite("Ahri", 96, skin_idx=14)
    finally:
        combatant.load_image = orig
    assert surf.get_size() == (96, 96)
    assert any("sprites/14.png" in p for p in seen), f"per-skin path not used: {seen}"

def test_falls_back_to_sprite_png_when_absent():
    from src.data.tuning import ASSET_DIR
    sp = os.path.join(ASSET_DIR, "characters", "Ahri", "sprites", "999.png")
    assert not os.path.exists(sp)
    seen = []
    orig = combatant.load_image
    combatant.load_image = lambda rel, scale=None: (seen.append(rel), orig(rel, scale))[1]
    try:
        combatant.load_char_sprite("Ahri", 96, skin_idx=999)
    finally:
        combatant.load_image = orig
    assert any("sprite.png" in p for p in seen), f"fallback not used: {seen}"

def test_default_skin_zero_uses_sprite_png():
    seen = []
    orig = combatant.load_image
    combatant.load_image = lambda rel, scale=None: (seen.append(rel), orig(rel, scale))[1]
    try:
        combatant.load_char_sprite("Ahri", 96)
    finally:
        combatant.load_image = orig
    assert any(p.endswith("sprite.png") for p in seen)

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("SKIN LOADER OK")

if __name__ == "__main__":
    run()
