"""Hand-author Hecarim — the committed sprite reads as a blob, not a centaur
(score 5, rec=False, "blobby shapes, no skeletal features, no armor, no mane").

Hecarim = spectral undead CENTAUR: humanoid torso on a horse body, glowing teal
eyes, heavy plate armor, flowing ghostly mane, massive polearm. Colors:
spectral teal / dark grey / silver.

Re-author a clear centaur silhouette: horse body (4 legs, horizontal) on the
bottom, humanoid torso rising from the front, polearm raised.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from champ_improver import improve, render, committed_score, gate, save

TEAL = [40, 175, 165]       # spectral teal
DTEAL = [25, 110, 105]
DGREY = [60, 65, 72]        # dark grey body
VGREY = [40, 45, 52]
SILVER = [180, 185, 195]    # silver armor
GLOW = [120, 255, 200]      # ghostly teal glow
BLK = [18, 22, 26]
MANE = [200, 230, 220]      # ghostly pale mane

prims = [
    # ===== SPECTRAL GLOW AURA (behind) =====
    {"type": "circle", "cx": 128, "cy": 150, "r": 80, "color": [25, 80, 80], "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 128, "cy": 150, "r": 68, "color": [30, 95, 90], "outline": None, "outline_w": 0},

    # ===== POLEARM (raised, right side, diagonal) — signature weapon =====
    {"type": "line", "start": [150, 150], "end": [222, 40], "color": SILVER, "width": 6},
    {"type": "line", "start": [150, 150], "end": [222, 40], "color": [210, 215, 225], "width": 2},
    # polearm blade (teal glowing)
    {"type": "polygon", "points": [[218, 44], [240, 20], [232, 14], [224, 26], [214, 38]], "color": TEAL, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[232, 30], [244, 22], [238, 18]], "color": GLOW, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 236, "cy": 22, "r": 3, "color": GLOW, "outline": None, "outline_w": 0},

    # ===== HORSE BODY (horizontal, lower) =====
    {"type": "ellipse", "x": 50, "y": 150, "w": 150, "h": 56, "color": DGREY, "outline": BLK, "outline_w": 2},
    # horse chest (front, left)
    {"type": "circle", "cx": 70, "cy": 168, "r": 26, "color": DGREY, "outline": BLK, "outline_w": 2},
    # horse rump (back, right)
    {"type": "circle", "cx": 186, "cy": 170, "r": 24, "color": DGREY, "outline": BLK, "outline_w": 2},
    # horse belly shade
    {"type": "ellipse", "x": 60, "y": 176, "w": 130, "h": 22, "color": VGREY, "outline": None, "outline_w": 0},

    # ===== HORSE LEGS (4, digitigrade) =====
    # front-left
    {"type": "rect", "x": 56, "y": 188, "w": 14, "h": 40, "color": DGREY, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[56, 226], [70, 226], [66, 238], [60, 238]], "color": VGREY, "outline": BLK, "outline_w": 1},  # hoof
    # front-right
    {"type": "rect", "x": 80, "y": 192, "w": 14, "h": 38, "color": VGREY, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[80, 228], [94, 228], [90, 238], [84, 238]], "color": BLK, "outline": BLK, "outline_w": 1},
    # back-left
    {"type": "rect", "x": 168, "y": 188, "w": 14, "h": 40, "color": DGREY, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[168, 226], [182, 226], [178, 238], [172, 238]], "color": VGREY, "outline": BLK, "outline_w": 1},
    # back-right
    {"type": "rect", "x": 192, "y": 192, "w": 14, "h": 38, "color": VGREY, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[192, 228], [206, 228], [202, 238], [196, 238]], "color": BLK, "outline": BLK, "outline_w": 1},

    # ===== HORSE NECK + HEAD (front-left, where the humanoid torso rises) =====
    # Actually Hecarim's HORSE head is at the front; the humanoid torso is on TOP.
    # Horse neck (front-left, going up-forward)
    {"type": "polygon", "points": [[58, 150], [40, 120], [34, 96], [50, 92], [60, 116], [72, 146]], "color": DGREY, "outline": BLK, "outline_w": 2},
    # horse head (elongated, front-left)
    {"type": "ellipse", "x": 24, "y": 84, "w": 36, "h": 26, "color": DGREY, "outline": BLK, "outline_w": 2},
    # horse snout
    {"type": "polygon", "points": [[24, 92], [6, 96], [4, 108], [26, 108]], "color": DGREY, "outline": BLK, "outline_w": 1},
    # horse nostril
    {"type": "circle", "cx": 10, "cy": 102, "r": 3, "color": BLK, "outline": None, "outline_w": 0},
    # horse mouth line
    {"type": "line", "start": [8, 106], "end": [24, 106], "color": BLK, "width": 1},
    # horse ears
    {"type": "polygon", "points": [[40, 84], [36, 70], [46, 80]], "color": DGREY, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[52, 84], [50, 70], [58, 80]], "color": DGREY, "outline": BLK, "outline_w": 1},

    # ===== FLOWING GHOSTLY MANE (along horse neck, teal/white, flowing) =====
    {"type":"polygon","points":[[44,96],[40,86],[48,90],[50,100]],"color":MANE,"outline":BLK,"outline_w":1},
    {"type":"polygon","points":[[50,108],[44,98],[54,102],[56,112]],"color":MANE,"outline":BLK,"outline_w":1},
    {"type":"polygon","points":[[56,120],[48,110],[60,114],[62,124]],"color":MANE,"outline":BLK,"outline_w":1},
    {"type":"polygon","points":[[62,132],[54,122],[66,126],[68,136]],"color":MANE,"outline":BLK,"outline_w":1},
    # mane glow strands
    {"type":"line","start":[48,92],"end":[44,82],"color":GLOW,"width":1},
    {"type":"line","start":[54,104],"end":[50,94],"color":GLOW,"width":1},
    {"type":"line","start":[60,116],"end":[56,106],"color":GLOW,"width":1},

    # ===== HUMANOID TORSO (rising on top of the horse body, where the rider sits) =====
    # Hecarim's torso emerges from the front of the horse body. Place it at x100-150, y90-150.
    {"type": "polygon", "points": [[100, 100], [150, 100], [146, 150], [104, 150]], "color": DGREY, "outline": BLK, "outline_w": 2},
    # heavy plate armor chest (silver)
    {"type": "polygon", "points": [[106, 110], [144, 110], [140, 146], [110, 146]], "color": SILVER, "outline": BLK, "outline_w": 1},
    # armor chest emblem (teal gem)
    {"type": "circle", "cx": 125, "cy": 128, "r": 7, "color": TEAL, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 125, "cy": 128, "r": 3, "color": GLOW, "outline": None, "outline_w": 0},
    # armor ribs
    {"type": "line", "start": [110, 122], "end": [140, 122], "color": [140, 145, 155], "width": 1},
    {"type": "line", "start": [110, 134], "end": [140, 134], "color": [140, 145, 155], "width": 1},
    # shoulder pauldrons (silver)
    {"type": "ellipse", "x": 92, "y": 98, "w": 22, "h": 16, "color": SILVER, "outline": BLK, "outline_w": 1},
    {"type": "ellipse", "x": 136, "y": 98, "w": 22, "h": 16, "color": SILVER, "outline": BLK, "outline_w": 1},

    # ===== HUMANOID HEAD (on top of torso) =====
    {"type": "rect", "x": 116, "y": 76, "w": 18, "h": 18, "color": DGREY, "outline": BLK, "outline_w": 1},  # neck
    {"type": "circle", "cx": 125, "cy": 68, "r": 18, "color": DGREY, "outline": BLK, "outline_w": 2},  # skull
    # helmet (silver plate)
    {"type": "polygon", "points": [[108, 60], [125, 44], [142, 60], [140, 72], [110, 72]], "color": SILVER, "outline": BLK, "outline_w": 1},
    # helmet crest (teal)
    {"type": "polygon", "points": [[125, 44], [120, 30], [130, 30]], "color": TEAL, "outline": BLK, "outline_w": 1},
    # GLOWING TEAL EYES — signature
    {"type": "circle", "cx": 118, "cy": 66, "r": 5, "color": GLOW, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 132, "cy": 66, "r": 5, "color": GLOW, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 118, "cy": 66, "r": 2, "color": [220, 255, 235], "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 132, "cy": 66, "r": 2, "color": [220, 255, 235], "outline": None, "outline_w": 0},
    # skeletal jaw (undead)
    {"type": "polygon", "points": [[116, 74], [134, 74], [132, 82], [118, 82]], "color": VGREY, "outline": BLK, "outline_w": 1},
    {"type": "line", "start": [120, 76], "end": [120, 80], "color": [200, 210, 215], "width": 1},
    {"type": "line", "start": [125, 76], "end": [125, 80], "color": [200, 210, 215], "width": 1},
    {"type": "line", "start": [130, 76], "end": [130, 80], "color": [200, 210, 215], "width": 1},

    # ===== ARMS (humanoid, right arm holds polearm) =====
    {"type": "polygon", "points": [[140, 110], [156, 110], [152, 146], [140, 146]], "color": DGREY, "outline": BLK, "outline_w": 1},
    {"type": "ellipse", "x": 146, "y": 140, "w": 16, "h": 14, "color": SILVER, "outline": BLK, "outline_w": 1},  # gauntlet
    # left arm
    {"type": "polygon", "points": [[100, 110], [116, 110], [112, 146], [100, 146]], "color": DGREY, "outline": BLK, "outline_w": 1},
    {"type": "ellipse", "x": 94, "y": 140, "w": 16, "h": 14, "color": SILVER, "outline": BLK, "outline_w": 1},

    # ===== TAIL (horse, flowing back-right) =====
    {"type": "polygon", "points": [[200, 168], [224, 176], [232, 196], [224, 210], [210, 196], [204, 180]], "color": DGREY, "outline": BLK, "outline_w": 1},
    {"type": "line", "start": [206, 176], "end": [226, 196], "color": MANE, "width": 2},
    {"type": "line", "start": [210, 180], "end": [228, 200], "color": GLOW, "width": 1},

    # spectral wisps
    {"type": "circle", "cx": 80, "cy": 120, "r": 3, "color": GLOW, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 170, "cy": 130, "r": 3, "color": GLOW, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 110, "cy": 220, "r": 2, "color": TEAL, "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 190, "cy": 220, "r": 2, "color": TEAL, "outline": None, "outline_w": 0},
]

if __name__ == "__main__":
    print(f"Hecarim committed score: {committed_score('Hecarim')}")
    r = improve("Hecarim", prims, do_save=True, gate_n=6)
    print(r)
    render(prims, "/tmp/hecarim_new.png")
