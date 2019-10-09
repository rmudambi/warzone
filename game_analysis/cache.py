import logging

from typing import Dict

from .models import Card, Game, Ladder, Player, Map, Order, OrderType
from .models import PlayerAccount, PlayerStateType, Template
from .models import TemplateCardSetting, Territory, Turn
from .wrappers import BonusWrapper, GameWrapper, MapWrapper, TerritoryWrapper

# Cached Ladders
ladders: Dict[int, Ladder] = {}

# Cached Cards
cards: Dict[int, Card] = {}

# Cached Player State Types
player_state_types: Dict[str, PlayerStateType] = {}

# Cached Order Types
order_types: Dict[str, OrderType] = {}

# Cached Templates
templates: Dict[int, Template] = {}

# Cached Maps
maps: Dict[int, MapWrapper] = {}

# Cached Player Accounts
player_accounts: Dict[int, PlayerAccount] = {}

# Cached Games
games: Dict[int, GameWrapper] = {}


# Get Ladder
def get_ladder(id: int) -> Ladder:
    try:
        return ladders[id]
    except KeyError:
        ladders[id] = Ladder.objects.get(pk=id)
        return ladders[id]


# Get Card
def get_card(id: int) -> Card:
    try:
        return cards[id]
    except KeyError:
        cards[id] = Card.objects.get(pk=id)
        return cards[id]


# Get Player State Type
def get_player_state_type(id: str) -> PlayerStateType:
    try:
        return player_state_types[id]
    except KeyError:
        player_state_types[id] = PlayerStateType.objects.get(pk=id)
        return player_state_types[id]


# Get OrderType
def get_order_type(id: str) -> OrderType:
    try:
        return order_types[id]
    except KeyError:
        order_types[id] = OrderType.objects.get(pk=id)
        return order_types[id]


# Get the Name of the Neutral "Player Account"
def get_neutral_name() -> str:
    return 'Neutral'


# Get ID of Neutral "Player Account"
def get_neutral_id() -> int:
    return 0


# Get Wasteland baseline state for territory
def get_wasteland_baseline_state() -> str:
    return 'Wasteland'


# Get 'In Distribution' baseline state for territory
def get_in_distribution_baseline_state() -> str:
    return 'In Distribution'


# Add MapWrapper to cache
def add_map_to_cache(map_id: int, for_import: bool) -> None:
    prefetches = ((
        'territory_set',
        'bonus_set'
    ) if for_import else (
        'territory_set__connected_territories',
        'territory_set__bonuses',
        'bonus_set__territories'
    ))

    maps[map_id] = MapWrapper(
        Map.objects.prefetch_related(*prefetches).get(pk=map_id),
        for_import
    )


# Get BonusWrapper
def get_bonus_wrapper(map_id: int, bonus_id: int) -> BonusWrapper:
    # If the Map is not in the cache or the Map is in the wrong format
    if map_id not in maps or maps[map_id].uses_api_ids:
        # Add the MapWrapper to the cache
        add_map_to_cache(map_id, False)

    return maps[map_id].bonuses[bonus_id]


# Get Territory
def get_territory(map_id: int, territory_id: int,
        for_import: bool) -> Territory:
    return get_territory_wrapper(map_id, territory_id, for_import).territory


# Get TerritoryWrapper
def get_territory_wrapper(map_id: int, territory_id: int,
        for_import:bool) -> TerritoryWrapper:
    # If the Map is not in the cache or the Map is in the wrong format
    if map_id not in maps or maps[map_id].uses_api_ids != for_import:
        # Add the MapWrapper to the cache
        add_map_to_cache(map_id, for_import)

    return maps[map_id].territories[territory_id]


# Fetches Map from cache if it exists.
# Otherwise, fetches Map from DB and adds it to the cache.
# Throws Maps.DoesNotExist if Map doesn't exist in the DB
def get_map(map_id: int, for_import: bool) -> Map:
    return get_map_wrapper(map_id, for_import).map


# Fetches MapWrapper from cache if it exists.
# Otherwise, fetches Map from DB and adds it to the cache.
# Throws Maps.DoesNotExist if Map doesn't exist in the DB
def get_map_wrapper(map_id: int, for_import: bool) -> MapWrapper:
    logging.debug(f'Getting Map {map_id}')

    # If map is not in the dictionary
    if map_id not in maps or maps[map_id].uses_api_ids != for_import:
        add_map_to_cache(map_id, for_import)

    # Return map wrapper
    return maps[map_id]


# Adds Template to cache
def add_template_to_cache(template: Template) -> None:
    templates[template.id] = template


# Fetches Template from cache if it exists
# Otherwise, Fetches Template from DB and adds it to the cache.
# Throws Template.DoesNotExist if Template doesn't exist in the DB.
def get_template(template_id: int) -> Template:
    # if template is not in the dictionary
    if template_id  not in templates:
        template = Template.objects.get(pk=template_id)

        add_template_to_cache(template)

    # Return template from dictionary
    return templates[template_id]


# Add the player account to the cache
def add_player_account_to_cache(player_account: PlayerAccount) -> None:
    player_accounts[player_account.id] = player_account


# Fetches PlayerAccount from DB if it exists.
# Throws PlayerAccount.DoesNotExist if PlayerAccount doesn't exist in the DB
# Add the player account to the player accounts cache. Uses ID as key
# Returns Player
def get_player_account(player_account_id: int) -> PlayerAccount:
    if player_account_id not in player_accounts:
        player_account = PlayerAccount.objects.get(pk=player_account_id)
        add_player_account_to_cache(player_account)
        
    return player_accounts[player_account_id]


# Add the Player to the cache
def add_player_to_cache(player: Player, id: int) -> None:
    games[player.game_id].players[id] = player


# Fetches Player from cache
def get_player(game_id: int, player_id: int) -> Player:
    return games[game_id].players[player_id]


# Clears all games from cache
def clear_games_from_cache() -> None:
    games.clear()


# Add Game to cache
def add_game_to_cache(game: Game) -> None:
    games[game.id] = GameWrapper(game, True)


# Get Game from cache
def get_game(game_id: int) -> Game:
    return games[game_id].game
