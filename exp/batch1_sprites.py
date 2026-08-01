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
    # tail blade tip (scythe)
    P.append({"type":"polygon","points":[(38,82),(52,76),(48,94)],"color":PLATE,"outline":OUT,"outline_w":1})

    # --- Quadruped body (horizontal trunk, low-slung, BIG) ---
    P.append({"type":"ellipse","x":44,"y":108,"w":150,"h":56,"color":VOID,"outline":VOID_DARK,"outline_w":2})
    # belly (darker underside)
    P.append({"type":"ellipse","x":60,"y":132,"w":118,"h":26,"color":VOID_DARK,"outline":OUT,"outline_w":1})

    # --- Four legs (digitigrade, splayed) with HUGE SCYTHE CLAWS (THE feature) ---
    leg_pts = [(70,158),(104,160),(146,160),(180,158)]
    for lx,ly in leg_pts:
        P.append({"type":"rect","x":lx-9,"y":ly,"w":18,"h":34,"color":VOID,"outline":VOID_DARK,"outline_w":1,"radius":4})
        # foot
        P.append({"type":"circle","cx":lx,"cy":ly+34,"r":8,"color":VOID_DARK,"outline":OUT,"outline_w":1})
        # HUGE curved scythe claws (THE icon — long, curved, prominent)
        for off in (-7,0,7):
            P.append({"type":"line","start":[lx+off,ly+36],"end":[lx+off+5,ly+54],"color":CLAW,"width":3})
        # big central scythe claw (curved blade)
        P.append({"type":"polygon","points":[(lx-3,ly+34),(lx+12,ly+38),(lx+6,ly+58)],"color":CLAW,"outline":CLAW_DARK,"outline_w":1})

    # --- Crystalline void armor plates on back (THE feature — big ridged plates) ---
    plate_pts = [(75,118),(108,110),(140,110),(172,118)]
    for i,(px,py) in enumerate(plate_pts):
        P.append({"type":"polygon","points":[(px-16,py+10),(px+16,py+10),(px+9,py-14),(px-9,py-14)],
                  "color":PLATE,"outline":PLATE_DARK,"outline_w":1})
        P.append({"type":"line","start":[px,py-14],"end":[px,py+10],"color":PLATE_DARK,"width":1})
    # ridge spikes between plates (chitinous ridges)
    for sx in (90,124,158):
        P.append({"type":"polygon","points":[(sx-5,104),(sx+5,104),(sx,90)],"color":PLATE_DARK,"outline":OUT,"outline_w":1})

    # --- HEAD (right side, elongated predatory snout — THE feature) ---
    P.append({"type":"circle","cx":200,"cy":128,"r":22,"color":VOID,"outline":VOID_DARK,"outline_w":2})
    # elongated snout pointing right (long predatory jaw)
    P.append({"type":"polygon","points":[(194,122),(240,128),(240,140),(194,136)],
              "color":VOID,"outline":VOID_DARK,"outline_w":1})
    # snout tip / jaw (tapered)
    P.append({"type":"polygon","points":[(232,130),(248,132),(232,140)],"color":VOID_DARK,"outline":OUT,"outline_w":1})
    # chitinous head ridges (crest)
    P.append({"type":"polygon","points":[(188,112),(204,106),(210,120),(192,124)],"color":PLATE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(196,100),(210,96),(214,108),(200,110)],"color":PLATE,"outline":PLATE_DARK,"outline_w":1})
    # glowing void eyes (two, menacing)
    P.append({"type":"circle","cx":196,"cy":124,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":210,"cy":128,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    # mandible teeth (sharp)
    for tx in (216,224,232):
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
    GOGGLE = (60, 50, 45)        # goggle frame (dark)
    LENS = (180, 200, 90)        # glowing green lenses (7-lens)
    KATANA = (210, 215, 225)     # big katana blade
    KATANA_DARK = (120, 125, 135)
    EYE = (30, 25, 20)
    OUT = (30, 25, 20)

    # --- BIG TOPKNOT PONYTAIL (high on head, flowing) ---
    P.append({"type":"circle","cx":128,"cy":52,"r":10,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(120,58),(136,58),(132,72),(124,72)],"color":HAIR,"outline":OUT,"outline_w":1})
    # hair tie
    P.append({"type":"rect","x":122,"y":56,"w":12,"h":4,"color":GOLD,"outline":OUT,"outline_w":1})
    # hair back
    P.append({"type":"circle","cx":128,"cy":78,"r":18,"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":80,"r":17,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- 7-LENS GOGGLES / MASK (THE feature — big, covering eyes, prominent) ---
    # goggle frame band across eyes
    P.append({"type":"rect","x":108,"y":74,"w":40,"h":14,"color":GOGGLE,"outline":OUT,"outline_w":2})
    # 7 lenses in a row (the iconic multi-lens goggles)
    lens_xs = [112,118,124,128,132,138,144]
    for lx in lens_xs:
        P.append({"type":"circle","cx":lx,"cy":81,"r":2,"color":LENS,"outline":OUT,"outline_w":1})
    # goggle strap (around head)
    P.append({"type":"rect","x":110,"y":78,"w":4,"h":6,"color":GOGGLE,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":142,"y":78,"w":4,"h":6,"color":GOGGLE,"outline":OUT,"outline_w":1})
    # mask fabric below goggles (lower face covered)
    P.append({"type":"polygon","points":[(110,88),(146,88),(144,98),(112,98)],"color":GOGGLE,"outline":OUT,"outline_w":1})

    # --- Traditional Ionian robes (green) ---
    P.append({"type":"polygon","points":[(108,100),(148,100),(156,195),(100,195)],
              "color":ROBE,"outline":OUT,"outline_w":1})
    # robe center opening
    P.append({"type":"line","start":[128,102],"end":[128,193],"color":ROBE_DARK,"width":2})
    # gold trim on collar
    P.append({"type":"rect","x":110,"y":100,"w":36,"h":5,"color":GOLD,"outline":OUT,"outline_w":1})
    # gold sash/belt
    P.append({"type":"rect","x":100,"y":150,"w":56,"h":8,"color":BROWN,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":100,"y":148,"w":56,"h":3,"color":GOLD,"outline":OUT,"outline_w":1})
    # wrapped forearms (THE missing feature — visible wraps)
    P.append({"type":"rect","x":98,"y":120,"w":12,"h":30,"color":BROWN,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":146,"y":120,"w":12,"h":30,"color":BROWN,"outline":OUT,"outline_w":1,"radius":3})
    # wrap bands (visible wrapping)
    for wy in (124,130,136,142):
        P.append({"type":"line","start":[98,wy],"end":[110,wy],"color":GOLD,"width":1})
        P.append({"type":"line","start":[146,wy],"end":[158,wy],"color":GOLD,"width":1})
    # hands
    P.append({"type":"circle","cx":104,"cy":152,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":152,"cy":152,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs ---
    P.append({"type":"rect","x":112,"y":193,"w":14,"h":30,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":130,"y":193,"w":14,"h":30,"color":ROBE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":110,"y":221,"w":18,"h":8,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":221,"w":18,"h":8,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})

    # --- BIG KATANA (THE feature — long blade held across body, prominent) ---
    # blade diagonal across body (drawn in front)
    P.append({"type":"line","start":[80,170],"end":[196,90],"color":KATANA,"width":6})
    P.append({"type":"line","start":[80,170],"end":[196,90],"color":KATANA_DARK,"width":1})
    # blade edge (white highlight)
    P.append({"type":"line","start":[82,168],"end":[194,88],"color":(255,255,255),"width":1})
    # guard (tsuba)
    P.append({"type":"rect","x":74,"y":164,"w":12,"h":14,"color":GOLD,"outline":OUT,"outline_w":1,"radius":2})
    # handle
    P.append({"type":"rect","x":62,"y":170,"w":16,"h":12,"color":BROWN,"outline":OUT,"outline_w":1,"radius":2})
    # handle wrap
    for hx in (64,68,72):
        P.append({"type":"line","start":[hx,170],"end":[hx,182],"color":GOLD,"width":1})
    # blade tip
    P.append({"type":"polygon","points":[(194,88),(202,82),(198,94)],"color":KATANA,"outline":KATANA_DARK,"outline_w":1})

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
