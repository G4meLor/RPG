# Aetheria — Big Bang Enhancement (Design)

Date: 2026-07-27
Status: Drafted — awaiting user review (Review-gate mode)
Origin: a 12-agent research+critique workflow (7 dimension researchers → 4 critics → 1 synthesis; 51 proposals → 204 verdicts → 20 enhancements). Core "90%-built but unwired" claims verified against the live code.

## Vision

Aetheria is already production-polished (134 audit fixes shipped). This pass targets the **highest-leverage gaps the audit left behind**, not greenfield work:

1. **Finish the half-built combat engine** — DoT ticks, toughness-break payoff, combo climax, variable hit-stop — so the 7 combat paths and 4 reactions actually play differently. (Verified: `tick_effects` is never driven; the break burst/multiplier are flagged but never applied; hit-stop is flat; the combo ramps to +40% with no climax.)
2. **Give the 25 heroes real identity** — constellation perks, signature passives, unique ultimate variants, lore, element leitmotifs — so pulling a dupe is exciting and each hero plays differently. (Verified: `ASCENSION_BONUS` is a flat 1.0→1.50 multiplier; 25 heroes share 7 ultimates and 9 passives.)
3. **Make the open world breathe** — gameplay-affecting weather, breakable props, hidden rift mini-dungeons, a quest compass — so exploration has direction and surprise. (Verified: `MapRenderer` cache is keyed on `(c,r)`; weather must stay a live overlay.)
4. **Make the gacha reveal and the endgame loop worth returning to** — a tension crescendo and an NG+ cycle. (The game ends structurally at the Demon King.)
5. **Ship the cheap accessibility/readability wins** — colorblind palette, boss HUD, reaction stings — pure draw/data, near-zero risk.

**Dropped (by the critics):** full-screen bloom (perf liability on a 1280×720 cached-overlay scene), live water reflections (L for 2 biomes), town hub (L, redundant with shop), adaptive music infrastructure (L, mixer contention — boss/leitmotif stings ship as one-shots instead), artifact relics (breaks the 3-slot equipment logic), per-hero voice stings (20 stings, robotic-sound risk, overlaps the swap moment), onboarding coach marks (controls hint already shown).

**Constraint discipline (every enhancement respects):** the cached-map model (weather/elite-ness computed at `_load_map`, never in `gen_map`), the LoL control scheme, the pure-procedural constraint (no external art/audio), single-dev, ~60fps, must verify headless, and the init-order gotchas (fields used in `_load_map` declared in `__init__` before `_load_map`).

The set is **20 enhancements: 8 P0 (cheap, high-impact, mostly draw/data/wiring) + 12 P1 (M-cost identity/world/meta wins)**.

---

## P0 — ship first (cheap, high-impact)

### 1. Hero Lore, Bio & Personality Text  *(characters, S)*
Add a lore/bio/quote field per hero (25 entries, ~50 words) shown in the codex and hero-detail screen — pure data, no art/runtime changes, the cheapest identity payoff that drives gacha attachment.
- **Inspiration:** Genshin Impact character profiles; Fire Emblem Heroes bios.
- **Value:** The codex (main.py:1869) shows portrait + name + stars and nothing else; heroes have a `title` but no backstory. A 2-sentence bio + signature quote turns "Aria, Knight of Dawn" into a character the player cares about. Pure data, zero combat/perf risk.
- **Sketch:** `data.py`: add `HERO_LORE` dict `hero_id -> {bio, quote, personality}` (25 entries, bios tying into existing title/element/role). `main.py` `HeroDetailScene.draw` (left panel x=40 y=110 w=400 h=480, space below portrait at y~560): add a lore panel with bio + centered italic quote, capped ~120 chars, word-wrapped with the existing `text()` helper. `CodexScene.draw`: on hero-card hover show a tooltip with the bio. No entities/world_scene/generate_assets changes.
- **Files:** data.py, main.py
- **Risk:** Writing 25 compelling bios is creative work but zero technical risk. Cap length + word-wrap is the only guard. No save migration; no headless-verify impact.

### 2. Wire the DoT/Status Engine into Real-Time Combat  *(combat, M)*
The `StatusEffect`/`tick_effects` machinery (entities.py:234) exists but is never driven in the world loop, so poison/burn/bleed from nihility heroes and debuff skills do nothing. Convert `tick_effects` to time-based and drive it in the enemy update loop so status-inflicting heroes become viable sustained-DPS dealers.
- **Inspiration:** Hades (stacking Doom/boon DoTs); Dead Cells (poison/bleed pressure).
- **Value:** Makes 3 of the 7 combat roles (nihility, dark/fire debuff kits) actually do what their tooltips say. Today a bleed/poison hero gets a 1.5s stun and nothing else. Unblocks the burn/freeze ultimate variants (enhancement #11).
- **Sketch:** `entities.py`: convert `StatusEffect.tick()` (line 55) from per-turn (`duration-=1`) to time-based — add a `self.t` accumulator; `tick(dt)` returns `(kind, val)` when the accumulator crosses an interval (~0.5s); duration becomes seconds. `world_scene.py`: in the enemy update loop (line ~1923, `for en in self.enemies: en.update(...)`) add `for res in en.enemy.tick_effects(sim_dt): apply damage + FloatText`. In the `_do_skill` debuff branch (line ~1385/1405) call `nearest.enemy.add_effect(skill['debuff'], dur, potency)` in addition to the proxy stun. `data.py`: add `dot_potency` per debuff skill so burn/bleed/poison have distinct tick values.
- **Files:** entities.py, world_scene.py, data.py
- **Risk:** Balance — DoTs could be negligible (potency too low) or trivialize bosses (stack with the +50% broken multiplier). Cap stacks; tune per debuff. `add_effect` already dedupes by type so re-application doesn't double-stack.

### 3. Complete the HSR Toughness-Break System  *(combat, M)*
Toughness shaving and the break flag exist (entities.py:98-190), but broken enemies never recover, the +50% break damage (`TOUGHNESS_BREAK_MULT` data.py:354) and the 15%-max-hp break burst (`TOUGHNESS_BREAK_DAMAGE` data.py:355) are never applied because `WorldEnemy.take_damage` (world_entities.py:751) bypasses `entities.take_damage`. Finish the wiring so breaking a boss is a real tactical milestone.
- **Inspiration:** Honkai Star Rail (weakness break: delay + bonus damage + recovery); Genshin (elemental gauge depletion).
- **Value:** Gives every enemy a visible "break" moment the player can aim for with weakness-element hits — a burst of bonus damage, a visible stagger, and a damage-up window. Today breaking a boss just stuns it for 1.2s with no payoff.
- **Sketch:** `world_entities.py` `WorldEnemy.take_damage` (line 751): after `broke = self.enemy.damage_toughness(dmg)`, if broke apply the `TOUGHNESS_BREAK_DAMAGE` burst (`hp -= int(max_hp * D.TOUGHNESS_BREAK_DAMAGE)`) and fire `on_attack('boss_break', self)`; apply the +50% broken multiplier by checking `self.enemy.broken` before `dmg = max(1, int(amount))`. `WorldEnemy.update` (line 780): add a `_broken_recover_t` timer; on elapse call `self.enemy.recover_toughness()` (entities.py:176) so the enemy re-breakable; reset the timer on break. `world_scene.py` `_on_enemy_event` (line ~2041): add a `boss_break` branch — big ring + "BROKEN!" float + longer hit-stop. **Gate the break burst to bosses/elites only** so it doesn't one-shot weak enemies.
- **Files:** world_entities.py, world_scene.py, data.py
- **Risk:** Recovery too fast → break feels pointless; too slow → perma-broken. The 15%-max-hp burst could one-shot weak enemies — gate to bosses/elites. Keep the break bonus from stacking absurdly with reaction/weakness bonuses.

### 4. Boss HUD: Toughness Bar + Phase Threshold Markers  *(ui, S)*
Visualize the toughness/break system as a thin white bar under enemy HP bars that depletes on hits and flashes "BROKEN" when broken, and add 66%/33% phase-threshold tick marks + a phase-transition flash to the boss HP bar — pure draw additions on data that already updates.
- **Inspiration:** Honkai Star Rail toughness bar; Monster Hunter Rise phase-break indicators; Genshin segmented boss HP.
- **Value:** Players can see how close an enemy is to a break (which grants +50% damage) and exactly when a boss enters its next phase (which unlocks new telegraphed patterns). The toughness/break system is computed but invisible; this makes the mechanic readable.
- **Sketch:** `world_entities.py` `Enemy.draw` (line ~1087): after the HP bar, if `has_toughness()`, draw a thin 4px white bar with `frac = toughness/max_toughness`; if `broken`, draw a flashing "BROKEN" tag in (255,200,90). Show the toughness bar only after first hit (toughness < max) to avoid clutter. `world_scene.py` boss bar (line ~2685): below the boss HP bar add a toughness bar + "BROKEN — +50% DMG" label when broken. Phase markers: after the HP fill draw two 2px vertical tick lines at 66% and 33% in (40,40,50). Phase-transition flash: in `_on_enemy_event` `boss_phase` (line ~2089) set `_boss_phase_flash_t = 0.5`; in the boss bar draw, if >0, draw a white alpha overlay that fades. **Respect `reduce_motion`** (skip the flash, keep the tick marks). Phase thresholds (0.66, 0.33) already in `WorldEnemy.update` (line ~806). Cache the "BROKEN" text surface.
- **Files:** world_entities.py, world_scene.py
- **Risk:** Low — the data already exists and updates; purely a draw addition. Only risk is visual clutter on small enemies — show the toughness bar only after first hit, keep it 4px. The phase flash must respect `reduce_motion`.

### 5. Distinct Elemental Reaction Stings  *(audio, S)*
Replace the single generic "explosion" sound that fires for every elemental reaction (world_scene.py:1559) with 4 distinct, element-flavored stings — Steam (airy hiss + chime), Spread (warm woosh), Freeze (crystalline ping), Rupture (dark dissonant hit) — so each reaction has its own audio signature.
- **Inspiration:** Genshin Impact — Vaporize/Melt/Overload/Superconduct each have a recognizable audio signature.
- **Value:** Elemental reactions are the reward for swapping heroes mid-fight (the design's signature mechanic), and all 4 reactions sound identical today. Distinct stings let a player hear "Freeze landed!" and know the enemy is stunned. Highest value-per-line in the set.
- **Sketch:** `audio.py`: add 4 synth functions — `synth_r_steam` (filtered noise hiss + high chime), `synth_r_spread` (warm low woosh + crackle), `synth_r_freeze` (crystalline sine ping + glassy harmonic), `synth_r_rupture` (low dissonant 2-note + noise). Cache `react_steam/spread/freeze/rupture` in the `SOUNDS` dict (line 322). `world_scene.py` where the reaction fires (line ~1559, currently `audio.play('explosion', 0.4)`) replace with `audio.play('react_'+rxn_name.lower(), 0.45)`. The `REACTIONS` dict (data.py:46) already names them; map name→sound key with a small dict.
- **Files:** audio.py, world_scene.py
- **Risk:** 4 new synth functions add ~0.1s to init (negligible). Keep reaction volume ~0.45 (slightly above the 0.2-0.4 hit/crit range) but short. The `REACTION_WINDOW=3s` + per-enemy `_last_element_hit` gate (world_scene.py:1562) already limits frequency.

### 6. Breakable Props (Pots/Crates/Barrels with Loot)  *(world, S)*
Scatter 4-8 breakable props per map (pots in plains, crates in castle, barrels in cave) that shatter on any attack or dash, dropping small gold/potions/shards. The single highest "world feels alive" payoff per line of code.
- **Inspiration:** Genshin breakable crates/pots; Zelda pots (rupees); Hades urns.
- **Value:** Every action game with breakables proves players will go out of their way to smash pots. Pairs naturally with the existing combo/particle system (a shatter is a free particle burst) and gives low-intensity moments a reward.
- **Sketch:** `world_data.py` `gen_map` (line 264): after chest placement (line ~396), add `breakables: [(x, y, kind, loot)]` — 4-8 props on free tiles via `_free_grid` (line 431), kind by biome (pot/crate/barrel), loot weighted to small gold (60%) / hp_potion (20%) / 1 shard (20%). Gate with `_free_grid` + the center-distance check already used for chests (line ~411) so they don't block the corridor/edge-portal gaps. Include in the return dict (line ~414). `world_scene.py`: in `_do_attack` (line ~1205) and the dash path, after the enemy hit scan, also scan `self.breakables` for overlap with the attack arc / dash endpoint; on hit, mark broken, spawn the loot (reuse `self.drops` / `_open_chest`-style reward) + a shatter particle burst. Draw breakables in the depth-sorted drawables list (line ~2189). `generate_assets.py`: add `draw_pot`/`draw_crate`/`draw_barrel` (simple procedural shapes, ~10 lines each).
- **Files:** world_data.py, world_scene.py, generate_assets.py
- **Risk:** Breakables must not spawn on edge-portal gaps or the central corridor (gate with `_free_grid` + center-distance check). The attack-arc scan must be cheap — small list, only when a swing actually happens, not per-frame.

### 7. Variable Hit-Stop by Attack Weight  *(combat, S)*
Hit-stop is flat today (0.05 normal, 0.11 crit, 0.22 ult) regardless of which skill landed. Scale hit-stop with the skill's cost tier so a heavy inferno (cost 5) or a meteor ult freezes the screen noticeably longer than a basic attack, giving each hit a weight that matches its animation.
- **Inspiration:** Dead Cells (hit-stop scales with weapon impact); Street Fighter (per-move hitstop); Hades (heavy freeze frames).
- **Value:** Makes heavy skills feel meaty and light skills feel snappy — the screen freeze is the single biggest "impact" cue in action combat, and right now a basic attack and an inferno feel the same on impact.
- **Sketch:** `world_scene.py`: in `_do_skill` (line ~1287) and `_do_ultimate` (line ~1440), replace the flat `self.hit_stop = max(self.hit_stop, 0.22)` (line ~1457) with a value derived from the skill's cost: `hs = 0.06 + skill.get('cost', 2) * 0.03` (cost-5 = 0.21s, cost-9 ult = 0.33s, capped at 0.4). In `_on_enemy_hit` (line ~1571) keep the crit hit-stop at 0.11 but add a small extra for high-combo hits (tier≥2 → +0.03). `data.py`: the `cost` field already exists on every skill; no data change. Cap at 0.4s and **respect `_reduce_motion`** (line ~1793) by scaling hit-stop down too, not just shake.
- **Files:** world_scene.py
- **Risk:** Too much hit-stop on a spammed heavy skill feels laggy — cap at 0.4s and scale down under `reduce_motion`. Must not let hit-stop stack from multi-hit AoE (use `max`, which the code already does).

### 8. Colorblind-Friendly Element Palette Toggle  *(ui, S)*
Add a colorblind-friendly palette toggle that swaps `ELEMENT_COLORS` (data.py:63) for a deuteranopia/protanopia-safe set, so colorblind players (and everyone on bright biomes) can tell fire from HP-red and wind from HP-green at a glance.
- **Inspiration:** League of Legends colorblind mode; Genshin element icons identifiable without color.
- **Value:** Colorblind players can distinguish the 5 elements from the HP/damage colors at a glance. Pure accessibility with no draw-call risk.
- **Sketch:** `data.py`: add `COLORBLIND_PALETTES` dict with deuteranopia-safe RGB triples for the 5 elements (distinct in hue/brightness, not just red/green). `main.py`: the `element_color` helper already exists (line ~303) — modify it to check the `colorblind_mode` setting and return the CB palette triple when on. Add a "Colorblind Mode" Toggle in the Access tab (line ~1569, next to `high_contrast` at line ~1581) and a `colorblind_mode` key in `player.py` settings. **Keep `REACTIONS` (data.py:46) on their fixed `rcol` tuples** so the palette swap doesn't break reaction colors. The setting persists via the existing settings save/load.
- **Files:** data.py, main.py, player.py
- **Risk:** Low — a palette swap is one function branch. Must not break reaction colors (REACTIONS uses its own `rcol` tuples). The CB palette must keep the 5 elements distinct from each other AND from HP-red/crit-yellow/heal-green.

---

## P1 — identity, world, meta (M-cost)

### 9. Constellation Perks (C1-C6) Replacing Flat Ascension  *(characters, M)*
Replace the boring flat 1.0→1.5 stat multiplier on ascension (`ASCENSION_BONUS` data.py:765) with per-hero gameplay-changing perks at each star — C1 shaves a skill cooldown, C3 adds a secondary effect to the ultimate, C6 transforms the kit — so pulling a dupe is exciting instead of just "+8% stats". Role-templated for stars 1-3 (7 roles × 3 = 21 perks) with a few hero-specific capstones.
- **Inspiration:** Genshin C0-C6 constellations (each node materially changes how a character plays); Honkai Star Rail Eidolons E0-E6.
- **Value:** The entire ascension system is a boring flat multiplier — players feel nothing when they pull a dupe. Constellation perks make every duplicate a strategic decision: "do I want C3 Kael's burn-on-ult, or save shards?" The single biggest lever for making the 25 heroes feel worth investing in.
- **Sketch:** `data.py`: add `CONSTELLATION_PERKS` keyed by role → list of 6 perk dicts (`id, name, desc, effect kind+val`); a few hero-specific overrides keyed by hero id. Perk kinds: `cd_reduction` (target a skill slot, val=0.2), `ult_extra` (add burn/freeze/heal/shock to the ult), `passive_boost`, `energy_cost_cut`, `crit_dmg_up`. **Keep the flat `ASCENSION_BONUS`** so old saves don't regress — perks layer on top. `entities.py` `Hero.__init__` (line ~267): after computing crit/energy, read `rec['ascension']` and apply perk effects to `skill_cost_mult`, a new `ult_extra` dict, and `crit_dmg_bonus`; `_recompute` must reapply them. `world_scene.py` `_do_ultimate` (line ~1440): after the ult damage, apply `ult_extra` (burn DoT via the wired tick_effects, self-heal, party buff). `_do_skill` (line ~1287): check per-skill `cd_reduction` perks. `main.py` `HeroDetailScene.draw` (line ~667): show the 6 constellation nodes with unlocked/locked state + the NEXT perk description under the Ascend button.
- **Files:** data.py, entities.py, world_scene.py, main.py
- **Risk:** Balancing 7 roles × 6 perks (+ overrides) is real design work; role-templated early stars mitigate this. Perks that modify cooldowns/energy must be read in the Q/W/E/R handlers, not just `Hero.__init__`. Coordinate with `EVO_TREE` (data.py:220) so ascension perks and evolve-tree passives don't duplicate the same passive id.

### 10. Per-Hero Signature Passives (Layered, Not Replacing)  *(characters, M)*
Layer 25 unique per-hero passives on top of the 9 shared passives — Ember revives once at low HP, Raven gains stacking ATK per kill, Tide gains a shield when hit — flavored to each hero's identity, so pulling Ember vs Cinder (both fire destruction, both `p_lifesteal` today) feels like different heroes.
- **Inspiration:** League of Legends champion passives (Garen's Perseverance, Yasuo's Way of the Wanderer); Honkai techniques.
- **Value:** Today pulling Ember vs Cinder (both fire destruction, both `p_lifesteal`) feels like the same hero with different art. Unique passives make each of the 25 heroes play differently. The passive is the one always-on thing that colors every second of combat.
- **Sketch:** `data.py`: add ~6-8 new passive kinds to `PASSIVES_DB` (line 152) — `revive_once`, `stacking_atk` (+ATK per kill, decays out of combat), `shield_on_hit`, `low_hp_frenzy` (+ATK +SPD below 30%), `cleave` (basic attacks hit nearby enemies). Add a `HERO_SIGNATURE` dict mapping each of the 25 heroes to a unique signature passive id (distinct from `HERO_PASSIVES` at line 176, which stays as the shared base). `world_entities.py` `WorldCharacter.take_damage` (line ~370): handle `revive_once` (return a 'revive' sentinel), `shield_on_hit`. `WorldCharacter.update` (line ~448): handle `low_hp_frenzy` (modify `effective_atk` + `move_speed` when HP < 30%). `world_scene.py` `_on_enemy_death` (line ~1583): apply `stacking_atk`. `_do_attack` (line ~1205): apply `cleave` (hit enemies within 60px of the primary target). **Gate each handler on a dict lookup (`passive_kind -> handler`), NOT 16 if/elif**, to avoid hot-loop branch risk. Reset `revive_once` in `_build_party` (line ~936) per combat to avoid an init-order trap.
- **Files:** data.py, world_entities.py, world_scene.py
- **Risk:** New branches in the hot combat loop — gate on a dict lookup, keep each handler 2-3 lines. `revive_once` needs a per-combat reset (clear on `_build_party`). Avoid the `stationary_def` passive (dead under the always-moving LoL scheme). Layer on top of the evolve tree's passive rewards (Bloodlust grants `p_lifesteal` at data.py:220), don't replace.

### 11. Per-Hero Ultimate Variants (Ship Safe Effects Now, Defer Burn/Freeze)  *(characters, M)*
Give each of the 25 heroes a unique ultimate name + one secondary effect on top of the shared base, so Kael's "Meteor" becomes "Crimson Meteor" (self-heal) and Ember's becomes "Phoenix Cataclysm" (party shield) — same power, different flavor and tactical use. Ship the one-liner effects (self_heal/shield/knockback) now; **defer burn/freeze until the DoT engine (#2) is wired**.
- **Inspiration:** Genshin bursts (Diluc's Dawn vs Hu Tao's Spirit Soother are both fire but play differently).
- **Value:** Today 25 heroes share just 7 ultimates — Kael, Ember, and Cinder all cast the identical "meteor". The ultimate is the hero's signature move and it's shared. Per-hero variants fix this with a unique name (shown in the HUD + codex) and one tactical secondary effect.
- **Sketch:** `data.py`: add `ULTIMATE_VARIANTS` dict `hero_id -> {name, extra_effect, potency, desc}`. Ship only the one-liner effects now: `self_heal` (heal the caster X% of damage dealt), `party_shield`, `knockback`, `energy_refund`, `atk_buff_self`. Defer `burn`/`freeze` until the DoT engine lands. `world_scene.py` `_do_ultimate` (line ~1440): after the main damage loop, read `ULTIMATE_VARIANTS.get(wc.hero.id)` and apply the extra — `self_heal` calls `wc.heal(int(total_dmg * potency))`, `party_shield` shields each party member, `knockback` pushes enemies. `main.py` `HeroDetailScene` (line ~697): show the variant name + desc instead of the generic `SKILLS_DB[ultimate]['name']`.
- **Files:** data.py, world_scene.py, main.py
- **Risk:** 25 variant entries is data work but only ~5 effect types to implement. Balance: the secondary effect should be modest so base power stays comparable. burn/freeze variants depend on the DoT engine first — without it, only self_heal/shield/knockback are coherent (which is why those ship first).

### 12. Elemental Resonance (Party Composition Buff + HUD Badge)  *(meta, S)*
Add Genshin-style party elemental resonance: if your 4-hero party has 2+ of the same element, the whole party gains a themed buff (2 fire = +15% ATK, 2 water = +20% healing, 2 wind = +10% move speed, 2 light = +15% energy regen, 2 dark = +10% crit damage), shown as a visible HUD badge so the player feels the comp bonus.
- **Inspiration:** Genshin elemental resonance (Fervent Flames = +25% ATK, Soothing Water = +30% healing).
- **Value:** Currently team-building is purely about individual hero strength — there's no reward for composition. Resonance makes the player think: "2 fire for raw damage, 2 water for sustain, or a rainbow team for reaction variety?" Immediately readable (a HUD badge) and ties the roster screen to combat outcomes.
- **Sketch:** `data.py`: add `ELEMENTAL_RESONANCE` dict: fire→`atk_pct` 0.15, water→`heal_amp` 0.20, wind→`move_speed` 0.10, light→`energy_regen` 0.15, dark→`crit_dmg` 0.10 (each with a name). `world_scene.py` `_build_party` (line ~936): after building the party, count elements among the 4 slots and compute `self._resonances`; recompute on `_switch` (line ~1753). Apply `atk_pct` via `effective_atk` (world_entities.py ~423), `move_speed` via `move_speed` (~435), `heal_amp` in the heal branch (~1365), `energy_regen` in `add_energy` (~445), `crit_dmg` in the crit_mul (~1220). `_draw_hud` (line ~2564): add a resonance badge row under the party icons. `main.py` `RosterScene` (line ~413): show the active resonance next to Team Power.
- **Files:** data.py, world_scene.py, world_entities.py, main.py
- **Risk:** Mono-element teams could crowd out rainbow reaction teams — cap resonance at 2-of-a-kind (no 3x/4x scaling), keep buffs modest (10-20%) but visible. `heal_amp`/`energy_regen` must flow through the existing paths without double-applying with `p_heal_amp`/`p_energy` — guard with a check. Must not undercut the weakness-break system that rewards mid-fight element swapping.

### 13. Combo Climax: Finishers + Musicality (Combo 5/10 Empowered + Milestone Stingers)  *(combat, M)*
The combo counter is a flat +4%/hit ramp to +40% with no payoff for reaching the cap. At combo milestones (5 and 10), grant the next skill or ultimate a bonus effect (wider AoE, an extra projectile, a free status), and add ascending musical stingers at 5/10 + a celebratory chord at max combo (`COMBO_MAX=10`), so building a streak has a tangible, audible climax.
- **Inspiration:** Hades (boon synergy milestones); Dead Cells (combo branches); Devil May Cry (combo style ratings each trigger a distinct musical sting).
- **Value:** Turns the combo counter from a passive number into a goal the player plays toward — "land 5 hits to get a free spread on my next skill" makes basic-attack weaving matter. The musical stingers make hitting a 5- or 10-combo feel like an achievement.
- **Sketch:** `world_scene.py`: add `self._combo_milestone` flags next to `_combo_count` (line ~894). In `_on_enemy_hit` (line ~1505) after incrementing `_combo_count`, check milestones: count hits 5 → `_skill_empowered = True`; at 10 → `_ult_empowered = True`. In `_do_skill`/`_do_ultimate`, if the empowered flag is set, apply a bonus: AoE skills widen the radius (200→260) + a second ring; single-target adds a second piercing projectile; ults add a free debuff application to all enemies hit. **Consume the flag on use; clear on swap** (line ~1753) so it can't be banked. For musicality: in the combo pitch-tier block (line ~1574, `if tier > self._combo_pitch_tier`) also `audio.play('combo_'+str(tier), 0.3)`. When `_combo_count` reaches `COMBO_MAX` play a one-shot max-combo chord + a brief hit-stop; gate with a `_combo_max_celebrated` flag reset on window expiry (line ~2026). `audio.py`: add `synth_combo_sting(tier)` — tier 1 = 2-note ascending, tier 2 = 4-note ascending arpeggio (reuse `synth_revive`'s arpeggio pattern at line ~80). Cache `combo_1`, `combo_2`. `data.py`: add `COMBO_MILESTONE_SKILL=5`, `COMBO_MILESTONE_ULT=10`. The HUD (line ~2669) already shows the combo; add a small "EMPOWERED" tag when a flag is active.
- **Files:** world_scene.py, audio.py, data.py
- **Risk:** An empowered ult could trivialize a boss if it lands at combo 10 — cap the bonus (empowered ult adds a status, not raw damage) and clear the flag on swap so it can't be banked. Milestone stingers fire only on a tier *increase*, not every hit; gate the max-combo celebration with a reset-on-expiry flag.

### 14. Dynamic Weather with Gameplay Effects (Rain/Storm/Fog as a Live Overlay)  *(world, M)*
Each map gets a deterministic weather state (clear/rain/fog/storm) that drifts with the day/night cycle and changes combat: rain applies a WET status (boosts water damage, weakens fire, extends the Freeze reaction window), storms spawn dodgeable telegraphed lightning strikes, fog cuts enemy aggro range. Weather stays a live overlay + combat modifier (never baked into `gen_map`) so the `MapRenderer` cache stays intact.
- **Inspiration:** Genshin's rain/wet elemental system; Terraria's blood-moon events; Stardew's weather-gated days.
- **Value:** The world stops feeling like 50 static arenas — weather makes the same map play differently each visit and ties the atmosphere into the elemental reaction system. Rain making Freeze trivial but fire weak is a real strategic beat.
- **Sketch:** `world_data.py`: add `WEATHER_BY_BIOME` and `weather_for(c, r, world_time)` that quantizes the cycle to 4 buckets (dawn/day/dusk/night) and picks a state deterministically from `cell_seed` (line 59, storm weight rises at night). `world_scene.py`: in `_load_map` (line ~987) store `self._weather = WD.weather_for(self.c, self.r, self._world_time)` — **NOT in gen_map**, so the `MapRenderer` cache (keyed on (c,r)) stays intact. In `_on_enemy_hit`/`_do_attack` apply a wet multiplier when rain (read a new `data.WET_EFFECT` = water ×1.2, fire ×0.8, `REACTION_WINDOW` ×1.5); gate the wet multiplier so it only modifies the reaction window, not stack with the Freeze stun itself. In the per-frame update (line ~1923), when storm, every ~6s spawn a telegraphed strike at a random near-hero tile (reuse the `boss_slam` telegraph + a damage check). Draw a cached rain overlay (diagonal alpha lines) and a fog darkening in `_draw_atmosphere` (line ~2336, reuse `_light_cache` at line ~873). `audio.py`: add `synth_rain` (filtered noise loop) + `synth_thunder` (low noise burst) and switch the ambience bed via `set_ambience` (line ~388) when weather != clear. `data.py`: `WET_EFFECT` constant.
- **Files:** world_data.py, world_scene.py, audio.py, data.py
- **Risk:** `gen_map` is cached by (c,r) with no `world_time`, so weather MUST stay a live overlay + combat modifier (like the atmosphere), never baked into `gen_map`. The wet-status must not double-apply with Freeze's stun window — gate the wet multiplier to the reaction window only. Storm strikes must be telegraphed (not instant) or they feel unfair. The weather particle layer must stay small (~100) and be skipped under `reduce_motion`, distinct from the 260 combat particle cap.

### 15. Hidden Rift Domains (Secret Mini-Dungeons)  *(world, M)*
~15% of non-boss maps (deterministic by `cell_seed`) hide a glowing rift prop; walking into it seals the map exits and spawns a wave of 3-5 scaled enemies. Clear the wave to unlock a guaranteed SR/SSR chest + a lore fragment. A real exploration payoff beyond the flat 0-2 chests.
- **Inspiration:** Genshin's Domains; Zelda's hidden Shrines; Hades' challenge rooms.
- **Value:** Exploration currently yields only walking and the occasional chest; a secret combat room with a guaranteed good reward makes "see the whole map" worth it and gives the procedural grid genuine surprises. The seal-on-enter adds a risk/reward decision.
- **Sketch:** `world_data.py` `gen_map` (line 264): with a deterministic 15% chance (rng from `cell_seed` at line 59), place a rift at a free tile (reuse `_free_grid` at line 431); return an additional `secret: (x, y, wave_level, wave_size)` or None in the dict (line ~414). `world_scene.py`: in the walk-over check (line ~1843, next to the chest pickup), detect rift proximity; on enter, set `self._rift_active = True`, spawn `wave_size` `WorldEnemies` from the row pool (`ROW_ENEMIES` at world_data.py:47) at level + `wave_level`, and suppress `_transition` while active (gate at line ~1832). On wave clear, spawn a guaranteed chest (reuse `_open_chest` reward logic with a forced SR/SSR pool) + a lore float. The party-wipe respawn (`teleport_to(0,0)`) already breaks the seal. `player.py`: persist `ow_secrets_done` (set of cell ids) so a cleared rift stays cleared; add to save (line ~378) and load (line ~407) with `setdefault`. `generate_assets.py`: extend the existing `rift` deco kind into a pulsing portal. `data.py`: a `LORE_FRAGMENTS` list for the lore drop text. **Cap `wave_size` by row** so early rows don't ambush a fresh player with 5 enemies.
- **Files:** world_data.py, world_scene.py, player.py, generate_assets.py, data.py
- **Risk:** Sealing exits while a wave is active could trap a low-HP party into a wipe — the existing party-wipe respawn (`teleport_to(0,0)`) must break the seal, and `wave_size` must be capped by row. Must not block the edge-portal gaps (gate placement with `_free_grid` + center-distance check).

### 16. Torchlight — Hero-Carried Dynamic Light at Night + Boss Light Pools  *(graphics, M)*
At night, a radial light pool follows the active hero and boss arenas glow as lit pools, while a stronger vignette darkens the periphery — the world is lit by the hero. The single highest-delight atmosphere win, reusing the existing quantized night levels as the cache key so the atmosphere cache doesn't thrash.
- **Inspiration:** Hollow Knight (lit areas in darkness); Hyper Light Drifter (vignette + light pools); Dark Souls (lantern).
- **Value:** Night exploration feels tense and atmospheric — you carry your light into the dark, and bosses read as radiant threats. Makes the day/night cycle visually meaningful beyond a flat blue tint.
- **Sketch:** `world_scene.py` `_draw_atmosphere` (line ~2336): after the night overlay blit (line ~2361), add a hero-centered light pool — reuse the cached radial light sprite pattern (`_light_cache` at line ~873, the fog sprite at line ~2439) but larger and warm-tinted, blitted with `BLEND_RGBA_ADD` at the hero's screen pos, intensity scaled by the night level from `_night_overlay` (line ~2486). Strengthen the vignette in `_biome_atmos` (line ~2413) at night (multiply the vignette alpha by a night factor). `world_entities.py` `WorldEnemy.draw` boss aura (line ~1099): at night, expand the aura radius and intensity so boss arenas read as lit pools. **Reuse the existing quantized night levels (line ~2500) as the cache key** so the atmosphere cache doesn't thrash.
- **Files:** world_scene.py, world_entities.py
- **Risk:** The light pool must track the hero screen pos correctly under camera shake, and could look flat if the gradient isn't tuned. Must not break the cached-overlay model — reuse the existing quantized night levels as the cache key.

### 17. Hero Elemental Leitmotifs on Party Swap  *(audio, M)*
Play a short (0.4-0.7s) musical sting themed to the incoming hero's element on every Genshin-style party swap (1/2/3/4), replacing the generic "skill" whoosh with an element-flavored motif so each swap-in feels like the hero's "entrance". Only 5 motifs for 25 heroes (the element is the identity the reaction system cares about).
- **Inspiration:** Genshin — each character has a short musical signature on swap-in.
- **Value:** The 4-hero party swap is the core combat verb (it sets up elemental reactions), and right now it sounds identical to a skill whoosh. A per-element sting makes the active hero feel like they "arrived" and gives each of the 5 elements an audible identity.
- **Sketch:** `audio.py`: add `synth_leitmotif(element)` — 5 short stings: fire=quick brass-like rising 2-note, water=cool descending bell, wind=open airy chirp, light=bright major 3rd pluck, dark=low dissonant 2-note. Cache `leit_<element>` in `SOUNDS` (line 322). `world_scene.py`: in `_switch` (line ~1753, currently `audio.play('skill', 0.3)`) replace with `audio.play('leit_'+new.element, 0.4)` and keep a quieter "skill" whoosh under it at 0.15. Add a swap-spam guard: track `self._last_swap_sound_t` and skip if <0.25s ago.
- **Files:** audio.py, world_scene.py
- **Risk:** Only 5 element motifs for 25 heroes — repetition across heroes of the same element (acceptable; the element is the identity the reaction system cares about). Rapid swap spam piling stings — mitigated by the 0.25s guard.

### 18. Gacha Roll Tension Crescendo + Rarity-Scaled Fanfare  *(audio, M)*
During the 1.6s gacha roll animation, play a rising tension drone on a dedicated channel that crescendos and resolves into a rarity-scaled reveal fanfare — SSR gets a full ascending arpeggio + pad, SR a simpler chord, R a soft chime — making the reveal moment dramatic instead of a flat shimmer into a sting.
- **Inspiration:** Honkai: Star Rail / Genshin gacha — the pull builds musical tension during the animation that releases into a rarity-scaled fanfare.
- **Value:** The gacha is the meta heart of the game, and right now the 1.6s roll is a static shimmer with a reveal sting tacked on the end. A crescendo that builds during the roll and resolves into a rarity-scaled fanfare makes an SSR pull feel like a moment. The single most emotionally under-served moment in the current audio.
- **Sketch:** `audio.py`: add `synth_gacha_tension(dur=1.6)` — a rising drone (low sine sweeping up + growing noise) that crescendos to the reveal. Cache `gacha_tension`. Reserve a dedicated channel `Channel(4)` for the tension loop. Add `synth_gacha_fanfare(rarity)` — SSR=full 4-note ascending arpeggio + choir-like pad (stacked detuned sines), SR=2-note chord, R=soft single chime. Cache `gacha_fanfare_ssr/sr/r`. `main.py` `GachaScene`: where the roll starts (line ~822, `audio.play('gacha_roll', 0.5)`) also `audio.play('gacha_tension', 0.5)`; at the reveal (lines ~844-850) replace the reuse with `audio.play('gacha_fanfare_'+best.lower(), 0.8)`. **MUST stop the tension channel in the skip branch** (line ~877, Esc/right-click) or the drone leaks past the reveal.
- **Files:** audio.py, main.py
- **Risk:** The tension bed not stopping if the player skips the reveal — must stop `Channel(4)` in the skip branch. The 1.6s crescendo timing must match the `anim_t>1.6` gate (line ~837). Keep fanfare mixed under the reveal burst.

### 19. Aetheric Cycle (NG+ with World Reset + Level Scaling)  *(meta, M)*
After defeating the final boss (Demon King at cell 9,4), the player may "Ascend the World" — resetting world exploration (`ow_discovered`, `ow_bosses_cleared`, `ow_current`, `ow_chests_opened`) while keeping all heroes/equipment/inventory, with each cycle scaling enemy levels up so the grind stays fresh. The upgrade-shop is deferred to keep this feasible as M.
- **Inspiration:** Dead Cells (Boss Stem Cells / NG+); Hades (Mirror of Memory); Genshin (Spiral Abyss reset cycles).
- **Value:** The game ends structurally once the 6 boss cells are cleared — there is no reason to keep playing. Aetheric Cycle gives the endgame a purpose: every cycle is a fresh, harder run, so even a wipe feels like forward progress. The single highest-impact addition for long-term retention.
- **Sketch:** `player.py`: add `self.ng_cycle=0`; add `reset_world_for_ng()` that clears `ow_discovered` (line 60)/`ow_bosses_cleared` (line 69)/`ow_current` (line 58)/`ow_pos` (line 59)/`ow_chests_opened` (line 66) and increments `ng_cycle`; **bump save version to 6 + migration** (the `load()` block at line ~407 already `setdefault`s each `ow_*` field). `world_scene.py`: in the boss-defeat handler (line ~1630, where `first_clear` is computed), if the cell is the final boss (`WD.is_boss_cell` and boss id `demonking` at world_data.py:52), set a flag + show a "World Ascended!" banner. `world_data.py`: `cell_level` (line 68) gains `+ ng_cycle*NG_PLUS_LEVEL_BONUS` (pass cycle into the world scene's enemy spawn at line ~1043, since `cell_level` is static). `data.py`: add `NG_PLUS_LEVEL_BONUS=8`. `main.py` `TitleScene` (line ~320): show "Cycle N" and an "Ascend World" button when the final boss is in `ow_bosses_cleared`.
- **Files:** player.py, world_scene.py, world_data.py, data.py, main.py
- **Risk:** Balancing the per-cycle level scaling so cycle 2+ doesn't wall the player; save migration for existing players with version 5 saves (straightforward — defaults via `d.get`). Final-boss detection must be robust — check `is_boss_cell` (world_data.py:73) + the `demonking` at (9,4) to not misfire on the other 5 row-end bosses.

### 20. Quest Tracker Panel + Compass Arrow to Nearest Objective  *(ui, M)*
Add a compact in-world quest tracker (top-right under the resource counters) showing the top daily quest's name + progress bar, and a screen-edge compass arrow pointing toward the nearest un-cleared boss cell or undiscovered map edge, so the player always knows where to go next in the 50-map world.
- **Inspiration:** Genshin's quest tracker + navigation arrow; Skyrim's compass with quest markers at the screen edge.
- **Value:** The open world has 50 maps and 5 bosses but no in-world guidance — players wander aimlessly. A quest tracker + compass turns exploration into directed adventure, surfacing daily quest progress and pointing toward the next meaningful destination without opening the Records screen.
- **Sketch:** `world_scene.py` `_draw_hud` (line ~2564, after the resource counters): add a small quest tracker panel (right-aligned at x>900, y~110, to avoid the boss HP bar at top-center) showing the first unclaimed `DAILY_QUESTS` entry (data.py ~942) with name + `draw_bar` progress + "N/goal". For the compass: compute the nearest un-cleared boss cell from `p.ow_bosses_cleared` (player.py:69) and the nearest undiscovered neighbor of the current cell via a new `_nearest_objective()` method returning `(world_x, world_y, label, color)` — O(50 cells) once per frame, negligible. Draw a directional arrow at the screen edge (top/bottom/left/right) pointing toward that target's world-map direction (WD cell center = `(c*MAP_W + MAP_W/2, r*MAP_H + MAP_H/2)`), using the camera offset. Reuse the `_draw_chevron` helper (line ~2524) for the arrow shape, colored by objective type (gold for boss, cyan for unexplored). Handle the on-screen case (show a marker at the target, not an edge arrow) and the all-bosses-cleared case (hide the boss arrow, fall back to unexplored).
- **Files:** world_scene.py
- **Risk:** The compass must handle the case where the target is on-screen (show a marker, not an edge arrow) and where all bosses are cleared (hide the boss arrow, fall back to unexplored). Quest tracker must not overlap the boss HP bar at top-center — keep it right-aligned at x>900. Performance: the nearest-objective scan is O(50 cells) per frame, negligible.

---

## Cross-cutting constraints (every enhancement)

- **Cached-map model:** weather/elite-ness/rift-ness computed at `_load_map` or as a live overlay, never baked into `gen_map` (the `MapRenderer` cache is keyed on `(c,r)` only).
- **LoL control scheme:** RMB click-to-move, J attack, Q/W/E skills, R/Space ult, 1-4 swap — unchanged.
- **Pure-procedural:** no external art/audio; all new art via `generate_assets.py`, all new audio via `audio.py` numpy synthesis.
- **Init-order traps:** any field used in `_load_map` (e.g. `_weather`, `_rift_active`, `_world_time`) must be declared in `__init__` BEFORE `_load_map` is called.
- **`reduce_motion` / `high_contrast`:** every visual effect (phase flash, weather particles, torchlight, hit-stop) must respect the existing accessibility settings.
- **Save migration:** `Aetheric Cycle` bumps save version to 6; all other P0/P1 use existing fields or static data (no migration). Old saves load without error.
- **No new external dependencies.**

## Verification plan (headless, per phase + final)

- `xvfb-run -a python3 verify_assets.py` — render every sprite (incl. new pot/crate/barrel/rift), report sizes.
- `SDL_VIDEODRIVER=dummy python3 main.py` — boot + exercise the world scene headless after each batch.
- The 20-test acceptance suite (`/tmp/verify_complete.py`) + the 8-feature suite (`/tmp/verify_features.py`) + a 1200-frame stress test + the per-scene benchmark (`/tmp/bench_aetheria.py`) — all PASS after the full set, world ≥ ~60fps.
- Manual: `python3 generate_assets.py && python3 main.py` → Enter World → explore, break props, weather, rift, fight (DoT/break/combo climax), swap (leitmotif/resonance), pull (tension crescendo), ascend a hero (constellations), clear the final boss → Aetheric Cycle.

## Implementation shape (Phase 2, after this spec is approved)

Each enhancement → **one specialist agent with worktree isolation** (the pattern that shipped the 134 audit fixes: parallel edits, no conflict, each agent owns its files, runs a headless smoke test, then merge + full verify + commit). Grouped into batches by shared-file dependency to avoid worktree conflicts:

- **Batch A — data-heavy (no hot-loop risk):** #1 lore, #8 colorblind palette, #12 resonance, #9 constellations, #11 ult variants, #19 Aetheric Cycle, #15 rifts.
- **Batch B — combat wiring (world_scene/world_entities hot paths):** #2 DoT, #3 toughness-break, #4 boss HUD, #7 variable hit-stop, #13 combo climax, #10 signature passives.
- **Batch C — world/atmosphere:** #6 breakables, #14 weather, #16 torchlight, #20 quest compass.
- **Batch D — audio:** #5 reaction stings, #17 leitmotifs, #18 gacha crescendo.

Each batch runs as a workflow; within a batch, each enhancement is one agent in its own worktree. Merge after each batch + headless verify; commit per batch.

## Out of scope (YAGNI — dropped by the critics)

- Full-screen bloom (perf liability on a 1280×720 cached-overlay scene).
- Live water reflections (L cost, 2 biomes only).
- Town hub (L, redundant with the existing shop/roster scenes).
- Adaptive music infrastructure (L, mixer contention; one-shot boss/leitmotif stings ship instead).
- Artifact relics (breaks the 3-slot equipment logic).
- Per-hero voice stings (20 stings, robotic-sound risk, overlaps the swap moment; 5 element leitmotifs ship instead).
- Onboarding coach marks (controls hint already shown).
- The upgrade-shop half of Aetheric Cycle (deferred; reset + level scaling ships as M).
