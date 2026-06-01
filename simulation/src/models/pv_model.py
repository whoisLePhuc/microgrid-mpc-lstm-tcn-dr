import numpy as np

class PVModel:
    def __init__(self, n_series: int = 20, n_parallel: int = 4):
        self.n_series = n_series
        self.n_parallel = n_parallel
        self.n_modules = n_series * n_parallel
        self.pmax_module = 250.0
        self.capacity_kwp = 20.0
        self.iph_ref = 7.76
        self.io_ref = 1.0e-10
        self.rs = 0.5
        self.rsh = 500.0
        self.n = 1.2
        self.voc_ref = 43.22
        self.mu_voc = -0.30278e-2
        self.mu_isc = 0.035271e-2
        self.area_m2 = 130.0
        self.eta = 0.18

    def compute_power(self, ghi: float, temp_c: float = 25.0,
                      mode: str = 'simplified') -> float:
        if mode == 'simplified':
            return self.eta * self.area_m2 * ghi / 1000
        v_mp_est = self.voc_ref * 0.8
        i_module = self._single_diode_current(v_mp_est, ghi, temp_c)
        p_module = v_mp_est * i_module
        return p_module * self.n_modules / 1000

    def _single_diode_current(self, v: float, ghi: float, temp_c: float) -> float:
        vt = 1.381e-23 * (temp_c + 273.15) / 1.602e-19
        iph = self.iph_ref * ghi / 1000 * (1 + self.mu_isc * (temp_c - 25))
        io = self.io_ref * (temp_c + 273.15) / 298.15 ** 3 * \
             np.exp(1.12 / vt * (1/298.15 - 1/(temp_c + 273.15)))
        i = iph * 0.9
        for _ in range(50):
            vd = v + i * self.rs
            try:
                exp_arg = vd / (self.n * vt)
                if exp_arg > 50:
                    i_new = iph - io * np.exp(50) - vd / self.rsh
                else:
                    i_new = iph - io * (np.exp(exp_arg) - 1) - vd / self.rsh
                if abs(i_new - i) < 1e-6:
                    break
                i = i_new
            except (OverflowError, FloatingPointError):
                i = 0
                break
        return max(i, 0)
