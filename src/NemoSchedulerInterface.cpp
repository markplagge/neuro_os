//
// Created by Mark Plagge on 7/19/20.
//

#include "NemoSchedulerInterface.h"
namespace neuro_os {
	NemoSchedulerInterface::NemoSchedulerInterface(bool use_dl, int cores_in_sim, int mode, int rr_time,
												   const std::string& json_path, bool debug_print, bool is_nengo) : NengoInterface(use_dl, cores_in_sim, mode, rr_time, json_path, debug_print, is_nengo) {
		sim_mod = py::module::import("nengo_os");
		std::string mode_str;
		if (mode == 0) {
			mode_str = std::string("FCFS");
		}
		else {
			mode_str = std::string("RR");
		}
		this->nengo_os_iface = sim_mod.attr("ConventScheduler")(py::none(), mode_str, cores_in_sim, rr_time, true, json_path);
		//this->nengo_os_iface.attr("init_process_list_from_json")(json_path);
		//this->nengo_os_iface.attr("init_model")();
		this->sim_mod.attr("debug_print");
		if (debug_print) {
			this->sim_mod.attr("debug_print") = true;
		}
		else {
			this->sim_mod.attr("debug_print") = false;
		}
	}
	/* def increment_pc(self):
        self.precompute_lookup_time += 1


    def get_precompute_lists_at_time(self,time):
        return self.precompute_waiting_time[time], self.precompute_running_procs[time]

    def get_precompute_wait_at_time(self, time):
        return  self.precompute_waiting_time[time]

    def get_precompute_run_at_time(self, time):
        return self.precompute_running_procs[time] */

	std::vector<int> precompute_run_q_non_nengo(const neuro_os::NengoInterface& nengo) {

		py::list run_q = nengo.nengo_os_iface.attr("get_precompute_run_at_time")();
		auto rq = convert_q(run_q);
		return rq;
	}
	std::vector<int> precompute_wait_q_non_nengo(const neuro_os::NengoInterface& nengo) {
		py::list wait_q = nengo.nengo_os_iface.attr("get_precompute_wait_at_time")();
		auto wq = convert_q(wait_q);
		return wq;
	}
	void increment_pc_non_nengo(const neuro_os::NengoInterface& nengo) {
		nengo.nengo_os_iface.attr("increment_pc")();
	}
	neuro_os::NengoSchedulerStatus get_nengo_status_non_nengo(const NengoInterface& nengo) {
		auto epoch = nengo.nengo_os_iface.attr("precompute_time").cast<int>();
		auto run_q = precompute_run_q_non_nengo(nengo);
		auto wait_q = precompute_wait_q_non_nengo(nengo);
		increment_pc_non_nengo(nengo);
		NengoSchedulerStatus status(epoch, run_q, wait_q);
		return status;
	}
	void run_precompute_sim_non_nengo(const NengoInterface& nengo, int n_ticks) {
		nengo.nengo_os_iface.attr("precompute_scheduler")(n_ticks);
	}

	std::vector<int> get_models_to_start_at_time(NengoInterface* nengo, unsigned long time) {
		std::vector<int> start_model_evts;
		auto start_messages = nengo->nengo_os_iface.attr("get_messages_at_time")(time, 1);
		for (auto& msg : start_messages) {
			start_model_evts.push_back(msg.cast<int>());
		}

		return start_model_evts;
	}
	std::vector<int> get_models_to_stop_at_time(NengoInterface* nengo, unsigned long time) {
		auto stop_messages = nengo->nengo_os_iface.attr("get_messages_at_time")(time, 0);
		std::vector<int> stop_model_evts;
		for (auto& msg : stop_messages) {
			stop_model_evts.push_back(msg.cast<int>());
		}
		return stop_model_evts;
	}
	int get_sched_time(NengoInterface* nengo) {
		return nengo->nengo_os_iface.attr("get_current_precompute_time")().cast<int>();
	}
	using namespace pybind11::literals;

	ProcEvent create_evt_from_py_dict(py::dict python_event, py::module& module) {
#define PY_CST(f) python_event[f].cast<int>()
		auto pe = ProcEvent(
				PY_CST("model_id"),
				PY_CST("task_id"),
				PY_CST("event_type"),
				PY_CST("time"));
#undef PY_CST
		return pe;
	}


	NemoSelfContainedScheduler::NemoSelfContainedScheduler(int mode, int total_cores, int time_slice, bool multiplexing, std::string proc_js_file, unsigned int end_ts) {
		py::scoped_interpreter guard{};
		py::module sim_mod = py::module::import("nengo_os");
		//run compute_nos_conventional_event_dict
		py::list scheduler_result = sim_mod.attr("compute_nos_conventional_event_list")(mode, total_cores, time_slice, multiplexing, proc_js_file, end_ts);
		//each element in the list is a Event so convert them, and create the self-contained list of events

		for (auto evt : scheduler_result) {
			py::dict evt_dict = evt.attr("get_event_from_c_int")().cast<py::dict>();
			auto proc_event = create_evt_from_py_dict(evt_dict, sim_mod);
			if (this->proc_events.count(proc_event.event_time) == 0) {
				this->proc_events[proc_event.event_time] = std::vector<ProcEvent>();
			}
			this->proc_events[proc_event.event_time].push_back(proc_event);
		}

		//		def compute_nos_conventional_event_list(mode="FCFS", total_cores=4096, time_slice=50, multiplexing=True,
		//		proc_js_file=None, end_ts = 10000):
	}
	std::vector<ProcEvent> NemoSelfContainedScheduler::get_event_at_time(int time) {
		if (this->proc_events.count(time)) {
			return this->proc_events[time];
		}
		else {
			return std::vector<ProcEvent>();
		}
	}



}// namespace neuro_os
