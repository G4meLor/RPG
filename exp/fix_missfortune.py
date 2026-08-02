"""Hand-author Miss Fortune — committed sprite is missing face/head/torso (just a
floating hat + hair + a gun). Re-author a FULL-BODY pirate gunwoman:
  - tricorne pirate hat (black with red trim)
  - long flowing red hair
  - face (pale skin, eyes)
  - captain's coat (white/red)
  - dual flintlock pistols (raised)
  - high-heeled boots + legs
Colors: red / black / white. Canon score 7.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from champ_improver import improve, render, committed_score, gate, save

RED = [200, 45, 50]        # red hair / coat trim
DRED = [150, 30, 35]       # dark red
BLACK = [35, 30, 35]       # hat / boots
WHITE = [240, 235, 230]    # coat
SKIN = [230, 195, 165]     # pale skin
DSKIN = [185, 150, 125]    # shaded skin
GOLD = [220, 180, 60]      # pistol accents
STEEL = [170, 170, 180]    # pistol barrels
BLK = [20, 18, 22]         # outline
CREAM = [250, 240, 215]    # coat highlight

prims = [
    # ===== LEGS + HIGH-HEELED BOOTS =====
    {"type": "polygon", "points": [[108, 178], [124, 178], [122, 224], [110, 228]], "color": BLACK, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[132, 178], [148, 178], [146, 224], [134, 228]], "color": BLACK, "outline": BLK, "outline_w": 1},
    # boot tops (cuff)
    {"type": "rect", "x": 106, "y": 176, "w": 20, "h": 8, "color": DRED, "outline": BLK, "outline_w": 1},
    {"type": "rect", "x": 130, "y": 176, "w": 20, "h": 8, "color": DRED, "outline": BLK, "outline_w": 1},
    # high heels
    {"type": "polygon", "points": [[108, 224], [124, 224], [122, 230], [118, 234], [110, 230]], "color": BLACK, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[132, 224], [148, 224], [146, 230], [142, 234], [134, 230]], "color": BLACK, "outline": BLK, "outline_w": 1},
    # thigh-high boot red trim stripe
    {"type": "line", "start": [114, 184], "end": [114, 220], "color": RED, "width": 2},
    {"type": "line", "start": [138, 184], "end": [138, 220], "color": RED, "width": 2},

    # ===== CAPTAIN'S COAT (torso) =====
    {"type": "polygon", "points": [[96, 120], [160, 120], [156, 182], [100, 182]], "color": WHITE, "outline": BLK, "outline_w": 2},
    # coat shading
    {"type": "polygon", "points": [[100, 122], [128, 122], [126, 180], [102, 180]], "color": CREAM, "outline": None, "outline_w": 0},
    # coat lapels (red)
    {"type": "polygon", "points": [[108, 122], [128, 122], [128, 150], [114, 146]], "color": RED, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[128, 122], [148, 122], [142, 146], [128, 150]], "color": RED, "outline": BLK, "outline_w": 1},
    # gold buttons down the coat
    {"type": "circle", "cx": 128, "cy": 150, "r": 3, "color": GOLD, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 128, "cy": 162, "r": 3, "color": GOLD, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 128, "cy": 174, "r": 3, "color": GOLD, "outline": BLK, "outline_w": 1},
    # belt
    {"type": "rect", "x": 98, "y": 174, "w": 60, "h": 8, "color": BLACK, "outline": BLK, "outline_w": 1},
    {"type": "rect", "x": 124, "y": 174, "w": 8, "h": 8, "color": GOLD, "outline": BLK, "outline_w": 1},

    # ===== LONG FLOWING RED HAIR (behind, down the back) =====
    {"type": "polygon", "points": [[104, 78], [86, 100], [78, 160], [88, 180], [98, 160], [100, 120], [110, 90]], "color": RED, "outline": DRED, "outline_w": 1},
    {"type": "polygon", "points": [[152, 78], [170, 100], [178, 160], [168, 180], [158, 160], [156, 120], [146, 90]], "color": RED, "outline": DRED, "outline_w": 1},
    # hair shine
    {"type": "line", "start": [92, 110], "end": [88, 150], "color": [230, 90, 90], "width": 2},
    {"type": "line", "start": [164, 110], "end": [168, 150], "color": [230, 90, 90], "width": 2},

    # ===== DUAL FLINTLOCK PISTOLS (raised, one each side) =====
    # LEFT pistol (raised, pointing up-left)
    {"type": "line", "start": [96, 140], "end": [60, 80], "color": STEEL, "width": 6},  # barrel
    {"type": "line", "start": [96, 140], "end": [60, 80], "color": [200, 200, 210], "width": 2},
    {"type": "polygon", "points": [[60, 80], [50, 70], [56, 76]], "color": STEEL, "outline": BLK, "outline_w": 1},  # muzzle
    {"type": "rect", "x": 92, "y": 134, "w": 14, "h": 10, "color": GOLD, "outline": BLK, "outline_w": 1},  # lock mechanism
    {"type": "rect", "x": 90, "y": 142, "w": 10, "h": 16, "color": BLACK, "outline": BLK, "outline_w": 1},  # grip
    # RIGHT pistol (raised, pointing up-right)
    {"type": "line", "start": [160, 140], "end": [196, 80], "color": STEEL, "width": 6},
    {"type": "line", "start": [160, 140], "end": [196, 80], "color": [200, 200, 210], "width": 2},
    {"type": "polygon", "points": [[196, 80], [206, 70], [200, 76]], "color": STEEL, "outline": BLK, "outline_w": 1},
    {"type": "rect", "x": 150, "y": 134, "w": 14, "h": 10, "color": GOLD, "outline": BLK, "outline_w": 1},
    {"type": "rect", "x": 156, "y": 142, "w": 10, "h": 16, "color": BLACK, "outline": BLK, "outline_w": 1},

    # ===== ARMS (gripping pistols) =====
    {"type": "polygon", "points": [[96, 128], [112, 128], [104, 154], [90, 148]], "color": WHITE, "outline": BLK, "outline_w": 1},  # left arm (coat sleeve)
    {"type": "circle", "cx": 96, "cy": 146, "r": 6, "color": SKIN, "outline": BLK, "outline_w": 1},  # left hand
    {"type": "polygon", "points": [[144, 128], [160, 128], [166, 148], [152, 154]], "color": WHITE, "outline": BLK, "outline_w": 1},  # right arm
    {"type": "circle", "cx": 160, "cy": 146, "r": 6, "color": SKIN, "outline": BLK, "outline_w": 1},  # right hand

    # ===== NECK + HEAD =====
    {"type": "rect", "x": 120, "y": 96, "w": 16, "h": 24, "color": SKIN, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 128, "cy": 86, "r": 22, "color": SKIN, "outline": BLK, "outline_w": 2},
    # cheek shade
    {"type": "polygon", "points": [[110, 90], [120, 90], [118, 102], [112, 102]], "color": DSKIN, "outline": None, "outline_w": 0},
    {"type": "polygon", "points": [[136, 90], [146, 90], [144, 102], [138, 102]], "color": DSKIN, "outline": None, "outline_w": 0},
    # eyes
    {"type": "circle", "cx": 121, "cy": 84, "r": 3, "color": BLK, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 135, "cy": 84, "r": 3, "color": BLK, "outline": None, "outline_w": 0},
    # eyelashes (flirty)
    {"type": "line", "start": [117, 80], "end": [114, 78], "color": BLK, "width": 1},
    {"type": "line", "start": [139, 80], "end": [142, 78], "color": BLK, "width": 1},
    # brow
    {"type": "line", "start": [116, 78], "end": [140, 78], "color": BLK, "width": 1},
    # lips (red)
    {"type": "rect", "x": 122, "y": 96, "w": 12, "h": 3, "color": RED, "outline": None, "outline_w": 0},

    # ===== TRICORNE PIRATE HAT (on top) =====
    {"type": "polygon", "points": [[96, 70], [128, 50], [160, 70], [156, 78], [100, 78]], "color": BLACK, "outline": BLK, "outline_w": 2},
    # hat brim three-point flare
    {"type": "polygon", "points": [[96, 70], [88, 76], [100, 74]], "color": BLACK, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[160, 70], [168, 76], [156, 74]], "color": BLACK, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[128, 50], [124, 42], [132, 42]], "color": BLACK, "outline": BLK, "outline_w": 1},
    # red hat trim
    {"type": "line", "start": [100, 76], "end": [156, 76], "color": RED, "width": 2},
    # gold hat emblem (skull/buckle)
    {"type": "circle", "cx": 128, "cy": 64, "r": 5, "color": GOLD, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 128, "cy": 64, "r": 2, "color": BLK, "outline": None, "outline_w": 0},
    # hat feather (red, flowing)
    {"type": "polygon", "points": [[156, 64], [172, 50], [176, 58], [160, 68]], "color": RED, "outline": DRED, "outline_w": 1},
]

if __name__ == "__main__":
    print(f"MissFortune committed score: {committed_score('MissFortune')}")
    r = improve("MissFortune", prims, do_save=True, gate_n=6)
    print(r)
    render(prims, "/tmp/mf_new.png")
