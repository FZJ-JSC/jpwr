import time
from multiprocessing import Process, Queue, Event

import pandas as pd

def power_loop(queue, event, interval, power_methods, options):
    power_value_dict = {
        'timestamps': []
    }

    for pmethod in power_methods:
        pmethod.init(power_value_dict)
    

    last_timestamp = time.time()

    while not event.is_set():
        try:
            for pmethod in power_methods:
                pmethod.measure(power_value_dict)
            timestamp = time.time()
            power_value_dict['timestamps'].append(timestamp)
        except:
            # We want timestamp to be measured after the power methods,
            # so instead of measuring it outside the try/except, measure
            # it in both
            timestamp = time.time()
            keep_values_upto = len(power_value_dict["timestamps"])
            not_timestamps = [k for k in power_value_dict if k != "timestamps"]
            for key in not_timestamps:
                power_value_dict[key] = power_value_dict[key][:keep_values_upto]
            if not options.get('ignore_measure_errors', False):
                raise RuntimeError("Measurement error")
        wait_for = max(0,1e-3*interval-(timestamp-last_timestamp))
        time.sleep(wait_for)
        last_timestamp = timestamp

    additional_data = {}

    for pmethod in power_methods:
        additional_data.update(pmethod.finalize(power_value_dict))
    queue.put(power_value_dict)
    queue.put(additional_data)

class get_power(object):
    
    def __init__(self, power_methods, interval, options={}):
        self.power_methods = power_methods
        self.interval = interval
        self.options = options
    def __enter__(self):
        self.end_event = Event()
        self.power_queue = Queue()
        
        self.pwp = Process(target=power_loop,
                args=(self.power_queue, self.end_event, self.interval, self.power_methods, self.options))
        self.pwp.start()
        return self
    def __exit__(self, type, value, traceback):
        self.end_event.set()
        power_value_dict = self.power_queue.get()
        self.additional_data = self.power_queue.get()
        self.pwp.join()

        self.df = pd.DataFrame(power_value_dict)
    def energy(self):
        import numpy as np
        energy_df = self.df.loc[:,self.df.columns != 'timestamps'].astype(float).multiply(self.df["timestamps"].diff(),axis="index")/3600
        energy_df = energy_df[1:].sum(axis=0)
        return energy_df,self.additional_data
