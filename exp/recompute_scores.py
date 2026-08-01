"""Recompute the canon gate scores with the REAL gate (canon_identity + canon_gate)
but READ the canon_identity from the existing exp/canon_gate_results.json cache
(so we only do 1 VLM call/champ, not 2) and re-run canon_gate on the CURRENT
committed sprite. This gives honest, current scores.

Concurrency 4 for speed. Results -> exp/canon_gate_results.json (overwrite)
so all downstream analysis uses fresh scores.

Also: re-gate each sprite 2x and take the MAX, to reduce the gate's
single-run variance (Fiora/Darius dropped 6->4 on re-gate — variance, not
real regression).
"""
import os, sys, json, base64, ssl, urllib.request, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.build.champions import CHAMPIONS_DB
from src.build.vlm_client import VLMClient
from src.data.tuning import ASSET_DIR

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
N_GATE_RUNS = 2  # re-gate each sprite 2x, take max (reduce variance)


def main():
    byid = {c["id"]: c for c in CHAMPIONS_DB}
    # Load existing canon identities (cached from the original gate run).
    cached = json.load(open(os.path.join(EXP_DIR, "canon_gate_results.json")))
    canon_by_id = {item["id"]: item.get("canon") for item in cached if item.get("canon")}

    champs = [c for c in CHAMPIONS_DB if c["id"] in canon_by_id]
    print(f"Re-gating {len(champs)} champs (canon_identity from cache, canon_gate x{N_GATE_RUNS} on committed sprite)")
    print(f"concurrency 4, take max of {N_GATE_RUNS} runs per champ\n")

    vlm = VLMClient()

    def gate_one(c):
        cid = c["id"]
        canon = canon_by_id.get(cid)
        if not canon:
            return {"id": cid, "error": "no cached canon"}
        sprite = os.path.join(ASSET_DIR, "characters", cid, "sprite.png")
        if not os.path.exists(sprite):
            return {"id": cid, "error": "missing sprite"}
        best = None
        for _ in range(N_GATE_RUNS):
            try:
                g = vlm.canon_gate(sprite, champ=c, canon=canon)
                if best is None or g["canonical_match"] > best["canonical_match"]:
                    best = g
            except Exception as e:
                pass
        if best is None:
            return {"id": cid, "error": "all gate calls failed"}
        return {"id": cid, "canon": canon, "gate": best, "sprite_path": sprite}

    t0 = time.time()
    results = [None] * len(champs)
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(gate_one, c): i for i, c in enumerate(champs)}
        done = 0
        for fut in as_completed(futs):
            i = futs[fut]
            try:
                results[i] = fut.result()
            except Exception as e:
                results[i] = {"id": champs[i]["id"], "error": str(e)}
            done += 1
            if done % 20 == 0:
                print(f"  {done}/{len(champs)} gated ({time.time()-t0:.0f}s)", flush=True)

    # Aggregate
    ok = [r for r in results if r and "gate" in r]
    errs = [r for r in results if r and "error" in r]
    matches = [r["gate"]["canonical_match"] for r in ok]
    rec = sum(1 for r in ok if r["gate"].get("recognizable"))
    stance = sum(1 for r in ok if r["gate"].get("stance_captured"))
    n = len(ok)
    mean = sum(matches) / n if n else 0
    print(f"\n=== RE-GATE ({n} ok, {len(errs)} errors, {time.time()-t0:.0f}s) ===")
    print(f"mean: {mean:.2f}/10")
    print(f"recognizable (>=7): {rec}/{n} = {100*rec/n:.0f}%")
    print(f"stance: {stance}/{n} = {100*stance/n:.0f}%")
    from collections import Counter
    print(f"distribution: {dict(sorted(Counter(matches).items()))}")

    # Compare to old
    old = {item["id"]: item["gate"]["canonical_match"] for item in cached if "gate" in item}
    new = {r["id"]: r["gate"]["canonical_match"] for r in ok}
    delta = sum(new[cid] - old[cid] for cid in new if cid in old)
    print(f"\nsum delta vs old gate: {delta:+d} across {len(new)} champs")
    moved = [(cid, old.get(cid, 0), new[cid]) for cid in new if cid in old and new[cid] != old[cid]]
    moved.sort(key=lambda x: x[2] - x[1])
    print(f"champs whose score changed: {len(moved)}")
    for cid, o, nw in moved[:15]:
        print(f"  {cid:14s}: {o} -> {nw} ({nw-o:+d})")
    print("  ...")
    for cid, o, nw in moved[-10:]:
        print(f"  {cid:14s}: {o} -> {nw} ({nw-o:+d})")

    # Save (overwrite the canon gate results with fresh scores)
    with open(os.path.join(EXP_DIR, "canon_gate_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nresults -> exp/canon_gate_results.json (overwritten with fresh scores)")


if __name__ == "__main__":
    main()
