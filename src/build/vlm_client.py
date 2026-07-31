"""VLM art-director client for the pixel-sprite loop (canon-grounded, Phase 2).

OpenAI-compatible chat/completions over HTTPS (self-signed cert -> verify=False).

describe(ref, fallback, champ)  -> stance-aware descriptor that captures the
                                  champ's canonical identity within the FIXED
                                  renderer vocab (stance + archetype + features
                                  + weapon + palette + build + motif).
critique(ref, sprite, last_good, champ)
                                -> {canonical_match, stance_captured,
                                    body_shape_score, features_missing,
                                    colors_captured, recognizable,
                                    suggested_descriptor}. STRICT judge of
                                    canonical identity capture (NOT splash
                                    similarity).

All output is JSON-validated against VOCAB (derived from RENDERER_VOCAB, the
single source of truth) and clamped; garbage -> the caller-supplied fallback,
never an exception. The `champ` arg is the champ dict from CHAMPIONS_DB (has
id/name/title/faction/role/ability_names/lore); a context string is built from
it via _champ_context() and sent with the splash so the VLM has the champ's
canonical identity in front of it.
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
    "vocabulary. You will be given a champion's CANONICAL IDENTITY (name, title, "
    "faction, role, abilities, lore) AND their skin splash image. Using your "
    "knowledge of the champion's canonical body (from League of Legends lore) "
    "PLUS what you see in the splash, produce the descriptor that BEST captures "
    "the champion's canonical identity within the fixed vocabulary below. "
    "Output a JSON descriptor ONLY (no prose). Fields: "
    "stance (one of {stance} — upright=bipedal humanoid, quadruped=four-legged "
    "beast, mounted=rider on a mount, flying=airborne with wings, "
    "floating=hovering with no legs visible), "
    "archetype (one of {arche}), weapon (one of {weap}), palette "
    "{{\"primary\":[r,g,b],\"secondary\":[r,g,b],\"accent\":[r,g,b]}} (0-255), "
    "features (list from {feat}, max 3 — pick the MOST signature canonical "
    "features), build (one of {build}), motif (one of {motif}). "
    "CRITICAL: pick stance from the champion's canonical body shape (e.g. "
    "Anivia=flying, Alistar=quadruped, Hecarim=mounted, Aurelion Sol=floating, "
    "most humanoids=upright), NOT from the splash pose. "
    "CRITICAL: extract the 3 MOST DOMINANT colors from the splash. "
    "primary = main clothing/body color, secondary = hair/secondary clothing, "
    "accent = magic/weapon/glow color. Output JSON only, no prose."
).format(stance=",".join(VOCAB["stance"]), arche=",".join(VOCAB["archetype"]),
         weap=",".join(VOCAB["weapon"]), feat=",".join(VOCAB["features"]),
         build=",".join(VOCAB["build"]), motif=",".join(VOCAB["motif"]))

_CRITIQUE_SYS = (
    "You are a STRICT art-director critic. You will be given a champion's "
    "CANONICAL IDENTITY (name, title, faction, role, abilities, lore), their "
    "skin splash (image 1), and a CHIBI PIXEL SPRITE (image 2). Judge whether "
    "the sprite captures the champion's CANONICAL identity (stance + body "
    "shape + signature features + colors), NOT mere splash similarity. The "
    "sprite is intentionally simplified (256px, blocky) — judge canonical "
    "identity capture, not photorealism. Be STRICT. Output JSON ONLY: "
    "{{\"canonical_match\":<0-10 integer, how well the sprite captures the "
    "champion's canonical identity>,"
    "\"stance_captured\":<true if the sprite's stance matches the champ's "
    "canonical body shape (upright/quadruped/mounted/flying/floating)>,"
    "\"body_shape_score\":<0-10 integer, how well the body shape matches the "
    "canonical body>,"
    "\"features_missing\":[<canonical features the sprite is missing, short "
    "strings>],"
    "\"colors_captured\":<true if the dominant color family matches the "
    "canonical/splash colors>,"
    "\"recognizable\":<true if a League of Legends player would recognize the "
    "champion from the sprite alone>,"
    "\"suggested_descriptor\":{{<full descriptor in the renderer vocab that "
    "would better capture the canonical identity>}}}}. "
    "Renderer vocabulary: stance {stance}; archetype {arche}; weapon {weap}; "
    "features {feat} (max 3); build {build}; motif {motif}; palette 3x[r,g,b]. "
    "canonical_match >= 7 means the sprite is good enough; < 7 means revise. "
    "Output JSON only, no prose."
).format(stance=",".join(VOCAB["stance"]), arche=",".join(VOCAB["archetype"]),
         weap=",".join(VOCAB["weapon"]), feat=",".join(VOCAB["features"]),
         build=",".join(VOCAB["build"]), motif=",".join(VOCAB["motif"]))


def _champ_context(champ):
    """Build the canonical-identity context text for the VLM prompt.

    `champ` is the champ dict from CHAMPIONS_DB (has id/name/title/faction/
    role/ability_names/lore). Returns a multi-line string suitable for the
    user-message text part. Tolerates missing keys (returns '' for None).
    """
    if not champ:
        return ""
    name  = champ.get("name")  or champ.get("id") or "Unknown"
    title = champ.get("title") or ""
    faction = champ.get("faction") or ""
    role    = champ.get("role")    or ""
    abilities = champ.get("ability_names") or {}
    lore = champ.get("lore") or {}
    bio  = lore.get("bio")  or ""
    quote = lore.get("quote") or ""
    personality = lore.get("personality") or ""

    ab_lines = []
    for slot in ("Q", "W", "E", "R"):
        if abilities.get(slot):
            ab_lines.append(f"  {slot}: {abilities[slot]}")
    ab_text = "\n".join(ab_lines) if ab_lines else "  (none)"

    parts = [
        f"Champion: {name}" + (f" — {title}" if title else ""),
        f"Faction: {faction}" if faction else None,
        f"Role: {role}" if role else None,
        "Abilities:\n" + ab_text,
        f"Lore: {bio}" if bio else None,
        f"Quote: \"{quote}\"" if quote else None,
        f"Personality: {personality}" if personality else None,
    ]
    return "\n".join(p for p in parts if p)


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
        """Clamp every field into VOCAB; on any structural problem return fallback.

        Validates `stance` against VOCAB["stance"] (clamps to fallback's stance
        or 'upright' if missing/invalid). All other fields are clamped the same
        way as before.
        """
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

    def describe(self, ref_path, fallback, champ=None, max_tokens=400):
        """One VLM call: champ identity + splash -> stance-aware descriptor.

        `champ` is the champ dict from CHAMPIONS_DB; its canonical identity
        (name/title/faction/role/abilities/lore) is built into a context
        string and sent with the splash so the VLM can ground the descriptor
        in the champ's canonical body + features + colors. `fallback` is the
        champ's current baked descriptor (used if the VLM returns garbage).
        Returns a descriptor WITH a `stance` field (validated against VOCAB).
        """
        ctx = _champ_context(champ)
        user_text = (
            (ctx + "\n\n") if ctx else ""
        ) + "Using the champion's canonical identity above AND the splash image, " \
            "produce the world-sprite descriptor that best captures the canonical " \
            "identity within the fixed vocabulary. JSON only."
        for _ in range(2):  # retry once on parse failure
            try:
                content = self._chat([
                    {"role": "system", "content": _DESCRIBE_SYS},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + self._b64(ref_path)}},
                    ]},
                ], max_tokens=max_tokens)
                d = json.loads(self._strip_json(content))
                return self._validate(d, fallback)
            except Exception:
                continue
        return fallback

    def critique(self, ref_path, sprite_path, last_good_descriptor, champ=None,
                 max_tokens=500):
        """One VLM call: judge canonical identity capture (splash vs sprite).

        Returns {canonical_match, stance_captured, body_shape_score,
        features_missing, colors_captured, recognizable, suggested_descriptor}.
        `champ` is the champ dict from CHAMPIONS_DB; its canonical identity is
        sent so the VLM judges against the champ's canonical body/features/
        colors (NOT mere splash similarity). On garbage: canonical_match=0,
        stance_captured=False, recognizable=False, suggested_descriptor=last_good.
        """
        ctx = _champ_context(champ)
        user_text = (
            (ctx + "\n\n") if ctx else ""
        ) + "Image 1 = reference splash. Image 2 = current procedural sprite. " \
            "Judge whether the sprite captures the champion's CANONICAL identity " \
            "(stance + body shape + signature features + colors), NOT splash " \
            "similarity. Be STRICT. Suggest a better descriptor if needed. JSON only."
        for _ in range(2):
            try:
                content = self._chat([
                    {"role": "system", "content": _CRITIQUE_SYS},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_text},
                        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + self._b64(ref_path)}},
                        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + self._b64(sprite_path)}},
                    ]},
                ], max_tokens=max_tokens)
                c = json.loads(self._strip_json(content))
                canonical_match = max(0, min(10, int(c.get("canonical_match", 0))))
                stance_captured = bool(c.get("stance_captured", False))
                body_shape_score = max(0, min(10, int(c.get("body_shape_score", 0))))
                features_missing = list(c.get("features_missing", []))
                colors_captured = bool(c.get("colors_captured", False))
                recognizable = bool(c.get("recognizable", False))
                sug = self._validate(c.get("suggested_descriptor", {}) or {},
                                     last_good_descriptor)
                return {
                    "canonical_match": canonical_match,
                    "stance_captured": stance_captured,
                    "body_shape_score": body_shape_score,
                    "features_missing": features_missing,
                    "colors_captured": colors_captured,
                    "recognizable": recognizable,
                    "suggested_descriptor": sug,
                }
            except Exception:
                continue
        return {
            "canonical_match": 0,
            "stance_captured": False,
            "body_shape_score": 0,
            "features_missing": ["parse error"],
            "colors_captured": False,
            "recognizable": False,
            "suggested_descriptor": last_good_descriptor,
        }
