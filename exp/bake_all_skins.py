"""Concurrent driver: bake per-skin sprites for all 170 champs (light mods from
skin 0). Resumable — skips skins already generated (generator=="skin_mod").

Usage:
  python3 exp/bake_all_skins.py                # all 170 champs
  python3 exp/bake_all_skins.py Ahri Garen      # specific champs
  python3 exp/bake_all_skins.py --resume        # continue from progress log

Progress -> exp/skin_bake_progress.jsonl (one line per skin).
"""
import os, sys, json, time, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skin_modder import mod_all_skins, _BYID
from src.data.tuning import ASSET_DIR

EXP_DIR = os.path.dirname(os.path.abspath(__file__))


def already_done(cid, idx):
    """Skip if this skin already has a skin_mod-generated sprite."""
    dp = os.path.join(ASSET_DIR, "characters", cid, "descriptors.json")
    if not os.path.exists(dp): return False
    try:
        d = json.load(open(dp))
    except Exception:
        return False
    v = d.get(str(idx))
    return isinstance(v, dict) and v.get("generator") == "skin_mod"


def count_todo(cid):
    """How many skins for this champ still need baking."""
    c = _BYID.get(cid)
    if not c: return 0
    n = 0
    for s in c.get("skins", []):
        idx = s.get("index", 0)
        if idx == 0: continue
        splash = os.path.join(ASSET_DIR, "characters", cid, "skins", f"{idx}.jpg")
        if not os.path.exists(splash): continue
        if not already_done(cid, idx): n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("champs", nargs="*", help="champ IDs (default: all 170)")
    ap.add_argument("--resume", action="store_true", help="skip already-baked skins")
    args = ap.parse_args()
    champs = args.champs or sorted(_BYID.keys())
    # order by most todo first (so progress is visible early)
    champs = sorted(champs, key=lambda c: -count_todo(c))

    total_todo = sum(count_todo(c) for c in champs)
    print(f"Baking per-skin sprites for {len(champs)} champs ({total_todo} skins to do, concurrency 4)")
    print(f"progress -> exp/skin_bake_progress.jsonl\n")

    log = open(os.path.join(EXP_DIR, "skin_bake_progress.jsonl"), "a")
    t0 = time.time()
    done = 0; saved = 0; errors = 0

    def run_champ(cid):
        c = _BYID.get(cid)
        if not c: return []
        results = []
        for s in c.get("skins", []):
            idx = s.get("index", 0)
            if idx == 0: continue
            splash = os.path.join(ASSET_DIR, "characters", cid, "skins", f"{idx}.jpg")
            if not os.path.exists(splash): continue
            if args.resume and already_done(cid, idx):
                results.append({"id": cid, "skin": idx, "name": s.get("name", "?"),
                                "saved": False, "skipped": True})
                continue
            from skin_modder import mod_skin
            try:
                r = mod_skin(cid, idx)
            except Exception as e:
                r = {"id": cid, "skin": idx, "name": s.get("name", "?"),
                     "saved": False, "error": str(e)}
            results.append(r)
        return results

    # Process champs concurrently (4 = VLM concurrency). Each champ's skins run
    # sequentially within its worker (avoids two workers touching the same
    # descriptors.json).
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(run_champ, c): c for c in champs if count_todo(c) > 0 or not args.resume}
        for fut in as_completed(futs):
            cid = futs[fut]
            try:
                rs = fut.result()
            except Exception as e:
                print(f"  {cid}: ERROR {e}", flush=True)
                errors += 1
                continue
            for r in rs:
                log.write(json.dumps(r, ensure_ascii=False) + "\n")
                log.flush()
                done += 1
                if r.get("saved"): saved += 1
                if r.get("error"): errors += 1
                if r.get("skipped"): continue
                name = r.get("name", "?")[:14]
                tag = "SAVED" if r.get("saved") else ("ERR" if r.get("error") else "skip")
                if done % 25 == 0:
                    print(f"  [{done}/{total_todo}] {r['id']} skin {r['skin']} {name} {tag} "
                          f"({time.time()-t0:.0f}s, saved={saved})", flush=True)
    log.close()
    print(f"\n=== DONE ({time.time()-t0:.0f}s) ===")
    print(f"skins processed: {done}")
    print(f"saved: {saved}")
    print(f"errors: {errors}")
    print(f"progress -> exp/skin_bake_progress.jsonl")


if __name__ == "__main__":
    main()
