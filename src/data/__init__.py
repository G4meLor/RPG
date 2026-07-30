"""data package — Phase 1 shim. The un-split data.py lives in _legacy_data;
this re-exports its public names so `import src.data as D; D.X` works.
Phase 2 splits _legacy_data into the 18 per-concern modules and removes this shim."""
from src.data._legacy_data import *  # noqa: F401,F403
# explicit re-export of names not covered by __all__ (the legacy module has no __all__)
from src.data._legacy_data import (  # noqa: F401
    ASSET_DIR, CHART, RESIST, WEAKNESS_FOR, element_mult, champion_enemy_def,
    REACTIONS, REACTION_WINDOW, WET_EFFECT, reaction_for, ELEMENT_COLORS, PIXEL,
    PIXEL_PALETTE, COLORBLIND_PALETTES, RARITY_COLORS, BASE_CRIT_CHANCE,
    COMBO_BONUS_PER, COMBO_MAX, COMBO_MILESTONE_SKILL, COMBO_MILESTONE_ULT,
    DEFEND_MITIGATION, AA_RANGE, AA_CD, NG_PLUS_LEVEL_BONUS, ADVENTURE_WAVE_INTERVAL,
    ADVENTURE_BOSS_TIME, ADVENTURE_STAGE_LEVEL_STEP, ADVENTURE_STAGE_TIME_LIMIT,
    ENERGY_MAX, ENERGY_START, ENERGY_COST_MULT, ENERGY_GAIN_BASIC, ENERGY_GAIN_DEAL,
    ENERGY_REGEN_PCT, skill_energy_cost, PASSIVES_DB, ELEMENTAL_RESONANCE,
    team_resonances, hero_abilities, EVO_TREE, EVO_TREE_DEFAULT, hero_evo_tree,
    EVO_NODE_POS, EVO_LINKS, evo_node_prereq_met, TOUGHNESS_BREAK_MULT,
    TOUGHNESS_BREAK_DAMAGE, TOUGHNESS_RECOVER_FRAC, SKILLS_DB, BOSS_ULT, BOSS_IDS,
    BOSS_PATTERNS, BOSS_PATTERNS_DEFAULT, boss_patterns, ROLES, role_mult, HEROES_DB,
    HERO_BY_ID, HERO_PASSIVES, hero_passive, HERO_SIGNATURE, hero_signature,
    ULTIMATE_VARIANTS, HERO_LORE, ENEMIES_DB, GACHA_RATES, GACHA_POOL, GACHA_COST,
    GACHA_BANNERS, GACHA_BANNER_BY_ID, GACHA_PITY_HARD, GACHA_PITY_SOFT,
    GACHA_SR_GUARANTEE_EVERY, GACHA_DUPE_GEM_REFUND, MAX_ASCENSION, ASCENSION_BONUS,
    CONSTELLATION_PERKS, CONSTELLATION_PERK_OVERRIDES, hero_constellation_perks,
    constellation_perks_for, _SKILL_CATEGORY, _HERO_SKILL_TEXT, _build_hero_assets,
    HERO_ASSETS, MAX_EVOLVE, EVOLVE_COST, EVOLVE_BONUS, EVOLVE_TITLES, EVOLVE_COLORS,
    EQUIPMENT_DB, EQUIPMENT_SETS, equipment_set_bonus, CONSUMABLES_DB, SHOP_GEMS,
    STARTING_GEMS, STARTING_GOLD, STARTING_TEAM, STARTING_OWNED, STARTING_INVENTORY,
    xp_to_next, STAT_GROWTH, MAX_LEVEL, ACHIEVEMENTS, DAILY_QUESTS, LORE_FRAGMENTS,
    LANDMARK_LORE, NPCS, STORY_QUESTS, STORY_QUEST_BY_ID, STORY_QUEST_ORDER,
    STORY_BIOME_QUEST, STORY_FINAL_QUEST,
    # underscore-prefixed names accessed externally (entities.py, world_scene.py,
    # world_entities.py reach D._CH, D._get_champion_enemy_pool). Without these
    # the star-import drops them and the game's champion-as-enemy feature breaks.
    _CH, _get_champion_enemy_pool, _CHAMPION_ENEMY_POOL, _CHAMPION_BOSS_POOL,
)
