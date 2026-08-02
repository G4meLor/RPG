# Sprite Fix Brief (shared)

You are improving ONE champion's default world sprite (skin 0) in a pygame gacha game.
The sprite is a 256x256 PNG built from JSON drawing primitives.

## CRITICAL RULES

1. **NEVER use the Read tool on any .png file in this repo — it crashes the session.**
   To "look at" a sprite, render it to an ASCII ramp:
   ```
   python3 exp/ascii_sprite.py --champ <ID> --no-color --cols 52 --rows 26
   ```
   Or for a color-coded cell view, use `/tmp/find_face.py` (copy below) — each cell = one named color initial.

2. **The gate is the arbiter.** `improve(cid, prims)` renders, gates with VLM canon_gate
   (max-of-3), and SAVES only if the new score STRICTLY beats the committed score.
   It never regresses. Trust the gate over your visual judgment — ASCII ramps can mislead.

3. **Canvas 256x256, body center ~(128,150).** Draw back-to-front (later prims on top).

## Harness API (exp/champ_improver.py)

```python
import sys, os
sys.path.insert(0, "/home/misa/Desktop/RD/Gacha/exp")
from champ_improver import improve, render, gate, save, committed_score, canon_for

# canon_for(cid) -> {stance, body_shape, signature_features, primary_colors, weapon}
# committed_score(cid) -> current gate score (int)
# improve(cid, prims, do_save=True, gate_n=3) -> {id, old, new, saved, missing, verdict, n_prims, rec}
#   renders, gates max-of-3, saves sprite.png + sprites/0.png + descriptors.json ONLY if new > old
# render(prims, path) -> writes a PNG to path (for your own ramp inspection)
# gate(cid, path, n=3) -> (score, missing_features, verdict) without saving
```

## Primitive format

```python
{"type":"circle","cx":int,"cy":int,"r":int,"color":[r,g,b],"outline":[r,g,b]|null,"outline_w":int}
{"type":"rect","x":int,"y":int,"w":int,"h":int,"color":[r,g,b],"outline":[r,g,b]|null,"outline_w":int,"radius":int}
{"type":"polygon","points":[[x,y],...],"color":[r,g,b],"outline":[r,g,b]|null,"outline_w":int}
{"type":"line","start":[x,y],"end":[x,y],"color":[r,g,b],"width":int}
{"type":"ellipse","x":int,"y":int,"w":int,"h":int,"color":[r,g,b],"outline":[r,g,b]|null,"outline_w":int}
```

## Color-cell inspection script (save to /tmp/look.py, run with `python3 /tmp/look.py <ID>`)

```python
import os,sys
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
sys.path.insert(0,"/home/misa/Desktop/RD/Gacha")
import pygame,pygame.surfarray as sa,numpy as np
pygame.init();pygame.display.set_mode((1,1))
from src.data.tuning import ASSET_DIR
NAMED=[("K",0,0,0),("g",60,60,60),("G",120,120,120),("L",190,190,190),("W",245,245,245),("1",240,200,165),("2",222,175,140),("3",196,145,110),("4",150,100,70),("5",110,70,45),("R",220,40,40),("r",140,30,30),("O",240,130,30),("Y",240,195,60),("B",120,75,40),("b",70,45,25),("n",60,170,70),("N",40,110,50),("T",40,170,160),("C",60,200,220),("U",50,110,220),("u",35,60,150),("l",150,200,240),("v",25,35,80),("P",140,60,180),("M",210,60,180),("p",245,130,190),("H",255,60,160)]
def nm(rgb):
    r,g,b=int(rgb[0]),int(rgb[1]),int(rgb[2]);bd=1e9;best="?"
    for s,pr,pg,pb in NAMED:
        d=(r-pr)**2+(g-pg)**2+(b-pb)**2
        if d<bd:bd=d;best=s
    return best
def ramp(path,cols=52,rows=26,th=24):
    s=pygame.image.load(path);rgb=sa.array3d(s)
    if s.get_flags()&pygame.SRCALPHA:
        pa=sa.pixels_alpha(s);a=np.array(pa,copy=True);del pa
    else:a=np.full(rgb.shape[:2],255,dtype=np.uint8)
    rgb=np.transpose(rgb,(1,0,2));a=np.transpose(a,(1,0))
    H,W=rgb.shape[:2];bx=W/cols;by=H/rows;out=[]
    for r in range(rows):
        y0=int(r*by);y1=int((r+1)*by);row=""
        for c in range(cols):
            x0=int(c*bx);x1=int((c+1)*bx)
            ba=a[y0:y1,x0:x1].reshape(-1);m=ba>=th
            if not m.any() or m.mean()<0.08:row+=" ";continue
            br=rgb[y0:y1,x0:x1].reshape(-1,3)[m].mean(axis=0).astype(int)
            row+=nm(br)
        out.append(row)
    return "\n".join(out)
cid=sys.argv[1]; p=os.path.join(ASSET_DIR,"characters",cid,"sprite.png")
print(ramp(p))
```

## Your workflow

1. Read `canon_for(cid)` and `committed_score(cid)`.
2. Look at the current sprite via the ramp script. Read the current primitives from
   `assets/characters/<ID>/descriptors.json` key "0" -> "primitives" (use python json, NOT Read on png).
3. Author an improved primitive list addressing the specific issue. Keep what works
   (colors, features the gate already accepts); change what's broken.
4. `render(prims, "/tmp/<cid>_try.png")`, ramp-inspect it, iterate visually.
5. `improve(cid, prims, do_save=True, gate_n=3)`. If `saved=True`, done. If not, read
   `missing` and `new` vs `old`, revise, retry. Up to 5 attempts.
6. If you can't beat the committed score after 5 attempts, report that — do NOT force
   a save (the harness won't let you anyway). The committed sprite stays.

## Report back

Return a one-line JSON: {"id":cid,"old":N,"new":N,"saved":bool,"attempts":N,"missing":[...]}
