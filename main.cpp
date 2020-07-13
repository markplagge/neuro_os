//
// Created by Mark Plagge on 6/20/20.
//
#include "include/neuro_os.h"

int main(){
	auto p = std::make_shared<neuro_os::sim_proc::SimProc>();
	neuro_os::sim_proc::SimProcessQueue q;
    neuro_os::NengoInterface iface;

    std::string js_test_path("/Users/plaggm/dev/nemo-codes/src/libs/neuro_os/scripts/ex_c.json");
	q.enqueue(p);
	return 0;
}