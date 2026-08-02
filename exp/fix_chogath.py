"""Hand-author Cho'Gath as a massive hulking void BEAST with a clear body + legs.

The committed/scaled sprite is a giant blob — no visible legs, body fills the
whole canvas (clipped). Cho'Gath canon: massive hulking beast with a
disproportionately large maw. Features: giant gaping mouth (with teeth),
six small spikes on back, void-infused skin (purple/dark violet), small
glowing eyes, massive claws. He's a quadrupedal void monster.

Re-author so the FULL creature fits with clear:
  - big horizontal body (the hulking mass)
  - giant gaping mouth with teeth (the signature — BIG)
  - 4 thick legs with massive claws (visible at the bottom)
  - 6 back spikes
  - small glowing green eyes
  - purple / dark violet
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from champ_improver import improve, render, committed_score, gate, save

PUR = [90, 45, 120]        # purple body (void-infused)
DPUR = [55, 25, 80]        # dark violet shade
VDPUR = [35, 15, 55]       # very dark void
BLK = [20, 10, 30]         # black outline
GLOW = [160, 255, 80]      # glowing green eyes
TOOTH = [235, 230, 215]    # teeth (bone white)
CLAW = [220, 215, 200]     # claws
SPIKE = [120, 60, 150]     # back spikes (lighter purple)
MAW = [60, 15, 30]         # mouth interior (dark red-violet)

prims = [
    # ===== 4 LEGS (drawn first, behind/below body) =====
    # front-left leg
    {"type": "polygon", "points": [[78, 170], [98, 170], [96, 218], [82, 224]], "color": DPUR, "outline": BLK, "outline_w": 2},
    {"type": "circle", "cx": 88, "cy": 220, "r": 9, "color": DPUR, "outline": BLK, "outline_w": 1},  # foot
    # front-left claws (3 big)
    {"type": "polygon", "points": [[80, 226], [76, 240], [82, 238], [84, 228]], "color": CLAW, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[88, 228], [86, 242], [92, 240], [92, 230]], "color": CLAW, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[96, 226], [96, 240], [102, 238], [100, 228]], "color": CLAW, "outline": BLK, "outline_w": 1},

    # front-right leg
    {"type": "polygon", "points": [[118, 170], [138, 170], [136, 218], [122, 224]], "color": DPUR, "outline": BLK, "outline_w": 2},
    {"type": "circle", "cx": 128, "cy": 220, "r": 9, "color": DPUR, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[120, 226], [116, 240], [122, 238], [124, 228]], "color": CLAW, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[128, 228], [126, 242], [132, 240], [132, 230]], "color": CLAW, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[136, 226], [136, 240], [142, 238], [140, 228]], "color": CLAW, "outline": BLK, "outline_w": 1},

    # back-left leg
    {"type": "polygon", "points": [[158, 170], [178, 170], [176, 218], [162, 224]], "color": DPUR, "outline": BLK, "outline_w": 2},
    {"type": "circle", "cx": 168, "cy": 220, "r": 9, "color": DPUR, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[160, 226], [156, 240], [162, 238], [164, 228]], "color": CLAW, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[168, 228], [166, 242], [172, 240], [172, 230]], "color": CLAW, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[176, 226], [176, 240], [182, 238], [180, 228]], "color": CLAW, "outline": BLK, "outline_w": 1},

    # back-right leg
    {"type": "polygon", "points": [[198, 170], [218, 170], [216, 218], [202, 224]], "color": DPUR, "outline": BLK, "outline_w": 2},
    {"type": "circle", "cx": 208, "cy": 220, "r": 9, "color": DPUR, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[200, 226], [196, 240], [202, 238], [204, 228]], "color": CLAW, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[208, 228], [206, 242], [212, 240], [212, 230]], "color": CLAW, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[216, 226], [216, 240], [222, 238], [220, 228]], "color": CLAW, "outline": BLK, "outline_w": 1},

    # ===== MAIN BODY (hulking mass, horizontal) =====
    {"type": "ellipse", "x": 60, "y": 110, "w": 180, "h": 80, "color": PUR, "outline": BLK, "outline_w": 3},
    # body shading (darker underside)
    {"type": "ellipse", "x": 72, "y": 150, "w": 156, "h": 36, "color": DPUR, "outline": None, "outline_w": 0},
    # body highlight (top)
    {"type": "ellipse", "x": 90, "y": 116, "w": 120, "h": 20, "color": [115, 60, 145], "outline": None, "outline_w": 0},

    # ===== 6 BACK SPIKES (on top of body) =====
    {"type": "polygon", "points": [[78, 112], [72, 84], [88, 110]], "color": SPIKE, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[100, 110], [96, 78], [112, 108]], "color": SPIKE, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[122, 108], [120, 74], [136, 106]], "color": SPIKE, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[144, 108], [144, 74], [158, 106]], "color": SPIKE, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[166, 110], [168, 78], [182, 108]], "color": SPIKE, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[188, 112], [192, 84], [206, 110]], "color": SPIKE, "outline": BLK, "outline_w": 1},
    # spike glints
    {"type": "line", "start": [80, 100], "end": [78, 90], "color": [180, 120, 210], "width": 1},
    {"type": "line", "start": [104, 98], "end": [102, 86], "color": [180, 120, 210], "width": 1},

    # ===== GIANT GAPING MOUTH (the signature — BIG, front-center) =====
    # mouth interior (dark)
    {"type": "ellipse", "x": 96, "y": 130, "w": 110, "h": 50, "color": MAW, "outline": BLK, "outline_w": 3},
    # upper teeth (big, pointing down)
    {"type": "polygon", "points": [[104, 132], [110, 156], [116, 132]], "color": TOOTH, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[120, 132], [128, 158], [136, 132]], "color": TOOTH, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[140, 132], [148, 156], [156, 132]], "color": TOOTH, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[160, 132], [168, 158], [176, 132]], "color": TOOTH, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[180, 132], [186, 154], [192, 132]], "color": TOOTH, "outline": BLK, "outline_w": 1},
    # lower teeth (big, pointing up)
    {"type": "polygon", "points": [[106, 178], [112, 156], [118, 178]], "color": TOOTH, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[122, 178], [130, 154], [138, 178]], "color": TOOTH, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[142, 178], [150, 156], [158, 178]], "color": TOOTH, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[162, 178], [170, 156], [178, 178]], "color": TOOTH, "outline": BLK, "outline_w": 1},
    {"type": "polygon", "points": [[182, 178], [188, 158], [194, 178]], "color": TOOTH, "outline": BLK, "outline_w": 1},

    # ===== SMALL GLOWING EYES (above the mouth, on the head region) =====
    {"type": "circle", "cx": 110, "cy": 120, "r": 6, "color": GLOW, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 190, "cy": 120, "r": 6, "color": GLOW, "outline": BLK, "outline_w": 1},
    {"type": "circle", "cx": 110, "cy": 120, "r": 3, "color": [220, 255, 180], "outline": None, "outline_w": 0},
    {"type": "circle", "cx": 190, "cy": 120, "r": 3, "color": [220, 255, 180], "outline": None, "outline_w": 0},
    # brow ridge
    {"type": "line", "start": [100, 112], "end": [200, 112], "color": DPUR, "width": 2},
]

if __name__ == "__main__":
    print(f"Chogath committed score: {committed_score('Chogath')}")
    r = improve("Chogath", prims, do_save=True, gate_n=6)
    print(r)
    render(prims, "/tmp/chogath_new.png")
