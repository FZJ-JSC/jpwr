import os
import re

import pandas as pd
rocm_path = os.getenv("ROCM_PATH")
if rocm_path is None:
    rocm_path = "/opt/rocm/"
try:
    from rsmiBindings import *
except:
    import sys
    # 6.x path
    sys.path.append(os.path.join(rocm_path, "libexec/rocm_smi/"))
    # 5.x path
    sys.path.append(os.path.join(rocm_path, "rocm_smi/bindings"))
    from rsmiBindings import *
from multiprocessing import Process, Queue, Event

class power(object):
    def init(self, power_value_dict : dict[str,list[float]]):
        init_bindings_required = True
        try:
            with open(os.path.join(rocm_path,'.info/version'), 'r') as vfile:
                vstr = vfile.readline()
                vmaj = int(re.search(r'\d+', vstr).group())
                if vmaj < 6:
                    init_bindings_required = False
        except:
            init_bindings_required = False
        if init_bindings_required:
            self.rocmsmi = initRsmiBindings(silent=False)
        else:
            self.rocmsmi = rocmsmi
        ret = self.rocmsmi.rsmi_init(0)
        if rsmi_status_t.RSMI_STATUS_SUCCESS != ret:
            raise RuntimeError("Failed initializing rocm_smi library")
        device_count = c_uint32(0)
        ret = self.rocmsmi.rsmi_num_monitor_devices(byref(device_count))
        if rsmi_status_t.RSMI_STATUS_SUCCESS != ret:
            raise RuntimeError("Failed enumerating ROCm devices")
        self.device_list = list(range(device_count.value))
        power_value_dict.update({
            f"rocm:{id}" : [] for id in self.device_list
        })
        self.dev_pwr_map = { id: True for id in self.device_list }
        self.start_energy_list = []
        for id in self.device_list:
            energy = c_uint64()
            energy_timestamp = c_uint64()
            energy_resolution = c_float()
            ret = self.rocmsmi.rsmi_dev_energy_count_get(id, 
                    byref(energy),
                    byref(energy_resolution),
                    byref(energy_timestamp))

            if rsmi_status_t.RSMI_STATUS_SUCCESS != ret:
                raise RuntimeError(f"Failed getting energy of device {id}: {ret}")
            if 0 == energy.value:
                self.dev_pwr_map[id] = False
            self.start_energy_list.append(round(energy.value*energy_resolution.value,2)) # unit is uJ
    def measure(self, power_value_dict : dict[str,list[float]]):
        for id in self.device_list:
            power = c_uint64()
            ptype = c_int()

            if not self.dev_pwr_map[id]:
                power.value = 0
            else:
                ret = self.rocmsmi.rsmi_dev_power_get(id, byref(power), byref(ptype))
                if rsmi_status_t.RSMI_STATUS_SUCCESS != ret:
                    raise RuntimeError(f"Failed getting power of device {id}: {ret}")
            power_value_dict[f"rocm:{id}"].append(float(power.value)*1e-6) # value is uW

    def finalize(self, power_value_dict : dict[str,list[float]]):
        energy_list = [0.0 for _ in self.device_list]
        for id in self.device_list:
            energy = c_uint64()
            energy_timestamp = c_uint64()
            energy_resolution = c_float()
            ret = self.rocmsmi.rsmi_dev_energy_count_get(id, 
                    byref(energy),
                    byref(energy_resolution),
                    byref(energy_timestamp))
            
            if rsmi_status_t.RSMI_STATUS_SUCCESS != ret:
                raise RuntimeError(f"Failed getting energy of device {id}")
            energy_list[id] = round(energy.value*energy_resolution.value,2) - self.start_energy_list[id]

        energy_list = [ (energy*1e-6)/3600 for energy in energy_list] # convert uJ to Wh
        self.rocmsmi.rsmi_shut_down()

        return {
            "energy_from_counter": pd.DataFrame({
                f"rocm:{idx}" : [value] for idx,value in zip(self.device_list,energy_list)
            })
        }

