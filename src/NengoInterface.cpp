//
// Created by Mark Plagge on 7/13/20.
//

#include "NengoInterface.h"
#include "SimProcess.h"
namespace neuro_os {
	NengoInterface::NengoInterface(bool use_dl, int cores_in_sim, int mode, int rr_time, std::string json_path, bool debug_print) {
		sim_mod = py::module::import("nengo_os");

		this->nengo_os_iface = sim_mod.attr("NemoNengoInterface")(use_dl, cores_in_sim, mode, rr_time);
		this->nengo_os_iface.attr("init_process_list_from_json")(json_path);
		this->nengo_os_iface.attr("init_model")();
		this->sim_mod.attr("debug_print");
		if (debug_print) {
			this->sim_mod.attr("debug_print")=true;
		}else{
			this->sim_mod.attr("debug_print")=false;
		}
	}

	void run_sim_n_ticks(const NengoInterface& nengo, int n_ticks) {
		nengo.nengo_os_iface.attr("run_sim_time")(n_ticks);
	}
	void run_precompute_sim(const NengoInterface& nengo, int n_ticks) {
		nengo.nengo_os_iface.attr("generate_full_results")(n_ticks);
	}
	std::vector<int> convert_q(py::list& pylist) {
		std::vector<int> rq;
		for (const auto& item : pylist) {
			auto i = py::cast<int>(item);
			rq.push_back(i);
		}
		return rq;
	}
	std::vector<int> precompute_run_q(const neuro_os::NengoInterface& nengo) {

		py::list run_q = nengo.nengo_os_iface.attr("running_proc_precompute")();
		auto rq = convert_q(run_q);
		return rq;
	}
	std::vector<int> precompute_wait_q(const neuro_os::NengoInterface& nengo) {
		py::list wait_q = nengo.nengo_os_iface.attr("waiting_proc_precompute")();
		auto wq = convert_q(wait_q);
		return wq;
	}
	void increment_pc(const neuro_os::NengoInterface& nengo) {
		nengo.nengo_os_iface.attr("increment_pc")();
	}
	neuro_os::NengoSchedulerStatus get_nengo_status(const NengoInterface& nengo) {
		auto epoch = nengo.nengo_os_iface.attr("precompute_time").cast<int>();
		auto run_q = precompute_run_q(nengo);
		auto wait_q = precompute_wait_q(nengo);
		increment_pc(nengo);
		NengoSchedulerStatus status(epoch, run_q, wait_q);
		return status;
	}

	template<typename SIM_PROC>
	std::vector<SIM_PROC> precompute_wait_q(const NengoInterface& nengo, int x) {
		return std::vector<SIM_PROC>();
	}
	neuro_os::NengoSchedulerStatus::NengoSchedulerStatus(int i,
														 std::vector<int, std::allocator<int>> vector,
														 std::vector<int, std::allocator<int>> vector_1) {
	}


	namespace  py = pybind11;



	sim_proc::SimProcess create_proc_from_pyobj(py::object python_process){
#define PV(S) proc_data[S].cast<int>()
		py::dict proc_data = python_process.attr("to_dict")();
		int state = sim_proc::PY_PROC_STATE::GET_STATE_FROM_NAME(proc_data["state"].cast<std::string>());
		return sim_proc::SimProcess(PV("MODEL_ID"),PV("needed_cores"),PV("needed_time"),state);
#undef PV
	}
	std::vector<sim_proc::SimProcess> convert_py_list(py::list py_list) {
		std::vector<sim_proc::SimProcess> proc_list;
		for (auto & py_proc : py_list){
			auto sim_proc = create_proc_from_pyobj(py_proc.cast<py::object>());
			proc_list.push_back(sim_proc);
		}
		return proc_list;
	}

	std::vector<neuro_os::sim_proc::SimProcess> precompute_run_proc(const NengoInterface& nengo) {

		auto list_of_procs = nengo.nengo_os_iface.attr("running_proc_precompute_procs")();
		return convert_py_list(list_of_procs);
	}


	std::vector<neuro_os::sim_proc::SimProcess> precompute_wait_proc(const NengoInterface& nengo) {

		auto list_of_procs = nengo.nengo_os_iface.attr("waiting_proc_precompute_procs")();
		return convert_py_list(list_of_procs);
	}
}