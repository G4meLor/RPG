"""VLM sprite generation Phase 2: splash-guided refinement + re-gen failures.

Phase 2a: For each champ that has a Phase-1 sprite (from vlm_sprite_gen.py results),
  feed the skin-0 splash + the Phase-1 sprite to the VLM. The VLM gives small
  tweaks (colors, proportions, missing features) and outputs revised primitives.
  1 pass only (per the user's design). Render + critique.

Phase 2b: Re-generate the 2 parse-error champs (Ahri, Gangplank) + the 26 champs
  scoring <4 with a more constrained prompt (fewer primitives, simpler shapes).

Then: save the best sprites to assets/characters/{id}/sprite.png + cache the
primitives to descriptors.json. Run the canon gate.
"""
import os, sys, json, base64, ssl, urllib.request, re, math, time
from concurrent.futures import ThreadPoolExecutor, as_completed

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.build.champions import CHAMPIONS_DB
from src.data.tuning import ASSET_DIR

BASE = "https://runai.misaonline.vpnlocal/prod-llm/misa-gemma4-31b-it-api/v1"
KEY = "sk-proj-runai-8p33H3qYneIaWOwjX5bsae3I1CIJhUjvKG0nTis6dJ1mzkJqHW"
MODEL = "misa-gemma-4-31b-it"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE
CONCURRENCY = 4

def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def chat(messages, max_tokens=4000, temperature=0.3):
    body = json.dumps({"model": MODEL, "messages": messages,
                       "max_tokens": max_tokens, "temperature": temperature}).encode()
    req = urllib.request.Request(BASE + "/chat/completions", data=body,
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, context=CTX, timeout=240) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

def strip_json(text):
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m: return m.group(1)
    start = text.find("{")
    if start < 0: return text.strip()
    depth = 0; end = start
    for i in range(start, len(text)):
        if text[i] == "{": depth += 1
        elif text[i] == "}": depth -= 1
        if depth == 0: end = i + 1; break
    if depth != 0: return text[start:] + "}" * depth
    return text[start:end]

def repair_json(s):
    s = re.sub(r",\s*([}\]])", r"\1", s)
    s = re.sub(r"(\w+)\s*:", r'"\1":', s)
    opens = s.count("[") - s.count("]")
    if opens > 0: s += "]" * opens
    opens = s.count("{") - s.count("}")
    if opens > 0: s += "}" * opens
    return s

def parse_prims(text):
    raw = strip_json(text)
    for attempt in range(3):
        try:
            d = json.loads(raw)
            return d.get("primitives", []), True
        except json.JSONDecodeError:
            if attempt == 0:
                raw = repair_json(raw)
            elif attempt == 1:
                # try to find just the array
                m = re.search(r'\[.*\]', raw, re.DOTALL)
                if m:
                    try:
                        return json.loads(m.group(0)), True
                    except: pass
                return [], False
            else:
                return [], False
    return [], False

def champ_canon_text(c):
    an = c.get("ability_names", {})
    abstr = ", ".join(f"{s}: {an[s]}" for s in ("Q","W","E","R") if s in an)
    bio = (c.get("lore",{}).get("bio","") or "")[:200]
    return (f"Champion: {c['name']} — {c.get('title','')}. "
            f"Faction: {c.get('faction','')}. Role: {c.get('role','')}. "
            f"Abilities: {abstr}. Lore: {bio}")

def render_primitives(prims, path):
    surf = pygame.Surface((256, 256), pygame.SRCALPHA)
    for p in prims:
        try:
            t = p.get("type", "")
            col = tuple(p.get("color", [200, 200, 200])[:3])
            ol = p.get("outline")
            ol = tuple(ol[:3]) if ol else None
            ow = p.get("outline_w", 1)
            if t == "circle":
                r = max(1, p.get("r", 5))
                pygame.draw.circle(surf, col, (p.get("cx", 128), p.get("cy", 128)), r)
                if ol: pygame.draw.circle(surf, ol, (p.get("cx", 128), p.get("cy", 128)), r, ow)
            elif t == "rect":
                w, h = max(1, p.get("w", 10)), max(1, p.get("h", 10))
                rad = p.get("radius", 0)
                rect = pygame.Rect(p.get("x", 0), p.get("y", 0), w, h)
                if rad > 0:
                    pygame.draw.rect(surf, col, rect, border_radius=rad)
                    if ol: pygame.draw.rect(surf, ol, rect, ow, border_radius=rad)
                else:
                    pygame.draw.rect(surf, col, rect)
                    if ol: pygame.draw.rect(surf, ol, rect, ow)
            elif t == "polygon":
                pts = [(int(x), int(y)) for x, y in p.get("points", [])]
                if len(pts) >= 3:
                    pygame.draw.polygon(surf, col, pts)
                    if ol: pygame.draw.polygon(surf, ol, pts, ow)
            elif t == "line":
                s_, e_ = p.get("start", [0,0]), p.get("end", [0,0])
                pygame.draw.line(surf, col, (int(s_[0]),int(s_[1])), (int(e_[0]),int(e_[1])), max(1, p.get("width", 1)))
            elif t == "ellipse":
                w, h = max(1, p.get("w", 10)), max(1, p.get("h", 10))
                rect = pygame.Rect(p.get("x", 0), p.get("y", 0), w, h)
                pygame.draw.ellipse(surf, col, rect)
                if ol: pygame.draw.ellipse(surf, ol, rect, ow)
        except Exception:
            continue
    pygame.image.save(surf, path)
    a = pygame.surfarray.pixels_alpha(surf); arr = a.__array__(); del a
    cov = float((arr > 8).sum()) / (256 * 256)
    return cov

GATE_SYS = (
    "You are a STRICT visual critic who knows League of Legends. You will be given a "
    "champion's canonical identity (text) and a 256x256 pixel-art sprite (image). Judge "
    "whether a LoL player would recognize the champion from the sprite.\n"
    "Output JSON ONLY: {canonical_match: 0-10, recognizable: true/false, "
    "stance_captured: true/false, features_captured: [list], features_missing: [list], "
    "verdict: one sentence}. canonical_match >= 7 means recognizable. Be STRICT."
)

REFINE_SYS = (
    "You are a pixel-art sprite artist. You will be given a champion's canonical identity, "
    "their skin-0 splash art (image 1), and your current pixel-art sprite (image 2). "
    "Make SMALL refinements to the sprite based on the splash — adjust colors to match, "
    "fix proportions, add any missing small details. Keep the overall silhouette and "
    "composition. Output the FULL revised JSON primitives. Keep JSON valid. Output JSON ONLY."
)

DRAW_SYS = (
    "You are a pixel-art sprite artist. You will be given a League of Legends champion's "
    "canonical identity (name, title, lore, abilities). Produce a JSON description of the "
    "drawing primitives that create a 256x256 pixel-art world sprite of this champion.\n\n"
    "Output JSON ONLY:\n"
    '{"primitives": [\n'
    '  {"type": "circle", "cx": int, "cy": int, "r": int, "color": [r,g,b], "outline": [r,g,b], "outline_w": int},\n'
    '  {"type": "rect", "x": int, "y": int, "w": int, "h": int, "color": [r,g,b], "outline": [r,g,b], "outline_w": int, "radius": int},\n'
    '  {"type": "polygon", "points": [[x,y],...], "color": [r,g,b], "outline": [r,g,b], "outline_w": int},\n'
    '  {"type": "line", "start": [x,y], "end": [x,y], "color": [r,g,b], "width": int},\n'
    '  {"type": "ellipse", "x": int, "y": int, "w": int, "h": int, "color": [r,g,b], "outline": [r,g,b], "outline_w": int}\n'
    "]}\n\n"
    "Rules:\n"
    "- All coordinates 0-255. The sprite is 256x256. Body center ~ (128, 150).\n"
    "- Draw the FULL BODY: head, torso, arms, legs, weapon, and ALL signature features.\n"
    "- Use the champion's CANONICAL colors (from your LoL knowledge).\n"
    "- Be SPECIFIC and CREATIVE — draw THIS champion's signature look, not a generic humanoid.\n"
    "- 15-30 primitives is ideal. Keep JSON valid — no trailing commas. Output JSON ONLY."
)

REVISE_SYS = (
    "You are a pixel-art sprite artist. Your sprite was critiqued. REVISE the primitives "
    "to fix the missing features. Keep what works, fix what's missing. Output the FULL "
    "revised JSON primitives. Keep JSON valid. Output JSON ONLY."
)

def critique_sprite(c, sprite_path):
    """Critique a sprite vs canon (no splash). Returns (cm, rec, missing)."""
    canon = champ_canon_text(c)
    crit = chat([
        {"role": "system", "content": GATE_SYS},
        {"role": "user", "content": [
            {"type": "text", "text": f"{canon}\n\nImage = the pixel-art sprite. "
             f"Does it capture {c['id']}'s canonical identity? JSON only."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64(sprite_path)}"}},
        ]},
    ], max_tokens=400)
    try:
        d = json.loads(strip_json(crit))
        cm = max(0, min(10, int(d.get("canonical_match", 0))))
        rec = bool(d.get("recognizable", False))
        missing = d.get("features_missing", [])
        return cm, rec, missing
    except Exception:
        return 0, False, ["parse error"]

def refine_one(c, phase1_prims, phase1_score):
    """Phase 2: splash-guided refinement of a Phase-1 sprite. 1 pass."""
    cid = c["id"]
    canon = champ_canon_text(c)
    splash = os.path.join(ASSET_DIR, "characters", cid, "skins", "0.jpg")
    tmp1 = f"/tmp/vlm_p1_{cid}.png"
    tmp2 = f"/tmp/vlm_p2_{cid}.png"

    # render phase-1 sprite
    render_primitives(phase1_prims, tmp1)

    if not os.path.exists(splash):
        return phase1_prims, phase1_score, "no splash"

    # Phase 2: feed splash + phase-1 sprite → VLM refines
    resp = chat([
        {"role": "system", "content": REFINE_SYS},
        {"role": "user", "content": [
            {"type": "text", "text": f"Champion: {cid}. Canon: {canon}\n\n"
             f"Image 1 = the skin-0 splash (reference for colors/proportions). "
             f"Image 2 = your current pixel-art sprite.\n"
             f"Make small refinements to match the splash's colors and fix any "
             f"missing details. Output the FULL revised JSON primitives.\n\n"
             f"Current primitives:\n{json.dumps({'primitives': phase1_prims})[:2000]}"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64(splash)}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64(tmp1)}"}},
        ]},
    ], max_tokens=4000)

    prims2, ok = parse_prims(resp)
    if not ok or not prims2:
        return phase1_prims, phase1_score, "phase2 parse fail"

    render_primitives(prims2, tmp2)
    cm2, rec2, missing2 = critique_sprite(c, tmp2)

    # keep whichever is better
    if cm2 > phase1_score:
        return prims2, cm2, f"phase2 improved {phase1_score}->{cm2}"
    else:
        return phase1_prims, phase1_score, f"phase2 no improve ({cm2}<= {phase1_score})"

def regen_one(c, max_iters=10):
    """Re-generate a failed/low-score champ from scratch with constrained prompt."""
    cid = c["id"]
    canon = champ_canon_text(c)
    tmp = f"/tmp/vlm_rg_{cid}.png"

    resp = chat([
        {"role": "system", "content": DRAW_SYS},
        {"role": "user", "content": f"{canon}\n\nProduce the drawing primitives JSON for {cid}. "
         f"Keep it under 25 primitives. Be specific to {cid}'s signature look."},
    ], max_tokens=4000)

    best_prims = None; best_score = -1; history = []
    for i in range(max_iters):
        prims, ok = parse_prims(resp)
        if not ok or not prims:
            history.append({"iter": i, "cm": 0, "error": "parse"})
            resp = chat([
                {"role": "system", "content": DRAW_SYS},
                {"role": "user", "content": f"{canon}\n\nOutput was not valid JSON. "
                 f"Output ONLY valid JSON for {cid}. Under 20 primitives."},
            ], max_tokens=3000)
            continue

        cov = render_primitives(prims, tmp)
        if cov < 0.01:
            history.append({"iter": i, "cm": 0, "error": "blank"})
            resp = chat([{"role":"system","content":DRAW_SYS},
                {"role":"user","content":f"{canon}\n\nSprite was blank. Draw {cid} visibly. Valid JSON."}],
                max_tokens=3000)
            continue

        cm, rec, missing = critique_sprite(c, tmp)
        history.append({"iter": i, "cm": cm, "rec": rec, "missing": missing[:3]})
        if cm > best_score: best_score = cm; best_prims = prims
        if cm >= 7: break
        if i < max_iters - 1:
            resp = chat([
                {"role": "system", "content": REVISE_SYS},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Champion: {cid}. Canon: {canon}\n"
                     f"Scored {cm}/10. Missing: {missing}.\n"
                     f"Revise. Output FULL JSON.\n\n"
                     f"Current:\n{json.dumps({'primitives': prims})[:2000]}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64(tmp)}"}},
                ]},
            ], max_tokens=4000)

    if best_prims: render_primitives(best_prims, tmp)
    return best_prims, best_score, history

def save_sprite(cid, prims):
    """Save the best primitives as the champ's sprite.png + sprites/0.png + cache."""
    char_dir = os.path.join(ASSET_DIR, "characters", cid)
    os.makedirs(char_dir, exist_ok=True)
    sprites_dir = os.path.join(char_dir, "sprites")
    os.makedirs(sprites_dir, exist_ok=True)
    # render to sprite.png + sprites/0.png
    surf = pygame.Surface((256, 256), pygame.SRCALPHA)
    render_primitives(prims, os.path.join(char_dir, "sprite.png"))
    # copy to sprites/0.png
    import shutil
    shutil.copy(os.path.join(char_dir, "sprite.png"), os.path.join(sprites_dir, "0.png"))
    # save primitives to descriptors.json
    cache_path = os.path.join(char_dir, "descriptors.json")
    cache = {}
    if os.path.exists(cache_path):
        try: cache = json.load(open(cache_path))
        except: cache = {}
    cache["0"] = {"primitives": prims, "generator": "vlm_primitives", "phase": "2"}
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2, default=str)

def main():
    # Load Phase-1 results
    p1 = json.load(open("/tmp/vlm_gen_results.json"))
    byid = {c["id"]: c for c in CHAMPIONS_DB}

    ok_p1 = [r for r in p1 if "error" not in r and r.get("primitives")]
    err_p1 = [r for r in p1 if "error" in r or not r.get("primitives")]
    low_p1 = [r for r in ok_p1 if r["best_score"] < 4]
    good_p1 = [r for r in ok_p1 if r["best_score"] >= 4]

    print(f"Phase 1: {len(ok_p1)} ok, {len(err_p1)} errors, {len(low_p1)} low (<4), {len(good_p1)} good (>=4)")
    print(f"Phase 2a: splash-refine {len(good_p1)} good champs (1 pass each)...")
    print(f"Phase 2b: re-generate {len(err_p1)+len(low_p1)} failed/low champs (loop)...")

    t0 = time.time()
    all_results = {}  # cid -> (prims, score, note)

    # Phase 2a: refine good champs (splash-guided, 1 pass)
    def do_refine(r):
        c = byid[r["id"]]
        prims, score, note = refine_one(c, r["primitives"], r["best_score"])
        return r["id"], prims, score, note

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = {ex.submit(do_refine, r): r["id"] for r in good_p1}
        done = 0
        for fut in as_completed(futs):
            cid, prims, score, note = fut.result()
            all_results[cid] = (prims, score, note)
            done += 1
            if done % 20 == 0:
                print(f"  2a: {done}/{len(good_p1)} refined ({time.time()-t0:.0f}s)", flush=True)

    # Phase 2b: re-generate failed/low champs
    def do_regen(r):
        c = byid.get(r["id"])
        if not c: return r["id"], None, -1, "no champ"
        prims, score, hist = regen_one(c, max_iters=10)
        return r["id"], prims, score, f"regen best={score}"

    regen_list = err_p1 + low_p1
    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        futs = {ex.submit(do_regen, r): r["id"] for r in regen_list}
        done = 0
        for fut in as_completed(futs):
            cid, prims, score, note = fut.result()
            all_results[cid] = (prims, score, note)
            done += 1
            if done % 5 == 0:
                print(f"  2b: {done}/{len(regen_list)} regen ({time.time()-t0:.0f}s)", flush=True)

    # Summary
    scores = [s for _, s, _ in all_results.values() if s >= 0]
    mean = sum(scores) / len(scores) if scores else 0
    rec = sum(1 for s in scores if s >= 7)
    print(f"\n=== Phase 2 complete: {len(scores)} champs, {time.time()-t0:.0f}s ===")
    print(f"mean: {mean:.2f}/10")
    print(f"recognizable (>=7): {rec}/{len(scores)} ({100*rec/len(scores):.0f}%)")
    from collections import Counter
    dist = Counter(scores)
    print(f"distribution: {dict(sorted(dist.items()))}")

    # Save sprites + cache
    print("\nSaving sprites...")
    saved = 0
    for cid, (prims, score, note) in all_results.items():
        if prims and score >= 0:
            save_sprite(cid, prims)
            saved += 1
    print(f"Saved {saved} sprites")

    # Save results
    out = {cid: {"score": s, "note": n, "n_prims": len(p) if p else 0}
           for cid, (p, s, n) in all_results.items()}
    with open("/tmp/vlm_gen_phase2_results.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"Results -> /tmp/vlm_gen_phase2_results.json")

    # Comparison
    p1_mean = sum(r["best_score"] for r in ok_p1) / len(ok_p1)
    p1_rec = sum(1 for r in ok_p1 if r["best_score"] >= 7)
    print(f"\n=== COMPARISON ===")
    print(f"  Phase 1: mean={p1_mean:.2f}, recognizable={p1_rec}/{len(ok_p1)} ({100*p1_rec/len(ok_p1):.0f}%)")
    print(f"  Phase 2: mean={mean:.2f}, recognizable={rec}/{len(scores)} ({100*rec/len(scores):.0f}%)")

if __name__ == "__main__":
    main()
