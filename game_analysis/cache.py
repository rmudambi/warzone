import logging

from .models import Card, Game, Player, Map, Order, OrderType, PlayerAccount
from .models import PlayerStateType, Template, TemplateCardSetting, Territory
from .models import Turn
from .wrappers import BonusWrapper, PlayerWrapper, GameWrapper, MapWrapper
from .wrappers import TerritoryWrapper

# Dictionary from card id -> card
cards = {}

# Dictionary from player state type id -> player state types
player_state_types = {}

# Dictionary from card order type id -> order type
order_types = {}

# Neutral and AvailableForDistribution "Players"
neutral_players = {}

# Dictionary from template id -> template
templates = {}

# Dictionary from map id -> MapWrapper
maps = {}

# Dictionary from player account id -> player account
player_accounts = {}

# Dictionary from game id -> GameWrapper
games = {}


# Get Card
def get_card(id=id):
    try:
        return cards[id]
    except KeyError:
        cards[id] = Card.objects.get(pk=id)
        return cards[id]


# Get Player State Type
def get_player_state_type(id=id):
    try:
        return player_state_types[id]
    except KeyError:
        player_state_types[id] = PlayerStateType.objects.get(pk=id)
        return player_state_types[id]


# Get OrderType
def get_order_type(id=id):
    try:
        return order_types[id]
    except KeyError:
        order_types[id] = OrderType.objects.get(pk=id)
        return order_types[id]

# Set Neutral "Players"
def set_neutral_players():
    neutral_players['Neutral'] = PlayerAccount.objects.get(pk=0)
    neutral_players['AvailableForDistribution'] = PlayerAccount.objects.get(pk=1)


# Add MapWrapper to cache
def add_map_to_cache(map_id, for_import):
    prefetches = ((
        'territory_set',
    ) if for_import else (
        'territory_set__connected_territories',
        'territory_set__bonuses',
        'bonus_set__territories'
    ))

    maps[map_id] = MapWrapper(
        Map.objects.prefetch_related(*prefetches).get(pk=map_id),
        for_import
    )


# Get Territory
def get_territory(map_id, territory_id, for_import):
    return get_territory_wrapper(map_id, territory_id, for_import).territory


# Get TerritoryWrapper
def get_territory_wrapper(map_id, territory_id, for_import):
    # If the Map is not in the Dictionary or the Map is in the wrong format
    if map_id not in maps or maps[map_id].uses_api_ids != for_import:
        # Add the MapWrapper to the cache
        add_map_to_cache(map_id, for_import)

    return maps[map_id].territories[territory_id]


# Fetches Map from dictionary if it exists.
# Otherwise, fetches Map from DB if it exists there and creates territories
# dictionary. Throws Maps.DoesNotExist if Map doesn't exist in the DB
# Adds Map and Territories to maps
# Returns Map
def get_map(map_id, for_import):
    logging.debug(f'Getting Map {map_id}')

    # If map is not in the dictionary
    if map_id not in maps or maps[map_id].uses_api_ids != for_import:
        add_map_to_cache(map_id, for_import)

    # Return map
    return maps[map_id].map


# Adds Template and Cards Settings to templates
def add_template_to_cache(template):
    templates[template.id] = template


# Fetches Template from imput template dictionary if it exists
# Otherwise, Fetches Template from DB if it exists there and creates card
# settings dictionary. Throws Template.DoesNotExist if Template doesn't exist
# in the DB. Adds Template and Cards Settings to templates. Returns Template
def get_template(template_id):
    # if template is not in the dictionary
    if template_id  not in templates:
        template = Template.objects.get(pk=template_id)

        add_template_to_cache(template)

    # Return template from dictionary
    return templates[template_id]


# Add the player account to the player accounts cache
def add_player_account_to_cache(player_account):
    player_accounts[player_account.id] = player_account


# Fetches PlayerAccount from DB if it exists.
# Throws PlayerAccount.DoesNotExist if PlayerAccount doesn't exist in the DB
# Add the player account to the player accounts cache. Uses ID as key
# Returns Player
def get_player_account(player_account_id):
    if player_account_id not in player_accounts:
        player_account = PlayerAccount.objects.get(pk=player_account_id)
        add_player_account_to_cache(player_account)
        
    return player_accounts[player_account_id]


# Add the Player to the players cache
def add_player_to_cache(player, id):
    games[player.game_id].players[id] = PlayerWrapper(player)


# Fetches Player from cache
def get_player(game_id, player_id):
    return games[game_id].players[player_id].player


# Clears all games from cache
def clear_games_from_cache():
    games.clear()


# Add Game to cache
def add_game_to_cache(game, game_players=None):
    games[game.id] = GameWrapper(game, game_players)


# Get Game from cache
def get_game(game_id):
    return games[game_id].game
