"""Fix the 15 low-score champs: targeted re-generation with specific fix guidance.

For each low champ, feed the VLM:
1. The champ's canon identity
2. The root-cause diagnosis (from the previous analysis)
3. The fix suggestion
4. The current sprite (so VLM sees what to fix)

The VLM generates NEW primitives with the specific fix applied. Loop: render →
critique → revise (max 8 iters, stop at cm>=7). Save the best.
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

# The 15 low champs + their specific fix guidance from the root-cause diagnosis
FIXES = {
    "Sejuani": "Draw Sejuani RIDING a large boar mount (Bristle). The boar should be a big furry body at the bottom with tusks. Sejuani sits on top holding a flail. Colors: white fur, blue ice armor.",
    "Shyvana": "Draw Shyvana as a humanoid with dragon features: dragon wings on the back, a long dragon tail, scales on the arms, horns on the head. Colors: red/orange dragon scales, dark armor.",
    "Udyr": "Draw Udyr as a muscular shirtless man with animal pelt/ fur on his shoulders, tribal tattoos, fighting stance with fists. NOT a robot. Colors: brown fur, dark skin, orange fire energy.",
    "Akshan": "Draw Akshan as a dashing rogue with a distinctive grappling hook gun weapon, stylish white/gold Sentinel attire, dark skin, confident pose. Colors: white, gold, teal accents.",
    "Aurora": "Draw Aurora as a young witch with a large fluffy spirit-fox companion beside her, flowing ethereal blue/purple robes, glowing spirit energy. NOT a generic wizard.",
    "Janna": "Draw Janna as a floating ethereal woman with flowing wind-swept hair and robes, bare feet (floating), a staff. Feminine silhouette. Colors: white, light blue, teal.",
    "Kayn": "Draw Kayn as a lean athletic shadow assassin with a large scythe weapon (The Darkin Scythe), dark purple/shadow energy, hooded outfit. Lean silhouette, NOT blocky.",
    "Lissandra": "Draw Lissandra with an ice-shard crown on her head, ornate blue ice-armor, a feminine silhouette, dark skin, glowing blue eyes. Colors: dark blue, ice blue, black.",
    "Nilah": "Draw Nilah as an aquatic warrior with blue/teal color palette, a flowing water-whip weapon, joyful dynamic pose, scale-like armor. Colors: blue, teal, gold accents.",
    "Morgana": "Draw Morgana with large dark drooping wings, a dark purple dress, restrained posture (chains), purple magic. NOT a cone shape. Colors: dark purple, black, magenta.",
    "Rakan": "Draw Rakan as a flamboyant bird-man with colorful feathered wings spread wide, a dynamic dancing pose, bright orange/yellow/gold feathers. Flowing, NOT rigid.",
    "Rell": "Draw Rell as a young girl riding a metallic horse construct (she controls metal). The horse should be angular, metallic. Rell sits on top with a lance. Colors: dark metal, red accents.",
    "Senna": "Draw Senna with a large ornate cannon weapon (her signature), flowing white hair, dark skin, dark coat, shadow energy. The cannon is her most iconic feature.",
    "Tryndamere": "Draw Tryndamere as a muscular barbarian with long flowing red/white hair, a massive greatsword, bare muscular chest, fur loincloth, angry expression. NOT a cone hat.",
    "Zyra": "Draw Zyra as a plant-woman with vine-like limbs, thorn protrusions, a flower-like head, green skin/leaves. Organic, NOT geometric. Colors: green, dark green, pink/red flowers.",
}

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
    a = pygame.surfarray.pixels_alpha(surf); arr = a.__array__(); del a
    cov = float((arr > 8).sum()) / (256 * 256)
    return cov

DRAW_SYS = (
    "You are a pixel-art sprite artist. You will be given a League of Legends champion's "
    "canonical identity AND specific fix guidance. Produce a JSON description of the "
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
    "- Draw the FULL BODY + ALL signature features mentioned in the fix guidance.\n"
    "- Use the champion's CANONICAL colors (specified in the fix guidance).\n"
    "- 15-35 primitives. Draw back-to-front. Keep JSON valid. Output JSON ONLY."
)

GATE_SYS = (
    "You are a STRICT visual critic who knows League of Legends. You will be given a "
    "champion's canonical identity (text) and a 256x256 pixel-art sprite (image). Judge "
    "whether a LoL player would recognize the champion from the sprite.\n"
    "Output JSON ONLY: {canonical_match: 0-10, recognizable: true/false, "
    "features_captured: [list], features_missing: [list], verdict: one sentence}. "
    "canonical_match >= 7 means recognizable. Be STRICT."
)

REVISE_SYS = (
    "You are a pixel-art sprite artist. Your sprite was critiqued. REVISE the primitives "
    "to fix the missing features. Output the FULL revised JSON primitives. Keep JSON valid."
)

def fix_one(c, fix_guidance, max_iters=8):
    cid = c["id"]
    canon = champ_canon_text(c)
    tmp = f"/tmp/vlmfix_{cid}.png"
    old_sprite = os.path.join(ASSET_DIR, "characters", cid, "sprite.png")

    # initial generation with fix guidance
    user_text = f"{canon}\n\nSPECIFIC FIX: {fix_guidance}\n\n"
    if os.path.exists(old_sprite):
        user_text += f"Your previous sprite (image) failed because of the issue above. "
        user_text += f"Draw a NEW sprite that fixes it. Output JSON primitives only."
    else:
        user_text += f"Produce the drawing primitives JSON for {cid}."

    messages = [{"role": "system", "content": DRAW_SYS}, {"role": "user", "content": user_text}]
    if os.path.exists(old_sprite):
        messages[1]["content"] = [
            {"type": "text", "text": user_text},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64(old_sprite)}"}},
        ]

    resp = chat(messages, max_tokens=4000)
    best_prims = None; best_score = -1; history = []

    for i in range(max_iters):
        prims, ok = parse_prims(resp)
        if not ok or not prims:
            history.append({"iter": i, "cm": 0, "error": "parse"})
            resp = chat([
                {"role": "system", "content": DRAW_SYS},
                {"role": "user", "content": f"{canon}\n\nFIX: {fix_guidance}\n\n"
                 f"Output was not valid JSON. Draw {cid} with the fix. Under 25 primitives. Valid JSON."},
            ], max_tokens=3000)
            continue

        cov = render_primitives(prims, tmp)
        if cov < 0.01:
            history.append({"iter": i, "cm": 0, "error": "blank"})
            resp = chat([{"role":"system","content":DRAW_SYS},
                {"role":"user","content":f"{canon}\n\nFIX: {fix_guidance}\n\nSprite blank. Draw {cid} visibly. Valid JSON."}],
                max_tokens=3000)
            continue

        crit = chat([
            {"role": "system", "content": GATE_SYS},
            {"role": "user", "content": [
                {"type": "text", "text": f"{canon}\n\nImage = the pixel-art sprite. Does it capture {cid}? JSON only."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64(tmp)}"}},
            ]},
        ], max_tokens=400)
        try:
            cd = json.loads(strip_json(crit))
            cm = max(0, min(10, int(cd.get("canonical_match", 0))))
            rec = bool(cd.get("recognizable", False))
            missing = cd.get("features_missing", [])
        except Exception:
            cm = 0; rec = False; missing = ["parse error"]

        history.append({"iter": i, "cm": cm, "rec": rec, "missing": missing[:3]})
        print(f"    {cid} iter {i}: cm={cm}/10 rec={rec} missing={missing[:2]}", flush=True)

        if cm > best_score:
            best_score = cm
            best_prims = prims

        if cm >= 7:
            print(f"    {cid} CONVERGED at iter {i}!", flush=True)
            break

        if i < max_iters - 1:
            resp = chat([
                {"role": "system", "content": REVISE_SYS},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Champion: {cid}. Canon: {canon}\n"
                     f"FIX NEEDED: {fix_guidance}\n"
                     f"Scored {cm}/10. Missing: {missing}.\n"
                     f"Revise to fix these. Output FULL JSON.\n\n"
                     f"Current:\n{json.dumps({'primitives': prims})[:2000]}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64(tmp)}"}},
                ]},
            ], max_tokens=4000)

    if best_prims:
        render_primitives(best_prims, tmp)
    return {"id": cid, "best_score": best_score, "best_prims": best_prims, "history": history}

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
    cache["0"] = {"primitives": prims, "generator": "vlm_primitives_fix", "phase": "fix"}
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2, default=str)

def main():
    byid = {c["id"]: c for c in CHAMPIONS_DB}
    champs_to_fix = [(byid[cid], FIXES[cid]) for cid in FIXES if cid in byid]
    print(f"Fixing {len(champs_to_fix)} low-score champs with targeted guidance...\n")

    t0 = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fix_one, c, fix, 8): c["id"] for c, fix in champs_to_fix}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            print(f"  {r['id']:14s}: best={r['best_score']}/10  iters={len(r['history'])}  "
                  f"history={[h.get('cm',0) for h in r['history']]}", flush=True)

    # save improved sprites
    improved = 0
    for r in results:
        if r["best_prims"] and r["best_score"] >= 3:  # only save if at least 3
            save_sprite(r["id"], r["best_prims"])
            improved += 1
    print(f"\nSaved {improved} improved sprites")

    scores = [r["best_score"] for r in results]
    mean = sum(scores)/len(scores)
    rec = sum(1 for s in scores if s >= 7)
    print(f"\n=== FIX RESULTS ({len(results)} champs, {time.time()-t0:.0f}s) ===")
    print(f"mean: {mean:.2f}/10")
    print(f"recognizable (>=7): {rec}/{len(results)}")
    for r in sorted(results, key=lambda r: -r["best_score"]):
        print(f"  {r['best_score']:2d}/10  {r['id']:14s}")

    with open("/tmp/vlm_fix_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

if __name__ == "__main__":
    main()
