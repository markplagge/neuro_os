import json
from pathlib import Path
from collections import defaultdict

import tqdm

from nengo_os import ConventScheduler

def convert_event_type_str(event_type):
    change_lookup = {
        # old, new, type
        "start_waiting":0,
        "start_running":1,
        "interrupted":2,
        "proc_complete":3
    }
    return change_lookup[event_type]


class Event:
    def __init__(self, task_id, model_id, event_type, time):
        self.model_id = model_id
        self.task_id = task_id
        self.event_type = event_type
        self.time = time

    def get_event_from_c(self):
        return {'model_id':self.model_id, 'task_id':self.task_id, 'evt_type':self.event_type,'time':self.time}

    def get_event_from_c_int(self):
        v = self.get_event_from_c()
        v['evt_type'] = convert_event_type_str(v['evt_type'])
        return v


    def __eq__(self, other):
        if isinstance(other, Event):
            return self.model_id == other.model_id and self.task_id == other.task_id and self.event_type == other.event_type and self.time == other.time
        else:
            return False


class Instruct:
    def __init__(self):
        self.ts = []
        self.waits = []
        self.runs = []

    def add_instruction(self, t, wait, run):
        self.ts.append(t)
        self.waits.append(wait)
        self.runs.append(run)

    def fixer(self, ls):
        wl = []
        for w in ls:
            if isinstance(w,int):
                wl.append(w)
            else:
                wl.append(w.to_dict())
        return wl


    def to_json(self):
        def entry(t, ws, rs):
            wlist = self.fixer(ws)
            rlist = self.fixer(rs)

            itm = {"time": t, "waits": [w for w in wlist], "runs":[r for r in rlist]}
            return itm

        entries = []
        for i in range(len(self.ts)):
            t = self.ts[i]
            w = self.waits[i]
            r = self.runs[i]
            entries.append(entry(t, w, r))
        return json.dumps(entries)

def sql_typemap_fn():
    done = "done"
    interrupted = "interrupted"
    pre_waiting = "pre_waiting"
    proc_complete = "proc_complete"
    running = "running"
    start_running = "start_running"
    start_waiting = "start_waiting"
    waiting = "waiting"
    return {15: interrupted, 12: pre_waiting, 16: proc_complete, 10: running, 14: start_running,
                       13: start_waiting, 11: waiting, 17: done}

class EventTracker:
    def __init__(self, scheduler, run_id):
        self.run_id = run_id


        self.proc_list = [proc for proc in scheduler.queue.wait_q]
        self.initial_state_list = {proc.job_id: proc.current_state() for proc in self.proc_list}
        self.updated_state_list = [s for s in self.initial_state_list]
        for proc in scheduler.queue.wait_q:
            proc.state_callback = self.proc_callback

        done = "done"
        interrupted = "interrupted"
        pre_waiting = "pre_waiting"
        proc_complete = "proc_complete"
        running = "running"
        start_running = "start_running"
        start_waiting = "start_waiting"
        waiting = "waiting"
        sql_typemap = sql_typemap_fn()

        self.sql_typemap = sql_typemap

        self.id_from_typemap = {v: k for k, v in sql_typemap.items()}
        no_chg_typemap = {"DONE": done, "WAITING": waiting, "RUNNING": running, "PRE_WAIT": pre_waiting}
        change_lookup = {
            # old, new, type
            "PRE_WAIT" "WAITING": "start_waiting",
            "PRE_WAIT" "RUNNING": "start_running",
            "WAITING"  "RUNNING": "start_running",
            "WAITING"  "PRE_WAIT": "waiting",
            "WAITING" "WAITING" : "waiting",
            "RUNNING" "RUNNING" : "running",
            "RUNNING"  "WAITING": "interrupted",
            "RUNNING"  "DONE": "proc_complete"
        }
        self.sql_typemap = sql_typemap
        self.no_chg_typemap = no_chg_typemap
        self.change_lookup = change_lookup

        self.event_list = []
        self.event_lookup = defaultdict(list)

    def add_event(self, job_id, model_id, job_event_id,time):
        event = Event(job_id, model_id, job_event_id,time)
        ## Check for dups:
        #if event not in self.event_list:
        self.event_list.append(event)
        #if event not in self.event_lookup[time]:
        self.event_lookup[time].append(event)

    def proc_callback(self, old_state, new_state, proc_state):
        job_id = proc_state.task_id
        model_id = proc_state.model_id
        event_time = proc_state.tick_time
        job_event_id = self.state_change(old_state, new_state)
        self.add_event(job_id, model_id, job_event_id,event_time)

    def update(self, scheduler):
        new_procs = [proc for proc in scheduler.queue.wait_q] + [proc for proc in scheduler.queue.run_q]
        new_states = {proc.task_id: proc.current_state() for proc in new_procs}
        proc_dict =  {proc.task_id: proc for proc in new_procs}
        event_time = scheduler.current_time
        event_updates = []
        for job_id, state in new_states.items():
            old_state = self.initial_state_list[job_id]
            if old_state != state:
                job_event_id = self.state_change(old_state, state)
            else:
                job_event_id = self.no_chg(state)
            self.add_event(job_id,proc_dict[job_id].model_id, job_event_id,proc_dict[job_id].tick_time)
        self.initial_state_list = new_states
        # else:
        #
        #     job_event_id = self.no_chg(state)

    def state_change(self, old_state, state, cb_state=None):
        stx = old_state + state
        if stx not in self.change_lookup.keys():
            print(f"{self.initial_state_list}")
        return self.change_lookup[stx]
        #return self.id_from_typemap[self.change_lookup[stx]]

    def no_chg(self, v):
        nc_tv = self.no_chg_typemap[v]
        sql_tp = self.id_from_typemap[nc_tv]
        return sql_tp






def sched_mode_int_to_str(sched_mode_int):
    if sched_mode_int == 0:
        return "FCFS"
    if sched_mode_int == 1:
        return "RR"
    if sched_mode_int == 2:
        return "FS"


def save_scheduler_instructions(sched, run_procs, wait_procs):
    rp = []
    wp = []
    for p in sched.queue.run_q:
        if p.current_state() == "RUNNING":
            rp.append(p.task_id)
    for p in sched.queue.wait_q:
        wp.append(p.task_id)
    rrb = run_procs
    wwb = wait_procs
    rrb.append(rp)
    wwb.append(wp)
    return (rrb, wwb)




def compute_nos_conventional(mode="FCFS", total_cores=4096, time_slice=50, multiplexing=True,
                 proc_js_file=None, end_ts = 10000,do_tq = False):
    if isinstance(mode, int):
        mode = sched_mode_int_to_str(mode)
    print("System Scheduler Starting....")
    t = []
    wp = []
    rp = []
    model_data_file = Path(proc_js_file)
    if( not model_data_file.exists() ) :
        print(f'{"-" * 10} std sched error - model data file {proc_js_file} does not exist! EXIT')
        return

    scheduler = ConventScheduler(mode=mode, total_cores=total_cores, time_slice=time_slice, multiplexing=multiplexing,proc_js_file=str(model_data_file))

    event_tracker = EventTracker(scheduler,0)
    print(f"{'-|-'*10} INTERNAL SCHEDULER - RUNNING FOR {end_ts} ticks")
    for i in tqdm.tqdm(range(end_ts)):
        ts = [p.current_state == "DONE" for p in scheduler.queue.run_q]
        if (ts and all(ts) ): # or scheduler.is_done:
            break
        rp, wp = save_scheduler_instructions(scheduler, rp, wp)
        t.append(i)
        scheduler.scheduler_run_tick()
        event_tracker.update(scheduler)

    return event_tracker, t, wp, rp



def compute_nos_conventional_event_dict(mode="FCFS", total_cores=4096, time_slice=50, multiplexing=True,
                 proc_js_file=None, end_ts = 10000):

    event_tracker,t,wp,rp = compute_nos_conventional(mode,total_cores,time_slice,multiplexing,proc_js_file,end_ts)
    event_map = event_tracker.event_lookup
    event_dict = {k:v for k,v in event_map.items()}
    return event_dict

def compute_nos_conventional_event_list(mode="FCFS", total_cores=4096, time_slice=50, multiplexing=True,
                                        proc_js_file=None, end_ts = 10000):
    event_tracker, t, wp, rp = compute_nos_conventional(mode, total_cores, time_slice, multiplexing, proc_js_file,
                                                        end_ts)

    event_list = event_tracker.event_list
    print(f"Evt list: {event_list}")
    return event_list

