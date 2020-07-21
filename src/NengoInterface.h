//
// Created by Mark Plagge on 7/13/20.
//

#ifndef NEUROOS_SRC_NENGOINTERFACE_H_
#define NEUROOS_SRC_NENGOINTERFACE_H_
#include "SimProcess.h"
//#include <pybind11/embed.h>
#include "../extern/pybind11/include/pybind11/embed.h"

namespace py = pybind11;
namespace neuro_os {
	/**
	 * NengoInterface Struct
	 * Struct that contains the python bindings for the nengo operating system scheduler. On init compiles the nengo network
	 */
	struct NengoInterface {

		py::scoped_interpreter guard{};
		py::module sim_mod = py::module::import("nengo_os");
		py::object nengo_os_iface;
		NengoInterface(){
			py::exec(R"(
print('PreNOS Init'
)");
		}

		NengoInterface(bool use_dl, int cores_in_sim, int mode, int rr_time,
					   std::string json_path, bool debug_print, bool is_nengo = true);
	};

	struct NengoSchedulerStatus {
		NengoSchedulerStatus(int i,
							 std::vector<int, std::allocator<int>> vector,
							 std::vector<int, std::allocator<int>> vector_1);
		int epoch;
		std::vector<int> run_q;
		std::vector<int> wait_q;
	};

	/**
	 * Given an instance of a NengoInterface struct, run the simulation for a set number of ticks.
	 * @param nengo NengoInterface containing current scheduler algorithm
	 * @param n_ticks Number of ticks to run
	 */
	void run_sim_n_ticks(const NengoInterface& nengo, int n_ticks);
	/**
	 * For precomputation of the scheduler stats. This runs the simulation for n_ticks and saves the state changes
	 * @param nengo
	 * @param n_ticks Number of ticks to compute. Should be greater than the end of the ROSS simulation
	 */
	void run_precompute_sim(const NengoInterface& nengo, int n_ticks);
	std::vector<int> precompute_run_q(const NengoInterface& nengo);
	std::vector<int> precompute_wait_q(const NengoInterface& nengo);

	std::vector<sim_proc::SimProcess> convert_py_list(py::list py_list);
	/**
	 * The NengoInterface struct, when precomputed, contains a current epoch value. This
	 * returns the currently running processes (SimProcess objects) in a vector at the current epoch
	 * @param nengo
	 * @return
	 */
	std::vector<neuro_os::sim_proc::SimProcess> precompute_run_proc(const NengoInterface& nengo);
	/**
	 * The NengoInterface struct, when precomputed, contains a current epoch value. This
	 * returns the currently waiting & pre-wait processes (SimProcess objects) in a vector at the current epoch
	 * @param nengo
	 * @return
	 */
	std::vector<neuro_os::sim_proc::SimProcess> precompute_wait_proc(const NengoInterface& nengo);
	/**
	 * Increments the current epoch time for precompute mode.
	 * @param nengo
	 */
	void increment_pc(const NengoInterface& nengo);
	/**
	 * returns the current status of the nengo interface -waiting, running, and current epoch-
	 * @param nengo
	 * @return
	 */
	NengoSchedulerStatus get_nengo_status(const NengoInterface& nengo);

	std::vector<int> convert_q(py::list& pylist);
}// namespace neuro_os

#endif//NEUROOS_SRC_NENGOINTERFACE_H_
