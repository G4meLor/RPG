"""Renata Glasc — chem-baroness of Zaun.
Iconic: BIG chemical tank/apparatus on back (glowing vial rack),
mechanical prosthetic arm, high-collared opulent dress, deep purple/gold/black.
The tank + prosthetic arm are THE features.
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve

OUT = (35, 25, 35)
DRESS = (75, 35, 90)         # deep purple
DRESS_DARK = (50, 20, 65)
GOLD = (215, 175, 60)
GOLD_DARK = (150, 110, 30)
SKIN = (215, 185, 165)       # pale chem-altered skin
HAIR = (220, 215, 225)       # white-silver hair
TANK = (50, 60, 75)          # dark metal tank
TANK_DARK = (30, 38, 50)
GLASS = (140, 220, 200)      # glowing chem green
GLASS_GLOW = (110, 255, 200)
VIAL_PURPLE = (190, 110, 220)
VIAL_GREEN = (110, 240, 170)
METAL = (140, 130, 135)      # prosthetic arm metal
METAL_DARK = (90, 80, 85)
EYE = (200, 80, 60)          # sharp red-pink eyes


def renata_prims():
    P = []
    # --- BIG chemical tank/apparatus on back (THE feature — vial rack) ---
    # main tank body (tall, behind shoulders, dominates upper silhouette)
    P.append({"type":"rect","x":96,"y":50,"w":64,"h":58,"color":TANK,"outline":OUT,"outline_w":2,"radius":6})
    # tank top cap (brass)
    P.append({"type":"rect","x":104,"y":44,"w":48,"h":10,"color":GOLD,"outline":OUT,"outline_w":1,"radius":3})
    # pressure gauge
    P.append({"type":"circle","cx":112,"cy":58,"r":5,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":112,"cy":58,"r":2,"color":EYE})
    P.append({"type":"circle","cx":144,"cy":58,"r":5,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":144,"cy":58,"r":2,"color":EYE})
    # 3 GLOWING vials in the rack (chem-tech — THE chem feature)
    for vx, vcol in [(108, VIAL_GREEN), (128, VIAL_PURPLE), (148, VIAL_GREEN)]:
        P.append({"type":"rect","x":vx-7,"y":68,"w":14,"h":30,"color":GLASS,"outline":OUT,"outline_w":1,"radius":2})
        P.append({"type":"rect","x":vx-5,"y":72,"w":10,"h":22,"color":vcol,"outline":None})
        P.append({"type":"circle","cx":vx,"cy":72,"r":6,"color":GLASS_GLOW})
    # tubes from tank down to arm (2 pipes)
    P.append({"type":"line","start":[100,96],"end":[86,120],"color":METAL_DARK,"width":4})
    P.append({"type":"line","start":[156,96],"end":[170,120],"color":METAL_DARK,"width":4})
    # tank straps (gold)
    P.append({"type":"line","start":[104,52],"end":[104,106],"color":GOLD,"width":2})
    P.append({"type":"line","start":[152,52],"end":[152,106],"color":GOLD,"width":2})

    # --- Hair back (silver-white, sleek) ---
    P.append({"type":"circle","cx":128,"cy":74,"r":18,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(112,70),(144,70),(140,90),(116,90)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (sharp features, chem-baroness) ---
    P.append({"type":"circle","cx":128,"cy":80,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # sharp eyes
    P.append({"type":"line","start":[118,78],"end":[124,78],"color":EYE,"width":2})
    P.append({"type":"line","start":[132,78],"end":[138,78],"color":EYE,"width":2})
    # thin smirk
    P.append({"type":"line","start":[122,88],"end":[134,88],"color":(120,40,50),"width":1})

    # --- High collar (opulent, THE dress feature) ---
    # tall collar framing head
    P.append({"type":"polygon","points":[(108,86),(118,80),(118,104),(108,112)],
              "color":DRESS,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(148,86),(138,80),(138,104),(148,112)],
              "color":DRESS,"outline":OUT,"outline_w":1})
    # gold collar trim
    P.append({"type":"line","start":[108,86],"end":[118,80],"color":GOLD,"width":2})
    P.append({"type":"line","start":[148,86],"end":[138,80],"color":GOLD,"width":2})

    # --- Opulent dress (deep purple, flared, high-waisted) ---
    P.append({"type":"polygon","points":[(108,104),(148,104),(168,210),(88,210)],
              "color":DRESS,"outline":OUT,"outline_w":1})
    # gold trim down center
    P.append({"type":"line","start":[128,104],"end":[128,210],"color":GOLD,"width":2})
    # gold brooch at chest
    P.append({"type":"circle","cx":128,"cy":116,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":116,"r":2,"color":VIAL_PURPLE})
    # dress side panels (darker purple, opulent)
    P.append({"type":"polygon","points":[(108,104),(128,104),(120,210),(88,210)],
              "color":DRESS_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(128,104),(148,104),(168,210),(136,210)],
              "color":DRESS_DARK,"outline":OUT,"outline_w":1})

    # --- Left arm: normal (in dress sleeve) ---
    P.append({"type":"rect","x":96,"y":112,"w":12,"h":42,"color":DRESS,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":102,"cy":156,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Right arm: MECHANICAL PROSTHETIC (THE feature — metal, gold joints) ---
    # upper arm
    P.append({"type":"rect","x":148,"y":112,"w":14,"h":20,"color":METAL,"outline":OUT,"outline_w":1,"radius":3})
    # gold elbow joint
    P.append({"type":"circle","cx":155,"cy":132,"r":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # forearm (mechanical, bigger)
    P.append({"type":"rect","x":150,"y":134,"w":16,"h":22,"color":METAL,"outline":OUT,"outline_w":1,"radius":3})
    # mechanical detail lines
    P.append({"type":"line","start":[152,138],"end":[164,138],"color":METAL_DARK,"width":1})
    P.append({"type":"line","start":[152,146],"end":[164,146],"color":METAL_DARK,"width":1})
    # gold wrist joint
    P.append({"type":"circle","cx":158,"cy":156,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # prosthetic hand (claw-like, mechanical fingers)
    P.append({"type":"rect","x":152,"y":158,"w":14,"h":10,"color":METAL,"outline":OUT,"outline_w":1,"radius":2})
    for fx in (154, 158, 162):
        P.append({"type":"line","start":[fx,167],"end":[fx,174],"color":METAL,"width":2})
        P.append({"type":"circle","cx":fx,"cy":175,"r":1,"color":GOLD})
    # glow at palm (chem-tech)
    P.append({"type":"circle","cx":159,"cy":163,"r":3,"color":GLASS_GLOW})

    # --- Chemical sprayer nozzle (weapon, held by prosthetic) ---
    P.append({"type":"rect","x":160,"y":160,"w":18,"h":8,"color":METAL_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"circle","cx":178,"cy":164,"r":4,"color":GLASS,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":178,"cy":164,"r":2,"color":GLASS_GLOW})

    # --- Legs (under dress, slight) ---
    P.append({"type":"rect","x":112,"y":200,"w":12,"h":14,"color":DRESS_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":132,"y":200,"w":12,"h":14,"color":DRESS_DARK,"outline":OUT,"outline_w":1,"radius":2})
    # gold-heeled shoes
    P.append({"type":"rect","x":110,"y":212,"w":16,"h":6,"color":GOLD,"outline":OUT,"outline_w":1,"radius":1})
    P.append({"type":"rect","x":130,"y":212,"w":16,"h":6,"color":GOLD,"outline":OUT,"outline_w":1,"radius":1})

    return P


if __name__ == "__main__":
    prims = renata_prims()
    prims = [p for p in prims if "cx" not in p or isinstance(p.get("cx"), int)]
    r = improve("Renata", prims, gate_n=3)
    print("RESULT:", r)
