from django.db import models
from uuid import uuid4

WARZONE_PATH = 'https://www.warzone.com'

class Ladder(models.Model):
    id = models.SmallIntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=40)

    def __str__(self):
        return self.name

    def get_url(self):
        return WARZONE_PATH + '/LadderSeason?ID=' + str(self.id)


class FogLevel(models.Model):
    id = models.CharField(primary_key=True, max_length=15, editable=False)
    name = models.CharField(max_length=15)

    def __str__(self):
        return self.name


class PlayerStateType(models.Model):
    id = models.CharField(primary_key=True, max_length=25, editable=False)

    def __str__(self):
        return self.id


class OrderType(models.Model):
    id = models.CharField(max_length=63, primary_key=True)
    name = models.CharField(max_length=63)

    def __str__(self):
        return self.name


class Card(models.Model):
    id = models.SmallIntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=31)

    def __str__(self):
        return self.name

    def get_order_type_id(self):
        # TODO ideally this should be explictly tied to the values of OrderType
        return f'GameOrderPlayCard{self.name[:-5].replace(" ", "")}'


class PlayerAccount(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)
    games = models.ManyToManyField('Game', through='Player')

    def __str__(self):
        return f'{self.id}:{self.name}'

    def get_url(self):
        return f'{WARZONE_PATH}/Profile?p={self.id}'
    
    # Get the id used in the games api
    def get_api_id(self):
        return int(str(self.id)[2:-2])


class Map(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def get_url(self):
        return f'{WARZONE_PATH}/SinglePlayer?PreviewMap={self.id}'


class Territory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    # value in json returned by api
    api_id = models.SmallIntegerField(editable=False)
    name = models.CharField(max_length=255)
    bonuses = models.ManyToManyField('bonus', through='BonusTerritory')
    connected_territories = models.ManyToManyField('self')

    def __str__(self):
        return self.name


class Bonus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    # value in json returned by api
    api_id = models.SmallIntegerField(editable=False)
    name = models.CharField(max_length=255)
    base_value = models.SmallIntegerField()
    territories = models.ManyToManyField(Territory, through='BonusTerritory')

    def __str__(self):
        return self.name
    

class BonusTerritory(models.Model):
    class Meta:
        unique_together = (('bonus', 'territory'),)
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    bonus = models.ForeignKey(Bonus, on_delete=models.CASCADE)
    territory = models.ForeignKey(Territory, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.bonus}.{self.territory}'
    

class Template(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    is_multi_day = models.BooleanField(default=True)
    fog_level = models.ForeignKey(FogLevel, default='Foggy', 
        on_delete=models.CASCADE)
    is_multi_attack = models.BooleanField(default=False)
    allow_percentage_attacks = models.BooleanField(default=True)
    allow_attack_only = models.BooleanField(default=True)
    allow_transfer_only = models.BooleanField(default=True)
    is_cycle_move_order = models.BooleanField(default=True)
    is_booted_to_ai = models.BooleanField(default=False)
    is_surrender_to_ai = models.BooleanField(default=False)
    times_return_from_ai = models.SmallIntegerField(default=2)
    is_manual_distribution = models.BooleanField(default=True)
    distribution_mode = models.SmallIntegerField(default=-1)
    territory_limit = models.IntegerField()
    initial_armies = models.IntegerField(default=4)
    out_distribution_neutrals = models.IntegerField(default=2)
    in_distribution_neutrals = models.IntegerField(default=4)
    wasteland_count = models.IntegerField()
    wasteland_size  = models.IntegerField(default=10)
    is_commerce = models.BooleanField(default=False)
    has_commanders = models.BooleanField(default=False)
    is_one_army_stand_guard = models.BooleanField(default=True)
    base_income = models.IntegerField(default=5)
    luck_modifier = models.FloatField(default=0.0)
    is_straight_round = models.BooleanField(default=True)
    bonus_army_per = models.SmallIntegerField(null=True, blank=True)
    army_cap = models.SmallIntegerField(null=True, blank=True)
    offensive_kill_rate = models.SmallIntegerField(default=60)
    defensive_kill_rate = models.SmallIntegerField(default=70)
    is_local_deployment = models.BooleanField(default=False)
    is_no_split = models.BooleanField(default=False)
    max_cards = models.SmallIntegerField()
    card_pieces_per_turn = models.SmallIntegerField()
    card_playing_visible = models.BooleanField(default=False)
    card_visible = models.BooleanField(default=False)
    uses_mods = models.BooleanField(default=False)
    overridden_bonuses = models.ManyToManyField(Bonus,
        through='TemplateOverriddenBonus')
    card_settings = models.ManyToManyField(Card, through='TemplateCardSetting')

    def __str__(self):
        return f'{self.map}-{self.id}'


class TemplateOverriddenBonus(models.Model):
    class Meta:
        unique_together = (('template', 'bonus'),)
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    bonus = models.ForeignKey(Bonus, on_delete=models.CASCADE)
    new_value = models.SmallIntegerField()

    def __str__(self):
        return str(self.bonus)


class TemplateCardSetting(models.Model):
    class Meta:
        unique_together = (('template', 'card'),)
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    number_of_pieces = models.SmallIntegerField()
    initial_pieces = models.SmallIntegerField()
    min_pieces_per_turn = models.SmallIntegerField()
    weight = models.FloatField()
    mode = models.SmallIntegerField(null=True, blank=True)
    value = models.FloatField(null=True, blank=True)
    duration = models.SmallIntegerField(null=True, blank=True)

    def __str__(self):
        return str(self.card)


class Game(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    number_of_turns = models.SmallIntegerField()
    players = models.ManyToManyField(PlayerAccount, through='Player')
    ladder = models.ForeignKey(Ladder, on_delete=models.CASCADE, null=True,
            blank=True)
    version = models.SmallIntegerField(default=0)

    def __str__(self):
        return self.name


class Player(models.Model):
    class Meta:
        unique_together = (('game', 'player'),)
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(PlayerAccount, on_delete=models.CASCADE)
    end_state = models.ForeignKey(PlayerStateType, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.game}:{self.player}'


class TerritoryBaseline(models.Model):
    class Meta:
        unique_together = (('game', 'territory'),)
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    territory = models.ForeignKey(Territory, on_delete=models.CASCADE)
    state = models.CharField(max_length=15)

    def __str__(self):
        return f'{self.game_id}:{self.territory} - {state}'


class Turn(models.Model):
    class Meta:
        unique_together = (('game', 'turn_number'),)
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    turn_number = models.SmallIntegerField()
    commit_date_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.game}: Turn {self.turn_number}'


class Order(models.Model):
    class Meta:
        unique_together = (('turn', 'order_number'),)
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    turn = models.ForeignKey(Turn, on_delete=models.CASCADE)
    order_number = models.SmallIntegerField()
    order_type = models.ForeignKey(OrderType, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, 
        related_name='order')
    armies = models.SmallIntegerField(blank=True, null=True)
    # in an attack/transfer/airlift this is the "from"
    primary_territory = models.ForeignKey(Territory, on_delete=models.CASCADE,
        related_name='+', null=True, blank=True)
    # in an attack/transfer/airlift this is the "to"
    secondary_territory = models.ForeignKey(Territory, 
        on_delete=models.CASCADE, related_name='+', null=True, blank=True)
    target_player = models.ForeignKey(Player, on_delete=models.CASCADE,
        related_name='+', null=True, blank=True)
    target_bonus = models.ForeignKey(Bonus, on_delete=models.CASCADE,
        null=True, blank=True)
    card_id = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return f'{self.turn} - {self.order_number}:{self.order_type}'


class AttackResult(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE,
        primary_key=True)
    attack_transfer = models.CharField(max_length=15, default='AttackTransfer')
    is_attack_teammates = models.BooleanField(default=False)
    is_attack_by_percent = models.BooleanField(default=False)
    is_attack = models.BooleanField(default=False)
    is_successful = models.BooleanField()
    attack_size = models.SmallIntegerField(blank=True, null=True)
    attacking_armies_killed = models.SmallIntegerField(blank=True, null=True)
    defending_armies_killed = models.SmallIntegerField(blank=True, null=True)
    offense_luck = models.FloatField(blank=True, null=True)
    defense_luck = models.FloatField(blank=True, null=True)

    def __str__(self):
        return str(self.order)


# TODO consider additional valuable metrics
class PlayerState(models.Model):
    class Meta:
        unique_together = (('turn', 'player'),)
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    turn = models.ForeignKey(Turn, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    income = models.SmallIntegerField()
    armies_on_board = models.SmallIntegerField()
    armies_deployed = models.SmallIntegerField()
    cumulative_armies_deployed = models.SmallIntegerField()
    territories_controlled = models.SmallIntegerField()
    # TODO for version 2
    bonuses_threatened = models.SmallIntegerField()
    # TODO for version 2
    income_threatened = models.SmallIntegerField()

    def get_movable_armies_on_board(self):
        return (self.armies_on_board 
            - int(turn.game.template.is_one_army_stand_guard) 
            * self.territories_controlled)

    def __str__(self):
        return f'{self.turn} - {self.player}'
