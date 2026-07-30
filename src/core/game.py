"""Aetheria Game controller + scene factory.

The Game owns the pygame display, the player, and the active scene. The scene
factory (_make_scene) maps scene names to the scene classes now living in
src.scenes.* (world/adventure) and src.scenes.menu.* (the 10 menu scenes).
The old lazy _get_world_scene_cls/_get_adventure_scene_cls getters are gone —
the cycle that forced them (world_scene importing from main) is broken, so
direct imports work.
"""
import pygame

import audio
from ui import (WIDTH, HEIGHT, FPS, TITLE, init_fonts, text)
from player import Player
from src.scenes.world import WorldScene
from src.scenes.adventure import AdventureScene
from src.scenes.menu import (TitleScene, RosterScene, HeroDetailScene, GachaScene,
    ShopScene, InventoryScene, SettingsScene, StatsScene, CodexScene)


class Game:
    _active = None  # class-level ref to the most-recently-constructed Game so
                    # module-level helpers (element_color) can read player.settings
    def __init__(self):
        pygame.init()
        audio.init()
        flags = pygame.SCALED
        try:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT), flags, vsync=1)
        except pygame.error:
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        init_fonts()
        self.player = Player.load()
        Game._active = self  # register this instance for element_color() lookups
        # apply persisted settings to the live audio + display on boot
        audio.set_enabled(self.player.settings.get("sound", True))
        audio.set_master_volume(self.player.settings.get("sfx_volume", 0.7))
        # apply the persisted display mode (fullscreen) on boot
        if self.player.settings.get("fullscreen", False):
            try:
                self.screen = pygame.display.set_mode((WIDTH, HEIGHT),
                                                      pygame.SCALED | pygame.FULLSCREEN)
            except Exception:
                pass
        # daily login bonus (7-day streak)
        granted, amt, streak = self.player.check_daily()
        if granted:
            self.player.save()
            self._login_bonus = (amt, streak)
        else:
            self._login_bonus = None
        self.scene = None
        self.scenes = {}
        self.running = True
        # navigation back-stack of (name, kw) tuples; title is a root
        self.scene_stack = []
        self._current = None
        # scene transition fade
        self._fade = 0.0          # 1.0 = fully black; fades out on scene change
        self._fade_target = 0.0
        self._pending_scene = None
        self.goto("title")
        self._fade = 1.0          # fade in on first launch

    def _make_scene(self, name, **kw):
        if name == "title":
            return TitleScene(self)
        elif name == "roster":
            return RosterScene(self)
        elif name == "gacha":
            return GachaScene(self)
        elif name == "shop":
            return ShopScene(self)
        elif name == "inventory":
            return InventoryScene(self)
        elif name == "hero_detail":
            return HeroDetailScene(self, kw["hero_id"])
        elif name == "settings":
            return SettingsScene(self)
        elif name == "stats":
            return StatsScene(self)
        elif name == "codex":
            return CodexScene(self)
        elif name == "world":
            # Adventure mode (Task D1/D2): route to AdventureScene when the
            # player's mode is "adventure" (the wave-survival mode with a fixed-4
            # party locked for the run). The open-world mode is "endless" (full
            # live swap + roster changes); a pre-D2 save that stored "world" is
            # treated as the open-world path here (not adventure), so the base
            # game is unchanged. AdventureScene is a subclass of WorldScene
            # (inherits the combat engine); the cycle that forced lazy imports
            # is now broken, so direct imports work.
            if getattr(self.player, "mode", "endless") == "adventure":
                return AdventureScene(self)
            return WorldScene(self)
        return TitleScene(self)

    def goto(self, name, **kw):
        # title is a root: clear the back-stack when going home
        if name == "title":
            self.scene_stack = []
        elif self.scene is not None and self._current is not None:
            self.scene_stack.append(self._current)
        self._current = (name, kw)
        self.scene = self._make_scene(name, **kw)
        # trigger a fade-out -> fade-in transition on scene change
        self._fade_target = 1.0
        # defensive: initialize the scene's cached draw-state so draw() is safe
        # even if it is called before the first update() (happens because goto
        # swaps self.scene mid-frame, then the same frame calls draw()).
        self._safe_init_scene()

    def back(self, fallback="title"):
        if self.scene_stack:
            name, kw = self.scene_stack.pop()
            self._current = (name, kw)
            self.scene = self._make_scene(name, **kw)
            self._fade_target = 1.0
            self._safe_init_scene()
        else:
            self.goto(fallback)

    def _safe_init_scene(self):
        try:
            self.scene.update(0.0, [])
        except Exception:
            # a scene that needs real input to init is still protected by the
            # per-scene __init__ defaults; never let init break the frame.
            pass

    def reset_save(self):
        self.player = Player()
        self.player.save()
        self.scene_stack = []
        self._current = None
        self.goto("title")

    def run(self):
        while self.running:
            # respect the user's FPS cap setting (default 60)
            cap = self.player.settings.get("fps_cap", FPS)
            dt = self.clock.tick(int(cap)) / 1000.0
            dt = min(dt, 1 / 30)
            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    self.running = False
            self.scene.update(dt, events)
            self.scene.draw(self.screen)
            # debug FPS overlay
            if self.player.settings.get("show_fps", False):
                fps = self.clock.get_fps()
                text(self.screen, f"{fps:4.0f} fps", 20, (120, 240, 160), (WIDTH - 90, HEIGHT - 30))
            # scene transition fade overlay
            if self._fade_target > 0 or self._fade > 0:
                # ease the fade toward its target
                self._fade += (self._fade_target - self._fade) * min(1, dt * 8)
                # once fully black, drop back to transparent (reveal new scene)
                if self._fade_target == 1.0 and self._fade > 0.9:
                    self._fade_target = 0.0
                if self._fade > 0.01:
                    fl = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    fl.fill((0, 0, 0, int(255 * min(1, self._fade))))
                    self.screen.blit(fl, (0, 0))
            pygame.display.flip()
        self.player.save()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
