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

    # --- Head (youthful face — BIG head relative to body = young teen) ---
    P.append({"type":"circle","cx":128,"cy":84,"r":20,"color":SKIN,"outline":OUT,"outline_w":1})
    # bangs (spiky, over forehead)
    P.append({"type":"polygon","points":[(110,72),(146,72),(142,84),(114,84)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # BIG youthful electric-blue eyes (very big = youthful teen)
    P.append({"type":"circle","cx":120,"cy":84,"r":6,"color":(255,255,255),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":136,"cy":84,"r":6,"color":(255,255,255),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":121,"cy":85,"r":4,"color":EYE})
    P.append({"type":"circle","cx":137,"cy":85,"r":4,"color":EYE})
    P.append({"type":"circle","cx":122,"cy":83,"r":2,"color":(255,255,255)})
    P.append({"type":"circle","cx":138,"cy":83,"r":2,"color":(255,255,255)})
    # small button nose (youthful)
    P.append({"type":"circle","cx":128,"cy":92,"r":2,"color":(190,150,130)})
    # big youthful grin (expressive, teen)
    P.append({"type":"polygon","points":[(120,96),(136,96),(132,102),(124,102)],
              "color":(220,130,110),"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[124,98],"end":[132,98],"color":(255,255,255),"width":1})
    # round rosy cheeks (youthful)
    P.append({"type":"circle","cx":112,"cy":94,"r":4,"color":(240,170,150)})
    P.append({"type":"circle","cx":144,"cy":94,"r":4,"color":(240,170,150)})
    # eyebrows (raised, youthful expressive)
    P.append({"type":"line","start":[114,76],"end":[124,74],"color":HAIR_DARK,"width":2})
    P.append({"type":"line","start":[132,74],"end":[142,76],"color":HAIR_DARK,"width":2})

    # --- Zaunite streetwear hoodie (blue, hood DOWN, visible jacket) ---
    # hood DOWN (behind neck, visible as collar fold)
    P.append({"type":"polygon","points":[(108,88),(148,88),(152,108),(104,108)],
              "color":JACKET_DARK,"outline":OUT,"outline_w":1})
    # jacket body (hoodie, slim athletic)
    P.append({"type":"polygon","points":[(106,100),(150,100),(156,176),(100,176)],
              "color":JACKET,"outline":OUT,"outline_w":1})
    # jacket collar (teal, visible V-neck)
    P.append({"type":"polygon","points":[(116,100),(140,100),(134,116),(122,116)],
              "color":TEAL,"outline":OUT,"outline_w":1})
    # t-shirt under jacket (white, streetwear layering)
    P.append({"type":"polygon","points":[(120,100),(136,100),(134,130),(122,130)],
              "color":(235,235,240),"outline":OUT,"outline_w":1})
    # jacket center zipper (electric)
    P.append({"type":"line","start":[128,116],"end":[128,176],"color":GLOVE_BLUE,"width":2})
    P.append({"type":"line","start":[128,116],"end":[128,176],"color":(200,200,210),"width":1})
    # jacket side panels (darker)
    P.append({"type":"polygon","points":[(106,100),(128,100),(122,176),(100,176)],
              "color":JACKET_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(128,100),(150,100),(156,176),(134,176)],
              "color":JACKET_DARK,"outline":OUT,"outline_w":1})
    # jacket hem trim (teal, streetwear)
    P.append({"type":"rect","x":100,"y":172,"w":56,"h":6,"color":TEAL,"outline":OUT,"outline_w":1})
    # jacket kangaroo pocket (streetwear)
    P.append({"type":"rect","x":108,"y":142,"w":40,"h":16,"color":JACKET_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # teal chest logo (streetwear brand mark, lightning bolt)
    P.append({"type":"polygon","points":[(122,124),(134,124),(128,136)],
              "color":TEAL,"outline":OUT,"outline_w":1})

    # --- HUGE OVERSIZED MECHANICAL GAUNTLETS (THE feature — MASSIVE, bigger than head) ---
    # LEFT gauntlet (HUGE, mechanical, glowing blue — bigger than torso)
    P.append({"type":"rect","x":70,"y":112,"w":38,"h":50,"color":GLOVE,"outline":OUT,"outline_w":2,"radius":8})
    # gauntlet blue energy core (BIG glowing)
    P.append({"type":"circle","cx":89,"cy":138,"r":12,"color":GLOVE_BLUE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":89,"cy":138,"r":7,"color":ELEC_BRIGHT})
    P.append({"type":"circle","cx":89,"cy":138,"r":3,"color":(255,255,255)})
    # gauntlet knuckle plates (BIG)
    for kx in (74, 84, 94):
        P.append({"type":"rect","x":kx,"y":160,"w":10,"h":10,"color":GLOVE_DARK,"outline":OUT,"outline_w":1,"radius":2})
    # gauntlet tech details (lines)
    P.append({"type":"line","start":[72,120],"end":[106,120],"color":GLOVE_DARK,"width":1})
    P.append({"type":"line","start":[72,148],"end":[106,148],"color":GLOVE_DARK,"width":1})
    # teal accent bands on gauntlet
    P.append({"type":"rect","x":70,"y":128,"w":38,"h":5,"color":TEAL,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":70,"y":154,"w":38,"h":3,"color":TEAL,"outline":OUT,"outline_w":1})
    # gauntlet bolts (tech detail)
    for bx in (74, 104):
        P.append({"type":"circle","cx":bx,"cy":116,"r":2,"color":GLOVE_DARK,"outline":OUT,"outline_w":1})
        P.append({"type":"circle","cx":bx,"cy":156,"r":2,"color":GLOVE_DARK,"outline":OUT,"outline_w":1})

    # RIGHT gauntlet (HUGE, raised, aiming — MASSIVE)
    P.append({"type":"rect","x":148,"y":104,"w":38,"h":50,"color":GLOVE,"outline":OUT,"outline_w":2,"radius":8})
    P.append({"type":"circle","cx":167,"cy":130,"r":12,"color":GLOVE_BLUE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":167,"cy":130,"r":7,"color":ELEC_BRIGHT})
    P.append({"type":"circle","cx":167,"cy":130,"r":3,"color":(255,255,255)})
    for kx in (152, 162, 172):
        P.append({"type":"rect","x":kx,"y":152,"w":10,"h":10,"color":GLOVE_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"line","start":[150,112],"end":[184,112],"color":GLOVE_DARK,"width":1})
    P.append({"type":"line","start":[150,140],"end":[184,140],"color":GLOVE_DARK,"width":1})
    P.append({"type":"rect","x":148,"y":120,"w":38,"h":5,"color":TEAL,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":148,"y":146,"w":38,"h":3,"color":TEAL,"outline":OUT,"outline_w":1})
    for bx in (152, 182):
        P.append({"type":"circle","cx":bx,"cy":108,"r":2,"color":GLOVE_DARK,"outline":OUT,"outline_w":1})
        P.append({"type":"circle","cx":bx,"cy":148,"r":2,"color":GLOVE_DARK,"outline":OUT,"outline_w":1})

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
