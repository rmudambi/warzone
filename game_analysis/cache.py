import logging

from .models import Card, Map, OrderType, Player, PlayerStateType, Template, TemplateCardSetting, Territory

# Dictionary from card id -> card
cards = {}

# Dictionary from player state type id -> player state types
player_state_types = {}

# Dictionary from card order type id -> order type
order_types = {}

# Neutral and AvailableForDistribution "Players"
neutral_players = {}

# Dictionary from template id -> {'template': template, 'cards_settings': {card id -> card settings}}
templates = {}

# Dictionary from map id -> {'map': map,  'territories': {territory api id -> territory}}
maps = {}

# Dictionary from player id -> {'player': player}
players = {}


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
    neutral_players['Neutral'] = Player.objects.get(pk=0)
    neutral_players['AvailableForDistribution'] = Player.objects.get(pk=1)


# Adds Map and Territories to maps
def add_to_maps(map, territories):
    maps[map.id] = {'map': map, 'territories': territories}


# Adds the Territories of the Map to the input dictionary along with the Map itself
def get_territories(map_id):
    if map_id in maps:
        return maps[map_id]['territories']
    else:
        # Create a Dictionary of the Map's Territories
        territories = {}
        for territory in Territory.objects.filter(map_id=map_id):
            territories[territory.api_id] = territory

        return territories


# Fetches Map from dictionary if it exists.
# Otherwise, fetches Map from DB if it exists there and creates territories dictionary.
# Throws Maps.DoesNotExist if Map doesn't exist in the DB
# Adds Map and Territories to maps
# Returns Map
def get_map(map_id):
    logging.debug(f'Getting Map {map_id}')
    # If map is not in the dictionary
    if map_id not in maps:
        map = Map.objects.get(pk=map_id)
            
        territories = get_territories(maps, map_id)
        add_to_maps(map, territories)

    # Return map
    return maps[map_id]['map']


# Adds Template and Cards Settings to templates
def add_to_templates(template, cards_settings):
    templates[template.id] = {'template': template, 'cards_settings': cards_settings}


def get_cards_settings(template_id):
    if template_id in templates:
        return templates[template_id]['cards_settings']
    else:
        # And add the template and list of Card Settings to the dictionary
        cards_settings = {}
        for card_settings in TemplateCardSetting.objects.filter(template_id=template_id):
            cards_settings[card_settings.card_id] = card_settings
        
        return cards_settings


# Fetches Template from imput template dictionary if it exists
# Otherwise, Fetches Template from DB if it exists there and creates card settings dictionary
# Throws Template.DoesNotExist if Template doesn't exist in the DB
# Adds Template and Cards Settings to templates
# Returns Template
def get_template(template_id):
    # if template is not in the dictionary
    if template_id  not in templates:
        template = Template.objects.get(pk=template_id)

        cards_settings = get_cards_settings(template_id)
        add_to_templates(template, cards_settings)

    # Return template from dictionary
    return templates[template_id]['template']


# Clears the players cache
def clear_players():
    players = {}


# Add the player to the players cache. Uses Player ID as default, but will key on input ID if provided
def add_to_players(player, player_id=None):
    players[player_id if bool(player_id) else player.id] = player


# Fetches Player from DB if it exists.
# Throws Player.DoesNotExist if Player doesn't exist in the DB
# Add the player to the players cache. Uses Player ID as default, but keys on API ID if are_id_key_different == True
# Returns Player
def get_player(player_id, are_id_key_different=False):
    if player_id not in players:
        player = Player.objects.get(pk=player_id)
        player_id = player.get_api_id() if are_id_key_different else player.id
        add_to_players(player, player_id)
        
    return players[player_id]
