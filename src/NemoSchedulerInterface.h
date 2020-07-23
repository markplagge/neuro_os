//
// Created by Mark Plagge on 7/19/20.
//

#ifndef NEMOTNG_NEMOSCHEDULERINTERFACE_H
#define NEMOTNG_NEMOSCHEDULERINTERFACE_H
#include "../extern/pybind11/include/pybind11/embed.h"
#include "NengoInterface.h"
#include "SimProcess.h"

namespace py = pybind11;
namespace neuro_os {
	/**
	 * Nemo Scheduler Interface - Non-Spiking Scheduler for Nemo
	 */
	struct NemoSchedulerInterface:NengoInterface {
		NemoSchedulerInterface(bool use_dl, int cores_in_sim, int mode, int rr_time, const std::string& json_path, bool debug_print, bool is_nengo);
		//NemoSchedulerInterface(bool use_dl, int cores_in_sim, int mode, int rr_time, const std::string& json_path, bool debug_print);

	};
	neuro_os::NengoSchedulerStatus get_nengo_status_non_nengo(const NengoInterface& nengo);
	std::vector<int> precompute_wait_q_non_nengo(const neuro_os::NengoInterface& nengo);
	std::vector<int> precompute_run_q_non_nengo(const neuro_os::NengoInterface& nengo);
	void increment_pc_non_nengo(const neuro_os::NengoInterface& nengo);
	void run_precompute_sim_non_nengo(const NengoInterface& nengo, int n_ticks);
	std::vector<int> get_models_to_start_at_time(NengoInterface *nengo, unsigned long time);
	std::vector<int> get_models_to_stop_at_time(NengoInterface *nengo, unsigned long time);
}
#endif//NEMOTNG_NEMOSCHEDULERINTERFACE_H
