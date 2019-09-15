class TerritoryWrapper():
    def __init__(self, territory, use_api_ids):
        self.territory = territory
        self.connected_territory_ids = {
            to_territory.api_id if use_api_ids else to_territory.pk
            for to_territory in territory.connected_territories.all()
        }
        self.bonus_ids = {
            bonus.api_id if use_api_ids else bonus.pk
            for bonus in territory.bonuses.all()
        }


class BonusWrapper():
    def __init__(self, bonus, use_api_ids):
        self.bonus = bonus
        self.territory_ids = {
            territory.api_id if use_api_ids else territory.pk
            for territory in bonus.territories.all()
        }


class MapWrapper():
    def __init__(self, map, use_api_ids):
        self.map = map
        self.uses_api_ids = use_api_ids
        self.territories = {
            territory.api_id if use_api_ids else territory.pk:
                TerritoryWrapper(territory, use_api_ids)
            for territory in map.territory_set.all()
        }
        self.bonuses = {
            bonus.api_id if use_api_ids else bonus.pk:
                BonusWrapper(bonus, use_api_ids)
            for bonus in map.bonus_set.all()
        }


class GamePlayerWrapper():
    def __init__(self, game_player):
        self.game_player = game_player


class GameWrapper():
    def __init__(self, game, game_players=None):
        self.game = game
        self.game_players = game_players if game_players != None else {
            game_player.id: GamePlayerWrapper(game_player)
                for game_player in game.gameplayer_set.all()
        }