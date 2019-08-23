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


class PlayerState(models.Model):
    id = models.CharField(primary_key=True, max_length=25, editable=False)

    def __str__(self):
        return self.id


class OrderType(models.Model):
    id = models.CharField(max_length=63, primary_key=True,)
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
        return 'GameOrderPlayCard' + self.name[:-5].replace(' ', '')


class Player(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)

    def __str__(self):
        return str(self.id) + ':' + self.name

    def get_url(self):
        return WARZONE_PATH + '/Profile?p=' + str(self.id)
    
    # Get the id used in the games api
    def get_api_id(self):
        return int(str(self.id)[2:-2])


class Map(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def get_url(self):
        return WARZONE_PATH + '/SinglePlayer?PreviewMap=' + str(self.id)


class Territory(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    # value in json returned by api
    api_id = models.SmallIntegerField(editable=False)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class TerritoryConnection(models.Model):
    class Meta:
        unique_together = (('from_territory', 'to_territory'),)
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    from_territory = models.ForeignKey(Territory, on_delete=models.CASCADE)
    to_territory = models.ForeignKey(Territory, on_delete=models.CASCADE, related_name='+')

    def __str__(self):
        return str(self.from_territory) + ' to ' + str(self.to_territory)


class Bonus(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    # value in json returned by api
    api_id = models.SmallIntegerField(editable=False)
    name = models.CharField(max_length=255)
    base_value = models.SmallIntegerField()

    def __str__(self):
        return self.name


class BonusTerritory(models.Model):
    class Meta:
        unique_together = (('bonus', 'territory'),)
    
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    bonus = models.ForeignKey(Bonus, on_delete=models.CASCADE)
    territory = models.ForeignKey(Territory, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.bonus) + '.' + str(self.territory)
    

class Template(models.Model):
    id = models.IntegerField(primary_key=True, editable=False)
    map = models.ForeignKey(Map, on_delete=models.CASCADE)
    is_multi_day = models.BooleanField(default=True)
    fog_level = models.ForeignKey(FogLevel, default='Foggy', on_delete=models.CASCADE)
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

    def __str__(self):
        return str(self.map) + '-' + str(self.id)


class TemplateOverriddenBonus(models.Model):
    class Meta:
        unique_together = (('template', 'bonus'),)
    
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    bonus = models.ForeignKey(Bonus, on_delete=models.CASCADE)
    new_value = models.SmallIntegerField()

    def __str__(self):
        return str(self.bonus)


class TemplateCardSetting(models.Model):
    class Meta:
        unique_together = (('template', 'card'),)
    
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
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

    def __str__(self):
        return self.name


class GamePlayer(models.Model):
    class Meta:
        unique_together = (('game', 'player'),)
    
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    end_state = models.ForeignKey(PlayerState, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.game) + ':' + str(self.player)


class Turn(models.Model):
    class Meta:
        unique_together = (('game', 'turn_number'),)
    
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    turn_number = models.SmallIntegerField()
    commit_date_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.game) + ': Turn ' + str(self.turn_number)


class Order(models.Model):
    class Meta:
        unique_together = (('turn', 'order_number'),)
    
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    turn = models.ForeignKey(Turn, on_delete=models.CASCADE)
    order_number = models.SmallIntegerField()
    order_type = models.ForeignKey(OrderType, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='player')
    armies = models.SmallIntegerField(blank=True, null=True)
    # in an attack/transfer/airlift this is the "from"
    primary_territory = models.ForeignKey(Territory, on_delete=models.CASCADE, related_name='primary_territory', 
            null=True, blank=True)
    # in an attack/transfer/airlift this is the "to"
    secondary_territory = models.ForeignKey(Territory, on_delete=models.CASCADE, related_name='secondary_territory', 
            null=True, blank=True)
    target_player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True, blank=True,
            related_name='target_player')
    target_bonus = models.ForeignKey(Bonus, on_delete=models.CASCADE, null=True, blank=True)
    attack_transfer = models.CharField(max_length=15, null=True, blank=True)
    is_attack_teammates = models.BooleanField(null=True, blank=True)
    is_attack_by_percent = models.BooleanField(null=True, blank=True)
    card_id = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self):
        return str(self.turn) + ' - ' + str(self.order_number) + ":" + str(self.order_type)


class AttackResult(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, unique=True)
    is_attack = models.BooleanField()
    is_successful = models.BooleanField()
    attack_size = models.SmallIntegerField()
    attacking_armies_killed = models.SmallIntegerField()
    defending_armies_killed = models.SmallIntegerField()
    offense_luck = models.FloatField()
    defense_luck = models.FloatField()

    def __str__(self):
        return 'Result:' + str(self.order)


class TerritoryState(models.Model):
    class Meta:
        unique_together = (('turn', 'territory'),)
    
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    turn = models.ForeignKey(Turn, on_delete=models.CASCADE)
    territory = models.ForeignKey(Territory, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    armies = models.SmallIntegerField()

    def __str__(self):
        return str(self.turn) + ' - ' + str(self.territory)


class CardState(models.Model):
    class Meta:
        unique_together = (('turn', 'card', 'player'),)
    
    uuid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    turn = models.ForeignKey(Turn, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    completed_cards = models.SmallIntegerField(default=0)
    pieces_until_next_card = models.SmallIntegerField()

    def __str__(self):
        return str(self.turn) + str(self.player.id) + ' - ' + str(self.card)
