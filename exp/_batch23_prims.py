"""Batch 23: Nautilus, Neeko, Orianna, Shaco, Shen, TahmKench.

All at 7 — need ONE big icon pushed to 8.

- Nautilus   -> MASSIVE DIVING SUIT (big helmet + huge anchor)
- Neeko      -> CHAMELEON TAIL (curling tail, big) + colorful head crests
- Orianna    -> BALL-JOINTED DOLL LIMBS + wind-up key + floating ball
- Shaco      -> JESTER HAT WITH BELLS (three-pointed, big)
- Shen       -> KINKOU MASK (over eyes, big) + shoulder guards
- TahmKench  -> MASSIVE WIDE MOUTH (huge gaping, like Chogath/KogMaw at 8)
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve


# ============================================================================
# Nautilus -- titan of the depths, MASSIVE DIVING SUIT + huge anchor
# ============================================================================
def nautilus_prims():
    P = []
    SUIT = (40, 70, 100)         # deep sea blue diving suit
    SUIT_DARK = (25, 50, 75)
    COPPER = (160, 110, 60)      # copper accents/trim
    COPPER_DARK = (110, 75, 40)
    TEAL = (60, 160, 160)        # teal glow
    TEAL_GLOW = (100, 200, 200)
    METAL = (90, 95, 105)        # metallic grey
    METAL_DARK = (60, 65, 75)
    HELM = (50, 80, 110)         # helm darker blue
    EYE = (100, 220, 220)        # glowing cyan eyes
    BARNACLE = (200, 200, 190)   # barnacle color
    OUT = (15, 25, 35)

    # --- MASSIVE ANCHOR (THE feature #2 -- HUGE, dominates right side) ---
    # anchor shaft (vertical, BIG, thick)
    P.append({"type":"rect","x":194,"y":50,"w":18,"h":170,"color":METAL,"outline":OUT,"outline_w":3})
    # anchor top ring (big)
    P.append({"type":"circle","cx":203,"cy":46,"r":12,"color":METAL,"outline":OUT,"outline_w":3})
    P.append({"type":"circle","cx":203,"cy":46,"r":6,"color":METAL_DARK})
    # anchor flukes (the curved hooks at bottom -- BIG, wide)
    P.append({"type":"polygon","points":[(194,200),(212,200),(230,224),(224,232),(206,216),(194,216)],
              "color":METAL,"outline":OUT,"outline_w":3})
    P.append({"type":"polygon","points":[(194,216),(206,216),(188,232),(182,224)],
              "color":METAL_DARK,"outline":OUT,"outline_w":2})
    # anchor crossbar (wide, obvious)
    P.append({"type":"rect","x":180,"y":96,"w":46,"h":10,"color":METAL_DARK,"outline":OUT,"outline_w":2})
    # anchor shaft highlight
    P.append({"type":"line","start":[198,56],"end":[198,216],"color":METAL_DARK,"width":1})

    # --- DIVING SUIT BODY (THE feature -- massive, bulky) ---
    # torso (big, broad)
    P.append({"type":"polygon","points":[(84,100),(172,100),(180,200),(76,200)],
              "color":SUIT,"outline":OUT,"outline_w":3})
    # suit chest plate (copper-rimmed)
    P.append({"type":"polygon","points":[(96,108),(160,108),(164,170),(92,170)],
              "color":SUIT_DARK,"outline":COPPER,"outline_w":2})
    # copper rivets on suit
    for rx in (104, 120, 136, 152):
        P.append({"type":"circle","cx":rx,"cy":118,"r":3,"color":COPPER,"outline":OUT,"outline_w":1})
        P.append({"type":"circle","cx":rx,"cy":160,"r":3,"color":COPPER,"outline":OUT,"outline_w":1})
    # teal glow line on chest (energy)
    P.append({"type":"line","start":[100,140],"end":[156,140],"color":TEAL,"width":2})
    # BARNACLES (THE missing feature -- big obvious barnacles on suit)
    for bx, by in [(88,130),(92,150),(168,130),(172,150),(100,180),(160,180)]:
        P.append({"type":"circle","cx":bx,"cy":by,"r":4,"color":BARNACLE,"outline":OUT,"outline_w":1})

    # --- Legs (massive suit legs) ---
    P.append({"type":"rect","x":88,"y":196,"w":36,"h":30,"color":SUIT_DARK,"outline":OUT,"outline_w":2,"radius":4})
    P.append({"type":"rect","x":132,"y":196,"w":36,"h":30,"color":SUIT_DARK,"outline":OUT,"outline_w":2,"radius":4})
    # mechanical joints (THE missing feature)
    P.append({"type":"circle","cx":106,"cy":210,"r":6,"color":COPPER,"outline":COPPER_DARK,"outline_w":1})
    P.append({"type":"circle","cx":150,"cy":210,"r":6,"color":COPPER,"outline":COPPER_DARK,"outline_w":1})

    # --- Arms (massive suit arms) ---
    P.append({"type":"rect","x":64,"y":108,"w":24,"h":60,"color":SUIT,"outline":OUT,"outline_w":2,"radius":5})
    P.append({"type":"rect","x":168,"y":108,"w":24,"h":60,"color":SUIT,"outline":OUT,"outline_w":2,"radius":5})
    # copper shoulder pads (big)
    P.append({"type":"circle","cx":76,"cy":112,"r":12,"color":COPPER,"outline":COPPER_DARK,"outline_w":2})
    P.append({"type":"circle","cx":180,"cy":112,"r":12,"color":COPPER,"outline":COPPER_DARK,"outline_w":2})
    # mechanical elbow joints
    P.append({"type":"circle","cx":76,"cy":150,"r":5,"color":COPPER,"outline":COPPER_DARK,"outline_w":1})
    P.append({"type":"circle","cx":180,"cy":150,"r":5,"color":COPPER,"outline":COPPER_DARK,"outline_w":1})
    # big suit hands
    P.append({"type":"circle","cx":76,"cy":172,"r":10,"color":SUIT_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":180,"cy":172,"r":10,"color":SUIT_DARK,"outline":OUT,"outline_w":2})

    # --- DIVING HELM (THE feature -- big, round, glowing) ---
    P.append({"type":"circle","cx":128,"cy":74,"r":28,"color":HELM,"outline":OUT,"outline_w":3})
    # helm viewport (copper-rimmed porthole)
    P.append({"type":"circle","cx":128,"cy":74,"r":20,"color":SUIT_DARK,"outline":COPPER,"outline_w":2})
    # glowing cyan eyes inside helm
    P.append({"type":"circle","cx":120,"cy":72,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":136,"cy":72,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":120,"cy":72,"r":2,"color":TEAL_GLOW})
    P.append({"type":"circle","cx":136,"cy":72,"r":2,"color":TEAL_GLOW})
    # helm bolts (copper rivets around rim)
    for ang_deg in (30, 90, 150, 210, 270, 330):
        import math
        hx = 128 + int(25 * math.cos(math.radians(ang_deg)))
        hy = 74 + int(25 * math.sin(math.radians(ang_deg)))
        P.append({"type":"circle","cx":hx,"cy":hy,"r":3,"color":COPPER,"outline":OUT,"outline_w":1})
    # helm top pipe/valve
    P.append({"type":"rect","x":124,"y":44,"w":8,"h":8,"color":METAL,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Neeko -- curious chameleon, CHAMELEON TAIL + colorful crests
# ============================================================================
def neeko_prims():
    P = []
    SKIN = (120, 200, 100)       # green skin
    SKIN_DARK = (85, 160, 70)
    PINK = (230, 100, 160)       # pink crest/accent
    PINK_DARK = (190, 70, 130)
    YELLOW = (240, 220, 80)      # yellow accents
    TAIL = (90, 170, 80)         # green tail
    TAIL_DARK = (60, 120, 55)
    TAIL_PINK = (220, 100, 150)  # pink tail stripe
    CREST = (230, 100, 160)      # head crest (pink)
    EYE = (240, 220, 80)         # big yellow eyes
    EYE_PUPIL = (30, 25, 20)
    CLOTH = (180, 80, 130)       # pink/magenta clothing
    OUT = (25, 35, 25)

    # --- CHAMELEON TAIL (THE feature -- BIG, curling spiral, VISIBLE to the right side) ---
    # tail curls from bottom-right up in a big spiral (visible, not hidden behind body)
    tail_pts = [(168,200),(184,186),(196,166),(198,142),(188,124),(172,120),
                (158,128),(156,142),(164,150),(174,148),(176,140)]
    for i in range(len(tail_pts)-1):
        s, e = tail_pts[i], tail_pts[i+1]
        P.append({"type":"line","start":s,"end":e,"color":TAIL,"width":14})
    for cx, cy in tail_pts:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":8,"color":TAIL,"outline":TAIL_DARK,"outline_w":1})
    # pink stripe along tail (chameleon color shift)
    for cx, cy in tail_pts[::2]:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":5,"color":TAIL_PINK,"outline":OUT,"outline_w":1})
    # tail tip (curled, pink, big)
    P.append({"type":"circle","cx":176,"cy":140,"r":7,"color":PINK,"outline":OUT,"outline_w":1})

    # --- Legs (slender, green skin) ---
    P.append({"type":"rect","x":108,"y":170,"w":14,"h":40,"color":SKIN,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":134,"y":170,"w":14,"h":40,"color":SKIN,"outline":OUT,"outline_w":1,"radius":3})
    # feet (small, yordle-ish)
    P.append({"type":"ellipse","x":106,"y":206,"w":16,"h":10,"color":SKIN_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"ellipse","x":134,"y":206,"w":16,"h":10,"color":SKIN_DARK,"outline":OUT,"outline_w":1})

    # --- Torso (slender, pink/magenta clothing) ---
    P.append({"type":"polygon","points":[(108,100),(148,100),(152,172),(104,172)],
              "color":CLOTH,"outline":OUT,"outline_w":1})
    # organic plant-like accessory (THE missing feature -- leaves)
    P.append({"type":"polygon","points":[(104,110),(96,100),(100,120)],"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(152,110),(160,100),(156,120)],"color":SKIN,"outline":OUT,"outline_w":1})
    # yellow accent on chest
    P.append({"type":"circle","cx":128,"cy":130,"r":5,"color":YELLOW,"outline":OUT,"outline_w":1})

    # --- Arms (slender, green skin, webbed fingers) ---
    P.append({"type":"rect","x":92,"y":108,"w":14,"h":44,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":150,"y":108,"w":14,"h":44,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    # webbed fingers (THE missing feature)
    for fx in (96, 100, 104):
        P.append({"type":"line","start":[fx,152],"end":[fx-2,160],"color":SKIN_DARK,"width":1})
    for fx in (154, 158, 162):
        P.append({"type":"line","start":[fx,152],"end":[fx+2,160],"color":SKIN_DARK,"width":1})

    # --- Head (big, expressive, chameleon) ---
    P.append({"type":"circle","cx":128,"cy":78,"r":24,"color":SKIN,"outline":OUT,"outline_w":2})
    # COLORFUL CRESTS on head (THE feature #2 -- BIG, pink/yellow, spiky)
    P.append({"type":"polygon","points":[(104,60),(152,60),(148,42),(128,28),(108,42)],
              "color":CREST,"outline":OUT,"outline_w":3})
    # crest spikes (BIG, pointy, colorful -- THE icon)
    for cx, cy in [(108,52),(118,42),(128,32),(138,42),(148,52)]:
        P.append({"type":"polygon","points":[(cx-5,cy+6),(cx+5,cy+6),(cx,cy-10)],
                  "color":PINK_DARK,"outline":OUT,"outline_w":2})
    # yellow crest accents (bright, big)
    P.append({"type":"circle","cx":128,"cy":40,"r":6,"color":YELLOW,"outline":OUT,"outline_w":1})
    for cx, cy in [(112,50),(144,50)]:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":4,"color":YELLOW,"outline":OUT,"outline_w":1})

    # --- LARGE EXPRESSIVE EYES (THE feature #3 -- big, yellow) ---
    P.append({"type":"circle","cx":118,"cy":80,"r":8,"color":(255,255,250),"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":138,"cy":80,"r":8,"color":(255,255,250),"outline":OUT,"outline_w":2})
    # big yellow irises
    P.append({"type":"circle","cx":118,"cy":80,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":138,"cy":80,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    # pupils (vertical slit -- chameleon)
    P.append({"type":"ellipse","x":117,"y":78,"w":2,"h":6,"color":EYE_PUPIL,"outline":OUT,"outline_w":1})
    P.append({"type":"ellipse","x":137,"y":78,"w":2,"h":6,"color":EYE_PUPIL,"outline":OUT,"outline_w":1})
    # eye shine
    P.append({"type":"circle","cx":116,"cy":77,"r":2,"color":(255,255,255)})
    P.append({"type":"circle","cx":136,"cy":77,"r":2,"color":(255,255,255)})
    # small nose
    P.append({"type":"circle","cx":128,"cy":90,"r":2,"color":SKIN_DARK})
    # mouth (small smile)
    P.append({"type":"line","start":[122,96],"end":[134,96],"color":OUT,"width":1})
    return P


# ============================================================================
# Orianna -- lady of clockwork, BALL-JOINTED LIMBS + wind-up key + ball
# ============================================================================
def orianna_prims():
    P = []
    PORCELAIN = (240, 235, 225)  # porcelain white
    PORCELAIN_DARK = (200, 195, 185)
    GOLD = (210, 175, 80)        # gold/brass
    GOLD_DARK = (150, 115, 40)
    BLUE = (100, 160, 220)       # blue accents
    BLUE_GLOW = (140, 200, 250)
    STEEL = (150, 155, 165)      # steel joints
    STEEL_DARK = (100, 105, 115)
    BALL = (180, 185, 200)       # floating ball companion
    BALL_GLOW = (140, 200, 250)
    EYE = (120, 180, 230)        # blue mechanical eyes
    OUT = (30, 25, 35)

    # --- FLOATING BALL COMPANION (THE feature #2 -- beside her) ---
    P.append({"type":"circle","cx":48,"cy":130,"r":18,"color":BALL,"outline":OUT,"outline_w":2})
    # ball seams (mechanical)
    P.append({"type":"line","start":[30,130],"end":[66,130],"color":STEEL_DARK,"width":1})
    P.append({"type":"line","start":[48,112],"end":[48,148],"color":STEEL_DARK,"width":1})
    # ball glowing core
    P.append({"type":"circle","cx":48,"cy":130,"r":8,"color":BLUE_GLOW,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":48,"cy":130,"r":4,"color":(220,240,255)})
    # ball energy link to Orianna
    P.append({"type":"line","start":[66,130],"end":[96,130],"color":BLUE_GLOW,"width":1})

    # --- WIND-UP KEY IN BACK (THE feature #3 -- visible behind shoulder) ---
    P.append({"type":"rect","x":176,"y":88,"w":8,"h":24,"color":GOLD,"outline":OUT,"outline_w":1})
    # key head (heart-shaped cog)
    P.append({"type":"circle","cx":184,"cy":84,"r":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":184,"cy":84,"r":5,"color":GOLD_DARK})
    # key teeth (cog spokes)
    for ang_deg in (0, 90, 180, 270):
        import math
        kx = 184 + int(12 * math.cos(math.radians(ang_deg)))
        ky = 84 + int(12 * math.sin(math.radians(ang_deg)))
        P.append({"type":"circle","cx":kx,"cy":ky,"r":3,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Legs (BALL-JOINTED -- THE feature, obvious joints) ---
    # upper legs
    P.append({"type":"rect","x":108,"y":170,"w":16,"h":22,"color":PORCELAIN,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":16,"h":22,"color":PORCELAIN,"outline":OUT,"outline_w":1,"radius":3})
    # BALL JOINTS (knees -- big obvious spherical joints)
    P.append({"type":"circle","cx":116,"cy":192,"r":8,"color":STEEL,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":140,"cy":192,"r":8,"color":STEEL,"outline":OUT,"outline_w":2})
    # gold joint bands
    P.append({"type":"circle","cx":116,"cy":192,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":140,"cy":192,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # lower legs
    P.append({"type":"rect","x":110,"y":198,"w":12,"h":18,"color":PORCELAIN,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":134,"y":198,"w":12,"h":18,"color":PORCELAIN,"outline":OUT,"outline_w":1,"radius":2})
    # porcelain feet
    P.append({"type":"ellipse","x":108,"y":214,"w":16,"h":8,"color":PORCELAIN_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"ellipse","x":132,"y":214,"w":16,"h":8,"color":PORCELAIN_DARK,"outline":OUT,"outline_w":1})

    # --- Torso (porcelain, clockwork) ---
    P.append({"type":"polygon","points":[(104,100),(152,100),(156,172),(100,172)],
              "color":PORCELAIN,"outline":OUT,"outline_w":2})
    # brass gear accents on chest
    P.append({"type":"circle","cx":128,"cy":128,"r":10,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":128,"r":6,"color":GOLD_DARK})
    # gear teeth
    for ang_deg in (0, 45, 90, 135, 180, 225, 270, 315):
        import math
        gx = 128 + int(12 * math.cos(math.radians(ang_deg)))
        gy = 128 + int(12 * math.sin(math.radians(ang_deg)))
        P.append({"type":"circle","cx":gx,"cy":gy,"r":2,"color":GOLD,"outline":OUT,"outline_w":1})
    # blue energy core
    P.append({"type":"circle","cx":128,"cy":128,"r":3,"color":BLUE_GLOW})
    # gold waist band
    P.append({"type":"rect","x":100,"y":160,"w":56,"h":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Arms (BALL-JOINTED -- THE feature, obvious joints) ---
    # upper arms
    P.append({"type":"rect","x":86,"y":108,"w":14,"h":24,"color":PORCELAIN,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":156,"y":108,"w":14,"h":24,"color":PORCELAIN,"outline":OUT,"outline_w":1,"radius":3})
    # BALL JOINTS (elbows -- big obvious spherical joints)
    P.append({"type":"circle","cx":93,"cy":134,"r":7,"color":STEEL,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":163,"cy":134,"r":7,"color":STEEL,"outline":OUT,"outline_w":2})
    # gold joint bands
    P.append({"type":"circle","cx":93,"cy":134,"r":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":163,"cy":134,"r":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # lower arms
    P.append({"type":"rect","x":87,"y":140,"w":12,"h":20,"color":PORCELAIN,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":157,"y":140,"w":12,"h":20,"color":PORCELAIN,"outline":OUT,"outline_w":1,"radius":2})
    # DETACHED FLOATING HANDS (THE missing feature -- hands not connected)
    P.append({"type":"circle","cx":93,"cy":168,"r":6,"color":PORCELAIN,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":163,"cy":168,"r":6,"color":PORCELAIN,"outline":OUT,"outline_w":2})
    # gold wrist bands on floating hands
    P.append({"type":"circle","cx":93,"cy":168,"r":3,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":163,"cy":168,"r":3,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold shoulder joints
    P.append({"type":"circle","cx":93,"cy":110,"r":7,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":163,"cy":110,"r":7,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})

    # --- Head (porcelain doll face) ---
    P.append({"type":"circle","cx":128,"cy":76,"r":22,"color":PORCELAIN,"outline":OUT,"outline_w":2})
    # porcelain face plate (slightly darker)
    P.append({"type":"circle","cx":128,"cy":78,"r":18,"color":PORCELAIN_DARK,"outline":OUT,"outline_w":1})
    # mechanical blue eyes
    P.append({"type":"circle","cx":120,"cy":76,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":136,"cy":76,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":120,"cy":76,"r":2,"color":BLUE_GLOW})
    P.append({"type":"circle","cx":136,"cy":76,"r":2,"color":BLUE_GLOW})
    # porcelain doll lips (small, blue-ish)
    P.append({"type":"line","start":[122,88],"end":[134,88],"color":BLUE,"width":2})
    # gold hairband / headpiece
    P.append({"type":"rect","x":108,"y":58,"w":40,"h":6,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # key socket on head (wind-up point)
    P.append({"type":"circle","cx":128,"cy":56,"r":4,"color":GOLD_DARK,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Shaco -- demon jester, JESTER HAT WITH BELLS
# ============================================================================
def shaco_prims():
    P = []
    PURPLE = (120, 50, 150)       # jester purple
    PURPLE_DARK = (80, 30, 110)
    RED = (180, 40, 50)           # jester red
    RED_DARK = (130, 25, 35)
    WHITE = (235, 230, 225)       # white face paint
    BELL = (220, 180, 60)         # golden bells
    BELL_DARK = (160, 120, 30)
    EYE = (180, 30, 40)           # menacing red eyes
    DAGGER = (160, 165, 175)      # dagger blades
    DAGGER_DARK = (100, 105, 115)
    OUT = (20, 15, 25)

    # --- JESTER HAT WITH BELLS (THE feature -- HUGE, three-pointed) ---
    # hat base band
    P.append({"type":"rect","x":96,"y":52,"w":64,"h":10,"color":PURPLE,"outline":OUT,"outline_w":2})
    # THREE POINTED JESTER HORNES (big, sweeping -- THE icon, 40% of head)
    # left horn (red, drooping)
    P.append({"type":"polygon","points":[(96,56),(72,30),(68,24),(80,20),(100,50)],
              "color":RED,"outline":OUT,"outline_w":2})
    # left horn bell (golden, at tip)
    P.append({"type":"circle","cx":72,"cy":28,"r":6,"color":BELL,"outline":BELL_DARK,"outline_w":2})
    P.append({"type":"circle","cx":72,"cy":28,"r":3,"color":BELL_DARK})

    # center horn (purple, tall, pointing up)
    P.append({"type":"polygon","points":[(112,52),(128,12),(144,52)],
              "color":PURPLE,"outline":OUT,"outline_w":2})
    # center horn bell (golden, at tip)
    P.append({"type":"circle","cx":128,"cy":12,"r":7,"color":BELL,"outline":BELL_DARK,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":12,"r":3,"color":BELL_DARK})

    # right horn (red, drooping, mirrored)
    P.append({"type":"polygon","points":[(160,56),(184,30),(188,24),(176,20),(156,50)],
              "color":RED,"outline":OUT,"outline_w":2})
    # right horn bell
    P.append({"type":"circle","cx":184,"cy":28,"r":6,"color":BELL,"outline":BELL_DARK,"outline_w":2})
    P.append({"type":"circle","cx":184,"cy":28,"r":3,"color":BELL_DARK})

    # hat band trim (gold)
    P.append({"type":"rect","x":96,"y":60,"w":64,"h":4,"color":BELL,"outline":BELL_DARK,"outline_w":1})

    # --- Body (jester outfit, purple/red diamond pattern) ---
    P.append({"type":"polygon","points":[(100,100),(156,100),(160,180),(96,180)],
              "color":PURPLE,"outline":OUT,"outline_w":2})
    # red diamond patterns (jester motley)
    for dy in (112, 132, 152):
        P.append({"type":"polygon","points":[(120,dy),(128,dy-6),(136,dy),(128,dy+6)],
                  "color":RED,"outline":OUT,"outline_w":1})
    # white collar (ruff)
    P.append({"type":"polygon","points":[(100,100),(156,100),(152,108),(104,108)],
              "color":WHITE,"outline":OUT,"outline_w":1})

    # --- Legs (slender, jester tights) ---
    P.append({"type":"rect","x":106,"y":178,"w":16,"h":28,"color":RED,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":134,"y":178,"w":16,"h":28,"color":PURPLE,"outline":OUT,"outline_w":1,"radius":3})
    # POINTED SHOES (THE missing feature -- curled jester shoes)
    P.append({"type":"polygon","points":[(106,206),(122,206),(128,214),(106,214)],
              "color":PURPLE_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(134,206),(150,206),(128,214),(134,214)],
              "color":RED_DARK,"outline":OUT,"outline_w":2})
    # shoe bells
    P.append({"type":"circle","cx":128,"cy":214,"r":4,"color":BELL,"outline":BELL_DARK,"outline_w":1})

    # --- Arms (slender, dual daggers) ---
    P.append({"type":"rect","x":84,"y":108,"w":14,"h":48,"color":PURPLE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":158,"y":108,"w":14,"h":48,"color":RED,"outline":OUT,"outline_w":1,"radius":4})
    # DAGGERS (THE weapon -- dual, one in each hand)
    # left dagger
    P.append({"type":"polygon","points":[(88,156),(94,156),(91,186)],
              "color":DAGGER,"outline":OUT,"outline_w":2})
    P.append({"type":"rect","x":86,"y":150,"w":10,"h":6,"color":BELL_DARK,"outline":OUT,"outline_w":1})
    # right dagger
    P.append({"type":"polygon","points":[(162,156),(168,156),(165,186)],
              "color":DAGGER,"outline":OUT,"outline_w":2})
    P.append({"type":"rect","x":160,"y":150,"w":10,"h":6,"color":BELL_DARK,"outline":OUT,"outline_w":1})

    # --- Head (white painted face, menacing smile) ---
    P.append({"type":"circle","cx":128,"cy":76,"r":22,"color":WHITE,"outline":OUT,"outline_w":2})
    # menacing red eyes (glowing)
    P.append({"type":"circle","cx":120,"cy":74,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":136,"cy":74,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":120,"cy":74,"r":2,"color":(255,120,120)})
    P.append({"type":"circle","cx":136,"cy":74,"r":2,"color":(255,120,120)})
    # MENACING PAINTED SMILE (THE feature #2 -- big, wide, creepy)
    P.append({"type":"line","start":[112,86],"end":[120,90],"color":OUT,"width":2})
    P.append({"type":"line","start":[120,90],"end":[136,90],"color":OUT,"width":2})
    P.append({"type":"line","start":[136,90],"end":[144,86],"color":OUT,"width":2})
    # smile paint (red, wide)
    P.append({"type":"polygon","points":[(112,86),(144,86),(140,92),(116,92)],
              "color":RED,"outline":OUT,"outline_w":1})
    # eye paint marks (jester face paint)
    P.append({"type":"line","start":[114,68],"end":[126,68],"color":OUT,"width":1})
    P.append({"type":"line","start":[130,68],"end":[142,68],"color":OUT,"width":1})
    return P


# ============================================================================
# Shen -- eye of twilight, KINKOU MASK + shoulder guards
# ============================================================================
def shen_prims():
    P = []
    RED = (160, 40, 45)           # red ninja attire
    RED_DARK = (110, 25, 30)
    BLACK = (30, 25, 30)          # black ninja
    BLACK_DARK = (20, 15, 20)
    WHITE = (235, 230, 225)       # white mask
    MASK_DARK = (180, 175, 170)
    GOLD = (200, 165, 70)         # gold accents
    GOLD_DARK = (140, 110, 40)
    STEEL = (150, 155, 165)       # spirit blade
    STEEL_GLOW = (180, 200, 220)
    EYE = (60, 100, 160)          # blue eyes behind mask
    OUT = (15, 12, 18)

    # --- SPIRIT BLADE (behind, glowing) ---
    P.append({"type":"rect","x":196,"y":80,"w":8,"h":120,"color":STEEL,"outline":OUT,"outline_w":2})
    # blade glow
    P.append({"type":"line","start":[200,80],"end":[200,200],"color":STEEL_GLOW,"width":1})
    # blade crossguard
    P.append({"type":"rect","x":188,"y":76,"w":24,"h":6,"color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # blade hilt
    P.append({"type":"rect","x":196,"y":200,"w":8,"h":16,"color":GOLD_DARK,"outline":OUT,"outline_w":1})

    # --- Flowing scarf (behind, red, flowing) ---
    P.append({"type":"polygon","points":[(88,90),(168,90),(176,110),(80,110)],
              "color":RED,"outline":OUT,"outline_w":1})
    # scarf flowing ends
    P.append({"type":"polygon","points":[(80,110),(72,140),(84,130)],"color":RED_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(176,110),(184,140),(172,130)],"color":RED_DARK,"outline":OUT,"outline_w":1})

    # --- Legs (ninja attire, black) ---
    P.append({"type":"rect","x":106,"y":170,"w":18,"h":42,"color":BLACK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":18,"h":42,"color":BLACK,"outline":OUT,"outline_w":1,"radius":3})
    # red leg wraps
    P.append({"type":"rect","x":106,"y":186,"w":18,"h":6,"color":RED_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":132,"y":186,"w":18,"h":6,"color":RED_DARK,"outline":OUT,"outline_w":1})
    # ninja boots
    P.append({"type":"rect","x":104,"y":206,"w":22,"h":10,"color":BLACK_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":206,"w":22,"h":10,"color":BLACK_DARK,"outline":OUT,"outline_w":1,"radius":2})

    # --- Torso (ninja attire, red/black) ---
    P.append({"type":"polygon","points":[(100,100),(156,100),(160,172),(96,172)],
              "color":RED,"outline":OUT,"outline_w":2})
    # black chest panel
    P.append({"type":"polygon","points":[(112,108),(144,108),(148,168),(108,168)],
              "color":BLACK,"outline":OUT,"outline_w":1})
    # gold chest emblem (Kinkou symbol)
    P.append({"type":"circle","cx":128,"cy":130,"r":8,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":130,"r":4,"color":GOLD_DARK})
    # gold belt
    P.append({"type":"rect","x":96,"y":160,"w":64,"h":6,"color":GOLD_DARK,"outline":OUT,"outline_w":1})

    # --- LARGE SHOULDER GUARDS (THE feature #2 -- big, obvious) ---
    # left shoulder guard (big, red with gold trim)
    P.append({"type":"ellipse","x":72,"y":96,"w":30,"h":24,"color":RED_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"ellipse","x":76,"y":98,"w":22,"h":18,"color":RED,"outline":OUT,"outline_w":1})
    # gold trim on left guard
    P.append({"type":"line","start":[76,106],"end":[98,106],"color":GOLD,"width":2})
    # right shoulder guard
    P.append({"type":"ellipse","x":154,"y":96,"w":30,"h":24,"color":RED_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"ellipse","x":158,"y":98,"w":22,"h":18,"color":RED,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[158,106],"end":[180,106],"color":GOLD,"width":2})

    # --- Arms (ninja, with gauntlets) ---
    P.append({"type":"rect","x":82,"y":118,"w":16,"h":44,"color":BLACK,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":158,"y":118,"w":16,"h":44,"color":BLACK,"outline":OUT,"outline_w":1,"radius":4})
    # gold gauntlet bracers
    P.append({"type":"rect","x":82,"y":150,"w":16,"h":8,"color":GOLD_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":158,"y":150,"w":16,"h":8,"color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # hands
    P.append({"type":"circle","cx":90,"cy":166,"r":5,"color":(200,180,160),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":166,"cy":166,"r":5,"color":(200,180,160),"outline":OUT,"outline_w":1})

    # --- KINKOU MASK (THE feature -- BIG, covers eyes, white with blue) ---
    # mask base (big, covers upper face)
    P.append({"type":"polygon","points":[(104,60),(152,60),(156,86),(100,86)],
              "color":WHITE,"outline":OUT,"outline_w":3})
    # mask eye area (dark band across eyes)
    P.append({"type":"rect","x":100,"y":68,"w":56,"h":12,"color":MASK_DARK,"outline":OUT,"outline_w":2})
    # blue eyes glowing through mask (THE icon)
    P.append({"type":"circle","cx":118,"cy":74,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":138,"cy":74,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":118,"cy":74,"r":2,"color":(120,180,240)})
    P.append({"type":"circle","cx":138,"cy":74,"r":2,"color":(120,180,240)})
    # mask center line (Kinkou design)
    P.append({"type":"line","start":[128,60],"end":[128,86],"color":OUT,"width":1})
    # mask side extensions (wrapping around head)
    P.append({"type":"polygon","points":[(104,66),(96,72),(100,82)],"color":MASK_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(152,66),(160,72),(156,82)],"color":MASK_DARK,"outline":OUT,"outline_w":2})
    # gold mask trim
    P.append({"type":"line","start":[104,60],"end":[152,60],"color":GOLD,"width":2})
    # head top (dark hair above mask)
    P.append({"type":"polygon","points":[(108,60),(148,60),(144,48),(128,42),(112,48)],
              "color":BLACK,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# TahmKench -- river king, MASSIVE WIDE MOUTH
# ============================================================================
def tahm_kench_prims():
    P = []
    SKIN = (80, 130, 70)         # green skin (catfish-frog)
    SKIN_DARK = (55, 95, 50)
    SKIN_LIGHT = (110, 160, 90)
    BELLY = (180, 170, 130)      # tan belly/waistcoat
    GOLD = (210, 175, 70)        # golden jewelry
    GOLD_DARK = (150, 115, 40)
    MOUTH = (40, 20, 25)         # dark mouth interior
    MOUTH_RED = (130, 30, 35)    # red mouth
    TONGUE = (200, 100, 120)     # pink tongue
    TONGUE_DARK = (160, 70, 90)
    WAISTCOAT = (90, 60, 50)     # brown formal waistcoat
    WAISTCOAT_DARK = (60, 40, 35)
    EYE = (240, 220, 80)         # yellow bulbous eyes
    EYE_PUPIL = (20, 15, 10)
    TOOTH = (240, 235, 220)      # white teeth
    OUT = (15, 25, 15)

    # --- MASSIVE WIDE MOUTH (THE feature -- HUGE, gaping, dominates face) ---
    # mouth interior (big, dark red, 50% of face area)
    P.append({"type":"ellipse","x":84,"y":72,"w":88,"h":44,"color":MOUTH_RED,"outline":OUT,"outline_w":3})
    # mouth interior dark
    P.append({"type":"ellipse","x":92,"y":78,"w":72,"h":32,"color":MOUTH,"outline":OUT,"outline_w":1})
    # TEETH (top row -- big, white, pointed)
    for tx in (96, 108, 120, 132, 144, 156):
        P.append({"type":"polygon","points":[(tx-4,76),(tx+4,76),(tx,84)],
                  "color":TOOTH,"outline":OUT,"outline_w":1})
    # TEETH (bottom row -- pointing up)
    for tx in (100, 112, 124, 136, 148):
        P.append({"type":"polygon","points":[(tx-4,112),(tx+4,112),(tx,104)],
                  "color":TOOTH,"outline":OUT,"outline_w":1})
    # fangs (big, at corners of mouth)
    P.append({"type":"polygon","points":[(88,76),(96,76),(90,90)],"color":TOOTH,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(160,76),(168,76),(166,90)],"color":TOOTH,"outline":OUT,"outline_w":2})

    # --- LONG PREHENSILE TONGUE (THE feature #2 -- extending out) ---
    # tongue (big, pink, curling out from mouth)
    P.append({"type":"polygon","points":[(120,100),(108,110),(96,120),(88,130),(84,140),(92,142),(104,132),(116,122),(126,112)],
              "color":TONGUE,"outline":OUT,"outline_w":2})
    # tongue texture (darker stripe)
    P.append({"type":"line","start":[120,100],"end":[88,138],"color":TONGUE_DARK,"width":2})
    # tongue tip
    P.append({"type":"circle","cx":88,"cy":140,"r":5,"color":TONGUE,"outline":OUT,"outline_w":1})

    # --- Head (big, wide, catfish-frog) ---
    P.append({"type":"circle","cx":128,"cy":80,"r":36,"color":SKIN,"outline":OUT,"outline_w":2})
    # head shading (darker green on sides)
    P.append({"type":"circle","cx":128,"cy":84,"r":30,"color":SKIN_DARK,"outline":OUT,"outline_w":1})

    # re-draw mouth on top of head (so it's on the face)
    P.append({"type":"ellipse","x":84,"y":72,"w":88,"h":44,"color":MOUTH_RED,"outline":OUT,"outline_w":3})
    P.append({"type":"ellipse","x":92,"y":78,"w":72,"h":32,"color":MOUTH,"outline":OUT,"outline_w":1})
    # teeth top
    for tx in (96, 108, 120, 132, 144, 156):
        P.append({"type":"polygon","points":[(tx-4,76),(tx+4,76),(tx,84)],
                  "color":TOOTH,"outline":OUT,"outline_w":1})
    # teeth bottom
    for tx in (100, 112, 124, 136, 148):
        P.append({"type":"polygon","points":[(tx-4,112),(tx+4,112),(tx,104)],
                  "color":TOOTH,"outline":OUT,"outline_w":1})
    # fangs
    P.append({"type":"polygon","points":[(88,76),(96,76),(90,90)],"color":TOOTH,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(160,76),(168,76),(166,90)],"color":TOOTH,"outline":OUT,"outline_w":2})
    # tongue on top
    P.append({"type":"polygon","points":[(120,100),(108,110),(96,120),(88,130),(84,140),(92,142),(104,132),(116,122),(126,112)],
              "color":TONGUE,"outline":OUT,"outline_w":2})
    P.append({"type":"line","start":[120,100],"end":[88,138],"color":TONGUE_DARK,"width":2})
    P.append({"type":"circle","cx":88,"cy":140,"r":5,"color":TONGUE,"outline":OUT,"outline_w":1})

    # --- BULBOUS EYES (THE feature #3 -- big, yellow, on sides of head) ---
    # left eye (bulging, yellow)
    P.append({"type":"circle","cx":96,"cy":56,"r":12,"color":EYE,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":96,"cy":56,"r":6,"color":EYE_PUPIL,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":94,"cy":54,"r":2,"color":(255,255,240)})
    # right eye
    P.append({"type":"circle","cx":160,"cy":56,"r":12,"color":EYE,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":160,"cy":56,"r":6,"color":EYE_PUPIL,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":158,"cy":54,"r":2,"color":(255,255,240)})

    # --- Body (obese, big belly, waistcoat) ---
    P.append({"type":"ellipse","x":76,"y":120,"w":104,"h":100,"color":SKIN,"outline":OUT,"outline_w":2})
    # big belly (lighter)
    P.append({"type":"ellipse","x":88,"y":140,"w":80,"h":76,"color":SKIN_LIGHT,"outline":OUT,"outline_w":1})
    # FORMAL WAISTCOAT (THE missing feature -- brown vest with gold buttons)
    P.append({"type":"polygon","points":[(92,128),(164,128),(168,210),(88,210)],
              "color":WAISTCOAT,"outline":OUT,"outline_w":2})
    # waistcoat lapels
    P.append({"type":"polygon","points":[(92,128),(120,128),(116,160),(100,150)],
              "color":WAISTCOAT_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(164,128),(136,128),(140,160),(156,150)],
              "color":WAISTCOAT_DARK,"outline":OUT,"outline_w":1})
    # gold buttons down the front
    for by in (140, 160, 180, 200):
        P.append({"type":"circle","cx":128,"cy":by,"r":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- GOLDEN JEWELRY (THE missing feature -- rings, gold chain) ---
    # gold chain around neck
    P.append({"type":"ellipse","x":96,"y":112,"w":64,"h":12,"color":GOLD,"outline":GOLD_DARK,"outline_w":2})
    # gold rings on fingers (visible at sides)
    P.append({"type":"circle","cx":84,"cy":190,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":172,"cy":190,"r":5,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    # gold earring/cuff
    P.append({"type":"circle","cx":86,"cy":62,"r":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":170,"cy":62,"r":4,"color":GOLD,"outline":GOLD_DARK,"outline_w":1})

    # --- Arms (stubby, green) ---
    P.append({"type":"ellipse","x":64,"y":160,"w":24,"h":40,"color":SKIN_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"ellipse","x":168,"y":160,"w":24,"h":40,"color":SKIN_DARK,"outline":OUT,"outline_w":2})
    # hands with gold rings
    P.append({"type":"circle","cx":76,"cy":196,"r":8,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":180,"cy":196,"r":8,"color":SKIN,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# RUN
# ============================================================================
if __name__ == "__main__":
    results = []
    for name, fn in [("Nautilus", nautilus_prims), ("Neeko", neeko_prims),
                     ("Orianna", orianna_prims), ("Shaco", shaco_prims),
                     ("Shen", shen_prims), ("TahmKench", tahm_kench_prims)]:
        prims = fn()
        r = improve(name, prims, gate_n=3)
        print(f"RESULT: {r}")
        results.append(r)
    print("\n=== BATCH 23 SUMMARY ===")
    for r in results:
        print(f"  {r['id']}: {r['old']} -> {r['new']} saved={r['saved']} missing={r['missing'][:3]}")
