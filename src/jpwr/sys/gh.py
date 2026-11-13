import os

import pandas as pd


class power(object):
    hwmon_base = "/sys/class/hwmon/"
    def init(self, power_value_dict : dict[str,list[float]]):
        # sort by hwmon number
        self.hwmons = sorted(os.listdir(self.hwmon_base),key=lambda x: int(x[5:]))
        for hwmon in self.hwmons:
            hwmon_path = os.path.join(self.hwmon_base, hwmon)
            oem_path = os.path.join(hwmon_path, "power1_oem_info")
            if not os.path.exists(oem_path):
                continue
            with open(oem_path, 'r') as oem_fd:
                name = oem_fd.read()
                name = name.strip()

            power_value_dict[f"gh:{name}"] = []
    def measure(self, power_value_dict : dict[str,list[float]]):
        for hwmon in self.hwmons:
            hwmon_path = os.path.join(self.hwmon_base, hwmon)
            oem_path = os.path.join(hwmon_path, "power1_oem_info")
            if not os.path.exists(oem_path):
                continue
            with open(oem_path, 'r') as oem_fd:
                name = oem_fd.read()
                name = name.strip()
            power_path = os.path.join(hwmon_path, "power1_average")
            with open(power_path) as power_fd:
                value = 1e-6*float(power_fd.read())

            power_value_dict[f"gh:{name}"].append(value)

    def finalize(self, power_value_dict : dict[str,list[float]]):
        return {}
