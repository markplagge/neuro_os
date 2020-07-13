from VirtualProcess import Process,ProcessQueues,ProcStates
from VirtualProcess import Simulator
import nengo
from nengo.dists import Choice
from nengo.utils.ensemble import response_curves, tuning_curves
from nengo.solvers import LstsqL2


## Nemo manages the the processes using NeuroOS library
## Howver, the scheduler core needs the neuron based algorithm
from nengo.dists import Uniform
from nengo.processes import WhiteSignal
from nengo.utils.ensemble import tuning_curves
import numpy as np

queue_nodes = ProcessQueues()
class FCFS():

    def __init__(self,num_cores = 4096):
        self.num_cores = num_cores
        self.model = nengo.Network()
        self.n_neu = 1024

    def init_model(self):
        num_cores = self.num_cores
        calc_n_neurons = self.n_neu



    def check_add(self,x):
        if x > 0:
            return 1
        else:
            return 0
    def waiting_q_input_logic(self,x):
            if x <= 0:
                return self.num_cores * 2
            else:
                return x

    def can_add_thd_logic(self,x):
        x = np.round(x)
        return x