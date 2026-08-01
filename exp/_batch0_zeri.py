"""Zeri — the Spark of Zaun.
Iconic: spiky electric hair, HUGE oversized mechanical gauntlets crackling
with lightning, electric blue/cyan, Zaunite streetwear, youthful.
The gauntlets + spiky hair are THE features.
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve

OUT = (25, 25, 30)
SKIN = (215, 185, 165)        # warm brown skin (Zaunite)
HAIR = (245, 220, 90)         # electric yellow-green hair (spiky)
HAIR_DARK = (190, 165, 50)
JACKET = (40, 70, 130)        # blue Zaunite jacket
JACKET_DARK = (25, 50, 95)
TEAL = (90, 200, 220)         # electric teal accent
GLOVE = (180, 180, 195)       # gauntlet metal (light)
GLOVE_DARK = (110, 110, 130)
GLOVE_BLUE = (90, 180, 230)   # electric blue gauntlet glow
ELEC = (140, 220, 255)        # lightning cyan
ELEC_BRIGHT = (220, 245, 255)
EYE = (90, 200, 220)          # electric blue eyes


def zeri_prims():
    P = []
    # --- Electric aura glow (behind) ---
    P.append({"type":"ellipse","x":50,"y":60,"w":156,"h":160,"color":(60,120,160),"outline":None})
    P.append({"type":"ellipse","x":70,"y":80,"w":116,"h":120,"color":(90,160,200),"outline":None})

    # --- SPIKY ELECTRIC HAIR (THE feature — big upward spikes) ---
    # hair base
    P.append({"type":"circle","cx":128,"cy":72,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    # BIG spiky hair points (5-6 upward spikes, electric)
    spikes = [(104,68),(112,40),(122,30),(128,24),(134,30),(144,40),(152,68)]
    for i in range(len(spikes)-1):
        P.append({"type":"polygon","points":[spikes[i],(spikes[i][0]+6,72),(spikes[i+1])],
                  "color":HAIR,"outline":OUT,"outline_w":1})
    # extra spike tips (sharper)
    P.append({"type":"polygon","points":[(108,66),(116,32),(120,66)],"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(120,64),(128,22),(136,64)],"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(136,66),(140,32),(148,66)],"color":HAIR,"outline":Out if False else OUT,"outline_w":1})
    # electric sparks at hair tips (cyan glow)
    for sx, sy in [(116,32),(128,22),(140,32)]:
        P.append({"type":"circle","cx":sx,"cy":sy,"r":4,"color":ELEC,"outline":OUT,"outline_w":1})
        P.append({"type":"circle","cx":sx,"cy":sy,"r":2,"color":ELEC_BRIGHT})
    # hair side locks
    P.append({"type":"polygon","points":[(110,68),(118,68),(114,100),(108,90)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(138,68),(146,68),(148,90),(142,100)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (youthful face) ---
    P.append({"type":"circle","cx":128,"cy":82,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # bangs
    P.append({"type":"polygon","points":[(112,70),(144,70),(140,80),(116,80)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # big youthful electric-blue eyes
    P.append({"type":"circle","cx":121,"cy":82,"r":4,"color":(255,255,255),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":82,"r":4,"color":(255,255,255),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":121,"cy":83,"r":2,"color":EYE})
    P.append({"type":"circle","cx":135,"cy":83,"r":2,"color":EYE})
    # confident youthful smile
    P.append({"type":"line","start":[122,90],"end":[134,90],"color":(140,70,60),"width":1})

    # --- Zaunite streetwear jacket (blue, cropped) ---
    P.append({"type":"polygon","points":[(108,100),(148,100),(152,170),(104,170)],
              "color":JACKET,"outline":OUT,"outline_w":1})
    # jacket collar (teal)
    P.append({"type":"polygon","points":[(114,100),(142,100),(138,114),(118,114)],
              "color":TEAL,"outline":OUT,"outline_w":1})
    # jacket center stripe (electric)
    P.append({"type":"line","start":[128,114],"end":[128,170],"color":GLOVE_BLUE,"width":3})
    # jacket side panels (darker)
    P.append({"type":"polygon","points":[(108,100),(128,100),(120,170),(104,170)],
              "color":JACKET_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(128,100),(148,100),(152,170),(136,170)],
              "color":JACKET_DARK,"outline":OUT,"outline_w":1})
    # jacket hem trim (teal)
    P.append({"type":"rect","x":104,"y":166,"w":48,"h":6,"color":TEAL,"outline":OUT,"outline_w":1})

    # --- HUGE OVERSIZED MECHANICAL GAUNTLETS (THE feature — bigger than head) ---
    # LEFT gauntlet (big, mechanical, glowing blue)
    P.append({"type":"rect","x":78,"y":118,"w":30,"h":40,"color":GLOVE,"outline":OUT,"outline_w":2,"radius":6})
    # gauntlet blue energy core
    P.append({"type":"circle","cx":93,"cy":138,"r":8,"color":GLOVE_BLUE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":93,"cy":138,"r":4,"color":ELEC_BRIGHT})
    # gauntlet knuckle plates
    for kx in (82, 90, 98):
        P.append({"type":"rect","x":kx,"y":156,"w":8,"h":8,"color":GLOVE_DARK,"outline":OUT,"outline_w":1,"radius":2})
    # gauntlet tech details (lines)
    P.append({"type":"line","start":[80,124],"end":[106,124],"color":GLOVE_DARK,"width":1})
    P.append({"type":"line","start":[80,150],"end":[106,150],"color":GLOVE_DARK,"width":1})
    # gold/teal accent on gauntlet
    P.append({"type":"rect","x":78,"y":130,"w":30,"h":4,"color":TEAL,"outline":OUT,"outline_w":1})

    # RIGHT gauntlet (big, mechanical, glowing blue) — raised, aiming
    P.append({"type":"rect","x":148,"y":110,"w":30,"h":40,"color":GLOVE,"outline":OUT,"outline_w":2,"radius":6})
    P.append({"type":"circle","cx":163,"cy":130,"r":8,"color":GLOVE_BLUE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":163,"cy":130,"r":4,"color":ELEC_BRIGHT})
    for kx in (152, 160, 168):
        P.append({"type":"rect","x":kx,"y":148,"w":8,"h":8,"color":GLOVE_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"line","start":[150,116],"end":[176,116],"color":GLOVE_DARK,"width":1})
    P.append({"type":"line","start":[150,142],"end":[176,142],"color":GLOVE_DARK,"width":1})
    P.append({"type":"rect","x":148,"y":122,"w":30,"h":4,"color":TEAL,"outline":OUT,"outline_w":1})

    # --- LIGHTNING / electric sparks (THE electric feature) ---
    # lightning bolts from right gauntlet (firing)
    bolt = [(178,130),(186,120),(182,128),(192,118),(188,126),(198,116)]
    for i in range(len(bolt)-1):
        P.append({"type":"line","start":bolt[i],"end":bolt[i+1],"color":ELEC_BRIGHT,"width":3})
    for i in range(len(bolt)-1):
        P.append({"type":"line","start":bolt[i],"end":bolt[i+1],"color":ELEC,"width":1})
    # small sparks around both gauntlets
    for sx, sy in [(70,128),(74,150),(118,160),(140,160),(186,108),(180,156)]:
        P.append({"type":"line","start":[sx,sy],"end":[sx+4,sy-8],"color":ELEC,"width":2})
        P.append({"type":"circle","cx":sx+4,"cy":sy-8,"r":2,"color":ELEC_BRIGHT})
    # electric arcs between gauntlets (across chest)
    P.append({"type":"line","start":[108,140],"end":[148,132],"color":ELEC,"width":1})

    # --- Legs (Zaunite pants + boots) ---
    P.append({"type":"rect","x":110,"y":170,"w":16,"h":32,"color":(60,50,70),"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":170,"w":16,"h":32,"color":(60,50,70),"outline":OUT,"outline_w":1,"radius":3})
    # boots (blue/teal Zaunite tech)
    P.append({"type":"rect","x":108,"y":198,"w":20,"h":12,"color":JACKET,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":198,"w":20,"h":12,"color":JACKET,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":108,"y":198,"w":20,"h":4,"color":TEAL,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":128,"y":198,"w":20,"h":4,"color":TEAL,"outline":OUT,"outline_w":1})

    return P


if __name__ == "__main__":
    prims = zeri_prims()
    prims = [p for p in prims if "cx" not in p or isinstance(p.get("cx"), int)]
    r = improve("Zeri", prims, gate_n=3)
    print("RESULT:", r)
