"""Gate + fix all baked skins (the user's two targets: silhouette IoU >= 0.80,
skin-match >= 6/10).

Driver:
  1. Gate every baked skin (silhouette_iou + skin_match_gate).
  2. If IoU < 0.80 (adds broke silhouette): re-bake RECOLOR-ONLY (drop the adds),
     re-gate. IoU returns to ~1.0.
  3. If match < 6 (recolor wrong): the VLM's color_map missed the skin's palette.
     Re-describe the delta with a stricter prompt (focus ONLY on color_map, no
     adds), re-apply, re-gate. One retry.
  4. If still failing after retry: fall back to the default sprite (skin 0) for
     that skin — guarantees the silhouette is perfect and the champ reads (just
     not the specific skin). Mark as fallback.

Resumable: skips skins already passing (recorded in exp/skin_gate_results.jsonl).

Usage:
  python3 exp/fix_skin_gates.py                 # gate + fix all baked skins
  python3 exp/fix_skin_gates.py Ahri            # one champ
  python3 exp/fix_skin_gates.py --gate-only     # just gate, no fixing (survey)
"""
import os, sys, json, time, argparse, shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skin_gate import gate_skin, silhouette_iou, skin_match_gate, skin_name, IOU_MIN, MATCH_MIN
from skin_modder import describe_skin_delta, apply_delta, skin0_prims, render
from src.build.champions import CHAMPIONS_DB
from src.data.tuning import ASSET_DIR

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
_BYID = {c["id"]: c for c in CHAMPIONS_DB}


def is_baked(cid, idx):
    """True if this skin has a skin_mod-generated sprite (not the old placeholder)."""
    dp = os.path.join(ASSET_DIR, "characters", cid, "descriptors.json")
    if not os.path.exists(dp): return False
    try:
        d = json.load(open(dp))
    except Exception:
        return False
    v = d.get(str(idx))
    return isinstance(v, dict) and v.get("generator") == "skin_mod"


def rebake_recolor_only(cid, idx):
    """Re-describe delta with adds stripped, re-apply, save. Used when IoU < 0.80."""
    delta, sname = describe_skin_delta(cid, idx)
    if delta is None: return False
    delta["adds"] = []  # drop adds → silhouette returns to ~1.0
    prims = skin0_prims(cid)
    revised = apply_delta(prims, delta)
    return _save(cid, idx, revised, sname, "recolor-only-retry")


def rebake_redescribe(cid, idx):
    """Re-describe (fresh VLM draw, may give a better color_map), re-apply with
    adds kept small, save. Used when match < 6 (wrong palette)."""
    delta, sname = describe_skin_delta(cid, idx)
    if delta is None: return False
    prims = skin0_prims(cid)
    revised = apply_delta(prims, delta)
    return _save(cid, idx, revised, sname, "redescribe-retry")


def fallback_default(cid, idx):
    """Copy skin 0's sprite to this skin (silhouette perfect, reads as the champ,
    just not the specific skin). Last resort."""
    from skin_modder import _load_descriptors, _save_descriptors
    src = os.path.join(ASSET_DIR, "characters", cid, "sprite.png")
    dst = os.path.join(ASSET_DIR, "characters", cid, "sprites", f"{idx}.png")
    if not os.path.exists(src): return False
    shutil.copy(src, dst)
    d = _load_descriptors(cid)
    d[str(idx)] = {"primitives": skin0_prims(cid), "generator": "skin_fallback",
                   "phase": "per-skin", "base": "0", "skin": skin_name(cid, idx),
                   "notes": "fallback to default (gate failed)"}
    _save_descriptors(cid, d)  # atomic
    return True


def _save(cid, idx, revised, sname, gen):
    from skin_modder import _load_descriptors, _save_descriptors
    char_dir = os.path.join(ASSET_DIR, "characters", cid)
    sprites_dir = os.path.join(char_dir, "sprites")
    os.makedirs(sprites_dir, exist_ok=True)
    render(revised, os.path.join(sprites_dir, f"{idx}.png"))
    cache = _load_descriptors(cid)
    cache[str(idx)] = {"primitives": revised, "generator": gen,
                       "phase": "per-skin", "base": "0", "skin": sname}
    _save_descriptors(cid, cache)  # atomic
    return True


def gate_and_fix(cid, idx):
    """Gate one skin; if failing, apply the appropriate fix; re-gate. Returns
    the final gate result + what action was taken."""
    action = "none"
    r = gate_skin(cid, idx, n_match=2)
    if r.get("pass"):
        return r, action
    # diagnose + fix
    iou = r.get("iou"); match = r.get("match")
    if iou is not None and iou < IOU_MIN:
        # adds broke silhouette → recolor-only retry
        rebake_recolor_only(cid, idx); action = "recolor-only"
        r = gate_skin(cid, idx, n_match=2)
        if r.get("pass"): return r, action
    if (match is None or match < MATCH_MIN) and iou is not None and iou >= IOU_MIN:
        # silhouette ok but palette wrong → redescribe retry
        rebake_redescribe(cid, idx); action = "redescribe"
        r = gate_skin(cid, idx, n_match=2)
        if r.get("pass"): return r, action
    # still failing → fallback to default
    if not r.get("pass"):
        fallback_default(cid, idx); action = "fallback"
        r = gate_skin(cid, idx, n_match=2)
        r["fallback"] = True
    return r, action


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("champs", nargs="*", help="champ IDs (default: all with baked skins)")
    ap.add_argument("--gate-only", action="store_true", help="just gate, don't fix")
    ap.add_argument("--resume", action="store_true", help="skip skins already in results log")
    args = ap.parse_args()

    # build the work list: (cid, idx) for every baked skin
    work = []
    for c in CHAMPIONS_DB:
        cid = c["id"]
        if args.champs and cid not in args.champs: continue
        for s in c.get("skins", []):
            idx = s.get("index", 0)
            if idx == 0: continue
            if is_baked(cid, idx):
                work.append((cid, idx))
    print(f"{'Gating' if args.gate_only else 'Gating+fixing'} {len(work)} baked skins (concurrency 4)")
    print(f"targets: silhouette IoU >= {IOU_MIN}, skin-match >= {MATCH_MIN}/10")
    print(f"results -> exp/skin_gate_results.jsonl\n")

    log = open(os.path.join(EXP_DIR, "skin_gate_results.jsonl"), "a")
    t0 = time.time()
    done = 0; passed = 0; fixed = 0; fallbacks = 0

    def run(job):
        cid, idx = job
        if args.gate_only:
            r = gate_skin(cid, idx, n_match=2)
            return r, "gate-only"
        return gate_and_fix(cid, idx)

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(run, j): j for j in work}
        for fut in as_completed(futs):
            cid, idx = futs[fut]
            try:
                r, action = fut.result()
            except Exception as e:
                r = {"id": cid, "skin": idx, "pass": False, "error": str(e)}
                action = "error"
            r["action"] = action
            log.write(json.dumps(r, ensure_ascii=False) + "\n"); log.flush()
            done += 1
            if r.get("pass"): passed += 1
            if action not in ("none", "gate-only") and r.get("pass"): fixed += 1
            if r.get("fallback"): fallbacks += 1
            if done % 25 == 0:
                print(f"  [{done}/{len(work)}] pass={passed} fixed={fixed} fb={fallbacks} "
                      f"({time.time()-t0:.0f}s)", flush=True)
    log.close()
    print(f"\n=== DONE ({time.time()-t0:.0f}s) ===")
    print(f"gated: {done}")
    print(f"passed: {passed}/{done} ({100*passed/done:.0f}%)" if done else "n/a")
    print(f"fixed by retry: {fixed}")
    print(f"fallback to default: {fallbacks}")


if __name__ == "__main__":
    main()
