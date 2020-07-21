//
// Created by Mark Plagge on 3/11/20.
//

#ifndef SUPERNEMO_PROCESS_STATES_H
#define SUPERNEMO_PROCESS_STATES_H
#include <string>
namespace neuro_os {
    namespace sim_proc {
        typedef enum {
            WAITING = 	1 << 0,
            RUNNING = 	1 << 1,
            COMPLETE =	1 << 2,
			PRE_WAIT =  1 << 3,
			NO_OP = 0
        } PROC_STATE;

        typedef enum {
            CAN_ADD,
            IS_FULL
        } SCHEDULER_STATE;

		struct PY_PROC_STATE {
			static constexpr unsigned int WAITING =  neuro_os::sim_proc::WAITING ;
			static constexpr unsigned int RUNNING =  neuro_os::sim_proc::RUNNING ;
			static constexpr unsigned int DONE =      neuro_os::sim_proc::COMPLETE;
			static constexpr unsigned int PRE_WAIT = neuro_os::sim_proc::PRE_WAIT;
			template <typename BTP>
			static bool strings_equal(const std::string & a, BTP b) {

				std::string bx(b);
				if (a == bx){
					return true;
				}
				return false;


			}

			static  unsigned int  GET_STATE_FROM_NAME(const std::string & a){
#define ct(b) if (PY_PROC_STATE::strings_equal(a,#b)) return PY_PROC_STATE::b;
				ct(WAITING);
				ct(RUNNING);
				ct(DONE);
				ct(PRE_WAIT);
				return -1;
#undef ct
			}


			static  int get_proc_state_from_py(int value){
				switch (value) {
				case 0:
					return WAITING;
				case 1:
					return RUNNING;
				case 2:
					return DONE;
				case 3:
					return PRE_WAIT;
				default:
					return 0;

				}
			}
		};

    }
}
#endif //SUPERNEMO_PROCESS_STATES_H
