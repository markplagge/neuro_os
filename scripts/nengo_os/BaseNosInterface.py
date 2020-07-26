import json
from collections import defaultdict
from enum import IntFlag

from nengo_os import compute_nos_conventional
from nengo_os.NonNengoNemoInterface import sql_typemap_fn, Event, EventTracker


class SchedFlag(IntFlag):
    SC_MD_NENGO = 1 << 0
    SC_MD_CONVENT = 1 << 1
    SC_MD_CACHED = 1 << 2
    SC_MD_RR = 1 << 3
    SC_MD_FCFS = 1 << 4
    SC_MD_USE_NENGO_DL = 1 << 5


def make_sys_event(event):
    return SystemEvent(
        event.model_id, event.task_id, event.event_type, event.time
    )


class SystemEvent(Event):
    def __init__(self, model_id, task_id, event_type, event_time):
        super().__init__(model_id, task_id, event_type, event_time)
        self.model_id = model_id
        self.task_id = task_id
        self.event_type = event_type
        self.event_time = event_time
        self.id_from_typemap = {v: k for k, v in sql_typemap_fn().items()}
        self.type_from_id = sql_typemap_fn()
        self.do_run_events = ["start_running"]
        self.do_stop_events = ["start_waiting", "interrupted", "proc_complete"]
        self.run_events = ["running"]
        self.stop_events = ["done", "pre_waiting", "waiting"]
        if isinstance(event_type, str):

            self.event_type = self.id_from_typemap[event_type]

    def is_event(self, type_list):
        return self.type_from_id[self.event_type] in type_list

    def is_start_event(self):
        return self.is_event(self.do_run_events)

    def is_stop_event(self):
        return self.is_event(self.do_stop_events)

    def is_running(self):
        return self.is_event(self.run_events)

    def is_stopped(self):
        return self.is_event(self.stop_events)

    def get_dict(self):
        return self.__dict__


def generate_timed_events(evt_tracker):
    timed_events = defaultdict(list)
    start_events = defaultdict(list)
    stop_events = defaultdict(list)
    running_events = defaultdict(list)
    waiting_events = defaultdict(list)

    for time, event_list in evt_tracker.event_lookup.items():
        start_event_count = 0
        stop_event_count = 0
        for ev_1 in event_list:
            event = make_sys_event(ev_1)
            timed_events[time].append(event)
            if event.is_start_event():
                start_events[time].append(event)
                start_event_count += 1
            elif event.is_stop_event():
                stop_events[time].append(event)
                stop_event_count += 1
            elif event.is_running():
                running_events[time].append(event)
            elif event.is_stopped():
                waiting_events[time].append(event)
    return timed_events, start_events, stop_events, running_events, waiting_events


def timed_events_to_dict(timed_events, start_events, stop_events, running_events, waiting_events):
    event_holder = {}
    for i in range(max(list(timed_events.keys()))):
        evt_sx = {"start_events": start_events[i], "stop_events": stop_events[i], "waiting": waiting_events[i],
                  "running": running_events[i]}
        event_holder[i] = evt_sx
    return event_holder


def timed_events_to_yaml(timed_events, start_events, stop_events, running_events, waiting_events):
    event_holder = timed_events(timed_events, start_events, stop_events, running_events, waiting_events)
    import yaml
    return yaml.dump(event_holder)


def timed_events_to_json(timed_events, start_events, stop_events, running_events, waiting_events):
    event_holder = timed_events(timed_events, start_events, stop_events, running_events, waiting_events)
    return json.dumps(event_holder)


def sys_evt_check(lis, e_type):
    for i in lis:
        ev = SystemEvent(i, i, i, i)
        start_ch = False
        stp_ch = False
        run_ch = False
        stopped_ch = False
        if e_type == "do_start":
            start_ch = True
        elif e_type == "do_stop":
            stp_ch = True
        elif e_type == "run":
            run_ch = True
        elif e_type == "stop":
            stopped_ch = True

        assert (ev.is_start_event() == start_ch)
        assert (ev.is_stop_event() == stp_ch)
        assert (ev.is_running() == run_ch)
        assert (ev.is_stopped() == stopped_ch)


def test_system_events():
    start_ids = [14]
    stop_ids = [15, 13, 16]
    running_ids = [10]
    stopped_ids = [11, 12, 17]
    sys_evt_check(start_ids, "do_start")
    sys_evt_check(stop_ids, "do_stop")
    sys_evt_check(running_ids, "run")
    sys_evt_check(stopped_ids, "stop")


class BaseNosInterface:

    def populate_events_from_tracker(self, event_tracker):
        start_time_counts = defaultdict(int)
        end_time_counts = defaultdict(int)
        self.timed_events, self.start_events, self.stop_events, self.running_events, self.waiting_events = generate_timed_events(
            event_tracker)
        for time, event_list in event_tracker.event_lookup.items():
            start_event_count = 0
            stop_event_count = 0
            for ev_1 in event_list:
                event = make_sys_event(ev_1)
                self.timed_events[time].append(event)
                if event.is_start_event():
                    start_event_count += 1
                elif event.is_stop_event():
                    stop_event_count += 1
                elif event.is_running():
                    self.running_events[time].append(event)
                elif event.is_stopped():
                    self.waiting_events[time].append(event)
            start_time_counts[time] += start_event_count
            end_time_counts[time] += stop_event_count
        self.start_time_counts = start_time_counts
        self.end_time_counts = end_time_counts

    def init_conventional_scheduler(self):
        # if self.mode & SchedFlag.SC_MD_CACHED:
        print("System Scheduler Cached Starting with " + self.json_path)
        event_tracker, t, wp, rp = compute_nos_conventional(self.arbiter_algo, self.cores_in_sim, self.rr_time_slice,
                                                            True,self.json_path,self.end_time, True)

        self.populate_events_from_tracker(event_tracker)

    def init_nengo_scheduler(self):
        pass

    def get_events_dict(self, time, tp):
        if time == -1:
            time = self.current_tick

        if tp == "run":
            d = self.running_events[time]
        elif tp == "start":
            d = self.start_events[time]
        elif tp == "stop":
            d = self.stop_events[time]
        elif tp == "wait":
            d = self.waiting_events[time]
        else:
            return None
        dx = []
        for evt in d:
            in_dx = any(
                evt.model_id == old_d["model_id"]
                and evt.task_id == old_d["task_id"]
                and evt.event_type == old_d["event_type"]
                for old_d in dx
            )
            if not in_dx:
                dx.append(evt.get_dict())

        vdt = [evt.get_dict() for evt in d]
        return dx

    def get_start_events(self, time=-1):
        return self.get_events_dict(time, "start")

    def get_stop_events(self, time=-1):
        return self.get_events_dict(time, "stop")

    def get_running_events(self, time=-1):
        return self.get_events_dict(time, "run")

    def get_waiting_events(self, time=-1):
        return self.get_events_dict(time, "wait")

    def get_and_set_time(self):
        t = self.current_tick
        self.current_tick += 1
        return t

    def print_mode(self):
        mode_st = ""
        mode = self.mode
        if mode & SchedFlag.SC_MD_CONVENT:
            mode_st += "Conventional "
        elif mode & SchedFlag.SC_MD_NENGO:
            mode_st += "Nengo "
            if mode & SchedFlag.SC_MD_USE_NENGO_DL:
                mode_st += "With DL "
        if mode & SchedFlag.SC_MD_CACHED:
            mode_st += "-Cached- "
        if mode & SchedFlag.SC_MD_RR:
            mode_st += " Round Robin"
        elif mode & SchedFlag.SC_MD_FCFS:
            mode_st += " FCFS"
        return mode_st

    def __init__(self, mode, rr_time_slice, cores_in_sim, json_path, debug_print, end_time = 20000, instruction_file=None):
        self.end_time = end_time

        self.mode = mode
        self.rr_time_slice = rr_time_slice
        self.cores_in_sim = cores_in_sim
        self.json_path = json_path
        self.debug_print = debug_print
        self.instruction_file = instruction_file

        self.current_tick = 0

        self.current_events = []
        self.timed_events = defaultdict(list)

        self.start_events = defaultdict(list)
        self.stop_events = defaultdict(list)
        self.running_events = defaultdict(list)
        self.waiting_events = defaultdict(list)
        self.ttl_start_event_counts = 0
        self.ttl_stop_event_counts = 0
        self.start_time_counts = 0
        self.end_time_counts = 0

        self.running_procs_at_time = {}

        self.arbiter_algo = "RR" if mode & SchedFlag.SC_MD_RR else "FCFS"
        self.scheduler = None
        if mode & SchedFlag.SC_MD_NENGO:
            self.init_nengo_scheduler()
        elif mode & SchedFlag.SC_MD_CONVENT:  # NON NENGO MODE
            print("Conventional Scheduler Init")
            self.init_conventional_scheduler()
        else:
            print(f"WARN FROM BaseNOSInterface: No Scheduler Mode Entered")


def main():
    md = SchedFlag.SC_MD_CONVENT | SchedFlag.SC_MD_RR
    js_path = "/Users/plaggm/dev/nemo-codes/config/example_config.json"
    nog = BaseNosInterface(md, 100, 4096, js_path, True)
    print("result:")
    return nog


if __name__ == '__main__':
    main()