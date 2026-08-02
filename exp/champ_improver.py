"""Shared harness for per-champ sprite improvement (the 170-task effort).

A subagent (or the coordinator) hand-authors a list of JSON drawing primitives
for ONE champion using LoL knowledge, then calls:

    from champ_improver import improve
    result = improve("Renekton", prims_list)
    print(result)   # {id, old, new, saved, missing, verdict, n_prims}

improve() renders the primitives to a 256x256 PNG, gates the sprite with the
SAME canon_gate method that produced the committed scores in
exp/canon_gate_results.json (VLMClient.canon_gate, max-of-3 to damp the ~2pt
run-to-run variance), and SAVES the sprite to
assets/characters/{id}/sprite.png + sprites/0.png + descriptors.json ONLY if
the new score strictly beats the committed score (never regresses).

It does NOT touch canon_gate_results.json (the coordinator re-gates changed
champs via regate_saved.py after a batch, to avoid parallel-write races).

Primitive format (same as hand_author_sprites.py / vlm_sprite_gen2.py):
  {"type":"circle","cx":int,"cy":int,"r":int,"color":[r,g,b],
   "outline":[r,g,b]|null,"outline_w":int}
  {"type":"rect","x":int,"y":int,"w":int,"h":int,"color":[r,g,b],
   "outline":[r,g,b]|null,"outline_w":int,"radius":int}
  {"type":"polygon","points":[[x,y],...],"color":[r,g,b],
   "outline":[r,g,b]|null,"outline_w":int}
  {"type":"line","start":[x,y],"end":[x,y],"color":[r,g,b],"width":int}
  {"type":"ellipse","x":int,"y":int,"w":int,"h":int,"color":[r,g,b],
   "outline":[r,g,b]|null,"outline_w":int}

Canvas: 256x256, body center ~(128,150). Draw back-to-front.
"""
import os, sys, json, shutil

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pygame  # noqa: E402
pygame.init()
pygame.display.set_mode((1, 1))

from src.build.champions import CHAMPIONS_DB  # noqa: E402
from src.data.tuning import ASSET_DIR  # noqa: E402
from src.build.vlm_client import VLMClient  # noqa: E402

EXP_DIR = os.path.dirname(os.path.abspath(__file__))
_BYID = {c["id"]: c for c in CHAMPIONS_DB}
_VLM = None


def _results():
    return json.load(open(os.path.join(EXP_DIR, "canon_gate_results.json")))


def canon_for(cid):
    """Cached canon identity dict for a champ (stance/body_shape/
    signature_features/primary_colors/weapon), or None."""
    for r in _results():
        if r["id"] == cid:
            return r.get("canon")
    return None


def committed_score(cid):
    """Current committed canon_gate canonical_match for a champ (0 if none)."""
    for r in _results():
        if r["id"] == cid and "gate" in r:
            return r["gate"]["canonical_match"]
    return 0


def render(prims, path):
    """Render a list of primitive dicts to a 256x256 PNG at `path`."""
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
                if ol:
                    pygame.draw.circle(surf, ol, (cx, cy), r, ow)
            elif t == "rect":
                w, h = max(1, p.get("w", 10)), max(1, p.get("h", 10))
                rad = p.get("radius", 0)
                rect = pygame.Rect(p.get("x", 0), p.get("y", 0), w, h)
                if rad > 0:
                    pygame.draw.rect(surf, col, rect, border_radius=rad)
                    if ol:
                        pygame.draw.rect(surf, ol, rect, ow, border_radius=rad)
                else:
                    pygame.draw.rect(surf, col, rect)
                    if ol:
                        pygame.draw.rect(surf, ol, rect, ow)
            elif t == "polygon":
                pts = [(int(x), int(y)) for x, y in p.get("points", [])]
                if len(pts) >= 3:
                    pygame.draw.polygon(surf, col, pts)
                    if ol:
                        pygame.draw.polygon(surf, ol, pts, ow)
            elif t == "line":
                s_, e_ = p.get("start", [0, 0]), p.get("end", [0, 0])
                pygame.draw.line(surf, col, (int(s_[0]), int(s_[1])),
                                 (int(e_[0]), int(e_[1])),
                                 max(1, p.get("width", 1)))
            elif t == "ellipse":
                w, h = max(1, p.get("w", 10)), max(1, p.get("h", 10))
                rect = pygame.Rect(p.get("x", 0), p.get("y", 0), w, h)
                pygame.draw.ellipse(surf, col, rect)
                if ol:
                    pygame.draw.ellipse(surf, ol, rect, ow)
        except Exception:
            continue
    pygame.image.save(surf, path)
    return surf


def gate(cid, path, n=3):
    """Gate a sprite with VLMClient.canon_gate (max-of-n). Returns
    (canonical_match, features_missing, verdict). Uses the cached canon so
    scores are directly comparable to the committed canon_gate_results.json."""
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
    return (best["canonical_match"],
            best.get("features_missing", []),
            best.get("verdict", "fail"))


def save(cid, prims):
    """Write sprite.png + sprites/0.png + descriptors.json for a champ."""
    char_dir = os.path.join(ASSET_DIR, "characters", cid)
    sprites_dir = os.path.join(char_dir, "sprites")
    os.makedirs(sprites_dir, exist_ok=True)
    render(prims, os.path.join(char_dir, "sprite.png"))
    shutil.copy(os.path.join(char_dir, "sprite.png"),
                os.path.join(sprites_dir, "0.png"))
    cache_path = os.path.join(char_dir, "descriptors.json")
    cache = {}
    if os.path.exists(cache_path):
        try:
            cache = json.load(open(cache_path))
        except Exception:
            cache = {}
    cache["0"] = {"primitives": prims, "generator": "hand_authored",
                  "phase": "per-champ"}
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2, default=str)


def improve(cid, prims, do_save=True, gate_n=3):
    """Render, gate (max-of-gate_n), save-if-beats-committed.

    Returns {id, old, new, saved, missing, verdict, n_prims, rec}.
    Never regresses: saves only when new > committed old score.
    """
    if not prims:
        return {"id": cid, "old": committed_score(cid), "new": 0,
                "saved": False, "missing": ["no primitives"], "verdict": "fail",
                "n_prims": 0, "rec": False}
    tmp = f"/tmp/improve_{cid}.png"
    render(prims, tmp)
    new_score, missing, verdict = gate(cid, tmp, n=gate_n)
    old_score = committed_score(cid)
    saved = False
    if do_save and new_score > old_score:
        save(cid, prims)
        saved = True
    return {"id": cid, "old": old_score, "new": new_score, "saved": saved,
            "missing": missing, "verdict": verdict, "n_prims": len(prims),
            "rec": new_score >= 7}


if __name__ == "__main__":
    # CLI: gate a champ's committed sprite (sanity check the harness wiring).
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cid")
    ap.add_argument("--gate-only", action="store_true",
                    help="just re-gate the committed sprite, don't author")
    args = ap.parse_args()
    if args.gate_only:
        sp = os.path.join(ASSET_DIR, "characters", args.cid, "sprite.png")
        cm, miss, v = gate(args.cid, sp, n=2)
        print(f"{args.cid}: committed gate={cm}/10 missing={miss[:3]} verdict={v} "
              f"(stored={committed_score(args.cid)})")
