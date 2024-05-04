from pypokerengine.players import BasePokerPlayer
import numpy as np
import random
import json
import joblib
import tensorflow as tf
from tensorflow import keras
from testchart.chart import *


class RF_AutoAImodel(BasePokerPlayer):  # Do not forget to make parent class as "BasePokerPlayer"
    #  we define the logic to make an action through this method. (so this method would be the core of your AI)
    def declare_action(self, valid_actions, hole_card, round_state):
        # valid_actions format => [raise_action_info, call_action_info, fold_action_info]
        # print("valid actions in RF: ",valid_actions)
        #no note
        if self.first_action==1:
            self.get_position(round_state['next_player'])
            self.first_action=self.first_action+1
            
        action_predict= self.predict_action(valid_actions)
        action=action_predict['action']
        amount=action_predict['amount']
        # print("action predict in rf")
        # no note
        # print(self.game_data)
        # no note
        return action, amount   # action returned here is sent to the poker engine

    def receive_game_start_message(self, game_info):
        self.game_data = np.zeros(15)
        self.game_data[10:16] = -1
        self.game_data[8]=0
        self.game_data[9]=1
        self.set_players(game_info['player_num'])
        self.sb=game_info['rule']['small_blind_amount']
        self.in_chips=np.zeros(15)
        self.ROUND_RESULT_CHART=Chart(game_info['player_num'],game_info['rule']['max_round'])
        #print("small blind: ",self.sb)
        return None

    def receive_round_start_message(self, round_count, hole_card, seats):
        #print("in RF_Auto receive_round_start_message hole card ",hole_card)
        #covert suite and face
        self.first_action=1
        self.hand1=self.convert_suite_and_face(hole_card[0])
        self.hand2=self.convert_suite_and_face(hole_card[1])
        hands=[self.hand1,self.hand2]
        self.set_hands(hands)
        self.set_hand_level(hands)
        return None

    def receive_street_start_message(self, street, round_state):  
        if street=="flop":
            self.flop1=self.convert_suite_and_face(round_state['community_card'][0])
            self.flop2=self.convert_suite_and_face(round_state['community_card'][1])
            self.flop3=self.convert_suite_and_face(round_state['community_card'][2])
            self.game_data[0]=self.card_convert(self.flop1.copy())
            self.game_data[1]=self.card_convert(self.flop2.copy())
            self.game_data[2]=self.card_convert(self.flop3.copy())
        if street=="turn":
            self.turn=self.convert_suite_and_face(round_state['community_card'][3])
            self.game_data[3]=self.card_convert(self.turn.copy())
        if street=="river":
            self.river=self.convert_suite_and_face(round_state['community_card'][4])
            self.game_data[4]=self.card_convert(self.river.copy())

        #print("set community cards in rf: ",self.game_data)
        return None

    def receive_game_update_message(self, action, round_state):
        self.set_action(action)
        self.set_chips(round_state['next_player']-1,action['amount'])
        return None

    def receive_round_result_message(self, winners, hand_info, round_state):
        self.game_data = np.zeros(15)
        self.game_data[10:16] = -1
        self.game_data[8]=0
        self.game_data[9]=1
        self.in_chips=np.zeros(15)
        self.first_action=0
        if self.position==0:
            self.ROUND_RESULT_CHART.round_result_chart(winners,round_state)
        return None
    
    #RF-------model------data------format----translation 
    def set_players(self,player_count):
        self.player_count=player_count
        return None

    def get_players(self):
        return self.player_count
    
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
    def set_hand_level(self,cards):
        #You can change the hand level simply by changing the array value 
        self.level_array = np.array([[1,1,2,2,3,3,3,3,3,3,3,3,3], 
                                     [1,1,2,3,3,4,5,6,6,6,6,6,6], 
                                     [2,2,1,3,4,4,5,6,6,6,6,6,6],
                                     [3,3,3,2,4,4,5,6,6,6,6,6,6],
                                     [4,4,4,4,2,4,4,5,6,6,6,6,6],
                                     [4,5,5,5,5,3,4,5,5,6,6,6,6],
                                     [4,6,6,5,5,5,3,4,5,6,6,6,6],
                                     [4,6,6,6,6,5,5,4,4,5,6,6,6],
                                     [4,6,6,6,6,6,5,5,4,4,5,6,6],
                                     [4,6,6,6,6,6,6,6,5,4,5,6,6],
                                     [5,6,6,6,6,6,6,6,6,6,4,5,6],
                                     [5,6,6,6,6,6,6,6,6,6,6,4,6],
                                     [5,6,6,6,6,6,6,6,6,6,6,6,4]])
        #print("level array:\n",level_array)   
        hand1=cards[0]
        hand2=cards[1]
        #hand face 1 trans to 14
        if(hand1['face']==1):
            hand1['face']=14
        if(hand2['face']==1):
            hand2['face']=14
        #hand1 is random variable always bigger than hand2
        if(cards[0]['face']>cards[1]['face']):
            hand1=cards[0]
            hand2=cards[1]
        else:
            hand1=cards[1]
            hand2=cards[0]
        #print("set_hand_level hand1,hand2:",hand1," ", hand2)
        suit_same=0
        if(hand1['suite']==hand2['suite']):
            suit_same=1
        self.level=self.set_level(hand1['face'],hand2['face'],suit_same)
        #print("level from set_hand_level: ",self.level)
        return None

    def set_level(self,hand1,hand2,suit_same):
        #find hand1 and hand2 in level array
        if(suit_same):
            level=self.level_array[14-hand1][14-hand2]
        else:
            level=self.level_array[14-hand2][14-hand1]
        return level
    
    def set_action(self,action):
        action_number=self.get_action(action)
        if np.count_nonzero(self.game_data == -1)!=0:
            self.game_data[np.argmax(self.game_data[10:16] == -1)+10]=action_number
        else:
            self.game_data[10:16] = -1
            self.set_action(action)
        #print("game_data_from_old_rf: \n",self.game_data)
        return None
    
    def set_chips(self,action_player_index,chips):
        self.in_chips[action_player_index]+=chips
        self.game_data[5]=np.amax(self.in_chips)
        return None

    def convert_suite_and_face(self,card):
        card_converted={'suite':'suite','face':0}
        if card[0]=='S':
            card_converted['suite']='spade'
        elif card[0]=='C':
            card_converted['suite']='club'
        elif card[0]=='D':
            card_converted['suite']='diamond'
        elif card[0]=='H':
            card_converted['suite']='heart'
        
        if card[1]=='T':
            card_converted['face']=10
        elif card[1]=='J':
            card_converted['face']=11
        elif card[1]=='Q':
            card_converted['face']=12
        elif card[1]=='K':
            card_converted['face']=13
        elif card[1]=='A':
            card_converted['face']=1
        else:
            card_converted['face']=int(card[1])
        return card_converted
    
    def set_hands(self,hands):
        self.hand1=hands[0]
        self.hand2=hands[1]
        self.game_data[6]=self.card_convert(hands[0].copy())
        self.game_data[7]=self.card_convert(hands[1].copy())
        #print("set hands in RF Auto: ",self.game_data)
        return None
    
    def card_convert(self,card):
        card_converted=card
        #note that card face A should be sent in as 1 
        if card_converted['face']==1:
            card_converted['face']=14
        card_converted=card
        if card['suite']=="club":
            card_converted['face']=-4+(card['face']-1)*4
        elif card['suite']=="diamond":
            card_converted['face']=-3+(card['face']-1)*4
        elif card['suite']=="heart":
            card_converted['face']=-2+(card['face']-1)*4
        elif card['suite']=="spade":
            card_converted['face']=-1+(card['face']-1)*4
        return card_converted['face']
    
    def get_action(self,action):
        if(action['action']=='raise'):
            return 2
        elif(action['action']=='call' and action['amount']>0):
            return 3
        #action check=4
        elif(action['action']=='call' and action['amount']==0):
            return 4
        elif(action=="fold"):
            return 8
        elif(action=="allin"):
            return 9
        return -1
    
    def get_predict_action(self,action):
        if action==2:#raise
            predict_action={'action':'raise' ,"amount":50}
            return predict_action
        elif action==3:#call
            predict_action={'action':'call' ,"amount":50}
            return predict_action
        elif action==4:#check
            predict_action={'action':'call' ,"amount":0}
            return predict_action
        elif action==8:#fold
            predict_action={'action':'fold' ,"amount":0}
            return predict_action
        elif action==9:#all-in
            predict_action={'action':'raise','amount':0}
            return predict_action
        else:
            predict_action={'action':'check' ,"amount":0}
            return predict_action
    
    def predict_action(self,valid_actions):
        predict_action=valid_actions[1]
        action=self.predict()
        for valid_action in valid_actions:
            if valid_action['action'] =="call":
                self.to_call=valid_action['amount']
            if valid_action['action'] == action['action']:
                predict_action=valid_action
                break
        if predict_action['action']=='raise' and predict_action['amount']!=0:
            if 5<=self.level<=6:
                predict_action={'action':'raise','amount':min(predict_action['amount']['max'],self.to_call+2*self.sb)}
            elif 3<=self.level<=4:
                predict_action={'action':'raise','amount':min(predict_action['amount']['max'],self.to_call+3*self.sb)}
            else:
                predict_action={'action':'raise','amount':min(predict_action['amount']['max'],self.to_call+4*self.sb)}
            return predict_action
        elif predict_action['action']=='raise' and predict_action['amount']==0:#all-in
            predict_action={'action':'raise','amount':predict_action['amount']['max']}
        else:
            predict_action=valid_action
            return predict_action
        
        
    def predict(self):
        model = joblib.load(r"..\model\RFmodel\my_random_forest.joblib")#path
        action_number= int(float(model.predict(np.array(self.game_data).reshape(1, -1))))
        #print("RF predict number:",action_number)
        predict_action=self.get_predict_action(action_number)
        #print("RF predict action: ",predict_action)
        return predict_action 
    
