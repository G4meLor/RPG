"""Kaisa deep-focus: hand-author primitives to break 7 -> 8-10.

v1=6, v2=6, v3=4 (regressed badly — too sparse, VLM lost void carapace).
The committed 7 has the void carapace reading but misses female silhouette +
sleek armor + pointed ears. Approach #4: START from the committed sprite's
structure (which scores 7) and ADD the 3 missing features surgically without
destroying the void carapace. Keep the dark void suit body + add: (a) clearer
hourglass waist, (b) sleek armor panel highlights with glowing seams, (c) BIG
pointed void ears on the helmet, (d) glowing visor. Bio-organic shoulder
cannons stay prominent.
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve

OUT = (18, 10, 28)
SUIT_DARK = (38, 20, 58)
SUIT = (78, 38, 115)
SUIT_LIGHT = (115, 55, 155)
MAGENTA = (210, 70, 165)
MAGENTA_BRIGHT = (245, 130, 225)
VOID_GLOW = (180, 90, 210)
VOID_DEEP = (120, 50, 175)
VISOR = (230, 110, 220)
CANNON_DARK = (30, 15, 48)
CANNON = (70, 32, 105)
SKIN = (220, 188, 168)


def kaisa_prims_v4():
    """Approach #4: build on the committed-7 structure. Keep void carapace body,
    ADD hourglass waist + sleek armor seams + BIG pointed void ears + visor."""
    P = []

    # ===== SHOULDER CANNONS (bio-organic, prominent, glowing ports) =====
    # LEFT cannon — organic curved, void port glowing
    P.append({"type":"polygon","points":[(76,88),(106,82),(110,108),(96,120),(74,112)],
              "color":CANNON,"outline":OUT,"outline_w":2})
    P.append({"type":"ellipse","x":70,"y":92,"w":18,"h":24,"color":CANNON_DARK,
              "outline":MAGENTA,"outline_w":2})
    P.append({"type":"circle","cx":80,"cy":104,"r":7,"color":VOID_GLOW,
              "outline":MAGENTA_BRIGHT,"outline_w":1})
    P.append({"type":"circle","cx":80,"cy":104,"r":3,"color":MAGENTA_BRIGHT})
    # organic ridge
    P.append({"type":"line","start":[84,88],"end":[100,114],"color":MAGENTA,"width":1})

    # RIGHT cannon
    P.append({"type":"polygon","points":[(180,88),(150,82),(146,108),(160,120),(182,112)],
              "color":CANNON,"outline":OUT,"outline_w":2})
    P.append({"type":"ellipse","x":168,"y":92,"w":18,"h":24,"color":CANNON_DARK,
              "outline":MAGENTA,"outline_w":2})
    P.append({"type":"circle","cx":176,"cy":104,"r":7,"color":VOID_GLOW,
              "outline":MAGENTA_BRIGHT,"outline_w":1})
    P.append({"type":"circle","cx":176,"cy":104,"r":3,"color":MAGENTA_BRIGHT})
    P.append({"type":"line","start":[172,88],"end":[156,114],"color":MAGENTA,"width":1})

    # ===== LEGS (athletic, void suit) =====
    P.append({"type":"polygon","points":[(106,154),(124,154),(122,214),(110,218)],
              "color":SUIT_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(132,154),(150,154),(146,218),(134,214)],
              "color":SUIT_DARK,"outline":OUT,"outline_w":2})
    # glowing seams (sleek futuristic armor)
    P.append({"type":"line","start":[115,156],"end":[116,212],"color":MAGENTA,"width":1})
    P.append({"type":"line","start":[141,156],"end":[140,212],"color":MAGENTA,"width":1})
    # thigh armor panels
    P.append({"type":"polygon","points":[(108,156),(122,156),(120,184),(110,184)],
              "color":SUIT,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(134,156),(148,156),(146,184),(136,184)],
              "color":SUIT,"outline":OUT,"outline_w":1})
    # boots
    P.append({"type":"rect","x":106,"y":214,"w":22,"h":8,"color":SUIT,
              "outline":OUT,"outline_w":2,"radius":2})
    P.append({"type":"rect","x":128,"y":214,"w":22,"h":8,"color":SUIT,
              "outline":OUT,"outline_w":2,"radius":2})

    # ===== TORSO — HOURGLASS female silhouette + void carapace =====
    # broad shoulders, NARROW waist (hourglass = athletic female)
    P.append({"type":"polygon","points":[(98,96),(158,96),(150,128),(154,156),
              (102,156),(106,128)],
              "color":SUIT_DARK,"outline":OUT,"outline_w":2})
    # sleek armor panels (futuristic — smooth, defined, NOT flat slab)
    P.append({"type":"polygon","points":[(104,100),(128,100),(126,140),(108,140)],
              "color":SUIT,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(128,100),(152,100),(148,140),(130,140)],
              "color":SUIT,"outline":OUT,"outline_w":1})
    # carapace texture — organic scale ridges (void carapace, not flat)
    for ry in (106, 114, 122, 130):
        P.append({"type":"line","start":[110,ry],"end":[146,ry],"color":SUIT_LIGHT,"width":1})
    # GLOWING CENTER SEAM (void energy + sleek armor)
    P.append({"type":"line","start":[128,96],"end":[128,156],"color":MAGENTA,"width":2})
    P.append({"type":"line","start":[128,96],"end":[128,156],"color":MAGENTA_BRIGHT,"width":1})
    # waist accent (hourglass emphasis)
    P.append({"type":"line","start":[106,128],"end":[150,128],"color":MAGENTA,"width":2})
    # chest void gem
    P.append({"type":"circle","cx":128,"cy":114,"r":5,"color":VOID_GLOW,
              "outline":MAGENTA_BRIGHT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":114,"r":2,"color":MAGENTA_BRIGHT})

    # ===== ARMS (sleek, athletic) =====
    P.append({"type":"polygon","points":[(90,102),(102,102),(100,148),(88,150)],
              "color":SUIT_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"line","start":[96,104],"end":[95,146],"color":MAGENTA,"width":1})
    P.append({"type":"polygon","points":[(154,102),(166,102),(168,150),(156,148)],
              "color":SUIT_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"line","start":[160,104],"end":[161,146],"color":MAGENTA,"width":1})
    # hands
    P.append({"type":"circle","cx":92,"cy":152,"r":5,"color":SUIT,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":164,"cy":152,"r":5,"color":SUIT,"outline":OUT,"outline_w":1})

    # ===== NECK (slender — female tell) =====
    P.append({"type":"rect","x":122,"y":84,"w":12,"h":12,"color":SKIN,
              "outline":OUT,"outline_w":1,"radius":2})

    # ===== HEAD + VOID HELMET (BIG pointed ears + glowing visor) =====
    P.append({"type":"circle","cx":128,"cy":70,"r":15,"color":SUIT_DARK,
              "outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":68,"r":13,"color":SUIT,
              "outline":OUT,"outline_w":1})

    # POINTED VOID-LIKE EARS — BIG, swept-back, glowing tips
    P.append({"type":"polygon","points":[(112,60),(100,40),(98,56),(110,68)],
              "color":SUIT,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(144,60),(156,40),(158,56),(146,68)],
              "color":SUIT,"outline":OUT,"outline_w":2})
    # ear tip glows (void energy)
    P.append({"type":"circle","cx":101,"cy":42,"r":3,"color":MAGENTA_BRIGHT,
              "outline":MAGENTA,"outline_w":1})
    P.append({"type":"circle","cx":155,"cy":42,"r":3,"color":MAGENTA_BRIGHT,
              "outline":MAGENTA,"outline_w":1})

    # GLOWING VISOR — prominent magenta band
    P.append({"type":"polygon","points":[(115,68),(141,68),(139,76),(117,76)],
              "color":VISOR,"outline":MAGENTA,"outline_w":1})
    P.append({"type":"line","start":[117,72],"end":[139,72],"color":MAGENTA_BRIGHT,"width":1})
    P.append({"type":"circle","cx":121,"cy":72,"r":2,"color":MAGENTA_BRIGHT})
    P.append({"type":"circle","cx":135,"cy":72,"r":2,"color":MAGENTA_BRIGHT})

    # helmet crest
    P.append({"type":"line","start":[128,56],"end":[128,68],"color":MAGENTA,"width":1})

    return P


if __name__ == "__main__":
    prims = kaisa_prims_v4()
    r = improve("Kaisa", prims, gate_n=3)
    print("RESULT v4:", r)
