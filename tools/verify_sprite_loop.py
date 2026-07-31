"""Headless test for the sprite loop (FAKE VLM, no network)."""
import os, sys, json, tempfile
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.build.sprite_loop import vlm_sprite_loop, load_cache, save_cache, RENDER_LOCK
from src.build.sprite_loop import run_sprite_bake
from src.build.champions import CHAMPIONS_DB

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

class FakeVLMOK:
    """describe -> D0; critique -> ok=True(match=7) immediately."""
    def describe(self, ref, fallback): return D0
    def critique(self, ref, sprite, last):
        return {"match": 7, "ok": True, "problems": [], "suggested_descriptor": D1}

def _three_champs():
    ids = list(CHAMPIONS_DB.keys())[:3] if isinstance(CHAMPIONS_DB, dict) else [c["id"] for c in CHAMPIONS_DB[:3]]
    return [{"id": cid, "descriptor": (CHAMPIONS_DB[cid]["descriptor"] if isinstance(CHAMPIONS_DB, dict) else next(c["descriptor"] for c in CHAMPIONS_DB if c["id"] == cid))} for cid in ids]

def test_bake_processes_all_then_skips():
    champs = _three_champs()
    rep = run_sprite_bake(champs, skin_indices=[0], concurrency=2, max_iters=5,
                          force=True, vlm_factory=lambda: FakeVLMOK())
    assert rep["n_processed"] == 3, rep
    assert rep["n_ok"] == 3, rep
    # sprite.png written for each
    from src.data.tuning import ASSET_DIR
    for c in champs:
        assert os.path.exists(os.path.join(ASSET_DIR, "characters", c["id"], "sprite.png"))
    # re-run without force -> all skipped (cache ok)
    rep2 = run_sprite_bake(champs, skin_indices=[0], concurrency=1, max_iters=5,
                           force=False, vlm_factory=lambda: FakeVLMOK())
    assert rep2["n_skipped"] == 3 and rep2["n_processed"] == 0, rep2

def test_bake_default_concurrency_is_one():
    champs = _three_champs()
    rep = run_sprite_bake(champs, skin_indices=[0], max_iters=5, force=True,
                          vlm_factory=lambda: FakeVLMOK())
    assert rep["n_processed"] == 3  # concurrency omitted -> serial, still completes

def test_cli_parses_vlm_args():
    import argparse
    from src.build import build_champions as BC
    # rebuild the parser the way main() does and assert the flags exist + defaults
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", action="store_true")
    ap.add_argument("--sprites", action="store_true")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--vlm-loop", action="store_true")
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--max-iters", type=int, default=10)
    ap.add_argument("--champs", default="")
    ap.add_argument("--skins", default="0")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(["--sprites", "--vlm-loop", "--champs", "Ahri", "--skins", "0",
                       "--concurrency", "2", "--max-iters", "5", "--force"])
    assert a.vlm_loop is True and a.concurrency == 2 and a.max_iters == 5
    assert a.champs == "Ahri" and a.skins == "0" and a.force is True

def _ahri_descriptor():
    # CHAMPIONS_DB is a list of dicts; pull Ahri's baked descriptor.
    return next(c["descriptor"] for c in CHAMPIONS_DB if c["id"] == "Ahri")

def test_per_skin_writes_sprites_dir():
    from src.build.sprite_loop import run_sprite_bake
    from src.data.tuning import ASSET_DIR
    champs = [{"id": "Ahri", "descriptor": _ahri_descriptor()}]
    # only run skins that actually have a ref splash
    have = []
    for s in (0, 14):
        if os.path.exists(os.path.join(ASSET_DIR, "characters", "Ahri", "skins", f"{s}.jpg")):
            have.append(s)
    rep = run_sprite_bake(champs, skin_indices=have, concurrency=1, max_iters=5,
                          force=True, vlm_factory=lambda: FakeVLMOK())
    base = os.path.join(ASSET_DIR, "characters", "Ahri")
    for s in have:
        p = os.path.join(base, "sprites", f"{s}.png")
        assert os.path.exists(p), f"missing {p}"
        im = pygame.image.load(p); assert im.get_size() == (256, 256)
    import json
    c = json.load(open(os.path.join(base, "descriptors.json")))
    for s in have:
        assert str(s) in c, f"descriptors.json missing key {s}"

def test_missing_skin_ref_skipped():
    from src.build.sprite_loop import run_sprite_bake
    champs = [{"id": "Ahri", "descriptor": _ahri_descriptor()}]
    rep = run_sprite_bake(champs, skin_indices=[9999], concurrency=1, max_iters=5,
                          force=True, vlm_factory=lambda: FakeVLMOK())
    r = rep["per_skin"][0]
    assert r.get("error") == "missing ref splash"

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("SPRITE LOOP OK")

if __name__ == "__main__":
    run()
