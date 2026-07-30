"""
Aetheria — UI color constants + element/rarity color lookups.

The color palette block (WHITE/DIM/GOLD/PANEL/PANEL_BORDER/HP_RED/HP_GREEN/
MP_BLUE/XP_PURPLE/BG_DARK) plus the element_color/rarity_color helpers. Split
out of primitives.py so the palette can be imported on its own (the widgets +
primitives both pull constants from here).

element_color does a LATE `from main import Game` inside the function body to
read Game._active.player.settings["colorblind_mode"] — the colorblind-palette
hook. This late import MUST stay (it's the cycle-avoidance pattern: Game lives
in main.py; importing it at module top would create a ui <-> main cycle). Root
main.py re-exports Game, so `from main import Game` still resolves after the
move into src/ui/.
"""
import data as D

# ---------------------------------------------------------------------------
# Color constants
# ---------------------------------------------------------------------------
WHITE = (245, 245, 250)
DIM   = (180, 180, 200)
GOLD  = (255, 210, 90)
PANEL = (28, 26, 44, 220)
PANEL_BORDER = (180, 180, 220)
HP_RED = (220, 70, 80)
HP_GREEN = (90, 210, 110)
MP_BLUE = (90, 150, 240)
XP_PURPLE = (200, 120, 240)
BG_DARK = (20, 18, 32)

# ---------------------------------------------------------------------------
# Color lookups
# ---------------------------------------------------------------------------
def element_color(el):
    # Branch on the colorblind_mode setting to swap the element palette for a
    # deuteranopia-safe set. The function reads the active Game's player
    # settings; if no Game has been instantiated yet (e.g. early import-time
    # probes), fall back to the default palette. REACTIONS are NOT routed here.
    if el not in D.ELEMENT_COLORS:
        return (200, 200, 200)
    try:
        # Late import to avoid a circular ui <-> main dependency: Game lives in
        # main.py and registers itself on __init__.
        from main import Game
        cb = Game._active.player.settings.get("colorblind_mode", False) \
            if Game._active is not None else False
    except Exception:
        cb = False
    if cb:
        return D.COLORBLIND_PALETTES[el]
    return D.ELEMENT_COLORS[el][0]

def rarity_color(rar):
    return D.RARITY_COLORS.get(rar, (200, 200, 200))
