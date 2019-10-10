from typing import Dict, List, Set

from .models import Bonus, Game, Map, Order, Player, PlayerState, Territory
from .models import Turn


class TerritoryWrapper():
    def __init__(self, territory: Territory, use_api_ids: bool):
        self.territory = territory
        self.connected_territory_ids: Set[int] = {
            to_territory.api_id if use_api_ids else to_territory.pk
            for to_territory in territory.connected_territories.all()
        }
        self.bonus_ids: Set[int] = {
            bonus.api_id if use_api_ids else bonus.pk
            for bonus in territory.bonuses.all()
        }


class BonusWrapper():
    def __init__(self, bonus: Bonus, use_api_ids: bool):
        self.bonus = bonus
        self.territory_ids: Set[int] = {
            territory.api_id if use_api_ids else territory.pk
            for territory in bonus.territories.all()
        }


class MapWrapper():
    def __init__(self, map: Map, use_api_ids: bool):
        self.map = map
        self.uses_api_ids = use_api_ids
        self.territories: Dict[int, TerritoryWrapper] = {
            territory.api_id if use_api_ids else territory.pk:
                TerritoryWrapper(territory, use_api_ids)
            for territory in map.territory_set.all()
        }
        self.bonuses: Dict[int, BonusWrapper] = {
            bonus.api_id if use_api_ids else bonus.pk:
                BonusWrapper(bonus, use_api_ids)
            for bonus in map.bonus_set.all()
        }


class PlayerStateWrapper():
    def __init__(self, player_state: PlayerState):
        self.player_state = player_state
        # A mapping from the territory id to number of armies
        self.territories: Dict[int, int] = {}
        # Set of bonuses controlled by player
        self.bonus_ids: Set[int] = set()


class TurnWrapper():
    def __init__(self, turn: Turn):
        self.turn = turn
        self.player_states: Dict[int, PlayerStateWrapper] = {
            player_state.player_id: PlayerStateWrapper(player_state)
            for player_state in turn.playerstate_set.all()
        }
        self.orders: List[Order] = sorted(
            list(turn.order_set.all()),
            key=lambda order: order.order_number
        )


class GameWrapper():
    def __init__(self, game: Game, shallow: bool = False):
        self.game: Game = game
        self.players: Dict[int, Player] = {} if shallow else {
            player.pk: player for player in game.player_set.all()
        }
        self.turns: List[TurnWrapper] = [] if shallow else sorted(
            [TurnWrapper(turn) for turn in game.turn_set.all()],
            key=lambda turn_wrapper: turn_wrapper.turn.turn_number
        )

        # Not needed for version 1
        # self.territories_baseline = {
        #     territory_baseline.territory_id: territory_baseline
        #     for territory_baseline in game.territorybaseline_set.all()
        # }
