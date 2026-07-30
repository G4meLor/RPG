"""Shim — real module at src.data (kept for legacy `import data as D`).
Re-exports ALL public + externally-accessed private names so `D.X` and
`D._CH` / `D._get_champion_enemy_pool()` keep working unchanged. Removed in Phase 5."""
from src.data import *  # noqa: F401,F403
from src.data import (  # noqa: F401
    _CH, _get_champion_enemy_pool, _CHAMPION_ENEMY_POOL, _CHAMPION_BOSS_POOL,
)
