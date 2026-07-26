"""
Aetheria Open World - World Data
10x5 grid of maps, biomes, deterministic per-cell generation, the teleport
graph (neighbor links), and difficulty scaling. All static so it is cheap.
"""
import random

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
    "cave":    dict(name="Crystal Caverns",  ground=( 56, 54, 78),  ground2=( 46, 44, 66),
                    obstacle=( 80, 78, 110), accent=(140, 200, 255), sky=( 30, 28, 44),
                    fog=( 60, 60, 100)),
    "castle":  dict(name="Ruined Citadel",   ground=( 90, 84, 92),  ground2=( 76, 70, 80),
                    obstacle=(140, 132, 150), accent=(230, 220, 200), sky=( 80, 76, 96),
                    fog=(120, 110, 130)),
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


def cell_level(c, r):
    """Enemy level for cell (c, r). Bosses add a flat bonus."""
    return 1 + r * 6 + int(c * 1.5)


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

    # scattered obstacles (skip the boss arena center for a fight space)
    # denser in forest, sparser in plains, more pillars in castle/cave
    base_n = {"plains": (6, 10), "forest": (14, 20), "cave": (10, 16),
              "castle": (10, 16), "void": (8, 14)}.get(biome, (8, 14))
    n_obs = 0 if is_boss else rng.randint(*base_n)
    placed = 0
    tries = 0
    cx_mid, cy_mid = MAP_W // 2, MAP_H // 2
    kind_pool = {"plains": ["tree", "bush", "rock"],
                 "forest": ["tree", "tree", "bush"],
                 "cave":   ["rock", "rock", "pillar"],
                 "castle": ["pillar", "pillar", "rock"],
                 "void":   ["pillar", "rock", "pillar"]}.get(biome, ["rock"])
    # a spatial grid (tile buckets) for fast overlap checks instead of scanning
    # every existing obstacle per candidate — the #1 cost in gen_map.
    grid = {}
    def _near(x, y):
        gx, gy = x // TILE, y // TILE
        for ny in (gy - 1, gy, gy + 1):
            for nx in (gx - 1, gx, gx + 1):
                for o in grid.get((nx, ny), ()):
                    if abs(x - o.x) < TILE and abs(y - o.y) < TILE:
                        return True
        return False
    while placed < n_obs and tries < 200:
        tries += 1
        tx = rng.randint(3, MAP_TW - 4)
        ty = rng.randint(3, MAP_TH - 4)
        x, y = tx * TILE, ty * TILE
        # keep a clear corridor through the center
        if abs(x - cx_mid) < TILE * 3 and abs(y - cy_mid) < TILE * 3:
            continue
        # avoid stacking exactly (spatial-grid lookup, O(1) amortized)
        if _near(x, y):
            continue
        w = h = TILE
        kind = rng.choice(kind_pool)
        size = rng.randint(28, 40)
        o = pygame_rect(x, y, w, h)
        obstacles.append(o)
        grid.setdefault((x // TILE, y // TILE), []).append(o)
        deco.append((x + TILE // 2, y + TILE // 2, kind, size))
        placed += 1

    # enemy spawns
    spawns = []
    if not is_boss:
        n_enemies = min(14, 4 + r * 2 + rng.randint(0, 3))
        for _ in range(n_enemies):
            for _try in range(30):
                tx = rng.randint(3, MAP_TW - 4)
                ty = rng.randint(3, MAP_TH - 4)
                x, y = tx * TILE, ty * TILE
                if _free_grid(x, y, grid) and _dist(x, y, cx_mid, cy_mid) > TILE * 4:
                    spawns.append((x, y))
                    break
    # boss spawn - centered, with a little arena ring of pillars
    boss = None
    if is_boss:
        boss = (cx_mid, cy_mid - TILE)
        import math
        for ang in range(0, 360, 45):
            ax = cx_mid + int(math.cos(math.radians(ang)) * TILE * 5)
            ay = cy_mid + int(math.sin(math.radians(ang)) * TILE * 5)
            if TILE < ax < MAP_W - TILE * 2 and TILE < ay < MAP_H - TILE * 2:
                o = pygame_rect(ax, ay, TILE, TILE)
                obstacles.append(o)
                grid.setdefault((ax // TILE, ay // TILE), []).append(o)
                deco.append((ax + TILE // 2, ay + TILE // 2, "pillar", 42))

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

    return dict(obstacles=obstacles, deco=deco, spawns=spawns, boss=boss,
                is_boss=is_boss, biome=biome, pal=pal, chests=chests)


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

def entry_point(edge):
    if edge == "left":    return (EDGE_MARGIN, MAP_H // 2)
    if edge == "right":   return (MAP_W - EDGE_MARGIN, MAP_H // 2)
    if edge == "top":     return (MAP_W // 2, EDGE_MARGIN)
    if edge == "bottom":  return (MAP_W // 2, MAP_H - EDGE_MARGIN)
    return (MAP_W // 2, MAP_H // 2)


# ---------------------------------------------------------------------------
# Cell id helpers (for save/load + teleport discovery)
# ---------------------------------------------------------------------------
def cell_id(c, r):
    return f"{c},{r}"


def parse_cell_id(s):
    a, b = s.split(",")
    return int(a), int(b)
