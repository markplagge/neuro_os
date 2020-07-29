import json
from enum import IntFlag
from pathlib import Path
from typing import List

import nengo_os
from . import ConventScheduler
from .print_control import d_print

from nengo_os import Process, SimulatedScheduler
from .rr_full import process_states, SimpleProc, RRProcessStatus
from .rr_full import calc_n_neurons


class NemoNengoInterfaceBase:
    def __init__(self, use_nengo_dl: bool =False, cores_in_sim: int = 4096, mode: int = 0, rr_time_slice: int = 4096):
        """
        NemoNengoInterface: Main interface between Nemo code and NemoOS-Python interface
        Use this to create and manage nengo based schedulers. MUST RUN init_process_list_from_json OR add_process
        before starting the scheduler.
        :type use_nengo_dl: bool
        :type cores_in_sim: int
        :type mode: int
        :type rr_time_slice: int
        :param use_nengo_dl: Set to True if using nengo_dl (deep learning, GPU acceleration)
        :param cores_in_sim: The numbers of neurosynaptic cores in the simulation
        :param mode: MODE: FCFS: 0, RR = 1
        :param rr_time_slice: TimeSlice for interrupts for round robin
        """
        self.process_list = []
        self.primary_scheduler = None
        self.use_neng_del = use_nengo_dl
        self.cores_in_sim = cores_in_sim
        self.sc_mode = "FCFS" if mode == 0 else "RR"
        self.rr_time_slice = rr_time_slice
        self.nemo_time = 0
        self.precompute_time = 1
        self.model_init = False
        self.scheduler_stat_file = Path("scheduler_data.json")

    def init_process_list_from_json(self, js_file):
        """
        Using the Nemo config file, populate jobs/processes
        :param js_file: Path to the nemo configuration json file
        :return: NONE
        """
        import json
        print("LOADING " + js_file)
        mdx = json.load(open(js_file, 'r'))

        models = mdx['models']
        mod_dat = {}
        for m in models:
            mid = m['id']

            needed_cores = m['needed_cores']
            needed_time = m['requested_time']
            if needed_time < 0:
                needed_time = 9223372036854775800
            mod_dat[mid] = {'needed_cores': needed_cores, 'needed_time': needed_time}
        for task in mdx['scheduler_inputs']:
            mid = task['model_id']
            needed_time = mod_dat[mid]['needed_time']
            needed_cores = mod_dat[mid]['needed_cores']
            scheduled_start_time = task['start_time']
            p = Process(n_cores=needed_cores, time_needed=needed_time, model_id=mid, start_time=scheduled_start_time)
            self.process_list.append(p)


    def add_process(self, model_id, n_cores, n_time, s_time):
        """
        Adds a process to the process queue
        :param model_id: model_id - Unique ID for process
        :param n_cores: number of cores for process
        :param n_time: needed time for the job
        :param s_time: scheduled start time
        :return: NONE
        """
        p = Process(n_cores=n_cores, time_needed=n_time, model_id=model_id, start_time=s_time)
        self.process_list.append(p)

    def init_model(self):
        print("Compiling Model")
        assert(self.process_list is not None)

        self.primary_scheduler = SimulatedScheduler(self.process_list, self.sc_mode, rr_time_slice=self.rr_time_slice,
                                                    num_cores=self.cores_in_sim,use_dl=self.use_neng_del)
        self.model_init = True
        print("Model compile complete")

    def run_sim_time(self, n_ticks=1):
        """
        Runs sim for a set number of ticks
        :param n_ticks:
        :return:
        """
        self.primary_scheduler.run(seconds=n_ticks)
        self.nemo_time += n_ticks

    def run_single(self):
        """
        Runs sim for a single second
        :return:
        """
        self.run_sim_time(1)

    def run_until_current_time(self, nemo_time):
        time_diff =  nemo_time - self.nemo_time
        if time_diff > 0:
            self.run_sim_time(time_diff)

    @property
    def running_procs(self) -> List[int]:
        """
        Gets a list of model_ids of running processes
        :return: A list of model IDs
        :rtype: List[int]
        """
        return [p.model_id for p in self.primary_scheduler.queue_nodes.run_q]

    @property
    def waiting_procs(self):
        """
        Gets a list of model_ids of waiting processses
        :return: A list of model IDs
        :rtype: List[int]
        """
        return [p.model_id for p in self.primary_scheduler.queue_nodes.wait_q]

    def generate_full_results(self, end_time = 5000):
        self.run_until_current_time(end_time)
        queue_stat_file = self.scheduler_stat_file.open("w")
        stats = self.primary_scheduler.queue_nodes.dict_stats
        json.dump(stats,queue_stat_file)
        print(f"Saved scheduler stats to {queue_stat_file.name}")


    def precompute_q(self, type):
        try:
            pq =  self.primary_scheduler.queue_nodes.dict_stats[float(self.precompute_time)][type]
        except KeyError:
            print("KEY " + str(self.precompute_time) + "NIC, attempting recovery")
            self.run_sim_time(50)
            pq = self.primary_scheduler.queue_nodes.dict_stats[float(self.precompute_time)][type]
        rq = []
        if type == "run_q":
            for p in pq:
                if p['state'] != 2:
                    rq.append(p)
        elif type == "done_q":
            for p in pq:
                if p['state'] == 2:
                    rq.append(p)
        else:
            rq = pq

        #if p['state'] == 2
        #rq = [p  for p in pq if p['state'] != 2 ]
        return rq

    @property
    def precompute_run_q(self):
        pq = self.precompute_q("run_q")

        return pq

    @property
    def precompute_wait_q(self):
        return self.precompute_q("wait_q")

    def running_proc_precompute(self) -> List[int]:
        data = self.precompute_run_q


        d =  [pd['model_id'] for pd in data]
        d_print ("Running Proc Value: " + str(d))
        return d

    def waiting_proc_precompute(self) -> List[int]:
        data = self.precompute_wait_q
        d = [pd['model_id'] for pd in data]
        d_print("Waiting Proc Value: " + str(d))
        return d

    def increment_pc(self):
        self.precompute_time += 1

    def running_proc_precompute_procs(self) -> List[dict]:
        return [p.to_dict() for p in  self.primary_scheduler.queue_nodes.run_q]

    def waiting_proc_precompute_procs(self) -> List[dict]:
        d = [p.to_dict() for p in self.primary_scheduler.queue_nodes.wait_q]
        return d

    def current_precompute_time(self):
        return self.primary_scheduler




class NemoNengoInterface(NemoNengoInterfaceBase):
    def __init__(self,use_own_procs=True, multiplexing=True,mode = None,total_cores=4096,time_slice=50,
                 use_conventional=True,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.multiplexing = multiplexing
        if mode is None:

            if self.sc_mode == "FCFS":
                mode = "FCFS"
            elif self.sc_mode == "RR":
                mode = "RR"
            else:
                raise Exception(f"Got None in NNI mode, and an invalid mode in base class {self.sc_mode} ")
        elif mode == "FCFS":
            time_slice = -1
        elif mode == "RR" and time_slice <1:
            raise Exception (f"Got Round Robin mode but a time_slice < 1: {time_slice} ")


        self.total_cores = total_cores
        self.current_time = 0
        self.time_slice = time_slice

        if use_own_procs:
            self.process_list = [p.proc for p in self.paper_procs()]
        else:
            self.process_list = []
        self.use_conventional =  use_conventional

    def init_process_list_from_json(self, js_file):

            """
            Using the Nemo config file, populate jobs/processes
            :param js_file: Path to the nemo configuration json file
            :return: NONE
            """
            self.process_list = []
            import json
            print("LOADING " + js_file)
            mdx = json.load(open(js_file, 'r'))

            models = mdx['models']
            mod_dat = {}
            for m in models:
                mid = m['id']

                needed_cores = m['needed_cores']
                needed_time = m['requested_time']
                if needed_time < 0:
                    needed_time = 9223372036854775800
                mod_dat[mid] = {'needed_cores': needed_cores, 'needed_time': needed_time}
            for task in mdx['scheduler_inputs']:
                mid = task['model_id']
                needed_time = mod_dat[mid]['needed_time']
                needed_cores = mod_dat[mid]['needed_cores']
                scheduled_start_time = task['start_time']
                task_id = task['task_id']
                p = RRProcessStatus(n_cores=needed_cores, time_needed=needed_time, model_id=mid,
                            start_time=scheduled_start_time,task_id=task_id)


                self.process_list.append(p)


    @staticmethod
    def paper_procs():
        return [       # name   id arrival1,+2,      comp_t, needed_cores
            SimpleProc("Cifar",      1, 0,0,         4450, 4038,1), #test single process
            SimpleProc("SAR",        2, 4450,4450,   1125, 3974,2),
            SimpleProc("Tonic",      3, 5575,5575,   8,    2   ,3),
            SimpleProc("Saturation", 4, 5575,5575,   81,   1439,4),
            SimpleProc("Cifar",      1, 5664,5664,   5325, 4038,5),
            SimpleProc("SAR",        2, 10989,10989, 1876, 3974,6),
            SimpleProc("Tonic",      3, 12865,12865, 7,    2   ,7),
            SimpleProc("Cifar",      1, 12872,12872, 5649, 4038,8),
            SimpleProc("SAR",        2, 18521,18521, 1196, 3974,9),
            SimpleProc("Tonic",      3, 19717,19717, 8, 2      ,10)
        ]

    @staticmethod
    def rr_paper_procs():
        return [       # name   id arrival1,+2, comp_t, needed_cores
            SimpleProc("Cifar", 1, 0, 0,        4000, 4038  ,1),  # test single process
            SimpleProc("SAR",   2, 0, 0,        1000, 3974  ,2),
            SimpleProc("Cifar", 3, 0, 0,        4000, 4038  ,3),  # test single process
            SimpleProc("SAR",   4, 110, 110,      1000, 3974,4),
            SimpleProc("Cifar", 5, 110, 110,      4000, 4038,5),  # test single process
            SimpleProc("SAR",   6, 110, 110,      1000, 3974,6)

        ]

class NemoNengoInterfaceConventional(NemoNengoInterface):
    def __init__(self,*args,**kwargs):
        super(NemoNengoInterfaceConventional, self).__init__(*args,**kwargs)
        self.primary_scheduler = ConventScheduler.ConventScheduler(self.sc_mode, self.total_cores, self.time_slice, self.multiplexing)



def test_pre():
    iface = NemoNengoInterfaceBase(rr_time_slice=5, use_nengo_dl=True)
    iface.init_model()
    iface.generate_full_results(end_time=25)
    run_procs_t = {}
    wait_procs_t = {}
    for i in range(25):
        run_procs_t[i] = iface.precompute_run_q
        wait_procs_t[i] = iface.precompute_wait_q
        iface.increment_pc()

    return run_procs_t, wait_procs_t