"""Per-skin sprite generator: light mods from the default skin (skin 0).

Now that skin 0 has high-quality hand-authored primitives (108 champs at 8-10),
each other skin is a LIGHT MODIFICATION of skin 0: mostly a RECOLOR to the skin's
palette, plus minor feature add/remove per the skin's theme. The skin's splash
image + name tell us what the skin looks like.

Approach (VLM describes, we apply — same safe pattern as vlm_review_revise):
  1. Load skin-0 primitives (the good hand-authored base).
  2. VLM looks at the skin's splash image + skin name + the skin-0 sprite, and
     outputs a JSON delta: a color map (which base colors → which skin colors)
     + a short list of feature adds/removes.
  3. We apply the delta to the skin-0 primitives (recolor + add/remove), render,
     and save to sprites/{N}.png + descriptors.json[{N}].
  4. Light gate: VLM checks the result vs the splash (optional, drop-in).

This is fast (1-2 VLM calls/skin, no revision loop) and reliable (recoloring a
good base can't break the silhouette). 1610 skins across 170 champs.

Usage:
  from exp.skin_modder import mod_skin, mod_all_skins
  mod_skin("Ahri", 1)          # one skin
  mod_all_skins("Ahri")        # all of a champ's skins
  # CLI:
  python3 exp/skin_modder.py Ahri 1            # one skin (describe+apply+save)
  python3 exp/skin_modder.py Ahri --all        # all skins for Ahri
  python3 exp/skin_modder.py --describe Ahri 1 # just print the VLM delta
"""
import os, sys, json, base64, ssl, urllib.request, re, time, shutil

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame  # noqa: E402
pygame.init(); pygame.display.set_mode((1, 1))

from src.build.champions import CHAMPIONS_DB  # noqa: E402
from src.data.tuning import ASSET_DIR  # noqa: E402

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
_BYID = {c["id"]: c for c in CHAMPIONS_DB}

BASE = "https://runai.misaonline.vpnlocal/prod-llm/misa-gemma4-31b-it-api/v1"
KEY = "sk-proj-runai-8p33H3qYneIaWOwjX5bsae3I1CIJhUjvKG0nTis6dJ1mzkJqHW"
MODEL = "misa-gemma-4-31b-it"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE


def _chat(messages, max_tokens=900, temperature=0.3, timeout=200):
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
                time.sleep(4); continue
            raise


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _strip_json(text):
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m: return m.group(1)
    s = text.find("{")
    if s < 0: return text.strip()
    depth = 0; e = s
    for i in range(s, len(text)):
        if text[i] == "{": depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0: e = i + 1; break
    return text[s:e] if depth == 0 else text[s:] + "}" * depth


def skin0_prims(cid):
    dp = os.path.join(ASSET_DIR, "characters", cid, "descriptors.json")
    d = json.load(open(dp)) if os.path.exists(dp) else {}
    return d.get("0", {}).get("primitives", [])


def skin_name(cid, idx):
    c = _BYID.get(cid)
    if not c: return "?"
    for s in c.get("skins", []):
        if s.get("index") == idx:
            return s.get("name", "?")
    return "?"


def render(prims, path):
    surf = pygame.Surface((256, 256), pygame.SRCALPHA)
    for p in prims:
        try:
            t = p.get("type", "")
            col = tuple(p.get("color", [200, 200, 200])[:3])
            ol = p.get("outline")
            ol = tuple(ol[:3]) if ol else None
            ow = p.get("outline_w", 1)
            if t == "circle":
                r = max(1, p.get("r", 5)); cx, cy = p.get("cx", 128), p.get("cy", 128)
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
                pygame.draw.line(surf, col, (int(s_[0]), int(s_[1])),
                                 (int(e_[0]), int(e_[1])), max(1, p.get("width", 1)))
            elif t == "ellipse":
                w, h = max(1, p.get("w", 10)), max(1, p.get("h", 10))
                rect = pygame.Rect(p.get("x", 0), p.get("y", 0), w, h)
                pygame.draw.ellipse(surf, col, rect)
                if ol: pygame.draw.ellipse(surf, ol, rect, ow)
        except Exception:
            continue
    pygame.image.save(surf, path)
    return surf


DELTA_SYS = (
    "You are a pixel-art sprite artist who knows League of Legends skins. You are "
    "given: (1) the splash art of a specific skin (image 1), (2) the champion's "
    "default-skin pixel sprite (image 2), the champion name, and the skin name. "
    "Your job: describe the MINIMAL changes to turn the default sprite into this "
    "skin. Most skins are a RECOLOR of the default — identify the color mapping. "
    "Some skins add/remove a feature (e.g. Star Guardian adds wings, Arcade adds "
    "pixel glow). Keep changes MINIMAL — the default silhouette is good; only "
    "recolor and add/remove what differs.\n\n"
    "Output JSON ONLY:\n"
    '{"color_map": [[[r,g,b],[r,g,b]], ...], "adds": [{"type":"circle","cx":int,"cy":int,"r":int,"color":[r,g,b]}, ...], "removes": [], "notes": "one line"}\n\n'
    "color_map: list of [base_color, skin_color] pairs. base_color is a color IN "
    "the default sprite (match the dominant fills); skin_color is what it becomes "
    "in this skin (from the splash). Cover the 3-5 dominant colors. "
    "adds: new primitives (circle/rect/polygon/line/ellipse) for features this "
    "skin adds that the default lacks (e.g. wings, halo, glasses). Keep to 0-5 "
    "adds. removes: usually empty. Output JSON ONLY."
)


def describe_skin_delta(cid, idx):
    """VLM looks at the skin splash + default sprite, returns a delta dict
    {color_map, adds, removes, notes}. Returns (delta, skin_name)."""
    c = _BYID.get(cid)
    if not c:
        return None, "?"
    splash = os.path.join(ASSET_DIR, "characters", cid, "skins", f"{idx}.jpg")
    if not os.path.exists(splash):
        return None, skin_name(cid, idx)
    prims = skin0_prims(cid)
    if not prims:
        return None, skin_name(cid, idx)
    base_png = f"/tmp/skin0_{cid}.png"
    render(prims, base_png)
    sname = skin_name(cid, idx)
    canon_feats = []
    for r in json.load(open(os.path.join(EXP_DIR, "canon_gate_results.json"))):
        if r["id"] == cid:
            canon_feats = r.get("canon", {}).get("signature_features", [])[:4]
            break
    resp = _chat([
        {"role": "system", "content": DELTA_SYS},
        {"role": "user", "content": [
            {"type": "text", "text": f"Champion: {cid}. Skin: {sname} (index {idx}). "
             f"Default signature features: {', '.join(canon_feats)}.\n"
             f"Image 1 = the {sname} skin splash art (reference for colors/theme). "
             f"Image 2 = the default-skin pixel sprite (the base to recolor).\n"
             f"Describe the minimal color_map + adds to turn image 2 into the {sname} skin. JSON only."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{_b64(splash)}"}},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_b64(base_png)}"}},
        ]},
    ], max_tokens=900, temperature=0.3)
    try:
        delta = json.loads(_strip_json(resp))
        return delta, sname
    except Exception:
        return {"color_map": [], "adds": [], "removes": [], "notes": "parse fail"}, sname


def _near(a, b, tol=40):
    if not a or not b: return False
    return all(abs(int(a[i]) - int(b[i])) <= tol for i in range(min(3, len(a), len(b))))


def apply_delta(prims, delta):
    """Apply a skin delta to a copy of the skin-0 primitives. Returns revised prims."""
    out = [dict(p) for p in prims]
    cmap = delta.get("color_map", []) or []
    # recolor: for each [base, skin] pair, recolor prims whose color matches base
    for pair in cmap:
        if not isinstance(pair, list) or len(pair) < 2: continue
        base, skin = pair[0], pair[1]
        if not base or not skin: continue
        for p in out:
            if _near(p.get("color"), base, tol=40):
                p["color"] = list(skin[:3])
            # also recolor outlines that match (so borders follow)
            if p.get("outline") and _near(p.get("outline"), base, tol=40):
                p["outline"] = list(skin[:3])
    # adds: append new primitives (validate shape)
    for a in (delta.get("adds", []) or []):
        if not isinstance(a, dict) or "type" not in a: continue
        a2 = dict(a)
        if "color" in a2 and a2["color"]: a2["color"] = list(a2["color"][:3])
        if "outline" in a2 and a2["outline"]: a2["outline"] = list(a2["outline"][:3])
        out.append(a2)
    return out


def mod_skin(cid, idx, do_save=True):
    """Describe + apply + save one skin. Returns result dict."""
    delta, sname = describe_skin_delta(cid, idx)
    if delta is None:
        return {"id": cid, "skin": idx, "name": sname, "saved": False, "error": "no splash/base"}
    prims = skin0_prims(cid)
    revised = apply_delta(prims, delta)
    if do_save:
        char_dir = os.path.join(ASSET_DIR, "characters", cid)
        sprites_dir = os.path.join(char_dir, "sprites")
        os.makedirs(sprites_dir, exist_ok=True)
        render(revised, os.path.join(sprites_dir, f"{idx}.png"))
        # update descriptors.json
        dp = os.path.join(char_dir, "descriptors.json")
        cache = {}
        if os.path.exists(dp):
            try: cache = json.load(open(dp))
            except Exception: cache = {}
        cache[str(idx)] = {"primitives": revised, "generator": "skin_mod",
                           "phase": "per-skin", "base": "0", "skin": sname,
                           "notes": delta.get("notes", "")}
        with open(dp, "w") as f:
            json.dump(cache, f, indent=2, default=str)
    return {"id": cid, "skin": idx, "name": sname, "saved": do_save,
            "n_prims": len(revised), "n_recolor": len(delta.get("color_map", [])),
            "n_adds": len(delta.get("adds", [])), "notes": delta.get("notes", "")}


def mod_all_skins(cid, skip_zero=True):
    """Generate all non-zero skins for a champ. Returns list of results."""
    c = _BYID.get(cid)
    if not c: return []
    results = []
    for s in c.get("skins", []):
        idx = s.get("index", 0)
        if skip_zero and idx == 0: continue
        splash = os.path.join(ASSET_DIR, "characters", cid, "skins", f"{idx}.jpg")
        if not os.path.exists(splash): continue
        try:
            r = mod_skin(cid, idx)
        except Exception as e:
            r = {"id": cid, "skin": idx, "name": s.get("name", "?"), "saved": False, "error": str(e)}
        results.append(r)
    return results


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cid")
    ap.add_argument("idx", nargs="?", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--describe", action="store_true")
    args = ap.parse_args()
    if args.describe and args.idx is not None:
        delta, sname = describe_skin_delta(args.cid, args.idx)
        print(f"=== {args.cid} skin {args.idx} ({sname}) ===")
        print(json.dumps(delta, indent=2) if delta else "(no delta)")
    elif args.all:
        rs = mod_all_skins(args.cid)
        for r in rs:
            print(f"  skin {r['skin']:>3} {r.get('name','?'):18s} recolor={r.get('n_recolor',0)} adds={r.get('n_adds',0)} {'SAVED' if r.get('saved') else 'SKIP'}")
        print(f"{sum(1 for r in rs if r.get('saved'))}/{len(rs)} skins saved")
    elif args.idx is not None:
        r = mod_skin(args.cid, args.idx)
        print(json.dumps(r, indent=2))
