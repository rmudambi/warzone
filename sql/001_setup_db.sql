-- LADDER TABLE
CREATE TABLE ladder (
	id SMALLINT PRIMARY KEY,
	name VARCHAR(255) NOT NULL
)

-- FOG LEVELS TABLE
CREATE TABLE fog_level (
	id TINYINT AUTO_INCREMENT PRIMARY KEY,
	json_id VARCHAR(15) NOT NULL,				-- value in json returned by api
	name VARCHAR(15) NOT NULL
)

-- ORDER TYPES TABLE
CREATE TABLE order_type (
	id TINYINT AUTO_INCREMENT PRIMARY KEY,
	json_id VARCHAR(31) NOT NULL,				-- value in json returned by api
	name VARCHAR(31) NOT NULL
)

-- CARD TABLE
CREATE TABLE card (
	id TINYINT PRIMARY KEY,
	name VARCHAR(31) NOT NULL
)

-- PLAYERS TABLE
CREATE TABLE player (
	id INT PRIMARY KEY,
	name VARCHAR(255) NOT NULL
)

-- MAPS TABLE
CREATE TABLE warzone_map (
	id INT PRIMARY KEY,
	name VARCHAR(255) NOT NULL
)

-- MAP TERRITORIES TABLE
CREATE TABLE territory (
	id INT AUTO_INCREMENT PRIMARY KEY,
	map_id INT NOT NULL,
	json_id SMALLINT NOT NULL,					-- value in json returned by api
	name VARCHAR(255) NOT NULL,
	FOREIGN KEY territory_ibfk_1(map_id)
	REFERENCES warzone_map(id)
)

-- MAP TERRITORY CONNECTIONS TABLE
CREATE TABLE territory_connection (
	first_map_territory_id INT NOT NULL,
	second_map_territory_id INT NOT NULL,
	PRIMARY KEY(first_map_territory_id, second_map_territory_id),
	FOREIGN KEY territory_connection_ibfk_1(first_map_territory_id)	REFERENCES territory(id),
	FOREIGN KEY territory_connection_ibfk_2(second_map_territory_id) REFERENCES territory(id)
)

-- MAP BONUSES TABLE
CREATE TABLE bonus (
	id INT PRIMARY KEY,
	map_id INT NOT NULL,
	json_id SMALLINT NOT NULL,					-- value in json returned by api
	name VARCHAR(255) NOT NULL,
	value SMALLINT NOT NULL,
	FOREIGN KEY bonus_ibfk_1(map_id)
	REFERENCES warzone_map(id)
)

-- MAP BONUS TERRITORIES TABLE
CREATE TABLE bonus_territory (
	bonus_id INT NOT NULL,
	territory_id INT NOT NULL,
	PRIMARY KEY(bonus_id, territory_id),
	FOREIGN KEY bonus_territory_ibfk_1(bonus_id) REFERENCES bonus(id),
	FOREIGN KEY bonus_territory_ibfk_2(territory_id) REFERENCES territory(id)
)

-- TEMPLATES TABLE
CREATE TABLE template (
	id INT PRIMARY KEY,
	map_id INT NOT NULL,
	is_multi_day BIT(1) NOT NULL,
	fog_level_id TINYINT NOT NULL,
	is_multi_attack BIT(1) NOT NULL,
	allow_percentage_attacks BIT(1) NOT NULL,
	allow_transfer_only BIT(1) NOT NULL,
	allow_attack_only BIT(1) NOT NULL,
	is_cycle_move_order BIT(1) NOT NULL,
	is_booted_to_ai BIT(1) NOT NULL,
	is_surrender_to_ai BIT(1) NOT NULL,
	times_return_from_ai TINYINT NOT NULL,
	is_manual_distribution BIT(1) NOT NULL,
	distribution_mode TINYINT NOT NULL,
	territory_limit SMALLINT NOT NULL,
	in_distribution_armies SMALLINT NOT NULL,
	out_distribution_neutrals SMALLINT NOT NULL,
	in_distribution_neutrals SMALLINT NOT NULL,
	wasteland_count SMALLINT NOT NULL,
	wasteland_size SMALLINT,
	is_commerce BIT(1) NOT NULL,
	has_commanders BIT(1) NOT NULL,
	is_one_army_stand_guard BIT(1) NOT NULL,
	base_income SMALLINT NOT NULL,
	luck_modifier float NOT NULL,
	is_straight_round BIT(1) NOT NULL,
	bonus_army_per TINYINT NOT NULL,
	army_cap TINYINT,
	offensive_kill_rate TINYINT NOT NULL,
	defensive_kill_rate TINYINT NOT NULL,
	is_local_deployment BIT(1) NOT NULL,
	is_no_split BIT(1) NOT NULL,
	max_cards SMALLINT,
	card_pieces_per_turn SMALLINT,
	card_playing_visible BIT(1),
	card_visible BIT(1),
	uses_mods BIT(1),
	FOREIGN KEY template_ibfk_1(map_id)
	REFERENCES warzone_map(id),
	FOREIGN KEY template_ibfk_2(fog_level_id)
	REFERENCES fog_level(id)
)

-- TEMPLATE OVERRIDDEN BONUSES TABLE
CREATE TABLE template_overridden_bonus (
	template_id INT NOT NULL,
	bonus_id INT NOT NULL,
	new_value SMALLINT NOT NULL,
	PRIMARY KEY(template_id, bonus_id),
	FOREIGN KEY template_overridden_bonus_ibfk_1(template_id)
	REFERENCES template(id),
	FOREIGN KEY template_overridden_bonus_ibfk_2(bonus_id)
	REFERENCES bonus(id)
)

-- TEMPLATE CARD SETTING TABLE
CREATE TABLE template_card_setting (
	template_id INT NOT NULL,
	card_id TINYINT NOT NULL,
	number_of_pieces SMALLINT NOT NULL,
	initial_pieces SMALLINT NOT NULL,
	min_pieces_per_turn SMALLINT NOT NULL,
	weight FLOAT NOT NULL,
	mode TINYINT,
	value FLOAT,
	PRIMARY KEY(template_id, card_id),
	FOREIGN KEY template_card_setting_ibfk_1(template_id)
	REFERENCES template(id),
	FOREIGN KEY template_card_setting_ibfk_2(card_id)
	REFERENCES card(id)
)

-- GAMES TABLE
CREATE TABLE game (
	id INT PRIMARY KEY,
	template_id INT NOT NULL,
	name VARCHAR(255) NOT NULL, 
	player_a_id INT NOT NULL,
	player_b_id INT NOT NULL,
	winner INT NOT NULL,
	number_of_turns SMALLINT NOT NULL,
	FOREIGN KEY game_ibfk_1(template_id)
	REFERENCES template(id),
	FOREIGN KEY game_ibfk_2(player_a_id)
	REFERENCES player(id),
	FOREIGN KEY game_ibfk_3(player_b_id)
	REFERENCES player(id)
)

-- TURNS TABLE
CREATE TABLE turn (
	id INT PRIMARY KEY,
	game_id INT NOT NULL,
	turn_number SMALLINT NOT NULL,
	commit_date_time DATETIME,
	FOREIGN KEY turn_ibfk_1(game_id)
	REFERENCES game(id)
)

-- ORDERS TABLE
CREATE TABLE game_order (
	id INT PRIMARY KEY,
	turn_id INT NOT NULL,
	order_type_id TINYINT NOT NULL,
	player_id INT NOT NULL,
	primary_territory_id INT NOT NULL,			-- in an attack/transfer/airlift this is the "from"
	secondary_territory_id INT NOT NULL,		-- in an attack/transfer/airlift this is the "to"
	attack_transfer VARCHAR(15),
	attack_teammates BIT(1),
	attack_by_percent BIT(1),
	attack_size SMALLINT,
	result_is_attack BIT(1),
	result_is_successful BIT(1),
	result_attack_size SMALLINT,
	attacking_armies_killed SMALLINT,
	defending_armies_killed SMALLINT,
	offense_luck FLOAT,
	defense_luck FLOAT,
	target_player_id INT,
	target_bonus_id INT,
	FOREIGN KEY game_order_ibfk_1(turn_id)
	REFERENCES turn(id),
	FOREIGN KEY game_order_ibfk_2(order_type_id)
	REFERENCES order_type(id),
	FOREIGN KEY game_order_ibfk_3(player_id)
	REFERENCES player(id),
	FOREIGN KEY game_order_ibfk_4(primary_territory_id)
	REFERENCES territory(id),
	FOREIGN KEY game_order_ibfk_5(secondary_territory_id)
	REFERENCES territory(id),
	FOREIGN KEY game_order_ibfk_6(target_player_id)
	REFERENCES player(id),
	FOREIGN KEY game_order_ibfk_7(target_bonus_id)
	REFERENCES bonus(id)
)

-- TERRITORY STATE TABLE
CREATE TABLE territory_state (
	turn_id INT NOT NULL,
	territory_id INT NOT NULL,
	controlling_player_id INT,
	armies SMALLINT NOT NULL,
	PRIMARY KEY(turn_id, territory_id),
	FOREIGN KEY territory_state_ibfk_1(turn_id)
	REFERENCES turn(id),
	FOREIGN KEY territory_state_ibfk_2(territory_id)
	REFERENCES territory(id),
	FOREIGN KEY territory_state_ibfk_3(controlling_player_id)
	REFERENCES player(id)
)

-- CARD STATE TABLE
CREATE TABLE card_state (
	turn_id INT NOT NULL,
	player_id INT NOT NULL,
	card_id TINYINT NOT NULL,
	completed_cards SMALLINT NOT NULL,
	pieces_for_next_card SMALLINT NOT NULL,
	PRIMARY KEY(turn_id, player_id, card_id),
	FOREIGN KEY card_state_ibfk_1(turn_id)
	REFERENCES turn(id),
	FOREIGN KEY card_state_ibfk_2(player_id)
	REFERENCES player(id),
	FOREIGN KEY card_state_ibfk_3(card_id)
	REFERENCES card(id)
)