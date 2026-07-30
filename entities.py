"""Shim — real module at src.entities._legacy_entities. Removed in Phase 5."""
from src.entities._legacy_entities import (  # noqa: F401
    Hero, Enemy, Combatant, StatusEffect, load_image, load_char_sprite,
    load_portrait, load_champ_icon, load_enemy_sprite, load_skill_icon, load_bg,
    load_ui, load_item_icon, load_terrain, load_landmark, load_village, load_drop,
)
