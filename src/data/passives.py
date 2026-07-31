"""Passive definitions — always-on combat modifiers keyed by id.

Mechanically split from _legacy_data.py — body copied verbatim.
"""

__all__ = ["PASSIVES_DB"]

# passive definitions — always-on combat modifiers, keyed by id.
#   kind values handled in world_scene combat:
#     lifesteal   - heal a fraction of damage dealt by basic attacks
#     thorns      - reflect a fraction of melee damage taken
#     crit_up     - +bonus crit chance
#     energy_gen  - +bonus energy on dealing damage
#     swift       - +move speed
#     regen       - slow HP regen out of combat
#     adrenaline  - +ATK when HP is low
#     shield_when_low - gain a shield when HP drops below 30%
#     heal_amp   - healing skills heal a fraction more
PASSIVES_DB = {
    "p_lifesteal": dict(name="Vampiric Touch", desc="Heal for 12% of basic-attack damage.",
                        kind="lifesteal", val=0.12),
    "p_thorns":    dict(name="Bramble Mail", desc="Reflect 20% of melee damage taken.",
                        kind="thorns", val=0.20),
    "p_crit":      dict(name="Keen Eye", desc="+10% critical strike chance.",
                        kind="crit_up", val=0.10),
    "p_energy":    dict(name="Flow State", desc="+50% energy gain on hit.",
                        kind="energy_gen", val=0.5),
    "p_swift":     dict(name="Fleet Footed", desc="+15% movement speed.",
                        kind="swift", val=0.15),
    "p_regen":     dict(name="Mending Aura", desc="Regen 2% HP/sec out of combat.",
                        kind="regen", val=0.02),
    "p_adrenaline":dict(name="Last Stand", desc="+30% ATK while below 35% HP.",
                        kind="adrenaline", val=0.30),
    "p_shield_low":dict(name="Guardian Spirit", desc="Gain a shield at low HP.",
                        kind="shield_when_low", val=0.25),
    "p_heal_amp":   dict(name="Mercy", desc="Healing skills heal 25% more.",
                        kind="heal_amp", val=0.25),
    # --- per-hero signature passives (C6) — layered on top of HERO_PASSIVES.
    # Each of the 25 heroes gets ONE signature id (see HERO_SIGNATURE). Heroes
    # sharing a kind reuse the same id; the per-hero flavor is the name/desc.
    # The signature is ADDITIONAL to the shared base passive — handlers in
    # world_entities/world_scene check the signature in addition to
    # self.hero.passive, not instead of it. Dispatch is a dict-lookup per hook
    # point (kind -> handler), NOT an if/elif chain.
    #   kind values handled in world_entities/world_scene:
    #     revive_once    - revive at val HP on death, once per combat (reset in _build_party)
    #     stacking_atk   - +val ATK per kill (stacking), decays out of combat
    #     shield_on_hit  - gain a shield when damaged (after the hit)
    #     low_hp_frenzy  - +val ATK & +20% SPD below 30% HP
    #     cleave         - basic attacks splash to enemies within 60px of the primary target
    "s_aria_frenzy":   dict(name="Dawn's Wrath",        desc="+25% ATK & SPD below 30% HP.",            kind="low_hp_frenzy",  val=0.25),
    "s_kael_cleave":   dict(name="Sweeping Strike",     desc="Basic attacks splash to nearby enemies.",  kind="cleave",         val=0.5),
    "s_luna_revive":   dict(name="Dark Pact",           desc="Revive once at 40% HP on death.",          kind="revive_once",    val=0.4),
    "s_zephyr_stack":  dict(name="Momentum",           desc="+5% ATK per kill (stacking).",             kind="stacking_atk",   val=0.05),
    "s_mira_shield":   dict(name="Tide Ward",          desc="Gain a shield when damaged.",              kind="shield_on_hit",  val=0.15),
}
