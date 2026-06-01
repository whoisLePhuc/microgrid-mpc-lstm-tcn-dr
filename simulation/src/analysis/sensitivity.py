import numpy as np
from engine.simulator import Simulator
from analysis.kpi_calculator import compute_all

class SensitivityAnalysis:
    def __init__(self, df=None):
        self.sim = Simulator()
        self.shared_df = df

    def _get_df(self):
        return self.shared_df if self.shared_df is not None else self.sim.dg.generate_all(168)

    def battery_capacity(self, capacities=[25, 50, 75, 100]):
        df = self._get_df()
        results = {}
        for cap in capacities:
            self.sim.battery.capacity_kwh = cap
            r = self.sim.run_outer('S5', 168, df)
            results[f'Bat{cap}kWh'] = compute_all(r)
        return results

    def dr_ratio(self, ratios=[0.10, 0.15, 0.20, 0.25]):
        df = self._get_df()
        results = {}
        for ratio in ratios:
            self.sim.dr.alpha_clip = ratio
            r = self.sim.run_outer('S5', 168, df)
            results[f'DR{ratio:.0%}'] = compute_all(r)
        return results

    def forecast_error(self, noise_levels=[0, 0.05, 0.10, 0.20]):
        df = self._get_df()
        results = {}
        for noise in noise_levels:
            r = self.sim.run_outer('S5', 168, df)
            noisy_load = r.load + np.random.normal(0, noise * np.mean(r.load), len(r.load))
            results[f'Err{noise:.0%}'] = compute_all(r)
        return results
