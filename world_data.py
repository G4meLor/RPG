"""
Aetheria Open World - World Data
10x5 grid of maps, biomes, deterministic per-cell generation, the teleport
graph (neighbor links), and difficulty scaling. All static so it is cheap.
"""
import random
import math

import data as D

# ---------------------------------------------------------------------------
# Grid + tile geometry
# ---------------------------------------------------------------------------
GRID_W = 10            # columns
GRID_H = 5             # rows  -> 50 maps total

TILE = 40             # px per tile
MAP_TW = 50           # tiles across one map
MAP_TH = 30           # tiles tall one map
MAP_W = MAP_TW * TILE  # 2000 px
MAP_H = MAP_TH * TILE  # 1200 px

# ---------------------------------------------------------------------------
# Biomes - one per row. palette = (ground_a, ground_b, obstacle, accent, sky)
# fog = a tinted haze drawn over distant tiles for depth.
# ---------------------------------------------------------------------------
BIOMES = {
    "plains":  dict(name="Sunlit Meadows",  ground=(110, 170, 90),  ground2=( 92, 150, 74),
                    obstacle=( 70, 110, 55), accent=(230, 230, 160), sky=(150, 200, 230),
                    fog=(180, 220, 200)),
    "forest":  dict(name="Whispering Woods", ground=( 60, 110, 64),  ground2=( 48,  92, 52),
                    obstacle=( 40,  80, 45), accent=(120, 200, 110), sky=(120, 170, 150),
                    fog=(110, 160, 120)),
    "cave":    dict(name="Crystal Caverns",  ground=( 40, 46, 82),  ground2=( 32, 38, 70),
                    obstacle=( 70, 80, 140), accent=(160, 220, 255), sky=( 20, 24, 48),
                    fog=( 50, 60, 120)),
    "castle":  dict(name="Ruined Citadel",   ground=( 96, 82, 66),  ground2=( 80, 66, 54),
                    obstacle=(150, 130, 100), accent=(230, 200, 140), sky=( 90, 80, 70),
                    fog=(140, 120, 90)),
    "void":    dict(name="The Void",         ground=( 30, 22, 44),  ground2=( 22, 16, 36),
                    obstacle=( 70, 40, 100), accent=(200, 120, 240), sky=( 10,  6, 20),
                    fog=( 60, 40, 90)),
}

# Row -> biome
ROW_BIOME = ["plains", "forest", "cave", "castle", "void"]

# Row -> (enemy pool, boss)
ROW_ENEMIES = {
    0: (["slime", "goblin", "bat"],            "golem"),
    1: (["wolf", "goblin", "harpy", "imp"],     "hydra"),
    2: (["bat", "skeleton", "ghoul", "golem"],  "frosttitan"),
    3: (["skeleton", "orc", "paladin", "wraith"], "dragon"),
    4: (["wraith", "paladin", "hydra", "demonking"], "demonking"),
}

# Master seed so the whole grid is stable across runs
WORLD_SEED = 1337


def cell_seed(c, r):
    """Deterministic seed for cell (c, r)."""
    return WORLD_SEED + r * 1000 + c * 7


def cell_biome(c, r):
    return ROW_BIOME[r]


def cell_level(c, r, ng_cycle=0):
    """Enemy level for cell (c, r). Bosses add a flat bonus. NG+ cycles add
    NG_PLUS_LEVEL_BONUS per cycle on top of the base level so a replayed world
    stays challenging after Ascending."""
    base = 1 + r * 6 + int(c * 1.5)
    if ng_cycle:
        base += ng_cycle * D.NG_PLUS_LEVEL_BONUS
    return base


def is_boss_cell(c, r):
    """Right-most column of each row is the boss arena for that row; the
    final cell (9,4) is the final boss."""
    return c == GRID_W - 1


def cell_name(c, r):
    biome = BIOMES[cell_biome(c, r)]["name"]
    if is_boss_cell(c, r):
        return f"{biome} - Sanctum"
    return f"{biome} ({c+1},{r+1})"


# ---------------------------------------------------------------------------
# Teleport graph - which neighbors does each cell connect to
# ---------------------------------------------------------------------------
def neighbors(c, r):
    """List of (nc, nr) neighbors this map links to (no diagonals)."""
    out = []
    if c > 0:           out.append((c - 1, r))
    if c < GRID_W - 1:  out.append((c + 1, r))
    if r > 0:           out.append((c, r - 1))
    if r < GRID_H - 1:  out.append((c, r + 1))
    return out


def edge_for(src, dst):
    """Given we are walking from src to dst, which edge do we exit through,
    and where do we enter the dst map (opposite edge)."""
    sc, sr = src
    dc, dr = dst
    if dc > sc:   return "right",  "left"
    if dc < sc:   return "left",   "right"
    if dr > sr:   return "bottom", "top"
    if dr < sr:   return "top",    "bottom"
    return "right", "left"


# ---------------------------------------------------------------------------
# Per-cell map generation
#   A generated map is a dict:
#     obstacles: list of pygame.Rect (tiled, in pixel coords) - collision
#     deco: list of (x, y, kind, size) - for the baked decorative render
#     spawns: list of (x, y) enemy spawn points (pixel)
#     boss: (x, y) or None
#     is_boss: bool
# ---------------------------------------------------------------------------
# Per-biome layout helpers — each biome gets a distinct generator so the 5
# biomes read as different places (open field / dense thicket / tunnels /
# pillar aisles / ringed clearing) instead of one shared dot-scatter. The
# spatial grid + rect-accurate overlap check are shared so collision stays
# correct even with multi-tile obstacles.
# ---------------------------------------------------------------------------
def _register(grid, o):
    """Register obstacle o in every tile bucket its rect covers, so the
    spatial-grid overlap check sees multi-tile obstacles correctly."""
    x0, y0 = o.x // TILE, o.y // TILE
    x1 = (o.x + o.w - 1) // TILE
    y1 = (o.y + o.h - 1) // TILE
    for gy in range(y0, y1 + 1):
        for gx in range(x0, x1 + 1):
            grid.setdefault((gx, gy), []).append(o)


def _place(obstacles, deco, grid, x, y, w, h, kind, deco_size):
    o = pygame_rect(x, y, w, h)
    obstacles.append(o)
    _register(grid, o)
    deco.append((x + w // 2, y + h // 2, kind, deco_size))
    return o


def _near_grid(grid, x, y, w, h, pad):
    """True if a candidate rect (x, y, w, h) overlaps or is within `pad` px of
    an existing obstacle in the spatial grid. Uses real rect intersection, so
    multi-tile obstacles are detected (a top-left-corner compare is not enough
    once obstacles can be 2-wide or 2-tall)."""
    px, py = x - pad, y - pad
    pw, ph = w + pad * 2, h + pad * 2
    probe = pygame_rect(px, py, pw, ph)
    gx0, gy0 = px // TILE, py // TILE
    gx1 = (px + pw - 1) // TILE
    gy1 = (py + ph - 1) // TILE
    for gy in range(gy0, gy1 + 1):
        for gx in range(gx0, gx1 + 1):
            for o in grid.get((gx, gy), ()):
                if probe.colliderect(o):
                    return True
    return False


def _layout_open(rng, obstacles, deco, grid, cx_mid, cy_mid, kind_pool, n_obs):
    """Plains: a genuinely open field — a few single rocks/bushes/trees
    scattered with a 1-tile gap and no center carve."""
    placed, tries = 0, 0
    while placed < n_obs and tries < 200:
        tries += 1
        tx = rng.randint(3, MAP_TW - 4)
        ty = rng.randint(3, MAP_TH - 4)
        x, y = tx * TILE, ty * TILE
        if _near_grid(grid, x, y, TILE, TILE, TILE):
            continue
        kind = rng.choice(kind_pool)
        _place(obstacles, deco, grid, x, y, TILE, TILE, kind, rng.randint(28, 40))
        placed += 1


def _layout_dense(rng, obstacles, deco, grid, cx_mid, cy_mid, kind_pool, n_obs):
    """Forest: dense thickets of trees with a small 4x4-tile central clearing."""
    placed, tries = 0, 0
    while placed < n_obs and tries < 300:
        tries += 1
        tx = rng.randint(3, MAP_TW - 4)
        ty = rng.randint(3, MAP_TH - 4)
        x, y = tx * TILE, ty * TILE
        if abs(x - cx_mid) < TILE * 2 and abs(y - cy_mid) < TILE * 2:
            continue
        if _near_grid(grid, x, y, TILE, TILE, TILE):
            continue
        kind = rng.choice(kind_pool)
        _place(obstacles, deco, grid, x, y, TILE, TILE, kind, rng.randint(30, 42))
        placed += 1


def _layout_tunnels(rng, obstacles, deco, grid, cx_mid, cy_mid, kind_pool, n_obs):
    """Cave: a horizontal tunnel corridor flanked by 2-wide rocks (and the
    occasional crystal pillar), with edge-adjacent placement so the walls read
    as continuous. All obstacles are 1 tile tall so none encroach the corridor.
    The corridor aligns with the left/right edge gap so the tunnel connects."""
    band = 4
    placed, tries = 0, 0
    while placed < n_obs and tries < 300:
        tries += 1
        ty = rng.randint(cy_mid // TILE - band, cy_mid // TILE + band)
        tx = rng.randint(3, MAP_TW - 4)
        x, y = tx * TILE, ty * TILE
        if abs(y - cy_mid) <= TILE * 2:
            continue
        kind = rng.choice(kind_pool)
        if kind == "pillar":
            w, h = TILE, TILE
        else:
            w, h = TILE * 2, TILE
        if _near_grid(grid, x, y, w, h, 0):
            continue
        _place(obstacles, deco, grid, x, y, w, h, kind, rng.randint(34, 44))
        placed += 1


def _layout_pillars(rng, obstacles, deco, grid, cx_mid, cy_mid, kind_pool, n_obs):
    """Castle: vertical pillar aisles flanking a central vertical corridor,
    with edge-adjacent placement so the 2-tall pillars form rows. The aisle
    aligns with the top/bottom edge gap so the hall connects vertically."""
    band = 4
    placed, tries = 0, 0
    while placed < n_obs and tries < 300:
        tries += 1
        tx = rng.randint(cx_mid // TILE - band, cx_mid // TILE + band)
        ty = rng.randint(3, MAP_TH - 4)
        x, y = tx * TILE, ty * TILE
        if abs(x - cx_mid) <= TILE * 2:
            continue
        kind = rng.choice(kind_pool)
        if kind == "pillar":
            w, h = TILE, TILE * 2
        else:
            w, h = TILE, TILE
        if _near_grid(grid, x, y, w, h, 0):
            continue
        _place(obstacles, deco, grid, x, y, w, h, kind, rng.randint(34, 44))
        placed += 1


def _layout_void(rng, obstacles, deco, grid, cx_mid, cy_mid, kind_pool, n_obs):
    """Void: a large central clearing ringed by scattered pillars/rocks that
    may cluster (edge-adjacent) into a broken ring around the open center."""
    placed, tries = 0, 0
    while placed < n_obs and tries < 200:
        tries += 1
        tx = rng.randint(3, MAP_TW - 4)
        ty = rng.randint(3, MAP_TH - 4)
        x, y = tx * TILE, ty * TILE
        if abs(x - cx_mid) < TILE * 3 and abs(y - cy_mid) < TILE * 3:
            continue
        if _near_grid(grid, x, y, TILE, TILE, 0):
            continue
        kind = rng.choice(kind_pool)
        _place(obstacles, deco, grid, x, y, TILE, TILE, kind, rng.randint(30, 42))
        placed += 1


def gen_map(c, r):
    """Return a generated map dict for cell (c, r). Deterministic."""
    rng = random.Random(cell_seed(c, r))
    biome = cell_biome(c, r)
    pal = BIOMES[biome]
    is_boss = is_boss_cell(c, r)

    obstacles = []
    deco = []

    # border walls (a few tiles thick visually; collision on the inner edge)
    bt = 1  # border thickness in tiles
    for t in range(bt):
        x = t * TILE
        # left + right vertical walls
        for ty in range(MAP_TH):
            obstacles.append(pygame_rect(x, ty * TILE, TILE, TILE))
            obstacles.append(pygame_rect(MAP_W - TILE - x, ty * TILE, TILE, TILE))
        # top + bottom
        for tx in range(MAP_TW):
            obstacles.append(pygame_rect(tx * TILE, t * TILE, TILE, TILE))
            obstacles.append(pygame_rect(tx * TILE, MAP_H - TILE - t * TILE, TILE, TILE))

    # carve a portal gap in the border wall at each traversable edge's midpoint
    # so the hero can actually walk through to the neighbor (the 1-tile-thick
    # wall + the hero's 20px radius would otherwise block the transition trigger
    # at x<8 / x>MAP_W-8). The gap is a few tiles wide centered on the edge
    # midpoint; we drop the wall tiles whose tile-row/col overlaps the gap.
    gap = 2   # half-width of the gap in tiles (so 5 tiles wide total)
    mid_tx = MAP_TW // 2
    mid_ty = MAP_TH // 2
    # left edge (always traversable horizontally): drop tiles at x==0 whose
    # tile-row is within `gap` of the midpoint row
    obstacles = [o for o in obstacles
                 if not (o.x == 0 and abs(o.y // TILE - mid_ty) <= gap)]
    # right edge
    obstacles = [o for o in obstacles
                 if not (o.x == MAP_W - TILE and abs(o.y // TILE - mid_ty) <= gap)]
    # top edge (only if r > 0)
    if r > 0:
        obstacles = [o for o in obstacles
                     if not (o.y == 0 and abs(o.x // TILE - mid_tx) <= gap)]
    # bottom edge (only if r < GRID_H - 1)
    if r < GRID_H - 1:
        obstacles = [o for o in obstacles
                     if not (o.y == MAP_H - TILE and abs(o.x // TILE - mid_tx) <= gap)]

    # scattered obstacles — dispatched to a per-biome generator so each biome
    # reads as a distinct place (open field / dense thicket / tunnels / pillar
    # aisles / ringed clearing) instead of one shared dot-scatter.
    base_n = {"plains": (3, 6),   "forest": (22, 30),
              "cave":   (8, 12),  "castle": (14, 20),
              "void":   (6, 10)}.get(biome, (8, 14))
    n_obs = 0 if is_boss else rng.randint(*base_n)
    cx_mid, cy_mid = MAP_W // 2, MAP_H // 2
    kind_pool = {"plains": ["tree", "bush", "rock"],
                 "forest": ["tree", "tree", "bush"],
                 "cave":   ["rock", "rock", "pillar"],
                 "castle": ["pillar", "pillar", "rock"],
                 "void":   ["pillar", "rock", "pillar"]}.get(biome, ["rock"])
    # a spatial grid (tile buckets) for fast overlap checks instead of scanning
    # every existing obstacle per candidate — the #1 cost in gen_map.
    grid = {}
    if not is_boss and n_obs > 0:
        layout_fn = {"plains":  _layout_open,
                     "forest":  _layout_dense,
                     "cave":    _layout_tunnels,
                     "castle":  _layout_pillars,
                     "void":    _layout_void}.get(biome, _layout_open)
        layout_fn(rng, obstacles, deco, grid, cx_mid, cy_mid, kind_pool, n_obs)

    # a single mid-row landmark per row so each row has a midpoint waypoint
    # that reads as a place (a great tree / crystal / statue / monolith / pond)
    # rather than just more tiles. Placed deterministically on column 5, offset
    # off each biome's central corridor so it never blocks the main path.
    if not is_boss and c == 5:
        landmark = {"plains":  ("bush",    TILE,     TILE,     46, cx_mid,           cy_mid + TILE * 3),
                    "forest":  ("tree",    TILE,     TILE,     48, cx_mid,           cy_mid + TILE * 3),
                    "cave":    ("pillar",  TILE,     TILE,     46, cx_mid,           cy_mid + TILE * 3),
                    "castle":  ("pillar",  TILE,     TILE * 2, 48, cx_mid + TILE * 3, cy_mid),
                    "void":    ("pillar",  TILE,     TILE,     48, cx_mid,           cy_mid + TILE * 4)}.get(biome)
        if landmark is not None:
            lk, lw, lh, ls, lx, ly = landmark
            if not _near_grid(grid, lx, ly, lw, lh, 0):
                _place(obstacles, deco, grid, lx, ly, lw, lh, lk, ls)

    # enemy spawns
    spawns = []
    if not is_boss:
        n_enemies = min(14, 4 + r * 2 + rng.randint(0, 3))
        # bias the spawn candidate region to the biome's structure so combat
        # geometry matches the layout (cave enemies in the tunnel, castle
        # enemies along the aisle, plains/forest/void in the open field).
        spawn_band = {"cave":   ("y", cy_mid, TILE * 3),
                      "castle": ("x", cx_mid, TILE * 4)}.get(biome, (None, None, None))
        axis, mid, half = spawn_band
        for _ in range(n_enemies):
            for _try in range(30):
                tx = rng.randint(3, MAP_TW - 4)
                ty = rng.randint(3, MAP_TH - 4)
                x, y = tx * TILE, ty * TILE
                if axis == "y" and abs(y - mid) > half:
                    continue
                if axis == "x" and abs(x - mid) > half:
                    continue
                if _free_grid(x, y, grid) and _dist(x, y, cx_mid, cy_mid) > TILE * 4:
                    spawns.append((x, y))
                    break
    # boss spawn - centered, with a biome-specific arena ring so each boss
    # arena has a distinct footprint (castle = tight 12-pillar cage, void =
    # wide 4-pillar, cave = 6-pillar with rng jitter, forest = tree ring,
    # plains = bush ring). Seeded from the cell so it stays deterministic.
    boss = None
    if is_boss:
        boss = (cx_mid, cy_mid - TILE)
        ring = {"plains":  (TILE * 6, 4,  "bush"),
                "forest":  (TILE * 5, 8,  "tree"),
                "cave":    (TILE * 7, 6,  "pillar"),
                "castle":  (TILE * 4, 12, "pillar"),
                "void":    (TILE * 8, 4,  "pillar")}.get(biome, (TILE * 5, 8, "pillar"))
        radius, n_ring, ring_kind = ring
        for i in range(n_ring):
            ang = 360 * i / n_ring + rng.randint(0, 45)
            ax = cx_mid + int(math.cos(math.radians(ang)) * radius)
            ay = cy_mid + int(math.sin(math.radians(ang)) * radius)
            if TILE < ax < MAP_W - TILE * 2 and TILE < ay < MAP_H - TILE * 2:
                _place(obstacles, deco, grid, ax, ay, TILE, TILE,
                       ring_kind, 42)

    # treasure chests — 0-2 per non-boss map, placed on free tiles away from the
    # center corridor. Kind is weighted by the row (deeper maps give better
    # loot). A chest is a reward pickup the hero opens by walking into it.
    chests = []
    if not is_boss:
        n_chests = rng.randint(0, 2)
        # loot kinds by row depth: shallower -> gold/gems, deeper -> shards/equip
        if r <= 1:
            kinds = ["gold", "gold", "gems"]
        elif r <= 2:
            kinds = ["gold", "gems", "shards"]
        else:
            kinds = ["gems", "shards", "shards", "equipment"]
        for _ in range(n_chests):
            for _try in range(30):
                tx = rng.randint(3, MAP_TW - 4)
                ty = rng.randint(3, MAP_TH - 4)
                x, y = tx * TILE, ty * TILE
                if _free_grid(x, y, grid) and _dist(x, y, cx_mid, cy_mid) > TILE * 3:
                    chests.append((x, y, rng.choice(kinds)))
                    break

    # breakable props — 4-8 per non-boss map, placed on free tiles away from the
    # center corridor (same gate as chests so they don't block the edge-portal
    # gaps). Kind by biome (plains=pot, castle=crate, cave=barrel; forest/void
    # fall back to pot/crate respectively). Loot is weighted: gold 60%,
    # hp_potion 20%, 1 shard 20%. A breakable shatters on attack/dash and drops
    # its loot — a small reward for exploring + a combat-feedback surface.
    breakables = []
    if not is_boss:
        n_break = rng.randint(4, 8)
        kind_by_biome = {"plains": "pot", "forest": "pot",
                         "cave":   "barrel", "castle": "crate",
                         "void":   "crate"}.get(biome, "pot")
        loot_weights = [("gold", 60), ("hp_potion", 20), ("shard", 20)]
        for _ in range(n_break):
            for _try in range(30):
                tx = rng.randint(3, MAP_TW - 4)
                ty = rng.randint(3, MAP_TH - 4)
                x, y = tx * TILE, ty * TILE
                if _free_grid(x, y, grid) and _dist(x, y, cx_mid, cy_mid) > TILE * 3:
                    # weighted loot pick (gold 60% / hp_potion 20% / shard 20%)
                    total_w = sum(w for _, w in loot_weights)
                    pick = rng.randint(1, total_w)
                    acc = 0
                    loot = "gold"
                    for lk, lw in loot_weights:
                        acc += lw
                        if pick <= acc:
                            loot = lk
                            break
                    breakables.append((x, y, kind_by_biome, loot))
                    break

    return dict(obstacles=obstacles, deco=deco, spawns=spawns, boss=boss,
                is_boss=is_boss, biome=biome, pal=pal, chests=chests,
                breakables=breakables)


def pygame_rect(x, y, w, h):
    # local import to avoid a hard pygame dependency at module import time for
    # tooling that only reads the constants; the real game always has pygame.
    import pygame
    return pygame.Rect(x, y, w, h)


def _free(x, y, obstacles, pad=8):
    r = pygame_rect(x - pad, y - pad, TILE + pad * 2, TILE + pad * 2)
    return not any(r.colliderect(o) for o in obstacles)


def _free_grid(x, y, grid, pad=8):
    """Free-check using the spatial grid built during obstacle placement,
    instead of scanning all obstacles. O(nearby tiles) not O(all)."""
    gx, gy = (x - pad) // TILE, (y - pad) // TILE
    r = pygame_rect(x - pad, y - pad, TILE + pad * 2, TILE + pad * 2)
    for ny in (gy - 1, gy, gy + 1):
        for nx in (gx - 1, gx, gx + 1):
            for o in grid.get((nx, ny), ()):
                if r.colliderect(o):
                    return False
    return True


def _dist(x1, y1, x2, y2):
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


# ---------------------------------------------------------------------------
# Entry point for a hero coming in through an edge
#   Returns (x, y) in pixel coords, centered on that edge with a margin.
# ---------------------------------------------------------------------------
EDGE_MARGIN = TILE * 2

def entry_point(edge, cross=None):
    """Entry (x, y) for a hero coming in through `edge`. If `cross` is given,
    preserve the cross-axis position so an edge transition near a corner
    re-enters near the same point instead of jumping to the edge midpoint."""
    if edge in ("left", "right"):
        x = EDGE_MARGIN if edge == "left" else MAP_W - EDGE_MARGIN
        y = cross if cross is not None else MAP_H // 2
        y = max(EDGE_MARGIN, min(MAP_H - EDGE_MARGIN, y))
        return (x, y)
    if edge in ("top", "bottom"):
        y = EDGE_MARGIN if edge == "top" else MAP_H - EDGE_MARGIN
        x = cross if cross is not None else MAP_W // 2
        x = max(EDGE_MARGIN, min(MAP_W - EDGE_MARGIN, x))
        return (x, y)
    return (MAP_W // 2, MAP_H // 2)


# ---------------------------------------------------------------------------
# Cell id helpers (for save/load + teleport discovery)
# ---------------------------------------------------------------------------
def cell_id(c, r):
    return f"{c},{r}"


def parse_cell_id(s):
    a, b = s.split(",")
    return int(a), int(b)
