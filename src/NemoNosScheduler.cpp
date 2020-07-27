//
// Created by Mark Plagge on 7/25/20.
//

#include "NemoNosScheduler.h"
namespace neuro_os {

	NemoNosScheduler::NemoNosScheduler(scheduler_mode mode, int rr_time_slice, int cores_in_sim,
									   const std::string& json_path, bool debug_print) :num_cores_in_sim(cores_in_sim),
									 	rr_time_slice(rr_time_slice), debug_print(debug_print), system_mode(mode)  {
		int m_mode = static_cast<unsigned int>(mode);
		nengo_os_iface = sim_module.attr("BaseNosInterface")(m_mode,rr_time_slice,cores_in_sim, json_path, debug_print);
		nos_spike_handler = sim_module.attr("SpikeHandler")(json_path);

	}

	ProcEvent convert_pydict_event(py::dict event){

		auto model_id = event["model_id"].cast<int>();
		auto task_id = event["task_id"].cast<int>();
		auto event_type = event["event_type"].cast<int>();
		auto event_time = event["event_time"].cast<int>();
		auto pe = ProcEvent(model_id,task_id,event_type,event_time);
		return pe;
	}
	std::vector<ProcEvent> convert_pylist_events(py::list event_list){
		std::vector<ProcEvent> events;
		events.reserve(event_list.size());
		for (const auto& event : event_list) {
			events.push_back(convert_pydict_event(event.cast<py::dict>()));
		}

		return events;
	}
	enum EVENT_TYPE_LOOKUP{
		START = 0,
		STOP = 1,
		WAIT = 2,
		RUN = 3
	};

	template<typename ET>
	std::vector<ProcEvent> NemoNosScheduler::get_events(int time, ET type){
		std::string command;
		switch (type) {
		case START:
			command = std::string("get_start_events");
			break;
		case STOP:
			command = std::string("get_stop_events");
			break;
		case WAIT:
			command = std::string("get_waiting_events");
			break;
		case RUN:
			command = std::string("get_running_events");
			break;
		}
		auto py_event_list = this->nengo_os_iface.attr(command.c_str())(time).cast<py::list>();
		return convert_pylist_events(py_event_list);

	}
	std::vector<ProcEvent> NemoNosScheduler::get_start_events() {
		return get_start_events(-1);
	}
	std::vector<ProcEvent> NemoNosScheduler::get_start_events(int time) {
		return get_events(time,START);
	}

	std::vector<ProcEvent> NemoNosScheduler::get_stop_events() {
		return get_stop_events(-1);
	}

	std::vector<ProcEvent> NemoNosScheduler::get_stop_events(int time) {
		return get_events(time, STOP);
	}


	std::vector<ProcEvent> NemoNosScheduler::get_all_events() {
		return get_all_events(-1);
	}


	std::vector<ProcEvent> NemoNosScheduler::get_all_events(int time) {
		return std::vector<ProcEvent>();
	}

	std::vector<ProcEvent> NemoNosScheduler::get_running_procs() {
		return get_running_procs(-1);
	}
	std::vector<ProcEvent> NemoNosScheduler::get_running_procs(int time) {
		return get_events(time, RUN);
	}
	std::vector<ProcEvent> NemoNosScheduler::get_waiting_procs() {
		return get_waiting_procs(-1);
	}
	std::vector<ProcEvent> NemoNosScheduler::get_waiting_procs(int time) {
		return get_events(time, WAIT);
	}


	int NemoNosScheduler::increment_scheduler_tick() {
		int ct;
		auto result = this->nengo_os_iface.attr("get_and_set_time")();
		ct = result.cast<int>();
		return ct;
	}
	int NemoNosScheduler::get_current_tick(){
		return this->nengo_os_iface.attr("current_tick")().cast<int>();
	}
	FileSpike convert_spike_dict_to_file_spike(py::dict elm) {
		auto sc_time = elm["time"].cast<int>();
		auto dest_core = elm["core"].cast<int>();
		auto dest_axon = elm["axon"].cast<int>();
		FileSpike sp;
		sp.time = sc_time;
		sp.dest_core = dest_core;
		sp.dest_axon = dest_axon;
		return sp;
	}
	std::vector<FileSpike> convert_spike_list_to_file_spike(py::list spike_list){
		std::vector<FileSpike> spikes;
		for (const auto& spike : spike_list) {
			spikes.push_back(convert_spike_dict_to_file_spike(spike.cast<py::dict>()));
		}
		return spikes;
	}
	std::vector<FileSpike> NemoNosScheduler::get_spikes_for_model_next_time(int model_id) {
		auto spike_element_list = this->nos_spike_handler.attr("get_next_spikes")(model_id).cast<py::list>();
		return convert_spike_list_to_file_spike(spike_element_list);
	}

}