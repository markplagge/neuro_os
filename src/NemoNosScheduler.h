//
// Created by Mark Plagge on 7/25/20.
//

#ifndef NEMOTNG_NEMONOSSCHEDULER_H
#define NEMOTNG_NEMONOSSCHEDULER_H
#include "NemoSchedulerInterface.h"
#include "../extern/pybind11/include/pybind11/pybind11.h"
#include "../extern/pybind11/include/pybind11/embed.h"
namespace neuro_os {

	enum scheduler_mode{
		SC_MD_NENGO =  1 << 0,
		SC_MD_CONVENT =  1 << 1,
		SC_MD_CACHED =  1 << 2,
		SC_MD_RR =  1 << 3,
		SC_MD_FCFS = 1 << 4,
		SC_MD_USE_NENGO_DL = 1 << 5,
		SC_BASE_INIT = 1 << 6
	};
	struct FileSpike{
		int time = -1;
		int dest_core = -1;
		int dest_axon = -1;
	};
	class NemoNosScheduler {
		py::scoped_interpreter guard{};
		py::module sim_module = py::module::import("nengo_os");
		py::object nengo_os_iface;
		py::object nos_spike_handler;
		int current_time = 0;
		int num_cores_in_sim = 0;
		int rr_time_slice = 0;
		bool debug_print = false;
		int last_scheduled_event;
		int num_models = 0;
		int num_tasks = 0;

		enum scheduler_mode system_mode;

	public:
		NemoNosScheduler(scheduler_mode mode, int rr_time_slice, int cores_in_sim, const std::string& json_path,
						 bool debug_print);


		std::vector<ProcEvent> get_start_events();
		std::vector<ProcEvent> get_stop_events();
		std::vector<ProcEvent> get_all_events();
		std::vector<ProcEvent> get_start_events(int time);
		std::vector<ProcEvent> get_stop_events(int time);
		std::vector<ProcEvent> get_all_events(int time);

		std::vector<ProcEvent> get_running_procs(int time);
		std::vector<ProcEvent> get_running_procs();
		std::vector<ProcEvent> get_waiting_procs();
		std::vector<ProcEvent> get_waiting_procs(int time);

		int increment_scheduler_tick();
		int get_current_tick();
		template <typename ET>
		std::vector<ProcEvent> get_events(int time, ET type);

		std::vector<FileSpike> get_spikes_for_model_next_time(int model_id);
	};
	void test_new_iface();
}

#endif//NEMOTNG_NEMONOSSCHEDULER_H
