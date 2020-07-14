//
// Created by Mark Plagge on 3/11/20.
//

#ifndef SUPERNEMO_SIMPROCESS_H
#define SUPERNEMO_SIMPROCESS_H

#include "../lib/json.hpp"
#include "./process_states.h"
#include <iostream>
#include <ostream>


namespace neuro_os {
	namespace sim_proc {
		using nlohmann::json;

		struct SimProcess {
			SimProcess(int pid, int neededCores, int neededRunTime, double scheduledStartTime);

			SimProcess() {
				PID = 0;
				model_id = 0;
				needed_cores = 0;
				needed_run_time = 0;
				scheduled_start_time = 0;
				total_wait_time = 0;
				total_run_time = 0;
				current_state = NO_OP;
			}
			SimProcess(int model_id, int needed_cores, int needed_time, int current_state);

			int PID;
			int model_id;
			int needed_cores;
			int needed_run_time;
			double scheduled_start_time;
			int total_wait_time;
			int total_run_time;
			int current_run_time = 0;
			int clock = -1;
			PROC_STATE current_state;
			//T neuron_state_system;

			PROC_STATE get_current_state() const;

			void set_current_state(PROC_STATE current_state);

			int get_pid() const;

			int get_needed_cores() const;

			int get_needed_run_time() const;

			double get_scheduled_start_time() const;

			int get_total_wait_time() const;

			int get_total_run_time() const;

			void system_tick();

			friend std::ostream& operator<<(std::ostream& os, const SimProcess& process);

			bool operator==(const SimProcess& rhs) const;

			bool operator!=(const SimProcess& rhs) const;

			bool can_start() const {
				return clock >= scheduled_start_time;
			}
			bool is_running() const {
				return current_state == RUNNING;
			}

			//control ops:
			void start();
			void stop();
		};
		template <typename PY_OB>
		SimProcess create_proc_from_pyobj(PY_OB python_process);




	}// namespace sim_proc
}// namespace neuro_os

#endif//SUPERNEMO_SIMPROCESS_H
