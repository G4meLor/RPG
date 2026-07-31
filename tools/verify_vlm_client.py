"""Headless test for the VLM client (no network — HTTP is monkeypatched).

Task 7: canon-grounded, stance-aware describe/critique.
- describe(ref, fallback, champ) -> descriptor WITH stance (validated)
- critique(ref, sprite, last_good, champ) -> {canonical_match, stance_captured,
  body_shape_score, features_missing, colors_captured, recognizable,
  suggested_descriptor}
- _champ_context(champ) builds the canonical-identity context text.
"""
import os, sys, json, io
os.environ["SDL_VIDEODRIVER"] = "dummy"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.build.vlm_client import VLMClient, VOCAB, _champ_context

# A representative champ dict (shaped like CHAMPIONS_DB entries) used across
# the describe/critique tests so the champ-context path is exercised.
_AHRI = {
    "id": "Ahri", "name": "Ahri", "title": "the Nine-Tailed Fox",
    "faction": "ionia", "role": "hunt",
    "ability_names": {"Q": "Orb of Deception", "W": "Fox-Fire",
                      "E": "Charm", "R": "Spirit Rush"},
    "lore": {"bio": "Innately connected to the magic of the spirit realm, Ahri "
                    "is a fox-like vastaya who can manipulate her prey's emotions.",
             "quote": "Don't worry, I'll be gentle.",
             "personality": "cold"},
}

# Canonical fallback descriptor used across tests (includes stance so the
# fallback path is stance-complete).
_FB = {
    "stance": "upright", "archetype": "knight", "weapon": "sword",
    "palette": {"primary": [0, 0, 0], "secondary": [0, 0, 0], "accent": [0, 0, 0]},
    "features": [], "build": "average", "motif": "flame",
}


class _FakeResp:
    def __init__(self, payload): self._buf = io.BytesIO(json.dumps(payload).encode())
    def read(self): return self._buf.read()
    def __enter__(self): return self
    def __exit__(self, *a): return False


def test_vocab_complete():
    for k in ("stance", "archetype", "weapon", "features", "build", "motif"):
        assert k in VOCAB and len(VOCAB[k]) > 0
    assert "primary" in VOCAB  # palette keys listed under "primary"? -> see below


def test_champ_context_built():
    ctx = _champ_context(_AHRI)
    assert "Ahri" in ctx and "Nine-Tailed Fox" in ctx
    assert "ionia" in ctx and "hunt" in ctx
    assert "Orb of Deception" in ctx and "Spirit Rush" in ctx
    assert "vastaya" in ctx or "fox" in ctx.lower()  # bio mentions fox-like
    # missing champ -> '' (no raise)
    assert _champ_context(None) == ""
    assert _champ_context({}) == ""


def test_describe_parses_and_validates():
    cl = VLMClient()
    fenced = ('```json\n{"stance":"upright","archetype":"vastaya","weapon":"orb",'
              '"palette":{"primary":[255,0,0],"secondary":[0,0,255],"accent":[0,255,0]},'
              '"features":["fox_tails"],"build":"slender","motif":"wind"}\n```')
    cl._post = lambda body: _FakeResp({"choices": [{"message": {"content": fenced}}]})
    d = cl.describe("assets/characters/Ahri/skins/0.jpg", fallback=_FB, champ=_AHRI)
    assert d["stance"] == "upright"
    assert d["archetype"] == "vastaya" and d["weapon"] == "orb"
    assert d["palette"]["primary"] == [255, 0, 0]
    assert d["features"] == ["fox_tails"] and d["build"] == "slender" and d["motif"] == "wind"


def test_describe_clamps_invalid():
    cl = VLMClient()
    bad = ('{"stance":"HOVER","archetype":"DRAGON","weapon":"lasgun",'
           '"palette":{"primary":[999,-5,0],"secondary":[0,0,0],"accent":[0,0,0]},'
           '"features":["jetpack","cape","horns","wings"],"build":"OBESE","motif":"plasma"}')
    cl._post = lambda body: _FakeResp({"choices": [{"message": {"content": bad}}]})
    d = cl.describe("x.jpg", fallback=_FB, champ=_AHRI)
    assert d["stance"] in VOCAB["stance"]                # clamped to a valid stance
    assert d["archetype"] in VOCAB["archetype"]          # clamped to a valid archetype
    assert d["weapon"] in VOCAB["weapon"]                # clamped to a valid weapon
    assert 0 <= d["palette"]["primary"][0] <= 255 and 0 <= d["palette"]["primary"][1] <= 255
    assert len(d["features"]) <= 3                       # capped at 3
    assert all(f in VOCAB["features"] for f in d["features"])
    assert d["build"] in VOCAB["build"] and d["motif"] in VOCAB["motif"]


def test_describe_fallback_on_garbage():
    cl = VLMClient()
    cl._post = lambda body: _FakeResp({"choices": [{"message": {"content": "not json at all"}}]})
    fb = dict(_FB, palette={"primary": [1, 2, 3], "secondary": [0, 0, 0], "accent": [0, 0, 0]})
    d = cl.describe("x.jpg", fallback=fb, champ=_AHRI)
    assert d == fb  # garbage -> fallback descriptor, no raise


def test_describe_fallback_preserves_stance():
    """When the VLM returns garbage, the fallback's stance is preserved
    (the fallback is the champ's baked descriptor, which has a stance)."""
    cl = VLMClient()
    cl._post = lambda body: _FakeResp({"choices": [{"message": {"content": "::garbage::"}}]})
    fb = dict(_FB, stance="quadruped")
    d = cl.describe("x.jpg", fallback=fb, champ=_AHRI)
    assert d == fb and d["stance"] == "quadruped"


def test_describe_no_champ_still_works():
    """describe with champ=None must still function (back-compat for callers
    that don't yet pass the champ context)."""
    cl = VLMClient()
    ok = ('{"stance":"upright","archetype":"mage","weapon":"staff",'
          '"palette":{"primary":[10,20,30],"secondary":[0,0,0],"accent":[0,0,0]},'
          '"features":[],"build":"average","motif":"ice"}')
    cl._post = lambda body: _FakeResp({"choices": [{"message": {"content": ok}}]})
    d = cl.describe("x.jpg", fallback=_FB, champ=None)
    assert d["stance"] == "upright" and d["archetype"] == "mage"


def test_critique_parses():
    cl = VLMClient()
    j = ('{"canonical_match":8,"stance_captured":true,"body_shape_score":7,'
         '"features_missing":[],"colors_captured":true,"recognizable":true,'
         '"suggested_descriptor":{"stance":"upright","archetype":"vastaya",'
         '"weapon":"orb","palette":{"primary":[255,255,255],"secondary":[200,0,0],'
         '"accent":[0,150,255]},"features":["fox_tails"],"build":"slender",'
         '"motif":"light"}}')
    cl._post = lambda body: _FakeResp({"choices": [{"message": {"content": j}}]})
    c = cl.critique("ref.jpg", "sprite.png", last_good_descriptor=_FB, champ=_AHRI)
    assert c["canonical_match"] == 8
    assert c["stance_captured"] is True
    assert c["body_shape_score"] == 7
    assert c["features_missing"] == []
    assert c["colors_captured"] is True
    assert c["recognizable"] is True
    assert c["suggested_descriptor"]["archetype"] == "vastaya"
    assert c["suggested_descriptor"]["stance"] == "upright"


def test_critique_clamps_canonical_match():
    cl = VLMClient()
    j = ('{"canonical_match":999,"stance_captured":"yes","body_shape_score":-3,'
         '"features_missing":"oops","colors_captured":1,"recognizable":"y",'
         '"suggested_descriptor":{}}')
    cl._post = lambda body: _FakeResp({"choices": [{"message": {"content": j}}]})
    c = cl.critique("ref.jpg", "sprite.png", last_good_descriptor=_FB, champ=_AHRI)
    assert c["canonical_match"] == 10          # clamped to 0-10
    assert c["body_shape_score"] == 0          # clamped to 0-10
    assert c["stance_captured"] is True        # truthy -> bool
    assert c["colors_captured"] is True
    assert c["recognizable"] is True
    # features_missing coerced to list (a string is iterable -> list of chars,
    # but the contract is "list"; just assert it's a list)
    assert isinstance(c["features_missing"], list)
    # empty suggested_descriptor -> validated to fallback (last_good)
    assert c["suggested_descriptor"]["archetype"] == _FB["archetype"]


def test_critique_fallback():
    cl = VLMClient()
    cl._post = lambda body: _FakeResp({"choices": [{"message": {"content": "::garbage::"}}]})
    last = dict(_FB, archetype="vastaya", weapon="orb")
    c = cl.critique("ref.jpg", "sprite.png", last_good_descriptor=last, champ=_AHRI)
    assert c["canonical_match"] == 0
    assert c["stance_captured"] is False
    assert c["recognizable"] is False
    assert c["suggested_descriptor"] == last   # falls back to last good


def test_critique_no_champ_still_works():
    """critique with champ=None must still function (back-compat)."""
    cl = VLMClient()
    j = ('{"canonical_match":6,"stance_captured":true,"body_shape_score":6,'
         '"features_missing":[],"colors_captured":true,"recognizable":true,'
         '"suggested_descriptor":{"stance":"upright","archetype":"knight",'
         '"weapon":"sword","palette":{"primary":[0,0,0],"secondary":[0,0,0],'
         '"accent":[0,0,0]},"features":[],"build":"average","motif":"flame"}}')
    cl._post = lambda body: _FakeResp({"choices": [{"message": {"content": j}}]})
    c = cl.critique("ref.jpg", "sprite.png", last_good_descriptor=_FB, champ=None)
    assert c["canonical_match"] == 6 and c["recognizable"] is True


def run():
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print(f"  pass {name}")
    print("VLM CLIENT OK")

if __name__ == "__main__":
    run()
