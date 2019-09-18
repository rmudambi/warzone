from .models import PlayerState

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


class PlayerStateWrapper():
    def __init__(self, player_state):
        self.player_state = player_state
        self.territories = {}
        self.bonus_ids = set()


class TurnWrapper():
    def __init__(self, turn):
        self.turn = turn
        self.player_states = {
            player_state.player_id: PlayerStateWrapper(player_state)
            for player_state in turn.playerstate_set.all()
        }
        self.orders = sorted(
            list(turn.order_set.all()),
            key=lambda order: order.order_number
        )
        self.territory_owners = {}


class GameWrapper():
    def __init__(self, game, players=None):
        self.game = game
        self.players = players if players != None else {
            player.pk: player
            for player in game.player_set.all()
        }
        self.turns = sorted(
            [TurnWrapper(turn) for turn in game.turn_set.all()],
            key=lambda turn_wrapper: turn_wrapper.turn.turn_number
        )
        self.territories_baseline = {
            territory_baseline.territory_id: territory_baseline
            for territory_baseline in game.territorybaseline_set.all()
        }
