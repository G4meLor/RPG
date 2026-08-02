"""Batch 14: Kayn, Kindred, LeeSin, Lucian, Malzahar, MonkeyKing.

- Kayn       -> SENTIENT SCYTHE Rhaast (big darkin scythe, glowing red eye)
- Kindred    -> TWO entities: white lamb + big spectral wolf (dual)
- LeeSin     -> BLINDFOLD + monk robes + martial arts fist stance
- Lucian     -> DUAL PISTOLS (two big glowing light pistols) + white coat
- Malzahar   -> DEEP HOOD + VOID ENERGY (purple, from hands) + floating voidlings
- MonkeyKing -> GOLDEN ARMOR + LONG TAIL (prehensile) + monkey face + staff
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve


# ============================================================================
# Kayn -- the shadow Reaper; SENTIENT SCYTHE Rhaast (big, glowing red eye)
# ============================================================================
def kayn_prims():
    P = []
    SKIN = (220, 200, 180)
    HAIR = (60, 45, 55)
    ATTIRE = (50, 40, 60)       # dark purple Ionian attire
    ATTIRE_DARK = (35, 30, 45)
    SHADOW = (60, 40, 70)       # dark shadow energy
    SHADOW_DARK = (35, 25, 45)
    RED = (180, 40, 40)         # Rhaast red
    RED_DARK = (120, 25, 25)
    RED_GLOW = (220, 80, 80)
    SCYTHE = (130, 35, 35)      # the Darkin scythe (red-purple)
    SCYTHE_DARK = (80, 20, 25)
    SCYTHE_BLADE = (180, 50, 50)
    GOLD = (200, 165, 55)
    EYE = (220, 60, 60)         # glowing red eyes
    OUT = (20, 15, 20)

    # --- Dark shadow energy aura (THE missing feature -- BIG, obvious, around body) ---
    P.append({"type":"circle","cx":50,"cy":110,"r":24,"color":SHADOW,"outline":SHADOW_DARK,"outline_w":2})
    P.append({"type":"circle","cx":206,"cy":110,"r":24,"color":SHADOW,"outline":SHADOW_DARK,"outline_w":2})
    P.append({"type":"circle","cx":40,"cy":150,"r":20,"color":SHADOW_DARK,"outline":SHADOW,"outline_w":1})
    P.append({"type":"circle","cx":216,"cy":150,"r":20,"color":SHADOW_DARK,"outline":SHADOW,"outline_w":1})
    # shadow wisps trailing from body (THE dark shadow energy)
    for sy in (90, 80, 70):
        P.append({"type":"circle","cx":50,"cy":sy,"r":6,"color":SHADOW,"outline":SHADOW_DARK,"outline_w":1})
    for sy in (90, 80, 70):
        P.append({"type":"circle","cx":206,"cy":sy,"r":6,"color":SHADOW,"outline":SHADOW_DARK,"outline_w":1})

    # --- Hair (dark) ---
    P.append({"type":"circle","cx":118,"cy":66,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(100,58),(136,58),(132,74),(104,74)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # angular hair spikes (sharp features)
    P.append({"type":"polygon","points":[(100,58),(96,48),(106,56)],"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(136,58),(140,48),(130,56)],"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (sharp, angular) ---
    P.append({"type":"circle","cx":118,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # glowing red eyes (THE feature)
    P.append({"type":"circle","cx":111,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":125,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":112,"cy":75,"r":2,"color":(255,200,200)})
    P.append({"type":"circle","cx":126,"cy":75,"r":2,"color":(255,200,200)})
    # sharp angular brows
    P.append({"type":"polygon","points":[(104,68),(116,71),(116,73),(104,70)],"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(120,71),(132,68),(132,70),(120,73)],"color":HAIR,"outline":OUT,"outline_w":1})
    # smirk
    P.append({"type":"line","start":[112,86],"end":[124,84],"color":(140,40,40),"width":1})

    # --- Flowing Ionian attire (dark purple) ---
    P.append({"type":"polygon","points":[(98,94),(138,94),(146,170),(90,170)],
              "color":ATTIRE,"outline":OUT,"outline_w":1})
    # attire shading
    P.append({"type":"polygon","points":[(104,98),(132,98),(138,168),(98,168)],
              "color":ATTIRE_DARK,"outline":OUT,"outline_w":1})
    # red trim (Rhaast influence)
    P.append({"type":"line","start":[98,94],"end":[138,94],"color":RED,"width":2})
    P.append({"type":"line","start":[90,170],"end":[146,170],"color":RED,"width":2})
    # gold center trim
    P.append({"type":"line","start":[118,98],"end":[118,170],"color":GOLD,"width":1})
    # shadow energy on chest
    P.append({"type":"circle","cx":118,"cy":120,"r":6,"color":SHADOW,"outline":SHADOW_DARK,"outline_w":1})

    # --- Arms ---
    P.append({"type":"rect","x":80,"y":104,"w":14,"h":50,"color":ATTIRE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":142,"y":104,"w":14,"h":50,"color":ATTIRE,"outline":OUT,"outline_w":1,"radius":4})
    # hands
    P.append({"type":"circle","cx":87,"cy":156,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":149,"cy":156,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs ---
    P.append({"type":"rect","x":96,"y":170,"w":18,"h":40,"color":ATTIRE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":122,"y":170,"w":18,"h":40,"color":ATTIRE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":94,"y":206,"w":22,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":120,"y":206,"w":22,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})

    # --- SENTIENT SCYTHE Rhaast (THE feature -- BIG, in front, with glowing eye) ---
    # scythe shaft (long, dark red, diagonal)
    P.append({"type":"line","start":[149,156],"end":[200,40],"color":SCYTHE_DARK,"width":7})
    # scythe blade (BIG curved blade at top -- THE darkin scythe)
    P.append({"type":"polygon","points":[(200,40),(220,30),(236,50),(228,70),(210,60)],
              "color":SCYTHE_BLADE,"outline":OUT,"outline_w":3})
    # blade inner edge (sharper, brighter red)
    P.append({"type":"polygon","points":[(206,46),(224,38),(230,52),(216,58)],
              "color":RED,"outline":RED_DARK,"outline_w":1})
    # Rhaast EYE (THE feature -- the scythe is sentient, has a glowing red eye)
    P.append({"type":"circle","cx":216,"cy":52,"r":6,"color":EYE,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":216,"cy":52,"r":3,"color":(255,200,200)})
    # scythe glow aura (darkin energy, red)
    P.append({"type":"circle","cx":216,"cy":52,"r":12,"color":(180,60,60),"outline":RED,"outline_w":1})
    # gold band on shaft
    P.append({"type":"rect","x":180,"y":80,"w":8,"h":8,"color":GOLD,"outline":OUT,"outline_w":1})
    # shadow energy wisps from scythe
    for sy in (30, 22, 14):
        P.append({"type":"circle","cx":210,"cy":sy,"r":4,"color":SHADOW,"outline":SHADOW_DARK,"outline_w":1})
    return P


# ============================================================================
# Kindred -- dual entity: white lamb + BIG spectral wolf
# ============================================================================
def kindred_prims():
    P = []
    LAMB_WOOL = (235, 235, 240)
    LAMB_DARK = (200, 200, 210)
    WOLF = (80, 65, 100)        # spectral wolf (purple-dark)
    WOLF_DARK = (50, 40, 75)
    WOLF_LIGHT = (110, 90, 130)
    MASK = (245, 245, 250)
    MASK_DARK = (180, 180, 195)
    BOW = (140, 100, 60)
    BOW_STRING = (220, 220, 220)
    GLOW = (150, 200, 255)      # ethereal blue glow
    GLOW_BRIGHT = (200, 230, 255)
    EYE = (140, 200, 255)       # spectral blue eyes
    OUT = (40, 30, 35)

    # --- Ethereal blue glow aura (behind -- THE missing feature, BIG but targeted) ---
    P.append({"type":"circle","cx":96,"cy":130,"r":40,"color":(180,210,240),"outline":GLOW,"outline_w":2})
    P.append({"type":"circle","cx":180,"cy":100,"r":35,"color":(180,210,240),"outline":GLOW,"outline_w":2})
    # glow wisps (ethereal blue, trailing)
    for sx, sy in [(60,100),(60,160),(220,60),(230,140)]:
        P.append({"type":"circle","cx":sx,"cy":sy,"r":6,"color":GLOW_BRIGHT,"outline":GLOW,"outline_w":1})

    # --- BIG SPECTRAL WOLF (THE feature -- large, looming behind/beside lamb) ---
    # wolf body (looming large, right side)
    P.append({"type":"ellipse","x":140,"y":60,"w":90,"h":100,"color":WOLF,"outline":OUT,"outline_w":2})
    # wolf head (snarling, up high, BIG)
    P.append({"type":"circle","cx":210,"cy":78,"r":26,"color":WOLF,"outline":OUT,"outline_w":2})
    # wolf snout (elongated, snarling)
    P.append({"type":"polygon","points":[(218,70),(246,76),(242,92),(218,86)],
              "color":WOLF_DARK,"outline":OUT,"outline_w":1})
    # wolf ears (pointed, spectral)
    P.append({"type":"polygon","points":[(192,58),(198,38),(206,58)],"color":WOLF,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(210,58),(218,38),(226,60)],"color":WOLF,"outline":OUT,"outline_w":1})
    # wolf glowing spectral eyes (THE feature -- blue, glowing)
    P.append({"type":"circle","cx":202,"cy":76,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":218,"cy":76,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":203,"cy":75,"r":2,"color":GLOW_BRIGHT})
    P.append({"type":"circle","cx":219,"cy":75,"r":2,"color":GLOW_BRIGHT})
    # wolf teeth (snarling)
    P.append({"type":"polygon","points":[(226,86),(230,86),(228,94)],"color":MASK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(232,86),(236,86),(234,94)],"color":MASK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(238,84),(242,84),(240,92)],"color":MASK,"outline":OUT,"outline_w":1})
    # ethereal glow around wolf (spectral)
    P.append({"type":"ellipse","x":138,"y":56,"w":94,"h":108,"color":WOLF_DARK,"outline":GLOW,"outline_w":1})
    # wolf legs (spectral, 2 visible)
    for lx in (160, 190):
        P.append({"type":"rect","x":lx,"y":140,"w":16,"h":24,"color":WOLF_DARK,"outline":OUT,"outline_w":1,"radius":3})

    # --- Lamb (white woolly, front -- THE entity) ---
    # lamb body (woolly, white)
    P.append({"type":"ellipse","x":60,"y":110,"w":80,"h":70,"color":LAMB_WOOL,"outline":OUT,"outline_w":2})
    # wool texture (fluffy circles)
    for cx, cy in [(76,118),(92,114),(108,116),(124,118),(88,128),(104,130),(96,142),(112,144)]:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":8,"color":LAMB_WOOL,"outline":LAMB_DARK,"outline_w":1})
    # lamb head
    P.append({"type":"circle","cx":72,"cy":86,"r":18,"color":LAMB_WOOL,"outline":OUT,"outline_w":1})
    # lamb ears (floppy)
    P.append({"type":"polygon","points":[(58,78),(48,82),(56,94)],"color":LAMB_WOOL,"outline":OUT,"outline_w":1})
    # lamb mask (white, THE feature -- Lamb wears a mask)
    P.append({"type":"circle","cx":72,"cy":86,"r":14,"color":MASK,"outline":MASK_DARK,"outline_w":1})
    # mask eye slits
    P.append({"type":"line","start":[66,86],"end":[72,86],"color":OUT,"width":2})
    P.append({"type":"line","start":[74,86],"end":[80,86],"color":OUT,"width":2})
    # lamb legs
    for lx in (72, 100, 120):
        P.append({"type":"rect","x":lx,"y":160,"w":12,"h":24,"color":LAMB_DARK,"outline":OUT,"outline_w":1,"radius":3})

    # --- Bow (Lamb's weapon, THE missing feature) ---
    # bow arc (curved, wooden)
    P.append({"type":"line","start":[88,100],"end":[88,160],"color":BOW,"width":4})
    # bow string
    P.append({"type":"line","start":[88,100],"end":[88,160],"color":BOW_STRING,"width":1})
    # bow tips
    P.append({"type":"circle","cx":88,"cy":100,"r":3,"color":BOW,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":88,"cy":160,"r":3,"color":BOW,"outline":OUT,"outline_w":1})
    # arrow (drawn, pointing at wolf)
    P.append({"type":"line","start":[92,130],"end":[120,130],"color":BOW,"width":2})
    P.append({"type":"polygon","points":[(118,127),(124,130),(118,133)],"color":OUT,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# LeeSin -- blind monk; BLINDFOLD + monk robes + martial arts stance
# ============================================================================
def leesin_prims():
    P = []
    SKIN = (220, 185, 150)
    SKIN_DARK = (175, 140, 110)
    ROBE = (170, 50, 50)        # red monk robes
    ROBE_DARK = (120, 35, 35)
    ROBE_TRIM = (215, 175, 60)  # gold trim
    WRAP = (235, 225, 210)      # hand wraps (off-white)
    WRAP_DARK = (190, 180, 165)
    BLINDFOLD = (60, 45, 45)    # blindfold (dark)
    GOLD = (215, 175, 60)
    EYE = (40, 30, 30)
    OUT = (35, 25, 25)

    # --- Hair (short, dark) ---
    P.append({"type":"circle","cx":128,"cy":66,"r":18,"color":(50,40,40),"outline":OUT,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # BLINDFOLD (THE feature -- BIG, across eyes, obvious)
    P.append({"type":"rect","x":108,"y":70,"w":40,"h":10,"color":BLINDFOLD,"outline":OUT,"outline_w":2})
    # blindfold knot (on the side)
    P.append({"type":"polygon","points":[(106,72),(100,68),(102,78)],"color":BLINDFOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(150,72),(156,68),(154,78)],"color":BLINDFOLD,"outline":OUT,"outline_w":1})
    # mouth (determined)
    P.append({"type":"line","start":[122,88],"end":[134,88],"color":(120,40,40),"width":1})

    # --- Monk robes (red, flowing -- THE feature) ---
    P.append({"type":"polygon","points":[(98,94),(158,94),(168,180),(88,180)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # robe shading
    P.append({"type":"polygon","points":[(106,98),(150,98),(158,178),(98,178)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # gold trim on robe
    P.append({"type":"line","start":[98,94],"end":[158,94],"color":ROBE_TRIM,"width":2})
    P.append({"type":"line","start":[88,180],"end":[168,180],"color":ROBE_TRIM,"width":2})
    # gold sash (martial arts belt)
    P.append({"type":"rect","x":92,"y":140,"w":72,"h":8,"color":ROBE_TRIM,"outline":OUT,"outline_w":1})
    # robe center fold
    P.append({"type":"line","start":[128,98],"end":[128,180],"color":ROBE_DARK,"width":1})
    # gold medallion on chest
    P.append({"type":"circle","cx":128,"cy":116,"r":5,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Arms (martial arts stance -- one fist raised, one forward) ---
    # left arm (raised fist, martial arts guard)
    P.append({"type":"rect","x":84,"y":100,"w":14,"h":36,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    # HAND WRAPS (THE missing feature -- on both fists, obvious)
    P.append({"type":"circle","cx":91,"cy":138,"r":7,"color":WRAP,"outline":OUT,"outline_w":2})
    # wrap lines (the bandages)
    P.append({"type":"line","start":[86,134],"end":[96,134],"color":WRAP_DARK,"width":1})
    P.append({"type":"line","start":[86,138],"end":[96,138],"color":WRAP_DARK,"width":1})
    P.append({"type":"line","start":[86,142],"end":[96,142],"color":WRAP_DARK,"width":1})
    # right arm (extended forward, punch stance)
    P.append({"type":"rect","x":158,"y":108,"w":14,"h":36,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    # right hand wraps
    P.append({"type":"circle","cx":165,"cy":146,"r":7,"color":WRAP,"outline":OUT,"outline_w":2})
    P.append({"type":"line","start":[160,142],"end":[170,142],"color":WRAP_DARK,"width":1})
    P.append({"type":"line","start":[160,146],"end":[170,146],"color":WRAP_DARK,"width":1})
    P.append({"type":"line","start":[160,150],"end":[170,150],"color":WRAP_DARK,"width":1})

    # --- Legs (martial arts stance, wide) ---
    P.append({"type":"rect","x":96,"y":180,"w":20,"h":38,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":138,"y":180,"w":20,"h":38,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    # gold shin trim
    P.append({"type":"rect","x":96,"y":196,"w":20,"h":4,"color":ROBE_TRIM,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":138,"y":196,"w":20,"h":4,"color":ROBE_TRIM,"outline":OUT,"outline_w":1})
    # bare feet (martial arts)
    P.append({"type":"ellipse","x":94,"y":210,"w":24,"h":14,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"ellipse","x":136,"y":210,"w":24,"h":14,"color":SKIN,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Lucian -- the Purifier; DUAL PISTOLS (two big glowing light pistols) + white coat
# ============================================================================
def lucian_prims():
    P = []
    SKIN = (225, 195, 165)
    HAIR = (245, 240, 235)      # white hair
    HAIR_DARK = (200, 195, 190)
    COAT = (235, 235, 240)      # white leather coat
    COAT_DARK = (190, 190, 200)
    COAT_TRIM = (200, 165, 55)  # gold trim
    LIGHT = (255, 240, 180)     # glowing light effects (golden)
    LIGHT_BRIGHT = (255, 255, 220)
    LIGHT_GLOW = (255, 220, 120)
    PISTOL = (60, 55, 65)       # pistol body (dark)
    PISTOL_GOLD = (200, 165, 55)
    PISTOL_LIGHT = (255, 240, 180)  # light emanating from pistols
    EYE = (50, 40, 35)
    OUT = (25, 20, 25)

    # --- Hair (white, short) ---
    P.append({"type":"circle","cx":128,"cy":66,"r":18,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(110,58),(146,58),(142,72),(114,72)],
              "color":HAIR,"outline":HAIR_DARK,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # determined eyes
    P.append({"type":"line","start":[119,74],"end":[125,74],"color":EYE,"width":2})
    P.append({"type":"line","start":[131,74],"end":[137,74],"color":EYE,"width":2})
    # determined brows
    P.append({"type":"polygon","points":[(116,68),(126,71),(126,73),(116,70)],"color":HAIR_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(130,71),(140,68),(140,70),(130,73)],"color":HAIR_DARK,"outline":OUT,"outline_w":1})
    # determined mouth
    P.append({"type":"line","start":[122,86],"end":[134,86],"color":(120,60,60),"width":1})

    # --- White leather coat (THE missing feature) ---
    P.append({"type":"polygon","points":[(100,94),(156,94),(164,180),(92,180)],
              "color":COAT,"outline":OUT,"outline_w":1})
    # coat shading
    P.append({"type":"polygon","points":[(108,98),(148,98),(156,178),(100,178)],
              "color":COAT_DARK,"outline":OUT,"outline_w":1})
    # gold coat trim
    P.append({"type":"line","start":[100,94],"end":[156,94],"color":COAT_TRIM,"width":2})
    P.append({"type":"line","start":[92,180],"end":[164,180],"color":COAT_TRIM,"width":2})
    # coat center line
    P.append({"type":"line","start":[128,94],"end":[128,180],"color":COAT_TRIM,"width":2})
    # gold coat buttons
    for by in (108, 124, 140, 156):
        P.append({"type":"circle","cx":128,"cy":by,"r":3,"color":COAT_TRIM,"outline":OUT,"outline_w":1})
    # coat collar (high)
    P.append({"type":"polygon","points":[(102,94),(154,94),(148,106),(108,106)],
              "color":COAT_DARK,"outline":OUT,"outline_w":1})

    # --- Arms (extended forward, dual wielding) ---
    # left arm extended forward-left
    P.append({"type":"polygon","points":[(98,104),(82,116),(76,138),(86,140),(100,120)],
              "color":COAT,"outline":OUT,"outline_w":1})
    # right arm extended forward-right
    P.append({"type":"polygon","points":[(158,104),(174,116),(180,138),(170,140),(156,120)],
              "color":COAT,"outline":OUT,"outline_w":1})
    # hands
    P.append({"type":"circle","cx":80,"cy":140,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":176,"cy":140,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs ---
    P.append({"type":"rect","x":104,"y":180,"w":18,"h":38,"color":COAT_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":134,"y":180,"w":18,"h":38,"color":COAT_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":102,"y":212,"w":22,"h":10,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":132,"y":212,"w":22,"h":10,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})

    # --- DUAL PISTOLS (THE feature -- TWO big glowing light pistols, drawn IN FRONT) ---
    # LEFT pistol (pointing left, light glowing from muzzle)
    P.append({"type":"rect","x":50,"y":134,"w":30,"h":12,"color":PISTOL,"outline":OUT,"outline_w":2})
    # left pistol gold accents
    P.append({"type":"rect","x":60,"y":134,"w":6,"h":12,"color":PISTOL_GOLD,"outline":OUT,"outline_w":1})
    # left pistol muzzle glow (THE light effect)
    P.append({"type":"circle","cx":48,"cy":140,"r":8,"color":LIGHT_GLOW,"outline":LIGHT,"outline_w":2})
    P.append({"type":"circle","cx":48,"cy":140,"r":5,"color":LIGHT_BRIGHT,"outline":LIGHT,"outline_w":1})
    P.append({"type":"circle","cx":48,"cy":140,"r":2,"color":(255,255,255)})
    # left pistol grip
    P.append({"type":"polygon","points":[(72,146),(82,146),(78,162),(68,158)],"color":PISTOL,"outline":OUT,"outline_w":1})

    # RIGHT pistol (pointing right, light glowing from muzzle)
    P.append({"type":"rect","x":176,"y":134,"w":30,"h":12,"color":PISTOL,"outline":OUT,"outline_w":2})
    # right pistol gold accents
    P.append({"type":"rect","x":190,"y":134,"w":6,"h":12,"color":PISTOL_GOLD,"outline":OUT,"outline_w":1})
    # right pistol muzzle glow (THE light effect)
    P.append({"type":"circle","cx":208,"cy":140,"r":8,"color":LIGHT_GLOW,"outline":LIGHT,"outline_w":2})
    P.append({"type":"circle","cx":208,"cy":140,"r":5,"color":LIGHT_BRIGHT,"outline":LIGHT,"outline_w":1})
    P.append({"type":"circle","cx":208,"cy":140,"r":2,"color":(255,255,255)})
    # right pistol grip
    P.append({"type":"polygon","points":[(174,146),(184,146),(188,158),(178,162)],"color":PISTOL,"outline":OUT,"outline_w":1})

    # --- Glowing light effects (light particles around pistols -- THE magic) ---
    for sx, sy in [(36,130),(220,130),(40,152),(216,152),(44,120),(212,120)]:
        P.append({"type":"circle","cx":sx,"cy":sy,"r":3,"color":LIGHT,"outline":LIGHT_GLOW,"outline_w":1})
    return P


# ============================================================================
# Malzahar -- the Prophet; DEEP HOOD + VOID ENERGY from hands + floating voidlings
# ============================================================================
def malzahar_prims():
    P = []
    SKIN = (215, 185, 160)
    ROBE = (80, 55, 100)        # purple robes
    ROBE_DARK = (55, 35, 70)
    ROBE_DARKER = (35, 25, 50)
    HOOD = (60, 40, 80)         # deep hood (dark purple)
    HOOD_DARK = (35, 25, 50)
    VOID = (160, 80, 200)       # purple void energy
    VOID_DARK = (100, 40, 140)
    VOID_BRIGHT = (200, 140, 240)
    VOIDLING = (90, 60, 110)    # voidlings (small purple creatures)
    VOIDLING_DARK = (55, 35, 70)
    GOLD = (200, 165, 55)
    EYE = (180, 80, 220)        # glowing purple eyes
    OUT = (20, 15, 25)

    # --- DEEP HOOD (THE feature -- BIG, conceals the face, obvious hood) ---
    # hood outer (big, dark purple, drapes over head + shoulders)
    P.append({"type":"polygon","points":[(92,60),(164,60),(176,110),(80,110)],
              "color":HOOD,"outline":OUT,"outline_w":2})
    # hood inner (darker, the shadow inside the hood)
    P.append({"type":"polygon","points":[(100,68),(156,68),(164,104),(92,104)],
              "color":HOOD_DARK,"outline":OUT,"outline_w":1})
    # hood opening (face shadow -- THE feature, face is concealed)
    P.append({"type":"ellipse","x":108,"y":72,"w":40,"h":32,"color":HOOD_DARK,"outline":OUT,"outline_w":1})
    # glowing purple eyes (inside the hood shadow -- THE feature)
    P.append({"type":"circle","cx":120,"cy":84,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":136,"cy":84,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":121,"cy":83,"r":2,"color":(255,200,255)})
    P.append({"type":"circle","cx":137,"cy":83,"r":2,"color":(255,200,255)})
    # hood drape (sides, flowing down)
    P.append({"type":"polygon","points":[(92,80),(80,100),(84,140),(96,120)],"color":HOOD,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(164,80),(176,100),(172,140),(160,120)],"color":HOOD,"outline":OUT,"outline_w":1})

    # --- VOID ENERGY from hands (THE feature -- purple, BIG, from both hands) ---
    # left hand void energy (big purple glow)
    P.append({"type":"circle","cx":72,"cy":148,"r":16,"color":VOID,"outline":VOID_DARK,"outline_w":2})
    P.append({"type":"circle","cx":72,"cy":148,"r":10,"color":VOID_BRIGHT,"outline":VOID,"outline_w":1})
    P.append({"type":"circle","cx":72,"cy":148,"r":5,"color":(255,220,255)})
    # void energy wisps from left hand
    for sy in (130, 120, 110):
        P.append({"type":"circle","cx":72,"cy":sy,"r":5,"color":VOID,"outline":VOID_DARK,"outline_w":1})
    # right hand void energy
    P.append({"type":"circle","cx":184,"cy":148,"r":16,"color":VOID,"outline":VOID_DARK,"outline_w":2})
    P.append({"type":"circle","cx":184,"cy":148,"r":10,"color":VOID_BRIGHT,"outline":VOID,"outline_w":1})
    P.append({"type":"circle","cx":184,"cy":148,"r":5,"color":(255,220,255)})
    # void energy wisps from right hand
    for sy in (130, 120, 110):
        P.append({"type":"circle","cx":184,"cy":sy,"r":5,"color":VOID,"outline":VOID_DARK,"outline_w":1})

    # --- Ornate Shuriman-style robes (purple, with gold) ---
    P.append({"type":"polygon","points":[(88,108),(168,108),(176,190),(80,190)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # robe shading
    P.append({"type":"polygon","points":[(96,112),(160,112),(166,188),(90,188)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # gold trim (Shuriman ornate -- THE missing feature)
    P.append({"type":"line","start":[88,108],"end":[168,108],"color":GOLD,"width":2})
    P.append({"type":"line","start":[80,190],"end":[176,190],"color":GOLD,"width":2})
    # gold center trim (Shuriman ornate)
    P.append({"type":"line","start":[128,112],"end":[128,190],"color":GOLD,"width":2})
    # gold ornate symbols on robe
    for sy in (124, 144, 164):
        P.append({"type":"circle","cx":128,"cy":sy,"r":4,"color":GOLD,"outline":OUT,"outline_w":1})
    # gold side trim
    P.append({"type":"line","start":[96,112],"end":[90,188],"color":GOLD,"width":1})
    P.append({"type":"line","start":[160,112],"end":[166,188],"color":GOLD,"width":1})

    # --- Arms (raised, channeling void energy) ---
    P.append({"type":"rect","x":80,"y":116,"w":14,"h":36,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":162,"y":116,"w":14,"h":36,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":4})
    # hands (glowing with void energy)
    P.append({"type":"circle","cx":72,"cy":148,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":184,"cy":148,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (robe-covered) ---
    P.append({"type":"rect","x":106,"y":190,"w":18,"h":28,"color":ROBE_DARKER,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":190,"w":18,"h":28,"color":ROBE_DARKER,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":104,"y":212,"w":22,"h":10,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":212,"w":22,"h":10,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})

    # --- FLOATING VOIDLINGS (THE feature -- small purple creatures floating around) ---
    # voidling 1 (left, floating)
    P.append({"type":"circle","cx":50,"cy":100,"r":8,"color":VOIDLING,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":46,"cy":98,"r":3,"color":EYE,"outline":OUT,"outline_w":1})  # eye
    P.append({"type":"circle","cx":54,"cy":98,"r":3,"color":EYE,"outline":OUT,"outline_w":1})  # eye
    # voidling legs
    P.append({"type":"line","start":[48,107],"end":[44,114],"color":VOIDLING_DARK,"width":2})
    P.append({"type":"line","start":[52,107],"end":[56,114],"color":VOIDLING_DARK,"width":2})
    # voidling 2 (right, floating)
    P.append({"type":"circle","cx":206,"cy":100,"r":8,"color":VOIDLING,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":202,"cy":98,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":210,"cy":98,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[204,107],"end":[200,114],"color":VOIDLING_DARK,"width":2})
    P.append({"type":"line","start":[208,107],"end":[212,114],"color":VOIDLING_DARK,"width":2})
    # voidling 3 (top, floating above)
    P.append({"type":"circle","cx":128,"cy":40,"r":7,"color":VOIDLING,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":125,"cy":39,"r":2,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":131,"cy":39,"r":2,"color":EYE,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# MonkeyKing -- Wukong; GOLDEN ARMOR + LONG TAIL + monkey face + staff
# ============================================================================
def monkeyking_prims():
    P = []
    FUR = (140, 100, 65)        # monkey fur (brown)
    FUR_DARK = (95, 65, 40)
    FUR_LIGHT = (175, 130, 90)
    SKIN = (225, 185, 145)      # monkey face skin (peach)
    GOLD = (225, 185, 65)       # golden armor
    GOLD_DARK = (160, 120, 30)
    GOLD_LIGHT = (245, 215, 100)
    RED = (180, 40, 40)         # red decorative fabric
    RED_DARK = (130, 25, 25)
    STAFF = (215, 175, 60)      # enchanted staff (gold)
    STAFF_DARK = (150, 110, 30)
    TAIL = (140, 100, 65)       # prehensile tail (same as fur)
    TAIL_DARK = (95, 65, 40)
    EYE = (40, 30, 25)
    OUT = (30, 20, 15)

    # --- LONG PREHENSILE TAIL (THE missing feature -- BIG, curling behind) ---
    tail = [(150,170),(176,180),(190,160),(196,130),(186,100)]
    for i in range(len(tail)-1):
        P.append({"type":"line","start":tail[i],"end":tail[i+1],"color":TAIL,"width":12})
    for cx, cy in tail:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":7,"color":TAIL,"outline":TAIL_DARK,"outline_w":1})
    # tail tip (curled)
    P.append({"type":"circle","cx":186,"cy":100,"r":8,"color":TAIL,"outline":TAIL_DARK,"outline_w":1})

    # --- Hair/fur (monkey, brown) ---
    P.append({"type":"circle","cx":118,"cy":66,"r":22,"color":FUR,"outline":OUT,"outline_w":1})
    # fur texture (spiky monkey hair)
    for fx, fy in [(100,56),(110,50),(118,48),(126,50),(136,56)]:
        P.append({"type":"polygon","points":[(fx-3,fy+4),(fx,fy-4),(fx+3,fy+4)],"color":FUR_DARK,"outline":OUT,"outline_w":1})

    # --- MONKEY FACE (THE feature -- peach skin face, monkey features) ---
    # face (peach skin, heart-shaped monkey face)
    P.append({"type":"polygon","points":[(100,62),(136,62),(132,90),(118,98),(104,90)],
              "color":SKIN,"outline":OUT,"outline_w":2})
    # monkey eyes
    P.append({"type":"circle","cx":110,"cy":76,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":126,"cy":76,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":111,"cy":75,"r":2,"color":(255,255,255)})
    P.append({"type":"circle","cx":127,"cy":75,"r":2,"color":(255,255,255)})
    # monkey nose (flat, wide)
    P.append({"type":"ellipse","x":114,"y":84,"w":10,"h":6,"color":SKIN_DARK if False else (180,140,110),"outline":OUT,"outline_w":1})
    # monkey mouth (wide, expressive)
    P.append({"type":"line","start":[108,92],"end":[128,92],"color":(120,60,50),"width":2})
    # monkey ears (big, on sides)
    P.append({"type":"circle","cx":96,"cy":72,"r":8,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":140,"cy":72,"r":8,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":96,"cy":72,"r":4,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":140,"cy":72,"r":4,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- GOLDEN ARMOR (THE feature -- BIG, shining gold plates) ---
    # chest plate (big golden armor)
    P.append({"type":"polygon","points":[(96,96),(140,96),(144,160),(92,160)],
              "color":GOLD,"outline":OUT,"outline_w":2})
    # armor shine (highlight)
    P.append({"type":"line","start":[100,100],"end":[100,156],"color":GOLD_LIGHT,"width":2})
    # armor plate segments
    P.append({"type":"line","start":[96,120],"end":[140,120],"color":GOLD_DARK,"width":2})
    P.append({"type":"line","start":[96,140],"end":[140,140],"color":GOLD_DARK,"width":2})
    # armor center crest
    P.append({"type":"line","start":[118,100],"end":[118,156],"color":GOLD_DARK,"width":1})
    P.append({"type":"circle","cx":118,"cy":120,"r":5,"color":RED,"outline":GOLD_DARK,"outline_w":1})
    # gold shoulder pads (BIG, armored)
    P.append({"type":"circle","cx":94,"cy":100,"r":12,"color":GOLD,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":142,"cy":100,"r":12,"color":GOLD,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":94,"cy":100,"r":7,"color":GOLD_LIGHT,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":142,"cy":100,"r":7,"color":GOLD_LIGHT,"outline":GOLD_DARK,"outline_w":1})

    # --- Red decorative fabric (sash, flowing) ---
    P.append({"type":"polygon","points":[(92,150),(144,150),(140,168),(96,168)],
              "color":RED,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[92,150],"end":[144,150],"color":GOLD,"width":2})
    # red fabric flowing (trailing)
    P.append({"type":"polygon","points":[(92,160),(80,176),(86,196),(96,170)],"color":RED,"outline":RED_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(144,160),(156,176),(150,196),(140,170)],"color":RED,"outline":RED_DARK,"outline_w":1})

    # --- Arms (muscular, furry) ---
    P.append({"type":"rect","x":76,"y":108,"w":16,"h":44,"color":FUR,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":144,"y":108,"w":16,"h":44,"color":FUR,"outline":OUT,"outline_w":1,"radius":4})
    # gold arm bands
    P.append({"type":"rect","x":76,"y":120,"w":16,"h":4,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":144,"y":120,"w":16,"h":4,"color":GOLD,"outline":OUT,"outline_w":1})
    # monkey hands
    P.append({"type":"circle","cx":84,"cy":154,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":152,"cy":154,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (furry, with gold shin armor) ---
    P.append({"type":"rect","x":100,"y":168,"w":18,"h":40,"color":FUR,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":122,"y":168,"w":18,"h":40,"color":FUR,"outline":OUT,"outline_w":1,"radius":3})
    # gold shin armor
    P.append({"type":"rect","x":100,"y":180,"w":18,"h":16,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"rect","x":122,"y":180,"w":18,"h":16,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # monkey feet
    P.append({"type":"ellipse","x":98,"y":204,"w":22,"h":14,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"ellipse","x":120,"y":204,"w":22,"h":14,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Enchanted staff (in right hand, BIG, gold) ---
    P.append({"type":"line","start":[152,154],"end":[200,40],"color":STAFF,"width":6})
    # staff ends (gold caps)
    P.append({"type":"circle","cx":200,"cy":40,"r":6,"color":STAFF,"outline":STAFF_DARK,"outline_w":2})
    P.append({"type":"circle","cx":152,"cy":154,"r":5,"color":STAFF,"outline":STAFF_DARK,"outline_w":1})
    # staff glow (enchanted)
    P.append({"type":"circle","cx":200,"cy":40,"r":10,"color":(255,230,140),"outline":STAFF,"outline_w":1})
    # gold bands on staff
    P.append({"type":"rect","x":170,"y":80,"w":10,"h":8,"color":STAFF_DARK,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Run all 6
# ============================================================================
CHAMPS = [
    ("Kayn", kayn_prims, "sentient scythe Rhaast + shadow energy"),
    ("Kindred", kindred_prims, "white lamb + big spectral wolf"),
    ("LeeSin", leesin_prims, "blindfold + monk robes + hand wraps"),
    ("Lucian", lucian_prims, "dual pistols + white coat + light effects"),
    ("Malzahar", malzahar_prims, "deep hood + void energy + voidlings"),
    ("MonkeyKing", monkeyking_prims, "golden armor + long tail + monkey face"),
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
