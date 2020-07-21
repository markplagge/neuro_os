# %%
import nengo_os
from nengo_os import  ConventScheduler, NemoNengoInterface


from nengo_os import SimpleProc, NemoNengoInterfaceBase

# @functools.total_ordering
# class CompareableRRProc(nengo_os.Process):
#
#     def __eq__(self, other):
#         if self.status !=
#         if self.status is other.status:
#             return True
#
from nengo_os.rr_full import SimpleProc


def nengo_sim_init(procs):
    iface = nengo_os.NemoNengoInterfaceBase(True, mode=1, rr_time_slice=50)
    for p in procs:
        iface.add_process(p.id, p.cores, p.compute, p.arrival)
    return iface


def nengo_sim_run(iface, end_time):
    iface.init_model()
    iface.generate_full_results(end_time)
    return iface


def interleave_procs():
    procs = [SimpleProc("TEST1", 0, 0, 0, 10, 50),
             SimpleProc("TEST2", 0, 2, 2, 10, 50),
             SimpleProc("TEST3", 0, 5, 5, 10, 50)]
    return procs


def interrupt_procs():
    return [SimpleProc("TEST1", 0, 0, 0, 10, 4000),
            SimpleProc("TEST2", 1, 2, 2, 10, 4000)]


def schedule(processes, mode="FCFS", total_cores=4096, time_slice=50, multiplexing=True):
    return ConventScheduler(processes, mode, total_cores, time_slice, multiplexing)


import pytest
import tqdm


def test_scheduler(pl=None):
    proc_list = interleave_procs() if pl is None else pl
    sch = schedule(proc_list, mode="RR")
    proc_0_run_times = []
    proc_1_run_times = []
    proc_1_pre_wait_times = []
    proc_1_wait_times = []
    assert (sch.current_time == 0)
    for i in range(1, 36):
        sch.scheduler_run_tick()
        assert (sch.current_time == i)
        proc_0_run_times.append(sch.queue.run_q[0].run_time)
        if len(sch.queue.run_q) >= 2:
            proc_1_run_times.append(sch.queue.run_q[1].run_time)
        if i < 2:
            assert (len(sch.queue.run_q) == 1)

        elif i < 5:
            assert (sch.queue.run_q[1].pre_wait_time == 2)
            assert (len(sch.queue.run_q) == 2)

        elif i == 50:
            for p in sch.queue.run_q:
                if p.current_state() != "DONE":
                    assert (p.current_state() == "DONE")

        if pl is None and len(sch.queue.run_q) > 0:
            test_time = 10
            assert (sch.queue.run_q[0].needed_time == test_time)

    return sch


"""
Paper Proc Test with 50 procs
Data schema:
Table of Processes (model_id, etc....)
Table of Process Events: (model_id, scheduler_time, event_type_id)
table of Event Types: 
event_id, name
"""

if __name__ == '__main__':
    test_scheduler()
    ips = test_scheduler(interrupt_procs())
    print(f"IPS RES: \n {ips}")
    proc_list = NemoNengoInterface.paper_procs()
    sch = schedule(NemoNengoInterface.paper_procs(), "RR")

    
