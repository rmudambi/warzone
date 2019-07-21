-- POPULATE FOG LEVEL TABLE
INSERT INTO fog_level (json_id, name)
VALUES
	('PLACEHOLDER-1', 'No Fog'),			-- TODO: get proper value
	('LightFog', 'Light Fog'),
	('Foggy', 'Normal Fog'),
	('ModerateFog', 'Dense Fog'),
	('PLACEHOLDER-2', 'Heavy Fog'),			-- TODO: get proper value
	('PLACEHOLDER-3', 'Complete Fog');		-- TODO: get proper value

-- POPULATE LADDER TABLE
INSERT INTO ladder (id, name)
VALUES
	(0, '1 v 1 Ladder'),
	(1, '2 v 2 Ladder'),
	(3, 'Real-Time Ladder'),
	(4, '3 v 3 Ladder'),
	(4000, 'Season I'),
	(4001, 'Season II'),
	(4002, 'Season III'),
	(4003, 'Season IV'),
	(4004, 'Season V'),
	(4005, 'Season VI'),
	(4006, 'Season VII'),
	(4007, 'Season VIII'),
	(4008, 'Season IX'),
	(4009, 'Season X'),
	(4010, 'Season XI'),
	(4011, 'Season XII'),
	(4012, 'Season XIII'),
	(4013, 'Season XIV'),
	(4014, 'Season XV'),
	(4015, 'Season XVI'),
	(4016, 'Season XVII'),
	(4017, 'Season XVIII'),
	(4018, 'Season XIX'),
	(4019, 'Season XX'),
	(4020, 'Season XXI'),
	(4021, 'Season XXII'),
	(4022, 'Season XXIII'),
	(4023, 'Season XXIV'),
	(4024, 'Season XXV'),
	(4025, 'Season XXVI'),
	(4026, 'Season XXVII'),
	(4027, 'Season XXVIII'),
	(4028, 'Season XXIX'),
	(4029, 'Season XXX'),
	(4030, 'Season XXXI'),
	(4031, 'Season XXXII'),
	(4032, 'Season XXXIII'),
	(4065, 'Season XXXIV'),
	(4066, 'Season XXXV'),
	(4067, 'Season XXXVI');
	
-- POPULATE CARD TABLE
INSERT INTO card (id, name)
VALUES
	(1, 'Reinforcement Card'),
	(2, 'Spy Card'),
	(3, 'Abandon Card'),
	(4, 'Order Priority Card'),
	(5, 'Order Delay Card'),
	(6, 'Airlift Card'),
	(7, 'Gift Card'),
	(8, 'Diplomacy Card'),
	(9, 'Sanctions Card'),
	(10, 'Reconnaissance Card'),
	(11, 'Surveillance Card'),
	(12, 'Blockade Card'),
	(13, 'Bomb Card')

-- POPULATE ORDER TYPE TABLE
INSERT INTO order_type (json_id, name)
VALUES
	('', 'Pick'),
	('GameOrderDeploy', 'Deploy'),
	('GameOrderAttackTransfer', 'Attack or Transfer'),
	('GameOrderReceiveCard', 'Receive Card Pieces'),
	('GameOrderStateTransition', 'Player State Change'),
	('GameOrderPlayCardReinforcement', 'Play Reinforcement Card'),
	('GameOrderPlayCardSpy', 'Play Spy Card'),
	('GameOrderPlayCardAbandon', 'Play Abandon Card'),
	('GameOrderPlayCardOrderPriority', 'Play Order Priority Card'),
	('GameOrderPlayCardOrderDelay', 'Play Order Delay Card'),
	('GameOrderPlayCardAirlift', 'Play Airlift Card'),
	('GameOrderPlayCardGift', 'Play Gift Card'),
	('GameOrderPlayCardDiplomacy', 'Play Diplomacy Card'),
	('GameOrderPlayCardSanctions', 'Play Sanctions Card'),
	('GameOrderPlayCardReconnaissance', 'Play Reconnaissance Card'),
	('GameOrderPlayCardSurveillance', 'Play Surveillance Card'),
	('GameOrderPlayCardBlockade', 'Play Blockade Card'),
	('GameOrderPlayCardBomb', 'Play Bomb Card')
