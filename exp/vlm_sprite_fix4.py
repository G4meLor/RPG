"""Fix round 4: ADDITIVE PATCHES (not full regeneration).

Root-cause lesson from fix3: asking the VLM to output the FULL revised JSON
regenerates the whole sprite and routinely LOSES the good base — score-3 hard
champs got WORSE (Sona 3->2, Zeri 3->2). The VLM 31b can't cleanly re-render
complex multi-feature champs in one pass.

New mechanism — ADDITIVE PATCH:
  1. Keep the existing primitives (the good base) untouched.
  2. Critique the current sprite -> get the missing features.
  3. Ask the VLM to output ONLY the new primitives needed for those missing
     features (never repeat existing ones).
  4. Append the patch to the existing primitives, re-render.
  5. Re-critique. Keep if improved; never regress below the base.

This guarantees we never lose the working base and only ever ADD detail.

Targets (highest leverage toward the gate):
  - 53 champs at score 6 (1 pt from recognizable >=7). Pushing ~26 to 7
    -> ~122/170 = 72% recognizable -> hits the 70% target.
  - 4 hard champs still <4 (Sona/Shyvana/Renata/Zeri) — additive patches
    on their existing base instead of regenerate-from-scratch.

Results -> exp/vlm_fix4_results.json (NOT /tmp, per user directive).
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


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def chat(messages, max_tokens=4000, temperature=0.3, timeout=300):
    for attempt in range(3):
        try:
            body = json.dumps({"model": MODEL, "messages": messages,
                               "max_tokens": max_tokens, "temperature": temperature}).encode()
            req = urllib.request.Request(BASE + "/chat/completions", data=body,
                headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except Exception as e:
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
    """Parse a primitives list. Accepts either {primitives:[...]} or a bare [...]."""
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
                cx, cy = p.get("cx", 128), p.get("cy", 128)
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


GATE_SYS = (
    "You are a STRICT visual critic who knows League of Legends. Given a "
    "champion's canonical identity (text) and a 256x256 pixel-art sprite (image), "
    "judge whether a LoL player would recognize the champion.\n"
    "Output JSON ONLY: {canonical_match: 0-10, recognizable: true/false, "
    "features_captured: [list], features_missing: [list], verdict: one sentence}. "
    "canonical_match >= 7 means recognizable. Be STRICT."
)

# The additive-patch prompt: output ONLY new primitives, never repeat existing.
PATCH_SYS = (
    "You are a pixel-art sprite artist. You will be shown a champion's current "
    "256x256 pixel-art sprite (image) and told which canonical features are MISSING. "
    "Your job is to ADD those missing features ONLY.\n\n"
    "Output JSON: a list of NEW drawing primitives to draw ON TOP of the existing "
    "sprite. Do NOT redraw the whole sprite — only the primitives needed for the "
    "missing features. They will be appended after the existing primitives (drawn on top).\n\n"
    "Primitive types:\n"
    '  {"type":"circle","cx":int,"cy":int,"r":int,"color":[r,g,b],"outline":[r,g,b],"outline_w":int}\n'
    '  {"type":"rect","x":int,"y":int,"w":int,"h":int,"color":[r,g,b],"outline":[r,g,b],"outline_w":int,"radius":int}\n'
    '  {"type":"polygon","points":[[x,y],...],"color":[r,g,b],"outline":[r,g,b],"outline_w":int}\n'
    '  {"type":"line","start":[x,y],"end":[x,y],"color":[r,g,b],"width":int}\n'
    '  {"type":"ellipse","x":int,"y":int,"w":int,"h":int,"color":[r,g,b],"outline":[r,g,b],"outline_w":int}\n\n'
    "Rules: coords 0-255, 256x256, body center ~(128,150). Use the champion's "
    "CANONICAL colors. Be SPECIFIC to the missing features. Output JSON ONLY: "
    "either {\"primitives\":[...]} or a bare [...].\n\n"
    "CRITICAL — VISIBILITY: at 256x256, a feature must be LARGE enough to read. "
    "A face is ~30px wide; eyes are ~6px; a weapon is ~40-80px; wings are ~60-100px "
    "span; a tail is ~50px long and ~12px thick. Do NOT add tiny 2-3px dots or thin "
    "1px lines for a whole feature — they are invisible. Draw each missing feature at "
    "a size a viewer can actually SEE and recognize. Prefer fewer, larger, bolder "
    "primitives over many tiny ones."
)


def load_base_prims(cid):
    """Load the current committed primitives for a champ (the good base)."""
    cache_path = os.path.join(ASSET_DIR, "characters", cid, "descriptors.json")
    try:
        cache = json.load(open(cache_path))
        prims = cache.get("0", {}).get("primitives", [])
        if prims:
            return prims
    except Exception:
        pass
    return None


def critique(canon, cid, img_path):
    """Return (canonical_match, recognizable, features_missing)."""
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
        if isinstance(missing, str):
            missing = [missing]
        return cm, rec, missing
    except Exception:
        return 0, False, ["parse error"]


def additive_fix(c, base_score, max_iters=4):
    """Additive-patch refinement. Never loses the base; only adds detail.

    Returns {id, base_score, best_score, best_prims, improved, history}.
    """
    cid = c["id"]
    canon = champ_canon_text(c)
    tmp = f"/tmp/vlmpatch_{cid}.png"

    base_prims = load_base_prims(cid)
    if not base_prims:
        return {"id": cid, "base_score": base_score, "best_score": base_score,
                "best_prims": None, "improved": False, "history": ["no base prims"]}

    best_prims = base_prims
    best_score = base_score
    history = []

    render_primitives(base_prims, tmp)

    for i in range(max_iters):
        cm, rec, missing = critique(canon, cid, tmp)
        history.append({"iter": i, "cm": cm, "rec": rec, "missing": missing[:4]})
        print(f"    {cid} iter {i}: cm={cm}/10 rec={rec} missing={missing[:3]}", flush=True)

        if cm >= 7:
            print(f"    {cid} CONVERGED at iter {i}!", flush=True)
            break
        if not missing or missing == ["parse error"]:
            break

        # Ask for ONLY the new primitives to add for the missing features.
        miss_str = ", ".join(missing[:5])
        # Give the VLM the count + bbox of the existing sprite so it places the
        # patch in the right region and at the right scale.
        n_existing = len(best_prims)
        resp = chat([
            {"role": "system", "content": PATCH_SYS},
            {"role": "user", "content": [
                {"type": "text", "text": f"Champion: {cid}. Canon: {canon}\n"
                 f"The sprite (image) is MISSING these features: {miss_str}.\n"
                 f"The existing sprite has {n_existing} primitives already drawn. "
                 f"Output ONLY the new primitives to ADD for the missing features. "
                 f"Do NOT redraw the existing sprite. Make each feature LARGE and "
                 f"visible (not tiny dots). JSON only."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64(tmp)}"}},
            ]},
        ], max_tokens=2500)

        patch, ok = parse_prims(resp)
        if not ok or not patch:
            history.append({"iter": i, "error": "patch parse fail"})
            continue

        # Append the patch to the CURRENT best (additive — never lose base).
        candidate = best_prims + patch
        render_primitives(candidate, tmp)

        # Re-critique the patched sprite.
        cm2, rec2, _ = critique(canon, cid, tmp)
        history.append({"iter": i, "patched_cm": cm2, "rec": rec2, "n_patch": len(patch)})
        print(f"    {cid} patched: cm={cm2}/10 rec={rec2} (+{len(patch)} prims)", flush=True)

        if cm2 > best_score:
            best_score = cm2
            best_prims = candidate
        # If the patch didn't help, we keep best_prims but try again next iter
        # with the (now updated) sprite so the VLM sees the current state.

    improved = best_score > base_score
    return {"id": cid, "base_score": base_score, "best_score": best_score,
            "best_prims": best_prims, "improved": improved, "history": history}


def save_sprite(cid, prims):
    char_dir = os.path.join(ASSET_DIR, "characters", cid)
    sprites_dir = os.path.join(char_dir, "sprites")
    os.makedirs(sprites_dir, exist_ok=True)
    render_primitives(prims, os.path.join(char_dir, "sprite.png"))
    shutil.copy(os.path.join(char_dir, "sprite.png"), os.path.join(sprites_dir, "0.png"))
    cache_path = os.path.join(char_dir, "descriptors.json")
    cache = {}
    if os.path.exists(cache_path):
        try:
            cache = json.load(open(cache_path))
        except Exception:
            cache = {}
    cache["0"] = {"primitives": prims, "generator": "vlm_fix4", "phase": "fix4_additive"}
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2, default=str)


def main():
    byid = {c["id"]: c for c in CHAMPIONS_DB}

    # Load the committed canon gate results.
    gate = json.load(open(os.path.join(EXP_DIR, "canon_gate_results.json")))
    scored = {}
    for item in gate:
        if "gate" in item:
            scored[item["id"]] = item["gate"]["canonical_match"]

    # Target 1: all score-6 champs (1 pt from recognizable) — highest leverage.
    # Target 2: the 4 hard champs still <4.
    targets = []
    for cid, cm in scored.items():
        if cid not in byid:
            continue
        if cm == 6 or cm < 4:
            targets.append((byid[cid], cm))

    targets.sort(key=lambda x: x[1])  # hardest first
    print(f"Fix round 4: ADDITIVE PATCHES (never lose the base)")
    print(f"  {sum(1 for _,cm in targets if cm==6)} champs at score 6 (push to 7)")
    print(f"  {sum(1 for _,cm in targets if cm<4)} champs <4 (additive on existing base)")
    print(f"  total: {len(targets)} champs, max 4 iters each, concurrency 4\n")

    t0 = time.time()
    all_results = {}

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(additive_fix, c, cm, 4): c["id"] for c, cm in targets}
        for fut in as_completed(futs):
            cid = futs[fut]
            try:
                r = fut.result()
                all_results[cid] = r
                delta = r["best_score"] - r["base_score"]
                tag = f"{r['best_score']}/10 (base {r['base_score']}, {'+' if delta>=0 else ''}{delta})"
                print(f"  {cid:14s}: {tag}  {'IMPROVED' if r['improved'] else 'no change'}", flush=True)
            except Exception as e:
                print(f"  {cid:14s}: ERROR {e}", flush=True)
                all_results[cid] = {"id": cid, "base_score": scored.get(cid, 0),
                                    "best_score": scored.get(cid, 0), "best_prims": None,
                                    "improved": False, "history": [str(e)]}

    # Save improved sprites (only if improved AND >= base — never regress).
    saved = 0
    for cid, r in all_results.items():
        if r["best_prims"] and r["improved"] and r["best_score"] >= r["base_score"]:
            save_sprite(cid, r["best_prims"])
            saved += 1
    print(f"\nSaved {saved} improved sprites (never regressed any)")

    # Summary
    deltas = [r["best_score"] - r["base_score"] for r in all_results.values()]
    improved = sum(1 for d in deltas if d > 0)
    converged = sum(1 for r in all_results.values() if r["best_score"] >= 7)
    print(f"\n=== FIX ROUND 4 ({len(all_results)} champs, {time.time()-t0:.0f}s) ===")
    print(f"improved: {improved}/{len(all_results)}")
    print(f"reached >=7: {converged}/{len(all_results)}")
    print(f"mean delta: {sum(deltas)/len(deltas):+.2f}")

    results_out = {cid: {"base_score": r["base_score"], "best_score": r["best_score"],
                         "improved": r["improved"]} for cid, r in all_results.items()}
    with open(os.path.join(EXP_DIR, "vlm_fix4_results.json"), "w") as f:
        json.dump(results_out, f, indent=2)
    print(f"results -> exp/vlm_fix4_results.json")


if __name__ == "__main__":
    main()
