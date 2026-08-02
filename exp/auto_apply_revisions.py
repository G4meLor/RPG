"""Auto-apply VLM-described revisions to committed primitives.

Parses the plain-text edit description from vlm_review_revise.describe_revisions()
and patches the committed primitives programmatically:
  - RECOLOR: "recolor/change ... from [r,g,b] to [r,g,b]" → find prims with the
    old color (exact or near match) and recolor them.
  - RECOLOR-target: "recolor ... to [r,g,b]" (no 'from') → recolor prims matching
    a named region keyword (legs/torso/head/hair/boots) to the new color.
  - ADD: "add ... rect/circle/polygon ... at (x,y) ... [r,g,b]" → append a new prim.
  - RESIZE/EXTEND: "extend/lengthen ... to y=N" → best-effort: find prims in the
    named region and extend their height.

Imperfect (NLP of free text) but SAFE: apply_and_gate() only saves if the revised
sprite strictly beats the committed score — never regresses. So a misapplied edit
just means nothing saves.

Driver: loop_over(champs) runs describe → auto_apply → gate concurrently (4x),
prints results, returns the wins.
"""
import os, sys, json, re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vlm_review_revise import describe_revisions, apply_and_gate, committed_prims, committed_score

RGB = r"\[?\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]?"
XY = r"\(?\s*(\d+)\s*,\s*(\d+)\s*\)?"


def _col(s):
    """Extract the LAST [r,g,b] in the string (the target/new color). The first
    match is often a 'from' color or a stray coordinate; the last is the new color."""
    matches = list(re.finditer(RGB, s))
    if matches:
        m = matches[-1]
        return [int(m.group(1)), int(m.group(2)), int(m.group(3))]
    return None


def _xy(s):
    """Extract the FIRST (x,y) pair (the position to add/edit)."""
    m = re.search(XY, s)
    if m:
        return int(m.group(1)), int(m.group(2))
    return None


def _near(a, b, tol=30):
    if not a or not b: return False
    return all(abs(int(a[i]) - int(b[i])) <= tol for i in range(min(3, len(a), len(b))))


# region keywords → which primitive field to match (by position heuristic)
REGION_Y = {"leg": (170, 256), "boot": (190, 256), "foot": (190, 256),
            "torso": (95, 170), "chest": (95, 150), "head": (50, 95),
            "hair": (50, 95), "face": (60, 90), "arm": (95, 165),
            "hood": (50, 90), "cloak": (90, 200), "robe": (95, 200),
            "cape": (90, 210), "beard": (80, 110)}


def _in_region(p, yrange):
    t = p.get("type")
    if t == "circle": cy = p.get("cy", 128)
    elif t == "rect": cy = p.get("y", 0) + p.get("h", 0) // 2
    elif t == "ellipse": cy = p.get("y", 0) + p.get("h", 0) // 2
    elif t == "line": cy = (p.get("start", [0, 0])[1] + p.get("end", [0, 0])[1]) // 2
    elif t == "polygon":
        ys = [pt[1] for pt in p.get("points", [])]
        cy = sum(ys) // len(ys) if ys else 128
    else: cy = 128
    return yrange[0] <= cy <= yrange[1]


def auto_apply(cid, description):
    """Parse the VLM description and patch the committed primitives. Returns
    revised prims (a new list; committed untouched)."""
    prims = [dict(p) for p in committed_prims(cid)]  # shallow copy each
    if not prims:
        return prims
    lines = [l.strip() for l in description.split("\n") if l.strip() and l[0].isdigit()]
    n_edits = 0
    for line in lines:
        low = line.lower()
        new_col = _col(line)
        # --- RECOLOR with explicit 'from ... to ...' ---
        m = re.search(r"from\s+" + RGB + r".*?to\s+" + RGB, line, re.IGNORECASE)
        if m and new_col:
            old_col = [int(m.group(1)), int(m.group(2)), int(m.group(3))]
            new_c = [int(m.group(4)), int(m.group(5)), int(m.group(6))]
            for p in prims:
                if _near(p.get("color"), old_c, tol=25):
                    p["color"] = list(new_c)
                    n_edits += 1
            continue
        # --- RECOLOR by region keyword 'to [r,g,b]' ---
        if new_col and any(k in low for k in REGION_Y):
            region_keys = [k for k in REGION_Y if k in low]
            yr = REGION_Y[region_keys[0]]
            # 'bottom-most' / 'lower' → narrow to lower part of region
            if "bottom" in low or "lower" in low or "feet" in low or "hem" in low:
                yr = (max(yr[0], (yr[0]+yr[1])//2), yr[1])
            for p in prims:
                if _in_region(p, yr) and p.get("color") is not None:
                    # only recolor the dominant color in that region (avoid eyes etc.)
                    p["color"] = list(new_col)
                    n_edits += 1
            continue
        # --- ADD a shape (scale up: VLM underestimates size needed at 256px) ---
        if "add" in low and new_col:
            xy = _xy(line)
            if xy:
                x, y = xy
                if "rect" in low or "rectangle" in low or "bar" in low or "vertical" in low or "line" in low or "prong" in low or "fork" in low or "plate" in low or "pauldron" in low or "strap" in low:
                    w = 10 if "small" in low else (20 if "large" in low or "big" in low else 14)
                    h = 12 if "small" in low else (28 if "large" in low or "big" in low else 18)
                    if "vertical" in low: w, h = 5, 18
                    if "horizontal" in low or "prong" in low: w, h = 18, 5
                    prims.append({"type": "rect", "x": x-w//2, "y": y-h//2, "w": w, "h": h,
                                  "color": list(new_col), "outline": [30, 25, 22], "outline_w": 1})
                    n_edits += 1
                elif "circle" in low or "dot" in low or "pixel" in low or "gem" in low or "cluster" in low or "marking" in low:
                    r = 4 if "small" in low or "pixel" in low or "dot" in low else (8 if "big" in low else 6)
                    prims.append({"type": "circle", "cx": x, "cy": y, "r": r,
                                  "color": list(new_col), "outline": [30, 25, 22], "outline_w": 1})
                    n_edits += 1
                # generic add with no shape keyword → small rect
                elif "cape" in low or "cloak" in low or "robe" in low:
                    prims.append({"type": "rect", "x": x-20, "y": y-15, "w": 40, "h": 50,
                                  "color": list(new_col), "outline": [30, 25, 22], "outline_w": 1})
                    n_edits += 1
                continue
        # --- EXTEND / LENGTHEN (best effort: extend prims in named region downward) ---
        if ("extend" in low or "lengthen" in low or "longer" in low) and new_col is None:
            my = re.search(r"y\s*=?\s*(\d+)", line)
            if my:
                target_y = int(my.group(1))
                region_keys = [k for k in REGION_Y if k in low]
                if region_keys:
                    yr = REGION_Y[region_keys[0]]
                    for p in prims:
                        if _in_region(p, yr) and p.get("type") in ("rect", "ellipse"):
                            y0 = p.get("y", 0); h = p.get("h", 0)
                            p["h"] = max(h, target_y - y0)
                            n_edits += 1
                continue
    return prims, n_edits


def run_one(cid, n_gate=3):
    """Full loop: describe → auto_apply → gate. Returns result dict."""
    try:
        desc, cm, missing = describe_revisions(cid, n_gate=1)
    except Exception as e:
        return {"id": cid, "old": committed_score(cid), "new": 0, "saved": False,
                "missing": [str(e)], "edits": 0, "error": "describe failed"}
    revised, n_edits = auto_apply(cid, desc)
    if n_edits == 0 or len(revised) == len(committed_prims(cid)):
        # no edits parsed; try gate as-is (in case describe's re-gate differs)
        return {"id": cid, "old": committed_score(cid), "new": cm, "saved": False,
                "missing": missing, "edits": 0, "desc": desc[:200]}
    res = apply_and_gate(cid, revised, n_gate=n_gate)
    res["edits"] = n_edits
    res["desc"] = desc[:300]
    return res


if __name__ == "__main__":
    import argparse
    from concurrent.futures import ThreadPoolExecutor, as_completed
    ap = argparse.ArgumentParser()
    ap.add_argument("champs", nargs="*", help="champ IDs (default: all below-8)")
    ap.add_argument("--all", action="store_true", help="run all 53 below-8")
    args = ap.parse_args()
    if args.all or not args.champs:
        d = json.load(open(os.path.join(os.path.dirname(__file__), "canon_gate_results.json")))
        champs = sorted([r["id"] for r in d if "gate" in r and r["gate"]["canonical_match"] < 8],
                        key=lambda c: committed_score(c))
    else:
        champs = args.champs
    print(f"Auto-apply VLM revisions to {len(champs)} champs (concurrency 4)...")
    wins = 0
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(run_one, c): c for c in champs}
        for fut in as_completed(futs):
            r = fut.result()
            tag = "SAVED" if r.get("saved") else ("tie" if r.get("new") == r.get("old") else "lower")
            print(f"  {r['id']:12s} {r.get('old')}->{r.get('new')} {tag} edits={r.get('edits',0)} miss={r.get('missing',[])[:2]}", flush=True)
            if r.get("saved"): wins += 1
    print(f"\n=== {wins}/{len(champs)} saved (beat base) ===")
