//
// Created by Mark Plagge on 7/13/20.
//

#include "NengoInterface.h"
//(self, use_nengo_dl: bool =False, cores_in_sim: int = 4096, mode: int = 0, rr_time_slice: int = 4096):
neuro_os::NengoInterface::NengoInterface(bool use_dl, int cores_in_sim, int mode, int rr_time) {

  py::exec(R"(
              print("inside pybind" )
              )");
  sim_mod = py::module::import("nengo_os");

  this->nengo_os_iface = sim_mod.attr("NemoNengoInterface")(use_dl,cores_in_sim,mode,rr_time);
}
neuro_os::NengoInterface::NengoInterface(bool use_dl, int cores_in_sim, int mode, int rr_time,std::string json_path){
  sim_mod = py::module::import("nengo_os");

  this->nengo_os_iface = sim_mod.attr("NemoNengoInterface")(use_dl,cores_in_sim,mode,rr_time);
  this->nengo_os_iface.attr("init_process_list_from_json")(json_path);
  this->nengo_os_iface.attr("init_model")();
}

void neuro_os::run_sim_n_ticks(const NengoInterface &nengo, int n_ticks){
  nengo.nengo_os_iface.attr("run_sim_time")(n_ticks);
}
void neuro_os::run_precompute_sim(const NengoInterface  &nengo, int n_ticks){
  nengo.nengo_os_iface.attr("generate_full_results")(n_ticks);
}
std::vector<int> neuro_os::convert_q(py::list &pylist){
  std::vector<int> rq;
  for (const auto &item : pylist) {
    auto i = py::cast<int>(item);
    rq.push_back(i);
  }
  return rq;
}
std::vector<int> neuro_os::precompute_run_q(const neuro_os::NengoInterface &nengo) {

  py::list run_q =  nengo.nengo_os_iface.attr("running_proc_precompute")();
  auto rq = convert_q(run_q);
  return rq;
}
std::vector<int> neuro_os::precompute_wait_q(const neuro_os::NengoInterface &nengo) {
  py::list wait_q =  nengo.nengo_os_iface.attr("waiting_proc_precompute")();
  auto wq = convert_q(wait_q);
  return wq;
}
void neuro_os::increment_pc(const neuro_os::NengoInterface &nengo) {
  nengo.nengo_os_iface.attr("increment_pc")();
}
neuro_os::NengoSchedulerStatus neuro_os::get_nengo_status(const NengoInterface  &nengo) {
  auto epoch = nengo.nengo_os_iface.attr("precompute_time").cast<int>();
  auto run_q = precompute_run_q(nengo);
  auto wait_q = precompute_wait_q(nengo);
  increment_pc(nengo);
  NengoSchedulerStatus status(epoch,run_q,wait_q);
  return status;
}
neuro_os::NengoSchedulerStatus::NengoSchedulerStatus(int i,
                                                     std::vector<int, std::allocator<int>> vector,
                                                     std::vector<int, std::allocator<int>> vector_1) {

}
