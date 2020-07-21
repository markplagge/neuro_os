import numpy as np
from .ProcStates import *

class VirtualQueue:
    _queue = []
    _states = []
    def __init__(self,id = 0):
        self._queue = []
        self._states = []

    @property
    def queue(self):
        if len(self._queue) > 0:
            return self._queue
        else:
            return -1

    @queue.setter
    def queue(self, value):
        self._queue = value

    def push(self,p):
        self._queue.append(p)


    def pop(self):
        if self.queue == -1:
            return -1

        return self.queue.pop(0)


    def get_top_proc_size(self):
        if self.get_top_proc() == -1:
            return self.get_top_proc()
        return self.get_top_proc().n_cores

    def get_top_proc(self):
        if self.queue != -1:
            return self.queue[0]
        else:
            return -1

    def iter_queue(self):
        yield from self._queue

    def tick(self):
        for p in self.iter_queue():
            p.tick()

class ProcessQueues():
    wait_q = VirtualQueue(0)
    run_q = VirtualQueue(1)

    def __init__(self):

        self.last_active = 0
        self.added_element = 0
        self.output_last_active = 0


    def start_next_proc(self, t):
        next_proc = self.wait_q.pop()
        next_proc.start_proc()
        self.run_q.push(next_proc)

    def start_proc(self, t, x):
        start_proc_ok = -1
        start_proc_size = -1
        if self.wait_q.get_top_proc_size() > -1:
            self.start_next_proc(t)
            start_proc_ok = 1
            start_proc_size = self.run_q.get_top_proc_size()
        start_proc_message = [start_proc_ok, start_proc_size]
        x[0] = start_proc_ok
        x[1] = start_proc_size
        return x

    def process_update(self, t):
        epoc_diff = self.epoch_check(t)
        if epoc_diff > 0:
            for i in range(0, epoc_diff):
                self.wait_q.tick()
                self.run_q.tick()

    def get_running_proc_core_usage(self):
        running_proc_cores = 0
        for i in range(0, len(self.run_q._queue)):
            if self.run_q.queue[i].state == PROC_STATE.RUNNING:
                running_proc_cores += self.run_q.queue[i].needed_cores
        return running_proc_cores

    def epoch_check(self, t):
        epoc_diff = t - self.last_active
        epoc_diff = int(np.floor(epoc_diff))
        return epoc_diff

    def output_message(self, t):

        epoc_diff = self.epoch_check(t)

        if epoc_diff > 0:
            wait_time_r = -1
            if self.wait_q != -1:
                wait_time_r = self.wait_q.get_top_proc().wait_time

            print(f"epoc_diff:{epoc_diff} | last_active: {self.last_active}|"
                  f"top_size:{self.wait_q.get_top_proc_size}"
                  f" | waiting_q_size: {len(self.wait_q.queue)}"
                  f" | wait_time: {wait_time_r}")
            self.process_update(t)
            self.last_active = np.floor(t)

        top_proc_size = self.wait_q.get_top_proc_size()
        running_proc_cores = self.get_running_proc_core_usage()
        return [top_proc_size, running_proc_cores, self.last_active]

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
                if self.run_q.queue != -1:
                    ttr = self.run_q.queue[0].needed_time
                    pstate = self.run_q.queue[0].current_state
                print(f"PMAN: {self.output_last_active} |"
                      f"RUNSZ:{self.get_running_proc_core_usage()}"
                      f"TTR:{ttr} | STATE:{pstate}")
                # self.added_element = 0
        return output_message[0]