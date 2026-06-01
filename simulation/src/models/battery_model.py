import numpy as np

class BatteryModel:
    def __init__(self, capacity_kwh: float = 50.0, soc_init: float = 0.50,
                 soc_min: float = 0.20, soc_max: float = 0.90,
                 eta_ch: float = 0.95, eta_dch: float = 0.95,
                 p_ch_max_kw: float = 25.0, p_dch_max_kw: float = 25.0):
        self.capacity_kwh = capacity_kwh
        self.soc = soc_init
        self.soc_min = soc_min
        self.soc_max = soc_max
        self.eta_ch = eta_ch
        self.eta_dch = eta_dch
        self.p_ch_max_kw = p_ch_max_kw
        self.p_dch_max_kw = p_dch_max_kw

    def update_soc(self, p_bat_kw: float, dt_s: float) -> float:
        delta_energy = 0.0
        if p_bat_kw > 0:
            delta_energy = -p_bat_kw * dt_s / 3600 / self.eta_dch
        elif p_bat_kw < 0:
            delta_energy = -p_bat_kw * dt_s / 3600 * self.eta_ch
        self.soc += delta_energy / self.capacity_kwh
        self.soc = np.clip(self.soc, self.soc_min, self.soc_max)
        return self.soc

    def get_constraints(self) -> dict:
        return {
            'soc_min': self.soc_min,
            'soc_max': self.soc_max,
            'p_ch_max': self.p_ch_max_kw,
            'p_dch_max': self.p_dch_max_kw,
        }
