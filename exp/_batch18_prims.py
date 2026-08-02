"""Batch 18: Taric, Teemo, Thresh, Trundle, Urgot, Varus.

- Taric   -> CRYSTALLINE ARMOR + glowing gemstones (big, shining) + flowing hair
- Teemo   -> GREEN SCOUT HAT + BIG GOGGLES + blowgun (yordle scout)
- Thresh  -> SOUL LANTERN (big glowing green lantern on chain) + spectral cloak
- Trundle -> BIG TUSKS + True Ice club (massive troll, blue skin, fur pelt)
- Urgot   -> SIX SPIDER-LIKE ROBOTIC LEGS (big, mechanical, cyborg body)
- Varus   -> COMPOSITE BOW (big) + glowing purple corruption on left side
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve


# ============================================================================
# Taric -- the Shield; CRYSTALLINE ARMOR + glowing gemstones + flowing hair
# ============================================================================
def taric_prims():
    P = []
    SKIN = (235, 215, 190)
    HAIR = (235, 220, 180)       # long flowing golden-blonde hair
    HAIR_DARK = (190, 175, 140)
    CRYSTAL = (120, 200, 230)    # crystalline armor (blue crystal)
    CRYSTAL_BRIGHT = (180, 230, 250)
    CRYSTAL_DARK = (60, 130, 180)
    GEM = (100, 200, 240)        # glowing gemstones (blue)
    GEM_BRIGHT = (180, 240, 255)
    GEM_PINK = (240, 130, 200)   # pink gem accents
    GOLD = (220, 180, 60)
    ROBE = (240, 240, 245)       # white robes
    ROBE_DARK = (200, 200, 215)
    SHIELD = (120, 200, 230)     # crystalline shield
    EYE = (80, 160, 200)         # blue eyes
    OUT = (30, 25, 35)

    # --- Long flowing hair (BIG, THE feature -- flowing past shoulders) ---
    P.append({"type":"circle","cx":128,"cy":66,"r":22,"color":HAIR,"outline":OUT,"outline_w":1})
    # long flowing hair (down past shoulders, BIG)
    P.append({"type":"polygon","points":[(100,60),(156,60),(170,140),(86,140)],
              "color":HAIR,"outline":HAIR_DARK,"outline_w":2})
    # hair highlight streaks
    P.append({"type":"polygon","points":[(108,66),(116,66),(112,130),(104,120)],
              "color":(255,245,210),"outline":HAIR_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(140,66),(148,66),(152,120),(144,130)],
              "color":(255,245,210),"outline":HAIR_DARK,"outline_w":1})
    # bangs
    P.append({"type":"polygon","points":[(108,58),(148,58),(144,72),(112,72)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (regal, muscular) ---
    P.append({"type":"circle","cx":128,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # blue eyes (regal)
    P.append({"type":"circle","cx":121,"cy":76,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":76,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":75,"r":1,"color":(255,255,255)})
    P.append({"type":"circle","cx":136,"cy":75,"r":1,"color":(255,255,255)})
    # regal smile
    P.append({"type":"line","start":[122,86],"end":[134,86],"color":(150,100,120),"width":1})

    # --- CRYSTALLINE ARMOR (THE feature -- BIG, shiny crystal plates) ---
    # torso crystalline chest plate (BIG, faceted crystal look)
    P.append({"type":"polygon","points":[(100,94),(156,94),(160,170),(96,170)],
              "color":CRYSTAL,"outline":OUT,"outline_w":2})
    # crystal facets (geometric cuts -- makes it read as crystal, not cloth)
    P.append({"type":"polygon","points":[(104,98),(128,98),(128,134),(100,134)],
              "color":CRYSTAL_BRIGHT,"outline":CRYSTAL_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(128,98),(152,98),(156,134),(128,134)],
              "color":CRYSTAL_DARK,"outline":OUT,"outline_w":1})
    # crystal facet lines (THE crystalline look)
    P.append({"type":"line","start":[128,98],"end":[128,170],"color":CRYSTAL_DARK,"width":2})
    P.append({"type":"line","start":[100,134],"end":[156,134],"color":CRYSTAL_DARK,"width":1})
    P.append({"type":"line","start":[108,98],"end":[108,134],"color":CRYSTAL_BRIGHT,"width":1})
    P.append({"type":"line","start":[148,98],"end":[148,134],"color":CRYSTAL_BRIGHT,"width":1})

    # --- GLOWING GEMSTONES (THE feature -- BIG, embedded in armor) ---
    # center gem (BIG, glowing blue)
    P.append({"type":"circle","cx":128,"cy":116,"r":8,"color":GEM,"outline":CRYSTAL_DARK,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":116,"r":5,"color":GEM_BRIGHT,"outline":GEM,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":116,"r":2,"color":(255,255,255)})
    # gem glow aura
    P.append({"type":"circle","cx":128,"cy":116,"r":14,"color":(140,220,250),"outline":GEM,"outline_w":1})
    # shoulder gems (glowing)
    P.append({"type":"circle","cx":104,"cy":100,"r":8,"color":GEM,"outline":CRYSTAL_DARK,"outline_w":2})
    P.append({"type":"circle","cx":104,"cy":100,"r":4,"color":GEM_BRIGHT,"outline":GEM,"outline_w":1})
    P.append({"type":"circle","cx":152,"cy":100,"r":8,"color":GEM,"outline":CRYSTAL_DARK,"outline_w":2})
    P.append({"type":"circle","cx":152,"cy":100,"r":4,"color":GEM_BRIGHT,"outline":GEM,"outline_w":1})
    # pink gem accents
    P.append({"type":"circle","cx":112,"cy":148,"r":5,"color":GEM_PINK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":144,"cy":148,"r":5,"color":GEM_PINK,"outline":OUT,"outline_w":1})

    # --- Gold trim ---
    P.append({"type":"line","start":[100,94],"end":[156,94],"color":GOLD,"width":2})
    P.append({"type":"line","start":[96,170],"end":[160,170],"color":GOLD,"width":2})

    # --- Arms (muscular, with crystal bracers) ---
    P.append({"type":"rect","x":82,"y":108,"w":16,"h":50,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":158,"y":108,"w":16,"h":50,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    # crystal bracers (with gems)
    P.append({"type":"rect","x":82,"y":140,"w":16,"h":14,"color":CRYSTAL,"outline":CRYSTAL_DARK,"outline_w":1})
    P.append({"type":"rect","x":158,"y":140,"w":16,"h":14,"color":CRYSTAL,"outline":CRYSTAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":90,"cy":147,"r":3,"color":GEM_BRIGHT,"outline":GEM,"outline_w":1})
    P.append({"type":"circle","cx":166,"cy":147,"r":3,"color":GEM_BRIGHT,"outline":GEM,"outline_w":1})
    # hands
    P.append({"type":"circle","cx":90,"cy":162,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":166,"cy":162,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs ---
    P.append({"type":"rect","x":106,"y":170,"w":18,"h":40,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":134,"y":170,"w":18,"h":40,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # crystal shin guards
    P.append({"type":"rect","x":106,"y":180,"w":18,"h":16,"color":CRYSTAL,"outline":CRYSTAL_DARK,"outline_w":1})
    P.append({"type":"rect","x":134,"y":180,"w":18,"h":16,"color":CRYSTAL,"outline":CRYSTAL_DARK,"outline_w":1})
    P.append({"type":"rect","x":104,"y":206,"w":22,"h":12,"color":GOLD,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":132,"y":206,"w":22,"h":12,"color":GOLD,"outline":OUT,"outline_w":1,"radius":2})

    # --- CRYSTALLINE SHIELD (THE weapon, big, in front of left arm) ---
    P.append({"type":"circle","cx":70,"cy":150,"r":20,"color":SHIELD,"outline":CRYSTAL_DARK,"outline_w":3})
    P.append({"type":"circle","cx":70,"cy":150,"r":12,"color":CRYSTAL_BRIGHT,"outline":CRYSTAL,"outline_w":1})
    P.append({"type":"circle","cx":70,"cy":150,"r":6,"color":GEM,"outline":CRYSTAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":70,"cy":150,"r":3,"color":GEM_BRIGHT,"outline":GEM,"outline_w":1})
    # shield glow
    P.append({"type":"circle","cx":70,"cy":150,"r":26,"color":(140,220,250),"outline":GEM,"outline_w":1})
    return P


# ============================================================================
# Teemo -- yordle scout; GREEN SCOUT HAT + BIG GOGGLES + blowgun
# ============================================================================
def teemo_prims():
    P = []
    FUR = (170, 135, 100)        # brown fur
    FUR_DARK = (120, 90, 60)
    SKIN = (230, 200, 175)
    HAT = (90, 140, 70)          # green scout hat
    HAT_DARK = (60, 100, 45)
    GOGGLE = (80, 80, 90)        # goggle frame (dark)
    GOGGLE_LENS = (180, 220, 200)  # goggle lens (light green-tinted)
    UNIFORM = (90, 140, 70)      # green scout uniform
    UNIFORM_DARK = (60, 100, 45)
    BROWN = (110, 80, 55)
    GOLD = (200, 165, 55)
    BLOWGUN = (110, 80, 55)      # blowgun (brown wood)
    EYE = (40, 30, 25)
    OUT = (25, 20, 15)

    # --- GREEN SCOUT HAT (THE feature -- BIG, the icon) ---
    # hat dome (big, green, rounded)
    P.append({"type":"ellipse","x":86,"y":48,"w":64,"h":36,"color":HAT,"outline":OUT,"outline_w":2})
    # hat brim (wide, flat)
    P.append({"type":"ellipse","x":78,"y":66,"w":80,"h":16,"color":HAT_DARK,"outline":OUT,"outline_w":2})
    # hat band (darker green)
    P.append({"type":"rect","x":88,"y":62,"w":60,"h":6,"color":HAT_DARK,"outline":OUT,"outline_w":1})

    # --- BIG GOGGLES (THE missing feature -- on hat/forehead, prominent) ---
    # goggle strap
    P.append({"type":"rect","x":86,"y":58,"w":64,"h":4,"color":GOGGLE,"outline":OUT,"outline_w":1})
    # left goggle lens (BIG, round)
    P.append({"type":"circle","cx":104,"cy":64,"r":10,"color":GOGGLE,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":104,"cy":64,"r":7,"color":GOGGLE_LENS,"outline":GOGGLE,"outline_w":1})
    P.append({"type":"circle","cx":104,"cy":63,"r":3,"color":(255,255,255),"outline":GOGGLE_LENS,"outline_w":1})
    # right goggle lens
    P.append({"type":"circle","cx":132,"cy":64,"r":10,"color":GOGGLE,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":132,"cy":64,"r":7,"color":GOGGLE_LENS,"outline":GOGGLE,"outline_w":1})
    P.append({"type":"circle","cx":132,"cy":63,"r":3,"color":(255,255,255),"outline":GOGGLE_LENS,"outline_w":1})
    # goggle bridge
    P.append({"type":"rect","x":114,"y":62,"w":8,"h":4,"color":GOGGLE,"outline":OUT,"outline_w":1})

    # --- Head (yordle, round cheeks) ---
    P.append({"type":"circle","cx":118,"cy":84,"r":20,"color":SKIN,"outline":OUT,"outline_w":1})
    # round cheeks (THE missing feature -- big, obvious)
    P.append({"type":"circle","cx":104,"cy":92,"r":6,"color":(255,180,150),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":132,"cy":92,"r":6,"color":(255,180,150),"outline":OUT,"outline_w":1})
    # big yordle ears (pointed, fur-covered)
    P.append({"type":"polygon","points":[(98,80),(78,68),(86,90)],"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(138,80),(158,68),(150,90)],"color":FUR,"outline":OUT,"outline_w":1})
    # eyes (under goggles)
    P.append({"type":"circle","cx":111,"cy":84,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":125,"cy":84,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    # mischievous smile
    P.append({"type":"line","start":[110,96],"end":[126,96],"color":(140,60,50),"width":1})
    # nose
    P.append({"type":"circle","cx":118,"cy":90,"r":2,"color":(200,150,130),"outline":OUT,"outline_w":1})

    # --- Scout uniform (green) ---
    P.append({"type":"polygon","points":[(96,106),(140,106),(144,170),(92,170)],
              "color":UNIFORM,"outline":OUT,"outline_w":1})
    # uniform shading
    P.append({"type":"polygon","points":[(102,110),(134,110),(138,168),(98,168)],
              "color":UNIFORM_DARK,"outline":OUT,"outline_w":1})
    # gold buttons
    for by in (120, 134, 148):
        P.append({"type":"circle","cx":118,"cy":by,"r":2,"color":GOLD,"outline":OUT,"outline_w":1})
    # uniform collar
    P.append({"type":"polygon","points":[(100,106),(136,106),(130,116),(106,116)],
              "color":UNIFORM_DARK,"outline":OUT,"outline_w":1})
    # brown belt
    P.append({"type":"rect","x":92,"y":150,"w":52,"h":6,"color":BROWN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":118,"cy":153,"r":3,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Arms (one holding blowgun) ---
    P.append({"type":"rect","x":84,"y":112,"w":14,"h":40,"color":UNIFORM,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":138,"y":112,"w":14,"h":40,"color":UNIFORM,"outline":OUT,"outline_w":1,"radius":4})
    # hands
    P.append({"type":"circle","cx":91,"cy":154,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":145,"cy":154,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (short, yordle) ---
    P.append({"type":"rect","x":100,"y":170,"w":16,"h":30,"color":UNIFORM_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":122,"y":170,"w":16,"h":30,"color":UNIFORM_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # fur around ankles (yordle fur)
    P.append({"type":"rect","x":98,"y":194,"w":20,"h":6,"color":FUR,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":120,"y":194,"w":20,"h":6,"color":FUR,"outline":OUT,"outline_w":1,"radius":2})
    # boots
    P.append({"type":"rect","x":98,"y":198,"w":20,"h":12,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":120,"y":198,"w":20,"h":12,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})

    # --- BLOWGUN (THE missing feature -- in hands, long, horizontal) ---
    P.append({"type":"rect","x":60,"y":150,"w":80,"h":8,"color":BLOWGUN,"outline":OUT,"outline_w":2,"radius":2})
    # blowgun mouthpiece (left end)
    P.append({"type":"circle","cx":60,"cy":154,"r":5,"color":BLOWGUN,"outline":OUT,"outline_w":1})
    # blowgun tip (right end, where dart comes out)
    P.append({"type":"circle","cx":140,"cy":154,"r":4,"color":BROWN,"outline":OUT,"outline_w":1})
    # gold blowgun band
    P.append({"type":"rect","x":96,"y":150,"w":8,"h":8,"color":GOLD,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Thresh -- the Chain Warden; SOUL LANTERN + spectral cloak + chains
# ============================================================================
def thresh_prims():
    P = []
    CLOAK = (50, 50, 60)         # tattered ghostly cloak (dark)
    CLOAK_DARK = (30, 30, 40)
    SPECTRAL = (100, 200, 100)   # spectral green
    SPECTRAL_BRIGHT = (160, 255, 160)
    SPECTRAL_DARK = (50, 130, 50)
    LANTERN = (120, 200, 80)     # soul lantern (green glow)
    LANTERN_BRIGHT = (180, 255, 120)
    LANTERN_DARK = (60, 130, 40)
    LANTERN_METAL = (80, 80, 90) # lantern frame (dark metal)
    CHAIN = (120, 120, 130)      # spectral chains
    CHAIN_DARK = (70, 70, 80)
    BONE = (220, 215, 200)       # skeletal features
    BONE_DARK = (150, 145, 130)
    EYE = (140, 255, 140)        # glowing green eyes
    OUT = (20, 25, 20)

    # --- TATTERED GHOSTLY CLOAK (THE missing feature -- BIG, flowing, tattered) ---
    P.append({"type":"polygon","points":[(80,90),(176,90),(200,210),(56,210)],
              "color":CLOAK,"outline":OUT,"outline_w":2})
    # cloak tattered edges (jagged hem -- THE feature)
    P.append({"type":"polygon","points":[(56,210),(64,220),(68,210),(72,222),(76,210),(80,222),(84,210),(88,222),(92,210),(96,222),(100,210),(104,222),(108,210),(112,222),(116,210),(120,222),(124,210),(128,222),(132,210),(136,222),(140,210),(144,222),(148,210),(152,222),(156,210),(160,222),(164,210),(168,222),(172,210),(176,222),(180,210),(184,222),(188,210),(192,222),(196,210),(200,210)],
              "color":CLOAK_DARK,"outline":OUT,"outline_w":1})
    # cloak shading
    P.append({"type":"polygon","points":[(90,94),(166,94),(186,206),(70,206)],
              "color":CLOAK_DARK,"outline":OUT,"outline_w":1})
    # spectral green glow trim on cloak
    P.append({"type":"line","start":[80,90],"end":[176,90],"color":SPECTRAL,"width":2})

    # --- EXPOSED RIBCAGE (THE missing feature -- skeletal, visible through cloak) ---
    P.append({"type":"polygon","points":[(108,110),(148,110),(144,160),(112,160)],
              "color":CLOAK_DARK,"outline":OUT,"outline_w":1})
    # rib bones (THE feature -- white ribs visible)
    for ry in (118, 126, 134, 142, 150):
        P.append({"type":"line","start":[112,ry],"end":[144,ry],"color":BONE,"outline":OUT,"outline_w":1,"width":2})
    # spine (center)
    P.append({"type":"line","start":[128,110],"end":[128,160],"color":BONE,"width":2})
    # spectral glow on ribs
    P.append({"type":"line","start":[128,114],"end":[128,156],"color":SPECTRAL,"width":1})

    # --- Head (skeletal, hooded) ---
    # hood (dark, over skull)
    P.append({"type":"polygon","points":[(104,72),(152,72),(148,96),(108,96)],
              "color":CLOAK_DARK,"outline":OUT,"outline_w":2})
    # skull (bone-colored, skeletal)
    P.append({"type":"circle","cx":128,"cy":80,"r":16,"color":BONE,"outline":OUT,"outline_w":2})
    # glowing green eyes (THE feature -- big, spectral)
    P.append({"type":"circle","cx":121,"cy":80,"r":5,"color":EYE,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":135,"cy":80,"r":5,"color":EYE,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":122,"cy":79,"r":2,"color":(255,255,200)})
    P.append({"type":"circle","cx":136,"cy":79,"r":2,"color":(255,255,200)})
    # eye glow aura
    P.append({"type":"circle","cx":121,"cy":80,"r":8,"color":(120,220,120),"outline":SPECTRAL,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":80,"r":8,"color":(120,220,120),"outline":SPECTRAL,"outline_w":1})
    # skeletal jaw (bone)
    P.append({"type":"polygon","points":[(118,90),(138,90),(134,100),(122,100)],
              "color":BONE,"outline":OUT,"outline_w":1})
    # teeth
    for tx in (122, 128, 134):
        P.append({"type":"line","start":[tx,90],"end":[tx,96],"color":OUT,"width":1})

    # --- SOUL LANTERN (THE feature -- BIG, glowing green, on a chain) ---
    # lantern chain (from hand, going up-right)
    P.append({"type":"line","start":[170,150],"end":[200,100],"color":CHAIN,"width":3})
    # chain links
    for cx, cy in [(178,140),(184,130),(190,120),(196,110)]:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":4,"color":CHAIN,"outline":CHAIN_DARK,"outline_w":1})
    # LANTERN body (BIG, glowing green -- THE feature)
    P.append({"type":"polygon","points":[(196,90),(220,90),(224,130),(192,130)],
              "color":LANTERN_METAL,"outline":OUT,"outline_w":2})
    # lantern glass (glowing green -- THE soul fire)
    P.append({"type":"polygon","points":[(200,96),(216,96),(220,126),(196,126)],
              "color":LANTERN,"outline":LANTERN_DARK,"outline_w":2})
    # lantern bright glow center
    P.append({"type":"circle","cx":208,"cy":112,"r":10,"color":LANTERN_BRIGHT,"outline":LANTERN,"outline_w":1})
    P.append({"type":"circle","cx":208,"cy":112,"r":5,"color":(255,255,200)})
    # lantern glow aura (BIG -- THE signature)
    P.append({"type":"circle","cx":208,"cy":112,"r":20,"color":(140,220,100),"outline":SPECTRAL,"outline_w":1})
    # lantern frame (metal top + bottom)
    P.append({"type":"rect","x":194,"y":86,"w":30,"h":6,"color":LANTERN_METAL,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":194,"y":128,"w":30,"h":6,"color":LANTERN_METAL,"outline":OUT,"outline_w":1})
    # lantern cap (top)
    P.append({"type":"polygon","points":[(200,86),(216,86),(208,76)],"color":LANTERN_METAL,"outline":OUT,"outline_w":1})
    # souls wisps inside lantern
    for sy in (104, 112, 120):
        P.append({"type":"circle","cx":206,"cy":sy,"r":2,"color":(255,255,200),"outline":LANTERN,"outline_w":1})
        P.append({"type":"circle","cx":212,"cy":sy,"r":2,"color":(255,255,200),"outline":LANTERN,"outline_w":1})

    # --- Arms (skeletal, one holding lantern chain) ---
    P.append({"type":"rect","x":90,"y":110,"w":14,"h":40,"color":CLOAK_DARK,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":156,"y":110,"w":14,"h":40,"color":CLOAK_DARK,"outline":OUT,"outline_w":1,"radius":4})
    # skeletal hands (bone)
    P.append({"type":"circle","cx":97,"cy":152,"r":5,"color":BONE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":170,"cy":152,"r":5,"color":BONE,"outline":OUT,"outline_w":1})

    # --- SCYTHE (THE missing feature -- in left hand, big) ---
    P.append({"type":"line","start":[97,152],"end":[60,60],"color":CHAIN_DARK,"width":5})
    # scythe blade (curved, at top)
    P.append({"type":"polygon","points":[(60,60),(40,50),(36,70),(52,72)],
              "color":BONE,"outline":OUT,"outline_w":2})
    # spectral glow on scythe
    P.append({"type":"circle","cx":48,"cy":60,"r":8,"color":SPECTRAL,"outline":SPECTRAL_DARK,"outline_w":1})

    # --- Legs (cloak-covered, floating -- no feet) ---
    P.append({"type":"polygon","points":[(96,180),(120,180),(116,210),(100,210)],"color":CLOAK_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(136,180),(160,180),(156,210),(140,210)],"color":CLOAK_DARK,"outline":OUT,"outline_w":1})
    # spectral wisps at bottom (floating, ghostly)
    for sx in (100, 116, 140, 156):
        P.append({"type":"circle","cx":sx,"cy":216,"r":5,"color":SPECTRAL,"outline":SPECTRAL_DARK,"outline_w":1})
    return P


# ============================================================================
# Trundle -- troll king; BIG TUSKS + True Ice club + blue skin + fur pelt
# ============================================================================
def trundle_prims():
    P = []
    SKIN = (120, 160, 180)       # blue skin (troll)
    SKIN_DARK = (80, 120, 150)
    FUR = (220, 220, 230)       # white fur pelt
    FUR_DARK = (180, 180, 195)
    ICE = (180, 220, 240)       # True Ice club (ice blue)
    ICE_BRIGHT = (220, 240, 250)
    ICE_DARK = (120, 180, 210)
    TUSK = (245, 240, 225)      # tusks (white-bone)
    TUSK_DARK = (200, 195, 180)
    BROWN = (110, 80, 55)       # wooden club handle
    EYE = (40, 30, 25)
    OUT = (25, 30, 40)

    # --- BIG PROTRUDING TUSKS (THE feature -- huge, from lower jaw) ---
    # left tusk (BIG, curving up)
    P.append({"type":"polygon","points":[(100,100),(88,100),(84,82),(96,90)],
              "color":TUSK,"outline":OUT,"outline_w":2})
    # right tusk
    P.append({"type":"polygon","points":[(156,100),(168,100),(172,82),(160,90)],
              "color":TUSK,"outline":OUT,"outline_w":2})
    # tusk shading
    P.append({"type":"line","start":[92,98],"end":[88,84],"color":TUSK_DARK,"width":1})
    P.append({"type":"line","start":[164,98],"end":[168,84],"color":TUSK_DARK,"width":1})

    # --- Head (big, troll, heavy brow) ---
    P.append({"type":"circle","cx":128,"cy":80,"r":24,"color":SKIN,"outline":OUT,"outline_w":2})
    # HEAVY BROW (THE missing feature -- big, protruding bone ridge)
    P.append({"type":"rect","x":104,"y":68,"w":48,"h":10,"color":SKIN_DARK,"outline":OUT,"outline_w":2,"radius":3})
    # brow bumps (protruding)
    for bx in (112, 128, 144):
        P.append({"type":"circle","cx":bx,"cy":70,"r":4,"color":SKIN_DARK,"outline":OUT,"outline_w":1})
    # eyes (under heavy brow)
    P.append({"type":"circle","cx":119,"cy":80,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":137,"cy":80,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    # menacing grin (THE feature -- wide, showing tusks)
    P.append({"type":"polygon","points":[(104,96),(152,96),(148,104),(108,104)],
              "color":OUT,"outline":SKIN_DARK,"outline_w":1})
    # teeth in grin
    for tx in (112, 120, 128, 136, 144):
        P.append({"type":"polygon","points":[(tx,96),(tx+3,96),(tx+1,102)],"color":TUSK,"outline":OUT,"outline_w":1})
    # big flat nose (troll)
    P.append({"type":"ellipse","x":120,"y":86,"w":16,"h":10,"color":SKIN_DARK,"outline":OUT,"outline_w":1})

    # --- RUGGED FUR PELT CLOTHING (THE missing feature -- BIG, obvious) ---
    # fur pelt over shoulders (big, white, shaggy)
    P.append({"type":"polygon","points":[(88,96),(168,96),(176,130),(80,130)],
              "color":FUR,"outline":OUT,"outline_w":2})
    # fur texture (shaggy edges -- THE feature)
    for fx in (88, 100, 112, 124, 136, 148, 160, 172):
        P.append({"type":"polygon","points":[(fx,126),(fx+4,126),(fx+2,136)],"color":FUR,"outline":FUR_DARK,"outline_w":1})
    # fur texture (fluffy circles on top)
    for fx in (96, 112, 128, 144, 160):
        P.append({"type":"circle","cx":fx,"cy":106,"r":8,"color":FUR,"outline":FUR_DARK,"outline_w":1})

    # --- Torso (massive, hulking, blue skin) ---
    P.append({"type":"polygon","points":[(96,130),(160,130),(168,200),(88,200)],
              "color":SKIN,"outline":OUT,"outline_w":2})
    # torso shading
    P.append({"type":"polygon","points":[(104,134),(152,134),(158,198),(98,198)],
              "color":SKIN_DARK,"outline":OUT,"outline_w":1})
    # fur pelt continued (down the back)
    P.append({"type":"polygon","points":[(88,130),(100,130),(96,200),(84,190)],
              "color":FUR,"outline":FUR_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(156,130),(168,130),(172,190),(160,200)],
              "color":FUR,"outline":FUR_DARK,"outline_w":1})

    # --- Arms (massive, muscular) ---
    P.append({"type":"rect","x":72,"y":136,"w":22,"h":56,"color":SKIN,"outline":OUT,"outline_w":2,"radius":5})
    P.append({"type":"rect","x":162,"y":136,"w":22,"h":56,"color":SKIN,"outline":OUT,"outline_w":2,"radius":5})
    # muscle definition
    P.append({"type":"circle","cx":83,"cy":156,"r":10,"color":SKIN_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":173,"cy":156,"r":10,"color":SKIN_DARK,"outline":OUT,"outline_w":1})
    # hands (big, clawed)
    P.append({"type":"circle","cx":83,"cy":196,"r":8,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":173,"cy":196,"r":8,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (massive, hulking) ---
    P.append({"type":"rect","x":98,"y":200,"w":26,"h":36,"color":SKIN_DARK,"outline":OUT,"outline_w":2,"radius":4})
    P.append({"type":"rect","x":132,"y":200,"w":26,"h":36,"color":SKIN_DARK,"outline":OUT,"outline_w":2,"radius":4})
    # big feet
    P.append({"type":"ellipse","x":94,"y":230,"w":32,"h":16,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"ellipse","x":128,"y":230,"w":32,"h":16,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- TRUE ICE CLUB (THE weapon -- BIG, ice-blue, massive) ---
    # club body (big, ice-blue, in right hand)
    P.append({"type":"polygon","points":[(176,196),(220,196),(228,80),(200,60),(180,80)],
              "color":ICE,"outline":OUT,"outline_w":3})
    # ice crystals on club (THE True Ice look -- jagged, crystalline)
    P.append({"type":"polygon","points":[(184,90),(220,90),(216,110),(188,110)],
              "color":ICE_BRIGHT,"outline":ICE_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(186,120),(218,120),(214,140),(190,140)],
              "color":ICE_BRIGHT,"outline":ICE_DARK,"outline_w":1})
    # ice crystal spikes on club top (THE True Ice feature)
    for cx in (194, 204, 214):
        P.append({"type":"polygon","points":[(cx-4,70),(cx+4,70),(cx,56)],"color":ICE_BRIGHT,"outline":ICE_DARK,"outline_w":1})
    # ice glow
    P.append({"type":"circle","cx":204,"cy":100,"r":16,"color":(200,230,245),"outline":ICE,"outline_w":1})
    # club handle (wooden, brown)
    P.append({"type":"rect","x":176,"y":190,"w":20,"h":16,"color":BROWN,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Urgot -- six-legged cyborg; SIX SPIDER-LIKE ROBOTIC LEGS + single glowing eye
# ============================================================================
def urgot_prims():
    P = []
    METAL = (110, 110, 120)      # dark grey metal
    METAL_DARK = (70, 70, 80)
    METAL_LIGHT = (150, 150, 160)
    RUST = (170, 110, 60)        # rust orange accents
    RUST_DARK = (110, 70, 35)
    CHEM_GREEN = (100, 200, 80)  # chemical green
    CHEM_BRIGHT = (160, 255, 120)
    EYE = (255, 100, 60)         # single glowing eye (red-orange)
    EYE_BRIGHT = (255, 200, 150)
    TANK = (90, 90, 100)         # chemical tanks
    OUT = (20, 20, 25)

    # --- SIX SPIDER-LIKE ROBOTIC LEGS (THE feature -- BIG, mechanical, spreading out) ---
    # 3 left legs (big, mechanical, spreading out left)
    leg_left = [
        [(96,140),(60,120),(36,140)],   # leg 1 (high)
        [(96,160),(56,160),(32,180)],   # leg 2 (mid)
        [(96,180),(60,200),(40,220)],   # leg 3 (low)
    ]
    for leg in leg_left:
        for i in range(len(leg)-1):
            P.append({"type":"line","start":leg[i],"end":leg[i+1],"color":METAL,"width":8})
        # leg joints (mechanical bulbs)
        for cx, cy in leg:
            P.append({"type":"circle","cx":cx,"cy":cy,"r":6,"color":METAL,"outline":METAL_DARK,"outline_w":2})
        # sharp leg tips (spider-like)
        tx, ty = leg[-1]
        P.append({"type":"polygon","points":[(tx-4,ty),(tx+4,ty),(tx,ty+10)],"color":METAL_DARK,"outline":OUT,"outline_w":1})
    # 3 right legs (big, mechanical, spreading out right)
    leg_right = [
        [(160,140),(196,120),(220,140)],
        [(160,160),(200,160),(224,180)],
        [(160,180),(196,200),(216,220)],
    ]
    for leg in leg_right:
        for i in range(len(leg)-1):
            P.append({"type":"line","start":leg[i],"end":leg[i+1],"color":METAL,"width":8})
        for cx, cy in leg:
            P.append({"type":"circle","cx":cx,"cy":cy,"r":6,"color":METAL,"outline":METAL_DARK,"outline_w":2})
        tx, ty = leg[-1]
        P.append({"type":"polygon","points":[(tx-4,ty),(tx+4,ty),(tx,ty+10)],"color":METAL_DARK,"outline":OUT,"outline_w":1})

    # --- AUGMENTED MECHANICAL TORSO (industrial armor) ---
    P.append({"type":"polygon","points":[(88,96),(168,96),(176,200),(80,200)],
              "color":METAL,"outline":OUT,"outline_w":3})
    # armor plates (industrial, segmented)
    P.append({"type":"polygon","points":[(96,104),(160,104),(164,180),(92,180)],
              "color":METAL_DARK,"outline":OUT,"outline_w":2})
    # rust orange accents (THE missing feature)
    P.append({"type":"rect","x":92,"y":120,"w":72,"h":8,"color":RUST,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":92,"y":150,"w":72,"h":8,"color":RUST,"outline":OUT,"outline_w":1})
    # metal plate seams
    P.append({"type":"line","start":[128,104],"end":[128,180],"color":METAL_LIGHT,"width":2})
    P.append({"type":"line","start":[96,140],"end":[160,140],"color":METAL_LIGHT,"width":1})
    # rivets (industrial)
    for rx in (104, 116, 128, 140, 152):
        P.append({"type":"circle","cx":rx,"cy":112,"r":3,"color":METAL_LIGHT,"outline":OUT,"outline_w":1})
        P.append({"type":"circle","cx":rx,"cy":172,"r":3,"color":METAL_LIGHT,"outline":OUT,"outline_w":1})

    # --- SINGLE GLOWING EYE (THE missing feature -- big, red-orange, center of head) ---
    # head (mechanical, armored)
    P.append({"type":"polygon","points":[(100,72),(156,72),(160,100),(96,100)],
              "color":METAL_DARK,"outline":OUT,"outline_w":2})
    # SINGLE GLOWING EYE (THE feature -- big, centered, red-orange)
    P.append({"type":"circle","cx":128,"cy":86,"r":10,"color":EYE,"outline":OUT,"outline_w":3})
    P.append({"type":"circle","cx":128,"cy":86,"r":6,"color":EYE_BRIGHT,"outline":EYE,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":86,"r":3,"color":(255,255,255)})
    # eye glow aura
    P.append({"type":"circle","cx":128,"cy":86,"r":16,"color":(220,120,80),"outline":EYE,"outline_w":1})
    # metal eye socket (mechanical housing)
    P.append({"type":"circle","cx":128,"cy":86,"r":13,"color":METAL_DARK,"outline":OUT,"outline_w":1})

    # --- CHEMICAL TANKS ON BACK (THE feature -- big, glowing green) ---
    # left tank
    P.append({"type":"rect","x":84,"y":100,"w":24,"h":50,"color":TANK,"outline":OUT,"outline_w":2,"radius":4})
    # green chemical liquid (glowing)
    P.append({"type":"rect","x":88,"y":112,"w":16,"h":30,"color":CHEM_GREEN,"outline":CHEM_BRIGHT,"outline_w":1})
    # chemical bubbles
    for by in (118, 128, 138):
        P.append({"type":"circle","cx":96,"cy":by,"r":3,"color":CHEM_BRIGHT,"outline":CHEM_GREEN,"outline_w":1})
    # right tank
    P.append({"type":"rect","x":148,"y":100,"w":24,"h":50,"color":TANK,"outline":OUT,"outline_w":2,"radius":4})
    P.append({"type":"rect","x":152,"y":112,"w":16,"h":30,"color":CHEM_GREEN,"outline":CHEM_BRIGHT,"outline_w":1})
    for by in (118, 128, 138):
        P.append({"type":"circle","cx":160,"cy":by,"r":3,"color":CHEM_BRIGHT,"outline":CHEM_GREEN,"outline_w":1})
    # tank pipes (connecting to body)
    P.append({"type":"line","start":[96,150],"end":[96,170],"color":METAL_DARK,"width":4})
    P.append({"type":"line","start":[160,150],"end":[160,170],"color":METAL_DARK,"width":4})

    # --- INTEGRATED KNEE-MOUNTED CANNONS (THE missing feature) ---
    # left cannon (on left side, at knee level)
    P.append({"type":"rect","x":80,"y":180,"w":20,"h":12,"color":METAL_DARK,"outline":OUT,"outline_w":2})
    # cannon muzzle
    P.append({"type":"circle","cx":80,"cy":186,"r":5,"color":OUT,"outline":METAL_DARK,"outline_w":1})
    # right cannon
    P.append({"type":"rect","x":156,"y":180,"w":20,"h":12,"color":METAL_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":176,"cy":186,"r":5,"color":OUT,"outline":METAL_DARK,"outline_w":1})
    return P


# ============================================================================
# Varus -- the Arrow of Retribution; COMPOSITE BOW + glowing purple corruption
# ============================================================================
def varus_prims():
    P = []
    SKIN = (225, 200, 175)
    CORRUPT = (140, 60, 180)     # glowing purple corruption (left side)
    CORRUPT_BRIGHT = (200, 120, 240)
    CORRUPT_DARK = (90, 40, 120)
    ARMOR = (60, 45, 70)         # darkin armor (dark purple-black)
    ARMOR_DARK = (35, 25, 45)
    ARMOR_GOLD = (200, 165, 55)
    BOW = (180, 160, 120)        # composite bow (wood + horn)
    BOW_DARK = (130, 100, 60)
    BOW_STRING = (220, 220, 220)
    HAIR = (220, 200, 180)       # white-silver hair (Varus)
    HAIR_DARK = (170, 150, 130)
    EYE = (200, 100, 240)        # single glowing purple eye (darkin)
    OUT = (25, 20, 30)

    # --- COMPOSITE BOW (THE feature -- BIG, held in front, the icon) ---
    # bow limbs (curved, composite -- BIG, vertical)
    P.append({"type":"line","start":[176,40],"end":[176,200],"color":BOW,"width":5})
    # bow curve (recurve tips -- THE composite bow look)
    P.append({"type":"polygon","points":[(170,40),(182,40),(186,30),(166,30)],"color":BOW,"outline":BOW_DARK,"outline_w":2})
    P.append({"type":"polygon","points":[(170,200),(182,200),(186,210),(166,210)],"color":BOW,"outline":BOW_DARK,"outline_w":2})
    # bow string
    P.append({"type":"line","start":[176,34],"end":[176,206],"color":BOW_STRING,"width":1})
    # bow grip (center, where hand holds)
    P.append({"type":"rect","x":172,"y":112,"w":8,"h":20,"color":BOW_DARK,"outline":OUT,"outline_w":1})
    # bow gold accents
    P.append({"type":"rect","x":172,"y":70,"w":8,"h":6,"color":ARMOR_GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":172,"y":160,"w":8,"h":6,"color":ARMOR_GOLD,"outline":OUT,"outline_w":1})
    # arrow nocked (drawn, pointing left -- THE archer pose)
    P.append({"type":"line","start":[176,120],"end":[120,120],"color":BOW_DARK,"width":2})
    # arrow head
    P.append({"type":"polygon","points":[(120,116),(120,124),(110,120)],"color":ARMOR_GOLD,"outline":OUT,"outline_w":1})
    # arrow fletching
    P.append({"type":"polygon","points":[(168,116),(176,116),(172,110)],"color":(220,200,180),"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(168,124),(176,124),(172,130)],"color":(220,200,180),"outline":OUT,"outline_w":1})

    # --- Hair (white-silver, flowing) ---
    P.append({"type":"circle","cx":118,"cy":66,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    # flowing hair back
    P.append({"type":"polygon","points":[(100,60),(136,60),(148,80),(92,80)],
              "color":HAIR,"outline":HAIR_DARK,"outline_w":1})
    # bangs
    P.append({"type":"polygon","points":[(100,58),(136,58),(132,72),(104,72)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (asymmetrical -- corruption on left side) ---
    P.append({"type":"circle","cx":118,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # SINGLE GLOWING EYE (THE missing feature -- purple, darkin)
    P.append({"type":"circle","cx":111,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":112,"cy":75,"r":2,"color":(255,200,255)})
    # right eye (normal)
    P.append({"type":"line","start":[125,76],"end":[131,76],"color":(60,40,60),"width":2})
    # sharp angular brow
    P.append({"type":"polygon","points":[(104,68),(116,71),(116,73),(104,70)],"color":HAIR_DARK,"outline":OUT,"outline_w":1})
    # determined mouth
    P.append({"type":"line","start":[112,86],"end":[124,86],"color":(120,60,80),"width":1})

    # --- GLOWING PURPLE CORRUPTION ON LEFT SIDE (THE feature -- BIG, obvious) ---
    # corruption spreading from left arm/shoulder (purple, glowing, organic)
    P.append({"type":"polygon","points":[(88,90),(108,90),(104,170),(84,160)],
              "color":CORRUPT,"outline":CORRUPT_DARK,"outline_w":2})
    # corruption tendrils (organic growths -- THE feature)
    for cy in (100, 115, 130, 145):
        P.append({"type":"line","start":[88,cy],"end":[76,cy-8],"color":CORRUPT_BRIGHT,"width":3})
    # corruption glow
    P.append({"type":"circle","cx":96,"cy":120,"r":12,"color":CORRUPT_BRIGHT,"outline":CORRUPT,"outline_w":1})
    P.append({"type":"circle","cx":96,"cy":120,"r":6,"color":(255,200,255)})
    # corruption on face (left cheek -- asymmetrical)
    P.append({"type":"polygon","points":[(104,80),(112,80),(108,92),(102,88)],
              "color":CORRUPT,"outline":CORRUPT_DARK,"outline_w":1})

    # --- DARKIN ARMOR PLATING (THE missing feature -- on right side) ---
    P.append({"type":"polygon","points":[(100,94),(136,94),(140,170),(96,170)],
              "color":ARMOR,"outline":OUT,"outline_w":2})
    # armor plates (darkin, segmented, gold-trimmed)
    P.append({"type":"polygon","points":[(106,100),(132,100),(136,150),(102,150)],
              "color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    # gold armor trim
    P.append({"type":"line","start":[100,94],"end":[136,94],"color":ARMOR_GOLD,"width":2})
    # armor plate segments
    for py in (110, 125, 140):
        P.append({"type":"line","start":[104,py],"end":[134,py],"color":ARMOR_GOLD,"width":1})
    # gold center crest
    P.append({"type":"line","start":[118,100],"end":[118,150],"color":ARMOR_GOLD,"width":2})

    # --- Arms (left corrupted, right normal holding bow) ---
    # left arm (corrupted -- purple, organic)
    P.append({"type":"rect","x":76,"y":104,"w":16,"h":50,"color":CORRUPT,"outline":CORRUPT_DARK,"outline_w":1,"radius":4})
    # corruption tendrils on arm
    P.append({"type":"line","start":[80,114],"end":[80,148],"color":CORRUPT_BRIGHT,"width":2})
    # right arm (armored, holding bow)
    P.append({"type":"rect","x":150,"y":108,"w":14,"h":44,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":4})
    # hands
    P.append({"type":"circle","cx":84,"cy":156,"r":5,"color":CORRUPT,"outline":CORRUPT_DARK,"outline_w":1})
    P.append({"type":"circle","cx":157,"cy":154,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (armored) ---
    P.append({"type":"rect","x":100,"y":170,"w":18,"h":40,"color":ARMOR_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":124,"y":170,"w":18,"h":40,"color":ARMOR_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # gold shin trim
    P.append({"type":"rect","x":100,"y":186,"w":18,"h":4,"color":ARMOR_GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":124,"y":186,"w":18,"h":4,"color":ARMOR_GOLD,"outline":OUT,"outline_w":1})
    # boots
    P.append({"type":"rect","x":98,"y":206,"w":22,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":122,"y":206,"w":22,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    return P


# ============================================================================
# Run all 6
# ============================================================================
CHAMPS = [
    ("Taric", taric_prims, "crystalline armor + glowing gemstones"),
    ("Teemo", teemo_prims, "green scout hat + big goggles + blowgun"),
    ("Thresh", thresh_prims, "soul lantern + spectral cloak + chains"),
    ("Trundle", trundle_prims, "big tusks + True Ice club + blue skin"),
    ("Urgot", urgot_prims, "six spider-like robotic legs + single eye"),
    ("Varus", varus_prims, "composite bow + glowing purple corruption"),
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
