"""Validate the improve() SAVE path on a fresh champ (Renekton, score 4).
Hand-authored from LoL knowledge: crocodile snout + Shuriman gold armor.
If this saves and scores >=7, the pipeline is ready to fan out to subagents.
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve

OUT = (30, 25, 20)
SCALE = (90, 130, 75)
SCALE_DARK = (55, 85, 45)
GOLD = (215, 175, 60)
GOLD_DARK = (150, 110, 30)
BELLY = (180, 165, 110)
EYE = (230, 60, 40)
TOOTH = (240, 235, 220)
CLAW = (235, 225, 200)


def renekton_prims():
    P = []
    # --- Tail (behind, curling) ---
    tail = [(140,165),(160,185),(150,205),(130,212),(118,200)]
    for i in range(len(tail)-1):
        P.append({"type":"line","start":tail[i],"end":tail[i+1],"color":SCALE,"width":14})
    for cx,cy in tail:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":7,"color":SCALE,"outline":SCALE_DARK,"outline_w":1})
    # tail ridge scales
    for cx,cy in tail[::2]:
        P.append({"type":"polygon","points":[(cx-4,cy),(cx,cy-5),(cx+4,cy)],"color":SCALE_DARK,"outline":OUT,"outline_w":1})

    # --- Legs (muscular, scaled) ---
    P.append({"type":"rect","x":108,"y":158,"w":18,"h":48,"color":SCALE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":130,"y":158,"w":18,"h":48,"color":SCALE,"outline":OUT,"outline_w":1,"radius":4})
    # gold shin armor
    P.append({"type":"rect","x":108,"y":180,"w":18,"h":18,"color":GOLD,"outline":GOLD_DARK,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":180,"w":18,"h":18,"color":GOLD,"outline":GOLD_DARK,"outline_w":1,"radius":3})
    # clawed feet
    for fx in (110,124,138):
        P.append({"type":"polygon","points":[(fx,206),(fx+6,206),(fx+3,214)],"color":CLAW,"outline":OUT,"outline_w":1})

    # --- Torso (broad, gold chest plate over scales) ---
    P.append({"type":"polygon","points":[(100,100),(156,100),(160,165),(96,165)],
              "color":SCALE,"outline":OUT,"outline_w":1})
    # belly (lighter)
    P.append({"type":"polygon","points":[(112,108),(144,108),(148,160),(108,160)],
              "color":BELLY,"outline":OUT,"outline_w":1})
    # gold chest plate (Shuriman)
    P.append({"type":"polygon","points":[(104,104),(152,104),(148,140),(108,140)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # chest gem
    P.append({"type":"circle","cx":128,"cy":120,"r":5,"color":(180,40,40),"outline":GOLD_DARK,"outline_w":1})
    # gold belt
    P.append({"type":"rect","x":100,"y":150,"w":56,"h":12,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":156,"r":4,"color":(180,40,40),"outline":GOLD_DARK,"outline_w":1})
    # belly scale texture
    for by in (118,132,146):
        P.append({"type":"line","start":[110,by],"end":[146,by],"color":SCALE_DARK,"width":1})

    # --- Arms (muscular, one raised with claw) ---
    P.append({"type":"rect","x":86,"y":108,"w":16,"h":44,"color":SCALE,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"rect","x":154,"y":108,"w":16,"h":44,"color":SCALE,"outline":OUT,"outline_w":1,"radius":5})
    # gold shoulder pads
    P.append({"type":"circle","cx":94,"cy":110,"r":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":162,"cy":110,"r":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # clawed hands
    P.append({"type":"circle","cx":94,"cy":154,"r":6,"color":SCALE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":162,"cy":154,"r":6,"color":SCALE,"outline":OUT,"outline_w":1})
    for hx in (90,94,98):
        P.append({"type":"line","start":[hx,158],"end":[hx,166],"color":CLAW,"width":1})

    # --- HEAD: CROCODILE (THE feature — long snout, teeth, scales, brow) ---
    # back of head / skull
    P.append({"type":"circle","cx":128,"cy":78,"r":24,"color":SCALE,"outline":OUT,"outline_w":1})
    # brow ridge (heavy bone over eyes)
    P.append({"type":"rect","x":106,"y":66,"w":44,"h":8,"color":SCALE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # LONG SNOUT extending forward/down (the crocodile jaw) — tapered
    P.append({"type":"polygon","points":[(108,84),(148,84),(140,118),(116,118)],
              "color":SCALE,"outline":OUT,"outline_w":1})
    # upper jaw tip
    P.append({"type":"polygon","points":[(116,118),(140,118),(128,128)],"color":SCALE_DARK,"outline":OUT,"outline_w":1})
    # nostrils
    P.append({"type":"circle","cx":124,"cy":92,"r":2,"color":OUT})
    P.append({"type":"circle","cx":132,"cy":92,"r":2,"color":OUT})
    # TEETH — white triangles along the jaw line (THE croc feature)
    for tx in (112,120,128,136,144):
        P.append({"type":"polygon","points":[(tx-3,114),(tx+3,114),(tx,120)],"color":TOOTH,"outline":OUT,"outline_w":1})
    for tx in (116,124,132,140):
        P.append({"type":"polygon","points":[(tx-3,118),(tx+3,118),(tx,112)],"color":TOOTH,"outline":OUT,"outline_w":1})
    # glowing red eyes (menacing)
    P.append({"type":"circle","cx":116,"cy":74,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":140,"cy":74,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":117,"cy":73,"r":1,"color":(255,200,180)})
    P.append({"type":"circle","cx":141,"cy":73,"r":1,"color":(255,200,180)})
    # scale bumps on head
    for sx,sy in [(110,62),(128,58),(146,62),(120,52),(136,52)]:
        P.append({"type":"circle","cx":sx,"cy":sy,"r":3,"color":SCALE_DARK,"outline":OUT,"outline_w":1})
    return P


if __name__ == "__main__":
    prims = renekton_prims()
    # fix the deliberate typo line if any survived
    prims = [p for p in prims if "cx" not in p or isinstance(p.get("cx"),int)]
    r = improve("Renekton", prims, gate_n=3)
    print("RESULT:", r)
