"""Sona — Maven of the Strings.
Iconic: BIG floating etwahl instrument (golden harp/zither) — THE feature,
bigger than her body. Long flowing hair, elegant Demacian gown, blue/gold/white.
The etwahl dominates the silhouette.
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve

OUT = (35, 30, 25)
SKIN = (235, 215, 200)       # fair skin
HAIR = (180, 140, 80)        # honey-blonde flowing hair (long)
HAIR_DARK = (140, 100, 55)
GOWN = (180, 210, 230)       # light blue-white Demacian gown
GOWN_DARK = (130, 170, 210)
GOLD = (225, 185, 70)
GOLD_DARK = (160, 120, 35)
ETWAHL = (235, 200, 90)      # golden etwahl
ETWAHL_DARK = (170, 130, 40)
STRING = (250, 240, 210)     # harp strings (white-gold)
AURA = (170, 220, 255)       # ethereal musical aura
EYE = (90, 130, 180)         # teal-blue eyes
PINK = (235, 180, 200)       # pink accent (Sona's canon pink/teal)


def sona_prims():
    P = []
    # --- Ethereal musical aura (behind everything, soft glow) ---
    P.append({"type":"ellipse","x":40,"y":60,"w":176,"h":170,"color":AURA,"outline":None})
    P.append({"type":"ellipse","x":60,"y":80,"w":136,"h":130,"color":(210,235,255),"outline":None})
    # subtle aura ring (visible but thin, outlined)
    P.append({"type":"ellipse","x":36,"y":56,"w":184,"h":178,"color":(220,240,255),"outline":AURA,"outline_w":2})

    # --- Hair back (long, flowing down past waist — BIG) ---
    P.append({"type":"circle","cx":128,"cy":72,"r":22,"color":HAIR,"outline":OUT,"outline_w":1})
    # long flowing hair down the back (wide, prominent)
    P.append({"type":"polygon","points":[(104,68),(152,68),(158,220),(98,220)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # hair strand highlights (more visible)
    P.append({"type":"line","start":[112,80],"end":[110,215],"color":HAIR_DARK,"width":2})
    P.append({"type":"line","start":[122,80],"end":[120,218],"color":HAIR_DARK,"width":2})
    P.append({"type":"line","start":[134,80],"end":[136,218],"color":HAIR_DARK,"width":2})
    P.append({"type":"line","start":[144,80],"end":[146,215],"color":HAIR_DARK,"width":2})
    # hair side locks framing face (more visible "long flowing")
    P.append({"type":"polygon","points":[(104,68),(112,68),(108,140),(100,130)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(144,68),(152,68),(156,130),(148,140)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- BIG floating etwahl (THE feature — golden harp/zither beside her) ---
    # Drawn prominently on her left (right side of image), BIG, floating
    # etwahl body (curved golden frame, harp-like)
    # main frame — tall curved golden arch
    P.append({"type":"polygon","points":[(180,40),(168,44),(168,200),(184,196),(196,180),(196,60)],
              "color":ETWAHL,"outline":OUT,"outline_w":2})
    # inner frame (darker gold)
    P.append({"type":"polygon","points":[(186,56),(178,58),(178,184),(190,182)],
              "color":ETWAHL_DARK,"outline":OUT,"outline_w":1})
    # soundboard (the resonator body, golden)
    P.append({"type":"ellipse","x":172,"y":100,"w":24,"h":80,"color":ETWAHL,"outline":OUT,"outline_w":2})
    # gold decorative gems on frame
    P.append({"type":"circle","cx":188,"cy":48,"r":4,"color":PINK,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":188,"cy":192,"r":4,"color":PINK,"outline":GOLD_DARK,"outline_w":1})
    # HARP STRINGS (THE etwahl feature — vertical golden strings)
    for sx in (176, 180, 184, 188, 192):
        P.append({"type":"line","start":[sx,56],"end":[sx,184],"color":STRING,"width":1})
    # tuning pegs (gold)
    for sy in (56, 100, 140, 184):
        P.append({"type":"circle","cx":196,"cy":sy,"r":2,"color":GOLD,"outline":OUT,"outline_w":1})
    # glow around etwahl (ethereal, floating)
    P.append({"type":"circle","cx":188,"cy":120,"r":36,"color":(255,240,180),"outline":None})
    P.append({"type":"ellipse","x":168,"y":90,"w":40,"h":100,"color":(255,245,200),"outline":None})

    # --- Head (beautiful, serene, mute) ---
    P.append({"type":"circle","cx":128,"cy":78,"r":17,"color":SKIN,"outline":OUT,"outline_w":1})
    # serene closed/soft eyes (mute — gentle)
    P.append({"type":"line","start":[120,78],"end":[126,78],"color":EYE,"width":2})
    P.append({"type":"line","start":[130,78],"end":[136,78],"color":EYE,"width":2})
    # gentle smile
    P.append({"type":"line","start":[122,86],"end":[134,86],"color":(170,110,120),"width":1})
    # hair front (bangs + headband)
    P.append({"type":"polygon","points":[(112,66),(144,66),(140,76),(116,76)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # gold headband (Demacian)
    P.append({"type":"rect","x":114,"y":64,"w":28,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":62,"r":3,"color":PINK,"outline":GOLD_DARK,"outline_w":1})

    # --- Elegant Demacian gown (blue-white, flowing) ---
    P.append({"type":"polygon","points":[(110,98),(146,98),(162,210),(94,210)],
              "color":GOWN,"outline":OUT,"outline_w":1})
    # gown center panel (lighter)
    P.append({"type":"polygon","points":[(118,98),(138,98),(142,210),(114,210)],
              "color":(225,240,250),"outline":OUT,"outline_w":1})
    # gold trim down gown
    P.append({"type":"line","start":[128,98],"end":[128,210],"color":GOLD,"width":2})
    # gold collar/neckline
    P.append({"type":"polygon","points":[(116,98),(140,98),(136,108),(120,108)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold sash at waist
    P.append({"type":"rect","x":104,"y":150,"w":48,"h":8,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":154,"r":4,"color":PINK,"outline":GOLD_DARK,"outline_w":1})

    # --- Arms (elegant, one raised toward etwahl) ---
    # left arm (down)
    P.append({"type":"rect","x":100,"y":108,"w":10,"h":44,"color":GOWN,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":105,"cy":154,"r":4,"color":SKIN,"outline":OUT,"outline_w":1})
    # right arm (raised toward etwahl, playing)
    P.append({"type":"rect","x":146,"y":108,"w":10,"h":30,"color":GOWN,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":152,"y":120,"w":10,"h":24,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":160,"cy":142,"r":4,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Floating musical notes (ethereal aura, THE magic feature) ---
    # glowing notes around etwahl + body (more visible aura)
    for nx, ny in [(212,76),(216,128),(212,172),(158,34),(92,46),(66,120),(76,176)]:
        P.append({"type":"circle","cx":nx,"cy":ny,"r":5,"color":AURA,"outline":OUT,"outline_w":1})
        P.append({"type":"line","start":[nx+4,ny-2],"end":[nx+4,ny-14],"color":AURA,"width":2})

    # --- Legs (under gown, slight) ---
    P.append({"type":"rect","x":114,"y":200,"w":10,"h":14,"color":SKIN,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":132,"y":200,"w":10,"h":14,"color":SKIN,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":112,"y":212,"w":14,"h":6,"color":GOLD,"outline":OUT,"outline_w":1,"radius":1})
    P.append({"type":"rect","x":130,"y":212,"w":14,"h":6,"color":GOLD,"outline":OUT,"outline_w":1,"radius":1})

    return P


if __name__ == "__main__":
    prims = sona_prims()
    prims = [p for p in prims if "cx" not in p or isinstance(p.get("cx"), int)]
    r = improve("Sona", prims, gate_n=3)
    print("RESULT:", r)
