"""Kaisa deep-focus: hand-author primitives to break 7 -> 8-10.

7 rounds done. Summary:
- v1 (cannons+visor): 6 (regressed)
- v2 (void-wings): 6 (regressed)
- v3 (sparse clean): 4 (regressed badly)
- v4 (committed-7 structure + ears+visor+seams): 7 (matched, missing female+carapace)
- v5 (segmented carapace + bust): 7 (matched, missing female+sleek armor)
- v6 (sleek bodysuit + bust + bright seams): 7 (matched, missing female+ears)
- v7 (fashion figurine + hair): 6 (regressed — hair covered the silhouette)

The consistent blocker: 'athletic humanoid female silhouette' — the VLM will NOT
confirm female/athletic from these 256px sprites. v4/v5/v6 all hit 7 (matched
committed, never beat). The committed 7 is the ceiling.

Approach #8 (FINAL): Go back to v4 (the most complete, 7 with all features
present) and make ONE bold change — give her a CLEAR dynamic action pose
(leaning forward, one leg forward = athletic stance) + make the void cannons
MUCH bigger and more prominent (the ONE huge unique feature that scores 8-10
on other champs). The pattern says: ONE HUGE signature feature dominating
30-50% of silhouette. The cannons should be that feature.
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
VISOR = (230, 110, 220)
CANNON_DARK = (30, 15, 48)
CANNON = (70, 32, 105)
SKIN = (220, 188, 168)


def kaisa_prims_v8():
    """Approach #8: HUGE bio-organic shoulder cannons as THE dominant icon
    (30-50% of silhouette) + dynamic forward-leaning athletic pose + void helmet."""
    P = []

    # ===== HUGE SHOULDER CANNONS (THE dominant icon — 30-50% of silhouette) =====
    # These are BIG, bio-organic, clearly void (glowing purple ports, organic curves)
    # LEFT cannon — massive, organic, tapered, dominates left side
    P.append({"type":"polygon","points":[(58,80),(104,74),(110,112),(92,128),(54,118)],
              "color":CANNON,"outline":OUT,"outline_w":3})
    # cannon mouth/barrel (front, big glowing port — void-organic, NOT flat)
    P.append({"type":"ellipse","x":48,"y":84,"w":24,"h":32,"color":CANNON_DARK,
              "outline":MAGENTA,"outline_w":3})
    # glowing void core (multi-layer glow = clearly energy, not a wall)
    P.append({"type":"circle","cx":62,"cy":100,"r":10,"color":VOID_GLOW,
              "outline":MAGENTA_BRIGHT,"outline_w":2})
    P.append({"type":"circle","cx":62,"cy":100,"r":6,"color":MAGENTA,"outline":MAGENTA_BRIGHT,"outline_w":1})
    P.append({"type":"circle","cx":62,"cy":100,"r":3,"color":MAGENTA_BRIGHT})
    # organic ridges on cannon (bio-organic texture)
    P.append({"type":"line","start":[70,82],"end":[96,110],"color":MAGENTA,"width":2})
    P.append({"type":"line","start":[74,88],"end":[98,116],"color":SUIT_LIGHT,"width":1})
    # cannon tip spikes (organic, void)
    P.append({"type":"polygon","points":[(54,80),(48,70),(58,78)],
              "color":CANNON,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(58,76),(54,64),(64,74)],
              "color":CANNON,"outline":OUT,"outline_w":1})

    # RIGHT cannon — massive, mirror
    P.append({"type":"polygon","points":[(198,80),(152,74),(146,112),(164,128),(202,118)],
              "color":CANNON,"outline":OUT,"outline_w":3})
    P.append({"type":"ellipse","x":184,"y":84,"w":24,"h":32,"color":CANNON_DARK,
              "outline":MAGENTA,"outline_w":3})
    P.append({"type":"circle","cx":194,"cy":100,"r":10,"color":VOID_GLOW,
              "outline":MAGENTA_BRIGHT,"outline_w":2})
    P.append({"type":"circle","cx":194,"cy":100,"r":6,"color":MAGENTA,"outline":MAGENTA_BRIGHT,"outline_w":1})
    P.append({"type":"circle","cx":194,"cy":100,"r":3,"color":MAGENTA_BRIGHT})
    P.append({"type":"line","start":[186,82],"end":[160,110],"color":MAGENTA,"width":2})
    P.append({"type":"line","start":[182,88],"end":[158,116],"color":SUIT_LIGHT,"width":1})
    P.append({"type":"polygon","points":[(202,80),(208,70),(198,78)],
              "color":CANNON,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(198,76),(202,64),(192,74)],
              "color":CANNON,"outline":OUT,"outline_w":1})

    # ===== LEGS (athletic stance, one forward) =====
    # back leg (left, slightly back)
    P.append({"type":"polygon","points":[(108,154),(124,154),(122,216),(112,220)],
              "color":SUIT_DARK,"outline":OUT,"outline_w":2})
    # front leg (right, forward)
    P.append({"type":"polygon","points":[(130,154),(150,154),(148,216),(134,216)],
              "color":SUIT_DARK,"outline":OUT,"outline_w":2})
    # glowing seams
    P.append({"type":"line","start":[116,156],"end":[117,214],"color":MAGENTA,"width":1})
    P.append({"type":"line","start":[140,156],"end":[141,214],"color":MAGENTA,"width":1})
    # boots
    P.append({"type":"rect","x":106,"y":216,"w":22,"h":8,"color":SUIT,
              "outline":OUT,"outline_w":2,"radius":2})
    P.append({"type":"rect","x":130,"y":216,"w":22,"h":8,"color":SUIT,
              "outline":OUT,"outline_w":2,"radius":2})

    # ===== TORSO — athletic female hourglass (sleek suit) =====
    P.append({"type":"polygon","points":[(100,94),(156,94),(148,124),(152,156),
              (104,156),(108,124)],
              "color":SUIT_DARK,"outline":OUT,"outline_w":2})
    # sleek armor panels
    P.append({"type":"polygon","points":[(106,98),(150,98),(146,152),(110,152)],
              "color":SUIT,"outline":OUT,"outline_w":1})
    # bust (female tell)
    P.append({"type":"circle","cx":118,"cy":108,"r":8,"color":SUIT_LIGHT,
              "outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":138,"cy":108,"r":8,"color":SUIT_LIGHT,
              "outline":OUT,"outline_w":1})
    # glowing center seam + waist
    P.append({"type":"line","start":[128,94],"end":[128,156],"color":MAGENTA_BRIGHT,"width":2})
    P.append({"type":"line","start":[108,124],"end":[148,124],"color":MAGENTA,"width":1})
    # chest gem
    P.append({"type":"circle","cx":128,"cy":108,"r":4,"color":VOID_GLOW,
              "outline":MAGENTA_BRIGHT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":108,"r":2,"color":MAGENTA_BRIGHT})

    # ===== ARMS (reaching forward toward cannons) =====
    P.append({"type":"polygon","points":[(92,100),(104,100),(102,140),(92,142)],
              "color":SUIT_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(152,100),(164,100),(164,142),(154,140)],
              "color":SUIT_DARK,"outline":OUT,"outline_w":2})
    # hands
    P.append({"type":"circle","cx":96,"cy":144,"r":5,"color":SUIT,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":160,"cy":144,"r":5,"color":SUIT,"outline":OUT,"outline_w":1})

    # ===== NECK (slender) =====
    P.append({"type":"rect","x":122,"y":82,"w":12,"h":12,"color":SKIN,
              "outline":OUT,"outline_w":1,"radius":2})

    # ===== HEAD + VOID HELMET (pointed ears + glowing visor) =====
    P.append({"type":"circle","cx":128,"cy":68,"r":15,"color":SUIT_DARK,
              "outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":66,"r":13,"color":SUIT,
              "outline":OUT,"outline_w":1})

    # POINTED VOID-LIKE EARS
    P.append({"type":"polygon","points":[(112,58),(100,38),(98,54),(110,66)],
              "color":SUIT,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(144,58),(156,38),(158,54),(146,66)],
              "color":SUIT,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":101,"cy":40,"r":3,"color":MAGENTA_BRIGHT,
              "outline":MAGENTA,"outline_w":1})
    P.append({"type":"circle","cx":155,"cy":40,"r":3,"color":MAGENTA_BRIGHT,
              "outline":MAGENTA,"outline_w":1})

    # GLOWING VISOR
    P.append({"type":"polygon","points":[(115,66),(141,66),(139,74),(117,74)],
              "color":VISOR,"outline":MAGENTA,"outline_w":1})
    P.append({"type":"line","start":[117,70],"end":[139,70],"color":MAGENTA_BRIGHT,"width":1})
    P.append({"type":"circle","cx":121,"cy":70,"r":2,"color":MAGENTA_BRIGHT})
    P.append({"type":"circle","cx":135,"cy":70,"r":2,"color":MAGENTA_BRIGHT})

    # helmet crest
    P.append({"type":"line","start":[128,54],"end":[128,66],"color":MAGENTA,"width":1})

    return P


if __name__ == "__main__":
    prims = kaisa_prims_v8()
    r = improve("Kaisa", prims, gate_n=3)
    print("RESULT v8:", r)
