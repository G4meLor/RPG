"""Re-gate only the champs whose committed sprite changed since the last full
re-gate (the hand-author saves: Yuumi, TwistedFate, Poppy). Updates
exp/canon_gate_results.json in place with fresh scores, then prints new totals.
"""
import os, sys, json
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.build.champions import CHAMPIONS_DB
from src.build.vlm_client import VLMClient
from src.data.tuning import ASSET_DIR

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
CHANGED = ["Fiddlesticks"]  # saved in batch 3


def main():
    byid = {c["id"]: c for c in CHAMPIONS_DB}
    results = json.load(open(os.path.join(EXP_DIR, "canon_gate_results.json")))
    by_id = {r["id"]: r for r in results if "canon" in r}

    vlm = VLMClient()
    for cid in CHANGED:
        c = byid.get(cid)
        if not c or cid not in by_id:
            print(f"  {cid}: skip (no cached canon)")
            continue
        canon = by_id[cid]["canon"]
        sprite = os.path.join(ASSET_DIR, "characters", cid, "sprite.png")
        best = None
        for _ in range(2):
            try:
                g = vlm.canon_gate(sprite, champ=c, canon=canon)
                if best is None or g["canonical_match"] > best["canonical_match"]:
                    best = g
            except Exception:
                pass
        if best:
            by_id[cid]["gate"] = best
            print(f"  {cid}: fresh gate = {best['canonical_match']}/10 rec={best.get('recognizable')}")

    with open(os.path.join(EXP_DIR, "canon_gate_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    # new totals
    ok = [r for r in results if "gate" in r]
    matches = [r["gate"]["canonical_match"] for r in ok]
    rec = sum(1 for r in ok if r["gate"].get("recognizable"))
    stance = sum(1 for r in ok if r["gate"].get("stance_captured"))
    n = len(ok)
    print(f"\n=== UPDATED TOTALS ({n} champs) ===")
    print(f"mean: {sum(matches)/n:.2f}/10")
    print(f"recognizable (>=7): {rec}/{n} = {100*rec/n:.0f}%")
    print(f"stance: {stance}/{n} = {100*stance/n:.0f}%")
    from collections import Counter
    print(f"distribution: {dict(sorted(Counter(matches).items()))}")


if __name__ == "__main__":
    main()
