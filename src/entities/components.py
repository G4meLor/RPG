"""ECS components — lightweight dataclass data bags (slots, no logic)."""
from dataclasses import dataclass, field

@dataclass(slots=True)
class Transform:
    x: float; y: float
    vx: float = 0.0; vy: float = 0.0
    r: float = 26.0

@dataclass(slots=True)
class Health:
    hp: float; max_hp: float
    energy: float; max_energy: float

@dataclass(slots=True)
class Combat:
    element: str
    atk: float; defn: float; spd: float
    atk_cd: float = 0.0
    stat_obj: object = None

@dataclass(slots=True)
class AI:
    kind: str
    state: str = "idle"
    target: int = -1
    aggro_t: float = 0.0

@dataclass(slots=True)
class Render:
    sprite_id: str
    weapon: str
    facing: int = 1
    anim_t: float = 0.0

@dataclass(slots=True)
class Identity:
    eid: int
    name: str
    is_hero: bool
    is_boss: bool = False

@dataclass(slots=True)
class Statuses:
    effects: list = field(default_factory=list)  # [StatusEffect]

@dataclass(slots=True)
class ChampionRef:
    hero_id: str
    skin: int = 0
    level: int = 1
    ascension: int = 0

@dataclass(slots=True)
class Movement:
    """Movement state for PhysicsSystem (Phase 4, Task 15). Mirrors the
    movement fields on the legacy `WorldCharacter` so the PhysicsSystem can
    read/write them via the entity instead of via the legacy object.

    Defaults match `WorldCharacter.__init__` (max_speed=230, accel=2400,
    friction=1800, r=20). The dash/knockback/click-to-move state lives here
    too (the legacy object's equivalents stay the source of truth this task;
    the entity's copy is the parallel-prove path)."""
    # facing direction (1 right, -1 left)
    facing: int = 1
    # collision radius (matches WorldCharacter.r=20 for heroes; spawn_enemy
    # sets r=40 for bosses via the constructor)
    r: float = 20.0
    # normal movement (LoL-style accel/friction)
    max_speed: float = 230.0
    accel: float = 2400.0
    friction: float = 1800.0
    moving: bool = False
    # dash (LoL-style shift-dash)
    dash_cd: float = 0.0
    dash_t: float = 0.0
    iframes: float = 0.0
    dash_dir: tuple = (0.0, 0.0)
    # knockback
    kb_x: float = 0.0
    kb_y: float = 0.0
    # LoL-style click-to-move (RMB-set auto-walk target)
    move_target: object = None        # (x, y) or None
    move_target_t: float = 0.0        # age of the current move_target
    _last_mt_dist: float = 0.0        # last distance to target (stall detection)
    _mt_stall_t: float = 0.0          # time the auto-walk has stalled
