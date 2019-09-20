create view game_analysis_turn_state as
    select 
        p1.end_state_id = 'Won' as p1_winner,   -- Did Player 1 win?
        g.id as game_id,                        -- Game ID
        t.turn_number as turn_number,           -- Turn Number
        -- Player 1 State
        s1.income as p1_income, s1.armies_on_board as p1_armies_on_board, 
            s1.armies_deployed as p1_armies_deployed,
            s1.cumulative_armies_deployed as p1_cumulative_armies_deployed,
            s1.territories_controlled as p1_territories_controlled,
        -- Player 2 State
        s2.income as p2_income, s2.armies_on_board as p2_armies_on_board, 
            s2.armies_deployed as p2_armies_deployed,
            s2.cumulative_armies_deployed as p2_cumulative_armies_deployed,
            s2.territories_controlled as p2_territories_controlled
    from
        game_analysis_game g,
        game_analysis_turn t,
        game_analysis_player p1, game_analysis_player p2,
        game_analysis_playerstate s1, game_analysis_playerstate s2
    where
        -- Join Conditions
        g.id = t.game_id and g.id = p1.game_id and g.id = p2.game_id
        and s1.player_id = p1.id and s2.player_id = p2.id
        and s1.turn_id = t.id and s2.turn_id = t.id
        and p1.id < p2.id                       -- Avoid Row Duplication
        and t.turn_number > -1                  -- Remove Post-Picks State
        and (                                   -- Remove Boot Wins
            p1.end_state_id in ('SurrenderAccepted', 'Eliminated')
            or p2.end_state_id in ('SurrenderAccepted', 'Eliminated')
        );