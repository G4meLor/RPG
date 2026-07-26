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

| File | Vai trò |
|------|---------|
| `main.py` | Game loop, scene manager (`Game`), các scene menu cũ (title, map, roster, gacha, shop, inventory, hero_detail, battle, tower, daily, codex, settings, stats). World scene được import lười qua `_get_world_scene_cls()`. |
| `world_data.py` | Lưới 10×5, biome, sinh map xác định theo seed, đồ thị teleport (neighbors), entry points. |
| `world_entities.py` | `Camera`, `Particles`, `Projectile`, `FloatText`, `WorldCharacter` (hero real-time), `WorldEnemy` (AI real-time). |
| `world_scene.py` | `WorldScene` (scene chính open-world), `MapRenderer` (bake map), `TeleportOverlay`, `PauseHub`, `EvolveOverlay` (cây tiến hóa). |
| `data.py` | Dữ liệu tĩnh: heroes, enemies, skills, equipment, consumables, gacha, achievements, tuning, **passives + evolution tree**. |
| `entities.py` | `Hero`/`Enemy` runtime, stats, leveling, ascension, equipment, effects, **passive + evo tree bonuses**, sprite loaders. |
| `combat.py` | **Đã xóa** (engine turn-based cũ đã remove). |
| `player.py` | Trạng thái người chơi + save/load (bao gồm `ow_*`, `evo_nodes`, settings đầy đủ). |
| `generate_assets.py` | Sinh toàn bộ PNG (characters, enemies, portraits, skills, items, ui, backgrounds). |
| `audio.py` | Synth âm thanh (numpy, không cần file). |

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
  SDL_VIDEODRIVER=dummy python3 -c "import world_scene, world_entities, world_data; print('ok')"
  # hoặc chạy vài frame:
  SDL_VIDEODRIVER=dummy python3 -m <smoke test>
  ```
- Scene turn-based cũ **đã xóa** — không còn "Adventure (Stages)".
- Giữ backward-compat save (`player.py` đã có migration version 5 + merge
  settings defaults + `evo_nodes` setdefault).
- Code phải chạy được với `pygame 2.6.x` + `numpy` trên Python 3.11.
- **Settings** ảnh hưởng runtime: `sound`, `sfx_volume` (audio.set_enabled /
  set_master_volume), `fullscreen` (set_mode), `fps_cap` (clock.tick),
  `show_fps`, `screen_shake`, `reduce_motion`, `damage_numbers`, `show_hints`,
  `particle_quality`. Thêm option mới → thêm vào `Player.__init__` defaults
  VÀ vào merge block trong `Player.load`.
