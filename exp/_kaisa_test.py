"""Kaisa deep-focus: hand-author primitives to break 7 -> 8-10.

v5=7 (matched, didn't beat). Missing: athletic humanoid female silhouette,
sleek futuristic armor. The carapace texture now reads but the silhouette still
isn't reading as female/athletic AND the armor isn't reading as "sleek futuristic."
Approach #6: SIMPLIFY the armor to read as sleek — use SMOOTH light-colored
panels with clean glowing seams (like Tron/electroluminescent), reduce the
chitinous segmentation (which may read as bulky/insectoid, not sleek). Make the
female silhouette MORE pronounced: bigger head-to-body ratio, clearer bust,
very narrow waist, wider hips. Think "sleek bodysuit" not "insect armor."
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve

OUT = (18, 10, 28)
SUIT_DARK = (42, 24, 65)
SUIT = (88, 44, 130)          # sleek purple suit
SUIT_LIGHT = (165, 80, 200)   # light purple highlight (sleek, smooth)
MAGENTA = (220, 80, 175)
MAGENTA_BRIGHT = (250, 145, 235)
VOID_GLOW = (185, 95, 215)
VISOR = (235, 120, 228)
CANNON_DARK = (32, 16, 50)
CANNON = (75, 34, 110)
SKIN = (225, 195, 175)


def kaisa_prims_v6():
    """Approach #6: SLEEK bodysuit (smooth light panels + glowing seams, not
    bulky insect plates) + pronounced female hourglass + void helmet."""
    P = []

    # ===== SHOULDER CANNONS (bio-organic, glowing ports) =====
    # LEFT cannon
    P.append({"type":"polygon","points":[(76,86),(106,80),(110,108),(96,120),(74,112)],
              "color":CANNON,"outline":OUT,"outline_w":2})
    P.append({"type":"ellipse","x":70,"y":90,"w":18,"h":24,"color":CANNON_DARK,
              "outline":MAGENTA,"outline_w":2})
    P.append({"type":"circle","cx":80,"cy":102,"r":7,"color":VOID_GLOW,
              "outline":MAGENTA_BRIGHT,"outline_w":1})
    P.append({"type":"circle","cx":80,"cy":102,"r":3,"color":MAGENTA_BRIGHT})
    P.append({"type":"line","start":[84,86],"end":[100,112],"color":MAGENTA,"width":1})

    # RIGHT cannon
    P.append({"type":"polygon","points":[(180,86),(150,80),(146,108),(160,120),(182,112)],
              "color":CANNON,"outline":OUT,"outline_w":2})
    P.append({"type":"ellipse","x":168,"y":90,"w":18,"h":24,"color":CANNON_DARK,
              "outline":MAGENTA,"outline_w":2})
    P.append({"type":"circle","cx":176,"cy":102,"r":7,"color":VOID_GLOW,
              "outline":MAGENTA_BRIGHT,"outline_w":1})
    P.append({"type":"circle","cx":176,"cy":102,"r":3,"color":MAGENTA_BRIGHT})
    P.append({"type":"line","start":[172,86],"end":[156,112],"color":MAGENTA,"width":1})

    # ===== LEGS (athletic, sleek suit) =====
    P.append({"type":"polygon","points":[(104,150),(124,150),(122,214),(110,218)],
              "color":SUIT,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(132,150),(152,150),(146,218),(134,214)],
              "color":SUIT,"outline":OUT,"outline_w":2})
    # glowing seams (sleek futuristic — electroluminescent lines)
    P.append({"type":"line","start":[114,152],"end":[116,212],"color":MAGENTA_BRIGHT,"width":2})
    P.append({"type":"line","start":[142,152],"end":[140,212],"color":MAGENTA_BRIGHT,"width":2})
    # boots (sleek)
    P.append({"type":"rect","x":104,"y":214,"w":24,"h":8,"color":SUIT_DARK,
              "outline":OUT,"outline_w":2,"radius":2})
    P.append({"type":"rect","x":128,"y":214,"w":24,"h":8,"color":SUIT_DARK,
              "outline":OUT,"outline_w":2,"radius":2})

    # ===== TORSO — SLEEK BODYSUIT, pronounced female hourglass =====
    # broad shoulders, NARROW waist, hip flare
    P.append({"type":"polygon","points":[(96,94),(160,94),(152,122),(156,156),
              (100,156),(104,122)],
              "color":SUIT,"outline":OUT,"outline_w":2})

    # SLEEK LIGHT PANELS (smooth, futuristic — like a bodysuit, not insect)
    # central panel (smooth, light purple)
    P.append({"type":"polygon","points":[(112,98),(144,98),(140,152),(116,152)],
              "color":SUIT_LIGHT,"outline":OUT,"outline_w":1})
    # BUST (female tell — two smooth rounded shapes at top)
    P.append({"type":"circle","cx":118,"cy":106,"r":8,"color":SUIT_LIGHT,
              "outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":138,"cy":106,"r":8,"color":SUIT_LIGHT,
              "outline":OUT,"outline_w":1})

    # GLOWING SEAMS (sleek futuristic — bright, clean lines)
    # center seam
    P.append({"type":"line","start":[128,94],"end":[128,156],"color":MAGENTA_BRIGHT,"width":2})
    # waist line (NARROW waist = hourglass emphasis)
    P.append({"type":"line","start":[104,122],"end":[152,122],"color":MAGENTA_BRIGHT,"width":2})
    # hip lines (flare)
    P.append({"type":"line","start":[104,140],"end":[116,140],"color":MAGENTA,"width":1})
    P.append({"type":"line","start":[140,140],"end":[152,140],"color":MAGENTA,"width":1})
    # chest void gem
    P.append({"type":"circle","cx":128,"cy":106,"r":4,"color":VOID_GLOW,
              "outline":MAGENTA_BRIGHT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":106,"r":2,"color":MAGENTA_BRIGHT})

    # ===== ARMS (sleek, slender) =====
    P.append({"type":"polygon","points":[(88,100),(100,100),(98,146),(86,148)],
              "color":SUIT,"outline":OUT,"outline_w":2})
    P.append({"type":"line","start":[94,102],"end":[93,144],"color":MAGENTA_BRIGHT,"width":1})
    P.append({"type":"polygon","points":[(156,100),(168,100),(170,148),(158,146)],
              "color":SUIT,"outline":OUT,"outline_w":2})
    P.append({"type":"line","start":[162,102],"end":[163,144],"color":MAGENTA_BRIGHT,"width":1})
    # hands (small)
    P.append({"type":"circle","cx":90,"cy":150,"r":4,"color":SUIT_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":166,"cy":150,"r":4,"color":SUIT_DARK,"outline":OUT,"outline_w":1})

    # ===== NECK (slender — female tell) =====
    P.append({"type":"rect","x":122,"y":82,"w":12,"h":12,"color":SKIN,
              "outline":OUT,"outline_w":1,"radius":2})

    # ===== HEAD + VOID HELMET (BIG pointed ears + glowing visor) =====
    P.append({"type":"circle","cx":128,"cy":66,"r":15,"color":SUIT_DARK,
              "outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":64,"r":13,"color":SUIT,
              "outline":OUT,"outline_w":1})

    # POINTED VOID-LIKE EARS — BIG, swept-back, glowing tips
    P.append({"type":"polygon","points":[(112,56),(100,36),(98,52),(110,64)],
              "color":SUIT,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(144,56),(156,36),(158,52),(146,64)],
              "color":SUIT,"outline":OUT,"outline_w":2})
    # ear tip glows (void energy)
    P.append({"type":"circle","cx":101,"cy":38,"r":3,"color":MAGENTA_BRIGHT,
              "outline":MAGENTA,"outline_w":1})
    P.append({"type":"circle","cx":155,"cy":38,"r":3,"color":MAGENTA_BRIGHT,
              "outline":MAGENTA,"outline_w":1})

    # GLOWING VISOR — prominent magenta band
    P.append({"type":"polygon","points":[(115,64),(141,64),(139,72),(117,72)],
              "color":VISOR,"outline":MAGENTA,"outline_w":1})
    P.append({"type":"line","start":[117,68],"end":[139,68],"color":MAGENTA_BRIGHT,"width":1})
    P.append({"type":"circle","cx":121,"cy":68,"r":2,"color":MAGENTA_BRIGHT})
    P.append({"type":"circle","cx":135,"cy":68,"r":2,"color":MAGENTA_BRIGHT})

    # helmet crest
    P.append({"type":"line","start":[128,52],"end":[128,64],"color":MAGENTA,"width":1})

    return P


if __name__ == "__main__":
    prims = kaisa_prims_v6()
    r = improve("Kaisa", prims, gate_n=3)
    print("RESULT v6:", r)
