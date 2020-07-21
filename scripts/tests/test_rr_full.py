import pytest

from nengo_os import SimpleProc, ConventScheduler



procs = [  # name   id arrival1,+2,  comp_t, needed_cores
        SimpleProc("Cifar", 0, 0, 0,   10, 4038),  # test single process
        SimpleProc("SAR", 1, 0, 0, 100, 3038), #test two procs that can not run together
        SimpleProc("SAR", 2, 0, 0, 100, 3038)
    ]

@pytest.fixture(params=["SINGLE","TWO_INT","ALL"])
def paper_procs(request):
    pl = procs
    if request.param == "SINGLE":
        return [pl[0]], 1
    if request.param == "TWO_INT":
        return [pl[1],pl[2]], 2
    if request.param == "ALL":
        pl[1].arrival = 10
        pl[2].arrival = 10
        return pl, len(pl)

@pytest.fixture
def create_non_nengo_scheduler(paper_procs):
    pl, num = paper_procs
    return ConventScheduler(simple_proc_list = pl, mode="RR",time_slice=5), num

class RR_Status:

    def __init__(self, time=0):
        self.time = time




def test_non_nengo_rr(create_non_nengo_scheduler):
    sched,num = create_non_nengo_scheduler
    end_time_est = sum(et.needed_time for et in sched.queue.wait_q)
    quant = sched.time_slice
    running_proc = 2
    waiting_proc = 1
    rtx = []
    for i in range(end_time_est):
        sched.scheduler_run_tick()
        if num == 1:
            if i == 0:
                assert(sched.running_proc_size == 4038)
        elif num == 2:


            if i == 10:
                print(i)
                assert(sched.running_proc_size == 3038)

            if i % sched.time_slice == 0:

                    #assert(sched.running_proc_list[0] == running_proc)
                    r = waiting_proc
                    running_proc = waiting_proc
                    waiting_proc = r
                    rtx.append(sched.running_proc_list[0])

            elif i > 200:
                assert(sched.waiting_proc_size < 1)
    print(rtx)

def test_load_json():
    from pathlib import Path
    model_data_file = Path("/Users/plaggm/dev/nemo-codes/config/paper_models.json")
    sched_type = "RR"
    rr_ts = 100
    scheduler = ConventScheduler(mode=sched_type, total_cores=4096, time_slice=rr_ts,
                                 proc_js_file=str(model_data_file.absolute()))

