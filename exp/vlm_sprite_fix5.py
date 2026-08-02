"""Fix round 5: SPLASH-GROUNDED FRESH GENERATION (best-of-N, no revision loop).

Root-cause lesson (fix1-4):
  - Full-regen revision loops (fix1-3): the VLM re-emits the whole JSON and
    routinely LOSES good features -> regress (Sona 3->2, Zeri 3->2).
  - Additive patches (fix4): appending primitives CLUTTERS the sprite -> the
    critic sees noise -> score drops (Ahri 6->4->3->4, Sona 3->2).
  - Both failure modes share one cause: the VLM 31b cannot cleanly REVISE a
    multi-feature sprite. It either drops features or piles primitives.

What actually produced the 8/10 sprites (Amumu, Chogath, Graves, Malphite,
Seraphine, Vi, Yasuo, Zac...): a SINGLE FRESH generation pass. No revision.

New approach:
  - Generate FRESH from the skin-0 SPLASH IMAGE (not canon text alone — the
    text-only path misses subtle features: facial markings, attire cut,
    proportions, color hue). The splash is the canonical visual ground truth.
  - Best-of-N (N=3) independent attempts, NO revision loop between them.
  - Gate each attempt + the current sprite with the canon gate (text+sprite,
    no splash — the gate must judge recognizability, not splash-similarity).
  - Keep the HIGHEST-scoring attempt. Save only if it beats the current
    committed sprite. Never regress.

Targets: the 53 champs at score 6 (1 pt from recognizable >=7). Pushing
~26 to 7 -> ~122/170 = 72% recognizable -> hits the 70% gate target.

Results -> exp/vlm_fix5_results.json (NOT /tmp, per user directive).
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
N_ATTEMPTS = 3


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def chat(messages, max_tokens=4000, temperature=0.4, timeout=300):
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
    """Parse primitives. Accepts {primitives:[...]} or bare [...]."""
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


# Splash-grounded fresh generation: ONE pass, full sprite, from the splash.
DRAW_SYS = (
    "You are a pixel-art sprite artist. You will be given a League of Legends "
    "champion's canonical identity (text) AND their official splash art (image). "
    "Draw a 256x256 FULL-BODY pixel-art world sprite of this champion, matching "
    "the splash's colors, silhouette, and signature features.\n\n"
    "Output JSON ONLY:\n"
    '{"primitives": [\n'
    '  {"type":"circle","cx":int,"cy":int,"r":int,"color":[r,g,b],"outline":[r,g,b],"outline_w":int},\n'
    '  {"type":"rect","x":int,"y":int,"w":int,"h":int,"color":[r,g,b],"outline":[r,g,b],"outline_w":int,"radius":int},\n'
    '  {"type":"polygon","points":[[x,y],...],"color":[r,g,b],"outline":[r,g,b],"outline_w":int},\n'
    '  {"type":"line","start":[x,y],"end":[x,y],"color":[r,g,b],"width":int},\n'
    '  {"type":"ellipse","x":int,"y":int,"w":int,"h":int,"color":[r,g,b],"outline":[r,g,b],"outline_w":int}\n'
    "]}\n\n"
    "Rules:\n"
    "- Coords 0-255, 256x256. Body center ~(128,150). Draw a FRONT-FACING full body.\n"
    "- Match the splash's COLORS exactly (skin, hair, outfit, weapon hues).\n"
    "- Draw the champion's SIGNATURE features visibly: weapon, hair, distinctive "
    "headgear, wings/tail if present, armor/attire. At 256px a feature must be "
    "LARGE enough to read (weapon 40-80px, wings 60-100px, face ~30px, eyes ~6px).\n"
    "- 15-30 primitives. Draw back-to-front. Output JSON ONLY, no prose."
)

GATE_SYS = (
    "You are a STRICT visual critic who knows League of Legends. Given a "
    "champion's canonical identity (text) and a 256x256 pixel-art sprite (image), "
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
        if isinstance(missing, str):
            missing = [missing]
        return cm, rec, missing
    except Exception:
        return 0, False, ["parse error"]


def fresh_gen_attempt(c, splash_path, canon, temp, attempt_n):
    """One fresh-generation attempt from the splash. Returns (prims, cm) or (None, -1)."""
    cid = c["id"]
    tmp = f"/tmp/vlmfresh_{cid}_{attempt_n}.png"
    user_text = (f"Champion: {cid}. Canon: {canon}\n\n"
                 f"Image = the official splash art. Draw a 256x256 full-body "
                 f"pixel-art sprite matching this splash's colors and features. "
                 f"Output JSON primitives only.")
    msgs = [
        {"role": "system", "content": DRAW_SYS},
        {"role": "user", "content": [
            {"type": "text", "text": user_text},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64(splash_path)}"}},
        ]},
    ]
    resp = chat(msgs, max_tokens=4000, temperature=temp)
    prims, ok = parse_prims(resp)
    if not ok or not prims:
        return None, -1
    render_primitives(prims, tmp)
    cm, rec, _ = critique(canon, cid, tmp)
    return prims, cm


def fresh_gen_bestofN(c, base_score, n=N_ATTEMPTS):
    """Best-of-N fresh generation. No revision loop. Keep highest; never regress."""
    cid = c["id"]
    canon = champ_canon_text(c)
    splash = os.path.join(ASSET_DIR, "characters", cid, "skins", "0.jpg")
    if not os.path.exists(splash):
        return {"id": cid, "base_score": base_score, "best_score": base_score,
                "best_prims": None, "improved": False, "attempts": ["no splash"]}

    best_prims = None
    best_score = -1
    attempts = []

    for n_i in range(n):
        # Vary temperature across attempts for diversity: 0.3, 0.5, 0.7
        temp = 0.3 + 0.2 * n_i
        prims, cm = fresh_gen_attempt(c, splash, canon, temp, n_i)
        if prims is None:
            attempts.append({"n": n_i, "cm": -1, "error": "parse"})
            print(f"    {cid} attempt {n_i}: PARSE FAIL", flush=True)
            continue
        attempts.append({"n": n_i, "cm": cm, "n_prims": len(prims)})
        print(f"    {cid} attempt {n_i} (t={temp}): cm={cm}/10 prims={len(prims)}", flush=True)
        if cm > best_score:
            best_score = cm
            best_prims = prims
        if cm >= 8:
            break  # strong hit, no need for more attempts

    improved = best_score > base_score
    return {"id": cid, "base_score": base_score, "best_score": best_score,
            "best_prims": best_prims, "improved": improved, "attempts": attempts}


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
    cache["0"] = {"primitives": prims, "generator": "vlm_fix5", "phase": "fix5_splash_fresh"}
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2, default=str)


def select_targets(scored, mode="score6"):
    """Select target champs. mode='score6' for the 53 at score 6; 'all_low' adds <4."""
    targets = []
    for cid, cm in scored.items():
        if mode == "score6" and cm == 6:
            targets.append(cid)
        elif mode == "all_low" and (cm == 6 or cm < 4):
            targets.append(cid)
    return targets


def main():
    byid = {c["id"]: c for c in CHAMPIONS_DB}
    # CLI: --mode score6|all_low|smoke  --limit N
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="score6", choices=["score6", "all_low", "smoke"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--champs", default="")
    args, _ = ap.parse_known_args()

    if args.mode == "smoke":
        targets = ["Ahri", "Annie", "Darius", "Fiora"]
    elif args.champs:
        targets = [x.strip() for x in args.champs.split(",") if x.strip()]
    else:
        gate = json.load(open(os.path.join(EXP_DIR, "canon_gate_results.json")))
        scored = {item["id"]: item["gate"]["canonical_match"]
                  for item in gate if "gate" in item}
        targets = select_targets(scored, args.mode)

    if args.limit and args.limit > 0:
        targets = targets[:args.limit]

    # base scores for reporting
    gate = json.load(open(os.path.join(EXP_DIR, "canon_gate_results.json")))
    base = {item["id"]: item["gate"]["canonical_match"] for item in gate if "gate" in item}

    print(f"Fix round 5: SPLASH-GROUNDED FRESH GEN (best-of-{N_ATTEMPTS}, no revision)")
    print(f"  mode={args.mode}, {len(targets)} champs, concurrency 4\n")

    t0 = time.time()
    all_results = {}

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(fresh_gen_bestofN, byid[cid], base.get(cid, 0)): cid
                for cid in targets if cid in byid}
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
                all_results[cid] = {"id": cid, "base_score": base.get(cid, 0),
                                    "best_score": base.get(cid, 0), "best_prims": None,
                                    "improved": False, "attempts": [str(e)]}

    # Save improved sprites (only if beats base — never regress).
    saved = 0
    for cid, r in all_results.items():
        if r["best_prims"] and r["improved"] and r["best_score"] > r["base_score"]:
            save_sprite(cid, r["best_prims"])
            saved += 1
    print(f"\nSaved {saved} improved sprites (never regressed any)")

    deltas = [r["best_score"] - r["base_score"] for r in all_results.values()]
    improved = sum(1 for d in deltas if d > 0)
    converged = sum(1 for r in all_results.values() if r["best_score"] >= 7)
    regressed = sum(1 for d in deltas if d < 0)
    print(f"\n=== FIX ROUND 5 ({len(all_results)} champs, {time.time()-t0:.0f}s) ===")
    print(f"improved: {improved}/{len(all_results)}")
    print(f"reached >=7: {converged}/{len(all_results)}")
    print(f"regressed (NOT saved): {regressed}/{len(all_results)}")
    print(f"mean delta: {sum(deltas)/len(deltas):+.2f}")

    results_out = {cid: {"base_score": r["base_score"], "best_score": r["best_score"],
                         "improved": r["improved"], "attempts": r.get("attempts", [])}
                   for cid, r in all_results.items()}
    with open(os.path.join(EXP_DIR, "vlm_fix5_results.json"), "w") as f:
        json.dump(results_out, f, indent=2)
    print(f"results -> exp/vlm_fix5_results.json")


if __name__ == "__main__":
    main()
