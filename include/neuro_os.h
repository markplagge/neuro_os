//
// Created by Mark Plagge on 5/28/20.
//

#ifndef NEMOTNG_NEURO_OS_H
#define NEMOTNG_NEURO_OS_H
#include <vector>
#include "../src/process_states.h"
#include "../src/SimProcess.h"
#include "../src/SimProcessSerial.h"
#include "../src/SimProcessQueue.h"
#define max_proc_time 64


namespace neuro_os {
	namespace sim_proc {


//simulated_processor defs

		template<class T>
		struct SimProcess;
		struct SimProcessQueue;
		struct SimProcessSerial;

	}
}

#endif//NEMOTNG_NEURO_OS_H
