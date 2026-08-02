"""Hand-author Vayne — committed sprite is undersized (tiny, bottom-half, no body
below the waist). Re-author a full-body night-hunter:
  - dark hooded cloak (purple/black)
  - sharp face (pale skin, eyes)
  - wrist-mounted crossbow (the signature — on one arm)
  - Demacian armor accents (silver)
  - high leather boots + legs + torso (full body, fills canvas)
Colors: dark purple / black / silver. Canon score 6.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from champ_improver import improve, render, committed_score, gate, save

PUR = [80, 40, 100]        # dark purple cloak
DPUR = [55, 25, 70]        # darker purple
BLACK = [35, 30, 38]       # black
SILVER = [190, 195, 205]   # silver armor
DSILVER = [130, 135, 145]  # dark silver
SKIN = [225, 200, 175]     # pale skin
DSKIN = [180, 150, 125]    # shaded skin
BROWN = [95, 60, 35]       # leather boots
DBROWN = [65, 40, 22]      # dark leather
STEEL = [170, 170, 180]    # crossbow
BLK = [20, 18, 24]         # outline
GOLD = [200, 165, 60]      # Demacian gold accent

prims = [
    # ===== LEGS + HIGH LEATHER BOOTS =====
    {"type": "polygon", "points": [[104, 176], [124, 176], [122, 224], [108, 228]], "color": BROWN, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[132, 176], [152, 176], [150, 224], [136, 228]], "color": BROWN, "outline": BLK, "outline_w": 1},
    # boot cuffs (knee-high)
    {"type": "rect", "x": 102, "y": 176, "w": 24, "h": 8, "color": DBROWN, "outline": BLK, "outline_w": 1},
    {"type": "rect", "x": 130, "y": 176, "w": 24, "h": 8, "color": DBROWN, "outline": BLK, "outline_w": 1},
    # boot feet
    {"type": "polygon", "points": [[104, 224], [126, 224], [124, 232], [106, 232]], "color": DBROWN, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[132, 224], [154, 224], [152, 232], [134, 232]], "color": DBROWN, "outline": BLK, "outline_w": 1},
    # boot buckle (silver)
    {"type": "circle", "cx": 114, "cy": 180, "r": 3, "color": SILVER, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 142, "cy": 180, "r": 3, "color": SILVER, "outline": BLK, "outline_w": 1},

    # ===== TORSO (under cloak) =====
    {"type": "polygon", "points": [[100, 120], [156, 120], [152, 180], [104, 180]], "color": PUR, "outline": BLK, "outline_w": 2},
    # Demacian silver chest armor
    {"type": "polygon", "points": [[110, 128], [146, 128], [142, 162], [114, 162]], "color": SILVER, "outline": BLK, "outline_w": 1},
    # armor chest emblem (gold)
    {"type": "circle", "cx": 128, "cy": 142, "r": 6, "color": GOLD, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 128, "cy": 142, "r": 3, "color": [240, 220, 120], "outline": None, "outline_w": 0},
    # armor ribs
    {"type": "line", "start": [114, 150], "end": [142, 150], "color": DSILVER, "width": 1},
    # belt
    {"type": "rect", "x": 100, "y": 172, "w": 56, "h": 8, "color": BLACK, "outline": BLK, "outline_w": 1},
    {"type": "rect", "x": 124, "y": 172, "w": 8, "h": 8, "color": SILVER, "outline": BLK, "outline_w": 1},

    # ===== HOODED CLOAK (behind/around body) =====
    # cloak body (drapes from shoulders down)
    {"type": "polygon", "points": [[92, 110], [164, 110], [170, 182], [86, 182]], "color": DPUR, "outline": BLK, "outline_w": 2},
    # cloak shading
    {"type": "polygon", "points": [[96, 112], [128, 112], [126, 180], [90, 180]], "color": [45, 20, 60], "outline": None, "outline_w": 0},
    # cloak tattered hem (jagged bottom)
    {"type": "polygon", "points": [[86, 182], [94, 190], [100, 184], [108, 192], [114, 184], [122, 192], [128, 184], [136, 192], [142, 184], [150, 192], [156, 184], [164, 190], [170, 182]], "color": DPUR, "outline": BLK, "outline_w": 1},

    # ===== LEFT ARM (with wrist-mounted crossbow — signature) =====
    {"type": "polygon", "points": [[100, 128], [116, 128], [110, 168], [96, 160]], "color": PUR, "outline": BLK, "outline_w": 1},
    # crossbow mounted on left wrist (the signature weapon)
    {"type": "rect", "x": 88, "y": 156, "w": 24, "h": 8, "color": STEEL, "outline": BLK, "outline_w": 1},  # crossbow body
    {"type": "line", "start": [88, 156], "end": [88, 168], "color": STEEL, "width": 2},  # left limb
    {"type": "line", "start": [112, 156], "end": [112, 168], "color": STEEL, "width": 2},  # right limb
    {"type": "line", "start": [88, 158], "end": [112, 158], "color": [220, 220, 225], "width": 1},  # bowstring
    {"type": "line", "start": [100, 158], "end": [76, 150], "color": STEEL, "width": 2},  # bolt
    {"type": "polygon", "points": [[76, 150], [70, 148], [74, 154]], "color": STEEL, "outline": BLK, "outline_w": 1},  # bolt tip
    # hand
    {"type": "circle", "cx": 100, "cy": 162, "r": 6, "color": SKIN, "outline": BLK, "outline_w": 1},

    # ===== RIGHT ARM =====
    {"type": "polygon", "points": [[140, 128], [156, 128], [162, 160], [146, 166]], "color": PUR, "outline": BLK, "outline_w": 1},
    # silver arm guard (Demacian accent)
    {"type": "ellipse", "x": 142, "y": 140, "w": 16, "h": 18, "color": SILVER, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 156, "cy": 162, "r": 6, "color": SKIN, "outline": BLK, "outline_w": 1},  # hand

    # ===== NECK + HEAD =====
    {"type": "rect", "x": 120, "y": 96, "w": 16, "h": 22, "color": SKIN, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 128, "cy": 86, "r": 22, "color": SKIN, "outline": BLK, "outline_w": 2},
    # sharp cheeks (shade)
    {"type": "polygon", "points": [[110, 88], [120, 88], [118, 102], [112, 102]], "color": DSKIN, "outline": None, "outline_w": 0},
    {"type": "polygon", "points": [[136, 88], [146, 88], [144, 102], [138, 102]], "color": DSKIN, "outline": None, "outline_w": 0},
    # sharp eyes (determined)
    {"type": "circle", "cx": 121, "cy": 84, "r": 3, "color": BLK, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 135, "cy": 84, "r": 3, "color": BLK, "outline": None, "outline_w": 0},
    # sharp brow
    {"type": "line", "start": [116, 80], "end": [126, 82], "color": BLK, "width": 2},
    {"type": "line", "start": [130, 82], "end": [140, 80], "color": BLK, "width": 2},
    # mouth (set jaw)
    {"type": "rect", "x": 122, "y": 96, "w": 12, "h": 2, "color": BLK, "outline": None, "outline_w": 0},

    # ===== HOOD (over head) =====
    {"type": "polygon", "points": [[100, 92], [128, 56], [156, 92], [150, 104], [106, 104]], "color": DPUR, "outline": BLK, "outline_w": 2},
    {"type": "polygon", "points": [[106, 90], [128, 62], [150, 90], [146, 100], [110, 100]], "color": PUR, "outline": None, "outline_w": 0},
    # hood opening shadow
    {"type": "circle", "cx": 128, "cy": 86, "r": 24, "color": None, "outline": BLK, "outline_w": 1},
    # hood point (back)
    {"type": "polygon", "points": [[150, 92], [166, 84], [160, 100]], "color": DPUR, "outline": BLK, "outline_w": 1},
]

if __name__ == "__main__":
    print(f"Vayne committed score: {committed_score('Vayne')}")
    r = improve("Vayne", prims, do_save=True, gate_n=6)
    print(r)
    render(prims, "/tmp/vayne_new.png")
