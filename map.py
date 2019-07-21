class Map:
    def __init__(self, map_id, name, territories=None, bonuses=None):
        self.id = map_id
        self.name = name
        self.territories = territories
        self.bonuses = bonuses


class Bonuses:
    def __init__(self, bonus_id, json_id, name, value, territories=None):
        self.id = bonus_id
        self.json_id = json_id
        self.name = name
        self.value = value
        self.territories = territories


class Territory:
    def __init__(self, territory_id, json_id, name, connections=None):
        self.id = territory_id
        self.json_id = json_id
        self.name = name
        self.connections = connections
