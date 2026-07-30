"""Settings scene."""
import pygame

from src.core.scene import Scene
from src.ui import (WIDTH, HEIGHT, WHITE, DIM, BG_DARK, PANEL_BORDER, FPS, Button,
                    draw_panel, text, f, Toggle, Slider)
import audio
class SettingsScene(Scene):
    """Full settings: Audio, Display, Gameplay, Accessibility, Data tabs."""
    TABS = ["Audio", "Display", "Gameplay", "Access", "Data"]

    def __init__(self, game):
        super().__init__(game)
        self.back_btn = Button((40, 40, 140, 48), "Back", (60, 60, 90), (90, 90, 130), size=20)
        self.tab = "Audio"
        self.t = 0
        self.confirming = False
        # tab buttons across the top
        tw = 150
        tx = WIDTH // 2 - (len(self.TABS) * tw) // 2
        self.tab_btns = []
        for i, name in enumerate(self.TABS):
            b = Button((tx + i * tw, 120, tw - 10, 44), name,
                       (60, 70, 110), (90, 120, 180), size=18)
            self.tab_btns.append((name, b))
        # panel area
        self.px, self.py = 220, 190
        self.pw, self.ph = WIDTH - 440, HEIGHT - 260
        # build widgets for the current tab (rebuilt on tab change)
        self._widgets = {}
        self._labels = []
        self._build_tab()

    # --- settings helpers ---
    def _s(self, key, default):
        return self.game.player.settings.get(key, default)

    def _set(self, key, value):
        self.game.player.settings[key] = value
        self.game.player.save()

    def _apply_runtime(self):
        """Push settings that have live runtime effects (audio, display)."""
        s = self.game.player.settings
        audio.set_enabled(s.get("sound", True))
        audio.set_master_volume(s.get("sfx_volume", 0.7))

    def _build_tab(self):
        self._widgets = {}
        self._labels = []
        s = self.game.player.settings
        x = self.px + 40
        y = self.py + 30
        row_h = 64

        def label(txt):
            self._labels.append((txt, x, y + 6))
            return y + 34   # widget y under the label

        if self.tab == "Audio":
            wy = label("Master Sound")
            t = Toggle(x, wy, value=s.get("sound", True),
                       on_change=lambda v: (self._set("sound", v), self._apply_runtime()))
            self._widgets["sound"] = t
            self._labels.append(("Enable all sound effects", x + 80, wy + 6))
            y += row_h
            wy = label("SFX Volume")
            sl = Slider(x, wy, 360, value=s.get("sfx_volume", 0.7),
                        on_change=lambda v: (self._set("sfx_volume", v), self._apply_runtime()))
            self._widgets["sfx_volume"] = sl
            self._labels.append((f"{int(s.get('sfx_volume',0.7)*100)}%", x + 380, wy - 2))
            y += row_h
            wy = label("Music Volume")
            sl2 = Slider(x, wy, 360, value=s.get("music_volume", 0.5),
                         on_change=lambda v: self._set("music_volume", v))
            self._widgets["music_volume"] = sl2
            self._labels.append((f"{int(s.get('music_volume',0.5)*100)}%", x + 380, wy - 2))
            y += row_h
            wy = label("Text Speed")
            sl3 = Slider(x, wy, 360, value=s.get("text_speed", 1.0),
                         vmin=0.5, vmax=2.0, step=0.05,
                         on_change=lambda v: self._set("text_speed", v))
            self._widgets["text_speed"] = sl3
            self._labels.append((f"x{s.get('text_speed',1.0):.2f}", x + 380, wy - 2))

        elif self.tab == "Display":
            wy = label("Fullscreen")
            t = Toggle(x, wy, value=s.get("fullscreen", False),
                       on_change=lambda v: (self._set("fullscreen", v), self._apply_display()))
            self._widgets["fullscreen"] = t
            self._labels.append(("Borderless fullscreen window", x + 80, wy + 6))
            y += row_h
            wy = label("Show FPS")
            t2 = Toggle(x, wy, value=s.get("show_fps", False),
                        on_change=lambda v: self._set("show_fps", v))
            self._widgets["show_fps"] = t2
            self._labels.append(("Show a frames-per-second counter", x + 80, wy + 6))
            y += row_h
            wy = label("Frame Rate Cap")
            sl = Slider(x, wy, 360, value=s.get("fps_cap", 60),
                        vmin=30, vmax=144, step=6,
                        on_change=lambda v: self._set("fps_cap", int(v)))
            self._widgets["fps_cap"] = sl
            self._labels.append((f"{int(s.get('fps_cap',60))} fps", x + 380, wy - 2))
            y += row_h
            wy = label("Particle Quality")
            sl2 = Slider(x, wy, 360, value=s.get("particle_quality", 1.0),
                         vmin=0.4, vmax=1.0, step=0.1,
                         on_change=lambda v: self._set("particle_quality", round(v, 2)))
            self._widgets["particle_quality"] = sl2
            self._labels.append((f"{int(s.get('particle_quality',1.0)*100)}%", x + 380, wy - 2))

        elif self.tab == "Gameplay":
            wy = label("Auto Save")
            t = Toggle(x, wy, value=s.get("auto_save", True),
                       on_change=lambda v: self._set("auto_save", v))
            self._widgets["auto_save"] = t
            self._labels.append(("Save on map changes and deaths", x + 80, wy + 6))
            y += row_h
            wy = label("Damage Numbers")
            t2 = Toggle(x, wy, value=s.get("damage_numbers", True),
                        on_change=lambda v: self._set("damage_numbers", v))
            self._widgets["damage_numbers"] = t2
            self._labels.append(("Show floating damage/heal text", x + 80, wy + 6))
            y += row_h
            wy = label("Controls Hints")
            t3 = Toggle(x, wy, value=s.get("show_hints", True),
                        on_change=lambda v: self._set("show_hints", v))
            self._widgets["show_hints"] = t3
            self._labels.append(("Show the controls bar in the world", x + 80, wy + 6))
            y += row_h
            wy = label("Screen Shake")
            sl = Slider(x, wy, 360, value=s.get("screen_shake", 1.0),
                        vmin=0.0, vmax=1.0, step=0.1,
                        on_change=lambda v: self._set("screen_shake", round(v, 2)))
            self._widgets["screen_shake"] = sl
            self._labels.append((f"{int(s.get('screen_shake',1.0)*100)}%", x + 380, wy - 2))

        elif self.tab == "Access":
            wy = label("Reduce Motion")
            t = Toggle(x, wy, value=s.get("reduce_motion", False),
                       on_change=lambda v: self._set("reduce_motion", v))
            self._widgets["reduce_motion"] = t
            self._labels.append(("Dampen screen shake, flashes, and wipes", x + 80, wy + 6))
            y += row_h
            # a friendly explanation block
            self._labels.append(("Reduce Motion overrides Shake and Particle", x, y + 6))
            self._labels.append(("settings for a calmer experience.", x, y + 30))
            y += row_h
            wy = label("High Contrast UI (auto)")
            t2 = Toggle(x, wy, value=s.get("high_contrast", False),
                        on_change=lambda v: self._set("high_contrast", v))
            self._widgets["high_contrast"] = t2
            self._labels.append(("Brighter text and panel borders", x + 80, wy + 6))
            y += row_h
            wy = label("Colorblind Mode")
            t3 = Toggle(x, wy, value=s.get("colorblind_mode", False),
                        on_change=lambda v: self._set("colorblind_mode", v))
            self._widgets["colorblind_mode"] = t3
            self._labels.append(("Use deuteranopia-safe element colors", x + 80, wy + 6))

        elif self.tab == "Data":
            wy = self.py + 40
            self._labels.append(("Save Data Management", x, wy))
            self._labels.append(("This permanently deletes all your progress:", x, wy + 36))
            self._labels.append(("heroes, levels, currency, and discovered maps.", x, wy + 60))
            self.reset_btn = Button((WIDTH // 2 - 120, wy + 120, 240, 56),
                                    "Reset Save", (120, 40, 60), (180, 60, 90), size=20)
            self.confirm_btn = Button((WIDTH // 2 - 220, wy + 220, 200, 56),
                                      "Confirm Reset", (160, 40, 50), (220, 60, 60), size=18)
            self.cancel_btn = Button((WIDTH // 2 + 20, wy + 220, 200, 56),
                                     "Cancel", (60, 80, 120), (90, 120, 180), size=20)

    def _apply_display(self):
        """Apply fullscreen/windowed mode to the running display."""
        try:
            s = self.game.player.settings
            if s.get("fullscreen", False):
                self.game.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.FULLSCREEN)
            else:
                self.game.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED)
        except Exception:
            pass

    def update(self, dt, events):
        self.t += dt
        mp = pygame.mouse.get_pos()
        mdown = pygame.mouse.get_pressed()[0]
        self.back_btn.update(mp, mdown)
        for name, b in self.tab_btns:
            b.update(mp, mdown)
        for w in self._widgets.values():
            w.update(mp, mdown)
        if self.tab == "Data":
            self.reset_btn.update(mp, mdown)
            self.confirm_btn.update(mp, mdown)
            self.cancel_btn.update(mp, mdown)
        for e in events:
            if self.back_btn.clicked(e) or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                self.game.back("title")
                return
            # keyboard tab switching (Left/Right arrows) for consistency with the
            # world scene's full keyboard control.
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_LEFT, pygame.K_RIGHT):
                idx = self.TABS.index(self.tab) if self.tab in self.TABS else 0
                if e.key == pygame.K_LEFT:
                    self.tab = self.TABS[max(0, idx - 1)]
                else:
                    self.tab = self.TABS[min(len(self.TABS) - 1, idx + 1)]
                self.confirming = False
                self._build_tab()
                audio.play("menu_click", 0.3)
                return
            for name, b in self.tab_btns:
                if b.clicked(e):
                    self.tab = name
                    self.confirming = False
                    self._build_tab()
                    audio.play("menu_click", 0.3)
                    return
            for w in self._widgets.values():
                if w.handle(e):
                    self._refresh_labels()
                    return
            if self.tab == "Data":
                if not self.confirming and self.reset_btn.clicked(e):
                    self.confirming = True
                    return
                if self.confirming:
                    if self.confirm_btn.clicked(e):
                        self.game.reset_save()
                        return
                    if self.cancel_btn.clicked(e):
                        self.confirming = False
                        return

    def _refresh_labels(self):
        """Re-render the dynamic value labels (percentages) after a change."""
        s = self.game.player.settings
        # find labels by matching the known prefix text and rewriting them
        # (simplest: rebuild the tab so labels reflect current values)
        self._build_tab()

    def draw(self, surf):
        surf.fill(BG_DARK)
        # high_contrast: brighten the title + label text so the Accessibility
        # toggle actually does something (brighter text + panel borders)
        hc = self.game.player.settings.get("high_contrast", False)
        title_col = (255, 255, 255) if hc else WHITE
        label_col = (240, 240, 255) if hc else (200, 200, 220)
        text(surf, "Settings", 40, title_col, (WIDTH // 2, 80), center=True)
        # tabs
        for name, b in self.tab_btns:
            b.color = (90, 120, 180) if self.tab == name else (60, 70, 110)
            b.draw(surf)
        # panel — a brighter border when high_contrast is on
        draw_panel(surf, (self.px, self.py, self.pw, self.ph),
                   border=(255, 255, 255) if hc else PANEL_BORDER)
        # labels
        for item in self._labels:
            if len(item) == 3:
                txt, lx, ly = item
                text(surf, txt, 18, label_col, (lx, ly))
        # widgets
        for w in self._widgets.values():
            w.draw(surf)
        # data tab extras
        if self.tab == "Data":
            if self.confirming:
                text(surf, "Delete ALL progress?", 22, (255, 120, 120),
                     (WIDTH // 2, self.py + 180), center=True)
                self.confirm_btn.draw(surf)
                self.cancel_btn.draw(surf)
            else:
                self.reset_btn.draw(surf)
        self.back_btn.draw(surf)
        # a subtle footer hint
        text(surf, "Changes save automatically", 14, DIM, (WIDTH // 2, HEIGHT - 30), center=True)


# ---------------------------------------------------------------------------
# Stats scene
# ---------------------------------------------------------------------------
