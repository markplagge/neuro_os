//
// Created by Mark Plagge on 6/20/20.
//
#include "include/neuro_os.h"
#include "src/process_states.h"
#include "src/NengoInterface.h"
#include <pybind11/embed.h>
namespace py = pybind11;

void test_py(){
	py::scoped_interpreter guard{};

	py::exec(R"(
        kwargs = dict(name="World", number=42)
        message = "Hello, {name}! The answer is {number}".format(**kwargs)
        print(message)
    )");
	auto locals = py::dict();
	py::exec(R"(
message = 'DONE'
)",py::globals(), locals);
	auto val = locals["message"].cast<std::string>();
	auto tv = const_cast<char *>(val.c_str());
	auto av = neuro_os::sim_proc::PY_PROC_STATE::GET_STATE_FROM_NAME(tv);
	std::cout << "DONE FROM PY: " << av << "\n";
}

int main(){

	test_py();

	auto p = std::make_shared<neuro_os::sim_proc::SimProc>();
	neuro_os::sim_proc::SimProcessQueue q;
	auto av = neuro_os::sim_proc::PY_PROC_STATE::GET_STATE_FROM_NAME("WAITING");
	auto ab = std::string("RUNNING").c_str();
	auto aab = const_cast<char *>(ab);
	auto rv = neuro_os::sim_proc::PY_PROC_STATE::GET_STATE_FROM_NAME(aab);
	std::cout << av << "\n";
	std::cout << "RV: " << rv << "\n";


    std::string js_test_path("/Users/plaggm/dev/nemo-codes/src/libs/neuro_os/scripts/ex_c.json");
    neuro_os::NengoInterface iface(false, 4096, 1, 1024,js_test_path,true);
	q.enqueue(p);
	iface.nengo_os_iface.attr("init_process_list_from_json")(js_test_path);

	auto mlist = precompute_wait_proc(iface);
	for(auto &p : mlist){
		std::cout << "GOT PROC MID: " << p.model_id << "\n";
	}
	return 0;
	neuro_os::run_sim_n_ticks(iface,10);
	auto e1 = neuro_os::get_nengo_status(iface);
    auto e2 = neuro_os::get_nengo_status(iface);
    auto e3 = neuro_os::get_nengo_status(iface);

    char *times = (char*)calloc(sizeof(char),65535);
    sprintf(times, "r1: ");
    for(int i : e1.run_q){
      sprintf(times,"%s %i ,",times, i);
    }
    sprintf(times,"%s\n", times);
  sprintf(times, "%s r3: ",times);
    for(int i : e3.run_q){
      sprintf(times,"%s %i ,",times, i);
    }
    printf("%s \n", times);


      //rq1: A B C D
      //rq2: A B C D

	free(times);
	return 0;

}