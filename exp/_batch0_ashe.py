"""Ashe — the Frost Archer.
Iconic: BIG crystalline ice bow, pale blue skin, long platinum blonde hair,
fur-lined Freljord cape/armor, white/light blue/silver.
The BIG bow + pale blue skin + fur cape are THE features.
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve

OUT = (40, 45, 60)
SKIN = (175, 205, 225)        # PALE BLUE skin (Freljord iceborn — more blue)
SKIN_DARK = (140, 175, 200)
HAIR = (240, 235, 220)        # platinum blonde (almost white)
HAIR_DARK = (200, 195, 180)
FUR = (245, 240, 230)         # white fur
FUR_DARK = (210, 200, 185)
ARMOR = (170, 195, 220)       # light blue armor
ARMOR_DARK = (120, 150, 185)
ICE = (160, 220, 240)         # ice blue
ICE_BRIGHT = (210, 240, 250)
BOW = (140, 200, 230)         # crystalline ice bow
BOW_DARK = (80, 140, 180)
BOW_GLOW = (180, 230, 250)
GOLD = (210, 175, 60)
EYE = (100, 150, 200)         # ice blue eyes
SNOW = (250, 250, 255)


def ashe_prims():
    P = []
    # --- Snow/ice aura (behind, soft Freljord glow) ---
    P.append({"type":"ellipse","x":40,"y":50,"w":176,"h":180,"color":(220,235,250),"outline":None})
    P.append({"type":"ellipse","x":60,"y":70,"w":136,"h":140,"color":(235,245,252),"outline":None})

    # --- Long platinum blonde hair (flowing down back, BIG) ---
    P.append({"type":"circle","cx":128,"cy":70,"r":22,"color":HAIR,"outline":OUT,"outline_w":1})
    # long flowing hair down back (wide, prominent)
    P.append({"type":"polygon","points":[(104,66),(152,66),(158,215),(98,215)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # hair strand highlights
    P.append({"type":"line","start":[114,78],"end":[112,210],"color":HAIR_DARK,"width":2})
    P.append({"type":"line","start":[128,78],"end":[128,212],"color":HAIR_DARK,"width":2})
    P.append({"type":"line","start":[142,78],"end":[144,210],"color":HAIR_DARK,"width":2})
    # hair side braids (Freljord style)
    P.append({"type":"polygon","points":[(104,66),(112,66),(108,140),(100,130)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(144,66),(152,66),(156,130),(148,140)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # hair braid ties (gold)
    P.append({"type":"circle","cx":108,"cy":138,"r":3,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":148,"cy":138,"r":3,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Head (PALE BLUE skin, beautiful — THE feature) ---
    P.append({"type":"circle","cx":128,"cy":80,"r":18,"color":SKIN,"outline":OUT,"outline_w":1})
    # extra blue tint layer on skin (more visibly blue)
    P.append({"type":"circle","cx":128,"cy":82,"r":15,"color":(185,210,228),"outline":None})
    # bangs (platinum, framing face)
    P.append({"type":"polygon","points":[(110,68),(146,68),(142,80),(114,80)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # ice-blue eyes (determined)
    P.append({"type":"circle","cx":121,"cy":80,"r":4,"color":(255,255,255),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":80,"r":4,"color":(255,255,255),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":81,"r":2,"color":EYE})
    P.append({"type":"circle","cx":136,"cy":81,"r":2,"color":EYE})
    # determined expression (slight frown, focused archer)
    P.append({"type":"line","start":[122,90],"end":[134,90],"color":(120,130,150),"width":1})
    # Freljord face markings (war paint, blue)
    P.append({"type":"line","start":[120,84],"end":[118,96],"color":ICE,"width":1})
    P.append({"type":"line","start":[136,84],"end":[138,96],"color":ICE,"width":1})
    # gold headband (Freljord princess)
    P.append({"type":"rect","x":112,"y":66,"w":32,"h":4,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":64,"r":3,"color":ICE_BRIGHT,"outline":GOLD,"outline_w":1})

    # --- FUR-LINED FRELJORD CAPE (THE feature — big white fur collar, draped) ---
    # cape body (behind, flowing, narrower at waist = slender female)
    P.append({"type":"polygon","points":[(100,96),(156,96),(166,150),(150,210),(106,210),(90,150)],
              "color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    # BIG fur collar/shoulder piece (THE feature — thick white fur)
    P.append({"type":"polygon","points":[(98,96),(158,96),(162,108),(94,108)],
              "color":FUR,"outline":OUT,"outline_w":2})
    # fur texture (fluffy bumps along collar)
    for fx in (98, 108, 118, 128, 138, 148, 158):
        P.append({"type":"circle","cx":fx,"cy":100,"r":6,"color":FUR,"outline":FUR_DARK,"outline_w":1})
    for fx in (103, 113, 123, 133, 143, 153):
        P.append({"type":"circle","cx":fx,"cy":104,"r":5,"color":FUR,"outline":FUR_DARK,"outline_w":1})
    # fur trim down cape front
    P.append({"type":"line","start":[96,108],"end":[92,200],"color":FUR,"width":5})
    P.append({"type":"line","start":[160,108],"end":[164,200],"color":FUR,"width":5})
    # fur tufts along trim
    for fy in (120, 140, 160, 180):
        P.append({"type":"circle","cx":95,"cy":fy,"r":4,"color":FUR,"outline":FUR_DARK,"outline_w":1})
        P.append({"type":"circle","cx":161,"cy":fy,"r":4,"color":FUR,"outline":FUR_DARK,"outline_w":1})

    # --- Freljord armor body (light blue, under cape, slender waist) ---
    P.append({"type":"polygon","points":[(114,108),(142,108),(146,150),(134,160),(122,160),(110,150)],
              "color":ARMOR,"outline":OUT,"outline_w":1})
    # armor chest plate
    P.append({"type":"polygon","points":[(112,112),(144,112),(140,150),(116,150)],
              "color":ICE,"outline":OUT,"outline_w":1})
    # gold chest emblem (Freljord)
    P.append({"type":"circle","cx":128,"cy":128,"r":6,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(124,128),(132,128),(128,136)],
              "color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    # armor belt (slender waist)
    P.append({"type":"rect","x":110,"y":150,"w":36,"h":8,"color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":154,"r":4,"color":GOLD,"outline":OUT,"outline_w":1})
    # hip flares (skirt/armor, slender female)
    P.append({"type":"polygon","points":[(110,158),(134,158),(140,176),(104,176)],
              "color":ARMOR,"outline":OUT,"outline_w":1})

    # --- BIG CRYSTALLINE ICE BOW (THE feature — HUGE, held in left hand) ---
    # bow is drawn BIG on her left side, crystalline ice recurve
    # bow body (upper limb, curving up)
    P.append({"type":"polygon","points":[(60,90),(66,86),(72,150),(66,154)],
              "color":BOW,"outline":OUT,"outline_w":2})
    # bow body (lower limb, curving down)
    P.append({"type":"polygon","points":[(66,154),(72,150),(78,214),(72,218)],
              "color":BOW,"outline":OUT,"outline_w":2})
    # bow grip (center, where hand holds)
    P.append({"type":"rect","x":62,"y":148,"w":12,"h":14,"color":BOW_DARK,"outline":OUT,"outline_w":1})
    # bow glow (crystalline ice magic)
    P.append({"type":"circle","cx":66,"cy":154,"r":8,"color":BOW_GLOW,"outline":None})
    # bow string (taut, vertical)
    P.append({"type":"line","start":[66,90],"end":[72,218],"color":(245,250,255),"width":1})
    # ice crystals on bow limbs (THE crystalline feature)
    for cy in (100, 120, 170, 195):
        P.append({"type":"polygon","points":[(62,cy),(68,cy-4),(70,cy),(68,cy+4)],
                  "color":ICE_BRIGHT,"outline":BOW_DARK,"outline_w":1})
    # gold bow tips
    P.append({"type":"circle","cx":63,"cy":90,"r":3,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":75,"cy":216,"r":3,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Arrow (nocked, crystalline ice arrow) ---
    P.append({"type":"line","start":[66,154],"end":[40,154],"color":(245,250,255),"width":2})
    # arrowhead (ice crystal)
    P.append({"type":"polygon","points":[(40,154),(50,150),(50,158)],
              "color":ICE_BRIGHT,"outline":BOW_DARK,"outline_w":1})
    # arrow fletching (white)
    P.append({"type":"polygon","points":[(80,150),(86,148),(86,160),(80,158)],
              "color":FUR,"outline":OUT,"outline_w":1})

    # --- Arms (slender, pale blue skin visible) ---
    # left arm (holding bow, raised, slender)
    P.append({"type":"rect","x":100,"y":118,"w":10,"h":34,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":106,"cy":150,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    # right arm (drawing bowstring, back, slender)
    P.append({"type":"rect","x":146,"y":118,"w":10,"h":34,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":150,"cy":150,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    # fur wrist cuffs
    P.append({"type":"rect","x":100,"y":146,"w":12,"h":5,"color":FUR,"outline":FUR_DARK,"outline_w":1})
    P.append({"type":"rect","x":144,"y":146,"w":12,"h":5,"color":FUR,"outline":FUR_DARK,"outline_w":1})

    # --- Legs (slender, Freljord boots, fur-lined) ---
    P.append({"type":"rect","x":112,"y":170,"w":12,"h":30,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":12,"h":30,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":3})
    # fur-lined boots
    P.append({"type":"rect","x":108,"y":196,"w":18,"h":16,"color":ARMOR_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":196,"w":18,"h":16,"color":ARMOR_DARK,"outline":OUT,"outline_w":1,"radius":2})
    # fur boot tops
    P.append({"type":"rect","x":108,"y":196,"w":18,"h":5,"color":FUR,"outline":FUR_DARK,"outline_w":1})
    P.append({"type":"rect","x":128,"y":196,"w":18,"h":5,"color":FUR,"outline":FUR_DARK,"outline_w":1})
    # fur boot tufts
    for fx in (112, 118, 124):
        P.append({"type":"circle","cx":fx,"cy":198,"r":3,"color":FUR,"outline":FUR_DARK,"outline_w":1})
    for fx in (132, 138, 144):
        P.append({"type":"circle","cx":fx,"cy":198,"r":3,"color":FUR,"outline":FUR_DARK,"outline_w":1})

    # --- Snowflakes (Freljord ice magic aura) ---
    for sx, sy in [(40,60),(210,70),(30,140),(220,150),(50,200),(200,200)]:
        P.append({"type":"circle","cx":sx,"cy":sy,"r":4,"color":SNOW,"outline":ICE,"outline_w":1})
        P.append({"type":"line","start":[sx-5,sy],"end":[sx+5,sy],"color":ICE,"width":1})
        P.append({"type":"line","start":[sx,sy-5],"end":[sx,sy+5],"color":ICE,"width":1})

    return P


if __name__ == "__main__":
    prims = ashe_prims()
    prims = [p for p in prims if "cx" not in p or isinstance(p.get("cx"), int)]
    r = improve("Ashe", prims, gate_n=3)
    print("RESULT:", r)
