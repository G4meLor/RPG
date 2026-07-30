"""ui package — shared UI primitives, colors, widgets."""
from src.ui.primitives import *  # noqa: F401,F403
from src.ui.primitives import (WIDTH, HEIGHT, FPS, TITLE, SEED, FONTS, init_fonts,  # noqa: F401
    get_font, f, text, Button, draw_panel, draw_bar, draw_stars, dim_overlay, scratch,
    _TEXT_CACHE, _TEXT_CACHE_CAP, _DIM_CACHE)
from src.ui.colors import (WHITE, DIM, GOLD, PANEL, PANEL_BORDER, HP_RED, HP_GREEN,  # noqa: F401
    MP_BLUE, XP_PURPLE, BG_DARK, element_color, rarity_color)
from src.ui.widgets import Toggle, Slider  # noqa: F401
