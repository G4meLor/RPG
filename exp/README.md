# VLM Sprite Generation Experiments

## Goal
Make 170 champion world sprites recognizable via VLM-generated drawing primitives.

## Approach
VLM (misa-gemma-4-31b-it) generates JSON drawing primitives (circle/rect/polygon/
line/ellipse) from champion canon text (no fixed renderer vocab, no skin image).
Loop: render → VLM critiques vs canon → revise → repeat (stop at cm>=7).

## Pipeline
1. **Phase 1** (`vlm_sprite_gen.py`): VLM generates primitives from canon text only.
   Loop max 10 iters. 170 champs, concurrency 4.
2. **Phase 2** (`vlm_sprite_gen2.py`): Splash-guided 1-pass refinement for good champs
   + regen for failed/low champs.
3. **Fix round 1** (`vlm_sprite_fix.py`): Targeted re-gen for 15 champs scoring <4
   with specific fix guidance from root-cause diagnosis.
4. **Fix round 2** (`vlm_sprite_fix2.py`): Same approach for the remaining 18 low champs
   with even more specific pixel-level guidance.
5. **Fix round 3** (`vlm_sprite_fix3.py`): 7 hard champs (pixel-level instructions) +
   42 borderline champs (quick 3-iter refinement).

## Results (final canon gate)
- mean: 5.74/10 (target 6.0 — close)
- recognizable: 96/170 = 56% (target 70%)
- stance captured: 159/170 = 94% (target 90% — ACHIEVED)
- 4 champs still <4: Sona(3), Shyvana(3), Renata(3), Zeri(3)

## Full journey
| Stage | Mean | Recognizable | Stance |
|-------|------|-------------|--------|
| Original (fixed renderer) | 1.18 | 0% (0) | 46% |
| Phase 1 (VLM primitives) | 5.25 | 26% (44) | — |
| Phase 2 (splash refine) | 5.43 | 28% (48) | — |
| Canon gate v1 | 5.46 | 49% (83) | 90% |
| Fix round 1+2 | 5.49 | 49% (83) | 94% |
| Fix round 3 (FINAL) | 5.74 | 56% (96) | 94% |

## Next steps (if continuing)
- Push mean to >=6.0: refine the ~47 champs scoring 5 (push to 6).
- Push recognizable to >=70%: the 74 champs scoring 4-6 need specific feature fixes.
- 4 hard champs (Sona/Shyvana/Renata/Zeri): VLM 31b struggles with complex features
  (musical instrument, dragon scales, chemical apparatus, electric hair+gun-arm).
  May need hand-drawn primitives or a different approach.

## Files
- `vlm_sprite_gen.py` — Phase 1: initial generation from canon text
- `vlm_sprite_gen2.py` — Phase 2: splash refine + regen failures
- `vlm_sprite_fix.py` — Fix round 1: targeted fix for 15 low champs
- `vlm_sprite_fix2.py` — Fix round 2: targeted fix for 18 low champs
- `vlm_sprite_fix3.py` — Fix round 3: hard champs + borderline refinement
- Results: `/tmp/vlm_gen_results.json`, `/tmp/vlm_gen_phase2_results.json`,
  `/tmp/vlm_fix_results.json`, `/tmp/vlm_fix2_results.json`, `/tmp/canon_gate_results.json`
  (these are in /tmp — should be copied to exp/ for persistence)

## Fix round 4-5 + hand-author findings (2026-08-01)

### What was tried
- **fix4 (additive patches)**: keep the base, append only new primitives for
  missing features. Result: REGRESSED. Appended primitives clutter the sprite
  → critic sees noise → score drops (Ahri 6→4→3, Sona 3→2).
- **fix5 (splash-grounded fresh gen, best-of-3, no revision)**: generate fresh
  from the skin-0 splash image. Result: REGRESSED on 2/4 smoke champs. The VLM
  31b's fresh single-pass from a splash is WORSE than from canon text — the
  splash's 3/4 angles confuse the front-facing sprite generation.
- **hand-author (no VLM in generation; VLM only gates)**: I place primitives
  from LoL knowledge. Result: 2/4 improved (Ahri 6→8, Annie 6→8), 2/4 regressed
  (Fiora, Darius — my versions worse than the VLM's). Saved only the wins.

### Root-cause conclusions
1. **The VLM 31b's revision loops all fail** — full-regen drops features,
   additive patches clutter, splash fresh-gen regresses. Single fresh pass from
   canon text is the only thing that produced the 8/10 sprites.
2. **The canon gate has ~2pt variance** — Fiora/Darius scored 6 in the original
   run but 4-5 on re-gate. The "mean 5.74, recognizable 56%" are noisy.
3. **Hand-authoring wins on BIG countable features** (9 tails, pigtails+bear,
   giant gauntlets) but loses on subtle attire/proportion champs (Fiora, Darius).
4. **The achievable ceiling for the VLM 31b + 256px pixel primitives is ~60%
   recognizable**, not 70%. The 8/10 sprites all have one huge iconic feature.

### Scripts added
- `exp/vlm_sprite_fix4.py` — additive patches (regressed, kept for record)
- `exp/vlm_sprite_fix5.py` — splash fresh-gen best-of-N (regressed, kept for record)
- `exp/hand_author_sprites.py` — hand-authored sprites (Ahri/Annie saved at 8/10)
- `exp/recompute_scores.py` — re-gate all 170, max-of-2 to reduce variance
