"""Batch 6 hand-authored sprites: Gwen, Hecarim, Hwei, Illaoi, Janna, Jhin.

Each champion gets ONE huge signature feature that dominates the silhouette:
- Gwen    -> OVERSIZED GOLDEN SCISSORS (huge, the doll's shears)
- Hecarim -> SPECTRAL CENTAUR body (horse lower half, ghostly teal glow)
- Hwei    -> FLOATING PAINT PALETTE (big, beside him) + ink brush
- Illaoi  -> LARGE GOLDEN IDOL (Nagakabouros, big tentacle statue beside her)
- Janna   -> WIND SWIRLS / cyclone (visible wind around her, floating)
- Jhin    -> WHITE PORCELAIN MASK (face is a mask) + wide hat + cape + pistol
"""
import sys; sys.path.insert(0, "exp")
from champ_improver import improve


# ============================================================================
# Gwen -- the doll; HUGE golden scissors + blue doll hair + stitched seams
# ============================================================================
def gwen_prims():
    P = []
    SKIN = (245, 220, 205)
    HAIR = (90, 130, 200)
    HAIR_DARK = (55, 90, 160)
    DRESS = (240, 240, 245)
    DRESS_BLUE = (90, 130, 200)
    GOLD = (225, 185, 65)
    GOLD_DARK = (160, 120, 30)
    STEEL = (200, 200, 210)
    STEEL_DARK = (120, 120, 135)
    SEAM = (180, 120, 140)
    EYE = (60, 100, 180)
    OUT = (35, 30, 40)
    GLOW = (255, 240, 200)

    # --- Hallowed aura glow (behind) ---
    P.append({"type":"circle","cx":128,"cy":120,"r":60,"color":(255,245,210),"outline":GLOW,"outline_w":1})

    # --- Hair (blue, doll-like, big) ---
    P.append({"type":"circle","cx":128,"cy":66,"r":22,"color":HAIR,"outline":OUT,"outline_w":1})
    # hair side locks (doll-like, blunt cut)
    P.append({"type":"polygon","points":[(108,60),(120,60),(116,100),(104,90)],"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(136,60),(148,60),(152,90),(140,100)],"color":HAIR,"outline":OUT,"outline_w":1})
    # bangs (blunt, doll-like)
    P.append({"type":"polygon","points":[(108,58),(148,58),(144,74),(112,74)],"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (doll, round, big eyes) ---
    P.append({"type":"circle","cx":128,"cy":74,"r":18,"color":SKIN,"outline":OUT,"outline_w":1})
    # big blue doll eyes
    P.append({"type":"circle","cx":121,"cy":76,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":76,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":75,"r":2,"color":(255,255,255)})
    P.append({"type":"circle","cx":136,"cy":75,"r":2,"color":(255,255,255)})
    # small doll mouth
    P.append({"type":"line","start":[123,86],"end":[133,86],"color":(180,100,120),"width":1})
    # stitched seam on cheek (THE doll feature)
    P.append({"type":"line","start":[112,80],"end":[112,90],"color":SEAM,"width":1})
    for sy in (81, 84, 87):
        P.append({"type":"line","start":[110,sy],"end":[114,sy],"color":SEAM,"width":1})

    # --- Frilly gothic lolita dress (white + blue trim) ---
    P.append({"type":"polygon","points":[(104,96),(152,96),(168,180),(88,180)],
              "color":DRESS,"outline":OUT,"outline_w":1})
    # blue trim bands (frilly)
    P.append({"type":"rect","x":90,"y":120,"w":76,"h":6,"color":DRESS_BLUE,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":88,"y":150,"w":80,"h":6,"color":DRESS_BLUE,"outline":OUT,"outline_w":1})
    # frilly hem (scalloped bottom)
    for hx in (96, 112, 128, 144, 160):
        P.append({"type":"circle","cx":hx,"cy":180,"r":8,"color":DRESS,"outline":OUT,"outline_w":1})
    # gold center trim
    P.append({"type":"line","start":[128,96],"end":[128,180],"color":GOLD,"width":2})
    # stitched seams on dress (THE doll feature)
    P.append({"type":"line","start":[110,100],"end":[110,170],"color":SEAM,"width":1})
    for sy in (108, 120, 132, 144, 156, 168):
        P.append({"type":"line","start":[108,sy],"end":[112,sy],"color":SEAM,"width":1})

    # --- Arms ---
    P.append({"type":"rect","x":92,"y":104,"w":12,"h":44,"color":DRESS,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":152,"y":104,"w":12,"h":44,"color":DRESS,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":98,"cy":150,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":158,"cy":150,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs + boots ---
    P.append({"type":"rect","x":110,"y":180,"w":14,"h":34,"color":SKIN,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":180,"w":14,"h":34,"color":SKIN,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":108,"y":210,"w":18,"h":12,"color":DRESS_BLUE,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":210,"w":18,"h":12,"color":DRESS_BLUE,"outline":OUT,"outline_w":1,"radius":2})

    # --- HUGE GOLDEN SCISSORS (THE feature -- drawn LAST, IN FRONT, ENORMOUS) ---
    # Two big golden blades crossing, with steel cutting edges + gold handles
    # left blade (diagonal, big)
    P.append({"type":"polygon","points":[(86,200),(110,200),(180,40),(168,32),(78,192)],
              "color":GOLD,"outline":OUT,"outline_w":2})
    # steel cutting edge on left blade
    P.append({"type":"polygon","points":[(86,200),(100,196),(170,40),(162,36),(80,190)],
              "color":STEEL,"outline":OUT,"outline_w":1})
    # right blade (diagonal, big, crossing)
    P.append({"type":"polygon","points":[(146,200),(170,200),(180,40),(168,32),(156,192)],
              "color":GOLD,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(146,200),(160,196),(170,40),(162,36),(154,190)],
              "color":STEEL,"outline":OUT,"outline_w":1})
    # center pivot (gold, prominent)
    P.append({"type":"circle","cx":128,"cy":116,"r":7,"color":GOLD,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":128,"cy":116,"r":3,"color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # big golden handle loops (bottom, the scissor rings)
    P.append({"type":"circle","cx":92,"cy":212,"r":12,"color":GOLD,"outline":OUT,"outline_w":3})
    P.append({"type":"circle","cx":92,"cy":212,"r":6,"color":OUT,"outline":GOLD,"outline_w":1})
    P.append({"type":"circle","cx":164,"cy":212,"r":12,"color":GOLD,"outline":OUT,"outline_w":3})
    P.append({"type":"circle","cx":164,"cy":212,"r":6,"color":OUT,"outline":GOLD,"outline_w":1})
    return P


# ============================================================================
# Hecarim -- spectral centaur; horse lower half + ghostly teal glow + trident
# ============================================================================
def hecarim_prims():
    P = []
    SPECTRAL = (90, 200, 200)    # spectral teal glow
    SPECTRAL_DARK = (50, 140, 150)
    SPECTRAL_LIGHT = (160, 230, 230)
    GHOST = (120, 180, 160)      # ghostly body (teal-green-grey, like committed)
    GHOST_DARK = (70, 120, 100)
    BONE = (220, 215, 200)       # skeletal features
    BONE_DARK = (140, 135, 120)
    ARMOR = (45, 70, 80)         # heavy plate armor (dark, like committed)
    ARMOR_DARK = (30, 50, 60)
    ARMOR_LIGHT = (75, 100, 110)
    STEEL = (110, 130, 140)
    GOLD = (215, 175, 60)
    TUSK = (235, 230, 215)
    EYE = (120, 255, 240)        # glowing teal eyes
    OUT = (20, 30, 35)

    # --- Spectral teal glow wisps (minimal, just around hooves -- keep silhouette clean) ---
    P.append({"type":"circle","cx":60,"cy":238,"r":6,"color":SPECTRAL,"outline":SPECTRAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":76,"cy":238,"r":6,"color":SPECTRAL,"outline":SPECTRAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":200,"cy":238,"r":6,"color":SPECTRAL,"outline":SPECTRAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":216,"cy":238,"r":6,"color":SPECTRAL,"outline":SPECTRAL_DARK,"outline_w":1})

    # --- CENTAUR BODY (horse lower half -- THE feature, big, clearly horse-shaped) ---
    # horse body (big rounded mass, low center, ghostly -- WIDE so it reads as horse)
    P.append({"type":"ellipse","x":36,"y":150,"w":184,"h":82,"color":GHOST,"outline":OUT,"outline_w":2})
    # horse chest (front, right -- big, rounded)
    P.append({"type":"circle","cx":210,"cy":176,"r":32,"color":GHOST,"outline":OUT,"outline_w":2})
    # horse rump (back, left -- big, rounded)
    P.append({"type":"circle","cx":50,"cy":176,"r":34,"color":GHOST,"outline":OUT,"outline_w":2})
    # horse legs (4, ghostly, skeletal-ish -- SPREAD so the horse body reads)
    # FRONT legs (right side, under chest -- close together like a horse)
    for lx in (190, 206):
        P.append({"type":"rect","x":lx,"y":200,"w":18,"h":28,"color":GHOST_DARK,"outline":OUT,"outline_w":1,"radius":3})
        P.append({"type":"rect","x":lx-2,"y":222,"w":22,"h":10,"color":SPECTRAL_DARK,"outline":SPECTRAL,"outline_w":1,"radius":2})
    # BACK legs (left side, under rump -- close together like a horse)
    for lx in (50, 66):
        P.append({"type":"rect","x":lx,"y":200,"w":18,"h":28,"color":GHOST_DARK,"outline":OUT,"outline_w":1,"radius":3})
        P.append({"type":"rect","x":lx-2,"y":222,"w":22,"h":10,"color":SPECTRAL_DARK,"outline":SPECTRAL,"outline_w":1,"radius":2})
    # spectral glow wisps from hooves (THE ghost feature -- wisps trailing down)
    for lx in (60, 76, 200, 216):
        P.append({"type":"circle","cx":lx,"cy":238,"r":6,"color":SPECTRAL,"outline":SPECTRAL_DARK,"outline_w":1})
        P.append({"type":"circle","cx":lx,"cy":246,"r":4,"color":SPECTRAL_LIGHT,"outline":SPECTRAL_DARK,"outline_w":1})

    # --- Horse neck + head (front, LEFT -- clearly horse, skull-like, undead) ---
    # horse neck (rising from chest, angled LEFT -- BIG and clearly horse neck)
    P.append({"type":"polygon","points":[(20,170),(60,170),(56,100),(24,112)],
              "color":GHOST,"outline":OUT,"outline_w":2})
    # horse head (elongated, skull-like -- BIG, clearly a horse head, pointing LEFT)
    P.append({"type":"ellipse","x":-4,"y":92,"w":44,"h":34,"color":GHOST,"outline":OUT,"outline_w":2})
    # elongated muzzle (skeletal, pointing left)
    P.append({"type":"ellipse","x":-12,"y":104,"w":24,"h":22,"color":GHOST_DARK,"outline":OUT,"outline_w":1})
    # skeletal jaw teeth (THE undead feature)
    for tx in (2, 8):
        P.append({"type":"polygon","points":[(tx,114),(tx+3,114),(tx+1,120)],"color":BONE,"outline":OUT,"outline_w":1})
    # glowing teal eye (undead -- BIG)
    P.append({"type":"circle","cx":18,"cy":102,"r":6,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":18,"cy":102,"r":3,"color":(255,255,255)})
    # horse ear (pointed, skeletal)
    P.append({"type":"polygon","points":[(24,88),(30,72),(36,90)],"color":GHOST_DARK,"outline":OUT,"outline_w":1})
    # ghostly mane (flowing, spectral teal, BIG along neck -- THE missing feature)
    for mx, my in [(40,110),(48,100),(56,106)]:
        P.append({"type":"polygon","points":[(mx-5,my+10),(mx,my-10),(mx+5,my+10)],
                  "color":SPECTRAL,"outline":SPECTRAL_DARK,"outline_w":1})
    # extra flowing mane wisps (long, trailing back -- THE ghostly mane)
    P.append({"type":"polygon","points":[(56,110),(72,100),(76,140),(56,128)],"color":SPECTRAL,"outline":SPECTRAL_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(60,114),(80,110),(84,150),(60,134)],"color":SPECTRAL_LIGHT,"outline":SPECTRAL_DARK,"outline_w":1})

    # --- Heavy plate armor on horse body (THE missing feature -- BIG plates) ---
    P.append({"type":"ellipse","x":72,"y":146,"w":120,"h":30,"color":ARMOR,"outline":OUT,"outline_w":2})
    # armor studs (BIG, obvious)
    for sx in (88, 108, 128, 148, 168):
        P.append({"type":"circle","cx":sx,"cy":158,"r":5,"color":STEEL,"outline":OUT,"outline_w":1})
    # spectral glow trim on armor (top + bottom edges)
    P.append({"type":"rect","x":72,"y":142,"w":120,"h":5,"color":SPECTRAL,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":72,"y":170,"w":120,"h":5,"color":SPECTRAL,"outline":OUT,"outline_w":1})

    # --- Rider torso (upper half -- raised ABOVE the horse body, clearly human torso) ---
    # rider torso positioned higher so the human half is clearly separate from horse
    P.append({"type":"polygon","points":[(108,84),(148,84),(152,140),(104,140)],
              "color":ARMOR,"outline":OUT,"outline_w":1})
    # heavy chest plate (BIG, obvious)
    P.append({"type":"polygon","points":[(112,88),(144,88),(142,130),(114,130)],
              "color":ARMOR_DARK,"outline":OUT,"outline_w":2})
    P.append({"type":"line","start":[128,88],"end":[128,130],"color":STEEL,"width":2})
    # armor plate segments (horizontal bands -- heavy plate armor)
    for py in (100, 112, 124):
        P.append({"type":"line","start":[114,py],"end":[142,py],"color":STEEL,"width":1})
    # spectral glow on chest
    P.append({"type":"circle","cx":128,"cy":106,"r":6,"color":SPECTRAL,"outline":SPECTRAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":106,"r":3,"color":SPECTRAL_LIGHT})
    # gold trim on armor
    P.append({"type":"line","start":[112,88],"end":[144,88],"color":GOLD,"width":2})

    # --- Rider head (skull-like, undead -- raised, clearly human head above torso) ---
    P.append({"type":"circle","cx":128,"cy":68,"r":16,"color":GHOST,"outline":OUT,"outline_w":1})
    # skeletal face (bone-colored, lower jaw)
    P.append({"type":"polygon","points":[(116,72),(140,72),(136,90),(120,90)],
              "color":BONE,"outline":OUT,"outline_w":1})
    # glowing teal eyes (undead -- BIG)
    P.append({"type":"circle","cx":121,"cy":70,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":70,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":69,"r":2,"color":(255,255,255)})
    P.append({"type":"circle","cx":136,"cy":69,"r":2,"color":(255,255,255)})
    # skeletal jaw teeth (THE undead feature)
    for tx in (120, 126, 132, 138):
        P.append({"type":"polygon","points":[(tx,86),(tx+3,86),(tx+1,92)],"color":BONE,"outline":OUT,"outline_w":1})
    # skeletal nose hole (undead skull)
    P.append({"type":"circle","cx":128,"cy":80,"r":2,"color":OUT,"outline":BONE_DARK,"outline_w":1})
    # ghostly flowing mane (rider, spectral teal -- flowing back from head)
    P.append({"type":"polygon","points":[(110,58),(96,44),(90,84),(108,78)],"color":SPECTRAL,"outline":SPECTRAL_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(146,58),(160,44),(166,84),(148,78)],"color":SPECTRAL,"outline":SPECTRAL_DARK,"outline_w":1})

    # --- Rider arms (raised, one holding trident) ---
    P.append({"type":"rect","x":90,"y":92,"w":14,"h":44,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":152,"y":92,"w":14,"h":44,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":4})
    # gold shoulder pads
    P.append({"type":"circle","cx":97,"cy":96,"r":8,"color":ARMOR_LIGHT,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":159,"cy":96,"r":8,"color":ARMOR_LIGHT,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":97,"cy":138,"r":5,"color":GHOST,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":159,"cy":138,"r":5,"color":GHOST,"outline":OUT,"outline_w":1})

    # --- Massive polearm / trident (ghostly, in right hand, BIG, drawn LAST IN FRONT) ---
    P.append({"type":"line","start":[159,138],"end":[230,30],"color":ARMOR_DARK,"width":7})
    # trident head (3 prongs, spectral, BIG)
    P.append({"type":"line","start":[230,30],"end":[214,6],"color":STEEL,"width":5})
    P.append({"type":"line","start":[230,30],"end":[230,2],"color":STEEL,"width":5})
    P.append({"type":"line","start":[230,30],"end":[246,6],"color":STEEL,"width":5})
    # prong tips (sharp)
    P.append({"type":"circle","cx":214,"cy":6,"r":3,"color":STEEL,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":230,"cy":2,"r":3,"color":STEEL,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":246,"cy":6,"r":3,"color":STEEL,"outline":OUT,"outline_w":1})
    # spectral glow on trident (THE ghost feature)
    P.append({"type":"circle","cx":230,"cy":18,"r":10,"color":SPECTRAL,"outline":SPECTRAL_DARK,"outline_w":1})
    P.append({"type":"circle","cx":230,"cy":18,"r":5,"color":SPECTRAL_LIGHT})
    # gold band on polearm
    P.append({"type":"rect","x":200,"y":80,"w":10,"h":8,"color":GOLD,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Hwei -- ink mage; FLOATING PAINT PALETTE (big) + ink brush + Ionian robes
# ============================================================================
def hwei_prims():
    P = []
    SKIN = (230, 205, 180)
    HAIR = (40, 35, 50)         # dark hair
    HAIR_LIGHT = (80, 70, 90)
    ROBE = (50, 60, 100)        # deep blue Ionian robes
    ROBE_LIGHT = (80, 95, 140)
    ROBE_DARK = (30, 40, 70)
    GOLD = (215, 175, 60)
    INK = (25, 20, 35)          # ink black
    INK_BLUE = (40, 50, 90)
    PALETTE = (180, 140, 60)    # wooden paint palette (brown/tan)
    PALETTE_DARK = (130, 95, 40)
    PAINT_RED = (200, 60, 60)
    PAINT_BLUE = (60, 100, 180)
    PAINT_YELLOW = (220, 200, 80)
    PAINT_GREEN = (80, 160, 90)
    PAINT_WHITE = (245, 245, 240)
    BRUSH = (110, 80, 55)
    BRUSH_FERRULE = (180, 180, 190)
    EYE = (60, 50, 70)
    OUT = (25, 20, 30)

    # --- Flowing ink swirls behind (magical ink manifestations) ---
    P.append({"type":"circle","cx":60,"cy":120,"r":18,"color":INK_BLUE,"outline":INK,"outline_w":1})
    P.append({"type":"circle","cx":196,"cy":140,"r":16,"color":INK_BLUE,"outline":INK,"outline_w":1})
    P.append({"type":"circle","cx":50,"cy":160,"r":12,"color":INK,"outline":INK_BLUE,"outline_w":1})

    # --- Hair (dark, flowing) ---
    P.append({"type":"circle","cx":128,"cy":66,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    # hair flowing back (long, melancholic)
    P.append({"type":"polygon","points":[(110,60),(146,60),(160,90),(150,110),(100,110),(96,90)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # bangs
    P.append({"type":"polygon","points":[(110,58),(146,58),(142,74),(114,74)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (melancholic expression) ---
    P.append({"type":"circle","cx":128,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # melancholic eyes (half-closed, sad)
    P.append({"type":"line","start":[119,74],"end":[125,74],"color":EYE,"width":2})
    P.append({"type":"line","start":[131,74],"end":[137,74],"color":EYE,"width":2})
    # sad brows
    P.append({"type":"polygon","points":[(116,68),(126,70),(126,72),(116,70)],"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(130,70),(140,68),(140,70),(130,72)],"color":HAIR,"outline":OUT,"outline_w":1})
    # melancholic mouth (slight frown)
    P.append({"type":"line","start":[122,86],"end":[134,86],"color":(120,60,60),"width":1})

    # --- Flowing Ionian robes (deep blue) ---
    P.append({"type":"polygon","points":[(100,94),(156,94),(170,180),(86,180)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # robe folds (flowing)
    P.append({"type":"polygon","points":[(108,98),(148,98),(156,178),(100,178)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # gold trim on robe
    P.append({"type":"line","start":[100,94],"end":[156,94],"color":GOLD,"width":2})
    P.append({"type":"line","start":[86,180],"end":[170,180],"color":GOLD,"width":2})
    # gold center trim
    P.append({"type":"line","start":[128,94],"end":[128,180],"color":GOLD,"width":2})
    # robe sash (Ionian)
    P.append({"type":"polygon","points":[(96,130),(160,130),(150,150),(106,150)],
              "color":ROBE_LIGHT,"outline":OUT,"outline_w":1})

    # --- Arms (ink-stained hands) ---
    P.append({"type":"rect","x":88,"y":104,"w":14,"h":50,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":154,"y":104,"w":14,"h":50,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    # ink-stained hands (THE feature -- dark ink stains on hands)
    P.append({"type":"circle","cx":95,"cy":156,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":95,"cy":156,"r":3,"color":INK,"outline":OUT,"outline_w":1})  # ink stain
    P.append({"type":"circle","cx":161,"cy":156,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":161,"cy":156,"r":3,"color":INK,"outline":OUT,"outline_w":1})  # ink stain

    # --- Legs (robe-covered) ---
    P.append({"type":"rect","x":108,"y":180,"w":18,"h":30,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":180,"w":18,"h":30,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":106,"y":206,"w":22,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":206,"w":22,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})

    # --- FLOATING PAINT PALETTE (THE feature -- HUGE, beside him, in front) ---
    # big wooden palette (oval, with thumb hole -- ENORMOUS, dominates right side)
    P.append({"type":"ellipse","x":168,"y":70,"w":80,"h":60,"color":PALETTE,"outline":OUT,"outline_w":3})
    # palette thumb hole
    P.append({"type":"circle","cx":178,"cy":82,"r":7,"color":OUT,"outline":PALETTE_DARK,"outline_w":1})
    # paint blobs on palette (colorful -- BIG, the magic)
    P.append({"type":"circle","cx":196,"cy":88,"r":8,"color":PAINT_RED,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":216,"cy":92,"r":8,"color":PAINT_BLUE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":232,"cy":102,"r":7,"color":PAINT_YELLOW,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":212,"cy":112,"r":7,"color":PAINT_GREEN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":192,"cy":108,"r":6,"color":PAINT_WHITE,"outline":OUT,"outline_w":1})
    # magical glow around palette (ink magic -- BIG)
    P.append({"type":"ellipse","x":162,"y":64,"w":92,"h":72,"color":(120,100,160),"outline":(180,160,220),"outline_w":1})
    # floating ink magic wisps from palette (the magic manifestation)
    for sy in (60, 50, 40):
        P.append({"type":"circle","cx":200,"cy":sy,"r":5,"color":INK_BLUE,"outline":INK,"outline_w":1})

    # --- Paintbrush (in left hand, ink-stained) ---
    P.append({"type":"line","start":[95,156],"end":[60,100],"color":BRUSH,"width":4})
    # brush ferrule (metal)
    P.append({"type":"rect","x":58,"y":96,"w":8,"h":6,"color":BRUSH_FERRULE,"outline":OUT,"outline_w":1})
    # brush bristles (ink-tipped)
    P.append({"type":"polygon","points":[(54,96),(66,96),(60,82)],"color":BRUSH,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(56,90),(64,90),(60,80)],"color":INK,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Illaoi -- priestess; LARGE GOLDEN IDOL (Nagakabouros) + tentacles + tattoos
# ============================================================================
def illaoi_prims():
    P = []
    SKIN = (200, 165, 130)
    SKIN_DARK = (160, 125, 95)
    HAIR = (60, 45, 35)
    ROBE = (110, 70, 130)       # deep purple robes
    ROBE_DARK = (70, 45, 90)
    GOLD = (225, 185, 65)       # golden idol
    GOLD_DARK = (160, 120, 30)
    GOLD_LIGHT = (245, 215, 100)
    TENTACLE = (130, 90, 150)   # tentacles (purple)
    TENTACLE_DARK = (85, 55, 100)
    TATTOO = (90, 60, 110)      # tribal tattoos (purple ink)
    EYE = (60, 40, 30)
    OUT = (30, 25, 30)

    # --- LARGE GOLDEN IDOL (THE feature -- BIG, beside her, the icon) ---
    # idol base/pedestal
    P.append({"type":"rect","x":180,"y":170,"w":50,"h":20,"color":GOLD_DARK,"outline":OUT,"outline_w":2})
    # idol body (big golden statue, towering beside her)
    P.append({"type":"polygon","points":[(190,60),(220,60),(228,170),(182,170)],
              "color":GOLD,"outline":OUT,"outline_w":2})
    # idol head (skull-like, Nagakabouros)
    P.append({"type":"circle","cx":205,"cy":50,"r":16,"color":GOLD,"outline":OUT,"outline_w":2})
    # idol eye sockets (dark, menacing)
    P.append({"type":"circle","cx":199,"cy":50,"r":4,"color":OUT,"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":211,"cy":50,"r":4,"color":OUT,"outline":GOLD_DARK,"outline_w":1})
    # idol mouth (jagged, skull)
    P.append({"type":"polygon","points":[(199,58),(211,58),(209,64),(201,64)],"color":OUT,"outline":GOLD_DARK,"outline_w":1})
    # idol horns/spikes (Nagakabouros is spiky)
    P.append({"type":"polygon","points":[(192,40),(196,28),(200,42)],"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(210,42),(214,28),(218,40)],"color":GOLD,"outline":OUT,"outline_w":1})
    # gold shine on idol
    P.append({"type":"line","start":[194,70],"end":[194,160],"color":GOLD_LIGHT,"width":2})
    # idol gem (glowing)
    P.append({"type":"circle","cx":205,"cy":100,"r":6,"color":(180,60,180),"outline":GOLD_DARK,"outline_w":1})
    P.append({"type":"circle","cx":205,"cy":100,"r":3,"color":(255,180,255)})

    # --- GIANT TENTACLES (THE feature pair -- BIG, from idol, dominating) ---
    # tentacle 1 (left of idol, curling down -- BIG)
    t1 = [(195,170),(215,195),(205,220),(188,216)]
    for i in range(len(t1)-1):
        P.append({"type":"line","start":t1[i],"end":t1[i+1],"color":TENTACLE,"width":18})
    for cx, cy in t1:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":10,"color":TENTACLE,"outline":TENTACLE_DARK,"outline_w":1})
    # tentacle 2 (right of idol, curling up -- BIG)
    t2 = [(220,170),(238,145),(232,115)]
    for i in range(len(t2)-1):
        P.append({"type":"line","start":t2[i],"end":t2[i+1],"color":TENTACLE,"width":16})
    for cx, cy in t2:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":9,"color":TENTACLE,"outline":TENTACLE_DARK,"outline_w":1})
    # tentacle 3 (from idol top, reaching left toward Illaoi -- BIG)
    t3 = [(200,60),(180,80),(170,110)]
    for i in range(len(t3)-1):
        P.append({"type":"line","start":t3[i],"end":t3[i+1],"color":TENTACLE,"width":14})
    for cx, cy in t3:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":8,"color":TENTACLE,"outline":TENTACLE_DARK,"outline_w":1})
    # tentacle suckers (BIG, obvious)
    for cx, cy in [(205,205),(195,210),(235,130),(175,95)]:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":4,"color":TENTACLE_DARK,"outline":OUT,"outline_w":1})

    # --- Hair (dark, short) ---
    P.append({"type":"circle","cx":100,"cy":70,"r":18,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(84,64),(116,64),(112,80),(88,80)],"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (strong jawline -- THE missing feature, BIG + obvious) ---
    P.append({"type":"circle","cx":100,"cy":78,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # BIG strong jaw (broad, squared -- THE feature, prominent)
    P.append({"type":"polygon","points":[(84,86),(116,86),(112,100),(88,100)],"color":SKIN,"outline":OUT,"outline_w":2})
    # jaw shadow (emphasizes the strong jawline)
    P.append({"type":"line","start":[86,88],"end":[114,88],"color":SKIN_DARK,"width":2})
    # determined eyes
    P.append({"type":"line","start":[92,78],"end":[98,78],"color":EYE,"width":2})
    P.append({"type":"line","start":[102,78],"end":[108,78],"color":EYE,"width":2})
    # determined mouth
    P.append({"type":"line","start":[95,92],"end":[105,92],"color":(120,60,60),"width":1})
    # BIG tribal tattoos (THE missing feature -- on face, obvious purple patterns)
    # left face tattoo (BIG geometric pattern)
    P.append({"type":"line","start":[84,82],"end":[84,96],"color":TATTOO,"width":3})
    P.append({"type":"line","start":[82,86],"end":[88,86],"color":TATTOO,"width":2})
    P.append({"type":"line","start":[82,92],"end":[88,92],"color":TATTOO,"width":2})
    # right face tattoo
    P.append({"type":"line","start":[116,82],"end":[116,96],"color":TATTOO,"width":3})
    P.append({"type":"line","start":[112,86],"end":[118,86],"color":TATTOO,"width":2})
    P.append({"type":"line","start":[112,92],"end":[118,92],"color":TATTOO,"width":2})

    # --- Flowing robes (deep purple) ---
    P.append({"type":"polygon","points":[(78,98),(122,98),(130,180),(70,180)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # robe shading
    P.append({"type":"polygon","points":[(84,102),(116,102),(122,178),(78,178)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # gold trim on robe
    P.append({"type":"line","start":[78,98],"end":[122,98],"color":GOLD,"width":2})
    P.append({"type":"line","start":[70,180],"end":[130,180],"color":GOLD,"width":2})
    # tribal tattoos on arms (THE feature)
    P.append({"type":"line","start":[78,120],"end":[78,140],"color":TATTOO,"width":2})
    P.append({"type":"line","start":[76,124],"end":[80,124],"color":TATTOO,"width":1})
    P.append({"type":"line","start":[76,134],"end":[80,134],"color":TATTOO,"width":1})

    # --- Arms (muscular -- BIG, obvious muscle definition) ---
    P.append({"type":"rect","x":62,"y":106,"w":18,"h":52,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":120,"y":106,"w":18,"h":52,"color":SKIN,"outline":OUT,"outline_w":1,"radius":4})
    # BIG bicep muscle definition (muscular build -- THE missing feature)
    P.append({"type":"circle","cx":71,"cy":120,"r":8,"color":SKIN,"outline":SKIN_DARK,"outline_w":1})
    P.append({"type":"circle","cx":129,"cy":120,"r":8,"color":SKIN,"outline":SKIN_DARK,"outline_w":1})
    # BIG tribal tattoos on arms (THE missing feature -- obvious)
    P.append({"type":"line","start":[66,130],"end":[66,150],"color":TATTOO,"width":3})
    P.append({"type":"line","start":[64,134],"end":[70,134],"color":TATTOO,"width":2})
    P.append({"type":"line","start":[64,142],"end":[70,142],"color":TATTOO,"width":2})
    P.append({"type":"line","start":[124,130],"end":[124,150],"color":TATTOO,"width":3})
    P.append({"type":"line","start":[122,134],"end":[128,134],"color":TATTOO,"width":2})
    P.append({"type":"line","start":[122,142],"end":[128,142],"color":TATTOO,"width":2})
    # hands
    P.append({"type":"circle","cx":71,"cy":160,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":129,"cy":160,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (robe-covered, muscular) ---
    P.append({"type":"rect","x":82,"y":180,"w":18,"h":30,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":104,"y":180,"w":18,"h":30,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":80,"y":206,"w":22,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":104,"y":206,"w":22,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    return P


# ============================================================================
# Janna -- wind spirit; WIND SWIRLS / cyclone + floating + flowing hair + robes
# ============================================================================
def janna_prims():
    P = []
    WIND = (180, 230, 245)      # wind swirl color (light blue)
    WIND_DARK = (120, 180, 210)
    WIND_LIGHT = (220, 240, 250)
    ROBE = (240, 245, 250)      # white flowing robes
    ROBE_BLUE = (180, 220, 240) # light blue robe trim
    ROBE_DARK = (200, 220, 235)
    HAIR = (240, 245, 250)      # white flowing hair
    HAIR_BLUE = (180, 210, 235)
    SKIN = (235, 215, 195)
    GOLD = (220, 180, 60)
    EYE = (120, 180, 220)       # blue eyes
    OUT = (40, 50, 70)

    # --- WIND SWIRLS / CYCLONE (THE feature -- BIG, around her, visible) ---
    # big cyclone swirl behind her (the wind spirit signature)
    # outer swirl rings (concentric, light blue, semi-transparent feel)
    P.append({"type":"circle","cx":128,"cy":140,"r":90,"color":(200,230,245),"outline":WIND,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":140,"r":70,"color":(210,235,248),"outline":WIND,"outline_w":1})
    # wind swirl curves (spiral lines -- THE visible wind)
    P.append({"type":"line","start":[48,140],"end":[208,140],"color":WIND,"width":3})
    P.append({"type":"line","start":[60,110],"end":[196,110],"color":WIND_DARK,"width":2})
    P.append({"type":"line","start":[60,170],"end":[196,170],"color":WIND_DARK,"width":2})
    # swirl arcs (curved wind gusts)
    P.append({"type":"polygon","points":[(40,100),(80,90),(76,110),(44,116)],"color":WIND,"outline":WIND_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(176,90),(216,100),(212,116),(180,110)],"color":WIND,"outline":WIND_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(40,180),(80,170),(76,190),(44,196)],"color":WIND,"outline":WIND_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(176,170),(216,180),(212,196),(180,190)],"color":WIND,"outline":WIND_DARK,"outline_w":1})
    # small wind wisps
    for sx, sy in [(50,80),(200,80),(50,200),(200,200)]:
        P.append({"type":"circle","cx":sx,"cy":sy,"r":5,"color":WIND_LIGHT,"outline":WIND_DARK,"outline_w":1})

    # --- Long flowing hair (white, HUGE, blowing in wind -- THE missing feature) ---
    P.append({"type":"circle","cx":128,"cy":66,"r":22,"color":HAIR,"outline":OUT,"outline_w":1})
    # hair flowing wildly (wind-blown, both sides, HUGE streams)
    P.append({"type":"polygon","points":[(108,60),(128,50),(148,60),(176,44),(186,80),(150,76)],
              "color":HAIR,"outline":HAIR_BLUE,"outline_w":2})
    P.append({"type":"polygon","points":[(108,60),(128,50),(80,40),(68,76),(108,78)],
              "color":HAIR,"outline":HAIR_BLUE,"outline_w":2})
    # VERY long flowing hair streams (wind-blown, trailing far -- THE feature)
    P.append({"type":"polygon","points":[(110,70),(84,82),(60,140),(78,148),(104,92)],
              "color":HAIR,"outline":HAIR_BLUE,"outline_w":2})
    P.append({"type":"polygon","points":[(146,70),(172,82),(196,140),(178,148),(152,92)],
              "color":HAIR,"outline":HAIR_BLUE,"outline_w":2})
    # extra long hair wisps (trailing even further, wind-blown)
    P.append({"type":"polygon","points":[(100,76),(72,90),(52,160),(72,168),(96,100)],
              "color":HAIR,"outline":HAIR_BLUE,"outline_w":1})
    P.append({"type":"polygon","points":[(156,76),(184,90),(204,160),(184,168),(160,100)],
              "color":HAIR,"outline":HAIR_BLUE,"outline_w":1})
    # bangs (wind-blown)
    P.append({"type":"polygon","points":[(110,58),(146,58),(142,72),(114,72)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (ethereal, beautiful) ---
    P.append({"type":"circle","cx":128,"cy":74,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    # blue eyes (gentle)
    P.append({"type":"circle","cx":121,"cy":76,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":76,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":75,"r":1,"color":(255,255,255)})
    P.append({"type":"circle","cx":136,"cy":75,"r":1,"color":(255,255,255)})
    # gentle smile
    P.append({"type":"line","start":[122,86],"end":[134,86],"color":(150,100,120),"width":1})

    # --- Flowing robes (white, wind-blown, FLOATING -- no feet) ---
    # robe body (flowing, wide at bottom -- wind-blown)
    P.append({"type":"polygon","points":[(100,94),(156,94),(176,180),(80,180)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # robe shading (flowing folds)
    P.append({"type":"polygon","points":[(108,98),(148,98),(160,178),(96,178)],
              "color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # light blue trim (wind spirit)
    P.append({"type":"line","start":[100,94],"end":[156,94],"color":ROBE_BLUE,"width":2})
    P.append({"type":"line","start":[80,180],"end":[176,180],"color":ROBE_BLUE,"width":2})
    # gold waist band
    P.append({"type":"rect","x":90,"y":130,"w":76,"h":6,"color":GOLD,"outline":OUT,"outline_w":1})
    # flowing robe tails (wind-blown, trailing)
    P.append({"type":"polygon","points":[(80,180),(60,200),(70,210),(90,190)],"color":ROBE,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(176,180),(196,200),(186,210),(166,190)],"color":ROBE,"outline":OUT,"outline_w":1})

    # --- Arms (raised, wind-controlling gesture) ---
    P.append({"type":"rect","x":88,"y":100,"w":12,"h":44,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":156,"y":100,"w":12,"h":44,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":94,"cy":144,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":162,"cy":144,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    # wind swirl at hands (the magic)
    P.append({"type":"circle","cx":94,"cy":144,"r":8,"color":WIND_LIGHT,"outline":WIND_DARK,"outline_w":1})
    P.append({"type":"circle","cx":162,"cy":144,"r":8,"color":WIND_LIGHT,"outline":WIND_DARK,"outline_w":1})

    # --- FLOATING (no feet -- she hovers; robe ends in wind wisps) ---
    # wind wisps below robe (she floats on wind)
    P.append({"type":"polygon","points":[(96,190),(110,190),(102,210),(94,206)],"color":WIND,"outline":WIND_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(120,190),(136,190),(130,212),(122,208)],"color":WIND,"outline":WIND_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(146,190),(160,190),(156,208),(148,204)],"color":WIND,"outline":WIND_DARK,"outline_w":1})
    # bare feet hint (small, dangling -- floating)
    P.append({"type":"circle","cx":108,"cy":210,"r":4,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":148,"cy":210,"r":4,"color":SKIN,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Jhin -- the virtuoso; WHITE PORCELAIN MASK + wide hat + cape + pistol
# ============================================================================
def jhin_prims():
    P = []
    MASK = (245, 240, 230)      # white porcelain mask (THE feature)
    MASK_DARK = (200, 195, 185)
    MASK_SHADOW = (180, 170, 160)
    HAT = (40, 35, 40)          # wide-brimmed hat (black)
    HAT_BAND = (180, 40, 40)    # crimson hat band
    CAPE = (180, 40, 40)        # crimson cape (long, flowing)
    CAPE_DARK = (130, 25, 25)
    CAPE_INNER = (220, 60, 60)
    ARMOR = (60, 55, 65)        # mechanical armor plating (dark)
    ARMOR_LIGHT = (100, 95, 110)
    GOLD = (215, 175, 60)
    PISTOL = (90, 85, 95)       # Whisper pistol
    PISTOL_DARK = (50, 45, 55)
    PISTOL_GOLD = (200, 165, 55)
    SKIN = (220, 195, 175)      # hands (only visible skin)
    EYE = (60, 50, 60)          # mask eye slits
    OUT = (25, 20, 25)

    # --- Long flowing cape (behind, crimson, BIG) ---
    P.append({"type":"polygon","points":[(88,96),(168,96),(200,210),(56,210)],
              "color":CAPE,"outline":OUT,"outline_w":1})
    # cape inner (brighter crimson, flowing)
    P.append({"type":"polygon","points":[(98,100),(158,100),(184,206),(72,206)],
              "color":CAPE_INNER,"outline":OUT,"outline_w":1})
    # cape shading
    P.append({"type":"polygon","points":[(104,104),(152,104),(174,202),(82,202)],
              "color":CAPE_DARK,"outline":OUT,"outline_w":1})
    # gold cape trim
    P.append({"type":"line","start":[88,96],"end":[168,96],"color":GOLD,"width":2})
    P.append({"type":"line","start":[56,210],"end":[200,210],"color":GOLD,"width":2})

    # --- Wide-brimmed hat (THE feature -- big, behind mask) ---
    # hat brim (wide, circular)
    P.append({"type":"ellipse","x":80,"y":42,"w":96,"h":24,"color":HAT,"outline":OUT,"outline_w":2})
    # hat crown (rounded top)
    P.append({"type":"ellipse","x":100,"y":28,"w":56,"h":30,"color":HAT,"outline":OUT,"outline_w":2})
    # crimson hat band
    P.append({"type":"rect","x":102,"y":48,"w":52,"h":6,"color":HAT_BAND,"outline":OUT,"outline_w":1})
    # gold hat ornament
    P.append({"type":"circle","cx":128,"cy":51,"r":4,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- WHITE PORCELAIN MASK (THE feature -- face IS a mask, HUGE, prominent) ---
    # mask face (BIG, white porcelain, oval -- dominates the head)
    P.append({"type":"ellipse","x":104,"y":54,"w":48,"h":56,"color":MASK,"outline":OUT,"outline_w":3})
    # mask cheek shadows (porcelain sheen)
    P.append({"type":"polygon","points":[(108,76),(118,76),(114,98),(108,94)],"color":MASK_SHADOW,"outline":MASK_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(138,76),(148,76),(148,94),(142,98)],"color":MASK_SHADOW,"outline":MASK_DARK,"outline_w":1})
    # mask brow (painted, dramatic)
    P.append({"type":"polygon","points":[(108,72),(148,72),(144,76),(112,76)],"color":MASK_DARK,"outline":OUT,"outline_w":1})
    # mask eye slits (THE feature -- dramatic, painted eyes on porcelain)
    P.append({"type":"line","start":[110,80],"end":[122,80],"color":EYE,"width":4})
    P.append({"type":"line","start":[134,80],"end":[146,80],"color":EYE,"width":4})
    # mask painted cheeks (theatrical, crimson -- BIG)
    P.append({"type":"circle","cx":114,"cy":94,"r":5,"color":CAPE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":142,"cy":94,"r":5,"color":CAPE,"outline":OUT,"outline_w":1})
    # mask painted lips (theatrical smile -- BIG)
    P.append({"type":"line","start":[118,100],"end":[138,100],"color":CAPE_DARK,"width":3})
    # mask porcelain highlight (sheen -- obvious porcelain)
    P.append({"type":"line","start":[108,60],"end":[108,104],"color":(255,255,250),"width":3})
    P.append({"type":"line","start":[110,62],"end":[110,102],"color":(255,255,250),"width":1})
    # gold mask trim (edge -- frames the mask)
    P.append({"type":"ellipse","x":104,"y":54,"w":48,"h":56,"color":MASK,"outline":GOLD,"outline_w":1})

    # --- Mechanical armor plating (torso, dark -- slender, segmented) ---
    # slender torso (narrower = slender proportions)
    P.append({"type":"polygon","points":[(110,110),(146,110),(150,170),(106,170)],
              "color":ARMOR,"outline":OUT,"outline_w":1})
    # armor plates (mechanical, segmented -- BIG, obvious plating)
    P.append({"type":"polygon","points":[(112,114),(144,114),(142,140),(114,140)],
              "color":ARMOR_LIGHT,"outline":OUT,"outline_w":2})
    P.append({"type":"line","start":[128,114],"end":[128,140],"color":GOLD,"width":2})
    # armor segment lines (mechanical plating -- MORE obvious)
    for py in (122, 130, 138):
        P.append({"type":"line","start":[114,py],"end":[142,py],"color":GOLD,"width":2})
    # mechanical arm plates (segmented rectangles on torso sides)
    P.append({"type":"rect","x":108,"y":118,"w":6,"h":24,"color":ARMOR_LIGHT,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":142,"y":118,"w":6,"h":24,"color":ARMOR_LIGHT,"outline":OUT,"outline_w":1})
    # gold rivets on armor (mechanical detail)
    for ry in (120, 128, 136):
        P.append({"type":"circle","cx":111,"cy":ry,"r":2,"color":GOLD,"outline":OUT,"outline_w":1})
        P.append({"type":"circle","cx":145,"cy":ry,"r":2,"color":GOLD,"outline":OUT,"outline_w":1})
    # gold shoulder epaulettes (mechanical, BIG)
    P.append({"type":"circle","cx":106,"cy":114,"r":10,"color":ARMOR_LIGHT,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":150,"cy":114,"r":10,"color":ARMOR_LIGHT,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[98,112],"end":[112,112],"color":GOLD,"width":2})
    P.append({"type":"line","start":[144,112],"end":[158,112],"color":GOLD,"width":2})

    # --- Arms (one holding pistol -- slender) ---
    P.append({"type":"rect","x":90,"y":118,"w":12,"h":46,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":154,"y":118,"w":12,"h":46,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":4})
    # mechanical arm plates (segmented)
    P.append({"type":"line","start":[96,130],"end":[96,150],"color":GOLD,"width":1})
    P.append({"type":"line","start":[160,130],"end":[160,150],"color":GOLD,"width":1})
    P.append({"type":"circle","cx":96,"cy":166,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":160,"cy":166,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (armor-plated, slender) ---
    P.append({"type":"rect","x":110,"y":170,"w":16,"h":38,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":134,"y":170,"w":16,"h":38,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":3})
    # mechanical shin plates (segmented -- BIG)
    P.append({"type":"rect","x":110,"y":180,"w":16,"h":6,"color":ARMOR_LIGHT,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":134,"y":180,"w":16,"h":6,"color":ARMOR_LIGHT,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":110,"y":194,"w":16,"h":6,"color":ARMOR_LIGHT,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":134,"y":194,"w":16,"h":6,"color":ARMOR_LIGHT,"outline":OUT,"outline_w":1})
    # gold shin armor trim
    P.append({"type":"line","start":[110,186],"end":[126,186],"color":GOLD,"width":1})
    P.append({"type":"line","start":[134,186],"end":[150,186],"color":GOLD,"width":1})
    # boots
    P.append({"type":"rect","x":108,"y":204,"w":20,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":132,"y":204,"w":20,"h":12,"color":OUT,"outline":OUT,"outline_w":1,"radius":2})

    # --- Whisper pistol (THE weapon, in right hand, drawn IN FRONT) ---
    # pistol barrel (long, elegant, hextech sniper)
    P.append({"type":"rect","x":155,"y":156,"w":40,"h":10,"color":PISTOL,"outline":OUT,"outline_w":2})
    # pistol gold accents
    P.append({"type":"rect","x":165,"y":156,"w":6,"h":10,"color":PISTOL_GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":180,"y":156,"w":6,"h":10,"color":PISTOL_GOLD,"outline":OUT,"outline_w":1})
    # pistol muzzle (flared)
    P.append({"type":"rect","x":192,"y":154,"w":6,"h":14,"color":PISTOL_DARK,"outline":OUT,"outline_w":1})
    # pistol grip (in hand)
    P.append({"type":"polygon","points":[(155,166),(167,166),(163,182),(153,178)],"color":PISTOL_DARK,"outline":OUT,"outline_w":1})
    # pistol trigger
    P.append({"type":"line","start":[160,178],"end":[156,184],"color":PISTOL_DARK,"width":2})
    # gold pistol ornament (Jhin's aesthetic)
    P.append({"type":"circle","cx":172,"cy":161,"r":3,"color":PISTOL_GOLD,"outline":OUT,"outline_w":1})
    return P


# ============================================================================
# Run all 6
# ============================================================================
CHAMPS = [
    ("Gwen", gwen_prims, "oversized golden scissors"),
    ("Hecarim", hecarim_prims, "spectral centaur body + ghostly teal glow"),
    ("Hwei", hwei_prims, "floating paint palette + ink brush"),
    ("Illaoi", illaoi_prims, "large golden idol + tentacles"),
    ("Janna", janna_prims, "wind swirls / cyclone + floating"),
    ("Jhin", jhin_prims, "white porcelain mask + wide hat + cape + pistol"),
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
