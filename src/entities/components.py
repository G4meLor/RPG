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
