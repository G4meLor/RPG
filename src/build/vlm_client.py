"""VLM art-director client for the pixel-sprite loop.

OpenAI-compatible chat/completions over HTTPS (self-signed cert -> verify=False).
describe(ref) -> descriptor ; critique(ref, sprite) -> {match, ok, problems,
suggested_descriptor}. All output is JSON-validated against VOCAB and clamped;
garbage -> the caller-supplied fallback, never an exception.
"""
import base64, json, os, re, ssl, urllib.request

DEFAULT_MODEL    = "misa-gemma-4-31b-it"
DEFAULT_BASE_URL = "https://runai.misaonline.vpnlocal/prod-llm/misa-gemma4-31b-it-api/v1"
DEFAULT_API_KEY  = "sk-proj-runai-8p33H3qYneIaWOwjX5bsae3I1CIJhUjvKG0nTis6dJ1mzkJqHW"

# VOCAB is derived from RENDERER_VOCAB (the single source of truth in the
# renderer) so the VLM-facing vocabulary can never drift from what the
# renderer actually dispatches. `stance` is included so describe()/critique()
# can validate it; `primary` lists the palette sub-keys (kept for back-compat
# with test_vocab_complete, which asserts "primary" in VOCAB).
from src.assets_gen.generate import RENDERER_VOCAB

VOCAB = dict(RENDERER_VOCAB)
VOCAB["primary"] = ["primary", "secondary", "accent"]
_PALETTE_KEYS = ("primary", "secondary", "accent")

_DESCRIBE_SYS = (
    "You are an art director for a pixel-art world-sprite renderer with a FIXED "
    "vocabulary. Look at the champion skin splash and output a JSON descriptor ONLY. "
    "Fields: stance (one of {stance}), archetype (one of {arche}), weapon (one of {weap}), palette "
    "{{\"primary\":[r,g,b],\"secondary\":[r,g,b],\"accent\":[r,g,b]}} (0-255), "
    "features (list from {feat}, max 3), build (one of {build}), motif (one of {motif}). "
    "CRITICAL: extract the 3 MOST DOMINANT colors from the splash. "
    "primary = main clothing/body color, secondary = hair/secondary clothing, "
    "accent = magic/weapon/glow color. Output JSON only, no prose."
).format(stance=",".join(VOCAB["stance"]), arche=",".join(VOCAB["archetype"]),
         weap=",".join(VOCAB["weapon"]), feat=",".join(VOCAB["features"]),
         build=",".join(VOCAB["build"]), motif=",".join(VOCAB["motif"]))

_CRITIQUE_SYS = (
    "You are an art director comparing a REFERENCE skin splash (image 1) to a "
    "CHIBI PIXEL SPRITE (image 2). The sprite is intentionally simplified (256px, "
    "blocky) — it is NOT meant to be a realistic replica. Score based on: "
    "(1) dominant color family match (red/blue/green/etc), (2) weapon type, "
    "(3) general class. A reasonable chibi with the right color family scores 6+. "
    "Good match 7-8. Excellent 9-10. Below 6 only if colors are completely wrong. "
    "Output JSON ONLY: "
    "{{\"match\":<0-10 integer>,\"ok\":<true if the sprite is good enough (match>=6)>,"
    "\"problems\":[<short strings>],\"suggested_descriptor\":{{<full descriptor in "
    "the renderer vocab>}}}}. Renderer vocabulary: stance {stance}; archetype {arche}; "
    "weapon {weap}; features {feat} (max 3); build {build}; motif {motif}; palette 3x[r,g,b]. "
    "Output JSON only, no prose."
).format(stance=",".join(VOCAB["stance"]), arche=",".join(VOCAB["archetype"]),
         weap=",".join(VOCAB["weapon"]), feat=",".join(VOCAB["features"]),
         build=",".join(VOCAB["build"]), motif=",".join(VOCAB["motif"]))


class VLMClient:
    def __init__(self, base_url=None, api_key=None, model=None, timeout=180):
        self.base_url = base_url or os.environ.get("VLM_BASE_URL", DEFAULT_BASE_URL)
        self.api_key  = api_key  or os.environ.get("VLM_API_KEY", DEFAULT_API_KEY)
        self.model    = model    or os.environ.get("VLM_MODEL", DEFAULT_MODEL)
        self.timeout  = timeout
        self._ctx = ssl.create_default_context()
        self._ctx.check_hostname = False
        self._ctx.verify_mode = ssl.CERT_NONE

    def _post(self, body):
        """Send a chat/completions request; return the raw HTTP response object
        (a context manager with .read()). Tests monkeypatch this to inject a
        _FakeResp canned response (no network)."""
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Authorization": "Bearer " + self.api_key,
                     "Content-Type": "application/json"})
        return urllib.request.urlopen(req, context=self._ctx, timeout=self.timeout)

    @staticmethod
    def _b64(path):
        """Base64-encode a file. Returns '' for a missing file so callers can
        still build a request body and exercise the HTTP seam (tests patch
        _post and pass fake paths)."""
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except OSError:
            return ""

    @staticmethod
    def _strip_json(text):
        """Extract the first {...} block, tolerating ```json fences."""
        m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if m:
            return m.group(1)
        m = re.search(r"\{.*\}", text, re.DOTALL)
        return m.group(0) if m else text.strip()

    def _chat(self, messages, max_tokens=500, temperature=0.2):
        body = {"model": self.model, "messages": messages,
                "max_tokens": max_tokens, "temperature": temperature}
        with self._post(body) as r:
            data = json.loads(r.read())
        return data["choices"][0]["message"]["content"]

    def _validate(self, d, fallback):
        """Clamp every field into VOCAB; on any structural problem return fallback."""
        try:
            out = {}
            out["stance"] = d["stance"] if d.get("stance") in VOCAB["stance"] \
                else fallback.get("stance", "upright")
            out["archetype"] = d["archetype"] if d.get("archetype") in VOCAB["archetype"] \
                else fallback["archetype"]
            out["weapon"] = d["weapon"] if d.get("weapon") in VOCAB["weapon"] \
                else fallback["weapon"]
            pal = d.get("palette") or {}
            out["palette"] = {}
            for k in _PALETTE_KEYS:
                v = pal.get(k) or fallback["palette"][k]
                out["palette"][k] = [max(0, min(255, int(v[0]))),
                                     max(0, min(255, int(v[1]))),
                                     max(0, min(255, int(v[2])))]
            feats = [f for f in (d.get("features") or []) if f in VOCAB["features"]]
            out["features"] = feats[:3]
            out["build"] = d["build"] if d.get("build") in VOCAB["build"] else fallback["build"]
            out["motif"] = d["motif"] if d.get("motif") in VOCAB["motif"] else fallback["motif"]
            return out
        except Exception:
            return fallback

    def describe(self, ref_path, fallback, max_tokens=400):
        """One VLM call: splash -> descriptor. `fallback` is the champ's current
        baked descriptor (used if the VLM returns garbage)."""
        for _ in range(2):  # retry once on parse failure
            try:
                content = self._chat([
                    {"role": "system", "content": _DESCRIBE_SYS},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Describe this skin as a world-sprite descriptor. JSON only."},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + self._b64(ref_path)}},
                    ]},
                ], max_tokens=max_tokens)
                d = json.loads(self._strip_json(content))
                return self._validate(d, fallback)
            except Exception:
                continue
        return fallback

    def critique(self, ref_path, sprite_path, last_good_descriptor, max_tokens=500):
        """One VLM call: compare splash vs rendered sprite. Returns
        {match, ok, problems, suggested_descriptor}; garbage -> {match:0,
        ok:False, problems:['parse error'], suggested_descriptor: last_good}."""
        for _ in range(2):
            try:
                content = self._chat([
                    {"role": "system", "content": _CRITIQUE_SYS},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Image 1 = reference splash. Image 2 = current procedural sprite. Critique + suggest a better descriptor. JSON only."},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + self._b64(ref_path)}},
                        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + self._b64(sprite_path)}},
                    ]},
                ], max_tokens=max_tokens)
                c = json.loads(self._strip_json(content))
                match = int(c.get("match", 0))
                match = max(0, min(10, match))
                ok = bool(c.get("ok", False))
                problems = list(c.get("problems", []))
                sug = self._validate(c.get("suggested_descriptor", {}) or {}, last_good_descriptor)
                return {"match": match, "ok": ok, "problems": problems, "suggested_descriptor": sug}
            except Exception:
                continue
        return {"match": 0, "ok": False, "problems": ["parse error"],
                "suggested_descriptor": last_good_descriptor}
