"""
Aetheria — runtime VFX helpers.

Small procedural draw helpers called every frame by the world/adventure
scenes. These used to live in generate_assets.py (the build-time art
generator), which forced a runtime dependency on a 3500-line build module.
Moved here so the runtime only imports what it actually draws at runtime.

Safe to import from any scene; depends only on pygame + math.
"""
import math

import pygame


def draw_rift_portal(surf, cx, cy, t=0.0):
    """A pulsing portal for the hidden rift mini-dungeon. A swirling violet
    ring + a bright core + a few orbiting shards, drawn inline (the same
    pattern as the chest/breakable draws) so it reads as a distinct place,
    not just another deco tile. The `t` arg is the pulse phase (0..1) so the
    caller can animate it with pygame.time.get_ticks."""
    # pulse 0..1 -> radius/alpha breathe
    pulse = 0.5 + 0.5 * math.sin(t * 0.006)
    # outer glow (a soft violet halo, reused scratch-surface pattern)
    gw = 56
    g = pygame.Surface((gw, gw), pygame.SRCALPHA)
    for rr in range(26, 6, -2):
        a = int(80 * pulse * (1 - (rr - 6) / 20))
        pygame.draw.circle(g, (180, 80, 220, a), (gw // 2, gw // 2), rr)
    surf.blit(g, (cx - gw // 2, cy - gw // 2))
    # the swirling ring (3 offset arcs so it reads as a spinning vortex, not a
    # static circle)
    for k in range(3):
        ang = t * 0.004 + k * (math.pi * 2 / 3)
        rx = int(cx + math.cos(ang) * 14)
        ry = int(cy + math.sin(ang) * 14)
        pygame.draw.circle(surf, (200, 120, 240), (rx, ry), 8, 2)
    # bright core
    pygame.draw.circle(surf, (220, 160, 255), (cx, cy), 6 + int(pulse * 3))
    pygame.draw.circle(surf, (255, 240, 255), (cx, cy), 3)
    # a few orbiting shards (jagged accent triangles around the rim)
    for k in range(5):
        ang = t * 0.005 + k * (math.pi * 2 / 5)
        sx = int(cx + math.cos(ang) * 20)
        sy = int(cy + math.sin(ang) * 20)
        pygame.draw.circle(surf, (200, 120, 240), (sx, sy), 2)
