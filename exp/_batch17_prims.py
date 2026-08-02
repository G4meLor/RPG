"""Batch 17: Rumble, Ryze, Sejuani, Singed, Skarner, Sylas.

- Rumble  -> JUNK-PILE MECH SUIT (bulky scrap-metal, small yordle in cockpit)
- Ryze    -> GLOWING BLUE RUNES on skin + massive forearms + floating arcane energy
- Sejuani -> GIANT ARMORED BOAR (mounted, the boar is the icon)
- Singed  -> CHEMICAL TANK on back + GAS MASK + glowing green vials
- Skarner -> MASSIVE CRYSTALLINE STINGER (scorpion, big tail with crystal)
- Sylas   -> BROKEN SHACKLES + glowing magical chains (big chains on wrists)
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve


# ============================================================================
# Rumble -- yordle in a junk-pile mech suit
# ============================================================================
def rumble_prims():
    P = []
    MECH = (170, 110, 60)       # rusty orange metal
    MECH_DARK = (110, 70, 35)
    MECH_LIGHT = (200, 140, 80)
    METAL = (140, 140, 150)     # metallic grey
    METAL_DARK = (90, 90, 100)
    BROWN = (110, 80, 55)
    YORDLE_SKIN = (235, 215, 195)
    YORDLE_FUR = (180, 145, 110)
    EXHAUST = (80, 80, 90)      # exhaust pipes (dark)
    EXHAUST_SMOKE = (120, 120, 130)
    FIRE = (255, 140, 40)       # flamethrower
    RIVET = (200, 200, 210)     # rivets
    EYE = (40, 30, 30)
    OUT = (25, 20, 15)

    # --- JUNK-PILE MECH SUIT (THE feature -- BIG, bulky, dominates the sprite) ---
    # mech body (big, bulky, rounded scrap-metal mass)
    P.append({"type":"ellipse","x":40,"y":100,"w":176,"h":130,"color":MECH,"outline":OUT,"outline_w":3})
    # mech chest plate (metallic grey, riveted)
    P.append({"type":"polygon","points":[(72,120),(184,120),(190,200),(66,200)],
              "color":METAL,"outline":OUT,"outline_w":2})
    # RIVETED METAL PLATING (THE missing feature -- big obvious rivets)
    for rx in (84, 100, 116, 132, 148, 164, 176):
        P.append({"type":"circle","cx":rx,"cy":132,"r":4,"color":RIVET,"outline":OUT,"outline_w":1})
    for rx in (84, 100, 116, 132, 148, 164, 176):
        P.append({"type":"circle","cx":rx,"cy":180,"r":4,"color":RIVET,"outline":OUT,"outline_w":1})
    # rusty orange accents (THE missing feature)
    P.append({"type":"rect","x":72,"y":150,"w":118,"h":10,"color":MECH,"outline":OUT,"outline_w":1})
    # metal plate seams
    P.append({"type":"line","start":[128,120],"end":[128,200],"color":METAL_DARK,"width":2})
    P.append({"type":"line","start":[72,160],"end":[184,160],"color":METAL_DARK,"width":1})

    # --- EXHAUST PIPES (THE missing feature -- BIG, on back/sides, with smoke) ---
    # left exhaust pipe (big, pointing up)
    P.append({"type":"rect","x":44,"y":60,"w":18,"h":50,"color":EXHAUST,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":53,"cy":60,"r":10,"color":EXHAUST,"outline":OUT,"outline_w":2})
    # exhaust smoke (grey wisps)
    for sy in (48, 38, 28):
        P.append({"type":"circle","cx":53,"cy":sy,"r":6,"color":EXHAUST_SMOKE,"outline":EXHAUST,"outline_w":1})
    # right exhaust pipe
    P.append({"type":"rect","x":198,"y":60,"w":18,"h":50,"color":EXHAUST,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":207,"cy":60,"r":10,"color":EXHAUST,"outline":OUT,"outline_w":2})
    for sy in (48, 38, 28):
        P.append({"type":"circle","cx":207,"cy":sy,"r":6,"color":EXHAUST_SMOKE,"outline":EXHAUST,"outline_w":1})

    # --- MECH ARMS (one with flamethrower) ---
    # left mech arm (big, metal)
    P.append({"type":"rect","x":30,"y":130,"w":24,"h":60,"color":MECH_DARK,"outline":OUT,"outline_w":2,"radius":5})
    # right mech arm with FLAMETHROWER (THE weapon)
    P.append({"type":"rect","x":202,"y":130,"w":24,"h":60,"color":MECH_DARK,"outline":OUT,"outline_w":2,"radius":5})
    # flamethrower nozzle
    P.append({"type":"rect","x":218,"y":140,"w":16,"h":14,"color":METAL_DARK,"outline":OUT,"outline_w":1})
    # flamethrower fire (THE weapon effect)
    P.append({"type":"polygon","points":[(234,142),(248,138),(254,150),(248,154),(234,150)],
              "color":FIRE,"outline":(200,80,20),"outline_w":1})
    P.append({"type":"circle","cx":246,"cy":146,"r":6,"color":(255,200,80),"outline":FIRE,"outline_w":1})

    # --- MECH LEGS (stubby, metal) ---
    for lx in (72, 108, 144, 180):
        P.append({"type":"rect","x":lx,"y":210,"w":24,"h":24,"color":MECH_DARK,"outline":OUT,"outline_w":2,"radius":4})
        P.append({"type":"rect","x":lx-2,"y":230,"w":28,"h":10,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})

    # --- COCKPIT (small yordle pilot visible in the mech) ---
    # cockpit opening (dark, where the yordle sits)
    P.append({"type":"ellipse","x":104,"y":84,"w":48,"h":36,"color":MECH_DARK,"outline":OUT,"outline_w":2})
    # small yordle head in cockpit (THE feature -- tiny pilot in big mech)
    P.append({"type":"circle","cx":128,"cy":96,"r":12,"color":YORDLE_SKIN,"outline":OUT,"outline_w":1})
    # yordle ears (big, pointed)
    P.append({"type":"polygon","points":[(116,88),(104,80),(110,96)],"color":YORDLE_SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(140,88),(152,80),(146,96)],"color":YORDLE_SKIN,"outline":OUT,"outline_w":1})
    # yordle eyes
    P.append({"type":"circle","cx":123,"cy":96,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":133,"cy":96,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    # yordle fur/hair
    P.append({"type":"circle","cx":128,"cy":90,"r":10,"color":YORDLE_FUR,"outline":OUT,"outline_w":1})
    # goggles (yordle pilot)
    P.append({"type":"rect","x":118,"y":92,"w":20,"h":4,"color":METAL_DARK,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Ryze -- rune mage; GLOWING BLUE RUNES on skin + massive forearms
# ============================================================================
def ryze_prims():
    P = []
    SKIN = (180, 150, 120)      # weathered tan skin
    SKIN_DARK = (140, 110, 85)
    RUNE_BLUE = (80, 180, 240)  # glowing blue runes
    RUNE_BRIGHT = (160, 220, 255)
    RUNE_DARK = (40, 100, 160)
    ROBE = (90, 70, 50)         # heavy leather travel gear (brown)
    ROBE_DARK = (60, 45, 30)
    ARCANE = (100, 180, 240)    # floating arcane energy (blue)
    ARCANE_BRIGHT = (180, 220, 255)
    HAIR = (60, 45, 35)         # dark hair
    EYE = (80, 180, 240)        # glowing blue eyes (rune mage)
    OUT = (25, 20, 20)

    # --- Floating arcane energy (behind -- THE missing feature) ---
    P.append({"type":"circle","cx":60,"cy":120,"r":18,"color":ARCANE,"outline":RUNE_DARK,"outline_w":1})
    P.append({"type":"circle","cx":196,"cy":120,"r":18,"color":ARCANE,"outline":RUNE_DARK,"outline_w":1})
    # arcane wisps floating up
    for sy in (100, 88, 76):
        P.append({"type":"circle","cx":50,"cy":sy,"r":5,"color":ARCANE_BRIGHT,"outline":ARCANE,"outline_w":1})
    for sy in (100, 88, 76):
        P.append({"type":"circle","cx":206,"cy":sy,"r":5,"color":ARCANE_BRIGHT,"outline":ARCANE,"outline_w":1})

    # --- Hair (dark, weathered) ---
    P.append({"type":"circle","cx":128,"cy":66,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(108,58),(148,58),(144,74),(112,74)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # beard (ancient weathered face)
    P.append({"type":"polygon","points":[(112,84),(144,84),(140,100),(116,100)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (ancient, weathered) ---
    P.append({"type":"circle","cx":128,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # weathered lines (ancient face -- THE missing feature)
    P.append({"type":"line","start":[112,76],"end":[116,80],"color":SKIN_DARK,"width":1})
    P.append({"type":"line","start":[140,76],"end":[144,80],"color":SKIN_DARK,"width":1})
    # glowing blue eyes (rune mage)
    P.append({"type":"circle","cx":121,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":75,"r":2,"color":RUNE_BRIGHT})
    P.append({"type":"circle","cx":136,"cy":75,"r":2,"color":RUNE_BRIGHT})
    # determined mouth
    P.append({"type":"line","start":[122,88],"end":[134,88],"color":(100,60,50),"width":1})

    # --- Heavy leather travel gear (brown) ---
    P.append({"type":"polygon","points":[(100,96),(156,96),(160,170),(96,170)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # robe shading
    P.append({"type":"polygon","points":[(108,100),(148,100),(152,168),(104,168)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # leather straps
    P.append({"type":"rect","x":100,"y":120,"w":56,"h":6,"color":ROBE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":100,"y":140,"w":56,"h":6,"color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # scroll on back (Ryze carries world runes)
    P.append({"type":"rect","x":118,"y":100,"w":20,"h":30,"color":(180,160,120),"outline":OUT,"outline_w":1})

    # --- MASSIVE MUSCULAR FOREARMS (THE feature -- ENORMOUS, with glowing runes) ---
    # left arm (HUGE forearm -- much bigger than normal, THE feature)
    P.append({"type":"circle","cx":80,"cy":130,"r":18,"color":SKIN,"outline":OUT,"outline_w":2})
    P.append({"type":"rect","x":66,"y":130,"w":28,"h":40,"color":SKIN,"outline":OUT,"outline_w":1,"radius":5})
    # right arm (HUGE forearm)
    P.append({"type":"circle","cx":176,"cy":130,"r":18,"color":SKIN,"outline":OUT,"outline_w":2})
    P.append({"type":"rect","x":162,"y":130,"w":28,"h":40,"color":SKIN,"outline":OUT,"outline_w":1,"radius":5})
    # GLOWING BLUE RUNES on forearms (THE feature -- BIG, obvious, multiple)
    for ry in (134, 142, 150, 158):
        P.append({"type":"line","start":[68,ry],"end":[92,ry],"color":RUNE_BLUE,"width":3})
        P.append({"type":"line","start":[164,ry],"end":[188,ry],"color":RUNE_BLUE,"width":3})
    # rune glow halos (THE glowing blue runes on skin)
    P.append({"type":"circle","cx":80,"cy":146,"r":12,"color":RUNE_BRIGHT,"outline":RUNE_BLUE,"outline_w":2})
    P.append({"type":"circle","cx":176,"cy":146,"r":12,"color":RUNE_BRIGHT,"outline":RUNE_BLUE,"outline_w":2})
    # muscle definition (massive forearms)
    P.append({"type":"circle","cx":80,"cy":140,"r":10,"color":SKIN_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":176,"cy":140,"r":10,"color":SKIN_DARK,"outline":OUT,"outline_w":1})

    # --- GLOWING BLUE RUNES on chest (THE feature) ---
    P.append({"type":"circle","cx":128,"cy":116,"r":8,"color":RUNE_BLUE,"outline":RUNE_DARK,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":116,"r":4,"color":RUNE_BRIGHT,"outline":RUNE_BLUE,"outline_w":1})
    # rune lines on chest
    P.append({"type":"line","start":[120,124],"end":[136,124],"color":RUNE_BLUE,"width":2})
    P.append({"type":"line","start":[124,108],"end":[132,108],"color":RUNE_BLUE,"width":2})

    # --- Hands (glowing with arcane energy) ---
    P.append({"type":"circle","cx":86,"cy":168,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":170,"cy":168,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})
    # arcane glow at hands
    P.append({"type":"circle","cx":86,"cy":168,"r":10,"color":ARCANE,"outline":RUNE_DARK,"outline_w":1})
    P.append({"type":"circle","cx":170,"cy":168,"r":10,"color":ARCANE,"outline":RUNE_DARK,"outline_w":1})

    # --- Legs ---
    P.append({"type":"rect","x":106,"y":170,"w":18,"h":40,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":18,"h":40,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":104,"y":206,"w":22,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":206,"w":22,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    return P


# ============================================================================
# Sejuani -- mounted on a GIANT ARMORED BOAR (Bristle)
# ============================================================================
def sejuani_prims():
    P = []
    BOAR = (120, 95, 80)
    BOAR_DARK = (85, 65, 55)
    ICE_BLUE = (180, 220, 240)
    FUR = (220, 220, 230)
    FUR_DARK = (180, 180, 195)
    RIDER_SKIN = (230, 220, 225)  # Iceborn pale skin
    RIDER_HAIR = (220, 215, 220)  # white-blonde
    RIDER_HAIR_DARK = (180, 175, 185)
    ARMOR = (150, 160, 175)
    ARMOR_DARK = (95, 105, 120)
    TUSK = (245, 240, 225)
    FLAIL = (180, 220, 240)
    EYE = (40, 30, 25)
    OUT = (40, 25, 20)

    # --- GIANT ARMORED BOAR (THE feature -- big body, low) ---
    P.append({"type":"ellipse","x":50,"y":150,"w":156,"h":78,"color":BOAR,"outline":OUT,"outline_w":2})
    # boar head (front, right)
    P.append({"type":"circle","cx":200,"cy":178,"r":28,"color":BOAR,"outline":OUT,"outline_w":2})
    # boar snout
    P.append({"type":"ellipse","x":210,"y":172,"w":28,"h":22,"color":BOAR_DARK,"outline":OUT,"outline_w":1})
    # nostrils
    P.append({"type":"circle","cx":226,"cy":178,"r":2,"color":OUT})
    P.append({"type":"circle","cx":226,"cy":184,"r":2,"color":OUT})
    # boar eye
    P.append({"type":"circle","cx":194,"cy":172,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    # boar ear
    P.append({"type":"polygon","points":[(182,156),(188,144),(196,156)],"color":BOAR_DARK,"outline":OUT,"outline_w":1})
    # BIG tusks (THE feature -- curved, white, from snout)
    P.append({"type":"polygon","points":[(212,186),(224,190),(218,206),(210,198)],"color":TUSK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(212,170),(224,166),(218,150),(210,158)],"color":TUSK,"outline":OUT,"outline_w":1})

    # --- Boar legs (4 stubby) ---
    for lx in (70, 105, 150, 185):
        P.append({"type":"rect","x":lx,"y":210,"w":18,"h":20,"color":BOAR_DARK,"outline":OUT,"outline_w":1,"radius":3})
        P.append({"type":"rect","x":lx-2,"y":224,"w":22,"h":8,"color":(60,45,35),"outline":OUT,"outline_w":1,"radius":2})

    # --- HEAVY FUR clothing + tribal armor on boar ---
    # fur trim (THE missing feature -- big fur on top of boar)
    P.append({"type":"rect","x":62,"y":138,"w":120,"h":14,"color":FUR,"outline":OUT,"outline_w":1})
    # fur texture (fluffy)
    for fx in (72, 88, 104, 120, 136, 152, 168):
        P.append({"type":"circle","cx":fx,"cy":142,"r":6,"color":FUR,"outline":FUR_DARK,"outline_w":1})
    # tribal Freljordian armor (ice-blue metal plating)
    P.append({"type":"ellipse","x":76,"y":146,"w":100,"h":24,"color":ARMOR,"outline":OUT,"outline_w":2})
    # armor studs
    for sx in (92, 112, 132, 152):
        P.append({"type":"circle","cx":sx,"cy":158,"r":4,"color":ICE_BLUE,"outline":OUT,"outline_w":1})

    # --- Ice crystals on boar (Freljord) ---
    P.append({"type":"polygon","points":[(110,130),(116,116),(122,130)],"color":ICE_BLUE,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(140,128),(146,114),(152,128)],"color":ICE_BLUE,"outline":OUT,"outline_w":1})

    # --- Rider: Sejuani (on top of boar) ---
    # rider torso (tribal armor)
    P.append({"type":"polygon","points":[(112,96),(144,96),(148,140),(108,140)],
              "color":ARMOR,"outline":OUT,"outline_w":1})
    # FUR CAPE (THE missing feature -- heavy fur clothing)
    P.append({"type":"polygon","points":[(108,96),(144,96),(100,130),(94,112)],"color":FUR,"outline":FUR_DARK,"outline_w":1})
    # fur texture on cape
    for fx in (98, 104, 110):
        P.append({"type":"circle","cx":fx,"cy":118,"r":4,"color":FUR,"outline":FUR_DARK,"outline_w":1})
    # rider head (Iceborn pale skin -- THE missing feature)
    P.append({"type":"circle","cx":128,"cy":80,"r":15,"color":RIDER_SKIN,"outline":OUT,"outline_w":1})
    # rider hair (white-blonde, braided)
    P.append({"type":"circle","cx":128,"cy":74,"r":15,"color":RIDER_HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(112,72),(144,72),(140,84),(116,84)],"color":RIDER_HAIR,"outline":RIDER_HAIR_DARK,"outline_w":1})
    # rider eyes
    P.append({"type":"circle","cx":122,"cy":82,"r":2,"color":EYE})
    P.append({"type":"circle","cx":134,"cy":82,"r":2,"color":EYE})
    # rider arms (holding flail)
    P.append({"type":"rect","x":144,"y":100,"w":12,"h":36,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":4})

    # --- Flail (morning star, ice) ---
    P.append({"type":"line","start":[156,136],"end":[180,118],"color":(90,60,40),"width":3})
    P.append({"type":"circle","cx":184,"cy":114,"r":12,"color":FLAIL,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":184,"cy":114,"r":8,"color":ARMOR,"outline":OUT,"outline_w":1})
    # spikes on flail
    for ang in (0, 72, 144, 216, 288):
        import math as _m
        sx = 184 + int(14 * _m.cos(_m.radians(ang)))
        sy = 114 + int(14 * _m.sin(_m.radians(ang)))
        P.append({"type":"circle","cx":sx,"cy":sy,"r":3,"color":FLAIL,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Singed -- mad chemist; CHEMICAL TANK on back + GAS MASK + green vials
# ============================================================================
def singed_prims():
    P = []
    SKIN = (210, 195, 175)
    LAB_COAT = (180, 175, 165)   # leather apron / lab coat (worn grey)
    LAB_DARK = (130, 120, 110)
    TANK = (120, 120, 130)       # chemical tank (metal grey)
    TANK_DARK = (80, 80, 90)
    TANK_GREEN = (100, 200, 80)  # glowing green chemical
    TANK_GLASS = (140, 220, 120)
    GAS_MASK = (60, 55, 55)      # gas mask (dark)
    GAS_MASK_FILTER = (90, 85, 85)
    GREEN = (100, 220, 80)       # toxic green
    GREEN_BRIGHT = (160, 255, 120)
    GREEN_DARK = (50, 140, 40)
    VIAL = (180, 255, 100)       # glowing chemical vials
    BROWN = (110, 80, 55)
    EYE = (40, 35, 35)
    OUT = (25, 20, 20)

    # --- CHEMICAL TANK ON BACK (THE feature -- BIG, with glowing green liquid) ---
    # tank body (big, metal, on back -- visible behind/around the body)
    P.append({"type":"ellipse","x":78,"y":80,"w":100,"h":80,"color":TANK,"outline":OUT,"outline_w":3})
    # tank glass section (glowing green chemical -- THE feature)
    P.append({"type":"ellipse","x":92,"y":92,"w":72,"h":56,"color":TANK_GREEN,"outline":TANK_DARK,"outline_w":2})
    # chemical liquid (glowing green, bright)
    P.append({"type":"ellipse","x":96,"y":100,"w":64,"h":40,"color":GREEN,"outline":GREEN_DARK,"outline_w":1})
    # chemical bubbles (glowing, THE toxic green)
    for bx, by in [(108,108),(124,104),(140,112),(156,106)]:
        P.append({"type":"circle","cx":bx,"cy":by,"r":4,"color":GREEN_BRIGHT,"outline":GREEN,"outline_w":1})
    # tank pipes (connecting to hands/sprayer)
    P.append({"type":"line","start":[88,120],"end":[72,150],"color":TANK_DARK,"width":5})
    P.append({"type":"line","start":[168,120],"end":[184,150],"color":TANK_DARK,"width":5})
    # tank metal straps
    P.append({"type":"rect","x":84,"y":86,"w":88,"h":6,"color":TANK_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":84,"y":140,"w":88,"h":6,"color":TANK_DARK,"outline":OUT,"outline_w":1})

    # --- Head + GAS MASK (THE feature -- big, obvious respirator) ---
    P.append({"type":"circle","cx":128,"cy":76,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # GAS MASK (covering lower face -- THE missing feature, BIG)
    P.append({"type":"polygon","points":[(110,76),(146,76),(142,96),(114,96)],
              "color":GAS_MASK,"outline":OUT,"outline_w":2})
    # gas mask eye lenses (round, dark)
    P.append({"type":"circle","cx":120,"cy":80,"r":5,"color":GAS_MASK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":136,"cy":80,"r":5,"color":GAS_MASK,"outline":OUT,"outline_w":1})
    # gas mask filter (THE feature -- big circular filter canister)
    P.append({"type":"circle","cx":128,"cy":90,"r":7,"color":GAS_MASK_FILTER,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":90,"r":4,"color":GAS_MASK,"outline":OUT,"outline_w":1})
    # mask straps
    P.append({"type":"line","start":[110,80],"end":[106,74],"color":GAS_MASK,"width":2})
    P.append({"type":"line","start":[146,80],"end":[150,74],"color":GAS_MASK,"width":2})

    # --- Hair (balding, grey) ---
    P.append({"type":"circle","cx":128,"cy":68,"r":14,"color":(180,175,170),"outline":OUT,"outline_w":1})

    # --- LEATHER APRON / lab coat (THE missing feature) ---
    P.append({"type":"polygon","points":[(100,100),(156,100),(160,190),(96,190)],
              "color":LAB_COAT,"outline":OUT,"outline_w":1})
    # apron shading
    P.append({"type":"polygon","points":[(108,104),(148,104),(152,188),(104,188)],
              "color":LAB_DARK,"outline":OUT,"outline_w":1})
    # apron straps
    P.append({"type":"line","start":[100,100],"end":[156,100],"color":BROWN,"width":2})
    # leather texture lines
    P.append({"type":"line","start":[128,104],"end":[128,188],"color":LAB_DARK,"width":1})

    # --- GLOWING CHEMICAL VIALS (THE feature -- on belt, glowing green) ---
    for vx in (108, 128, 148):
        P.append({"type":"rect","x":vx-4,"y":150,"w":8,"h":16,"color":VIAL,"outline":OUT,"outline_w":1,"radius":2})
        P.append({"type":"circle","cx":vx,"cy":158,"r":5,"color":GREEN_BRIGHT,"outline":GREEN,"outline_w":1})
    # vial glow
    for vx in (108, 128, 148):
        P.append({"type":"circle","cx":vx,"cy":158,"r":8,"color":(140,220,100),"outline":GREEN_DARK,"outline_w":1})

    # --- Arms (hunched posture -- THE missing feature) ---
    # hunched: arms forward/down, not straight
    P.append({"type":"polygon","points":[(96,108),(80,120),(76,156),(88,156),(96,130)],
              "color":LAB_COAT,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(160,108),(176,120),(180,156),(168,156),(160,130)],
              "color":LAB_COAT,"outline":OUT,"outline_w":1})
    # hands (holding chemical sprayer)
    P.append({"type":"circle","cx":80,"cy":156,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":176,"cy":156,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- CHEMICAL SPRAYER (THE weapon -- in hands, spraying green) ---
    P.append({"type":"rect","x":76,"y":150,"w":24,"h":12,"color":TANK_DARK,"outline":OUT,"outline_w":2})
    # sprayer nozzle
    P.append({"type":"rect","x":64,"y":153,"w":14,"h":6,"color":TANK_DARK,"outline":OUT,"outline_w":1})
    # chemical spray (toxic green cloud)
    P.append({"type":"circle","cx":56,"cy":156,"r":10,"color":GREEN,"outline":GREEN_DARK,"outline_w":1})
    P.append({"type":"circle","cx":48,"cy":150,"r":7,"color":GREEN_BRIGHT,"outline":GREEN,"outline_w":1})
    P.append({"type":"circle","cx":48,"cy":162,"r":6,"color":GREEN,"outline":GREEN_DARK,"outline_w":1})

    # --- Legs (hunched posture, bent) ---
    P.append({"type":"rect","x":106,"y":190,"w":18,"h":28,"color":LAB_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":190,"w":18,"h":28,"color":LAB_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":104,"y":212,"w":22,"h":10,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":212,"w":22,"h":10,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})
    return P


# ============================================================================
# Skarner -- colossal armored scorpion; MASSIVE CRYSTALLINE STINGER tail
# ============================================================================
def skarner_prims():
    P = []
    SHELL = (80, 130, 120)       # teal chitinous plating
    SHELL_DARK = (50, 90, 85)
    SHELL_LIGHT = (120, 180, 170)
    CRYSTAL = (140, 100, 180)    # glowing purple crystals
    CRYSTAL_BRIGHT = (200, 160, 240)
    CRYSTAL_DARK = (90, 60, 120)
    GOLD = (215, 175, 60)
    CLAW = (200, 190, 180)       # claw (bone)
    CLAW_DARK = (140, 130, 120)
    EYE = (200, 160, 240)        # glowing purple eyes
    OUT = (25, 30, 35)

    # --- MASSIVE CRYSTALLINE STINGER TAIL (THE feature -- BIG, curling up + over) ---
    tail = [(160,170),(190,150),(210,110),(200,70),(170,50),(140,56)]
    for i in range(len(tail)-1):
        P.append({"type":"line","start":tail[i],"end":tail[i+1],"color":SHELL,"width":18})
    for cx, cy in tail:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":11,"color":SHELL,"outline":SHELL_DARK,"outline_w":2})
    # tail segments (chitinous plates)
    for cx, cy in tail:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":7,"color":SHELL_DARK,"outline":OUT,"outline_w":1})
    # CRYSTALLINE STINGER (THE feature -- big glowing purple crystal at tail tip)
    P.append({"type":"polygon","points":[(135,56),(145,56),(140,38)],"color":CRYSTAL,"outline":CRYSTAL_DARK,"outline_w":3})
    P.append({"type":"circle","cx":140,"cy":50,"r":10,"color":CRYSTAL_BRIGHT,"outline":CRYSTAL,"outline_w":2})
    P.append({"type":"circle","cx":140,"cy":50,"r":5,"color":(255,220,255)})
    # crystal glow aura
    P.append({"type":"circle","cx":140,"cy":50,"r":16,"color":(160,120,200),"outline":CRYSTAL,"outline_w":1})
    # glowing crystals along the tail
    for cx, cy in [(190,150),(210,110),(200,70)]:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":6,"color":CRYSTAL,"outline":CRYSTAL_DARK,"outline_w":1})
        P.append({"type":"circle","cx":cx,"cy":cy,"r":3,"color":CRYSTAL_BRIGHT,"outline":CRYSTAL,"outline_w":1})

    # --- SCORPION BODY (big, armored, low) ---
    P.append({"type":"ellipse","x":40,"y":150,"w":130,"h":70,"color":SHELL,"outline":OUT,"outline_w":3})
    # body segments (chitinous plating -- THE missing feature)
    P.append({"type":"line","start":[80,150],"end":[80,220],"color":SHELL_DARK,"width":2})
    P.append({"type":"line","start":[110,150],"end":[110,220],"color":SHELL_DARK,"width":2})
    # body plate texture
    for sx in (60, 80, 100, 120):
        P.append({"type":"polygon","points":[(sx-6,155),(sx,148),(sx+6,155)],"color":SHELL_DARK,"outline":OUT,"outline_w":1})
    # GLOWING CRYSTALS on body (THE missing feature)
    for cx, cy in [(70,170),(100,170),(130,170)]:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":7,"color":CRYSTAL,"outline":CRYSTAL_DARK,"outline_w":2})
        P.append({"type":"circle","cx":cx,"cy":cy,"r":4,"color":CRYSTAL_BRIGHT,"outline":CRYSTAL,"outline_w":1})

    # --- SCORPION HEAD (front, left) ---
    P.append({"type":"circle","cx":50,"cy":170,"r":22,"color":SHELL,"outline":OUT,"outline_w":2})
    # glowing purple eyes
    P.append({"type":"circle","cx":42,"cy":166,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":58,"cy":166,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":43,"cy":165,"r":2,"color":(255,220,255)})
    P.append({"type":"circle","cx":59,"cy":165,"r":2,"color":(255,220,255)})
    # mandibles
    P.append({"type":"polygon","points":[(36,178),(28,184),(34,188)],"color":SHELL_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(64,178),(72,184),(66,188)],"color":SHELL_DARK,"outline":OUT,"outline_w":1})

    # --- BIG CLAWS (THE feature -- two massive pincers, front) ---
    # left claw (big, at front-left)
    P.append({"type":"circle","cx":30,"cy":150,"r":14,"color":SHELL,"outline":OUT,"outline_w":2})
    # pincer fingers
    P.append({"type":"polygon","points":[(20,140),(10,130),(18,150)],"color":CLAW,"outline":CLAW_DARK,"outline_w":2})
    P.append({"type":"polygon","points":[(20,160),(10,170),(18,150)],"color":CLAW,"outline":CLAW_DARK,"outline_w":2})
    # right claw
    P.append({"type":"circle","cx":30,"cy":190,"r":14,"color":SHELL,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(20,180),(10,170),(18,190)],"color":CLAW,"outline":CLAW_DARK,"outline_w":2})
    P.append({"type":"polygon","points":[(20,200),(10,210),(18,190)],"color":CLAW,"outline":CLAW_DARK,"outline_w":2})

    # --- SIX LEGS (THE missing feature -- scorpion has 6 legs) ---
    for lx in (70, 95, 120, 145):
        # left legs
        P.append({"type":"line","start":[lx,200],"end":[lx-12,220],"color":SHELL_DARK,"width":5})
        P.append({"type":"line","start":[lx-12,220],"end":[lx-16,230],"color":SHELL_DARK,"width":4})
        # right legs
        P.append({"type":"line","start":[lx,200],"end":[lx+12,220],"color":SHELL_DARK,"width":5})
        P.append({"type":"line","start":[lx+12,220],"end":[lx+16,230],"color":SHELL_DARK,"width":4})
    return P


# ============================================================================
# Sylas -- the Unshackled; BROKEN SHACKLES + glowing magical chains
# ============================================================================
def sylas_prims():
    P = []
    SKIN = (225, 200, 175)
    HAIR = (60, 50, 45)         # dark brown hair
    BEARD = (70, 60, 55)        # rugged beard
    SHIRT = (110, 100, 95)      # tattered prisoner clothing (grey)
    SHIRT_DARK = (75, 68, 65)
    CHAIN = (160, 160, 170)     # magical chains (metallic grey)
    CHAIN_DARK = (100, 100, 110)
    SHACKLE = (120, 120, 130)   # shackles (dark metal)
    SHACKLE_DARK = (70, 70, 80)
    BLUE = (100, 200, 255)      # electric blue glow
    BLUE_BRIGHT = (180, 230, 255)
    BLUE_DARK = (40, 120, 200)
    EYE = (50, 40, 35)
    OUT = (25, 20, 20)

    # --- GLOWING MAGICAL CHAINS (THE feature -- BIG, on wrists, electric blue) ---
    # chain glow aura (electric blue, behind chains)
    P.append({"type":"circle","cx":76,"cy":156,"r":16,"color":(80,160,220),"outline":BLUE,"outline_w":1})
    P.append({"type":"circle","cx":180,"cy":156,"r":16,"color":(80,160,220),"outline":BLUE,"outline_w":1})
    # left chain (dangling from wrist, glowing blue)
    chain_l = [(76,156),(68,176),(72,196)]
    for i in range(len(chain_l)-1):
        P.append({"type":"line","start":chain_l[i],"end":chain_l[i+1],"color":CHAIN,"width":5})
    for cx, cy in chain_l:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":5,"color":CHAIN,"outline":CHAIN_DARK,"outline_w":1})
    # blue glow on left chain
    P.append({"type":"line","start":[76,156],"end":[72,196],"color":BLUE,"width":2})
    # right chain
    chain_r = [(180,156),(188,176),(184,196)]
    for i in range(len(chain_r)-1):
        P.append({"type":"line","start":chain_r[i],"end":chain_r[i+1],"color":CHAIN,"width":5})
    for cx, cy in chain_r:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":5,"color":CHAIN,"outline":CHAIN_DARK,"outline_w":1})
    P.append({"type":"line","start":[180,156],"end":[184,196],"color":BLUE,"width":2})
    # blue energy sparks from chains
    for sx, sy in [(64,166),(80,166),(176,166),(192,166)]:
        P.append({"type":"circle","cx":sx,"cy":sy,"r":3,"color":BLUE_BRIGHT,"outline":BLUE,"outline_w":1})

    # --- HEAVY BROKEN SHACKLES ON WRISTS (THE feature -- BIG, obvious) ---
    # left shackle (big, dark metal, broken open)
    P.append({"type":"circle","cx":76,"cy":156,"r":10,"color":SHACKLE,"outline":OUT,"outline_w":3})
    # broken shackle gap (the shackle is broken open -- THE feature)
    P.append({"type":"polygon","points":[(72,148),(80,148),(78,144),(74,144)],"color":OUT,"outline":SHACKLE_DARK,"outline_w":1})
    # shackle spike (broken metal spike)
    P.append({"type":"polygon","points":[(70,146),(66,140),(74,148)],"color":SHACKLE_DARK,"outline":OUT,"outline_w":1})
    # right shackle
    P.append({"type":"circle","cx":180,"cy":156,"r":10,"color":SHACKLE,"outline":OUT,"outline_w":3})
    P.append({"type":"polygon","points":[(176,148),(184,148),(182,144),(178,144)],"color":OUT,"outline":SHACKLE_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(186,146),(190,140),(182,148)],"color":SHACKLE_DARK,"outline":OUT,"outline_w":1})

    # --- Hair (dark, rugged) ---
    P.append({"type":"circle","cx":128,"cy":66,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(108,58),(148,58),(144,72),(112,72)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head + RUGGED BEARD (THE feature) ---
    P.append({"type":"circle","cx":128,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # rugged beard (THE feature -- big, obvious)
    P.append({"type":"polygon","points":[(110,82),(146,82),(142,102),(114,102)],
              "color":BEARD,"outline":OUT,"outline_w":1})
    # beard texture
    P.append({"type":"line","start":[120,88],"end":[120,100],"color":HAIR,"width":1})
    P.append({"type":"line","start":[128,88],"end":[128,100],"color":HAIR,"width":1})
    P.append({"type":"line","start":[136,88],"end":[136,100],"color":HAIR,"width":1})
    # determined eyes
    P.append({"type":"line","start":[119,74],"end":[125,74],"color":EYE,"width":2})
    P.append({"type":"line","start":[131,74],"end":[137,74],"color":EYE,"width":2})
    # determined brows
    P.append({"type":"polygon","points":[(114,68),(126,71),(126,73),(114,70)],"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(130,71),(142,68),(142,70),(130,73)],"color":HAIR,"outline":OUT,"outline_w":1})

    # --- TATTERED PRISONER CLOTHING (THE missing feature) ---
    P.append({"type":"polygon","points":[(100,96),(156,96),(160,170),(96,170)],
              "color":SHIRT,"outline":OUT,"outline_w":1})
    # tattered edges (jagged hem -- THE feature)
    P.append({"type":"polygon","points":[(96,170),(100,180),(104,170),(108,182),(112,170),(116,180),(120,170),(124,182),(128,170),(132,180),(136,170),(140,182),(144,170),(148,180),(152,170),(156,182),(160,170)],
              "color":SHIRT_DARK,"outline":OUT,"outline_w":1})
    # clothing shading
    P.append({"type":"polygon","points":[(108,100),(148,100),(152,168),(104,168)],
              "color":SHIRT_DARK,"outline":OUT,"outline_w":1})
    # tattered tears in clothing
    P.append({"type":"line","start":[112,130],"end":[118,140],"color":OUT,"width":1})
    P.append({"type":"line","start":[140,120],"end":[134,134],"color":OUT,"width":1})
    # rope belt
    P.append({"type":"rect","x":98,"y":140,"w":60,"h":6,"color":(90,70,50),"outline":OUT,"outline_w":1})

    # --- Arms (muscular, raised -- showing shackles) ---
    P.append({"type":"rect","x":84,"y":104,"w":14,"h":50,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":158,"y":104,"w":14,"h":50,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    # muscular forearms
    P.append({"type":"circle","cx":91,"cy":130,"r":8,"color":SKIN,"outline":SKIN_DARK if False else (190,165,140),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":165,"cy":130,"r":8,"color":SKIN,"outline":(190,165,140),"outline":OUT,"outline_w":1})

    # --- Legs (tattered pants) ---
    P.append({"type":"rect","x":106,"y":170,"w":18,"h":40,"color":SHIRT_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":18,"h":40,"color":SHIRT_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # tattered leg hems
    P.append({"type":"polygon","points":[(106,206),(124,206),(120,214),(116,208),(112,214),(108,208)],"color":SHIRT_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(132,206),(150,206),(146,214),(142,208),(138,214),(134,208)],"color":SHIRT_DARK,"outline":OUT,"outline_w":1})
    # bare feet (prisoner)
    P.append({"type":"ellipse","x":104,"y":210,"w":22,"h":12,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"ellipse","x":130,"y":210,"w":22,"h":12,"color":SKIN,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Run all 6
# ============================================================================
CHAMPS = [
    ("Rumble", rumble_prims, "junk-pile mech suit + yordle pilot"),
    ("Ryze", ryze_prims, "glowing blue runes + massive forearms"),
    ("Sejuani", sejuani_prims, "giant armored boar (mounted)"),
    ("Singed", singed_prims, "chemical tank + gas mask + green vials"),
    ("Skarner", skarner_prims, "massive crystalline stinger (scorpion)"),
    ("Sylas", sylas_prims, "broken shackles + glowing magical chains"),
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
