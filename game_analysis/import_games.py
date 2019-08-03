import json
import sys

from . import api
from .models import Game, Player, Card
# todo move this into a view

ADMIN_EMAIL = 'redacted'
ADMIN_PASSWORD = 'redacted'

# MAX_OFFSET = 154850
MAX_OFFSET = 0
# RESULTS_PER_PAGE = 50
RESULTS_PER_PAGE = 1
ONE_VS_ONE_LADDER_ID = 0

offset = 0

print(Card.objects.all())

api_token_response = api.get_api_token(ADMIN_EMAIL, ADMIN_PASSWORD)
api_token = json.loads(api_token_response)['APIToken']

# Fetches Player from DB if it exists.
# Otherwise creates Player from Node and saves it to DB
# Returns Player
def get_player(player_node):
    try:
        return Player.objects.get(id=player_node['id'])
    except Player.DoesNotExist:
        player = Player(id=player_node['id'], name=player_node['name'])
        player.save()
        return player


while offset <= MAX_OFFSET:
    # Retrieve game ids at offset
    game_ids = api.get_ladder_game_ids(ONE_VS_ONE_LADDER_ID, offset, RESULTS_PER_PAGE)

    for game_id in game_ids:
        # Retrieve game data
        game_data = api.get_game_data_from_id(game_id, ADMIN_EMAIL, api_token)
        
        # todo parse game data
        game_json = json.loads(game_data)
        game = Game(id=game_json['id'], name=game_json['name'], number_of_turns=game_json['numberOfTurns'])

        player_nodes = game_json['players']
        for player_node in player_nodes:
            game.players.add(get_player(player_node))

        # todo persist into db
        game.save()
    offset += RESULTS_PER_PAGE
