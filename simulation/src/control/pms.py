import numpy as np

class PMS:
    def __init__(self, config=None):
        self.soc_charge_stop = 0.85; self.soc_charge_resume = 0.80
        self.soc_discharge_stop = 0.30; self.soc_discharge_resume = 0.35
        self.hysteresis_power = 0.05 * 30; self.prev_mode = 3
        if config is not None:
            bat = config.battery
            self.soc_charge_stop = bat.soc_max * 0.95
            self.soc_charge_resume = self.soc_charge_stop - 0.05
            self.soc_discharge_stop = bat.soc_min + 0.10
            self.soc_discharge_resume = self.soc_discharge_stop + 0.05

    def select_mode(self, p_net, soc, is_onpeak, is_offpeak):
        diff = self.hysteresis_power
        p_eff = p_net + diff if self.prev_mode in [1, 2, 3] else p_net - diff
        if p_eff < 0:
            if soc < self.soc_charge_stop:
                self.prev_mode = 1; return (1, 'M1_Charge')
            elif is_offpeak:
                self.prev_mode = 2; return (2, 'M2_ValleyFill')
            else:
                self.prev_mode = 3; return (3, 'M3_Export')
        else:
            if soc > self.soc_discharge_stop:
                if is_onpeak:
                    self.prev_mode = 4; return (4, 'M4_PeakClip')
                else:
                    self.prev_mode = 5; return (5, 'M5_Discharge')
            else:
                self.prev_mode = 6; return (6, 'M6_Import')

    def compute_references(self, mode, p_surplus, p_deficit, p_pv, p_wind):
        r = {'p_bat_ref': 0., 'p_grid_ref': 0., 'p_dr_ref': 0.}
        if mode == 1:
            p_bat = min(p_surplus, 25)
            r['p_bat_ref'] = -p_bat
            r['p_grid_ref'] = max(p_surplus - p_bat, 0)
        elif mode == 2:
            r['p_bat_ref'] = -5
            r['p_grid_ref'] = p_surplus + 5
            r['p_dr_ref'] = -0.10 * (p_pv + p_wind)
        elif mode == 3:
            r['p_grid_ref'] = p_surplus
        elif mode == 4:
            p_bat = min(p_deficit, 25)
            r['p_bat_ref'] = p_bat
            r['p_grid_ref'] = max(p_deficit - p_bat, 0)
            r['p_dr_ref'] = 0.15 * (p_pv + p_wind + p_bat)
        elif mode == 5:
            p_bat = min(p_deficit, 25)
            r['p_bat_ref'] = p_bat
            r['p_grid_ref'] = max(p_deficit - p_bat, 0)
        elif mode == 6:
            r['p_grid_ref'] = p_deficit
        return r

    @staticmethod
    def smooth_transition(old, new, k, k0, z=0.5, delta=3):
        out = {}
        for key in old:
            f = 1 / (1 + np.exp(-z * (k - k0 - delta)))
            out[key] = old[key] + (new[key] - old[key]) * f
        return out
