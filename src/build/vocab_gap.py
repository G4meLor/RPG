"""VLM free-form gap-analysis: find distinct visual features the renderer cannot
yet draw, so Phase 2 can implement them. NOT the fixed-vocab describe task."""
import json, os, re, random
from collections import Counter

from src.build.vlm_client import VLMClient
from src.data.tuning import ASSET_DIR

_GAP_SYS = (
    "Look at this champion skin splash. Name the 1-2 MOST distinct visual "
    "features of this character's world appearance that a small pixel sprite "
    "MUST capture (e.g. 'nine tails', 'shield', 'dual pistols', 'huge hammer', "
    "'fox ears'). Output JSON ONLY: {\"features\":[...],\"weapons\":[...]}. "
    "Free-form strings, not from a fixed vocabulary."
)


class GapVLM(VLMClient):
    """VLM client specialized for the free-form gap prompt."""
    def freeform_features(self, ref_path):
        for _ in range(2):
            try:
                content = self._chat([
                    {"role": "system", "content": _GAP_SYS},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Name the distinct features. JSON only."},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + self._b64(ref_path)}},
                    ]},
                ], max_tokens=200)
                d = json.loads(self._strip_json(content))
                return {"features": [str(x).lower().strip() for x in (d.get("features") or [])],
                        "weapons": [str(x).lower().strip() for x in (d.get("weapons") or [])]}
            except Exception:
                continue
        return {"features": [], "weapons": []}


def analyze(champs, sample_n=None, vlm_factory=None):
    """Aggregate free-form feature/weapon frequency across a sample of splashes."""
    vlm_factory = vlm_factory or (lambda: GapVLM())
    if sample_n and sample_n < len(champs):
        # deterministic sample (no Math.random in workflows; here plain random is fine)
        rng = random.Random(42)
        champs = rng.sample(champs, sample_n)
    feats, weaps = Counter(), Counter()
    vlm = vlm_factory()
    for c in champs:
        ref = os.path.join(ASSET_DIR, "characters", c["id"], "skins", "0.jpg")
        if not os.path.exists(ref):
            continue
        r = vlm.freeform_features(ref)
        for f in r["features"]:
            feats[f] += 1
        for w in r["weapons"]:
            weaps[w] += 1
    return {"features": dict(feats), "weapons": dict(weaps)}


def top_n_gap(report, renderer_features, renderer_weapons, n=10):
    """Top-N features + weapons NOT already in the renderer vocab, by frequency."""
    known_f = set(renderer_features)
    known_w = set(renderer_weapons)
    feat_gap = [(k, v) for k, v in report["features"].items() if k not in known_f]
    weap_gap = [(k, v) for k, v in report["weapons"].items() if k not in known_w]
    feat_gap.sort(key=lambda kv: (-kv[1], kv[0]))
    weap_gap.sort(key=lambda kv: (-kv[1], kv[0]))
    return {"features": [k for k, _ in feat_gap[:n]],
            "weapons": [k for k, _ in weap_gap[:n]],
            "feature_counts": dict(feat_gap[:n]),
            "weapon_counts": dict(weap_gap[:n])}
