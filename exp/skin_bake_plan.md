# Per-Skin Sprite Bake — Design (170 tasks)

## Goal
Generate a world sprite for every skin of every champ (1610 skins across 170 champs), as a LIGHT MODIFICATION of the now-high-quality default skin (skin 0).

## Why light mods
Skin 0 is hand-authored to 8-10 canon_gate for 108 champs (96% recognizable). A skin is mostly a RECOLOR of the default (different palette) ± a feature add/remove (e.g. Star Guardian adds wings, Arcade adds neon glow). Recoloring a good base can't break the silhouette, so each skin inherits the base's recognizability.

## Per-champ task (×170)
For champ C with skins [0, 1, 7, 14, ...]:
1. Load skin-0 primitives (the hand-authored base).
2. For each non-zero skin N with a splash (skins/N.jpg):
   - VLM looks at the skin splash (image 1) + the default sprite (image 2) + skin name → outputs a JSON delta: `color_map` (base→skin color pairs) + `adds` (new primitives for skin-specific features).
   - Apply delta to skin-0 primitives: recolor matching fills/outlines, append adds.
   - Render → `sprites/N.png` + `descriptors.json[N]`.
3. One VLM call per skin (describe only, no revision loop). ~40s/skin.

## Harness
`exp/skin_modder.py`:
- `describe_skin_delta(cid, idx)` → VLM delta (color_map + adds)
- `apply_delta(prims, delta)` → revised prims (recolor + add)
- `mod_skin(cid, idx)` → describe + apply + save
- `mod_all_skins(cid)` → all non-zero skins for a champ

## Execution
`exp/bake_all_skins.py` — concurrent driver (ThreadPoolExecutor 4 = VLM concurrency). 170 champs, each processes its skins sequentially. Resumable: skips skins already generated (`generator=="skin_mod"` in descriptors). Progress logged to `exp/skin_bake_progress.jsonl`.

~1610 skins × ~40s / 4 concurrent ≈ 4.5 hrs (background job).

## No per-skin gate (by construction)
Skins inherit the base silhouette (8-10 for 108 champs). A recolor can't make Ahri stop reading as Ahri. Spot-check a random sample instead of gating all 1610 (saves ~1610 VLM calls / ~2hrs).

## Tracking
`exp/skin_bake_progress.jsonl` — one line per skin: {cid, skin, name, recolor, adds, saved, t}. Final summary: skins generated / total.
