"""Test 512px VLM sprite generation vs the 256px baseline.

Hypothesis: 256px is too small for the VLM 31b to render fine features (facial
markings, attire detail, proportions). At 512px the VLM has 4x the pixel budget
→ finer features → higher canonical_match.

Runtime is unaffected: the loader (load_char_sprite) smoothscales any source
size to the 96px display size. So 512px source works with ZERO runtime changes.
This is generation-only.

Method (the PROVEN approach — single fresh pass from canon text, no revision
loop, which is what produced all the 8/10 sprites):
  - Generate FRESH at 512x512 from canon text. Best-of-2 (one at t=0.3, one at
    t=0.5). No revision loop.
  - Gate each at 512px with the canon gate (text + 512px sprite image).
  - Compare to the committed 256px sprite's gate score.

Test set (8 champs):
  - 2 already-8/10 (Seraphine, Vi): does 512px match/beat the proven 256px?
  - 4 score-6 (Darius, Fiora, Brand, Katarina): does 512px push them to 7?
  - 2 hard <4 (Sona, Shyvana): does 512px help the hardest cases?

Results -> exp/gen512_test_results.json.
"""
import os, sys, json, base64, ssl, urllib.request, re, time, shutil
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

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
SIZE = 512  # the new generation size
CENTER = (SIZE // 2, int(SIZE * 0.585))  # body center, scaled from 256's (128,150)

TEST_CHAMPS = ["Seraphine", "Vi", "Darius", "Fiora", "Brand", "Katarina", "Sona", "Shyvana"]


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def chat(messages, max_tokens=6000, temperature=0.4, timeout=300):
    for attempt in range(3):
        try:
            body = json.dumps({"model": MODEL, "messages": messages,
                               "max_tokens": max_tokens, "temperature": temperature}).encode()
            req = urllib.request.Request(BASE + "/chat/completions", data=body,
                headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except Exception:
            if attempt < 2:
                time.sleep(5)
                continue
            raise


def strip_json(text):
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    start = text.find("{")
    if start < 0:
        return text.strip()
    depth = 0; end = start
    for i in range(start, len(text)):
        if text[i] == "{": depth += 1
        elif text[i] == "}": depth -= 1
        if depth == 0: end = i + 1; break
    if depth != 0:
        return text[start:] + "}" * depth
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
            if isinstance(d, list):
                return d, True
            return d.get("primitives", []), True
        except json.JSONDecodeError:
            if attempt == 0:
                raw = repair_json(raw)
            elif attempt == 1:
                m = re.search(r'\[.*\]', raw, re.DOTALL)
                if m:
                    try:
                        return json.loads(m.group(0)), True
                    except Exception:
                        pass
                return [], False
            else:
                return [], False
    return [], False


def champ_canon_text(c):
    an = c.get("ability_names", {})
    abstr = ", ".join(f"{s}: {an[s]}" for s in ("Q", "W", "E", "R") if s in an)
    bio = (c.get("lore", {}).get("bio", "") or "")[:200]
    return (f"Champion: {c['name']} — {c.get('title', '')}. "
            f"Faction: {c.get('faction', '')}. Role: {c.get('role', '')}. "
            f"Abilities: {abstr}. Lore: {bio}")


def render_primitives(prims, path, size=SIZE):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for p in prims:
        try:
            t = p.get("type", "")
            col = tuple(p.get("color", [200, 200, 200])[:3])
            ol = p.get("outline")
            ol = tuple(ol[:3]) if ol else None
            ow = p.get("outline_w", 1)
            if t == "circle":
                r = max(1, p.get("r", 5))
                cx, cy = p.get("cx", size // 2), p.get("cy", size // 2)
                pygame.draw.circle(surf, col, (cx, cy), r)
                if ol: pygame.draw.circle(surf, ol, (cx, cy), r, ow)
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
                s_, e_ = p.get("start", [0, 0]), p.get("end", [0, 0])
                pygame.draw.line(surf, col, (int(s_[0]), int(s_[1])), (int(e_[0]), int(e_[1])), max(1, p.get("width", 1)))
            elif t == "ellipse":
                w, h = max(1, p.get("w", 10)), max(1, p.get("h", 10))
                rect = pygame.Rect(p.get("x", 0), p.get("y", 0), w, h)
                pygame.draw.ellipse(surf, col, rect)
                if ol: pygame.draw.ellipse(surf, ol, rect, ow)
        except Exception:
            continue
    pygame.image.save(surf, path)
    return surf


# Fresh generation at 512px — single pass from canon text (the proven approach).
DRAW_SYS = (
    "You are a pixel-art sprite artist. You will be given a League of Legends "
    "champion's canonical identity (name, title, lore, abilities). Draw a "
    f"{SIZE}x{SIZE} FULL-BODY pixel-art world sprite of this champion.\n\n"
    "Output JSON ONLY:\n"
    '{"primitives": [\n'
    '  {"type":"circle","cx":int,"cy":int,"r":int,"color":[r,g,b],"outline":[r,g,b],"outline_w":int},\n'
    '  {"type":"rect","x":int,"y":int,"w":int,"h":int,"color":[r,g,b],"outline":[r,g,b],"outline_w":int,"radius":int},\n'
    '  {"type":"polygon","points":[[x,y],...],"color":[r,g,b],"outline":[r,g,b],"outline_w":int},\n'
    '  {"type":"line","start":[x,y],"end":[x,y],"color":[r,g,b],"width":int},\n'
    '  {"type":"ellipse","x":int,"y":int,"w":int,"h":int,"color":[r,g,b],"outline":[r,g,b],"outline_w":int}\n'
    "]}\n\n"
    f"Rules:\n"
    f"- All coordinates 0-{SIZE-1}. The sprite is {SIZE}x{SIZE}. "
    f"Body center ~ ({CENTER[0]}, {CENTER[1]}). Draw a FRONT-FACING full body.\n"
    "- Draw the FULL BODY: head, torso, arms, legs, weapon, and ALL signature features.\n"
    "- Use the champion's CANONICAL colors (from your LoL knowledge).\n"
    "- Be SPECIFIC and CREATIVE — draw THIS champion's signature look, not a generic humanoid.\n"
    f"- At {SIZE}px you have room for DETAIL: facial features (eyes, markings, expression), "
    f"attire texture, armor segments, hair strands. USE the resolution — a face is ~60px wide, "
    f"eyes ~12px, a weapon ~80-160px, wings ~120-200px. Draw fine features, not just big blocks.\n"
    "- 25-60 primitives is typical. Draw back-to-front. Output JSON ONLY, no prose."
)

GATE_SYS = (
    "You are a STRICT visual critic who knows League of Legends. Given a "
    f"champion's canonical identity (text) and a {SIZE}x{SIZE} pixel-art sprite (image), "
    "judge whether a LoL player would recognize the champion.\n"
    "Output JSON ONLY: {canonical_match: 0-10, recognizable: true/false, "
    "features_captured: [list], features_missing: [list], verdict: one sentence}. "
    "canonical_match >= 7 means recognizable. Be STRICT."
)


def critique(canon, cid, img_path):
    crit = chat([
        {"role": "system", "content": GATE_SYS},
        {"role": "user", "content": [
            {"type": "text", "text": f"{canon}\n\nImage = the pixel-art sprite. "
             f"Does it capture {cid}'s canonical identity? JSON only."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64(img_path)}"}},
        ]},
    ], max_tokens=400)
    try:
        cd = json.loads(strip_json(crit))
        cm = max(0, min(10, int(cd.get("canonical_match", 0))))
        rec = bool(cd.get("recognizable", False))
        missing = cd.get("features_missing", [])
        verdict = cd.get("verdict", "")
        if isinstance(missing, str):
            missing = [missing]
        return cm, rec, missing, verdict
    except Exception:
        return 0, False, ["parse error"], "parse error"


def gen_512_bestof2(c):
    """Fresh gen at 512px, best-of-2 (t=0.3, t=0.5). Returns (best_prims, best_cm)."""
    cid = c["id"]
    canon = champ_canon_text(c)
    best_prims = None
    best_cm = -1
    for n_i, temp in enumerate([0.3, 0.5]):
        tmp = f"/tmp/gen512_{cid}_{n_i}.png"
        resp = chat([
            {"role": "system", "content": DRAW_SYS},
            {"role": "user", "content": f"{canon}\n\nProduce the drawing primitives JSON for {cid}. "
             f"Be specific to {cid}'s signature look. Use the {SIZE}px resolution for detail."},
        ], max_tokens=6000, temperature=temp)
        prims, ok = parse_prims(resp)
        if not ok or not prims:
            print(f"    {cid} attempt {n_i} (t={temp}): PARSE FAIL", flush=True)
            continue
        render_primitives(prims, tmp)
        cm, rec, missing, _ = critique(canon, cid, tmp)
        print(f"    {cid} attempt {n_i} (t={temp}): cm={cm}/10 rec={rec} prims={len(prims)} miss={missing[:2]}", flush=True)
        if cm > best_cm:
            best_cm = cm
            best_prims = prims
    return best_prims, best_cm


def main():
    byid = {c["id"]: c for c in CHAMPIONS_DB}
    gate = json.load(open(os.path.join(EXP_DIR, "canon_gate_results.json")))
    base_256 = {item["id"]: item["gate"]["canonical_match"] for item in gate if "gate" in item}

    print(f"512px VLM generation test (vs 256px baseline)")
    print(f"  {len(TEST_CHAMPS)} champs, best-of-2 fresh gen, no revision loop")
    print(f"  size={SIZE}, body center {CENTER}\n")

    t0 = time.time()
    results = {}

    # Run concurrently (4 workers)
    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(gen_512_bestof2, byid[cid]): cid for cid in TEST_CHAMPS if cid in byid}
        for fut in as_completed(futs):
            cid = futs[fut]
            try:
                prims, cm = fut.result()
                b = base_256.get(cid, 0)
                delta = cm - b
                tag = "512 BEATS 256" if cm > b else ("512 == 256" if cm == b else "256 BETTER")
                print(f"  {cid:14s}: 512={cm}/10 (256 baseline {b}, {'+' if delta>=0 else ''}{delta})  {tag}", flush=True)
                results[cid] = {"base_256": b, "gen_512": cm, "delta": delta,
                                "prims": len(prims) if prims else 0, "best_prims": prims}
            except Exception as e:
                print(f"  {cid:14s}: ERROR {e}", flush=True)
                results[cid] = {"base_256": base_256.get(cid, 0), "gen_512": -1, "delta": -99, "error": str(e)}

    # Summary
    valid = [r for r in results.values() if r.get("gen_512", -1) >= 0]
    beats = sum(1 for r in valid if r["delta"] > 0)
    ties = sum(1 for r in valid if r["delta"] == 0)
    worse = sum(1 for r in valid if r["delta"] < 0)
    print(f"\n=== 512px TEST ({len(valid)} champs, {time.time()-t0:.0f}s) ===")
    print(f"512 beats 256: {beats}/{len(valid)}")
    print(f"512 == 256:    {ties}/{len(valid)}")
    print(f"256 better:    {worse}/{len(valid)}")
    if valid:
        mean_delta = sum(r["delta"] for r in valid) / len(valid)
        print(f"mean delta: {mean_delta:+.2f}")

    # Save the 512px sprites that BEAT 256 to /tmp for inspection (not committed yet)
    saved = 0
    for cid, r in results.items():
        if r.get("best_prims") and r.get("gen_512", -1) > r.get("base_256", 0):
            tmp = f"/tmp/gen512_best_{cid}.png"
            render_primitives(r["best_prims"], tmp)
            saved += 1
    print(f"saved {saved} winning 512px sprites to /tmp/gen512_best_*.png (inspect before committing)")

    with open(os.path.join(EXP_DIR, "gen512_test_results.json"), "w") as f:
        # don't dump the full prims (big); just scores
        out = {cid: {k: v for k, v in r.items() if k != "best_prims"} for cid, r in results.items()}
        json.dump(out, f, indent=2)
    print(f"results -> exp/gen512_test_results.json")


if __name__ == "__main__":
    main()
