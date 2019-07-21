class Turn:
    # Constructor for a Turn object
    def __init__(self, turn_id, name, template=None, players=(None, None), winner=None):
        self.id = turn_id
        self.name = name
        self.template = template
        self.player_a = players[0]
        self.player_b = players[1]
        self.winner = winner
        self.turns = []
