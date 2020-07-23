from VirtualProcess import Process
from VirtualProcess import Simulator
import nengo
from nengo.dists import Choice
from nengo.utils.ensemble import response_curves, tuning_curves
from nengo.solvers import LstsqL2
from nengo.dists import Uniform
from nengo.processes import WhiteSignal
from nengo.utils.ensemble import tuning_curves
import nengo_spa as spa
import numpy as np


import VirtualProcess
#####################################################
#
# RR Logic Training Functions
##################################################
class RoundRobinScheduler():

    def __init__(self,num_ns_cores = 4096):
        self.queue_nodes = VirtualProcess.NengoQueue(n_cores = num_ns_cores)
        self.running_process_size = self.queue_nodes.get_running_proc_core_usage
        self.num_cores = self.queue_nodes.n_cores
        self.calc_n_neurons = self.queue_nodes.calc_neurons
        self.time_slice_ticks = 10
        self.model = spa.Network(label="Scheduler Network")
        self.model_init()

    def add_process(self,process_id, process_needed_cores, process_scheduled_start_time, process_needed_time):
        if process_needed_time < 1:
            process_needed_time = 655350

        p = VirtualProcess.Process(n_cores = process_needed_cores,time_needed=process_needed_time,process_id=process_id,
                                   scheduled_start_time=process_scheduled_start_time)
        self.queue_nodes.add_wait_proc(p)
        print(f"Added process {p} to wait_queue")

    def model_init(self):
        model = nengo.Network(label='Neuron Scheduler')
        with model:
            # running_processes = waiting_processes
            print(self.running_process_size())
            num_cores_node = nengo.Node(self.num_cores)
            running_size = nengo.Node(output=self.running_process_size())  # output=running_process_size())
            running_procs_size_en = nengo.Ensemble(self.calc_n_neurons, 1, radius=self.num_cores)

            num_cores_en = nengo.Ensemble(1024, 1, radius=self.num_cores)
            nengo.Connection(num_cores_node, num_cores_en)

            avail_procs = nengo.Ensemble(self.calc_n_neurons, 1, radius=self.num_cores)

            nengo.Connection(num_cores_en, avail_procs)
            # nengo.Connection(running_procs_size_en, avail_procs.neurons, transform=[[-1]]*calc_n_neurons)
            nengo.Connection(running_procs_size_en, avail_procs, transform=-1)



            def can_add_thd_logic(x):
                x = np.round(x)
                return x



            ## New Process Addition

            waiting_proc_q_top_size = nengo.Node(1)
            waiting_proc_size = nengo.Ensemble(self.calc_n_neurons, 1, radius=self.num_cores)


            def waiting_q_input_logic(x):
                if x <= 0:
                    return self.num_cores * 2
                else:
                    return x


            # nengo.Connection(waiting_proc_q_top_size,waiting_proc_size,function=waiting_q_input_logic)
            can_add_next_proc = nengo.Ensemble(self.calc_n_neurons, 1)

            next_proc_size_check = nengo.Ensemble(self.calc_n_neurons, 1,
                                                  radius=self.num_cores, neuron_type=nengo.neurons.SpikingRectifiedLinear())
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
            qsim_waiting = nengo.Node(self.queue_nodes.output_message, size_out=3)
            qsim_add_spike = nengo.Node(self.queue_nodes.input_message, size_in=1, size_out=1)

            v = nengo.Ensemble(32, 3, radius=128)
            nengo.Connection(qsim_waiting, v)
            nengo.Connection(qsim_waiting[0], waiting_proc_size, function=waiting_q_input_logic)
            # nengo.Connection(qsim_waiting[1] , running_procs_size_en)

            add_new_proc_system = nengo.Ensemble(self.calc_n_neurons, 1, radius=2, neuron_type=nengo.Izhikevich(reset_recovery=0))
            nengo.Connection(can_add_next_proc, add_new_proc_system, function=np.ceil)

            nengo.Connection(running_size, running_procs_size_en)
            ## Filter for spikes:

            nengo.Connection(add_new_proc_system, qsim_add_spike)
            #  deepcode ignore MultiplyList: Pointing to the list is okay here since neurons are read-only
            nengo.Connection(qsim_add_spike, add_new_proc_system.neurons, transform=[[-1]] * self.calc_n_neurons)

            ## RR Clock
            clock_input = nengo.Node(size_out=1)
            check_proc_ens = nengo.Ensemble(self.calc_n_neurons, dimensions=2)

            rr_clock = nengo.Network()
            with rr_clock:
                def node_tick_clock(t):
                    t = np.round(t) % 10
                    return t


                def neuron_timer_check(x):

                    nv = x[0]
                    if x[0] > 10:
                        nv = 0
                    else:
                        nv = x[0]
                    return nv


                stim = nengo.Node(1)
                inhibition = nengo.Node(0)
                interupt_proc = nengo.Ensemble(n_neurons=1024, dimensions=1)
                c = nengo.Ensemble(n_neurons=1024, dimensions=1)
                nengo.Connection(stim, interupt_proc)
                # deepcode ignore MultiplyList: Read-Only list, only used to modify the nengo connection
                nengo.Connection(c, interupt_proc.neurons, transform=[[-2.5]] * 1024)
                nengo.Connection(inhibition, c)
                clock = nengo.Node(node_tick_clock)
                time_slice = nengo.Node(10)

                cl_enc = nengo.Ensemble(1024, dimensions=1, radius=25)
                ts_enc = nengo.Ensemble(1024, dimensions=1, radius=25)
                nengo.Connection(time_slice, ts_enc, function=lambda x: x % self.time_slice_ticks)
                nengo.Connection(clock, cl_enc)
                time_check = nengo.Ensemble(1024, dimensions=1, radius=20)
                # summation = nengo.networks.
                tau = 0.1
                nengo.Connection(cl_enc, time_check, synapse=tau, function=neuron_timer_check)

                nengo.Connection(time_check, c)

            qsim_running_interrupt = nengo.Node(size_in=1, size_out=0)
            nengo.Connection(interupt_proc, qsim_running_interrupt)

        self.model = model
        self.sim = nengo.Simulator(model)

    def run_model(self,n_steps = 1):
        #self.sim.run_steps(n_steps)
        self.sim.run(n_steps)

    def get_running_models(self):
        return self.get_running_models()

rr = RoundRobinScheduler()
rr.add_process(1,4096,0,100)
rr.add_process(2,4096,1,100)
rr.run_model(10)
