"""Fix round 3: the 7 champs still scoring <4 + push mean toward 6.0.

Two-pronged approach:
1. Re-fix the 7 hard champs with EVEN MORE specific guidance (reference the exact
   gate feedback, give pixel-level instructions).
2. For the ~26 champs scoring 4-5 (borderline), run a quick 3-iter refinement
   to push them toward 6+.
"""
import os, sys, json, base64, ssl, urllib.request, re, time
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

# 7 hard champs with VERY specific pixel-level guidance
HARD_FIXES = {
    "Shyvana": "Draw Shyvana as a humanoid woman with dragon parts. CRITICAL features: 1) Two large BAT-LIKE DRAGON WINGS on her back (spread wide, use polygons for membrane + lines for bone structure). 2) A long thick DRAGON TAIL curving from her lower back to the ground (use a chain of overlapping circles). 3) Two curved HORNS on her head. 4) Red/orange SCALE TEXTURE on her arms (small overlapping arcs). Colors: crimson red body, orange wings, dark armor. She must look like a half-dragon, NOT a bird.",
    "Akali": "Draw Akali as a ninja assassin. CRITICAL features: 1) A HIGH PONYTAIL (long hair pulled up, use a curved polygon from the top of the head going back). 2) A GREEN MASK covering the lower half of her face (a green rectangle/triangle over the nose-mouth area). 3) Dark purple/black NINJA OUTFIT (tight bodysuit, use dark colors with green accents). 4) Two KAMA (sickle weapons) in her hands. Colors: dark purple outfit, green mask/accent, dark skin. She must look like a stealthy ninja, NOT a generic fighter.",
    "Janna": "Draw Janna as a floating wind goddess. CRITICAL features: 1) She FLOATS (no legs, her lower body fades into wisps — draw the upper body only, with flowing cloth trails below instead of legs). 2) LONG FLOWING HAIR blowing to the side (use curved polygons, light blue/white). 3) A staff with a glowing orb on top. 4) WIND SWIRLS around her (small curved lines). Colors: white, light blue, teal. She must look ethereal and floating, NOT a standing figure.",
    "Rell": "Draw Rell as a girl on a METALLIC HORSE. CRITICAL: 1) Draw a HORSE body at the bottom (quadruped shape, 4 legs, a head with mane — make it clearly angular/metallic, NOT organic). 2) Rell sits on top (small upper body, dark hair, holding a lance). 3) The horse is made of DARK METAL PLATES (use dark grey with metallic sheen lines). Colors: dark steel grey horse, red accents on Rell. This is a MOUNTED champ — the horse is the biggest part.",
    "Sona": "Draw Sona as an elegant musician. CRITICAL: 1) A large FLOATING ETWAHL (string instrument) — a wide flat harp-like shape floating in front of her (use an ellipse + vertical string lines). 2) LONG FLOWING PINK/BLUE HAIR (curved polygons). 3) An elegant flowing GOWN (wide at the bottom). 4) Floating musical notes around her (small circles + lines). Colors: pink hair, blue gown, gold instrument. She must have a VISIBLE instrument — it's her most iconic feature.",
    "Udyr": "Draw Udyr as a wild shirtless fighter. CRITICAL: 1) BARE MUSCULAR CHEST (show skin tone, NOT armor — use a skin-colored torso). 2) ANIMAL FUR PELT draped over one shoulder (brown, use a curved polygon with jagged edges). 3) TRIBAL TATTOOS (a few dark lines/patterns on the chest and arms). 4) WILD HAIR (unkempt, use jagged polygons). 5) Fighting stance with clenched FISTS. Colors: dark skin, brown fur, dark tattoos. He must look like a wildman, NOT a robot or knight.",
    "Zeri": "Draw Zeri as an electric Zaunite girl. CRITICAL: 1) SPIKY ELECTRIC YELLOW HAIR (jagged upward-pointing polygons, bright yellow). 2) Her RIGHT ARM is a GLOWING GUN (replace the right arm with a mechanical gun shape, blue/teal glow). 3) ZAUNITE STREETWEAR — a hoodie (use a colored torso with a hood shape). 4) OVERSIZED BOOTS (large feet). 5) Lightning effects (small yellow zigzag lines around her). Colors: yellow hair, teal gun-arm, dark hoodie. She must have VISIBLE electric hair + gun-arm.",
}

# ~26 borderline champs (score 4-5) — quick 3-iter refinement
# We'll identify them from the gate results at runtime

def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def chat(messages, max_tokens=4000, temperature=0.3):
    for attempt in range(3):
        try:
            body = json.dumps({"model": MODEL, "messages": messages,
                               "max_tokens": max_tokens, "temperature": temperature}).encode()
            req = urllib.request.Request(BASE + "/chat/completions", data=body,
                headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, context=CTX, timeout=300) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
                continue
            raise

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
            if attempt == 0: raw = repair_json(raw)
            elif attempt == 1:
                m = re.search(r'\[.*\]', raw, re.DOTALL)
                if m:
                    try: return json.loads(m.group(0)), True
                    except: pass
                return [], False
            else: return [], False
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
    return surf

DRAW_SYS = (
    "You are a pixel-art sprite artist. You will be given a League of Legends champion's "
    "canonical identity AND very specific pixel-level drawing instructions. Follow the "
    "instructions EXACTLY — draw every feature mentioned, in the colors specified.\n\n"
    "Output JSON ONLY:\n"
    '{"primitives": [\n'
    '  {"type": "circle", "cx": int, "cy": int, "r": int, "color": [r,g,b], "outline": [r,g,b], "outline_w": int},\n'
    '  {"type": "rect", "x": int, "y": int, "w": int, "h": int, "color": [r,g,b], "outline": [r,g,b], "outline_w": int, "radius": int},\n'
    '  {"type": "polygon", "points": [[x,y],...], "color": [r,g,b], "outline": [r,g,b], "outline_w": int},\n'
    '  {"type": "line", "start": [x,y], "end": [x,y], "color": [r,g,b], "width": int},\n'
    '  {"type": "ellipse", "x": int, "y": int, "w": int, "h": int, "color": [r,g,b], "outline": [r,g,b], "outline_w": int}\n'
    "]}\n\n"
    "Rules: coords 0-255, 256x256, body center ~ (128,150). 15-35 primitives. "
    "Draw back-to-front. Keep JSON valid. Output JSON ONLY."
)

GATE_SYS = (
    "You are a STRICT visual critic who knows League of Legends. Given a champion's "
    "canonical identity (text) and a 256x256 pixel-art sprite (image), judge whether a "
    "LoL player would recognize the champion.\n"
    "Output JSON ONLY: {canonical_match: 0-10, recognizable: true/false, "
    "features_captured: [list], features_missing: [list], verdict: one sentence}. "
    "canonical_match >= 7 means recognizable. Be STRICT."
)

REVISE_SYS = (
    "You are a pixel-art sprite artist. REVISE the primitives to fix the missing features. "
    "Output the FULL revised JSON. Keep JSON valid."
)

REFINE_SYS = (
    "You are a pixel-art sprite artist. Given a champion's identity, their current sprite, "
    "and the critic's feedback, make targeted improvements. Keep the good parts, fix what's "
    "missing. Output the FULL revised JSON primitives. Keep JSON valid. Output JSON ONLY."
)

def fix_hard(c, fix_guidance, max_iters=10):
    cid = c["id"]
    canon = champ_canon_text(c)
    tmp = f"/tmp/vlmfix3_{cid}.png"
    old = os.path.join(ASSET_DIR, "characters", cid, "sprite.png")

    user_text = f"{canon}\n\nPIXEL-LEVEL INSTRUCTIONS:\n{fix_guidance}\n\nDraw {cid} following these instructions EXACTLY. Output JSON primitives only."
    msgs = [{"role":"system","content":DRAW_SYS},{"role":"user","content":user_text}]
    if os.path.exists(old):
        msgs[1]["content"] = [
            {"type":"text","text":user_text + f"\n\nYour previous sprite (image) failed. Draw a COMPLETELY NEW one following the instructions."},
            {"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64(old)}"}},
        ]

    resp = chat(msgs, max_tokens=4000)
    best_prims = None; best_score = -1; history = []

    for i in range(max_iters):
        prims, ok = parse_prims(resp)
        if not ok or not prims:
            history.append({"iter":i,"cm":0,"error":"parse"})
            resp = chat([{"role":"system","content":DRAW_SYS},
                {"role":"user","content":f"{canon}\n\n{fix_guidance}\n\nNot valid JSON. Under 25 prims. Valid JSON only."}], max_tokens=3000)
            continue
        render_primitives(prims, tmp)
        crit = chat([
            {"role":"system","content":GATE_SYS},
            {"role":"user","content":[
                {"type":"text","text":f"{canon}\n\nImage = sprite. Does it capture {cid}? JSON only."},
                {"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64(tmp)}"}},
            ]},
        ], max_tokens=400)
        try:
            cd = json.loads(strip_json(crit))
            cm = max(0,min(10,int(cd.get("canonical_match",0))))
            rec = bool(cd.get("recognizable",False))
            missing = cd.get("features_missing",[])
        except: cm=0; rec=False; missing=["parse"]
        history.append({"iter":i,"cm":cm,"rec":rec,"missing":missing[:3]})
        print(f"    {cid} iter {i}: cm={cm}/10 rec={rec} missing={missing[:2]}", flush=True)
        if cm > best_score: best_score=cm; best_prims=prims
        if cm >= 7: print(f"    {cid} CONVERGED!", flush=True); break
        if i < max_iters-1:
            resp = chat([
                {"role":"system","content":REVISE_SYS},
                {"role":"user","content":[
                    {"type":"text","text":f"Champion: {cid}. Canon: {canon}\nINSTRUCTIONS: {fix_guidance}\nScored {cm}/10. Missing: {missing}.\nRevise. Output FULL JSON.\n\nCurrent:\n{json.dumps({'primitives':prims})[:2000]}"},
                    {"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64(tmp)}"}},
                ]},
            ], max_tokens=4000)

    if best_prims: render_primitives(best_prims, tmp)
    return {"id":cid,"best_score":best_score,"best_prims":best_prims,"history":history}

def refine_borderline(c, current_prims, current_score, max_iters=3):
    """Quick 3-iter refinement for borderline (4-5) champs."""
    cid = c["id"]
    canon = champ_canon_text(c)
    tmp = f"/tmp/vlmref_{cid}.png"
    render_primitives(current_prims, tmp)

    best_prims = current_prims; best_score = current_score
    for i in range(max_iters):
        crit = chat([
            {"role":"system","content":GATE_SYS},
            {"role":"user","content":[
                {"type":"text","text":f"{canon}\n\nImage = sprite. What's missing? JSON only."},
                {"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64(tmp)}"}},
            ]},
        ], max_tokens=400)
        try:
            cd = json.loads(strip_json(crit))
            cm = max(0,min(10,int(cd.get("canonical_match",0))))
            missing = cd.get("features_missing",[])
        except: cm=0; missing=["parse"]

        if cm > best_score: best_score=cm; best_prims=current_prims
        if cm >= 7: break

        resp = chat([
            {"role":"system","content":REFINE_SYS},
            {"role":"user","content":[
                {"type":"text","text":f"Champion: {cid}. Canon: {canon}\nScored {cm}/10. Missing: {missing}.\n"
                 f"Improve the sprite. Output FULL JSON.\n\nCurrent:\n{json.dumps({'primitives':current_prims})[:2000]}"},
                {"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64(tmp)}"}},
            ]},
        ], max_tokens=4000)
        prims, ok = parse_prims(resp)
        if ok and prims:
            render_primitives(prims, tmp)
            current_prims = prims
            # re-critique
            crit2 = chat([
                {"role":"system","content":GATE_SYS},
                {"role":"user","content":[
                    {"type":"text","text":f"{canon}\n\nImage = revised sprite. Score? JSON only."},
                    {"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64(tmp)}"}},
                ]},
            ], max_tokens=400)
            try:
                cd2 = json.loads(strip_json(crit2))
                cm2 = max(0,min(10,int(cd2.get("canonical_match",0))))
                if cm2 > best_score: best_score=cm2; best_prims=prims
            except: pass

    return {"id":cid,"best_score":best_score,"best_prims":best_prims,"history":[]}

def save_sprite(cid, prims):
    char_dir = os.path.join(ASSET_DIR, "characters", cid)
    sprites_dir = os.path.join(char_dir, "sprites")
    os.makedirs(sprites_dir, exist_ok=True)
    render_primitives(prims, os.path.join(char_dir, "sprite.png"))
    import shutil
    shutil.copy(os.path.join(char_dir, "sprite.png"), os.path.join(sprites_dir, "0.png"))
    cache_path = os.path.join(char_dir, "descriptors.json")
    cache = {}
    if os.path.exists(cache_path):
        try: cache = json.load(open(cache_path))
        except: cache = {}
    cache["0"] = {"primitives": prims, "generator": "vlm_fix3", "phase": "fix3"}
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2, default=str)

def main():
    byid = {c["id"]: c for c in CHAMPIONS_DB}

    # Load gate results to find borderline champs (score 4-5)
    gate = json.load(open("/tmp/canon_gate_results.json"))
    borderline = []
    for r in gate:
        if "gate" in r:
            cm = r["gate"]["canonical_match"]
            if 4 <= cm <= 5:  # borderline — push toward 6+
                cid = r["id"]
                # load current primitives from descriptors.json
                cache_path = os.path.join(ASSET_DIR, "characters", cid, "descriptors.json")
                try:
                    cache = json.load(open(cache_path))
                    prims = cache.get("0", {}).get("primitives", [])
                    if prims:
                        borderline.append((byid.get(cid), prims, cm))
                except: pass

    print(f"Part 1: Fix {len(HARD_FIXES)} hard champs (score <4, pixel-level guidance, max 10 iters)")
    print(f"Part 2: Refine {len(borderline)} borderline champs (score 4-5, quick 3-iter)\n")

    t0 = time.time()
    all_results = {}

    # Part 1: hard champs
    hard_champs = [(byid[cid], HARD_FIXES[cid]) for cid in HARD_FIXES if cid in byid]
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fix_hard, c, fix, 10): c["id"] for c, fix in hard_champs}
        for fut in as_completed(futs):
            try:
                r = fut.result()
                all_results[r["id"]] = r
                print(f"  HARD {r['id']:14s}: best={r['best_score']}/10  iters={len(r['history'])}", flush=True)
            except Exception as e:
                cid = futs[fut]
                print(f"  HARD {cid:14s}: ERROR {e}", flush=True)
                all_results[cid] = {"id": cid, "best_score": -1, "best_prims": None, "history": []}

    # Part 2: borderline champs
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(refine_borderline, c, prims, score, 3): c["id"] for c, prims, score in borderline if c}
        for fut in as_completed(futs):
            try:
                r = fut.result()
                all_results[r["id"]] = r
                print(f"  REFINE {r['id']:14s}: best={r['best_score']}/10", flush=True)
            except Exception as e:
                cid = futs[fut]
                print(f"  REFINE {cid:14s}: ERROR {e}", flush=True)

    # save improved sprites
    saved = 0
    for cid, r in all_results.items():
        if r["best_prims"] and r["best_score"] >= 3:
            save_sprite(cid, r["best_prims"])
            saved += 1
    print(f"\nSaved {saved} improved sprites")

    scores = [r["best_score"] for r in all_results.values()]
    mean = sum(scores)/len(scores) if scores else 0
    rec = sum(1 for s in scores if s >= 7)
    print(f"\n=== FIX ROUND 3 ({len(scores)} champs, {time.time()-t0:.0f}s) ===")
    print(f"mean: {mean:.2f}/10, recognizable (>=7): {rec}/{len(scores)}")
    for cid, r in sorted(all_results.items(), key=lambda kv: -kv[1]["best_score"]):
        print(f"  {r['best_score']:2d}/10  {cid:14s}")

    with open("/tmp/vlm_fix3_results.json", "w") as f:
        json.dump({k: {"score": v["best_score"]} for k, v in all_results.items()}, f, indent=2)

if __name__ == "__main__":
    main()
