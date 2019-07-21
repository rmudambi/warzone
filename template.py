class Template:
    def __init__(self, template_id, wz_map, is_multi_day, base_income, luck_modifier, is_straight_round, distribution_mode,
                 territory_limit, in_distribution_armies, out_distribution_neutrals, in_distribution_neutrals,
                 wasteland_count, wasteland_size, max_cards, card_pieces_per_turn, fog_level, overridden_bonuses,
                 is_manual_distribution=True, allow_percentage_attacks=True, allow_transfer_only=True,
                 allow_attack_only=True, is_cycle_move_order=True,  bonus_army_per=0, army_cap=None, is_commerce=False,
                 has_commanders=False, is_one_army_stand_guard=True, offensive_kill_rate=60, defensive_kill_rate=70,
                 is_multi_attack=False, is_local_deployment=False, is_no_split=False, card_playing_visible=False,
                 card_visible=False, uses_mods=False, is_booted_to_ai=False, is_surrender_to_ai=False,
                 times_return_from_ai=2):
        self.id = template_id
        self.map = wz_map
        self.is_multi_day = is_multi_day
        self.fog_level_id = fog_level
        self.is_multi_attack = is_multi_attack
        self.allow_percentage_attacks = allow_percentage_attacks
        self.allow_transfer_only = allow_transfer_only
        self.allow_attack_only = allow_attack_only
        self.is_cycle_move_order = is_cycle_move_order
        self.is_booted_to_ai = is_booted_to_ai
        self.is_surrender_to_ai = is_surrender_to_ai
        self.times_return_from_ai = times_return_from_ai
        self.is_manual_distribution = is_manual_distribution
        self.distribution_mode = distribution_mode
        self.territory_limit = territory_limit
        self.in_distribution_armies = in_distribution_armies
        self.out_distribution_neutrals = out_distribution_neutrals
        self.in_distribution_neutrals = in_distribution_neutrals
        self.wasteland_count = wasteland_count
        self.wasteland_size = wasteland_size
        self.is_commerce = is_commerce
        self.has_commanders = has_commanders
        self.is_one_army_stand_guard = is_one_army_stand_guard
        self.base_income = base_income
        self.luck_modifier = luck_modifier
        self.is_straight_round = is_straight_round
        self.bonus_army_per = bonus_army_per
        self.army_cap = army_cap
        self.offensive_kill_rate = offensive_kill_rate
        self.defensive_kill_rate = defensive_kill_rate
        self.is_local_deployment = is_local_deployment
        self.is_no_split = is_no_split
        self.max_cards = max_cards
        self.card_pieces_per_turn = card_pieces_per_turn
        self.card_playing_visible = card_playing_visible
        self.card_visible = card_visible
        self.uses_mods = uses_mods
        self.overridden_bonuses = overridden_bonuses


class OverriddenBonus:
    def __init__(self, bonus_id, new_value):
        self.bonus_id = bonus_id
        self.new_value = new_value

# todo add card settings
