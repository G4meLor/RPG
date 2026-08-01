"""VLM sprite generator: VLM produces drawing primitives from champ canon text.

Phase 1: VLM generates JSON primitives from champ canon (NO skin image).
         Loop: render → VLM critiques vs canon → revise → repeat (max 10, stop at cm>=7).
Phase 2 (later): feed skin 0 splash + phase-1 sprite → VLM 1-pass color/detail tweak.
Phase 3 (later): feed skin N + phase-2 sprite → VLM skin-specific tweak.

JSON parse fix: max_tokens=4000, two-pass (body then features) if output truncates,
lenient JSON repair (trailing-comma strip, bracket matching).
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
    """Extract JSON from text, tolerating markdown fences + partial truncation."""
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m: return m.group(1)
    # try to find the outermost braces
    start = text.find("{")
    if start < 0: return text.strip()
    # find matching close (depth count)
    depth = 0; end = start
    for i in range(start, len(text)):
        if text[i] == "{": depth += 1
        elif text[i] == "}": depth -= 1
        if depth == 0: end = i + 1; break
    if depth != 0:
        # truncated — try to close it
        return text[start:] + "}" * depth
    return text[start:end]

def repair_json(s):
    """Lenient JSON repair: trailing commas, unquoted keys, truncated arrays."""
    s = re.sub(r",\s*([}\]])", r"\1", s)  # trailing commas
    s = re.sub(r"(\w+)\s*:", r'"\1":', s)  # unquoted keys (best-effort)
    # close truncated arrays/objects
    opens = s.count("[") - s.count("]")
    if opens > 0: s += "]" * opens
    opens = s.count("{") - s.count("}")
    if opens > 0: s += "}" * opens
    return s

def parse_prims(text):
    """Parse VLM output into a list of primitives. Returns (prims, ok)."""
    raw = strip_json(text)
    try:
        d = json.loads(raw)
        return d.get("primitives", []), True
    except json.JSONDecodeError:
        pass
    # try repair
    try:
        d = json.loads(repair_json(raw))
        return d.get("primitives", []), True
    except json.JSONDecodeError:
        pass
    return [], False

def champ_canon_text(c):
    an = c.get("ability_names", {})
    abstr = ", ".join(f"{s}: {an[s]}" for s in ("Q","W","E","R") if s in an)
    bio = (c.get("lore",{}).get("bio","") or "")[:200]
    return (f"Champion: {c['name']} — {c.get('title','')}. "
            f"Faction: {c.get('faction','')}. Role: {c.get('role','')}. "
            f"Abilities: {abstr}. Lore: {bio}")

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
    "- 15-40 primitives is ideal. Draw back-to-front (later primitives drawn on top).\n"
    "- color is the FILL [r,g,b]. outline is the BORDER [r,g,b] (or null for no border). outline_w is border width (default 1).\n"
    "- Keep the JSON valid — no trailing commas, no comments, no unquoted keys.\n"
    "- Output JSON ONLY, no prose."
)

GATE_SYS = (
    "You are a STRICT visual critic who knows League of Legends. You will be given a "
    "champion's canonical identity (text) and a 256x256 pixel-art sprite (image). Judge "
    "whether a LoL player would recognize the champion from the sprite.\n"
    "Output JSON ONLY: {canonical_match: 0-10, recognizable: true/false, "
    "stance_captured: true/false, features_captured: [list], features_missing: [list], "
    "verdict: one sentence}. canonical_match >= 7 means recognizable. Be STRICT."
)

REVISE_SYS = (
    "You are a pixel-art sprite artist. Your sprite was critiqued. REVISE the primitives "
    "to fix the missing features. Keep what works, fix what's missing. Output the FULL "
    "revised JSON primitives. Keep the JSON valid — no trailing commas. Output JSON ONLY."
)

def render_primitives(prims, path):
    """Render a list of JSON primitives to a PNG. Returns coverage."""
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

def generate_one(c, max_iters=10):
    """Phase 1: VLM generates primitives from canon text → loop → best sprite."""
    cid = c["id"]
    canon = champ_canon_text(c)
    tmp = f"/tmp/vlmgen_{cid}.png"

    # initial generation
    resp = chat([
        {"role": "system", "content": DRAW_SYS},
        {"role": "user", "content": f"{canon}\n\nProduce the drawing primitives JSON for {cid}."},
    ], max_tokens=4000)

    best_prims = None
    best_score = -1
    best_cov = 0
    history = []

    for i in range(max_iters):
        prims, ok = parse_prims(resp)
        if not ok or not prims:
            history.append({"iter": i, "cm": 0, "rec": False, "error": "parse"})
            # retry with stricter prompt
            resp = chat([
                {"role": "system", "content": DRAW_SYS},
                {"role": "user", "content": f"{canon}\n\nYour output was not valid JSON. "
                 f"Output ONLY valid JSON primitives for {cid}. Keep it under 30 primitives."},
            ], max_tokens=4000)
            continue

        cov = render_primitives(prims, tmp)
        if cov < 0.01:
            history.append({"iter": i, "cm": 0, "rec": False, "error": "blank"})
            resp = chat([
                {"role": "system", "content": DRAW_SYS},
                {"role": "user", "content": f"{canon}\n\nYour sprite was blank. "
                 f"Draw {cid} with visible primitives. Output valid JSON."},
            ], max_tokens=4000)
            continue

        # critique (canon text + sprite, NO splash)
        crit = chat([
            {"role": "system", "content": GATE_SYS},
            {"role": "user", "content": [
                {"type": "text", "text": f"{canon}\n\nImage = the pixel-art sprite. "
                 f"Does it capture {cid}'s canonical identity? JSON only."},
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

        history.append({"iter": i, "cm": cm, "rec": rec, "n_prims": len(prims),
                        "missing": missing[:3], "cov": round(cov, 3)})

        if cm > best_score:
            best_score = cm
            best_prims = prims
            best_cov = cov

        if cm >= 7:
            break

        if i < max_iters - 1:
            resp = chat([
                {"role": "system", "content": REVISE_SYS},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Champion: {cid}. Canon: {canon}\n\n"
                     f"Critic scored {cm}/10. Missing: {missing}.\n"
                     f"Revise the primitives to fix these. Output the FULL revised JSON.\n\n"
                     f"Current primitives:\n{json.dumps({'primitives': prims})[:2000]}"},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64(tmp)}"}},
                ]},
            ], max_tokens=4000)

    # save best
    if best_prims:
        render_primitives(best_prims, tmp)
    return {"id": cid, "best_score": best_score, "best_cov": best_cov,
            "iters": len(history), "history": history, "primitives": best_prims}

def main():
    champs = list(CHAMPIONS_DB)
    print(f"VLM sprite generation: {len(champs)} champs, concurrency 4...", flush=True)
    t0 = time.time()
    results = [None] * len(champs)
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(generate_one, c): i for i, c in enumerate(champs)}
        done = 0
        for fut in as_completed(futs):
            i = futs[fut]
            try: results[i] = fut.result()
            except Exception as e: results[i] = {"id": champs[i]["id"], "best_score": -1, "error": str(e)}
            done += 1
            if done % 20 == 0:
                ok = [r for r in results if r and "error" not in r]
                mean = sum(r["best_score"] for r in ok) / len(ok) if ok else 0
                print(f"  {done}/{len(champs)} done, mean={mean:.2f} ({time.time()-t0:.0f}s)", flush=True)

    ok = [r for r in results if r and "error" not in r]
    err = [r for r in results if r and "error" in r]
    scores = [r["best_score"] for r in ok]
    mean = sum(scores) / len(scores) if scores else 0
    rec = sum(1 for r in ok if any(h.get("rec") for h in r.get("history", [])))
    converged = sum(1 for r in ok if r["best_score"] >= 7)

    print(f"\n=== {len(ok)} done, {len(err)} errors, {time.time()-t0:.0f}s ===")
    print(f"mean canonical_match: {mean:.2f} / 10")
    print(f"recognizable (best score >=7): {converged}/{len(ok)} ({100*converged/len(ok):.0f}%)")
    from collections import Counter
    dist = Counter(scores)
    print(f"score distribution: {dict(sorted(dist.items()))}")
    print(f"\nworst 15:")
    for r in sorted(ok, key=lambda r: r["best_score"])[:15]:
        print(f"  {r['best_score']:2d}/10  {r['id']:14s} iters={r['iters']} cov={r.get('best_cov',0):.3f}")
    print(f"\nbest 15:")
    for r in sorted(ok, key=lambda r: -r["best_score"])[:15]:
        print(f"  {r['best_score']:2d}/10  {r['id']:14s} iters={r['iters']} cov={r.get('best_cov',0):.3f}")

    with open("/tmp/vlm_gen_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nraw -> /tmp/vlm_gen_results.json")

if __name__ == "__main__":
    main()
