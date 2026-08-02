"""Generate a per-champ batch subagent prompt for a given batch index.

Usage: python3 exp/gen_batch_prompt.py <batch_index>
Prints the dispatch prompt (ready to paste into an Agent call) for that batch.
Pulls champ canon + scores from exp/per_champ_ledger.json and batches from
exp/_batches.json.
"""
import json, sys, os

EXP = os.path.dirname(os.path.abspath(__file__))
LEDGER = {x["id"]: x for x in json.load(open(os.path.join(EXP, "per_champ_ledger.json")))}
BATCHES = json.load(open(os.path.join(EXP, "_batches.json")))

# One-line LoL-knowledge hint per champ: the ONE huge signature feature to make.
# This is the crux — it tells the subagent what icon to draw BIG.
HINTS = {
 "Renata": "chem-baroness: BIG chemical tank/vial rack on her back + mechanical prosthetic arm + high-collared opulent dress",
 "Sona": "mute mage: the ETWAHL is THE feature — a big floating golden harp/zither beside her, bigger than her body + long flowing hair + elegant gown",
 "Zeri": "Zaun electric girl: spiky electric hair + HUGE oversized mechanical gauntlets crackling with lightning + electric blue/cyan",
 "Akshan": "rogue Sentinel: grappling-hook rifle gun (big) + stylish rogue coat + confident smirk",
 "Ashe": "Freljord ice archer: BIG bow + pale blue skin + long platinum blonde hair + fur-lined cape",
 "Aurora": "vastayan spirit-fox witch: a glowing SPIRIT FOX companion beside/below her + ethereal glow + deer-like",
 "Belveth": "void empress (QUADRUPED): big curved scythe CLAWS + void-crystalline plates. Draw as a low four-legged void beast, not standing.",
 "Diana": "lunar priestess: silver CRESCENT MOONBLADE (big curved blade) + crescent moon halo/symbol above + dark hair + silver lunar armor",
 "Gragas": "fat brewmaster: the HUGE round belly (biggest circle on sprite) + beer barrel + wild bushy beard. Belly dominates.",
 "Irelia": "blade dancer: MULTIPLE floating blade shards orbiting her (5-7 floating metal shards in an arc — THE feature) + flowing Ionian robes",
 "Kennen": "ninja yordle: big pointed yordle EARS + lightning sparks. Yordle proportions: head/ears huge vs tiny body.",
 "MasterYi": "Wuju swordsman: the 7-lens GOGGLES/mask over eyes (his icon) + big katana + topknot ponytail",
 "Rell": "ferromancy mage (MOUNTED): rides a big METAL ARMORED HORSE she forged. Draw the metal horse big, she sits on top.",
 "Riven": "exile: the BROKEN greatsword (jagged broken-off tip, glowing green runes — THE feature) + white cape + asymmetrical Noxian armor",
 "Shyvana": "half-dragon: long DRAGON TAIL (big, curling behind) + dragon horns + dragon wings. Tail/wings dominate.",
 "Soraka": "celestial healer: HOOVES instead of feet (no human legs — goat-like hooves — THE feature) + long purple hair + celestial glow + horn-like protrusions",
 "Swain": "Noxian grand general: the GIANT RED DEMONIC ARM/WING on one side (bigger than his body — a demonic raven claw/wing — THE feature) + officer uniform + cane",
 "Tristana": "yordle gunner: OVERSIZED CANNON (big gun bigger than her — THE feature) + big pointed ears. Yordle proportions.",
 "Twitch": "rat: LONG PINK RAT TAIL (big, curling — THE feature) + pointed rat ears + hunched rat posture + rat snout + crossbow. He's a RAT.",
 "Udyr": "spirit walker: glowing SPIRIT ANIMAL TATTOOS/marks on bare chest (bear/turtle/eagle/ram spirit symbols glowing — THE icon) + wild hair + furs",
 "Vladimir": "hemomancer vampire: high-collared Noxian noble coat + pale skin + BLOOD magic (crimson blood orbs/pool — THE motif)",
 "Volibear": "thunder war-bear (QUADRUPED): a big FOUR-LEGGED BEAR body + blue lightning crackling around it + tribal armor. Bear + lightning.",
 "Ziggs": "bomb yordle: BIG ROUND GOGGLES on head (THE feature) + wild orange hair + bomb backpack. Yordle proportions.",
 "Zyra": "plant mage: VINE/THORN HAIR (hair made of green vines with thorns + flowers — THE feature) + thorny protrusions + petals. Plant-woman.",
 "Aatrox": "darkin: LARGE DEMONIC WINGS (big, spread — THE feature) + glowing red eyes + massive greatsword + menacing horns",
 "Akali": "ninja: dark face MASK + high ponytail + ninja attire + smoke bomb effect. The mask + smoke.",
 "Ambessa": "Noxian matriarch: heavy Noxian plate armor + grey-streaked hair + big weapon (blade). Make the armor/blade distinct.",
 "Aphelios": "moon gunman: pale skin + dark flowing cloak + moon-themed armor + rotating moon weapons (moonstone pistols/crescents)",
 "Briar": "blood-crazed: PILLORY COLLAR around neck (THE feature — a big metal collar/cuff) + long wild reddish-pink hair + gaunt",
 "Camille": "hextech enforcer: BLADE-LEGS (legs end in blades — THE feature) + hextech augmentations + sharp features + blue",
 "Corki": "yordle pilot (MOUNTED): rides a BIPLANE/FLYING MACHINE (THE feature — the little plane he pilots) + mustache + aviator goggles",
 "DrMundo": "purple brute: PURPLE skin + oversized protruding JAW + medical bandages + big cleaver/blade. Purple + jaw + cleaver.",
 "Evelynn": "demon succubus: long LASHERS/TENTACLES (whip-like tentacles from back — THE feature) + glowing eyes + clawed fingers",
 "Galio": "gargoyle colossus: GIANT STONE FISTS + hollow chest cavity + ornate Demacian armor + wings. Big stone gargoyle.",
 "Gangplank": "pirate captain: long black BEARD + captain's TRICORNE HAT + heavy leather coat + flintlock pistols + orange barrels",
 "Garen": "Might of Demacia: heavy plate armor + large BLUE CAPE + golden WINGED HELMET (THE feature — winged helm) + big broadsword",
 "Gwen": "the doll: large OVERSIZED SCISSORS (THE feature — big golden scissors) + blue doll-like hair + stitched seams + thimble hat",
 "Hecarim": "spectral centaur (half-horse): spectral ghostly glow + undead skeletal features + ghostly trident. Centaur body (horse lower).",
 "Hwei": "ink mage: ink-stained hands + floating PAINT PALETTE (THE feature) + flowing Ionian robes + ink brush",
 "Illaoi": "priestess: the LARGE GOLDEN IDOL (Nagakabouros — a big golden idol/tentacle statue beside her — THE feature) + tribal tattoos",
 "Janna": "wind spirit: long flowing hair + ethereal WIND SWIRLS (THE feature — visible wind/cyclone around her) + flowing robes + barefoot floating",
 "Jhin": "the virtuoso: WHITE PORCELAIN MASK (THE feature — face is a white mask, not human) + wide-brimmed hat + long flowing cape + pistol",
 "Jinx": "loose cannon: EXTREMELY long blue BRAIDED PIGTAILS (THE feature — super long blue braids) + pale skin + colorful tattoos + minigun/pistol",
 "KSante": "Nazumah defender: large ornate SHOULDER GUARDS (THE feature — big shoulder armor) + traditional Nazumah attire + big mace/weapon",
 "Karma": "enlightened one: large floating MANTRA SCROLL (THE feature — floating golden scrolls around her) + meditative pose + ornate Ionian robes",
 "Kayle": "judicator: LARGE WHITE WINGS (big, spread wide — THE feature) + golden plate armor + HALO of light + blinded/folded eyes",
 "Khazix": "voidreaver (QUADRUPED): scythe-like CLAWS + chitinous exoskeleton + glowing purple eyes. Draw as a low four-legged void insect-beast.",
 "Kled": "cantankerous cavalryman (MOUNTED): rides SKAAARL the lizard (a big long lizard mount — THE feature) + tattered Noxian armor + wild facial hair",
 "Lillia": "fawn (QUADRUPED-ish): DEER LEGS + small ANTLERS + large expressive eyes + floral accents + lantern. Deer-fawn girl.",
 "Lissandra": "ice witch: ICE-COVERED FACE MASK (frozen mask over face — THE feature) + frozen bandages + floating ice shards",
 "Mel": "Noxian mage: golden skin/metallic accents + elegant Noxian robes + glowing golden sigils/magic",
 "Milio": "sweetheart fireboy: large BACKPACK with FUEL CANISTERS + FUEMIGO fire spirit companion (THE feature — a little fire sprite) + big ears (yordle-ish)",
 "Olaf": "berserker: long blonde HAIR and BEARD (THE feature — big braided beard) + fur-lined armor + war paint + dual axes",
 "Ornn": "fire demigod: large curved HORNS (THE feature — ram horns) + thick fur + broad shoulders + hooves + blacksmith hammer/anvil",
 "Quinn": "Demacian ranger: blonde ponytail + Demacian light armor + accompanied by VALOR (an eagle companion — THE feature) + crossbow",
 "RekSai": "void burrower (QUADRUPED): large GAPING MAW (huge mouth — THE feature) + sharp chitinous claws + segmented carapace. Big void beast.",
 "Rengar": "Pride stalker: cat-like EARS + thick FUR + TROPHY NECKLACES (THE feature — bone/trophy necklaces) + sharp claws + one eye",
 "Samira": "the daredevil: long dark curly hair + Noxian military attire + DUAL PISTOLS (THE feature — two big guns) + styling",
 "Senna": "shadow slayer: glowing WHITE EYES + ethereal grey skin + Sentinel armor + big Relic Cannon (THE feature — large gun)",
 "Sett": "the boss: vastayan demi-human EARS (big) + thick fur collar + heavy gold jewelry + BIG MUSCULAR ARMS (THE feature — huge arms)",
 "Sion": "undead juggernaut: exposed SKELETAL JAW (THE feature — jaw visible/skull-like) + bolted metal armor plates + giant axe",
 "Sivir": "battle mistress: large CROSSBLADE weapon (THE feature — her iconic boomerang-blade) + Shuriman desert armor + ponytail",
 "Taliyah": "weaver: FLOATING ROCKS orbiting her (THE feature — rocks circling around her) + wrapped nomadic clothing + dark hair",
 "Tryndamere": "barbarian king: long wild HAIR + fur-lined armor + BARE CHEST + rugged beard + big sword. Barbarian.",
 "Warwick": "uncaged wrath: glowing green CHEMICAL VIALS in back + metal restraints/shackles + wolf-like features (claws, snout, ears — he's a WEREWOLF)",
 "Zilean": "chronokeeper: long white BEARD + large FLOATING CLOCK (THE feature — a big floating clock/cog) + flowing robes + glowing time magic",
 "Zoe": "aspect of twilight: long flowing COSMIC HAIR + STAR-SHAPED PUPILS + floating celestial orbs/sparkles + hoodie. Cosmic girl.",
 "Ahri": "nine-tailed fox: NINE FOX TAILS fanned behind (THE feature — big fanned tails) + fox ears + whisker markings + orb",
 "Anivia": "cryophoenix (FLYING): crystalline ICE FEATHERS + glowing blue eyes + frost trail + wings. Ice phoenix bird.",
 "AurelionSol": "star forger (FLOATING): long SERPENTINE BODY (THE feature — a long coiling star-dragon body, not humanoid) + glowing star mane + horns",
 "Azir": "emperor of sands: HAWK-LIKE HEAD (bird head — THE feature) + golden ornate armor + large royal cape + sun disk",
 "Blitzcrank": "golem: large ROCKET-HAND (THE feature — one big fist) + glowing yellow eyes + exposed gears + yellow metal body",
 "Brand": "fire mage: head ENGULFED IN FLAMES (THE feature — a flame head) + molten lava veins + charred black body + fire",
 "Ekko": "boy shatterer: white hair + ZAURITE TIME DEVICE on back (THE feature — a big glowing device/backpack) + streetwear + bat",
 "Elise": "spider queen: SPIDER LEGS emerging from back (THE feature — 4-6 spider legs) + elegant gothic gown + pale skin",
 "Ezreal": "prodigy: blonde swept-back hair + floating ARCANE GAUNTLET (THE feature — a big glowing gauntlet on one arm) + leather jacket",
 "Fiora": "duelist: high-collared Demacian attire + elegant RAPIER (BIG, held forward in front — THE feature) + ponytail + rose",
 "Fizz": "trickster: large pointed EARS + webbed hands/feet + FISH-LIKE GILLS + trident. Amphibious fish-boy.",
 "JarvanIV": "exemplar: full plate armor + golden ROYAL CREST + white flowing cape + big spear/cataphract standard",
 "Jayce": "defender of tomorrow: groomed brown hair + Piltover aristocratic attire + TRANSFORMING HAMMER (THE feature — big mercury hammer)",
 "Kaisa": "void daughter: living VOID CARAPACE (bio-organic armor — THE feature) + void-infused shoulder cannons + helmet",
 "Kalista": "spear of vengeance (FLOATING): ghostly ethereal form + flowing tattered robes + hollow glowing eyes + MANY SPEARS",
 "Karthus": "death singer (FLOATING): exposed RIBCAGE + tattered burial robes + hollow glowing eyes + floating. Lich.",
 "Katarina": "sinister blade: long CRIMSON HAIR (THE feature — big red hair) + Noxian leather armor + sharp features + daggers",
 "Kayn": "shadow reaper: glowing eyes + dark SHADOW ENERGY AURA (THE feature) + flowing Ionian attire + scythe (Rhaast)",
 "Kindred": "eternal hunters: white WOOLLY LAMB (Lamb, the mask) + large SPECTRAL WOLF (Wolf companion — THE feature) + white mask",
 "LeeSin": "blind monk: BLINDFOLD (THE feature — cloth over eyes) + hand wraps + monk robes + martial arts stance",
 "Lucian": "purifier: white hair + white leather coat + DUAL PISTOLS (THE feature — two glowing light pistols) + light effects",
 "Malzahar": "prophet of the void: purple VOID ENERGY emanating from hands (THE feature) + deep hood concealing face + robes",
 "MonkeyKing": "monkey king: MONKEY FACE and FUR (THE feature — clearly a monkey) + golden armor plates + long staff (staff big)",
 "Morgana": "fallen: BOUND PURPLE WINGS (THE feature — dark wings, partially bound) + dark flowing robes + pale skin + pointed",
 "Naafiri": "darkin (QUADRUPED): Darkin living steel armor + glowing red eyes + jagged metallic form. Draw as a four-legged darkin beast.",
 "Nami": "tidecaller (mermaid): long flowing FISH TAIL (no legs — THE feature) + webbed fins + vastayan aquatic ears + staff with tide orb",
 "Nidalee": "bestial huntress: cougar-like EARS + tribal markings + leopard-print clothing + spear. Cougar-woman.",
 "Nilah": "joy unbound: flowing WATER-LIKE WHIP (THE feature — a water whip) + ornate gold jewelry + flowing robes + blue",
 "Nocturne": "eternal nightmare: BLADE-LIKE ARM (THE feature — one arm is a blade) + shadowy smoke aura + glowing eyes + sharp claws. Shadow demon.",
 "Pantheon": "unbreakable spear: plumed GREEK HELMET (THE feature — big crested helm) + LARGE CIRCULAR SHIELD + bronze armor + cape + spear",
 "Poppy": "keeper: OVERSIZED WARHAMMER (THE feature — hammer bigger than her) + heavy Demacian plate armor + blonde pigtails",
 "Pyke": "bloodharbor ripper: glowing GHOSTLY EYES + tattered nautical clothing + undead pale skin + big bone-harpoon blade",
 "Qiyana": "empress of elements: large CIRCULAR ELEMENTAL WEAPON (THE feature — a big ring-blade) + ornate Ixtali gold jewelry + green",
 "Rakan": "charmer: large GOLDEN PLUMAGE CAPE (THE feature — big feathered cape/wings on arms) + bird-like facial features + gold",
 "Rammus": "armordillo (QUADRUPED): SEGMENTED PLATING (armadillo — THE feature) + curled ball form + sturdy claws. Armadillo.",
 "Rumble": "mechanics yordle: JUNK-PILE MECHANICAL SUIT (THE feature — a big mech suit he pilots) + exhaust pipes + small yordle pilot",
 "Ryze": "rune mage: glowing BLUE RUNES on skin (THE feature) + massive muscular forearms + ancient scroll + hood",
 "Sejuani": "winter's wrath (MOUNTED): rides BRISTLE a GIANT ARMORED BOAR (THE feature — big boar mount) + heavy fur clothing + flail",
 "Singed": "mad chemist: CHEMICAL TANK on back (THE feature — big tank) + gas mask/respirator + leather apron + syringe shield",
 "Skarner": "crystal vanguard (QUADRUPED): massive CRYSTALLINE STINGER (THE feature — big crystal tail) + heavy chitinous plating + glowing",
 "Sylas": "unshackled: heavy BROKEN SHACKLES on wrists (THE feature — big dangling broken chains/cuffs) + glowing magical chains + rebel",
 "Taric": "shield of valoran: long flowing HAIR + CRYSTALLINE ARMOR (THE feature — pink/gem armor) + glowing gemstones + radiant pose",
 "Teemo": "swift scout: GREEN SCOUT HAT (THE feature — big mushroom-cap hat) + large goggles + round cheeks + brown fur. Yordle.",
 "Thresh": "chain warden (FLOATING): glowing GREEN EYES + tattered ghostly cloak + exposed RIBCAGE + big scythe + lantern (THE feature — soul lantern)",
 "Trundle": "troll king: BLUE SKIN + large protruding TUSKS (THE feature) + rugged fur pelt + big club/ice pillar",
 "Urgot": "dreadnought: SIX SPIDER-LIKE ROBOTIC LEGS (THE feature — mechanical legs) + heavy industrial armor + single red eye + cannons",
 "Varus": "arrow of retribution: glowing PURPLE CORRUPTION on left side (THE feature) + darkin armor plating + bow",
 "Vayne": "night hunter: WRIST-MOUNTED CROSSBOW (THE feature) + dark hooded cloak + high leather boots + silver bolts",
 "Vex": "gloom: long DROOPING EARS (THE feature — big droopy ears) + gloomy expression + oversized dark cloak + yordle",
 "Viego": "ruined king: pale GHOSTLY SKIN + tattered royal regalia + CROWN OF THORNS (THE feature) + big ruined sword",
 "Viktor": "machine herald: glowing HEXCORE CHEST PIECE (THE feature) + mechanical third arm + metallic body + staff",
 "Xayah": "rebel: large PURPLE FEATHERED WINGS on hips (THE feature — feathered wing-blades) + bird-like talons for feet + red/black hair",
 "Xerath": "magus ascended (FLOATING): FLOATING STONE ARMOR SHARDS (THE feature — a body made of floating stone/energy shards, no physical body) + glowing energy core",
 "XinZhao": "seneschal: Demacian plate armor + flowing cape + big SPEAR (THE feature — a long spear). Determined.",
 "Yuumi": "magical cat (FLOATING): cat floating on a BIG open MAGICAL BOOK (THE feature) + cat ears + tail + glowing aura",
 "Alistar": "minotaur: large BOVINE HORNS (THE feature — big bull horns) + broad shoulders + hooves + nose ring. Minotaur.",
 "Braum": "heart of freljord: large BRAIDED BEARD (THE feature — huge beard) + huge biceps + warm winter furs + big shield",
 "Caitlyn": "sheriff: TOP HAT (THE feature — tall top hat) + long purple coat + high boots + rifle",
 "Darius": "hand of noxus: heavy Noxian plate armor + large red cape + big AXE (THE feature — massive axe) + stern",
 "Draven": "glorious executioner: elaborate POMPADOUR HAIRSTYLE (THE feature — big hair) + ornate Noxian armor + spinning axes",
 "Gnar": "missing link: furry orange-brown COAT + large expressive eyes + transforming. Small yordle-cave-boy with bone boomerang.",
 "Heimerdinger": "revered inventor: large bushy MUSTACHE + oversized GOGGLES + academic robes + big hair. Yordle scientist.",
 "Ivern": "green father: WOODEN SKIN (THE feature — bark-like body) + leafy crown/hair + long spindly limbs + gentle. Tree-man.",
 "Jax": "grandmaster: animalistic facial features + leather straps/armor + big LAMPLIGHT POST weapon (THE feature — a glowing lamp-post staff)",
 "Kassadin": "void walker: void-infused GLOWING EYES + dark purple crystalline armor + floating void blade",
 "Leblanc": "deceiver: ornate high-collared DRESS + pale complexion + POINTED HAT (THE feature) + mirror/illusion motifs",
 "Leona": "radiant dawn: massive GOLDEN SUN-THEMED SHIELD (THE feature — big sun shield) + full plate armor + plumed helm + sun rays",
 "Lux": "lady luminosity: blonde hair + Demacian armor plating + white and gold attire + glowing LIGHT STAFF/wand (THE feature — big light magic)",
 "Maokai": "twisted treant: BARK-LIKE SKIN (THE feature — tree body) + branching arms + glowing eyes + wooden root-feet. Tree.",
 "MissFortune": "bounty hunter: long flowing RED HAIR (THE feature — big red hair) + tricorne pirate hat + dual flintlock pistols + guns big",
 "Nasus": "curator: JACKAL HEAD (THE feature — animal jackal head) + ancient Egyptian-style armor + pointed ears + staff",
 "Nautilus": "titan: heavy DIVING SUIT (THE feature — big diving suit/armor) + glowing nautical helm + massive anchor",
 "Neeko": "curious chameleon: CHAMELEON-LIKE TAIL (THE feature — a curling tail) + colorful crests on head + large expressive eyes + yordle-ish",
 "Orianna": "lady of clockwork: BALL-JOINTED LIMBS (THE feature — doll/mechanical joints) + wind-up key in back + detachable ball companion",
 "Shaco": "demon jester: JESTER HAT WITH BELLS (THE feature — three-pointed jester hat) + menacing painted smile + pointed shoes + daggers",
 "Shen": "eye of twilight: ninja attire + large SHOULDER GUARDS + KINKOU MASK (THE feature — a mask over eyes) + flowing",
 "TahmKench": "river king: MASSIVE WIDE MOUTH (THE feature — huge gaping mouth) + long prehensile tongue + golden jewelry + catfish-frog man",
 "Yone": "unforgotten: DEMONIC AZAKANA MASK (THE feature — a demon mask on face) + two swords + flowing traditional Ionian attire",
 "Yorick": "shepherd of souls: pale undead skin + tattered burial robes + sunken eyes + ACCOMPANIED BY GHOULS/Maiden (THE feature) + shovel",
 "Zed": "master of shadows: metal armor plating + FACE MASK (THE feature — a metal mask) + glowing red eyes + shadowy aura + blades",
}


def build(batch_idx):
    ids = BATCHES[batch_idx]
    lines = []
    lines.append("You are a pixel-art sprite artist AND a League of Legends expert. Hand-author JSON drawing primitives for %d specific LoL champions so their 256x256 world sprite becomes RECOGNIZABLE as that champion (canon_gate score 8-10). The VLM only JUDGES (gates); YOU author the primitives from LoL knowledge." % len(ids))
    lines.append("")
    lines.append("## Your assigned champions (process sequentially)")
    for i, cid in enumerate(ids, 1):
        c = LEDGER.get(cid, {})
        stance = c.get("stance", "")
        st = f" ({stance.upper()} stance)" if stance and stance != "upright" else ""
        hint = HINTS.get(cid, c.get("signature_features", ["?"])[0] if c.get("signature_features") else "?")
        lines.append(f"{i}. {cid} (score {c.get('score','?')}){st} — {hint}")
    lines.append("")
    lines.append("## The harness (USE THIS — do not reinvent)")
    lines.append("```python")
    lines.append('import sys; sys.path.insert(0, "exp")')
    lines.append("from champ_improver import improve, canon_for, committed_score")
    lines.append('result = improve("%s", prims_list, gate_n=3)' % ids[0])
    lines.append('# -> {"id","old","new","saved","missing","verdict","n_prims","rec"}')
    lines.append("# improve() renders to 256x256, gates (max-of-3 VLM calls to damp ~2pt")
    lines.append("# variance), and SAVES to assets/characters/{id}/sprite.png + sprites/0.png")
    lines.append("# + descriptors.json ONLY if new > old (NEVER regresses).")
    lines.append("```")
    lines.append("")
    lines.append("To see a champ's full canon identity + current missing features:")
    lines.append("```python")
    lines.append("import json")
    lines.append('d = {x["id"]: x for x in json.load(open("exp/per_champ_ledger.json"))}')
    lines.append('c = d["%s"]' % ids[0])
    lines.append('print(c["score"], c["stance"], c["body_shape"])')
    lines.append('print("features:", c["signature_features"])')
    lines.append('print("colors:", c["primary_colors"], "weapon:", c["weapon"])')
    lines.append('print("missing:", c["missing"])')
    lines.append("```")
    lines.append("")
    lines.append("## THE WINNING PATTERN (read carefully — it is the whole game)")
    lines.append("At 256px, fine detail (facial features, attire texture, armor segments) does NOT read. What scores 8-10 is exactly ONE thing:")
    lines.append("")
    lines.append("**ONE HUGE, UNIQUE signature feature that DOMINATES the silhouette (30-50% of the sprite).**")
    lines.append("")
    lines.append("22 champions are already at 8-10 — every one has a single unambiguous giant icon: Annie 9 (twin pigtails + red dress + teddy bear), Cassiopeia 8 (long snake tail + gold jewelry), Fiddlesticks 8 (scarecrow on cross-pole + straw), Velkoz 8 (single giant central eye + tentacles), Vi 8 (massive hextech gauntlets bigger than her head), Nunu 8 (giant yeti + tiny boy), Renekton (just validated 8: LONG crocodile snout with teeth + huge crescent blade).")
    lines.append("")
    lines.append("LOSERS (score 5-6) are generic humanoids where the 'feature' is 'heavy armor' or 'a sword' — at 256px that reads as a generic knight.")
    lines.append("")
    lines.append("SO for EACH of your champs, take the ONE signature feature named above and make it BIG and UNAMBIGUOUS — occupying 30-50% of the sprite. Sacrifice generic body detail to make the icon huge. Use the champion's CANONICAL colors. Outlines (dark) on everything so shapes read at 96px display.")
    lines.append("")
    lines.append("## Canvas + primitive format")
    lines.append("- 256x256, transparent background. Body center ~(128,150). Draw back-to-front. Coordinates 0-255. 20-40 primitives typical.")
    lines.append("- circle: {\"type\":\"circle\",\"cx\":int,\"cy\":int,\"r\":int,\"color\":[r,g,b],\"outline\":[r,g,b],\"outline_w\":int}")
    lines.append("- rect: {\"type\":\"rect\",\"x\":int,\"y\":int,\"w\":int,\"h\":int,\"color\":[r,g,b],\"outline\":[r,g,b],\"outline_w\":int,\"radius\":int}")
    lines.append("- polygon: {\"type\":\"polygon\",\"points\":[[x,y],...],\"color\":[r,g,b],\"outline\":[r,g,b],\"outline_w\":int}  (>=3 pts)")
    lines.append("- line: {\"type\":\"line\",\"start\":[x,y],\"end\":[x,y],\"color\":[r,g,b],\"width\":int}")
    lines.append("- ellipse: {\"type\":\"ellipse\",\"x\":int,\"y\":int,\"w\":int,\"h\":int,\"color\":[r,g,b],\"outline\":[r,g,b],\"outline_w\":int}")
    lines.append("- color = fill [r,g,b]; outline = border [r,g,b] or null; outline_w default 1.")
    lines.append("")
    lines.append("## Style reference (READ 2 before authoring)")
    lines.append("`exp/hand_author_sprites.py` has 30 worked examples. Read `annie_prims` and `cassiopeia_prims` (or `yuumi_prims`; `sejuani_prims` for mounted; `volibear_prims` for quadruped). Named color constants, back-to-front order, the signature feature drawn BIG, outlines on everything. Also `exp/_renekton_test.py` (just-validated 8: big crescent blade + crocodile snout).")
    lines.append("")
    lines.append("## Workflow per champion (do this for EACH assigned champ)")
    lines.append("1. Fetch its canon + missing features (snippet above).")
    lines.append("2. Decide the ONE huge signature feature (named above).")
    lines.append("3. Author a full primitive list (back-to-front, the icon BIG, outlines on everything).")
    lines.append("4. Call `improve(cid, prims, gate_n=3)`. Note `new` and `missing`.")
    lines.append("5. If `new < 8` and `missing` lists fixable features: make the missing feature BIGGER/more obvious (don't add tiny detail — make the icon bigger/clearer). Re-call improve. Up to 3 authoring rounds. Keep the best.")
    lines.append("6. Move to the next champ. Process champs SEQUENTIALLY (one VLM call at a time — concurrency 4 is the global limit and other agents are running too).")
    lines.append("")
    lines.append("## Hard constraints")
    lines.append("- NEVER use the Read tool on any .png file in this repo — it crashes the session. Inspect sprites only through the harness (render + gate) or via ASCII grid (render to /tmp, load with pygame.surfarray, print a 32x32 alpha grid — see exp/_renekton_test.py).")
    lines.append("- Only touch YOUR assigned champions. Do not save or modify others.")
    lines.append("- improve() auto-saves when new > old. Never force a save that doesn't beat base.")
    lines.append("- Do not edit exp/canon_gate_results.json — the coordinator re-gates after the batch.")
    lines.append("- Work in /home/misa/Desktop/RD/Gacha on branch vlm-canon-overhaul.")
    lines.append("- VLM endpoint is slow (~30-60s per gate call). Be patient; the harness retries.")
    lines.append("")
    lines.append("## Report back (return ONLY this — a JSON array + one-line summary)")
    lines.append("```")
    lines.append("[")
    lines.append('  {"id":"%s","old":4,"new":8,"saved":true,"rounds":2,"missing_final":[],"feature":"..."},' % ids[0])
    lines.append("  ...")
    lines.append("]")
    lines.append("```")
    lines.append('Plus a one-line summary: "X/%d champs improved, Y reached >=8."' % len(ids))
    return "\n".join(lines)


if __name__ == "__main__":
    idx = int(sys.argv[1])
    print(build(idx))
