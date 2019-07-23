class Game:
    # Constructor for a Game object
    def __init__(self, game_id, name, template=None, players=(None, None), winner=None):
        self.id = game_id
        self.name = name
        self.template = template
        self.player_a = players[0]
        self.player_b = players[1]
        self.winner = winner
        self.turns = []

    # Add a turn to a Game
    def add_turn(self, turn):
        self.turns.append(turn)

    # Get number of turns in Game - picks don't count as a turn
    def get_number_of_turns(self):
        return len(self.turns) - 1


class Turn:
    def __init__(self, turn_id, turn_number, commit_date, orders=None, territory_states=None, card_states=None):
        self.id = turn_id
        self.turn_number = turn_number
        self.commit_date = commit_date
        self.orders = orders
        self.territory_states = territory_states
        self.card_states = card_states


class Order:
    def __init__(self, order_id, order_type, player_id, primary_territory_id, secondary_territory_id,
                 target_player_id=None, target_bonus=None):
        self.id = order_id
        self.order_type = order_type
        self.player_id = player_id
        self.primary_territory_id = primary_territory_id
        self.secondary_territory_id = secondary_territory_id
        self.target_player_id = target_player_id
        self.target_bonus = target_bonus


class AttackTransferOrder(Order):
    def __init__(self, order_id, order_type, player_id, primary_territory_id, secondary_territory_id, attack_size,
                 attack_transfer='AttackTransfer', attack_teammates=False, attack_by_percent=False, attack_result=None):
        Order.__init__(self, order_id, order_type, player_id, primary_territory_id, secondary_territory_id)
        self.attack_size = attack_size
        self.attack_transfer = attack_transfer
        self.attack_teammates = attack_teammates
        self.attack_by_percent = attack_by_percent
        self.attack_result = attack_result


class AttackResult:
    def __init__(self, is_attack, is_successful, attack_size, attacking_armies_killed, defending_armies_killed,
                 offense_luck, defense_luck):
        self.is_attack = is_attack
        self.is_successful = is_successful
        self.attack_size = attack_size
        self.attacking_armies_killed = attacking_armies_killed
        self.defending_armies_killed = defending_armies_killed
        self.offense_luck = offense_luck
        self.defense_luck = defense_luck


class TerritoryState:
    def __init__(self, territory_id, armies, player_id=None):
        self.territory_id = territory_id
        self.armies = armies
        self.player_id = player_id


class CardState:
    def __init__(self, player_id, card_id, pieces_until_next_card, completed_cards=0):
        self.player_id = player_id
        self.card_id = card_id
        self.pieces_until_next_card = pieces_until_next_card
        self.completed_cards = completed_cards
