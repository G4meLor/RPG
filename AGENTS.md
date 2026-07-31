# AGENTS.md — Aetheria (Gacha → Open World 2D)

> File này ghi lại **phạm vi công việc** và **các ràng buộc** cho mọi agent
> làm việc trong repo này. Đọc kỹ trước khi bắt đầu.

## 1. Mục tiêu dự án

Chuyển đổi game từ **turn-based** sang **open-world 2D** (giống Genshin Impact).
Lớp turn-based cũ **đã bị xóa** (`combat.py` đã delete). Trọng tâm là **World
Scene** (`world_scene.py`, `world_entities.py`, `world_data.py`).

### Các yếu tố đã hoàn thành (theo yêu cầu người dùng)

1. **Performance** — mượt, không giật, cache surface + font, ~150-180fps
   headless. Có settings: FPS cap, particle quality, reduce motion.
2. **Độ hoàn thiện** — 25 nhân vật, 50 map, hệ thống skill LoL-style
   (Q/W/E + R ultimate + passive), cây tiến hóa phân nhánh, quái + boss.
3. **Độ đẹp mắt** — sprite chibi + portrait + cape/aura, VFX (rings/sparks/
   shockwaves), atmosphere (fog/vignette/biome light), HUD đẹp.
4. **Chuyển động mượt mà** — camera critically-damped spring, accel/friction,
   walk/squash animation, slide-wipe khi chuyển map.
5. **Hệ thống items / level / evolve** — XP, level up, ascension (limit break),
   equipment, consumables, soul shards → evolve tier + **cây tiến hóa**.
6. **Party 4 nhân vật + đổi bằng 1/2/3/4** — Genshin-style, HP/energy persist.
7. **50 maps, camera focus, chuyển map ở biên + teleport (M)**.
8. **Settings menu đầy đủ** — Audio/Display/Gameplay/Accessibility/Data,
   toggle + slider widgets, persist + apply runtime (volume, fullscreen, FPS).

Người dùng **không tham gia loop** — làm bất ngờ với thành phẩm cuối.

## 2. RÀNG BUỘC QUAN TRỌNG — KHÔNG ĐỌC ẢNH

> ⚠️ **Trong repo này, KHÔNG được cố đọc file ảnh (PNG/JPG) bằng tool Read.**

Lý do: việc đọc ảnh (PNG) đã làm **phiên làm việc bị lỗi/crash**. Đây là một
ràng buộc cứng cho toàn bộ agent làm việc trong repo:

- **KHÔNG** dùng `Read` tool với các file `*.png`, `*.jpg`, `*.jpeg`, `*.gif`,
  `*.bmp`, `*.webp` (đặc biệt trong `assets/`).
- Nếu cần kiểm tra nội dung/nội dung sinh ra của ảnh, hãy:
  - Đọc **code sinh ảnh** (`generate_assets.py`) thay vì file PNG.
  - Chạy game ở chế độ **headless** (`SDL_VIDEODRIVER=dummy` hoặc `xvfb-run`)
    để smoke-test logic mà không cần xem ảnh.
  - Kiểm tra **kích thước/số lượng file** bằng `ls`/`stat`, không đọc nội dung.
- Có thể **ghi/ghi đè** file PNG bằng cách chạy `generate_assets.py` (với
  `xvfb-run`), nhưng tuyệt đối không đọc lại chúng.

## 3. Kiến trúc hiện tại

Codebase là package `src/` với kiến trúc **ECS-lite** (entity = component data bag, system = processor). `main.py` ở root là entry mỏng. Hybrid: 9 systems giữ logic (port verbatim từ god-class cũ), `WorldCharacter`/`WorldEnemy` còn làm data carrier + delegate `update` mỏng sang systems.

| Module | Vai trò |
|------|---------|
| `main.py` | Entry mỏng (bootstrap `src.core.main`). |
| `src/core/` | `game.py` (Game loop + scene manager), `scene.py` (base Scene), `world.py` (entity container + query), `main.py` (bootstrap). |
| `src/ui/` | `primitives.py` (font/text cache, Button, bars, dim overlay), `colors.py` (element/rarity colors), `widgets.py` (Toggle/Slider). |
| `src/data/` | **16 module per-concern** (tuning, elements, skills, heroes, enemies, gacha_data, equipment, story, resonance, passives, evolution, constellation, roles, shop, consumables, progression) — tách từ `data.py` cũ. |
| `src/entities/` | `components.py` (ECS dataclass: Transform/Health/Combat/AI/Render/Identity/Statuses/ChampionRef/Movement), `entity.py` (Entity), `combatant.py` (Hero/Enemy stat class), `hero.py`/`enemy.py` (entity factories `spawn_hero`/`spawn_enemy`), `world_actors.py` (WorldCharacter/WorldEnemy carrier + Particles/Projectile/FloatText/scratch/WEAPON_STYLE). |
| `src/systems/` | **9 systems**: `map_ctrl.py` (MapController), `physics.py` (PhysicsSystem + Camera), `ai.py` (AISystem), `combat.py` (CombatSystem), `render.py` (RenderSystem), `hud.py` (HudSystem), `drops.py` (DropSystem), `rift.py` (RiftSystem), `dialogue.py` (DialogueSystem). Mỗi system port verbatim từ god-class cũ. |
| `src/scenes/` | `world.py` (WorldScene — thin coordinator, delegate sang systems), `adventure.py` (AdventureScene), `menu/` (9 menu scene: title/roster/hero_detail/gacha_scene/shop/inventory/settings/stats/codex). |
| `src/world/` | `data.py` (map grid + biome + gen_map), `map_renderer.py` (MapRenderer). |
| `src/fx/` | `rift.py` (runtime VFX: draw_rift_portal). |
| `src/build/` | `champions.py` (170-champ bake), `build_champions.py` (one-shot roster builder). |
| `src/assets_gen/` | `generate.py` (build-only art generator). |
| `src/audio.py` / `src/player.py` / `src/gacha.py` | Synth audio, save state, summoning. |
| `tools/` | `verify_assets.py` (headless asset check), `verify_ecs.py` (ECS acceptance suite). |

**Verify (headless):**
- `SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets` — 170 bundles, archetype + per-skill distinctness, loaders, enemies/bosses.
- `SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs` — ECS acceptance suite (entity/component/world + factories + systems).
- `/tmp/verify_complete.py` — 21-test legacy acceptance suite (combat, edge transitions, teleport, save, gacha, boss).

## 4. Điều khiển (World Scene)

- `WASD` / mũi tên — di chuyển
- `Shift` / RMB — dash (i-frames)
- `J` / LMB — tấn công thường
- `Q` / `W` / `E` — skill 1 / skill 2 / skill 3 (LoL-style, có cooldown + energy)
- `U` / Space — ultimate (R slot, cần đầy energy)
- `1` `2` `3` `4` — đổi nhân vật đang điều khiển (Genshin-style)
- `R` — dùng HP potion cho nhân vật đang active
- `M` — mở world map / teleport
- `G` — mở Evolve screen (soul shards → evolve tier + cây tiến hóa)
- `Esc` — pause hub (roster/shop/inventory/gacha/quit)

Mỗi hero còn có **passive** (luôn bật) + **cây tiến hóa** (root + 2 nhánh,
mỗi nhánh 3 node). Node dùng soul shards để unlock, cho stat bonus / crit /
energy / passive.

## 5. Khi làm việc trong repo

- **Luôn** chạy smoke-test headless sau khi sửa code world:
  ```bash
  SDL_VIDEODRIVER=dummy python3 -m tools.verify_assets
  SDL_VIDEODRIVER=dummy python3 -m tools.verify_ecs
  # hoặc chạy vài frame:
  SDL_VIDEODRIVER=dummy python3 -c "import main; g=main.Game(); from src.scenes.world import WorldScene; sc=WorldScene(g); g.scene=sc; [sc.update(0.016,[]) or sc.draw(g.screen) for _ in range(120)]; print('ok')"
  ```
- Scene turn-based cũ **đã xóa** — không còn "Adventure (Stages)".
- Giữ backward-compat save (`src/player.py` đã có migration version 5 + merge
  settings defaults + `evo_nodes` setdefault).
- Code phải chạy được với `pygame 2.6.x` + `numpy` trên Python 3.11.
- **Settings** ảnh hưởng runtime: `sound`, `sfx_volume` (audio.set_enabled /
  set_master_volume), `fullscreen` (set_mode), `fps_cap` (clock.tick),
  `show_fps`, `screen_shake`, `reduce_motion`, `damage_numbers`, `show_hints`,
  `particle_quality`. Thêm option mới → thêm vào `Player.__init__` defaults
  VÀ vào merge block trong `Player.load`.
- **Kiến trúc ECS-lite hybrid**: logic sống trong `src/systems/` (9 systems,
  port verbatim). `WorldCharacter`/`WorldEnemy` (trong `src/entities/world_actors.py`)
  còn làm data carrier + delegate `update` mỏng sang systems. Khi sửa combat/AI/
  movement/render/HUD, sửa trong system tương ứng, KHÔNG sửa trong WorldScene
  (chỉ là coordinator). Entity components (`src/entities/components.py`) + factories
  (`spawn_hero`/`spawn_enemy`) sẵn sàng cho future full takeover.
