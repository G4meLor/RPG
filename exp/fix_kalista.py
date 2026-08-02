"""Hand-author Kalista — committed sprite is undersized + spear clips top-right.
Kalista = the Spear of Vengeance: spectral ghostly humanoid, flowing tattered
robes, hollow glowing eyes, spectral armor, hovering. Weapon: spectral spear.
Colors: teal / dark green / black. Canon score 6.

Re-author full-body, centered, spear vertical (not clipping), with the
spectral ghostly form BIG and readable.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from champ_improver import improve, render, committed_score, gate, save

TEAL = [40, 175, 165]       # spectral teal
DTEAL = [25, 110, 105]      # dark teal
GREEN = [40, 95, 70]        # dark green
DGREEN = [25, 65, 45]       # very dark green
BLACK = [25, 30, 30]        # black robes
GLOW = [120, 255, 200]      # ghostly glow (eyes, edges)
SILVER = [170, 200, 195]    # spectral armor
BLK = [15, 20, 20]          # outline
ROBE = [30, 80, 75]         # robe teal-green

prims = [
    # ===== SPECTRAL GLOW AURA (behind) =====
    {"type": "circle", "cx": 128, "cy": 140, "r": 76, "color": [25, 75, 70], "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 128, "cy": 140, "r": 64, "color": [30, 90, 85], "outline": None, "outline_w": 0},

    # ===== SPECTRAL SPEAR (vertical, right side, NOT clipping) =====
    {"type": "line", "start": [186, 50], "end": [186, 210], "color": SILVER, "width": 5},  # shaft
    {"type": "line", "start": [186, 50], "end": [186, 210], "color": [210, 230, 220], "width": 2},  # shine
    # spear blade (teal, glowing) at top
    {"type": "polygon", "points": [[186, 50], [176, 30], [186, 18], [196, 30]], "color": TEAL, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[186, 40], [180, 28], [186, 24]], "color": GLOW, "outline": None, "outline_w": 0},
    # spear butt
    {"type": "circle", "cx": 186, "cy": 210, "r": 4, "color": SILVER, "outline": BLK, "outline_w": 1},

    # ===== FLOWING TATTERED ROBES (lower body, hovering — no feet) =====
    {"type": "polygon", "points": [[88, 150], [168, 150], [176, 230], [80, 230]], "color": ROBE, "outline": BLK, "outline_w": 2},
    # robe shading
    {"type": "polygon", "points": [[92, 152], [128, 152], [126, 228], [84, 228]], "color": DGREEN, "outline": None, "outline_w": 0},
    # tattered hem (jagged, ghostly)
    {"type": "polygon", "points": [[80, 230], [88, 240], [96, 232], [104, 242], [112, 232], [120, 242], [128, 232], [136, 242], [144, 232], [152, 242], [160, 232], [168, 240], [176, 230]], "color": BLACK, "outline": BLK, "outline_w": 1},
    # robe flow lines (spectral)
    {"type": "line", "start": [100, 160], "end": [96, 220], "color": TEAL, "width": 1},
    {"type": "line", "start": [128, 160], "end": [128, 220], "color": TEAL, "width": 1},
    {"type": "line", "start": [156, 160], "end": [160, 220], "color": TEAL, "width": 1},

    # ===== TORSO (spectral armor) =====
    {"type": "polygon", "points": [[100, 110], [156, 110], [152, 156], [104, 156]], "color": BLACK, "outline": BLK, "outline_w": 2},
    # spectral armor plating (silver/teal)
    {"type": "polygon", "points": [[108, 118], [148, 118], [144, 150], [112, 150]], "color": SILVER, "outline": BLK, "outline_w": 1},
    # armor gem (teal glow)
    {"type": "circle", "cx": 128, "cy": 132, "r": 6, "color": TEAL, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 128, "cy": 132, "r": 3, "color": GLOW, "outline": None, "outline_w": 0},
    # armor ribs
    {"type": "line", "start": [112, 140], "end": [144, 140], "color": DTEAL, "width": 1},
    # belt
    {"type": "rect", "x": 102, "y": 150, "w": 52, "h": 7, "color": DGREEN, "outline": BLK, "outline_w": 1},

    # ===== ARMS =====
    # right arm (holding spear)
    {"type": "polygon", "points": [[148, 118], [164, 118], [172, 156], [156, 160]], "color": BLACK, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 168, "cy": 158, "r": 6, "color": SILVER, "outline": BLK, "outline_w": 1},  # gauntlet gripping spear
    # left arm
    {"type": "polygon", "points": [[92, 118], [108, 118], [100, 158], [84, 154]], "color": BLACK, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 92, "cy": 156, "r": 6, "color": SILVER, "outline": BLK, "outline_w": 1},

    # ===== NECK + HEAD (spectral, ghostly) =====
    {"type": "rect", "x": 120, "y": 88, "w": 16, "h": 22, "color": [50, 110, 100], "outline": BLK, "outline_w": 1},
    # skull (pale spectral)
    {"type": "circle", "cx": 128, "cy": 78, "r": 22, "color": [60, 130, 120], "outline": BLK, "outline_w": 2},
    # cheek shade (hollow)
    {"type": "polygon", "points": [[110, 80], [120, 80], [118, 94], [112, 94]], "color": DTEAL, "outline": None, "outline_w": 0},
    {"type": "polygon", "points": [[136, 80], [146, 80], [144, 94], [138, 94]], "color": DTEAL, "outline": None, "outline_w": 0},

    # HOLLOW GLOWING EYES — signature
    {"type": "circle", "cx": 120, "cy": 76, "r": 6, "color": GLOW, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 136, "cy": 76, "r": 6, "color": GLOW, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 120, "cy": 76, "r": 3, "color": [220, 255, 235], "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 136, "cy": 76, "r": 3, "color": [220, 255, 235], "outline": None, "outline_w": 0},
    # brow (hollow, menacing)
    {"type": "line", "start": [112, 70], "end": [144, 70], "color": BLK, "width": 2},
    # grim mouth (hollow)
    {"type": "rect", "x": 120, "y": 88, "w": 16, "h": 3, "color": BLK, "outline": None, "outline_w": 0},

    # ===== HOOD (spectral, over head) =====
    {"type": "polygon", "points": [[100, 84], [128, 48], [156, 84], [150, 96], [106, 96]], "color": BLACK, "outline": BLK, "outline_w": 2},
    {"type": "polygon", "points": [[106, 82], [128, 54], [150, 82], [146, 92], [110, 92]], "color": DGREEN, "outline": None, "outline_w": 0},
    # hood point (flowing back)
    {"type": "polygon", "points": [[150, 84], [170, 76], [164, 96]], "color": BLACK, "outline": BLK, "outline_w": 1},

    # ===== SPECTRAL WISPS (ghostly trail below hovering body) =====
    {"type": "polygon", "points": [[96, 230], [88, 250], [100, 246]], "color": TEAL, "outline": None, "outline_w": 0},
    {"type": "polygon", "points": [[128, 230], [128, 252], [136, 246]], "color": TEAL, "outline": None, "outline_w": 0},
    {"type": "polygon", "points": [[160, 230], [168, 250], [156, 246]], "color": TEAL, "outline": None, "outline_w": 0},
    # floating glow particles
    {"type": "circle", "cx": 70, "cy": 120, "r": 3, "color": GLOW, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 200, "cy": 130, "r": 3, "color": GLOW, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 60, "cy": 180, "r": 2, "color": TEAL, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 210, "cy": 180, "r": 2, "color": TEAL, "outline": None, "outline_w": 0},
]

if __name__ == "__main__":
    print(f"Kalista committed score: {committed_score('Kalista')}")
    r = improve("Kalista", prims, do_save=True, gate_n=6)
    print(r)
    render(prims, "/tmp/kalista_new.png")
