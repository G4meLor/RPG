"""P1 gate: read every descriptors.json, assert mean final match >= 6 and no
skin regressed (final match >= round-0 match). Headless, no image reading."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data.tuning import ASSET_DIR
from src.build.champions import CHAMPIONS_DB

def main():
    chars = os.path.join(ASSET_DIR, "characters")
    ids = [c["id"] for c in CHAMPIONS_DB]
    matches, before, regressions, missing = [], [], 0, []
    for cid in ids:
        p = os.path.join(chars, cid, "descriptors.json")
        if not os.path.exists(p):
            missing.append(cid); continue
        with open(p) as f:
            c = json.load(f)
        e = c.get("0")
        if not e:
            missing.append(cid); continue
        matches.append(e["match"]); before.append(e.get("match_before", e["match"]))
        if e["match"] < e.get("match_before", e["match"]):
            regressions += 1
            print(f"  REGRESSION {cid}: {e.get('match_before')} -> {e['match']}")
    mean = round(sum(matches) / len(matches), 2) if matches else 0
    print(f"champs={len(matches)} mean_match={mean} regressions={regressions} missing={len(missing)}")
    ok = mean >= 6.0 and regressions == 0 and len(missing) == 0
    print("P1 GATE OK" if ok else "P1 GATE FAIL")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
