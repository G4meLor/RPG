"""Gacha pool, rates, cost, banners + banner-by-id lookup.

Mechanically split from _legacy_data.py — bodies copied verbatim.
"""
from src.data.heroes import HEROES_DB, HERO_BY_ID  # noqa: F401 (pool derivation source)

__all__ = [
    "GACHA_RATES", "GACHA_POOL", "GACHA_COST",
    "GACHA_BANNERS", "GACHA_BANNER_BY_ID",
]

# ---------------------------------------------------------------------------
# Gacha pool
# ---------------------------------------------------------------------------
GACHA_RATES = {"SSR": 0.06, "SR": 0.34, "R": 0.60}
# Gacha pool — auto-derived from HEROES_DB grouped by rarity. Every champ
# is in exactly one rarity bucket so random.choice never hits an empty pool.
GACHA_POOL = {
    'SSR': ['Ahri', 'Akali', 'Akshan', 'Anivia', 'Aphelios', 'Ashe', 'AurelionSol', 'Azir', 'Bard', 'Brand', 'Camille', 'Cassiopeia', 'Darius', 'Draven', 'Ekko', 'Ezreal', 'Gangplank', 'Garen', 'Gnar', 'Hwei', 'Irelia', 'Ivern', 'Jhin', 'Jinx', 'KSante', 'Kaisa', 'Kalista', 'Katarina', 'Kindred', 'LeeSin', 'Lillia', 'Lissandra', 'Lux', 'Mordekaiser', 'Nilah', 'Ornn', 'Pyke', 'Qiyana', 'Riven', 'Sett', 'Shaco', 'Swain', 'Sylas', 'Syndra', 'Teemo', 'Thresh', 'Veigar', 'Viego', 'Viktor', 'Volibear', 'Yasuo', 'Yone', 'Zed', 'Zoe'],
    'SR': ['Aatrox', 'Ambessa', 'Aurora', 'Belveth', 'Braum', 'Briar', 'Corki', 'Elise', 'Evelynn', 'Fiddlesticks', 'Fiora', 'Fizz', 'Galio', 'Gragas', 'Graves', 'Gwen', 'Hecarim', 'Heimerdinger', 'Illaoi', 'Jayce', 'Karthus', 'Kassadin', 'Kayle', 'Kayn', 'Kennen', 'Khazix', 'Kled', 'KogMaw', 'Leblanc', 'Lucian', 'Lulu', 'Mel', 'Nami', 'Nautilus', 'Nidalee', 'Orianna', 'Poppy', 'Quinn', 'Rakan', 'RekSai', 'Rell', 'Renata', 'Rengar', 'Rumble', 'Ryze', 'Samira', 'Sejuani', 'Senna', 'Shen', 'Singed', 'Sivir', 'Skarner', 'Smolder', 'Taliyah', 'Talon', 'Taric', 'TwistedFate', 'Twitch', 'Urgot', 'Varus', 'Vayne', 'Velkoz', 'Vex', 'Vladimir', 'Xayah', 'Xerath', 'Yorick', 'Zeri', 'Ziggs', 'Zilean', 'Zyra'],
    'R': ['Alistar', 'Amumu', 'Annie', 'Blitzcrank', 'Caitlyn', 'Chogath', 'Diana', 'DrMundo', 'Janna', 'JarvanIV', 'Jax', 'Karma', 'Leona', 'Malphite', 'Malzahar', 'Maokai', 'MasterYi', 'Milio', 'MissFortune', 'MonkeyKing', 'Morgana', 'Naafiri', 'Nasus', 'Neeko', 'Nocturne', 'Nunu', 'Olaf', 'Pantheon', 'Rammus', 'Renekton', 'Seraphine', 'Shyvana', 'Sion', 'Sona', 'Soraka', 'TahmKench', 'Tristana', 'Trundle', 'Tryndamere', 'Udyr', 'Vi', 'Warwick', 'XinZhao', 'Yuumi', 'Zac'],
}

GACHA_COST = dict(single=dict(gems=10, gold=0), multi=dict(gems=90, gold=0))

# --- Banners (multi-banner summoning) --------------------------------------
#   Standard: every champion, no rate-up. Featured banners: one per element,
#   each rate-ups an iconic SSR + SR of that element (50% of SSR pulls land
#   on the featured champ). Pity rules unchanged (per-banner pity counter).
GACHA_BANNERS = [
    dict(id="standard", name="Eternal Gate",
         desc="All champions. No rate-up.",
         pool=GACHA_POOL,
         featured_ssr=None, featured_sr=None,
         color=(120, 180, 255)),
    dict(id='fire', name='Crimson Pact',
         desc='Rate-up: Brand & Rumble (Fire).',
         pool={"SSR": ['Akshan', 'Azir', 'Brand', 'Cassiopeia', 'Darius', 'Draven', 'KSante', 'Katarina'],
               "SR":  ['Aatrox', 'Ambessa', 'Briar', 'Kled', 'Leblanc', 'Mel', 'Rell', 'Rumble'],
               "R":   ['Alistar', 'Amumu', 'Annie', 'Blitzcrank', 'Caitlyn', 'Chogath']},
         featured_ssr='Brand', featured_sr='Rumble',
         color=(255, 120, 90)),
    dict(id='water', name='Tidal Covenant',
         desc='Rate-up: Ashe & Braum (Water).',
         pool={"SSR": ['Anivia', 'Ashe', 'Gangplank', 'Gnar', 'Lissandra', 'Nilah', 'Ornn', 'Pyke'],
               "SR":  ['Aurora', 'Braum', 'Gragas', 'Graves', 'Illaoi', 'Nami', 'Nautilus', 'Sejuani'],
               "R":   ['Alistar', 'Amumu', 'Annie', 'Blitzcrank', 'Caitlyn', 'Chogath']},
         featured_ssr='Ashe', featured_sr='Braum',
         color=(90, 180, 255)),
    dict(id='wind', name='Tempest Call',
         desc='Rate-up: Yasuo & Janna (Wind).',
         pool={"SSR": ['Yasuo', 'Ahri', 'Akali', 'Hwei', 'Irelia', 'Ivern', 'Jhin', 'LeeSin', 'Lillia'],
               "SR":  ['Corki', 'Janna', 'Kayn', 'Kennen', 'Lulu', 'Nidalee', 'Quinn', 'Rakan'],
               "R":   ['Alistar', 'Amumu', 'Annie', 'Blitzcrank', 'Caitlyn', 'Chogath']},
         featured_ssr='Yasuo', featured_sr='Janna',
         color=(140, 230, 170)),
    dict(id='light', name='Dawn Covenant',
         desc='Rate-up: Lux & Sona (Light).',
         pool={"SSR": ['Aphelios', 'AurelionSol', 'Camille', 'Ezreal', 'Garen', 'Lux', 'Sylas', 'Zoe'],
               "SR":  ['Fiora', 'Galio', 'Heimerdinger', 'Jayce', 'Kayle', 'Orianna', 'Poppy', 'Sona'],
               "R":   ['Alistar', 'Amumu', 'Annie', 'Blitzcrank', 'Caitlyn', 'Chogath']},
         featured_ssr='Lux', featured_sr='Sona',
         color=(255, 220, 120)),
    dict(id='dark', name='Abyssal Veil',
         desc='Rate-up: Thresh & Pyke (Dark).',
         pool={"SSR": ['Thresh', 'Bard', 'Ekko', 'Jinx', 'Kaisa', 'Kalista', 'Kindred', 'Mordekaiser', 'Shaco'],
               "SR":  ['Pyke', 'Belveth', 'Elise', 'Evelynn', 'Fiddlesticks', 'Fizz', 'Gwen', 'Hecarim', 'Karthus'],
               "R":   ['Alistar', 'Amumu', 'Annie', 'Blitzcrank', 'Caitlyn', 'Chogath']},
         featured_ssr='Thresh', featured_sr='Pyke',
         color=(190, 120, 240)),
]
GACHA_BANNER_BY_ID = {b["id"]: b for b in GACHA_BANNERS}
