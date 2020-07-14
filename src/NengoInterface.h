//
// Created by Mark Plagge on 7/13/20.
//

#ifndef NEUROOS_SRC_NENGOINTERFACE_H_
#define NEUROOS_SRC_NENGOINTERFACE_H_
#include <include/pybind11/embed.h>
namespace py = pybind11;
namespace neuro_os {
struct NengoInterface {
  py::scoped_interpreter guard{};
  py::module sim_mod = py::module::import("nengo_os");
  py::object nengo_os_iface;
  NengoInterface(bool use_dl, int cores_in_sim, int mode, int rr_time );
  NengoInterface(bool use_dl, int cores_in_sim, int mode, int rr_time,std::string json_path);
};


struct NengoSchedulerStatus{
  NengoSchedulerStatus(int i,
                       std::vector<int, std::allocator<int>> vector,
                       std::vector<int, std::allocator<int>> vector_1);
  int epoch;
  std::vector<int> run_q;
  std::vector<int> wait_q;
};

void run_sim_n_ticks(const NengoInterface &nengo, int n_ticks);
void run_precompute_sim(const NengoInterface  &nengo, int n_ticks);
std::vector<int> precompute_run_q(const NengoInterface  &nengo);
std::vector<int> precompute_wait_q(const NengoInterface  &nengo);
void increment_pc(const NengoInterface  &nengo);
NengoSchedulerStatus get_nengo_status(const NengoInterface  &nengo);
std::vector<int> convert_q(py::list &pylist);
}



#endif //NEUROOS_SRC_NENGOINTERFACE_H_
