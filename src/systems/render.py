"""RenderSystem (Phase 4, Task 19 of the ECS restructure) — world renderer.

Renders the world layer (ground + entities + VFX + atmosphere) to a surface,
reading entity ``Transform``/``Health``/``Identity``/``Render`` components +
the scene's camera/map state. Runs IN PARALLEL with the legacy
``WorldScene.draw`` (additive) — the legacy draw STAYS the source of truth
this task; this system proves it can render entities to a surface without
raising. Full takeover (moving all ~25 ``_draw_*`` methods + atmosphere
helpers verbatim into this system) is Task 20.

The minimal gate (this task) is the brief's ``test_render_one_frame``:
``RenderSystem.draw`` iterates ``world.heroes()`` + ``world.enemies()``, reads
each entity's ``Transform``, and draws a small circle at the screen-space
position ``(x - ox, y - oy)`` using the camera offset from ``scene.camera``.
Heroes draw in their element color; enemies draw red; bosses draw a larger
crimson circle. This proves the system can render entities to a surface
without raising — the faithful extraction of the full draw pipeline (depth-
sorted drawables, water/bridges, atmosphere, vignette, etc.) is deferred to
Task 20 so this task stays minimal + low-risk.
"""
import pygame

from src.entities.components import Transform, Identity, Health, Render
from src.data.elements import ELEMENT_COLORS


class RenderSystem:
    """ECS world renderer — draws the world layer (entities + proxies) to a
    surface. The legacy ``WorldScene.draw`` stays the source of truth this
    task; this system runs in parallel (additive) to prove the extraction
    works in isolation. Full takeover is Task 20.

    Parameters
    ----------
    world : World
        The ECS entity world (read for ``heroes()`` / ``enemies()``).
    scene : WorldScene or None
        The owning scene. Used to read ``scene.camera.offset()`` for the
        world->screen transform. May be None for headless tests (the draw
        falls back to drawing at world coords with no camera offset).
    """

    def __init__(self, world, scene=None):
        self.world = world
        self.scene = scene

    def _camera_offset(self):
        """Return the (ox, oy) camera offset for the world->screen transform.

        Reads ``self.scene.camera.offset()`` (mirrors the legacy
        ``WorldScene.draw`` line ``ox, oy = self.camera.offset()``). Falls
        back to (0, 0) when there is no scene/camera so the system never
        raises in a headless test.
        """
        if self.scene is None:
            return 0, 0
        cam = getattr(self.scene, "camera", None)
        if cam is None:
            return 0, 0
        try:
            return cam.offset()
        except Exception:
            return 0, 0

    def draw(self, surf, map_ctrl=None):
        """Render the world layer to ``surf``.

        For the MINIMAL gate (this task): iterate ``world.heroes()`` +
        ``world.enemies()``, read each ``Transform``, draw a small circle at
        the screen-space position ``(x - ox, y - oy)``. Heroes use their
        element color; enemies are red; bosses are a larger crimson circle.
        Must NOT raise.

        The ``map_ctrl`` arg is accepted per the brief's signature contract
        (``RenderSystem.draw(surf, map_ctrl)``) for the Task 20 full
        extraction (ground + water + bridges + atmosphere, which read map
        state via the controller). This task's minimal draw does not need it
        yet — it is kept in the signature so the call site
        ``sc.render.draw(g.screen, sc.map_ctrl)`` works today.

        Args:
            surf: the destination pygame.Surface.
            map_ctrl: the MapController (unused this task; reserved for the
                Task 20 full ground/atmosphere extraction).
        """
        ox, oy = self._camera_offset()
        # heroes — element-colored circles at their Transform position
        for e in self.world.heroes():
            t = e.get(Transform)
            if t is None:
                continue
            ident = e.get(Identity)
            name = ident.name if ident is not None else "hero"
            # element color: read from the Render sprite_id (hero_id) via the
            # HERO_BY_ID lookup would pull a heavy import; instead use the
            # element-color fallback for unknown elements. The legacy draw
            # uses ELEMENT_COLORS the same way.
            col = (120, 220, 180)  # default hero green-cyan
            try:
                r = e.get(Render)
                if r is not None and r.sprite_id:
                    from src.data.heroes import HERO_BY_ID
                    hdef = HERO_BY_ID.get(r.sprite_id)
                    if hdef is not None:
                        col = ELEMENT_COLORS.get(
                            hdef["element"], ((120, 220, 180),))[0]
            except Exception:
                pass
            sx = int(t.x - ox)
            sy = int(t.y - oy)
            pygame.draw.circle(surf, col, (sx, sy), int(t.r))
            pygame.draw.circle(surf, (0, 0, 0), (sx, sy), int(t.r), 2)
        # enemies — red circles; bosses a larger crimson circle
        for e in self.world.enemies():
            t = e.get(Transform)
            if t is None:
                continue
            ident = e.get(Identity)
            is_boss = ident.is_boss if ident is not None else False
            sx = int(t.x - ox)
            sy = int(t.y - oy)
            if is_boss:
                pygame.draw.circle(surf, (180, 30, 40), (sx, sy), int(t.r) + 6)
                pygame.draw.circle(surf, (0, 0, 0), (sx, sy), int(t.r) + 6, 3)
            else:
                pygame.draw.circle(surf, (220, 80, 80), (sx, sy), int(t.r))
                pygame.draw.circle(surf, (0, 0, 0), (sx, sy), int(t.r), 2)
