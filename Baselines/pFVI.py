from blackjack import Game
from chain import Chain
from pong import Pong #--> uncomment to run Pong
#from tetris import Tetris #--> uncomment to run Tetris
from time import clock
from sklearn.neural_network import MLPRegressor
import numpy as np


class FVI(object):

    def __init__(self,transfer=0,simulator="logistics",batch_size=1,number_of_iterations=10,loss="LS",trees=10):
        self.transfer = transfer
        self.simulator = simulator
        self.batch_size = batch_size
        self.loss = loss
        self.trees = trees
        self.number_of_iterations = number_of_iterations
        self.model = None
	self.state_number = 1
        self.compute_transfer_model()

    def compute_value_of_trajectory(self,values,trajectory,discount_factor=0.9,goal_value=1,AVI=False): 
        reversed_trajectory = trajectory[::-1]
        number_of_transitions = len(reversed_trajectory)
        if not AVI:
            for i in range(number_of_transitions):
                state_number = reversed_trajectory[i][0]
                state = reversed_trajectory[i][1]
                value_of_state = (goal_value)*(discount_factor**i) #immediate reward 0
                key = (state_number,tuple(state))
                values[key] = value_of_state
        elif AVI:
            for i in range(number_of_transitions-1):
                state_number = trajectory[i][0]
                state = trajectory[i][1]
                next_state_number = trajectory[i+1][0]
                next_state = trajectory[i+1][1]
                facts = np.array([list(next_state)])
                #examples = ["value(s"+str(next_state_number)+") "+str(0.0)]
                #self.model.infer(facts,examples)
                value_of_next_state = self.model.predict(facts)
                value_of_state = discount_factor*value_of_next_state
                key = (state_number,tuple(state))
                values[key] = value_of_state
                
            
    def compute_transfer_model(self):
        X,Y,bk = [],[],[]
        i = 0
        values = {}
        while i < self.transfer+1: #at least one iteration burn in time
            if self.simulator == "logistics":
                state = Logistics(number = self.state_number,start=True)
                if not bk:
                    bk = Logistics.bk
            elif self.simulator == "pong":
                state = Pong(number = self.state_number,start=True)
                if not bk:
                    bk = Pong.bk
            elif self.simulator == "tetris":
                state = Tetris(number = self.state_number,start=True)
                if not bk:
                    bk = Tetris.bk
            elif self.simulator == "wumpus":
                state = Wumpus(number = self.state_number,start=True)
                if not bk:
                    bk = Wumpus.bk
            elif self.simulator == "blocks":
                state = Blocks_world(number = self.state_number,start=True)
                if not bk:
                    bk = Blocks_world.bk
            elif self.simulator == "blackjack":
                state = Game(number = self.state_number,start=True)
                if not bk:
                    bk = Game.bk
            elif self.simulator == "50chain":
                state = Chain(number = self.state_number,start=True)
                if not bk:
                    bk = Chain.bk
            elif self.simulator == "net_admin":
                state = Admin(number = self.state_number,start=True)
                if not bk:
                    bk = Admin.bk
            with open(self.simulator+"_transfer_out.txt","a") as f:
                if self.transfer:
                    f.write("start state: "+str(state.get_state_facts())+"\n")
                time_elapsed = 0
                within_time = True
                start = clock()
                trajectory = [(state.state_number,state.get_state_facts())]
                while not state.goal():
                    if self.transfer:
                        f.write("="*80+"\n")
                    state_action_pair = state.execute_random_action()
                    state = state_action_pair[0] #state
                    if self.transfer:
                        f.write(str(state.get_state_facts())+"\n")
                    trajectory.append((state.state_number,state.get_state_facts()))
                    end = clock()
                    time_elapsed = abs(end-start)
                    if self.simulator == "logistics" and time_elapsed > 0.5:
                        within_time = False
                        break
                    elif self.simulator == "pong" and time_elapsed > 1000:
                        within_time = False
                        break
                    elif self.simulator == "tetris" and time_elapsed > 1000:
                        within_time = False
                        break
                    elif self.simulator == "wumpus" and time_elapsed > 1:
                        within_time = False
                        break
                    elif self.simulator == "blocks" and time_elapsed > 1:
                        within_time = False
                        break
                    elif self.simulator == "blackjack" and time_elapsed > 1:
                        within_time = False
                        break
                    elif self.simulator == "50chain" and time_elapsed > 2:
                        within_time = False
                        break
                    elif self.simulator == "net_admin" and time_elapsed > 1:
                        within_time = False
                        break
                if within_time:
                    self.compute_value_of_trajectory(values,trajectory)
		    self.state_number += len(trajectory)+1
                    for key in values:
                        state = list(key[1])
                        value = values[key]
                        X.append(state)
                        Y.append(value)
                    '''
                    for key in values:
                        facts += list(key[1])
                        example_predicate = "value(s"+str(key[0])+") "+str(values[key])
                        examples.append(example_predicate)
                    '''
                    i += 1
        npX = np.array(X)
        npY = np.array(Y)
	if not self.transfer:
		npY = np.zeros(len(npY))
        model = MLPRegressor(hidden_layer_sizes=(25,),
                             activation="logistic",
                             solver="lbfgs",
                             alpha=0.0001,
                             batch_size="auto",
                             learning_rate="constant",
                             learning_rate_init=0.001,
                             power_t=0.5,
                             max_iter=200,
                             shuffle=True,
                             random_state=None,
                             tol=0.0001,
                             verbose=False,
                             warm_start=False,
                             momentum=0.9,
                             nesterovs_momentum=True,
                             early_stopping=False,
                             validation_fraction=0.1,
                             beta_1=0.9,
                             beta_2=0.999,
                             epsilon=1e-08)
        print (npX)
	model.fit(npX,npY)
        #reg = GradientBoosting(regression = True,treeDepth=2,trees=self.trees,sampling_rate=0.7,loss=self.loss)
        #reg.setTargets(["value"])
        #reg.learn(facts,examples,bk)
        self.model = model
        self.AVI()

    def compute_bellman_error(self,values,inferred_values):
        bellman_error = []
        for key in values:
            inferred_value = inferred_values[key]
            computed_value = values[key]
            bellman_error.append(abs(inferred_value-computed_value))
            values[key] += computed_value-inferred_value
        return sum(bellman_error)/float(len(bellman_error)) #average bellman error

    def AVI(self):
        for i in range(self.number_of_iterations):
            j = 0
            X,Y,bk = [],[],[]
            values = {}
            fitted_values = {}
            while j < self.batch_size:
                if self.simulator == "logistics":
                    state = Logistics(number = self.state_number,start=True)
                    if not bk:
                        bk = Logistics.bk
                elif self.simulator == "pong":
                    state = Pong(number = self.state_number,start=True)
                    if not bk:
                        bk = Pong.bk
                elif self.simulator == "tetris":
                    state = Tetris(number = self.state_number,start=True)
                    if not bk:
                        bk = Tetris.bk
                elif self.simulator == "wumpus":
                    state = Wumpus(number = self.state_number,start=True)
                    if not bk:
                        bk = Wumpus.bk
                elif self.simulator == "blocks":
                    state = Blocks_world(number = self.state_number,start=True)
                    if not bk:
                        bk = Blocks_world.bk
                elif self.simulator == "blackjack":
                    state = Game(number = self.state_number,start=True)
                    if not bk:
                        bk = Game.bk
                elif self.simulator == "50chain":
                    state = Chain(number = self.state_number,start=True)
                    if not bk:
                        bk = Chain.bk
                elif self.simulator == "net_admin":
                    state = Admin(number = self.state_number,start=True)
                    if not bk:
                        bk = Admin.bk
                with open(self.simulator+"_FVI_out.txt","a") as fp:
                    fp.write("*"*80+"\nstart state: "+str(state.get_state_facts())+"\n")
                    time_elapsed = 0
                    within_time = True
                    start = clock()
                    trajectory = [(state.state_number,state.get_state_facts())]
                    while not state.goal():
                        fp.write("="*80+"\n")
                        state_action_pair = state.execute_random_action()
                        state = state_action_pair[0]
                        fp.write(str(state.get_state_facts())+"\n")
                        trajectory.append((state.state_number,state.get_state_facts()))
                        end = clock()
                        time_elapsed = abs(end-start)
                        if self.simulator == "logistics" and time_elapsed > 0.5:
                            within_time = False
                            break
                        elif self.simulator == "pong" and time_elapsed > 1000:
                            within_time = False
                            break
                        elif self.simulator == "tetris" and time_elapsed > 10:
                            within_time = False
                            break
                        elif self.simulator == "wumpus" and time_elapsed > 1:
                            within_time = False
                            break
                        elif self.simulator == "blocks" and time_elapsed > 1:
                            within_time = False
                            break
                        elif self.simulator == "blackjack" and time_elapsed > 1:
                            within_time = False
                            break
                        elif self.simulator == "50chain" and time_elapsed > 1:
                            within_time = False
                            break
                        elif self.simulator == "net_id" and time_elapsed > 1:
                            within_time = False
                    if within_time:
			if i > 0:
                            self.compute_value_of_trajectory(values,trajectory,AVI=True)
                        else:
                            self.compute_value_of_trajectory(values,trajectory,AVI=False)
			self.state_number += 1
                        for key in values:
                            state = list(key[1])
                            value = values[key]
                            #X.append(state)
                            fitted_values[key] = self.model.predict(np.array([state]))
                            #Y.append([value])
                        '''
                        for key in values:
                            facts += list(key[1])
                            example_predicate = "value(s"+str(key[0])+") "+str(values[key])
                            examples.append(example_predicate)
                        '''
                        j += 1
            #fitted_values = self.model.predict(np.array(X))
            bellman_error = self.compute_bellman_error(values,fitted_values)
            with open(self.simulator+"_BEs.txt","a") as f:
                f.write("iteration: "+str(i)+" average bellman error: "+str(bellman_error)+"\n")
            for key in values:
                X.append(list(key[1]))
                Y.append(values[key])
            npX = np.array(X)
            npY = np.array(Y)
            self.model.fit(npX,npY)
