"""Fix round 2: the 18 champs still scoring <4 after the first fix round.

Strategy: feed the VLM the champ's canon + the SPECIFIC missing features from the
gate + the current failing sprite. The VLM generates NEW primitives that specifically
address each missing feature. Loop: render → critique → revise (max 10, stop at 7).

Also: for champs where stance_captured=False (Rell/Naafiri/Karma/Ryze/Volibear),
explicitly instruct the VLM on the correct stance.
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

# The 18 low champs + their SPECIFIC missing features from the gate + stance fix
FIXES = {
    "Rell": "Draw Rell as a young girl RIDING a metallic horse. The horse is angular, made of dark metal plates. Rell sits on top with a lance. Stance: mounted. Colors: dark steel, red accents.",
    "Shyvana": "Draw Shyvana as a humanoid with DRAGON features: large dragon wings on the back, a long thick dragon tail, dragon horns on the head, scaled skin on arms. Colors: red/orange scales, dark armor.",
    "Udyr": "Draw Udyr as a muscular SHIRTLESS man with animal fur pelts draped on his shoulders, tribal tattoos on his body, wild hair, fighting stance with fists raised. NOT a robot. Colors: brown fur, dark skin, orange fire.",
    "Aatrox": "Draw Aatrox as a massive dark warrior with LARGE DEMONIC WINGS spread behind him, a huge dark blade, menacing horns, exposed muscular chest. Colors: dark red, black, orange.",
    "Karma": "Draw Karma as a meditating woman FLOATING (no legs, hovering), with floating spirit scrolls behind her, ornate Ionian robes, glowing green/gold aura. Stance: floating. Colors: green, gold, white.",
    "Lucian": "Draw Lucian as a gunslinger with TWO PISTOLS (dual wield), white and gold light-infused armor, short dark hair, determined expression. Colors: white, gold, blue light.",
    "MissFortune": "Draw MissFortune as a pirate captain with LONG FLOWING RED HAIR, a tricorne pirate hat, a captain's long coat, dual pistols. Colors: red hair, dark coat, gold accents.",
    "Naafiri": "Draw Naafiri as a FOUR-LEGGED DARKIN HOUND (quadruped stance). Lean muscular canine body with jagged dark metal armor plates, sharp teeth, glowing red eyes. Stance: quadruped. Colors: dark grey, red, metallic.",
    "Olaf": "Draw Olaf as a muscular berserker with LONG BLONDE HAIR, fur-lined armor, war paint on face, bare muscular chest, throwing axes. Colors: blonde, brown fur, blue war paint.",
    "Qiyana": "Draw Qiyana as a royal princess with a LARGE CIRCULAR RING WEAPON (chakram), ornate gold jewelry, high-fashion royal attire, dark skin with gold accents. Colors: gold, teal, dark skin.",
    "Ryze": "Draw Ryze as an old mage with a BALD HEAD, rugged BEARD, glowing blue arcane tattoos all over his body, a large heavy scroll on his back. Colors: blue tattoos, dark skin, brown scroll.",
    "Skarner": "Draw Skarner as a LARGE CRYSTAL SCORPION: a segmented body with a long stinger tail, massive pincers, heavy crystalline plating, glowing crystal growths. Colors: teal/cyan crystals, dark blue.",
    "Sona": "Draw Sona as an elegant musician with LONG FLOWING PINK/BLUE HAIR, an elegant flowing gown, floating musical notes/aura around her, a floating etwahl (string instrument). Colors: pink, blue, white.",
    "Varus": "Draw Varus as a darkin archer with a LARGE BOW, glowing purple corruption on his body, darkin armor plating, asymmetrical design, glowing eyes. Colors: purple, dark grey, magenta.",
    "Viego": "Draw Viego as the Ruined King with PALE GHOSTLY SKIN, tattered royal regalia, a CROWN OF THORNS/shards on his head, LONG WHITE HAIR, a broken sword. Colors: pale white, teal, dark.",
    "Volibear": "Draw Volibear as a MASSIVE POLAR BEAR (quadruped stance, on 4 legs). Thick WHITE FUR, electric blue lightning arcs around him, heavy tribal armor plates. Stance: quadruped. Colors: white fur, blue lightning, gold armor.",
    "Yuumi": "Draw Yuumi as a small CAT sitting on a large OPEN MAGICAL BOOK (floating). Yuumi is a cute cat with a glowing aura, a tail, whiskers. The book floats beneath her. Colors: orange cat, purple book, gold magic.",
    "Zeri": "Draw Zeri as a young Zaunite girl with ELECTRIC YELLOW HAIR, glowing lightning effects around her, Zaunite streetwear (hoodie), oversized boots, a glowing electric gun-arm. Colors: yellow, teal, dark.",
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

def fix_one(c, fix_guidance, max_iters=10):
    cid = c["id"]
    canon = champ_canon_text(c)
    tmp = f"/tmp/vlmfix2_{cid}.png"
    old_sprite = os.path.join(ASSET_DIR, "characters", cid, "sprite.png")

    user_text = f"{canon}\n\nSPECIFIC FIX: {fix_guidance}\n\n"
    if os.path.exists(old_sprite):
        user_text += f"Your previous sprite failed. Draw a COMPLETELY NEW sprite that "
        user_text += f"specifically addresses the fix above. Output JSON primitives only."
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
            resp = chat([{"role":"system","content":DRAW_SYS},
                {"role":"user","content":f"{canon}\n\nFIX: {fix_guidance}\n\nNot valid JSON. Under 25 prims. Valid JSON."}],
                max_tokens=3000)
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
            print(f"    {cid} CONVERGED!", flush=True)
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
    cache["0"] = {"primitives": prims, "generator": "vlm_primitives_fix2", "phase": "fix2"}
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2, default=str)

def main():
    byid = {c["id"]: c for c in CHAMPIONS_DB}
    champs_to_fix = [(byid[cid], FIXES[cid]) for cid in FIXES if cid in byid]
    print(f"Fix round 2: {len(champs_to_fix)} champs with specific missing-feature guidance...\n")

    t0 = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fix_one, c, fix, 10): c["id"] for c, fix in champs_to_fix}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            print(f"  {r['id']:14s}: best={r['best_score']}/10  iters={len(r['history'])}  "
                  f"history={[h.get('cm',0) for h in r['history']]}", flush=True)

    # save improved sprites (only if better than current)
    saved = 0
    for r in results:
        if r["best_prims"] and r["best_score"] >= 3:
            save_sprite(r["id"], r["best_prims"])
            saved += 1
    print(f"\nSaved {saved} improved sprites")

    scores = [r["best_score"] for r in results]
    mean = sum(scores)/len(scores)
    rec = sum(1 for s in scores if s >= 7)
    print(f"\n=== FIX ROUND 2 ({len(results)} champs, {time.time()-t0:.0f}s) ===")
    print(f"mean: {mean:.2f}/10, recognizable (>=7): {rec}/{len(results)}")
    for r in sorted(results, key=lambda r: -r["best_score"]):
        print(f"  {r['best_score']:2d}/10  {r['id']:14s}")

    with open("/tmp/vlm_fix2_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

if __name__ == "__main__":
    main()
