"""Batch 2 hand-authored sprites: Rell, Riven, Shyvana, Soraka, Swain, Tristana.

Each champion gets ONE huge signature feature that dominates the silhouette:
- Rell  -> big METAL HORSE (mounted, she sits on top)
- Riven -> BROKEN greatsword (jagged broken tip, green runes) + white cape
- Shyvana -> long DRAGON TAIL + dragon horns + dragon wings
- Soraka -> HOOVES (goat-like, no human feet) + long purple hair + horns
- Swain  -> GIANT RED DEMONIC ARM/WING (bigger than his body)
- Tristana -> OVERSIZED CANNON (bigger than the yordle) + big pointed ears
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve


# ============================================================================
# Rell -- ferromancy metal mage, MOUNTED on a big metal armored horse
# ============================================================================
def rell_prims():
    P = []
    STEEL = (150, 160, 175)
    STEEL_DARK = (95, 105, 120)
    STEEL_LIGHT = (200, 210, 220)
    DEEP_BLUE = (50, 70, 110)
    BLUE_LIGHT = (90, 120, 170)
    METAL_SHARD = (180, 190, 205)
    SKIN = (235, 200, 175)
    HAIR = (240, 235, 220)       # flowing white-silver hair
    HAIR_DARK = (180, 175, 165)
    GOLD = (215, 175, 60)
    OUT = (35, 30, 35)
    EYE = (40, 30, 35)

    # --- METAL HORSE (THE feature -- big, armored, she sits on top) ---
    # horse body (big rounded mass, low center -- SILVER/STEEL, the metal horse)
    P.append({"type":"ellipse","x":40,"y":150,"w":150,"h":78,"color":STEEL_LIGHT,"outline":OUT,"outline_w":2})
    # horse chest (front, left -- SILVER)
    P.append({"type":"circle","cx":52,"cy":182,"r":26,"color":STEEL_LIGHT,"outline":OUT,"outline_w":2})
    # horse rump (back, right -- SILVER)
    P.append({"type":"circle","cx":186,"cy":178,"r":28,"color":STEEL_LIGHT,"outline":OUT,"outline_w":2})
    # horse neck (armored, rising from chest)
    P.append({"type":"polygon","points":[(36,170),(72,170),(64,120),(40,128)],
              "color":STEEL,"outline":OUT,"outline_w":2})
    # neck armor plates (ferromancy metal plating -- stacked)
    P.append({"type":"polygon","points":[(38,128),(66,120),(60,134),(40,140)],
              "color":STEEL_LIGHT,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(40,140),(62,134),(58,148),(42,152)],
              "color":STEEL_DARK,"outline":OUT,"outline_w":1})
    # horse head (elongated, metal)
    P.append({"type":"ellipse","x":24,"y":108,"w":36,"h":26,"color":STEEL,"outline":OUT,"outline_w":2})
    # horse muzzle
    P.append({"type":"ellipse","x":18,"y":118,"w":20,"h":18,"color":STEEL_DARK,"outline":OUT,"outline_w":1})
    # horse nostril
    P.append({"type":"circle","cx":24,"cy":126,"r":2,"color":OUT})
    # horse eye
    P.append({"type":"circle","cx":38,"cy":118,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    # horse ear (metal, pointed)
    P.append({"type":"polygon","points":[(46,104),(52,86),(58,106)],"color":STEEL_DARK,"outline":OUT,"outline_w":1})
    # metal horse mane (ferromancy shards -- spiky, metallic)
    for mx, my in [(70,118),(78,108),(86,114),(94,108),(102,116),(110,110)]:
        P.append({"type":"polygon","points":[(mx-4,my+8),(mx,my-6),(mx+4,my+8)],
                  "color":METAL_SHARD,"outline":OUT,"outline_w":1})
    # horse legs (4, metallic, stubby-armored)
    for lx in (60, 90, 150, 178):
        P.append({"type":"rect","x":lx,"y":206,"w":18,"h":22,"color":STEEL_DARK,"outline":OUT,"outline_w":1,"radius":3})
        P.append({"type":"rect","x":lx-2,"y":222,"w":22,"h":10,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    # horse hooves (metal, dark)
    for hx in (60, 90, 150, 178):
        P.append({"type":"rect","x":hx-3,"y":224,"w":24,"h":8,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})

    # --- Armor plating on horse body (ferromancy -- BIG distinct SHINY SILVER plates) ---
    # 3 big overlapping SILVER steel plates (ferromancy metal plating -- THE missing feature)
    P.append({"type":"polygon","points":[(70,148),(110,144),(108,168),(72,170)],
              "color":STEEL_LIGHT,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(108,144),(148,144),(148,168),(108,168)],
              "color":STEEL_LIGHT,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(148,144),(182,148),(180,170),(148,168)],
              "color":STEEL_LIGHT,"outline":OUT,"outline_w":2})
    # plate highlights (shiny metal sheen -- makes it read as polished metal)
    P.append({"type":"line","start":[74,152],"end":[108,148],"color":(230,235,245),"width":2})
    P.append({"type":"line","start":[110,148],"end":[146,148],"color":(230,235,245),"width":2})
    P.append({"type":"line","start":[150,148],"end":[180,152],"color":(230,235,245),"width":2})
    # BIG gold studs on each plate (metallic shards -- obvious)
    for sx in (84, 96):
        P.append({"type":"circle","cx":sx,"cy":156,"r":5,"color":GOLD,"outline":OUT,"outline_w":1})
    for sx in (118, 130, 138):
        P.append({"type":"circle","cx":sx,"cy":156,"r":5,"color":GOLD,"outline":OUT,"outline_w":1})
    for sx in (160, 172):
        P.append({"type":"circle","cx":sx,"cy":158,"r":5,"color":GOLD,"outline":OUT,"outline_w":1})
    # gold trim band (top of plates)
    P.append({"type":"rect","x":70,"y":142,"w":114,"h":5,"color":GOLD,"outline":OUT,"outline_w":1})
    # deep blue under-armor visible between plates
    P.append({"type":"rect","x":70,"y":168,"w":114,"h":6,"color":DEEP_BLUE,"outline":OUT,"outline_w":1})

    # --- Floating ferromancy metal shards (around horse -- BIG, obvious magic) ---
    for sx, sy, sz in [(28,138,7),(18,160,6),(212,148,7),(222,168,6),(96,128,7)]:
        P.append({"type":"polygon","points":[(sx-sz,sy),(sx,sy-sz*2),(sx+sz,sy),(sx,sy+sz)],
                  "color":METAL_SHARD,"outline":OUT,"outline_w":2})

    # --- Rider: Rell (on top of horse, small relative to mount) ---
    # rider torso (deep blue coat with BIG steel chest plate)
    P.append({"type":"polygon","points":[(112,96),(146,96),(150,140),(108,140)],
              "color":DEEP_BLUE,"outline":OUT,"outline_w":1})
    # BIG steel chest plate (heavy plate armor -- THE missing feature, obvious)
    P.append({"type":"polygon","points":[(114,98),(144,98),(142,134),(116,134)],
              "color":STEEL_LIGHT,"outline":OUT,"outline_w":2})
    # gold crest on chest plate
    P.append({"type":"circle","cx":128,"cy":112,"r":6,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":112,"r":3,"color":DEEP_BLUE,"outline":OUT,"outline_w":1})
    # gold belt
    P.append({"type":"rect","x":108,"y":134,"w":42,"h":6,"color":GOLD,"outline":OUT,"outline_w":1})
    # flowing hair (long, white-silver, BIG + flowing back -- THE missing feature)
    P.append({"type":"polygon","points":[(108,70),(148,70),(176,96),(168,118),(100,118),(88,96)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # rider head
    P.append({"type":"circle","cx":128,"cy":80,"r":14,"color":SKIN,"outline":OUT,"outline_w":1})
    # hair top (BIG)
    P.append({"type":"circle","cx":128,"cy":72,"r":15,"color":HAIR,"outline":OUT,"outline_w":1})
    # hair flowing back (BIG long ponytail, prominent)
    P.append({"type":"polygon","points":[(142,74),(186,82),(192,120),(170,112)],
              "color":HAIR,"outline":HAIR_DARK,"outline_w":1})
    # second hair streak
    P.append({"type":"polygon","points":[(138,78),(176,86),(180,116),(160,108)],
              "color":HAIR_DARK,"outline":OUT,"outline_w":1})
    # eyes
    P.append({"type":"circle","cx":123,"cy":82,"r":2,"color":EYE})
    P.append({"type":"circle","cx":133,"cy":82,"r":2,"color":EYE})
    # rider arms (holding reins)
    P.append({"type":"rect","x":100,"y":104,"w":12,"h":34,"color":DEEP_BLUE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":146,"y":104,"w":12,"h":34,"color":DEEP_BLUE,"outline":OUT,"outline_w":1,"radius":4})
    # reins to horse
    P.append({"type":"line","start":[100,138],"end":[60,124],"color":OUT,"width":2})
    P.append({"type":"line","start":[158,138],"end":[60,128],"color":OUT,"width":2})
    # rider legs (down the horse sides)
    P.append({"type":"rect","x":104,"y":140,"w":12,"h":30,"color":DEEP_BLUE,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":142,"y":140,"w":12,"h":30,"color":DEEP_BLUE,"outline":OUT,"outline_w":1,"radius":3})
    # steel boots
    P.append({"type":"rect","x":100,"y":166,"w":18,"h":10,"color":STEEL_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":142,"y":166,"w":18,"h":10,"color":STEEL_DARK,"outline":OUT,"outline_w":1,"radius":2})
    return P


# ============================================================================
# Riven -- exile warrior, BROKEN runic greatsword (jagged broken tip) + cape
# ============================================================================
def riven_prims():
    P = []
    SKIN = (235, 205, 180)
    HAIR = (245, 240, 230)       # white hair
    HAIR_DARK = (200, 195, 185)
    CAPE = (235, 235, 240)       # white cape
    CAPE_DARK = (180, 180, 190)
    ARMOR_DARK = (60, 50, 50)    # asymmetrical Noxian armor (dark)
    ARMOR = (95, 85, 85)
    STEEL = (170, 175, 185)
    RUNE_GREEN = (90, 230, 110)  # green glowing energy
    RUNE_DARK = (40, 120, 60)
    BROWN = (110, 80, 55)
    EYE = (50, 80, 50)           # green-ish determined eyes
    OUT = (35, 30, 30)

    # --- White cape (behind, flowing) ---
    P.append({"type":"polygon","points":[(96,96),(160,96),(176,170),(150,196),(106,196),(80,170)],
              "color":CAPE,"outline":OUT,"outline_w":1})
    # cape inner shading
    P.append({"type":"polygon","points":[(108,100),(148,100),(158,168),(98,168)],
              "color":CAPE_DARK,"outline":OUT,"outline_w":1})

    # --- Hair (white, BIG ponytail -- THE missing feature, make it prominent) ---
    P.append({"type":"circle","cx":128,"cy":66,"r":18,"color":HAIR,"outline":OUT,"outline_w":1})
    # BIG ponytail flowing back (long, prominent -- THE signature hair feature)
    P.append({"type":"polygon","points":[(138,58),(176,48),(196,76),(188,108),(160,96),(144,78)],
              "color":HAIR,"outline":HAIR_DARK,"outline_w":2})
    # ponytail highlight streak
    P.append({"type":"polygon","points":[(148,62),(176,54),(184,80),(168,90)],
              "color":(255,255,255),"outline":HAIR_DARK,"outline_w":1})
    # ponytail tail tip (tapered)
    P.append({"type":"polygon","points":[(184,82),(198,76),(196,104),(182,100)],
              "color":HAIR,"outline":HAIR_DARK,"outline_w":1})
    # bangs
    P.append({"type":"polygon","points":[(112,58),(144,58),(140,72),(116,72)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":72,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # determined eyes (green-ish)
    P.append({"type":"line","start":[118,72],"end":[124,72],"color":EYE,"width":2})
    P.append({"type":"line","start":[132,72],"end":[138,72],"color":EYE,"width":2})
    # scar over eye (battle-worn)
    P.append({"type":"line","start":[120,66],"end":[126,78],"color":OUT,"width":1})
    # determined mouth
    P.append({"type":"line","start":[122,84],"end":[134,84],"color":(140,60,60),"width":1})

    # --- Asymmetrical Noxian armor (left shoulder BIG, right light) ---
    # torso
    P.append({"type":"polygon","points":[(108,92),(148,92),(150,160),(106,160)],
              "color":ARMOR,"outline":OUT,"outline_w":1})
    # BIG left shoulder pad (asymmetrical -- Noxian heavy on one side)
    P.append({"type":"circle","cx":100,"cy":100,"r":14,"color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(86,94),(114,94),(112,118),(88,118)],
              "color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    # gold/red Noxian trim on big shoulder
    P.append({"type":"rect","x":88,"y":108,"w":24,"h":4,"color":(180,40,40),"outline":OUT,"outline_w":1})
    # small right shoulder
    P.append({"type":"circle","cx":152,"cy":100,"r":8,"color":ARMOR,"outline":OUT,"outline_w":1})
    # chest plate detail (Noxian plating -- BIG, obvious)
    P.append({"type":"polygon","points":[(110,96),(146,96),(144,150),(112,150)],
              "color":ARMOR_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"line","start":[128,96],"end":[128,150],"color":STEEL,"width":3})
    # Noxian armor plates (horizontal bands -- detailed plating)
    for py in (108, 122, 136):
        P.append({"type":"line","start":[112,py],"end":[144,py],"color":STEEL,"width":2})
    # red Noxian trim on chest
    P.append({"type":"line","start":[110,96],"end":[146,96],"color":(180,40,40),"width":2})

    # --- Arms ---
    P.append({"type":"rect","x":86,"y":118,"w":14,"h":40,"color":ARMOR_DARK,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":150,"y":118,"w":14,"h":40,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":4})
    # hands
    P.append({"type":"circle","cx":93,"cy":160,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":157,"cy":160,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (battle-worn, apart stance -- torn cloth visible) ---
    P.append({"type":"rect","x":106,"y":160,"w":18,"h":46,"color":BROWN,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":160,"w":18,"h":46,"color":BROWN,"outline":OUT,"outline_w":1,"radius":3})
    # battle-worn: torn cloth strips hanging (jagged hem)
    P.append({"type":"polygon","points":[(106,196),(124,196),(120,208),(116,200),(112,210),(108,202)],
              "color":BROWN,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(132,196),(150,196),(146,208),(142,200),(138,210),(134,202)],
              "color":BROWN,"outline":OUT,"outline_w":1})
    # shin armor (battle-worn, dented)
    P.append({"type":"rect","x":106,"y":180,"w":18,"h":20,"color":ARMOR_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":180,"w":18,"h":20,"color":ARMOR_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # dents/scratches on armor (battle-worn detail)
    P.append({"type":"line","start":[110,184],"end":[114,194],"color":OUT,"width":1})
    P.append({"type":"line","start":[136,184],"end":[140,194],"color":OUT,"width":1})
    # boots
    P.append({"type":"rect","x":102,"y":204,"w":24,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":204,"w":24,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})

    # --- BROKEN RUNIC GREATSWORD (THE feature -- drawn LAST, IN FRONT, ENORMOUS) ---
    # THE SWORD IS BROKEN: the blade is clearly snapped at ~60% height. Above the
    # break: only a jagged stump. Below: full blade with green runes. A HUGE green
    # energy explosion marks the break point (the signature). The sword is WIDE
    # and takes up a huge portion of the canvas.
    # blade lower (from hilt up to the break -- WIDE, full blade)
    P.append({"type":"polygon","points":[(160,200),(210,200),(206,110),(164,110)],
              "color":STEEL,"outline":OUT,"outline_w":3})
    # blade center groove
    P.append({"type":"line","start":[185,200],"end":[185,110],"color":(150,150,160),"width":3})
    # THE JAGGED BREAK at y=110 -- the blade is clearly snapped off
    P.append({"type":"polygon","points":[(164,110),(206,110),(202,96),(196,106),(192,90),(188,104),(184,92),(180,106),(176,96)],
              "color":STEEL,"outline":OUT,"outline_w":3})
    # short broken stump above the break (clearly the remnant -- NOT a full tip)
    P.append({"type":"polygon","points":[(172,96),(198,96),(194,82),(176,82)],
              "color":STEEL,"outline":OUT,"outline_w":3})
    # jagged broken edge highlight (the snap is obvious -- thick dark line)
    P.append({"type":"line","start":[164,108],"end":[206,108],"color":OUT,"width":4})
    # BIG green glowing runes along the blade (THE runic energy -- PROMINENT)
    for ry in (128, 142, 156, 170, 184):
        P.append({"type":"line","start":[166,ry],"end":[204,ry],"color":RUNE_GREEN,"width":4})
    # green glow halo around the whole blade (semi-transparent green aura)
    P.append({"type":"rect","x":156,"y":106,"w":58,"h":96,"color":(120,220,140),"outline":RUNE_GREEN,"outline_w":1})
    # hilt guard (gold, wide -- Noxian, BIG)
    P.append({"type":"polygon","points":[(148,200),(222,200),(220,212),(150,212)],
              "color":(180,140,40),"outline":OUT,"outline_w":2})
    # grip (wrapped, brown)
    P.append({"type":"rect","x":178,"y":212,"w":16,"h":22,"color":BROWN,"outline":OUT,"outline_w":1})
    # pommel (gold)
    P.append({"type":"circle","cx":186,"cy":240,"r":7,"color":(180,140,40),"outline":OUT,"outline_w":1})
    # ENORMOUS green energy explosion at the break (THE signature -- MASSIVE)
    P.append({"type":"circle","cx":185,"cy":100,"r":22,"color":RUNE_GREEN,"outline":RUNE_DARK,"outline_w":3})
    P.append({"type":"circle","cx":185,"cy":100,"r":14,"color":(180,255,200)})
    P.append({"type":"circle","cx":185,"cy":100,"r":7,"color":(255,255,255)})
    # green energy wisps trailing up from the break (BIG)
    for wy in (76, 66, 56, 46):
        P.append({"type":"circle","cx":185,"cy":wy,"r":6,"color":RUNE_GREEN,"outline":RUNE_DARK,"outline_w":1})
    # green sparks radiating from the break (BIG)
    for ang in (20, 70, 110, 160, 200, 250, 290, 340):
        import math as _m
        sx = 185 + int(28 * _m.cos(_m.radians(ang)))
        sy = 100 + int(28 * _m.sin(_m.radians(ang)))
        P.append({"type":"circle","cx":sx,"cy":sy,"r":4,"color":RUNE_GREEN,"outline":RUNE_DARK,"outline_w":1})
    return P


# ============================================================================
# Shyvana -- half-dragon, long DRAGON TAIL + horns + wings + scaled skin
# ============================================================================
def shyvana_prims():
    P = []
    SCALE = (170, 60, 55)        # red scaled skin
    SCALE_DARK = (115, 35, 35)
    SCALE_LIGHT = (210, 90, 80)
    GOLD = (220, 180, 60)
    BRONZE = (180, 130, 50)
    WING = (140, 45, 45)         # dragon wing membrane
    WING_DARK = (90, 25, 25)
    WING_BONE = (60, 40, 40)
    HORN = (235, 220, 195)       # draconic horns (bone-colored)
    HORN_DARK = (180, 160, 130)
    SKIN = (200, 175, 150)       # face skin
    HAIR = (220, 90, 70)         # red-purple hair
    EYE = (240, 180, 40)         # golden dragon eyes
    CLAW = (235, 225, 200)
    OUT = (35, 25, 25)

    # --- DRAGON WINGS (behind, big -- THE feature pair) ---
    # left wing (big, spread back)
    P.append({"type":"polygon","points":[(96,100),(40,60),(28,110),(50,140),(88,128)],
              "color":WING,"outline":OUT,"outline_w":2})
    # wing bone struts
    P.append({"type":"line","start":[90,108],"end":[40,64],"color":WING_BONE,"width":2})
    P.append({"type":"line","start":[92,116],"end":[34,92],"color":WING_BONE,"width":2})
    P.append({"type":"line","start":[94,124],"end":[48,138],"color":WING_BONE,"width":2})
    # right wing (smaller, behind body)
    P.append({"type":"polygon","points":[(160,100),(210,70),(218,116),(196,140),(168,128)],
              "color":WING_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[166,108],"end":[208,74],"color":WING_BONE,"width":2})
    P.append({"type":"line","start":[168,118],"end":[214,100],"color":WING_BONE,"width":2})

    # --- LONG DRAGON TAIL (THE feature -- big, curling behind/down) ---
    tail = [(150,165),(170,180),(180,205),(165,222),(140,220),(128,206)]
    for i in range(len(tail)-1):
        P.append({"type":"line","start":tail[i],"end":tail[i+1],"color":SCALE,"width":16})
    for cx, cy in tail:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":9,"color":SCALE,"outline":SCALE_DARK,"outline_w":1})
    # tail ridge scales (spiky along the top)
    for cx, cy in tail[::2]:
        P.append({"type":"polygon","points":[(cx-5,cy-2),(cx,cy-10),(cx+5,cy-2)],
                  "color":SCALE_DARK,"outline":OUT,"outline_w":1})
    # tail tip (arrowhead/spade)
    P.append({"type":"polygon","points":[(122,206),(128,196),(134,206),(128,216)],
              "color":GOLD,"outline":OUT,"outline_w":1})

    # --- Hair (red-purple, back) ---
    P.append({"type":"circle","cx":128,"cy":64,"r":18,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(110,58),(146,58),(142,74),(114,74)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":72,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # scaled skin patches on cheeks + forehead (BIG red scales -- obvious scaled skin)
    P.append({"type":"polygon","points":[(110,76),(126,76),(122,90),(112,86)],
              "color":SCALE,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(130,76),(146,76),(144,86),(134,90)],
              "color":SCALE,"outline":OUT,"outline_w":1})
    # forehead scale patches
    for sx, sy in [(118,64),(128,62),(138,64)]:
        P.append({"type":"polygon","points":[(sx-4,sy),(sx,sy-4),(sx+4,sy),(sx,sy+4)],
                  "color":SCALE_DARK,"outline":OUT,"outline_w":1})
    # golden dragon eyes (slit)
    P.append({"type":"circle","cx":121,"cy":72,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":72,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[121,68],"end":[121,76],"color":OUT,"width":1})
    P.append({"type":"line","start":[135,68],"end":[135,76],"color":OUT,"width":1})
    # determined mouth
    P.append({"type":"line","start":[122,84],"end":[134,84],"color":(120,40,40),"width":1})

    # --- DRACONIC HORNS (THE feature -- big, curved back from head) ---
    # left horn (big, curving back)
    P.append({"type":"polygon","points":[(108,58),(118,46),(128,52),(120,62)],
              "color":HORN,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(118,46),(108,38),(104,52),(118,52)],
              "color":HORN_DARK,"outline":OUT,"outline_w":1})
    # right horn
    P.append({"type":"polygon","points":[(128,52),(138,46),(148,58),(136,62)],
              "color":HORN,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(138,46),(148,38),(152,52),(138,52)],
              "color":HORN_DARK,"outline":OUT,"outline_w":1})

    # --- Torso (scaled, red, athletic) ---
    P.append({"type":"polygon","points":[(108,92),(148,92),(152,160),(104,160)],
              "color":SCALE,"outline":OUT,"outline_w":1})
    # belly (lighter bronze)
    P.append({"type":"polygon","points":[(116,100),(140,100),(144,155),(112,155)],
              "color":BRONZE,"outline":OUT,"outline_w":1})
    # scale texture (BIG diamond scales -- obvious scaled skin, on torso)
    for sy in (106, 118, 130, 142, 154):
        for sx in (116, 128, 140):
            P.append({"type":"polygon","points":[(sx-5,sy),(sx,sy-5),(sx+5,sy),(sx,sy+5)],
                      "color":SCALE_DARK,"outline":OUT,"outline_w":1})
    # gold chest plate
    P.append({"type":"polygon","points":[(118,96),(138,96),(136,124),(120,124)],
              "color":GOLD,"outline":OUT,"outline_w":1})

    # --- Scaled skin on ARMS (THE missing feature -- scales on arms too) ---
    # scale patches on left arm
    for sy in (112, 124, 136):
        P.append({"type":"polygon","points":[(94,sy),(100,sy-4),(94,sy-8),(88,sy-4)],
                  "color":SCALE_DARK,"outline":OUT,"outline_w":1})
    # scale patches on right arm
    for sy in (112, 124, 136):
        P.append({"type":"polygon","points":[(162,sy),(168,sy-4),(162,sy-8),(156,sy-4)],
                  "color":SCALE_DARK,"outline":OUT,"outline_w":1})

    # --- Arms (clawed hands) ---
    P.append({"type":"rect","x":92,"y":100,"w":16,"h":50,"color":SCALE,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"rect","x":148,"y":100,"w":16,"h":50,"color":SCALE,"outline":OUT,"outline_w":1,"radius":5})
    # clawed hands
    P.append({"type":"circle","cx":100,"cy":154,"r":7,"color":SCALE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":156,"cy":154,"r":7,"color":SCALE,"outline":OUT,"outline_w":1})
    for hx in (96, 100, 104):
        P.append({"type":"line","start":[hx,160],"end":[hx,170],"color":CLAW,"width":2})
    for hx in (152, 156, 160):
        P.append({"type":"line","start":[hx,160],"end":[hx,170],"color":CLAW,"width":2})

    # --- Legs (scaled, clawed feet) ---
    P.append({"type":"rect","x":108,"y":160,"w":18,"h":46,"color":SCALE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":132,"y":160,"w":18,"h":46,"color":SCALE,"outline":OUT,"outline_w":1,"radius":4})
    # gold shin armor
    P.append({"type":"rect","x":108,"y":180,"w":18,"h":18,"color":GOLD,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":180,"w":18,"h":18,"color":GOLD,"outline":OUT,"outline_w":1,"radius":3})
    # clawed feet
    for fx in (108, 116, 124):
        P.append({"type":"polygon","points":[(fx,206),(fx+4,206),(fx+2,214)],"color":CLAW,"outline":OUT,"outline_w":1})
    for fx in (132, 140, 148):
        P.append({"type":"polygon","points":[(fx,206),(fx+4,206),(fx+2,214)],"color":CLAW,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Soraka -- celestial healer, HOOVES (goat-like, no human feet) + purple hair
# ============================================================================
def soraka_prims():
    P = []
    SKIN = (235, 215, 195)
    HAIR = (160, 90, 180)        # long flowing purple hair
    HAIR_DARK = (110, 55, 130)
    HAIR_LIGHT = (200, 130, 220)
    ROBE = (245, 245, 250)       # ethereal white robes
    ROBE_DARK = (200, 200, 215)
    GOLD = (225, 185, 70)
    HORN = (235, 220, 195)       # horn-like protrusions
    HORN_DARK = (180, 160, 130)
    HOOF = (60, 45, 40)          # dark hooves
    LEG_FUR = (220, 200, 180)    # goat-like leg fur
    GLOW = (200, 220, 255)       # celestial glow
    EYE = (140, 100, 200)        # violet celestial eyes
    OUT = (40, 30, 40)

    # --- Celestial glow halo (behind everything) ---
    P.append({"type":"circle","cx":128,"cy":80,"r":40,"color":(220,230,255),"outline":GLOW,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":80,"r":30,"color":(230,235,250),"outline":GLOW,"outline_w":1})

    # --- Long flowing purple hair (THE feature -- big, behind + flowing down) ---
    P.append({"type":"polygon","points":[(100,60),(156,60),(168,180),(140,200),(116,200),(88,180)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # hair top
    P.append({"type":"circle","cx":128,"cy":66,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    # hair highlight streaks
    P.append({"type":"polygon","points":[(108,70),(120,70),(116,180),(104,170)],
              "color":HAIR_LIGHT,"outline":HAIR_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(136,70),(148,70),(152,170),(140,180)],
              "color":HAIR_LIGHT,"outline":HAIR_DARK,"outline_w":1})
    # bangs
    P.append({"type":"polygon","points":[(110,60),(146,60),(142,76),(114,76)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # violet celestial eyes (gentle)
    P.append({"type":"circle","cx":121,"cy":74,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":74,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":73,"r":1,"color":(255,255,255)})
    P.append({"type":"circle","cx":136,"cy":73,"r":1,"color":(255,255,255)})
    # gentle smile (healer)
    P.append({"type":"line","start":[122,84],"end":[134,84],"color":(150,80,150),"width":1})
    # celestial marking on forehead (gold)
    P.append({"type":"polygon","points":[(124,62),(132,62),(128,56)],"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Horn-like protrusions (THE feature -- from head, curved) ---
    # left horn
    P.append({"type":"polygon","points":[(108,62),(100,48),(96,58),(106,68)],
              "color":HORN,"outline":OUT,"outline_w":2})
    # right horn
    P.append({"type":"polygon","points":[(148,62),(156,48),(160,58),(150,68)],
              "color":HORN,"outline":OUT,"outline_w":2})

    # --- Ethereal robes (white, flowing -- BIG, obvious) ---
    P.append({"type":"polygon","points":[(100,92),(156,92),(170,170),(86,170)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # robe shading (ethereal layers)
    P.append({"type":"polygon","points":[(110,96),(146,96),(152,168),(104,168)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # gold trim on robe (BIG)
    P.append({"type":"line","start":[100,92],"end":[156,92],"color":GOLD,"width":3})
    P.append({"type":"line","start":[86,170],"end":[170,170],"color":GOLD,"width":3})
    # ethereal flowing folds (white streaks -- the robe is clearly flowing)
    P.append({"type":"line","start":[110,100],"end":[100,168],"color":(255,255,255),"width":2})
    P.append({"type":"line","start":[146,100],"end":[156,168],"color":(255,255,255),"width":2})
    P.append({"type":"line","start":[128,100],"end":[128,168],"color":(255,255,255),"width":1})
    # gold celestial symbol on chest (BIG -- celestial markings)
    P.append({"type":"circle","cx":128,"cy":116,"r":8,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(122,116),(134,116),(128,106)],"color":(255,255,255),"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(122,116),(134,116),(128,126)],"color":(255,255,255),"outline":OUT,"outline_w":1})
    # celestial markings (gold streaks down robe -- more obvious)
    P.append({"type":"line","start":[128,128],"end":[128,168],"color":GOLD,"width":2})
    P.append({"type":"line","start":[116,140],"end":[140,140],"color":GOLD,"width":1})
    P.append({"type":"line","start":[118,154],"end":[138,154],"color":GOLD,"width":1})

    # --- Arms (slender, raised -- healing gesture) ---
    P.append({"type":"rect","x":96,"y":100,"w":12,"h":44,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":148,"y":100,"w":12,"h":44,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":102,"cy":144,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":154,"cy":144,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    # celestial glow at hands (healing magic)
    P.append({"type":"circle","cx":102,"cy":144,"r":8,"color":GLOW,"outline":(150,180,220),"outline_w":1})
    P.append({"type":"circle","cx":154,"cy":144,"r":8,"color":GLOW,"outline":(150,180,220),"outline_w":1})

    # --- HOOVES (THE feature -- HUGE goat-like cloven hooves, NO human feet) ---
    # upper legs (robe-covered, slender)
    P.append({"type":"rect","x":112,"y":166,"w":14,"h":22,"color":ROBE,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":166,"w":14,"h":22,"color":ROBE,"outline":OUT,"outline_w":1,"radius":3})
    # goat-like lower legs (fur-covered, slender -- reverse-joint look, BIG)
    P.append({"type":"rect","x":110,"y":186,"w":18,"h":24,"color":LEG_FUR,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":128,"y":186,"w":18,"h":24,"color":LEG_FUR,"outline":OUT,"outline_w":1,"radius":3})
    # fur tufts at top of hooves (fluffy goat leggings -- BIG)
    P.append({"type":"polygon","points":[(104,206),(134,206),(130,216),(108,216)],"color":LEG_FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(122,206),(152,206),(148,216),(126,216)],"color":LEG_FUR,"outline":OUT,"outline_w":1})
    # HUGE HOOVES (dark, cloven -- THE feature, distinctly hoof-shaped, NOT shoes)
    # left hoof (big, dark, cloven -- dominates the lower body)
    P.append({"type":"polygon","points":[(102,214),(134,214),(132,236),(104,236)],
              "color":HOOF,"outline":OUT,"outline_w":3})
    # right hoof
    P.append({"type":"polygon","points":[(122,214),(154,214),(152,236),(124,236)],
              "color":HOOF,"outline":OUT,"outline_w":3})
    # BIG cloven split in each hoof (THE goat detail -- obvious, thick)
    P.append({"type":"line","start":[118,214],"end":[118,236],"color":OUT,"width":3})
    P.append({"type":"line","start":[138,214],"end":[138,236],"color":OUT,"width":3})
    # hoof highlight (top edge -- makes it read as a hard hoof, not a shoe)
    P.append({"type":"line","start":[104,216],"end":[132,216],"color":(100,80,70),"width":2})
    P.append({"type":"line","start":[124,216],"end":[152,216],"color":(100,80,70),"width":2})
    # hoof toe line (front of hoof -- goat detail)
    P.append({"type":"line","start":[110,220],"end":[110,236],"color":(40,30,25),"width":1})
    P.append({"type":"line","start":[128,220],"end":[128,236],"color":(40,30,25),"width":1})

    # --- Floating celestial stars/sparkles (the magic) ---
    for sx, sy in [(80,120),(176,120),(70,160),(186,160),(60,90)]:
        P.append({"type":"polygon","points":[(sx-3,sy),(sx+3,sy),(sx,sy-4),(sx,sy+4)],
                  "color":GOLD,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Swain -- Noxian grand general, GIANT RED DEMONIC ARM/WING on one side
# ============================================================================
def swain_prims():
    P = []
    COAT = (50, 45, 50)          # black Noxian coat
    COAT_DARK = (30, 25, 30)
    COAT_RED = (130, 35, 35)     # red coat trim/lining
    GREY = (110, 110, 120)       # grey uniform details
    GOLD = (200, 165, 60)        # Noxian gold trim
    SKIN = (220, 195, 175)
    HAIR = (200, 200, 205)       # grey-white hair (older)
    HAIR_DARK = (150, 150, 160)
    DEMON_RED = (180, 35, 40)    # THE demonic arm/wing -- deep red
    DEMON_DARK = (110, 20, 25)
    DEMON_LIGHT = (220, 70, 70)
    RAVEN = (35, 30, 35)         # raven motifs (black)
    EYE = (200, 50, 50)          # red demonic eye
    OUT = (25, 20, 25)
    CANE = (110, 80, 50)
    CANE_TOP = (200, 165, 60)

    # --- GIANT RED DEMONIC ARM/WING (THE feature -- huge, on left side, bigger than body) ---
    # main wing/arm mass (big, looming behind+left, bigger than torso)
    P.append({"type":"polygon","points":[(96,90),(20,50),(8,130),(30,180),(80,170),(96,140)],
              "color":DEMON_RED,"outline":OUT,"outline_w":2})
    # wing membrane struts (demonic bone fingers)
    P.append({"type":"line","start":[90,96],"end":[24,56],"color":DEMON_DARK,"width":3})
    P.append({"type":"line","start":[92,110],"end":[14,90],"color":DEMON_DARK,"width":3})
    P.append({"type":"line","start":[94,128],"end":[12,130],"color":DEMON_DARK,"width":3})
    P.append({"type":"line","start":[92,144],"end":[28,176],"color":DEMON_DARK,"width":3})
    # membrane highlights (red veins)
    P.append({"type":"line","start":[88,100],"end":[28,62],"color":DEMON_LIGHT,"width":1})
    P.append({"type":"line","start":[90,120],"end":[18,110],"color":DEMON_LIGHT,"width":1})
    # DEMONIC CLAW at the wing tip (top -- a giant clawed hand)
    P.append({"type":"polygon","points":[(20,50),(10,40),(18,30),(26,44)],
              "color":DEMON_DARK,"outline":OUT,"outline_w":2})
    # claw talons (3 sharp claws at top)
    for cx, cy in [(12,38),(18,30),(24,40)]:
        P.append({"type":"polygon","points":[(cx-2,cy),(cx+2,cy),(cx,cy-10)],
                  "color":DEMON_DARK,"outline":OUT,"outline_w":1})
    # DEMONIC EYE in the wing (raven demon eye -- glowing red)
    P.append({"type":"circle","cx":50,"cy":110,"r":7,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":50,"cy":110,"r":3,"color":(255,200,200)})
    # demonic glow around the eye
    P.append({"type":"circle","cx":50,"cy":110,"r":11,"color":(220,80,80),"outline":DEMON_DARK,"outline_w":1})

    # --- Coat back (black, high-collared) ---
    P.append({"type":"polygon","points":[(104,96),(152,96),(160,180),(96,180)],
              "color":COAT,"outline":OUT,"outline_w":1})

    # --- Hair (grey-white, swept back, older general) ---
    P.append({"type":"circle","cx":128,"cy":68,"r":18,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(110,60),(146,60),(142,74),(114,74)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # hair sides (grey)
    P.append({"type":"polygon","points":[(110,60),(104,80),(114,80)],"color":HAIR_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(146,60),(152,80),(142,80)],"color":HAIR_DARK,"outline":OUT,"outline_w":1})

    # --- Head (stern, older Noxian general) ---
    P.append({"type":"circle","cx":128,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # stern eyes (red-tinged -- demonic influence)
    P.append({"type":"line","start":[118,74],"end":[124,74],"color":EYE,"width":2})
    P.append({"type":"line","start":[132,74],"end":[138,74],"color":EYE,"width":2})
    # stern brow (frowning)
    P.append({"type":"polygon","points":[(114,68),(126,71),(126,69),(114,66)],"color":HAIR_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(130,69),(142,66),(142,68),(130,71)],"color":HAIR_DARK,"outline":OUT,"outline_w":1})
    # stern mouth (frown)
    P.append({"type":"line","start":[122,86],"end":[134,86],"color":(120,40,40),"width":1})
    # beard (grey, trimmed)
    P.append({"type":"polygon","points":[(116,84),(140,84),(136,96),(120,96)],
              "color":HAIR_DARK,"outline":OUT,"outline_w":1})

    # --- HIGH-COLLARED Noxian coat (THE uniform feature) ---
    # torso coat (black)
    P.append({"type":"polygon","points":[(108,92),(148,92),(150,170),(106,170)],
              "color":COAT,"outline":OUT,"outline_w":1})
    # red coat lining (visible at edges)
    P.append({"type":"polygon","points":[(106,170),(150,170),(148,176),(108,176)],
              "color":COAT_RED,"outline":OUT,"outline_w":1})
    # HIGH COLLAR (up to chin, gold-trimmed -- very prominent)
    P.append({"type":"polygon","points":[(108,92),(148,92),(144,72),(112,72)],
              "color":COAT_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":110,"y":74,"w":36,"h":4,"color":GOLD,"outline":OUT,"outline_w":1})
    # gold center trim + Noxian crest
    P.append({"type":"line","start":[128,92],"end":[128,170],"color":GOLD,"width":2})
    P.append({"type":"circle","cx":128,"cy":110,"r":5,"color":GOLD,"outline":OUT,"outline_w":1})
    # raven motif on chest (black bird silhouette)
    P.append({"type":"polygon","points":[(122,128),(134,128),(130,136),(126,136)],
              "color":RAVEN,"outline":OUT,"outline_w":1})
    # shoulder epaulettes (Noxian military, gold)
    P.append({"type":"circle","cx":106,"cy":96,"r":9,"color":COAT_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":150,"cy":96,"r":9,"color":COAT_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[100,94],"end":[112,94],"color":GOLD,"width":1})
    P.append({"type":"line","start":[144,94],"end":[156,94],"color":GOLD,"width":1})

    # --- Right arm (normal, human, holding cane) ---
    P.append({"type":"rect","x":148,"y":100,"w":14,"h":50,"color":COAT,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":155,"cy":152,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Cane (Noxian general's cane, in right hand) ---
    P.append({"type":"line","start":[155,152],"end":[170,210],"color":CANE,"width":4})
    P.append({"type":"circle","cx":170,"cy":210,"r":4,"color":CANE,"outline":OUT,"outline_w":1})
    # cane handle (raven-head gold)
    P.append({"type":"circle","cx":155,"cy":148,"r":6,"color":CANE_TOP,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(150,144),(160,144),(155,138)],"color":CANE_TOP,"outline":OUT,"outline_w":1})

    # --- Legs (black coat tails + boots) ---
    P.append({"type":"rect","x":108,"y":170,"w":18,"h":40,"color":COAT,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":18,"h":40,"color":COAT,"outline":OUT,"outline_w":1,"radius":3})
    # boots (black, knee-high)
    P.append({"type":"rect","x":106,"y":200,"w":22,"h":16,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":200,"w":22,"h":16,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    # gold boot trim
    P.append({"type":"rect","x":106,"y":200,"w":22,"h":3,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":130,"y":200,"w":22,"h":3,"color":GOLD,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Tristana -- yordle gunner, OVERSIZED CANNON + big pointed ears (yordle)
# ============================================================================
def tristana_prims():
    P = []
    SKIN = (235, 215, 195)       # yordle skin (peachy)
    FUR = (180, 145, 110)        # fur (yordle)
    HAIR = (60, 90, 160)         # blue hair (canonical)
    HAIR_DARK = (35, 60, 120)
    UNIFORM = (90, 110, 160)     # blue military uniform
    UNIFORM_DARK = (55, 70, 110)
    GOLD = (215, 175, 60)
    BROWN = (110, 80, 55)
    CANNON = (90, 90, 100)       # cannon metal (grey)
    CANNON_DARK = (50, 50, 60)
    CANNON_LIGHT = (140, 140, 150)
    CANNON_BRASS = (180, 140, 50) # brass cannon bands
    EYE = (60, 100, 180)         # blue eyes
    OUT = (30, 25, 30)

    # --- OVERSIZED CANNON (THE feature -- big gun, bigger than the yordle, drawn behind/aside) ---
    # cannon barrel (BIG, diagonal, bigger than her body)
    P.append({"type":"polygon","points":[(150,100),(230,60),(244,72),(164,116)],
              "color":CANNON,"outline":OUT,"outline_w":2})
    # cannon muzzle (wide opening at front)
    P.append({"type":"ellipse","x":226,"y":58,"w":22,"h":22,"color":CANNON_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":237,"cy":69,"r":8,"color":OUT,"outline":CANNON_DARK,"outline_w":1})
    # brass bands on cannon
    P.append({"type":"polygon","points":[(168,108),(176,104),(180,112),(172,116)],
              "color":CANNON_BRASS,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(196,94),(204,90),(208,98),(200,102)],
              "color":CANNON_BRASS,"outline":OUT,"outline_w":1})
    # cannon highlight (metal sheen)
    P.append({"type":"line","start":[156,104],"end":[228,66],"color":CANNON_LIGHT,"width":2})
    # cannon back/breech (where she holds it)
    P.append({"type":"polygon","points":[(150,100),(140,108),(146,120),(156,116)],
              "color":CANNON_DARK,"outline":OUT,"outline_w":1})
    # cannon trigger/grip
    P.append({"type":"rect","x":138,"y":116,"w":10,"h":14,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})

    # --- Fur tail (behind, small -- yordle) ---
    P.append({"type":"circle","cx":96,"cy":150,"r":8,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":90,"cy":156,"r":5,"color":FUR,"outline":OUT,"outline_w":1})

    # --- Hair (blue, big relative to small yordle body) ---
    P.append({"type":"circle","cx":110,"cy":78,"r":22,"color":HAIR,"outline":OUT,"outline_w":1})
    # hair top swirl (yordle style)
    P.append({"type":"polygon","points":[(96,66),(124,66),(118,54),(102,58)],
              "color":HAIR_DARK,"outline":OUT,"outline_w":1})

    # --- BIG POINTED EARS (THE yordle feature -- huge, pointed, sticking out) ---
    # left ear (big, pointed, sticking out left)
    P.append({"type":"polygon","points":[(90,76),(64,56),(72,84),(88,86)],
              "color":SKIN,"outline":OUT,"outline_w":2})
    # ear interior
    P.append({"type":"polygon","points":[(86,78),(72,64),(76,82)],
              "color":(220,180,170),"outline":OUT,"outline_w":1})
    # right ear (big, pointed, sticking out right -- behind cannon but visible)
    P.append({"type":"polygon","points":[(130,76),(150,60),(146,86),(132,86)],
              "color":SKIN,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(132,78),(146,66),(142,82)],
              "color":(220,180,170),"outline":OUT,"outline_w":1})

    # --- Head (yordle -- big head relative to small body) ---
    P.append({"type":"circle","cx":110,"cy":84,"r":18,"color":SKIN,"outline":OUT,"outline_w":1})
    # big blue eyes (yordle -- determined)
    P.append({"type":"circle","cx":103,"cy":84,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":117,"cy":84,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":104,"cy":83,"r":1,"color":(255,255,255)})
    P.append({"type":"circle","cx":118,"cy":83,"r":1,"color":(255,255,255)})
    # determined mouth
    P.append({"type":"line","start":[104,94],"end":[116,94],"color":(140,60,60),"width":1})
    # yordle nose (small)
    P.append({"type":"circle","cx":110,"cy":90,"r":2,"color":(200,160,150),"outline":OUT,"outline_w":1})

    # --- Small body (yordle = tiny body vs big head + ears) ---
    # torso (blue military uniform)
    P.append({"type":"polygon","points":[(94,108),(126,108),(130,160),(90,160)],
              "color":UNIFORM,"outline":OUT,"outline_w":1})
    # uniform chest detail (gold buttons + belt)
    P.append({"type":"line","start":[110,108],"end":[110,160],"color":GOLD,"width":1})
    for by in (118, 132, 146):
        P.append({"type":"circle","cx":110,"cy":by,"r":2,"color":GOLD,"outline":OUT,"outline_w":1})
    # gold belt
    P.append({"type":"rect","x":90,"y":150,"w":40,"h":6,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":110,"cy":153,"r":3,"color":CANNON_DARK,"outline":OUT,"outline_w":1})
    # uniform collar
    P.append({"type":"polygon","points":[(96,108),(124,108),(120,116),(100,116)],
              "color":UNIFORM_DARK,"outline":OUT,"outline_w":1})

    # --- Arms (small, holding cannon grip) ---
    P.append({"type":"rect","x":82,"y":112,"w":12,"h":34,"color":UNIFORM,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":126,"y":112,"w":12,"h":34,"color":UNIFORM,"outline":OUT,"outline_w":1,"radius":4})
    # hands (one on cannon grip)
    P.append({"type":"circle","cx":88,"cy":148,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":143,"cy":122,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (small, short -- yordle proportions) ---
    P.append({"type":"rect","x":94,"y":160,"w":14,"h":28,"color":UNIFORM_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":114,"y":160,"w":14,"h":28,"color":UNIFORM_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # fur around ankles (yordle fur)
    P.append({"type":"rect","x":92,"y":184,"w":18,"h":6,"color":FUR,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":112,"y":184,"w":18,"h":6,"color":FUR,"outline":OUT,"outline_w":1,"radius":2})
    # boots
    P.append({"type":"rect","x":92,"y":188,"w":18,"h":10,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":112,"y":188,"w":18,"h":10,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})
    return P


# ============================================================================
# Run all 6
# ============================================================================
CHAMPS = [
    ("Rell", rell_prims, "big metal armored horse (mounted)"),
    ("Riven", riven_prims, "broken runic greatsword + white cape"),
    ("Shyvana", shyvana_prims, "long dragon tail + horns + wings"),
    ("Soraka", soraka_prims, "hooves + long purple hair + horns"),
    ("Swain", swain_prims, "giant red demonic arm/wing"),
    ("Tristana", tristana_prims, "oversized cannon + big ears"),
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
