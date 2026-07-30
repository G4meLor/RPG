"""entities package — re-exports combatant (Combatant/Hero/Enemy + loaders) +
_legacy_world_entities (Camera, WorldEnemy, ...).

combatant.py is the renamed _legacy_entities.py (Task 11). It is imported
eagerly (it only depends on data, no cycle). _legacy_world_entities imports
Hero/Enemy/load_char_sprite/load_enemy_sprite directly from
src.entities.combatant (the sibling module), so both modules can be eagerly
imported here.
"""
from src.entities.combatant import *  # noqa: F401,F403
from src.entities.combatant import (  # noqa: F401
    Hero, Enemy, Combatant, StatusEffect, load_image, load_char_sprite,
    load_portrait, load_champ_icon, load_enemy_sprite, load_skill_icon, load_bg,
    load_ui, load_item_icon, load_terrain, load_landmark, load_village, load_drop,
)
from src.entities.hero import spawn_hero  # noqa: F401
from src.entities.enemy import spawn_enemy  # noqa: F401
from src.entities._legacy_world_entities import (  # noqa: F401
    Camera, Particle, Particles, Projectile, FloatText,
    WorldCharacter, WorldEnemy, SummonAlly, Trap, WEAPON_STYLE, scratch,
)
