# VLM Canonical Sprite Overhaul — Design Spec

**Date:** 2026-07-31 (supersedes the 2026-07-31 VLM-in-the-loop spec; that feature
shipped but a strict canonical audit proved 0/170 sprites recognizable — the
calibrated gate was dishonest. This spec is the real fix.)
**Status:** Approved (brainstorm sections 1-3)
**Author:** design session

## Goal

Make the per-champion world sprites **actually recognizable** as their champion.
The honest target: canonical mean match ≥ 6.0, recognizable ≥ 70%, stance
captured ≥ 90% (from today's 1.18 / 0% / 46%). Accept that pixel-art at 256px
cannot depict specific faces — recognizability comes from **stance + body
silhouette + signature features + colors** (a white bear with lightning =
Volibear; a 9-tailed red fox-girl = Ahri), not from a face.

## Background — what the audit proved

A strict canonical gate (VLM LoL knowledge as ground truth, NOT splash
similarity) scored the 170 baked sprites: **mean 1.18/10, 0/170 recognizable,
46% stance captured, 8% colors captured, 169/170 ≤ 3/10.** The earlier
"6.18/6.24 gate pass" was a calibrated prompt scoring "right color family" as
6+ — dishonest. Root causes (three independent layers, all broken):

1. **Gate** was splash-similarity + calibrated (fake). Must become canonical
   (VLM LoL knowledge, strict, multi-axis).
2. **Descriptor** was VLM-flying-blind (only the splash image, no champ
   identity). Grounding prototypes proved that feeding name/title/lore/abilities
   makes the VLM pick the right archetype/weapon/features/colors (Ahri →
   vastaya/orb/fox_tails/red).
3. **Renderer** is the ceiling: 10 archetypes, ALL humanoid-upright. 92/170
   champs need a different body shape (39 non-upright: quadruped/mounted/flying/
   floating; 51 upright-but-wrong-body: minotaur/rock-golem/spider/primate...).
   No prompt/loop fix can make a knight-body look like Volibear (a bear).

Surveys that drove this spec (raw in /tmp):
- `body_type_survey.json` — VLM text-classified 170 champs → 5 stances
  (upright-biped 139, quadruped 14, floating 9, mounted 6, flying 2).
- `canon_survey_full.json` — per-champ canonical identity (stance, body_shape,
  signature_features, colors, weapon) + canonical gate scores, proving 0%
  recognizable and the 92-champ stance gap.

## Architecture — stance-driven 2-level dispatch

Add a `stance` field to the descriptor; `draw_chibi_descriptor` dispatches by
stance, then by archetype within stance, then applies features + weapon.

```
descriptor = {stance, archetype, weapon, palette, features, build, motif}  # +stance

draw_chibi_descriptor(surf, desc):
  stance = desc["stance"]
  upright   → _ARCH_DRAW[archetype](...)                 # 10 existing + 5 new bodies
  quadruped → _QUAD_DRAW[archetype](...)                 # 1-2 new + feature mods
  mounted   → _draw_mounted(rider_archetype, mount_kind) # 1 new (rider + mount)
  flying    → _FLY_DRAW[archetype](...)                  # 2 new (bird/dragon)
  floating  → _ARCH_DRAW[archetype] + _floating_modifier # modifier on humanoid + 1 unique (eye)
  _apply_features(...)   # ~15 new feature primitives
  draw_weapon(...)
```

`stance` and the new `archetype`/`features` values are VLM-facing vocab. The
VLM picks them from the champ's canonical identity + splash.

## Renderer primitives — data-shaped (Section 2)

Body clusters from the survey (21 clusters → ~10 drawers + feature mods):

### New stance/body drawers (8)
| Drawer | Stance | Champs | Notes |
|--------|--------|--------|-------|
| `quadruped` | quadruped | 14 | one drawer + feature mods: `shell` (Rammus), `stinger` (Skarner), `fur` (Volibear/Warwick), `insect_carapace` (Khazix/Belveth), `void_fins` (KogMaw/Chogath) |
| `mounted` | mounted | 6 | rider (reuses an upright archetype) + a mount body (boar/yeti/lizard/bird/wolf/plane) chosen by a `mount_kind` field |
| `flying_bird` | flying | 1 (Anivia) | winged bird body |
| `flying_dragon` | flying | 1 (AurelionSol) | serpentine dragon body |
| `rock_giant` | upright | 2 (Malphite, Galio; +Ornn) | massive rocky humanoid, craggy texture |
| `treant` | upright | 2 (Maokai, Ivern) | tree-bark humanoid |
| `blob` | upright | 1 (Zac) | amorphous slime body with arms |
| `naga` | floating/upright | 2 (Cassiopeia, Nami) | humanoid upper + serpentine/fish lower |

### Stance modifiers (2)
- `floating_modifier` — applied to an existing humanoid archetype (mage/rogue/
  knight): no legs, hover aura disc. Covers 17 float-humanoid champs
  (Janna/Karthus/Sona/Syndra/Thresh/Orianna/Seraphine/Karma/Lissandra/Morgana/
  Kayle/Bard/Vex/Xerath/Zilean/Zoe/Evelynn).
- `float_eye` — 1 unique body (Velkoz): central eye + floating tentacles.

### Upright bodies via feature-mod on existing archetypes (no new drawer)
- minotaur (Alistar) = brute + `large_horns` + `bovine_head`
- scarecrow (Fiddlesticks) = mage + `mask` + gaunt build
- avian_humanoid (Rakan, Xayah) = vastaya + `feathered_wings`
- arachnid (Elise) = humanoid + `spider_legs`
- dragon_humanoid (Shyvana) = humanoid + `dragon_horns` + `dragon_wings`
- small_beast (Gnar, Twitch, Kennen) = yordle + `tail` + `animal_ears`
- crocodilian (Renekton), jackal (Nasus), feline (Rengar) = beast-upright
  variant + `snout`/`fur`/`tail`

### New feature primitives (15, frequency-shaped)
| Feature | Champs | Existing? |
|---------|--------|-----------|
| `tail` (generic, multi-tail via count) | 26 | new (vastaya has 1; generalize) |
| `long_hair` / `mane` | 40 | new (build handles proportion; this adds visible hair) |
| `pointed_ears` (merge with animal_ears) | 30 | animal_ears exists; add pointed variant |
| `large_horns` | 10 | horns exists; add large/curved variant |
| `feathered_wings` | 8 | wings exists; add feathered variant |
| `dragon_wings` | 3 | new (bat/scale wing) |
| `fur` | 20 | new (body texture overlay) |
| `scales` | 2 | new (body texture overlay) |
| `hat` / `plumed_helmet` | 20 | new (headgear) |
| `beard` | 6 | new |
| `chains` | 3 | new (Thresh/Sylas) |
| `dual_pistols` (weapon variant) | 3 | new weapon drawer |
| `spider_legs` | 1 (Elise) | new |
| `bovine_head` / `snout` | 2 | new (animal head) |
| `glowing_eyes` | 32 | new (small eye-glow modifier) |

Existing features kept: cape, hood, horns, wings, mask, halo, spikes, crown,
fox_tails, animal_ears, claws.

**Total new primitives: ~8 body drawers + 2 stance modifiers + 15 features + 1
weapon variant = ~26 new draw functions (~1800 lines of pixel-art).**

## VLM pipeline — grounding + canonical gate (Section 3)

### describe (champ context + canon identity + splash → descriptor)
```
system: "art director, FIXED vocab (stance + archetype + features + weapon +
         palette + build + motif). Given the champ's IDENTITY (name, title,
         faction, role, abilities, lore) AND CANONICAL body (from LoL knowledge)
         AND the splash, produce the descriptor that best captures the canonical
         identity within the fixed vocab."
user:   "Champion: Ahri — the Nine-Tailed Fox. Faction ionia, role hunt.
         Abilities: Orb of Deception, Fox-Fire, Charm, Spirit Rush.
         CANONICAL: fox-girl vastaya, 9 fluffy white tails, fox ears,
         red & white kimono, floating orb, upright-biped.
         [splash image]. Produce best descriptor. JSON only."
output: {stance, archetype, weapon, palette, features, build, motif}
```

### critique (champ context + canon + splash + sprite → canonical match + suggested)
```
system: "STRICT critic. Judge whether the sprite captures the champion's
         CANONICAL identity (stance + body shape + signature features + colors),
         NOT splash-similarity. Be strict."
output: {canonical_match:0-10, stance_captured:bool, body_shape_score:0-10,
         features_missing:[...], colors_captured:bool, recognizable:bool,
         suggested_descriptor:{...}}
```

### canonical gate (canon + sprite, NO splash — measures against the origin)
```
output: {canonical_match:0-10, stance_captured, body_shape_score,
         features_captured:[...], features_missing:[...], colors_captured,
         recognizable, verdict}
```
This is the HONEST gate (VLM LoL knowledge as ground truth). It replaces the
calibrated splash-similarity gate.

### Loop
describe → draw → critique → revise, max 10 rounds, stop when
`canonical_match ≥ 7` (canonical, not splash). Keep best-`canonical_match`
round if never converges.

### Canonical gate script (`tools/verify_canon_gate.py`)
Reads every `descriptors.json` + sends sprite + canon identity to the VLM →
canonical_match. Pass conditions:
- mean canonical_match ≥ 6.0
- recognizable ≥ 70% (≥119/170)
- stance_captured ≥ 90% (≥153/170)

## Phasing

| Phase | What | Output | Gate |
|-------|------|--------|------|
| **P1: Renderer overhaul** | Implement ~26 new primitives (8 body drawers + 2 stance mods + 15 features + 1 weapon) in `src/assets_gen/generate.py`; add `stance` to the descriptor + dispatch; widen the VLM vocab. | Renderer can draw all 5 stances + new bodies + features. | `tools/verify_primitives.py` — each new primitive renders 256×256, coverage > 0, in-bounds, distinct from siblings. |
| **P2: VLM pipeline rewrite** | Rewrite `vlm_client.py` prompts (grounding + canon); add canonical gate; rewrite `sprite_loop.py` to use canonical_match (not splash match) + stop at 7. | Pipeline drives the new renderer with canon-grounded descriptors. | `tools/verify_vlm_client.py` + `tools/verify_sprite_loop.py` updated; FakeVLM tests pass. |
| **P3: Re-bake 170 Original** | Bake all 170 Original skins with the new renderer + canon-grounded pipeline. | 170 re-tuned `sprite.png` + `descriptors.json` with canonical_match. | `verify_canon_gate.py`: mean ≥ 6, recognizable ≥ 70%, stance ≥ 90%. + `verify_assets` + 21-test. |
| **P4: Re-bake 1780 per-skin** | Extend to all ~1780 skins (resumable). | 1780 per-skin `sprites/{idx}.png`. | `verify_assets` (per-skin coverage) + canon gate sample + 21-test. |

P1+P2 are code; P3+P4 are bakes. P3 is the proof point (must hit the canonical
gate targets before P4 scales).

## Verification strategy

1. **Primitive tests** (P1): each new drawer/feature renders 256×256, coverage
   > 0, in-bounds, distinct coverage from siblings. Headless, no image Read.
2. **VLM client/loop tests** (P2): FakeVLM (no network) — describe/critique/gate
   parse + validate; loop stops at canonical_match ≥ 7; cache round-trips.
3. **Canonical gate** (P3/P4): `verify_canon_gate.py` — real VLM, mean ≥ 6,
   recognizable ≥ 70%, stance ≥ 90%. The honest metric.
4. **Asset verify** (`tools/verify_assets.py`): every sprite 256×256, coverage
   > 0, archetype distinctness (updated for new archetypes), descriptors.json
   per skin.
5. **Game acceptance** (`/tmp/verify_complete.py`, 21 tests): no game-logic
   regression (renderer is build-time only; runtime loads PNGs — combat/AI/
   physics untouched).

## Risk fences

- **Stochastic VLM** → baked PNGs committed (deterministic runtime). Re-bake
  only on `--force`. Canonical gate re-runnable on committed assets.
- **VLM endpoint down** → build fails gracefully (skip skin, keep old sprite,
  log error). Never crashes the game.
- **Renderer primitive broken** → `verify_primitives` catches (coverage 0 /
  out-of-bounds) before bake.
- **Scope** — ~26 primitives is large; P1 implements + tests each before P3
  bakes. If a primitive can't depict its champs (canon gate < 6 for that
  cluster), iterate the primitive before scaling.
- **HARD CONSTRAINT preserved**: never Read a PNG/JPG via the Read tool. VLM
  reads images over HTTP base64 (outside the session); build uses headless
  `pygame.image.load`. Tests assert load-path/size/coverage, never pixel Read.

## Out of scope

- Specific faces (pixel-art at 256px can't depict a specific face; recognizability
  via silhouette + features + colors).
- Mid-scene hot-swap of the world sprite on skin change (re-entering the world
  suffices — already wired).
- Re-baking non-sprite assets (portraits/icons are real LoL art; unchanged).
- The latent `ow_party_state` level/ascension/evolve ECS-mirror bug (out-of-scope
  from the sprite work; does not affect sprites/combat).

## Relationship to the shipped (broken) feature

The merged `vlm-sprite-loop` branch (commits 08c7c42..eb9292c) shipped the
plumbing: VLM client, sprite loop, concurrent bake, CLI, per-skin `sprites/`
output, skin-switch runtime wiring, `descriptors.json` cache. That plumbing is
REUSED — this overhaul rewrites the renderer primitives, the VLM prompts
(grounding + canonical), and the gate (canonical, strict), then re-bakes. The
runtime wiring (load_char_sprite skin_idx, Hero.skin, WorldCharacter._load_sprite)
is unchanged and correct.
