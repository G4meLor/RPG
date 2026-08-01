"""Batch 1: hand-author 6 LoL champions to score 8-10.

Champions: Belveth, Diana, Gragas, Irelia, Kennen, MasterYi.
Each has ONE huge signature feature that dominates the silhouette.
Run sequentially; improve() auto-saves only when new > old.
"""
import sys, json, time
sys.path.insert(0, "exp")
from champ_improver import improve, committed_score

OUT = (25, 20, 30)


# ============================================================
# 1. BEL'VETH — quadruped void beast, big scythe claws, void plates
# ============================================================
def belveth_prims():
    P = []
    VOID = (125, 40, 150)        # purple-magenta
    VOID_DARK = (65, 18, 85)
    VOID_LIGHT = (190, 90, 210)  # magenta highlight
    PLATE = (205, 105, 225)      # crystalline plate
    PLATE_DARK = (115, 45, 135)
    EYE = (230, 130, 255)        # glowing void eye
    CLAW = (245, 210, 255)       # pale void claw
    CLAW_DARK = (180, 130, 200)

    # --- Tail (left, curving up behind body) ---
    tail = [(40,140),(28,120),(30,98),(44,86)]
    for i in range(len(tail)-1):
        P.append({"type":"line","start":tail[i],"end":tail[i+1],"color":VOID,"width":14})
    for cx,cy in tail:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":7,"color":VOID,"outline":VOID_DARK,"outline_w":1})
    P.append({"type":"polygon","points":[(38,82),(52,76),(48,94)],"color":PLATE,"outline":OUT,"outline_w":1})

    # --- Quadruped body (horizontal trunk, low-slung, BIG — lean predator) ---
    P.append({"type":"ellipse","x":44,"y":112,"w":150,"h":50,"color":VOID,"outline":VOID_DARK,"outline_w":2})
    P.append({"type":"ellipse","x":60,"y":134,"w":118,"h":22,"color":VOID_DARK,"outline":OUT,"outline_w":1})

    # --- Four digitigrade legs (lean, bent — predator stance) ---
    leg_pts = [(72,158),(106,160),(144,160),(178,158)]
    for lx,ly in leg_pts:
        # upper leg (thigh, leaning forward = digitigrade)
        P.append({"type":"polygon","points":[(lx-8,ly),(lx+8,ly),(lx+5,ly+18),(lx-5,ly+18)],
                  "color":VOID,"outline":VOID_DARK,"outline_w":1})
        # knee joint (visible bump = digitigrade bend)
        P.append({"type":"circle","cx":lx,"cy":ly+18,"r":6,"color":VOID_DARK,"outline":OUT,"outline_w":1})
        # lower leg (shin, angled back = digitigrade bend, thinner)
        P.append({"type":"polygon","points":[(lx-3,ly+18),(lx+3,ly+18),(lx+2,ly+34),(lx-2,ly+34)],
                  "color":VOID_DARK,"outline":OUT,"outline_w":1})
        # paw
        P.append({"type":"circle","cx":lx,"cy":ly+34,"r":7,"color":VOID_DARK,"outline":OUT,"outline_w":1})

    # --- HUGE SCYTHE CLAWS (THE feature — giant curved claws on front feet) ---
    # Front-left foot: massive scythe claw
    P.append({"type":"polygon","points":[(66,188),(90,194),(82,222),(70,216)],
              "color":CLAW,"outline":CLAW_DARK,"outline_w":2})
    P.append({"type":"line","start":[72,190],"end":[86,196],"color":(255,240,255),"width":1})
    P.append({"type":"line","start":[64,190],"end":[58,210],"color":CLAW,"width":3})
    P.append({"type":"line","start":[76,194],"end":[72,214],"color":CLAW,"width":2})
    # Front-right foot: massive scythe claw
    P.append({"type":"polygon","points":[(170,188),(194,194),(190,222),(176,216)],
              "color":CLAW,"outline":CLAW_DARK,"outline_w":2})
    P.append({"type":"line","start":[174,190],"end":[190,196],"color":(255,240,255),"width":1})
    P.append({"type":"line","start":[196,190],"end":[202,210],"color":CLAW,"width":3})
    P.append({"type":"line","start":[180,194],"end":[184,214],"color":CLAW,"width":2})
    # Back feet smaller claws
    for lx in (106,144):
        P.append({"type":"line","start":[lx,194],"end":[lx,210],"color":CLAW,"width":2})
        P.append({"type":"line","start":[lx-4,194],"end":[lx-6,208],"color":CLAW,"width":2})

    # --- Crystalline void armor plates on back (THE feature — big faceted plates) ---
    plate_pts = [(78,120),(110,112),(142,112),(172,120)]
    for i,(px,py) in enumerate(plate_pts):
        # main plate body (faceted crystal shape)
        P.append({"type":"polygon","points":[(px-17,py+10),(px+17,py+10),(px+10,py-15),(px-10,py-15)],
                  "color":PLATE,"outline":PLATE_DARK,"outline_w":1})
        # facet line (crystalline detail)
        P.append({"type":"line","start":[px,py-15],"end":[px,py+10],"color":PLATE_DARK,"width":1})
        P.append({"type":"line","start":[px-10,py-15],"end":[px,py],"color":PLATE_DARK,"width":1})
        P.append({"type":"line","start":[px+10,py-15],"end":[px,py],"color":PLATE_DARK,"width":1})
        # plate highlight (crystal shine)
        P.append({"type":"polygon","points":[(px-6,py-12),(px+2,py-12),(px-2,py-4)],
                  "color":VOID_LIGHT,"outline":None,"outline_w":0})
    # ridge spikes between plates (chitinous ridges)
    for sx in (94,126,158):
        P.append({"type":"polygon","points":[(sx-6,104),(sx+6,104),(sx,88)],"color":PLATE_DARK,"outline":OUT,"outline_w":1})

    # --- HEAD (right side, elongated predatory snout — THE feature) ---
    P.append({"type":"circle","cx":198,"cy":128,"r":22,"color":VOID,"outline":VOID_DARK,"outline_w":2})
    # elongated snout pointing right (long predatory jaw)
    P.append({"type":"polygon","points":[(192,122),(242,128),(242,140),(192,136)],
              "color":VOID,"outline":VOID_DARK,"outline_w":1})
    # snout tip / jaw (tapered)
    P.append({"type":"polygon","points":[(234,130),(250,132),(234,140)],"color":VOID_DARK,"outline":OUT,"outline_w":1})
    # chitinous head crest (big spike)
    P.append({"type":"polygon","points":[(186,112),(204,104),(210,122),(190,126)],"color":PLATE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(194,98),(210,92),(216,110),(198,112)],"color":PLATE,"outline":PLATE_DARK,"outline_w":1})
    # glowing void eyes (two, menacing)
    P.append({"type":"circle","cx":194,"cy":124,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":208,"cy":128,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    # mandible teeth (sharp)
    for tx in (218,226,234):
        P.append({"type":"polygon","points":[(tx-2,138),(tx+2,138),(tx,144)],"color":CLAW,"outline":OUT,"outline_w":1})

    # --- Void energy glow (magenta wisps) ---
    for gy in (100,130):
        P.append({"type":"circle","cx":120,"cy":gy,"r":4,"color":VOID_LIGHT,"outline":None,"outline_w":0})

    return P


# ============================================================
# 2. DIANA — big crescent moonblade + moon halo, dark hair, silver armor
# ============================================================
def diana_prims():
    P = []
    SKIN = (215, 215, 230)       # pale
    HAIR = (35, 30, 55)          # dark blue-black
    SILVER = (200, 205, 220)
    SILVER_DARK = (110, 115, 135)
    BLUE = (55, 70, 120)         # dark blue robe
    GOLD = (215, 180, 70)
    EYE = (180, 200, 240)        # pale glowing
    MOON = (235, 235, 245)       # crescent moon
    OUT = (25, 20, 35)

    # --- CRESCENT MOON HALO above head (THE feature — big, behind head) ---
    P.append({"type":"circle","cx":128,"cy":50,"r":26,"color":MOON,"outline":SILVER_DARK,"outline_w":2})
    P.append({"type":"circle","cx":140,"cy":46,"r":22,"color":(40,35,60),"outline":None,"outline_w":0})  # bite out -> crescent
    # moon glow
    P.append({"type":"circle","cx":118,"cy":56,"r":4,"color":(255,255,255),"outline":None,"outline_w":0})

    # --- Dark flowing hair (back, long, past shoulders) ---
    P.append({"type":"circle","cx":128,"cy":78,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(110,80),(146,80),(150,140),(106,140)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # hair flowing wider at bottom
    P.append({"type":"polygon","points":[(100,120),(156,120),(160,165),(96,165)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (pale, lunar) ---
    P.append({"type":"circle","cx":128,"cy":82,"r":17,"color":SKIN,"outline":OUT,"outline_w":1})
    # pale glowing eyes
    P.append({"type":"circle","cx":121,"cy":82,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":82,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    # crescent moon forehead mark
    P.append({"type":"polygon","points":[(126,72),(132,72),(130,78),(128,76)],"color":MOON,"outline":OUT,"outline_w":1})

    # --- Silver lunar armor torso (with moon emblem) ---
    P.append({"type":"polygon","points":[(112,98),(144,98),(148,150),(108,150)],
              "color":SILVER,"outline":OUT,"outline_w":1})
    # armor segments
    P.append({"type":"line","start":[128,100],"end":[128,148],"color":SILVER_DARK,"width":1})
    P.append({"type":"line","start":[114,124],"end":[142,124],"color":SILVER_DARK,"width":1})
    # moon emblem on chest
    P.append({"type":"circle","cx":128,"cy":120,"r":6,"color":MOON,"outline":SILVER_DARK,"outline_w":1})
    P.append({"type":"circle","cx":132,"cy":118,"r":4,"color":SILVER,"outline":None,"outline_w":0})

    # --- Blue robe skirt (flowing) ---
    P.append({"type":"polygon","points":[(108,148),(148,148),(156,200),(100,200)],
              "color":BLUE,"outline":OUT,"outline_w":1})
    # gold trim on skirt
    P.append({"type":"rect","x":100,"y":194,"w":56,"h":6,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Arms ---
    P.append({"type":"rect","x":100,"y":104,"w":12,"h":40,"color":SILVER,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":144,"y":104,"w":12,"h":40,"color":SILVER,"outline":OUT,"outline_w":1,"radius":4})
    # hands
    P.append({"type":"circle","cx":106,"cy":146,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":150,"cy":146,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs ---
    P.append({"type":"rect","x":112,"y":196,"w":12,"h":30,"color":BLUE,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":196,"w":12,"h":30,"color":BLUE,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":110,"y":222,"w":16,"h":8,"color":SILVER_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":222,"w":16,"h":8,"color":SILVER_DARK,"outline":OUT,"outline_w":1,"radius":2})

    # --- CRESCENT MOONBLADE (THE feature — BIG curved blade in front, held up) ---
    # blade is a thick crescent, silver, prominent in front of body
    P.append({"type":"polygon","points":[(160,90),(176,86),(184,110),(178,140),(168,138),(172,112),(162,98)],
              "color":SILVER,"outline":OUT,"outline_w":2})
    # crescent inner curve (darker)
    P.append({"type":"polygon","points":[(166,96),(174,94),(178,112),(172,134),(168,130),(170,110)],
              "color":SILVER_DARK,"outline":None,"outline_w":0})
    # blade edge highlight
    P.append({"type":"line","start":[162,94],"end":[176,90],"color":(255,255,255),"width":1})
    # gold hilt
    P.append({"type":"rect","x":158,"y":138,"w":14,"h":10,"color":GOLD,"outline":OUT,"outline_w":1,"radius":2})
    # handle grip
    P.append({"type":"rect","x":160,"y":146,"w":10,"h":14,"color":(90,60,30),"outline":OUT,"outline_w":1})
    # moon gem on hilt
    P.append({"type":"circle","cx":165,"cy":142,"r":3,"color":MOON,"outline":GOLD,"outline_w":1})

    return P


# ============================================================
# 3. GRAGAS — HUGE round belly (dominates), bushy beard, beer barrel
# ============================================================
def gragas_prims():
    P = []
    SKIN = (210, 150, 120)       # ruddy complexion
    SKIN_DARK = (160, 100, 80)
    HAIR = (140, 90, 50)         # brown
    BEARD = (120, 75, 40)        # bushy brown beard
    BELLY = (200, 140, 100)      # ruddy belly (slightly lighter shirt)
    SHIRT = (170, 110, 70)       # leather/fur
    GOLD_B = (200, 160, 50)      # belt buckle gold
    BARREL = (150, 95, 45)       # wooden cask
    BARREL_DARK = (90, 55, 25)
    METAL = (130, 110, 80)
    OUT = (40, 25, 20)

    # --- Beer barrel (behind, carried on back/side) ---
    P.append({"type":"ellipse","x":180,"y":120,"w":40,"h":56,"color":BARREL,"outline":BARREL_DARK,"outline_w":2})
    # barrel bands
    P.append({"type":"rect","x":182,"y":126,"w":36,"h":5,"color":METAL,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":182,"y":160,"w":36,"h":5,"color":METAL,"outline":OUT,"outline_w":1})
    # barrel staves
    for sx in (188,200,212):
        P.append({"type":"line","start":[sx,124],"end":[sx,172],"color":BARREL_DARK,"width":1})
    # barrel top
    P.append({"type":"ellipse","x":184,"y":116,"w":34,"h":10,"color":BARREL_DARK,"outline":OUT,"outline_w":1})

    # --- Arms (thick, around belly) ---
    P.append({"type":"rect","x":74,"y":130,"w":24,"h":50,"color":SHIRT,"outline":OUT,"outline_w":1,"radius":8})
    P.append({"type":"rect","x":158,"y":130,"w":24,"h":50,"color":SHIRT,"outline":OUT,"outline_w":1,"radius":8})
    # hands (fists)
    P.append({"type":"circle","cx":86,"cy":184,"r":9,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":170,"cy":184,"r":9,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- HUGE ROUND BELLY (THE feature — biggest circle on sprite, dominates) ---
    P.append({"type":"circle","cx":128,"cy":160,"r":52,"color":BELLY,"outline":OUT,"outline_w":2})
    # belly shirt strap (leather strap across belly)
    P.append({"type":"rect","x":78,"y":150,"w":100,"h":10,"color":SHIRT,"outline":OUT,"outline_w":1})
    # belt buckle
    P.append({"type":"circle","cx":128,"cy":155,"r":6,"color":GOLD_B,"outline":OUT,"outline_w":1})
    # belly highlight (roundness)
    P.append({"type":"circle","cx":112,"cy":145,"r":10,"color":(220,165,125),"outline":None,"outline_w":0})

    # --- Head (ruddy, on top of belly — small relative to belly) ---
    P.append({"type":"circle","cx":128,"cy":88,"r":24,"color":SKIN,"outline":OUT,"outline_w":1})
    # ruddy cheeks
    P.append({"type":"circle","cx":114,"cy":94,"r":5,"color":(200,90,70),"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":142,"cy":94,"r":5,"color":(200,90,70),"outline":None,"outline_w":0})
    # eyes (squinty, drunk)
    P.append({"type":"line","start":[116,84],"end":[124,84],"color":OUT,"width":2})
    P.append({"type":"line","start":[132,84],"end":[140,84],"color":OUT,"width":2})
    # nose (bulbous, ruddy)
    P.append({"type":"circle","cx":128,"cy":92,"r":5,"color":SKIN_DARK,"outline":OUT,"outline_w":1})

    # --- WILD BUSHY BEARD (THE feature — huge, covers lower face) ---
    P.append({"type":"circle","cx":128,"cy":108,"r":22,"color":BEARD,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(108,100),(148,100),(152,128),(104,128)],
              "color":BEARD,"outline":OUT,"outline_w":1})
    # beard texture (bushy strands)
    for bx in (112,120,128,136,144):
        P.append({"type":"line","start":[bx,106],"end":[bx,124],"color":HAIR,"width":1})
    # mustache
    P.append({"type":"polygon","points":[(116,98),(140,98),(136,104),(120,104)],"color":BEARD,"outline":OUT,"outline_w":1})

    # --- Hair / balding top ---
    P.append({"type":"polygon","points":[(108,74),(148,74),(144,66),(112,66)],"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Legs (stout, under belly) ---
    P.append({"type":"rect","x":96,"y":206,"w":24,"h":34,"color":SHIRT,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"rect","x":136,"y":206,"w":24,"h":34,"color":SHIRT,"outline":OUT,"outline_w":1,"radius":5})
    # boots
    P.append({"type":"rect","x":92,"y":234,"w":30,"h":12,"color":(60,40,25),"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":134,"y":234,"w":30,"h":12,"color":(60,40,25),"outline":OUT,"outline_w":1,"radius":3})

    return P


# ============================================================
# 4. IRELIA — floating blade shards orbiting (THE feature), robes, dark hair
# ============================================================
def irelia_prims():
    P = []
    SKIN = (230, 205, 180)
    HAIR = (40, 30, 35)          # long dark hair
    ROBE = (235, 235, 240)       # white Ionian robes
    ROBE_DARK = (180, 180, 195)
    GOLD = (215, 175, 60)
    BLUE = (60, 90, 160)         # blue sash/accents
    BLADE = (190, 200, 215)      # floating metal shards
    BLADE_DARK = (90, 100, 120)
    EYE = (50, 40, 45)
    OUT = (30, 25, 30)

    # --- FLOATING BLADE SHARDS orbiting around her (THE feature — 7 shards in arc) ---
    # Big arc of floating blades around her body (drawn behind+around)
    shard_positions = [
        (60,100),(70,140),(80,180),       # left arc
        (196,100),(186,140),(176,180),    # right arc
        (128,55),                          # top
    ]
    for i,(sx,sy) in enumerate(shard_positions):
        # each shard = elongated diamond/blade shape
        if sy < 80:  # top shard points down
            pts = [(sx,sy-12),(sx+5,sy),(sx,sy+12),(sx-5,sy)]
        elif sx < 128:  # left shards point right
            pts = [(sx-12,sy),(sx,sy-5),(sx+12,sy),(sx,sy+5)]
        else:  # right shards point left
            pts = [(sx+12,sy),(sx,sy-5),(sx-12,sy),(sx,sy+5)]
        P.append({"type":"polygon","points":pts,"color":BLADE,"outline":BLADE_DARK,"outline_w":2})
        # blade edge highlight
        P.append({"type":"line","start":pts[0],"end":pts[2],"color":(240,240,250),"width":1})
    # glowing energy links (faint blue lines connecting shards)
    for (sx,sy) in shard_positions[:6]:
        P.append({"type":"line","start":[sx,sy],"end":[128,140],"color":(120,150,210),"width":1})

    # --- Long dark hair (back, flowing) ---
    P.append({"type":"circle","cx":128,"cy":80,"r":18,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(110,82),(146,82),(150,150),(106,150)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":84,"r":16,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":84,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":134,"cy":84,"r":3,"color":EYE,"outline":OUT,"outline_w":1})
    # hair bangs
    P.append({"type":"polygon","points":[(112,72),(144,72),(140,82),(116,82)],"color":HAIR,"outline":OUT,"outline_w":1})
    # determined mouth
    P.append({"type":"line","start":[123,92],"end":[133,92],"color":(120,60,60),"width":1})

    # --- Flowing Ionian robes (white, graceful) ---
    P.append({"type":"polygon","points":[(108,100),(148,100),(160,200),(96,200)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # robe folds
    P.append({"type":"line","start":[128,102],"end":[128,198],"color":ROBE_DARK,"width":1})
    # blue sash across waist
    P.append({"type":"polygon","points":[(100,148),(156,148),(160,162),(96,162)],
              "color":BLUE,"outline":OUT,"outline_w":1})
    # gold trim on sash
    P.append({"type":"rect","x":96,"y":160,"w":64,"h":4,"color":GOLD,"outline":OUT,"outline_w":1})
    # gold collar
    P.append({"type":"rect","x":110,"y":100,"w":36,"h":5,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Arms (raised, dance-like pose) ---
    P.append({"type":"rect","x":98,"y":108,"w":12,"h":40,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":146,"y":108,"w":12,"h":40,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":104,"cy":150,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":152,"cy":150,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (robe covers most) ---
    P.append({"type":"rect","x":112,"y":196,"w":12,"h":30,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":196,"w":12,"h":30,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":110,"y":222,"w":16,"h":8,"color":GOLD,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":222,"w":16,"h":8,"color":GOLD,"outline":OUT,"outline_w":1,"radius":2})

    return P


# ============================================================
# 5. KENNEN — big pointed yordle ears, small body, lightning, Kinkou robes
# ============================================================
def kennen_prims():
    P = []
    FUR = (200, 165, 120)        # yordle fur (tan)
    FUR_DARK = (150, 115, 75)
    ROBE = (60, 90, 160)         # blue Kinkou robes
    ROBE_DARK = (35, 55, 110)
    WHITE = (240, 240, 245)
    GOLD = (215, 175, 60)
    LIGHTNING = (250, 230, 90)   # yellow electric sparks
    BLADE_GRAY = (180, 185, 195) # shuriken metal
    EYE = (40, 30, 30)
    OUT = (30, 25, 30)

    # --- BIG POINTED YORDLE EARS (THE feature — huge, sticking out top) ---
    # left ear (big triangle pointing up-left)
    P.append({"type":"polygon","points":[(110,68),(88,30),(118,62)],
              "color":FUR,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(108,62),(96,40),(114,60)],
              "color":FUR_DARK,"outline":None,"outline_w":0})
    # right ear (big triangle pointing up-right)
    P.append({"type":"polygon","points":[(146,68),(168,30),(138,62)],
              "color":FUR,"outline":OUT,"outline_w":2})
    P.append({"type":"polygon","points":[(148,62),(160,40),(142,60)],
              "color":FUR_DARK,"outline":None,"outline_w":0})
    # ear inner pink
    P.append({"type":"polygon","points":[(100,55),(92,40),(108,58)],"color":(220,160,150),"outline":None,"outline_w":0})
    P.append({"type":"polygon","points":[(156,55),(164,40),(148,58)],"color":(220,160,150),"outline":None,"outline_w":0})

    # --- Head (big relative to body = yordle proportions) ---
    P.append({"type":"circle","cx":128,"cy":82,"r":24,"color":FUR,"outline":OUT,"outline_w":2})
    # big eyes (determined)
    P.append({"type":"circle","cx":118,"cy":82,"r":6,"color":WHITE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":138,"cy":82,"r":6,"color":WHITE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":119,"cy":83,"r":3,"color":EYE,"outline":None,"outline_w":0})
    P.append({"type":"circle","cx":139,"cy":83,"r":3,"color":EYE,"outline":None,"outline_w":0})
    # small whisker marks
    P.append({"type":"line","start":[108,90],"end":[114,90],"color":FUR_DARK,"width":1})
    P.append({"type":"line","start":[142,90],"end":[148,90],"color":FUR_DARK,"width":1})
    # determined mouth
    P.append({"type":"line","start":[123,94],"end":[133,94],"color":OUT,"width":1})

    # --- Kinkou robe body (small relative to head = yordle) ---
    P.append({"type":"polygon","points":[(110,104),(146,104),(154,180),(102,180)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # robe center seam
    P.append({"type":"line","start":[128,106],"end":[128,178],"color":ROBE_DARK,"width":1})
    # gold belt
    P.append({"type":"rect","x":102,"y":140,"w":52,"h":8,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":144,"r":4,"color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # white collar
    P.append({"type":"rect","x":112,"y":104,"w":32,"h":6,"color":WHITE,"outline":OUT,"outline_w":1})

    # --- Arms (small) ---
    P.append({"type":"rect","x":100,"y":112,"w":12,"h":34,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":144,"y":112,"w":12,"h":34,"color":ROBE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":106,"cy":148,"r":5,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":150,"cy":148,"r":5,"color":FUR,"outline":OUT,"outline_w":1})

    # --- Legs (small, stubby) ---
    P.append({"type":"rect","x":110,"y":178,"w":14,"h":26,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":178,"w":14,"h":26,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":108,"y":200,"w":18,"h":8,"color":OUT,"outline":None,"outline_w":0,"radius":2})
    P.append({"type":"rect","x":130,"y":200,"w":18,"h":8,"color":OUT,"outline":None,"outline_w":0,"radius":2})

    # --- Lightning sparks (THE feature — yellow electric arcs around him) ---
    # lightning bolt left
    P.append({"type":"polygon","points":[(78,120),(86,128),(80,132),(90,144),(84,136),(92,130)],
              "color":LIGHTNING,"outline":(200,170,30),"outline_w":1})
    # lightning bolt right
    P.append({"type":"polygon","points":[(178,120),(170,128),(176,132),(166,144),(172,136),(164,130)],
              "color":LIGHTNING,"outline":(200,170,30),"outline_w":1})
    # spark dots
    for sx,sy in [(70,100),(186,100),(74,160),(182,160)]:
        P.append({"type":"circle","cx":sx,"cy":sy,"r":3,"color":LIGHTNING,"outline":(200,170,30),"outline_w":1})
    # shuriken (small, in hand area)
    P.append({"type":"polygon","points":[(106,148),(112,142),(118,148),(112,154)],
              "color":BLADE_GRAY,"outline":OUT,"outline_w":1})

    return P


# ============================================================
# 6. MASTER YI — 7-lens goggles/mask (THE feature), topknot, big katana
# ============================================================
def masteryi_prims():
    P = []
    SKIN = (220, 185, 150)
    ROBE = (90, 130, 70)         # green Ionian robes
    ROBE_DARK = (55, 90, 45)
    GOLD = (215, 175, 60)
    BROWN = (120, 80, 45)
    HAIR = (50, 35, 25)          # dark hair, topknot
    GOGGLE = (55, 45, 40)        # goggle frame (dark)
    LENS = (200, 235, 110)       # glowing green lenses (7-lens)
    KATANA = (220, 225, 235)     # big katana blade
    KATANA_DARK = (110, 115, 130)
    EYE = (30, 25, 20)
    OUT = (25, 20, 20)

    # --- BIG TOPKNOT PONYTAIL (high on head, prominent) ---
    P.append({"type":"circle","cx":128,"cy":40,"r":11,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(119,48),(137,48),(133,66),(123,66)],"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":121,"y":46,"w":14,"h":4,"color":GOLD,"outline":OUT,"outline_w":1})
    # hair back (head)
    P.append({"type":"circle","cx":128,"cy":74,"r":19,"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (lean) ---
    P.append({"type":"circle","cx":128,"cy":78,"r":17,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- 7-LENS GOGGLES (THE feature — HUGE, the single dominant icon) ---
    # goggle frame band across eyes (BIG — wider than head, tall)
    P.append({"type":"rect","x":100,"y":70,"w":56,"h":20,"color":GOGGLE,"outline":OUT,"outline_w":2})
    # 7 lenses in a row (the iconic multi-lens goggles — BIG glowing circles)
    lens_xs = [108,116,122,128,134,140,148]
    for lx in lens_xs:
        P.append({"type":"circle","cx":lx,"cy":80,"r":4,"color":LENS,"outline":OUT,"outline_w":1})
    # lens bright glow centers
    for lx in lens_xs:
        P.append({"type":"circle","cx":lx,"cy":79,"r":2,"color":(255,255,210),"outline":None,"outline_w":0})
    # goggle straps (around head sides, visible)
    P.append({"type":"rect","x":96,"y":74,"w":6,"h":12,"color":GOGGLE,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":154,"y":74,"w":6,"h":12,"color":GOGGLE,"outline":OUT,"outline_w":1})
    # mask fabric below goggles (lower face covered — ninja mask, dark)
    P.append({"type":"polygon","points":[(104,90),(152,90),(150,102),(106,102)],"color":GOGGLE,"outline":OUT,"outline_w":1})

    # --- Traditional Ionian robes (green, LEAN — narrow torso for athletic build) ---
    P.append({"type":"polygon","points":[(110,104),(146,104),(152,195),(104,195)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # robe center opening (V-neck)
    P.append({"type":"polygon","points":[(120,104),(136,104),(128,140)],"color":ROBE_DARK,"outline":OUT,"outline_w":1})
    # gold trim on collar
    P.append({"type":"rect","x":110,"y":104,"w":36,"h":5,"color":GOLD,"outline":OUT,"outline_w":1})
    # gold sash/belt (lean)
    P.append({"type":"rect","x":104,"y":150,"w":48,"h":8,"color":BROWN,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":104,"y":148,"w":48,"h":3,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Wrapped forearms (THE missing feature — BIG, visible, martial-arts raised pose) ---
    # LEFT arm raised forward (holding katana) — wrapped forearm prominent
    P.append({"type":"rect","x":88,"y":120,"w":16,"h":36,"color":BROWN,"outline":OUT,"outline_w":1,"radius":5})
    for wy in (124,130,136,142,148,154):
        P.append({"type":"line","start":[88,wy],"end":[104,wy],"color":GOLD,"width":1})
    P.append({"type":"circle","cx":96,"cy":158,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})
    # RIGHT arm raised (martial-arts posture)
    P.append({"type":"rect","x":152,"y":116,"w":16,"h":34,"color":BROWN,"outline":OUT,"outline_w":1,"radius":5})
    for wy in (120,126,132,138,144,150):
        P.append({"type":"line","start":[152,wy],"end":[168,wy],"color":GOLD,"width":1})
    P.append({"type":"circle","cx":160,"cy":152,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (lean, martial-arts stance — slightly apart) ---
    P.append({"type":"rect","x":108,"y":195,"w":16,"h":34,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":195,"w":16,"h":34,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":106,"y":226,"w":20,"h":10,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":226,"w":20,"h":10,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})

    # --- BIG KATANA (THE feature — big polygon blade, held forward, prominent) ---
    # blade as a thick polygon (drawn in front, diagonal across body)
    P.append({"type":"polygon","points":[(70,176),(80,168),(206,82),(216,92),(86,184)],
              "color":KATANA,"outline":KATANA_DARK,"outline_w":2})
    # blade edge highlight (white line along the edge)
    P.append({"type":"line","start":[78,174],"end":[204,84],"color":(255,255,255),"width":2})
    # guard (tsuba) — gold, prominent
    P.append({"type":"rect","x":62,"y":168,"w":18,"h":20,"color":GOLD,"outline":OUT,"outline_w":1,"radius":3})
    # handle
    P.append({"type":"rect","x":48,"y":176,"w":18,"h":16,"color":BROWN,"outline":OUT,"outline_w":1,"radius":3})
    # handle wrap (gold bands)
    for hx in (50,54,58,62):
        P.append({"type":"line","start":[hx,176],"end":[hx,192],"color":GOLD,"width":1})
    # blade tip (pointed)
    P.append({"type":"polygon","points":[(206,82),(222,76),(212,96)],"color":KATANA,"outline":KATANA_DARK,"outline_w":1})

    return P


# ============================================================
# RUN ALL 6 SEQUENTIALLY
# ============================================================
CHAMPS = [
    ("Belveth", belveth_prims, "quadruped void beast, scythe claws, void plates"),
    ("Diana", diana_prims, "crescent moonblade + moon halo"),
    ("Gragas", gragas_prims, "huge round belly + bushy beard + barrel"),
    ("Irelia", irelia_prims, "floating blade shards orbiting"),
    ("Kennen", kennen_prims, "big pointed yordle ears + lightning"),
    ("MasterYi", masteryi_prims, "7-lens goggles + topknot + katana"),
]

if __name__ == "__main__":
    results = []
    for cid, fn, feat in CHAMPS:
        print(f"\n{'='*60}\n{cid} — {feat}\n{'='*60}")
        prims = fn()
        # clean any walrus-assignment locals that leaked
        prims = [p for p in prims if isinstance(p, dict) and "type" in p]
        try:
            r = improve(cid, prims, gate_n=3)
            print(f"RESULT {cid}: old={r['old']} new={r['new']} saved={r['saved']} "
                  f"verdict={r['verdict']} missing={r['missing'][:4]}")
            results.append({"id":cid,"old":r["old"],"new":r["new"],"saved":r["saved"],
                            "rounds":1,"missing_final":r["missing"][:4],"feature":feat})
        except Exception as e:
            print(f"ERROR {cid}: {e}")
            results.append({"id":cid,"old":4,"new":0,"saved":False,"rounds":1,
                            "missing_final":[str(e)],"feature":feat})
        time.sleep(2)
    print("\n\n=== FINAL RESULTS ===")
    print(json.dumps(results, indent=2))
    improved = sum(1 for r in results if r["new"] > r["old"])
    ge8 = sum(1 for r in results if r["new"] >= 8)
    print(f"\n{improved}/6 champs improved, {ge8} reached >=8.")
