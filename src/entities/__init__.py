"""entities package — Phase 1 shim re-exporting _legacy_entities + _legacy_world_entities.

_legacy_entities is imported eagerly (it only depends on data, no cycle).
_legacy_world_entities is exposed lazily via __getattr__ because it does
`from entities import Hero, ...` (the root shim) — eagerly importing it here
would create a cycle when `entities` (root) is the first entry point:
entities(root) -> src.entities.__init__ -> _legacy_world_entities ->
`from entities import Hero` -> entities(root) mid-init -> ImportError.
Lazy access lets `entities` (root) finish initializing first.
"""
from src.entities._legacy_entities import *  # noqa: F401,F403
from src.entities._legacy_entities import (  # noqa: F401
    Hero, Enemy, Combatant, StatusEffect, load_image, load_char_sprite,
    load_portrait, load_champ_icon, load_enemy_sprite, load_skill_icon, load_bg,
    load_ui, load_item_icon, load_terrain, load_landmark, load_village, load_drop,
)

# world_entities names — lazily resolved to avoid the circular import described
# above. `from src.entities import Camera` triggers __getattr__('Camera'),
# which imports _legacy_world_entities (by then `entities` root shim is fully
# loaded, so its `from entities import Hero` resolves cleanly).
_WORLD_ENTITIES_NAMES = (
    "Camera", "Particle", "Particles", "Projectile", "FloatText",
    "WorldCharacter", "WorldEnemy", "SummonAlly", "Trap", "WEAPON_STYLE", "scratch",
)


def __getattr__(name):
    if name in _WORLD_ENTITIES_NAMES:
        from src.entities import _legacy_world_entities as _we
        return getattr(_we, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    from src.entities import _legacy_world_entities as _we
    return dir(_we) + list(_WORLD_ENTITIES_NAMES)
