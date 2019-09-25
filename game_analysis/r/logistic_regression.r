library(RSQLite)
library(dbplyr)
library(ggplot2)
library(caret)

# connect to the sqlite file
con <- dbConnect(drv=SQLite(), dbname="Workspace/warzone/db.sqlite3")

# get the turn_state view as a data.frame
turn_states <- dbGetQuery( con,'select * from game_analysis_turn_state limit 10000') %>% 
  mutate(result = ifelse(p1_winner > 0.5, "Winner", "Loser") %>% factor()) %>% 
   select(-p1_winner) %>% as_tibble()
  

test_set <- dbGetQuery( con,'select * from game_analysis_turn_state limit 10000 offset 10000') %>% 
  mutate(result = ifelse(p1_winner > 0.5, "Winner", "Loser") %>% factor()) %>% 
  # select(-game_id, -p1_winner)
  select(-p1_winner)


# **NOTE**: watch the warning -- might end up mattering 
fit <- turn_states %>% mutate(y = as.numeric(result == "Winner")) %>%  
  glm(y ~ 
       p1_income + 
       p1_armies_deployed +
       p1_armies_on_board +
       p1_cumulative_armies_deployed +
       p1_territories_controlled +
       p2_income +
       p2_armies_deployed +
       p2_armies_on_board +
       p2_cumulative_armies_deployed +
       p2_territories_controlled,
     data = ., family = 'binomial')

p_hat <- predict(fit, test_set)
y_hat <- ifelse(p_hat > 0.5, "Winner", "Loser") %>% factor()


confusionMatrix(y_hat, test_set$result)


baseline_income_guess <- ifelse(test_set$p1_income > test_set$p2_income, "Winner", "Loser") %>% factor()
confusionMatrix(baseline_income_guess, test_set$result)

