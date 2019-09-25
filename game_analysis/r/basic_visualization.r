library(RSQLite)
library(dplyr)
library(dbplyr)
library(ggplot2)

# connect to the sqlite file
con <- dbConnect(drv=SQLite(), dbname="Workspace/warzone/db.sqlite3")
# get the turn_state view as a data.frame
turn_states <- dbGetQuery( con,'select * from game_analysis_turn_state limit 1000' ) %>% as_tibble()

# Visualize income vs income
turn_states %>% ggplot(aes(p1_income, p2_income)) + 
  geom_point(aes(color = p1_winner), alpha = 0.5)

# Visualize armies on board
turn_states %>% ggplot(aes(p1_armies_on_board, p2_armies_on_board)) + 
  geom_point(aes(color = p1_winner), alpha = 0.5)

# Visualize armies deployed
turn_states %>% ggplot(aes(p1_armies_deployed, p2_armies_deployed)) + 
  geom_point(aes(color = p1_winner), alpha = 0.5)

# Visualize cumulative armies deployed
turn_states %>% ggplot(aes(p1_cumulative_armies_deployed, p2_cumulative_armies_deployed)) + 
  geom_point(aes(color = p1_winner), alpha = 0.5)

# Visualize territories controlled
turn_states %>% ggplot(aes(p1_territories_controlled, p2_territories_controlled)) + 
  geom_point(aes(color = p1_winner), alpha = 0.5)


# Visualize win probability by income difference
turn_states %>%
  group_by(p1_income - p2_income) %>% 
  filter(n() >= 2) %>%
  mutate(win_probability = mean(p1_winner)) %>% 
  ggplot(aes(p1_income - p2_income, win_probability)) + 
  geom_point(alpha = 0.5)

# Visualize win probability by income ratio
turn_states %>%
  group_by(p1_income / p2_income) %>% 
  filter(n() >= 2) %>%
  mutate(win_probability = mean(p1_winner)) %>% 
  ggplot(aes(p1_income / p2_income, win_probability)) + 
  geom_point(alpha = 0.5) +
  scale_x_log10()
