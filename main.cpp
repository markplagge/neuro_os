//
// Created by Mark Plagge on 6/20/20.
//
#include "include/neuro_os.h"

int main(){
	auto p = std::make_shared<neuro_os::sim_proc::SimProc>();
	neuro_os::sim_proc::SimProcessQueue q;


    std::string js_test_path("/Users/plaggm/dev/nemo-codes/src/libs/neuro_os/scripts/ex_c.json");
    neuro_os::NengoInterface iface(false, 4096, 1, 1024,js_test_path);
	q.enqueue(p);
	iface.nengo_os_iface.attr("init_process_list_from_json")(js_test_path);
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


	return 0;

}