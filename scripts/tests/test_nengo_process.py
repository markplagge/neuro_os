import nengo_os
import pytest

"""basic fixture"""
@pytest.fixture
def interuptable_proc():
    pass

"""fixture factory"""
@pytest.fixture
def make_customer_record():
    def _make_customer_record(name):
        return {"name": name, "orders": []}

    return _make_customer_record


# """Paramater pytest"""
# @pytest.fixture(scope="module", params=["smtp.gmail.com", "mail.python.org"])
# def smtp_connection(request):
#     smtp_connection = smtplib.SMTP(request.param, 587, timeout=5)
#     yield smtp_connection
#     print("finalizing {}".format(smtp_connection))
#     smtp_connection.close()

"""Custom strings"""
#@pytest.fixture(params=[0, 1], ids=["spam", "ham"])
"""Create proc factory"""
@pytest.fixture
def make_process():
    def _make_process(start_time, needed_cores, needed_time):
        return nengo_os.RRProcessStatus(n_cores = needed_cores, time_needed=needed_time, start_time=start_time)
    return _make_process




"""Create procs for interrupt"""
@pytest.fixture
def make_single_int_proc(make_process):
    start_time = 0
    needed_cores = 1000
    needed_time = 10
    return make_process(start_time, needed_cores,needed_time)


@pytest.fixture(params=[2,4,8], ids=['2 procs','4 procs','8 procs'])
def make_multi_int_large_procs(request,make_process):
    return [
        make_process(
            start_time=0, needed_cores=4000, needed_time=10 * request.param
        )
        for _ in range(request.param)
    ]

def test_single_proc_set_states(make_single_int_proc):
    p = make_single_int_proc
    assert(p.current_state() == "WAITING")
    p.tick()
    assert (p.current_state() == "WAITING")
    p.set_current_state("RUNNING")
    assert (p.current_state() == "RUNNING")


def test_single_proc_interrupt(make_single_int_proc):
    p = make_single_int_proc
    p.set_current_state("RUNNING")
    p.tick()
    if(p.current_state() != "RUNNING"):
        pytest.fail(f"Not running after running set at time 0: {str(p)}")
    if p.run_time != 1:
        pytest.fail(f"Process time issues: {str(p)}")
    assert(p.run_time == 1)
    p.tick()
    assert(p.run_time == 2)
    p.interrupt()
    assert(p.current_state() == "WAITING")
    p.tick()
    assert(p.run_time == 2)
    assert(p.wait_time == 1)
    p.tick()
    assert(p.wait_time == 2)
    p.start()
    assert(p.current_state() == "RUNNING")



def test_multi_single_proc_interrupt(make_multi_int_large_procs):
    proc_list = make_multi_int_large_procs
    num_procss = len(proc_list)
    total_time = sum(p.needed_time for p in proc_list)
    for i in range(total_time):
        for p in proc_list:
            p.set_current_state("RUNNING")
            p.tick()
            if p.needed_time <= p.run_time:
                assert(p.current_state() == "DONE")

    for p in proc_list:
        assert(p.current_state() == "DONE")

######## pytest.fail("MESSAGE!")
# def checkconfig(x):
#     __tracebackhide__ = True
#     if not hasattr(x, "config"):
#         pytest.fail("not configured: {}".format(x))

