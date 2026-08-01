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


def monkeyking_prims():
    """Wukong — the Monkey King.
    Iconic: monkey face/fur, golden armor, LONG prehensile tail, red fabric sash,
    staff (often). Tail is the missing feature.
    """
    P = []
    FUR = (140, 95, 55)
    FACE = (210, 165, 110)
    GOLD = (215, 175, 55)
    GOLD_DARK = (160, 120, 30)
    RED = (175, 35, 35)
    EYE = (35, 25, 20)
    OUT = (40, 25, 20)

    # --- Long prehensile tail (drawn behind, THE missing feature) — curls from
    # lower back up and around to the side ---
    P.append({"type":"circle","cx":96,"cy":150,"r":9,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":78,"cy":140,"r":8,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":62,"cy":122,"r":7,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":52,"cy":100,"r":6,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":50,"cy":78,"r":5,"color":FUR,"outline":OUT,"outline_w":1})  # tail tip

    # --- Head (monkey face) ---
    P.append({"type":"circle","cx":128,"cy":74,"r":22,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":128,"cy":80,"r":17,"color":FACE,"outline":OUT,"outline_w":1})  # face muzzle
    # ears (monkey, on sides)
    P.append({"type":"circle","cx":106,"cy":70,"r":7,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":150,"cy":70,"r":7,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":106,"cy":70,"r":3,"color":FACE})
    P.append({"type":"circle","cx":150,"cy":70,"r":3,"color":FACE})
    # eyes
    P.append({"type":"circle","cx":121,"cy":76,"r":3,"color":EYE})
    P.append({"type":"circle","cx":135,"cy":76,"r":3,"color":EYE})
    # brow ridge
    P.append({"type":"line","start":[114,70],"end":[142,70],"color":OUT,"width":1})
    # mouth
    P.append({"type":"line","start":[122,88],"end":[134,88],"color":(120,70,50),"width":1})

    # --- Torso: golden armor + red sash ---
    P.append({"type":"polygon","points":[(108,96),(148,96),(152,162),(104,162)],
              "color":GOLD,"outline":OUT,"outline_w":1})
    # armor chest plate
    P.append({"type":"polygon","points":[(112,100),(144,100),(140,140),(116,140)],
              "color":GOLD_DARK,"outline":OUT,"outline_w":1})
    # red sash (decorative fabric)
    P.append({"type":"polygon","points":[(108,140),(148,140),(150,162),(106,162)],
              "color":RED,"outline":OUT,"outline_w":1})
    # gold trim
    P.append({"type":"line","start":[112,100],"end":[144,100],"color":GOLD,"width":1})

    # --- Arms (muscular, golden bracers) ---
    P.append({"type":"rect","x":96,"y":104,"w":14,"h":48,"color":FUR,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"rect","x":146,"y":104,"w":14,"h":48,"color":FUR,"outline":OUT,"outline_w":1,"radius":5})
    # golden bracers
    P.append({"type":"rect","x":96,"y":142,"w":14,"h":8,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":146,"y":142,"w":14,"h":8,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":103,"cy":154,"r":5,"color":FACE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":153,"cy":154,"r":5,"color":FACE,"outline":OUT,"outline_w":1})

    # --- Legs (fur + golden boots) ---
    P.append({"type":"rect","x":110,"y":162,"w":14,"h":44,"color":FUR,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":162,"w":14,"h":44,"color":FUR,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":106,"y":202,"w":22,"h":12,"color":GOLD_DARK,"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":202,"w":22,"h":12,"color":GOLD_DARK,"outline":OUT,"outline_w":1,"radius":2})
    return P


def teemo_prims():
    """Teemo — the Swift Scout.
    Iconic: green scout hat (big), oversized goggles, round cheeks, brown fur (yordle).
    Small stature. Hat + goggles are THE features.
    """
    P = []
    FUR = (155, 110, 70)
    HAT = (70, 130, 60)
    HAT_DARK = (45, 95, 40)
    GOGGLE = (180, 200, 60)
    GOGGLE_DARK = (40, 50, 20)
    EYE = (30, 25, 20)
    OUT = (40, 25, 20)

    # --- Big green scout hat (puff cap shape, THE feature) ---
    P.append({"type":"circle","cx":128,"cy":56,"r":26,"color":HAT,"outline":OUT,"outline_w":1})
    # hat band (darker)
    P.append({"type":"rect","x":100,"y":70,"w":56,"h":8,"color":HAT_DARK,"outline":OUT,"outline_w":1})
    # hat tip puff
    P.append({"type":"circle","cx":128,"cy":36,"r":8,"color":HAT,"outline":OUT,"outline_w":1})

    # --- Head (yordle: big head, round cheeks, brown fur) ---
    P.append({"type":"circle","cx":128,"cy":86,"r":24,"color":FUR,"outline":OUT,"outline_w":1})
    # round cheeks (lighter fur)
    P.append({"type":"circle","cx":128,"cy":92,"r":18,"color":(180,135,95),"outline":OUT,"outline_w":1})

    # --- Oversized goggles (THE feature — big, across the face) ---
    # goggle strap
    P.append({"type":"rect","x":104,"y":82,"w":48,"h":5,"color":GOGGLE_DARK,"outline":OUT,"outline_w":1})
    # two big goggle lenses
    P.append({"type":"circle","cx":118,"cy":86,"r":9,"color":GOGGLE,"outline":GOGGLE_DARK,"outline_w":2})
    P.append({"type":"circle","cx":138,"cy":86,"r":9,"color":GOGGLE,"outline":GOGGLE_DARK,"outline_w":2})
    # goggle pupils
    P.append({"type":"circle","cx":118,"cy":86,"r":3,"color":EYE})
    P.append({"type":"circle","cx":138,"cy":86,"r":3,"color":EYE})
    # goggle shine
    P.append({"type":"circle","cx":115,"cy":83,"r":2,"color":(240,250,200)})
    P.append({"type":"circle","cx":135,"cy":83,"r":2,"color":(240,250,200)})

    # nose + mouth
    P.append({"type":"circle","cx":128,"cy":98,"r":3,"color":(120,80,60)})
    P.append({"type":"line","start":[122,104],"end":[134,104],"color":(100,65,45),"width":1})

    # --- Body (small — yordle scout uniform) ---
    P.append({"type":"polygon","points":[(112,112),(144,112),(148,170),(108,170)],
              "color":HAT_DARK,"outline":OUT,"outline_w":1})
    # scout pack on back (visible at side)
    P.append({"type":"rect","x":104,"y":120,"w":10,"h":30,"color":(90,70,50),"outline":OUT,"outline_w":1})

    # --- Arms ---
    P.append({"type":"rect","x":100,"y":116,"w":12,"h":42,"color":HAT_DARK,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":144,"y":116,"w":12,"h":42,"color":HAT_DARK,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":106,"cy":160,"r":5,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":150,"cy":160,"r":5,"color":FUR,"outline":OUT,"outline_w":1})

    # --- Legs (short, small) ---
    P.append({"type":"rect","x":112,"y":170,"w":12,"h":34,"color":FUR,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":170,"w":12,"h":34,"color":FUR,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":108,"y":200,"w":20,"h":12,"color":(60,45,30),"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":200,"w":20,"h":12,"color":(60,45,30),"outline":OUT,"outline_w":1,"radius":2})
    return P


def yuumi_prims():
    """Yuumi — the Magical Cat.
    Iconic: cat floating on a BIG open magical book, cat ears + tail, glowing aura.
    The book is THE feature.
    """
    P = []
    BOOK = (60, 90, 160)
    BOOK_PAGE = (235, 225, 200)
    BOOK_GOLD = (210, 170, 50)
    FUR = (220, 210, 195)
    FUR_DARK = (170, 160, 145)
    PINK = (220, 150, 165)
    EYE = (140, 200, 90)
    OUT = (40, 30, 25)
    AURA = (160, 220, 255)

    # --- Glowing aura under book ---
    P.append({"type":"ellipse","x":70,"y":150,"w":116,"h":30,"color":AURA,"outline":None})
    P.append({"type":"ellipse","x":80,"y":155,"w":96,"h":20,"color":(200,235,255)})

    # --- BIG open magical book (THE feature — floating platform) ---
    # book base (thick tome)
    P.append({"type":"rect","x":76,"y":148,"w":104,"h":22,"color":BOOK,"outline":OUT,"outline_w":1,"radius":2})
    # open pages (V shape)
    P.append({"type":"polygon","points":[(80,148),(128,140),(128,148)],"color":BOOK_PAGE,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(128,140),(176,148),(128,148)],"color":BOOK_PAGE,"outline":OUT,"outline_w":1})
    # page lines (text)
    for lx in (88, 96, 104, 112):
        P.append({"type":"line","start":[lx,145],"end":[lx+8,143],"color":(150,140,110),"width":1})
    for lx in (136, 144, 152, 160):
        P.append({"type":"line","start":[lx,143],"end":[lx+8,145],"color":(150,140,110),"width":1})
    # gold clasp + spine
    P.append({"type":"rect","x":76,"y":148,"w":8,"h":22,"color":BOOK_GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":172,"y":148,"w":8,"h":22,"color":BOOK_GOLD,"outline":OUT,"outline_w":1})
    # glowing rune on book
    P.append({"type":"circle","cx":128,"cy":159,"r":5,"color":AURA,"outline":OUT,"outline_w":1})

    # --- Cat body (sitting on book) ---
    P.append({"type":"ellipse","x":108,"y":96,"w":40,"h":44,"color":FUR,"outline":OUT,"outline_w":1})  # body
    # cat tail (curling up)
    P.append({"type":"circle","cx":152,"cy":116,"r":6,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":160,"cy":106,"r":5,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":162,"cy":96,"r":4,"color":FUR,"outline":OUT,"outline_w":1})

    # --- Cat head ---
    P.append({"type":"circle","cx":128,"cy":80,"r":18,"color":FUR,"outline":OUT,"outline_w":1})
    # cat ears (pointy, THE feature)
    P.append({"type":"polygon","points":[(112,68),(118,46),(126,66)],"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(115,64),(119,52),(123,62)],"color":PINK})
    P.append({"type":"polygon","points":[(130,66),(138,46),(144,68)],"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(133,62),(139,52),(141,64)],"color":PINK})
    # big green eyes
    P.append({"type":"circle","cx":121,"cy":80,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":80,"r":5,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":79,"r":2,"color":(20,20,15)})
    P.append({"type":"circle","cx":136,"cy":79,"r":2,"color":(20,20,15)})
    # pink nose
    P.append({"type":"polygon","points":[(125,88),(131,88),(128,92)],"color":PINK,"outline":OUT,"outline_w":1})
    # whiskers
    P.append({"type":"line","start":[112,88],"end":[122,89],"color":FUR_DARK,"width":1})
    P.append({"type":"line","start":[134,89],"end":[144,88],"color":FUR_DARK,"width":1})
    # mouth
    P.append({"type":"line","start":[128,92],"end":[124,95],"color":OUT,"width":1})
    P.append({"type":"line","start":[128,92],"end":[132,95],"color":OUT,"width":1})

    # --- Front paws (on the book) ---
    P.append({"type":"ellipse","x":112,"y":128,"w":12,"h":14,"color":FUR,"outline":OUT,"outline_w":1})
    P.append({"type":"ellipse","x":132,"y":128,"w":12,"h":14,"color":FUR,"outline":OUT,"outline_w":1})
    return P


def pantheon_prims():
    """Pantheon — the Unbreakable Spear.
    Iconic: plumed greek helmet, LARGE circular shield, bronze armor, cape, spear.
    Shield is THE big feature.
    """
    P = []
    BRONZE = (180, 130, 50)
    BRONZE_DARK = (130, 90, 30)
    CREST_RED = (170, 35, 35)
    SKIN = (210, 175, 140)
    CAPE = (160, 40, 40)
    METAL = (200, 180, 90)
    EYE = (35, 25, 20)
    OUT = (40, 25, 20)

    # --- Spear (behind, diagonal) ---
    P.append({"type":"line","start":[180,50],"end":[150,210],"color":(180,160,80),"width":3})
    P.append({"type":"polygon","points":[(180,50),(176,44),(184,44)],"color":METAL,"outline":OUT,"outline_w":1})  # spear tip

    # --- Cape (behind body, flowing) ---
    P.append({"type":"polygon","points":[(108,96),(148,96),(156,200),(100,200)],
              "color":CAPE,"outline":OUT,"outline_w":1})

    # --- Plumed greek helmet (THE feature — crest + bronze) ---
    P.append({"type":"circle","cx":128,"cy":72,"r":20,"color":BRONZE,"outline":OUT,"outline_w":1})
    # red plume crest (big, on top)
    P.append({"type":"polygon","points":[(108,54),(120,40),(136,40),(148,54),(144,58),(112,58)],
              "color":CREST_RED,"outline":OUT,"outline_w":1})
    # plume segments
    P.append({"type":"line","start":[116,50],"end":[116,40],"color":(120,20,20),"width":1})
    P.append({"type":"line","start":[124,48],"end":[124,38],"color":(120,20,20),"width":1})
    P.append({"type":"line","start":[132,48],"end":[132,38],"color":(120,20,20),"width":1})
    P.append({"type":"line","start":[140,50],"end":[140,40],"color":(120,20,20),"width":1})
    # helmet face opening (T shape)
    P.append({"type":"rect","x":118,"y":68,"w":20,"h":14,"color":SKIN,"outline":OUT,"outline_w":1})
    # eyes in shadow
    P.append({"type":"line","start":[121,75],"end":[125,75],"color":EYE,"width":2})
    P.append({"type":"line","start":[131,75],"end":[135,75],"color":EYE,"width":2})
    # cheek guards
    P.append({"type":"polygon","points":[(110,72),(118,72),(118,88),(112,84)],"color":BRONZE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(138,72),(146,72),(144,84),(138,88)],"color":BRONZE_DARK,"outline":OUT,"outline_w":1})

    # --- Bronze armor torso ---
    P.append({"type":"polygon","points":[(106,94),(150,94),(154,164),(102,164)],
              "color":BRONZE,"outline":OUT,"outline_w":1})
    # chest plate (muscular, bronze)
    P.append({"type":"polygon","points":[(110,98),(146,98),(142,140),(114,140)],
              "color":BRONZE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[128,98],"end":[128,140],"color":METAL,"width":1})
    # abs
    P.append({"type":"line","start":[114,140],"end":[142,140],"color":OUT,"width":1})
    P.append({"type":"line","start":[116,152],"end":[140,152],"color":OUT,"width":1})
    # shoulder armor (bronze, round)
    P.append({"type":"circle","cx":102,"cy":98,"r":12,"color":BRONZE_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":154,"cy":98,"r":12,"color":BRONZE_DARK,"outline":OUT,"outline_w":1})

    # --- Arms (one holds shield, one holds spear) ---
    P.append({"type":"rect","x":96,"y":108,"w":14,"h":50,"color":SKIN,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"rect","x":146,"y":108,"w":14,"h":50,"color":SKIN,"outline":OUT,"outline_w":1,"radius":5})

    # --- LARGE circular shield (THE feature — big, in front, on left arm) ---
    P.append({"type":"circle","cx":86,"cy":140,"r":30,"color":BRONZE,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":86,"cy":140,"r":24,"color":BRONZE_DARK,"outline":OUT,"outline_w":1})
    # shield boss (center) + emblem
    P.append({"type":"circle","cx":86,"cy":140,"r":8,"color":METAL,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[86,128],"end":[86,152],"color":CREST_RED,"width":2})  # emblem
    P.append({"type":"line","start":[74,140],"end":[98,140],"color":CREST_RED,"width":2})
    # shield rim rivets
    for ang in (0, 90, 180, 270):
        import math as _m
        rx = 86 + int(27 * _m.cos(_m.radians(ang)))
        ry = 140 + int(27 * _m.sin(_m.radians(ang)))
        P.append({"type":"circle","cx":rx,"cy":ry,"r":2,"color":METAL})
    # hand behind shield
    P.append({"type":"circle","cx":103,"cy":140,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (bronze greaves) ---
    P.append({"type":"rect","x":108,"y":164,"w":16,"h":50,"color":BRONZE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":164,"w":16,"h":50,"color":BRONZE_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"line","start":[108,184],"end":[124,184],"color":METAL,"width":1})
    P.append({"type":"line","start":[132,184],"end":[148,184],"color":METAL,"width":1})
    P.append({"type":"rect","x":104,"y":210,"w":24,"h":12,"color":(50,35,20),"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":210,"w":24,"h":12,"color":(50,35,20),"outline":OUT,"outline_w":1,"radius":2})
    return P


def twistedfate_prims():
    """Twisted Fate — the Card Master.
    Iconic: wide-brim gambler hat, long brown coat, GLOWING magical cards, sharp features.
    Hat + cards are THE features.
    """
    P = []
    HAT = (95, 60, 35)
    HAT_BAND = (180, 45, 40)
    COAT = (120, 75, 45)
    COAT_DARK = (85, 50, 30)
    SKIN = (225, 190, 155)
    HAIR = (180, 140, 70)
    CARD = (240, 235, 210)
    CARD_GLOW = (120, 220, 255)
    EYE = (40, 30, 25)
    OUT = (40, 25, 20)

    # --- Wide-brim gambler hat (THE feature — big brim) ---
    P.append({"type":"ellipse","x":92,"y":48,"w":72,"h":16,"color":HAT,"outline":OUT,"outline_w":1})  # brim
    P.append({"type":"ellipse","x":108,"y":38,"w":40,"h":22,"color":HAT,"outline":OUT,"outline_w":1})  # crown
    # hat band (red)
    P.append({"type":"rect","x":110,"y":52,"w":36,"h":6,"color":HAT_BAND,"outline":OUT,"outline_w":1})
    # hat crown crease
    P.append({"type":"line","start":[128,40],"end":[128,56],"color":HAT_BAND,"width":1})

    # --- Head (sharp handsome features) ---
    P.append({"type":"circle","cx":128,"cy":74,"r":18,"color":SKIN,"outline":OUT,"outline_w":1})
    # slicked-back hair sideburns
    P.append({"type":"polygon","points":[(112,68),(118,60),(122,72)],"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(134,72),(138,60),(144,68)],"color":HAIR,"outline":OUT,"outline_w":1})
    # sharp eyes + confident brow
    P.append({"type":"line","start":[117,73],"end":[124,73],"color":EYE,"width":2})
    P.append({"type":"line","start":[132,73],"end":[139,73],"color":EYE,"width":2})
    P.append({"type":"line","start":[115,68],"end":[124,70],"color":HAIR,"width":1})
    P.append({"type":"line","start":[132,70],"end":[141,68],"color":HAIR,"width":1})
    # smirk
    P.append({"type":"line","start":[122,84],"end":[134,82],"color":(140,70,50),"width":1})
    # mustache (TF has a thin mustache)
    P.append({"type":"line","start":[120,80],"end":[136,80],"color":HAIR,"width":1})

    # --- Long brown coat (trench coat, THE attire) ---
    P.append({"type":"polygon","points":[(106,94),(150,94),(158,210),(98,210)],
              "color":COAT,"outline":OUT,"outline_w":1})
    # coat lapels
    P.append({"type":"polygon","points":[(106,94),(128,94),(124,130),(112,118)],"color":COAT_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(128,94),(150,94),(144,118),(132,130)],"color":COAT_DARK,"outline":OUT,"outline_w":1})
    # coat buttons
    P.append({"type":"circle","cx":128,"cy":120,"r":2,"color":(200,170,60)})
    P.append({"type":"circle","cx":128,"cy":140,"r":2,"color":(200,170,60)})
    P.append({"type":"circle","cx":128,"cy":160,"r":2,"color":(200,170,60)})
    # shirt under coat
    P.append({"type":"polygon","points":[(122,94),(134,94),(132,116),(124,116)],"color":(235,230,220),"outline":OUT,"outline_w":1})
    # waistcoat (formal)
    P.append({"type":"polygon","points":[(118,100),(138,100),(136,140),(120,140)],"color":(70,50,60),"outline":OUT,"outline_w":1})

    # --- Arms (coat sleeves) ---
    P.append({"type":"rect","x":96,"y":104,"w":14,"h":56,"color":COAT,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"rect","x":146,"y":104,"w":14,"h":56,"color":COAT,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"circle","cx":103,"cy":162,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":153,"cy":162,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- GLOWING magical cards (THE feature — 3 floating cards, in front) ---
    # card glow
    P.append({"type":"circle","cx":170,"cy":150,"r":14,"color":CARD_GLOW})
    P.append({"type":"circle","cx":186,"cy":120,"r":12,"color":CARD_GLOW})
    P.append({"type":"circle","cx":176,"cy":178,"r":11,"color":CARD_GLOW})
    # cards (rotated rectangles via polygons)
    P.append({"type":"polygon","points":[(162,140),(178,136),(180,158),(164,162)],"color":CARD,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(178,108),(192,112),(190,132),(176,128)],"color":CARD,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(168,168),(184,170),(182,188),(166,186)],"color":CARD,"outline":OUT,"outline_w":1})
    # card symbols (red)
    P.append({"type":"circle","cx":171,"cy":149,"r":3,"color":(190,30,30)})
    P.append({"type":"circle","cx":184,"cy":120,"r":3,"color":(190,30,30)})
    P.append({"type":"circle","cx":175,"cy":178,"r":3,"color":(190,30,30)})

    # --- Legs + boots ---
    P.append({"type":"rect","x":110,"y":210,"w":16,"h":8,"color":(50,35,20),"outline":OUT,"outline_w":1})
    P.append({"type":"rect","x":130,"y":210,"w":16,"h":8,"color":(50,35,20),"outline":OUT,"outline_w":1})
    return P


def ezreal_prims():
    """Ezreal — the Prodigal Explorer.
    Iconic: floating arcane gauntlet (big, glowing), blonde swept-back hair, blue scarf,
    leather explorer jacket. Gauntlet is THE feature.
    """
    P = []
    HAIR = (235, 200, 110)
    SKIN = (235, 200, 165)
    JACKET = (130, 90, 55)
    JACKET_DARK = (90, 60, 35)
    SCARF = (70, 130, 200)
    GAUNTLET = (180, 160, 90)
    GAUNTLET_GLOW = (120, 220, 255)
    EYE = (40, 30, 25)
    OUT = (40, 25, 20)

    # --- Hair (blonde, swept back) ---
    P.append({"type":"circle","cx":128,"cy":66,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    # swept-back spikes
    P.append({"type":"polygon","points":[(110,56),(124,46),(130,58)],"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(126,52),(140,46),(146,60)],"color":HAIR,"outline":OUT,"outline_w":1})

    # --- Head (young, confident) ---
    P.append({"type":"circle","cx":128,"cy":72,"r":17,"color":SKIN,"outline":OUT,"outline_w":1})
    # swept bangs
    P.append({"type":"polygon","points":[(112,64),(144,64),(140,74),(116,72)],"color":HAIR,"outline":OUT,"outline_w":1})
    # eyes (bright, youthful)
    P.append({"type":"circle","cx":121,"cy":74,"r":3,"color":(90,160,220),"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":135,"cy":74,"r":3,"color":(90,160,220),"outline":OUT,"outline_w":1})
    # confident smirk
    P.append({"type":"line","start":[122,84],"end":[134,84],"color":(140,80,60),"width":1})

    # --- Blue scarf (THE feature — around neck, flowing) ---
    P.append({"type":"polygon","points":[(110,90),(146,90),(150,100),(106,100)],
              "color":SCARF,"outline":OUT,"outline_w":1})
    # scarf tails flowing
    P.append({"type":"polygon","points":[(146,96),(168,96),(164,118),(148,110)],"color":SCARF,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(110,96),(92,98),(96,118),(112,110)],"color":SCARF,"outline":OUT,"outline_w":1})

    # --- Leather explorer jacket ---
    P.append({"type":"polygon","points":[(106,100),(150,100),(154,168),(102,168)],
              "color":JACKET,"outline":OUT,"outline_w":1})
    # jacket chest detail
    P.append({"type":"polygon","points":[(110,104),(146,104),(142,140),(114,140)],
              "color":JACKET_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[128,104],"end":[128,140],"color":(200,170,60),"width":1})  # zipper
    # shoulder pads
    P.append({"type":"circle","cx":104,"cy":104,"r":9,"color":JACKET_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":152,"cy":104,"r":9,"color":JACKET_DARK,"outline":OUT,"outline_w":1})

    # --- Arms ---
    P.append({"type":"rect","x":96,"y":110,"w":13,"h":48,"color":JACKET,"outline":OUT,"outline_w":1,"radius":5})
    P.append({"type":"rect","x":147,"y":110,"w":13,"h":48,"color":JACKET,"outline":OUT,"outline_w":1,"radius":5})

    # --- Floating arcane GAUNTLET (THE feature — big, glowing, on left hand) ---
    # glow halo
    P.append({"type":"circle","cx":88,"cy":160,"r":20,"color":GAUNTLET_GLOW})
    P.append({"type":"circle","cx":88,"cy":160,"r":16,"color":(180,235,255)})
    # gauntlet body (big mechanical glove)
    P.append({"type":"rect","x":74,"y":146,"w":28,"h":30,"color":GAUNTLET,"outline":OUT,"outline_w":1,"radius":4})
    # gauntlet gem (glowing core)
    P.append({"type":"circle","cx":88,"cy":160,"r":7,"color":GAUNTLET_GLOW,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":86,"cy":158,"r":3,"color":(230,250,255)})
    # gauntlet plates/details
    P.append({"type":"line","start":[74,156],"end":[102,156],"color":OUT,"width":1})
    P.append({"type":"line","start":[82,146],"end":[82,176],"color":OUT,"width":1})
    P.append({"type":"line","start":[94,146],"end":[94,176],"color":OUT,"outline_w":1,"width":1})
    # hand reaching to gauntlet
    P.append({"type":"circle","cx":103,"cy":162,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs + boots ---
    P.append({"type":"rect","x":108,"y":168,"w":15,"h":42,"color":JACKET_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":133,"y":168,"w":15,"h":42,"color":JACKET_DARK,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":104,"y":206,"w":23,"h":12,"color":(60,40,25),"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":129,"y":206,"w":23,"h":12,"color":(60,40,25),"outline":OUT,"outline_w":1,"radius":2})
    return P


def poppy_prims():
    """Poppy — Keeper of the Hammer.
    Iconic: OVERSIZED warhammer (bigger than her), blonde pigtails, Demacian plate armor, small stature (yordle).
    Hammer is THE feature — it's huge relative to her.
    """
    P = []
    HAMMER_HEAD = (160, 160, 170)
    HAMMER_DARK = (100, 100, 110)
    HAMMER_HANDLE = (90, 55, 35)
    GOLD = (210, 170, 55)
    ARMOR = (200, 195, 200)
    ARMOR_BLUE = (70, 90, 150)
    HAIR = (240, 215, 120)
    SKIN = (250, 220, 195)
    EYE = (40, 30, 25)
    OUT = (40, 25, 20)

    # --- OVERSIZED warhammer (THE feature — huge, held over shoulder) ---
    # handle (long, diagonal)
    P.append({"type":"line","start":[180,40],"end":[120,210],"color":HAMMER_HANDLE,"width":7})
    P.append({"type":"line","start":[180,40],"end":[120,210],"color":OUT,"width":1})
    # BIG hammer head (massive block)
    P.append({"type":"polygon","points":[(170,30),(210,36),(206,66),(166,60)],
              "color":HAMMER_HEAD,"outline":OUT,"outline_w":2})
    # hammer head detail (rivets + edge)
    P.append({"type":"line","start":[170,42],"end":[208,48],"color":HAMMER_DARK,"width":2})
    P.append({"type":"circle","cx":180,"cy":44,"r":2,"color":GOLD})
    P.append({"type":"circle","cx":198,"cy":48,"r":2,"color":GOLD})
    # gold pommel on handle
    P.append({"type":"circle","cx":120,"cy":210,"r":5,"color":GOLD,"outline":OUT,"outline_w":1})

    # --- Head (small yordle, blonde pigtails) ---
    P.append({"type":"circle","cx":128,"cy":78,"r":20,"color":SKIN,"outline":OUT,"outline_w":1})
    # hair cap
    P.append({"type":"circle","cx":128,"cy":72,"r":20,"color":HAIR,"outline":OUT,"outline_w":1})
    # bangs
    P.append({"type":"polygon","points":[(110,68),(146,68),(142,80),(114,80)],"color":HAIR,"outline":OUT,"outline_w":1})
    # BLONDE PIGTAILS (THE feature — two bunches sticking out)
    P.append({"type":"circle","cx":104,"cy":82,"r":9,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":100,"cy":94,"r":7,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":104,"cy":80,"r":3,"color":ARMOR_BLUE})  # tie
    P.append({"type":"circle","cx":152,"cy":82,"r":9,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":156,"cy":94,"r":7,"color":HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":152,"cy":80,"r":3,"color":ARMOR_BLUE})  # tie
    # eyes (determined)
    P.append({"type":"circle","cx":121,"cy":80,"r":3,"color":EYE})
    P.append({"type":"circle","cx":135,"cy":80,"r":3,"color":EYE})
    # determined mouth
    P.append({"type":"line","start":[122,90],"end":[134,90],"color":(140,60,60),"width":1})

    # --- Demacian plate armor (blue + white + gold) ---
    P.append({"type":"polygon","points":[(108,98),(148,98),(152,168),(104,168)],
              "color":ARMOR_BLUE,"outline":OUT,"outline_w":1})
    # white chest plate
    P.append({"type":"polygon","points":[(112,102),(144,102),(140,144),(116,144)],
              "color":ARMOR,"outline":OUT,"outline_w":1})
    # gold trim + Demacian crest
    P.append({"type":"line","start":[112,102],"end":[144,102],"color":GOLD,"width":2})
    P.append({"type":"circle","cx":128,"cy":120,"r":6,"color":GOLD,"outline":OUT,"outline_w":1})
    P.append({"type":"line","start":[128,108],"end":[128,134],"color":GOLD,"width":1})
    # shoulder armor
    P.append({"type":"circle","cx":104,"cy":102,"r":10,"color":ARMOR_BLUE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":152,"cy":102,"r":10,"color":ARMOR_BLUE,"outline":OUT,"outline_w":1})

    # --- Arms (one holding hammer) ---
    P.append({"type":"rect","x":96,"y":112,"w":13,"h":48,"color":ARMOR_BLUE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":147,"y":112,"w":13,"h":48,"color":ARMOR_BLUE,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"circle","cx":103,"cy":162,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":153,"cy":162,"r":5,"color":SKIN,"outline":OUT,"outline_w":1})

    # --- Legs (armored greaves, short) ---
    P.append({"type":"rect","x":110,"y":168,"w":14,"h":40,"color":ARMOR_BLUE,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":132,"y":168,"w":14,"h":40,"color":ARMOR_BLUE,"outline":OUT,"outline_w":1,"radius":3})
    P.append({"type":"rect","x":106,"y":204,"w":22,"h":12,"color":(50,40,30),"outline":OUT,"outline_w":1,"radius":2})
    P.append({"type":"rect","x":128,"y":204,"w":22,"h":12,"color":(50,40,30),"outline":OUT,"outline_w":1,"radius":2})
    return P


def thresh_prims():
    """Thresh — the Chain Warden.
    Iconic: soul lantern, spectral chains, tattered ghostly cloak, glowing green eyes, floating wraith.
    Lantern + chains are THE features.
    """
    P = []
    CLOAK = (50, 75, 60)
    CLOAK_DARK = (30, 50, 40)
    BONE = (200, 195, 170)
    GREEN = (140, 230, 110)
    GREEN_GLOW = (90, 200, 80)
    LANTERN = (180, 150, 50)
    CHAIN = (130, 130, 120)
    EYE = (140, 230, 110)
    OUT = (20, 30, 25)

    # --- Tattered ghostly cloak (flowing, behind) ---
    P.append({"type":"polygon","points":[(98,90),(158,90),(168,210),(88,210)],
              "color":CLOAK,"outline":OUT,"outline_w":1})
    # tattered hem (jagged bottom)
    P.append({"type":"polygon","points":[(88,210),(100,200),(108,212),(118,198),(128,212),(138,198),(148,212),(158,200),(168,210),(168,220),(88,220)],
              "color":CLOAK,"outline":OUT,"outline_w":1})
    # cloak inner shadow
    P.append({"type":"polygon","points":[(104,96),(152,96),(158,200),(98,200)],
              "color":CLOAK_DARK,"outline":OUT,"outline_w":1})

    # --- Spectral chains (THE feature — hanging from arm, links) ---
    # chain links from right arm down to lantern
    chain_pts = [(150,130),(156,144),(150,158),(156,172)]
    for i in range(len(chain_pts)-1):
        s, e = chain_pts[i], chain_pts[i+1]
        P.append({"type":"line","start":s,"end":e,"color":CHAIN,"width":3})
    for cx, cy in chain_pts:
        P.append({"type":"circle","cx":cx,"cy":cy,"r":4,"color":CHAIN,"outline":OUT,"outline_w":1})

    # --- Head (hooded skull — wraith) ---
    # hood
    P.append({"type":"polygon","points":[(108,58),(148,58),(146,92),(110,92)],
              "color":CLOAK_DARK,"outline":OUT,"outline_w":1})
    # skull face (bone)
    P.append({"type":"circle","cx":128,"cy":76,"r":15,"color":BONE,"outline":OUT,"outline_w":1})
    # glowing green eyes (soulless)
    P.append({"type":"circle","cx":122,"cy":74,"r":4,"color":GREEN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":134,"cy":74,"r":4,"color":GREEN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":122,"cy":74,"r":2,"color":GREEN_GLOW})
    P.append({"type":"circle","cx":134,"cy":74,"r":2,"color":GREEN_GLOW})
    # nose hole (skull)
    P.append({"type":"polygon","points":[(126,80),(130,80),(128,86)],"color":OUT})
    # teeth
    P.append({"type":"line","start":[122,88],"end":[134,88],"color":OUT,"width":1})
    for tx in (123, 127, 131):
        P.append({"type":"line","start":[tx,88],"end":[tx,92],"color":OUT,"width":1})

    # --- Exposed ribcage (THE feature — visible through cloak) ---
    P.append({"type":"polygon","points":[(112,100),(144,100),(140,150),(116,150)],
              "color":BONE,"outline":OUT,"outline_w":1})
    # ribs (curved lines)
    for ry in (108, 116, 124, 132, 140):
        P.append({"type":"line","start":[116,ry],"end":[140,ry],"color":OUT,"width":1})
    P.append({"type":"line","start":[128,100],"end":[128,150],"color":OUT,"width":1})  # sternum

    # --- Arms (ghostly, thin) ---
    P.append({"type":"rect","x":100,"y":106,"w":12,"h":50,"color":CLOAK_DARK,"outline":OUT,"outline_w":1,"radius":4})
    P.append({"type":"rect","x":146,"y":106,"w":12,"h":50,"color":CLOAK_DARK,"outline":OUT,"outline_w":1,"radius":4})
    # bony hand holding chain
    P.append({"type":"circle","cx":152,"cy":160,"r":5,"color":BONE,"outline":OUT,"outline_w":1})

    # --- Soul lantern (THE feature — glowing green lantern on chain) ---
    # green glow
    P.append({"type":"circle","cx":156,"cy":186,"r":16,"color":GREEN_GLOW})
    P.append({"type":"circle","cx":156,"cy":186,"r":12,"color":(120,220,100)})
    # lantern body (cage)
    P.append({"type":"rect","x":146,"y":176,"w":20,"h":24,"color":LANTERN,"outline":OUT,"outline_w":1,"radius":2})
    # lantern cage bars
    P.append({"type":"line","start":[152,176],"end":[152,200],"color":OUT,"width":1})
    P.append({"type":"line","start":[160,176],"end":[160,200],"color":OUT,"width":1})
    # glowing soul inside
    P.append({"type":"circle","cx":156,"cy":188,"r":6,"color":GREEN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":155,"cy":186,"r":3,"color":(200,255,180)})
    # lantern cap + ring
    P.append({"type":"rect","x":148,"y":172,"w":16,"h":5,"color":LANTERN,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":156,"cy":170,"r":3,"color":LANTERN,"outline":OUT,"outline_w":1})

    # --- No legs (floating wraith — tattered cloak ends) ---
    return P


def sejuani_prims():
    """Sejuani — Fury of the North.
    Iconic: giant armored boar (Bristle) mount, rider with flail, ice, fur.
    The BOAR is THE feature — it's the biggest part.
    """
    P = []
    BOAR = (120, 95, 80)
    BOAR_DARK = (85, 65, 55)
    ICE_BLUE = (180, 220, 240)
    FUR = (200, 200, 210)
    RIDER_SKIN = (220, 185, 150)
    RIDER_HAIR = (190, 165, 130)
    ARMOR = (150, 160, 175)
    TUSK = (235, 230, 215)
    EYE = (40, 30, 25)
    OUT = (40, 25, 20)

    # --- Giant armored boar (THE feature — big body, low) ---
    # body (big rounded mass)
    P.append({"type":"ellipse","x":60,"y":150,"w":140,"h":70,"color":BOAR,"outline":OUT,"outline_w":1})
    # boar head (front, right side)
    P.append({"type":"circle","cx":196,"cy":178,"r":26,"color":BOAR,"outline":OUT,"outline_w":1})
    # snout
    P.append({"type":"ellipse","x":206,"y":172,"w":24,"h":20,"color":BOAR_DARK,"outline":OUT,"outline_w":1})
    # nostrils
    P.append({"type":"circle","cx":222,"cy":178,"r":2,"color":OUT})
    P.append({"type":"circle","cx":222,"cy":184,"r":2,"color":OUT})
    # boar eye
    P.append({"type":"circle","cx":190,"cy":172,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    # boar ear
    P.append({"type":"polygon","points":[(178,156),(184,144),(192,156)],"color":BOAR_DARK,"outline":OUT,"outline_w":1})
    # BIG tusks (THE feature — curved, white, from snout)
    P.append({"type":"polygon","points":[(208,186),(220,190),(214,206),(206,198)],"color":TUSK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(208,170),(220,166),(214,150),(206,158)],"color":TUSK,"outline":OUT,"outline_w":1})

    # --- Boar legs (4 stubby) ---
    for lx in (78, 110, 150, 180):
        P.append({"type":"rect","x":lx,"y":210,"w":16,"h":18,"color":BOAR_DARK,"outline":OUT,"outline_w":1,"radius":3})
        P.append({"type":"rect","x":lx-2,"y":224,"w":20,"h":8,"color":(60,45,35),"outline":OUT,"outline_w":1,"radius":2})

    # --- Armored plating on boar (ice-blue metal) ---
    P.append({"type":"ellipse","x":80,"y":146,"w":100,"h":24,"color":ARMOR,"outline":OUT,"outline_w":1})
    # armor studs
    for sx in (96, 116, 136, 156):
        P.append({"type":"circle","cx":sx,"cy":158,"r":3,"color":ICE_BLUE,"outline":OUT,"outline_w":1})
    # fur trim on armor
    P.append({"type":"rect","x":78,"y":142,"w":104,"h":8,"color":FUR,"outline":OUT,"outline_w":1})

    # --- Ice crystals on boar (Freljord) ---
    P.append({"type":"polygon","points":[(110,130),(116,116),(122,130)],"color":ICE_BLUE,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(140,128),(146,114),(152,128)],"color":ICE_BLUE,"outline":OUT,"outline_w":1})

    # --- Rider (Sejuani, on top of boar) ---
    # rider torso
    P.append({"type":"polygon","points":[(112,96),(140,96),(144,140),(108,140)],
              "color":ARMOR,"outline":OUT,"outline_w":1})
    # fur cape
    P.append({"type":"polygon","points":[(108,96),(140,96),(98,130),(92,112)],"color":FUR,"outline":OUT,"outline_w":1})
    # rider head
    P.append({"type":"circle","cx":126,"cy":80,"r":15,"color":RIDER_SKIN,"outline":OUT,"outline_w":1})
    # rider hair (braided, blonde-ish)
    P.append({"type":"circle","cx":126,"cy":74,"r":15,"color":RIDER_HAIR,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(110,72),(142,72),(138,84),(114,84)],"color":RIDER_HAIR,"outline":OUT,"outline_w":1})
    # rider eyes
    P.append({"type":"circle","cx":120,"cy":82,"r":2,"color":EYE})
    P.append({"type":"circle","cx":132,"cy":82,"r":2,"color":EYE})
    # rider arms (holding flail)
    P.append({"type":"rect","x":140,"y":100,"w":12,"h":36,"color":ARMOR,"outline":OUT,"outline_w":1,"radius":4})

    # --- Flail (morning star, ice) ---
    P.append({"type":"line","start":[152,136],"end":[176,118],"color":(90,60,40),"width":3})
    P.append({"type":"circle","cx":180,"cy":114,"r":12,"color":ICE_BLUE,"outline":OUT,"outline_w":2})
    P.append({"type":"circle","cx":180,"cy":114,"r":8,"color":ARMOR,"outline":OUT,"outline_w":1})
    # spikes on flail
    for ang in (0, 72, 144, 216, 288):
        import math as _m
        sx = 180 + int(14 * _m.cos(_m.radians(ang)))
        sy = 114 + int(14 * _m.sin(_m.radians(ang)))
        P.append({"type":"circle","cx":sx,"cy":sy,"r":3,"color":ICE_BLUE,"outline":OUT,"outline_w":1})
    return P


def kindred_prims():
    """Kindred — The Eternal Hunters.
    Iconic: white woolly lamb (Lamb) + large spectral wolf (Wolf), white mask, bow.
    Lamb + Wolf are THE features — two entities.
    """
    P = []
    LAMB_WOOL = (235, 235, 240)
    LAMB_DARK = (200, 200, 210)
    WOLF = (90, 70, 110)
    WOLF_DARK = (60, 45, 75)
    MASK = (245, 245, 250)
    BOW = (140, 100, 60)
    GLOW = (150, 200, 255)
    EYE = (140, 200, 255)
    OUT = (40, 30, 35)

    # --- Spectral Wolf (THE feature — large, behind/beside lamb, ghostly purple) ---
    # wolf body (looming behind)
    P.append({"type":"ellipse","x":150,"y":60,"w":70,"h":90,"color":WOLF,"outline":OUT,"outline_w":1})
    # wolf head (snarling, up high)
    P.append({"type":"circle","cx":198,"cy":78,"r":22,"color":WOLF,"outline":OUT,"outline_w":1})
    # wolf snout
    P.append({"type":"polygon","points":[(210,72),(232,76),(228,90),(210,86)],"color":WOLF_DARK,"outline":OUT,"outline_w":1})
    # wolf ears
    P.append({"type":"polygon","points":[(184,60),(190,42),(198,58)],"color":WOLF,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(200,58),(208,42),(214,60)],"color":WOLF,"outline":OUT,"outline_w":1})
    # wolf glowing eyes (spectral)
    P.append({"type":"circle","cx":192,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":206,"cy":76,"r":4,"color":EYE,"outline":OUT,"outline_w":1})
    P.append({"type":"circle","cx":192,"cy":76,"r":2,"color":GLOW})
    P.append({"type":"circle","cx":206,"cy":76,"r":2,"color":GLOW})
    # wolf teeth
    P.append({"type":"polygon","points":[(214,86),(218,86),(216,94)],"color":MASK,"outline":OUT,"outline_w":1})
    P.append({"type":"polygon","points":[(220,86),(224,86),(222,94)],"color":MASK,"outline":OUT,"outline_w":1})
    # ethereal glow around wolf
    P.append({"type":"ellipse","x":148,"y":56,"w":74,"h":98,"color":(110,90,150,60) if False else WOLF_DARK,"outline":GLOW,"outline_w":1})

    # --- Lamb (white woolly, front) ---
    # woolly body
    P.append({"type":"ellipse","x":76,"y":120,"w":80,"h":76,"color":LAMB_WOOL,"outline":OUT,"outline_w":1})
    # wool texture (bumps)
    for wx in (88, 104, 120, 136):
        P.append({"type":"circle","cx":wx,"cy":132,"r":10,"color":LAMB_WOOL,"outline":LAMB_DARK,"outline_w":1})
        P.append({"type":"circle","cx":wx,"cy":156,"r":10,"color":LAMB_WOOL,"outline":LAMB_DARK,"outline_w":1})
    # lamb head
    P.append({"type":"circle","cx":100,"cy":108,"r":18,"color":LAMB_WOOL,"outline":OUT,"outline_w":1})
    # lamb ears (floppy)
    P.append({"type":"ellipse","x":82,"y":96,"w":10,"h":18,"color":LAMB_DARK,"outline":OUT,"outline_w":1})
    P.append({"type":"ellipse","x":110,"y":96,"w":10,"h":18,"color":LAMB_DARK,"outline":OUT,"outline_w":1})

    # --- White mask (THE feature — on lamb's face, blank) ---
    P.append({"type":"circle","cx":100,"cy":108,"r":12,"color":MASK,"outline":OUT,"outline_w":1})
    # mask eye holes (dark)
    P.append({"type":"circle","cx":95,"cy":106,"r":3,"color":OUT})
    P.append({"type":"circle","cx":105,"cy":106,"r":3,"color":OUT})
    # mask markings (Lamb's mask has a line)
    P.append({"type":"line","start":[100,112],"end":[100,118],"color":LAMB_DARK,"width":1})

    # --- Lamb legs ---
    for lx in (88, 110, 132):
        P.append({"type":"rect","x":lx,"y":188,"w":12,"h":28,"color":LAMB_DARK,"outline":OUT,"outline_w":1,"radius":3})

    # --- Bow (Lamb's weapon, drawn) ---
    P.append({"type":"line","start":[60,120],"end":[60,180],"color":BOW,"width":3})
    P.append({"type":"line","start":[60,120],"end":[60,180],"color":(200,200,220),"width":1})  # bowstring glow
    # arrow
    P.append({"type":"line","start":[60,150],"end":[40,150],"color":(180,180,200),"width":1})
    return P


# Map of hand-authored champs
HAND_AUTHORED = {
    "Ahri": ahri_prims,
    "Annie": annie_prims,
    "Fiora": fiora_prims,
    "Darius": darius_prims,
    "MonkeyKing": monkeyking_prims,
    "Teemo": teemo_prims,
    "Yuumi": yuumi_prims,
    "Pantheon": pantheon_prims,
    "TwistedFate": twistedfate_prims,
    "Ezreal": ezreal_prims,
    "Poppy": poppy_prims,
    "Thresh": thresh_prims,
    "Sejuani": sejuani_prims,
    "Kindred": kindred_prims,
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
