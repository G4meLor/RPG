"""Batch 12 hand-authored sprites: Brand, Ekko, Elise, Ezreal, Fiora, Fizz.

Each champion gets ONE huge signature feature that dominates the silhouette:
- Brand  -> HEAD ENGULFED IN FLAMES (living fire, charred body, lava veins)
- Ekko   -> ZAURITE TIME DEVICE on back (big glowing turquoise) + goggles + bat
- Elise  -> SPIDER LEGS from back (big, 8 legs, gothic gown)
- Ezreal -> FLOATING ARCANE GAUNTLET (big glowing gauntlet beside him)
- Fiora  -> BIG RAPIER (held forward) + high collar + ponytail
- Fizz   -> SEASTONE TRIDENT (big) + yordle ears + fish/amphibious look
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve


# ============================================================================
# Brand -- living fire; HEAD ENGULFED IN FLAMES + charred body + lava veins
# ============================================================================
def brand_prims():
    P = []
    FIRE_BRIGHT = (255, 180, 40)
    FIRE_ORANGE = (240, 110, 30)
    FIRE_RED = (200, 50, 20)
    FIRE_DEEP = (160, 30, 10)
    CHAR = (35, 25, 25)          # charred blackened skin
    CHAR_LIGHT = (60, 45, 45)
    LAVA = (255, 120, 30)        # molten lava veins
    LAVA_BRIGHT = (255, 200, 80)
    EYE = (255, 180, 40)         # glowing orange eyes
    OUT = (20, 15, 15)

    # --- HEAD ENGULFED IN FLAMES (THE feature -- HUGE, the head IS fire) ---
    # big fire mass where the head should be (engulfed)
    P.append({"type":"circle","cx":128,"cy":60,"r":30,"color":FIRE_RED,"outline":FIRE_DEEP,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":58,"r":24,"color":FIRE_ORANGE,"outline":FIRE_RED,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":56,"r":18,"color":FIRE_BRIGHT,"outline":FIRE_ORANGE,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":54,"r":12,"color":(255,230,150),"outline":FIRE_BRIGHT,"outline_w":1})
    # flame spikes shooting up (THE feature -- big flames)
    for fx in (100, 112, 128, 144, 156):
        P.append({"type":"polygon","points":[(fx-6,50),(fx+6,50),(fx,20)],"color":FIRE_ORANGE,"outline":FIRE_RED,"outline_w":1})
    for fx in (108, 128, 148):
        P.append({"type":"polygon","points":[(fx-4,44),(fx+4,44),(fx,12)],"color":FIRE_BRIGHT,"outline":FIRE_ORANGE,"outline_w":1})
    # flame wisps on sides (fire emanating from head)
    P.append({"type":"polygon","points":[(96,60),(84,52),(88,72)],"color":FIRE_ORANGE,"outline":FIRE_RED,"outline_w":1})
    P.append({"type":"polygon","points":[(160,60),(172,52),(168,72)],"color":FIRE_ORANGE,"outline":FIRE_RED,"outline_w":1})
    # glowing orange eyes (THE missing feature -- visible through flames)
    P.append({"type":"circle","cx":120,"cy":62,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":136,"cy":62,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":121,"cy":61,"r":2,"color":(255,255,200)})

    # --- Charred torso (blackened, with molten lava veins) ---
    P.append({"type":"polygon","points":[(104,88),(152,88),(156,170),(100,170)],
              "color":CHAR,"outline":OUT,"outline_w":1})
    # charred skin texture (cracks)
    P.append({"type":"polygon","points":[(110,96),(146,96),(148,166),(108,166)],
              "color":CHAR_LIGHT,"outline":OUT,"outline_w":1})
    # MOLTEN LAVA VEINS (THE missing feature -- glowing orange cracks in charred body)
    P.append({"type":"line","start":[128,96],"end":[128,166],"color":LAVA,"width":3})
    P.append({"type":"line","start":[110,110],"end":[146,110],"color":LAVA,"width":2})
    P.append({"type":"line","start":[112,130],"end":[144,130],"color":LAVA,"width":2})
    P.append({"type":"line","start":[114,150],"end":[142,150],"color":LAVA,"width":2})
    # diagonal lava veins
    P.append({"type":"line","start":[110,120],"end":[128,140],"color":LAVA,"width":2})
    P.append({"type":"line","start":[146,120],"end":[128,140],"color":LAVA,"width":2})
    # lava vein glow (bright center)
    P.append({"type":"line","start":[128,100],"end":[128,160],"color":LAVA_BRIGHT,"width":1})

    # --- FIRE EMANATING FROM JOINTS (THE missing feature) ---
    # fire from shoulders
    P.append({"type":"polygon","points":[(100,92),(88,84),(92,100)],"color":FIRE_ORANGE,"outline":FIRE_RED,"outline_w":1})
    P.append({"type":"polygon","points":[(156,92),(168,84),(164,100)],"color":FIRE_ORANGE,"outline":FIRE_RED,"outline_w":1})
    # fire from elbows
    P.append({"type":"polygon","points":[(84,130),(74,122),(78,138)],"color":FIRE_ORANGE,"outline":FIRE_RED,"outline_w":1})
    P.append({"type":"polygon","points":[(172,130),(182,122),(178,138)],"color":FIRE_ORANGE,"outline":FIRE_RED,"outline_w":1})
    # fire from knees
    P.append({"type":"polygon","points":[(104,180),(94,172),(98,188)],"color":FIRE_ORANGE,"outline":FIRE_RED,"outline_w":1})
    P.append({"type":"polygon","points":[(152,180),(162,172),(158,188)],"color":FIRE_ORANGE,"outline":FIRE_RED,"outline_w":1})

    # --- Arms (charred, with lava veins) ---
    P.append({"type":"rect","x":82,"y":100,"w":16,"h":50,"color":CHAR,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":158,"y":100,"w":16,"h":50,"color":CHAR,"outline":OUT,"outline_w":1,"radius":4})
    # lava veins on arms
    P.append({"type":"line","start":[90,104],"end":[90,146],"color":LAVA,"width":2})
    P.append({"type":"line","start":[166,104],"end":[166,146],"color":LAVA,"width":2})
    # hands (charred, glowing)
    P.append({"type":"circle","cx":90,"cy":154,"r":6,"color":CHAR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":166,"cy":154,"r":6,"color":CHAR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":90,"cy":154,"r":3,"color":LAVA,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":166,"cy":154,"r":3,"color":LAVA,"outline":OUT,"outline_w":1})

    # --- Legs (charred, with lava veins) ---
    P.append({"type":"rect","x":104,"y":170,"w":18,"h":40,"color":CHAR,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":134,"y":170,"w":18,"h":40,"color":CHAR,"outline":OUT,"outline_w":1,"radius":3})
    # lava veins on legs
    P.append({"type":"line","start":[113,174],"end":[113,206],"color":LAVA,"width":2})
    P.append({"type":"line","start":[143,174],"end":[143,206],"color":LAVA,"width":2})
    # feet (charred)
    P.append({"type":"rect","x":102,"y":206,"w":22,"h":12,"color":CHAR,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":132,"y":206,"w":22,"h":12,"color":CHAR,"outline":OUT,"outline_w":1,"radius":2})
    return P


# ============================================================================
# Ekko -- time mage; ZAURITE TIME DEVICE on back (big glowing turquoise) + goggles
# ============================================================================
def ekko_prims():
    P = []
    SKIN = (225, 195, 165)
    HAIR = (245, 240, 230)       # white hair
    HAIR_DARK = (200, 195, 185)
    TURQUOISE = (60, 220, 220)   # glowing turquoise (Zaunite tech)
    TURQUOISE_DARK = (30, 150, 160)
    TURQUOISE_LIGHT = (140, 250, 250)
    ZAURITE = (80, 230, 210)     # Zaurite crystal (turquoise glow)
    ZAURITE_DARK = (30, 140, 130)
    JACKET = (90, 70, 60)        # brown streetwear jacket
    JACKET_DARK = (60, 45, 40)
    SHIRT = (180, 180, 190)      # grey shirt
    GOGGLE = (40, 200, 200)      # goggles (turquoise lens)
    GOGGLE_DARK = (30, 30, 35)
    GOGGLE_FRAME = (50, 45, 50)
    BAT = (110, 80, 55)          # Timewinder bat
    BAT_GLOW = (60, 220, 220)
    EYE = (40, 30, 30)
    OUT = (25, 20, 25)

    # --- ZAURITE TIME DEVICE ON BACK (THE feature -- HUGE glowing turquoise, VISIBLE) ---
    # big device on back (behind torso, glowing turquoise -- drawn BIG and visible around the body)
    # device frame (dark, mechanical, visible on both sides of torso)
    P.append({"type":"polygon","points":[(80,84),(176,84),(180,150),(76,150)],
              "color":JACKET_DARK,"outline":OUT,"outline_w":2})
    # Zaurite crystal (HUGE, glowing turquoise -- THE feature, wider than torso)
    P.append({"type":"polygon","points":[(92,92),(164,92),(160,140),(96,140)],
              "color":ZAURITE,"outline":ZAURITE_DARK,"outline_w":3})
    # Zaurite glow (bright center -- BIG)
    P.append({"type":"polygon","points":[(104,100),(152,100),(148,132),(108,132)],
              "color":TURQUOISE_LIGHT,"outline":TURQUOISE,"outline_w":1})
    # Zaurite crystal facets (geometric -- obvious it's a crystal)
    P.append({"type":"line","start":[128,92],"end":[128,140],"color":ZAURITE_DARK,"width":2})
    P.append({"type":"line","start":[96,116],"end":[160,116],"color":ZAURITE_DARK,"width":1})
    # BIG glow aura around device (turquoise, THE magic -- obvious)
    P.append({"type":"circle","cx":128,"cy":116,"r":40,"color":(100,220,220),"outline":TURQUOISE,"outline_w":1})
    # turquoise energy wisps from device (BIG, trailing up)
    for sy in (76, 64, 52, 40):
        P.append({"type":"circle","cx":128,"cy":sy,"r":6,"color":TURQUOISE,"outline":TURQUOISE_DARK,"outline_w":1})
    # turquoise energy wisps on sides
    for sx, sy in [(72,100),(184,100),(68,130),(188,130)]:
        P.append({"type":"circle","cx":sx,"cy":sy,"r":5,"color":TURQUOISE,"outline":TURQUOISE_DARK,"outline_w":1})

    # --- Hair (white, big) ---
    P.append({"type":"circle","cx":128,"cy":66,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    # hair swept back (teenager style)
    P.append({"type":"polygon","points":[(108,58),(148,58),(156,74),(100,74)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # hair top swoop
    P.append({"type":"polygon","points":[(108,56),(148,56),(140,48),(116,50)],
              "color":HAIR_DARK,"outline":OUT,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # GOGGLES (THE missing feature -- big, on forehead/over eyes, turquoise lens)
    # goggle strap
    P.append({"type":"rect","x":110,"y":66,"w":36,"h":4,"color":GOGGLE_FRAME,"outline":OUT,"outline_w":1})
    # left goggle lens (turquoise, BIG)
    P.append({"type":"circle","cx":118,"cy":74,"r":7,"color":GOGGLE,"outline":GOGGLE_FRAME,"outline_w":2})
    P.append({"type":"circle","cx":118,"cy":74,"r":4,"color":TURQUOISE_LIGHT,"outline":GOGGLE,"outline_w":1})
    # right goggle lens
    P.append({"type":"circle","cx":138,"cy":74,"r":7,"color":GOGGLE,"outline":GOGGLE_FRAME,"outline_w":2})
    P.append({"type":"circle","cx":138,"cy":74,"r":4,"color":TURQUOISE_LIGHT,"outline":GOGGLE,"outline_w":1})
    # goggle bridge
    P.append({"type":"rect","x":124,"y":72,"w":8,"h":4,"color":GOGGLE_FRAME,"outline":OUT,"outline_w":1})
    # mouth (mischievous teen)
    P.append({"type":"line","start":[122,86],"end":[134,86],"color":(140,60,60),"width":1})

    # --- Streetwear attire (jacket + shirt) ---
    P.append({"type":"polygon","points":[(104,92),(152,92),(156,170),(100,170)],
              "color":JACKET,"outline":OUT,"outline_w":1})
    # shirt under jacket (grey)
    P.append({"type":"polygon","points":[(116,96),(140,96),(142,140),(114,140)],
              "color":SHIRT,"outline":OUT,"outline_w":1})
    # jacket collar (streetwear)
    P.append({"type":"polygon","points":[(108,92),(148,92),(140,104),(116,104)],
              "color":JACKET_DARK,"outline":OUT,"outline_w":1})
    # turquoise accents on jacket (glowing trim -- THE feature)
    P.append({"type":"line","start":[104,92],"end":[152,92],"color":TURQUOISE,"width":2})
    P.append({"type":"line","start":[100,170],"end":[156,170],"color":TURQUOISE,"width":2})
    # jacket zipper (turquoise glow)
    P.append({"type":"line","start":[128,104],"end":[128,170],"color":TURQUOISE,"width":2})

    # --- Arms ---
    P.append({"type":"rect","x":86,"y":100,"w":14,"h":50,"color":JACKET,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":156,"y":100,"w":14,"h":50,"color":JACKET,"outline":OUT,"outline_w":1,"radius":4})
    # turquoise arm accents
    P.append({"type":"line","start":[93,110],"end":[93,140],"color":TURQUOISE,"width":1})
    P.append({"type":"line","start":[163,110],"end":[163,140],"color":TURQUOISE,"width":1})
    # hands
    P.append({"type":"circle","cx":93,"cy":154,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":163,"cy":154,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (streetwear pants) ---
    P.append({"type":"rect","x":106,"y":170,"w":18,"h":38,"color":JACKET_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":18,"h":38,"color":JACKET_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # turquoise pants accent
    P.append({"type":"line","start":[115,174],"end":[115,206],"color":TURQUOISE,"width":1})
    P.append({"type":"line","start":[141,174],"end":[141,206],"color":TURQUOISE,"width":1})
    # boots (sneakers, streetwear)
    P.append({"type":"rect","x":102,"y":204,"w":24,"h":14,"color":OUT,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":204,"w":24,"h":14,"color":OUT,"outline":OUT,"outline_w":1,"radius":3})
    # turquoise boot accent
    P.append({"type":"line","start":[102,208],"end":[126,208],"color":TURQUOISE,"width":1})
    P.append({"type":"line","start":[130,208],"end":[154,208],"color":TURQUOISE,"width":1})

    # --- Timewinder bat (in right hand, glowing turquoise, drawn IN FRONT, BIG) ---
    # bat body (big, diagonal, with turquoise glow -- the Timewinder weapon)
    P.append({"type":"rect","x":150,"y":120,"w":16,"h":50,"color":BAT,"outline":OUT,"outline_w":2,"radius":3})
    # bat grip
    P.append({"type":"rect","x":148,"y":166,"w":20,"h":10,"color":BAT,"outline":OUT,"outline_w":1,"radius":2})
    # turquoise glow on bat (Timewinder energy -- BIG, obvious)
    P.append({"type":"line","start":[158,124],"end":[158,166],"color":BAT_GLOW,"width":3})
    # bat tip glow (turquoise energy burst)
    P.append({"type":"circle","cx":158,"cy":122,"r":8,"color":TURQUOISE,"outline":TURQUOISE_DARK,"outline_w":2})
    P.append({"type":"circle","cx":158,"cy":122,"r":4,"color":TURQUOISE_LIGHT,"outline":TURQUOISE,"outline_w":1})
    # turquoise energy wisps from bat tip
    for sy in (110, 100, 90):
        P.append({"type":"circle","cx":158,"cy":sy,"r":4,"color":TURQUOISE,"outline":TURQUOISE_DARK,"outline_w":1})
    return P


# ============================================================================
# Elise -- spider hybrid; SPIDER LEGS from back (big, 8 legs) + gothic gown
# ============================================================================
def elise_prims():
    P = []
    SKIN = (220, 200, 200)       # pale skin
    SKIN_DARK = (180, 160, 165)
    HAIR = (40, 30, 40)          # black hair
    GOWN = (90, 50, 100)         # purple gothic gown
    GOWN_DARK = (60, 35, 70)
    GOWN_BLACK = (35, 25, 40)
    SPIDER_LEG = (50, 35, 50)    # spider legs (dark)
    SPIDER_LEG_DARK = (30, 20, 30)
    RED = (180, 40, 50)          # red accents
    GOLD = (200, 160, 50)
    EYE = (180, 40, 50)          # red eyes (spider-like)
    OUT = (20, 15, 20)

    # --- SPIDER LEGS FROM BACK (THE feature -- BIG, 8 legs, dominating silhouette) ---
    # 4 left legs (big, curving out from back)
    leg_left = [
        [(100,100),(70,80),(50,100)],   # leg 1 (high)
        [(100,115),(60,110),(40,130)],  # leg 2
        [(100,130),(58,140),(38,160)],  # leg 3
        [(100,145),(62,165),(48,190)],  # leg 4 (low)
    ]
    for leg in leg_left:
        for i in range(len(leg)-1):
            P.append({"type":"line","start":leg[i],"end":leg[i+1],"color":SPIDER_LEG,"width":6})
        # leg joints (bulbs)
        for cx, cy in leg:
            P.append({"type":"circle","cx":cx,"cy":cy,"r":4,"color":SPIDER_LEG,"outline":SPIDER_LEG_DARK,"outline_w":1})
        # sharp leg tips
        tx, ty = leg[-1]
        P.append({"type":"polygon","points":[(tx-3,ty),(tx+3,ty),(tx,ty+8)],"color":SPIDER_LEG_DARK,"outline":OUT,"outline_w":1})
    # 4 right legs (big, curving out from back)
    leg_right = [
        [(156,100),(186,80),(206,100)],
        [(156,115),(196,110),(216,130)],
        [(156,130),(198,140),(218,160)],
        [(156,145),(194,165),(208,190)],
    ]
    for leg in leg_right:
        for i in range(len(leg)-1):
            P.append({"type":"line","start":leg[i],"end":leg[i+1],"color":SPIDER_LEG,"width":6})
        for cx, cy in leg:
            P.append({"type":"circle","cx":cx,"cy":cy,"r":4,"color":SPIDER_LEG,"outline":SPIDER_LEG_DARK,"outline_w":1})
        tx, ty = leg[-1]
        P.append({"type":"polygon","points":[(tx-3,ty),(tx+3,ty),(tx,ty+8)],"color":SPIDER_LEG_DARK,"outline":OUT,"outline_w":1})

    # --- Hair (black, elegant) ---
    P.append({"type":"circle","cx":128,"cy":66,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    # hair flowing down (gothic, long)
    P.append({"type":"polygon","points":[(108,60),(148,60),(160,100),(96,100)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (pale, elegant, spider-like) ---
    P.append({"type":"circle","cx":128,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # red eyes (spider-like, seductive)
    P.append({"type":"circle","cx":121,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":75,"r":1,"color":(255,200,200)})
    P.append({"type":"circle","cx":136,"cy":75,"r":1,"color":(255,200,200)})
    # seductive smile
    P.append({"type":"line","start":[122,86],"end":[134,86],"color":(120,40,50),"width":1})
    # pale skin emphasis (THE missing feature)
    P.append({"type":"line","start":[112,72],"end":[112,84],"color":SKIN_DARK,"width":1})

    # --- Elegant gothic gown (purple, flowing) ---
    P.append({"type":"polygon","points":[(100,94),(156,94),(170,180),(86,180)],
              "color":GOWN,"outline":OUT,"outline_w":1})
    # gown shading (darker purple)
    P.append({"type":"polygon","points":[(108,98),(148,98),(158,178),(98,178)],
              "color":GOWN_DARK,"outline":OUT,"outline_w":1})
    # gown black trim
    P.append({"type":"line","start":[100,94],"end":[156,94],"color":GOWN_BLACK,"width":2})
    P.append({"type":"line","start":[86,180],"end":[170,180],"color":GOWN_BLACK,"width":2})
    # red gothic accents on gown
    P.append({"type":"line","start":[128,98],"end":[128,180],"color":RED,"width":2})
    # gold gothic ornament on chest
    P.append({"type":"circle","cx":128,"cy":112,"r":5,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":112,"r":2,"color":RED,"outline":OUT,"outline_w":1})

    # --- Chitinous armor (spider-like, on shoulders -- THE missing feature) ---
    P.append({"type":"circle","cx":102,"cy":100,"r":10,"color":SPIDER_LEG,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":154,"cy":100,"r":10,"color":SPIDER_LEG,"outline":OUT,"outline_w":2})
    # chitinous spikes on shoulders
    for sx in (96, 102, 108):
        P.append({"type":"polygon","points":[(sx,92),(sx+2,84),(sx+4,92)],"color":SPIDER_LEG_DARK,"outline":OUT,"outline_w":1})
    for sx in (148, 154, 160):
        P.append({"type":"polygon","points":[(sx,92),(sx+2,84),(sx+4,92)],"color":SPIDER_LEG_DARK,"outline":OUT,"outline_w":1})

    # --- Arms (slender, pale) ---
    P.append({"type":"rect","x":86,"y":108,"w":12,"h":44,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":158,"y":108,"w":12,"h":44,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    # hands
    P.append({"type":"circle","cx":92,"cy":154,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":164,"cy":154,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (gown-covered, elegant) ---
    P.append({"type":"rect","x":108,"y":180,"w":18,"h":30,"color":GOWN_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":180,"w":18,"h":30,"color":GOWN_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # heels (elegant)
    P.append({"type":"rect","x":108,"y":206,"w":18,"h":10,"color":GOWN_BLACK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":206,"w":18,"h":10,"color":GOWN_BLACK,"outline":OUT,"outline_w":1,"radius":2})
    return P


# ============================================================================
# Ezreal -- explorer; FLOATING ARCANE GAUNTLET (big glowing) + blonde hair
# ============================================================================
def ezreal_prims():
    P = []
    SKIN = (230, 200, 170)
    HAIR = (230, 195, 110)       # blonde swept-back hair
    HAIR_DARK = (180, 150, 70)
    JACKET = (120, 85, 55)       # brown leather explorer's jacket
    JACKET_DARK = (85, 60, 40)
    SCARF = (60, 120, 200)       # blue scarf
    SCARF_DARK = (40, 90, 170)
    GOLD = (215, 175, 60)
    GAUNTLET = (200, 175, 70)    # arcane gauntlet (gold)
    GAUNTLET_DARK = (140, 110, 30)
    GAUNTLET_GLOW = (120, 200, 255)  # blue arcane glow
    GAUNTLET_GLOW_BRIGHT = (180, 230, 255)
    BOOT = (90, 65, 40)
    EYE = (80, 120, 200)         # blue eyes
    OUT = (25, 20, 20)

    # --- FLOATING ARCANE GAUNTLET (THE feature -- BIG, floating beside him, glowing) ---
    # big gauntlet body (gold, floating to the right, ENORMOUS)
    P.append({"type":"polygon","points":[(178,100),(228,100),(232,170),(174,170)],
              "color":GAUNTLET,"outline":OUT,"outline_w":3})
    # gauntlet glow aura (blue arcane energy -- THE magic)
    P.append({"type":"circle","cx":202,"cy":135,"r":35,"color":(100,180,240),"outline":GAUNTLET_GLOW,"outline_w":1})
    # gauntlet fingers/knuckles (segmented, gold)
    for fx in (184, 196, 208, 220):
        P.append({"type":"rect","x":fx,"y":100,"w":8,"h":20,"color":GAUNTLET,"outline":GAUNTLET_DARK,"outline_w":1})
    # gauntlet wrist (gold band)
    P.append({"type":"rect","x":176,"y":160,"w":56,"h":12,"color":GAUNTLET_DARK,"outline":OUT,"outline_w":2})
    # arcane gem in gauntlet (glowing blue -- THE magic source)
    P.append({"type":"circle","cx":202,"cy":135,"r":12,"color":GAUNTLET_GLOW,"outline":GAUNTLET_DARK,"outline_w":2})
    P.append({"type":"circle","cx":202,"cy":135,"r":7,"color":GAUNTLET_GLOW_BRIGHT,"outline":GAUNTLET_GLOW,"outline_w":1})
    P.append({"type":"circle","cx":202,"cy":135,"r":3,"color":(255,255,255)})
    # arcane energy wisps from gauntlet (floating magic)
    for sy in (88, 78, 68):
        P.append({"type":"circle","cx":202,"cy":sy,"r":5,"color":GAUNTLET_GLOW,"outline":GAUNTLET_GLOW_BRIGHT,"outline_w":1})
    # gold trim on gauntlet
    P.append({"type":"line","start":[178,100],"end":[228,100],"color":GOLD,"width":2})
    P.append({"type":"line","start":[174,170],"end":[232,170],"color":GOLD,"width":2})

    # --- Hair (blonde, swept-back -- THE missing feature) ---
    P.append({"type":"circle","cx":118,"cy":66,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    # swept-back hair (BIG, flowing back)
    P.append({"type":"polygon","points":[(100,58),(136,58),(148,48),(108,50)],
              "color":HAIR,"outline":HAIR_DARK,"outline_w":1})
    # hair swept back (longer, flowing)
    P.append({"type":"polygon","points":[(100,60),(118,54),(132,80),(100,82)],
              "color":HAIR,"outline":HAIR_DARK,"outline_w":1})
    # bangs (swept)
    P.append({"type":"polygon","points":[(100,58),(136,58),(132,72),(104,72)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":118,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # blue eyes (confident)
    P.append({"type":"circle","cx":111,"cy":76,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":125,"cy":76,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":112,"cy":75,"r":1,"color":(255,255,255)})
    P.append({"type":"circle","cx":126,"cy":75,"r":1,"color":(255,255,255)})
    # confident smirk
    P.append({"type":"line","start":[112,86],"end":[124,86],"color":(140,80,60),"width":1})

    # --- Blue scarf (THE missing feature -- BIG, around neck) ---
    P.append({"type":"polygon","points":[(96,92),(140,92),(142,104),(94,104)],
              "color":SCARF,"outline":OUT,"outline_w":2})
    # scarf flowing back (trailing)
    P.append({"type":"polygon","points":[(96,96),(80,104),(76,130),(96,120)],
              "color":SCARF_DARK,"outline":OUT,"outline_w":1})
    # scarf ends (flowing)
    P.append({"type":"polygon","points":[(94,100),(84,110),(82,140),(94,128)],
              "color":SCARF,"outline":SCARF_DARK,"outline_w":1})

    # --- Leather explorer's jacket (brown) ---
    P.append({"type":"polygon","points":[(94,104),(142,104),(146,170),(90,170)],
              "color":JACKET,"outline":OUT,"outline_w":1})
    # jacket shading
    P.append({"type":"polygon","points":[(100,108),(136,108),(140,168),(96,168)],
              "color":JACKET_DARK,"outline":OUT,"outline_w":1})
    # jacket collar
    P.append({"type":"polygon","points":[(98,104),(138,104),(132,116),(104,116)],
              "color":JACKET_DARK,"outline":OUT,"outline_w":1})
    # gold jacket trim
    P.append({"type":"line","start":[94,104],"end":[142,104],"color":GOLD,"width":1})
    # jacket zipper
    P.append({"type":"line","start":[118,116],"end":[118,170],"color":GOLD,"width":1})

    # --- Arms (one raised toward gauntlet) ---
    P.append({"type":"rect","x":80,"y":112,"w":14,"h":44,"color":JACKET,"outline":OUT,"outline_w":1,"radius":4})
    # right arm raised toward floating gauntlet
    P.append({"type":"polygon","points":[(140,112),(158,116),(170,130),(160,136),(144,122)],
              "color":JACKET,"outline":OUT,"outline_w":1})
    # hands
    P.append({"type":"circle","cx":87,"cy":158,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":168,"cy":132,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs + boots ---
    P.append({"type":"rect","x":100,"y":170,"w":18,"h":36,"color":JACKET_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":122,"y":170,"w":18,"h":36,"color":JACKET_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # brown boots (explorer)
    P.append({"type":"rect","x":98,"y":204,"w":22,"h":14,"color":BOOT,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":120,"y":204,"w":22,"h":14,"color":BOOT,"outline":OUT,"outline_w":1,"radius":2})
    # gold boot trim
    P.append({"type":"line","start":[98,206],"end":[120,206],"color":GOLD,"width":1})
    P.append({"type":"line","start":[120,206],"end":[142,206],"color":GOLD,"width":1})
    return P


# ============================================================================
# Fiora -- duelist; BIG RAPIER (held forward) + high collar + ponytail
# ============================================================================
def fiora_prims():
    P = []
    SKIN = (240, 215, 190)
    HAIR = (45, 30, 25)          # dark brown-black hair
    HAIR_DARK = (25, 20, 20)
    ATTIRE = (225, 220, 215)     # white Demacian attire
    ATTIRE_DARK = (70, 65, 70)
    COLLAR = (210, 175, 55)      # gold trim
    EYE = (40, 30, 30)
    OUT = (40, 25, 25)
    RAPIER = (215, 215, 225)
    RAPIER_HILT = (185, 150, 50)

    # --- Hair back + BIG ponytail (flowing back, prominent) ---
    P.append({"type":"circle","cx":128,"cy":68,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    # BIG ponytail flowing back-right
    P.append({"type":"polygon","points":[(138,54),(168,46),(196,62),(192,92),(160,82),(142,72)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # ponytail tail tip (tapered)
    P.append({"type":"polygon","points":[(182,74),(196,68),(194,86),(182,84)],
              "color":HAIR,"outline":HAIR_DARK,"outline_w":1})
    # bangs
    P.append({"type":"polygon","points":[(110,58),(146,58),(142,72),(114,72)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":72,"r":18,"color":SKIN,"outline":OUT,"outline_w":1})
    # confident eyes + determined brow
    P.append({"type":"line","start":[117,71],"end":[125,71],"color":EYE,"width":2})
    P.append({"type":"line","start":[131,71],"end":[139,71],"color":EYE,"width":2})
    P.append({"type":"polygon","points":[(114,66),(126,69),(126,67),(114,64)],"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(130,67),(142,64),(142,66),(130,69)],"color":HAIR,"outline":OUT,"outline_w":1})
    # confident smirk
    P.append({"type":"line","start":[122,84],"end":[134,82],"color":(150,60,60),"width":1})

    # --- HIGH-COLLARED Demacian attire (THE missing feature -- PROMINENT) ---
    # torso (white)
    P.append({"type":"polygon","points":[(108,94),(148,94),(152,162),(104,162)],
              "color":ATTIRE,"outline":OUT,"outline_w":1})
    # HIGH COLLAR (tall, up to the chin, gold-trimmed -- very visible)
    P.append({"type":"polygon","points":[(108,94),(148,94),(144,74),(112,74)],
              "color":ATTIRE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":110,"y":76,"w":36,"h":4,"color":COLLAR,"outline":OUT,"outline_w":1})
    # gold center trim + Demacian crest
    P.append({"type":"line","start":[128,94],"end":[128,162],"color":COLLAR,"width":2})
    P.append({"type":"circle","cx":128,"cy":110,"r":5,"color":COLLAR,"outline":OUT,"outline_w":1})
    # shoulder armor (duelist epaulettes)
    P.append({"type":"circle","cx":106,"cy":98,"r":10,"color":ATTIRE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":150,"cy":98,"r":10,"color":ATTIRE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[100,96],"end":[112,96],"color":COLLAR,"width":1})
    P.append({"type":"line","start":[144,96],"end":[156,96],"color":COLLAR,"width":1})

    # --- Arms (duelist pose: forward arm extended toward rapier) ---
    P.append({"type":"rect","x":98,"y":104,"w":12,"h":48,"color":ATTIRE,"outline":OUT,"outline_w":1,"radius":4})
    # forward arm extended right toward rapier grip
    P.append({"type":"polygon","points":[(148,104),(166,108),(176,128),(168,134),(150,118)],
              "color":ATTIRE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":174,"cy":130,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (duelist stance, apart) ---
    P.append({"type":"rect","x":106,"y":162,"w":16,"h":52,"color":ATTIRE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":134,"y":162,"w":16,"h":52,"color":ATTIRE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":102,"y":210,"w":22,"h":12,"color":(45,35,35),"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":210,"w":22,"h":12,"color":(45,35,35),"outline":OUT,"outline_w":1,"radius":2})

    # --- RAPIER (THE signature weapon -- drawn LAST, IN FRONT, BIG, HORIZONTAL) ---
    # rapier held horizontally forward (thrust pose) -- reads as a rapier, not a tower
    # blade: long horizontal tapered polygon pointing RIGHT from the hand
    P.append({"type":"polygon","points":[(176,128),(176,136),(240,130),(244,134),(240,138),(176,136)],
              "color":RAPIER,"outline":OUT,"outline_w":2})
    # blade center groove
    P.append({"type":"line","start":[176,132],"end":[240,132],"color":(170,170,180),"width":1})
    # blade tip (sharp point, right side)
    P.append({"type":"polygon","points":[(236,128),(236,140),(246,134)],"color":RAPIER,"outline":OUT,"outline_w":1})
    # basket hilt (gold, prominent guard at the grip)
    P.append({"type":"circle","cx":172,"cy":132,"r":9,"color":RAPIER_HILT,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(164,132),(180,132),(180,142),(164,142)],
              "color":RAPIER_HILT,"outline":OUT,"outline_w":1})
    # hilt guard (wide, gold -- the duelist guard, vertical bar)
    P.append({"type":"line","start":[162,124],"end":[162,142],"color":RAPIER_HILT,"width":3})
    # grip
    P.append({"type":"rect","x":156,"y":138,"w":12,"h":18,"color":(90,50,30),"outline":OUT,"outline_w":1})
    # pommel (gold)
    P.append({"type":"circle","cx":162,"cy":160,"r":5,"color":RAPIER_HILT,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Fizz -- amphibious yordle; SEASTONE TRIDENT (big) + yordle ears + fish gills
# ============================================================================
def fizz_prims():
    P = []
    SKIN = (90, 200, 180)        # teal amphibious skin
    SKIN_DARK = (50, 150, 140)
    SKIN_LIGHT = (140, 230, 210)
    EAR = (80, 190, 170)
    FINS = (120, 220, 200)       # fin accents
    TRIDENT = (180, 180, 195)    # seastone trident (silver)
    TRIDENT_DARK = (110, 110, 130)
    TRIDENT_GOLD = (200, 165, 55)
    ATTIRE = (130, 90, 50)       # brown sea-themed attire
    ATTIRE_DARK = (90, 60, 35)
    GOLD = (215, 175, 60)
    EYE = (40, 100, 120)
    OUT = (25, 35, 40)

    # --- SEASTONE TRIDENT (THE feature -- BIG, bigger than the yordle) ---
    # trident shaft (long, diagonal, BIG)
    P.append({"type":"line","start":[150,100],"end":[210,220],"color":TRIDENT_DARK,"width":7})
    # trident head (3 prongs, BIG, at top)
    P.append({"type":"line","start":[150,100],"end":[136,60],"color":TRIDENT,"width":5})
    P.append({"type":"line","start":[150,100],"end":[150,52],"color":TRIDENT,"width":5})
    P.append({"type":"line","start":[150,100],"end":[164,60],"color":TRIDENT,"width":5})
    # prong tips (sharp, silver)
    P.append({"type":"circle","cx":136,"cy":60,"r":3,"color":TRIDENT,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":150,"cy":52,"r":3,"color":TRIDENT,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":164,"cy":60,"r":3,"color":TRIDENT,"outline":OUT,"outline_w":1})
    # gold band on trident
    P.append({"type":"rect","x":166,"y":130,"w":10,"h":8,"color":TRIDENT_GOLD,"outline":OUT,"outline_w":1})
    # trident glow (seastone energy)
    P.append({"type":"circle","cx":150,"cy":72,"r":8,"color":(140,200,220),"outline":FINS,"outline_w":1})

    # --- BIG POINTED EARS (THE yordle feature -- huge, pointed, sticking out) ---
    # left ear (big, pointed, amphibious teal)
    P.append({"type":"polygon","points":[(92,76),(60,56),(72,84),(88,86)],
              "color":EAR,"outline":OUT,"outline_w":2})
    # ear interior (lighter)
    P.append({"type":"polygon","points":[(88,78),(70,64),(76,82)],
              "color":SKIN_LIGHT,"outline":OUT,"outline_w":1})
    # right ear (big, pointed, behind trident but visible)
    P.append({"type":"polygon","points":[(130,76),(156,60),(150,86),(132,86)],
              "color":EAR,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(132,78),(150,66),(146,82)],
              "color":SKIN_LIGHT,"outline":OUT,"outline_w":1})

    # --- Head (yordle -- big head, amphibious) ---
    P.append({"type":"circle","cx":110,"cy":84,"r":18,"color":SKIN,"outline":OUT,"outline_w":1})
    # big eyes (yordle, mischievous)
    P.append({"type":"circle","cx":103,"cy":84,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":117,"cy":84,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":104,"cy":83,"r":1,"color":(255,255,255)})
    P.append({"type":"circle","cx":118,"cy":83,"r":1,"color":(255,255,255)})
    # mischievous mouth
    P.append({"type":"line","start":[104,94],"end":[116,94],"color":(40,80,90),"width":1})
    # FISH-LIKE GILLS (THE missing feature -- on cheeks/neck)
    P.append({"type":"line","start":[96,88],"end":[96,94],"color":SKIN_DARK,"width":2})
    P.append({"type":"line","start":[94,90],"end":[94,96],"color":SKIN_DARK,"width":1})
    P.append({"type":"line","start":[124,88],"end":[124,94],"color":SKIN_DARK,"width":2})
    P.append({"type":"line","start":[126,90],"end":[126,96],"color":SKIN_DARK,"width":1})

    # --- Small body (yordle proportions -- tiny body vs big head) ---
    # torso (sea-themed attire, brown)
    P.append({"type":"polygon","points":[(94,108),(126,108),(130,160),(90,160)],
              "color":ATTIRE,"outline":OUT,"outline_w":1})
    # attire detail (gold belt)
    P.append({"type":"rect","x":90,"y":150,"w":40,"h":6,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":110,"cy":153,"r":3,"color":TRIDENT_DARK,"outline":OUT,"outline_w":1})
    # attire collar
    P.append({"type":"polygon","points":[(96,108),(124,108),(120,116),(100,116)],
              "color":ATTIRE_DARK,"outline":OUT,"outline_w":1})

    # --- Arms (webbed hands -- THE missing feature) ---
    P.append({"type":"rect","x":82,"y":112,"w":12,"h":34,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":126,"y":112,"w":12,"h":34,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    # webbed hands (THE feature -- webbing between fingers)
    P.append({"type":"circle","cx":88,"cy":148,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":132,"cy":148,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})
    # webbed fingers (membrane)
    P.append({"type":"polygon","points":[(84,150),(92,150),(88,158)],"color":FINS,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(128,150),(136,150),(132,158)],"color":FINS,"outline":OUT,"outline_w":1})

    # --- Legs (short, webbed feet -- THE missing feature) ---
    P.append({"type":"rect","x":94,"y":160,"w":14,"h":28,"color":ATTIRE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":114,"y":160,"w":14,"h":28,"color":ATTIRE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # WEBBED FEET (THE feature -- big webbed amphibious feet)
    P.append({"type":"ellipse","x":90,"y":184,"w":22,"h":14,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"ellipse","x":110,"y":184,"w":22,"h":14,"color":SKIN,"outline":OUT,"outline_w":1})
    # webbed toes
    P.append({"type":"line","start":[96,188],"end":[96,196],"color":SKIN_DARK,"width":1})
    P.append({"type":"line","start":[104,188],"end":[104,196],"color":SKIN_DARK,"width":1})
    P.append({"type":"line","start":[116,188],"end":[116,196],"color":SKIN_DARK,"width":1})
    P.append({"type":"line","start":[124,188],"end":[124,196],"color":SKIN_DARK,"width":1})
    return P


# ============================================================================
# Run all 6
# ============================================================================
CHAMPS = [
    ("Brand", brand_prims, "head engulfed in flames + lava veins"),
    ("Ekko", ekko_prims, "Zaurite time device on back + goggles"),
    ("Elise", elise_prims, "spider legs from back + gothic gown"),
    ("Ezreal", ezreal_prims, "floating arcane gauntlet + blonde hair"),
    ("Fiora", fiora_prims, "big rapier + high collar + ponytail"),
    ("Fizz", fizz_prims, "seastone trident + yordle ears + webbed feet"),
]

if __name__ == "__main__":
    results = []
    for cid, fn, feature in CHAMPS:
        print(f"\n=== {cid} ===", flush=True)
        prims = fn()
        r = improve(cid, prims, gate_n=3)
        print(f"RESULT: {r}", flush=True)
        results.append({"id": cid, "old": r["old"], "new": r["new"],
                        "saved": r["saved"], "rounds": 1,
                        "missing_final": r["missing"][:4],
                        "feature": feature})
    print("\n=== SUMMARY ===")
    print(results)
    improved = sum(1 for x in results if x["new"] > x["old"])
    reached = sum(1 for x in results if x["new"] >= 8)
    print(f"{improved}/6 champs improved, {reached}/6 reached >=8")
