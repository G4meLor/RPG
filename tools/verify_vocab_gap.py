"""Headless test for the vocab gap-analysis (FakeVLM, no network)."""
import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.build.vocab_gap import analyze, top_n_gap

class FakeGapVLM:
    """free-form feature/weapon per champ, rotated by id."""
    def freeform_features(self, ref_path):
        # ref_path = .../characters/<cid>/skins/0.jpg
        # dirname -> .../characters/<cid>/skins ; dirname again -> .../characters/<cid>
        # basename -> <cid>
        cid = os.path.basename(os.path.dirname(os.path.dirname(ref_path)))
        if cid == "Ahri":
            return {"features": ["fox_tails", "animal_ears"], "weapons": ["orb"]}
        if cid == "Garen":
            return {"features": ["cape", "shield"], "weapons": ["sword", "shield"]}
        return {"features": ["claws"], "weapons": ["fists"]}

def test_analyze_aggregates():
    champs = [{"id": "Ahri"}, {"id": "Garen"}, {"id": "Volibear"}]
    rep = analyze(champs, sample_n=3, vlm_factory=lambda: FakeGapVLM())
    assert rep["features"]["fox_tails"] == 1
    assert rep["features"]["cape"] == 1
    assert rep["weapons"]["sword"] == 1

def test_top_n_gap_excludes_known():
    rep = {"features": {"fox_tails": 1, "cape": 1, "animal_ears": 1, "claws": 1},
           "weapons": {"orb": 1, "sword": 1, "shield": 1, "fists": 1}}
    g = top_n_gap(rep,
                  renderer_features=["cape", "hood", "horns", "wings", "mask", "halo", "spikes", "crown"],
                  renderer_weapons=["sword", "bow", "staff", "orb", "scythe", "spear", "gauntlet", "dagger", "axe", "gun", "shield", "whip", "fists", "none"],
                  n=5)
    assert "fox_tails" in g["features"] and "cape" not in g["features"]
    assert "animal_ears" in g["features"] and "claws" in g["features"]
    # all weapons already known -> empty gap
    assert g["weapons"] == []

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("VOCAB GAP OK")

if __name__ == "__main__":
    run()
