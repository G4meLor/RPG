"""Base Scene class."""


class Scene:
    def __init__(self, game):
        self.game = game

    def update(self, dt, events):
        pass

    def draw(self, surf):
        pass
