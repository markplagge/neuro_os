import nengo
import nengo_spa as spa
from nengo_spa import Vocabulary
from nengo.dists import Choice
from nengo.utils.ensemble import response_curves, tuning_curves
import random
import numpy as np
import nengo_extras

import tensorflow as tf

import nengo_dl

from collections import deque

import matplotlib.pyplot as plt
import numpy as np

from nengo.utils.filter_design import cont2discrete

scheduler_states = ['ADD', 'FULL']
process_states = ['WAITING', 'RUNNING', 'DONE']

dimensions = 16
num_cores = 64
calc_n_neurons = 256

from nengo.solvers import LstsqL2


class Process:
    def __init__(self, max_cores, n_cores=None, time_needed=None, max_time=32):
        if n_cores is None:
            self.needed_cores = random.randint(1, max_cores)
        else:
            self.needed_cores = n_cores

        if time_needed is None:
            self.needed_time = random.randint(1, max_time)
        else:
            self.needed_time = time_needed

        self.current_state = process_states[0]
        self.wait_time = 0
        self.run_time = 0
        self.start_time = 0

    def tick(self):

        if self.current_state == process_states[0]:
            self.wait_time += 1
        elif self.current_state == process_states[1]:
            self.run_time += 1

        if self.run_time >= self.needed_time:
            self.current_state = process_states[2]
            print(f"Process completed with rt:{self.run_time}, wt:{self.wait_time}")


test_process_list = [Process(num_cores, max_time=4) for _ in range(0, 10)]
waiting_processes = []
running_processes = []


def populate_waiting():
    start_time = 1
    end_time = 32
    bucket = list(range(start_time, end_time))
    rand_times = np.random.choice(bucket, size=len(test_process_list), replace=False)
    for i in range(0, len(test_process_list)):

        p = test_process_list.pop()
        if i == 0:
            p.start_time = 0
        else:
            p.start_time = rand_times[i]
        waiting_processes.append(p)
    cm = f"LOC\t| ST\t| NC\t| NT\n"
    cm += "---------------------------------------"
    i = 0

    def gpp(item):
        return f"{item}\t| "

    for p in waiting_processes:
        cm = f"{cm}\n" + gpp(i) + gpp(p.start_time) + gpp(p.needed_cores) + gpp(p.needed_time)
    print(cm)
    return waiting_processes


def process_ready(t):
    if t >= waiting_processes[0].start_time:
        return 1
    return 0


def run_process(t):
    p = waiting_processes.pop()
    p.current_state = process_states[1]
    running_processes.append(p)
    return 1


def waiting_process_size():
    if len(waiting_processes) > 0:
        return waiting_processes.needed_cores
    else:
        return num_cores + 1


def is_ready(x):
    nc = x[0]
    next_proc = waiting_process_size()
    if nc - next_proc > 0:
        return 1
    return 0


def running_process_size(x=0):
    if len(running_processes) > 0:
        return sum([p.needed_cores for p in running_processes])
    else:
        return 0


def can_add(x):
    if (x[0] - x[1]) > 0:
        return 1
    else:
        return 0


class QueueNode:
    def __init__(self, **kwargs):

        self.wait_q = populate_waiting()
        self.wait_q[0].start_time = 1
        self.run_q = []
        self.last_active = 0
        print(len(self.wait_q))
        print("-")
        print(self.wait_q[0].start_time)
        self.added_element = 0
        self.output_last_active = 0

        # self.wait_q[0].start_time = 0


    def get_top_proc_size(self, t):
        tm = -1
        if len(self.wait_q) > 0:
            top_proc = self.wait_q[0]
            if t >= top_proc.start_time:
                tm = top_proc.needed_cores

        return tm

    def start_next_proc(self, t):
        next_proc = self.wait_q.pop()
        next_proc.current_state = "RUNNING"
        self.run_q.append(next_proc)

    def start_proc(self, t, x):
        start_proc_ok = -1
        start_proc_size = -1

        if self.get_top_proc_size(t) > -1:
            self.start_next_proc(t)
            start_proc_ok = 1
            start_proc_size = self.get_top_proc_size(t)

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
        running_proc_cores = 0
        for i in range(0, len(self.run_q)):
            if self.run_q[i].current_state == "RUNNING":
                running_proc_cores += self.run_q[i].needed_cores
        return running_proc_cores

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

        top_proc_size = self.get_top_proc_size(t)
        running_proc_cores = self.get_running_proc_core_usage()
        output_message = [top_proc_size, running_proc_cores, self.last_active]
        return output_message

    def input_message(self, t, x):

        output_message = [0, -1]
        epoc_diff = int(np.floor(t - self.output_last_active))
        if epoc_diff > 0:
            print('------- ' + str(x))
            self.output_last_active = int(np.floor(t))

            if x[0] > 1.0:
                print(f"PMAN x:{x}|ade:{self.added_element}")
                # if self.added_element == 0:
                #    self.added_element = 1

                print(f"add_new_proc: {t},{x} ")
                output_message = self.start_proc(t, output_message)
                output_message[0] = -2
                # else:
                #    output_message = [-1]
            else:
                ttr = 0
                pstate = "NONE"
                if len(self.run_q) > 0:
                    ttr = self.run_q[0].needed_time
                    pstate = self.run_q[0].current_state
                print(f"PMAN: {self.output_last_active} |"
                      f"RUNSZ:{self.get_running_proc_core_usage()}"
                      f"TTR:{ttr} | STATE:{pstate}")
                # self.added_element = 0
        return output_message[0]


def AddLogic(num_cores=32, calc_n_neurons=512):
    add_logic = spa.Network(label="can_add")
    with add_logic:
        # running_processes = waiting_processes
        print(running_process_size())
        num_cores_node = nengo.Node(num_cores)
        running_size = nengo.Node(0)  # output=running_process_size())
        running_procs_size_en = nengo.Ensemble(calc_n_neurons, 1, radius=num_cores)

        # this works
        # nengo.Connection(running_size, running_procs_size_en, function=running_process_size)
        # nengo.Connection(running_size, running_procs_size_en)
        num_cores_en = nengo.Ensemble(1024, 1, radius=num_cores)
        nengo.Connection(num_cores_node, num_cores_en)

        avail_procs = nengo.Ensemble(calc_n_neurons, 1, radius=num_cores)

        nengo.Connection(num_cores_en, avail_procs)
        # nengo.Connection(running_procs_size_en, avail_procs.neurons, transform=[[-1]]*calc_n_neurons)
        nengo.Connection(running_procs_size_en, avail_procs, transform=-1)

        # nengo.Connection(running_procs_size_en, avail_procs[1])
        # can_add_process = nengo.Ensemble(calc_n_neurons,dimensions=1,encoders=nengo.dists.Choice([[1]]),
        #                    neuron_type=nengo.SpikingRectifiedLinear())
        # can_add_process = spa.networks.selection.WTA(calc_n_neurons,1 ,threshold=.5)
        # nengo.Connection(avail_procs,can_add_process,function=can_add)
        def can_add_thd_logic(x):
            x = np.round(x)

        can_add_en = spa.networks.selection.Thresholding(calc_n_neurons, 1, 1,
                                                         function=lambda x: np.clip(np.floor(x), 0, 1))
        nengo.Connection(avail_procs, can_add_en.input)

        output = nengo.Node(size_in=1)
        nengo.Connection(can_add_en.output, output)
    return add_logic


dimensions = 32

model = spa.Network(label="Scheduler Network")
from nengo.dists import Uniform
from nengo.processes import WhiteSignal
from nengo.utils.ensemble import tuning_curves

queue_nodes = QueueNode()
with model:
    # running_processes = waiting_processes
    print(running_process_size())
    num_cores_node = nengo.Node(num_cores)
    # running_size = nengo.Node(0)#output=running_process_size())
    running_procs_size_en = nengo.Ensemble(calc_n_neurons, 1, radius=num_cores)

    # this works
    # nengo.Connection(running_size, running_procs_size_en, function=running_process_size)
    # nengo.Connection(running_size, running_procs_size_en)
    num_cores_en = nengo.Ensemble(1024, 1, radius=num_cores)
    nengo.Connection(num_cores_node, num_cores_en)

    avail_procs = nengo.Ensemble(calc_n_neurons, 1, radius=num_cores)

    nengo.Connection(num_cores_en, avail_procs)
    # nengo.Connection(running_procs_size_en, avail_procs.neurons, transform=[[-1]]*calc_n_neurons)
    nengo.Connection(running_procs_size_en, avail_procs, transform=-1)


    # nengo.Connection(running_procs_size_en, avail_procs[1])
    # can_add_process = nengo.Ensemble(calc_n_neurons,dimensions=1,encoders=nengo.dists.Choice([[1]]),
    #                    neuron_type=nengo.SpikingRectifiedLinear())
    # can_add_process = spa.networks.selection.WTA(calc_n_neurons,1 ,threshold=.5)
    # nengo.Connection(avail_procs,can_add_process,function=can_add)
    def can_add_thd_logic(x):
        x = np.round(x)
        return x


    # can_add_en = spa.networks.selection.Thresholding(calc_n_neurons,1,1,function=lambda x: np.clip(np.floor(x),0,1))
    # nengo.Connection(avail_procs,can_add_en.input)

    # output = nengo.Node(size_in=1)
    # nengo.Connection(can_add_en.output, output)

    ## New Process Addition

    waiting_proc_q_top_size = nengo.Node(1)
    waiting_proc_size = nengo.Ensemble(calc_n_neurons, 1, radius=num_cores)


    def waiting_q_input_logic(x):
        if x <= 0:
            return num_cores * 2
        else:
            return x


    # nengo.Connection(waiting_proc_q_top_size,waiting_proc_size,function=waiting_q_input_logic)
    can_add_next_proc = nengo.Ensemble(calc_n_neurons, 1)

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
    qsim_waiting = nengo.Node(queue_nodes.output_message, size_out=3)
    qsim_add_spike = nengo.Node(queue_nodes.input_message, size_in=1, size_out=1)

    # v = nengo.Ensemble(32,3,radius = 128)
    # nengo.Connection(qsim_waiting, v)
    nengo.Connection(qsim_waiting[0], waiting_proc_size, function=waiting_q_input_logic)
    nengo.Connection(qsim_waiting[1], running_procs_size_en)

    ###WORKS GREAT!
    add_new_proc_system = nengo.Ensemble(calc_n_neurons, 1, radius=2, neuron_type=nengo.LIF(tau_rc=0.001))
    ##add_new_proc_system = nengo.Ensemble(calc_n_neurons,1,radius=2,neuron_type=nengo.Izhikevich())
    nengo.Connection(can_add_next_proc, add_new_proc_system, function=np.ceil)

    # nengo.Connection(running_size, running_procs_size_en)
    ## Filter for spikes:

    # nengo.Connection(add_new_proc_system,qsim_add_spike)
    # nengo.Connection(qsim_add_spike,add_new_proc_system.neurons,transform=[[-2]] * calc_n_neurons)

    # intr = nengo.networks.Integrator(n_neurons=calc_n_neurons,dimensions=1,recurrent_tau=0.1)
    # nengo.Connection(can_add_next_proc,intr.input)
    igm = nengo.networks.workingmemory.InputGatedMemory(calc_n_neurons, 1, difference_gain=.8)
    nengo.Connection(add_new_proc_system, qsim_add_spike)
    nengo.Connection(can_add_next_proc, igm.input)
    nengo.Connection(qsim_add_spike, igm.gate)
    # nengo.Connection(can_add_next_proc,igm.input,function=np.negative)
    # #nengo.Connection(qsim_add_spike,igm.gate)
    # nengo.Connection(add_new_proc_system,igm.gate,function=np.negative)
    # nengo.Connection(igm.output,qsim_add_spike)
    # #const_reset_val = nengo.Node(1)
    # nengo.Connection(const_reset_val,igm.reset)

    al = AddLogic()

