import json
import math

import nengo
import nengo_spa as spa
from nengo.dists import Choice
import random
import numpy as np
import operator
# import nengo_dl
import matplotlib.pyplot as plt

scheduler_states = ['ADD', 'FULL']
process_states = ['WAITING', 'RUNNING', 'DONE', "PRE_WAIT"]

dimensions = 16

calc_n_neurons = 4096

g_num_cores = 4096

class Process:
    def __init__(self, max_cores=4096, n_cores=None, time_needed=None, max_time=32, model_id=0, start_time = 0):
        if n_cores is None:
            self.needed_cores = random.randint(1, max_cores)
        else:
            self.needed_cores = n_cores

        if time_needed is None:
            self.needed_time = random.randint(1, max_time)
        else:
            self.needed_time = time_needed

        self.start_time = start_time
        if start_time == 0:
            self.current_state = process_states[0]
        else:
            self.current_state = process_states[3]

        self.wait_time = 0
        self.run_time = 0

        self.current_run_time = 0
        self.model_id = model_id


    @property
    def current_state(self):
        if self._current_state == process_states[3]:  # pre_wait
            if self.wait_time >= self.start_time:
                self._current_state = process_states[0]
                # return process_states[0]
        elif self._current_state == process_states[0]:  # wait:
            if self.wait_time < self.start_time:
                self._current_state = process_states[3]  ## Pre wait since start_time is not yet hit

        return self._current_state

    @current_state.setter
    def current_state(self, value):
        self._current_state = value

    def tick(self):

        if self.current_state == process_states[0]:
            self.wait_time += 1
        elif self.current_state == process_states[1]:
            self.run_time += 1
            self.current_run_time += 1

        if self.run_time >= self.needed_time:
            self.current_state = process_states[2]
            print(f"Process completed with rt:{self.run_time}, wt:{self.wait_time}")

    def interrupt(self):
        if self.current_state != process_states[3]:
            self.current_state = process_states[0]
            print(f"Proc {self.model_id} interrupt with {self.current_run_time} rt")
            self.current_run_time = 0

    def to_dict(self):
        return {
            'wait_time': int(self.wait_time),
            'run_time': int(self.run_time),
            'needed_time': int(self.needed_time),
            'start_time': int(self.start_time),
            'current_run_time': int(self.current_run_time),
            'state': self.current_state,
            'model_id': int(self.model_id)
        }


test_process_list = [Process(4096, max_time=4) for _ in range(0, 10)]
waiting_processes = []
running_processes = []


def populate_waiting(start_time=1, end_time=32, num_simult=3, total=10):
    """
    Populates a waiting queue list (task_process_list base)
    Used for testing algorithm
    :return:
    """
    # start_time = 1
    # end_time = 32
    bucket = list(range(start_time, end_time))
    rand_times = np.random.choice(bucket, size=len(test_process_list), replace=False)
    run_times = [min(max((i % num_simult * rand_times[i]), 1), end_time) for i in range(total)]
    for i in range(0, len(test_process_list)):

        p = test_process_list.pop()
        if i <= 3:
            p.start_time = i
        else:
            p.start_time = rand_times[i]
        p.needed_time = run_times[i]
        p.model_id = i
        waiting_processes.append(p)
    cm = f"LOC\t| ST\t| NC\t| NT\n"
    cm += "---------------------------------------"
    i = 0

    def gpp(item):
        return f"{item}\t| "

    for p in waiting_processes:
        cm = f"{cm}\n" + gpp(i) + gpp(p.start_time) + gpp(p.needed_cores) + gpp(p.needed_time)
        i += 1
    print(cm)
    return waiting_processes


def waiting_process_size():
    global g_num_cores
    if len(waiting_processes) > 0:
        return waiting_processes.needed_cores
    else:
        return g_num_cores + 1


def is_ready(x):
    nc = x[0]
    next_proc = waiting_process_size()
    if nc - next_proc > 0:
        return 1
    return 0


def running_process_size(x=0):
    if len(running_processes) > 0:
        return sum(p.needed_cores for p in running_processes)
    else:
        return 0


def can_add(x):
    if (x[0] - x[1]) > 0:
        return 1
    else:
        return 0


class QueueNode:
    def __init__(self, wait_q_ovr=None, time_slice=3):
        self.time_slice = time_slice

        if wait_q_ovr is None or len(wait_q_ovr) < 1:
            self.wait_q = populate_waiting()
            self.wait_q[0].start_time = 1

        else:
            self.wait_q = wait_q_ovr

        self.run_q = []
        self.last_active = 0
        print(len(self.wait_q))
        print("-")
        print(self.wait_q[0].start_time)
        self.added_element = 0
        self.output_last_active = 0
        self.stats = ""
        self.dict_stats = {}
        self.last_inter = 0
        self._wait_q = []


    def check_inter(self, t):
        epoc_diff = t - self.last_inter
        epoc_diff = int(np.floor(epoc_diff))
        if epoc_diff > 0:
            self.last_inter = int(np.floor(t))
        return epoc_diff

    def get_stats(self):
        return self.dict_stats

    def get_str_stats(self):
        return self.stats

    @property
    def run_pq(self):
        rpq = self.run_q
        rpq = sorted(rpq, key=operator.attrgetter('current_run_time'))
        print(rpq)
        if len(rpq) > 0:
            for p in rpq:
                if p.current_state == process_states[0]:
                    return p

        else:
            return -1

        # self.wait_q[0].start_time = 0

    def get_procs_that_should_run(self):
        nprocs = 0
        procs = []
        for p in self.run_q:
            if p.current_state == process_states[1]:
                procs.append(p.model_id)
                nprocs += 1

        return nprocs, procs

    def get_procs_that_should_wait(self):
        nprocs = 0
        procs = []
        for p in self.run_q:
            if p.current_state == process_states[0]:
                procs.append(p.model_id)
                nprocs += 1
        return nprocs, procs

    def get_top_proc_size(self, t):
        tm = -1
        if len(self.wait_q) > 0:
            top_proc = self.wait_q[0]
            if t >= top_proc.start_time:
                tm = top_proc.needed_cores

        return tm

    def start_next_proc(self, t):
        next_proc = self.wait_q.pop(0)
        next_proc.current_state = "RUNNING"
        self.run_q.append(next_proc)

    def start_proc(self, t, x):
        start_proc_ok = -1
        start_proc_size = -1
        #@todo: This is a secondary check (the size of the process is not too big to fit) double checking the neurons
        if self.get_top_proc_size(t) > -1:
            self.start_next_proc(t)
            start_proc_ok = 1
            start_proc_size = self.run_q[0].needed_cores

        start_proc_message = [start_proc_ok, start_proc_size]
        x[0] = start_proc_ok
        x[1] = start_proc_size
        return x

    def process_update(self, t):
        epoc_diff = self.epoch_check(t)
        if epoc_diff > 0:
            for i in range(0, epoc_diff):
                [p.tick() for p in self.wait_q]
                [p.tick() for p in self.run_q]

    def get_running_proc_core_usage(self):
        return sum(
            item.needed_cores
            for item in self.run_q
            if item.current_state == "RUNNING"
        )

    def epoch_check(self, t):
        epoc_diff = t - self.last_active
        epoc_diff = int(np.floor(epoc_diff))
        return epoc_diff

    def output_message(self, t):

        epoc_diff = self.epoch_check(t)

        if epoc_diff > 0:
            wait_time_r = -1
            if len(self.wait_q) > 0:
                wait_time_r = self.wait_q[0].wait_time

            print(f"epoc_diff:{epoc_diff} | last_active: {self.last_active}|"
                  f"top_size:{self.get_top_proc_size(t)}"
                  f" | waiting_q_size: {len(self.wait_q)}"
                  f" | wait_time: {wait_time_r}")
            self.process_update(t)
            self.last_active = np.floor(t)
            self.compile_stats(t)
            self.compile_stats_dict(t)

        top_proc_size = self.get_top_proc_size(t)
        running_proc_cores = self.get_running_proc_core_usage()
        return [top_proc_size, running_proc_cores, self.last_active]

    def output_run_message(self, t):
        # Just change the logic for RR.
        # A process is ready to stop if it has a current run time > time_slice
        top_proc_remove = 0
        if self.get_running_proc_core_usage() > 0:
            for p in self.run_q:
                if p.current_run_time >= self.time_slice:
                    top_proc_remove += 1
        return [top_proc_remove]

    def epoch_diff(self, t):
        return int(np.floor(t - self.output_last_active))

    def input_message(self, t, x):

        om = [0, -1]
        epoc_diff = self.epoch_diff(t)
        if epoc_diff > 0:
            #print('------- ' + str(x))
            #self.output_last_active = int(np.floor(t))

            if x[0] > 1.0:
                #print(f"PMAN x:{x} | adder :{self.added_element}")
                # if self.added_element == 0:
                #    self.added_element = 1

                #print(f"add_new_proc: {t},{x} ")
                om = self.start_proc(t, om)

                om[0] = -2
                # else:
                #    output_message = [-1]

            else:
                ttr = 0
                pstate = "NONE"
                if len(self.run_q) > 0:
                    ttr = self.run_q[0].needed_time
                    pstate = self.run_q[0].current_state
                # print(f"PMAN: {self.output_last_active} |"
                #       f"RUNSZ:{self.get_running_proc_core_usage()}"
                #       f"TTR:{ttr} | STATE:{pstate}")
                # self.added_element = 0
            self.output_message(t)

            
        return om[0]

    def input_interrupt(self, t, x):
        output_message = [-1]
        if x[0] >= 1.0:
            if self.check_inter(t) > 0 and t > 2:
                print(f"PMAN INTERUPT x:{x} ")
                ## Make spiking
                num_done = 0
                wait_append = []
                run_append = []
                for i in range(len(self.run_q)):
                    p = self.run_q[i]
                    crt = p.current_run_time
                    ts = self.time_slice
                    if (crt >= ts):
                        #self.run_q.pop(i)
                        p.interrupt()
                        wait_append.append(p)
                        #self.wait_q.append(p)
                    else:
                        run_append.append(p)
                for p in wait_append:
                    self.wait_q.append(p)

                self.run_q = run_append


                output_message[0] = num_done * -1
        return output_message

    def compile_stats(self, t):
        def hdr(tp="WAIT"):
            return f"**** {tp} QUEUE **** \nCS \t WT \t RT\t CUR_RT \t \n"

        def pm(p):
            return f"{p.current_state}\t{p.wait_time}\t{p.run_time} \t {p.current_run_time}\n"

        message = f"** STATS CT: {t} | Epoch {self.output_last_active} ** \n"

        message += hdr()
        for p in self.wait_q:
            message += pm(p)
        message += hdr("RUN")
        for p in self.run_q:
            message += pm(p)

        self.stats += message

    def gen_pq(self, which_queue="RUN", t = 0):
        statd = []
        q_q = self.run_q if which_queue == "RUN" else self.wait_q
        for p in q_q:
            dat = p.to_dict()
            dat['epoch'] = t
            statd.append( dat )
        return statd

    def compile_stats_dict(self, t):
        stat_t = {'epoch': self.output_last_active, 'time': float(t)}
        wq = self.gen_pq("WAIT",float(t))
        rq = self.gen_pq("RUN",float(t))
        stat_t['wait_q'] = wq
        stat_t['run_q'] = rq
        self.dict_stats[float(t)] = stat_t



def FCFS_sys(num_cores=4096, calc_n_neurons=512, sim_q_input=None):
    fcfs = nengo.Network()
    with fcfs:
        # if sim_q_input is None:
        #     qsim_waiting = nengo.Node(queue_nodes.output_message, size_out=3)
        # else:
        qsim_waiting = nengo.Node(sim_q_input, size_out=3)
        fcfs.qsim_waiting = qsim_waiting
        print(running_process_size())
        num_cores_node = nengo.Node(num_cores)

        running_procs_size_en = nengo.Ensemble(calc_n_neurons, 1, radius=num_cores)
        fcfs.running_procs_size_en = running_procs_size_en
        fcfs.num_coresa_node = num_cores_node
        # this works

        num_cores_en = nengo.Ensemble(1024, 1, radius=num_cores)
        fcfs.num_cores_en = num_cores_en

        nengo.Connection(num_cores_node, num_cores_en)
        avail_procs = nengo.Ensemble(calc_n_neurons, 1, radius=num_cores)
        fcfs.avail_procs = avail_procs

        nengo.Connection(num_cores_en, avail_procs)
        nengo.Connection(running_procs_size_en, avail_procs, transform=-1)

        def can_add_thd_logic(x):
            x = np.round(x)
            return x

        # New Process Addition
        # waiting_proc_q_top_size = nengo.Node(1)
        waiting_proc_size = nengo.Ensemble(calc_n_neurons, 1, radius=num_cores)
        fcfs.waiting_proc_size = waiting_proc_size

        def waiting_q_input_logic(x):
            if x <= 0:
                return num_cores * 2
            else:
                return x

        can_add_next_proc = nengo.Ensemble(calc_n_neurons, 1)
        fcfs.can_add_next_proc = can_add_next_proc
        next_proc_size_check = nengo.Ensemble(calc_n_neurons, 1,
                                              radius=num_cores, neuron_type=nengo.neurons.SpikingRectifiedLinear())
        next_proc_size_check.intercepts = Choice([-.1])
        nengo.Connection(avail_procs, next_proc_size_check)
        nengo.Connection(waiting_proc_size, next_proc_size_check, transform=-1)

        def can_add_next_proc_logic(x):
            if x > 0:
                return 1
            else:
                return 0

        nengo.Connection(next_proc_size_check, can_add_next_proc, function=can_add_thd_logic)
        ### Add New
        ## Queue Repr:
        nengo.Connection(qsim_waiting[0], waiting_proc_size, function=waiting_q_input_logic)
        nengo.Connection(qsim_waiting[1], running_procs_size_en)

        ###WORKS GREAT!
        add_new_proc_system = nengo.Ensemble(calc_n_neurons, 1, radius=2, neuron_type=nengo.LIF(tau_rc=0.001))

        nengo.Connection(can_add_next_proc, add_new_proc_system, function=np.ceil)
        igm = nengo.networks.workingmemory.InputGatedMemory(calc_n_neurons, 1, difference_gain=.8)
        # nengo.Connection(add_new_proc_system, fcfs_output_node)
        nengo.Connection(can_add_next_proc, igm.input)
        # nengo.Connection(fcfs_output_node, igm.gate)

        fcfs.add_new_proc_system = add_new_proc_system
        # fcfs.fcfs_out_node = fcfs_output_node
        fcfs.qsim_waiting_node = qsim_waiting
        fcfs.gate_out = igm.gate

    return fcfs


def timer_clock(time_slice=3):
    def nd_time(t):
        rv = t % 3
        if math.isclose(rv, round(rv), rel_tol=0.02):
            return 7
        return 0

    tcm = nengo.Network()
    with tcm:
        a = nengo.Ensemble(n_neurons=200, dimensions=2, radius=1.5)

        # Define an input signal within our model
        stim = nengo.Node(nd_time)

        # Connect the Input signal to ensemble a, affecting only the
        # first dimension. The `transform` argument scales the effective
        # strength of the connection by tau.
        tau = 0.1
        nengo.Connection(stim, a[0], transform=tau, synapse=tau)

        control = nengo.Node(1)

        # Connect the "Control" signal to the second of a's two input channels.
        nengo.Connection(control, a[1], synapse=0.005)

        # Create a recurrent connection that first takes the product
        # of both dimensions in A (i.e., the value times the control)
        # and then adds this back into the first dimension of A using
        # a transform
        nengo.Connection(a, a[0],
                         function=lambda x: x[0] * x[1],
                         synapse=tau)

        reset_val = nengo.Ensemble(n_neurons=200, dimensions=1, radius=5)
        nengo.Connection(stim, reset_val, function=lambda x: -5 if x < 1 else 0)
        nengo.Connection(reset_val, a[1], synapse=0.0005)

        def clock_ctrl(t, x):
            out = [0]
            if t % time_slice == 0:
                return 5
            else:
                return 0

        clock_out_nd = nengo.Node(clock_ctrl, size_in=1, size_out=1)
        nengo.Connection(a[0], clock_out_nd, function=lambda x: 1 if x > 0.5 else 0)
        tcm.clock_out = clock_out_nd
    return tcm


class SimulatedScheduler:
    def __init__(self, process_list=None, scheduler_mode="RR", rr_time_slice=5,num_cores=4096,use_dl=False):
        self.num_cores = num_cores
        self.probes = []
        if rr_time_slice < 0:
            rr_time_slice = 3
        if scheduler_mode == "FCFS":
            rr_time_slice = 99999
        self.rr_time_slice = rr_time_slice

        if process_list is None:
            queue_nodes = QueueNode()
        else:
            queue_nodes = QueueNode(process_list, rr_time_slice)
        self.queue_nodes = queue_nodes
        #self.main_scheduler()
        self.model_two()
        if use_dl:
            import nengo_dl
            self.sim = nengo_dl.Simulator(self.model)
        else:
            self.sim = nengo.Simulator(self.model)
        global g_num_cores
        g_num_cores = num_cores
        self.calc_n_neurons = 4096
        self.clock_neurons = 2048


    def main_scheduler(self):
        model = spa.Network(label="Scheduler Network")
        time_slice = self.rr_time_slice
        queue_nodes = self.queue_nodes
        with model:
            fcfs_loader = FCFS_sys(num_cores=self.num_cores, sim_q_input=queue_nodes.output_message)
            # Create nodes for communication to virtual queue
            virtual_queue_start_proc = nengo.Node(queue_nodes.input_message, size_in=1, size_out=1)
            nengo.Connection(fcfs_loader.add_new_proc_system, virtual_queue_start_proc, function=lambda x: x + 1)
            nengo.Connection(virtual_queue_start_proc, fcfs_loader.gate_out)
            interrupt_clock_sys = timer_clock(time_slice)
            interupt_check = nengo.Ensemble(256, 1)
            nengo.Connection(interrupt_clock_sys.clock_out[0], interupt_check)
            outpt_p = nengo.Probe(interupt_check, synapse=0.01)

            interrupt_node = nengo.Node(queue_nodes.input_interrupt, size_in=2, size_out=2)
            int_sig = nengo.Ensemble(1024, dimensions=2, radius=time_slice + 1, neuron_type=nengo.neurons.RectifiedLinear())
            #nengo.Connection(interrupt_clock_sys.clock_out, interrupt_node[1])
            nengo.Connection(int_sig,interrupt_node,function=lambda x: [np.max(x),np.max(x)])

            # sim = nengo.Simulator(model)
        self.model = model
        self.probes.append(outpt_p)

    def model_two(self):
        model = nengo.Network()
        num_cores = self.num_cores
        time_slice = self.rr_time_slice
        queue_nodes = self.queue_nodes
        with model:
            print(running_process_size())
            num_cores_node = nengo.Node(num_cores)

            running_procs_size_en = nengo.Ensemble(num_cores * 2, 1, radius=num_cores + 2,
                                                   neuron_type=nengo.neurons.RectifiedLinear())

            num_cores_en = nengo.Ensemble(self.num_cores * 2, 1, radius=num_cores)
            nengo.Connection(num_cores_node, num_cores_en)

            avail_procs = nengo.Ensemble(num_cores * 2, 1, radius=num_cores)
            nengo.Connection(num_cores_en, avail_procs)
            nengo.Connection(running_procs_size_en, avail_procs, transform=-1)

            def can_add_thd_logic(x):
                x = np.round(x)
                return x

            ## New Process Addition

            waiting_proc_q_top_size = nengo.Node(1)
            waiting_proc_size = nengo.Ensemble(self.calc_n_neurons, 1, radius=num_cores)

            def waiting_q_input_logic(x):
                if x <= 0:
                    return num_cores * 2
                else:
                    return x

            can_add_next_proc = nengo.Ensemble(self.calc_n_neurons, 1)
            next_proc_size_check = nengo.Ensemble(self.calc_n_neurons, 1,
                                                  radius=num_cores, neuron_type=nengo.neurons.SpikingRectifiedLinear())
            next_proc_size_check.intercepts = Choice([-.1])
            nengo.Connection(avail_procs, next_proc_size_check)
            nengo.Connection(waiting_proc_size, next_proc_size_check, transform=-1)

            def can_add_next_proc_logic(x):
                if x > 0:
                    return 1
                else:
                    return 0

            nengo.Connection(next_proc_size_check, can_add_next_proc, function=can_add_thd_logic)
            ### Add New
            ## Queue Repr:
            qsim_waiting = nengo.Node(queue_nodes.output_message, size_out=3)
            qsim_add_spike = nengo.Node(queue_nodes.input_message, size_in=1, size_out=1)
            nengo.Connection(qsim_waiting[0], waiting_proc_size, function=waiting_q_input_logic)
            nengo.Connection(qsim_waiting[1], running_procs_size_en)

            ###WORKS GREAT!
            add_new_proc_system = nengo.Ensemble(self.calc_n_neurons, 1, radius=2, neuron_type=nengo.LIF(tau_rc=0.001))
            nengo.Connection(can_add_next_proc, add_new_proc_system, function=np.ceil)

            igm = nengo.networks.workingmemory.InputGatedMemory(self.calc_n_neurons, 1, difference_gain=.8)
            nengo.Connection(add_new_proc_system, qsim_add_spike)
            nengo.Connection(can_add_next_proc, igm.input)
            nengo.Connection(qsim_add_spike, igm.gate)

            ## Round Robin Logic

            clock_in = nengo.Node(lambda t: t)
            clock_neurons = self.clock_neurons
            nx = nengo.LIF(tau_ref=1)
            inter_clock = nengo.Ensemble(clock_neurons, dimensions=1)
            nengo.Connection(clock_in, inter_clock, function=lambda x: 0 - np.fmod(x, time_slice)[0])
            inter_spike_clock = nengo.Ensemble(clock_neurons, dimensions=1,
                                               neuron_type=nx,
                                               max_rates=[.5] * clock_neurons,
                                               gain=[-1] * clock_neurons,
                                               bias=[1] * clock_neurons)
            nengo.Connection(inter_clock, inter_spike_clock)
            clock_out = nengo.Ensemble(clock_neurons, dimensions=1)
            nengo.Connection(inter_spike_clock, clock_out, function=lambda x: np.negative(x))
            interrupt_node = nengo.Node(queue_nodes.input_interrupt, size_in=1, size_out=1)
            nengo.Connection(clock_out, interrupt_node)

        self.model = model
        return model


    def get_plots(self, ax=None):
        ax = None
        for plt in self.probes:
            ax = self.plot(plt, ax)
        return ax

    def plot(self, itm, ax=None, idx=slice(None)):
        if ax is None:
            plt.figure()
            ax = plt.gca()
        ax.plot(self.sim.trange(), self.sim.data[itm][idx], label="item")
        ax.legend()
        return ax

    def run(self, seconds=1):
        self.sim.run(seconds)



def proc_list_test_gen():
    start_times =  [0 ,0 ,10,10,20,20]
    needed_times = [20  ,20  ,20  ,20  ,20  ,20]
    needed_cores = [4000,4000,2000,2000,1000,1000]
    proc_list = []
    for i in range(len(start_times)):
        p = Process(0,needed_cores[i],time_needed=needed_times[i],model_id = i,start_time=start_times[i])
        proc_list.append(p)

    return proc_list


def demo():
    system = SimulatedScheduler(process_list = proc_list_test_gen())
    system.run(30)
    return system


def save_simulated_scheduler_stats(scheduler, filename="./scheduler_stats.json"):
    stats = scheduler.queue_nodes.get_stats()
    with open(filename, 'w') as out_f:
        json.dump(stats, out_f)


# s = demo()
# data = s.queue_nodes.get_stats()
# save_simulated_scheduler_stats(s, "../test_stats.json")
