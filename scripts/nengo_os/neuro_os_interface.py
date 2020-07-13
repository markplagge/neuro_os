from typing import List

from . import Process, SimulatedScheduler
from .rr_full import process_states
from .rr_full import calc_n_neurons


class NemoNengoInterface:

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


    def init_process_list_from_json(self, js_file):
        """
        Using the Nemo config file, populate jobs/processes
        :param js_file: Path to the nemo configuration json file
        :return: NONE
        """
        import json
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
            needed_cores = mod_dat[mid]['requested_time']
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
        self.primary_scheduler = SimulatedScheduler(self.process_list, self.sc_mode, rr_time_slice=self.rr_time_slice,
                                                    num_cores=self.cores_in_sim)
        self.model_init = True

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
    def precompute_q(self, type):
        return self.primary_scheduler.queue_nodes.dict_stats[float(self.precompute_time)][type][float(self.precompute_time)]

    @property
    def precompute_run_q(self):
        return self.precompute_q("run_q")

    @property
    def precompute_wait_q(self):
        return self.precompute_q("wait_q")

    def running_proc_precompute(self) -> List[int]:
        data = self.precompute_run_q
        return [pd['model_id'] for pd in data if pd['state'] == "RUNNING"]

    def waiting_proc_precompute(self) -> List[int]:
        data = self.precompute_wait_q
        return [pd['model_id'] for pd in data]

    def increment_pc(self):
        self.precompute_time += 1



def test_pre():
    iface = NemoNengoInterface(rr_time_slice=5)
    iface.init_model()
    iface.generate_full_results(end_time=25)
    run_procs_t = {}
    wait_procs_t = {}
    for i in range(25):
        run_procs_t[i] = iface.precompute_run_q
        wait_procs_t[i] = iface.precompute_wait_q
        iface.increment_pc()

    return run_procs_t, wait_procs_t