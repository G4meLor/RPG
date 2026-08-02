"""Akshan — the Rogue Sentinel.
Iconic: grappling-hook rifle (Avengerang), stylish rogue attire (white/gold),
confident smirk, Sentinel insignia, trimmed facial hair, lean athletic.
The grappling-hook rifle + rogue coat are THE features.
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve

OUT = (35, 30, 25)
SKIN = (220, 180, 145)        # tan Shuriman skin
HAIR = (45, 35, 30)           # dark brown hair
HAIR_DARK = (25, 20, 18)
COAT = (235, 230, 215)        # white rogue coat
COAT_DARK = (190, 180, 160)
GOLD = (220, 180, 65)         # Sentinel gold
GOLD_DARK = (160, 120, 35)
BROWN = (130, 85, 50)         # leather brown
BROWN_DARK = (85, 55, 30)
RIFLE = (90, 75, 60)          # rifle stock
RIFLE_DARK = (55, 45, 35)
METAL = (160, 160, 170)       # rifle metal
HOOK = (180, 175, 180)        # grappling hook
EYE = (40, 30, 25)
RED = (190, 40, 40)           # Sentinel red accent


def akshan_prims():
    P = []
    # --- Hair back (dark, tousled rogue) ---
    P.append({"type":"circle","cx":128,"cy":72,"r":19,"color":HAIR,"outline":OUT,"outline_w":1})
    # tousled hair top (spiky-messy rogue)
    P.append({"type":"polygon","points":[(110,64),(116,52),(122,60),(128,48),(134,60),(140,52),(146,64)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # side hair
    P.append({"type":"polygon","points":[(110,68),(118,68),(114,90),(108,82)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(138,68),(146,68),(148,82),(142,90)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (handsome rogue, smirk) ---
    P.append({"type":"circle","cx":128,"cy":78,"r":17,"color":SKIN,"outline":OUT,"outline_w":1})
    # confident eyes (sharp)
    P.append({"type":"circle","cx":121,"cy":78,"r":3,"color":(255,255,255),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":78,"r":3,"color":(255,255,255),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":79,"r":2,"color":EYE})
    P.append({"type":"circle","cx":136,"cy":79,"r":2,"color":EYE})
    # eyebrows (confident, raised)
    P.append({"type":"line","start":[115,72],"end":[125,74],"color":HAIR_DARK,"width":2})
    P.append({"type":"line","start":[131,74],"end":[141,72],"color":HAIR_DARK,"width":2})
    # SMIRK (THE feature — BIG one-sided confident smile, very visible)
    P.append({"type":"polygon","points":[(118,88),(138,84),(136,94),(122,93)],
              "color":(180,80,60),"outline":OUT,"outline_w":2})
    # smirk upturn (right side raised)
    P.append({"type":"line","start":[136,84],"end":[140,82],"color":(140,50,40),"width":2})
    # trimmed beard / stubble (facial hair)
    P.append({"type":"polygon","points":[(114,88),(142,88),(140,96),(116,96)],
              "color":HAIR_DARK,"outline":None})
    P.append({"type":"line","start":[118,92],"end":[138,92],"color":HAIR,"width":1})
    # jaw stubble
    P.append({"type":"line","start":[116,94],"end":[120,98],"color":HAIR_DARK,"width":1})
    P.append({"type":"line","start":[136,94],"end":[132,98],"color":HAIR_DARK,"width":1})

    # --- Stylish rogue coat (white, gold-trimmed, BIG flared — THE attire) ---
    # coat body (long, flared, dramatic rogue silhouette)
    P.append({"type":"polygon","points":[(100,96),(156,96),(176,212),(80,212)],
              "color":COAT,"outline":OUT,"outline_w":1})
    # coat tails (longer, dramatic)
    P.append({"type":"polygon","points":[(80,212),(176,212),(168,224),(88,224)],
              "color":COAT_DARK,"outline":OUT,"outline_w":1})
    # coat lapels (gold-trimmed, stylish, BIG)
    P.append({"type":"polygon","points":[(100,96),(128,96),(124,144),(106,122)],
              "color":COAT_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(128,96),(156,96),(150,122),(132,144)],
              "color":COAT_DARK,"outline":OUT,"outline_w":1})
    # gold trim on lapels (bolder)
    P.append({"type":"line","start":[106,96],"end":[124,142],"color":GOLD,"width":3})
    P.append({"type":"line","start":[150,96],"end":[132,142],"color":GOLD,"width":3})
    # gold epaulettes (shoulder detail, stylish rogue)
    P.append({"type":"polygon","points":[(100,96),(118,96),(114,104),(102,104)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(138,96),(156,96),(154,104),(142,104)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # shirt under coat (dark)
    P.append({"type":"polygon","points":[(120,96),(136,96),(134,140),(122,140)],
              "color":BROWN_DARK,"outline":OUT,"outline_w":1})
    # Sentinel insignia (BIG gold emblem on chest, THE feature — very visible)
    P.append({"type":"circle","cx":128,"cy":118,"r":12,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":118,"r":9,"color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # Sentinel symbol (sun/star burst in red)
    P.append({"type":"polygon","points":[(120,118),(136,118),(128,128)],
              "color":RED,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(128,110),(132,122),(128,128),(124,122)],
              "color":RED,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":116,"r":3,"color":(255,235,180),"outline":GOLD_DARK,"outline_w":1})
    # gold halo rays around insignia
    for ang in [(116,110),(140,110),(116,126),(140,126)]:
        P.append({"type":"line","start":[128,118],"end":ang,"color":GOLD,"width":1})
    # gold buttons down coat
    for by in (130, 150, 170, 190):
        P.append({"type":"circle","cx":128,"cy":by,"r":2,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold belt
    P.append({"type":"rect","x":100,"y":148,"w":56,"h":8,"color":BROWN,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":100,"y":148,"w":56,"h":3,"color":GOLD,"outline":None})
    P.append({"type":"circle","cx":128,"cy":152,"r":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- GRAPPLING-HOOK RIFLE (Avengerang — THE feature, BIG, held across body) ---
    # rifle stock (wooden, diagonal across body)
    P.append({"type":"polygon","points":[(150,108),(186,92),(192,98),(156,114)],
              "color":RIFLE,"outline":OUT,"outline_w":2})
    # rifle barrel (metal, extending forward)
    P.append({"type":"rect","x":178,"y":88,"w":40,"h":10,"color":METAL,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":178,"y":88,"w":40,"h":3,"color":RIFLE_DARK,"outline":None})
    # rifle scope (on top)
    P.append({"type":"rect","x":186,"y":82,"w":14,"h":8,"color":RIFLE_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"circle","cx":193,"cy":86,"r":3,"color":GOLD,"outline":OUT,"outline_w":1})
    # gold trim on rifle
    P.append({"type":"line","start":[156,108],"end":[186,92],"color":GOLD,"width":2})
    # GRAPPLING HOOK (the distinctive end — THE feature)
    # hook mechanism at barrel tip
    P.append({"type":"circle","cx":218,"cy":93,"r":7,"color":METAL,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":218,"cy":93,"r":4,"color":RIFLE_DARK,"outline":OUT,"outline_w":1})
    # grappling hook prongs (3 curved claws)
    P.append({"type":"polygon","points":[(218,86),(224,80),(228,84),(222,90)],
              "color":HOOK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(218,86),(212,80),(208,84),(214,90)],
              "color":HOOK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(224,96),(230,100),(228,106),(222,102)],
              "color":HOOK,"outline":OUT,"outline_w":1})
    # gold accent on hook
    P.append({"type":"circle","cx":218,"cy":93,"r":2,"color":GOLD})
    # rope/cord from hook (grappling line)
    P.append({"type":"line","start":[218,93],"end":[228,70],"color":BROWN_DARK,"width":2})

    # --- Arms (lean, athletic — one holding rifle) ---
    # left arm (down, coat sleeve, slim = lean athletic)
    P.append({"type":"rect","x":92,"y":106,"w":12,"h":52,"color":COAT,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"circle","cx":98,"cy":160,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    # leather glove (left, THE rogue feature)
    P.append({"type":"circle","cx":98,"cy":160,"r":5,"color":BROWN,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":92,"y":150,"w":12,"h":8,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})
    # gold cuff on left sleeve
    P.append({"type":"rect","x":92,"y":152,"w":12,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # right arm (raised, holding rifle, slim)
    P.append({"type":"rect","x":148,"y":106,"w":12,"h":28,"color":COAT,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"rect","x":152,"y":128,"w":10,"h":16,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    # leather glove (right)
    P.append({"type":"circle","cx":158,"cy":142,"r":5,"color":BROWN,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":152,"y":136,"w":10,"h":8,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})
    # gold cuff on right sleeve
    P.append({"type":"rect","x":148,"y":122,"w":12,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Legs + leather boots (lean, tall, rogue) ---
    # slim legs (lean athletic)
    P.append({"type":"rect","x":110,"y":198,"w":14,"h":16,"color":BROWN_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":132,"y":198,"w":14,"h":16,"color":BROWN_DARK,"outline":OUT,"outline_w":1,"radius":2})
    # tall leather boots (brown, rogue, BIG)
    P.append({"type":"rect","x":106,"y":206,"w":22,"h":14,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":206,"w":22,"h":14,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})
    # boot cuff (gold-trimmed, stylish)
    P.append({"type":"rect","x":106,"y":206,"w":22,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":128,"y":206,"w":22,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold boot buckle
    P.append({"type":"circle","cx":117,"cy":216,"r":2,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":139,"cy":216,"r":2,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    return P


if __name__ == "__main__":
    prims = akshan_prims()
    prims = [p for p in prims if "cx" not in p or isinstance(p.get("cx"), int)]
    r = improve("Akshan", prims, gate_n=3)
    print("RESULT:", r)
