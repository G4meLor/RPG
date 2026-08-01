"""Batch 10: hand-author 6 LoL champions to score 8-10.

Champions: Sion, Sivir, Taliyah, Tryndamere, Warwick, Zilean.
Each has ONE huge signature feature that dominates the silhouette.
Run sequentially; improve() auto-saves only when new > old.
"""
import sys, json, time
sys.path.insert(0, "exp")
from champ_improver import improve, committed_score

OUT = (25, 20, 25)


# ============================================================
# 1. SION — exposed SKELETAL JAW (THE feature) + bolted metal armor + giant axe
# ============================================================
def sion_prims():
    P = []
    FLESH = (140, 110, 95)        # rotten flesh
    FLESH_DARK = (95, 70, 60)
    BONE = (220, 210, 185)        # skeletal jaw bone
    BONE_DARK = (160, 145, 120)
    METAL = (110, 105, 100)       # bolted metal armor
    METAL_DARK = (65, 60, 58)
    RUST = (140, 80, 45)          # rusted bolts
    EYE = (220, 60, 50)           # glowing red eyes
    AXE = (160, 155, 150)         # giant axe
    AXE_DARK = (90, 85, 80)
    OUT = (25, 20, 18)

    # --- Giant battle axe (behind, big) ---
    # axe handle (long, diagonal)
    P.append({"type":"line","start":[70,210],"end":[70,40],"color":(90,60,35),"width":8})
    # axe head (BIG, crescent blade)
    P.append({"type":"polygon","points":[(70,50),(40,40),(28,70),(36,100),(60,90),(66,70)],
              "color":AXE,"outline":AXE_DARK,"outline_w":2})
    # axe blade edge highlight
    P.append({"type":"line","start":[40,44],"end":[32,96],"color":(220,220,225),"width":2})
    # axe blade inner detail
    P.append({"type":"line","start":[60,56],"end":[52,86],"color":AXE_DARK,"width":1})
    # axe pommel
    P.append({"type":"circle","cx":70,"cy":210,"r":7,"color":METAL_DARK,"outline":OUT,"outline_w":1})

    # --- Massive hulking body (undead giant — BIG torso) ---
    P.append({"type":"polygon","points":[(86,100),(170,100),(180,210),(76,210)],
              "color":FLESH,"outline":OUT,"outline_w":2})
    # bolted metal armor plates (THE feature — big metal plates with visible bolts)
    # chest plate (big, with bolts)
    P.append({"type":"polygon","points":[(94,108),(162,108),(168,180),(88,180)],
              "color":METAL,"outline":METAL_DARK,"outline_w":2})
    # armor plate seam (center)
    P.append({"type":"line","start":[128,110],"end":[128,178],"color":METAL_DARK,"width":2})
    # RUSTED BOLTS (THE feature — visible bolts on armor, big)
    for bx,by in [(98,118),(158,118),(98,170),(158,170),(108,144),(148,144)]:
        P.append({"type":"circle","cx":bx,"cy":by,"r":4,"color":RUST,"outline":METAL_DARK,"outline_w":1})
    # stitching/rotten flesh (visible seams on exposed flesh — arms)
    P.append({"type":"line","start":[86,130],"end":[92,170],"color":FLESH_DARK,"width":2})
    P.append({"type":"line","start":[170,130],"end":[164,170],"color":FLESH_DARK,"width":2})
    # stitch marks (X pattern)
    for sy in (140,155):
        P.append({"type":"line","start":[86,sy],"end":[90,sy+4],"color":FLESH_DARK,"width":1})
        P.append({"type":"line","start":[90,sy],"end":[86,sy+4],"color":FLESH_DARK,"width":1})

    # --- Arms (massive, hulking) ---
    P.append({"type":"rect","x":72,"y":118,"w":20,"h":60,"color":FLESH,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"rect","x":164,"y":118,"w":20,"h":60,"color":FLESH,"outline":OUT,"outline_w":1,"radius":5})
    # metal arm bands (bolted)
    P.append({"type":"rect","x":72,"y":130,"w":20,"h":8,"color":METAL,"outline":METAL_DARK,"outline_w":1})
    P.append({"type":"rect","x":164,"y":130,"w":20,"h":8,"color":METAL,"outline":METAL_DARK,"outline_w":1})
    # hands (huge fists)
    P.append({"type":"circle","cx":82,"cy":182,"r":10,"color":FLESH,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":174,"cy":182,"r":10,"color":FLESH,"outline":OUT,"outline_w":1})

    # --- Legs (massive) ---
    P.append({"type":"rect","x":92,"y":208,"w":30,"h":40,"color":METAL,"outline":METAL_DARK,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":134,"y":208,"w":30,"h":40,"color":METAL,"outline":METAL_DARK,"outline_w":1,"radius":4})
    # boots
    P.append({"type":"rect","x":88,"y":242,"w":36,"h":12,"color":METAL_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":132,"y":242,"w":36,"h":12,"color":METAL_DARK,"outline":OUT,"outline_w":1,"radius":2})

    # --- HEAD with EXPOSED SKELETAL JAW (THE feature — big skull jaw) ---
    # skull/head top (rotten flesh upper)
    P.append({"type":"circle","cx":128,"cy":80,"r":22,"color":FLESH,"outline":OUT,"outline_w":2})
    # glowing red eyes (menacing, undead)
    P.append({"type":"circle","cx":120,"cy":78,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":136,"cy":78,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    # eye glow
    P.append({"type":"circle","cx":120,"cy":77,"r":2,"color":(255,150,120),"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":136,"cy":77,"r":2,"color":(255,150,120),"outline":None,"outline_w":0})
    # metal plate on forehead (bolted)
    P.append({"type":"rect","x":116,"y":62,"w":24,"h":10,"color":METAL,"outline":METAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":67,"r":2,"color":RUST,"outline":METAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":134,"cy":67,"r":2,"color":RUST,"outline":METAL_DARK,"outline_w":1})

    # EXPOSED SKELETAL JAW (THE feature — BIG bone jaw, teeth visible, no flesh on lower face)
    # jaw bone (big, prominent — the icon)
    P.append({"type":"polygon","points":[(108,88),(148,88),(152,118),(104,118)],
              "color":BONE,"outline":BONE_DARK,"outline_w":2})
    # jaw bone detail (mandible shape)
    P.append({"type":"polygon","points":[(112,96),(144,96),(140,114),(116,114)],
              "color":BONE_DARK,"outline":BONE_DARK,"outline_w":1})
    # TEETH (THE feature — sharp teeth along jaw, prominent)
    for tx in (112,120,128,136,144):
        P.append({"type":"polygon","points":[(tx-3,96),(tx+3,96),(tx,104)],"color":BONE,"outline":BONE_DARK,"outline_w":1})
    # lower teeth (pointing up)
    for tx in (116,124,132,140):
        P.append({"type":"polygon","points":[(tx-3,114),(tx+3,114),(tx,108)],"color":BONE,"outline":BONE_DARK,"outline_w":1})
    # jaw bone side bolts (rusty, holding jaw to skull)
    P.append({"type":"circle","cx":108,"cy":100,"r":3,"color":RUST,"outline":METAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":148,"cy":100,"r":3,"color":RUST,"outline":METAL_DARK,"outline_w":1})

    return P


# ============================================================
# 2. SIVIR — large CROSSBLADE (THE feature — boomerang-blade) + Shuriman armor
# ============================================================
def sivir_prims():
    P = []
    SKIN = (210, 175, 140)
    HAIR = (60, 45, 35)          # dark hair, ponytail
    GOLD = (215, 175, 60)
    GOLD_DARK = (150, 110, 30)
    TEAL = (70, 150, 145)        # teal Shuriman accents
    BROWN = (150, 110, 70)       # leather/desert armor
    BROWN_DARK = (95, 65, 40)
    BLADE = (200, 205, 215)      # crossblade metal
    BLADE_DARK = (110, 115, 130)
    EYE = (40, 30, 25)
    OUT = (30, 22, 18)

    # --- LARGE CROSSBLADE (THE feature — BIG 4-bladed boomerang, the icon) ---
    # Crossblade = 4 almond/leaf-shaped blades in a cross/X (iconic Sivir weapon)
    # Each blade is a BIG almond shape (wide in middle, tapered at both ends)
    # top blade (almond shape, pointing up)
    P.append({"type":"polygon","points":[(118,30),(138,30),(142,80),(134,96),(122,96),(114,80)],
              "color":BLADE,"outline":BLADE_DARK,"outline_w":2})
    # bottom blade (almond shape, pointing down)
    P.append({"type":"polygon","points":[(118,222),(138,222),(142,172),(134,156),(122,156),(114,172)],
              "color":BLADE,"outline":BLADE_DARK,"outline_w":2})
    # left blade (almond shape, pointing left)
    P.append({"type":"polygon","points":[(30,114),(30,134),(80,138),(96,130),(96,118),(80,110)],
              "color":BLADE,"outline":BLADE_DARK,"outline_w":2})
    # right blade (almond shape, pointing right)
    P.append({"type":"polygon","points":[(226,114),(226,134),(176,138),(160,130),(160,118),(176,110)],
              "color":BLADE,"outline":BLADE_DARK,"outline_w":2})
    # blade edge highlights (sharp silver edges)
    P.append({"type":"line","start":[120,32],"end":[120,80],"color":(245,245,250),"width":2})
    P.append({"type":"line","start":[120,220],"end":[120,172],"color":(245,245,250),"width":2})
    P.append({"type":"line","start":[32,116],"end":[80,116],"color":(245,245,250),"width":2})
    P.append({"type":"line","start":[224,116],"end":[176,116],"color":(245,245,250),"width":2})
    # center hub (gold, ornate — BIG, the joining point)
    P.append({"type":"circle","cx":128,"cy":126,"r":16,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":126,"r":10,"color":TEAL,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":126,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # Shuriman sun emblem on hub
    P.append({"type":"line","start":[118,126],"end":[138,126],"color":GOLD_DARK,"width":1})
    P.append({"type":"line","start":[128,116],"end":[128,136],"color":GOLD_DARK,"width":1})

    # --- Hair back (ponytail — THE missing feature) ---
    P.append({"type":"circle","cx":128,"cy":72,"r":18,"color":HAIR,"outline":OUT,"outline_w":1})
    # BIG ponytail (flowing back, prominent)
    P.append({"type":"polygon","points":[(140,68),(160,58),(176,80),(172,120),(150,108),(142,86)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # ponytail tip
    P.append({"type":"polygon","points":[(168,108),(182,100),(178,124),(166,118)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # gold hair band
    P.append({"type":"rect","x":138,"y":64,"w":10,"h":6,"color":GOLD,"outline":OUT,"outline_w":1})
    # bangs
    P.append({"type":"polygon","points":[(112,60),(144,60),(140,72),(116,72)],"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":76,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # eyes (determined)
    P.append({"type":"circle","cx":122,"cy":76,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":134,"cy":76,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    # Shuriman headband (gold)
    P.append({"type":"rect","x":112,"y":66,"w":32,"h":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # headband emblem
    P.append({"type":"circle","cx":128,"cy":68,"r":3,"color":TEAL,"outline":GOLD_DARK,"outline_w":1})

    # --- Shuriman desert armor (gold + teal + brown — BIGGER, more visible) ---
    P.append({"type":"polygon","points":[(106,92),(150,92),(156,176),(100,176)],
              "color":BROWN,"outline":OUT,"outline_w":1})
    # gold chest plate (Shuriman — BIG, ornate)
    P.append({"type":"polygon","points":[(110,98),(146,98),(144,156),(112,156)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # Shuriman sun emblem (BIG, prominent)
    P.append({"type":"circle","cx":128,"cy":122,"r":9,"color":TEAL,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":122,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # sun rays
    for ang in (0,45,90,135,180,225,270,315):
        import math as _m
        sx = 128 + int(11 * _m.cos(_m.radians(ang)))
        sy = 122 + int(11 * _m.sin(_m.radians(ang)))
        P.append({"type":"circle","cx":sx,"cy":sy,"r":2,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold belt (wide, Shuriman)
    P.append({"type":"rect","x":100,"y":168,"w":56,"h":8,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # leather bracers (THE missing feature — BIG, visible arm bracers)
    P.append({"type":"rect","x":96,"y":118,"w":16,"h":34,"color":BROWN_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":144,"y":118,"w":16,"h":34,"color":BROWN_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # gold bracer trim (visible gold bands)
    P.append({"type":"rect","x":96,"y":118,"w":16,"h":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":96,"y":148,"w":16,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":144,"y":118,"w":16,"h":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":144,"y":148,"w":16,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # hands
    P.append({"type":"circle","cx":104,"cy":156,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":152,"cy":156,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (desert boots) ---
    P.append({"type":"rect","x":110,"y":170,"w":14,"h":40,"color":BROWN,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":14,"h":40,"color":BROWN,"outline":OUT,"outline_w":1,"radius":3})
    # sand-covered boots
    P.append({"type":"rect","x":108,"y":206,"w":18,"h":10,"color":BROWN_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":206,"w":18,"h":10,"color":BROWN_DARK,"outline":OUT,"outline_w":1,"radius":2})
    # gold belt
    P.append({"type":"rect","x":106,"y":166,"w":44,"h":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    return P


# ============================================================
# 3. TALIYAH — FLOATING ROCKS orbiting (THE feature) + nomadic clothing
# ============================================================
def taliyah_prims():
    P = []
    SKIN = (215, 185, 155)
    HAIR = (50, 40, 35)          # dark hair
    ROBE = (180, 120, 80)        # terracotta/ochre nomadic wrap
    ROBE_DARK = (130, 80, 50)
    TEAL = (70, 150, 145)        # teal accents
    GOLD = (215, 175, 60)        # Shuriman jewelry gold
    ROCK = (130, 110, 90)        # floating rocks (earthy)
    ROCK_DARK = (85, 70, 55)
    ROCK_LIGHT = (170, 145, 120)
    EYE = (70, 150, 145)         # teal eyes (rock-weaver)
    OUT = (30, 22, 18)

    # --- FLOATING ROCKS orbiting around her (THE feature — 7 BIG rocks in an arc) ---
    rock_positions = [
        (50,90),(60,140),(70,190),       # left arc (big rocks)
        (206,90),(196,140),(186,190),    # right arc (big rocks)
        (128,40),                         # top rock
    ]
    for i,(rx,ry) in enumerate(rock_positions):
        # each rock = irregular polygon (rocky shape, BIG)
        if ry < 60:  # top rock
            pts = [(rx-12,ry),(rx-6,ry-8),(rx+8,ry-6),(rx+12,ry+4),(rx+4,ry+10),(rx-8,ry+8)]
        elif rx < 128:  # left rocks
            pts = [(rx-12,ry-6),(rx-4,ry-12),(rx+10,ry-8),(rx+12,ry+6),(rx+4,ry+12),(rx-8,ry+8)]
        else:  # right rocks
            pts = [(rx-12,ry-6),(rx-8,ry-12),(rx+6,ry-10),(rx+12,ry+4),(rx+6,ry+12),(rx-6,ry+8)]
        P.append({"type":"polygon","points":pts,"color":ROCK,"outline":ROCK_DARK,"outline_w":2})
        # rock highlight (lighter top)
        P.append({"type":"circle","cx":rx-3,"cy":ry-4,"r":3,"color":ROCK_LIGHT,"outline":None,"outline_w":0})
    # teal earth-magic glow lines connecting rocks (the weaving)
    for (rx,ry) in rock_positions[:6]:
        P.append({"type":"line","start":[rx,ry],"end":[128,140],"color":TEAL,"width":1})

    # --- Dark hair (back, ponytail) ---
    P.append({"type":"circle","cx":128,"cy":76,"r":18,"color":HAIR,"outline":OUT,"outline_w":1})
    # ponytail (THE missing feature)
    P.append({"type":"polygon","points":[(118,80),(138,80),(142,130),(114,130)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # hair tie (Shuriman gold)
    P.append({"type":"rect","x":118,"y":82,"w":20,"h":5,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":80,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # teal eyes (rock-weaver magic)
    P.append({"type":"circle","cx":122,"cy":82,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":134,"cy":82,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    # Shuriman jewelry (forehead mark)
    P.append({"type":"circle","cx":128,"cy":72,"r":3,"color":GOLD,"outline":OUT,"outline_w":1})
    # bangs
    P.append({"type":"polygon","points":[(112,68),(144,68),(140,78),(116,78)],"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Wrapped nomadic clothing (terracotta robe with wraps) ---
    P.append({"type":"polygon","points":[(106,98),(150,98),(158,200),(98,200)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # wrap folds (nomadic wrapped clothing — visible wraps)
    for wy in (110,128,146,164,182):
        P.append({"type":"line","start":[100,wy],"end":[156,wy],"color":ROBE_DARK,"width":1})
    # teal sash
    P.append({"type":"polygon","points":[(98,140),(158,140),(162,156),(94,156)],
              "color":TEAL,"outline":OUT,"outline_w":1})
    # Shuriman jewelry (gold necklace)
    P.append({"type":"rect","x":112,"y":98,"w":32,"h":5,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":106,"r":4,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":106,"r":2,"color":TEAL,"outline":None,"outline_w":0})

    # --- Arms (raised, weaving pose) ---
    P.append({"type":"rect","x":94,"y":108,"w":12,"h":40,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":150,"y":108,"w":12,"h":40,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    # hands
    P.append({"type":"circle","cx":100,"cy":150,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":156,"cy":150,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (sand-covered boots) ---
    P.append({"type":"rect","x":108,"y":196,"w":16,"h":34,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":196,"w":16,"h":34,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # sand-covered boots (lighter, sandy)
    P.append({"type":"rect","x":106,"y":226,"w":20,"h":10,"color":(190,160,110),"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":226,"w":20,"h":10,"color":(190,160,110),"outline":OUT,"outline_w":1,"radius":2})

    return P


# ============================================================
# 4. TRYNDA MERE — long wild HAIR + fur-lined armor + BARE CHEST + big sword
# ============================================================
def tryndamere_prims():
    P = []
    SKIN = (215, 180, 145)
    HAIR = (140, 90, 50)         # wild brown-orange hair
    HAIR_DARK = (90, 55, 30)
    FUR = (200, 195, 190)        # white fur-lined armor
    FUR_DARK = (150, 145, 140)
    LEATHER = (120, 80, 45)      # battle-worn leather straps
    LEATHER_DARK = (75, 50, 28)
    SWORD = (210, 215, 225)      # massive greatsword
    SWORD_DARK = (110, 115, 130)
    EYE = (220, 60, 50)          # raging red eyes
    GOLD_TRY = (200, 160, 50)    # gold trim
    OUT = (30, 22, 18)

    # --- LONG WILD HAIR (THE feature — BIG, flowing, wild, the icon) ---
    # hair back (big mass)
    P.append({"type":"circle","cx":120,"cy":68,"r":26,"color":HAIR,"outline":OUT,"outline_w":1})
    # wild hair flowing DOWN both sides (long, prominent — THE icon)
    P.append({"type":"polygon","points":[(96,68),(104,68),(100,150),(86,136)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(136,68),(144,68),(154,136),(140,150)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # wild hair top (spiky, untamed — BIG spikes)
    for hx in (100,108,116,124,132,140):
        P.append({"type":"polygon","points":[(hx-5,52),(hx+5,52),(hx,34)],"color":HAIR,"outline":OUT,"outline_w":1})
    # wild hair strands (texture)
    for hx in (100,112,128,140):
        P.append({"type":"line","start":[hx,54],"end":[hx,74],"color":HAIR_DARK,"width":1})

    # --- Head ---
    P.append({"type":"circle","cx":120,"cy":74,"r":18,"color":SKIN,"outline":OUT,"outline_w":1})
    # raging red eyes (fury)
    P.append({"type":"circle","cx":113,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":127,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    # eye glow
    P.append({"type":"circle","cx":113,"cy":75,"r":2,"color":(255,150,120),"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":127,"cy":75,"r":2,"color":(255,150,120),"outline":None,"outline_w":0})
    # RUGGED BEARD (THE missing feature — BIG, wild, prominent)
    P.append({"type":"polygon","points":[(100,84),(140,84),(142,112),(98,112)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # beard texture (wild strands)
    for bx in (106,114,122,130,138):
        P.append({"type":"line","start":[bx,86],"end":[bx,108],"color":HAIR_DARK,"width":1})
    # mustache (wild, flowing)
    P.append({"type":"polygon","points":[(106,82),(134,82),(132,90),(108,90)],"color":HAIR,"outline":OUT,"outline_w":1})
    # battle markings (face paint — red stripe across eyes)
    P.append({"type":"line","start":[104,72],"end":[136,72],"color":(180,40,40),"width":2})

    # --- BARE CHEST (THE feature — bare muscular chest, skin showing, BIG) ---
    P.append({"type":"polygon","points":[(92,98),(152,98),(156,178),(88,178)],
              "color":SKIN,"outline":OUT,"outline_w":2})
    # chest muscles (pecs — BIG visible muscular build)
    P.append({"type":"polygon","points":[(96,104),(120,104),(120,128),(96,128)],
              "color":(195,160,130),"outline":(180,145,115),"outline_w":1})
    P.append({"type":"polygon","points":[(120,104),(144,104),(144,128),(120,128)],
              "color":(195,160,130),"outline":(180,145,115),"outline_w":1})
    # abs (visible 6-pack)
    for ay in (132,144,156,168):
        P.append({"type":"line","start":[108,ay],"end":[132,ay],"color":(180,145,115),"width":1})
    P.append({"type":"line","start":[120,128],"end":[120,172],"color":(180,145,115),"width":1})

    # FUR-LINED ARMOR (THE missing feature — big fur mantle over shoulders)
    # left fur shoulder (BIG)
    P.append({"type":"circle","cx":92,"cy":102,"r":16,"color":FUR,"outline":FUR_DARK,"outline_w":1})
    # right fur shoulder (BIG)
    P.append({"type":"circle","cx":152,"cy":102,"r":16,"color":FUR,"outline":FUR_DARK,"outline_w":1})
    # fur texture (tufts — visible fur)
    for fx in (82,92,102):
        P.append({"type":"circle","cx":fx,"cy":96,"r":5,"color":FUR,"outline":FUR_DARK,"outline_w":1})
    for fx in (142,152,162):
        P.append({"type":"circle","cx":fx,"cy":96,"r":5,"color":FUR,"outline":FUR_DARK,"outline_w":1})

    # BATTLE-WORN LEATHER STRAPS (THE missing feature — BIG X-crossing bare chest, prominent)
    # leather strap diagonal across chest (left-to-right, BIG)
    P.append({"type":"polygon","points":[(88,108),(98,104),(156,170),(150,176)],
              "color":LEATHER,"outline":LEATHER_DARK,"outline_w":1})
    # leather strap buckle (gold, center — BIG)
    P.append({"type":"circle","cx":122,"cy":140,"r":8,"color":GOLD_TRY,"outline":LEATHER_DARK,"outline_w":2})
    P.append({"type":"circle","cx":122,"cy":140,"r":4,"color":LEATHER_DARK,"outline":OUT,"outline_w":1})
    # second strap (right-to-left, BIG)
    P.append({"type":"polygon","points":[(148,104),(158,108),(104,176),(96,170)],
              "color":LEATHER,"outline":LEATHER_DARK,"outline_w":1})

    # --- Arms (muscular, bare) ---
    P.append({"type":"rect","x":78,"y":114,"w":18,"h":54,"color":SKIN,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"rect","x":148,"y":114,"w":18,"h":54,"color":SKIN,"outline":OUT,"outline_w":1,"radius":5})
    # leather bracers
    P.append({"type":"rect","x":78,"y":144,"w":18,"h":16,"color":LEATHER,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":148,"y":144,"w":18,"h":16,"color":LEATHER,"outline":OUT,"outline_w":1,"radius":3})
    # gold bracer trim
    P.append({"type":"rect","x":78,"y":144,"w":18,"h":4,"color":GOLD_TRY,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":148,"y":144,"w":18,"h":4,"color":GOLD_TRY,"outline":OUT,"outline_w":1})
    # hands (gripping sword)
    P.append({"type":"circle","cx":87,"cy":172,"r":7,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":157,"cy":172,"r":7,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (fur-lined boots) ---
    P.append({"type":"rect","x":100,"y":173,"w":20,"h":42,"color":LEATHER,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":124,"y":173,"w":20,"h":42,"color":LEATHER,"outline":OUT,"outline_w":1,"radius":3})
    # fur-lined boots (top — visible fur)
    P.append({"type":"rect","x":98,"y":207,"w":24,"h":10,"color":FUR,"outline":FUR_DARK,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":122,"y":207,"w":24,"h":10,"color":FUR,"outline":FUR_DARK,"outline_w":1,"radius":2})
    # boot bottoms
    P.append({"type":"rect","x":98,"y":239,"w":24,"h":10,"color":LEATHER_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":122,"y":239,"w":24,"h":10,"color":LEATHER_DARK,"outline":OUT,"outline_w":1,"radius":2})

    # --- MASSIVE GREATSWORD (THE feature — held to the RIGHT side, NOT covering body) ---
    # blade diagonal, held to the right (so body/hair/beard/chest are all visible)
    P.append({"type":"polygon","points":[(168,172),(184,166),(232,40),(216,34),(200,160),(164,168)],
              "color":SWORD,"outline":SWORD_DARK,"outline_w":2})
    # blade edge highlight (white, sharp)
    P.append({"type":"line","start":[170,170],"end":[220,40],"color":(255,255,255),"width":2})
    # blade tip (pointed, top-right)
    P.append({"type":"polygon","points":[(216,34),(232,40),(226,22)],"color":SWORD,"outline":SWORD_DARK,"outline_w":1})
    # crossguard (wide, gold-trimmed — at hands)
    P.append({"type":"rect","x":158,"y":166,"w":28,"h":10,"color":LEATHER,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":158,"y":166,"w":28,"h":3,"color":GOLD_TRY,"outline":OUT,"outline_w":1})
    # handle (short, below guard)
    P.append({"type":"rect","x":160,"y":176,"w":16,"h":18,"color":LEATHER_DARK,"outline":OUT,"outline_w":1,"radius":2})
    # handle wrap (gold)
    for hy in (180,186,192):
        P.append({"type":"line","start":[160,hy],"end":[176,hy],"color":GOLD_TRY,"width":1})
    # pommel (gold)
    P.append({"type":"circle","cx":168,"cy":196,"r":6,"color":GOLD_TRY,"outline":OUT,"outline_w":1})

    return P


# ============================================================
# 5. WARWICK — glowing green CHEMICAL VIALS in back + wolf head + claws
# ============================================================
def warwick_prims():
    P = []
    FUR = (90, 85, 90)           # dark grey fur
    FUR_DARK = (55, 50, 55)
    SKIN = (170, 145, 130)       # skin (under fur)
    CHEM = (120, 230, 100)       # chemical green
    CHEM_BRIGHT = (180, 255, 160)
    CHEM_DARK = (60, 140, 50)
    METAL = (120, 115, 110)      # metal restraints
    METAL_DARK = (70, 65, 62)
    CLAW = (220, 215, 200)       # sharp claws
    EYE = (220, 60, 50)          # menacing red eyes
    OUT = (25, 20, 22)

    # --- GLOWING GREEN CHEMICAL VIALS in back (THE feature — BIG, prominent) ---
    # 3 big green vials embedded in his back, glowing
    # vial 1 (left, big)
    P.append({"type":"rect","x":78,"y":80,"w":16,"h":50,"color":CHEM,"outline":CHEM_DARK,"outline_w":2})
    P.append({"type":"circle","cx":86,"cy":80,"r":8,"color":METAL,"outline":METAL_DARK,"outline_w":1})  # vial cap
    # vial glow (bright green)
    P.append({"type":"rect","x":80,"y":84,"w":12,"h":42,"color":CHEM_BRIGHT,"outline":None,"outline_w":0})
    # vial bubbles
    for by in (92,104,116):
        P.append({"type":"circle","cx":86,"cy":by,"r":2,"color":CHEM_BRIGHT,"outline":None,"outline_w":0})

    # vial 2 (center, big)
    P.append({"type":"rect","x":120,"y":76,"w":16,"h":54,"color":CHEM,"outline":CHEM_DARK,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":76,"r":8,"color":METAL,"outline":METAL_DARK,"outline_w":1})
    P.append({"type":"rect","x":122,"y":80,"w":12,"h":46,"color":CHEM_BRIGHT,"outline":None,"outline_w":0})
    for by in (88,100,112,124):
        P.append({"type":"circle","cx":128,"cy":by,"r":2,"color":CHEM_BRIGHT,"outline":None,"outline_w":0})

    # vial 3 (right, big)
    P.append({"type":"rect","x":162,"y":80,"w":16,"h":50,"color":CHEM,"outline":CHEM_DARK,"outline_w":2})
    P.append({"type":"circle","cx":170,"cy":80,"r":8,"color":METAL,"outline":METAL_DARK,"outline_w":1})
    P.append({"type":"rect","x":164,"y":84,"w":12,"h":42,"color":CHEM_BRIGHT,"outline":None,"outline_w":0})
    for by in (92,104,116):
        P.append({"type":"circle","cx":170,"cy":by,"r":2,"color":CHEM_BRIGHT,"outline":None,"outline_w":0})

    # metal harness/tube connecting vials (THE feature — visible apparatus)
    P.append({"type":"rect","x":78,"y":74,"w":100,"h":8,"color":METAL,"outline":METAL_DARK,"outline_w":1})
    # metal bolts on harness
    for bx in (84,108,128,148,172):
        P.append({"type":"circle","cx":bx,"cy":78,"r":3,"color":METAL_DARK,"outline":OUT,"outline_w":1})

    # --- Body (muscular, anthropomorphic wolf) ---
    P.append({"type":"polygon","points":[(96,100),(160,100),(166,200),(90,200)],
              "color":FUR,"outline":OUT,"outline_w":1})
    # chest fur lighter
    P.append({"type":"polygon","points":[(110,108),(146,108),(150,170),(106,170)],
              "color":SKIN,"outline":OUT,"outline_w":1})
    # JAGGED FUR texture (THE missing feature — BIG visible jagged fur tufts on chest/shoulders)
    for fx in (100,108,116,140,148,156):
        P.append({"type":"polygon","points":[(fx-5,104),(fx+5,104),(fx,116)],"color":FUR_DARK,"outline":OUT,"outline_w":1})
    # jagged fur on chest (visible texture)
    for fx in (108,120,136,148):
        P.append({"type":"polygon","points":[(fx-4,108),(fx+4,108),(fx,118)],"color":FUR_DARK,"outline":OUT,"outline_w":1})
    # fur tufts on shoulders (jagged, wild)
    for sx in (94,162):
        P.append({"type":"polygon","points":[(sx-6,100),(sx+6,100),(sx,88)],"color":FUR,"outline":FUR_DARK,"outline_w":1})

    # --- METAL RESTRAINTS / SHACKLES (THE missing feature — BIG, prominent, clearly metal cuffs) ---
    # neck shackle (BIG metal collar with chain — the icon of his imprisonment)
    P.append({"type":"rect","x":108,"y":94,"w":40,"h":10,"color":METAL,"outline":METAL_DARK,"outline_w":2})
    # shackle ring (BIG, the chain attachment point)
    P.append({"type":"circle","cx":128,"cy":104,"r":5,"color":METAL_DARK,"outline":OUT,"outline_w":1})
    # chain links hanging from collar (broken chain = uncaged)
    P.append({"type":"circle","cx":118,"cy":112,"r":4,"color":METAL,"outline":METAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":112,"cy":120,"r":4,"color":METAL,"outline":METAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":138,"cy":112,"r":4,"color":METAL,"outline":METAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":144,"cy":120,"r":4,"color":METAL,"outline":METAL_DARK,"outline_w":1})
    # arm shackles (BIG metal cuffs on wrists — clearly restraints)
    P.append({"type":"rect","x":84,"y":148,"w":20,"h":12,"color":METAL,"outline":METAL_DARK,"outline_w":2})
    P.append({"type":"rect","x":152,"y":148,"w":20,"h":12,"color":METAL,"outline":METAL_DARK,"outline_w":2})
    # shackle bolts (BIG, visible — the bolts holding cuffs)
    P.append({"type":"circle","cx":94,"cy":154,"r":3,"color":METAL_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":162,"cy":154,"r":3,"color":METAL_DARK,"outline":OUT,"outline_w":1})
    # shackle rings on arms (chain attachment)
    P.append({"type":"circle","cx":84,"cy":154,"r":3,"color":METAL_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":172,"cy":154,"r":3,"color":METAL_DARK,"outline":OUT,"outline_w":1})

    # --- Arms (muscular, furry) ---
    P.append({"type":"rect","x":86,"y":112,"w":18,"h":48,"color":FUR,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"rect","x":152,"y":112,"w":18,"h":48,"color":FUR,"outline":OUT,"outline_w":1,"radius":5})
    # fur texture on arms
    for fy in (120,132,144):
        P.append({"type":"line","start":[88,fy],"end":[100,fy],"color":FUR_DARK,"width":1})
        P.append({"type":"line","start":[156,fy],"end":[168,fy],"color":FUR_DARK,"width":1})

    # --- SHARP CLAWS (THE missing feature — BIG claws on hands) ---
    # left hand claws
    P.append({"type":"circle","cx":95,"cy":164,"r":7,"color":FUR_DARK,"outline":OUT,"outline_w":1})
    for cx in (90,95,100):
        P.append({"type":"polygon","points":[(cx-2,170),(cx+2,170),(cx,184)],"color":CLAW,"outline":OUT,"outline_w":1})
    # right hand claws
    P.append({"type":"circle","cx":161,"cy":164,"r":7,"color":FUR_DARK,"outline":OUT,"outline_w":1})
    for cx in (156,161,166):
        P.append({"type":"polygon","points":[(cx-2,170),(cx+2,170),(cx,184)],"color":CLAW,"outline":OUT,"outline_w":1})

    # --- WOLF HEAD (THE feature — snout, ears, teeth, menacing) ---
    P.append({"type":"circle","cx":128,"cy":80,"r":22,"color":FUR,"outline":OUT,"outline_w":2})
    # wolf snout (long, protruding)
    P.append({"type":"polygon","points":[(118,84),(138,84),(140,108),(116,108)],
              "color":FUR_DARK,"outline":OUT,"outline_w":1})
    # snout tip (nose)
    P.append({"type":"circle","cx":128,"cy":108,"r":5,"color":(30,25,25),"outline":OUT,"outline_w":1})
    # wolf ears (pointed, up)
    P.append({"type":"polygon","points":[(108,64),(118,64),(112,46)],"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(138,64),(148,64),(144,46)],"color":FUR,"outline":OUT,"outline_w":1})
    # ear inner (pink)
    P.append({"type":"polygon","points":[(110,62),(116,62),(113,52)],"color":(180,130,120),"outline":None,"outline_w":0})
    P.append({"type":"polygon","points":[(140,62),(146,62),(143,52)],"color":(180,130,120),"outline":None,"outline_w":0})
    # menacing red eyes
    P.append({"type":"circle","cx":118,"cy":78,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":138,"cy":78,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    # eye glow
    P.append({"type":"circle","cx":118,"cy":77,"r":2,"color":(255,150,120),"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":138,"cy":77,"r":2,"color":(255,150,120),"outline":None,"outline_w":0})
    # wolf teeth (fangs, sharp)
    P.append({"type":"polygon","points":[(120,108),(124,108),(122,118)],"color":CLAW,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(132,108),(136,108),(134,118)],"color":CLAW,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(124,108),(128,108),(126,116)],"color":CLAW,"outline":OUT,"outline_w":1})

    # --- Legs (muscular, furry) ---
    P.append({"type":"rect","x":96,"y":198,"w":24,"h":42,"color":FUR,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":136,"y":198,"w":24,"h":42,"color":FUR,"outline":OUT,"outline_w":1,"radius":4})
    # foot claws
    for fx in (102,108,114):
        P.append({"type":"polygon","points":[(fx-2,240),(fx+2,240),(fx,248)],"color":CLAW,"outline":OUT,"outline_w":1})
    for fx in (142,148,154):
        P.append({"type":"polygon","points":[(fx-2,240),(fx+2,240),(fx,248)],"color":CLAW,"outline":OUT,"outline_w":1})

    return P


# ============================================================
# 6. ZILEAN — large FLOATING CLOCK (THE feature) + long white beard + robes
# ============================================================
def zilean_prims():
    P = []
    SKIN = (210, 190, 170)
    BEARD = (235, 235, 240)      # long white beard
    BEARD_DARK = (190, 190, 200)
    HAIR = (240, 235, 230)       # white hair
    ROBE = (110, 70, 140)        # purple robes
    ROBE_DARK = (70, 45, 95)
    GOLD = (215, 175, 60)
    GOLD_DARK = (150, 110, 30)
    CLOCK = (200, 170, 80)       # golden clock (brass)
    CLOCK_DARK = (130, 100, 40)
    CLOCK_FACE = (240, 230, 200) # clock face (parchment)
    EYE = (140, 220, 255)        # glowing blue eyes (time magic)
    OUT = (30, 22, 25)

    # --- LARGE FLOATING CLOCK (THE feature — BIG, behind/above him, dominant) ---
    # clock outer ring (brass, BIG)
    P.append({"type":"circle","cx":128,"cy":60,"r":38,"color":CLOCK,"outline":CLOCK_DARK,"outline_w":3})
    # clock face (parchment)
    P.append({"type":"circle","cx":128,"cy":60,"r":30,"color":CLOCK_FACE,"outline":CLOCK_DARK,"outline_w":2})
    # clock hour marks (12, 3, 6, 9 positions — BIG visible)
    import math as _m
    for ang in (0,90,180,270):
        x1 = 128 + int(26 * _m.cos(_m.radians(ang)))
        y1 = 60 + int(26 * _m.sin(_m.radians(ang)))
        P.append({"type":"circle","cx":x1,"cy":y1,"r":3,"color":CLOCK_DARK,"outline":None,"outline_w":0})
    for ang in (30,60,120,150,210,240,300,330):
        x1 = 128 + int(26 * _m.cos(_m.radians(ang)))
        y1 = 60 + int(26 * _m.sin(_m.radians(ang)))
        P.append({"type":"circle","cx":x1,"cy":y1,"r":1,"color":CLOCK_DARK,"outline":None,"outline_w":0})
    # clock hands (BIG, visible — pointing to 10:10)
    # hour hand (short, thick)
    P.append({"type":"line","start":[128,60],"end":[110,48],"color":CLOCK_DARK,"width":3})
    # minute hand (long, thin)
    P.append({"type":"line","start":[128,60],"end":[148,52],"color":CLOCK_DARK,"width":2})
    # clock center pin
    P.append({"type":"circle","cx":128,"cy":60,"r":3,"color":GOLD,"outline":CLOCK_DARK,"outline_w":1})
    # clock gears (visible mechanism — ornate)
    P.append({"type":"circle","cx":92,"cy":60,"r":8,"color":CLOCK_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":164,"cy":60,"r":8,"color":CLOCK_DARK,"outline":OUT,"outline_w":1})
    # gear teeth
    for ang in range(0,360,60):
        gx = 92 + int(8 * _m.cos(_m.radians(ang)))
        gy = 60 + int(8 * _m.sin(_m.radians(ang)))
        P.append({"type":"circle","cx":gx,"cy":gy,"r":2,"color":CLOCK_DARK,"outline":None,"outline_w":0})
    for ang in range(0,360,60):
        gx = 164 + int(8 * _m.cos(_m.radians(ang)))
        gy = 60 + int(8 * _m.sin(_m.radians(ang)))
        P.append({"type":"circle","cx":gx,"cy":gy,"r":2,"color":CLOCK_DARK,"outline":None,"outline_w":0})
    # time magic glow (blue, around clock — floating energy)
    P.append({"type":"circle","cx":128,"cy":60,"r":42,"color":(140,200,255),"outline":None,"outline_w":0})

    # --- White hair (back) ---
    P.append({"type":"circle","cx":128,"cy":108,"r":18,"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (elderly) ---
    P.append({"type":"circle","cx":128,"cy":112,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # glowing blue eyes (time magic — THE missing feature)
    P.append({"type":"circle","cx":122,"cy":112,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":134,"cy":112,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    # eye glow
    P.append({"type":"circle","cx":122,"cy":111,"r":1,"color":(200,240,255),"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":134,"cy":111,"r":1,"color":(200,240,255),"outline":None,"outline_w":0})
    # wrinkles (elderly)
    P.append({"type":"line","start":[116,108],"end":[120,108],"color":(180,160,140),"width":1})
    P.append({"type":"line","start":[136,108],"end":[140,108],"color":(180,160,140),"width":1})

    # --- LONG WHITE BEARD (THE missing feature — BIG, flowing, prominent) ---
    P.append({"type":"polygon","points":[(110,118),(146,118),(150,170),(106,170)],
              "color":BEARD,"outline":OUT,"outline_w":1})
    # beard flowing longer (down to chest)
    P.append({"type":"polygon","points":[(108,140),(148,140),(146,180),(110,180)],
              "color":BEARD,"outline":BEARD_DARK,"outline_w":1})
    # beard texture (strands)
    for bx in (114,122,130,138):
        P.append({"type":"line","start":[bx,120],"end":[bx,176],"color":BEARD_DARK,"width":1})
    # mustache (white, flowing)
    P.append({"type":"polygon","points":[(114,114),(142,114),(140,122),(116,122)],"color":BEARD,"outline":OUT,"outline_w":1})
    # mustache ends (curled)
    P.append({"type":"circle","cx":112,"cy":118,"r":3,"color":BEARD,"outline":BEARD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":144,"cy":118,"r":3,"color":BEARD,"outline":BEARD_DARK,"outline_w":1})

    # --- Flowing purple robes (with gold trim) ---
    P.append({"type":"polygon","points":[(100,134),(156,134),(166,220),(90,220)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # gold trim on collar
    P.append({"type":"rect","x":100,"y":134,"w":56,"h":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold sash/belt
    P.append({"type":"rect","x":90,"y":180,"w":76,"h":8,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # robe center fold
    P.append({"type":"line","start":[128,140],"end":[128,218],"color":ROBE_DARK,"width":1})
    # gold clock emblem on robe
    P.append({"type":"circle","cx":128,"cy":156,"r":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"line","start":[128,152],"end":[128,160],"color":GOLD_DARK,"width":1})
    P.append({"type":"line","start":[124,156],"end":[132,156],"color":GOLD_DARK,"width":1})

    # --- Arms (in robes, raised — time magic pose) ---
    P.append({"type":"rect","x":88,"y":142,"w":14,"h":40,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":154,"y":142,"w":14,"h":40,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    # gold cuff trim
    P.append({"type":"rect","x":88,"y":142,"w":14,"h":4,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":154,"y":142,"w":14,"h":4,"color":GOLD,"outline":OUT,"outline_w":1})
    # hands (elderly)
    P.append({"type":"circle","cx":95,"cy":184,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":161,"cy":184,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (robe covers — FLOATING, no feet on ground) ---
    P.append({"type":"ellipse","x":88,"y":218,"w":80,"h":20,"color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # gold trim at hem
    P.append({"type":"rect","x":88,"y":218,"w":80,"h":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # floating time magic wisps (he hovers)
    for fx in (100,128,156):
        P.append({"type":"circle","cx":fx,"cy":244,"r":4,"color":(140,200,255),"outline":EYE,"outline_w":1})

    return P


# ============================================================
# RUN ALL 6 SEQUENTIALLY
# ============================================================
CHAMPS = [
    ("Sion", sion_prims, "exposed skeletal jaw + bolted metal armor + giant axe"),
    ("Sivir", sivir_prims, "large crossblade + Shuriman armor + ponytail"),
    ("Taliyah", taliyah_prims, "floating rocks orbiting + nomadic clothing"),
    ("Tryndamere", tryndamere_prims, "long wild hair + bare chest + fur armor + greatsword"),
    ("Warwick", warwick_prims, "glowing green chemical vials + wolf head + claws"),
    ("Zilean", zilean_prims, "large floating clock + long white beard + robes"),
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
