"""Generate a DEEP-FOCUS per-champ prompt for ONE champ.

Usage: python3 exp/gen_champ_prompt.py <ChampId>
Prints a dispatch prompt for a single-champ agent that gives that champ deep
focus: up to 6 authoring rounds, try 2-3 FUNDAMENTALLY DIFFERENT visual
approaches (not just "make the icon bigger"), keep the best. Includes the
champ's SPECIFIC missing features from the latest gate so the agent knows
exactly what to fix.
"""
import json, sys, os

EXP = os.path.dirname(os.path.abspath(__file__))

# LoL-knowledge hint per champ: the signature feature + a SECOND approach idea
# (the first approach already got this champ to its current score; the agent
# should try a DIFFERENT composition to break the ceiling).
HINTS = json.load(open(os.path.join(EXP, "_below8_worklist.json")))
HINTS = {x["id"]: x for x in HINTS}

# Secondary approach idea per champ — what to try if "make the icon bigger"
# already failed. Often a different stance angle, a different feature as the
# dominant icon, or adding a companion/secondary icon.
APPROACH2 = {
 "Aatrox": "wings already drawn — try making the GREATSWORD the dominant icon instead (huge vertical blade) OR add a big glowing chest-core. Or spread wings WIDER to fill top half.",
 "Ambessa": "try DUAL CURVED BLADES as the dominant icon (crossed/scissored, big) + crimson cape. Or make the grey-streaked hair a huge crest.",
 "Belveth": "quadruped ceiling — try a more UPRIGHT/leaping pose (front claws raised high) so it reads as a predator, not a low beast. Or make the void-crystal plates glow brightly.",
 "Blitzcrank": "make the ROCKET-HAND fist HUGE with visible rocket exhaust flames + fins (clearly a rocket, not just a big fist). Or expose big GEARS on the chest.",
 "Braum": "beard already huge — try making the VAULT-DOOR SHIELD the dominant icon (massive shield with mustache painted on it). Or unibrow + huge mustache + bare muscular chest.",
 "Briar": "make the PILLORY COLLAR even bigger + add big FANGS (open mouth) + wrist chains dangling. Or blood-red aura around her.",
 "Camille": "BLADE-LEGS — make the leg-blades long and obvious (scythe-shaped feet) + hextech blue glow on legs. Or the hook-line grappling hook.",
 "Draven": "pompadour misreads as hat — try making the DUAL SPINNING AXES the dominant icon (two big axes with motion arcs) + the mustache. Or a big red CAPE with axe emblem.",
 "Ekko": "Zaurite device on back reads as chest — try showing the device from a 3/4 angle so the BACKPACK is clearly behind him, + big glowing turquoise. Or the bat weapon big.",
 "Fiora": "rapier read as Riven's sword — make the rapier THIN and clearly thrust-forward (not a slab) + big rose emblem + high collar. Or dueling pose with rapier pointing at viewer.",
 "Galio": "stone fists + WINGS — make the wings HUGE (gargoyle wings spread) so it reads as a winged gargoyle, not a guy with big hands. Or the hollow chest with glowing core.",
 "Gnar": "try BIG-MINI GNAR (transformed, hulking) instead of small gnar — big fangs + muscular + bone club. Or the boomerang as a huge spinning icon.",
 "Hwei": "floating paint palette — make it BIGGER + add visible PAINT STROKES/ink swirls around him (ink magic effects as a secondary icon). Or the ink brush as a big glowing staff.",
 "Illaoi": "golden idol + TENTACLES — make 2-3 big tentacles erupting from the idol (not just beside her) so it reads as a tentacle-priestess. Or the idol as a huge skull-statue.",
 "Ivern": "tree-man — make the BRANCHING ARMS obvious (arms split into branches with leaves) + a small Daisy (deer companion) beside him. Or bark texture as big plates.",
 "Kaisa": "void carapace — make the SHOULDER CANNONS big and clearly void-organic (glowing purple ports) + helmet visor. Or the void-wings from her ultimate.",
 "Katarina": "red hair read as hood — make the crimson hair clearly HAIR (flowing strands, not a solid hood shape) + dual DAGGERS big. Or the Katarina death-lotus (spinning daggers).",
 "Kayn": "shadow aura — make the SCYTHE (Rhaast) the dominant icon (huge darkin scythe with glowing red eye) + shadow tendrils. Or the blue/red half-and-half body (Kayn vs Rhaast).",
 "Khazix": "quadruped ceiling — make the SCYTHE CLAWS raised high + big glowing purple eyes + wings extended (he has wings). Or a leaping pounce pose.",
 "Kindred": "two-entity — make the SPECTRAL WOLF big and clearly separate from Lamb (wolf behind/beside, glowing blue) + Lamb's bow. Or the death-mask on Lamb's face.",
 "Leblanc": "pointed hat + dress — make the hat BIGGER (witch-like) + a MIRROR/illusion clone beside her (two Leblancs). Or the purple orb/staff.",
 "Lux": "light staff — make the staff glow BRIGHTLY with radiating light rays (a sun-burst of light around the staff tip) + blonde hair. Or the double-rainbow light effect.",
 "Maokai": "tree — make the BRANCHING ARMS split into 3-4 limbs with leaves + glowing sap-eyes + root-feet splayed. Or a big magic-sapling beside him.",
 "MissFortune": "dual pistols — make BOTH pistols huge (one in each hand, pointing out) + big red flowing hair + tricorne hat. Or the gun-strut pose with pistols prominent.",
 "Nasus": "jackal head — make the SNOUT longer (clearly canine, not human) + Egyptian gold staff BIG + ankh/sun emblem. Or the spirit-fire aura (golden).",
 "Nautilus": "diving suit — make the MASSIVE ANCHOR the dominant icon (huge, dragging) + glowing helm + big brass rivets on the suit. Or the depth-pressure aura.",
 "Neeko": "chameleon tail — make the tail BIG and curling visibly + colorful head crest + a shapeshift clone beside her. Or the big curious eyes + lizard-skin green.",
 "Nilah": "water whip — make the whip a big flowing WATER STREAM (clearly liquid, with droplets) + gold jewelry + joyful pose. Or the water-blade as a crescent.",
 "Orianna": "ball-jointed doll — make the WIND-UP KEY clearly visible on her back (3/4 angle) + the floating BALL companion big + porcelain doll face. Or the jointed elbows/knees obvious.",
 "Ryze": "blue runes — make the runes GLOW BRIGHTLY on big muscular forearms + the giant scroll + hood. Or floating rune-stones around him.",
 "Sejuani": "mounted boar — make BRISTLE the boar HUGE (lower 60%) with big tusks + ice-armor plates + the flail big. Or ice-breath from the boar.",
 "Shaco": "jester hat — make the THREE-POINTED HAT with bells HUGE + painted grin + a JACK-IN-BOX clone popping up. Or the daggers big + pointed curl-toe shoes.",
 "Shen": "Kinkou mask — make the mask BIG (clearly a spirit-mask over eyes) + the spirit-blade (katana) + shoulder guards. Or the spirit-realm portal behind him.",
 "Sivir": "crossblade — make the BOOMERANG-BLADE huge (her iconic X-shaped weapon) + Shuriman gold armor + ponytail. Or the crossblade mid-throw (spinning).",
 "Taliyah": "floating rocks — make 5-7 BIG rocks orbiting her clearly + rock-wall shield + nomadic wrappings. Or the weaving-loom of rock.",
 "Udyr": "spirit tattoos — make 4 GLOWING ANIMAL-SPIRIT symbols on his body (bear/turtle/eagle/ram) clearly glowing + bare chest + furs. Or one big spirit-aura animal behind him.",
 "Warwick": "werewolf — make the WOLF SNOUT + EARS + CLAWS clearly wolf (he's a werewolf, not a man) + green chemical vials on back + shackles. Or the blood-hunt red-eyes + fangs.",
 "Yone": "demon mask — make the AZAKANA MASK a big horned demon-face (clearly a mask, not a construct) + two katanas + spirit-half (a translucent second self). Or the wind-spirit blade.",
 "Zed": "metal mask + shadow — make the MASK + glowing red eyes dominant + 2-3 SHADOW CLONES around him (the iconic shadow technique) + arm blades. Or the shadow-shuriken.",
 "Zeri": "electric girl — make the OVERSIZED GAUNTLETS huge + spiky hair + lightning arcs between hands + Zaun streetwear. Or the electrical trail/sparks.",
 "Ahri": "9 tails read as hair/wings — try fanning the 9 tails in a CLEAR PEACOCK-FAN behind her (each tail a distinct separated triangle) + fox ears + orb. Or fewer but HUGE tails.",
 "Aphelios": "rotating arsenal ceiling — try ONE big MOONSTONE WEAPON (the pistol or chakram) as the dominant icon + moon emblem + pale skin + dark cloak. Or the moon-cycle halo.",
 "Darius": "generic axe-man — make the NOXIAN AXE massive + bright RED CAPE (Noxian, not Demacian) + the big beard + Noxian skull-emblem on armor. Or the pull-grab hand (Apprehend).",
 "Janna": "wind — make VISIBLE CYCLONE/swirl lines around her body (a clear wind aura) + floating + flowing hair + staff. Or the tornado at her base.",
 "Kalista": "ghost spear-thrower — make MANY SPEARS floating around her + tattered ghost-robe + hollow eyes + ethereal teal. Or the spear-throw pose with 3-4 spectral spears.",
 "Olaf": "misread as Swain — make the DUAL THROWING AXES clearly axes (not a banner) + big braided BLONDE beard + bare muscular chest + round Viking shield. Or the berserker-rage pose.",
 "Pyke": "spectral undead — make the BONE-HARPOON big + glowing teal eyes + tattered nautical clothes + pale undead skin + the death-from-below water splash. Or the dagger-ghost form.",
 "Qiyana": "ring-blade — make the CIRCULAR OHMLATL weapon big + Ixtali gold jewelry + green/water element. Or make the weapon clearly a RING (donut shape) not a disc.",
 "Rakan": "feathered cape — make the GOLDEN FEATHERED WINGS huge (spread wide, clearly bird-plumage) + bird-crest on head + gold. Or the dance-pose with feathers trailing.",
 "Riven": "broken sword — make the BROKEN GREATSWORD clearly broken (jagged snapped tip, glowing green rune at the break) + white cape + green runic glow. Or the wind-slash effect.",
 "Shyvana": "half-dragon — make the DRAGON WINGS + TAIL big + scaled skin (visible scale texture) + horns. Or the dragon-form hybrid (more dragon, less human).",
 "Soraka": "celestial — make the HOOVES clearly hooved legs (not boots) + long purple hair + horn-like protrusions + star-staff + celestial glow. Or the wish-heal stars.",
 "Taric": "crystalline — make the PINK/GEM ARMOR clearly crystalline (faceted gem shapes, not flat metal) + floating gemstones + big shield + radiant pose. Or the gems glowing.",
 "Trundle": "troll — make the TUSKS big + TRUE-ICE CLUB huge + blue skin + fur pelt + heavy brow. Or the ice-subject aura (frost).",
 "Tryndamere": "barbarian — make the BARE CHEST clearly bare (skin tone, not armor) + big greatsword + wild hair + fur + rage-glow eyes. Or the spin-attack (Spinning Slash).",
 "Varus": "darkin corruption — make the PURPLE CORRUPTION clearly asymmetrical (left half corrupted, right half clean) + blight-bow + darkin arm. Or the corruption-arms (3 darkin arms).",
 "Vayne": "crossbow — make the WRIST-MOUNTED CROSSBOW clearly a crossbow (bow-limb + stock + bolt) + silver bolts + dark cloak + high boots. Or the tumble/stealth pose.",
 "Viego": "ruined king — make the CROWN OF THORNS big + the BLADE OF THE RUINED KING (broken/glowing) + ghostly teal + tattered royal robe + mist. Or the herald (his wraith).",
 "Viktor": "hexcore — make the HEXCORE CHEST clearly a glowing mechanical core (visible through a chest-window) + third arm + staff + metallic legs. Or the death-ray beam.",
 "Xayah": "feathered rebel — make the PURPLE FEATHERED WING-BLADES on hips big + talon-feet + feather daggers + red/black hair. Or the bladecaller (feathers swirling).",
 "XinZhao": "spearman generic — make the THREE-TALON SPEAR HEAD distinct (Audacity) + Demacian BLUE/GOLD + big flowing cape + wing-crest helm. Or the sweep-attack arc.",
 "Zoe": "cosmic — make the STAR-SHAPED PUPILS + floating celestial ORBS + cosmic hair + the sparkly trail + hoodie. Or the portal-jump (a glowing portal).",
 "Hecarim": "centaur — try a cleaner SIMPLER silhouette: clear horse-body (4 legs) + spectral rider + ghostly trident + teal glow. DON'T over-densify (that regressed to 3). Keep it clean.",
 "Rell": "mounted — make the METAL HORSE clearly forged-metal (rivets, plates, glowing seams) + Rell on top with metal armor + floating metal shards (ferromancy). Or the metal-horse rearing.",
}


def build(cid):
    x = HINTS[cid]
    sig = x["sig"]
    miss = x["missing"]
    approach2 = APPROACH2.get(cid, "try a DIFFERENT composition/angle/feature emphasis than what got it to its current score")
    return f"""You are a pixel-art sprite artist AND a League of Legends expert. ONE champ, DEEP FOCUS: hand-author JSON drawing primitives for {cid} so its 256x256 world sprite scores 8-10 on the canon gate. The VLM only JUDGES (gates); YOU author the primitives.

## Your single champ: {cid} (current score {x['score']}/10)
Canon signature features: {', '.join(sig[:5]) if sig else 'unknown'}
The gate says these are MISSING: {', '.join(miss[:5]) if miss else 'none'}

This champ is at {x['score']} — it's already recognizable (rec=True) but the VLM won't push to 8. The previous batch already tried "make the icon bigger" — that hit a ceiling. To break through, you need a DIFFERENT approach.

## SECOND APPROACH TO TRY (if the obvious one fails):
{approach2}

## The harness (USE THIS — do not reinvent)
```python
import sys; sys.path.insert(0, "exp")
from champ_improver import improve, canon_for, committed_score
result = improve("{cid}", prims_list, gate_n=3)
# -> {{"id","old","new","saved","missing","verdict","n_prims","rec"}}
# improve() renders to 256x256, gates (max-of-3 VLM calls to damp ~2pt
# variance), and SAVES to assets/characters/{cid}/sprite.png + sprites/0.png
# + descriptors.json ONLY if new > old (NEVER regresses).
```

To see the full canon:
```python
import json
d = {{x["id"]: x for x in json.load(open("exp/per_champ_ledger.json"))}}
c = d["{cid}"]
print(c["score"], c["stance"], c["body_shape"])
print("features:", c["signature_features"])
print("colors:", c["primary_colors"], "weapon:", c["weapon"])
print("missing:", c["missing"])
```

## THE PATTERN (the whole game)
At 256px, fine detail does NOT read. What scores 8-10 is ONE HUGE, UNIQUE signature feature dominating 30-50% of the silhouette. 106 champions are already at 8-10 this way (Annie 9, Gragas 9, Azir 9, MonkeyKing 9, Teemo 9, Pantheon 9, TahmKench 9, plus 97 at 8). Keep the silhouette CLEAN — over-densifying regresses (Hecarim 5->3, Viktor 6->5, Braum 7->5).

## DEEP-FOCUS WORKFLOW (up to 6 rounds, try DIFFERENT approaches)
1. Fetch the canon (snippet above). Note the SPECIFIC missing features.
2. Author approach #1 (the obvious icon). Call improve. Note new + missing.
3. If new < 8: DON'T just make the icon bigger. Try approach #2 (the SECOND APPROACH above — a different composition/angle/feature). Call improve.
4. If new < 8: try approach #3 (a third fundamentally different idea — different stance, a companion, a secondary icon, an effect aura). Call improve.
5. Up to 6 rounds total, trying distinct approaches. Keep the BEST result.
6. If still < 8 after 6 rounds with distinct approaches: accept it — it's a VLM recognition limit, not a technique failure. Report the best score.

## Canvas + primitive format
- 256x256, transparent. Body center ~(128,150). Draw back-to-front. Coordinates 0-255. 20-40 prims.
- circle: {{"type":"circle","cx":int,"cy":int,"r":int,"color":[r,g,b],"outline":[r,g,b],"outline_w":int}}
- rect: {{"type":"rect","x":int,"y":int,"w":int,"h":int,"color":[r,g,b],"outline":[r,g,b],"outline_w":int,"radius":int}}
- polygon: {{"type":"polygon","points":[[x,y],...],"color":[r,g,b],"outline":[r,g,b],"outline_w":int}}
- line: {{"type":"line","start":[x,y],"end":[x,y],"color":[r,g,b],"width":int}}
- ellipse: {{"type":"ellipse","x":int,"y":int,"w":int,"h":int,"color":[r,g,b],"outline":[r,g,b],"outline_w":int}}
- color=fill [r,g,b]; outline=border [r,g,b] or null; outline_w default 1.

## Style reference (READ 1-2 before authoring)
`exp/hand_author_sprites.py` — 30 worked examples (read annie_prims + one relevant to {cid}). `exp/_renekton_test.py` (validated 8). Named color constants, back-to-front, icon BIG, outlines on everything, CLEAN silhouette.

## Hard constraints
- NEVER use Read on any .png file — it crashes the session. Inspect via harness (render+gate) or ASCII grid (render to /tmp, pygame.surfarray, 32x32 alpha grid).
- Only touch {cid}. Do not save/modify others.
- improve() auto-saves when new > old. Never force a non-beating save.
- Do not edit exp/canon_gate_results.json — coordinator re-gates after.
- Work in /home/misa/Desktop/RD/Gacha on branch vlm-canon-overhaul.
- VLM slow (~30-60s/gate). Be patient; harness retries.

## Report back (return ONLY this — one JSON object + one line)
```
{{"id":"{cid}","old":{x['score']},"new":8,"saved":true,"rounds":3,"approach":"which approach won","missing_final":[],"feature":"the dominant icon"}}
```
Plus one line: "{cid}: {x['score']}-><new> (saved/not saved), approach: <which>"."""


if __name__ == "__main__":
    cid = sys.argv[1]
    print(build(cid))
