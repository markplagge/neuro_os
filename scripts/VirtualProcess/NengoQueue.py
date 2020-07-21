from VirtualProcess import VirtualProcess
from .ProcStates import PROC_MESSAGE,PROC_STATE
from .VirtualQueue import ProcessQueues
from .VirtualQueue import VirtualQueue

class NengoQueue(ProcessQueues):
    wait_q = VirtualQueue(0)
    run_q = VirtualQueue(1)
    def __init__(self, n_cores=4096, calc_neurons=512):
        super().__init__()
        self.n_cores = n_cores
        self.calc_neurons = calc_neurons


    def running_process_size(self,x=0):
        #if len(running_processes) > 0:
        if self.run_q != -1:
            return sum(p.needed_cores for p in self.run_q._queue)
        else:
            return 0

    def can_add(self,x):
        if (x[0] - x[1]) > 0 and self.running_process_size() == 0:
            return 1
        return 0

    def get_running_procs(self):
        return [
            p.process_id
            for p in self.run_q.iter_queue()
            if p.state == PROC_STATE.RUNNING
        ]
    def add_wait_proc(self, p):
        self.wait_q._queue.append(p)