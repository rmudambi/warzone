class Ladder:
    def __init__(self, ladder_id, name):
        self.id = ladder_id
        self.name = name


class FogLevel:
    def __init__(self, fog_level_id, json_id, name):
        self.id = fog_level_id
        self.json_id = json_id
        self.name = name


class OrderType:
    def __init__(self, order_type_id, json_id, name):
        self.id = order_type_id
        self.json_id = json_id
        self.name = name


class Card:
    def __init__(self, card_id, name):
        self.id = card_id
        self.name = name
