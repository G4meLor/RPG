"""Batch 24 (FINAL): Yone, Yorick, Zed.

All at 7 — need ONE big icon pushed to 8.

- Yone   -> DEMONIC AZAKANA MASK (big horned mask) + dual katanas
- Yorick -> MASSIVE SHOVEL + small ghouls (companions) + tattered robes
- Zed    -> FACE MASK with GLOWING RED EYES + arm-mounted blades + shadow aura
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve


# ============================================================================
# Yone -- the unforgotten, DEMONIC AZAKANA MASK + dual katanas
# ============================================================================
def yone_prims():
    P = []
    ROBE = (180, 50, 50)          # red Ionian robes
    ROBE_DARK = (130, 30, 30)
    WHITE = (235, 230, 225)       # white robe accents
    DARK_BLUE = (30, 35, 55)      # dark blue under-robe
    MASK = (180, 50, 50)          # red demonic azakana mask
    MASK_DARK = (120, 30, 30)
    HORN = (220, 210, 200)        # mask horns (bone white)
    HORN_DARK = (160, 150, 140)
    SPIRIT = (100, 200, 220)      # spirit-half (cyan/teal)
    SPIRIT_GLOW = (140, 230, 240)
    KATANA = (180, 185, 195)      # katana blades
    KATANA_DARK = (120, 125, 135)
    HAIR = (30, 35, 50)           # dark blue ponytail
    EYE = (240, 220, 100)         # glowing yellow eyes
    OUT = (15, 15, 25)

    # --- DUAL KATANAS (THE feature #2 -- crossed on back, big) ---
    # left katana (diagonal across back)
    P.append({"type":"line","start":[80,80],"end":[170,200],"color":KATANA,"width":5})
    P.append({"type":"line","start":[80,80],"end":[170,200],"color":KATANA_DARK,"width":1})
    # left katana guard
    P.append({"type":"rect","x":74,"y":74,"w":12,"h":6,"color":(200,165,70),"outline":OUT,"outline_w":1})
    # left katana hilt
    P.append({"type":"rect","x":76,"y":60,"w":8,"h":18,"color":HAIR,"outline":OUT,"outline_w":1})
    # right katana (mirror diagonal)
    P.append({"type":"line","start":[176,80],"end":[86,200],"color":KATANA,"width":5})
    P.append({"type":"line","start":[176,80],"end":[86,200],"color":KATANA_DARK,"width":1})
    # right katana guard
    P.append({"type":"rect","x":170,"y":74,"w":12,"h":6,"color":(200,165,70),"outline":OUT,"outline_w":1})
    # right katana hilt
    P.append({"type":"rect","x":172,"y":60,"w":8,"h":18,"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Long ponytail (behind, flowing) ---
    P.append({"type":"polygon","points":[(120,70),(136,70),(148,180),(108,180)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # ponytail tie (red)
    P.append({"type":"rect","x":120,"y":70,"w":16,"h":6,"color":ROBE_DARK,"outline":OUT,"outline_w":1})

    # --- Spirit-half manifestation (THE missing feature -- cyan glow on left side) ---
    P.append({"type":"polygon","points":[(84,90),(128,90),(128,200),(80,200)],
              "color":SPIRIT,"outline":SPIRIT_GLOW,"outline_w":1})
    # spirit glow lines
    P.append({"type":"line","start":[88,100],"end":[88,190],"color":SPIRIT_GLOW,"width":2})
    P.append({"type":"line","start":[100,100],"end":[100,190],"color":SPIRIT_GLOW,"width":1})

    # --- Legs (dark blue under-robe) ---
    P.append({"type":"rect","x":108,"y":170,"w":16,"h":40,"color":DARK_BLUE,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":16,"h":40,"color":DARK_BLUE,"outline":OUT,"outline_w":1,"radius":3})
    # white leg wraps
    P.append({"type":"rect","x":108,"y":186,"w":16,"h":6,"color":WHITE,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":132,"y":186,"w":16,"h":6,"color":WHITE,"outline":OUT,"outline_w":1})
    # sandals
    P.append({"type":"rect","x":104,"y":206,"w":24,"h":8,"color":(90,60,40),"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":206,"w":24,"h":8,"color":(90,60,40),"outline":OUT,"outline_w":1,"radius":2})

    # --- Torso (flowing Ionian robes -- red + white) ---
    P.append({"type":"polygon","points":[(96,100),(160,100),(164,172),(92,172)],
              "color":ROBE,"outline":OUT,"outline_w":2})
    # white robe panel (center)
    P.append({"type":"polygon","points":[(112,108),(144,108),(148,168),(108,168)],
              "color":WHITE,"outline":OUT,"outline_w":1})
    # red sash (obi belt)
    P.append({"type":"rect","x":92,"y":150,"w":72,"h":10,"color":ROBE_DARK,"outline":OUT,"outline_w":2})
    # robe flowing edges (THE missing feature -- flowing robes)
    P.append({"type":"polygon","points":[(92,172),(80,200),(96,190)],"color":ROBE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(164,172),(176,200),(160,190)],"color":ROBE_DARK,"outline":OUT,"outline_w":1})

    # --- Arms (robed) ---
    P.append({"type":"rect","x":80,"y":108,"w":16,"h":50,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":160,"y":108,"w":16,"h":50,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    # white forearm wraps
    P.append({"type":"rect","x":80,"y":140,"w":16,"h":14,"color":WHITE,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":160,"y":140,"w":16,"h":14,"color":WHITE,"outline":OUT,"outline_w":1})
    # hands
    P.append({"type":"circle","cx":88,"cy":162,"r":5,"color":(210,190,170),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":168,"cy":162,"r":5,"color":(210,190,170),"outline":OUT,"outline_w":1})

    # --- DEMONIC AZAKANA MASK (THE feature -- HUGE horned mask, dominates head) ---
    # mask base (BIG, red, covers face -- 40% of head area)
    P.append({"type":"circle","cx":128,"cy":76,"r":30,"color":MASK,"outline":OUT,"outline_w":3})
    # mask face (darker red)
    P.append({"type":"circle","cx":128,"cy":78,"r":24,"color":MASK_DARK,"outline":OUT,"outline_w":1})
    # DEMON HORNS (THE icon -- HUGE, sweeping up from mask, bone-white, 30% of sprite)
    # left horn (BIG, curving up and out)
    P.append({"type":"polygon","points":[(102,58),(90,38),(82,18),(94,22),(106,48)],
              "color":HORN,"outline":OUT,"outline_w":3})
    # right horn (BIG, mirrored)
    P.append({"type":"polygon","points":[(154,58),(166,38),(174,18),(162,22),(150,48)],
              "color":HORN,"outline":OUT,"outline_w":3})
    # horn ridges (texture, dark lines)
    P.append({"type":"line","start":[98,40],"end":[92,34],"color":HORN_DARK,"width":1})
    P.append({"type":"line","start":[158,40],"end":[164,34],"color":HORN_DARK,"width":1})
    # center horn spike (bigger, between big horns)
    P.append({"type":"polygon","points":[(120,56),(136,56),(128,36)],
              "color":HORN,"outline":OUT,"outline_w":2})
    # horn base rings (demonic detail)
    P.append({"type":"circle","cx":100,"cy":54,"r":4,"color":MASK_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":156,"cy":54,"r":4,"color":MASK_DARK,"outline":OUT,"outline_w":1})

    # mask eyes (glowing yellow, demonic -- BIG slit-shaped)
    P.append({"type":"ellipse","x":114,"y":72,"w":10,"h":5,"color":EYE,"outline":OUT,"outline_w":2})
    P.append({"type":"ellipse","x":132,"y":72,"w":10,"h":5,"color":EYE,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":120,"cy":75,"r":2,"color":(255,255,200)})
    P.append({"type":"circle","cx":136,"cy":75,"r":2,"color":(255,255,200)})

    # mask mouth (demonic grin, fanged)
    P.append({"type":"line","start":[116,92],"end":[140,92],"color":OUT,"width":2})
    # fangs (bigger)
    P.append({"type":"polygon","points":[(118,92),(124,92),(121,100)],"color":HORN,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(132,92),(138,92),(135,100)],"color":HORN,"outline":OUT,"outline_w":1})

    # mask side markings (azakana tribal lines -- bigger)
    P.append({"type":"line","start":[106,66],"end":[112,82],"color":OUT,"width":2})
    P.append({"type":"line","start":[150,66],"end":[144,82],"color":OUT,"width":2})
    return P


# ============================================================================
# Yorick -- gravedigger, MASSIVE SHOVEL + ghouls + tattered robes
# ============================================================================
def yorick_prims():
    P = []
    ROBE = (70, 80, 65)           # dark green-grey burial robes
    ROBE_DARK = (45, 55, 40)
    SKIN = (180, 190, 175)        # pale undead skin
    SKIN_DARK = (140, 155, 130)
    SHOVEL = (120, 125, 135)      # iron shovel
    SHOVEL_DARK = (80, 85, 95)
    WOOD = (100, 70, 45)          # wooden handle
    GHoul = (120, 140, 100)       # small ghoul (greenish-grey)
    GHoul_DARK = (80, 100, 70)
    SHACKLE = (90, 90, 95)        # iron shackles
    EYE = (240, 220, 100)         # sunken yellow eyes
    OUT = (20, 25, 20)

    # --- SMALL GHOULS (THE missing feature -- companion creatures, beside him) ---
    # left ghoul (small, hunched, at his feet)
    P.append({"type":"circle","cx":56,"cy":196,"r":12,"color":GHoul,"outline":OUT,"outline_w":2})
    # ghoul eyes (glowing)
    P.append({"type":"circle","cx":52,"cy":192,"r":2,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":60,"cy":192,"r":2,"color":EYE,"outline":OUT,"outline_w":1})
    # ghoul mouth (toothed)
    P.append({"type":"line","start":[52,200],"end":[60,200],"color":OUT,"width":1})
    # ghoul body (small hunched)
    P.append({"type":"ellipse","x":44,"y":204,"w":24,"h":20,"color":GHoul_DARK,"outline":OUT,"outline_w":1})
    # ghoul claws
    P.append({"type":"line","start":[48,220],"end":[46,226],"color":OUT,"width":1})
    P.append({"type":"line","start":[64,220],"end":[66,226],"color":OUT,"width":1})

    # right ghoul (small, at his feet, mirrored)
    P.append({"type":"circle","cx":200,"cy":196,"r":12,"color":GHoul,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":196,"cy":192,"r":2,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":204,"cy":192,"r":2,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[196,200],"end":[204,200],"color":OUT,"width":1})
    P.append({"type":"ellipse","x":188,"y":204,"w":24,"h":20,"color":GHoul_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[192,220],"end":[190,226],"color":OUT,"width":1})
    P.append({"type":"line","start":[208,220],"end":[210,226],"color":OUT,"width":1})

    # --- MASSIVE SHOVEL (THE feature -- HUGE, over shoulder) ---
    # shovel handle (long, wooden, diagonal)
    P.append({"type":"line","start":[176,60],"end":[120,200],"color":WOOD,"width":8})
    # shovel blade (BIG iron spade at top)
    P.append({"type":"polygon","points":[(168,40),(192,40),(196,72),(164,72)],
              "color":SHOVEL,"outline":OUT,"outline_w":3})
    # shovel blade ridge
    P.append({"type":"line","start":[180,44],"end":[180,68],"color":SHOVEL_DARK,"width":2})
    # shovel blade edge (darker)
    P.append({"type":"polygon","points":[(168,68),(192,68),(196,72),(164,72)],
              "color":SHOVEL_DARK,"outline":OUT,"outline_w":1})
    # shovel handle grip (bottom)
    P.append({"type":"circle","cx":120,"cy":200,"r":5,"color":WOOD,"outline":OUT,"outline_w":1})

    # --- TATTERED BURIAL ROBES (body) ---
    P.append({"type":"polygon","points":[(84,100),(172,100),(180,210),(76,210)],
              "color":ROBE,"outline":OUT,"outline_w":2})
    # tattered edges (jagged bottom -- THE feature of the robes)
    for bx in (80, 96, 112, 128, 144, 160, 176):
        P.append({"type":"polygon","points":[(bx-6,206),(bx+6,206),(bx,218)],
                  "color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # robe chest area (darker)
    P.append({"type":"polygon","points":[(100,108),(156,108),(160,170),(96,170)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # rope belt/cincture
    P.append({"type":"rect","x":84,"y":160,"w":88,"h":8,"color":(120,100,70),"outline":OUT,"outline_w":1})

    # --- HEAVY IRON SHACKLES (THE missing feature -- on wrists) ---
    # left shackle (big, iron, on wrist)
    P.append({"type":"circle","cx":84,"cy":166,"r":9,"color":SHACKLE,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":84,"cy":166,"r":5,"color":(60,60,65)})
    # chain links hanging from left shackle
    P.append({"type":"circle","cx":84,"cy":178,"r":4,"color":SHACKLE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":84,"cy":186,"r":4,"color":SHACKLE,"outline":OUT,"outline_w":1})
    # right shackle
    P.append({"type":"circle","cx":172,"cy":166,"r":9,"color":SHACKLE,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":172,"cy":166,"r":5,"color":(60,60,65)})
    P.append({"type":"circle","cx":172,"cy":178,"r":4,"color":SHACKLE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":172,"cy":186,"r":4,"color":SHACKLE,"outline":OUT,"outline_w":1})

    # --- Legs (boots, under robe) ---
    P.append({"type":"rect","x":104,"y":200,"w":20,"h":16,"color":(50,40,35),"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":132,"y":200,"w":20,"h":16,"color":(50,40,35),"outline":OUT,"outline_w":1,"radius":2})

    # --- Arms (thick, robed) ---
    P.append({"type":"rect","x":72,"y":110,"w":20,"h":54,"color":ROBE,"outline":OUT,"outline_w":2,"radius":5})
    P.append({"type":"rect","x":164,"y":110,"w":20,"h":54,"color":ROBE,"outline":OUT,"outline_w":2,"radius":5})
    # big hands (hulking)
    P.append({"type":"circle","cx":82,"cy":168,"r":7,"color":SKIN_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":174,"cy":168,"r":7,"color":SKIN_DARK,"outline":OUT,"outline_w":1})

    # --- Head (pale undead, sunken eyes, hood) ---
    P.append({"type":"circle","cx":128,"cy":76,"r":24,"color":SKIN,"outline":OUT,"outline_w":2})
    # hood (dark green-grey, covers top of head)
    P.append({"type":"polygon","points":[(104,68),(152,68),(148,52),(128,42),(108,52)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":2})
    # hood drape (behind)
    P.append({"type":"polygon","points":[(104,68),(108,52),(96,90),(100,110)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(152,68),(148,52),(160,90),(156,110)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # SUNKEN EYES (THE missing feature -- dark sockets with yellow glow)
    P.append({"type":"circle","cx":119,"cy":76,"r":6,"color":(40,45,35),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":137,"cy":76,"r":6,"color":(40,45,35),"outline":OUT,"outline_w":1})
    # glowing yellow pupils (sunken but glowing)
    P.append({"type":"circle","cx":119,"cy":76,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":137,"cy":76,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    # sunken cheeks (shadow)
    P.append({"type":"circle","cx":128,"cy":86,"r":10,"color":SKIN_DARK,"outline":OUT,"outline_w":1})
    # mouth (thin, grim)
    P.append({"type":"line","start":[120,92],"end":[136,92],"color":OUT,"width":2})
    return P


# ============================================================================
# Zed -- the master of shadows, FACE MASK + GLOWING RED EYES + arm blades
# ============================================================================
def zed_prims():
    P = []
    ARMOR = (40, 40, 50)          # black/dark grey armor
    ARMOR_DARK = (25, 25, 35)
    ARMOR_LIGHT = (70, 70, 80)    # lighter grey accents
    METAL = (100, 100, 110)       # metallic plating
    METAL_DARK = (60, 60, 70)
    RED = (200, 30, 35)           # red accents
    RED_GLOW = (255, 60, 60)      # glowing red
    MASK = (50, 50, 60)           # face mask (dark)
    MASK_DARK = (30, 30, 40)
    BLADE = (160, 165, 175)       # arm-mounted blades
    BLADE_DARK = (100, 105, 115)
    SHADOW = (20, 20, 30)         # shadow aura
    EYE = (255, 40, 40)           # glowing red eyes
    OUT = (10, 10, 18)

    # --- SHADOWY AURA (THE missing feature -- dark wisps around body) ---
    # shadow aura (dark, behind everything)
    P.append({"type":"ellipse","x":72,"y":60,"w":112,"h":170,"color":SHADOW,"outline":(40,40,60),"outline_w":1})
    # shadow wisps (rising from ground)
    for sx in (84, 100, 128, 156, 172):
        P.append({"type":"line","start":[sx,210],"end":[sx,196],"color":SHADOW,"width":4})
        P.append({"type":"circle","cx":sx,"cy":194,"r":5,"color":(30,30,45),"outline":SHADOW,"outline_w":1})

    # --- ARM-MOUNTED BLADES (THE feature #2 -- HUGE, on forearms, dominate sides) ---
    # left arm blade (HUGE, extending far out from left forearm)
    P.append({"type":"polygon","points":[(72,148),(40,130),(28,148),(40,162),(72,158)],
              "color":BLADE,"outline":OUT,"outline_w":3})
    # left blade edge (sharp, bright)
    P.append({"type":"line","start":[40,130],"end":[28,148],"color":BLADE_DARK,"width":2})
    P.append({"type":"line","start":[40,162],"end":[28,148],"color":BLADE_DARK,"width":1})
    # left blade mount (on arm)
    P.append({"type":"rect","x":72,"y":144,"w":16,"h":14,"color":METAL_DARK,"outline":OUT,"outline_w":2})
    # red accent on left blade mount
    P.append({"type":"line","start":[72,151],"end":[88,151],"color":RED,"width":2})
    # right arm blade (HUGE, mirrored)
    P.append({"type":"polygon","points":[(184,148),(216,130),(228,148),(216,162),(184,158)],
              "color":BLADE,"outline":OUT,"outline_w":3})
    P.append({"type":"line","start":[216,130],"end":[228,148],"color":BLADE_DARK,"width":2})
    P.append({"type":"line","start":[216,162],"end":[228,148],"color":BLADE_DARK,"width":1})
    P.append({"type":"rect","x":168,"y":144,"w":16,"h":14,"color":METAL_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"line","start":[168,151],"end":[184,151],"color":RED,"width":2})

    # --- Legs (armored, dark) ---
    P.append({"type":"rect","x":106,"y":170,"w":18,"h":42,"color":ARMOR,"outline":OUT,"outline_w":2,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":18,"h":42,"color":ARMOR,"outline":OUT,"outline_w":2,"radius":3})
    # metal shin plates (THE missing feature -- sharp metallic accents)
    P.append({"type":"rect","x":106,"y":180,"w":18,"h":20,"color":METAL,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":132,"y":180,"w":18,"h":20,"color":METAL,"outline":OUT,"outline_w":1})
    # red trim on shins
    P.append({"type":"line","start":[106,180],"end":[124,180],"color":RED,"width":2})
    P.append({"type":"line","start":[132,180],"end":[150,180],"color":RED,"width":2})
    # ninja boots
    P.append({"type":"rect","x":104,"y":206,"w":22,"h":10,"color":ARMOR_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":206,"w":22,"h":10,"color":ARMOR_DARK,"outline":OUT,"outline_w":1,"radius":2})

    # --- Torso (metal armor plating) ---
    P.append({"type":"polygon","points":[(98,100),(158,100),(162,172),(94,172)],
              "color":ARMOR,"outline":OUT,"outline_w":2})
    # METAL CHEST PLATE (THE missing feature -- sharp metallic accents)
    P.append({"type":"polygon","points":[(106,108),(150,108),(154,160),(102,160)],
              "color":METAL,"outline":OUT,"outline_w":2})
    # chest plate seams (sharp metallic lines)
    P.append({"type":"line","start":[128,108],"end":[128,160],"color":METAL_DARK,"width":2})
    P.append({"type":"line","start":[106,130],"end":[150,130],"color":METAL_DARK,"width":1})
    # RED ACCENT on chest (Zed's red symbol)
    P.append({"type":"circle","cx":128,"cy":130,"r":8,"color":RED,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":130,"r":4,"color":RED_GLOW})
    # red belt
    P.append({"type":"rect","x":94,"y":158,"w":68,"h":8,"color":RED,"outline":OUT,"outline_w":1})
    # metal belt buckle
    P.append({"type":"rect","x":120,"y":158,"w":16,"h":8,"color":METAL_DARK,"outline":OUT,"outline_w":1})

    # --- Arms (armored, with metal plating) ---
    P.append({"type":"rect","x":80,"y":108,"w":18,"h":48,"color":ARMOR,"outline":OUT,"outline_w":2,"radius":4})
    P.append({"type":"rect","x":158,"y":108,"w":18,"h":48,"color":ARMOR,"outline":OUT,"outline_w":2,"radius":4})
    # metal shoulder plates (sharp, big)
    P.append({"type":"polygon","points":[(78,108),(98,108),(96,96),(80,98)],
              "color":METAL,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(158,108),(178,108),(176,98),(160,96)],
              "color":METAL,"outline":OUT,"outline_w":2})
    # red shoulder trim
    P.append({"type":"line","start":[80,98],"end":[96,96],"color":RED,"width":2})
    P.append({"type":"line","start":[160,96],"end":[176,98],"color":RED,"width":2})
    # metal forearm plates
    P.append({"type":"rect","x":80,"y":140,"w":18,"h":16,"color":METAL,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":158,"y":140,"w":18,"h":16,"color":METAL,"outline":OUT,"outline_w":1})
    # hands (gloved)
    P.append({"type":"circle","cx":89,"cy":160,"r":6,"color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":167,"cy":160,"r":6,"color":ARMOR_DARK,"outline":OUT,"outline_w":1})

    # --- FACE MASK (THE feature -- BIG, covers face, with GLOWING RED EYES) ---
    # mask base (big, dark, covers entire face)
    P.append({"type":"polygon","points":[(104,56),(152,56),(156,96),(100,96)],
              "color":MASK,"outline":OUT,"outline_w":3})
    # mask face (darker)
    P.append({"type":"polygon","points":[(108,60),(148,60),(152,92),(104,92)],
              "color":MASK_DARK,"outline":OUT,"outline_w":1})
    # mask top edge (metallic)
    P.append({"type":"rect","x":104,"y":54,"w":52,"h":6,"color":METAL,"outline":OUT,"outline_w":2})
    # red trim on mask top
    P.append({"type":"line","start":[108,56],"end":[148,56],"color":RED,"width":2})

    # GLOWING RED EYES (THE icon -- big, bright, menacing -- the key feature)
    P.append({"type":"ellipse","x":114,"y":70,"w":12,"h":6,"color":EYE,"outline":OUT,"outline_w":2})
    P.append({"type":"ellipse","x":130,"y":70,"w":12,"h":6,"color":EYE,"outline":OUT,"outline_w":2})
    # eye glow (bright center)
    P.append({"type":"circle","cx":120,"cy":73,"r":3,"color":RED_GLOW})
    P.append({"type":"circle","cx":136,"cy":73,"r":3,"color":RED_GLOW})
    P.append({"type":"circle","cx":120,"cy":73,"r":1,"color":(255,200,200)})
    P.append({"type":"circle","cx":136,"cy":73,"r":1,"color":(255,200,200)})

    # mask mouth area (dark, covered)
    P.append({"type":"rect","x":112,"y":84,"w":32,"h":8,"color":MASK_DARK,"outline":OUT,"outline_w":1})
    # mask breathing slits
    P.append({"type":"line","start":[118,86],"end":[118,90],"color":METAL_DARK,"width":1})
    P.append({"type":"line","start":[124,86],"end":[124,90],"color":METAL_DARK,"width":1})
    P.append({"type":"line","start":[130,86],"end":[130,90],"color":METAL_DARK,"width":1})
    P.append({"type":"line","start":[136,86],"end":[136,90],"color":METAL_DARK,"width":1})

    # hood/cowl (dark, behind mask)
    P.append({"type":"polygon","points":[(104,56),(152,56),(148,42),(128,34),(108,42)],
              "color":ARMOR_DARK,"outline":OUT,"outline_w":2})
    # hood side drape
    P.append({"type":"polygon","points":[(104,56),(108,42),(96,80),(100,100)],
              "color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(152,56),(148,42),(160,80),(156,100)],
              "color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# RUN
# ============================================================================
if __name__ == "__main__":
    results = []
    for name, fn in [("Yone", yone_prims), ("Yorick", yorick_prims),
                     ("Zed", zed_prims)]:
        prims = fn()
        r = improve(name, prims, gate_n=3)
        print(f"RESULT: {r}")
        results.append(r)
    print("\n=== BATCH 24 SUMMARY ===")
    for r in results:
        print(f"  {r['id']}: {r['old']} -> {r['new']} saved={r['saved']} missing={r['missing'][:3]}")
