import json

from . import api
from .models import Bonus, BonusTerritory, Card, FogLevel, Game, Map, Player, Template, TemplateCardSetting
from .models import TemplateOverriddenBonus, Territory, TerritoryConnection

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
    player_nodes = game_json['players']
    for player_node in player_nodes:
        player = get_player(player_node)
        game.players.add(player)
        # Set Player as winner if they won the game
        if player_node['state'] == 'Won':
            game.winner = player


# Import all territories to the DB for a given Map
# Return a Dictionary mapping api ids to Territries
def get_territories(map, territories_node):
    # Dictionary of Territory api_ids to Territories
    territories = {}

    # Import all Territories to the DB and add them to the dictionary
    for territory_node in territories_node:
        territory = Territory(map=map, api_id=territory_node['id'], name=territory_node['name'])
        territory.save()
        territories[territory.api_id] = territory
    
    # Import all TerritoryConnections to the DB for each Territory in the Map
    for territory_node in territories_node:
        territory = territories[territories_node['id']]
        for connection in territory_node['connectedTo']:
            connection = TerritoryConnection(from_territory=territory, to_territory=territories[connection])
            connection.save()
    
    return territories


# Import all bonuses to the DB for a given Map
def import_bonuses(map, bonuses_node, territories):
    for bonus_node in bonuses_node:
        bonus = Bonus(map=map, api_id=bonus_node['id'], name=bonus_node['name'], base_value=['value'])
        bonus.save()
        for territory_id in bonus_node['territoryIDs']:
            territory = BonusTerritory(bonus=bonus, territory=territories[territory_id])
            territory.save()


# Fetches Map from DB if it exists.
# Otherwise creates Map from Node and saves it to DB
# Returns Map
def get_map(map_node):
    try:
        return Map.objects.get(pk=map_node['id'])
    except Map.DoesNotExist:
        map = Map(id=map_node['id'], name=map_node['name'])
        map.save()
        
        # Import Territories and Bonuses
        territories = get_territories(map, map_node['territories'])
        import_bonuses(map, map_node['bonuses'], territories)

        return map


# Import all Overridden Bonuses to the DB for a given Template
def import_overridden_bonuses(template, overridden_bonus_nodes):
    # TODO
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
        reinforcement_card = get_card_settings(template, Card.objects.get(pk=1), reconnaissance_card_node)
        # TODO support other reinforcement card modes
        reinforcement_card.mode = reinforcement_card_node['Mode']
        reinforcement_card.value = reinforcement_card_node['FixedArmies']
        reinforcement_card.save()

    if spy_card_node != 'none':
        spy_card = get_card_settings(template, Card.objects.get(pk=2), spy_card_node)
        # TODO find node name for duration
        # spy_card.duration = spy_card_node['Duration']
        spy_card.save()

    if abandon_card_node != 'none':
        abandon_card = get_card_settings(template, Card.objects.get(pk=3), abandon_card_node)
        # TODO find node name for value
        # abandon_card.value = abandon_card_node['MultiplyAmount']
        abandon_card.save()

    if op_card_node != 'none':
        get_card_settings(template, Card.objects.get(pk=4), op_card_node).save()

    if od_card_node != 'none':
        get_card_settings(template, Card.objects.get(pk=5), od_card_node).save()

    if airlift_card_node != 'none':
        get_card_settings(template, Card.objects.get(pk=6), airlift_card_node).save()

    if gift_card_node != 'none':
        get_card_settings(template, Card.objects.get(pk=7), gift_card_node).save()

    if diplomacy_card_node != 'none':
        diplomacy_card = get_card_settings(template, Card.objects.get(pk=8), diplomacy_card_node)
        # TODO find node namef or duration
        # diplomacy_card.duration = diplomacy_card_node['Duration']
        diplomacy_card.save()

    if sanctions_card_node != 'none':
        sanctions_card = get_card_settings(template, Card.objects.get(pk=9), sanctions_card_node)
        # TODO find node name for value and duration
        # sanctions_card.value = spy_card_node['SanctionValue']
        # sanctions_card.duration = sanctions_card_node['Duration']
        sanctions_card.save()

    if reconnaissance_card_node != 'none':
        reconnaissance_card = get_card_settings(template, Card.objects.get(pk=10), reconnaissance_card_node)
        # TODO find node name for duration
        # reconnaissance_card.duration = reconnaissance_card_node['Duration']
        reconnaissance_card.save()

    if surveillance_card_node != 'none':
        surveillance_card = get_card_settings(template, Card.objects.get(pk=11), surveillance_card_node)
        # TODO find node name for duration
        # surveillance_card.duration = surveillance_card_node['Duration']
        surveillance_card.save()

    if blockade_card_node != 'none':
        blockade_card = get_card_settings(template, Card.objects.get(pk=12), blockade_card_node)
        MultiplyAmount.value = blockade_card_node['MultiplyAmount']
        blockade_card.save()

    if bomb_card_node != 'none':
        get_card_settings(template, Card.objects.get(pk=13), bomb_card_node).save()


# Fetches Template from DB if it exists.
# Otherwise creates Template from game_json and saves it to DB
# Returns Template
def get_template(game_json):
    try:
        return Template.objects.get(pk=game_json['templateID'])
    except Template.DoesNotExist:
        template = Template(id=game_json['templateID'])

        # Get Map
        template.map = get_map(game_json['map'])

        # Get Settings
        settings_node = game_json['settings']
        template.is_multi_day = settings_node['Pace'] == 'MultiDay'
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
        # TODO add support for Commerce templates
        template.is_commerce = False
        template.has_commanders = settings_node['Commanders']
        template.is_one_army_stand_guard = settings_node['OneArmyStandsGuard']
        template.base_income = settings_node['MinimumArmyBonus']
        template.luck_modifier = settings_node['LuckModifier']
        template.is_straight_round = settings_node['RoundingMode'] == 'StraightRound'
        # TODO use ternary here if possible
        if settings_node['BonusArmyPer'] != 0:
            template.bonus_army_per = settings_node['BonusArmyPer']
        if settings_node['ArmyCap'] != 'null':
            template.army_cap = settings_node['ArmyCap']
        template.offensive_kill_rate = settings_node['OffensiveKillRate']
        template.defensive_kill_rate = settings_node['DefensiveKillRate']
        template.is_local_deployment = settings_node['LocalDeployments']
        template.is_no_split = settings_node['NoSplit']
        template.max_cards = settings_node['MaxCardsHold']
        template.card_pieces_per_turn = settings_node['NumberOfCardsToReceiveEachTurn']
        template.card_playing_visible = settings_node['CardPlayingsFogged']
        template.card_visible = settings_node['CardsHoldingAndReceivingFogged']
        template.uses_mods = len(settings_node['Mods']) != 0
        
        template.save()

        import_overridden_bonuses(template, settings_node['OverriddenBonuses'])
        import_card_settings(template, settings_node)

        return template


# Add Turn data to Game
def add_turns_to_game(game, game_json):
    # TODO
    pass

    
# Imports a Game into with the given ID into the DB along with associated data if they do not yet exist
# Does nothing if the Game already exists
# Returns True if the Game is imported and False otherwise
def import_game(email, api_token, game_id):
    try:
        # Check if Game already exists
        Game.get(pk=game_id)
        return False
    except Game.DoesNotExist:
        # Retrieve Game data
        game_data = api.get_game_data_from_id(email, api_token, game_id)
        
        # Parse Game data
        game_json = json.loads(game_data)
        game = Game(id=game_json['id'], name=game_json['name'], number_of_turns=game_json['numberOfTurns'])

        add_players_to_game(game, game_json)
        game.template = get_template(game_json)
        add_turns_to_game(game, game_json)
        
        game.save()
        return True

# Imports max_results Games (and associated data) from the specified ladder starting from offset
# For each Game, does nothing if the Game already exists
def import_ladder_games(email, api_token, ladder_id, max_results, offset):
    results_left_to_get = max_results
    imported_games_count = 0

    while 0 < results_left_to_get:
        # Retrieve game ids at offset
        game_ids = api.get_ladder_game_ids(ladder_id, offset, results_left_to_get)
        
        # If game_ids empty break
        if len(game_ids == 0):
            return imported_games_count
        
        # Import each game if it does not yet exist
        for game_id in game_ids:
            # TODO DOES A TERNARY OPERATOR EXIST IN PYTHON?
            if import_game(email, api_token, game_id):
                imported_games_count += 1
        
        results_left_to_get -= len(game_ids)
