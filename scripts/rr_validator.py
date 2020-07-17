#%%
from enum import IntFlag


class PROC_STATE(IntFlag):
    WAITING = 1
    RUNNING = 2
    COMPLETE = 4
    PRE_WAIT = 8
    NO_OP = 0

class SimpleProc:
    def __init__(self,name, id,arrival,start,compute,cores):
        self.name = name
        self.id = id
        self.arrival = arrival

        self.compute = compute
        self.cores = cores
        self.current_time = 0
        if self.arrival == 0:
            self.state = PROC_STATE.WAITING
        else:
            self.state = PROC_STATE.PRE_WAIT
procs = []
procs.append(SimpleProc("Cifar",1,0,0,4450,4038))
procs.append(SimpleProc("SAR",2,10,4450,1125,3038))
procs.append(SimpleProc("Tonic",3,100,5575,8,2))
procs.append(SimpleProc("Saturation",4,120,5583,81,1439))
procs.append(SimpleProc("Cifar",5,1000,5664,5325,4038))
procs.append(SimpleProc("SAR",6,1010,10989,1876,3038))
procs.append(SimpleProc("Tonic",7,1500,12865,7,2))
procs.append(SimpleProc("Cifar",8,2000,12872,5649,4038))
procs.append(SimpleProc("SAR",9,2010,18521,1196,3038))
procs.append(SimpleProc("Tonic",10,2100,19717,8,2))
procs.append(SimpleProc("Saturation",11,3000,19725,54,1091))

import nengo_os
iface = nengo_os.NemoNengoInterface(True,mode=1,rr_time_slice=50)
for p in procs:
    iface.add_process(p.id,p.cores,p.compute,p.arrival)
#iface.run_sim_time(5000)
iface.init_model()
iface.generate_full_results()