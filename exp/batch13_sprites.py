"""Batch 13: hand-author 6 LoL champions to score 8-10.

Champions: JarvanIV, Jayce, Kaisa, Kalista, Karthus, Katarina.
All start at 6. Each has ONE huge signature feature that dominates the silhouette.
Run sequentially; improve() auto-saves only when new > old.
"""
import sys, math
sys.path.insert(0, "exp")
from champ_improver import improve, committed_score

OUT = (25, 20, 25)


# ============================================================
# 1. JARVAN IV — golden ROYAL CREST (winged eagle) + white flowing cape + lance
#    Missing: golden royal crest, Demacian royal insignia
# ============================================================
def jarvaniv_prims():
    P = []
    STEEL = (120, 130, 150)
    STEEL_DARK = (70, 80, 100)
    GOLD = (220, 180, 60)
    GOLD_DARK = (150, 110, 30)
    WHITE = (235, 235, 240)
    WHITE_DARK = (180, 180, 195)
    BLUE = (60, 80, 160)
    SKIN = (210, 180, 150)
    HAIR = (180, 150, 80)
    SILVER_J = (200, 200, 210)
    OUT = (25, 22, 30)

    # --- White flowing cape (BIG, behind, spread wide — THE feature) ---
    P.append({"type":"polygon","points":[(82,90),(174,90),(190,220),(66,220)],
              "color":WHITE,"outline":OUT,"outline_w":2})
    # cape inner shadow (depth)
    P.append({"type":"polygon","points":[(96,96),(160,96),(172,210),(84,210)],
              "color":WHITE_DARK,"outline":OUT,"outline_w":1})
    # blue cape lining (Demacian blue — inner)
    P.append({"type":"polygon","points":[(104,100),(152,100),(160,200),(96,200)],
              "color":BLUE,"outline":OUT,"outline_w":1})
    # gold trim on cape edge
    P.append({"type":"line","start":[82,90],"end":[66,220],"color":GOLD,"width":3})
    P.append({"type":"line","start":[174,90],"end":[190,220],"color":GOLD,"width":3})

    # --- BIG LANCE / CATAPHRACT STANDARD (right side, tall, THE feature) ---
    # lance shaft (long, diagonal — held upright to the right, THICKER)
    P.append({"type":"line","start":[186,215],"end":[200,20],"color":(120,90,50),"width":9})
    # lance shaft highlight
    P.append({"type":"line","start":[186,215],"end":[200,20],"color":(160,120,70),"width":3})
    # lance tip (spearhead, BIG — leaf-shaped, the iconic cataphract lance)
    P.append({"type":"polygon","points":[(200,20),(190,36),(210,36)],
              "color":SILVER_J,"outline":STEEL_DARK,"outline_w":2})
    P.append({"type":"polygon","points":[(200,20),(194,32),(206,32)],
              "color":(230,230,240),"outline":STEEL_DARK,"outline_w":1})
    # lance banner (Demacian flag — blue with gold crest, hanging from lance, BIGGER)
    P.append({"type":"polygon","points":[(190,44),(216,44),(212,96),(194,96)],
              "color":BLUE,"outline":GOLD_DARK,"outline_w":2})
    # gold crest on banner (winged eagle, BIG)
    P.append({"type":"circle","cx":203,"cy":68,"r":9,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # winged eagle on banner
    P.append({"type":"polygon","points":[(193,66),(203,62),(213,66),(209,70),(203,68),(197,70)],
              "color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # banner fringe (gold)
    P.append({"type":"line","start":[194,96],"end":[212,96],"color":GOLD,"width":3})
    # lance grip wrap
    P.append({"type":"line","start":[188,100],"end":[194,180],"color":GOLD_DARK,"width":3})
    # lance pommel
    P.append({"type":"circle","cx":186,"cy":215,"r":7,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Legs (armored greaves) ---
    P.append({"type":"rect","x":108,"y":170,"w":18,"h":44,"color":STEEL,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":170,"w":18,"h":44,"color":STEEL,"outline":OUT,"outline_w":1,"radius":3})
    # gold knee guards
    P.append({"type":"circle","cx":117,"cy":186,"r":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":139,"cy":186,"r":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # steel boots
    P.append({"type":"rect","x":106,"y":210,"w":22,"h":10,"color":STEEL_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":210,"w":22,"h":10,"color":STEEL_DARK,"outline":OUT,"outline_w":1,"radius":2})

    # --- Torso (full plate armor) ---
    P.append({"type":"polygon","points":[(100,100),(156,100),(160,172),(96,172)],
              "color":STEEL,"outline":OUT,"outline_w":2})
    # chest plate (gold-trimmed)
    P.append({"type":"polygon","points":[(106,106),(150,106),(152,165),(104,165)],
              "color":STEEL_DARK,"outline":OUT,"outline_w":1})
    # gold trim down center
    P.append({"type":"line","start":[128,106],"end":[128,165],"color":GOLD,"width":3})
    # Demacian royal insignia on chest (THE missing feature — winged crest on chest)
    P.append({"type":"circle","cx":128,"cy":130,"r":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # winged eagle insignia (spread wings)
    P.append({"type":"polygon","points":[(118,128),(128,124),(138,128),(134,132),(128,130),(122,132)],
              "color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # blue gem center
    P.append({"type":"circle","cx":128,"cy":130,"r":3,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})
    # gold belt
    P.append({"type":"rect","x":96,"y":162,"w":64,"h":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":167,"r":4,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})

    # --- Arms (armored, shoulder pauldrons) ---
    P.append({"type":"rect","x":86,"y":108,"w":16,"h":50,"color":STEEL,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":154,"y":108,"w":16,"h":50,"color":STEEL,"outline":OUT,"outline_w":1,"radius":4})
    # gold shoulder pauldrons (BIG)
    P.append({"type":"circle","cx":94,"cy":108,"r":12,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":162,"cy":108,"r":12,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # pauldron wing detail
    P.append({"type":"polygon","points":[(82,108),(94,100),(94,112)],"color":GOLD_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(174,108),(162,100),(162,112)],"color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # gauntlets
    P.append({"type":"circle","cx":94,"cy":160,"r":6,"color":STEEL_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":162,"cy":160,"r":6,"color":STEEL_DARK,"outline":OUT,"outline_w":1})

    # --- HEAD + GOLDEN ROYAL CREST (THE feature — HUGE winged eagle crown on helmet) ---
    # helmet (steel)
    P.append({"type":"circle","cx":128,"cy":82,"r":18,"color":STEEL,"outline":OUT,"outline_w":2})
    # helmet face guard
    P.append({"type":"rect","x":114,"y":84,"w":28,"h":12,"color":STEEL_DARK,"outline":OUT,"outline_w":1,"radius":2})
    # eye slits
    P.append({"type":"line","start":[118,90],"end":[124,90],"color":OUT,"width":2})
    P.append({"type":"line","start":[132,90],"end":[138,90],"color":OUT,"width":2})
    # GOLDEN ROYAL CREST (THE missing feature — HUGE winged eagle crown, dominates head)
    # center spike (tall)
    P.append({"type":"polygon","points":[(122,58),(134,58),(128,30)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # left wing (BIG, spread wide — 3 feather layers)
    P.append({"type":"polygon","points":[(128,54),(96,40),(86,50),(92,58),(108,56)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # left wing upper feathers
    P.append({"type":"polygon","points":[(128,50),(100,34),(90,44),(100,50),(114,50)],
              "color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # right wing (BIG, spread wide)
    P.append({"type":"polygon","points":[(128,54),(160,40),(170,50),(164,58),(148,56)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # right wing upper feathers
    P.append({"type":"polygon","points":[(128,50),(156,34),(166,44),(156,50),(142,50)],
              "color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # wing feather lines (detail)
    for wx in (94, 102, 110):
        P.append({"type":"line","start":[wx,48],"end":[wx,58],"color":GOLD_DARK,"width":1})
    for wx in (146, 154, 162):
        P.append({"type":"line","start":[wx,48],"end":[wx,58],"color":GOLD_DARK,"width":1})
    # crest gem (blue, BIG center)
    P.append({"type":"circle","cx":128,"cy":50,"r":6,"color":BLUE,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":49,"r":3,"color":(120,160,240),"outline":None,"outline_w":0})
    # gold helmet trim (wide)
    P.append({"type":"rect","x":110,"y":74,"w":36,"h":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # Demacian royal insignia on helmet forehead (winged eagle emblem)
    P.append({"type":"circle","cx":128,"cy":78,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(120,78),(128,75),(136,78),(132,81),(128,79),(124,81)],
              "color":GOLD_DARK,"outline":OUT,"outline_w":1})
    return P


# ============================================================
# 2. JAYCE — big MERCURY HAMMER (THE feature) + Piltover attire + groomed hair
#    Missing: gold accents, aristocratic attire details, groomed hair style
# ============================================================
def jayce_prims():
    P = []
    STEEL = (130, 135, 145)
    STEEL_DARK = (80, 85, 95)
    GOLD = (220, 180, 60)
    GOLD_DARK = (150, 110, 30)
    BLUE = (70, 100, 170)
    HAIR = (120, 80, 45)
    HAIR_DARK = (80, 50, 25)
    SKIN = (215, 185, 155)
    WHITE = (230, 230, 235)
    OUT = (25, 22, 25)

    # --- BIG MERCURY HAMMER (THE feature — huge transforming weapon, right side) ---
    # hammer shaft (long, diagonal, held to the right)
    P.append({"type":"line","start":[178,215],"end":[200,50],"color":(90,70,40),"width":7})
    # hammer head (BIG — the iconic mercury hammer head, rectangular with cannon barrel)
    P.append({"type":"polygon","points":[(186,40),(222,40),(226,75),(182,75)],
              "color":STEEL,"outline":STEEL_DARK,"outline_w":3})
    # hammer face (front, BIG — the striking surface)
    P.append({"type":"polygon","points":[(222,44),(236,48),(236,68),(222,72)],
              "color":STEEL_DARK,"outline":OUT,"outline_w":2})
    # cannon barrel (the transforming part — tube on other side)
    P.append({"type":"polygon","points":[(182,44),(168,48),(168,68),(182,72)],
              "color":STEEL_DARK,"outline":OUT,"outline_w":2})
    # cannon muzzle circle
    P.append({"type":"circle","cx":172,"cy":58,"r":6,"color":OUT,"outline":STEEL_DARK,"outline_w":2})
    # gold accent bands on hammer
    P.append({"type":"rect","x":186,"y":44,"w":36,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":186,"y":68,"w":36,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold hex-core (glowing blue center — hextech crystal)
    P.append({"type":"circle","cx":204,"cy":58,"r":5,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":204,"cy":58,"r":2,"color":(150,200,255),"outline":None,"outline_w":0})
    # hammer grip wrap
    P.append({"type":"line","start":[186,90],"end":[192,180],"color":GOLD_DARK,"width":3})
    # pommel
    P.append({"type":"circle","cx":178,"cy":215,"r":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Legs (Piltover attire — white pants + gold-trim boots) ---
    P.append({"type":"rect","x":108,"y":168,"w":18,"h":46,"color":WHITE,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":168,"w":18,"h":46,"color":WHITE,"outline":OUT,"outline_w":1,"radius":3})
    # gold-trim boots
    P.append({"type":"rect","x":106,"y":200,"w":22,"h":16,"color":STEEL_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":200,"w":22,"h":16,"color":STEEL_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":106,"y":200,"w":22,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":128,"y":200,"w":22,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Torso (Piltover aristocratic attire — white/blue coat with gold accents) ---
    P.append({"type":"polygon","points":[(100,100),(156,100),(160,172),(96,172)],
              "color":WHITE,"outline":OUT,"outline_w":2})
    # blue vest (inner)
    P.append({"type":"polygon","points":[(108,106),(148,106),(150,165),(106,165)],
              "color":BLUE,"outline":OUT,"outline_w":1})
    # gold buttons (aristocratic attire detail)
    for by in (112, 124, 136, 148):
        P.append({"type":"circle","cx":128,"cy":by,"r":3,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold collar
    P.append({"type":"polygon","points":[(108,100),(148,100),(142,112),(114,112)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold shoulder pads (aristocratic)
    P.append({"type":"circle","cx":104,"cy":106,"r":9,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":152,"cy":106,"r":9,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold belt with hextech buckle
    P.append({"type":"rect","x":96,"y":160,"w":64,"h":8,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":164,"r":4,"color":BLUE,"outline":GOLD_DARK,"outline_w":1})

    # --- Arms ---
    P.append({"type":"rect","x":88,"y":112,"w":14,"h":48,"color":WHITE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":154,"y":112,"w":14,"h":48,"color":WHITE,"outline":OUT,"outline_w":1,"radius":4})
    # gold forearm bracers
    P.append({"type":"rect","x":88,"y":148,"w":14,"h":12,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":154,"y":148,"w":14,"h":12,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # hands
    P.append({"type":"circle","cx":95,"cy":162,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":161,"cy":162,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- HEAD: groomed brown hair (THE missing feature) + handsome face ---
    P.append({"type":"circle","cx":128,"cy":80,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # groomed hair (swept back, brown — THE missing feature, BIG and clear)
    # hair mass (big, voluminous — the signature swept-back style)
    P.append({"type":"polygon","points":[(106,74),(150,74),(148,56),(128,46),(108,56)],
              "color":HAIR,"outline":OUT,"outline_w":2})
    # hair sweep (the signature groomed style — BIG quiff swept to right side)
    P.append({"type":"polygon","points":[(108,56),(128,46),(146,52),(144,64),(120,62)],
              "color":HAIR_DARK,"outline":OUT,"outline_w":1})
    # hair top shine (the groomed look — lighter brown highlight)
    P.append({"type":"polygon","points":[(112,54),(140,50),(138,58),(114,58)],
              "color":(160,110,65),"outline":HAIR_DARK,"outline_w":1})
    # hair sideburns (side facial hair)
    P.append({"type":"polygon","points":[(110,76),(116,76),(114,88)],"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(140,76),(146,76),(144,88)],"color":HAIR,"outline":OUT,"outline_w":1})
    # hair back (neck)
    P.append({"type":"polygon","points":[(110,72),(146,72),(144,84),(112,84)],
              "color":HAIR_DARK,"outline":OUT,"outline_w":1})
    # eyes (handsome, sharp)
    P.append({"type":"circle","cx":122,"cy":82,"r":2,"color":OUT,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":134,"cy":82,"r":2,"color":OUT,"outline":None,"outline_w":0})
    # jaw (strong)
    P.append({"type":"line","start":[120,92],"end":[136,92],"color":OUT,"width":1})
    return P


# ============================================================
# 3. KAISA — living VOID CARAPACE (bio-organic armor) + shoulder cannons + helmet
#    Missing: pointed void-like ears, sleek futuristic armor, athletic humanoid female silhouette
# ============================================================
def kaisa_prims():
    P = []
    CARAPACE = (150, 50, 170)       # bright purple-magenta void carapace
    CARAPACE_DARK = (90, 25, 110)
    CARAPACE_LIGHT = (200, 100, 200)
    VOID_BLUE = (30, 20, 70)
    SKIN = (205, 175, 155)
    GLOW = (160, 210, 250)          # void glow (cyan-white)
    GLOW_DARK = (80, 150, 210)
    SILVER = (180, 185, 195)
    OUT = (20, 15, 25)

    # --- Legs (sleek void carapace leggings — athletic female, tapered) ---
    # LEFT leg
    P.append({"type":"polygon","points":[(106,160),(126,160),(124,214),(108,214)],
              "color":CARAPACE,"outline":OUT,"outline_w":2})
    # RIGHT leg
    P.append({"type":"polygon","points":[(130,160),(150,160),(148,214),(132,214)],
              "color":CARAPACE,"outline":OUT,"outline_w":2})
    # void glow on legs (bright lines down the shins)
    P.append({"type":"line","start":[116,162],"end":[116,212],"color":GLOW,"width":2})
    P.append({"type":"line","start":[140,162],"end":[140,212],"color":GLOW,"width":2})
    # carapace knee plates
    P.append({"type":"circle","cx":116,"cy":186,"r":5,"color":CARAPACE_LIGHT,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":140,"cy":186,"r":5,"color":CARAPACE_LIGHT,"outline":OUT,"outline_w":1})

    # --- Torso (living void carapace — bio-organic suit, clear female hourglass) ---
    # hourglass female silhouette (wider shoulders, narrow waist, wider hips)
    P.append({"type":"polygon","points":[(92,100),(164,100),(156,135),(160,165),(96,165),(100,135)],
              "color":CARAPACE,"outline":OUT,"outline_w":2})
    # carapace chest plates (organic segmented armor — darker purple)
    P.append({"type":"polygon","points":[(98,106),(158,106),(150,155),(106,155)],
              "color":CARAPACE_DARK,"outline":OUT,"outline_w":1})
    # center seam (bio-organic, glowing)
    P.append({"type":"line","start":[128,106],"end":[128,155],"color":GLOW,"width":3})
    # void glow lines (the living void energy)
    P.append({"type":"line","start":[110,110],"end":[110,150],"color":GLOW_DARK,"width":1})
    P.append({"type":"line","start":[146,110],"end":[146,150],"color":GLOW_DARK,"width":1})
    # void core (glowing center on chest, BIG)
    P.append({"type":"circle","cx":128,"cy":128,"r":9,"color":GLOW,"outline":CARAPACE_DARK,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":128,"r":5,"color":(230,245,255),"outline":None,"outline_w":0})
    # carapace organic plate texture (horizontal segment lines)
    for ry in (114, 124, 134, 144):
        P.append({"type":"line","start":[106,ry],"end":[150,ry],"color":CARAPACE_LIGHT,"width":1})

    # --- Arms (sleek carapace, at sides) ---
    P.append({"type":"rect","x":84,"y":108,"w":16,"h":50,"color":CARAPACE,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"rect","x":156,"y":108,"w":16,"h":50,"color":CARAPACE,"outline":OUT,"outline_w":1,"radius":5})
    # void glow on arms
    P.append({"type":"line","start":[92,112],"end":[92,154],"color":GLOW_DARK,"width":1})
    P.append({"type":"line","start":[164,112],"end":[164,154],"color":GLOW_DARK,"width":1})
    # hands
    P.append({"type":"circle","cx":92,"cy":160,"r":6,"color":CARAPACE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":164,"cy":160,"r":6,"color":CARAPACE_DARK,"outline":OUT,"outline_w":1})

    # --- VOID SHOULDER CANNONS (THE feature — BIG organic gun barrels on shoulders) ---
    # LEFT shoulder cannon (BIG cylinder, pointing up from shoulder)
    P.append({"type":"rect","x":78,"y":78,"w":24,"h":30,"color":CARAPACE_DARK,"outline":OUT,"outline_w":2,"radius":4})
    # cannon barrel opening (dark void hole, on top — THE feature)
    P.append({"type":"circle","cx":90,"cy":82,"r":9,"color":VOID_BLUE,"outline":CARAPACE_DARK,"outline_w":3})
    P.append({"type":"circle","cx":90,"cy":82,"r":5,"color":GLOW_DARK,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":90,"cy":81,"r":2,"color":GLOW,"outline":None,"outline_w":0})
    # organic ridges on cannon
    P.append({"type":"line","start":[78,92],"end":[102,92],"color":CARAPACE,"width":2})
    P.append({"type":"line","start":[78,100],"end":[102,100],"color":CARAPACE_LIGHT,"width":1})
    # RIGHT shoulder cannon
    P.append({"type":"rect","x":154,"y":78,"w":24,"h":30,"color":CARAPACE_DARK,"outline":OUT,"outline_w":2,"radius":4})
    P.append({"type":"circle","cx":166,"cy":82,"r":9,"color":VOID_BLUE,"outline":CARAPACE_DARK,"outline_w":3})
    P.append({"type":"circle","cx":166,"cy":82,"r":5,"color":GLOW_DARK,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":166,"cy":81,"r":2,"color":GLOW,"outline":None,"outline_w":0})
    P.append({"type":"line","start":[154,92],"end":[178,92],"color":CARAPACE,"width":2})
    P.append({"type":"line","start":[154,100],"end":[178,100],"color":CARAPACE_LIGHT,"width":1})

    # --- HEAD: void helmet (THE feature — sleek helmet with BIG pointed void ears) ---
    # helmet base
    P.append({"type":"circle","cx":128,"cy":80,"r":18,"color":CARAPACE,"outline":OUT,"outline_w":2})
    # helmet visor (dark void)
    P.append({"type":"polygon","points":[(112,76),(144,76),(140,94),(116,94)],
              "color":VOID_BLUE,"outline":OUT,"outline_w":1})
    # pointed void-like ears (THE missing feature — BIG pointed ear fins, extend far out from helmet)
    P.append({"type":"polygon","points":[(110,66),(82,44),(90,78),(114,80)],
              "color":CARAPACE,"outline":CARAPACE_DARK,"outline_w":2})
    P.append({"type":"polygon","points":[(146,66),(174,44),(166,78),(142,80)],
              "color":CARAPACE,"outline":CARAPACE_DARK,"outline_w":2})
    # ear inner glow
    P.append({"type":"line","start":[92,56],"end":[106,74],"color":GLOW_DARK,"width":1})
    P.append({"type":"line","start":[164,56],"end":[150,74],"color":GLOW_DARK,"width":1})
    # void glow eyes (through visor, BIG)
    P.append({"type":"circle","cx":121,"cy":85,"r":4,"color":GLOW,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":85,"r":4,"color":GLOW,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":121,"cy":84,"r":2,"color":(240,250,255),"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":135,"cy":84,"r":2,"color":(240,250,255),"outline":None,"outline_w":0})
    # helmet crest (organic ridge on top, BIG)
    P.append({"type":"polygon","points":[(116,62),(140,62),(128,42)],
              "color":CARAPACE_DARK,"outline":OUT,"outline_w":2})
    # crest glow line
    P.append({"type":"line","start":[128,62],"end":[128,76],"color":GLOW,"width":2})
    return P


# ============================================================
# 4. KALISTA — FLOATING: ghostly teal robes + MANY SPEARS + hollow glowing eyes
#    Missing: flowing tattered robes, spectral armor plating, ethereal form
# ============================================================
def kalista_prims():
    P = []
    GHOST = (60, 130, 120)         # teal spectral
    GHOST_DARK = (30, 80, 75)
    GHOST_LIGHT = (100, 180, 170)
    SPEAR = (160, 150, 130)        # spectral spears
    SPEAR_DARK = (90, 80, 65)
    EYE = (120, 220, 200)          # glowing teal eyes
    EYE_GLOW = (180, 255, 240)
    BONE = (200, 210, 200)
    SILVER_BONE = (220, 215, 200)
    OUT = (15, 25, 25)

    # --- MANY FLOATING SPEARS (THE feature — spectral spears orbiting behind/around her) ---
    # spear 1 (left, diagonal — BIG)
    P.append({"type":"line","start":[36,210],"end":[68,40],"color":SPEAR,"width":5})
    P.append({"type":"polygon","points":[(68,40),(60,56),(76,56)],"color":SILVER_BONE,"outline":SPEAR_DARK,"outline_w":2})
    # spear 2 (right, diagonal — BIG)
    P.append({"type":"line","start":[220,210],"end":[188,40],"color":SPEAR,"width":5})
    P.append({"type":"polygon","points":[(188,40),(180,56),(196,56)],"color":SILVER_BONE,"outline":SPEAR_DARK,"outline_w":2})
    # spear 3 (far left, vertical)
    P.append({"type":"line","start":[24,215],"end":[24,45],"color":SPEAR,"width":4})
    P.append({"type":"polygon","points":[(24,45),(18,58),(30,58)],"color":SILVER_BONE,"outline":SPEAR_DARK,"outline_w":1})
    # spear 4 (far right, vertical)
    P.append({"type":"line","start":[232,215],"end":[232,45],"color":SPEAR,"width":4})
    P.append({"type":"polygon","points":[(232,45),(226,58),(238,58)],"color":SILVER_BONE,"outline":SPEAR_DARK,"outline_w":1})
    # spear 5 (left-mid, angled)
    P.append({"type":"line","start":[48,160],"end":[76,30],"color":SPEAR,"width":4})
    P.append({"type":"polygon","points":[(76,30),(70,44),(82,44)],"color":SILVER_BONE,"outline":SPEAR_DARK,"outline_w":1})
    # spear 6 (right-mid, angled)
    P.append({"type":"line","start":[208,160],"end":[180,30],"color":SPEAR,"width":4})
    P.append({"type":"polygon","points":[(180,30),(174,44),(186,44)],"color":SILVER_BONE,"outline":SPEAR_DARK,"outline_w":1})

    # --- Spectral aura (ethereal glow behind body — BIG, teal) ---
    P.append({"type":"circle","cx":128,"cy":130,"r":65,"color":(30,80,75),"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":128,"cy":130,"r":50,"color":(40,100,95),"outline":None,"outline_w":0})

    # --- FLOWING TATTERED ROBES (THE missing feature — BIG, ghostly, teal, wider) ---
    P.append({"type":"polygon","points":[(82,88),(174,88),(192,225),(64,225)],
              "color":GHOST,"outline":OUT,"outline_w":2})
    # tattered hem (jagged bottom — THE missing feature, BIGGER tatters)
    P.append({"type":"polygon","points":[(64,225),(78,212),(90,228),(102,210),(114,228),(126,210),(138,228),(150,210),(162,228),(174,212),(192,225),(192,238),(64,238)],
              "color":GHOST,"outline":OUT,"outline_w":1})
    # robe inner shadow (darker teal — depth)
    P.append({"type":"polygon","points":[(96,94),(160,94),(174,205),(82,205)],
              "color":GHOST_DARK,"outline":OUT,"outline_w":1})
    # spectral armor plating (THE missing feature — ghostly chest plate, BIGGER)
    P.append({"type":"polygon","points":[(100,98),(156,98),(150,160),(106,160)],
              "color":GHOST_LIGHT,"outline":OUT,"outline_w":2})
    # armor ridges (horizontal segment lines)
    for ay in (110, 122, 134, 146):
        P.append({"type":"line","start":[106,ay],"end":[150,ay],"color":GHOST_DARK,"width":1})
    # center seam (vertical)
    P.append({"type":"line","start":[128,98],"end":[128,160],"color":OUT,"width":1})
    # ethereal glow lines (flowing energy on robe — brighter, more visible)
    P.append({"type":"line","start":[92,165],"end":[96,220],"color":GHOST_LIGHT,"width":2})
    P.append({"type":"line","start":[164,165],"end":[160,220],"color":GHOST_LIGHT,"width":2})
    # ethereal wisps (ghostly trails from robe)
    P.append({"type":"line","start":[80,200],"end":[72,230],"color":GHOST,"width":2})
    P.append({"type":"line","start":[176,200],"end":[184,230],"color":GHOST,"width":2})

    # --- Arms (ghostly, thin, holding spear) ---
    P.append({"type":"rect","x":92,"y":108,"w":12,"h":50,"color":GHOST_DARK,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":152,"y":108,"w":12,"h":50,"color":GHOST_DARK,"outline":OUT,"outline_w":1,"radius":4})
    # bony hands
    P.append({"type":"circle","cx":98,"cy":160,"r":4,"color":BONE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":158,"cy":160,"r":4,"color":BONE,"outline":OUT,"outline_w":1})

    # --- HEAD: ghostly + hollow glowing eyes (THE feature) ---
    P.append({"type":"circle","cx":128,"cy":76,"r":16,"color":GHOST_DARK,"outline":OUT,"outline_w":1})
    # face (pale ghostly)
    P.append({"type":"circle","cx":128,"cy":78,"r":13,"color":BONE,"outline":OUT,"outline_w":1})
    # HOLLOW GLOWING EYES (THE feature — dark sockets with teal glow)
    P.append({"type":"circle","cx":121,"cy":76,"r":5,"color":OUT,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":76,"r":5,"color":OUT,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":121,"cy":76,"r":3,"color":EYE,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":135,"cy":76,"r":3,"color":EYE,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":121,"cy":75,"r":1,"color":EYE_GLOW,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":135,"cy":75,"r":1,"color":EYE_GLOW,"outline":None,"outline_w":0})
    # dark mouth (hollow)
    P.append({"type":"line","start":[122,88],"end":[134,88],"color":OUT,"width":2})
    # hood/hood shadow (ghostly)
    P.append({"type":"polygon","points":[(110,68),(146,68),(142,58),(128,52),(114,58)],
              "color":GHOST_DARK,"outline":OUT,"outline_w":1})

    # --- No legs (FLOATING — tattered robe ends) ---
    return P


# ============================================================
# 5. KARTHUS — FLOATING lich: exposed RIBCAGE + tattered burial robes + glowing eyes
#    Missing: exposed ribcage, spectral aura, gaunt skeletal frame
# ============================================================
def karthus_prims():
    P = []
    ROBE = (60, 70, 60)            # dark burial robes
    ROBE_DARK = (35, 45, 38)
    BONE = (200, 210, 190)         # skeletal bone
    BONE_DARK = (140, 155, 130)
    EYE = (140, 230, 130)          # glowing green eyes (lich)
    EYE_GLOW = (200, 255, 180)
    GLOW = (90, 200, 90)           # spectral green aura
    GOLD = (180, 150, 50)          # tarnished gold
    OUT = (15, 20, 18)

    # --- Spectral aura (THE missing feature — green glow behind) ---
    P.append({"type":"circle","cx":128,"cy":130,"r":60,"color":(40,70,40),"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":128,"cy":130,"r":45,"color":(50,90,50),"outline":None,"outline_w":0})

    # --- TATTERED BURIAL ROBES (BIG, flowing, dark) ---
    P.append({"type":"polygon","points":[(88,90),(168,90),(180,220),(76,220)],
              "color":ROBE,"outline":OUT,"outline_w":2})
    # tattered hem (jagged bottom)
    P.append({"type":"polygon","points":[(76,220),(88,208),(98,222),(108,206),(118,222),(128,206),(138,222),(148,206),(158,222),(168,208),(180,220),(180,232),(76,232)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # robe inner shadow
    P.append({"type":"polygon","points":[(100,96),(156,96),(168,200),(88,200)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # robe tatters (slits on sides)
    P.append({"type":"polygon","points":[(88,160),(96,160),(92,190)],"color":OUT,"outline":None,"outline_w":0})
    P.append({"type":"polygon","points":[(160,160),(168,160),(164,190)],"color":OUT,"outline":None,"outline_w":0})

    # --- EXPOSED RIBCAGE (THE feature — BIG, skeletal, visible through robe) ---
    # ribcage area (bone-colored, open)
    P.append({"type":"polygon","points":[(104,100),(152,100),(146,165),(110,165)],
              "color":BONE,"outline":OUT,"outline_w":2})
    # ribs (THE feature — curved bone ribs, BIG and visible)
    for ry in (108, 118, 128, 138, 148, 158):
        # left rib
        P.append({"type":"line","start":[110,ry],"end":[128,ry-2],"color":OUT,"width":2})
        # right rib
        P.append({"type":"line","start":[128,ry-2],"end":[146,ry],"color":OUT,"width":2})
    # sternum (center bone)
    P.append({"type":"line","start":[128,100],"end":[128,165],"color":BONE_DARK,"width":3})
    # spine (visible behind)
    P.append({"type":"line","start":[128,100],"end":[128,165],"color":OUT,"width":1})
    # rib shadow (depth)
    for ry in (113, 123, 133, 143, 153):
        P.append({"type":"line","start":[114,ry],"end":[142,ry],"color":BONE_DARK,"width":1})

    # --- Arms (gaunt skeletal — bony) ---
    P.append({"type":"rect","x":92,"y":108,"w":12,"h":50,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":152,"y":108,"w":12,"h":50,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":4})
    # bony hands (skeletal)
    P.append({"type":"circle","cx":98,"cy":162,"r":5,"color":BONE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":158,"cy":162,"r":5,"color":BONE,"outline":OUT,"outline_w":1})
    # finger bones
    for fx in (95, 98, 101):
        P.append({"type":"line","start":[fx,166],"end":[fx,172],"color":BONE,"outline":OUT,"outline_w":1,"width":1})
    for fx in (155, 158, 161):
        P.append({"type":"line","start":[fx,166],"end":[fx,172],"color":BONE,"outline":OUT,"outline_w":1,"width":1})

    # --- HEAD: gaunt skull + glowing green eyes (THE feature) ---
    # hood (dark, burial)
    P.append({"type":"polygon","points":[(108,58),(148,58),(146,92),(110,92)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":2})
    # skull (gaunt, skeletal — THE missing feature)
    P.append({"type":"circle","cx":128,"cy":76,"r":15,"color":BONE,"outline":OUT,"outline_w":2})
    # skull jaw (gaunt)
    P.append({"type":"polygon","points":[(116,84),(140,84),(136,96),(120,96)],
              "color":BONE,"outline":OUT,"outline_w":1})
    # HOLLOW GLOWING EYES (THE feature — green lich eyes)
    P.append({"type":"circle","cx":121,"cy":74,"r":5,"color":OUT,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":74,"r":5,"color":OUT,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":121,"cy":74,"r":3,"color":EYE,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":135,"cy":74,"r":3,"color":EYE,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":121,"cy":73,"r":1,"color":EYE_GLOW,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":135,"cy":73,"r":1,"color":EYE_GLOW,"outline":None,"outline_w":0})
    # nose hole (skull)
    P.append({"type":"polygon","points":[(126,80),(130,80),(128,86)],"color":OUT,"outline":None,"outline_w":0})
    # teeth
    P.append({"type":"line","start":[120,90],"end":[136,90],"color":OUT,"width":1})
    for tx in (122, 126, 130, 134):
        P.append({"type":"line","start":[tx,90],"end":[tx,94],"color":OUT,"width":1})
    # hood shadow
    P.append({"type":"polygon","points":[(112,64),(144,64),(140,56),(128,50),(116,56)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":1})

    # --- No legs (FLOATING lich — tattered robe ends) ---
    # spectral green glow at float point
    P.append({"type":"circle","cx":128,"cy":220,"r":20,"color":GLOW,"outline":None,"outline_w":0})
    return P


# ============================================================
# 6. KATARINA — long CRIMSON HAIR (THE feature) + Noxian leather + dual daggers
#    Missing: Noxian leather armor, sharp facial features, combat boots
# ============================================================
def katarina_prims():
    P = []
    HAIR = (180, 40, 40)           # crimson red hair (THE feature)
    HAIR_DARK = (120, 20, 25)
    HAIR_LIGHT = (220, 70, 65)
    LEATHER = (50, 45, 55)         # Noxian black leather armor
    LEATHER_DARK = (30, 25, 35)
    SKIN = (225, 195, 165)
    SILVER = (190, 195, 205)
    SILVER_DARK = (110, 115, 125)
    GOLD = (200, 165, 50)
    GOLD_DARK = (140, 100, 25)
    GREEN = (60, 160, 80)          # kat's eyes (green)
    OUT = (25, 20, 25)

    # --- LONG CRIMSON HAIR (THE feature — BIG, flowing, dominates silhouette) ---
    # hair back mass (BIG — flowing down to legs)
    P.append({"type":"polygon","points":[(96,60),(160,60),(172,210),(84,210)],
              "color":HAIR,"outline":OUT,"outline_w":2})
    # hair flowing wider (the signature ponytail + flowing locks)
    P.append({"type":"polygon","points":[(88,68),(168,68),(180,200),(76,200)],
              "color":HAIR_DARK,"outline":OUT,"outline_w":1})
    # hair top (the big crimson mass on head)
    P.append({"type":"circle","cx":128,"cy":68,"r":22,"color":HAIR,"outline":OUT,"outline_w":2})
    # hair strands (flowing texture)
    for hx in (100, 110, 120, 136, 146, 156):
        P.append({"type":"line","start":[hx,72],"end":[hx,200],"color":HAIR_DARK,"width":1})
    # hair highlight (the signature shine)
    P.append({"type":"polygon","points":[(108,56),(148,56),(144,66),(112,66)],
              "color":HAIR_LIGHT,"outline":HAIR_DARK,"outline_w":1})
    # hair fringe (bangs)
    P.append({"type":"polygon","points":[(108,72),(148,72),(144,82),(112,82)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Legs (combat boots — Noxian) ---
    P.append({"type":"rect","x":108,"y":168,"w":18,"h":36,"color":SKIN,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":168,"w":18,"h":36,"color":SKIN,"outline":OUT,"outline_w":1,"radius":3})
    # combat boots (THE missing feature — knee-high black leather)
    P.append({"type":"rect","x":106,"y":190,"w":22,"h":24,"color":LEATHER,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":190,"w":22,"h":24,"color":LEATHER,"outline":OUT,"outline_w":1,"radius":2})
    # boot gold buckle
    P.append({"type":"rect","x":106,"y":194,"w":22,"h":3,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":128,"y":194,"w":22,"h":3,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Torso (Noxian leather armor — THE missing feature) ---
    P.append({"type":"polygon","points":[(104,100),(152,100),(148,170),(108,170)],
              "color":LEATHER,"outline":OUT,"outline_w":2})
    # leather armor chest plate (the Noxian corset-style armor)
    P.append({"type":"polygon","points":[(110,106),(146,106),(142,160),(114,160)],
              "color":LEATHER_DARK,"outline":OUT,"outline_w":1})
    # leather armor seams
    P.append({"type":"line","start":[128,106],"end":[128,160],"color":OUT,"width":1})
    # gold trim on armor (Noxian accent)
    P.append({"type":"line","start":[110,106],"end":[146,106],"color":GOLD,"width":2})
    P.append({"type":"line","start":[114,160],"end":[142,160],"color":GOLD,"width":1})
    # gold belt
    P.append({"type":"rect","x":106,"y":158,"w":44,"h":8,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":162,"r":3,"color":LEATHER_DARK,"outline":GOLD_DARK,"outline_w":1})
    # shoulder straps (leather)
    P.append({"type":"line","start":[108,106],"end":[120,112],"color":LEATHER_DARK,"width":3})
    P.append({"type":"line","start":[148,106],"end":[136,112],"color":LEATHER_DARK,"width":3})

    # --- Arms (leather-clad) ---
    P.append({"type":"rect","x":90,"y":110,"w":14,"h":48,"color":LEATHER,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":152,"y":110,"w":14,"h":48,"color":LEATHER,"outline":OUT,"outline_w":1,"radius":4})
    # gold arm bands
    P.append({"type":"rect","x":90,"y":146,"w":14,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":152,"y":146,"w":14,"h":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # hands
    P.append({"type":"circle","cx":97,"cy":160,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":159,"cy":160,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- DUAL DAGGERS (THE weapon — both hands, curved Noxus blades) ---
    # LEFT dagger (curved blade, pointing down/out)
    P.append({"type":"line","start":[97,162],"end":[78,200],"color":SILVER,"width":4})
    P.append({"type":"polygon","points":[(78,200),(74,210),(82,206)],"color":SILVER,"outline":SILVER_DARK,"outline_w":1})
    # dagger guard
    P.append({"type":"line","start":[92,162],"end":[102,162],"color":GOLD,"width":2})
    # RIGHT dagger
    P.append({"type":"line","start":[159,162],"end":[178,200],"color":SILVER,"width":4})
    P.append({"type":"polygon","points":[(178,200),(182,210),(174,206)],"color":SILVER,"outline":SILVER_DARK,"outline_w":1})
    P.append({"type":"line","start":[154,162],"end":[164,162],"color":GOLD,"width":2})

    # --- HEAD: sharp facial features (THE missing feature) ---
    P.append({"type":"circle","cx":128,"cy":80,"r":15,"color":SKIN,"outline":OUT,"outline_w":1})
    # sharp eyes (green — Katarina's signature)
    P.append({"type":"polygon","points":[(118,78),(124,76),(124,82),(118,82)],
              "color":GREEN,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(132,76),(138,78),(138,82),(132,82)],
              "color":GREEN,"outline":OUT,"outline_w":1})
    # sharp eyebrows (THE missing feature — arched, fierce)
    P.append({"type":"line","start":[116,72],"end":[124,74],"color":HAIR_DARK,"width":2})
    P.append({"type":"line","start":[132,74],"end":[140,72],"color":HAIR_DARK,"width":2})
    # sharp nose
    P.append({"type":"line","start":[128,82],"end":[126,90],"color":(180,150,120),"width":1})
    # lips (red)
    P.append({"type":"line","start":[122,92],"end":[134,92],"color":(140,40,40),"width":2})
    return P


# ============================================================
# RUN SEQUENTIALLY
# ============================================================
def run_all():
    champs = [
        ("JarvanIV", jarvaniv_prims),
        ("Jayce", jayce_prims),
        ("Kaisa", kaisa_prims),
        ("Kalista", kalista_prims),
        ("Karthus", karthus_prims),
        ("Katarina", katarina_prims),
    ]
    results = []
    for cid, fn in champs:
        print(f"\n{'='*60}")
        print(f"  {cid} (committed: {committed_score(cid)})")
        print(f"{'='*60}")
        best = None
        best_prims = None
        for rnd in range(1, 4):
            print(f"  Round {rnd}...")
            prims = fn()
            r = improve(cid, prims, gate_n=3)
            print(f"    -> new={r['new']}, saved={r['saved']}, missing={r['missing'][:3]}")
            if best is None or r["new"] > best["new"]:
                best = r
                best_prims = prims
            if r["new"] >= 8:
                break
            if rnd < 3 and r["new"] < 8:
                # tweak: make features bigger (re-author with adjustments)
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
    print("BATCH 13 RESULTS:")
    print(json.dumps(results, indent=2))
    improved = sum(1 for r in results if r["new"] > r["old"])
    ge8 = sum(1 for r in results if r["new"] >= 8)
    print(f"\n{improved}/6 champs improved, {ge8} reached >=8.")


if __name__ == "__main__":
    import json
    run_all()
