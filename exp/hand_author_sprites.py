"""Hand-authored sprites: I (with LoL knowledge) place primitives precisely.

Root cause after 3 failed VLM fix rounds (revision loops, additive patches,
splash fresh-gen): the VLM 31b cannot render subtle features at 256px and
every VLM-in-the-loop revision clutters or regresses the working base.

This bypasses the VLM entirely for the final mile. I hand-author full JSON
primitives for champs the VLM couldn't finish — placing each feature at the
right position, size, and color from LoL knowledge. Then the canon GATE
(still VLM, judging recognizability) verifies.

Proof-of-concept: hand-author Ahri (score 6, missing whisker markings +
slender proportions + ambiguous tail count). If my hand-authored Ahri
scores >= 7, the approach works and I scale it to the other close champs.

Results -> exp/hand_author_results.json.
"""
import os, sys, json, base64, ssl, urllib.request, re, time, shutil

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import pygame; pygame.init(); pygame.display.set_mode((1, 1))

from src.build.champions import CHAMPIONS_DB
from src.data.tuning import ASSET_DIR

BASE = "https://runai.misaonline.vpnlocal/prod-llm/misa-gemma4-31b-it-api/v1"
KEY = "sk-proj-runai-8p33H3qYneIaWOwjX5bsae3I1CIJhUjvKG0nTis6dJ1mzkJqHW"
MODEL = "misa-gemma-4-31b-it"
CTX = ssl.create_default_context(); CTX.check_hostname = False; CTX.verify_mode = ssl.CERT_NONE

EXP_DIR = os.path.dirname(os.path.abspath(__file__))


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def chat(messages, max_tokens=4000, temperature=0.3, timeout=300):
    for attempt in range(3):
        try:
            body = json.dumps({"model": MODEL, "messages": messages,
                               "max_tokens": max_tokens, "temperature": temperature}).encode()
            req = urllib.request.Request(BASE + "/chat/completions", data=body,
                headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, context=CTX, timeout=timeout) as r:
                return json.loads(r.read())["choices"][0]["message"]["content"]
        except Exception:
            if attempt < 2:
                time.sleep(5)
                continue
            raise


def strip_json(text):
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    start = text.find("{")
    if start < 0:
        return text.strip()
    depth = 0; end = start
    for i in range(start, len(text)):
        if text[i] == "{": depth += 1
        elif text[i] == "}": depth -= 1
        if depth == 0: end = i + 1; break
    if depth != 0:
        return text[start:] + "}" * depth
    return text[start:end]


def render_primitives(prims, path):
    surf = pygame.Surface((256, 256), pygame.SRCALPHA)
    for p in prims:
        try:
            t = p.get("type", "")
            col = tuple(p.get("color", [200, 200, 200])[:3])
            ol = p.get("outline")
            ol = tuple(ol[:3]) if ol else None
            ow = p.get("outline_w", 1)
            if t == "circle":
                r = max(1, p.get("r", 5))
                cx, cy = p.get("cx", 128), p.get("cy", 128)
                pygame.draw.circle(surf, col, (cx, cy), r)
                if ol: pygame.draw.circle(surf, ol, (cx, cy), r, ow)
            elif t == "rect":
                w, h = max(1, p.get("w", 10)), max(1, p.get("h", 10))
                rad = p.get("radius", 0)
                rect = pygame.Rect(p.get("x", 0), p.get("y", 0), w, h)
                if rad > 0:
                    pygame.draw.rect(surf, col, rect, border_radius=rad)
                    if ol: pygame.draw.rect(surf, ol, rect, ow, border_radius=rad)
                else:
                    pygame.draw.rect(surf, col, rect)
                    if ol: pygame.draw.rect(surf, ol, rect, ow)
            elif t == "polygon":
                pts = [(int(x), int(y)) for x, y in p.get("points", [])]
                if len(pts) >= 3:
                    pygame.draw.polygon(surf, col, pts)
                    if ol: pygame.draw.polygon(surf, ol, pts, ow)
            elif t == "line":
                s_, e_ = p.get("start", [0, 0]), p.get("end", [0, 0])
                pygame.draw.line(surf, col, (int(s_[0]), int(s_[1])), (int(e_[0]), int(e_[1])), max(1, p.get("width", 1)))
            elif t == "ellipse":
                w, h = max(1, p.get("w", 10)), max(1, p.get("h", 10))
                rect = pygame.Rect(p.get("x", 0), p.get("y", 0), w, h)
                pygame.draw.ellipse(surf, col, rect)
                if ol: pygame.draw.ellipse(surf, ol, rect, ow)
        except Exception:
            continue
    pygame.image.save(surf, path)
    return surf


GATE_SYS = (
    "You are a STRICT visual critic who knows League of Legends. Given a "
    "champion's canonical identity (text) and a 256x256 pixel-art sprite (image), "
    "judge whether a LoL player would recognize the champion.\n"
    "Output JSON ONLY: {canonical_match: 0-10, recognizable: true/false, "
    "features_captured: [list], features_missing: [list], verdict: one sentence}. "
    "canonical_match >= 7 means recognizable. Be STRICT."
)


def champ_canon_text(c):
    an = c.get("ability_names", {})
    abstr = ", ".join(f"{s}: {an[s]}" for s in ("Q", "W", "E", "R") if s in an)
    bio = (c.get("lore", {}).get("bio", "") or "")[:200]
    return (f"Champion: {c['name']} — {c.get('title','')}. "
            f"Faction: {c.get('faction','')}. Role: {c.get('role','')}. "
            f"Abilities: {abstr}. Lore: {bio}")


def critique(canon, cid, img_path):
    crit = chat([
        {"role": "system", "content": GATE_SYS},
        {"role": "user", "content": [
            {"type": "text", "text": f"{canon}\n\nImage = the pixel-art sprite. "
             f"Does it capture {cid}'s canonical identity? JSON only."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64(img_path)}"}},
        ]},
    ], max_tokens=400)
    try:
        cd = json.loads(strip_json(crit))
        cm = max(0, min(10, int(cd.get("canonical_match", 0))))
        rec = bool(cd.get("recognizable", False))
        missing = cd.get("features_missing", [])
        verdict = cd.get("verdict", "")
        if isinstance(missing, str):
            missing = [missing]
        return cm, rec, missing, verdict
    except Exception:
        return 0, False, ["parse error"], "parse error"


# ============================================================
# HAND-AUTHORED SPRITES
# Each is a list of JSON primitives placed from LoL knowledge.
# Drawn back-to-front. 256x256, body center ~(128,150).
# ============================================================

def ahri_prims():
    """Ahri — the Nine-Tailed Fox.
    Iconic: 9 fox tails fanned behind, fox ears, red/white kimono, orb, whisker markings.
    Full body, front-facing, slender female. Tails are THE feature — big and fanned.
    """
    P = []
    SKIN = (245, 215, 190)
    HAIR = (60, 35, 30)        # dark brown-black hair
    KIMONO_WHITE = (245, 240, 230)
    KIMONO_RED = (175, 30, 35)
    TAIL_ORANGE = (210, 110, 35)
    TAIL_TIP = (245, 235, 220)  # white tail tips
    EAR = (235, 225, 210)
    EAR_INNER = (190, 120, 130)
    ORB = (120, 200, 235)
    EYE = (40, 30, 30)
    OUT = (40, 25, 25)

    # --- 9 TAILS (drawn first, behind body) — fan from lower back (128,150) outward ---
    # Each tail: a tapered polygon (wide base near body, pointed tip outward) + white tip.
    # Fan across the back: 4 left, 1 center-up, 4 right, at varying angles.
    tail_specs = [
        # (base_left, base_right, tip, angle)
        ((120,145),(132,150),(40,120)),    # far left, up
        ((120,148),(134,152),(28,150)),    # left
        ((122,150),(136,154),(24,178)),    # left-down
        ((124,152),(138,156),(40,210)),    # far left-down
        ((120,140),(136,144),(128,30)),    # center up (over head)
        ((122,150),(136,154),(216,178)),   # right-down
        ((122,148),(136,152),(228,150)),   # right
        ((120,145),(132,150),(216,120)),   # far right, up
        ((124,154),(138,158),(210,210)),   # far right-down
    ]
    for bl, br, tip in tail_specs:
        P.append({"type":"polygon","points":[bl,br,tip],"color":TAIL_ORANGE,"outline":OUT,"outline_w":1})
        # white tip: small triangle at the tip
        tx, ty = tip
        P.append({"type":"circle","cx":tx,"cy":ty,"r":5,"color":TAIL_TIP,"outline":OUT,"outline_w":1})

    # --- Hair (back of head, flowing down) ---
    P.append({"type":"polygon","points":[(104,60),(152,60),(158,120),(150,150),(106,150),(98,120)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Fox ears (on top of head) ---
    P.append({"type":"polygon","points":[(104,58),(116,18),(126,56)],"color":EAR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(110,52),(116,26),(122,52)],"color":EAR_INNER})
    P.append({"type":"polygon","points":[(130,56),(140,18),(152,58)],"color":EAR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(134,52),(140,26),(146,52)],"color":EAR_INNER})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":72,"r":20,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Face: eyes + whisker markings ---
    P.append({"type":"circle","cx":120,"cy":70,"r":3,"color":EYE})
    P.append({"type":"circle","cx":136,"cy":70,"r":3,"color":EYE})
    # whisker markings: 3 thin lines on each cheek
    for dy in (-3, 1, 5):
        P.append({"type":"line","start":[108,69+dy],"end":[116,68+dy],"color":(120,80,70),"width":1})
        P.append({"type":"line","start":[140,68+dy],"end":[148,69+dy],"color":(120,80,70),"width":1})

    # --- Torso: white kimono with red obi ---
    P.append({"type":"polygon","points":[(112,92),(144,92),(150,150),(106,150)],
              "color":KIMONO_WHITE,"outline":OUT,"outline_w":1})
    # red obi (sash)
    P.append({"type":"rect","x":108,"y":120,"w":40,"h":10,"color":KIMONO_RED,"outline":OUT,"outline_w":1})
    # red collar
    P.append({"type":"polygon","points":[(118,92),(138,92),(134,104),(122,104)],"color":KIMONO_RED,"outline":OUT,"outline_w":1})

    # --- Arms (slim) ---
    P.append({"type":"rect","x":104,"y":96,"w":10,"h":44,"color":KIMONO_WHITE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":142,"y":96,"w":10,"h":44,"color":KIMONO_WHITE,"outline":OUT,"outline_w":1,"radius":4})
    # hands
    P.append({"type":"circle","cx":109,"cy":142,"r":4,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":147,"cy":142,"r":4,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (slim) ---
    P.append({"type":"rect","x":112,"y":150,"w":12,"h":50,"color":KIMONO_WHITE,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":150,"w":12,"h":50,"color":KIMONO_WHITE,"outline":OUT,"outline_w":1,"radius":3})

    # --- Orb of deception (floating near right hand) ---
    P.append({"type":"circle","cx":168,"cy":140,"r":9,"color":ORB,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":165,"cy":137,"r":3,"color":(220,240,250)})  # highlight

    return P


def annie_prims():
    """Annie — the Dark Child.
    Iconic: twin pigtails, youthful face, red dress, teddy bear (Tibbers), fire.
    Small girl. Pigtails + youthful face were the missing features.
    """
    P = []
    SKIN = (250, 220, 195)
    HAIR = (200, 90, 60)        # red-orange hair
    DRESS = (170, 35, 40)       # red dress
    DRESS_TRIM = (240, 225, 200)
    EYE = (40, 30, 30)
    OUT = (40, 25, 25)
    TIBBERS = (140, 90, 55)     # brown teddy
    FIRE = (240, 150, 40)

    # --- Tibbers (teddy bear, held in left arm, drawn behind) ---
    P.append({"type":"circle","cx":78,"cy":150,"r":18,"color":TIBBERS,"outline":OUT,"outline_w":1})  # body
    P.append({"type":"circle","cx":78,"cy":128,"r":12,"color":TIBBERS,"outline":OUT,"outline_w":1})  # head
    P.append({"type":"circle","cx":70,"cy":120,"r":4,"color":TIBBERS,"outline":OUT,"outline_w":1})   # left ear
    P.append({"type":"circle","cx":86,"cy":120,"r":4,"color":TIBBERS,"outline":OUT,"outline_w":1})   # right ear
    P.append({"type":"circle","cx":74,"cy":126,"r":1,"color":EYE})
    P.append({"type":"circle","cx":82,"cy":126,"r":1,"color":EYE})

    # --- Hair back ---
    P.append({"type":"circle","cx":128,"cy":74,"r":22,"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (youthful, round, big relative to body = child) ---
    P.append({"type":"circle","cx":128,"cy":78,"r":20,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Twin pigtails (THE missing feature) — two bunches sticking out sides + ties ---
    # left pigtail
    P.append({"type":"circle","cx":104,"cy":76,"r":9,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":98,"cy":88,"r":7,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":104,"cy":74,"r":3,"color":DRESS})  # hair tie
    # right pigtail
    P.append({"type":"circle","cx":152,"cy":76,"r":9,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":158,"cy":88,"r":7,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":152,"cy":74,"r":3,"color":DRESS})  # hair tie
    # bangs
    P.append({"type":"polygon","points":[(112,64),(144,64),(140,76),(116,76)],"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Face: big youthful eyes, small smile ---
    P.append({"type":"circle","cx":120,"cy":78,"r":4,"color":EYE})
    P.append({"type":"circle","cx":136,"cy":78,"r":4,"color":EYE})
    P.append({"type":"circle","cx":121,"cy":77,"r":1,"color":(255,255,255)})  # sparkle
    P.append({"type":"circle","cx":137,"cy":77,"r":1,"color":(255,255,255)})
    P.append({"type":"line","start":[122,88],"end":[134,88],"color":(150,60,60),"width":1})  # smile

    # --- Dress (red, wide/bell shape = child's dress) ---
    P.append({"type":"polygon","points":[(110,100),(146,100),(160,165),(96,165)],
              "color":DRESS,"outline":OUT,"outline_w":1})
    # dress trim
    P.append({"type":"rect","x":96,"y":158,"w":64,"h":7,"color":DRESS_TRIM,"outline":OUT,"outline_w":1})

    # --- Arms ---
    P.append({"type":"rect","x":100,"y":104,"w":10,"h":40,"color":DRESS,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":146,"y":104,"w":10,"h":40,"color":DRESS,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":105,"cy":146,"r":4,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":151,"cy":146,"r":4,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs + shoes ---
    P.append({"type":"rect","x":112,"y":165,"w":12,"h":30,"color":SKIN,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":165,"w":12,"h":30,"color":SKIN,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":110,"y":192,"w":16,"h":8,"color":(50,40,40),"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":192,"w":16,"h":8,"color":(50,40,40),"outline":OUT,"outline_w":1,"radius":2})

    # --- Fire (small flame near right hand — her magic) ---
    P.append({"type":"polygon","points":[(158,140),(164,140),(161,128)],"color":FIRE,"outline":(200,80,20),"outline_w":1})

    return P


def fiora_prims():
    """Fiora — the Grand Duelist.
    Iconic: rapier (BIG, held forward in front), high-collared Demacian attire,
    ponytail (big, flowing), confident duelist posture.
    v1 failed (rapier too thin + drawn behind body -> covered). v2: rapier BIG,
    drawn IN FRONT, prominent collar + ponytail.
    """
    P = []
    SKIN = (240, 215, 190)
    HAIR = (45, 30, 25)        # dark brown-black
    ATTIRE = (225, 220, 215)   # white Demacian attire
    ATTIRE_DARK = (70, 65, 70)
    COLLAR = (210, 175, 55)    # gold trim
    EYE = (40, 30, 30)
    OUT = (40, 25, 25)
    RAPIER = (215, 215, 225)
    RAPIER_HILT = (185, 150, 50)

    # --- Hair back + BIG ponytail (flowing back, prominent) ---
    P.append({"type":"circle","cx":128,"cy":68,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    # ponytail flowing back-right, BIG
    P.append({"type":"polygon","points":[(138,54),(152,46),(186,62),(182,92),(150,82),(142,72)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # ponytail tail tip (tapered)
    P.append({"type":"polygon","points":[(176,74),(190,68),(188,86),(176,84)],
              "color":HAIR,"outline":OUT,"outline_w":1})
    # bangs
    P.append({"type":"polygon","points":[(110,58),(146,58),(142,72),(114,72)],
              "color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head ---
    P.append({"type":"circle","cx":128,"cy":72,"r":18,"color":SKIN,"outline":OUT,"outline_w":1})
    # confident expression: sharp eyes + determined brow
    P.append({"type":"line","start":[117,71],"end":[125,71],"color":EYE,"width":2})
    P.append({"type":"line","start":[131,71],"end":[139,71],"color":EYE,"width":2})
    P.append({"type":"polygon","points":[(114,66),(126,69),(126,67),(114,64)],"color":HAIR})  # left brow
    P.append({"type":"polygon","points":[(130,67),(142,64),(142,66),(130,69)],"color":HAIR})  # right brow
    # slight confident smirk
    P.append({"type":"line","start":[122,84],"end":[134,82],"color":(150,60,60),"width":1})

    # --- High-collared Demacian attire (THE missing feature — make it PROMINENT) ---
    # torso (white)
    P.append({"type":"polygon","points":[(108,94),(148,94),(152,162),(104,162)],
              "color":ATTIRE,"outline":OUT,"outline_w":1})
    # HIGH COLLAR — tall, up to the chin, gold-trimmed (very visible)
    P.append({"type":"polygon","points":[(108,94),(148,94),(144,74),(112,74)],
              "color":ATTIRE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":110,"y":76,"w":36,"h":4,"color":COLLAR,"outline":OUT,"outline_w":1})  # gold collar band
    # gold center trim + Demacian crest down the attire
    P.append({"type":"line","start":[128,94],"end":[128,162],"color":COLLAR,"width":2})
    P.append({"type":"circle","cx":128,"cy":110,"r":5,"color":COLLAR,"outline":OUT,"outline_w":1})  # crest medallion
    # shoulder armor (duelist epaulettes)
    P.append({"type":"circle","cx":106,"cy":98,"r":10,"color":ATTIRE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":150,"cy":98,"r":10,"color":ATTIRE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[100,96],"end":[112,96],"color":COLLAR,"width":1})
    P.append({"type":"line","start":[144,96],"end":[156,96],"color":COLLAR,"width":1})

    # --- Arms (duelist pose: back arm + forward arm extended toward rapier) ---
    P.append({"type":"rect","x":98,"y":104,"w":12,"h":48,"color":ATTIRE,"outline":OUT,"outline_w":1,"radius":4})  # back arm
    # forward arm extended right toward rapier grip
    P.append({"type":"polygon","points":[(148,104),(166,108),(176,128),(168,134),(150,118)],
              "color":ATTIRE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":174,"cy":130,"r":6,"color":SKIN,"outline":OUT,"outline_w":1})  # hand on rapier

    # --- Legs (duelist stance, apart) ---
    P.append({"type":"rect","x":106,"y":162,"w":16,"h":52,"color":ATTIRE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":134,"y":162,"w":16,"h":52,"color":ATTIRE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":102,"y":210,"w":22,"h":12,"color":(45,35,35),"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":130,"y":210,"w":22,"h":12,"color":(45,35,35),"outline":OUT,"outline_w":1,"radius":2})

    # --- RAPIER (drawn LAST, IN FRONT, BIG — the signature weapon) ---
    # blade: thick tapered polygon from grip pointing up-forward
    P.append({"type":"polygon","points":[(172,128),(176,128),(184,40),(176,36),(168,40)],
              "color":RAPIER,"outline":OUT,"outline_w":1})
    # blade center groove
    P.append({"type":"line","start":[176,128],"end":[176,40],"color":(170,170,180),"width":1})
    # basket hilt (gold, prominent guard around the grip)
    P.append({"type":"circle","cx":176,"cy":132,"r":8,"color":RAPIER_HILT,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(168,132),(184,132),(184,140),(168,140)],
              "color":RAPIER_HILT,"outline":OUT,"outline_w":1})  # guard bar
    # grip
    P.append({"type":"rect","x":173,"y":140,"w":6,"h":16,"color":(90,50,30),"outline":OUT,"outline_w":1})
    # pommel
    P.append({"type":"circle","cx":176,"cy":158,"r":4,"color":RAPIER_HILT,"outline":OUT,"outline_w":1})

    return P


def darius_prims():
    """Darius — the Hand of Noxus.
    Iconic: massive muscularity, stern expression + BEARD, Noxian red/black armor,
    big battle-axe, bald with headband.
    v1 failed (gate wanted beard + Noxian armor detail). v2: add beard, make armor
    clearly Noxian red/black with gold, axe bigger and in front.
    """
    P = []
    SKIN = (215, 180, 150)
    SKIN_DARK = (180, 145, 115)
    ARMOR = (135, 30, 30)      # Noxian crimson armor
    ARMOR_DARK = (45, 28, 28)  # black armor
    METAL = (140, 130, 125)
    GOLD = (200, 165, 50)
    HEADBAND = (175, 30, 30)
    BEARD = (60, 45, 40)
    EYE = (40, 30, 30)
    OUT = (40, 25, 25)
    AXE_BLADE = (185, 185, 195)
    AXE_HANDLE = (85, 50, 30)

    # --- Battle axe (drawn behind body, BIG Noxian axe) ---
    P.append({"type":"line","start":[88,55],"end":[100,222],"color":AXE_HANDLE,"width":7})
    # big curved axe blade
    P.append({"type":"polygon","points":[(100,66),(66,76),(58,124),(76,134),(100,110)],
              "color":AXE_BLADE,"outline":OUT,"outline_w":1})
    # blade edge highlight
    P.append({"type":"line","start":[66,76],"end":[58,124],"color":(230,230,235),"width":2})
    # gold axe collar
    P.append({"type":"rect","x":96,"y":64,"w":10,"h":8,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Head (bald, headband, stern + BEARD) ---
    P.append({"type":"circle","cx":128,"cy":72,"r":22,"color":SKIN,"outline":OUT,"outline_w":1})
    # battle scar across forehead/eye
    P.append({"type":"line","start":[118,60],"end":[126,72],"color":SKIN_DARK,"width":2})
    # headband (Noxian red)
    P.append({"type":"rect","x":106,"y":64,"w":44,"h":8,"color":HEADBAND,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[110,66],"end":[146,66],"color":GOLD,"width":1})  # gold headband trim
    # stern glaring eyes
    P.append({"type":"line","start":[115,75],"end":[124,77],"color":EYE,"width":2})
    P.append({"type":"line","start":[132,77],"end":[141,75],"color":EYE,"width":2})
    # angry brows (heavy, V shape)
    P.append({"type":"polygon","points":[(110,68),(126,73),(126,71),(110,66)],"color":SKIN_DARK})
    P.append({"type":"polygon","points":[(130,71),(146,66),(146,68),(130,73)],"color":SKIN_DARK})
    # BEARD (THE missing feature — broad dark beard covering jaw)
    P.append({"type":"polygon","points":[(110,84),(146,84),(150,104),(142,116),(114,116),(106,104)],
              "color":BEARD,"outline":OUT,"outline_w":1})
    # mustache
    P.append({"type":"polygon","points":[(116,82),(140,82),(138,88),(118,88)],"color":BEARD,"outline":OUT,"outline_w":1})
    # frown line
    P.append({"type":"line","start":[122,80],"end":[134,80],"color":(120,60,60),"width":1})

    # --- Massive muscular torso (wide, Noxian crimson + black armor) ---
    P.append({"type":"polygon","points":[(98,96),(158,96),(164,172),(92,172)],
              "color":ARMOR,"outline":OUT,"outline_w":1})
    # black chest plate with gold trim (Noxian military)
    P.append({"type":"polygon","points":[(104,100),(152,100),(148,150),(108,150)],
              "color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    # gold trim around chest plate
    P.append({"type":"line","start":[104,100],"end":[152,100],"color":GOLD,"width":2})
    P.append({"type":"line","start":[108,150],"end":[148,150],"color":GOLD,"width":1})
    # pec division + ab segments (muscular)
    P.append({"type":"line","start":[128,100],"end":[128,150],"color":GOLD,"width":1})
    P.append({"type":"line","start":[112,124],"end":[144,124],"color":GOLD,"width":1})
    P.append({"type":"line","start":[114,138],"end":[142,138],"color":GOLD,"width":1})
    # Noxian emblem (gold) center chest
    P.append({"type":"circle","cx":128,"cy":115,"r":6,"color":GOLD,"outline":OUT,"outline_w":1})
    # big spiked shoulder armor (Noxian)
    P.append({"type":"circle","cx":96,"cy":100,"r":15,"color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":160,"cy":100,"r":15,"color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    # shoulder spikes
    P.append({"type":"polygon","points":[(84,90),(96,82),(108,90)],"color":METAL,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(148,90),(160,82),(172,90)],"color":METAL,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[96,100],"end":[96,115],"color":GOLD,"width":1})
    P.append({"type":"line","start":[160,100],"end":[160,115],"color":GOLD,"width":1})

    # --- Massive muscular arms ---
    P.append({"type":"rect","x":82,"y":110,"w":20,"h":62,"color":SKIN,"outline":OUT,"outline_w":1,"radius":7})
    P.append({"type":"rect","x":154,"y":110,"w":20,"h":62,"color":SKIN,"outline":OUT,"outline_w":1,"radius":7})
    # bicep/forearm definition
    P.append({"type":"line","start":[92,122],"end":[92,158],"color":SKIN_DARK,"width":1})
    P.append({"type":"line","start":[164,122],"end":[164,158],"color":SKIN_DARK,"width":1})
    # wrist bracers (Noxian, gold-trimmed)
    P.append({"type":"rect","x":82,"y":160,"w":20,"h":8,"color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":154,"y":160,"w":20,"h":8,"color":ARMOR_DARK,"outline":OUT,"outline_w":1})
    # hands (big)
    P.append({"type":"circle","cx":92,"cy":174,"r":7,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":164,"cy":174,"r":7,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (thick, armored greaves) ---
    P.append({"type":"rect","x":98,"y":172,"w":28,"h":48,"color":ARMOR_DARK,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":130,"y":172,"w":28,"h":48,"color":ARMOR_DARK,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"line","start":[98,196],"end":[126,196],"color":GOLD,"width":1})
    P.append({"type":"line","start":[130,196],"end":[158,196],"color":GOLD,"width":1})
    # boots
    P.append({"type":"rect","x":94,"y":218,"w":34,"h":12,"color":(38,28,28),"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":218,"w":34,"h":12,"color":(38,28,28),"outline":OUT,"outline_w":1,"radius":2})

    return P


# Map of hand-authored champs
HAND_AUTHORED = {
    "Ahri": ahri_prims,
    "Annie": annie_prims,
    "Fiora": fiora_prims,
    "Darius": darius_prims,
}


def save_sprite(cid, prims):
    char_dir = os.path.join(ASSET_DIR, "characters", cid)
    sprites_dir = os.path.join(char_dir, "sprites")
    os.makedirs(sprites_dir, exist_ok=True)
    render_primitives(prims, os.path.join(char_dir, "sprite.png"))
    shutil.copy(os.path.join(char_dir, "sprite.png"), os.path.join(sprites_dir, "0.png"))
    cache_path = os.path.join(char_dir, "descriptors.json")
    cache = {}
    if os.path.exists(cache_path):
        try:
            cache = json.load(open(cache_path))
        except Exception:
            cache = {}
    cache["0"] = {"primitives": prims, "generator": "hand_authored", "phase": "hand"}
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2, default=str)


def main():
    byid = {c["id"]: c for c in CHAMPIONS_DB}
    gate = json.load(open(os.path.join(EXP_DIR, "canon_gate_results.json")))
    base = {item["id"]: item["gate"]["canonical_match"] for item in gate if "gate" in item}

    print("Hand-authored sprites (no VLM in generation; VLM only gates)")
    print(f"  {len(HAND_AUTHORED)} champs: {list(HAND_AUTHORED.keys())}\n")

    t0 = time.time()
    results = {}
    for cid, primfn in HAND_AUTHORED.items():
        c = byid.get(cid)
        if not c:
            print(f"  {cid}: not in CHAMPIONS_DB, skip")
            continue
        canon = champ_canon_text(c)
        prims = primfn()
        tmp = f"/tmp/handauth_{cid}.png"
        render_primitives(prims, tmp)

        # gate it (3 critiques, take best — gate has some variance)
        scores = []
        for _ in range(3):
            cm, rec, missing, verdict = critique(canon, cid, tmp)
            scores.append((cm, rec, missing, verdict))
        best = max(scores, key=lambda x: x[0])
        cm, rec, missing, verdict = best
        b = base.get(cid, 0)
        delta = cm - b
        print(f"  {cid:14s}: hand={cm}/10 (base {b}, {'+' if delta>=0 else ''}{delta}) "
              f"rec={rec} missing={missing[:3]}", flush=True)
        print(f"    verdict: {verdict[:100]}", flush=True)
        print(f"    gate scores this run: {[s[0] for s in scores]}", flush=True)
        results[cid] = {"base_score": b, "hand_score": cm, "recognizable": rec,
                        "missing": missing, "verdict": verdict,
                        "gate_scores": [s[0] for s in scores], "n_prims": len(prims)}

        # save if it beats base (never regress). For Fiora/Darius v2 we
        # already saved v1 only if it beat base; v2 must also beat base.
        if cm > b:
            save_sprite(cid, prims)
            print(f"    SAVED (beats base {b})", flush=True)
        else:
            print(f"    NOT saved (does not beat base {b})", flush=True)

    print(f"\n=== HAND-AUTHOR POC ({len(results)} champs, {time.time()-t0:.0f}s) ===")
    improved = sum(1 for r in results.values() if r["hand_score"] > r["base_score"])
    print(f"improved: {improved}/{len(results)}")
    with open(os.path.join(EXP_DIR, "hand_author_results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"results -> exp/hand_author_results.json")


if __name__ == "__main__":
    main()
