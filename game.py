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
