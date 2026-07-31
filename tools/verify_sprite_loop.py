"""Headless test for the sprite loop (FAKE VLM, no network)."""
import os, sys, json, tempfile
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.build.sprite_loop import vlm_sprite_loop, load_cache, save_cache, RENDER_LOCK

D0 = {"archetype":"knight","weapon":"sword",
      "palette":{"primary":[10,10,10],"secondary":[0,0,0],"accent":[0,0,0]},
      "features":[],"build":"average","motif":"flame"}
D1 = {"archetype":"vastaya","weapon":"orb",
      "palette":{"primary":[255,255,255],"secondary":[200,0,0],"accent":[0,150,255]},
      "features":["horns"],"build":"slender","motif":"light"}

class FakeVLM:
    """describe -> D0; critique -> ok=False(match=4) round 0, ok=True(match=8) round 1."""
    def __init__(self): self.calls = 0
    def describe(self, ref, fallback): return D0
    def critique(self, ref, sprite, last_good_descriptor):
        self.calls += 1
        if self.calls == 1:
            return {"match": 4, "ok": False, "problems": ["bad"], "suggested_descriptor": D1}
        return {"match": 8, "ok": True, "problems": [], "suggested_descriptor": D1}

def test_loop_stops_on_ok():
    v = FakeVLM()
    # ref/sprite paths are never read by the fake; pass real splash so renderer runs
    ref = "assets/characters/Ahri/skins/0.jpg"
    best, hist = vlm_sprite_loop("Ahri", 0, ref, vlm=v, max_iters=10, fallback=D0)
    assert len(hist) == 2, f"expected 2 rounds, got {len(hist)}"
    assert hist[0]["match"] == 4 and hist[0]["ok"] is False
    assert hist[1]["match"] == 8 and hist[1]["ok"] is True
    assert best["archetype"] == "vastaya"  # the ok round's descriptor

def test_loop_keeps_best_when_never_ok():
    class NeverOK:
        def describe(self, ref, fallback): return D0
        def critique(self, ref, sprite, last):
            return {"match": 3, "ok": False, "problems": [], "suggested_descriptor": D1}
    best, hist = vlm_sprite_loop("Ahri", 0, "assets/characters/Ahri/skins/0.jpg",
                                 vlm=NeverOK(), max_iters=3, fallback=D0)
    assert len(hist) == 3            # hit the cap
    assert best["archetype"] == "knight"  # round 0 (match 3) >= others (match 3) -> first wins via stable max

def test_loop_respects_max_iters():
    class AlwaysCritique:
        def describe(self, ref, fallback): return D0
        def critique(self, ref, sprite, last):
            return {"match": 1, "ok": False, "problems": [], "suggested_descriptor": D1}
    _, hist = vlm_sprite_loop("Ahri", 0, "assets/characters/Ahri/skins/0.jpg",
                              vlm=AlwaysCritique(), max_iters=4, fallback=D0)
    assert len(hist) == 4

def test_cache_roundtrip():
    d = tempfile.mkdtemp()
    assert load_cache(d) == {}
    save_cache(d, {"0": {"descriptor": D0, "match": 7, "iters": 2, "ok": True}})
    c = load_cache(d)
    assert "0" in c and c["0"]["match"] == 7 and c["0"]["ok"] is True

def test_render_lock_exists():
    import threading
    assert isinstance(RENDER_LOCK, type(threading.Lock()))

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("SPRITE LOOP OK")

if __name__ == "__main__":
    run()
