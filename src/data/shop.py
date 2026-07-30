"""Shop offers (gems for gold, equipment, consumables).

Mechanically split from _legacy_data.py — body copied verbatim.
"""

__all__ = ["SHOP_GEMS"]

# ---------------------------------------------------------------------------
# Shop offers (gems for gold, equipment, consumables)
# ---------------------------------------------------------------------------
SHOP_GEMS = [
    dict(id="gems_small",  name="100 Gems",  gems=100,  price=800),
    dict(id="gems_medium", name="600 Gems",  gems=600,  price=4200),
    dict(id="gems_large",  name="1500 Gems", gems=1500, price=9500),
]
