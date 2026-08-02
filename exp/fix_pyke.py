"""Hand-author Pyke — current sprite is severely undersized (tiny cluster at
center, ~14 thin primitives). Re-author a FULL-BODY gaunt undead bilgewater
assassin filling the canvas.

Pyke canon: lean gaunt humanoid, glowing ghostly eyes, tattered nautical
clothing, undead pale skin, bone-like armor accents, spectral aura.
Colors: teal / dark grey / deep blue. Weapon: bone harpoon.

Draw him BIG, centered, hooded, with the signature glowing green-ghost eyes
and a raised bone harpoon.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from champ_improver import improve, render, committed_score

# palette
TEAL = [40, 175, 165]       # spectral teal
DTEAL = [25, 110, 105]      # dark teal
DGREY = [55, 60, 68]        # dark grey clothing
VGREY = [35, 40, 48]        # very dark grey
SK = [175, 190, 180]        # undead pale greenish skin
DSK = [120, 140, 130]       # shaded skin
BONE = [210, 200, 170]      # bone armor
GLOW = [120, 255, 170]      # ghostly green glow (eyes, aura)
BLK = [15, 18, 22]          # black outline
DBLUE = [30, 50, 80]        # deep blue accents

prims = [
    # ===== SPECTRAL AURA (behind, visible teal glow around whole body) =====
    {"type": "circle", "cx": 128, "cy": 150, "r": 78, "color": [35, 110, 100], "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 128, "cy": 150, "r": 66, "color": [28, 90, 85], "outline": None, "outline_w": 0},
    # spectral wisps trailing up
    {"type": "polygon", "points": [[96, 100], [88, 70], [98, 76], [104, 104]], "color": [30, 130, 120], "outline": None, "outline_w": 0},
    {"type": "polygon", "points": [[160, 100], [168, 70], [158, 76], [152, 104]], "color": [30, 130, 120], "outline": None, "outline_w": 0},

    # ===== BONE HARPOON (raised, right side, diagonal) — signature weapon =====
    # shaft
    {"type": "line", "start": [150, 170], "end": [220, 70], "color": BONE, "width": 7},
    {"type": "line", "start": [150, 170], "end": [220, 70], "color": [180, 170, 140], "width": 3},
    # harpoon head (barbed) at top-right
    {"type": "polygon", "points": [[218, 72], [240, 50], [232, 44], [224, 56], [214, 66]],
     "color": BONE, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[232, 60], [244, 52], [238, 48]], "color": [180, 170, 140], "outline": BLK, "outline_w": 1},  # barb
    # rope/chain wrap at grip
    {"type": "line", "start": [150, 170], "end": [156, 162], "color": DGREY, "width": 4},

    # ===== LEGS (tattered, gaunt) =====
    {"type": "polygon", "points": [[108, 178], [124, 178], [122, 226], [110, 230]],
     "color": DGREY, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[132, 178], [148, 178], [146, 226], [134, 230]],
     "color": DGREY, "outline": BLK, "outline_w": 1},
    # tattered hems (jagged)
    {"type": "polygon", "points": [[108, 224], [116, 230], [112, 232], [108, 228]], "color": VGREY, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[118, 224], [124, 230], [120, 232], [116, 228]], "color": VGREY, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[132, 224], [140, 230], [136, 232], [132, 228]], "color": VGREY, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[142, 224], [148, 230], [144, 232], [140, 228]], "color": VGREY, "outline": BLK, "outline_w": 1},
    # boots
    {"type": "ellipse", "x": 106, "y": 226, "w": 22, "h": 12, "color": BLK, "outline": None, "outline_w": 0},
    {"type": "ellipse", "x": 130, "y": 226, "w": 22, "h": 12, "color": BLK, "outline": None, "outline_w": 0},

    # ===== TORSO (tattered nautical coat) =====
    {"type": "polygon", "points": [[96, 120], [160, 120], [156, 182], [100, 182]],
     "color": DGREY, "outline": BLK, "outline_w": 2},
    # coat shading
    {"type": "polygon", "points": [[100, 122], [128, 122], [126, 180], [102, 180]], "color": VGREY, "outline": None, "outline_w": 0},
    # bone chest plate accent (clearly BONE-colored, not metallic)
    {"type": "polygon", "points": [[110, 130], [146, 130], [142, 160], [114, 160]], "color": BONE, "outline": BLK, "outline_w": 1},
    {"type": "line", "start": [128, 130], "end": [128, 160], "color": [180, 170, 140], "width": 2},
    # rib accents (bone-like armor)
    {"type": "line", "start": [114, 140], "end": [142, 140], "color": [180, 170, 140], "width": 1},
    {"type": "line", "start": [114, 150], "end": [142, 150], "color": [180, 170, 140], "width": 1},
    # tattered coat edges (jagged hem at sides — nautical rags)
    {"type": "polygon", "points": [[96, 150], [88, 156], [94, 158], [96, 156]], "color": VGREY, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[160, 150], [168, 156], [162, 158], [160, 156]], "color": VGREY, "outline": BLK, "outline_w": 1},
    # belt
    {"type": "rect", "x": 98, "y": 174, "w": 60, "h": 8, "color": DBLUE, "outline": BLK, "outline_w": 1},
    {"type": "rect", "x": 124, "y": 174, "w": 8, "h": 8, "color": BONE, "outline": BLK, "outline_w": 1},

    # ===== LEFT ARM (holding harpoon lower / dagger) =====
    {"type": "polygon", "points": [[96, 128], [112, 128], [104, 170], [88, 162]], "color": DGREY, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 96, "cy": 164, "r": 7, "color": SK, "outline": BLK, "outline_w": 1},  # hand
    # bone dagger in left hand
    {"type": "line", "start": [92, 166], "end": [70, 200], "color": BONE, "width": 4},
    {"type": "polygon", "points": [[68, 198], [62, 208], [66, 210], [72, 202]], "color": BONE, "outline": BLK, "outline_w": 1},

    # ===== RIGHT ARM (raised holding harpoon) =====
    {"type": "polygon", "points": [[148, 128], [164, 128], [156, 168], [142, 162]], "color": DGREY, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 150, "cy": 168, "r": 7, "color": SK, "outline": BLK, "outline_w": 1},  # hand gripping harpoon

    # ===== NECK + HEAD (gaunt undead, PALE skin visible) =====
    {"type": "rect", "x": 120, "y": 100, "w": 16, "h": 22, "color": SK, "outline": BLK, "outline_w": 1},
    # skull (pale undead skin, bigger)
    {"type": "circle", "cx": 128, "cy": 88, "r": 24, "color": SK, "outline": BLK, "outline_w": 2},
    # gaunt cheeks (shade — sunken)
    {"type": "polygon", "points": [[108, 92], [120, 92], [118, 106], [112, 106]], "color": DSK, "outline": None, "outline_w": 0},
    {"type": "polygon", "points": [[136, 92], [148, 92], [144, 106], [138, 106]], "color": DSK, "outline": None, "outline_w": 0},
    # pale forehead highlight (make skin read as pale, not grey)
    {"type": "ellipse", "x": 116, "y": 70, "w": 24, "h": 12, "color": [200, 215, 200], "outline": None, "outline_w": 0},
    # mouth (grim)
    {"type": "rect", "x": 120, "y": 100, "w": 16, "h": 3, "color": BLK, "outline": None, "outline_w": 0},
    # teeth
    {"type": "line", "start": [122, 100], "end": [122, 104], "color": BONE, "width": 1},
    {"type": "line", "start": [128, 100], "end": [128, 104], "color": BONE, "width": 1},
    {"type": "line", "start": [134, 100], "end": [134, 104], "color": BONE, "width": 1},

    # ===== HOOD (tattered, over head) — signature nautical =====
    {"type": "polygon", "points": [[100, 96], [128, 56], [156, 96], [150, 110], [106, 110]],
     "color": DGREY, "outline": BLK, "outline_w": 2},
    {"type": "polygon", "points": [[106, 94], [128, 62], [150, 94], [146, 104], [110, 104]],
     "color": VGREY, "outline": None, "outline_w": 0},
    # hood opening shadow (around face)
    {"type": "circle", "cx": 128, "cy": 88, "r": 24, "color": None, "outline": BLK, "outline_w": 1},

    # ===== GLOWING GHOSTLY EYES — signature =====
    {"type": "circle", "cx": 120, "cy": 86, "r": 6, "color": GLOW, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 136, "cy": 86, "r": 6, "color": GLOW, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 120, "cy": 86, "r": 3, "color": [200, 255, 220], "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 136, "cy": 86, "r": 3, "color": [200, 255, 220], "outline": None, "outline_w": 0},
    # brow
    {"type": "line", "start": [112, 80], "end": [144, 80], "color": BLK, "width": 2},

    # ===== SPECTRAL TRAIL / glow wisps =====
    {"type": "circle", "cx": 80, "cy": 110, "r": 4, "color": GLOW, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 176, "cy": 110, "r": 4, "color": GLOW, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 70, "cy": 180, "r": 3, "color": TEAL, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 186, "cy": 180, "r": 3, "color": TEAL, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 128, "cy": 240, "r": 4, "color": TEAL, "outline": None, "outline_w": 0},
]

if __name__ == "__main__":
    print(f"Pyke committed score: {committed_score('Pyke')}")
    r = improve("Pyke", prims, do_save=True, gate_n=3)
    print(r)
    render(prims, "/tmp/pyke_new.png")
