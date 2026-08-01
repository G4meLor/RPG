"""Aurora — the Spirit-fox Witch.
Iconic: SPIRIT-FOX COMPANION (a glowing fox beside/below her), flowing ethereal
clothing, glowing magical accents, Freljordian winter attire, mystical aura.
The spirit-fox companion + ethereal glow are THE features.
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve

OUT = (35, 30, 40)
SKIN = (225, 200, 215)        # warm pinkish skin (vastayan)
HAIR = (180, 220, 235)        # teal-cyan hair (ethereal)
HAIR_DARK = (130, 175, 200)
TEAL = (110, 200, 210)        # teal primary
TEAL_DARK = (70, 150, 170)
PURPLE = (170, 130, 210)      # purple accent
PURPLE_DARK = (120, 85, 160)
GOWN = (220, 230, 240)        # white ethereal gown
GOWN_DARK = (180, 200, 220)
GLOW = (180, 230, 250)        # spirit glow (cyan-white)
GLOW_BRIGHT = (220, 245, 255)
FOX = (240, 230, 220)         # spirit fox (pale, ghostly)
FOX_DARK = (190, 175, 165)
FOX_GLOW = (180, 230, 250)
EYE = (140, 90, 180)          # purple mystical eyes
SNOW = (250, 250, 255)


def aurora_prims():
    P = []
    # --- Mystical spirit aura (BIG, behind everything) ---
    P.append({"type":"ellipse","x":20,"y":30,"w":216,"h":200,"color":GLOW,"outline":None})
    P.append({"type":"ellipse","x":40,"y":50,"w":176,"h":160,"color":(200,230,250),"outline":None})
    P.append({"type":"ellipse","x":70,"y":80,"w":116,"h":120,"color":(225,245,255),"outline":None})
    # aura ring (visible ethereal outline)
    P.append({"type":"ellipse","x":24,"y":34,"w":208,"h":192,"color":(220,240,255),"outline":GLOW,"outline_w":2})

    # --- SPIRIT FOX COMPANION (THE feature — glowing fox beside/below her) ---
    # fox is drawn BIG, floating beside her at lower-left, glowing
    # fox body (curled, ghostly)
    P.append({"type":"ellipse","x":28,"y":150,"w":56,"h":40,"color":FOX,"outline":FOX_DARK,"outline_w":2})
    # fox glow halo
    P.append({"type":"ellipse","x":24,"y":146,"w":64,"h":48,"color":FOX_GLOW,"outline":None})
    P.append({"type":"ellipse","x":28,"y":150,"w":56,"h":40,"color":FOX,"outline":FOX_DARK,"outline_w":2})
    # fox head (pointed, spirit-fox)
    P.append({"type":"circle","cx":80,"cy":158,"r":16,"color":FOX,"outline":FOX_DARK,"outline_w":2})
    # fox ears (pointy, THE fox feature)
    P.append({"type":"polygon","points":[(70,148),(74,132),(80,146)],"color":FOX,"outline":FOX_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(82,146),(88,132),(92,148)],"color":FOX,"outline":FOX_DARK,"outline_w":1})
    # inner ears (pink)
    P.append({"type":"polygon","points":[(72,146),(76,138),(78,146)],"color":PURPLE})
    P.append({"type":"polygon","points":[(84,146),(88,138),(90,148)],"color":PURPLE})
    # fox eyes (glowing mystical)
    P.append({"type":"circle","cx":76,"cy":158,"r":3,"color":GLOW_BRIGHT,"outline":FOX_DARK,"outline_w":1})
    P.append({"type":"circle","cx":86,"cy":158,"r":3,"color":GLOW_BRIGHT,"outline":FOX_DARK,"outline_w":1})
    P.append({"type":"circle","cx":77,"cy":158,"r":1,"color":(255,255,255)})
    P.append({"type":"circle","cx":87,"cy":158,"r":1,"color":(255,255,255)})
    # fox nose
    P.append({"type":"circle","cx":91,"cy":162,"r":2,"color":(80,50,90),"outline":FOX_DARK,"outline_w":1})
    # fox snout (tapered)
    P.append({"type":"polygon","points":[(86,164),(96,160),(96,168),(88,170)],
              "color":FOX,"outline":FOX_DARK,"outline_w":1})
    # fox tail (BIG, fluffy, spirit-fox — sweeping up)
    P.append({"type":"polygon","points":[(30,160),(10,130),(18,120),(38,150)],
              "color":FOX,"outline":FOX_DARK,"outline_w":2})
    # tail tip (white/glowing)
    P.append({"type":"circle","cx":14,"cy":126,"r":6,"color":GLOW_BRIGHT,"outline":FOX_DARK,"outline_w":1})
    # fox legs (front, delicate)
    P.append({"type":"line","start":[42,182],"end":[40,196],"color":FOX_DARK,"width":4})
    P.append({"type":"line","start":[54,184],"end":[52,196],"color":FOX_DARK,"width":4})
    P.append({"type":"line","start":[64,184],"end":[62,196],"color":FOX_DARK,"width":4})
    # fox spirit glow particles
    for fx, fy in [(20,140),(50,130),(90,140),(15,170),(70,180)]:
        P.append({"type":"circle","cx":fx,"cy":fy,"r":3,"color":GLOW,"outline":None})

    # --- Hair (teal-cyan, flowing, ethereal) ---
    P.append({"type":"circle","cx":128,"cy":72,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    # long flowing hair down back
    P.append({"type":"polygon","points":[(108,68),(148,68),(154,200),(102,200)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # hair highlights
    P.append({"type":"line","start":[116,78],"end":[114,195],"color":HAIR_DARK,"width":2})
    P.append({"type":"line","start":[128,78],"end":[128,198],"color":HAIR_DARK,"width":2})
    P.append({"type":"line","start":[140,78],"end":[142,195],"color":HAIR_DARK,"width":2})
    # hair side locks (framing face)
    P.append({"type":"polygon","points":[(108,68),(116,68),(112,130),(104,120)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(140,68),(148,68),(152,120),(144,130)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (vastayan, mystical) ---
    P.append({"type":"circle","cx":128,"cy":80,"r":17,"color":SKIN,"outline":OUT,"outline_w":1})
    # bangs (teal)
    P.append({"type":"polygon","points":[(112,68),(144,68),(140,80),(116,80)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # mystical purple eyes (glowing)
    P.append({"type":"circle","cx":121,"cy":80,"r":4,"color":(255,255,255),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":80,"r":4,"color":(255,255,255),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":81,"r":2,"color":EYE})
    P.append({"type":"circle","cx":136,"cy":81,"r":2,"color":EYE})
    P.append({"type":"circle","cx":123,"cy":80,"r":1,"color":GLOW_BRIGHT})
    P.append({"type":"circle","cx":137,"cy":80,"r":1,"color":GLOW_BRIGHT})
    # gentle smile
    P.append({"type":"line","start":[122,90],"end":[134,90],"color":(140,90,120),"width":1})
    # vastayan deer-like antler/horn accents (small, mystical)
    P.append({"type":"line","start":[110,62],"end":[106,52],"color":HAIR_DARK,"width":2})
    P.append({"type":"line","start":[106,52],"end":[110,46],"color":HAIR_DARK,"width":2})
    P.append({"type":"line","start":[146,62],"end":[150,52],"color":HAIR_DARK,"width":2})
    P.append({"type":"line","start":[150,52],"end":[146,46],"color":HAIR_DARK,"width":2})
    # glowing gems on antler tips
    P.append({"type":"circle","cx":110,"cy":46,"r":2,"color":GLOW_BRIGHT,"outline":TEAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":146,"cy":46,"r":2,"color":GLOW_BRIGHT,"outline":TEAL_DARK,"outline_w":1})

    # --- Flowing ethereal gown (white, teal-trimmed, Freljordian) ---
    P.append({"type":"polygon","points":[(108,98),(148,98),(162,210),(94,210)],
              "color":GOWN,"outline":OUT,"outline_w":1})
    # gown center panel (lighter, ethereal)
    P.append({"type":"polygon","points":[(118,98),(138,98),(142,210),(114,210)],
              "color":(240,248,252),"outline":OUT,"outline_w":1})
    # teal trim down gown (ethereal accent)
    P.append({"type":"line","start":[128,98],"end":[128,210],"color":TEAL,"width":2})
    # teal collar/neckline
    P.append({"type":"polygon","points":[(116,98),(140,98),(136,110),(120,110)],
              "color":TEAL,"outline":OUT,"outline_w":1})
    # purple gem at chest (magical)
    P.append({"type":"circle","cx":128,"cy":116,"r":6,"color":PURPLE,"outline":PURPLE_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":115,"r":2,"color":GLOW_BRIGHT})
    # teal sash at waist
    P.append({"type":"rect","x":104,"y":150,"w":48,"h":8,"color":TEAL,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":154,"r":4,"color":PURPLE,"outline":PURPLE_DARK,"outline_w":1})
    # gown flow layers (ethereal, flowing)
    P.append({"type":"polygon","points":[(94,210),(100,180),(128,190),(156,180),(162,210)],
              "color":GOWN_DARK,"outline":OUT,"outline_w":1})

    # --- Arms (slender, ethereal) ---
    P.append({"type":"rect","x":100,"y":108,"w":10,"h":44,"color":GOWN,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":105,"cy":154,"r":4,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":146,"y":108,"w":10,"h":44,"color":GOWN,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":151,"cy":154,"r":4,"color":SKIN,"outline":OUT,"outline_w":1})
    # glowing magic at hands (ethereal)
    P.append({"type":"circle","cx":105,"cy":156,"r":4,"color":GLOW,"outline":None})
    P.append({"type":"circle","cx":151,"cy":156,"r":4,"color":GLOW,"outline":None})

    # --- Legs (under gown) ---
    P.append({"type":"rect","x":114,"y":200,"w":10,"h":14,"color":SKIN,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":132,"y":200,"w":10,"h":14,"color":SKIN,"outline":OUT,"outline_w":1,"radius":2})
    # teal shoes
    P.append({"type":"rect","x":112,"y":212,"w":14,"h":6,"color":TEAL,"outline":OUT,"outline_w":1,"radius":1})
    P.append({"type":"rect","x":130,"y":212,"w":14,"h":6,"color":TEAL,"outline":OUT,"outline_w":1,"radius":1})

    # --- Floating magic spirits/sparks (ethereal aura, BIG glowing accents) ---
    for sx, sy, sr in [(200,60,7),(214,110,6),(208,160,7),(170,38,6),(90,38,6),(30,90,7)]:
        P.append({"type":"circle","cx":sx,"cy":sy,"r":sr,"color":GLOW,"outline":TEAL_DARK,"outline_w":1})
        P.append({"type":"circle","cx":sx,"cy":sy,"r":sr-3,"color":GLOW_BRIGHT})
        P.append({"type":"circle","cx":sx,"cy":sy,"r":1,"color":(255,255,255)})
    # magic swirls (ethereal, BIGGER)
    P.append({"type":"circle","cx":40,"cy":100,"r":8,"color":GLOW,"outline":TEAL_DARK,"outline_w":2})
    P.append({"type":"circle","cx":214,"cy":90,"r":8,"color":GLOW,"outline":PURPLE_DARK,"outline_w":2})
    # glowing magic streamers from hands (ethereal)
    P.append({"type":"line","start":[105,156],"end":[90,180],"color":GLOW,"width":3})
    P.append({"type":"line","start":[151,156],"end":[166,180],"color":GLOW,"width":3})
    P.append({"type":"line","start":[105,156],"end":[90,180],"color":GLOW_BRIGHT,"width":1})
    P.append({"type":"line","start":[151,156],"end":[166,180],"color":GLOW_BRIGHT,"width":1})
    # purple magical gem glow on chest (bigger)
    P.append({"type":"circle","cx":128,"cy":116,"r":8,"color":GLOW,"outline":None})
    P.append({"type":"circle","cx":128,"cy":116,"r":5,"color":PURPLE,"outline":PURPLE_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":115,"r":2,"color":GLOW_BRIGHT})

    return P


if __name__ == "__main__":
    prims = aurora_prims()
    prims = [p for p in prims if "cx" not in p or isinstance(p.get("cx"), int)]
    r = improve("Aurora", prims, gate_n=3)
    print("RESULT:", r)
