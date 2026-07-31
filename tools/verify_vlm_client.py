"""Headless test for the VLM client (no network — HTTP is monkeypatched)."""
import os, sys, json, io
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.build.vlm_client import VLMClient, VOCAB

class _FakeResp:
    def __init__(self, payload): self._buf = io.BytesIO(json.dumps(payload).encode())
    def read(self): return self._buf.read()
    def __enter__(self): return self
    def __exit__(self, *a): return False

def test_vocab_complete():
    for k in ("archetype", "weapon", "features", "build", "motif"):
        assert k in VOCAB and len(VOCAB[k]) > 0
    assert "primary" in VOCAB  # palette keys listed under "primary"? -> see below

def test_describe_parses_and_validates():
    cl = VLMClient()
    fenced = '```json\n{"archetype":"vastaya","weapon":"orb","palette":{"primary":[255,0,0],"secondary":[0,0,255],"accent":[0,255,0]},"features":["horns"],"build":"slender","motif":"wind"}\n```'
    cl._post = lambda body: _FakeResp({"choices":[{"message":{"content":fenced}}]})
    d = cl.describe("assets/characters/Ahri/skins/0.jpg", fallback={"archetype":"knight","weapon":"sword","palette":{"primary":[0,0,0],"secondary":[0,0,0],"accent":[0,0,0]},"features":[],"build":"average","motif":"flame"})
    assert d["archetype"] == "vastaya" and d["weapon"] == "orb"
    assert d["palette"]["primary"] == [255, 0, 0]
    assert d["features"] == ["horns"] and d["build"] == "slender" and d["motif"] == "wind"

def test_describe_clamps_invalid():
    cl = VLMClient()
    bad = '{"archetype":"DRAGON","weapon":"lasgun","palette":{"primary":[999,-5,0],"secondary":[0,0,0],"accent":[0,0,0]},"features":["jetpack","cape","horns","wings"],"build":"OBESE","motif":"plasma"}'
    cl._post = lambda body: _FakeResp({"choices":[{"message":{"content":bad}}]})
    fb = {"archetype":"knight","weapon":"sword","palette":{"primary":[0,0,0],"secondary":[0,0,0],"accent":[0,0,0]},"features":[],"build":"average","motif":"flame"}
    d = cl.describe("x.jpg", fallback=fb)
    assert d["archetype"] in VOCAB["archetype"]      # clamped to a valid archetype
    assert d["weapon"] in VOCAB["weapon"]            # clamped to a valid weapon
    assert 0 <= d["palette"]["primary"][0] <= 255 and 0 <= d["palette"]["primary"][1] <= 255
    assert len(d["features"]) <= 3                   # capped at 3
    assert all(f in VOCAB["features"] for f in d["features"])
    assert d["build"] in VOCAB["build"] and d["motif"] in VOCAB["motif"]

def test_describe_fallback_on_garbage():
    cl = VLMClient()
    cl._post = lambda body: _FakeResp({"choices":[{"message":{"content":"not json at all"}}]})
    fb = {"archetype":"knight","weapon":"sword","palette":{"primary":[1,2,3],"secondary":[0,0,0],"accent":[0,0,0]},"features":[],"build":"average","motif":"flame"}
    d = cl.describe("x.jpg", fallback=fb)
    assert d == fb  # garbage -> fallback descriptor, no raise

def test_critique_parses():
    cl = VLMClient()
    j = '{"match":8,"ok":true,"problems":[],"suggested_descriptor":{"archetype":"vastaya","weapon":"orb","palette":{"primary":[255,255,255],"secondary":[200,0,0],"accent":[0,150,255]},"features":[],"build":"slender","motif":"light"}}'
    cl._post = lambda body: _FakeResp({"choices":[{"message":{"content":j}}]})
    c = cl.critique("ref.jpg", "sprite.png", last_good_descriptor={"archetype":"knight","weapon":"sword","palette":{"primary":[0,0,0],"secondary":[0,0,0],"accent":[0,0,0]},"features":[],"build":"average","motif":"flame"})
    assert c["match"] == 8 and c["ok"] is True and c["problems"] == []
    assert c["suggested_descriptor"]["archetype"] == "vastaya"

def test_critique_fallback():
    cl = VLMClient()
    cl._post = lambda body: _FakeResp({"choices":[{"message":{"content":"::garbage::"}}]})
    last = {"archetype":"knight","weapon":"sword","palette":{"primary":[0,0,0],"secondary":[0,0,0],"accent":[0,0,0]},"features":[],"build":"average","motif":"flame"}
    c = cl.critique("ref.jpg", "sprite.png", last_good_descriptor=last)
    assert c["ok"] is False and c["match"] == 0
    assert c["suggested_descriptor"] == last  # falls back to last good

def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("VLM CLIENT OK")

if __name__ == "__main__":
    run()
