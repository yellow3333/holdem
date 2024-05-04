from pypokerengine.players import BasePokerPlayer
import random as rand

from testchart.chart import *

class RandomPlayer(BasePokerPlayer):

  def set_action_ratio(self, fold_ratio, call_ratio, raise_ratio, round_state):
    ratio = [fold_ratio, call_ratio, raise_ratio]
    scaled_ratio = [ 1.0 * num / sum(ratio) for num in ratio]
    self.fold_ratio, self.call_ratio, self.raise_ratio = scaled_ratio

  def declare_action(self, valid_actions, hole_card, round_state):
    # /////
    if self.first_action==1:
            self.get_position(round_state['next_player'])
            self.first_action=self.first_action+1
    # /////
    choice = self.__choice_action(valid_actions)
    action = choice["action"]
    amount = choice["amount"]
    if action == "raise":
      amount = rand.randrange(amount["min"], max(amount["min"], amount["max"]) + 1)
    return action, amount

  def __choice_action(self, valid_actions):
    r = rand.random()
    if r <= self.fold_ratio:
      return valid_actions[0]
    elif r <= self.call_ratio:
      return valid_actions[1]
    else:
      return valid_actions[2]


  def receive_game_start_message(self, game_info):
    # /////
    self.set_players(game_info['player_num'])
    self.sb=game_info['rule']['small_blind_amount']
    self.ROUND_RESULT_CHART=Chart(game_info['player_num'],game_info['rule']['max_round'])
    # /////
    pass

  def receive_round_start_message(self, round_count, hole_card, seats):
    # /////
    self.fold_ratio = self.call_ratio = self.raise_ratio = 1.0/3
    self.position = 0
    self.first_action=1
    # /////
    pass

  def receive_street_start_message(self, street, round_state):
    pass

  def receive_game_update_message(self, new_action, round_state):
    pass

  def receive_round_result_message(self, winners, hand_info, round_state):
    # /////
    self.first_action=0
    if self.position==0:
            self.ROUND_RESULT_CHART.round_result_chart(winners,round_state)
    # /////
    pass
# ////
  def get_position(self,next_player_position):
        #next player 0 1
        #this player 1 0
        if self.get_players()==2:
            position_array=np.array([1,0])
            self.position = position_array[next_player_position]
            return position_array[next_player_position]
            
        #next player 0 1 2
        #this player 2 0 1
        elif self.get_players()==3:
            position_array=np.array([2,0,1])
            self.position=position_array[next_player_position]
            return position_array[next_player_position]
        #next player 0 1 2 3
        #this player 3 0 1 2
        elif self.get_players()==4:
            position_array=np.array([3,0,1,2])
            self.position=position_array[next_player_position]
            return position_array[next_player_position]
        return 0
  def get_players(self):
        return self.player_count
  
  def set_players(self,player_count):
        self.player_count=player_count