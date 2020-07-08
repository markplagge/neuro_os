import pytest
from VirtualProcess import VirtualQueue
from VirtualProcess import Process
from VirtualProcess import PROC_STATE, PROC_MESSAGE, SCHEDULER_STATE
import numpy as np
n_cores = np.linspace(0,4000,10,dtype=np.int)
start_times = np.linspace(0,50,10,dtype=np.int)
time_needed = [i * 10 for i in np.arange(1,11)]

def test_vq_add():
    proc_list = []
    for i in range(3):
        p = Process(n_cores = n_cores[i], time_needed=time_needed[i], scheduled_start_time=start_times[i])
        proc_list.append(p)
    q = VirtualQueue.VirtualQueue()
    [q.push(px) for px in proc_list]
    q.tick()
    for proc in q._queue:
        assert(proc.state == PROC_STATE.PRE_WAIT)


