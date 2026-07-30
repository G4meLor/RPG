"""
Aetheria — settings-menu widgets (Toggle + Slider).

Split out of the main.py settings scene (where they originally lived) into the
ui package so the settings scene can import them via `from src.ui import Toggle,
Slider` without pulling in the whole game loop. They depend on the `text`
helper (from primitives) and `audio` (the root shim, which proxies to
src.audio — kept as `import audio` to match the original ui.py convention).
"""
import pygame

from src.ui.primitives import text
import audio


class Toggle:
    """An on/off switch. Calls on_change(bool) when clicked."""
    def __init__(self, x, y, value=False, on_change=None, w=64, h=30):
        self.rect = pygame.Rect(x, y, w, h)
        self.value = bool(value)
        self.on_change = on_change
        self.hover = False
        self.knob = 1.0 if self.value else 0.0   # animated 0..1

    def set(self, v):
        self.value = bool(v)
        self.knob = 1.0 if self.value else 0.0

    def update(self, mp, mdown):
        self.hover = self.rect.collidepoint(mp)
        target = 1.0 if self.value else 0.0
        self.knob += (target - self.knob) * 0.25

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.value = not self.value
                audio.play("menu_click", 0.3)
                if self.on_change:
                    self.on_change(self.value)
                return True
        return False

    def draw(self, surf):
        r = self.rect
        # track
        on_col = (90, 200, 130)
        off_col = (70, 70, 90)
        col = on_col if self.value else off_col
        pygame.draw.rect(surf, (20, 20, 30), r, border_radius=r.height // 2)
        pygame.draw.rect(surf, col, r, border_radius=r.height // 2)
        pygame.draw.rect(surf, (220, 220, 240) if self.hover else (150, 150, 170),
                         r, 2, border_radius=r.height // 2)
        # knob
        kx = r.x + 4 + int(self.knob * (r.width - r.height))
        kr = r.height // 2 - 4
        pygame.draw.circle(surf, (245, 245, 250), (kx + kr, r.centery), kr)
        pygame.draw.circle(surf, (60, 60, 80), (kx + kr, r.centery), kr, 2)
        # tiny on/off label
        text(surf, "ON" if self.value else "OFF", 11,
             (240, 240, 250) if self.value else (160, 160, 180),
             (r.x - 30, r.centery - 8))


class Slider:
    """A horizontal slider for a 0..1 (or min..max) value.
    on_change(value) fires while dragging and on click."""
    def __init__(self, x, y, w, value=0.5, on_change=None,
                 vmin=0.0, vmax=1.0, step=None):
        self.rect = pygame.Rect(x, y, w, 16)
        self.value = float(value)
        self.vmin = float(vmin)
        self.vmax = float(vmax)
        self.step = step
        self.on_change = on_change
        self.hover = False
        self.dragging = False

    def _norm(self):
        return (self.value - self.vmin) / max(1e-6, self.vmax - self.vmin)

    def _set_from_x(self, mx):
        n = (mx - self.rect.x) / max(1, self.rect.width)
        n = max(0.0, min(1.0, n))
        v = self.vmin + n * (self.vmax - self.vmin)
        if self.step:
            v = round(v / self.step) * self.step
        v = max(self.vmin, min(self.vmax, v))
        if v != self.value:
            self.value = v
            if self.on_change:
                self.on_change(self.value)

    def update(self, mp, mdown):
        self.hover = self.rect.collidepoint(mp) or self.dragging
        if self.dragging and not mdown:
            self.dragging = False

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # grab if click on the track or near the knob
            hit = self.rect.inflate(0, 20).collidepoint(event.pos)
            if hit:
                self.dragging = True
                self._set_from_x(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging:
                self.dragging = False
                return True
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self._set_from_x(event.pos[0])
            return True
        return False

    def draw(self, surf):
        r = self.rect
        # track
        pygame.draw.rect(surf, (30, 30, 44), r, border_radius=8)
        pygame.draw.rect(surf, (70, 70, 100) if self.hover else (50, 50, 70),
                         r, 2, border_radius=8)
        # fill
        fw = int(r.width * self._norm())
        if fw > 0:
            pygame.draw.rect(surf, (120, 180, 240), (r.x, r.y, fw, r.height),
                             border_radius=8)
        # knob
        kx = r.x + fw
        pygame.draw.circle(surf, (240, 240, 250), (kx, r.centery), 9)
        pygame.draw.circle(surf, (60, 60, 90), (kx, r.centery), 9, 2)
