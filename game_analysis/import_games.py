import logging

from copy import deepcopy
from datetime import datetime
from json import loads as json_loads
from pytz import UTC
from uuid import uuid4

from . import api
from .models import *

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Dictionary from card id -> card
cards = {}

# Dictionary from player state type id -> player state types
player_state_types = {}

# Dictionary from card order type id -> order type
order_types = {}

# Neutral and AvailableForDistribution "Players"
neutral_players = {}

# Dictionary from template id -> (template, {card id -> card settings})
templates_cards_settings = {}

# Dictionary from map id-> (map, {territory api id -> territory})
maps_territories = {}

# Dictionary from player api id -> player
players_by_api_id = {}


# Get Card
def get_card(id=id):
    try:
        return cards[id]
    except KeyError:
        cards[id] = Card.objects.get(pk=id)
        return cards[id]


# Get Player State
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


# Fetches Player from DB if it exists.
# Otherwise creates Player from Node and saves it to DB
# Returns Player
def get_player(player_node):
    try:
        return Player.objects.get(pk=player_node['id'])
    except Player.DoesNotExist:
        player = Player(id=player_node['id'], name=player_node['name'])
        player.save()
        return player


# Add Player data to Game
def add_players_to_game(game, game_json):
    # Reset players by api id dictionary
    players_by_api_id.clear()
    game_players = []

    logging.debug(f'Adding Players to Game {game.id}')

    player_nodes = game_json['players']
    for player_node in player_nodes:
        player = get_player(player_node)
        players_by_api_id[player.get_api_id()] = player
        game_players.append(GamePlayer(game=game, player=player, 
                end_state=get_player_state_type(player_node['state'])))
    
    GamePlayer.objects.bulk_create(game_players)


# Import all territories to the DB for a given Map
# Return a Dictionary mapping api ids to Territries
def get_territories(map, territories_node):
    # Dictionary of Territory api_ids to Territories
    territories = {}

    # Import all Territories to the DB and add them to the dictionary
    for territory_node in territories_node:
        territory = Territory(map=map, api_id=int(territory_node['id']), name=territory_node['name'])
        territories[territory.api_id] = territory
    
    # Import all TerritoryConnections to the DB for each Territory in the Map
    territory_connections = []
    for territory_node in territories_node:
        territory_id = int(territory_node['id'])
        territory = territories[territory_id]
        for connection in territory_node['connectedTo']:
            connection = TerritoryConnection(from_territory=territory, to_territory=territories[connection])
            territory_connections.append(connection)
    
    # Save Territories and Connections to DB
    Territory.objects.bulk_create(list(territories.values()))
    TerritoryConnection.objects.bulk_create(territory_connections)

    return territories


# Import all bonuses to the DB for a given Map
def import_bonuses(map, bonuses_node, territories):
    bonuses = []
    bonus_territories = []
    for bonus_node in bonuses_node:
        bonus = Bonus(map=map, api_id=bonus_node['id'], name=bonus_node['name'], base_value=bonus_node['value'])
        bonuses.append(bonus)
        for territory_id in bonus_node['territoryIDs']:
            territory = BonusTerritory(bonus=bonus, territory=territories[territory_id])
            bonus_territories.append(territory)

    # Save Bonuses and Territories to DB
    Bonus.objects.bulk_create(bonuses)
    BonusTerritory.objects.bulk_create(bonus_territories)


# Fetches Map from dictionary if it exists.
# Otherwise, fetches Map from DB if it exists there and creates territories dictionary.
# Otherwise creates Map from Node, saves it to DB and dictionary, and creates territories dictionary.
# Returns Map
def get_map(map_node):
    map_id = int(map_node['id'])
    logging.debug(f'Getting Map {map_id}')
    # If map is not in the dictionary
    if map_id not in maps_territories:
        try:
            # Try to get map from DB
            map = Map.objects.get(pk=map_id)
        except Map.DoesNotExist:
            # Otherwise, create map and save it to the DB
            logging.info(f'Creating Map {map_id}')
            map = Map(id=map_id, name=map_node['name'])
            map.save()
            
            # Import Territories and Bonuses
            territories = get_territories(map, map_node['territories'])
            import_bonuses(map, map_node['bonuses'], territories)
            
        # Create a Dictionary of the Map's Territories
        territories = Territory.objects.filter(map=map)
        map_territories = {}
        for territory in territories:
            map_territories[territory.api_id] = territory

        # Add map and dictionary of map territories to dictionary
        maps_territories[map_id] = (map, map_territories)

    # Return map
    return maps_territories[map_id][0]


# Import all Overridden Bonuses to the DB for a given Template
def import_overridden_bonuses(template, overridden_bonus_nodes):
    # TODO - not needed for 1v1 ladder template
    pass


# Create Template Card Settings initialized with all common fields
def get_card_settings(template, card, card_node):
    card_instance = TemplateCardSetting(template=template, card=card)
    card_instance.number_of_pieces = card_node['NumPieces']
    card_instance.initial_pieces = card_node['InitialPieces']
    card_instance.min_pieces_per_turn = card_node['MinimumPiecesPerTurn']
    card_instance.weight = card_node['Weight']
    return card_instance


# Import Card Settings to the DB for a given Template
def import_card_settings(template, settings_node):
    template_cards_settings = []

    reinforcement_card_node = settings_node['ReinforcementCard']
    spy_card_node = settings_node['SpyCard']
    abandon_card_node = settings_node['AbandonCard']
    op_card_node = settings_node['OrderPriorityCard']
    od_card_node = settings_node['OrderDelayCard']
    airlift_card_node = settings_node['AirliftCard']
    gift_card_node = settings_node['GiftCard']
    diplomacy_card_node = settings_node['DiplomacyCard']
    sanctions_card_node = settings_node['SanctionsCard']
    reconnaissance_card_node = settings_node['ReconnaissanceCard']
    surveillance_card_node = settings_node['SurveillanceCard']
    blockade_card_node = settings_node['BlockadeCard']
    bomb_card_node = settings_node['BombCard']

    if reinforcement_card_node != 'none':
        reinforcement_card = get_card_settings(template, get_card(1), reinforcement_card_node)
        # TODO support other reinforcement card modes - not needed for most (all?) strategic templates
        reinforcement_card.mode = reinforcement_card_node['Mode']
        reinforcement_card.value = reinforcement_card_node['FixedArmies']
        template_cards_settings.append(reinforcement_card)

    if spy_card_node != 'none':
        spy_card = get_card_settings(template, get_card(2), spy_card_node)
        # TODO find node name for duration - not needed for most strategic templates
        # spy_card.duration = spy_card_node['Duration']
        template_cards_settings.append(spy_card)

    if abandon_card_node != 'none':
        abandon_card = get_card_settings(template, get_card(3), abandon_card_node)
        # TODO find node name for value - not needed for most (all?) strategic templates
        # abandon_card.value = abandon_card_node['MultiplyAmount']
        template_cards_settings.append(abandon_card)

    if op_card_node != 'none':
        template_cards_settings.append(get_card_settings(template, get_card(4), op_card_node))

    if od_card_node != 'none':
        template_cards_settings.append(get_card_settings(template, get_card(5), op_card_node))

    if airlift_card_node != 'none':
        template_cards_settings.append(get_card_settings(template, get_card(6), op_card_node))

    if gift_card_node != 'none':
        template_cards_settings.append(get_card_settings(template, get_card(7), op_card_node))

    if diplomacy_card_node != 'none':
        diplomacy_card = get_card_settings(template, get_card(8), diplomacy_card_node)
        # TODO find node namef or duration - not needed for most (all?) strategic templates
        # diplomacy_card.duration = diplomacy_card_node['Duration']
        template_cards_settings.append(diplomacy_card)

    if sanctions_card_node != 'none':
        sanctions_card = get_card_settings(template, get_card(9), sanctions_card_node)
        # TODO find node name for value and duration - not needed for most strategic templates
        # sanctions_card.value = spy_card_node['SanctionValue']
        # sanctions_card.duration = sanctions_card_node['Duration']
        template_cards_settings.append(sanctions_card)

    if reconnaissance_card_node != 'none':
        reconnaissance_card = get_card_settings(template, get_card(10), reconnaissance_card_node)
        # TODO find node name for duration - not needed for most strategic templates
        # reconnaissance_card.duration = reconnaissance_card_node['Duration']
        template_cards_settings.append(reconnaissance_card)

    if surveillance_card_node != 'none':
        surveillance_card = get_card_settings(template, get_card(11), surveillance_card_node)
        # TODO find node name for duration - not needed for most (all?) strategic templates
        # surveillance_card.duration = surveillance_card_node['Duration']
        template_cards_settings.append(surveillance_card)

    if blockade_card_node != 'none':
        blockade_card = get_card_settings(template, get_card(12), blockade_card_node)
        blockade_card.value = blockade_card_node['MultiplyAmount']
        template_cards_settings.append(blockade_card)

    if bomb_card_node != 'none':
        template_cards_settings.append(get_card_settings(template, get_card(13), op_card_node))
    
    # Save Template Card Settings to DB
    TemplateCardSetting.objects.bulk_create(template_cards_settings)


# Fetches Template from imput template dictionary if it exists
# Otherwise, Fetches Template from DB if it exists there and creates card settings dictionary
# Otherwise creates Template from game_json, saves it to DB and dictionary, and creates card settings dictionary
# Returns Template
def get_template(game_json):
    template_id = int(game_json['templateID'])
    # if template is not in the dictionary
    if template_id  not in templates_cards_settings:
        map = get_map(game_json['map'])
        try:
            # Try to get template from the DB
            template = Template.objects.get(pk=template_id)
        except Template.DoesNotExist:
            # Otherwise create template
            logging.info(f'Creating Template {template_id}')
            template = Template(id=template_id, map=map)

            # Get Settings
            settings_node = game_json['settings']
            template.is_multi_day = settings_node['Pace'] == 'MultiDay'
            if settings_node['Fog'] != 'Foggy':         # default is 'Foggy'
                template.fog_level = FogLevel.objects.get(pk=settings_node['Fog'])
            template.is_multi_attack = settings_node['MultiAttack']
            template.allow_percentage_attacks = settings_node['AllowPercentageAttacks']
            template.allow_transfer_only = settings_node['AllowTransferOnly']
            template.allow_attack_only = settings_node['AllowAttackOnly']
            template.is_cycle_move_order = settings_node['MoveOrder'] == 'Cycle'
            template.is_booted_to_ai = settings_node['BootedPlayersTurnIntoAIs']
            template.is_surrender_to_ai = settings_node['SurrenderedPlayersTurnIntoAIs']
            template.times_return_from_ai = settings_node['TimesCanComeBackFromAI']
            template.is_manual_distribution = settings_node['AutomaticTerritoryDistribution'] == 'Manual'
            template.distribution_mode = settings_node['DistributionMode']
            template.territory_limit = settings_node['TerritoryLimit']
            template.initial_armies = settings_node['InitialPlayerArmiesPerTerritory']
            template.out_distribution_neutrals = settings_node['InitialNonDistributionArmies']
            template.in_distribution_neutrals = settings_node['InitialNeutralsInDistribution']
            template.wasteland_count = settings_node['Wastelands']['NumberOfWastelands']
            template.wasteland_size = settings_node['Wastelands']['WastelandSize']
            # TODO add support for Commerce templates - not needed for most strategic templates
            template.is_commerce = False
            template.has_commanders = settings_node['Commanders']
            template.is_one_army_stand_guard = settings_node['OneArmyStandsGuard']
            template.base_income = settings_node['MinimumArmyBonus']
            template.luck_modifier = settings_node['LuckModifier']
            template.is_straight_round = settings_node['RoundingMode'] == 'StraightRound'
            template.bonus_army_per = settings_node['BonusArmyPer'] if settings_node['BonusArmyPer'] != 0  else None
            template.army_cap = settings_node['ArmyCap'] if settings_node['ArmyCap'] != 'null' else None
            template.offensive_kill_rate = settings_node['OffensiveKillRate']
            template.defensive_kill_rate = settings_node['DefensiveKillRate']
            template.is_local_deployment = settings_node['LocalDeployments']
            template.is_no_split = settings_node['NoSplit']
            template.max_cards = settings_node['MaxCardsHold']
            template.card_pieces_per_turn = settings_node['NumberOfCardsToReceiveEachTurn']
            template.card_playing_visible = not settings_node['CardPlayingsFogged']
            template.card_visible = not settings_node['CardsHoldingAndReceivingFogged']
            template.uses_mods = bool(settings_node['Mods'])
            
            # And add it to the DB
            template.save()

            import_overridden_bonuses(template, settings_node['OverriddenBonuses'])
            import_card_settings(template, settings_node)

        # And add the template and list of Card Settings to the dictionary
        cards_settings = {}
        for card_settings in TemplateCardSetting.objects.filter(template=template):
            cards_settings[card_settings.card.id] = card_settings
        
        templates_cards_settings[template_id] = (template, cards_settings)

    # Return template from dictionary
    return templates_cards_settings[template_id][0]


# Parse state of all territories at the end of a given turn
def parse_territories_states(standing_node, turn, map_territories, territories_states):
    for territory_node in standing_node:
        territory_id = int(territory_node['terrID'])
        territory_state = TerritoryState(turn=turn, territory=map_territories[territory_id],
                armies=territory_node['armies'])
        # Territory owner is Neutral, AvailableForDistribution (only in DistributionStanding), or a Player
        territory_owner = territory_node['ownedBy']
        try:
            territory_state.player = neutral_players[territory_owner]
        except KeyError:
            territory_state.player = players_by_api_id[int(territory_owner)]
        territories_states.append(territory_state)
    return territories_states


# Parse initial state of all territories for the game
def parse_initial_territory_states(game, distribution_node, map_territories, territories_states):
    turn = Turn(game=game, turn_number=-2)
    turn.save()

    # Import the initial state of the territories
    return parse_territories_states(distribution_node, turn, map_territories, territories_states)


# Parse the picks turn
def parse_picks_turn(game, picks_node, state_node, map_territories, template_cards_settings, orders,
        territories_states, cards_state):
    turn = Turn(game=game, turn_number=-1)
    turn.save()

    pick_type = get_order_type('GameOrderPick')

    for player_number, player_node_key in enumerate(picks_node):
        # Get Player from node by stripping the prefix ('player_') and looking up the id
        player_api_id = int(player_node_key[7:])
        player = players_by_api_id[player_api_id]

        for pick_number, pick in enumerate(picks_node[player_node_key]):
            order = Order(turn=turn, order_number=len(orders), order_type=pick_type, player=player, 
                    primary_territory=map_territories[pick])
            orders.append(order)

    # Import the state of the territories after picks
    parse_territories_states(state_node, turn, map_territories, territories_states)
    
    initial_cards_state = {}

    # Import initial state of the cards
    for card_id in template_cards_settings:
        template_card_settings = template_cards_settings[card_id]
        # Get iniial completed cards
        completed_cards = template_card_settings.initial_pieces // template_card_settings.number_of_pieces
        # Get intial pieces needed for next card
        pieces_until_next_card = -template_card_settings.initial_pieces % template_card_settings.number_of_pieces
        # If result is 0 make it the number of pieces in the card
        pieces_until_next_card += template_card_settings.number_of_pieces if not pieces_until_next_card else 0
        initial_cards_state[template_card_settings.card.get_order_type_id()] = {}
        for player_api_id in players_by_api_id:
            # Add card state to dictionary
            current_card_state = CardState(turn=turn, card=template_card_settings.card, player=players_by_api_id[player_api_id],
                    completed_cards = completed_cards, pieces_until_next_card=pieces_until_next_card)
            initial_cards_state[template_card_settings.card.get_order_type_id()][player_api_id] = current_card_state
    
    cards_state.append(initial_cards_state)


# Copy the current state, but update the uuid and turn
def copy_previous_card_state(turn, previous_card_state):
    next_card_state = deepcopy(previous_card_state)
    next_card_state.uuid = uuid4()
    next_card_state.turn = turn
    return next_card_state


# Update card states in receive card order
# TODO handle the case where card pieces received per turn isn't 1 (not needed for 1v1 ladder analysis)
def update_cards_state_receive_card(turn, player_api_id, template_cards_settings, current_cards_state):
    # Iterate through each card
    for card_order_type_id in current_cards_state:
        card_state = current_cards_state[card_order_type_id][player_api_id]

        if card_state.pieces_until_next_card == 1:
            # If player received a card, increment completed cards and reset pieces until next card
            card_state.completed_cards += 1
            card_state.pieces_until_next_card = template_cards_settings[card_state.card.id].number_of_pieces
        else:
            # Otherwise decrement pieces until next card
            card_state.pieces_until_next_card -= 1


# Parse the Card State for a Turn
def parse_cards_state(turn, order_nodes, template_cards_settings, cards_states):
    previous_cards_state = cards_states[-1]
    current_cards_state = {}
    for card_order_type_id in previous_cards_state:
        current_cards_state[card_order_type_id] = {}
        for player_api_id in previous_cards_state[card_order_type_id]:
            # Copy the previous state, but update the uuid and turn
            current_cards_state[card_order_type_id][player_api_id] = copy_previous_card_state(turn, 
                        previous_cards_state[card_order_type_id][player_api_id])

    for order_node in order_nodes:
        if order_node['type'] == 'GameOrderReceiveCard':
            # Update card state from receive card orders
            update_cards_state_receive_card(turn, order_node['playerID'], template_cards_settings, current_cards_state)
        elif order_node['type'].startswith('GameOrderPlayCard'):
            # Copy the current state, but update the uuid and turn and decrement current cards by one
            player_api_id = order_node['playerID']
            card_order_type_id = order_node['type']
            current_cards_state[card_order_type_id][player_api_id].completed_cards -= 1

    cards_states.append(current_cards_state)
        

# Parse basic Order
def parse_basic_order(turn, order_number, order_node, orders):
    player_api_id = int(order_node['playerID'])

    order = Order(turn=turn, order_number=order_number)
    order.order_type=get_order_type(order_node['type'])
    order.player = players_by_api_id[player_api_id]
    orders.append(order)


# Parse deploy Order
def parse_deploy_order(turn, order_number, order_node, map_territories, orders):
    player_api_id = int(order_node['playerID'])
    territory_id = int(order_node['deployOn'])

    order = Order(turn=turn, order_number=order_number)
    order.order_type=get_order_type(order_node['type'])
    order.player = players_by_api_id[player_api_id]
    order.primary_territory = map_territories[territory_id]
    order.armies = order_node['armies']
    orders.append(order)


# Parse attack/transfer Order
def parse_attack_transfer_order(turn, order_number, order_node, map_territories, orders, attack_results):
    player_api_id = int(order_node['playerID'])
    from_territory_id = int(order_node['from'])
    to_territory_id = int(order_node['to'])

    order = Order(turn=turn, order_number=order_number)
    order.order_type = get_order_type(order_node['type'])
    order.player = players_by_api_id[player_api_id]
    order.primary_territory = map_territories[from_territory_id]
    order.secondary_territory = map_territories[to_territory_id]
    order.armies = order_node['numArmies']
    order.attack_transfer = order_node['attackTransfer']
    order.is_attack_teammates = order_node['attackTeammates']
    order.is_attack_by_percent = order_node['byPercent']
    orders.append(order)
    
    # Parse AttackResult node
    result_node = order_node['result']
    attack_result = AttackResult(order=order)
    attack_result.is_attack = result_node['isAttack'] 
    attack_result.is_successful = result_node['isSuccessful']
    attack_result.attack_size = result_node['armies']
    attack_result.attacking_armies_killed = result_node['attackingArmiesKilled']
    attack_result.defending_armies_killed = result_node['defendingArmiesKilled']
    attack_result.offense_luck = 0.0 if not result_node['offenseLuck'] else float(result_node['offenseLuck'])
    attack_result.defense_luck = 0.0 if not result_node['defenseLuck'] else float(result_node['defenseLuck'])
    attack_results.append(attack_result)
        

# Parse basic play card Order
def parse_basic_play_card_order(turn, order_number, order_node, orders):
    player_api_id = int(order_node['playerID'])

    order = Order(turn=turn, order_number=order_number)
    order.order_type=get_order_type(order_node['type'])
    order.player = players_by_api_id[player_api_id]
    order.card_id = order_node['cardInstanceID']
    orders.append(order)


# Parse blockade Order
def parse_blockade_order(turn, order_number, order_node, map_territories, orders):
    player_api_id = int(order_node['playerID'])
    territory_id = int(order_node['targetTerritoryID'])

    order = Order(turn=turn, order_number=order_number)
    order.order_type=get_order_type(order_node['type'])
    order.player = players_by_api_id[player_api_id]
    order.primary_territory = map_territories[territory_id]
    order.card_id = order_node['cardInstanceID']
    orders.append(order)


# Parses state transition Order
def import_state_transition_order(order, order_node):
    # TODO implement state transitions (not needed for 1v1 games where ai does not take over)
    pass


# Parses the Orders for a Turn
def parse_orders(turn, order_nodes, map_territories, orders, attack_results):
    for order_number, order_node in enumerate(order_nodes):
        order_node = order_nodes[order_number]
        if order_node['type'] == 'GameOrderDeploy':
            parse_deploy_order(turn, order_number, order_node, map_territories, orders)
        elif order_node['type'] == 'GameOrderAttackTransfer':
            parse_attack_transfer_order(turn, order_number, order_node, map_territories, orders, attack_results)
        elif order_node['type'] in ['GameOrderReceiveCard', 'GameOrderStateTransition']:
            # TODO Confirm that this is sufficient for 'GameOrderStateTransition' 
            # (not needed for 1v1 games where ai does not take over)
            parse_basic_order(turn, order_number, order_node, orders)
        elif order_node['type'] in ['GameOrderPlayCardReinforcement', 'GameOrderPlayCardOrderPriority', 
                'GameOrderPlayCardOrderDelay']:
            parse_basic_play_card_order(turn, order_number, order_node, orders)
        elif order_node['type'] == 'GameOrderPlayCardBlockade':
            parse_blockade_order(turn, order_number, order_node, map_territories, orders)
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


# Flatten and import Cards States to DB
def import_cards_states(cards_states):
    # Flatten Card States
    flattened_cards_states = []
    for turn_cards_states in cards_states:
        for card_id in turn_cards_states:
            for player_api_id in turn_cards_states[card_id]:
                flattened_cards_states.append(turn_cards_states[card_id][player_api_id])
    
    # Save Card States to DB
    CardState.objects.bulk_create(flattened_cards_states)


# Import Turns into the DB
def import_turns(game, game_json):
    logging.debug(f'Importing Turns for Game {game.id}')
    # Create list of turn nodes
    turn_nodes = []
    for key in game_json:
        if key.startswith('turn'):
            turn_nodes.append(game_json[key])
    
    # Create list of state nodes
    standing_nodes = []
    for key in game_json:
        if key.startswith('standing'):
            standing_nodes.append(game_json[key])

    # Shift standing one index to the left so that a standing corresponds to the state after a turn rather than before
    standing_nodes = standing_nodes[1:]

    map_territories = maps_territories[game.template.map.id][1]
    template_cards_settings = templates_cards_settings[game.template.id][1]
    
    # Return if the game doesn't have any picks
    try:
        # TODO fix this to handle auto-distribution games (not needed for most templates)
        picks_node = game_json['picks']
    except KeyError:
        return
    
    orders = []
    attack_results = []
    territories_states = []
    cards_states = []           # List of card states at each turn: [{Card ID -> {Player ID -> Card State}}]

    # Import picks and initial game state
    parse_initial_territory_states(game, game_json['distributionStanding'], map_territories, territories_states)
    parse_picks_turn(game, picks_node, game_json['standing0'], map_territories, template_cards_settings, orders,
            territories_states, cards_states)

    for turn_number, turn_node in enumerate(turn_nodes):
        # create Turn object and set fields
        commit_date_time = datetime.strptime(turn_node['date'], '%m/%d/%Y %H:%M:%S').replace(tzinfo=UTC)
        turn = Turn(game=game, turn_number=turn_number, commit_date_time=commit_date_time)
        turn.save()
    
        parse_orders(turn, turn_node['orders'], map_territories, orders, attack_results)
        parse_territories_states(standing_nodes[turn_number], turn, map_territories, territories_states)
        parse_cards_state(turn, turn_node['orders'], template_cards_settings, cards_states)

    # Save Orders, Territory States, and Card States to DB
    Order.objects.bulk_create(orders)
    AttackResult.objects.bulk_create(attack_results)
    TerritoryState.objects.bulk_create(territories_states)
    import_cards_states(cards_states)

    logging.debug(f'Imported {game.number_of_turns} Turns, {len(orders)} Orders, and {len(territories_states)} Territory States.')

    
# Imports a Game into with the given ID into the DB along with associated data if they do not yet exist
# Does nothing if the Game already exists
# Returns True if the Game is imported and False otherwise
def import_game(email, api_token, game_id):
    logging.debug(f'Importing game {game_id}')
    try:
        # Check if Game already exists
        Game.objects.get(pk=game_id)
        logging.debug(f'Game {game_id} already exists.')
        return False
    except Game.DoesNotExist:
        logging.debug(f'Retrieving Game {game_id} data from Warzone')
        # Retrieve Game data
        game_data = api.get_game_data_from_id(email, api_token, game_id)
        
        # Parse Game data
        game_json = json_loads(game_data)

        try:
            # Will throw KeyError if map node doesn't exist
            # TODO this should be fixed by Fizzer soon
            map = game_json['map']
        except KeyError:
            # Map node doesn't exist, so game ended on turn -1
            # Ignore game, since it adds no value
            logging.debug(f'Game {game_id} has no map node. Game ended on turn -1')
            return False

        game = Game(id=game_json['id'], name=game_json['name'], number_of_turns=game_json['numberOfTurns'])
        
        game.template = get_template(game_json)

        if int(map['id']) != game.template.map.id:
            # Map doesn't match the map in the template so the template has changed
            # TODO add complete template compatibility checks
            return False
        else:
            game.save()
            
            add_players_to_game(game, game_json)
            import_turns(game, game_json)
            
            game.save()
            logging.debug(f'Finished importing Game {game_id}')
            return True


# Imports max_results Games (and associated data) from the specified ladder starting from offset
# For each Game, does nothing if the Game already exists
def import_ladder_games(email, api_token, ladder_id, max_results, offset, games_per_page, halt_if_exists):
    # Initialize neutral players
    logging.info('Initializing neutral players')
    neutral_players['Neutral'] = Player.objects.get(pk=0)
    neutral_players['AvailableForDistribution'] = Player.objects.get(pk=1)
    
    results_left_to_get = max_results
    imported_games_count = 0

    logging.info(f'Retrieving {max_results} ladder games from ladder {ladder_id} starting at offset {offset}')
    while 0 < results_left_to_get:
        # Retrieve game ids at offset
        logging.info(f'Retrieving {min(games_per_page, max_results)} game ids from ladder {ladder_id}: Offset {offset}')
        game_ids = api.get_ladder_game_ids(ladder_id, offset, results_left_to_get)
        
        # If game_ids empty break
        if not game_ids:
            return imported_games_count
        
        # Import each game if it does not yet exist
        for game_id in game_ids:
            if import_game(email, api_token, game_id):
                imported_games_count += 1
            elif halt_if_exists:
                return imported_games_count
        
        results_left_to_get -= len(game_ids)
        offset +=games_per_page
    
    return imported_games_count
