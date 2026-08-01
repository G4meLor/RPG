"""Batch 22: hand-author 6 LoL champions to score 8-10.

Champions: Leblanc, Leona, Lux, Maokai, MissFortune, Nasus.
All start at 7. Each has ONE huge signature feature that dominates the silhouette.
Run sequentially; improve() auto-saves only when new > old.
"""
import sys, math
sys.path.insert(0, "exp")
from champ_improver import improve, committed_score

OUT = (25, 20, 25)


# ============================================================
# 1. LEBLANC — POINTED HAT (THE feature) + high-collared purple dress + pale skin
#    Missing: ornate high-collared dress, elegant Noxian attire, mystical floating energy
# ============================================================
def leblanc_prims():
    P = []
    PURPLE = (110, 50, 130)
    PURPLE_DARK = (70, 30, 90)
    PURPLE_LIGHT = (160, 80, 180)
    GOLD = (210, 170, 55)
    GOLD_DARK = (140, 100, 25)
    BLACK = (35, 25, 40)
    SKIN = (225, 200, 185)         # pale complexion
    HAIR = (50, 40, 55)            # dark hair
    EYE = (180, 80, 200)           # purple mystical eyes
    OUT = (20, 15, 25)

    # --- Mystical floating energy (behind — purple glow orbs, BIG) ---
    P.append({"type":"circle","cx":56,"cy":110,"r":16,"color":(90,35,110),"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":200,"cy":110,"r":16,"color":(90,35,110),"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":44,"cy":160,"r":12,"color":(110,45,130),"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":212,"cy":160,"r":12,"color":(110,45,130),"outline":None,"outline_w":0})
    # purple energy glow around body
    P.append({"type":"circle","cx":128,"cy":140,"r":60,"color":(50,20,70),"outline":None,"outline_w":0})

    # --- Ornate high-collared dress (THE missing feature — BIG purple dress, wider) ---
    # dress skirt (flowing, wide at bottom — THE feature)
    P.append({"type":"polygon","points":[(86,108),(170,108),(186,225),(70,225)],
              "color":PURPLE,"outline":OUT,"outline_w":2})
    # dress inner shadow (darker purple — depth)
    P.append({"type":"polygon","points":[(100,114),(156,114),(170,215),(86,215)],
              "color":PURPLE_DARK,"outline":OUT,"outline_w":1})
    # HIGH COLLAR (THE missing feature — BIG, pointed up around neck, visible behind head)
    P.append({"type":"polygon","points":[(96,92),(160,92),(152,70),(104,70)],
              "color":PURPLE_DARK,"outline":OUT,"outline_w":3})
    # collar inner (gold trim — ornate)
    P.append({"type":"polygon","points":[(102,90),(154,90),(148,74),(108,74)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # collar gold ornate detail (gems)
    P.append({"type":"circle","cx":128,"cy":82,"r":4,"color":(180,60,200),"outline":GOLD_DARK,"outline_w":1})
    # gold trim on dress center (ornate Noxian)
    P.append({"type":"line","start":[128,110],"end":[128,222],"color":GOLD,"width":3})
    # gold ornate belt (wide, Noxian)
    P.append({"type":"rect","x":82,"y":148,"w":92,"h":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":153,"r":5,"color":PURPLE_DARK,"outline":GOLD_DARK,"outline_w":1})
    # dress gold trim at hem (Noxian ornate)
    P.append({"type":"line","start":[72,220],"end":[184,220],"color":GOLD,"width":3})
    # dress ornate side panels (gold trim on edges)
    P.append({"type":"line","start":[86,110],"end":[70,225],"color":GOLD,"width":2})
    P.append({"type":"line","start":[170,110],"end":[186,225],"color":GOLD,"width":2})

    # --- Legs (hidden by dress, just boots peeking) ---
    P.append({"type":"rect","x":112,"y":215,"w":14,"h":12,"color":BLACK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":215,"w":14,"h":12,"color":BLACK,"outline":OUT,"outline_w":1,"radius":2})

    # --- Arms (slender, in purple sleeves — Noxian attire) ---
    P.append({"type":"rect","x":84,"y":110,"w":14,"h":42,"color":PURPLE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":158,"y":110,"w":14,"h":42,"color":PURPLE,"outline":OUT,"outline_w":1,"radius":4})
    # gold bracelets (Noxian ornate)
    P.append({"type":"rect","x":84,"y":146,"w":14,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":158,"y":146,"w":14,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # pale hands (THE missing feature — pale complexion)
    P.append({"type":"circle","cx":91,"cy":154,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":165,"cy":154,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- HEAD: pale complexion + dark hair (THE missing feature) ---
    P.append({"type":"circle","cx":128,"cy":68,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # dark hair (flowing down sides — BIG)
    P.append({"type":"polygon","points":[(108,60),(148,60),(146,82),(110,82)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # hair back (behind head)
    P.append({"type":"circle","cx":128,"cy":64,"r":18,"color":HAIR,"outline":OUT,"outline_w":1})
    # purple mystical eyes
    P.append({"type":"circle","cx":121,"cy":70,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":70,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":121,"cy":69,"r":1,"color":(220,120,240),"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":135,"cy":69,"r":1,"color":(220,120,240),"outline":None,"outline_w":0})
    # lips (red)
    P.append({"type":"line","start":[121,80],"end":[135,80],"color":(150,40,55),"width":2})

    # --- POINTED HAT (THE feature — BIG, tall, curved tip, dominates head) ---
    # hat brim (wide, flat)
    P.append({"type":"ellipse","x":96,"y":50,"w":64,"h":14,"color":PURPLE_DARK,"outline":OUT,"outline_w":2})
    # hat cone (tall, curved — the signature pointed witch hat)
    P.append({"type":"polygon","points":[(104,52),(152,52),(140,10),(128,2)],
              "color":PURPLE,"outline":OUT,"outline_w":2})
    # hat cone highlight
    P.append({"type":"polygon","points":[(110,50),(128,50),(128,8)],
              "color":PURPLE_LIGHT,"outline":PURPLE_DARK,"outline_w":1})
    # gold hat band
    P.append({"type":"rect","x":100,"y":48,"w":56,"h":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold gem on hat band
    P.append({"type":"circle","cx":128,"cy":51,"r":4,"color":(180,60,200),"outline":GOLD_DARK,"outline_w":1})
    # hat tip curl (the signature curve at top)
    P.append({"type":"circle","cx":128,"cy":4,"r":4,"color":PURPLE,"outline":OUT,"outline_w":1})
    return P


# ============================================================
# 2. LEONA — massive GOLDEN SUN SHIELD (THE feature) + plate armor + plumed helm
#    Missing: plumed helmet, glowing golden accents
# ============================================================
def leona_prims():
    P = []
    GOLD = (225, 185, 60)
    GOLD_DARK = (150, 110, 30)
    GOLD_LIGHT = (250, 220, 100)
    STEEL = (160, 165, 175)
    STEEL_DARK = (100, 105, 115)
    WHITE = (235, 235, 240)
    SKIN = (215, 185, 150)
    HAIR = (180, 140, 60)          # blonde hair
    PLUME = (220, 50, 50)          # red plume
    SUN = (255, 200, 50)           # sun yellow
    SILVER_L = (210, 210, 220)
    OUT = (25, 22, 30)

    # --- MASSIVE GOLDEN SUN SHIELD (THE feature — HUGE, dominates left side) ---
    # shield outer ring (golden, BIG)
    P.append({"type":"circle","cx":72,"cy":140,"r":42,"color":GOLD,"outline":GOLD_DARK,"outline_w":3})
    # shield inner field (steel)
    P.append({"type":"circle","cx":72,"cy":140,"r":35,"color":STEEL,"outline":GOLD_DARK,"outline_w":2})
    # SUN RAYS (THE feature — big golden sun rays around shield)
    import math as _m
    for ang in range(0, 360, 30):
        r1, r2 = 40, 50
        x1 = 72 + int(r1 * _m.cos(_m.radians(ang)))
        y1 = 140 + int(r1 * _m.sin(_m.radians(ang)))
        x2 = 72 + int(r2 * _m.cos(_m.radians(ang)))
        y2 = 140 + int(r2 * _m.sin(_m.radians(ang)))
        P.append({"type":"line","start":[x1,y1],"end":[x2,y2],"color":SUN,"width":4})
    # sun emblem center (BIG golden sun face)
    P.append({"type":"circle","cx":72,"cy":140,"r":18,"color":SUN,"outline":GOLD_DARK,"outline_w":2})
    # sun face rays (inner)
    for ang in range(0, 360, 45):
        x1 = 72 + int(14 * _m.cos(_m.radians(ang)))
        y1 = 140 + int(14 * _m.sin(_m.radians(ang)))
        x2 = 72 + int(20 * _m.cos(_m.radians(ang)))
        y2 = 140 + int(20 * _m.sin(_m.radians(ang)))
        P.append({"type":"line","start":[x1,y1],"end":[x2,y2],"color":GOLD_DARK,"width":2})
    # shield center boss
    P.append({"type":"circle","cx":72,"cy":140,"r":8,"color":GOLD_LIGHT,"outline":GOLD_DARK,"outline_w":1})

    # --- Legs (golden greaves) ---
    P.append({"type":"rect","x":112,"y":168,"w":18,"h":48,"color":STEEL,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":168,"w":18,"h":48,"color":STEEL,"outline":OUT,"outline_w":1,"radius":3})
    # gold knee guards
    P.append({"type":"circle","cx":121,"cy":184,"r":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":141,"cy":184,"r":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold boots
    P.append({"type":"rect","x":110,"y":210,"w":22,"h":10,"color":GOLD_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":210,"w":22,"h":10,"color":GOLD_DARK,"outline":OUT,"outline_w":1,"radius":2})

    # --- Torso (full plate armor, golden accents) ---
    P.append({"type":"polygon","points":[(104,100),(152,100),(156,170),(100,170)],
              "color":STEEL,"outline":OUT,"outline_w":2})
    # gold chest plate
    P.append({"type":"polygon","points":[(110,106),(146,106),(148,160),(108,160)],
              "color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # glowing golden accents (sun motif on chest)
    P.append({"type":"circle","cx":128,"cy":130,"r":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # sun rays on chest
    for ang in range(0, 360, 60):
        x1 = 128 + int(8 * _m.cos(_m.radians(ang)))
        y1 = 130 + int(8 * _m.sin(_m.radians(ang)))
        x2 = 128 + int(14 * _m.cos(_m.radians(ang)))
        y2 = 130 + int(14 * _m.sin(_m.radians(ang)))
        P.append({"type":"line","start":[x1,y1],"end":[x2,y2],"color":GOLD_LIGHT,"width":2})
    # gold center
    P.append({"type":"circle","cx":128,"cy":130,"r":5,"color":GOLD_LIGHT,"outline":GOLD_DARK,"outline_w":1})
    # gold belt
    P.append({"type":"rect","x":100,"y":158,"w":56,"h":8,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Right arm (armored, holds Zenith Blade) ---
    P.append({"type":"rect","x":150,"y":108,"w":16,"h":48,"color":STEEL,"outline":OUT,"outline_w":1,"radius":4})
    # gold shoulder pauldron
    P.append({"type":"circle","cx":158,"cy":108,"r":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # gauntlet
    P.append({"type":"circle","cx":158,"cy":158,"r":6,"color":STEEL_DARK,"outline":OUT,"outline_w":1})
    # Zenith Blade (sword, diagonal)
    P.append({"type":"line","start":[158,160],"end":[200,100],"color":SILVER_L,"width":5})
    P.append({"type":"polygon","points":[(200,100),(194,106),(206,106)],"color":SILVER_L,"outline":STEEL_DARK,"outline_w":2})
    # blade guard
    P.append({"type":"line","start":[152,162],"end":[164,162],"color":GOLD,"width":3})

    # --- PLUMED HELMET (THE missing feature — golden helm with red plume) ---
    # helmet
    P.append({"type":"circle","cx":128,"cy":78,"r":18,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # helmet face guard
    P.append({"type":"rect","x":114,"y":80,"w":28,"h":14,"color":STEEL_DARK,"outline":OUT,"outline_w":1,"radius":2})
    # eye slits
    P.append({"type":"line","start":[118,86],"end":[124,86],"color":OUT,"width":2})
    P.append({"type":"line","start":[132,86],"end":[138,86],"color":OUT,"width":2})
    # RED PLUME (THE missing feature — BIG, flowing from helmet top)
    P.append({"type":"polygon","points":[(108,56),(128,30),(148,56),(144,62),(112,62)],
              "color":PLUME,"outline":OUT,"outline_w":2})
    # plume segments (feather lines)
    for px in (114, 122, 130, 138):
        P.append({"type":"line","start":[px,54],"end":[px,38],"color":(150,30,30),"width":1})
    # gold helmet trim
    P.append({"type":"rect","x":112,"y":72,"w":32,"h":4,"color":GOLD_LIGHT,"outline":GOLD_DARK,"outline_w":1})
    # sun emblem on helmet forehead
    P.append({"type":"circle","cx":128,"cy":76,"r":4,"color":SUN,"outline":GOLD_DARK,"outline_w":1})
    return P


# ============================================================
# 3. LUX — glowing LIGHT STAFF (THE feature) + blonde hair + white/gold Demacian armor
#    Missing: Demacian armor plating, magical light effects
# ============================================================
def lux_prims():
    P = []
    WHITE = (240, 240, 245)
    WHITE_DARK = (190, 190, 200)
    GOLD = (220, 180, 60)
    GOLD_DARK = (150, 110, 30)
    BLUE = (70, 100, 170)
    SKIN = (220, 190, 160)
    HAIR = (240, 210, 120)         # blonde
    HAIR_DARK = (200, 170, 80)
    LIGHT = (180, 220, 255)        # light blue glow
    LIGHT_BRIGHT = (230, 245, 255)
    STAFF = (160, 120, 50)         # wooden staff
    OUT = (25, 22, 30)

    # --- GLOWING LIGHT STAFF (THE feature — BIG, glowing, dominates right side) ---
    # staff shaft (long, diagonal, held to the right)
    P.append({"type":"line","start":[176,215],"end":[200,40],"color":STAFF,"width":6})
    # staff highlight
    P.append({"type":"line","start":[176,215],"end":[200,40],"color":(200,160,80),"width":2})
    # BIG LIGHT ORB on top (THE feature — glowing magical light, huge)
    P.append({"type":"circle","cx":200,"cy":40,"r":22,"color":LIGHT,"outline":(100,160,220),"outline_w":2})
    P.append({"type":"circle","cx":200,"cy":40,"r":16,"color":LIGHT_BRIGHT,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":200,"cy":40,"r":8,"color":(255,255,255),"outline":None,"outline_w":0})
    # light rays (radiating from orb — THE magical light effect)
    import math as _m
    for ang in range(0, 360, 30):
        x1 = 200 + int(22 * _m.cos(_m.radians(ang)))
        y1 = 40 + int(22 * _m.sin(_m.radians(ang)))
        x2 = 200 + int(32 * _m.cos(_m.radians(ang)))
        y2 = 40 + int(32 * _m.sin(_m.radians(ang)))
        P.append({"type":"line","start":[x1,y1],"end":[x2,y2],"color":LIGHT_BRIGHT,"width":3})
    # gold staff cap (ornate)
    P.append({"type":"circle","cx":200,"cy":58,"r":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # staff grip wrap
    P.append({"type":"line","start":[180,100],"end":[186,180],"color":GOLD_DARK,"width":3})

    # --- Legs (white pants + gold-trim boots) ---
    P.append({"type":"rect","x":110,"y":168,"w":16,"h":46,"color":WHITE,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":168,"w":16,"h":46,"color":WHITE,"outline":OUT,"outline_w":1,"radius":3})
    # gold-trim boots
    P.append({"type":"rect","x":108,"y":200,"w":20,"h":16,"color":GOLD_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":200,"w":20,"h":16,"color":GOLD_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":108,"y":200,"w":20,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":128,"y":200,"w":20,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Torso (white/gold Demacian armor plating — THE missing feature) ---
    P.append({"type":"polygon","points":[(102,100),(154,100),(150,168),(106,168)],
              "color":WHITE,"outline":OUT,"outline_w":2})
    # Demacian armor chest plate (gold-trimmed)
    P.append({"type":"polygon","points":[(108,106),(148,106),(144,160),(112,160)],
              "color":WHITE_DARK,"outline":OUT,"outline_w":1})
    # gold center trim
    P.append({"type":"line","start":[128,106],"end":[128,160],"color":GOLD,"width":3})
    # Demacian winged emblem on chest
    P.append({"type":"circle","cx":128,"cy":128,"r":8,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(116,128),(128,124),(140,128),(136,132),(128,130),(120,132)],
              "color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # blue gem center
    P.append({"type":"circle","cx":128,"cy":128,"r":3,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})
    # gold shoulder pauldrons
    P.append({"type":"circle","cx":106,"cy":106,"r":9,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":150,"cy":106,"r":9,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold belt
    P.append({"type":"rect","x":104,"y":158,"w":48,"h":8,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":162,"r":3,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})

    # --- Left arm (white sleeve) ---
    P.append({"type":"rect","x":90,"y":110,"w":14,"h":48,"color":WHITE,"outline":OUT,"outline_w":1,"radius":4})
    # gold bracer
    P.append({"type":"rect","x":90,"y":146,"w":14,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # hand
    P.append({"type":"circle","cx":97,"cy":160,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- HEAD: blonde hair + light magic ---
    P.append({"type":"circle","cx":128,"cy":78,"r":15,"color":SKIN,"outline":OUT,"outline_w":1})
    # blonde hair (flowing, THE feature — BIG)
    P.append({"type":"polygon","points":[(108,70),(148,70),(146,56),(128,48),(110,56)],
              "color":HAIR,"outline":OUT,"outline_w":2})
    # hair sides (flowing down)
    P.append({"type":"polygon","points":[(110,72),(116,72),(114,92)],"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(140,72),(146,72),(144,92)],"color":HAIR,"outline":OUT,"outline_w":1})
    # hair highlight
    P.append({"type":"polygon","points":[(112,60),(144,60),(140,68),(116,68)],
              "color":HAIR_DARK,"outline":OUT,"outline_w":1})
    # eyes (blue)
    P.append({"type":"circle","cx":122,"cy":80,"r":2,"color":BLUE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":134,"cy":80,"r":2,"color":BLUE,"outline":OUT,"outline_w":1})
    # smile
    P.append({"type":"line","start":[122,88],"end":[134,88],"color":(140,80,80),"width":1})
    # light magic glow around hands (subtle)
    P.append({"type":"circle","cx":97,"cy":160,"r":8,"color":(180,220,255),"outline":None,"outline_w":0})
    return P


# ============================================================
# 4. MAOKAI — BARK-LIKE SKIN / TREE BODY (THE feature) + branching arms + glowing eyes
#    Missing: branching arms
# ============================================================
def maokai_prims():
    P = []
    BARK = (110, 80, 50)           # brown bark
    BARK_DARK = (70, 50, 30)
    BARK_LIGHT = (150, 115, 75)
    LEAF = (60, 110, 55)           # dark green foliage
    LEAF_DARK = (35, 75, 35)
    LEAF_LIGHT = (90, 150, 80)
    GLOW = (100, 220, 180)         # teal glowing eyes
    GLOW_BRIGHT = (160, 255, 220)
    ROOT = (80, 55, 35)            # root-feet
    OUT = (25, 20, 15)

    # --- FOLIAGE/LEAVES on head (THE tree feature — BIG leafy crown) ---
    P.append({"type":"circle","cx":128,"cy":40,"r":30,"color":LEAF,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":100,"cy":44,"r":18,"color":LEAF_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":156,"cy":44,"r":18,"color":LEAF_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":118,"cy":30,"r":14,"color":LEAF_LIGHT,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":140,"cy":30,"r":14,"color":LEAF_LIGHT,"outline":OUT,"outline_w":1})
    # leaf texture (small circles)
    for lx, ly in [(108,38),(128,34),(148,38),(118,48),(138,48)]:
        P.append({"type":"circle","cx":lx,"cy":ly,"r":5,"color":LEAF_DARK,"outline":OUT,"outline_w":1})

    # --- BRANCHING ARMS (THE missing feature — big wooden branches extending out) ---
    # LEFT branch arm (extends out and up, with leaves)
    P.append({"type":"line","start":[96,120],"end":[60,90],"color":BARK_DARK,"width":10})
    P.append({"type":"line","start":[60,90],"end":[44,72],"color":BARK_DARK,"width":7})
    # branch joints (knobby)
    P.append({"type":"circle","cx":60,"cy":90,"r":6,"color":BARK,"outline":BARK_DARK,"outline_w":1})
    # leaves on left branch
    P.append({"type":"circle","cx":44,"cy":72,"r":8,"color":LEAF,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":50,"cy":80,"r":5,"color":LEAF_LIGHT,"outline":OUT,"outline_w":1})
    # RIGHT branch arm
    P.append({"type":"line","start":[160,120],"end":[196,90],"color":BARK_DARK,"width":10})
    P.append({"type":"line","start":[196,90],"end":[212,72],"color":BARK_DARK,"width":7})
    P.append({"type":"circle","cx":196,"cy":90,"r":6,"color":BARK,"outline":BARK_DARK,"outline_w":1})
    # leaves on right branch
    P.append({"type":"circle","cx":212,"cy":72,"r":8,"color":LEAF,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":206,"cy":80,"r":5,"color":LEAF_LIGHT,"outline":OUT,"outline_w":1})

    # --- TREE BODY (THE feature — bark-like torso, wide, wooden) ---
    P.append({"type":"polygon","points":[(92,80),(164,80),(172,190),(84,190)],
              "color":BARK,"outline":OUT,"outline_w":2})
    # bark texture (vertical lines — THE feature)
    for bx in (100, 112, 128, 144, 156):
        P.append({"type":"line","start":[bx,84],"end":[bx,188],"color":BARK_DARK,"width":2})
    # bark knots (wooden bumps)
    for kx, ky in [(108,110),(148,130),(118,150),(140,170)]:
        P.append({"type":"circle","cx":kx,"cy":ky,"r":4,"color":BARK_DARK,"outline":OUT,"outline_w":1})
    # bark texture (horizontal cracks)
    for by in (100, 130, 160):
        P.append({"type":"line","start":[92,by],"end":[164,by],"color":BARK_LIGHT,"width":1})

    # --- HEAD (wooden face — bark with glowing eyes) ---
    P.append({"type":"circle","cx":128,"cy":70,"r":18,"color":BARK,"outline":OUT,"outline_w":2})
    # bark face texture
    P.append({"type":"line","start":[116,60],"end":[116,82],"color":BARK_DARK,"width":1})
    P.append({"type":"line","start":[140,60],"end":[140,82],"color":BARK_DARK,"width":1})
    # GLOWING EYES (THE feature — teal glow)
    P.append({"type":"circle","cx":120,"cy":72,"r":5,"color":GLOW,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":136,"cy":72,"r":5,"color":GLOW,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":120,"cy":71,"r":2,"color":GLOW_BRIGHT,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":136,"cy":71,"r":2,"color":GLOW_BRIGHT,"outline":None,"outline_w":0})
    # wooden mouth (bark crack)
    P.append({"type":"line","start":[120,84],"end":[136,84],"color":BARK_DARK,"width":2})

    # --- ROOT FEET (THE tree feature — wooden roots instead of legs) ---
    # left root
    P.append({"type":"polygon","points":[(92,190),(112,190),(106,220),(88,220)],
              "color":ROOT,"outline":OUT,"outline_w":2})
    # root toes (spreading)
    P.append({"type":"line","start":[96,220],"end":[88,230],"color":ROOT,"width":4})
    P.append({"type":"line","start":[104,220],"end":[100,232],"color":ROOT,"width":4})
    # right root
    P.append({"type":"polygon","points":[(128,190),(164,190),(168,220),(136,220)],
              "color":ROOT,"outline":OUT,"outline_w":2})
    P.append({"type":"line","start":[144,220],"end":[140,232],"color":ROOT,"width":4})
    P.append({"type":"line","start":[160,220],"end":[168,230],"color":ROOT,"width":4})
    return P


# ============================================================
# 5. MISSFORTUNE — long flowing RED HAIR (THE feature) + tricorne hat + dual pistols
#    Missing: captain's coat, high-heeled boots
# ============================================================
def missfortune_prims():
    P = []
    HAIR = (190, 50, 50)           # red hair (THE feature)
    HAIR_DARK = (130, 25, 30)
    HAIR_LIGHT = (230, 80, 75)
    HAT = (40, 30, 35)             # black tricorne hat
    HAT_DARK = (20, 15, 20)
    COAT = (30, 25, 35)            # black captain's coat
    COAT_DARK = (15, 12, 20)
    GOLD = (210, 170, 55)
    GOLD_DARK = (140, 100, 25)
    SKIN = (225, 195, 165)
    WHITE = (235, 230, 225)        # white shirt
    SILVER = (190, 195, 205)
    SILVER_DARK = (110, 115, 125)
    RED_LIP = (160, 40, 45)
    OUT = (25, 20, 25)

    # --- LONG FLOWING RED HAIR (THE feature — HUGE, flowing down sides and back) ---
    # hair left flow (behind body, flowing down left side)
    P.append({"type":"polygon","points":[(84,58),(112,58),(100,215),(72,215)],
              "color":HAIR,"outline":OUT,"outline_w":2})
    # hair right flow (behind body, flowing down right side)
    P.append({"type":"polygon","points":[(144,58),(172,58),(184,215),(156,215)],
              "color":HAIR,"outline":OUT,"outline_w":2})
    # hair back (behind head)
    P.append({"type":"polygon","points":[(98,54),(158,54),(162,90),(94,90)],
              "color":HAIR_DARK,"outline":OUT,"outline_w":1})
    # hair top (on head, under hat)
    P.append({"type":"circle","cx":128,"cy":66,"r":18,"color":HAIR,"outline":OUT,"outline_w":1})
    # hair highlight (shine)
    P.append({"type":"polygon","points":[(106,56),(150,56),(146,64),(110,64)],
              "color":HAIR_LIGHT,"outline":HAIR_DARK,"outline_w":1})
    # hair strand texture (left)
    for hy in (90, 120, 150, 180):
        P.append({"type":"line","start":[88,hy],"end":[84,hy+20],"color":HAIR_DARK,"width":1})
    # hair strand texture (right)
    for hy in (90, 120, 150, 180):
        P.append({"type":"line","start":[168,hy],"end":[172,hy+20],"color":HAIR_DARK,"width":1})

    # --- DUAL FLINTLOCK PISTOLS (THE weapon — BIG, both hands, held at sides) ---
    # LEFT pistol (held at left side, pointing down-out)
    P.append({"type":"rect","x":60,"y":140,"w":30,"h":10,"color":SILVER_DARK,"outline":OUT,"outline_w":2,"radius":2})
    # pistol barrel
    P.append({"type":"rect","x":56,"y":142,"w":8,"h":6,"color":SILVER,"outline":OUT,"outline_w":1})
    # pistol grip
    P.append({"type":"polygon","points":[(78,150),(88,150),(84,168),(82,168)],
              "color":(90,60,35),"outline":OUT,"outline_w":1})
    # gold pistol ornament
    P.append({"type":"circle","cx":75,"cy":145,"r":3,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # RIGHT pistol (held at right side, pointing down-out)
    P.append({"type":"rect","x":166,"y":140,"w":30,"h":10,"color":SILVER_DARK,"outline":OUT,"outline_w":2,"radius":2})
    P.append({"type":"rect","x":192,"y":142,"w":8,"h":6,"color":SILVER,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(168,150),(178,150),(174,168),(172,168)],
              "color":(90,60,35),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":181,"cy":145,"r":3,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Legs (high-heeled boots — THE missing feature) ---
    P.append({"type":"rect","x":110,"y":168,"w":16,"h":36,"color":COAT,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":168,"w":16,"h":36,"color":COAT,"outline":OUT,"outline_w":1,"radius":3})
    # high-heeled boots (THE missing feature — black, with heel)
    P.append({"type":"rect","x":106,"y":200,"w":22,"h":18,"color":COAT_DARK,"outline":OUT,"outline_w":2,"radius":2})
    P.append({"type":"rect","x":128,"y":200,"w":22,"h":18,"color":COAT_DARK,"outline":OUT,"outline_w":2,"radius":2})
    # gold boot trim
    P.append({"type":"rect","x":106,"y":200,"w":22,"h":3,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":128,"y":200,"w":22,"h":3,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # high heels
    P.append({"type":"polygon","points":[(106,218),(112,218),(110,228),(108,228)],"color":COAT_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(128,218),(134,218),(132,228),(130,228)],"color":COAT_DARK,"outline":OUT,"outline_w":1})

    # --- CAPTAIN'S COAT (THE missing feature — black, long, with gold trim) ---
    P.append({"type":"polygon","points":[(98,100),(158,100),(168,205),(88,205)],
              "color":COAT,"outline":OUT,"outline_w":2})
    # coat inner (white shirt visible)
    P.append({"type":"polygon","points":[(112,106),(144,106),(140,160),(116,160)],
              "color":WHITE,"outline":OUT,"outline_w":1})
    # coat gold trim (center line)
    P.append({"type":"line","start":[128,106],"end":[128,200],"color":GOLD,"width":2})
    # gold coat buttons
    for by in (112, 124, 136, 148):
        P.append({"type":"circle","cx":128,"cy":by,"r":2,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold coat collar
    P.append({"type":"polygon","points":[(108,100),(148,100),(142,112),(114,112)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold belt
    P.append({"type":"rect","x":92,"y":158,"w":72,"h":8,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":162,"r":4,"color":COAT_DARK,"outline":GOLD_DARK,"outline_w":1})
    # coat gold trim at hem
    P.append({"type":"line","start":[90,200],"end":[166,200],"color":GOLD,"width":2})

    # --- Arms (in coat sleeves, holding pistols) ---
    P.append({"type":"rect","x":86,"y":112,"w":14,"h":40,"color":COAT,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":156,"y":112,"w":14,"h":40,"color":COAT,"outline":OUT,"outline_w":1,"radius":4})
    # hands
    P.append({"type":"circle","cx":93,"cy":154,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":163,"cy":154,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- HEAD: pretty face + red lips ---
    P.append({"type":"circle","cx":128,"cy":78,"r":15,"color":SKIN,"outline":OUT,"outline_w":1})
    # eyes
    P.append({"type":"circle","cx":122,"cy":78,"r":2,"color":OUT,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":134,"cy":78,"r":2,"color":OUT,"outline":None,"outline_w":0})
    # red lips (THE feature)
    P.append({"type":"line","start":[121,88],"end":[135,88],"color":RED_LIP,"width":2})

    # --- TRICORNE PIRATE HAT (THE feature — black, three-cornered, with gold trim) ---
    # hat brim (wide, three-cornered)
    P.append({"type":"polygon","points":[(92,58),(164,58),(170,66),(86,66)],
              "color":HAT_DARK,"outline":OUT,"outline_w":2})
    # hat crown (the tricorne peak)
    P.append({"type":"polygon","points":[(104,58),(152,58),(144,42),(128,36),(112,42)],
              "color":HAT,"outline":OUT,"outline_w":2})
    # gold hat trim
    P.append({"type":"line","start":[92,58],"end":[164,58],"color":GOLD,"width":2})
    # gold hat buckle/ornament
    P.append({"type":"circle","cx":128,"cy":48,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # hat feather (red, from behind hat)
    P.append({"type":"line","start":[150,44],"end":[160,30],"color":HAIR,"width":3})
    return P


# ============================================================
# 6. NASUS — JACKAL HEAD (THE feature) + Egyptian gold armor + staff
#    Missing: ancient Egyptian-style armor, golden ornaments, towering stature
# ============================================================
def nasus_prims():
    P = []
    FUR = (160, 130, 80)           # golden-tan jackal fur
    FUR_DARK = (110, 85, 50)
    FUR_LIGHT = (200, 170, 110)
    GOLD = (220, 180, 60)
    GOLD_DARK = (150, 110, 30)
    SAND = (200, 175, 120)         # sand-colored armor
    BLUE = (50, 70, 140)           # deep blue accents
    STAFF = (140, 100, 50)         # stone staff
    STAFF_DARK = (90, 60, 30)
    EYE = (220, 180, 60)           # golden eyes
    EYE_GLOW = (255, 220, 100)
    WHITE_T = (240, 235, 220)
    OUT = (25, 20, 15)

    # --- MASSIVE STONE STAFF (THE weapon — tall, held to the right) ---
    P.append({"type":"line","start":[178,220],"end":[194,30],"color":STAFF,"width":8})
    # staff highlight
    P.append({"type":"line","start":[178,220],"end":[194,30],"color":STAFF_DARK,"width":3})
    # staff head (ornate Egyptian top — the curved crook/heka style)
    P.append({"type":"polygon","points":[(194,30),(186,44),(202,44)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # staff Egyptian ornament (golden band)
    P.append({"type":"rect","x":184,"y":60,"w":20,"h":8,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":194,"cy":64,"r":4,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})
    # staff shaft wrap
    P.append({"type":"line","start":[182,100],"end":[190,200],"color":GOLD_DARK,"width":3})

    # --- Legs (Egyptian gold armor greaves) ---
    P.append({"type":"rect","x":106,"y":168,"w":18,"h":48,"color":SAND,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":168,"w":18,"h":48,"color":SAND,"outline":OUT,"outline_w":1,"radius":3})
    # gold knee ornaments (Egyptian)
    P.append({"type":"circle","cx":115,"cy":184,"r":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":139,"cy":184,"r":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold Egyptian greave ornaments
    P.append({"type":"rect","x":106,"y":200,"w":22,"h":16,"color":GOLD_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":200,"w":22,"h":16,"color":GOLD_DARK,"outline":OUT,"outline_w":1,"radius":2})
    # gold trim on boots
    P.append({"type":"rect","x":106,"y":200,"w":22,"h":3,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":128,"y":200,"w":22,"h":3,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- TORSO (ancient Egyptian-style armor — THE missing feature) ---
    # towering stature (broad torso)
    P.append({"type":"polygon","points":[(96,100),(160,100),(158,168),(98,168)],
              "color":SAND,"outline":OUT,"outline_w":2})
    # Egyptian gold chest plate (THE missing feature)
    P.append({"type":"polygon","points":[(102,106),(154,106),(150,160),(106,160)],
              "color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # gold center trim (Egyptian ornamental)
    P.append({"type":"line","start":[128,106],"end":[128,160],"color":GOLD,"width":3})
    # Egyptian ornament on chest (sun disk / ankh style)
    P.append({"type":"circle","cx":128,"cy":128,"r":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # Egyptian ankh-like emblem
    P.append({"type":"line","start":[128,120],"end":[128,138],"color":GOLD_DARK,"width":2})
    P.append({"type":"line","start":[122,126],"end":[134,126],"color":GOLD_DARK,"width":2})
    # blue gem center
    P.append({"type":"circle","cx":128,"cy":128,"r":4,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})
    # golden ornaments (shoulder pauldrons — Egyptian style)
    P.append({"type":"circle","cx":100,"cy":106,"r":11,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":156,"cy":106,"r":11,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # Egyptian shoulder ornament detail
    P.append({"type":"circle","cx":100,"cy":106,"r":5,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":156,"cy":106,"r":5,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})
    # gold belt (Egyptian ornamental)
    P.append({"type":"rect","x":96,"y":156,"w":66,"h":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":161,"r":4,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})

    # --- Arms (muscular, golden armbands) ---
    P.append({"type":"rect","x":84,"y":112,"w":14,"h":50,"color":FUR,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":158,"y":112,"w":14,"h":50,"color":FUR,"outline":OUT,"outline_w":1,"radius":4})
    # gold Egyptian armbands
    P.append({"type":"rect","x":84,"y":148,"w":14,"h":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":158,"y":148,"w":14,"h":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # jackal hands (paw-like)
    P.append({"type":"circle","cx":91,"cy":164,"r":5,"color":FUR_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":165,"cy":164,"r":5,"color":FUR_DARK,"outline":OUT,"outline_w":1})

    # --- JACKAL HEAD (THE feature — long snout, pointed ears, golden eyes) ---
    # head skull (jackal — tall, narrow)
    P.append({"type":"circle","cx":128,"cy":72,"r":20,"color":FUR,"outline":OUT,"outline_w":2})
    # jackal brow (heavy bone ridge)
    P.append({"type":"rect","x":106,"y":60,"w":44,"h":8,"color":FUR_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # LONG JACKAL SNOUT (THE feature — long, tapered, extending forward/down)
    P.append({"type":"polygon","points":[(108,78),(148,78),(140,108),(116,108)],
              "color":FUR,"outline":OUT,"outline_w":2})
    # snout tip (dark nose)
    P.append({"type":"circle","cx":128,"cy":106,"r":5,"color":FUR_DARK,"outline":OUT,"outline_w":1})
    # nostrils
    P.append({"type":"circle","cx":124,"cy":92,"r":1,"color":OUT,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":132,"cy":92,"r":1,"color":OUT,"outline":None,"outline_w":0})
    # POINTED EARS (THE feature — BIG, tall, jackal ears)
    P.append({"type":"polygon","points":[(108,56),(96,34),(106,54),(114,60)],
              "color":FUR,"outline":FUR_DARK,"outline_w":2})
    P.append({"type":"polygon","points":[(148,56),(160,34),(150,54),(142,60)],
              "color":FUR,"outline":FUR_DARK,"outline_w":2})
    # ear inner (pink)
    P.append({"type":"polygon","points":[(104,48),(100,40),(106,50)],"color":FUR_LIGHT,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(152,48),(156,40),(150,50)],"color":FUR_LIGHT,"outline":OUT,"outline_w":1})
    # GOLDEN EYES (THE feature — glowing gold)
    P.append({"type":"circle","cx":116,"cy":70,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":140,"cy":70,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":117,"cy":69,"r":2,"color":EYE_GLOW,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":141,"cy":69,"r":2,"color":EYE_GLOW,"outline":None,"outline_w":0})
    # jackal teeth (visible fangs)
    P.append({"type":"polygon","points":[(118,104),(122,104),(120,112)],"color":WHITE_T,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(134,104),(138,104),(136,112)],"color":WHITE_T,"outline":OUT,"outline_w":1})
    # Egyptian gold headdress (pharaoh-style circlet on head)
    P.append({"type":"rect","x":108,"y":54,"w":40,"h":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold cobra ornament on headdress (uraeus)
    P.append({"type":"circle","cx":128,"cy":52,"r":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":50,"r":2,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})
    return P


# ============================================================
# RUN SEQUENTIALLY
# ============================================================
def run_all():
    champs = [
        ("Leblanc", leblanc_prims),
        ("Leona", leona_prims),
        ("Lux", lux_prims),
        ("Maokai", maokai_prims),
        ("MissFortune", missfortune_prims),
        ("Nasus", nasus_prims),
    ]
    results = []
    for cid, fn in champs:
        print(f"\n{'='*60}")
        print(f"  {cid} (committed: {committed_score(cid)})")
        print(f"{'='*60}")
        best = None
        for rnd in range(1, 4):
            print(f"  Round {rnd}...")
            prims = fn()
            r = improve(cid, prims, gate_n=3)
            print(f"    -> new={r['new']}, saved={r['saved']}, missing={r['missing'][:3]}")
            if best is None or r["new"] > best["new"]:
                best = r
            if r["new"] >= 8:
                break
            if rnd < 3 and r["new"] < 8:
                print(f"    Score <8, will retry...")
        results.append({
            "id": cid,
            "old": best["old"],
            "new": best["new"],
            "saved": best["saved"],
            "rounds": rnd,
            "missing_final": best["missing"][:3],
            "feature": best.get("verdict", ""),
        })
        print(f"  FINAL: {cid} {best['old']} -> {best['new']} (saved={best['saved']})")
    print(f"\n{'='*60}")
    print("BATCH 22 RESULTS:")
    print(json.dumps(results, indent=2))
    improved = sum(1 for r in results if r["new"] > r["old"])
    ge8 = sum(1 for r in results if r["new"] >= 8)
    print(f"\n{improved}/6 champs improved, {ge8} reached >=8.")


if __name__ == "__main__":
    import json
    run_all()
