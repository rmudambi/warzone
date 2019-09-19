import logging

from django.db.models import Prefetch

from . import cache
from .models import Game, Map, Order, Player, PlayerState, Turn
from .wrappers import GameWrapper, PlayerStateWrapper

player_states_to_save = []

CURRENT_VERSION = 1
SELECT_GAMES_QUERY = (
    Game.objects
        .exclude(version=CURRENT_VERSION)
        .prefetch_related(
            'player_set',
            'territorybaseline_set',
            Prefetch(
                'turn_set__order_set',
                queryset=Order.objects.select_related('attackresult')),
            'turn_set__playerstate_set'
        )
)


# Create a Player State Wrapper for the next turn
def set_player_state_wrapper_turn(wrapper, turn):
    wrapper.player_state = PlayerState(
        turn = turn,
        player = wrapper.player_state.player,
        income = wrapper.player_state.income,
        armies_deployed = 0,
        cumulative_armies_deployed = (
            wrapper.player_state.cumulative_armies_deployed),
        territories_controlled = wrapper.player_state.territories_controlled,
        armies_on_board = wrapper.player_state.armies_on_board,
        income_threatened = wrapper.player_state.income_threatened,
        bonuses_threatened = wrapper.player_state.bonuses_threatened
    )


# Get ids of all bonuses that have been completed by acquiring this territory
def get_completed_bonus_ids(map_wrapper, territory_id, controlled_territories):
    # Get all bonuses this territory is a part of
    territory_bonus_ids = map_wrapper.territories[territory_id].bonus_ids

    completed_bonus_ids = []
    for bonus_id in territory_bonus_ids:
        # If the player controls all territories in a bonus
        if controlled_territories.issuperset(
                map_wrapper.bonuses[bonus_id].territory_ids):
            # Add it to the list of completed bonuses
            completed_bonus_ids.append(bonus_id)

    return completed_bonus_ids


# Process a Player gaining possession of a Territory
def process_territory_gain(map_wrapper, territory_owners, attacker, order):
    result = order.attackresult
    if order.order_type_id == 'GameOrderAttackTransfer':
        to_territory_id = order.secondary_territory_id
        from_territory_id = order.primary_territory_id
    else:
        to_territory_id = order.primary_territory_id
        from_territory_id = None

    # Update Territory owner
    territory_owners[to_territory_id] = attacker.player_state.player_id

    # Add territory to attacker and increment territory count
    attacker.territories[to_territory_id] = (
        result.attack_size - result.attacking_armies_killed)
    attacker.player_state.territories_controlled += 1
    
    if order.order_type_id == 'GameOrderAttackTransfer':
        # Remove attacking armies from 'from territory'
        attacker.territories[from_territory_id] -= result.attack_size

    # Get completed bonus ids
    completed_bonus_ids = get_completed_bonus_ids(map_wrapper,
        to_territory_id, set(attacker.territories.keys()))
    
    # Add completed bonus ids
    attacker.bonus_ids.update(completed_bonus_ids)

    # Add earned income
    # TODO add income from territories - not needed for most templates
    for bonus_id in completed_bonus_ids:
        attacker.player_state.income += (
        # TODO handle overridden bonuses - not needed for 1v1 ladder
            map_wrapper.bonuses[bonus_id].bonus.base_value
        )

    # TODO check if territory borders opponent's completed bonus
    # For Version 2
    
    # TODO if bonus has been completed check if it is threatened
    # For Version 2


# Process a Player losing possession of a Territory
def process_territory_loss(map_wrapper, territory_owners, defender, order):
    territory_id = (
        order.secondary_territory_id
            if order.secondary_territory_id
            else order.primary_territory_id
    )    
    
    # Remove territory from player and reduce territory count
    del defender.territories[territory_id]
    defender.player_state.territories_controlled -= 1

    # Get all bonuses that are broken by losing the territory
    broken_bonus_ids = defender.bonus_ids.intersection(
        map_wrapper.territories[territory_id].bonus_ids)

    # Remove broken bonuses
    defender.bonus_ids.difference_update(broken_bonus_ids)
    
    # Remove broken income
    # TODO handle income from territories - not needed for most templates
    for bonus_id in broken_bonus_ids:
        defender.player_state.income -= (
        # TODO handle overridden bonuses - not needed for 1v1 ladder
            map_wrapper.bonuses[bonus_id].bonus.base_value)

    # TODO check if territory borders opponent's completed bonus
    # For Version 2
    
    # TODO if bonus has been broken check if it had been threatened
    # For Version 2


# Update Player States following a Pick Order
def process_pick(map_wrapper, territory_owners, players_state, order):
    if order.attackresult.is_successful:
        picker = players_state[order.player_id]
        territory_id = order.primary_territory_id

        # Add initial armies per territory to total armies on board
        picker.player_state.armies_on_board += order.attackresult.attack_size

        process_territory_gain(map_wrapper, territory_owners, picker, order)


# Update Player States following a Deployment Order
def process_deployment(map_wrapper, players_state, order):
    deployer = players_state[order.player_id]
    deployer.player_state.armies_on_board += order.armies
    deployer.territories[order.primary_territory_id] += order.armies
    deployer.player_state.armies_deployed += order.armies
    deployer.player_state.cumulative_armies_deployed += order.armies


def process_army_movement(map_wrapper, territory_owners, players_state, order):
    result = order.attackresult
    if result.attack_size > 0:
        # Get territories
        from_territory_id = order.primary_territory_id
        to_territory_id = order.secondary_territory_id

        # Get Attacker
        attacker = players_state[order.player_id]

        if result.is_attack:
            # Get defending player
            defender = (
                players_state[territory_owners[to_territory_id]]
                if territory_owners[to_territory_id] != 0 else None
            )

            # Remove armies from armies on board
            attacker.player_state.armies_on_board -= (
                result.attacking_armies_killed)
            if defender != None:
                defender.player_state.armies_on_board -= (
                    result.defending_armies_killed)
            
            # If the attack is successful
            if result.is_successful:
                # Give the territory to the attacker
                process_territory_gain(map_wrapper, territory_owners,
                    attacker, order)
                
                # And remove it from the defender if the defender isn't neutral
                if defender != None:
                    process_territory_loss(map_wrapper, territory_owners,
                        defender, order)
            else:
                # Remove armies killed from their respective territories
                attacker.territories[from_territory_id] -= (
                    result.attacking_armies_killed)
                if defender != None:
                    defender.territories[to_territory_id] -= (
                        result.defending_armies_killed)
        else:
            # Move attacking armies from 'from territory' to 'to_territory'
            attacker.territories[from_territory_id] -= result.attack_size
            attacker.territories[to_territory_id] += result.attack_size


def process_blockade(map_wrapper, territory_owners, players_state, order):
    blockader = players_state[order.player_id]
    territory_id = order.primary_territory_id

    # If the player still controls the blockaded territory
    if territory_id in blockader.territories.keys():
        # Update territory owner
        territory_owners[territory_id] = cache.get_neutral_id()

        # Remove armies from armies on board
        blockader.player_state.armies_on_board -= (
            blockader.territories[territory_id])

        process_territory_loss(map_wrapper, territory_owners, blockader, order)


# Return Player States data for a Game
def parse_player_states(game_wrapper):
    template = cache.get_template(game_wrapper.game.template_id)
    map_wrapper = cache.get_map_wrapper(template.map_id, False)

    # Initialize a dictionary to contain the current state of each player
    players_state = {
        player_id: PlayerStateWrapper(
            PlayerState(
                turn = None,
                player = game_wrapper.players[player_id],
                income = template.base_income, 
                armies_deployed = 0,
                cumulative_armies_deployed = 0,
                territories_controlled = 0,
                armies_on_board = 0,
                income_threatened = 0,
                bonuses_threatened = 0
            )
        ) for player_id in game_wrapper.players
    }

    # Dictionary of territory ids to the player id of the current controller
    territory_owners = {
        territory_id: cache.get_neutral_id()
        for territory_id in map_wrapper.territories
    }
    
    for turn_wrapper in game_wrapper.turns:
        # Update players_state to current turn
        for player_state_wrapper in players_state.values():
            set_player_state_wrapper_turn(player_state_wrapper, 
                turn_wrapper.turn)

         # Process Orders
        for order in turn_wrapper.orders:
            if order.order_type_id in ['GameOrderPick', 'GameOrderAutoPick']:
                process_pick(map_wrapper, territory_owners, players_state,
                    order)
            elif order.order_type_id == 'GameOrderDeploy':
                process_deployment(map_wrapper, players_state, order)
            elif order.order_type_id == 'GameOrderAttackTransfer':
                process_army_movement(map_wrapper, territory_owners,
                    players_state, order)
            elif order.order_type_id in ['GameOrderPlayCardBlockade', 
                    'GameOrderPlayCardAbandon']:
                process_blockade(map_wrapper, territory_owners, players_state,
                    order)
            
            # No action required for ReceiveCard, StateTransition, Play
            # Reinforcement, Spy, OP, OD, Sanctions, Reconnaissance, or
            # Surveillance Card, or Card Wore Off Orders

            # TODO handle Gift - not needed for 1v1 ladder
            # TODO handle Airlift - not needed for most templates
            # TODO handle Bomb - not needed for most templates
            # TODO handle Diplomacy - not needed for most templates

        # Add PlayerStates to list of PlayerStates to save
        player_states_to_save.extend([
            player_state_wrapper.player_state
            for player_state_wrapper in players_state.values()
        ])


# Create Player State data for a given number of games from an given offset
def calculate_game_data(max_games_to_process, batch_size=5):
    logging.info(
        f'Processing {max_games_to_process} games'
    )

    counter = 0
    are_games_to_process = counter < max_games_to_process

    while are_games_to_process:
        games_to_process = min(batch_size, max_games_to_process - counter)

        # Process game ids at offset
        logging.info(
            f'Processing {games_to_process} games: '
            f'Offset {counter}'
        )
        
        # Get the next batch of games
        games = SELECT_GAMES_QUERY.all()[:games_to_process]

        # Clear save queue
        player_states_to_save.clear()
        
        for game in games:
            logging.info(
                f'Processing game {game.id}: Offset {counter}')
            
            parse_player_states(GameWrapper(game))
            game.version = CURRENT_VERSION
            counter += 1
        
        # Save Player States to the DB
        Game.objects.bulk_update(games, ['version'])
        PlayerState.objects.bulk_create(player_states_to_save)

        are_games_to_process = games and counter < max_games_to_process

    return counter
