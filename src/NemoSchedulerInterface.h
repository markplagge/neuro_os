//
// Created by Mark Plagge on 7/19/20.
//

#ifndef NEMOTNG_NEMOSCHEDULERINTERFACE_H
#define NEMOTNG_NEMOSCHEDULERINTERFACE_H
#include "../extern/pybind11/include/pybind11/embed.h"
#include "NengoInterface.h"
#include "SimProcess.h"
#include "../extern/pybind11/include/pybind11/pybind11.h"
#include <vector>
#include <deque>
#include <map>
namespace py = pybind11;
namespace neuro_os {
	/**
	 * Nemo Scheduler Interface - Non-Spiking Scheduler for Nemo
	 */
	struct NemoSchedulerInterface:NengoInterface {
		NemoSchedulerInterface(bool use_dl, int cores_in_sim, int mode, int rr_time, const std::string& json_path, bool debug_print, bool is_nengo);
		//NemoSchedulerInterface(bool use_dl, int cores_in_sim, int mode, int rr_time, const std::string& json_path, bool debug_print);

	};

	enum event_types{
		SCH_INTERRUPT = 15,
		SCH_PRE_WAIT = 12,
		SCH_DONE = 16,
		SCH_RUNNING = 10,
		SCH_START_RUNNING = 14,
		SCH_START_WAIT = 13,
		SCH_WAIT = 11

	};

	struct ProcEvent {
		int model_id;
		int task_id;
		int event_type;
		int event_time;
		ProcEvent(int model_id, int task_id, int event_type, int event_time) : model_id(model_id), task_id(task_id), event_type(event_type), event_time(event_time) {}


	};
	ProcEvent create_evt_from_py_dict(py::dict python_event, py::module &module);

	struct NemoSelfContainedScheduler {
		std::map<int,std::vector<ProcEvent>> proc_events;
		NemoSelfContainedScheduler(int  mode, int  total_cores, int  time_slice, bool multiplexing, std::string proc_js_file, unsigned int end_ts);
		std::vector<ProcEvent> get_event_at_time(int time);
	};


	neuro_os::NengoSchedulerStatus get_nengo_status_non_nengo(const NengoInterface& nengo);
	std::vector<int> precompute_wait_q_non_nengo(const neuro_os::NengoInterface& nengo);
	std::vector<int> precompute_run_q_non_nengo(const neuro_os::NengoInterface& nengo);
	void increment_pc_non_nengo(const neuro_os::NengoInterface& nengo);
	void run_precompute_sim_non_nengo(const NengoInterface& nengo, int n_ticks);
	std::vector<int> get_models_to_start_at_time(NengoInterface *nengo, unsigned long time);
	std::vector<int> get_models_to_stop_at_time(NengoInterface *nengo, unsigned long time);
	int get_sched_time(NengoInterface * nengo);

}

#endif//NEMOTNG_NEMOSCHEDULERINTERFACE_H
