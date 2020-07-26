//
// Created by Mark Plagge on 6/20/20.
//
//#include "include/neuro_os.h"
//#include "src/process_states.h"
//#include "src/NengoInterface.h"
#include "./extern/pybind11/include/pybind11/embed.h"
#include "./extern/pybind11/include/pybind11/pybind11.h"
#include "src/NemoNosScheduler.h"
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
	neuro_os::test_new_iface();
	test_py();

	return 0;


}