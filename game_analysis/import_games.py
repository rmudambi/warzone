import logging

from datetime import datetime
from json import loads as json_loads
from pytz import UTC
from urllib.error import URLError

from . import api
from . import cache
from .models import *

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)


# Lists of objects to save in bulk to DB
games_to_save = []
games_to_update = []
player_accounts_to_save = []
players_to_save = []
turns_to_save = []
orders_to_save = []
attack_results_to_save = []


# Clear lists of objects to save
def clear_save_queue():
    games_to_save.clear()
    games_to_update.clear()
    player_accounts_to_save.clear()
    players_to_save.clear()
    turns_to_save.clear()
    orders_to_save.clear()
    attack_results_to_save.clear()


# Save game and associated objects
def save_games_in_queue():
    Game.objects.bulk_create(games_to_save)
    Game.objects.bulk_update(games_to_update, ['ladder'])
    PlayerAccount.objects.bulk_create(player_accounts_to_save)
    Player.objects.bulk_create(players_to_save)
    Turn.objects.bulk_create(turns_to_save)
    Order.objects.bulk_create(orders_to_save)
    AttackResult.objects.bulk_create(attack_results_to_save)


# Fetches PlayerAccount from DB if it exists. Otherwise creates PlayerAccount
# from Node and queue it for insertion to the DB
def get_player_account(player_node):
    try:
        return cache.get_player_account(int(player_node['id']))
    except PlayerAccount.DoesNotExist:
        player_account = PlayerAccount(
            id=int(player_node['id']), name=player_node['name'])
        cache.add_player_account_to_cache(player_account)
        player_accounts_to_save.append(player_account)
        return player_account


# Parse Player data and queue it for insertion to the DB
def parse_players(game, game_json):
    logging.debug(f'Adding Players to Game {game.id}')

    player_nodes = game_json['players']
    for player_node in player_nodes:
        # Get the player account
        player_account = get_player_account(player_node)

        # Create Player
        player = Player(
            game=game,
            player=player_account,
            end_state=cache.get_player_state_type(player_node['state'])
        )

        #  Save Player to cache and queue to be saved to DB
        cache.add_player_to_cache(player, player_account.get_api_id())
        players_to_save.append(player)


# Import all territories and bonuses to the DB for a given Map
def import_territories_and_bonuses(map, territories_node, bonuses_node):
    # Dictionary of Territory api_ids to Territories
    territories = {}

    # Import all Territories to the DB and add them to the dictionary
    for territory_node in territories_node:
        territory = Territory(map=map, api_id=int(territory_node['id']),
            name=territory_node['name'])
        territories[territory.api_id] = territory
    
    # Save Territories to DB
    Territory.objects.bulk_create(list(territories.values()))

    # Import connected territories to the DB for each Territory in the Map
    Connections = Territory.connected_territories.through
    connections = []
    for territory_node in territories_node:
        territory_id = int(territory_node['id'])
        territory = territories[territory_id]
        for connection_id in territory_node['connectedTo']:
            connections.append(
                Connections(from_territory=territories[territory_id],
                    to_territory=territories[connection_id]))

    # Save Connections to DB
    Connections.objects.bulk_create(connections)

    # Import Bonuses and BonusTerritories
    bonuses = []
    bonus_territories = []
    for bonus_node in bonuses_node:
        bonus = Bonus(map=map, api_id=bonus_node['id'],
            name=bonus_node['name'], base_value=bonus_node['value'])
        bonuses.append(bonus)
        for territory_id in bonus_node['territoryIDs']:
            territory = BonusTerritory(bonus=bonus, 
                territory=territories[territory_id])
            bonus_territories.append(territory)

    # Save Bonuses and Territories to DB
    Bonus.objects.bulk_create(bonuses)
    BonusTerritory.objects.bulk_create(bonus_territories)


# Gets the Territory specified by the map id and territory id
def get_territory(map_id, territory_id):
    return cache.get_territory(map_id, territory_id, True)


# Fetches Mapfor_importonary if it exists.
# Otherwise, fetches Map from DB if it exists there and creates territories 
# dictionary. Otherwise creates Map from Node, saves it to DB and dictionary,
# and creates territories dictionary. Returns Map
def get_map(map_node):
    map_id = int(map_node['id'])
    logging.debug(f'Getting Map {map_id}')

    try:
        # Get Map if it exists already
        return cache.get_map(map_id, True)
    except Map.DoesNotExist:
        # Otherwise, create map and save it to the DB
        logging.info(f'Creating Map {map_id}')
        map = Map(id=map_id, name=map_node['name'])
        map.save()
        
        # Import Territories and Bonuses
        import_territories_and_bonuses(map, map_node['territories'],
            map_node['bonuses'])

        cache.add_map_to_cache(map_id, True)
        return map


# Import all Overridden Bonuses to the DB for a given Template
def import_overridden_bonuses(template, overridden_bonus_nodes):
    # TODO - not needed for 1v1 ladder template
    pass


# Parse Template Card Settings and queue it for insertion to the DB
def parse_card_settings(cards_settings_to_save, template, card_id,
        settings_node, field_mappings):
    card = cache.get_card(card_id)
    card_node = settings_node[card.name.replace(' ', '')]

    if card_node != 'none':
        fields = {
            'template': template,
            'card': card,
            'number_of_pieces': card_node['NumPieces'],
            'initial_pieces': card_node['InitialPieces'],
            'min_pieces_per_turn': card_node['MinimumPiecesPerTurn'],
            'weight': card_node['Weight'],
            'mode': None,
            'value': None,
            'duration': None
        }
        
        for db_field_name in field_mappings:
            fields[db_field_name] = card_node[field_mappings[db_field_name]]
        
        cards_settings_to_save.append(TemplateCardSetting(**fields))


# Import Card Settings to the DB for a given Template
def import_cards_settings(template, settings_node):
    # List of custom argument for the settings of each card type
    # Key is the field in the DB
    # Value is the corresponding key in the API
    field_mappings = (
        # Reinforcement
        # TODO support other reinforcement card modes
        # not needed for most (all?) strategic templates
        {'mode': 'Mode', 'value': 'FixedArmies'},
        # Spy
        {'mode': 'CanSpyOnNeutral', 'duration': 'Duration'},
        # Abandon
        {'value': 'MultiplyAmount'},
        # Order Priority
        {},
        # Order Delay
        {},
        # Airlift
        {},
        # Gift
        {},
        # Diplomacy
        {'duration': 'Duration'},
        # Sanctions
        {'value': 'Percentage', 'duration': 'Duration'},
        # Reconnaissance
        {'duration': 'Duration'},
        # Surveillance
        {'duration': 'Duration'},
        # Blockade
        {'value': 'MultiplyAmount'},
        # Bomb
        {}
    )

    cards_settings_to_save = []
    for index, card_field_mappings in enumerate(field_mappings):
        parse_card_settings(cards_settings_to_save, template, index + 1,
            settings_node, card_field_mappings)
    
    # Save Template Card Settings to DB
    TemplateCardSetting.objects.bulk_create(cards_settings_to_save)


# Fetches Template from imput template dictionary if it exists
# Otherwise, Fetches Template from DB if it exists there and creates card
# settings dictionary. Otherwise creates Template from game_json, saves it to
# DB and dictionary, and creates card settings dictionary. Returns Template
def get_template(game_json):
    template_id = int(game_json['templateID'])

    try:
        # Get Template if it exists already
        return cache.get_template(template_id)
    except Template.DoesNotExist:
        # Otherwise create template
        logging.info(f'Creating Template {template_id}')
        
        settings = game_json['settings']
        template = Template(
            id = template_id,
            map = get_map(game_json['map']),
            is_multi_day = settings['Pace'] == 'MultiDay',
            fog_level = FogLevel.objects.get(pk=settings['Fog']),
            is_multi_attack = settings['MultiAttack'],
            allow_transfer_only = settings['AllowTransferOnly'],
            allow_attack_only = settings['AllowAttackOnly'],
            is_cycle_move_order = settings['MoveOrder'] == 'Cycle',
            is_booted_to_ai = settings['BootedPlayersTurnIntoAIs'],
            is_surrender_to_ai = settings['SurrenderedPlayersTurnIntoAIs'],
            times_return_from_ai = settings['TimesCanComeBackFromAI'],
            is_manual_distribution = (
                settings['AutomaticTerritoryDistribution'] == 'Manual'),
            distribution_mode = settings['DistributionMode'],
            territory_limit = settings['TerritoryLimit'],
            initial_armies = settings['InitialPlayerArmiesPerTerritory'],
            out_distribution_neutrals = (
                settings['InitialNonDistributionArmies']),
            in_distribution_neutrals = (
                settings['InitialNeutralsInDistribution']),
            wasteland_count = settings['Wastelands']['NumberOfWastelands'],
            wasteland_size = settings['Wastelands']['WastelandSize'],
            # TODO add support for Commerce templates
            # not needed for most strategic templates
            is_commerce = False,
            has_commanders = settings['Commanders'],
            is_one_army_stand_guard = settings['OneArmyStandsGuard'],
            base_income = settings['MinimumArmyBonus'],
            luck_modifier = settings['LuckModifier'],
            is_straight_round = settings['RoundingMode'] == 'StraightRound',
            bonus_army_per = (settings['BonusArmyPer']
                if settings['BonusArmyPer'] != 0  else None),
            army_cap = (settings['ArmyCap']
                if settings['ArmyCap'] != 'null' else None),
            offensive_kill_rate = settings['OffensiveKillRate'],
            defensive_kill_rate = settings['DefensiveKillRate'],
            is_local_deployment = settings['LocalDeployments'],
            is_no_split = settings['NoSplit'],
            max_cards = settings['MaxCardsHold'],
            card_pieces_per_turn = settings['NumberOfCardsToReceiveEachTurn'],
            card_playing_visible = not settings['CardPlayingsFogged'],
            card_visible = not settings['CardsHoldingAndReceivingFogged'],
            uses_mods = bool(settings['Mods']))
        
        template.save()

        import_overridden_bonuses(template, settings['OverriddenBonuses'])
        import_cards_settings(template, settings)

        cache.add_template_to_cache(template)
        return template


# Parse the picks turn and queue it for insertion to the DB
def parse_picks_turn(game, map_id, picks_node, state_node):
    turn = Turn(game=game, turn_number=-1)
    
    # Get pick results
    # Needed since the api doesn't reveal who received which picks otherwise
    raw_pick_results = {}
    for territory_node in state_node:
        territory_owner = territory_node['ownedBy']
        territory = int(territory_node['terrID'])

        # If owner is not neutral or available for distribution
        if territory_owner not in cache.get_neutral_player_names():
            territory_owner = int(territory_owner)
            if territory_owner not in raw_pick_results.keys():
                raw_pick_results[territory_owner] = set([territory])
            else:
                raw_pick_results[territory_owner].add(territory)

    order_number = 0
    initial_armies = cache.get_template(game.template_id).initial_armies

    for player_number, player_node_key in enumerate(picks_node):
        # Get Player from node by stripping the prefix ('player_') and looking
        #   up the id
        player_api_id = int(player_node_key[7:])
        player = cache.get_player(game.id, player_api_id)
    
        for pick, territory_id in enumerate(picks_node[player_node_key]):
            territory = get_territory(map_id, territory_id)
            is_successful = territory.api_id in raw_pick_results[player_api_id]
            parse_pick_order(territory, turn, order_number, False, player,
                is_successful, initial_armies)
            
            # If the player controls the territory after picks
            if is_successful:
                # Remove territory from list of territories
                raw_pick_results[player_api_id].remove(territory.api_id)

            order_number += 1

    # All leftover territories must have been assigned randomly due to the
    #   player not making enough picks
    for player_api_id in raw_pick_results:
        player = cache.get_player(game.id, player_api_id)
        for territory_id in raw_pick_results[player_api_id]:
            parse_pick_order(get_territory(map_id, territory_id), turn,
                order_number, True, player, True, initial_armies)
            
            order_number += 1

    turns_to_save.append(turn)


# Parse pick Order and queue it for insertion to the DB
def parse_pick_order(territory, turn, order_number, is_auto_pick, player,
        is_successful, initial_armies):
    order = Order(
        turn = turn,
        order_number = order_number,
        order_type = cache.get_order_type(
            'GameOrderAutoPick' if is_auto_pick else 'GameOrderPick'),
        player = player,
        primary_territory = territory)

    attack_result = AttackResult(
        order = order,
        attack_transfer = 'AutoPick' if is_auto_pick else 'Pick',
        attack_size = initial_armies,
        attacking_armies_killed = 0,
        is_successful = is_successful)

    orders_to_save.append(order)
    attack_results_to_save.append(attack_result)


# Parse basic Order and queue it for insertion to the DB
def parse_basic_order(turn, order_number, order_node):
    order = Order(
        turn = turn,
        order_number = order_number,
        order_type = cache.get_order_type(order_node['type']),
        player = cache.get_player(turn.game.id, 
            int(order_node['playerID'])))
    orders_to_save.append(order)


# Parse deploy Order and queue it for insertion to the DB
def parse_deploy_order(turn, map_id, order_number, order_node):
    order = Order(
        turn = turn,
        order_number = order_number,
        order_type = cache.get_order_type(order_node['type']),
        player = cache.get_player(turn.game.id, 
            int(order_node['playerID'])),
        primary_territory = get_territory(map_id, int(order_node['deployOn'])),
        armies = order_node['armies'])
    orders_to_save.append(order)


# Parse attack/transfer Order and queue it for insertion to the DB
def parse_attack_transfer_order(turn, map_id, order_number, order_node):
    order = Order(
        turn=turn,
        order_number=order_number,
        order_type = cache.get_order_type(order_node['type']),
        player = cache.get_player(turn.game.id, 
            int(order_node['playerID'])),
        primary_territory = get_territory(map_id, int(order_node['from'])),
        secondary_territory = get_territory(map_id, int(order_node['to'])),
        armies = order_node['numArmies'])
    orders_to_save.append(order)
    
    # Parse AttackResult node
    result_node = order_node['result']
    attack_result = AttackResult(
        order = order,
        attack_transfer = order_node['attackTransfer'],
        is_attack_teammates = order_node['attackTeammates'],
        is_attack_by_percent = order_node['byPercent'],
        is_attack = result_node['isAttack'],
        is_successful = result_node['isSuccessful'],
        attack_size = result_node['armies'],
        attacking_armies_killed = result_node['attackingArmiesKilled'],
        defending_armies_killed = result_node['defendingArmiesKilled'],
        offense_luck = 0.0 if not result_node['offenseLuck'] 
            else float(result_node['offenseLuck']),
        defense_luck = 0.0 if not result_node['defenseLuck'] 
            else float(result_node['defenseLuck']))
    attack_results_to_save.append(attack_result)
        

# Parse basic play card Order and queue it for insertion to the DB
def parse_basic_play_card_order(turn, order_number, order_node):
    order = Order(
        turn=turn,
        order_number = order_number,
        order_type = cache.get_order_type(order_node['type']),
        player = cache.get_player(turn.game.id, 
            int(order_node['playerID'])),
        card_id = order_node['cardInstanceID'])
    orders_to_save.append(order)


# Parse blockade Order and queue it for insertion to the DB
def parse_blockade_order(turn, map_id, order_number, order_node):
    order = Order(
        turn=turn,
        order_number = order_number,
        order_type = cache.get_order_type(order_node['type']),
        player = cache.get_player(turn.game.id, 
            int(order_node['playerID'])),
        primary_territory = get_territory(map_id,
            int(order_node['targetTerritoryID'])),
        card_id = order_node['cardInstanceID'])
    orders_to_save.append(order)


# Parses state transition Order
def import_state_transition_order(order, order_node):
    # TODO implement state transitions (not needed for 1v1 games where ai
    #   does not take over)
    pass


# Parses the Orders for a Turn and queue them for insertion to the DB
def parse_orders(turn, map_id, order_nodes):
    for order_number, order_node in enumerate(order_nodes):
        order_node = order_nodes[order_number]
        if order_node['type'] == 'GameOrderDeploy':
            parse_deploy_order(turn, map_id, order_number, order_node)
        elif order_node['type'] == 'GameOrderAttackTransfer':
            parse_attack_transfer_order(turn, map_id, order_number, order_node)
        elif order_node['type'] in [
                'GameOrderReceiveCard', 
                'GameOrderStateTransition']:
            # TODO Confirm that this is sufficient for State Transition
            # (not needed for 1v1 games where ai does not take over)
            parse_basic_order(turn, order_number, order_node)
        elif order_node['type'] in [
                'GameOrderPlayCardReinforcement',
                'GameOrderPlayCardOrderPriority',
                'GameOrderPlayCardOrderDelay']:
            parse_basic_play_card_order(turn, order_number, order_node)
        elif order_node['type'] == 'GameOrderPlayCardBlockade':
            parse_blockade_order(turn, map_id, order_number, order_node)
        elif order_node['type'] == 'GameOrderPlayCardSpy':
            # TODO not needed for 1v1 ladder
            pass
        elif order_node['type'] == 'GameOrderPlayCardAbandon':
            # TODO not needed for 1v1 ladder
            pass
        elif order_node['type'] == 'GameOrderPlayCardAirlift':
            # TODO not needed for 1v1 ladder
            pass
        elif order_node['type'] == 'GameOrderPlayCardGift':
            # TODO not needed for 1v1 ladder
            pass
        elif order_node['type'] == 'GameOrderPlayCardDiplomacy':
            # TODO not needed for 1v1 ladder
            pass
        elif order_node['type'] == 'GameOrderPlayCardSanctions':
            # TODO not needed for 1v1 ladder
            pass
        elif order_node['type'] == 'ActiveCardWoreOff':
            # TODO not needed for 1v1 ladder
            pass


# Parse Turns and queue for insertion into the DB
def parse_turns(game, map_id, game_json):
    logging.debug(f'Importing Turns for Game {game.id}')
    # Create list of turn nodes
    turn_nodes = []
    for key in game_json:
        if key.startswith('turn'):
            turn_nodes.append(game_json[key])

    # Get picks node for manual distribution games - otherwise use empty list
    try:
        picks_node = game_json['picks']
    except KeyError:
        picks_node = []
    
    # Import picks
    parse_picks_turn(game, map_id, picks_node, game_json['standing0'])

    for turn_number, turn_node in enumerate(turn_nodes):
        # create Turn object and set fields
        commit_date_time = datetime.strptime(turn_node['date'],
            '%m/%d/%Y %H:%M:%S').replace(tzinfo=UTC)
        turn = Turn(
            game = game,
            turn_number = turn_number,
            commit_date_time = commit_date_time)
    
        parse_orders(turn, map_id, turn_node['orders'])

        turns_to_save.append(turn)

    # Save Orders, Territory States, and Card States to DB

    logging.debug(
        f'Imported {game.number_of_turns} Turns.'
    )

    
# Parse Game and queue it for insertion to the DB
def parse_game(game_data, ladder=None):
    game_json = json_loads(game_data)
    game_id = game_json['id']

    try:
        # Will throw KeyError if map node doesn't exist
        # TODO this should be fixed by Fizzer soon
        map = game_json['map']
    except KeyError:
        # Map node doesn't exist, so game ended on turn -1
        # Ignore game, since it adds no value
        logging.debug(
            f'Game {game_id} has no map node. Game ended on turn -1'
        )
        return None

    template = get_template(game_json)

    if int(map['id']) != template.map_id:
        # Map doesn't match the map in the template so the template has
        #   changed
        # TODO add complete template compatibility checks
        return None
    else:
        game = Game(
            id = game_json['id'],
            name = game_json['name'],
            template = template,
            ladder = ladder,
            number_of_turns = game_json['numberOfTurns']
        )

        cache.add_game_to_cache(game, {})
        parse_players(game, game_json)
        parse_turns(game, template.map_id, game_json)
        games_to_save.append(game)
        
        logging.debug(f'Finished parsing Game {game}')
        return game


# Imports a Ladder Game with the given ID into the DB along with associated
# data if they do not yet exist. Does nothing if the Game already exists.
# If the Games already exists but doesn't have the correct Ladder, updates it.
# Returns the Game if it is imported and None otherwise
def parse_ladder_game(email, api_token, game_id, offset, ladder):
    logging.info(f'Parsing game {game_id}: Offset {offset}')
    cache.clear_games_from_cache()

    try:
        # Check if Game already exists
        additional_info = ''
        game = Game.objects.get(pk=game_id)
        
        # If Game exists check that it has the correct Ladder
        if ladder and game.ladder_id != ladder.id:
            game.ladder = ladder
            games_to_update.append(game)
            additional_info = f'Ladder set to {ladder}.'

        logging.debug(f'Game {game_id} already exists. {additional_info}')
        return None
    except Game.DoesNotExist:
        logging.debug(f'Retrieving Game {game_id} data from Warzone')
        
        # Retrieve Game data
        game_data = api.get_game_data_from_id(email, api_token, game_id)

        # Parse Game data
        game = parse_game(game_data, ladder)
        return game


# Imports a Game into with the given ID into the DB along with associated data
# if they do not yet exist. Does nothing if the Game already exists.
# Returns the Game if it is imported and None otherwise
def import_game(email, api_token, game_id):
    logging.info(f'Importing game {game_id}')

    try:
        # Check if Game already exists
        Game.objects.get(pk=game_id)
        logging.debug(f'Game {game_id} already exists.')
        return None
    except Game.DoesNotExist:
        logging.debug(f'Retrieving Game {game_id} data from Warzone')
        
        # Retrieve Game data
        try:
            game_data = api.get_game_data_from_id(email, api_token, game_id)
        except URLError as e:
            raise URLError(
                f'Connection failed getting game data for game {game_id}.'
            ) from e

        # Clear save queue
        clear_save_queue()

        # Parse Game data
        game = parse_game(game_data)

        # Save Game to DB
        save_games_in_queue()

        return game


# Imports max_results Games (and associated data) from the specified ladder
# starting from offset. For each Game, does nothing if the Game already exists
def import_ladder_games(email, api_token, ladder_id, max_results, offset,
        games_per_page):
    results_left_to_get = max_results
    imported_games_count = 0
    successful_imported_games_count = 0

    logging.info(
        f'Retrieving {max_results} ladder games from ladder {ladder_id} '
        f'starting at offset {offset}'
    )

    ladder = cache.get_ladder(ladder_id)

    while 0 < results_left_to_get:
        # Retrieve game ids at offset
        logging.info(
            f'Retrieving {min(games_per_page, max_results)} game ids from '
            f'ladder {ladder}: Offset {offset}.'
        )

        try:
            game_ids = api.get_ladder_game_ids(ladder_id, offset,
                results_left_to_get)
        except URLError as e:
            raise URLError(
                f'Connection failed getting ladder games at offset {offset} '
                f'after importing {imported_games_count} games.'
            ) from e
        
        # If game_ids empty break
        if not game_ids:
            return imported_games_count

        # Clear save queue
        clear_save_queue()
        
        # Import each game if it does not yet exist
        try:
            for game_id in game_ids:
                if parse_ladder_game(email, api_token, game_id,
                        imported_games_count,ladder):
                    successful_imported_games_count += 1
                imported_games_count += 1
        except URLError as e:
            raise URLError(
                f'Connection failed getting game data for game {game_id} '
                f'after importing {imported_games_count} games.'
            ) from e

        # Save Games to DB
        save_games_in_queue()

        results_left_to_get -= len(game_ids)
        offset +=games_per_page
    
    return successful_imported_games_count
