"""Batch 19: Vayne, Vex, Viego, Viktor, Xayah, Xerath.

- Vayne  -> WRIST-MOUNTED CROSSBOW (huge, on forearm, silver bolts)
- Vex    -> LONG DROOPING EARS (big floppy yordle ears) + gloomy cloak
- Viego  -> CROWN OF THORNS (spiky crown) + ghostly pale skin + ruined sword
- Viktor -> GLOWING HEXCORE CHEST PIECE (big glowing core in chest)
- Xayah  -> LARGE PURPLE FEATHERED WINGS on hips (big feather-blades)
- Xerath -> FLOATING STONE ARMOR SHARDS (body made of floating shards, no legs)
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve


# ============================================================================
# Vayne -- night hunter with WRIST-MOUNTED CROSSBOW
# ============================================================================
def vayne_prims():
    P = []
    CLOAK = (45, 30, 55)        # dark purple cloak
    CLOAK_DARK = (28, 18, 38)
    LEATHER = (70, 50, 65)      # dark leather armor
    SILVER = (180, 185, 195)    # silver metal
    SILVER_DARK = (120, 125, 135)
    BOLT = (200, 205, 215)
    SKIN = (220, 200, 185)
    HAIR = (130, 110, 100)      # dark brown hair
    PURPLE = (110, 70, 130)     # Demacian purple accent
    EYE = (140, 100, 160)
    OUT = (20, 15, 25)

    # --- Cloak (behind, flaring wide) ---
    P.append({"type":"polygon","points":[(88,90),(168,90),(180,210),(76,210)],
              "color":CLOAK,"outline":OUT,"outline_w":2})
    # cloak inner shadow
    P.append({"type":"polygon","points":[(96,100),(160,100),(168,200),(88,200)],
              "color":CLOAK_DARK,"outline":OUT,"outline_w":1})

    # --- Legs (high leather boots) ---
    P.append({"type":"rect","x":108,"y":170,"w":18,"h":40,"color":LEATHER,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":170,"w":18,"h":40,"color":LEATHER,"outline":OUT,"outline_w":1,"radius":3})
    # boot tops (cuff detail)
    P.append({"type":"rect","x":106,"y":170,"w":22,"h":6,"color":SILVER_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":128,"y":170,"w":22,"h":6,"color":SILVER_DARK,"outline":OUT,"outline_w":1})

    # --- Torso (slender, dark leather armor) ---
    P.append({"type":"polygon","points":[(104,100),(152,100),(156,172),(100,172)],
              "color":LEATHER,"outline":OUT,"outline_w":1})
    # silver chest accents (Demacian)
    P.append({"type":"polygon","points":[(116,108),(140,108),(136,150),(120,150)],
              "color":SILVER_DARK,"outline":OUT,"outline_w":1})
    # purple gem on chest
    P.append({"type":"circle","cx":128,"cy":128,"r":5,"color":PURPLE,"outline":SILVER_DARK,"outline_w":1})

    # --- Left arm (normal) ---
    P.append({"type":"rect","x":88,"y":108,"w":16,"h":44,"color":LEATHER,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":96,"cy":154,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Right arm with WRIST-MOUNTED CROSSBOW (THE feature -- HUGE, dominates) ---
    # forearm
    P.append({"type":"rect","x":152,"y":108,"w":16,"h":36,"color":LEATHER,"outline":OUT,"outline_w":1,"radius":4})
    # CROSSBOW body (mounted on wrist, BIG -- THE feature, 40%+ of sprite)
    P.append({"type":"rect","x":146,"y":136,"w":36,"h":24,"color":SILVER_DARK,"outline":OUT,"outline_w":3})
    # crossbow limbs (wide horizontal bow arms -- BIG, sweeping)
    P.append({"type":"line","start":[146,148],"end":[108,120],"color":SILVER,"width":7})
    P.append({"type":"line","start":[146,148],"end":[108,176],"color":SILVER,"width":7})
    # bowstring
    P.append({"type":"line","start":[108,120],"end":[108,176],"color":(200,200,210),"width":1})
    # loaded bolt (silver, pointing forward -- BIG)
    P.append({"type":"line","start":[146,148],"end":[200,148],"color":BOLT,"width":4})
    # bolt tip (arrowhead -- big)
    P.append({"type":"polygon","points":[(200,148),(214,142),(214,154)],"color":SILVER,"outline":OUT,"outline_w":1})
    # crossbow mechanism detail
    P.append({"type":"circle","cx":160,"cy":148,"r":5,"color":SILVER,"outline":OUT,"outline_w":1})
    # purple glow on crossbow (Demacian magic)
    P.append({"type":"circle","cx":160,"cy":148,"r":3,"color":PURPLE,"outline":OUT,"outline_w":1})
    # second crossbow on left arm (dual wrist crossbows - very Vayne, also BIG)
    P.append({"type":"rect","x":74,"y":136,"w":32,"h":22,"color":SILVER_DARK,"outline":OUT,"outline_w":3})
    P.append({"type":"line","start":[74,147],"end":[40,120],"color":SILVER,"width":7})
    P.append({"type":"line","start":[74,147],"end":[40,174],"color":SILVER,"width":7})
    P.append({"type":"line","start":[40,120],"end":[40,174],"color":(200,200,210),"width":1})
    P.append({"type":"line","start":[74,147],"end":[28,147],"color":BOLT,"width":4})
    P.append({"type":"polygon","points":[(28,147),(16,141),(16,153)],"color":SILVER,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":62,"cy":147,"r":5,"color":SILVER,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":62,"cy":147,"r":3,"color":PURPLE,"outline":OUT,"outline_w":1})

    # --- Head (hooded) ---
    P.append({"type":"circle","cx":128,"cy":78,"r":20,"color":SKIN,"outline":OUT,"outline_w":1})
    # hood (dark purple, covers top of head)
    P.append({"type":"polygon","points":[(106,72),(150,72),(148,60),(128,48),(108,60)],
              "color":CLOAK,"outline":OUT,"outline_w":2})
    # hood back drape
    P.append({"type":"polygon","points":[(106,72),(108,60),(96,90),(100,110)],
              "color":CLOAK_DARK,"outline":OUT,"outline_w":1})
    # hair strands from under hood
    P.append({"type":"line","start":[112,86],"end":[108,100],"color":HAIR,"width":2})
    P.append({"type":"line","start":[144,86],"end":[148,100],"color":HAIR,"width":2})
    # sharp eyes
    P.append({"type":"circle","cx":121,"cy":78,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":78,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Vex -- gloomy yordle with LONG DROOPING EARS
# ============================================================================
def vex_prims():
    P = []
    CLOAK = (55, 40, 70)         # dark purple cloak
    CLOAK_DARK = (35, 25, 50)
    EAR = (60, 45, 75)           # ear color (same as cloak, dark)
    EAR_INNER = (85, 65, 100)
    SKIN = (180, 165, 180)       # pale greyish skin
    FUR = (90, 70, 100)          # dark fur
    SHADOW = (40, 30, 60)        # floating shadow companion
    SHADOW_GLOW = (100, 70, 140)
    STAFF = (90, 70, 55)         # wooden staff
    GEM = (130, 80, 170)         # purple gem on staff
    EYE = (240, 230, 250)
    OUT = (20, 15, 30)

    # --- Floating shadow companion (behind, above) ---
    P.append({"type":"ellipse","x":160,"y":30,"w":50,"h":40,"color":SHADOW,"outline":SHADOW_GLOW,"outline_w":1})
    # shadow eyes (glowing)
    P.append({"type":"circle","cx":178,"cy":46,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":194,"cy":46,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    # shadow wisps
    for sx in (168, 176, 184, 192, 200):
        P.append({"type":"line","start":[sx,66],"end":[sx,76],"color":SHADOW,"width":3})

    # --- LONG DROOPING EARS (THE feature -- HUGE, hanging down from head) ---
    # left ear (big, drooping down past shoulders)
    P.append({"type":"ellipse","x":78,"y":80,"w":20,"h":60,"color":EAR,"outline":OUT,"outline_w":2})
    P.append({"type":"ellipse","x":80,"y":84,"w":12,"h":48,"color":EAR_INNER,"outline":OUT,"outline_w":1})
    # right ear
    P.append({"type":"ellipse","x":158,"y":80,"w":20,"h":60,"color":EAR,"outline":OUT,"outline_w":2})
    P.append({"type":"ellipse","x":160,"y":84,"w":12,"h":48,"color":EAR_INNER,"outline":OUT,"outline_w":1})
    # ear tips (pointed, drooping)
    P.append({"type":"polygon","points":[(88,138),(96,138),(92,150)],"color":EAR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(168,138),(176,138),(172,150)],"color":EAR,"outline":OUT,"outline_w":1})

    # --- Oversized dark cloak (body) ---
    P.append({"type":"polygon","points":[(86,100),(170,100),(180,220),(76,220)],
              "color":CLOAK,"outline":OUT,"outline_w":2})
    # cloak shading
    P.append({"type":"polygon","points":[(96,110),(160,110),(168,210),(88,210)],
              "color":CLOAK_DARK,"outline":OUT,"outline_w":1})

    # --- Head (yordle -- big head, pale skin, gloomy) ---
    P.append({"type":"circle","cx":128,"cy":80,"r":24,"color":SKIN,"outline":OUT,"outline_w":2})
    # fur/hair top (dark)
    P.append({"type":"polygon","points":[(108,68),(148,68),(144,56),(128,48),(112,56)],
              "color":FUR,"outline":OUT,"outline_w":1})
    # bangs
    P.append({"type":"line","start":[112,72],"end":[144,72],"color":FUR,"width":3})

    # --- Gloomy expression (THE feature -- big frown) ---
    # eyes (half-lidded, gloomy)
    P.append({"type":"ellipse","x":116,"y":78,"w":10,"h":6,"color":(40,30,50),"outline":OUT,"outline_w":1})
    P.append({"type":"ellipse","x":134,"y":78,"w":10,"h":6,"color":(40,30,50),"outline":OUT,"outline_w":1})
    # eye highlights (small, unenthusiastic)
    P.append({"type":"circle","cx":120,"cy":79,"r":2,"color":EYE})
    P.append({"type":"circle","cx":138,"cy":79,"r":2,"color":EYE})
    # BIG FROWN (gloomy mouth)
    P.append({"type":"line","start":[118,94],"end":[128,98],"color":OUT,"width":2})
    P.append({"type":"line","start":[128,98],"end":[138,94],"color":OUT,"width":2})

    # --- Staff (shadow staff, left side) ---
    P.append({"type":"line","start":[60,100],"end":[60,210],"color":STAFF,"width":4})
    # staff gem (purple, glowing)
    P.append({"type":"circle","cx":60,"cy":96,"r":8,"color":GEM,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":60,"cy":96,"r":4,"color":(180,120,220)})

    # --- Small yordle feet (peeking from cloak) ---
    P.append({"type":"rect","x":104,"y":218,"w":16,"h":14,"color":FUR,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":136,"y":218,"w":16,"h":14,"color":FUR,"outline":OUT,"outline_w":1,"radius":3})
    return P


# ============================================================================
# Viego -- ruined king with CROWN OF THORNS
# ============================================================================
def viego_prims():
    P = []
    SKIN = (200, 210, 215)       # pale ghostly skin
    SKIN_DARK = (160, 175, 185)
    REGALIA = (35, 50, 55)       # dark teal-black royal regalia
    REGALIA_DARK = (20, 30, 35)
    TEAL = (60, 180, 175)        # glowing teal accents
    TEAL_GLOW = (100, 220, 210)
    GOLD = (180, 150, 70)        # tarnished gold
    GOLD_DARK = (120, 95, 40)
    HAIR = (230, 235, 240)       # long white hair
    BLADE = (90, 100, 110)       # ruined sword
    BLADE_GLOW = (80, 200, 195)  # teal blade glow
    CROWN = (140, 145, 155)      # iron thorns
    CROWN_DARK = (80, 85, 95)
    EYE = (100, 220, 210)        # glowing teal eyes
    OUT = (15, 20, 25)

    # --- Long white hair (behind, flowing down) ---
    P.append({"type":"polygon","points":[(100,70),(156,70),(170,200),(86,200)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # hair strands
    for hx in (100, 112, 124, 136, 148):
        P.append({"type":"line","start":[hx,72],"end":[hx-4,190],"color":(200,210,220),"width":3})

    # --- Tattered royal regalia (body, torn cape) ---
    P.append({"type":"polygon","points":[(92,100),(164,100),(176,210),(80,210)],
              "color":REGALIA,"outline":OUT,"outline_w":2})
    # tattered edges (jagged bottom)
    for bx in (84, 100, 116, 132, 148, 164, 176):
        P.append({"type":"polygon","points":[(bx-6,206),(bx+6,206),(bx,216)],"color":REGALIA_DARK,"outline":OUT,"outline_w":1})
    # teal glowing accents on regalia
    P.append({"type":"line","start":[100,120],"end":[156,120],"color":TEAL,"width":2})
    P.append({"type":"line","start":[100,160],"end":[156,160],"color":TEAL,"width":1})

    # --- Legs ---
    P.append({"type":"rect","x":106,"y":170,"w":18,"h":42,"color":REGALIA_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":18,"h":42,"color":REGALIA_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # gold leg armor
    P.append({"type":"rect","x":106,"y":186,"w":18,"h":16,"color":GOLD_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":132,"y":186,"w":18,"h":16,"color":GOLD_DARK,"outline":OUT,"outline_w":1})

    # --- Torso (royal chest plate) ---
    P.append({"type":"polygon","points":[(104,100),(152,100),(156,172),(100,172)],
              "color":REGALIA_DARK,"outline":OUT,"outline_w":1})
    # tarnished gold chest emblem
    P.append({"type":"polygon","points":[(116,112),(140,112),(136,148),(120,148)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # teal gem on chest (glowing)
    P.append({"type":"circle","cx":128,"cy":128,"r":6,"color":TEAL,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":128,"r":3,"color":TEAL_GLOW})

    # --- Arms ---
    P.append({"type":"rect","x":86,"y":108,"w":16,"h":50,"color":REGALIA,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":154,"y":108,"w":16,"h":50,"color":REGALIA,"outline":OUT,"outline_w":1,"radius":4})
    # gold shoulder pauldrons
    P.append({"type":"circle","cx":94,"cy":110,"r":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":162,"cy":110,"r":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- BIG RUINED SWORD (Blade of the Ruined King -- THE weapon, HUGE) ---
    # sword blade (long, pointing down from right hand, BIG)
    P.append({"type":"polygon","points":[(168,156),(184,156),(190,240),(162,240)],
              "color":BLADE,"outline":OUT,"outline_w":2})
    # teal glow along blade (corrupted, bright)
    P.append({"type":"line","start":[176,156],"end":[176,240],"color":BLADE_GLOW,"width":3})
    P.append({"type":"line","start":[172,160],"end":[172,236],"color":TEAL_GLOW,"width":1})
    P.append({"type":"line","start":[180,160],"end":[180,236],"color":TEAL_GLOW,"width":1})
    # sword crossguard (wide, ornate)
    P.append({"type":"rect","x":160,"y":148,"w":32,"h":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # sword hilt
    P.append({"type":"rect","x":170,"y":138,"w":12,"h":12,"color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # sword pommel (glowing teal gem)
    P.append({"type":"circle","cx":176,"cy":136,"r":6,"color":TEAL,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":176,"cy":136,"r":3,"color":TEAL_GLOW})

    # --- Head (pale ghostly) ---
    P.append({"type":"circle","cx":128,"cy":76,"r":22,"color":SKIN,"outline":OUT,"outline_w":1})
    # ghostly skin shading
    P.append({"type":"circle","cx":128,"cy":80,"r":18,"color":SKIN_DARK,"outline":OUT,"outline_w":1})
    # glowing teal eyes (ghostly)
    P.append({"type":"circle","cx":120,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":136,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":120,"cy":76,"r":2,"color":TEAL_GLOW})
    P.append({"type":"circle","cx":136,"cy":76,"r":2,"color":TEAL_GLOW})

    # --- CROWN OF THORNS (THE feature -- HUGE spiky iron crown, dominates head) ---
    # crown base band (wider)
    P.append({"type":"rect","x":100,"y":52,"w":56,"h":12,"color":CROWN,"outline":OUT,"outline_w":3})
    # THORN SPIKES (BIG, pointing up and outward -- THE icon, 30% of sprite)
    for tx, ty, tx2, ty2 in [(106,52,96,30),(116,52,110,22),(128,52,128,18),
                              (140,52,146,22),(150,52,160,30)]:
        P.append({"type":"polygon","points":[(tx-4,52),(tx+4,52),(tx2,ty2)],
                  "color":CROWN,"outline":OUT,"outline_w":3})
    # extra side thorns (wider, more menacing, sweeping out)
    P.append({"type":"polygon","points":[(100,58),(88,42),(94,62)],"color":CROWN_DARK,"outline":OUT,"outline_w":3})
    P.append({"type":"polygon","points":[(156,58),(168,42),(162,62)],"color":CROWN_DARK,"outline":OUT,"outline_w":3})
    # lower side thorns (downward, like a real thorn crown wrapping)
    P.append({"type":"polygon","points":[(100,64),(90,72),(104,66)],"color":CROWN_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(156,64),(166,72),(152,66)],"color":CROWN_DARK,"outline":OUT,"outline_w":2})
    # teal glow at thorn tips (glowing corruption)
    for tx2, ty2 in [(96,30),(128,18),(160,30)]:
        P.append({"type":"circle","cx":tx2,"cy":ty2,"r":4,"color":TEAL_GLOW,"outline":TEAL,"outline_w":1})
    # teal glow on side thorns
    P.append({"type":"circle","cx":88,"cy":42,"r":3,"color":TEAL_GLOW,"outline":TEAL,"outline_w":1})
    P.append({"type":"circle","cx":168,"cy":42,"r":3,"color":TEAL_GLOW,"outline":TEAL,"outline_w":1})
    return P


# ============================================================================
# Viktor -- machine herald with GLOWING HEXCORE CHEST PIECE
# ============================================================================
def viktor_prims():
    P = []
    STEEL = (130, 135, 145)       # metallic grey body
    STEEL_DARK = (85, 90, 100)
    STEEL_LIGHT = (170, 175, 185)
    GOLD = (200, 165, 70)         # gold accents
    GOLD_DARK = (140, 110, 40)
    PURPLE = (120, 60, 160)       # deep purple
    HEXCORE = (120, 220, 180)     # glowing green-cyan hexcore
    HEXCORE_GLOW = (180, 250, 220)
    EYE = (140, 240, 200)         # glowing arcane eyes
    STAFF = (100, 105, 115)
    OUT = (20, 22, 28)

    # --- Hexcore staff (behind, left) ---
    P.append({"type":"line","start":[56,80],"end":[56,200],"color":STAFF,"width":5})
    # staff top (hexcore device)
    P.append({"type":"circle","cx":56,"cy":74,"r":10,"color":STEEL,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":56,"cy":74,"r":6,"color":HEXCORE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":56,"cy":74,"r":3,"color":HEXCORE_GLOW})

    # --- Mechanical third arm (THE feature #2 -- extra arm from shoulder, BIG) ---
    # third arm extending from right shoulder, mechanical, BIG and obvious
    P.append({"type":"rect","x":166,"y":82,"w":18,"h":50,"color":STEEL_DARK,"outline":OUT,"outline_w":2,"radius":3})
    P.append({"type":"circle","cx":175,"cy":86,"r":10,"color":STEEL,"outline":OUT,"outline_w":2})
    # third arm joint (gold, mechanical)
    P.append({"type":"circle","cx":175,"cy":132,"r":8,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # third hand (mechanical claw, BIG)
    P.append({"type":"rect","x":168,"y":136,"w":14,"h":20,"color":STEEL,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(168,156),(176,156),(164,166)],"color":STEEL_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(168,156),(176,156),(180,166)],"color":STEEL_DARK,"outline":OUT,"outline_w":2})
    # gold joint on third arm
    P.append({"type":"circle","cx":175,"cy":110,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(172,146),(178,146),(180,154)],"color":STEEL_DARK,"outline":OUT,"outline_w":1})

    # --- Legs (metallic, mechanical) ---
    P.append({"type":"rect","x":106,"y":170,"w":18,"h":44,"color":STEEL,"outline":OUT,"outline_w":2,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":18,"h":44,"color":STEEL,"outline":OUT,"outline_w":2,"radius":3})
    # mechanical joints (knees)
    P.append({"type":"circle","cx":115,"cy":188,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":141,"cy":188,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # mechanical feet
    P.append({"type":"rect","x":102,"y":210,"w":24,"h":10,"color":STEEL_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":210,"w":24,"h":10,"color":STEEL_DARK,"outline":OUT,"outline_w":1,"radius":2})

    # --- Torso (metallic body with chest plate) ---
    P.append({"type":"polygon","points":[(100,100),(156,100),(160,172),(96,172)],
              "color":STEEL,"outline":OUT,"outline_w":2})
    # gold chest plates
    P.append({"type":"polygon","points":[(108,108),(148,108),(144,140),(112,140)],
              "color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # purple under-armor
    P.append({"type":"polygon","points":[(114,140),(142,140),(146,168),(110,168)],
              "color":PURPLE,"outline":OUT,"outline_w":1})

    # --- GLOWING HEXCORE CHEST PIECE (THE feature -- HUGE, dominates torso) ---
    # hexcore housing (BIG metallic ring, 40% of torso)
    P.append({"type":"circle","cx":128,"cy":130,"r":30,"color":STEEL_DARK,"outline":OUT,"outline_w":4})
    # hexcore inner ring (gold, thick)
    P.append({"type":"circle","cx":128,"cy":130,"r":24,"color":GOLD,"outline":GOLD_DARK,"outline_w":3})
    # hexcore GLOWING CORE (BIG bright -- THE icon)
    P.append({"type":"circle","cx":128,"cy":130,"r":18,"color":HEXCORE,"outline":OUT,"outline_w":2})
    # hex pattern (hexcore signature -- bright)
    P.append({"type":"circle","cx":128,"cy":130,"r":12,"color":HEXCORE_GLOW})
    # hexcore rays (glowing lines emanating outward -- BIG)
    import math
    for ang in (0, 60, 120, 180, 240, 300):
        x2 = 128 + int(28 * math.cos(math.radians(ang)))
        y2 = 130 + int(28 * math.sin(math.radians(ang)))
        P.append({"type":"line","start":[128,130],"end":[x2,y2],"color":HEXCORE_GLOW,"width":2})
    # hexcore center bright spot (blinding)
    P.append({"type":"circle","cx":128,"cy":130,"r":7,"color":(240,255,250)})
    # hexcore outer glow (aura around the core)
    P.append({"type":"circle","cx":128,"cy":130,"r":34,"color":(120,220,180,40) if False else (80,180,150),"outline":HEXCORE,"outline_w":1})

    # --- Arms (mechanical, both sides) ---
    P.append({"type":"rect","x":84,"y":108,"w":16,"h":50,"color":STEEL,"outline":OUT,"outline_w":2,"radius":4})
    P.append({"type":"rect","x":156,"y":108,"w":16,"h":50,"color":STEEL,"outline":OUT,"outline_w":2,"radius":4})
    # gold shoulder pads (mechanical)
    P.append({"type":"circle","cx":92,"cy":110,"r":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":164,"cy":110,"r":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # mechanical hands
    P.append({"type":"circle","cx":92,"cy":160,"r":6,"color":STEEL_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":164,"cy":160,"r":6,"color":STEEL_DARK,"outline":OUT,"outline_w":1})

    # --- Head (augmented facial plating) ---
    P.append({"type":"circle","cx":128,"cy":76,"r":22,"color":STEEL,"outline":OUT,"outline_w":2})
    # augmented face plate (metallic lower half)
    P.append({"type":"polygon","points":[(108,80),(148,80),(144,96),(112,96)],
              "color":STEEL_DARK,"outline":OUT,"outline_w":1})
    # face plate seams
    P.append({"type":"line","start":[128,80],"end":[128,96],"color":GOLD_DARK,"width":1})
    # glowing arcane eyes
    P.append({"type":"circle","cx":120,"cy":74,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":136,"cy":74,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":120,"cy":74,"r":2,"color":HEXCORE_GLOW})
    P.append({"type":"circle","cx":136,"cy":74,"r":2,"color":HEXCORE_GLOW})
    # head crest (gold)
    P.append({"type":"polygon","points":[(118,58),(138,58),(128,48)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    return P


# ============================================================================
# Xayah -- rebel with LARGE PURPLE FEATHERED WINGS on hips
# ============================================================================
def xayah_prims():
    P = []
    FEATHER = (140, 70, 170)      # purple feathers
    FEATHER_DARK = (95, 45, 125)
    FEATHER_LIGHT = (180, 100, 200)
    MAGENTA = (200, 80, 160)      # magenta accents
    HAIR = (170, 60, 130)         # red/magenta hair
    HAIR_DARK = (120, 40, 90)
    SKIN = (220, 195, 200)        # pale skin
    CLOTH = (55, 40, 60)          # dark grey clothing
    CLOTH_DARK = (35, 25, 40)
    TALON = (180, 150, 130)       # bird-like talon feet
    BEAK = (150, 120, 100)
    EYE = (180, 80, 160)
    OUT = (25, 20, 30)

    # --- LARGE PURPLE FEATHERED WINGS ON HIPS (THE feature -- HUGE, dominates) ---
    # LEFT WING (big feather-blade, sweeping out from hip, 40% of sprite)
    P.append({"type":"polygon","points":[(96,150),(24,100),(16,150),(28,196),(92,172)],
              "color":FEATHER,"outline":OUT,"outline_w":3})
    # left wing feather blades (individual big feathers)
    for fy in (116, 135, 155, 175):
        P.append({"type":"polygon","points":[(92,150),(32,fy-10),(22,fy),(36,fy+8),(88,168)],
                  "color":FEATHER_DARK,"outline":OUT,"outline_w":1})
    # left wing top feather (big, sweeping up)
    P.append({"type":"polygon","points":[(92,150),(36,92),(22,102),(32,120),(84,146)],
              "color":FEATHER_LIGHT,"outline":OUT,"outline_w":2})

    # RIGHT WING (mirrored, big)
    P.append({"type":"polygon","points":[(160,150),(232,100),(240,150),(228,196),(164,172)],
              "color":FEATHER,"outline":OUT,"outline_w":3})
    for fy in (116, 135, 155, 175):
        P.append({"type":"polygon","points":[(164,150),(224,fy-10),(234,fy),(220,fy+8),(168,168)],
                  "color":FEATHER_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(164,150),(220,92),(234,102),(224,120),(172,146)],
              "color":FEATHER_LIGHT,"outline":OUT,"outline_w":2})

    # feather highlights (magenta tips -- bright, on wing tips)
    P.append({"type":"circle","cx":24,"cy":100,"r":7,"color":MAGENTA,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":232,"cy":100,"r":7,"color":MAGENTA,"outline":OUT,"outline_w":1})
    # additional magenta feather tips
    P.append({"type":"circle","cx":16,"cy":150,"r":5,"color":MAGENTA,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":240,"cy":150,"r":5,"color":MAGENTA,"outline":OUT,"outline_w":1})

    # --- Legs (bird-like talons for feet) ---
    P.append({"type":"rect","x":108,"y":170,"w":16,"h":36,"color":CLOTH,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":16,"h":36,"color":CLOTH,"outline":OUT,"outline_w":1,"radius":3})
    # TALON FEET (bird-like claws -- THE missing feature)
    P.append({"type":"polygon","points":[(108,206),(124,206),(116,218)],"color":TALON,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(132,206),(148,206),(140,218)],"color":TALON,"outline":OUT,"outline_w":1})
    # talon claws
    for tx in (110, 116, 122):
        P.append({"type":"line","start":[tx,206],"end":[tx-2,214],"color":BEAK,"width":1})
    for tx in (134, 140, 146):
        P.append({"type":"line","start":[tx,206],"end":[tx+2,214],"color":BEAK,"width":1})

    # --- Torso (plumage-inspired clothing) ---
    P.append({"type":"polygon","points":[(104,100),(152,100),(156,172),(100,172)],
              "color":CLOTH,"outline":OUT,"outline_w":1})
    # plumage feather texture on chest
    for fy in (112, 128, 144):
        P.append({"type":"polygon","points":[(112,fy),(144,fy),(140,fy+8),(116,fy+8)],
                  "color":FEATHER_DARK,"outline":OUT,"outline_w":1})
    # magenta chest accent
    P.append({"type":"circle","cx":128,"cy":120,"r":5,"color":MAGENTA,"outline":OUT,"outline_w":1})

    # --- Arms ---
    P.append({"type":"rect","x":88,"y":108,"w":14,"h":44,"color":CLOTH,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":154,"y":108,"w":14,"h":44,"color":CLOTH,"outline":OUT,"outline_w":1,"radius":4})
    # feather blades on arms (daggers)
    P.append({"type":"polygon","points":[(88,150),(76,160),(80,152)],"color":FEATHER,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(168,150),(180,160),(176,152)],"color":FEATHER,"outline":OUT,"outline_w":1})

    # --- Head (vastayan, red/magenta hair, avian features) ---
    P.append({"type":"circle","cx":128,"cy":78,"r":20,"color":SKIN,"outline":OUT,"outline_w":1})
    # red/magenta hair (big, flowing)
    P.append({"type":"polygon","points":[(108,68),(148,68),(156,54),(128,40),(100,54)],
              "color":HAIR,"outline":OUT,"outline_w":2})
    # hair flowing down sides
    P.append({"type":"polygon","points":[(108,68),(100,54),(92,100),(100,100)],
              "color":HAIR_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(148,68),(156,54),(164,100),(156,100)],
              "color":HAIR_DARK,"outline":OUT,"outline_w":1})
    # avian facial features (sharp eyes)
    P.append({"type":"circle","cx":121,"cy":78,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":78,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    # avian nose (slight beak shape)
    P.append({"type":"polygon","points":[(126,84),(130,84),(128,90)],"color":BEAK,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Xerath -- magus ascended, FLOATING, body of STONE ARMOR SHARDS
# ============================================================================
def xerath_prims():
    P = []
    SHARD = (100, 160, 220)       # electric blue stone shards
    SHARD_DARK = (60, 110, 170)
    SHARD_LIGHT = (150, 200, 240)
    ENERGY = (140, 220, 255)      # glowing energy core
    ENERGY_GLOW = (200, 240, 255)
    GOLD = (200, 165, 70)         # ancient Shuriman gold plating
    GOLD_DARK = (140, 110, 40)
    GREY = (80, 85, 95)           # dark grey stone
    EYE = (180, 230, 255)
    OUT = (25, 35, 55)

    # --- FLOATING ENERGY AURA (behind everything, glowing) ---
    P.append({"type":"ellipse","x":76,"y":60,"w":104,"h":180,"color":(60,120,180),"outline":ENERGY,"outline_w":1})
    # energy swirls
    for sy in (80, 120, 160, 200):
        P.append({"type":"ellipse","x":88,"y":sy-10,"w":80,"h":20,"color":SHARD_DARK,"outline":ENERGY,"outline_w":1})

    # --- NO LEGS (floating -- lower body is just energy/shards) ---
    # lower body = floating shards + energy (not legs)
    for sx, sy, sw, sh in [(108,180,16,24),(132,180,16,24),(118,200,14,20),(136,200,14,20)]:
        P.append({"type":"rect","x":sx,"y":sy,"w":sw,"h":sh,"color":SHARD,"outline":OUT,"outline_w":2,"radius":2})
    # floating shard fragments around lower body
    P.append({"type":"polygon","points":[(96,190),(86,185),(90,200)],"color":SHARD_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(160,190),(170,185),(166,200)],"color":SHARD_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(100,210),(90,215),(98,222)],"color":SHARD,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(156,210),(166,215),(158,222)],"color":SHARD,"outline":OUT,"outline_w":1})

    # --- GLOWING ENERGY CORE (chest, bright -- THE feature #2) ---
    P.append({"type":"circle","cx":128,"cy":130,"r":20,"color":ENERGY,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":130,"r":14,"color":ENERGY_GLOW})
    P.append({"type":"circle","cx":128,"cy":130,"r":8,"color":(240,255,255)})
    # energy rays from core
    for sy in (112, 148):
        P.append({"type":"line","start":[128,sy],"end":[128,sy-6 if sy>130 else sy+6],"color":ENERGY_GLOW,"width":2})

    # --- FLOATING STONE ARMOR SHARDS (THE feature -- body made of shards) ---
    # torso = floating shard plates (not a solid body)
    # left shoulder shard (big, floating)
    P.append({"type":"polygon","points":[(88,96),(112,100),(108,124),(84,118)],
              "color":SHARD,"outline":OUT,"outline_w":2})
    # right shoulder shard
    P.append({"type":"polygon","points":[(144,100),(168,96),(172,118),(148,124)],
              "color":SHARD,"outline":OUT,"outline_w":2})
    # chest shard plates (floating, with gaps showing energy)
    P.append({"type":"polygon","points":[(96,104),(120,104),(116,128),(100,126)],
              "color":SHARD_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(136,104),(160,104),(156,126),(140,128)],
              "color":SHARD_DARK,"outline":OUT,"outline_w":2})
    # lower torso shards
    P.append({"type":"polygon","points":[(100,150),(156,150),(152,172),(104,172)],
              "color":SHARD,"outline":OUT,"outline_w":2})

    # --- Shuriman gold plating (ancient gold accents on shards) ---
    P.append({"type":"polygon","points":[(92,98),(108,100),(106,112),(90,110)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(148,100),(164,98),(166,110),(150,112)],
              "color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold band on lower torso
    P.append({"type":"rect","x":100,"y":156,"w":56,"h":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Arms (floating shards, not connected) ---
    # left arm shards (floating, segmented)
    P.append({"type":"polygon","points":[(76,108),(92,110),(90,130),(74,128)],
              "color":SHARD,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(72,134),(88,136),(86,154),(70,152)],
              "color":SHARD_DARK,"outline":OUT,"outline_w":2})
    # right arm shards
    P.append({"type":"polygon","points":[(164,110),(180,108),(182,128),(166,130)],
              "color":SHARD,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(168,136),(184,134),(186,152),(170,154)],
              "color":SHARD_DARK,"outline":OUT,"outline_w":2})
    # gold arm bands
    P.append({"type":"rect","x":74,"y":114,"w":18,"h":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":164,"y":114,"w":18,"h":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Head (floating shard helmet, no physical face) ---
    # head shard (main)
    P.append({"type":"polygon","points":[(108,60),(148,60),(152,88),(104,88)],
              "color":SHARD,"outline":OUT,"outline_w":2})
    # head side shards (floating, pointed)
    P.append({"type":"polygon","points":[(104,64),(96,54),(100,80),(108,78)],
              "color":SHARD_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(152,64),(160,54),(156,80),(148,78)],
              "color":SHARD_DARK,"outline":OUT,"outline_w":2})
    # top crown shard (pointed up)
    P.append({"type":"polygon","points":[(118,60),(138,60),(128,40)],
              "color":SHARD,"outline":OUT,"outline_w":2})
    # gold head band (Shuriman)
    P.append({"type":"rect","x":108,"y":66,"w":44,"h":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # glowing eyes (energy, no face)
    P.append({"type":"circle","cx":118,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":138,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":118,"cy":76,"r":2,"color":ENERGY_GLOW})
    P.append({"type":"circle","cx":138,"cy":76,"r":2,"color":ENERGY_GLOW})
    # energy between eyes (glowing line)
    P.append({"type":"line","start":[118,76],"end":[138,76],"color":ENERGY_GLOW,"width":1})
    return P


# ============================================================================
# RUN
# ============================================================================
if __name__ == "__main__":
    results = []
    for name, fn in [("Vayne", vayne_prims), ("Vex", vex_prims),
                     ("Viego", viego_prims), ("Viktor", viktor_prims),
                     ("Xayah", xayah_prims), ("Xerath", xerath_prims)]:
        prims = fn()
        r = improve(name, prims, gate_n=3)
        print(f"RESULT: {r}")
        results.append(r)
    print("\n=== BATCH 19 SUMMARY ===")
    for r in results:
        print(f"  {r['id']}: {r['old']} -> {r['new']} saved={r['saved']} missing={r['missing'][:3]}")
