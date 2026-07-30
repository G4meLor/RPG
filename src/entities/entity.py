"""Entity — an eid + a component dict. __slots__ to stay cheap."""
class Entity:
    __slots__ = ("eid", "components")
    def __init__(self, eid):
        self.eid = eid
        self.components = {}
    def add(self, comp):
        self.components[type(comp)] = comp
        return self
    def get(self, comp_cls):
        return self.components.get(comp_cls)
    def has(self, comp_cls):
        return comp_cls in self.components
