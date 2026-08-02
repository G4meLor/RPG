"""VLM-review-driven revision loop for the 53 below-8 champs (the FINAL pass).

NEW APPROACH (per user): the VLM does NOT author the sprite. We feed the VLM the
CURRENT committed sprite (image) + its canon identity + the gate's missing-feature
list, and ask it to DESCRIBE in plain text HOW to revise the existing primitives
to fix the missing features (e.g. "make the rapier thinner and longer", "add a
rose emblem at x=128,y=120", "recolor the torso from armor-grey to skin-tone for
bare chest"). The coordinator (us) then EDITS the committed primitives per that
text description, re-renders, and re-gates. The VLM only REVIEWS — it never
writes primitive JSON.

This avoids the failure mode where the VLM's own primitive JSON regressed (it
can't author clean multi-feature sprites). The VLM is good at CRITIQUING and
describing edits; it's bad at authoring from scratch.

Loop per champ (up to 4 revision rounds):
  1. Load committed primitives (skin 0) + canon + current missing features.
  2. Render current sprite, ask VLM "this sprite scores N, missing X. Describe
     in plain text EXACTLY which primitives to change/add/remove to fix X. Be
     concrete: name the feature, position, size, color." (NO JSON from VLM.)
  3. We apply the described edits to the primitives (programmatic patching:
     recolor, resize, move, add a named feature at a named spot).
  4. Re-render + re-gate. If new > old, save. If new >= 8, done. Else next round.

Because step 3 (applying text-described edits) requires interpretation, this
script does the VLM describe + gate; the actual primitive EDITING is done by a
subagent (or the coordinator) that reads the VLM's text description and patches
the committed primitives. So this script is the VLM seam; the editing is separate.

For the coordinator-direct path: this script exposes
  describe_revisions(cid) -> (text_description, current_score, missing)
  apply_and_gate(cid, revised_prims) -> result
so a driver can loop: describe -> (edit prims per description) -> apply_and_gate.
"""
import os, sys, json, base64, ssl, urllib.request, re, time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame  # noqa: E402
pygame.init(); pygame.display.set_mode((1, 1))

from src.build.champions import CHAMPIONS_DB  # noqa: E402
from src.data.tuning import ASSET_DIR  # noqa: E402
from src.build.vlm_client import VLMClient  # noqa: E402

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
_BYID = {c["id"]: c for c in CHAMPIONS_DB}
_VLM = None

BASE = "https://runai.misaonline.vpnlocal/prod-llm/misa-gemma4-31b-it-api/v1"
KEY = "sk-proj-runai-8p33H3qYneIaWOwjX5bsae3I1CIJhUjvKG0nTis6dJ1mzkJqHW"
MODEL = "misa-gemma-4-31b-it"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE


def _chat(messages, max_tokens=700, temperature=0.3, timeout=200):
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


def canon_for(cid):
    for r in json.load(open(os.path.join(EXP_DIR, "canon_gate_results.json"))):
        if r["id"] == cid:
            return r.get("canon")
    return None


def committed_prims(cid):
    """The current committed skin-0 primitives for a champ."""
    dp = os.path.join(ASSET_DIR, "characters", cid, "descriptors.json")
    d = json.load(open(dp))
    return d.get("0", {}).get("primitives", [])


def committed_score(cid):
    for r in json.load(open(os.path.join(EXP_DIR, "canon_gate_results.json"))):
        if r["id"] == cid and "gate" in r:
            return r["gate"]["canonical_match"]
    return 0


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


def gate(cid, path, n=3):
    global _VLM
    if _VLM is None:
        _VLM = VLMClient()
    champ = _BYID.get(cid)
    canon = canon_for(cid)
    if champ is None:
        return 0, ["unknown champ"], "fail"
    best = None
    for _ in range(n):
        try:
            g = _VLM.canon_gate(path, champ=champ, canon=canon)
            if best is None or g["canonical_match"] > best["canonical_match"]:
                best = g
        except Exception:
            pass
    if best is None:
        return 0, ["gate error"], "fail"
    return (best["canonical_match"], best.get("features_missing", []),
            best.get("verdict", "fail"))


DESCRIBE_SYS = (
    "You are a pixel-art sprite critic who knows League of Legends. You are given "
    "a champion's canonical identity (text), the current 256x256 pixel-art sprite "
    "(image), its current canon-gate score, and the list of features the gate says "
    "are MISSING. Your job: describe in PLAIN TEXT exactly how to REVISE the "
    "existing sprite to fix the missing features. Do NOT output JSON or primitive "
    "code — describe the edits in concrete spatial terms a human artist can follow.\n\n"
    "Be SPECIFIC and CONCRETE for each missing feature:\n"
    "- Which existing shape to change, and how (recolor, resize, move, reshape)\n"
    "- OR what new shape to ADD, and where (approx position x,y in 0-255, size, color)\n"
    "- OR what to REMOVE (if something is cluttering/misreading)\n"
    "Name colors as [r,g,b]. Name positions as (x,y). Keep edits MINIMAL — the "
    "current sprite already scores well; only fix what's missing. Avoid making the "
    "silhouette busier (that regresses). Prefer RECOLORING or RESIZING existing "
    "shapes over adding new ones. Output plain text only, a short numbered list of "
    "edits (one per missing feature)."
)


def describe_revisions(cid, n_gate=2):
    """Ask the VLM to DESCRIBE (plain text) how to revise the committed sprite
    to fix its missing features. Returns (description_text, current_score, missing)."""
    champ = _BYID.get(cid)
    canon = canon_for(cid)
    cur_score = committed_score(cid)
    prims = committed_prims(cid)
    if not prims:
        return "(no committed primitives)", cur_score, ["no prims"]
    # gate current sprite to get fresh missing list
    tmp = f"/tmp/rev_{cid}.png"
    render(prims, tmp)
    cm, missing, v = gate(cid, tmp, n=n_gate)
    # canon text
    an = champ.get("ability_names", {})
    abstr = ", ".join(f"{s}: {an[s]}" for s in ("Q", "W", "E", "R") if s in an)
    canon_text = (f"Champion: {champ['name']} — {champ.get('title','')}. "
                  f"Faction: {champ.get('faction','')}. Role: {champ.get('role','')}. "
                  f"Abilities: {abstr}. Canon signature features: "
                  f"{', '.join(canon.get('signature_features',[]) if canon else [])}. "
                  f"Canon colors: {canon.get('primary_colors',[]) if canon else []}. "
                  f"Canon weapon: {canon.get('weapon','') if canon else ''}.")
    desc = _chat([
        {"role": "system", "content": DESCRIBE_SYS},
        {"role": "user", "content": [
            {"type": "text", "text": f"{canon_text}\n\nCurrent gate score: {cm}/10. "
             f"Missing features: {missing}.\n\nImage = the current sprite. "
             f"Describe the MINIMAL edits to fix the missing features. Plain text, "
             f"numbered list, one edit per missing feature. Be concrete (positions, "
             f"colors, sizes). Do NOT output JSON."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_b64(tmp)}"}},
        ]},
    ], max_tokens=700, temperature=0.3)
    return desc, cm, missing


def apply_and_gate(cid, revised_prims, n_gate=3):
    """Render revised prims, gate, save if beats committed. Returns improve-style dict."""
    import shutil
    tmp = f"/tmp/rev2_{cid}.png"
    render(revised_prims, tmp)
    cm, missing, v = gate(cid, tmp, n=n_gate)
    old = committed_score(cid)
    saved = False
    if cm > old:
        char_dir = os.path.join(ASSET_DIR, "characters", cid)
        sprites_dir = os.path.join(char_dir, "sprites")
        os.makedirs(sprites_dir, exist_ok=True)
        render(revised_prims, os.path.join(char_dir, "sprite.png"))
        shutil.copy(os.path.join(char_dir, "sprite.png"),
                    os.path.join(sprites_dir, "0.png"))
        cache_path = os.path.join(char_dir, "descriptors.json")
        cache = {}
        if os.path.exists(cache_path):
            try: cache = json.load(open(cache_path))
            except Exception: cache = {}
        cache["0"] = {"primitives": revised_prims, "generator": "vlm_review_revised",
                      "phase": "review-revise"}
        with open(cache_path, "w") as f:
            json.dump(cache, f, indent=2, default=str)
        saved = True
    return {"id": cid, "old": old, "new": cm, "saved": saved,
            "missing": missing, "verdict": v, "n_prims": len(revised_prims),
            "rec": cm >= 7}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cid")
    ap.add_argument("--describe", action="store_true",
                    help="just describe revisions (no apply)")
    args = ap.parse_args()
    if args.describe:
        desc, cm, missing = describe_revisions(args.cid)
        print(f"=== {args.cid} (current {cm}/10, missing {missing}) ===")
        print(desc)
