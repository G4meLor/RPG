"""The HONEST canonical gate (Task 9).

Reads every champ's `descriptors.json` (the baked descriptor + canonical_match
from the sprite loop) + the champ's canonical ORIGIN identity (built via a
text-only VLM call `VLMClient.canon_identity(champ)`) + the baked sprite PNG
(loaded via pygame.image.load, in-process — NEVER the Read tool) and calls
`VLMClient.canon_gate(sprite, champ, canon)` to judge the sprite against the
champ's canonical ORIGIN (NO splash). Aggregates per-champ canonical_match +
recognizable + stance_captured across the roster and prints:

    mean canonical_match: X.XX / 10
    recognizable:         N/M (PP%)
    stance_captured:      N/M (PP%)
    CANON GATE OK   (or FAIL)

Exits 0 if mean >= 6 AND recognizable >= 70% AND stance_captured >= 90%,
else 1. The thresholds are the brief's acceptance criteria for the canon gate.

Self-test: `SDL_VIDEODRIVER=dummy python3 tools/verify_canon_gate.py` with no
args runs the self-test path (FakeVLM monkeypatches `canon_identity` +
`canon_gate` so no network is touched) -> prints `CANON GATE OK` and exits 0.
Run with `--real` to do a real network run over the roster (slow, one VLM call
per champ for canon_identity + one for canon_gate).

NEVER use the Read tool on a PNG/JPG — this script loads PNGs via
pygame.image.load (in-process) for the VLM. Safe under SDL_VIDEODRIVER=dummy.

Run:
    SDL_VIDEODRIVER=dummy python3 tools/verify_canon_gate.py           # self-test
    SDL_VIDEODRIVER=dummy python3 tools/verify_canon_gate.py --real    # network
"""
import os, sys, json, argparse
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.build.champions import CHAMPIONS_DB
from src.build.vlm_client import VLMClient, VOCAB
from src.data.tuning import ASSET_DIR

# Gate thresholds (brief acceptance criteria).
MEAN_FLOOR     = 6.0
RECOGNIZABLE_PCT = 70.0
STANCE_PCT      = 90.0


def _sprite_path(champ_id, skin_idx=0):
    """The baked sprite PNG for (champ, skin). Prefers sprites/{idx}.png
    (Phase 3 per-skin layout); falls back to sprite.png (index 0 back-compat)."""
    base = os.path.join(ASSET_DIR, "characters", champ_id)
    p = os.path.join(base, "sprites", f"{skin_idx}.png")
    if os.path.exists(p):
        return p
    if skin_idx == 0:
        p2 = os.path.join(base, "sprite.png")
        if os.path.exists(p2):
            return p2
    return p  # return the preferred path even if missing (caller checks)


def _load_descriptor(char_dir, skin_idx=0):
    """Read the baked descriptor + canonical_match from descriptors.json.
    Returns (descriptor, canonical_match_cached) or (None, None) if absent."""
    p = os.path.join(char_dir, "descriptors.json")
    if not os.path.exists(p):
        return None, None
    try:
        with open(p) as f:
            cache = json.load(f)
    except Exception:
        return None, None
    entry = cache.get(str(skin_idx))
    if not entry:
        return None, None
    return entry.get("descriptor"), entry.get("canonical_match")


def _enumerate_champs(limit=None, only=None):
    """Pick the champ subset to gate. `only` = set of ids; `limit` = cap."""
    out = []
    for c in CHAMPIONS_DB:
        if only and c["id"] not in only:
            continue
        out.append(c)
        if limit and len(out) >= limit:
            break
    return out


def _run_gate(champs, vlm, build_canon):
    """Run canon_gate per champ. `build_canon(champ)` -> canon dict (text-only
    VLM call in real mode; a fake in self-test). Returns list of per-champ
    result dicts: {id, canon, gate, sprite_path, error}."""
    results = []
    for c in champs:
        cid = c["id"]
        char_dir = os.path.join(ASSET_DIR, "characters", cid)
        sprite = _sprite_path(cid, 0)
        if not os.path.exists(sprite):
            results.append({"id": cid, "error": "missing sprite"})
            continue
        try:
            canon = build_canon(c)
        except Exception as e:
            results.append({"id": cid, "error": f"canon_identity: {e}"})
            continue
        try:
            g = vlm.canon_gate(sprite, champ=c, canon=canon)
        except Exception as e:
            results.append({"id": cid, "error": f"canon_gate: {e}", "canon": canon})
            continue
        results.append({"id": cid, "canon": canon, "gate": g, "sprite_path": sprite})
    return results


def _aggregate(results):
    """Compute mean canonical_match, recognizable %, stance_captured %."""
    ok = [r for r in results if "gate" in r]
    n = len(ok)
    if n == 0:
        return {"n": 0, "mean": 0.0, "recognizable_pct": 0.0, "stance_pct": 0.0}
    matches = [r["gate"]["canonical_match"] for r in ok]
    rec = sum(1 for r in ok if r["gate"].get("recognizable"))
    stance = sum(1 for r in ok if r["gate"].get("stance_captured"))
    return {
        "n": n,
        "mean": round(sum(matches) / n, 2),
        "recognizable_pct": round(100.0 * rec / n, 1),
        "stance_pct": round(100.0 * stance / n, 1),
        "n_recognizable": rec,
        "n_stance": stance,
    }


def _print_report(agg, results, label="CANON GATE"):
    """Print the gate report + the per-champ worst 10 + verdict."""
    n = agg["n"]
    print(f"\n=== {label} ===")
    print(f"champs judged:        {n}")
    print(f"mean canonical_match: {agg['mean']} / 10")
    print(f"recognizable:         {agg.get('n_recognizable', 0)}/{n} "
          f"({agg['recognizable_pct']}%)")
    print(f"stance_captured:      {agg.get('n_stance', 0)}/{n} "
          f"({agg['stance_pct']}%)")
    errs = [r for r in results if "error" in r]
    if errs:
        print(f"errors:               {len(errs)}")
        for r in errs[:10]:
            print(f"  {r['id']:16s} {r['error']}")
    # worst 10 (lowest canonical_match) so failures are visible
    ok = [r for r in results if "gate" in r]
    if ok:
        worst = sorted(ok, key=lambda r: r["gate"]["canonical_match"])[:10]
        print("\nworst 10 (canonical_match):")
        for r in worst:
            g = r["gate"]
            miss = ", ".join(g.get("features_missing", [])[:3]) or "(none)"
            print(f"  {g['canonical_match']:2d}/10  {r['id']:16s} "
                  f"stance_ok={g.get('stance_captured')} "
                  f"recog={g.get('recognizable')} missing=[{miss}]")
    verdict = (agg["mean"] >= MEAN_FLOOR and
               agg["recognizable_pct"] >= RECOGNIZABLE_PCT and
               agg["stance_pct"] >= STANCE_PCT)
    print(f"\nthresholds: mean>={MEAN_FLOOR} recognizable>={RECOGNIZABLE_PCT}% "
          f"stance>={STANCE_PCT}%")
    print(f"verdict: {'PASS' if verdict else 'FAIL'}")
    return verdict


# ---------------------------------------------------------------------------
# Self-test: FakeVLM monkeypatches canon_identity + canon_gate (no network).
# ---------------------------------------------------------------------------

class _FakeVLM:
    """Test double for VLMClient. canon_identity -> a hardcoded canon dict per
    champ id; canon_gate -> a deterministic score from the canon's stance. No
    network. The gate logic exercised is the real `_run_gate`/`_aggregate`/
    `_print_report`/`_sprite_path`/`_load_descriptor` code paths."""

    def __init__(self, mode="pass"):
        # mode='pass' -> all gates return canonical_match=8, recognizable=True,
        # stance_captured=True (passes all thresholds). mode='fail' -> all 3.
        self.mode = mode
        self.calls = 0

    def canon_identity(self, champ, max_tokens=300):
        # Build a plausible canon dict for the champ (stance from a small
        # lookup so the gate's stance_captured path is exercised honestly).
        cid = champ.get("id", "?")
        stance = _FAKE_STANCE.get(cid, "upright")
        return {
            "stance": stance,
            "body_shape": "fake-body",
            "signature_features": ["fake_feature_1", "fake_feature_2"],
            "primary_colors": ["red", "blue"],
            "weapon": "sword",
        }

    def canon_gate(self, sprite_path, champ=None, canon=None, max_tokens=400):
        self.calls += 1
        if self.mode == "pass":
            return {
                "canonical_match": 8, "stance_captured": True,
                "body_shape_score": 7, "features_captured": ["fake_feature_1"],
                "features_missing": [], "colors_captured": True,
                "recognizable": True, "verdict": "pass",
            }
        # fail mode: low score, not recognizable, stance not captured
        return {
            "canonical_match": 2, "stance_captured": False,
            "body_shape_score": 1, "features_captured": [],
            "features_missing": ["fake_feature_1", "fake_feature_2"],
            "colors_captured": False, "recognizable": False, "verdict": "fail",
        }


# A tiny stance lookup so the self-test's canon_identity returns a realistic
# stance per champ (Anivia=flying, Alistar=quadruped, Hecarim=mounted,
# AurelionSol=floating, most humanoids=upright). Falls back to upright.
_FAKE_STANCE = {
    "Anivia": "flying", "Alistar": "quadruped", "Hecarim": "mounted",
    "AurelionSol": "floating", "Velkoz": "floating", "Malzahar": "upright",
    "Ahri": "upright", "Aatrox": "upright", "Ashe": "upright",
}


def _self_test():
    """Self-test: FakeVLM (no network) over a 6-champ slice. Asserts the
    aggregation + threshold logic + exit code are correct for both a passing
    and a failing fake gate. Prints `CANON GATE OK` on success."""
    print("== verify_canon_gate self-test (FakeVLM, no network) ==")
    # Pick 6 champs that actually have baked sprites on disk so _sprite_path
    # returns a real file (the FakeVLM never reads it, but the gate code path
    # checks os.path.exists).
    candidates = []
    for c in CHAMPIONS_DB:
        if os.path.exists(_sprite_path(c["id"], 0)):
            candidates.append(c)
        if len(candidates) >= 6:
            break
    assert len(candidates) >= 1, "no baked sprites found for self-test"
    champs = candidates

    # --- PASS path: fake gate returns canonical_match=8, recognizable, stance
    # for every champ -> mean=8 >= 6, recognizable 100% >= 70%, stance 100% >=
    # 90% -> verdict PASS.
    vlm = _FakeVLM(mode="pass")
    results = _run_gate(champs, vlm, build_canon=vlm.canon_identity)
    assert all("gate" in r for r in results), \
        f"self-test pass path had errors: {[r for r in results if 'error' in r]}"
    agg = _aggregate(results)
    assert agg["mean"] == 8.0, f"expected mean 8.0, got {agg['mean']}"
    assert agg["recognizable_pct"] == 100.0, agg
    assert agg["stance_pct"] == 100.0, agg
    verdict = _print_report(agg, results, label="SELF-TEST PASS PATH")
    assert verdict is True, "pass path should pass thresholds"
    print("  pass path: thresholds met (mean=8, rec=100%, stance=100%)")

    # --- FAIL path: fake gate returns canonical_match=2, not recognizable,
    # stance not captured -> mean=2 < 6, recognizable 0% < 70%, stance 0% < 90%
    # -> verdict FAIL.
    vlm2 = _FakeVLM(mode="fail")
    results2 = _run_gate(champs, vlm2, build_canon=vlm2.canon_identity)
    assert all("gate" in r for r in results2), "fail path had errors"
    agg2 = _aggregate(results2)
    assert agg2["mean"] == 2.0, f"expected mean 2.0, got {agg2['mean']}"
    assert agg2["recognizable_pct"] == 0.0, agg2
    assert agg2["stance_pct"] == 0.0, agg2
    verdict2 = _print_report(agg2, results2, label="SELF-TEST FAIL PATH")
    assert verdict2 is False, "fail path should fail thresholds"
    print("  fail path: thresholds missed (mean=2, rec=0%, stance=0%)")

    # --- canon_identity stance validation: an invalid stance clamps to upright.
    class _BadCanonVLM(_FakeVLM):
        def canon_identity(self, champ, max_tokens=300):
            return {"stance": "HOVER", "body_shape": "x",
                    "signature_features": [], "primary_colors": [],
                    "weapon": ""}
    bad = _BadCanonVLM(mode="pass")
    ci = bad.canon_identity(champs[0])
    # The real VLMClient.canon_identity clamps invalid stance to "upright"; the
    # FakeVLM._BadCanonVLM override above bypasses that clamping (it returns the
    # raw dict). So we instead exercise the REAL clamping path by calling the
    # real VLMClient.canon_identity with a monkeypatched _chat that returns an
    # invalid stance, to prove the clamp lives in VLMClient.canon_identity.
    real = VLMClient()
    real._post = lambda body: _FakeResp({
        "choices": [{"message": {"content":
            '{"stance":"HOVER","body_shape":"x","signature_features":[],'
            '"primary_colors":[],"weapon":""}'}}]})
    ci_real = real.canon_identity(champs[0])
    assert ci_real["stance"] == "upright", \
        f"invalid stance should clamp to upright, got {ci_real['stance']}"
    print("  canon_identity clamps invalid stance -> upright (real path)")

    # --- _sprite_path prefers sprites/{idx}.png over sprite.png
    sp = _sprite_path(champs[0]["id"], 0)
    assert sp.endswith(os.path.join("sprites", "0.png")), sp
    print(f"  _sprite_path prefers sprites/0.png: {sp}")

    # --- _load_descriptor reads descriptors.json
    desc, cm = _load_descriptor(os.path.join(ASSET_DIR, "characters",
                                             champs[0]["id"]), 0)
    assert desc is not None, "descriptors.json missing for self-test champ"
    assert "archetype" in desc, desc
    print(f"  _load_descriptor: archetype={desc['archetype']} "
          f"cached canonical_match={cm}")

    print("\nCANON GATE OK")
    return 0


class _FakeResp:
    """Minimal _FakeResp for the VLMClient._post monkeypatch (canon_identity
    clamping test). Mirrors tools/verify_vlm_client._FakeResp."""
    def __init__(self, payload):
        import io
        self._buf = io.BytesIO(json.dumps(payload).encode())
    def read(self): return self._buf.read()
    def __enter__(self): return self
    def __exit__(self, *a): return False


def _real_run(limit=None, only=None):
    """Real network run: build canon_identity per champ (text-only VLM call) +
    call canon_gate on the baked sprite. Slow (2 VLM calls/champ)."""
    champs = _enumerate_champs(limit=limit, only=only)
    print(f"== verify_canon_gate REAL run: {len(champs)} champs (network) ==")
    vlm = VLMClient()

    def build_canon(c):
        return vlm.canon_identity(c)

    results = _run_gate(champs, vlm, build_canon=build_canon)
    agg = _aggregate(results)
    verdict = _print_report(agg, results, label="CANON GATE (REAL)")
    # Persist raw results for offline analysis.
    out = "/tmp/canon_gate_results.json"
    try:
        with open(out, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nraw -> {out}")
    except Exception as e:
        print(f"\n(warn: could not write {out}: {e})")
    return 0 if verdict else 1


def main():
    ap = argparse.ArgumentParser(description="Honest canonical gate (Task 9)")
    ap.add_argument("--real", action="store_true",
                    help="real network run (default: self-test with FakeVLM)")
    ap.add_argument("--limit", type=int, default=None,
                    help="cap champs judged (real mode only)")
    ap.add_argument("--champs", default="",
                    help="comma-separated champ ids (real mode only)")
    args = ap.parse_args()
    if args.real:
        only = set(s.strip() for s in args.champs.split(",") if s.strip()) or None
        return _real_run(limit=args.limit, only=only)
    return _self_test()


if __name__ == "__main__":
    sys.exit(main())
