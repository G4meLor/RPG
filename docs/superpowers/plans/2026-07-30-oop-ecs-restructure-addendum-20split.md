# Addendum: Task 20 Split (20a-20e)

> **Parent plan:** `docs/superpowers/plans/2026-07-30-oop-ecs-restructure.md`
> **Reason:** Task 20 (big-bang takeover) did not converge — the 9 systems are minimal stubs, and a faithful port is ~3700 lines of intricate interdependent logic. The user approved splitting Task 20 into 5 sub-tasks (20a-20e), each porting one system to full fidelity (verbatim from legacy) while KEEPING the legacy running in parallel, with a 21/21 regression gate per sub-task.

## Sub-tasks

### Task 20a: RenderSystem full-fidelity port
**Goal:** Port all ~25 `_draw_*` methods + atmosphere helpers (_biome_atmos/_rain_overlay/_fog_overlay/_sky_for_phase/_night_level/_night_overlay/_torch_sprite/_draw_chevron/_draw_edge_hints) from WorldScene into `RenderSystem.draw(surf, map_ctrl)`, operating on entity components (Transform/Health/Render) + map_ctrl + legacy particles/projectiles/floats. Keep legacy `WorldScene.draw` running in parallel (additive). Gate: verify_ecs + verify_assets + 21/21 + 120f world no crash.

### Task 20b: HudSystem full-fidelity port
**Goal:** Port `_draw_hud`/`_draw_skill_bar`/`_draw_skill_tooltip`/`_draw_minimap`/`_draw_boss_banner`/`_draw_ascend_banner`/`_hud_portrait`/`_skill_icon` into `HudSystem.draw(surf)`, reading entity components + active hero. Keep legacy HUD running in parallel. Gate: same.

### Task 20c: CombatSystem full-fidelity port
**Goal:** Port `_do_attack`/`_do_skill`/`_do_ultimate`/`_on_enemy_hit`/`_on_enemy_death`/`_element_mult` + boss patterns + toughness break + reactions + combo climax + signature passives + summons/traps + projectiles + DoT + ult variants into `CombatSystem`, operating on entities (Combat.stat_obj for stat reads, Health/Statuses mutation, Transform for spatial). Keep legacy combat running in parallel. Gate: same (ranged_combat + melee_combat must pass via legacy; the system computes in parallel).

### Task 20d: AISystem + PhysicsSystem full-fidelity port
**Goal:** Port `WorldEnemy.update` AI (all per-id branches + boss patterns + state machine) into `AISystem`, and `WorldCharacter.update` movement (click-to-move + dash + accel/friction + collision + move_speed modifiers) into `PhysicsSystem`, operating on entity Transform/Movement/AI + Combat.stat_obj. Keep legacy running in parallel. Gate: same.

### Task 20e: The swap — delete legacy driving, entities become source of truth, WorldScene thin coordinator + rewire dependents
**Goal:** Now that all systems are full-fidelity, delete the legacy `WorldCharacter`/`WorldEnemy` driving + the entity adapter. `WorldScene.update` calls systems only; `WorldScene.draw` calls render/hud only. WorldScene shrinks to ~150-800 lines. Rewire `adventure.py` (subclass), `map_ctrl.py` (scene refs), `verify_ecs.py` + `verify_complete.py` (use entity API). Update the 21-test suite's setup to use `spawn_enemy`/entity API. Gate: verify_ecs + verify_assets + boot smoke (world + adventure 120f) + as many acceptance tests as feasible + 1200-frame stress no regression.
