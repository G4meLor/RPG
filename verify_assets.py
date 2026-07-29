"""
Headless asset verification — NO image reading.

Renders each character / enemy / portrait via the same code paths the game uses,
then reports metadata (size, alpha-bbox, mean color, per-channel stats, element
tint) so art quality can be checked without ever opening a PNG with the Read
tool. Safe to run under `SDL_VIDEODRIVER=dummy` or `xvfb-run`.

Run:
    SDL_VIDEODRIVER=dummy python3 verify_assets.py
"""
import os
import sys
import math
import statistics

import pygame

import generate_assets as GA

ASSET_DIR = GA.ASSET_DIR


def _stats(surf):
    """Return lightweight metadata about a Surface without 'reading' it as art."""
    w, h = surf.get_size()
    arr = pygame.surfarray.pixels_alpha(surf)  # (w,h) uint8 view
    alpha = arr.__array__()
    del arr
    # opaque bounding box
    ys, xs = (alpha > 8).nonzero()
    if len(xs) == 0:
        bbox = None
        coverage = 0.0
    else:
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))
        coverage = float((alpha > 8).sum()) / (w * h)
    # mean RGB over opaque pixels (sample a small grid to stay cheap)
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


def _hue_bucket(rgb):
    """Crude element guess from mean color for a sanity cross-check."""
    if rgb is None:
        return "?"
    r, g, b = rgb
    mx, mn = max(r, g, b), min(r, g, b)
    if mx - mn < 18:
        return "neutral"
    if r >= g and r >= b:
        return "fire/light" if g > 120 else "fire/dark"
    if b >= r and b >= g:
        return "water/dark"
    if g >= r and g >= b:
        return "wind"
    return "light"


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))  # needed for some font/surface ops

    # Expected sprite sizes (sacred — a regression here breaks load_char_sprite /
    # load_portrait / load_enemy_sprite / load_skill_icon + the scene caches).
    EXPECT = {
        "characters": (256, 256),
        "portraits": (512, 512),
        "enemies": (256, 256),
        "skills": (128, 128),
        "terrain": (40, 40),
        "landmarks": (80, 80),
        "villages": (60, 60),
        "drops": (16, 16),
    }
    failures = []

    print("=" * 64)
    print("CHARACTERS (chibi 256x256)")
    print("=" * 64)
    rows = []
    for name, element, weapon, hair_style, hair, body, accent in GA.HEROES:
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        GA.draw_chibi(s, element, body, hair, accent, weapon, hair_style)
        st = _stats(s)
        rows.append((name, element, st))
        print(f"{name:9s} el={element:5s} {st['size']} cov={st['coverage_pct']:5.1f}% "
              f"bbox={st['bbox']} mean={st['mean_rgb_opaque']} hue~{_hue_bucket(st['mean_rgb_opaque'])}")
        if st["size"] != EXPECT["characters"]:
            failures.append(f"characters/{name}: {st['size']} != {EXPECT['characters']}")

    # quick distinctness check: no two heroes should have identical mean color
    means = [r[2]["mean_rgb_opaque"] for r in rows]
    dups = [m for m in means if means.count(m) > 1]
    print(f"  duplicate mean colors: {len(dups)} (expect ~0)")

    print()
    print("=" * 64)
    print("PORTRAITS (512x512)")
    print("=" * 64)
    for name, element, weapon, hair_style, hair, body, accent in GA.HEROES:
        path = os.path.join(ASSET_DIR, "portraits", f"{name}.png")
        GA.make_portrait(element, body, hair, accent, hair_style, weapon, path)
        # load the saved portrait back to measure the actual saved pixels
        # (loading via pygame.image.load is fine — it is NOT the Read tool)
        s = pygame.image.load(path)
        st = _stats(s)
        print(f"{name:9s} el={element:5s} {st['size']} cov={st['coverage_pct']:5.1f}% "
              f"bbox={st['bbox']} mean={st['mean_rgb_opaque']}")
        if st["size"] != EXPECT["portraits"]:
            failures.append(f"portraits/{name}: {st['size']} != {EXPECT['portraits']}")

    print()
    print("=" * 64)
    print("ENEMIES (256x256)")
    print("=" * 64)
    for name, el, pal in GA.ENEMIES:
        s = pygame.Surface((256, 256), pygame.SRCALPHA)
        GA.draw_enemy(s, name, pal)
        st = _stats(s)
        print(f"{name:13s} el={el:5s} {st['size']} cov={st['coverage_pct']:5.1f}% "
              f"bbox={st['bbox']} mean={st['mean_rgb_opaque']}")
        if st["size"] != EXPECT["enemies"]:
            failures.append(f"enemies/{name}: {st['size']} != {EXPECT['enemies']}")

    print()
    print("=" * 64)
    print("SKILL ICONS (128x128) — on-disk size check")
    print("=" * 64)
    for name, el, kind in GA.SKILLS:
        path = os.path.join(ASSET_DIR, "skills", f"{name}.png")
        s = pygame.image.load(path)
        sz = s.get_size()
        print(f"{name:18s} el={el:5s} {sz}")
        if sz != EXPECT["skills"]:
            failures.append(f"skills/{name}: {sz} != {EXPECT['skills']}")

    # per-character bundles: assets/characters/{hero_id}/sprite.png +
    # portrait.png + skills/{skill_id}.png. Each hero's kit (3 active +
    # ult + basic_attack) is rendered with per-skill distinct art + the
    # hero's accent tint, so the same skill on two heroes looks different.
    print()
    print("=" * 64)
    print("PER-CHARACTER BUNDLES (characters/{hero_id}/)")
    print("=" * 64)
    import data as D
    for name, element, weapon, hair_style, hair, body, accent in GA.HEROES:
        hero_dir = os.path.join(ASSET_DIR, "characters", name)
        # sprite
        spath = os.path.join(hero_dir, "sprite.png")
        if not os.path.exists(spath):
            failures.append(f"characters/{name}/sprite.png missing")
        else:
            ds = pygame.image.load(spath)
            if ds.get_size() != EXPECT["characters"]:
                failures.append(f"characters/{name}/sprite.png: {ds.get_size()} != {EXPECT['characters']}")
        # portrait
        ppath = os.path.join(hero_dir, "portrait.png")
        if not os.path.exists(ppath):
            failures.append(f"characters/{name}/portrait.png missing")
        else:
            ds = pygame.image.load(ppath)
            if ds.get_size() != EXPECT["portraits"]:
                failures.append(f"characters/{name}/portrait.png: {ds.get_size()} != {EXPECT['portraits']}")
        # per-hero skill icons
        hdef = next((h for h in D.HEROES_DB if h["id"] == name), None)
        if hdef is None:
            failures.append(f"characters/{name}: no HEROES_DB entry")
            continue
        skill_ids = [sid for sid in hdef["skills"] if sid]
        if hdef.get("ultimate"):
            skill_ids.append(hdef["ultimate"])
        n_icons = 0
        for sid in skill_ids:
            if sid not in D.SKILLS_DB:
                continue
            ipath = os.path.join(hero_dir, "skills", f"{sid}.png")
            if not os.path.exists(ipath):
                failures.append(f"characters/{name}/skills/{sid}.png missing")
            else:
                ds = pygame.image.load(ipath)
                if ds.get_size() != EXPECT["skills"]:
                    failures.append(f"characters/{name}/skills/{sid}.png: {ds.get_size()} != {EXPECT['skills']}")
                n_icons += 1
        print(f"{name:9s} el={element:5s} sprite+portrait+{n_icons} skill icons")

    # per-skill distinctness: the same skill on two heroes should look different
    # (different accent tint → different mean color). Pick a shared skill that
    # appears in multiple heroes' kits + check the per-hero copies differ.
    print()
    print("=" * 64)
    print("PER-SKILL DISTINCTNESS (same skill, different hero → different art)")
    print("=" * 64)
    # find a skill shared by >=2 heroes
    from collections import defaultdict
    by_skill = defaultdict(list)
    for name, element, weapon, hair_style, hair, body, accent in GA.HEROES:
        hdef = next((h for h in D.HEROES_DB if h["id"] == name), None)
        if hdef is None:
            continue
        skill_ids = [sid for sid in hdef["skills"] if sid]
        if hdef.get("ultimate"):
            skill_ids.append(hdef["ultimate"])
        for sid in skill_ids:
            if sid in D.SKILLS_DB:
                by_skill[sid].append(name)
    # check the first shared skill — its per-hero copies should differ in mean color
    distinct_checks = 0
    for sid, heroes in by_skill.items():
        if len(heroes) < 2:
            continue
        means = []
        for hn in heroes[:4]:
            ipath = os.path.join(ASSET_DIR, "characters", hn, "skills", f"{sid}.png")
            if os.path.exists(ipath):
                s = pygame.image.load(ipath)
                st = _stats(s)
                means.append((hn, st["mean_rgb_opaque"]))
        if len(means) >= 2:
            distinct = len({m for _, m in means}) > 1
            distinct_checks += 1
            print(f"  {sid:16s} heroes={[m[0] for m in means]} means={[m[1] for m in means]} distinct={distinct}")
            if not distinct:
                failures.append(f"per-skill distinctness: {sid} identical across heroes")
        if distinct_checks >= 5:
            break

    # per-skill variant distinctness: two different skills of the same kind
    # should pick different variants (so fire_slash vs light_slash differ in
    # shape, not just color). Check by rendering two same-kind skills + the
    # alpha-bbox / mean should differ.
    print()
    print("=" * 64)
    print("PER-SKILL VARIANT (same kind, different skill → different shape)")
    print("=" * 64)
    # pick two skills of the same kind (slash) + render them with the same
    # element (so the only difference is the variant) — the mean color should
    # still differ because the shapes differ.
    kind_groups = defaultdict(list)
    for name, el, kind in GA.SKILLS:
        kind_groups[kind].append((name, el))
    variant_checks = 0
    for kind, skills in kind_groups.items():
        if len(skills) < 2:
            continue
        s1, e1 = skills[0]
        s2, e2 = skills[1]
        # render both with the same element + no accent (so the only diff is
        # the variant derived from the skill name)
        surf1 = pygame.Surface((128, 128), pygame.SRCALPHA)
        GA.draw_skill_icon(surf1, s1, e1, kind)
        surf2 = pygame.Surface((128, 128), pygame.SRCALPHA)
        GA.draw_skill_icon(surf2, s2, e1, kind)
        st1 = _stats(surf1)
        st2 = _stats(surf2)
        diff = st1["mean_rgb_opaque"] != st2["mean_rgb_opaque"] or st1["coverage_pct"] != st2["coverage_pct"]
        variant_checks += 1
        print(f"  kind={kind:8s} {s1:16s} vs {s2:16s} mean1={st1['mean_rgb_opaque']} cov1={st1['coverage_pct']:.1f}% mean2={st2['mean_rgb_opaque']} cov2={st2['coverage_pct']:.1f}% diff={diff}")
        if not diff:
            failures.append(f"per-skill variant: {s1} vs {s2} (kind={kind}) identical")
        if variant_checks >= 5:
            break

    # v2 world sprites (Task A4) — terrain tiles, landmarks, village buildings,
    # ground loot drops. Render each via the real draw_ helpers + assert the
    # on-disk files exist at the expected sizes.
    print()
    print("=" * 64)
    print("TERRAIN TILES (40x40)")
    print("=" * 64)
    for name in ("water", "bridge"):
        s = pygame.Surface((40, 40), pygame.SRCALPHA)
        if name == "water":
            GA.draw_water_tile(s)
        else:
            GA.draw_bridge_tile(s)
        st = _stats(s)
        print(f"{name:8s} {st['size']} cov={st['coverage_pct']:5.1f}% "
              f"bbox={st['bbox']} mean={st['mean_rgb_opaque']}")
        if st["size"] != EXPECT["terrain"]:
            failures.append(f"terrain/{name}: {st['size']} != {EXPECT['terrain']}")
        if st["coverage_pct"] < 80.0:
            failures.append(f"terrain/{name}: coverage {st['coverage_pct']}% < 80")
        path = os.path.join(ASSET_DIR, "terrain", f"{name}.png")
        if not os.path.exists(path):
            failures.append(f"terrain/{name}.png missing")
        else:
            ds = pygame.image.load(path)
            if ds.get_size() != EXPECT["terrain"]:
                failures.append(f"terrain/{name} on-disk: {ds.get_size()} != {EXPECT['terrain']}")

    print()
    print("=" * 64)
    print("LANDMARKS (80x80)")
    print("=" * 64)
    for kind in ("statue", "ruin", "shrine", "obelisk", "rift_anchor"):
        s = pygame.Surface((80, 80), pygame.SRCALPHA)
        GA.draw_landmark(s, kind)
        st = _stats(s)
        print(f"{kind:14s} {st['size']} cov={st['coverage_pct']:5.1f}% "
              f"bbox={st['bbox']} mean={st['mean_rgb_opaque']} hue~{_hue_bucket(st['mean_rgb_opaque'])}")
        if st["size"] != EXPECT["landmarks"]:
            failures.append(f"landmarks/{kind}: {st['size']} != {EXPECT['landmarks']}")
        if st["coverage_pct"] < 8.0:
            failures.append(f"landmarks/{kind}: coverage {st['coverage_pct']}% < 8")
        path = os.path.join(ASSET_DIR, "landmarks", f"{kind}.png")
        if not os.path.exists(path):
            failures.append(f"landmarks/{kind}.png missing")
        else:
            ds = pygame.image.load(path)
            if ds.get_size() != EXPECT["landmarks"]:
                failures.append(f"landmarks/{kind} on-disk: {ds.get_size()} != {EXPECT['landmarks']}")

    print()
    print("=" * 64)
    print("VILLAGE BUILDINGS (60x60)")
    print("=" * 64)
    for kind in ("house", "shop", "temple"):
        s = pygame.Surface((60, 60), pygame.SRCALPHA)
        GA.draw_village_building(s, kind)
        st = _stats(s)
        print(f"{kind:8s} {st['size']} cov={st['coverage_pct']:5.1f}% "
              f"bbox={st['bbox']} mean={st['mean_rgb_opaque']}")
        if st["size"] != EXPECT["villages"]:
            failures.append(f"villages/{kind}: {st['size']} != {EXPECT['villages']}")
        if st["coverage_pct"] < 15.0:
            failures.append(f"villages/{kind}: coverage {st['coverage_pct']}% < 15")
        path = os.path.join(ASSET_DIR, "villages", f"{kind}.png")
        if not os.path.exists(path):
            failures.append(f"villages/{kind}.png missing")
        else:
            ds = pygame.image.load(path)
            if ds.get_size() != EXPECT["villages"]:
                failures.append(f"villages/{kind} on-disk: {ds.get_size()} != {EXPECT['villages']}")

    print()
    print("=" * 64)
    print("GROUND LOOT DROPS (16x16)")
    print("=" * 64)
    for kind in ("gold", "potion", "shard", "equipment"):
        s = pygame.Surface((16, 16), pygame.SRCALPHA)
        GA.draw_drop(s, kind)
        st = _stats(s)
        print(f"{kind:11s} {st['size']} cov={st['coverage_pct']:5.1f}% "
              f"bbox={st['bbox']} mean={st['mean_rgb_opaque']} hue~{_hue_bucket(st['mean_rgb_opaque'])}")
        if st["size"] != EXPECT["drops"]:
            failures.append(f"drops/{kind}: {st['size']} != {EXPECT['drops']}")
        if st["coverage_pct"] < 5.0:
            failures.append(f"drops/{kind}: coverage {st['coverage_pct']}% < 5")
        path = os.path.join(ASSET_DIR, "drops", f"{kind}.png")
        if not os.path.exists(path):
            failures.append(f"drops/{kind}.png missing")
        else:
            ds = pygame.image.load(path)
            if ds.get_size() != EXPECT["drops"]:
                failures.append(f"drops/{kind} on-disk: {ds.get_size()} != {EXPECT['drops']}")

    # loader smoke test — the entities.py loaders must resolve + return a
    # converted-alpha surface (so the scene can blit them without a per-frame
    # convert). Catches a path mismatch or a missing file. Includes the
    # per-character bundle loaders (load_char_sprite / load_portrait) + the
    # new per-hero load_skill_icon (which takes hero_id + skill_id).
    print()
    print("=" * 64)
    print("LOADER SMOKE TEST (entities.load_*)")
    print("=" * 64)
    import entities as E
    for fn, args in (("load_terrain", ("water",)),
                     ("load_landmark", ("statue",)),
                     ("load_village", ("house",)),
                     ("load_drop", ("gold",)),
                     ("load_char_sprite", ("kael",)),
                     ("load_portrait", ("kael",)),
                     ("load_skill_icon", ("kael", "fire_slash")),
                     ("load_skill_icon", (None, "hellfire"))):
        try:
            surf = getattr(E, fn)(*args)
            print(f"{fn}({args[0]!r}, {args[1] if len(args)>1 else ''!r}) -> {surf.get_size()} OK")
        except Exception as e:
            failures.append(f"{fn}({args!r}): {e}")
            print(f"{fn}({args!r}) FAIL {e}")

    print()
    if failures:
        print("FAIL — size regressions:")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)
    print("OK — all rendered without error, sizes unchanged.")


if __name__ == "__main__":
    main()
