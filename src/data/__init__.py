"""data package — per-concern modules. Public API re-exported here so
`from src.data import SKILLS_DB` works. The root data.py shim is removed and
all call sites now import from the per-concern modules directly.

Mechanically split from _legacy_data.py in Phase 2 of the ECS restructure.
"""
from src.data.tuning import *  # noqa: F401,F403
from src.data.elements import *  # noqa: F401,F403
from src.data.roles import *  # noqa: F401,F403
from src.data.passives import *  # noqa: F401,F403
from src.data.shop import *  # noqa: F401,F403
from src.data.consumables import *  # noqa: F401,F403
from src.data.skills import *  # noqa: F401,F403
from src.data.evolution import *  # noqa: F401,F403
from src.data.constellation import *  # noqa: F401,F403
from src.data.equipment import *  # noqa: F401,F403
from src.data.resonance import *  # noqa: F401,F403
from src.data.enemies import *  # noqa: F401,F403
from src.data.progression import *  # noqa: F401,F403
from src.data.story import *  # noqa: F401,F403
from src.data.heroes import *  # noqa: F401,F403
from src.data.gacha_data import *  # noqa: F401,F403

# Explicit re-export of the underscore-prefixed names accessed externally
# (entities.py, world_scene.py, world_entities.py reach _CH,
# _get_champion_enemy_pool, _CHAMPION_ENEMY_POOL, _CHAMPION_BOSS_POOL).
# The star-imports above cover these via __all__, but keep the explicit block
# as a safety net so a missing __all__ entry can never break the game's
# champion-as-enemy feature.
from src.data.heroes import (  # noqa: F401
    _CH, _get_champion_enemy_pool, _CHAMPION_ENEMY_POOL, _CHAMPION_BOSS_POOL,
    _build_hero_assets, _HERO_SKILL_TEXT, _SKILL_CATEGORY,
    _PASSIVE_BY_ROLE, _PASSIVE_OVERRIDE, _SIGNATURE_BY_ROLE,
    _SIGNATURE_OVERRIDE, _ULT_BY_ROLE, _ULT_OVERRIDE,
)
from src.data.skills import _SKILL_TYPE_CATEGORY  # noqa: F401
