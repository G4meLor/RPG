"""P2 gate: mean match after vocab expansion > P1 baseline mean."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data.tuning import ASSET_DIR
from src.build.champions import CHAMPIONS_DB

def _mean():
    ms = []
    for c in CHAMPIONS_DB:
        cid = c["id"]
        p = os.path.join(ASSET_DIR, "characters", cid, "descriptors.json")
        if os.path.exists(p):
            e = json.load(open(p)).get("0")
            if e: ms.append(e["match"])
    return round(sum(ms) / len(ms), 2) if ms else 0

def main():
    p2 = _mean()
    p1 = float(open("p1_baseline_mean.txt").read().strip())
    print(f"P1 mean={p1} P2 mean={p2}")
    ok = p2 > p1
    print("P2 GATE OK" if ok else "P2 GATE FAIL (no improvement)")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
