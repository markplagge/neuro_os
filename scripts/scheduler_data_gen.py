from operator import itemgetter
## RUN 1:
import tqdm.notebook
import json
# %%
import nengo_os
from nengo_os import ConventScheduler
# @functools.total_ordering
# class CompareableRRProc(nengo_os.Process):
#
#     def __eq__(self, other):
#         if self.status !=
#         if self.status is other.status:
#             return True
#
from nengo_os.rr_full import SimpleProc



class ProcSQL:
    job_cols = ["model_id", "arrival_time", "requested_run_time"]
    job_stat_cols = ["job_id", "run_id", "pre_wait_time", "current_wait_time", "actual_start_time", "current_run_time",
                     "current_scheduler_time"]

    # (job_id, run_id, pre_wait_time, current_wait_time, actual_start_time, current_run_time,current_scheduler_time)
    # VALUES (null, null, null, null, null, null, null);

    def __insert_job(self):
        query = f"INSERT INTO jobs (model_id, arrival_time, requested_run_time, task_id) values (?,?,?,?);"
        self.cur.execute(query, self.job_info)
        self.job_id = self.cur.lastrowid
        q1 = "INSERT INTO run_job_list (job_id, run_id) VALUES (?,?);"
        self.cur.execute(q1, (self.job_id, self.runid))

    def job_stats(self, p=None):
        if p is None:
            p = self.p
        values = [self.job_id, self.runid, p.pre_wait_time, p.wait_time, p.process_began_run, p.run_time, p.tick_time, p.current_state()]
        query = f"INSERT INTO run_job_stats (job_id, run_id, pre_wait_time, current_wait_time, actual_start_time, current_run_time,current_scheduler_time,current_state)" \
                f"values (?,?,?,?,?,?,?,?);"
        self.cur.execute(query, values)

    def __init__(self, p, db_cur, task_id=0, rid=0):
        p.tick_callback = self.job_stats

        self.job_info = [p.model_id, p.start_time, p.needed_time, task_id]
        self.p = p
        self.task_id = task_id
        self.runid = rid
        self.cur = db_cur
        self.__insert_job()


def generate_proc_sql(run_id, scheduler, cur):
    job_data = []
    i = 1
    for p in scheduler.queue.wait_q:
        job_stats_sql = ProcSQL(p, cur, i, run_id)
        i += 1
        job_stats_sql.job_stats()
        job_data.append(job_stats_sql)
        #p.job_id = job_stats_sql.job_id
        p.set_job_id(job_stats_sql.job_id)
    return job_data


### JOB EVENT GENERATION ###
class EventTracker:

    def state_change(self, old_state, state, cb_state=None):

        stx = old_state + state
        if stx not in self.change_lookup.keys():
            print(f"{self.initial_state_list}")
        return self.id_from_typemap[self.change_lookup[stx]]

    def no_chg(self, v):
        nc_tv = self.no_chg_typemap[v]
        sql_tp = self.id_from_typemap[nc_tv]
        return sql_tp

    def __init__(self, scheduler, run_id, cursor):
        self.run_id = run_id
        self.cur = cursor

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

        sql_typemap = {15: interrupted, 12: pre_waiting, 16: proc_complete, 10: running, 14: start_running,
                       13: start_waiting, 11: waiting}
        self.id_from_typemap = {v: k for k, v in sql_typemap.items()}
        no_chg_typemap = {"DONE": done, "WAITING": waiting, "RUNNING": running, "PRE_WAIT": pre_waiting}
        change_lookup = {
            # old, new, type
            "PRE_WAIT" "WAITING": "start_waiting",
            "PRE_WAIT" "RUNNING": "start_running",
            "WAITING"  "RUNNING": "start_running",
            "RUNNING"  "WAITING": "interrupted",
            "RUNNING"  "DONE": "proc_complete"
        }
        self.sql_typemap = sql_typemap
        self.no_chg_typemap = no_chg_typemap
        self.change_lookup = change_lookup

    def proc_callback(self, old_state, new_state, proc_state):
        job_id = proc_state.job_id
        job_event_id = self.state_change(old_state, new_state)
        query = "INSERT INTO run_job_events (event_type, run, job, sched_event_time) " \
                "values (?,?,?,?)"
        self.cur.execute(query, (job_event_id, self.run_id, job_id, proc_state.tick_time))

    def update(self, scheduler):
        new_procs = [proc for proc in scheduler.queue.wait_q] + [proc for proc in scheduler.queue.run_q]
        new_states = {proc.job_id: proc.current_state() for proc in new_procs}
        event_time = scheduler.current_time
        event_updates = []
        for job_id, state in new_states.items():
            old_state = self.initial_state_list[job_id]
            if old_state != state:
                job_event_id = self.state_change(old_state, state)
                query = "INSERT INTO run_job_events (event_type, run, job, sched_event_time) " \
                        "values (?,?,?,?)"
                self.cur.execute(query, (job_event_id, self.run_id, job_id, event_time))
        self.initial_state_list = new_states
        # else:
        #
        #     job_event_id = self.no_chg(state)


import sqlite3
from pathlib import Path
import shutil

result_path = Path("./results")
template_db = result_path / "run_result_template.sqlite"
result_db = result_path / "run_result.sqlite"
backup_tp = "./run_result_backup-*-.sqlite"

INIT_TEMPLATE = True

if not result_db.exists():
    shutil.copy(template_db, result_db)
else:
    num_bkps = 0
    backup_list = []
    for f in result_path.glob(backup_tp):
        bpl = str(f.absolute().name).split("-")
        bpl[1] = int(bpl[1])
        backup_list.append(bpl)
        # run_result_backup,*,.sqlite
    if len(backup_list) > 0:
        backup_list = sorted(backup_list, key=itemgetter(1))
        num_bkps = max(map(lambda x: int(x[1]), backup_list))
        num_bkps += 1

    new_backup_name = backup_tp.replace("*", str(num_bkps))
    new_path = result_path / new_backup_name
    shutil.move(result_db, new_path)
    shutil.copy(new_path, result_db)


def init_run_in_sql(sched_type="RR", ts=100, nemo_stats=""):
    query = "INSERT INTO runs (sched_type, rr_time_slice, nemo_stats) VALUES (?, ?, ?);"
    cur.execute(query, (sched_type, ts, nemo_stats))
    id = cur.lastrowid
    conn.commit()
    return id





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


def save_scheduler_instructions(sched, run_procs, wait_procs):
    rp = []
    wp = []
    for p in sched.queue.run_q:
        if p.current_state() == "RUNNING":
            rp.append(p.job_id)
    for p in sched.queue.wait_q:
        wp.append(p.job_id)
    rrb = run_procs
    wwb = wait_procs
    rrb.append(rp)
    wwb.append(wp)
    return (rrb, wwb)





conn = sqlite3.connect(result_db)
cur = conn.cursor()

# load run data
model_data_file = Path("/Users/plaggm/dev/nemo-codes/config/paper_models.json")
sched_type = "RR"
rr_ts = 100
#rr_ts = 4455
scheduler = ConventScheduler(mode=sched_type, total_cores=4096, time_slice=rr_ts,
                             proc_js_file= str(model_data_file.absolute()))
# scheduler = ConventScheduler(mode=sched_type, total_cores=4096, time_slice=rr_ts)
#                             proc_js_file= str(model_data_file.absolute()))
run_id = init_run_in_sql(sched_type, rr_ts, "")
p = scheduler.queue.wait_q[0]
## Start of system, create awesome stat objects
job_data = generate_proc_sql(run_id, scheduler, cur)
conn.commit()
evt_tracker = EventTracker(scheduler, run_id, cur)
evt_tracker.update(scheduler)
conn.commit()
sttl = sum(pv.needed_time for pv in scheduler.queue.wait_q)
t = []
wp = []
rp = []
inst = Instruct()
for i in tqdm.tqdm(range(sttl * 10)):

    test = True
    tv = 0
    for p in scheduler.queue.run_q:
        tv += 1
        test = test and (p.current_state == "DONE")
    if (test and tv > 1) :
        break


    rp, wp = save_scheduler_instructions(scheduler, rp, wp)
    t.append(i)
    scheduler.scheduler_run_tick()
    if len(scheduler.queue.run_q) > 1:
        print("RUN QUEUE WAS BIGGER")

    #evt_tracker.update(scheduler)
    inst.add_instruction(i,scheduler.queue.wait_q, scheduler.queue.run_q)
    for jd in job_data:
         jd.job_stats()
conn.commit()

jdt = inst.to_json()

conn.commit()
with open("scheduler_instructions.json","w") as f:
    f.write(jdt)
