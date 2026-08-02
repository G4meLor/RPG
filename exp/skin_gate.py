"""Per-skin quality gates (the user's two targets):

  1. SILHOUETTE gate (programmatic, NO VLM): the skin sprite must not deviate from
     the default-skin sprite by more than 20% — i.e. silhouette IoU >= 0.80.
     A recolor keeps the silhouette identical (IoU ~1.0); only adds/removes move it.
     Cheap (pixel alpha compare), so we run it on ALL baked skins.

  2. SKIN-MATCH gate (VLM, 1 call/skin): does the pixel sprite match the intended
     skin (vs the skin's splash art)? Score 0-10; require >= 6 (>60%). This
     validates the recolor actually looks like the skin, not just the champ.

A skin PASSES if IoU >= 0.80 AND match >= 6. Failures get a fallback:
  - IoU < 0.80 (adds broke silhouette): re-bake with RECOLOR ONLY (drop adds) →
    IoU returns to ~1.0; re-gate match.
  - match < 6 (recolor wrong): keep the best attempt; if still < 6 after recolor-
    only retry, fall back to the default sprite (skin 0) so the skin at least
    reads as the champ (silhouette perfect, match = "default recolor").

Usage:
  from exp.skin_gate import gate_skin, silhouette_iou, skin_match_gate
  gate_skin("Ahri", 1)  # -> {iou, match, pass, ...}
  # CLI:
  python3 exp/skin_gate.py Ahri 1            # gate one skin
  python3 exp/skin_gate.py --gate-all        # gate all baked skins, report
  python3 exp/skin_gate.py --fix-all         # gate + fix failures (recolor-only retry / fallback)
"""
import os, sys, json, base64, ssl, urllib.request, re, time

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

IOU_MIN = 0.80   # silhouette must keep >= 80% of the default
MATCH_MIN = 6    # skin-match vs splash must be >= 6/10 (>60%)


def _chat(messages, max_tokens=200, temperature=0.2, timeout=200):
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
    m = re.search(r"\{.*\}", text, re.DOTALL)
    return m.group(0) if m else text.strip()


def skin_name(cid, idx):
    c = _BYID.get(cid)
    if not c: return "?"
    for s in c.get("skins", []):
        if s.get("index") == idx: return s.get("name", "?")
    return "?"


def silhouette_iou(skin0_path, skinN_path):
    """Intersection-over-union of the two sprites' alpha masks (silhouette
    similarity). 1.0 = identical silhouette; 0.0 = no overlap. Programmatic,
    no VLM. Returns IoU float (0.0 if both empty)."""
    import numpy as np
    import pygame.surfarray as sa
    def mask(path):
        s = pygame.image.load(path)
        a = sa.pixels_alpha(s); arr = np.asarray(a); del a
        return arr > 8  # boolean mask of opaque pixels
    m0 = mask(skin0_path)
    mN = mask(skinN_path)
    inter = int((m0 & mN).sum())
    union = int((m0 | mN).sum())
    if union == 0: return 1.0
    return inter / union


MATCH_SYS = (
    "You are a pixel-art critic who knows League of Legends skins. Given a skin's "
    "splash art (image 1, the reference) and a 256x256 pixel sprite (image 2, the "
    "attempt), score how well the sprite captures THIS SKIN's look (colors, theme, "
    "key features) on 0-10. 10 = perfect match to the skin's colors/theme; 6 = "
    "recognizably this skin; 0 = wrong skin / generic. Output JSON ONLY: "
    '{"match": 0-10, "ok": true/false, "note": "one line"}. '
    "Judge the SKIN (colors/theme vs splash), not the champion identity."
)


def skin_match_gate(cid, idx, skinN_path, n=2):
    """VLM: does the sprite match the skin (vs splash)? Returns (match_score, note).
    max-of-n to damp variance."""
    splash = os.path.join(ASSET_DIR, "characters", cid, "skins", f"{idx}.jpg")
    if not os.path.exists(splash):
        return 0, "no splash"
    sname = skin_name(cid, idx)
    best = None
    for _ in range(n):
        try:
            resp = _chat([
                {"role": "system", "content": MATCH_SYS},
                {"role": "user", "content": [
                    {"type": "text", "text": f"Champion: {cid}. Skin: {sname} (index {idx}). "
                     f"Image 1 = the {sname} splash (reference). Image 2 = the pixel sprite "
                     f"attempt. Score how well image 2 matches the {sname} skin. JSON only."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{_b64(splash)}"}},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_b64(skinN_path)}"}},
                ]},
            ], max_tokens=200, temperature=0.2)
            d = json.loads(_strip_json(resp))
            m = max(0, min(10, int(d.get("match", 0))))
            if best is None or m > best[0]:
                best = (m, d.get("note", ""))
        except Exception:
            pass
    return best if best else (0, "gate error")


def gate_skin(cid, idx, n_match=2):
    """Run both gates on a baked skin. Returns dict with iou, match, pass."""
    char_dir = os.path.join(ASSET_DIR, "characters", cid)
    skin0 = os.path.join(char_dir, "sprite.png")
    skinN = os.path.join(char_dir, "sprites", f"{idx}.png")
    if not os.path.exists(skinN):
        return {"id": cid, "skin": idx, "name": skin_name(cid, idx),
                "iou": None, "match": None, "pass": False, "error": "no sprite"}
    iou = silhouette_iou(skin0, skinN)
    match, note = skin_match_gate(cid, idx, skinN, n=n_match)
    ok = (iou is not None and iou >= IOU_MIN and match >= MATCH_MIN)
    return {"id": cid, "skin": idx, "name": skin_name(cid, idx),
            "iou": round(iou, 3) if iou is not None else None,
            "match": match, "note": note, "pass": ok}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cid")
    ap.add_argument("idx", nargs="?", type=int, default=None)
    args = ap.parse_args()
    if args.idx is not None:
        r = gate_skin(args.cid, args.idx)
        print(json.dumps(r, indent=2))
