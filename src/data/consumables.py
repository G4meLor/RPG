"""Consumables (inventory items).

Mechanically split from _legacy_data.py — body copied verbatim.
"""

__all__ = ["CONSUMABLES_DB"]

# ---------------------------------------------------------------------------
# Consumables (inventory items)
# ---------------------------------------------------------------------------
CONSUMABLES_DB = {
    "hp_potion":    dict(name="HP Potion",     type="heal_hp",   power=60,  price=40,  sell=8,  desc="Restore 60 HP to one hero."),
    "mp_potion":    dict(name="MP Potion",     type="heal_mp",   power=40,  price=30,  sell=10, desc="Restore 40 MP to one hero."),
    "full_elixir":  dict(name="Full Elixir",   type="heal_full", power=0,   price=200, sell=40, desc="Fully restore HP & MP of one hero."),
    "revive_scroll":dict(name="Revive Scroll", type="revive",    power=0.5, price=300, sell=60, desc="Revive a fallen ally at 50% HP."),
    "bomb":         dict(name="Bomb",          type="damage",    power=80,  price=80,  sell=16, desc="Deal 80 damage to one enemy."),
    # --- new consumables (Phase B) ---
    "mega_potion":  dict(name="Mega Potion",   type="heal_hp",   power=200, price=100, sell=24, desc="Restore 200 HP to one hero."),
    "ether":        dict(name="Ether",         type="heal_mp",   power=80,  price=120, sell=28, desc="Restore 80 MP to one hero."),
    "mega_bomb":    dict(name="Mega Bomb",     type="damage",    power=240, price=220, sell=44, desc="Deal 240 damage to one enemy."),
}
