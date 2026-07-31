"""Enemy definitions — LoL jungle mobs + villain bosses.

Mechanically split from _legacy_data.py — body copied verbatim.
"""

__all__ = ["ENEMIES_DB"]

# ---------------------------------------------------------------------------
# Enemy definitions
# ---------------------------------------------------------------------------
ENEMIES_DB = {
    # --- LoL jungle mobs (open-world trash) ---
    "Razorbeaks":  dict(name="Razorbeak",    element="wind",   hp=60,  atk=14, defn=6,  spd=8,  xp=20, gold=15,
                        skills=["basic_attack"], weakness="fire", toughness=40),
    "Krugs":       dict(name="Krugs",        element="fire",   hp=80,  atk=18, defn=8,  spd=11, xp=28, gold=22,
                        skills=["basic_attack", "fire_bolt"], weakness="water", toughness=50),
    "MurkWolves":  dict(name="Murk Wolf",    element="wind",   hp=100, atk=22, defn=9,  spd=15, xp=36, gold=30,
                        skills=["basic_attack", "wind_arrow"], weakness="fire", toughness=60),
    "Raptors":     dict(name="Raptor",       element="fire",   hp=70,  atk=20, defn=6,  spd=14, xp=30, gold=24,
                        skills=["basic_attack", "fire_bolt"], weakness="water", toughness=45),
    "Gromp":       dict(name="Gromp",        element="water",  hp=90,  atk=20, defn=10, spd=9,  xp=32, gold=26,
                        skills=["basic_attack", "water_bolt"], weakness="wind", toughness=55),
    "Voidlings":   dict(name="Voidling",     element="dark",   hp=55,  atk=16, defn=5,  spd=16, xp=24, gold=18,
                        skills=["basic_attack", "dark_bolt"], weakness="light", toughness=35),
    "Wraiths":     dict(name="Wraith",       element="dark",   hp=120, atk=28, defn=12, spd=14, xp=55, gold=45,
                        skills=["basic_attack", "dark_bolt", "dark_curse"], weakness="light", toughness=70),
    "CrimsonRaptor": dict(name="Crimson Raptor", element="fire", hp=140, atk=26, defn=14, spd=8,  xp=48, gold=40,
                        skills=["basic_attack", "fire_slash"], weakness="water", toughness=80),
    "VoidHound":   dict(name="Void Hound",   element="dark",   hp=110, atk=24, defn=10, spd=12, xp=40, gold=32,
                        skills=["basic_attack", "dark_bolt"], weakness="light", toughness=65),
    "FallenKnight":dict(name="Fallen Knight",element="light",  hp=160, atk=26, defn=18, spd=10, xp=60, gold=48,
                        skills=["basic_attack", "light_slash"], weakness="dark", toughness=90),
    # --- LoL villain bosses (the open-world arena fights) ---
    "Sylas":       dict(name="Sylas",        element="dark",   hp=340, atk=34, defn=20, spd=12, xp=120, gold=120,
                        skills=["basic_attack", "dark_bolt", "dark_aoe"], weakness="light", toughness=160),
    "Swain":       dict(name="Swain",        element="fire",   hp=380, atk=36, defn=22, spd=11, xp=160, gold=160,
                        skills=["basic_attack", "fire_bolt", "inferno"], weakness="water", toughness=180),
    "Lissandra":   dict(name="Lissandra",    element="water",  hp=440, atk=36, defn=26, spd=10, xp=260, gold=260,
                        skills=["basic_attack", "water_bolt", "frost_nova"], weakness="fire", toughness=200),
    "Mordekaiser": dict(name="Mordekaiser",  element="dark",   hp=520, atk=38, defn=24, spd=13, xp=300, gold=300,
                        skills=["basic_attack", "dark_bolt", "dark_aoe", "dark_curse"], weakness="light", toughness=220),
    "Viego":       dict(name="Viego",        element="dark",   hp=460, atk=40, defn=22, spd=15, xp=280, gold=280,
                        skills=["basic_attack", "dark_bolt", "dark_aoe"], weakness="light", toughness=210),
    "Baron":       dict(name="Baron Nashor", element="dark",   hp=620, atk=42, defn=26, spd=14, xp=360, gold=360,
                        skills=["basic_attack", "fire_bolt", "inferno", "fire_slash"], weakness="light", toughness=260),
}
