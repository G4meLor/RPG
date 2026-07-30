"""HudSystem (Phase 4, Task 19 of the ECS restructure) — HUD renderer.

Renders the HUD layer (skill bar + party + boss bar + minimap) to a surface,
reading entity ``Transform``/``Health``/``Identity``/``ChampionRef``
components + the player/party state. Runs IN PARALLEL with the legacy
``WorldScene._draw_hud``/``_draw_skill_bar``/``_draw_minimap`` (additive) —
the legacy HUD draw STAYS the source of truth this task; this system proves
it can render a HUD to a surface without raising. Full takeover (moving all
the ``_draw_hud``/``_draw_skill_bar``/``_draw_skill_tooltip``/
``_draw_minimap``/``_draw_boss_banner``/``_draw_ascend_banner``/
``_hud_portrait``/``_skill_icon`` methods verbatim into this system) is
Task 20.

The minimal gate (this task) is the brief's ``test_render_one_frame``:
``HudSystem.draw`` draws the active hero's name + an HP bar + an energy bar
using ``text`` + ``draw_bar`` from ``src.ui``. This proves the system can
render a HUD to a surface without raising — the faithful extraction of the
full HUD (party slot row, skill bar with cooldown overlays, minimap, boss
bar, ascend banner, portraits) is deferred to Task 20 so this task stays
minimal + low-risk.
"""
from src.entities.components import Transform, Identity, Health, ChampionRef
from src.ui.primitives import text, draw_bar


class HudSystem:
    """ECS HUD renderer — draws the HUD layer to a surface. The legacy
    ``WorldScene._draw_hud`` stays the source of truth this task; this
    system runs in parallel (additive) to prove the extraction works in
    isolation. Full takeover is Task 20.

    Parameters
    ----------
    world : World
        The ECS entity world (read for ``heroes()`` to find the active hero
        entity + its ``Health``/``Identity``/``ChampionRef``).
    scene : WorldScene or None
        The owning scene. Used to read ``scene.active`` / ``scene.party`` /
        ``scene._entity_for_hero`` to find the active hero entity, and
        ``scene.game.player`` for any player-level HUD state. May be None
        for headless tests (the draw falls back to the first hero entity).
    """

    def __init__(self, world, scene=None):
        self.world = world
        self.scene = scene

    def _active_hero_entity(self):
        """Find the active hero entity (the one the player controls).

        Mirrors the legacy ``wc = self.party[self.active]`` selection, but
        returns the ECS hero entity (so we can read its ``Health`` /
        ``Identity`` / ``ChampionRef`` for the HUD). Falls back to the first
        hero entity if the active slot has no entity. Returns None if there
        are no hero entities (so the draw is a no-op, never raises).
        """
        if self.scene is not None:
            idx = getattr(self.scene, "active", 0)
            party = getattr(self.scene, "party", [])
            hero_map = getattr(self.scene, "_entity_for_hero", {})
            if 0 <= idx < len(party) and party[idx] is not None:
                wc = party[idx]
                hid = wc.hero.id
                e = hero_map.get(hid)
                if e is not None:
                    return e
        heroes = self.world.heroes()
        return heroes[0] if heroes else None

    def draw(self, surf):
        """Render a minimal HUD to ``surf``.

        For the MINIMAL gate (this task): draw the active hero's name +
        an HP bar + an energy bar at the top-left, using ``text`` +
        ``draw_bar`` from ``src.ui``. Must NOT raise.

        The full HUD (party slot row, skill bar with cooldown overlays,
        minimap, boss bar, ascend banner, portraits) is deferred to Task 20
        — this minimal draw proves the system can render a HUD to a surface
        without raising.

        Args:
            surf: the destination pygame.Surface.
        """
        e = self._active_hero_entity()
        if e is None:
            return  # no hero entity — no-op (never raises)
        ident = e.get(Identity)
        hp = e.get(Health)
        ref = e.get(ChampionRef)
        name = ident.name if ident is not None else "Hero"
        # active hero name (top-left)
        text(surf, name, 18, (255, 255, 255), (16, 16))
        # level + hero_id subtitle
        if ref is not None:
            text(surf, f"Lv {ref.level}  {ref.hero_id}", 13,
                 (180, 200, 255), (16, 38))
        # HP bar
        if hp is not None:
            frac_hp = hp.hp / max(1, hp.max_hp)
            draw_bar(surf, (16, 58, 200, 14), frac_hp, (220, 70, 80))
            text(surf, f"{int(hp.hp)}/{int(hp.max_hp)}", 12,
                 (255, 255, 255), (16, 56))
            # energy bar
            frac_en = hp.energy / max(1, hp.max_energy)
            draw_bar(surf, (16, 76, 200, 10), frac_en, (90, 150, 240))
            text(surf, f"{int(hp.energy)}/{int(hp.max_energy)}", 10,
                 (200, 220, 255), (16, 74))
