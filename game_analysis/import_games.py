import logging

from datetime import datetime
from json import loads as json_loads
from pytz import UTC
from typing import Dict, List, Optional, Set, Tuple
from urllib.error import URLError

from . import api
from . import cache
from .models import *


# Tuple of custom argument for the settings of each card type
# Key is the field in the DB
# Value is the corresponding key in the API
CARD_SETTINGS_FIELD_MAPPINGS: Tuple[Dict[str, str], ...] = (
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


# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)


# Lists of objects to save in bulk to DB
games_to_save: List[Game] = []
games_to_update: List[Game] = []
player_accounts_to_save: List[PlayerAccount] = []
territory_baselines_to_save: List[TerritoryBaseline] = []
players_to_save: List[Player] = []
turns_to_save: List[Turn] = []
orders_to_save: List[Order] = []
attack_results_to_save: List[AttackResult] = []


# Clear lists of objects to save
def _clear_save_queue() -> None:
    games_to_save.clear()
    games_to_update.clear()
    player_accounts_to_save.clear()
    territory_baselines_to_save.clear()
    players_to_save.clear()
    turns_to_save.clear()
    orders_to_save.clear()
    attack_results_to_save.clear()


# Save game and associated objects
def _save_games_in_queue() -> None:
    Game.objects.bulk_create(games_to_save)
    Game.objects.bulk_update(games_to_update, ['ladder'])
    PlayerAccount.objects.bulk_create(player_accounts_to_save)
    TerritoryBaseline.objects.bulk_create(territory_baselines_to_save)
    Player.objects.bulk_create(players_to_save)
    Turn.objects.bulk_create(turns_to_save)
    Order.objects.bulk_create(orders_to_save)
    AttackResult.objects.bulk_create(attack_results_to_save)


# Fetches PlayerAccount from DB if it exists. Otherwise creates PlayerAccount
# from Node and queue it for insertion to the DB
def _get_player_account(player_node: Dict[str, str]) -> PlayerAccount:
    try:
        return cache.get_player_account(int(player_node['id']))
    except PlayerAccount.DoesNotExist:
        player_account = PlayerAccount(
            id=int(player_node['id']), name=player_node['name'])
        cache.add_player_account_to_cache(player_account)
        player_accounts_to_save.append(player_account)
        return player_account


# Parse Player data and queue it for insertion to the DB
def _parse_players(game: Game, game_json: dict) -> None:
    logging.debug(f'Adding Players to Game {game.id}')

    player_nodes = game_json['players']
    for player_node in player_nodes:
        # Get the player account
        player_account = _get_player_account(player_node)

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
def _import_territories_and_bonuses(map: Map, territories_node: dict,
        bonuses_node: dict) -> None:
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
def _get_territory(map_id: int, territory_id: int) -> Territory:
    return cache.get_territory(map_id, territory_id, True)


# Fetches Mapfor_importonary if it exists.
# Otherwise, fetches Map from DB if it exists there and creates territories 
# dictionary. Otherwise creates Map from Node, saves it to DB and dictionary,
# and creates territories dictionary. Returns Map
def get_map(map_node: dict) -> Map:
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
        _import_territories_and_bonuses(map, map_node['territories'],
            map_node['bonuses'])

        cache.add_map_to_cache(map_id, True)
        return map


# Import all Overridden Bonuses to the DB for a given Template
def _import_overridden_bonuses(template: Template,
        overridden_bonus_nodes: dict) -> None:
    # TODO - not needed for 1v1 ladder template
    pass


# Parse Template Card Settings and queue it for insertion to the DB
def _parse_card_settings(cards_settings_to_save: List[TemplateCardSetting],
        template: Template, card_id: int, settings_node: dict,
        field_mappings: Dict[str, str]) -> None:
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
def _import_cards_settings(template: Template, settings_node: dict) -> None:
    cards_settings_to_save: List[TemplateCardSetting] = []
    for index, card_field_mappings in enumerate(CARD_SETTINGS_FIELD_MAPPINGS):
        _parse_card_settings(cards_settings_to_save, template, index + 1,
            settings_node, card_field_mappings)
    
    # Save Template Card Settings to DB
    TemplateCardSetting.objects.bulk_create(cards_settings_to_save)


# Fetches Template from imput template dictionary if it exists
# Otherwise, Fetches Template from DB if it exists there and creates card
# settings dictionary. Otherwise creates Template from game_json, saves it to
# DB and dictionary, and creates card settings dictionary. Returns Template
def _get_template(game_json: dict) -> Template:
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

        _import_overridden_bonuses(template, settings['OverriddenBonuses'])
        _import_cards_settings(template, settings)

        cache.add_template_to_cache(template)
        return template


# Parse baseline
def _parse_baseline(game: Game, map_id: int, initial_state_node: dict) -> None:
    template = cache.get_template(game.template_id)
    wasteland_size = template.wasteland_size
    out_distribution_size = template.out_distribution_neutrals
    in_distribution_size = template.in_distribution_neutrals

    for territory_node in initial_state_node:
        territory_owner = territory_node['ownedBy']
        territory = _get_territory(map_id, int(territory_node['terrID']))
        armies = int(territory_node['armies'])

        # If territory is not owned by Neutral it is in distribution
        if territory_owner != cache.get_neutral_name():
            baseline_state = cache.get_in_distribution_baseline_state()

        # Check if the territory is generically out of distribution
        elif armies == out_distribution_size:
            # Don't store out of distribution territories
            continue
        
        # Check if the territory is wastelanded
        elif armies == wasteland_size:
            baseline_state = cache.get_wasteland_baseline_state()

        # Otherwise territory is in distribution in an auto distribution game
        else:
            baseline_state = cache.get_in_distribution_baseline_state()

        # Create Territory Baseline and queue it for insertion to the DB
        territory_baselines_to_save.append(
            TerritoryBaseline(
                game = game,
                territory = territory,
                state = baseline_state
            )
        )


# Parse the picks turn and queue it for insertion to the DB
def _parse_picks_turn(game: Game, map_id: int, picks_node: dict,
        after_picks_state_node: dict) -> None:
    turn = Turn(game=game, turn_number=-1)
    
    # Get pick results
    # Needed since the api doesn't reveal who received which picks otherwise
    raw_pick_results: Dict[int, Set[int]] = {}
    for territory_node in after_picks_state_node:
        territory_owner = territory_node['ownedBy']
        territory_id = int(territory_node['terrID'])

        # If owner is not neutral
        if territory_owner != cache.get_neutral_name():
            territory_owner = int(territory_owner)
            if territory_owner not in raw_pick_results.keys():
                raw_pick_results[territory_owner] = {territory_id}
            else:
                raw_pick_results[territory_owner].add(territory_id)

    order_number = 0
    initial_armies = cache.get_template(game.template_id).initial_armies

    for _, player_node_key in enumerate(picks_node):
        # Get Player from node by stripping the prefix ('player_') and looking
        #   up the id
        player_api_id = int(player_node_key[7:])
        player = cache.get_player(game.id, player_api_id)
    
        for pick, territory_id in enumerate(picks_node[player_node_key]):
            territory = _get_territory(map_id, territory_id)
            is_successful = territory.api_id in raw_pick_results[player_api_id]
            _parse_pick_order(territory, turn, order_number, False, player,
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
            _parse_pick_order(_get_territory(map_id, territory_id), turn,
                order_number, True, player, True, initial_armies)
            
            order_number += 1

    turns_to_save.append(turn)


# Parse pick Order and queue it for insertion to the DB
def _parse_pick_order(territory: Territory, turn: Turn, order_number: int,
        is_auto_pick: bool, player: Player, is_successful: bool,
        initial_armies: int) -> None:
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
def _parse_basic_order(turn: Turn, order_number: int,
        order_node: dict) -> None:
    order = Order(
        turn = turn,
        order_number = order_number,
        order_type = cache.get_order_type(order_node['type']),
        player = cache.get_player(turn.game.id, 
            int(order_node['playerID'])))
    orders_to_save.append(order)


# Parse deploy Order and queue it for insertion to the DB
def _parse_deploy_order(turn: Turn, map_id: int, order_number: int,
        order_node: dict) -> None:
    order = Order(
        turn = turn,
        order_number = order_number,
        order_type = cache.get_order_type(order_node['type']),
        player = cache.get_player(turn.game.id, 
            int(order_node['playerID'])),
        primary_territory = _get_territory(map_id,
            int(order_node['deployOn'])),
        armies = order_node['armies'])
    orders_to_save.append(order)


# Parse attack/transfer Order and queue it for insertion to the DB
def _parse_attack_transfer_order(turn: Turn, map_id: int, order_number: int,
        order_node: dict) -> None:
    order = Order(
        turn=turn,
        order_number=order_number,
        order_type = cache.get_order_type(order_node['type']),
        player = cache.get_player(turn.game.id, 
            int(order_node['playerID'])),
        primary_territory = _get_territory(map_id, int(order_node['from'])),
        secondary_territory = _get_territory(map_id, int(order_node['to'])),
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
def _parse_basic_play_card_order(turn: Turn, order_number: int,
        order_node: dict) -> None:
    order = Order(
        turn=turn,
        order_number = order_number,
        order_type = cache.get_order_type(order_node['type']),
        player = cache.get_player(turn.game.id, 
            int(order_node['playerID'])),
        card_id = order_node['cardInstanceID'])
    orders_to_save.append(order)


# Parse blockade Order and queue it for insertion to the DB
def _parse_blockade_order(turn: Turn, map_id: int, order_number: int,
        order_node: dict) -> None:
    order = Order(
        turn=turn,
        order_number = order_number,
        order_type = cache.get_order_type(order_node['type']),
        player = cache.get_player(turn.game.id, 
            int(order_node['playerID'])),
        primary_territory = _get_territory(map_id,
            int(order_node['targetTerritoryID'])),
        card_id = order_node['cardInstanceID'])
    orders_to_save.append(order)


# Parses the Orders for a Turn and queue them for insertion to the DB
def _parse_orders(turn: Turn, map_id: int, order_nodes: List[dict]) -> None:
    for order_number, order_node in enumerate(order_nodes):
        order_node = order_nodes[order_number]
        if order_node['type'] == 'GameOrderDeploy':
            _parse_deploy_order(turn, map_id, order_number, order_node)
        elif order_node['type'] == 'GameOrderAttackTransfer':
            _parse_attack_transfer_order(turn, map_id, order_number, 
                order_node)
        elif order_node['type'] in [
                'GameOrderReceiveCard', 
                'GameOrderStateTransition']:
            # TODO Confirm that this is sufficient for State Transition
            # (not needed for 1v1 games where ai does not take over)
            _parse_basic_order(turn, order_number, order_node)
        elif order_node['type'] in [
                'GameOrderPlayCardReinforcement',
                'GameOrderPlayCardOrderPriority',
                'GameOrderPlayCardOrderDelay']:
            _parse_basic_play_card_order(turn, order_number, order_node)
        elif order_node['type'] == 'GameOrderPlayCardBlockade':
            _parse_blockade_order(turn, map_id, order_number, order_node)
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
def _parse_turns(game: Game, map_id: int, game_json: dict) -> None:
    logging.debug(f'Importing Turns for Game {game.id}')
    # Create list of turn nodes
    turn_nodes: List[dict] = []
    for key in game_json:
        if key.startswith('turn'):
            turn_nodes.append(game_json[key])

    # Get picks node for manual distribution games - otherwise use empty list
    try:
        picks_node = game_json['picks']
        baseline_standing = game_json['distributionStanding']
    except KeyError:
        picks_node = {}
        baseline_standing = game_json['standing0']
    
    # Parse Game baseline
    _parse_baseline(game, map_id, baseline_standing)

    # Import picks
    _parse_picks_turn(game, map_id, picks_node, game_json['standing0'])

    for turn_number, turn_node in enumerate(turn_nodes):
        # create Turn object and set fields
        commit_date_time = datetime.strptime(turn_node['date'],
            '%m/%d/%Y %H:%M:%S').replace(tzinfo=UTC)
        turn = Turn(
            game = game,
            turn_number = turn_number,
            commit_date_time = commit_date_time)
    
        _parse_orders(turn, map_id, turn_node['orders'])

        turns_to_save.append(turn)

    # Save Orders, Territory States, and Card States to DB

    logging.debug(
        f'Imported {game.number_of_turns} Turns.'
    )

    
# Parse Game and queue it for insertion to the DB
def _parse_game(game_data: bytes,
        ladder: Optional[Ladder] = None) -> Optional[Game]:
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

    template = _get_template(game_json)

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

        cache.add_game_to_cache(game)
        _parse_players(game, game_json)
        _parse_turns(game, template.map_id, game_json)
        games_to_save.append(game)
        
        logging.debug(f'Finished parsing Game {game}')
        return game


# Imports a Ladder Game with the given ID into the DB along with associated
# data if they do not yet exist. Does nothing if the Game already exists.
# If the Games already exists but doesn't have the correct Ladder, updates it.
# Returns the Game if it is imported and None otherwise
def _parse_ladder_game(email: str, api_token: str, game_id: int, offset: int,
        ladder: Ladder) -> Optional[Game]:
    logging.info(f'Parsing game {game_id}: Offset {offset}')
    cache.clear_games_from_cache()

    try:
        # Check if Game already exists
        additional_info = ''
        game_from_db = Game.objects.get(pk=game_id)
        
        # If Game exists check that it has the correct Ladder
        if ladder and game_from_db.ladder_id != ladder.id:
            game_from_db.ladder = ladder
            games_to_update.append(game_from_db)
            additional_info = f'Ladder set to {ladder}.'

        logging.debug(f'Game {game_id} already exists. {additional_info}')
        return None
    except Game.DoesNotExist:
        logging.debug(f'Retrieving Game {game_id} data from Warzone')
        
        # Retrieve Game data
        game_data = api.get_game_data_from_id(email, api_token, game_id)

        # Parse Game data
        new_game = _parse_game(game_data, ladder)
        return new_game


# Imports a Game into with the given ID into the DB along with associated data
# if they do not yet exist. Does nothing if the Game already exists.
# Returns the Game if it is imported and None otherwise
def import_game(email: str, api_token: str, game_id: int) -> Optional[Game]:
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
        _clear_save_queue()

        # Parse Game data
        game = _parse_game(game_data)

        # Save Game to DB
        _save_games_in_queue()

        return game


# Imports max_results Games (and associated data) from the specified ladder
# starting from offset. For each Game, does nothing if the Game already exists
# Return the count of games imported
def import_ladder_games(email: str, api_token: str, ladder_id: int,
        max_results: int, offset: int, games_per_page: int) -> int:
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
        _clear_save_queue()
        
        # Import each game if it does not yet exist
        try:
            for game_id in game_ids:
                if _parse_ladder_game(email, api_token, game_id,
                        imported_games_count, ladder):
                    successful_imported_games_count += 1
                imported_games_count += 1
        except URLError as e:
            raise URLError(
                f'Connection failed getting game data for game {game_id} '
                f'after importing {imported_games_count} games.'
            ) from e

        # Save Games to DB
        _save_games_in_queue()

        results_left_to_get -= len(game_ids)
        offset +=games_per_page
    
    return successful_imported_games_count
