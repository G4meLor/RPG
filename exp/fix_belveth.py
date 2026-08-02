"""Bel'veth attempt 3: low-slung void PREDATOR (quadruped, per canon) with HUGE
readable features. Lessons from attempts 1-2:
  - v1 quadruped scored 5: features too small/thin (claws read as floating shards,
    snout tiny). Gate said scythe claws / void armor / snout all MISSING.
  - v2 humanoid scored 2: gate dings "quadruped stance" missing — canon wants 4 legs.

So: keep quadruped, but make EVERY signature feature 2x bigger and unambiguous:
  - THICK crescent scythe claws (not thin shards) reared up front, glowing edge
  - BIG elongated snout with visible fangs + nostril (like Renekton's readable head)
  - BIG glowing void eyes
  - Clear 4 digitigrade legs
  - Void-crystalline back plates as big triangles
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from champ_improver import improve, render, committed_score

PUR = [125, 40, 150]
MAG = [210, 110, 230]
DPUR = [65, 18, 85]
BLK = [25, 20, 30]
GLOW = [240, 150, 255]
LILAC = [245, 210, 255]
CRY = [185, 135, 205]

prims = [
    # ---- TAIL (right) ----
    {"type": "polygon", "points": [[200, 150], [246, 136], [252, 162], [240, 182], [202, 170]],
     "color": PUR, "outline": DPUR, "outline_w": 2},
    {"type": "polygon", "points": [[224, 146], [246, 152], [238, 160]], "color": MAG, "outline": BLK, "outline_w": 1},
    {"type": "line", "start": [230, 150], "end": [248, 156], "color": GLOW, "width": 2},

    # ---- HIND LEGS (right, 2 legs) ----
    {"type": "polygon", "points": [[170, 168], [190, 168], [196, 200], [182, 212], [168, 200]],
     "color": DPUR, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 184, "cy": 202, "r": 7, "color": DPUR, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[176, 206], [192, 206], [190, 220], [178, 220]], "color": PUR, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[178, 220], [184, 230], [180, 232], [174, 222]], "color": MAG, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[186, 220], [192, 230], [188, 232], [182, 222]], "color": MAG, "outline": BLK, "outline_w": 1},
    # near hind leg
    {"type": "polygon", "points": [[148, 170], [168, 170], [174, 202], [160, 214], [146, 202]],
     "color": PUR, "outline": DPUR, "outline_w": 1},
    {"type": "circle", "cx": 162, "cy": 204, "r": 7, "color": DPUR, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[154, 208], [170, 208], [168, 222], [156, 222]], "color": PUR, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[156, 222], [162, 232], [158, 234], [152, 224]], "color": MAG, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[164, 222], [170, 232], [166, 234], [160, 224]], "color": MAG, "outline": BLK, "outline_w": 1},

    # ---- BODY (horizontal, bigger) ----
    {"type": "ellipse", "x": 56, "y": 116, "w": 156, "h": 64, "color": PUR, "outline": DPUR, "outline_w": 2},
    {"type": "ellipse", "x": 70, "y": 142, "w": 128, "h": 28, "color": DPUR, "outline": BLK, "outline_w": 1},
    # BIG crystalline back plates (void-crystalline armor) — tall triangles
    {"type": "polygon", "points": [[76, 120], [88, 92], [100, 120]], "color": CRY, "outline": DPUR, "outline_w": 2},
    {"type": "polygon", "points": [[100, 120], [114, 88], [128, 120]], "color": CRY, "outline": DPUR, "outline_w": 2},
    {"type": "polygon", "points": [[128, 120], [142, 92], [156, 120]], "color": CRY, "outline": DPUR, "outline_w": 2},
    {"type": "polygon", "points": [[156, 120], [170, 96], [182, 122]], "color": CRY, "outline": DPUR, "outline_w": 2},
    # glints on plates
    {"type": "line", "start": [88, 96], "end": [88, 116], "color": GLOW, "width": 2},
    {"type": "line", "start": [114, 92], "end": [114, 116], "color": GLOW, "width": 2},
    {"type": "line", "start": [142, 96], "end": [142, 116], "color": GLOW, "width": 2},
    # side crystalline plates
    {"type": "polygon", "points": [[108, 150], [130, 144], [128, 164], [110, 162]], "color": MAG, "outline": DPUR, "outline_w": 1},
    {"type": "polygon", "points": [[142, 150], [164, 144], [162, 164], [144, 162]], "color": MAG, "outline": DPUR, "outline_w": 1},

    # ---- FRONT LEGS (left, 2 legs, one rearing with claws) ----
    # far front leg (down)
    {"type": "polygon", "points": [[98, 168], [118, 168], [124, 202], [110, 214], [96, 202]],
     "color": DPUR, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 112, "cy": 204, "r": 7, "color": DPUR, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[104, 208], [120, 208], [118, 222], [106, 222]], "color": PUR, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[106, 222], [112, 232], [108, 234], [102, 224]], "color": MAG, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[114, 222], [120, 232], [116, 234], [110, 224]], "color": MAG, "outline": BLK, "outline_w": 1},
    # near front leg (rearing up to hold the BIG claws)
    {"type": "polygon", "points": [[70, 162], [92, 162], [96, 140], [76, 136]], "color": PUR, "outline": DPUR, "outline_w": 1},
    {"type": "circle", "cx": 88, "cy": 142, "r": 8, "color": DPUR, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[82, 140], [96, 140], [92, 108], [78, 112]], "color": PUR, "outline": DPUR, "outline_w": 1},
    {"type": "circle", "cx": 86, "cy": 112, "r": 7, "color": DPUR, "outline": BLK, "outline_w": 1},

    # ===== TWO BIG SCYTHE CLAWS (long thin CURVED crescents, glowing) — signature =====
    # claw 1 (front-most, long thin crescent curving up-left, scythe-shaped)
    {"type": "polygon", "points": [[86, 112], [74, 30], [56, 18], [44, 30], [52, 56], [70, 92]],
     "color": MAG, "outline": DPUR, "outline_w": 2},
    {"type": "polygon", "points": [[80, 100], [68, 40], [58, 28], [52, 38], [60, 64], [74, 90]],
     "color": GLOW, "outline": None, "outline_w": 0},  # inner glow band (thin)
    {"type": "line", "start": [74, 30], "end": [60, 64], "color": LILAC, "width": 2},
    {"type": "circle", "cx": 56, "cy": 24, "r": 4, "color": LILAC, "outline": BLK, "outline_w": 1},
    # claw 2 (behind, long thin crescent curving up, scythe-shaped)
    {"type": "polygon", "points": [[96, 112], [110, 44], [128, 32], [142, 44], [134, 70], [108, 100]],
     "color": MAG, "outline": DPUR, "outline_w": 2},
    {"type": "polygon", "points": [[100, 100], [114, 50], [126, 40], [132, 50], [124, 72], [104, 96]],
     "color": GLOW, "outline": None, "outline_w": 0},
    {"type": "line", "start": [110, 44], "end": [124, 72], "color": LILAC, "width": 2},
    {"type": "circle", "cx": 130, "cy": 38, "r": 4, "color": LILAC, "outline": BLK, "outline_w": 1},

    # ===== HEAD (BIG elongated snout, left end) =====
    {"type": "circle", "cx": 66, "cy": 138, "r": 30, "color": PUR, "outline": DPUR, "outline_w": 2},
    # BIG elongated snout pointing left
    {"type": "polygon", "points": [[52, 122], [6, 118], [2, 152], [52, 158]],
     "color": PUR, "outline": DPUR, "outline_w": 2},
    # snout top ridge (magenta)
    {"type": "polygon", "points": [[52, 122], [10, 118], [12, 130], [52, 132]], "color": MAG, "outline": DPUR, "outline_w": 1},
    # lower jaw
    {"type": "polygon", "points": [[48, 154], [8, 156], [14, 170], [50, 162]], "color": DPUR, "outline": BLK, "outline_w": 1},
    # BIG fangs
    {"type": "polygon", "points": [[10, 152], [18, 166], [24, 152]], "color": LILAC, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[26, 152], [34, 166], [40, 152]], "color": LILAC, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[40, 152], [46, 164], [50, 152]], "color": LILAC, "outline": BLK, "outline_w": 1},
    # nostril
    {"type": "circle", "cx": 8, "cy": 138, "r": 4, "color": BLK, "outline": None, "outline_w": 0},
    # ear crests
    {"type": "polygon", "points": [[60, 112], [54, 84], [72, 106]], "color": PUR, "outline": DPUR, "outline_w": 1},
    {"type": "polygon", "points": [[82, 112], [78, 86], [94, 108]], "color": PUR, "outline": DPUR, "outline_w": 1},
    {"type": "polygon", "points": [[56, 90], [62, 76], [68, 92]], "color": MAG, "outline": DPUR, "outline_w": 1},

    # BIG VOID EYES (glowing)
    {"type": "circle", "cx": 54, "cy": 132, "r": 8, "color": GLOW, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 78, "cy": 130, "r": 8, "color": GLOW, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 54, "cy": 132, "r": 3, "color": LILAC, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 78, "cy": 130, "r": 3, "color": LILAC, "outline": None, "outline_w": 0},
    {"type": "line", "start": [46, 124], "end": [84, 122], "color": DPUR, "width": 3},

    # void sparkles
    {"type": "circle", "cx": 196, "cy": 150, "r": 3, "color": GLOW, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 60, "cy": 200, "r": 2, "color": GLOW, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 180, "cy": 200, "r": 2, "color": GLOW, "outline": None, "outline_w": 0},
]

if __name__ == "__main__":
    print(f"Belveth committed score: {committed_score('Belveth')}")
    r = improve("Belveth", prims, do_save=True, gate_n=3)
    print(r)
    render(prims, "/tmp/belveth_new.png")
