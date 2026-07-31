"""Equipment DB, equipment set bonuses, set-bonus lookup.

Mechanically split from _legacy_data.py — bodies copied verbatim.
"""

__all__ = ["EQUIPMENT_DB", "EQUIPMENT_SETS", "equipment_set_bonus"]

# ---------------------------------------------------------------------------
# Equipment
#   slot: weapon, armor, accessory
#   stat bonuses added to hero base stats
# ---------------------------------------------------------------------------
EQUIPMENT_DB = {
    # weapons -> atk
    "rusty_sword":  dict(name="Rusty Sword",   slot="weapon",    rarity="R",  stats=dict(atk=6),  price=120, sell=40),
    "steel_blade":  dict(name="Steel Blade",   slot="weapon",    rarity="SR", stats=dict(atk=14), price=400, sell=140),
    "dragon_fang":  dict(name="Dragon Fang",   slot="weapon",    rarity="SSR",stats=dict(atk=24), price=1800, sell=480),
    "mage_rod":     dict(name="Mage Rod",      slot="weapon",    rarity="SR", stats=dict(atk=10, mp=10), price=450, sell=160),
    # armor -> hp, defn
    "leather_armor":dict(name="Leather Armor", slot="armor",     rarity="R",  stats=dict(hp=20, defn=4), price=120, sell=40),
    "plate_mail":   dict(name="Plate Mail",    slot="armor",     rarity="SR", stats=dict(hp=40, defn=10), price=420, sell=150),
    "aether_vest":  dict(name="Aether Vest",   slot="armor",     rarity="SSR",stats=dict(hp=70, defn=18), price=1900, sell=520),
    # accessory -> spd / mp / misc
    "swift_boots":  dict(name="Swift Boots",   slot="accessory", rarity="R",  stats=dict(spd=4), price=120, sell=40),
    "mana_pendant": dict(name="Mana Pendant",  slot="accessory", rarity="SR", stats=dict(mp=14, atk=4), price=440, sell=160),
    "hero_crest":   dict(name="Hero Crest",    slot="accessory", rarity="SSR",stats=dict(spd=5, atk=8, hp=30), price=2000, sell=560),
    # --- new equipment (Phase B) ---
    "inferno_blade":dict(name="Inferno Blade", slot="weapon",    rarity="SSR",stats=dict(atk=28, hp=20), price=2400, sell=640),
    "frost_staff":  dict(name="Frost Staff",   slot="weapon",    rarity="SR", stats=dict(atk=12, mp=12), price=480, sell=170),
    "void_blade":   dict(name="Void Blade",    slot="weapon",    rarity="SSR",stats=dict(atk=26, spd=4), price=2200, sell=600),
    "guardian_aegis":dict(name="Guardian Aegis",slot="armor",    rarity="SSR",stats=dict(hp=90, defn=22), price=2500, sell=680),
    "shadow_cloak": dict(name="Shadow Cloak",  slot="armor",     rarity="SR", stats=dict(hp=30, defn=12, spd=3), price=520, sell=190),
    "berserker_ring":dict(name="Berserker Ring",slot="accessory",rarity="SR", stats=dict(atk=10, spd=3), price=560, sell=200),
    "sage_amulet":  dict(name="Sage Amulet",   slot="accessory", rarity="SSR",stats=dict(mp=20, atk=6, hp=40), price=2500, sell=680),
}

# Equipment set bonuses: equip a matching set across the 3 slots for a bonus.
# A "set" is keyed by a prefix on the item id. Bonuses stack onto the hero.
EQUIPMENT_SETS = {
    "ember":  dict(name="Ember Warden",  items=("inferno_blade", "aether_vest", "berserker_ring"),
                  bonus=dict(atk_pct=0.10, hp=30, crit_dmg=0.15), desc="+10% ATK, +30 HP, +15% crit dmg",
                  bonus2=dict(atk_pct=0.05)),
    "frost":  dict(name="Aegis Sovereign", items=("frost_staff", "guardian_aegis", "sage_amulet"),
                  bonus=dict(defn_pct=0.12, hp=60), desc="+12% DEF, +60 HP",
                  bonus2=dict(defn_pct=0.05)),
    "void":   dict(name="Voidwalker",   items=("void_blade", "shadow_cloak", "mana_pendant"),
                  bonus=dict(atk_pct=0.06, crit=0.10, crit_dmg=0.20), desc="+6% ATK, +10% crit, +20% crit dmg",
                  bonus2=dict(atk_pct=0.03)),
    "hero":   dict(name="Hero's Valor", items=("dragon_fang", "plate_mail", "hero_crest"),
                  bonus=dict(atk_pct=0.06, hp=40, defn=8), desc="+6% ATK, +40 HP, +8 DEF",
                  bonus2=dict(hp=20)),
}

def equipment_set_bonus(equipped_ids):
    """Return (set_name, bonus_dict) for a complete set (3/3) or a 2-piece
    partial bonus, or (None, {})."""
    eqset = set(equipped_ids)
    for sid, sdef in EQUIPMENT_SETS.items():
        items = set(sdef["items"])
        if items.issubset(eqset):
            return sdef["name"], dict(sdef["bonus"])
        if len(items & eqset) >= 2 and sdef.get("bonus2"):
            return sdef["name"] + " (2/3)", dict(sdef["bonus2"])
    return None, {}
