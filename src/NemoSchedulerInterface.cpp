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
		auto run_q = precompute_run_q(nengo);
		auto wait_q = precompute_wait_q(nengo);
		increment_pc(nengo);
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
}

