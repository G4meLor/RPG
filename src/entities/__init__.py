"""entities package — re-exports _legacy_entities + _legacy_world_entities.

_legacy_entities is imported eagerly (it only depends on data, no cycle).
_legacy_world_entities now imports Hero/Enemy/load_char_sprite/load_enemy_sprite
directly from src.entities._legacy_entities (the sibling module), so the
former circular import via the root `entities` shim is gone — both modules
can be eagerly imported here.
"""
from src.entities._legacy_entities import *  # noqa: F401,F403
from src.entities._legacy_entities import (  # noqa: F401
    Hero, Enemy, Combatant, StatusEffect, load_image, load_char_sprite,
    load_portrait, load_champ_icon, load_enemy_sprite, load_skill_icon, load_bg,
    load_ui, load_item_icon, load_terrain, load_landmark, load_village, load_drop,
)
from src.entities._legacy_world_entities import (  # noqa: F401
    Camera, Particle, Particles, Projectile, FloatText,
    WorldCharacter, WorldEnemy, SummonAlly, Trap, WEAPON_STYLE, scratch,
)
