from .rr_full import QueueNodeEnh
from .neuro_os_interface import NemoNengoInterface

try:
    from numba import jit
except:
    print("NUMBA not found not using JIT")

    def jit(func):
        def wrapper_do_twice(*args, **kwargs):
            func(*args, **kwargs)

        return wrapper_do_twice


class ConventScheduler:
    def __init__(self, simple_proc_list=None, mode="FCFS", total_cores=4096, time_slice=50, multiplexing=True,
                 proc_js_file=None):
        self.multiplexing = multiplexing
        if mode == "FCFS":
            time_slice = -1
        if simple_proc_list is None:
            iface = NemoNengoInterface(True)
            if proc_js_file is None:
                print("Using paper task list")
                big_p_list = iface.process_list
            else:
                print(f"Loading procs from file: {proc_js_file}")
                big_p_list = iface.paper_procs()
        else:
            mm = "\n".join([str(pl) for pl in simple_proc_list])
            print(f"Using given proc list: {mm}`")
            big_p_list = [p.proc for p in simple_proc_list]

        self.queue = QueueNodeEnh(wait_q_ovr=big_p_list, time_slice=time_slice)

        self.total_cores = total_cores
        self.current_time = 0
        self.time_slice = time_slice

    @property
    def waiting_procs(self):
        waiting_procs = []
        next_waiting_proc_size = -1
        for proc in self.queue.wait_q:
            if proc.current_state() == "WAITING":
                if next_waiting_proc_size == -1:
                    next_waiting_proc_size = proc.needed_cores
            waiting_procs.append(proc.model_id)
        return next_waiting_proc_size, waiting_procs

    @property
    def running_procs(self):
        running_procs = []
        running_proc_size = 0
        for proc in self.queue.run_q:
            if proc.current_state() == "RUNNING":
                running_procs.append(proc.model_id)
                running_proc_size += proc.needed_cores
        return running_proc_size, running_procs

    @property
    def running_proc_size(self):
        return self.running_procs[0]

    @property
    def running_proc_list(self):
        return self.running_procs[1]

    @property
    def waiting_proc_size(self):
        return self.waiting_procs[0]

    @property
    def waiting_proc_list(self):
        return self.waiting_procs[1]

    @property
    def available_cores(self):
        return self.total_cores - self.running_proc_size

    @property
    def is_process_waiting(self):
        return self.waiting_proc_size > 0

    @property
    def is_done(self):
        done = all(p.current_state == "DONE" for p in self.queue.wait_q)
        for p in self.queue.run_q:
            if p.current_state != "DONE":
                done = False

        return done

    def can_add_next_proc(self):
        if self.is_process_waiting:
            if self.multiplexing:
                wps = self.waiting_proc_size
                if wps <= self.available_cores and self.waiting_proc_size > 0:
                    return True
            elif self.running_proc_size == 0:
                return True
        return False

    def start_next_proc(self):
        for p in self.queue.wait_q:
            if p.status == "WAITING":
                p.start()
                return True
        return False

    def interrupt_running_proc(self, model_id):
        stopped_procs = []
        for p in self.queue.run_q:
            if p.model_id == model_id:
                p.interrupt()
                stopped_procs.append(p)

        for p in stopped_procs:
            self.queue.run_q.remove(p)
            self.queue.wait_q.append(p)

    def interrupt_all_available_procs(self):
        if self.current_time % self.time_slice == 0 and self.current_time > 0:
            self.queue.input_interrupt(self.current_time, [500, 500])

    def scheduler_run_tick(self):
        self.current_time += 1
        self.queue.process_update(self.current_time)
        if self.can_add_next_proc():
            self.queue.start_next_proc(self.current_time)

        self.interrupt_all_available_procs()
        return self.current_time

    def __str__(self):
        rp = "\n".join([str(p) for p in self.queue.run_q])
        wp = "\n".join([str(p) for p in self.queue.wait_q])
        return f"CT: {self.current_time} - Proc list\n-----RUN:-----\n{rp}\n----WAIT---\n{wp}"