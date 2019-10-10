from __future__ import annotations

from datetime import datetime
from uuid import uuid4, UUID

from django.db import models

WARZONE_PATH = 'https://www.warzone.com'

class Ladder(models.Model):
    id: int = models.SmallIntegerField(primary_key=True, editable=False)
    name: str = models.CharField(max_length=40)

    def __str__(self) -> str:
        return self.name

    def get_url(self) -> str:
        return WARZONE_PATH + '/LadderSeason?ID=' + str(self.id)


class FogLevel(models.Model):
    id: str = models.CharField(primary_key=True, max_length=15, editable=False)
    name: str = models.CharField(max_length=15)

    def __str__(self) -> str:
        return self.name


class PlayerStateType(models.Model):
    id: str = models.CharField(primary_key=True, max_length=25, editable=False)

    def __str__(self) -> str:
        return self.id


class OrderType(models.Model):
    id: str = models.CharField(max_length=63, primary_key=True)
    name: str = models.CharField(max_length=63)

    def __str__(self) -> str:
        return self.name


class Card(models.Model):
    id: int = models.SmallIntegerField(primary_key=True, editable=False)
    name: str = models.CharField(max_length=31)

    def __str__(self) -> str:
        return self.name

    def get_order_type_id(self) -> str:
        # TODO ideally this should be explictly tied to the values of OrderType
        return f'GameOrderPlayCard{self.name[:-5].replace(" ", "")}'


class PlayerAccount(models.Model):
    id: int = models.IntegerField(primary_key=True, editable=False)
    name: str = models.CharField(max_length=255)
    games: 'Game' = models.ManyToManyField('Game', through='Player')

    def __str__(self) -> str:
        return f'{self.id}:{self.name}'

    def get_url(self) -> str:
        return f'{WARZONE_PATH}/Profile?p={self.id}'
    
    # Get the id used in the games api
    def get_api_id(self) -> int:
        return int(str(self.id)[2:-2])


class Map(models.Model):
    id: int = models.IntegerField(primary_key=True, editable=False)
    name: str = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name

    def get_url(self) -> str:
        return f'{WARZONE_PATH}/SinglePlayer?PreviewMap={self.id}'


class Territory(models.Model):
    id: UUID = models.UUIDField(primary_key=True, default=uuid4,
        editable=False)
    map: Map = models.ForeignKey(Map, on_delete=models.CASCADE)
    # value in json returned by api
    api_id: int = models.SmallIntegerField(editable=False)
    name: str = models.CharField(max_length=255)
    bonuses: 'BonusTerritory' = models.ManyToManyField('bonus', 
        through='BonusTerritory')
    connected_territories: Territory = models.ManyToManyField('self')

    def __str__(self) -> str:
        return self.name


class Bonus(models.Model):
    id: UUID = models.UUIDField(primary_key=True, default=uuid4,
        editable=False)
    map: Map = models.ForeignKey(Map, on_delete=models.CASCADE)
    # value in json returned by api
    api_id: int = models.SmallIntegerField(editable=False)
    name: str = models.CharField(max_length=255)
    base_value: int = models.SmallIntegerField()
    territories: 'BonusTerritory' = models.ManyToManyField(Territory,
        through='BonusTerritory')

    def __str__(self) -> str:
        return self.name
    

class BonusTerritory(models.Model):
    class Meta:
        unique_together = (('bonus', 'territory'),)
    
    id: UUID = models.UUIDField(primary_key=True, default=uuid4,
        editable=False)
    bonus: Bonus = models.ForeignKey(Bonus, on_delete=models.CASCADE)
    territory: Territory = models.ForeignKey(Territory,
        on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f'{self.bonus}.{self.territory}'
    

class Template(models.Model):
    id: int = models.IntegerField(primary_key=True, editable=False)
    map: Map = models.ForeignKey(Map, on_delete=models.CASCADE)
    is_multi_day: bool = models.BooleanField(default=True)
    fog_level: FogLevel = models.ForeignKey(FogLevel, default='Foggy', 
        on_delete=models.CASCADE)
    is_multi_attack: bool = models.BooleanField(default=False)
    allow_percentage_attacks: bool = models.BooleanField(default=True)
    allow_attack_only: bool = models.BooleanField(default=True)
    allow_transfer_only: bool = models.BooleanField(default=True)
    is_cycle_move_order: bool = models.BooleanField(default=True)
    is_booted_to_ai: bool = models.BooleanField(default=False)
    is_surrender_to_ai: bool = models.BooleanField(default=False)
    times_return_from_ai: int = models.SmallIntegerField(default=2)
    is_manual_distribution: bool = models.BooleanField(default=True)
    distribution_mode: int = models.SmallIntegerField(default=-1)
    territory_limit: int = models.IntegerField()
    initial_armies: int = models.IntegerField(default=4)
    out_distribution_neutrals: int = models.IntegerField(default=2)
    in_distribution_neutrals: int = models.IntegerField(default=4)
    wasteland_count: int = models.IntegerField()
    wasteland_size : int = models.IntegerField(default=10)
    is_commerce: bool = models.BooleanField(default=False)
    has_commanders: bool = models.BooleanField(default=False)
    is_one_army_stand_guard: bool = models.BooleanField(default=True)
    base_income: int = models.IntegerField(default=5)
    luck_modifier: float = models.FloatField(default=0.0)
    is_straight_round: bool = models.BooleanField(default=True)
    bonus_army_per: int = models.SmallIntegerField(null=True, blank=True)
    army_cap: int = models.SmallIntegerField(null=True, blank=True)
    offensive_kill_rate: int = models.SmallIntegerField(default=60)
    defensive_kill_rate: int = models.SmallIntegerField(default=70)
    is_local_deployment: bool = models.BooleanField(default=False)
    is_no_split: bool = models.BooleanField(default=False)
    max_cards: int = models.SmallIntegerField()
    card_pieces_per_turn: int = models.SmallIntegerField()
    card_playing_visible: bool = models.BooleanField(default=False)
    card_visible: bool = models.BooleanField(default=False)
    uses_mods: bool = models.BooleanField(default=False)
    overridden_bonuses: 'TemplateOverriddenBonus' = models.ManyToManyField(
        Bonus, through='TemplateOverriddenBonus')
    card_settings: 'TemplateCardSetting' = models.ManyToManyField(Card,
        through='TemplateCardSetting')

    def __str__(self) -> str:
        return f'{self.map}-{self.id}'


class TemplateOverriddenBonus(models.Model):
    class Meta:
        unique_together = (('template', 'bonus'),)
    
    id: UUID = models.UUIDField(primary_key=True, default=uuid4,
        editable=False)
    template: Template = models.ForeignKey(Template, on_delete=models.CASCADE)
    bonus: Bonus = models.ForeignKey(Bonus, on_delete=models.CASCADE)
    new_value: int = models.SmallIntegerField()

    def __str__(self) -> str:
        return str(self.bonus)


class TemplateCardSetting(models.Model):
    class Meta:
        unique_together = (('template', 'card'),)
    
    id: UUID = models.UUIDField(primary_key=True, default=uuid4,
        editable=False)
    template: Template = models.ForeignKey(Template, on_delete=models.CASCADE)
    card: Card = models.ForeignKey(Card, on_delete=models.CASCADE)
    number_of_pieces: int = models.SmallIntegerField()
    initial_pieces: int = models.SmallIntegerField()
    min_pieces_per_turn: int = models.SmallIntegerField()
    weight: float = models.FloatField()
    mode: int = models.SmallIntegerField(null=True, blank=True)
    value: float = models.FloatField(null=True, blank=True)
    duration: int = models.SmallIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return str(self.card)


class Game(models.Model):
    id: int = models.IntegerField(primary_key=True, editable=False)
    template: Template = models.ForeignKey(Template, on_delete=models.CASCADE)
    name: str = models.CharField(max_length=255)
    number_of_turns: int = models.SmallIntegerField()
    players: PlayerAccount = models.ManyToManyField(PlayerAccount,
        through='Player')
    ladder: Ladder = models.ForeignKey(Ladder, on_delete=models.CASCADE,
        null=True, blank=True)
    version: int = models.SmallIntegerField(default=0, db_index=True)

    def __str__(self) -> str:
        return self.name


class Player(models.Model):
    class Meta:
        unique_together = (('game', 'player'),)
    
    id: UUID = models.UUIDField(primary_key=True, default=uuid4,
        editable=False)
    game: Game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player: PlayerAccount = models.ForeignKey(PlayerAccount,
        on_delete=models.CASCADE)
    end_state: PlayerStateType = models.ForeignKey(PlayerStateType,
        on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f'{self.game}:{self.player}'


class TerritoryBaseline(models.Model):
    class Meta:
        unique_together = (('game', 'territory'),)
    
    id: UUID = models.UUIDField(primary_key=True, default=uuid4,
        editable=False)
    game: Game = models.ForeignKey(Game, on_delete=models.CASCADE)
    territory: Territory = models.ForeignKey(Territory,
        on_delete=models.CASCADE)
    state: str = models.CharField(max_length=15)

    def __str__(self) -> str:
        return f'{self.game_id}:{self.territory} - {self.state}'


class Turn(models.Model):
    class Meta:
        unique_together = (('game', 'turn_number'),)
    
    id: UUID = models.UUIDField(primary_key=True, default=uuid4,
        editable=False)
    game: Game = models.ForeignKey(Game, on_delete=models.CASCADE)
    turn_number: int = models.SmallIntegerField()
    commit_date_time: datetime = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.game}: Turn {self.turn_number}'


class Order(models.Model):
    class Meta:
        unique_together = (('turn', 'order_number'),)
    
    id: UUID = models.UUIDField(primary_key=True, default=uuid4,
        editable=False)
    turn: Turn = models.ForeignKey(Turn, on_delete=models.CASCADE)
    order_number: int = models.SmallIntegerField()
    order_type: OrderType = models.ForeignKey(OrderType,
        on_delete=models.CASCADE)
    player: Player = models.ForeignKey(Player, on_delete=models.CASCADE, 
        related_name='order')
    armies: int = models.SmallIntegerField(blank=True, null=True)
    # in an attack/transfer/airlift this is the "from"
    primary_territory: Territory = models.ForeignKey(Territory,
        on_delete=models.CASCADE, related_name='+', null=True, blank=True)
    # in an attack/transfer/airlift this is the "to"
    secondary_territory: Territory = models.ForeignKey(Territory, 
        on_delete=models.CASCADE, related_name='+', null=True, blank=True)
    target_player: Player = models.ForeignKey(Player, on_delete=models.CASCADE,
        related_name='+', null=True, blank=True)
    target_bonus: Bonus = models.ForeignKey(Bonus, on_delete=models.CASCADE,
        null=True, blank=True)
    card_id: str = models.CharField(max_length=64, blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.turn} - {self.order_number}:{self.order_type}'


class AttackResult(models.Model):
    order: Order = models.OneToOneField(Order, on_delete=models.CASCADE,
        primary_key=True)
    attack_transfer: str = models.CharField(max_length=15, default='AttackTransfer')
    is_attack_teammates: bool = models.BooleanField(default=False)
    is_attack_by_percent: bool = models.BooleanField(default=False)
    is_attack: bool = models.BooleanField(default=False)
    is_successful: bool = models.BooleanField()
    attack_size: int = models.SmallIntegerField(blank=True, null=True)
    attacking_armies_killed: int = models.SmallIntegerField(blank=True, null=True)
    defending_armies_killed: int = models.SmallIntegerField(blank=True, null=True)
    offense_luck: float = models.FloatField(blank=True, null=True)
    defense_luck: float = models.FloatField(blank=True, null=True)

    def __str__(self) -> str:
        return str(self.order)


# TODO consider additional valuable metrics
class PlayerState(models.Model):
    class Meta:
        unique_together = (('turn', 'player'),)
    
    id: UUID = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    turn: Turn = models.ForeignKey(Turn, on_delete=models.CASCADE)
    player: Player = models.ForeignKey(Player, on_delete=models.CASCADE)
    income: int = models.SmallIntegerField()
    armies_on_board: int = models.SmallIntegerField()
    armies_deployed: int = models.SmallIntegerField()
    cumulative_armies_deployed: int = models.SmallIntegerField()
    territories_controlled: int = models.SmallIntegerField()
    # TODO for version 2
    bonuses_threatened: int = models.SmallIntegerField()
    # TODO for version 2
    income_threatened: int = models.SmallIntegerField()

    def get_movable_armies_on_board(self) -> int:
        return (self.armies_on_board 
            - int(self.turn.game.template.is_one_army_stand_guard) 
            * self.territories_controlled)

    def __str__(self) -> str:
        return f'{self.turn} - {self.player}'
