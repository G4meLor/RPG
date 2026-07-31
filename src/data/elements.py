"""Element colors, pixel-art palette, colorblind palette, rarity colors,
elemental reactions + reaction lookup.

Mechanically split from _legacy_data.py — bodies copied verbatim.
"""

__all__ = [
    "ELEMENT_COLORS", "PIXEL", "PIXEL_PALETTE", "COLORBLIND_PALETTES",
    "RARITY_COLORS", "REACTIONS", "REACTION_WINDOW", "WET_EFFECT",
    "reaction_for",
]

# ---------------------------------------------------------------------------
# Elemental reactions — a bonus effect when a hit of one element lands shortly
# after a hit of a *different* element (Genshin-style). Rewards swapping the
# active hero mid-fight (the 4-hero party). The reaction fires on the SECOND
# element's hit; both elements must be different and within the reaction window.
#   key: frozenset({el_a, el_b}) -> (name, bonus_dmg_frac, effect, color)
#   effect: "aoe" = bonus damage to nearby enemies, "stun" = brief enemy stun,
#           "burst" = a big particle burst on the target
# ---------------------------------------------------------------------------
REACTIONS = {
    frozenset({"fire", "water"}):  ("Steam",    0.30, "aoe",   (220, 230, 240)),
    frozenset({"fire", "wind"}):   ("Spread",   0.25, "burst", (255, 180, 90)),
    frozenset({"water", "wind"}):  ("Freeze",   0.20, "stun",  (180, 220, 255)),
    frozenset({"light", "dark"}):  ("Rupture",  0.35, "burst", (255, 200, 220)),
}
REACTION_WINDOW = 3.0   # seconds after a hit during which a different element triggers

# Wet effect: when the current map's weather is rain, the reaction window is
# extended (x1.5) and water hits are amplified (x1.2) / fire hits are dampened
# (x0.8). Gated to the reaction window ONLY — the wet effect extends the
# window, not the Freeze stun duration (see world_scene._on_enemy_hit).
WET_EFFECT = {"water": 1.2, "fire": 0.8, "reaction_window": 1.5}

def reaction_for(el_a, el_b):
    """Return the reaction dict for two elements, or None if no reaction."""
    if el_a == el_b:
        return None
    return REACTIONS.get(frozenset({el_a, el_b}))

# ---------------------------------------------------------------------------
# Element colors (used by UI for badges, glows, text)
# ---------------------------------------------------------------------------
ELEMENT_COLORS = {
    "fire":  ( (232, 86, 60),  (255,168, 90), (120, 24, 18) ),
    "water": ( ( 64,150,230),  (140,220,255), ( 18, 48, 96) ),
    "wind":  ( ( 96,200,140),  (180,240,190), ( 24, 84, 56) ),
    "light": ( (245,210, 90),  (255,245,200), (140,110, 30) ),
    "dark":  ( (150, 90,200),  (210,170,240), ( 56, 28, 84) ),
}

# pixel-art scale: each logical pixel is rendered as a PIXEL×PIXEL block so the
# art reads as chunky pixel-art at higher density than Stardew (Stardew tiles are
# 16x16; a 256px sprite at PIXEL=5 -> ~51 logical pixels, 3x Stardew). Palette is
# locked per element (base/light/shadow/outline/accent) so gradients dither
# instead of smoothing.
PIXEL = 5
PIXEL_PALETTE = {
    "fire":   {"base": (220, 90, 40), "light": (255, 170, 90), "shadow": (130, 40, 20),
               "outline": (60, 20, 10), "accent": (255, 230, 140)},
    "water":  {"base": (40, 120, 210), "light": (120, 200, 255), "shadow": (20, 60, 120),
               "outline": (10, 30, 60), "accent": (200, 240, 255)},
    "wind":   {"base": (120, 220, 160), "light": (200, 255, 220), "shadow": (60, 130, 90),
               "outline": (20, 50, 40), "accent": (240, 255, 200)},
    "light":  {"base": (250, 220, 90), "light": (255, 250, 200), "shadow": (180, 140, 40),
               "outline": (80, 60, 20), "accent": (255, 255, 240)},
    "dark":   {"base": (110, 50, 150), "light": (180, 110, 220), "shadow": (60, 20, 90),
               "outline": (30, 10, 50), "accent": (200, 160, 255)},
}
# Colorblind-friendly element palette (deuteranopia-safe). Single RGB triples
# (main color only) chosen to stay distinct from each other AND from HP_RED
# (220,70,80), GOLD/crit-yellow (255,210,90), and HP_GREEN/heal-green
# (90,210,110). Separation relies on hue + brightness, not red/green alone:
#   fire  = bright orange   (warm, low blue; distinct from pinkish HP_RED)
#   water = sky blue        (high blue; no clash)
#   wind  = chartreuse      (yellow-green; distinct from GOLD and HP_GREEN)
#   light = pale cream      (very high brightness; distinct from GOLD)
#   dark  = purple         (high blue + red; no clash)
# REACTIONS keep their own fixed rcol tuples and are NOT routed through this.
COLORBLIND_PALETTES = {
    "fire":  (235,  90,  30),
    "water": ( 40, 140, 220),
    "wind":  (200, 230,  60),
    "light": (255, 235, 150),
    "dark":  (140,  50, 190),
}

RARITY_COLORS = {
    "R":   (140, 150, 165),
    "SR":  (220, 150, 60),
    "SSR": (220, 80, 150),
}
