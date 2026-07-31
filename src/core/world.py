"""World — entity container + query."""
from src.entities.entity import Entity
from src.entities.components import Identity

class World:
    def __init__(self):
        self.entities = {}
        self._next_eid = 0
    def spawn(self):
        e = Entity(self._next_eid)
        self.entities[self._next_eid] = e
        self._next_eid += 1
        return e
    def destroy(self, eid):
        self.entities.pop(eid, None)
    def query(self, *comp_classes):
        for e in self.entities.values():
            if all(e.has(c) for c in comp_classes):
                yield e
    def heroes(self):
        return [e for e in self.entities.values()
                if e.has(Identity) and e.get(Identity).is_hero]
    def enemies(self):
        return [e for e in self.entities.values()
                if e.has(Identity) and not e.get(Identity).is_hero]
