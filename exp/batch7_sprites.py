"""Batch 7: hand-author 6 LoL champions to score 8-10.

Champions: Jinx, KSante, Karma, Kayle, Khazix, Kled.
Each has ONE huge signature feature that dominates the silhouette.
Run sequentially; improve() auto-saves only when new > old.
"""
import sys, json, time
sys.path.insert(0, "exp")
from champ_improver import improve, committed_score

OUT = (25, 20, 30)


# ============================================================
# 1. JINX — EXTREMELY long blue braided pigtails (THE feature) + minigun
# ============================================================
def jinx_prims():
    P = []
    SKIN = (245, 225, 210)       # pale
    HAIR = (90, 140, 220)        # blue
    HAIR_DARK = (50, 90, 170)
    HAIR_TIE = (220, 80, 130)    # pink hair ties
    TATTOO = (180, 80, 160)      # pink/purple tattoos
    SHIRT = (50, 45, 55)         # black punk top
    PINK = (220, 90, 140)        # pink accents
    MINIGUN = (130, 120, 110)    # Pow-Pow minigun
    MINIGUN_DARK = (80, 70, 65)
    EYE = (220, 80, 130)         # manic pink eyes
    OUT = (25, 20, 25)

    # --- EXTREMELY LONG BLUE BRAIDED PIGTAILS (THE feature — super long, both sides) ---
    # LEFT braid — long, hanging down past the body to bottom of frame
    braid_left = [(104,78),(92,108),(84,148),(80,188),(82,228)]
    for i in range(len(braid_left)-1):
        P.append({"type":"line","start":braid_left[i],"end":braid_left[i+1],"color":HAIR,"width":12})
    # braid segments (visible braided texture — circles along the braid)
    for cx,cy in braid_left:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":7,"color":HAIR,"outline":HAIR_DARK,"outline_w":1})
    # braid crisscross pattern (braided texture)
    for i in range(0,len(braid_left)-1):
        cx,cy = braid_left[i]
        P.append({"type":"line","start":[cx-4,cy],"end":[cx+4,cy+4],"color":HAIR_DARK,"width":1})
        P.append({"type":"line","start":[cx+4,cy],"end":[cx-4,cy+4],"color":HAIR_DARK,"width":1})
    # pink hair tie at end of left braid
    P.append({"type":"circle","cx":82,"cy":228,"r":6,"color":HAIR_TIE,"outline":OUT,"outline_w":1})
    # braid tip (tassel)
    P.append({"type":"polygon","points":[(78,232),(86,232),(82,244)],"color":HAIR,"outline":OUT,"outline_w":1})

    # RIGHT braid — long, hanging down past the body to bottom of frame
    braid_right = [(152,78),(164,108),(172,148),(176,188),(174,228)]
    for i in range(len(braid_right)-1):
        P.append({"type":"line","start":braid_right[i],"end":braid_right[i+1],"color":HAIR,"width":12})
    for cx,cy in braid_right:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":7,"color":HAIR,"outline":HAIR_DARK,"outline_w":1})
    for i in range(0,len(braid_right)-1):
        cx,cy = braid_right[i]
        P.append({"type":"line","start":[cx-4,cy],"end":[cx+4,cy+4],"color":HAIR_DARK,"width":1})
        P.append({"type":"line","start":[cx+4,cy],"end":[cx-4,cy+4],"color":HAIR_DARK,"width":1})
    P.append({"type":"circle","cx":174,"cy":228,"r":6,"color":HAIR_TIE,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(170,232),(178,232),(174,244)],"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Hair top (blue, messy) ---
    P.append({"type":"circle","cx":128,"cy":72,"r":22,"color":HAIR,"outline":OUT,"outline_w":1})
    # wild bangs
    P.append({"type":"polygon","points":[(108,62),(148,62),(144,76),(112,76)],"color":HAIR,"outline":OUT,"outline_w":1})
    # pink streak in hair
    P.append({"type":"polygon","points":[(120,58),(132,58),(130,68),(122,68)],"color":PINK,"outline":OUT,"outline_w":1})

    # --- Head (pale) ---
    P.append({"type":"circle","cx":128,"cy":78,"r":18,"color":SKIN,"outline":OUT,"outline_w":1})
    # manic eyes (wild pink)
    P.append({"type":"circle","cx":121,"cy":80,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":80,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    # manic grin (wide)
    P.append({"type":"polygon","points":[(120,90),(136,90),(134,94),(122,94)],"color":OUT,"outline":None,"outline_w":0})

    # --- Colorful tattoos (on arms/shoulders — pink/purple) ---
    P.append({"type":"circle","cx":108,"cy":110,"r":4,"color":TATTOO,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":148,"cy":110,"r":4,"color":TATTOO,"outline":None,"outline_w":0})

    # --- Punk top (black, mismatched) ---
    P.append({"type":"polygon","points":[(108,98),(148,98),(154,170),(102,170)],
              "color":SHIRT,"outline":OUT,"outline_w":1})
    # pink stripe on shirt
    P.append({"type":"rect","x":108,"y":120,"w":40,"h":6,"color":PINK,"outline":OUT,"outline_w":1})
    # pink strap
    P.append({"type":"rect","x":108,"y":140,"w":40,"h":4,"color":PINK,"outline":OUT,"outline_w":1})

    # --- Arms ---
    P.append({"type":"rect","x":98,"y":106,"w":12,"h":50,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":146,"y":106,"w":12,"h":50,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":104,"cy":158,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":152,"cy":158,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (striped) ---
    P.append({"type":"rect","x":110,"y":170,"w":14,"h":40,"color":SHIRT,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":14,"h":40,"color":PINK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":108,"y":206,"w":18,"h":10,"color":MINIGUN_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":206,"w":18,"h":10,"color":MINIGUN_DARK,"outline":OUT,"outline_w":1,"radius":2})

    # --- POW-POW MINIGUN (THE feature — big, held in front) ---
    # minigun body (cylindrical)
    P.append({"type":"rect","x":150,"y":140,"w":40,"h":24,"color":MINIGUN,"outline":OUT,"outline_w":2})
    # minigun barrels (multiple barrels = gatling)
    for by in (144,150,156,162):
        P.append({"type":"line","start":[190,by],"end":[210,by],"color":MINIGUN_DARK,"width":3})
    # minigun ammo belt
    P.append({"type":"rect","x":146,"y":138,"w":10,"h":28,"color":MINIGUN_DARK,"outline":OUT,"outline_w":1})
    # pink bow on minigun (Jinx's signature decoration)
    P.append({"type":"circle","cx":160,"cy":134,"r":4,"color":PINK,"outline":OUT,"outline_w":1})

    return P


# ============================================================
# 2. KSANTE — large ornate SHOULDER GUARDS (THE feature) + big mace
# ============================================================
def ksante_prims():
    P = []
    SKIN = (150, 110, 80)        # dark skin
    GOLD = (215, 175, 60)
    GOLD_DARK = (150, 110, 30)
    BLUE = (40, 60, 110)         # deep blue Nazumah attire
    BLUE_DARK = (25, 40, 75)
    BROWN = (110, 75, 45)
    MACE = (130, 110, 90)        # Ntofo war hammer
    MACE_DARK = (70, 55, 40)
    EYE = (30, 25, 20)
    OUT = (30, 22, 15)

    # --- LARGE ORNATE SHOULDER GUARDS (THE feature — huge, both shoulders) ---
    # LEFT shoulder guard (big, ornate, gold-trimmed)
    P.append({"type":"circle","cx":86,"cy":108,"r":22,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":86,"cy":108,"r":16,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})
    # ornate spike on left shoulder
    P.append({"type":"polygon","points":[(80,90),(92,90),(86,74)],"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold trim detailing
    P.append({"type":"circle","cx":86,"cy":108,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # RIGHT shoulder guard (big, ornate, gold-trimmed)
    P.append({"type":"circle","cx":170,"cy":108,"r":22,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":170,"cy":108,"r":16,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(164,90),(176,90),(170,74)],"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":170,"cy":108,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Head (dark skin, braided hair) ---
    P.append({"type":"circle","cx":128,"cy":78,"r":18,"color":SKIN,"outline":OUT,"outline_w":1})
    # braided hair (top)
    P.append({"type":"circle","cx":128,"cy":62,"r":14,"color":BROWN,"outline":OUT,"outline_w":1})
    # braids (visible texture)
    for bx in (120,128,136):
        P.append({"type":"line","start":[bx,56],"end":[bx,72],"color":BLUE_DARK,"width":1})
    # gold headband
    P.append({"type":"rect","x":112,"y":68,"w":32,"h":4,"color":GOLD,"outline":OUT,"outline_w":1})
    # eyes (determined)
    P.append({"type":"circle","cx":122,"cy":80,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":134,"cy":80,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    # beard (short)
    P.append({"type":"polygon","points":[(118,90),(138,90),(136,98),(120,98)],"color":BROWN,"outline":OUT,"outline_w":1})

    # --- Torso (Nazumah attire — deep blue with gold trim) ---
    P.append({"type":"polygon","points":[(108,98),(148,98),(152,180),(104,180)],
              "color":BLUE,"outline":OUT,"outline_w":1})
    # gold chest plate (ornate)
    P.append({"type":"polygon","points":[(112,104),(144,104),(140,150),(116,150)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # chest emblem (Nazumah symbol)
    P.append({"type":"circle","cx":128,"cy":120,"r":6,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":120,"r":3,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold belt
    P.append({"type":"rect","x":104,"y":168,"w":48,"h":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Arms (under shoulder guards) ---
    P.append({"type":"rect","x":96,"y":128,"w":14,"h":40,"color":BLUE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":146,"y":128,"w":14,"h":40,"color":BLUE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":103,"cy":170,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":153,"cy":170,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs ---
    P.append({"type":"rect","x":110,"y":180,"w":16,"h":40,"color":BLUE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":180,"w":16,"h":40,"color":BLUE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":108,"y":216,"w":20,"h":10,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":216,"w":20,"h":10,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})

    # --- NTOFO WAR HAMMER (THE feature — massive two-handed mace, held across body) ---
    # handle (long, diagonal)
    P.append({"type":"line","start":[80,180],"end":[176,90],"color":BROWN,"width":7})
    # hammer head (BIG, massive — the Ntofo)
    P.append({"type":"polygon","points":[(168,80),(200,72),(206,96),(176,104)],
              "color":MACE,"outline":MACE_DARK,"outline_w":2})
    # hammer head detail (gold bands)
    P.append({"type":"line","start":[172,84],"end":[200,78],"color":GOLD,"width":2})
    P.append({"type":"line","start":[174,100],"end":[202,94],"color":GOLD,"width":2})
    # hammer spikes (top)
    P.append({"type":"polygon","points":[(180,72),(188,72),(184,60)],"color":MACE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(192,70),(200,70),(196,58)],"color":MACE_DARK,"outline":OUT,"outline_w":1})
    # handle grip wrap
    for hx in (88,96,104,112):
        P.append({"type":"line","start":[hx,172],"end":[hx+4,168],"color":GOLD,"width":1})
    # handle pommel
    P.append({"type":"circle","cx":80,"cy":182,"r":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    return P


# ============================================================
# 3. KARMA — large floating MANTRA SCROLLS (THE feature) + floating
# ============================================================
def karma_prims():
    P = []
    SKIN = (215, 185, 165)
    HAIR = (60, 45, 40)         # dark hair
    ROBE = (245, 240, 230)      # white Ionian robes
    ROBE_DARK = (200, 195, 185)
    GOLD = (220, 180, 70)
    TEAL = (90, 180, 175)       # teal spiritual energy
    TEAL_BRIGHT = (140, 230, 220)
    SCROLL = (235, 215, 170)    # golden scroll parchment
    SCROLL_DARK = (180, 150, 90)
    EYE = (90, 180, 175)        # glowing teal eyes
    OUT = (30, 25, 25)

    # --- LARGE FLOATING MANTRA SCROLLS (THE feature — BIG, clearly scrolls, orbiting) ---
    # Scroll 1: left side (BIG vertical scroll, unrolled, with rolled ends)
    # rolled top cap (cylinder)
    P.append({"type":"ellipse","x":30,"y":50,"w":30,"h":14,"color":GOLD,"outline":SCROLL_DARK,"outline_w":2})
    # parchment body (BIG)
    P.append({"type":"rect","x":34,"y":58,"w":22,"h":72,"color":SCROLL,"outline":SCROLL_DARK,"outline_w":2})
    # rolled bottom cap (cylinder)
    P.append({"type":"ellipse","x":30,"y":124,"w":30,"h":14,"color":GOLD,"outline":SCROLL_DARK,"outline_w":2})
    # mantra text markings (teal symbols — BIG visible)
    for sy in (66,76,86,96,106,116):
        P.append({"type":"line","start":[40,sy],"end":[50,sy],"color":TEAL,"width":2})
    # teal glow around scroll (floating energy)
    P.append({"type":"circle","cx":45,"cy":94,"r":22,"color":TEAL_BRIGHT,"outline":None,"outline_w":0})

    # Scroll 2: right side (BIG vertical scroll, unrolled, with rolled ends)
    P.append({"type":"ellipse","x":196,"y":50,"w":30,"h":14,"color":GOLD,"outline":SCROLL_DARK,"outline_w":2})
    P.append({"type":"rect","x":200,"y":58,"w":22,"h":72,"color":SCROLL,"outline":SCROLL_DARK,"outline_w":2})
    P.append({"type":"ellipse","x":196,"y":124,"w":30,"h":14,"color":GOLD,"outline":SCROLL_DARK,"outline_w":2})
    for sy in (66,76,86,96,106,116):
        P.append({"type":"line","start":[206,sy],"end":[216,sy],"color":TEAL,"width":2})
    P.append({"type":"circle","cx":211,"cy":94,"r":22,"color":TEAL_BRIGHT,"outline":None,"outline_w":0})

    # Scroll 3: behind/above head (horizontal scroll, BIG — clearly a scroll)
    P.append({"type":"ellipse","x":72,"y":34,"w":14,"h":30,"color":GOLD,"outline":SCROLL_DARK,"outline_w":2})
    P.append({"type":"rect","x":80,"y":38,"w":96,"h":22,"color":SCROLL,"outline":SCROLL_DARK,"outline_w":2})
    P.append({"type":"ellipse","x":170,"y":34,"w":14,"h":30,"color":GOLD,"outline":SCROLL_DARK,"outline_w":2})
    for sx in (92,108,124,140,156):
        P.append({"type":"line","start":[sx,44],"end":[sx,54],"color":TEAL,"width":2})

    # --- Spiritual teal aura glow (around her — floating, BIG) ---
    P.append({"type":"circle","cx":128,"cy":80,"r":36,"color":TEAL_BRIGHT,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":128,"cy":160,"r":44,"color":TEAL_BRIGHT,"outline":None,"outline_w":0})

    # --- Dark hair (back) ---
    P.append({"type":"circle","cx":128,"cy":78,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    # gold hair ornaments
    P.append({"type":"circle","cx":116,"cy":68,"r":4,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":140,"cy":68,"r":4,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Head (meditative, serene — FLOATING, no legs, lotus pose) ---
    P.append({"type":"circle","cx":128,"cy":86,"r":17,"color":SKIN,"outline":OUT,"outline_w":1})
    # glowing teal eyes (spiritual)
    P.append({"type":"circle","cx":121,"cy":88,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":88,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    # serene mark on forehead (tilaka)
    P.append({"type":"circle","cx":128,"cy":78,"r":3,"color":TEAL,"outline":OUT,"outline_w":1})
    # calm mouth (serene meditative)
    P.append({"type":"line","start":[123,96],"end":[133,96],"color":(120,80,70),"width":1})

    # --- Ornate Ionian robes (white + gold + teal — MEDITATIVE lotus pose) ---
    P.append({"type":"polygon","points":[(104,104),(152,104),(164,180),(92,180)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # gold trim collar
    P.append({"type":"rect","x":104,"y":104,"w":48,"h":6,"color":GOLD,"outline":OUT,"outline_w":1})
    # teal sash (spiritual)
    P.append({"type":"polygon","points":[(96,140),(160,140),(164,156),(92,156)],
              "color":TEAL,"outline":OUT,"outline_w":1})
    # gold belt
    P.append({"type":"rect","x":92,"y":154,"w":72,"h":6,"color":GOLD,"outline":OUT,"outline_w":1})
    # robe center fold
    P.append({"type":"line","start":[128,110],"end":[128,178],"color":ROBE_DARK,"width":1})
    # golden jewelry on robe (chest)
    P.append({"type":"circle","cx":128,"cy":124,"r":5,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":124,"r":2,"color":TEAL_BRIGHT,"outline":None,"outline_w":0})

    # --- Arms (meditative pose — both raised forward, palms up = meditation) ---
    P.append({"type":"rect","x":92,"y":116,"w":12,"h":36,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":152,"y":116,"w":12,"h":36,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    # hands (palms up, meditative — visible)
    P.append({"type":"circle","cx":98,"cy":154,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":158,"cy":154,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (crossed lotus pose — FLOATING, no feet on ground) ---
    P.append({"type":"ellipse","x":88,"y":178,"w":80,"h":28,"color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # crossed legs (visible fold)
    P.append({"type":"line","start":[96,190],"end":[160,190],"color":ROBE_DARK,"width":1})
    # gold trim at hem
    P.append({"type":"rect","x":88,"y":178,"w":80,"h":5,"color":GOLD,"outline":OUT,"outline_w":1})
    # floating energy wisps under her (she hovers)
    for fx in (96,128,160):
        P.append({"type":"circle","cx":fx,"cy":210,"r":5,"color":TEAL_BRIGHT,"outline":TEAL,"outline_w":1})

    # --- Floating teal energy wisps (spiritual aura) ---
    for sx,sy in [(70,140),(186,140),(80,180),(176,180)]:
        P.append({"type":"circle","cx":sx,"cy":sy,"r":4,"color":TEAL_BRIGHT,"outline":TEAL,"outline_w":1})

    return P


# ============================================================
# 4. KAYLE — LARGE WHITE WINGS (THE feature, spread wide) + halo + golden armor
# ============================================================
def kayle_prims():
    P = []
    SKIN = (230, 210, 195)
    HAIR = (240, 230, 220)       # white-gold hair
    WING = (245, 245, 250)       # white wings
    WING_DARK = (190, 195, 210)
    GOLD = (225, 185, 70)
    GOLD_DARK = (155, 120, 35)
    SILVER = (200, 205, 220)
    SILVER_DARK = (120, 125, 140)
    HALO = (255, 235, 150)       # golden halo of light
    EYE = (255, 230, 150)        # divine glowing eyes
    OUT = (30, 25, 25)

    # --- HALO OF LIGHT (THE feature — big golden ring above head) ---
    P.append({"type":"circle","cx":128,"cy":40,"r":22,"color":HALO,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":40,"r":14,"color":None if False else (250,250,255),"outline":None,"outline_w":0})
    # halo rays (divine radiance)
    import math as _m
    for ang in range(0, 360, 30):
        x1 = 128 + int(22 * _m.cos(_m.radians(ang)))
        y1 = 40 + int(22 * _m.sin(_m.radians(ang)))
        x2 = 128 + int(30 * _m.cos(_m.radians(ang)))
        y2 = 40 + int(30 * _m.sin(_m.radians(ang)))
        P.append({"type":"line","start":[x1,y1],"end":[x2,y2],"color":HALO,"width":2})

    # --- LARGE WHITE WINGS (THE feature — spread wide, both sides, BIG) ---
    # LEFT wing (spread out to the left, big feathers)
    P.append({"type":"polygon","points":[(108,90),(40,80),(28,120),(40,150),(60,140),(80,130),(100,120)],
              "color":WING,"outline":WING_DARK,"outline_w":2})
    # left wing feather details (rows of feathers)
    for fy in (96,108,120,132):
        P.append({"type":"line","start":[100,fy],"end":[44,fy-4],"color":WING_DARK,"width":1})
    # left wing primary feathers (long, at wingtip)
    for i,fx in enumerate((32,40,48,56)):
        P.append({"type":"polygon","points":[(fx,108),(fx-8,104),(fx-4,118)],"color":WING,"outline":WING_DARK,"outline_w":1})

    # RIGHT wing (spread out to the right, big feathers)
    P.append({"type":"polygon","points":[(148,90),(216,80),(228,120),(216,150),(196,140),(176,130),(156,120)],
              "color":WING,"outline":WING_DARK,"outline_w":2})
    for fy in (96,108,120,132):
        P.append({"type":"line","start":[156,fy],"end":[212,fy-4],"color":WING_DARK,"width":1})
    for i,fx in enumerate((224,216,208,200)):
        P.append({"type":"polygon","points":[(fx,108),(fx+8,104),(fx+4,118)],"color":WING,"outline":WING_DARK,"outline_w":1})

    # --- Hair (white-gold, flowing) ---
    P.append({"type":"circle","cx":128,"cy":74,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(110,76),(146,76),(150,110),(106,110)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":80,"r":17,"color":SKIN,"outline":OUT,"outline_w":1})
    # BLINDFOLD / VEILED EYES (THE missing feature — golden blindfold over eyes)
    P.append({"type":"rect","x":110,"y":76,"w":36,"h":8,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # blindfold divine glow
    P.append({"type":"line","start":[112,80],"end":[144,80],"color":HALO,"width":1})
    # serene mouth
    P.append({"type":"line","start":[123,92],"end":[133,92],"color":(150,100,90),"width":1})

    # --- Golden plate armor torso ---
    P.append({"type":"polygon","points":[(108,98),(148,98),(154,180),(102,180)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # armor segments (breastplate)
    P.append({"type":"line","start":[128,100],"end":[128,178],"color":GOLD_DARK,"width":1})
    P.append({"type":"line","start":[112,130],"end":[144,130],"color":GOLD_DARK,"width":1})
    # silver chest emblem (divine)
    P.append({"type":"circle","cx":128,"cy":120,"r":6,"color":SILVER,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":120,"r":3,"color":HALO,"outline":None,"outline_w":0})
    # silver shoulder plates
    P.append({"type":"circle","cx":104,"cy":104,"r":8,"color":SILVER,"outline":SILVER_DARK,"outline_w":1})
    P.append({"type":"circle","cx":152,"cy":104,"r":8,"color":SILVER,"outline":SILVER_DARK,"outline_w":1})
    # gold belt
    P.append({"type":"rect","x":102,"y":168,"w":52,"h":10,"color":SILVER,"outline":SILVER_DARK,"outline_w":1})
    P.append({"type":"rect","x":102,"y":166,"w":52,"h":3,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Arms (raised, holding flaming swords) ---
    P.append({"type":"rect","x":96,"y":110,"w":12,"h":40,"color":GOLD,"outline":GOLD_DARK,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":148,"y":110,"w":12,"h":40,"color":GOLD,"outline":GOLD_DARK,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":102,"cy":152,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":154,"cy":152,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (robe/armor skirt) ---
    P.append({"type":"polygon","points":[(102,178),(154,178),(158,225),(98,225)],
              "color":SILVER,"outline":SILVER_DARK,"outline_w":1})
    P.append({"type":"rect","x":98,"y":222,"w":60,"h":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- DUAL FLAMING SWORDS (THE missing feature — two swords, flaming) ---
    # LEFT flaming sword (held up-left)
    P.append({"type":"line","start":[100,150],"end":[68,100],"color":SILVER,"width":4})
    P.append({"type":"line","start":[100,150],"end":[68,100],"color":HALO,"width":1})
    # flame on left sword
    P.append({"type":"polygon","points":[(64,96),(72,96),(68,80)],"color":HALO,"outline":(220,150,40),"outline_w":1})
    P.append({"type":"polygon","points":[(66,94),(70,94),(68,84)],"color":(255,200,80),"outline":None,"outline_w":0})
    # left sword hilt
    P.append({"type":"rect","x":94,"y":148,"w":12,"h":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # RIGHT flaming sword (held up-right)
    P.append({"type":"line","start":[156,150],"end":[188,100],"color":SILVER,"width":4})
    P.append({"type":"line","start":[156,150],"end":[188,100],"color":HALO,"width":1})
    # flame on right sword
    P.append({"type":"polygon","points":[(184,96),(192,96),(188,80)],"color":HALO,"outline":(220,150,40),"outline_w":1})
    P.append({"type":"polygon","points":[(186,94),(190,94),(188,84)],"color":(255,200,80),"outline":None,"outline_w":0})
    # right sword hilt
    P.append({"type":"rect","x":150,"y":148,"w":12,"h":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    return P


# ============================================================
# 5. KHA'ZIX — scythe claws + chitinous exoskeleton + glowing purple eyes (quadruped)
# ============================================================
def khazix_prims():
    P = []
    CHITIN = (115, 70, 135)
    CHITIN_DARK = (70, 40, 85)
    VOID = (180, 100, 220)
    VOID_GLOW = (220, 140, 255)
    CLAW = (210, 190, 225)
    CLAW_DARK = (150, 110, 170)
    EYE = (230, 110, 255)
    OUT = (25, 15, 30)

    # --- Segmented tail (behind, curling up — THE missing feature) ---
    tail_pts = [(60,150),(48,134),(40,114),(44,94),(58,82)]
    for i in range(len(tail_pts)-1):
        P.append({"type":"line","start":tail_pts[i],"end":tail_pts[i+1],"color":CHITIN_DARK,"width":12})
    for cx, cy in tail_pts:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":7,"color":CHITIN,"outline":CHITIN_DARK,"outline_w":1})
    # tail segments (visible segmentation)
    for cx,cy in tail_pts:
        P.append({"type":"line","start":[cx-5,cy],"end":[cx+5,cy],"color":CHITIN_DARK,"width":1})
    # tail blade tip
    P.append({"type":"polygon","points":[(56,80),(68,72),(62,90)],"color":CLAW,"outline":CLAW_DARK,"outline_w":1})

    # --- Chitinous body (hunched insectoid, low quadruped) ---
    P.append({"type":"ellipse","x":64,"y":120,"w":120,"h":52,"color":CHITIN,"outline":CHITIN_DARK,"outline_w":2})
    # belly (darker underside)
    P.append({"type":"ellipse","x":80,"y":142,"w":90,"h":20,"color":CHITIN_DARK,"outline":OUT,"outline_w":1})
    # exoskeleton plates (chitinous ridges — THE feature)
    for px in (84,108,132,156):
        P.append({"type":"polygon","points":[(px-12,128),(px+12,128),(px+7,114),(px-7,114)],
                  "color":VOID,"outline":CHITIN_DARK,"outline_w":1})
        P.append({"type":"line","start":[px,114],"end":[px,128],"color":CHITIN_DARK,"width":1})
    # dorsal spikes (chitinous ridges)
    for dx in (96,120,144):
        P.append({"type":"polygon","points":[(dx-5,114),(dx,100),(dx+5,114)],"color":CHITIN_DARK,"outline":OUT,"outline_w":1})

    # --- Four digitigrade legs (insectoid, splayed) ---
    leg_pts = [(80,168),(108,170),(140,170),(168,168)]
    for lx,ly in leg_pts:
        P.append({"type":"polygon","points":[(lx-6,ly),(lx+6,ly),(lx+4,ly+16),(lx-4,ly+16)],
                  "color":CHITIN,"outline":CHITIN_DARK,"outline_w":1})
        P.append({"type":"circle","cx":lx,"cy":ly+16,"r":5,"color":CHITIN_DARK,"outline":OUT,"outline_w":1})
        P.append({"type":"line","start":[lx,ly+16],"end":[lx,ly+30],"color":CHITIN_DARK,"width":4})
        P.append({"type":"circle","cx":lx,"cy":ly+30,"r":5,"color":CHITIN_DARK,"outline":OUT,"outline_w":1})

    # --- SCYTHE-LIKE CLAWS (THE feature — HUGE, raised high above body, prominent) ---
    # Front-left scythe claw (giant curved blade raised up — the icon)
    P.append({"type":"polygon","points":[(76,160),(40,120),(30,160),(54,176)],
              "color":CLAW,"outline":CLAW_DARK,"outline_w":2})
    P.append({"type":"line","start":[60,164],"end":[36,128],"color":(255,240,255),"width":1})
    # secondary scythe claw (slightly smaller, behind)
    P.append({"type":"polygon","points":[(80,156),(56,118),(48,150),(68,168)],
              "color":CLAW,"outline":CLAW_DARK,"outline_w":1})
    # Front-right scythe claw (giant curved blade raised up)
    P.append({"type":"polygon","points":[(180,160),(216,120),(226,160),(202,176)],
              "color":CLAW,"outline":CLAW_DARK,"outline_w":2})
    P.append({"type":"line","start":[196,164],"end":[220,128],"color":(255,240,255),"width":1})
    P.append({"type":"polygon","points":[(176,156),(200,118),(208,150),(188,168)],
              "color":CLAW,"outline":CLAW_DARK,"outline_w":1})
    # Back leg claws (smaller, pointing down)
    for lx in (108,140):
        P.append({"type":"line","start":[lx,196],"end":[lx,210],"color":CLAW,"width":2})

    # --- HEAD (insectoid, with BIG mandibles — THE missing feature) ---
    P.append({"type":"circle","cx":192,"cy":138,"r":20,"color":CHITIN,"outline":CHITIN_DARK,"outline_w":2})
    # BIG mandibles (THE feature — sharp, curved, prominent, like scythe jaws)
    P.append({"type":"polygon","points":[(198,148),(224,156),(216,172),(200,164)],
              "color":CLAW,"outline":CLAW_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(198,128),(224,120),(216,104),(200,112)],
              "color":CLAW,"outline":CLAW_DARK,"outline_w":1})
    # mandible inner teeth
    P.append({"type":"line","start":[206,150],"end":[214,156],"color":CLAW_DARK,"width":1})
    P.append({"type":"line","start":[206,126],"end":[214,120],"color":CLAW_DARK,"width":1})
    # chitinous head crest
    P.append({"type":"polygon","points":[(184,122),(200,114),(206,130),(188,134)],"color":CHITIN_DARK,"outline":OUT,"outline_w":1})
    # glowing purple eyes (THE feature — 3 eyes, insectoid, BIG and bright)
    P.append({"type":"circle","cx":184,"cy":132,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":198,"cy":134,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":192,"cy":126,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    # eye glow cores
    P.append({"type":"circle","cx":184,"cy":131,"r":2,"color":VOID_GLOW,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":198,"cy":133,"r":2,"color":VOID_GLOW,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":192,"cy":125,"r":2,"color":VOID_GLOW,"outline":None,"outline_w":0})

    # --- Void energy glow (purple wisps) ---
    for gy in (110,140):
        P.append({"type":"circle","cx":120,"cy":gy,"r":4,"color":VOID_GLOW,"outline":None,"outline_w":0})

    return P


# ============================================================
# 6. KLED — rides SKAAARL the lizard (THE feature — big mount) + Noxian armor
# ============================================================
def kled_prims():
    P = []
    LIZARD = (110, 130, 90)      # Skaarl - green-grey lizard
    LIZARD_DARK = (70, 90, 60)
    LIZARD_BELLY = (180, 190, 150)
    SKIN = (210, 175, 145)       # yordle skin
    FUR = (200, 180, 150)        # wild facial hair
    ARMOR = (140, 60, 55)        # tattered Noxian red armor
    ARMOR_DARK = (90, 35, 30)
    STEEL = (120, 115, 110)      # scrap metal
    SWORD = (180, 180, 190)      # scrap-metal sword
    SWORD_DARK = (100, 95, 90)
    EYE = (220, 80, 60)          # manic red eyes
    OUT = (30, 25, 20)

    # --- SKAAARL THE LIZARD (THE feature — big long mount, low body) ---
    # lizard body (big, horizontal, low-slung)
    P.append({"type":"ellipse","x":40,"y":140,"w":160,"h":56,"color":LIZARD,"outline":OUT,"outline_w":2})
    # lizard belly (lighter)
    P.append({"type":"ellipse","x":56,"y":158,"w":128,"h":26,"color":LIZARD_BELLY,"outline":OUT,"outline_w":1})
    # lizard back scales (ridge)
    for sx in (64,88,112,136,160):
        P.append({"type":"polygon","points":[(sx-6,128),(sx+6,128),(sx,116)],"color":LIZARD_DARK,"outline":OUT,"outline_w":1})

    # --- Lizard head (front, right — long snout) ---
    P.append({"type":"circle","cx":200,"cy":160,"r":22,"color":LIZARD,"outline":OUT,"outline_w":2})
    # long lizard snout
    P.append({"type":"polygon","points":[(196,154),(238,162),(238,172),(196,168)],
              "color":LIZARD,"outline":OUT,"outline_w":1})
    # snout tip
    P.append({"type":"polygon","points":[(232,164),(248,166),(232,170)],"color":LIZARD_DARK,"outline":OUT,"outline_w":1})
    # nostril
    P.append({"type":"circle","cx":228,"cy":164,"r":2,"color":OUT})
    # lizard eye (yellow, slit)
    P.append({"type":"circle","cx":194,"cy":154,"r":5,"color":(220,200,80),"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[194,150],"end":[194,158],"color":OUT,"width":1})
    # lizard teeth (sharp)
    for tx in (210,218,226):
        P.append({"type":"polygon","points":[(tx-2,168),(tx+2,168),(tx,174)],"color":(240,235,220),"outline":OUT,"outline_w":1})

    # --- Lizard legs (4, splayed with claws) ---
    for lx in (68,100,150,180):
        P.append({"type":"rect","x":lx-7,"y":190,"w":14,"h":24,"color":LIZARD_DARK,"outline":OUT,"outline_w":1,"radius":3})
        # claws
        for cx in (lx-4,lx,lx+4):
            P.append({"type":"line","start":[cx,214],"end":[cx,222],"color":(240,235,220),"width":2})

    # --- Lizard tail (left, long, curving) ---
    tail = [(48,160),(32,150),(22,130),(24,108),(36,96)]
    for i in range(len(tail)-1):
        P.append({"type":"line","start":tail[i],"end":tail[i+1],"color":LIZARD,"width":10})
    for cx,cy in tail:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":5,"color":LIZARD,"outline":LIZARD_DARK,"outline_w":1})

    # --- KLED (small yordle rider on top of Skaarl — BIGGER, clearer) ---
    # rider body (tattered Noxian red armor — BIGGER)
    P.append({"type":"polygon","points":[(108,92),(148,92),(152,142),(104,142)],
              "color":ARMOR,"outline":OUT,"outline_w":1})
    # tattered armor straps (steel — visible tattered Noxian armor)
    P.append({"type":"rect","x":104,"y":112,"w":48,"h":5,"color":STEEL,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":104,"y":126,"w":48,"h":5,"color":STEEL,"outline":OUT,"outline_w":1})
    # tattered edges (jagged bottom of armor = tattered look)
    for tx in (108,118,128,138,148):
        P.append({"type":"polygon","points":[(tx-4,142),(tx+4,142),(tx,148)],"color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    # scrap metal plate on chest (Noxian emblem)
    P.append({"type":"polygon","points":[(116,100),(140,100),(138,128),(118,128)],
              "color":STEEL,"outline":OUT,"outline_w":1})
    # Noxian emblem (red)
    P.append({"type":"circle","cx":128,"cy":114,"r":5,"color":ARMOR,"outline":OUT,"outline_w":1})

    # --- Kled head (BIGGER, wild — make rider read clearly) ---
    P.append({"type":"circle","cx":128,"cy":78,"r":18,"color":SKIN,"outline":OUT,"outline_w":1})
    # WILD FACIAL HAIR (THE missing feature — BIG bushy mustache + sideburns, prominent)
    P.append({"type":"polygon","points":[(110,84),(146,84),(144,102),(112,102)],
              "color":FUR,"outline":OUT,"outline_w":1})
    # BIG bushy mustache (the icon of his face)
    P.append({"type":"polygon","points":[(112,90),(144,90),(142,100),(114,100)],"color":FUR,"outline":OUT,"outline_w":1})
    # mustache texture (wild strands)
    for mx in (116,124,132,140):
        P.append({"type":"line","start":[mx,90],"end":[mx,98],"color":ARMOR_DARK,"width":1})
    # big sideburns (wild facial hair)
    P.append({"type":"polygon","points":[(110,80),(116,80),(114,96),(110,94)],"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(140,80),(146,80),(146,94),(142,96)],"color":FUR,"outline":OUT,"outline_w":1})
    # manic eyes (red, wild — BIGGER)
    P.append({"type":"circle","cx":121,"cy":78,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":78,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    # eye glow (manic)
    P.append({"type":"circle","cx":121,"cy":77,"r":2,"color":(255,150,120),"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":135,"cy":77,"r":2,"color":(255,150,120),"outline":None,"outline_w":0})
    # manic grin (wide, crazy)
    P.append({"type":"polygon","points":[(118,88),(138,88),(136,94),(120,94)],"color":OUT,"outline":None,"outline_w":0})
    # wild hair top (bushy, sticking up)
    P.append({"type":"polygon","points":[(110,66),(146,66),(142,54),(116,54)],"color":FUR,"outline":OUT,"outline_w":1})
    # wild hair tufts (sticking up crazily)
    for hx in (116,124,132,140):
        P.append({"type":"polygon","points":[(hx-3,54),(hx+3,54),(hx,46)],"color":FUR,"outline":OUT,"outline_w":1})
    # scrap-metal helmet (Noxian)
    P.append({"type":"polygon","points":[(110,64),(146,64),(142,52),(116,52)],"color":STEEL,"outline":OUT,"outline_w":1})
    # helmet spike (Noxian)
    P.append({"type":"polygon","points":[(126,52),(130,52),(128,42)],"color":STEEL,"outline":OUT,"outline_w":1})

    # --- Rider arms (holding sword — BIGGER) ---
    P.append({"type":"rect","x":96,"y":100,"w":14,"h":36,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":146,"y":100,"w":14,"h":36,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":103,"cy":138,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":153,"cy":138,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- SCRAP-METAL SWORD (THE missing feature — held up) ---
    P.append({"type":"line","start":[150,138],"end":[178,80],"color":SWORD,"width":5})
    P.append({"type":"line","start":[150,138],"end":[178,80],"color":SWORD_DARK,"width":1})
    # sword edge (jagged = scrap metal)
    P.append({"type":"polygon","points":[(170,98),(176,96),(174,104)],"color":SWORD_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(162,116),(168,114),(166,122)],"color":SWORD_DARK,"outline":OUT,"outline_w":1})
    # sword hilt (scrap)
    P.append({"type":"rect","x":144,"y":134,"w":12,"h":8,"color":STEEL,"outline":OUT,"outline_w":1,"radius":2})
    # sword tip
    P.append({"type":"polygon","points":[(176,82),(184,74),(180,90)],"color":SWORD,"outline":SWORD_DARK,"outline_w":1})

    return P


# ============================================================
# RUN ALL 6 SEQUENTIALLY
# ============================================================
CHAMPS = [
    ("Jinx", jinx_prims, "extremely long blue braided pigtails + minigun"),
    ("KSante", ksante_prims, "large ornate shoulder guards + Ntofo mace"),
    ("Karma", karma_prims, "floating mantra scrolls + Ionian robes"),
    ("Kayle", kayle_prims, "large white wings + halo + golden armor"),
    ("Khazix", khazix_prims, "scythe claws + chitinous exoskeleton + purple eyes"),
    ("Kled", kled_prims, "Skaarl lizard mount + Noxian armor + wild facial hair"),
]

if __name__ == "__main__":
    results = []
    for cid, fn, feat in CHAMPS:
        print(f"\n{'='*60}\n{cid} — {feat}\n{'='*60}", flush=True)
        prims = fn()
        prims = [p for p in prims if isinstance(p, dict) and "type" in p]
        try:
            r = improve(cid, prims, gate_n=3)
            print(f"RESULT {cid}: old={r['old']} new={r['new']} saved={r['saved']} "
                  f"verdict={r['verdict']} missing={r['missing'][:4]}", flush=True)
            results.append({"id":cid,"old":r["old"],"new":r["new"],"saved":r["saved"],
                            "rounds":1,"missing_final":r["missing"][:4],"feature":feat})
        except Exception as e:
            print(f"ERROR {cid}: {e}", flush=True)
            results.append({"id":cid,"old":5,"new":0,"saved":False,"rounds":1,
                            "missing_final":[str(e)],"feature":feat})
        time.sleep(2)
    print("\n\n=== FINAL RESULTS ===")
    print(json.dumps(results, indent=2))
    improved = sum(1 for r in results if r["new"] > r["old"])
    ge8 = sum(1 for r in results if r["new"] >= 8)
    print(f"\n{improved}/6 champs improved, {ge8} reached >=8.")
