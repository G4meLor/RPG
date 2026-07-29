"""
Headless asset verification — NO image reading.

Verifies the LoL roster's per-champion bundle layout (the real splash art +
the descriptor-driven world sprite + the real ability icons + the per-skin
splash variants) without ever opening a PNG/JPG with the Read tool. Reports
metadata (size, alpha-bbox, mean color) so art completeness can be checked
headless. Safe to run under SDL_VIDEODRIVER=dummy or xvfb-run.

Run:
    SDL_VIDEODRIVER=dummy python3 verify_assets.py
"""
import os
import sys

import pygame

import champions as C
import data as D
import entities as E

ASSET_DIR = D.ASSET_DIR


def _stats(surf):
    """Return lightweight metadata about a Surface without 'reading' it as art.
    Works for both alpha (32-bit png) and opaque (jpg / 24-bit) surfaces — the
    ability icons are real LoL art and may be 24-bit with no alpha channel."""
    w, h = surf.get_size()
    # normalize to a 32-bit alpha surface so pixels_alpha/pixels3d always work
    if not (surf.get_flags() & 0x00010000):
        surf = surf.convert_alpha()
    arr = pygame.surfarray.pixels_alpha(surf)  # (w,h) uint8 view
    alpha = arr.__array__()
    del arr
    ys, xs = (alpha > 8).nonzero()
    if len(xs) == 0:
        bbox = None
        coverage = 0.0
        mean_rgb = None
    else:
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
        coverage = float((alpha > 8).sum()) / (w * h)
        mean_rgb = None
        try:
            rgb = pygame.surfarray.pixels3d(surf)
            mask = alpha > 8
            if mask.any():
                r = rgb[:, :, 0][mask].mean()
                g = rgb[:, :, 1][mask].mean()
                b = rgb[:, :, 2][mask].mean()
                mean_rgb = (round(float(r), 1), round(float(g), 1), round(float(b), 1))
            del rgb
        except Exception:
            pass
    return {
        "size": (w, h),
        "bbox": bbox,
        "coverage_pct": round(coverage * 100, 2),
        "mean_rgb_opaque": mean_rgb,
    }


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))

    EXPECT = {
        "sprite": (256, 256),
        "portrait": (380, 380),   # the real splash_tile square
        "icon": (128, 128),        # the real LoL champ icon
        "skill": (64, 64),         # the real LoL ability icon
    }
    failures = []

    champs = C.CHAMPIONS_DB
    print("=" * 64)
    print(f"CHAMPION BUNDLES ({len(champs)} champions)")
    print("=" * 64)
    n_sprite = n_portrait = n_icon = n_skins = n_skills = 0
    archetype_cov = {}   # archetype -> list of sprite coverage (distinctness)
    for c in champs:
        key = c["id"]
        base = os.path.join(ASSET_DIR, "characters", key)
        # sprite.png (procedural world billboard)
        spath = os.path.join(base, "sprite.png")
        if not os.path.exists(spath):
            failures.append(f"characters/{key}/sprite.png missing")
        else:
            s = pygame.image.load(spath)
            if s.get_size() != EXPECT["sprite"]:
                failures.append(f"characters/{key}/sprite.png: {s.get_size()} != {EXPECT['sprite']}")
            else:
                n_sprite += 1
                st = _stats(s)
                archetype_cov.setdefault(c["archetype"], []).append(st["coverage_pct"])
        # portrait.jpg (default skin splash)
        ppath = os.path.join(base, "portrait.jpg")
        if not os.path.exists(ppath):
            failures.append(f"characters/{key}/portrait.jpg missing")
        else:
            s = pygame.image.load(ppath)
            if s.get_size() != EXPECT["portrait"]:
                failures.append(f"characters/{key}/portrait.jpg: {s.get_size()} != {EXPECT['portrait']}")
            else:
                n_portrait += 1
        # icon.png (the real LoL champ icon)
        ipath = os.path.join(base, "icon.png")
        if not os.path.exists(ipath):
            failures.append(f"characters/{key}/icon.png missing")
        else:
            s = pygame.image.load(ipath)
            if s.get_size() != EXPECT["icon"]:
                failures.append(f"characters/{key}/icon.png: {s.get_size()} != {EXPECT['icon']}")
            else:
                n_icon += 1
        # skins/{N}.jpg (per-skin splash variants)
        skins_dir = os.path.join(base, "skins")
        if os.path.isdir(skins_dir):
            for fn in os.listdir(skins_dir):
                if fn.endswith(".jpg"):
                    n_skins += 1
        # skills/{skill_id}.png (real ability icons) for each kit skill
        hdef = D.HERO_BY_ID.get(key)
        if hdef is None:
            failures.append(f"characters/{key}: no HEROES_DB entry")
            continue
        skill_ids = [sid for sid in hdef["skills"] if sid]
        if hdef.get("ultimate"):
            skill_ids.append(hdef["ultimate"])
        for sid in skill_ids:
            if sid not in D.SKILLS_DB:
                failures.append(f"characters/{key}: skill {sid} not in SKILLS_DB")
                continue
            ipath = os.path.join(base, "skills", f"{sid}.png")
            if not os.path.exists(ipath):
                failures.append(f"characters/{key}/skills/{sid}.png missing")
            else:
                s = pygame.image.load(ipath)
                if s.get_size() != EXPECT["skill"]:
                    failures.append(f"characters/{key}/skills/{sid}.png: {s.get_size()} != {EXPECT['skill']}")
                else:
                    n_skills += 1
    print(f"  sprite.png: {n_sprite}/{len(champs)}")
    print(f"  portrait.jpg: {n_portrait}/{len(champs)}")
    print(f"  icon.png: {n_icon}/{len(champs)}")
    print(f"  skin splash variants: {n_skins}")
    print(f"  skill icons: {n_skills}")

    # archetype distinctness (the procedural world sprite): each archetype's
    # mean coverage should differ so the 10 silhouettes read as distinct.
    print()
    print("=" * 64)
    print("WORLD-SPRITE ARCHETYPE DISTINCTNESS")
    print("=" * 64)
    arch_means = {}
    for a in sorted(archetype_cov):
        vals = archetype_cov[a]
        m = sum(vals) / len(vals)
        arch_means[a] = round(m, 2)
        print(f"  {a:10s} n={len(vals):3d} mean_cov={m:.2f}%")
    distinct_means = len(set(round(v, 1) for v in arch_means.values()))
    print(f"  distinct mean-coverages (rounded to 0.1%): {distinct_means}/{len(arch_means)}")
    if distinct_means < 7:
        failures.append(f"archetype distinctness: only {distinct_means} distinct mean-coverages")

    # per-skill distinctness: the same skill_id on two champs should have
    # different (real) ability icons -> different mean color. Pick a shared
    # skill that appears in multiple champs' kits.
    print()
    print("=" * 64)
    print("PER-SKILL DISTINCTNESS (same skill_id, different champ -> different icon)")
    print("=" * 64)
    from collections import defaultdict
    by_skill = defaultdict(list)
    for c in champs:
        hdef = D.HERO_BY_ID.get(c["id"])
        if hdef is None:
            continue
        sids = [sid for sid in hdef["skills"] if sid]
        if hdef.get("ultimate"):
            sids.append(hdef["ultimate"])
        for sid in sids:
            if sid in D.SKILLS_DB:
                by_skill[sid].append(c["id"])
    distinct_checks = 0
    for sid, heroes in by_skill.items():
        if len(heroes) < 2:
            continue
        means = []
        for hn in heroes[:5]:
            ipath = os.path.join(ASSET_DIR, "characters", hn, "skills", f"{sid}.png")
            if os.path.exists(ipath):
                s = pygame.image.load(ipath)
                st = _stats(s)
                means.append((hn, st["mean_rgb_opaque"]))
        if len(means) >= 2:
            distinct = len({m for _, m in means}) > 1
            distinct_checks += 1
            if not distinct:
                failures.append(f"per-skill distinctness: {sid} identical across champs")
            if distinct_checks <= 8:
                print(f"  {sid:16s} heroes={[m[0] for m in means]} "
                      f"means={[m[1] for m in means]} distinct={distinct}")
        if distinct_checks >= 12:
            break

    # loader smoke test — the entities.py loaders must resolve + return a
    # converted surface for a few champs + the boss-ult global skill icon.
    print()
    print("=" * 64)
    print("LOADER SMOKE TEST (entities.load_*)")
    print("=" * 64)
    for fn, args in (("load_char_sprite", ("Ahri",)),
                     ("load_portrait", ("Ahri", 0)),
                     ("load_portrait", ("Garen", 0)),
                     ("load_champ_icon", ("Lux",)),
                     ("load_skill_icon", ("Ahri", "wind_arrow")),
                     ("load_skill_icon", (None, "hellfire"))):
        try:
            surf = getattr(E, fn)(*args)
            print(f"  {fn}({args}) -> {surf.get_size()} OK")
        except Exception as e:
            failures.append(f"{fn}({args}): {e}")
            print(f"  {fn}({args}) FAIL {e}")

    # enemies + bosses — every ENEMIES_DB id has a sprite OR is drawn
    # procedurally by draw_enemy at runtime (load_enemy_sprite is wrapped in
    # try/except in WorldEnemy). Just confirm the DB + ROW_ENEMIES are
    # internally consistent (no KeyError at spawn).
    print()
    print("=" * 64)
    print("ENEMIES + BOSSES (data consistency)")
    print("=" * 64)
    import world_data as WD
    for row, (pool, boss) in WD.ROW_ENEMIES.items():
        for eid in pool + [boss]:
            if eid not in D.ENEMIES_DB:
                failures.append(f"ROW_ENEMIES[{row}] id {eid} not in ENEMIES_DB")
            else:
                for s in D.ENEMIES_DB[eid]["skills"]:
                    if s not in D.SKILLS_DB:
                        failures.append(f"enemy {eid} skill {s} not in SKILLS_DB")
    for bid in D.BOSS_IDS:
        if bid not in D.ENEMIES_DB:
            failures.append(f"boss {bid} not in ENEMIES_DB")
        ult = D.BOSS_ULT.get(bid)
        if ult and ult not in D.SKILLS_DB:
            failures.append(f"boss {bid} ult {ult} not in SKILLS_DB")
    print(f"  mobs: {len(D.ENEMIES_DB) - len(D.BOSS_IDS)}, bosses: {len(D.BOSS_IDS)}")
    print(f"  ROW_ENEMIES + BOSS_ULT consistent: "
          f"{'OK' if not any('ROW_ENEMIES' in f or 'boss ' in f for f in failures) else 'FAIL'}")

    print()
    if failures:
        print(f"FAIL — {len(failures)} issues:")
        for f in failures[:30]:
            print(f"  {f}")
        if len(failures) > 30:
            print(f"  ...and {len(failures) - 30} more")
        sys.exit(1)
    print("OK — all champion bundles complete, sizes correct, archetype + "
          "per-skill distinctness hold, loaders resolve, enemies/bosses consistent.")


if __name__ == "__main__":
    main()
