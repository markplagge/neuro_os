import json
import multiprocessing
from collections import defaultdict



class SpikeFile:
    def __init__(self, model_id, file_path):
        self.file = open(file_path, "r")
        self.model_id = model_id
        self.current_time = 0
        self.current_line = defaultdict(list)
        self.file_path = file_path
        self.readlines()
        self.file = None


    def readlines(self):
        for l in self.file:

            l = l.rstrip(",\n").lstrip("[").rstrip("]")

            obj = json.loads(l)
            obj['time'] = int(obj['time'])
            obj['core'] = int(obj['core'])
            obj['axon'] = int(obj['axon'])
            self.current_line[obj['time']].append(obj)



    def get_spikes_at_time(self,time):
        return self.current_line[time]

    #[{"time": 2, "core": 512, "axon": 0},


def loader(mid, spikef):
    return SpikeFile(mid, spikef)


class SpikeHandler:
    def __init__(self, config_file):
        config = json.load(open(config_file,'r'))
        spike_files = {}
        with multiprocessing.Pool(processes=8) as pool:
            workers = []
            for model_item in config['models']:
                mid = model_item['id']
                spikef = model_item['spike_file_path']
                workers.append(pool.apply_async(loader, (mid, spikef, )))

            for worker in workers:
                spike_f = worker.get()
                mid = spike_f.model_id
                spike_files[mid] = spike_f

        self.spike_files = spike_files
        self.spike_times = {id: 0 for id in spike_files}


    def get_spikes_at_time(self,model_id,time):
        spike_file = self.spike_files[model_id].get_spikes_at_time(time)
        return spike_file

    def get_next_spikes(self, model_id):
        cur_time = self.spike_times[model_id]
        spike_data = self.spike_files[model_id].get_spikes_at_time(cur_time)
        self.spike_times[model_id] += 1
        return spike_data

def line_o_matic():
    pth = "/Users/plaggm/dev/nemo-codes/config/example_config.json"
    spike_handler = SpikeHandler(pth)

    return spike_handler


if __name__ == '__main__':
    pass

