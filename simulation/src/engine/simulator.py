import numpy as np
from dataclasses import dataclass, field

@dataclass
class SimulationResults:
    scenario: str = ''
    time_h: np.ndarray = field(default_factory=lambda: np.array([]))
    p_pv: np.ndarray = field(default_factory=lambda: np.array([]))
    p_wind: np.ndarray = field(default_factory=lambda: np.array([]))
    p_bat: np.ndarray = field(default_factory=lambda: np.array([]))
    p_grid: np.ndarray = field(default_factory=lambda: np.array([]))
    p_dr: np.ndarray = field(default_factory=lambda: np.array([]))
    vdc: np.ndarray = field(default_factory=lambda: np.array([]))
    soc: np.ndarray = field(default_factory=lambda: np.array([]))
    mode: list = field(default_factory=list)
    price: np.ndarray = field(default_factory=lambda: np.array([]))
    cost: np.ndarray = field(default_factory=lambda: np.array([]))
    dr_mode: list = field(default_factory=list)
    load: np.ndarray = field(default_factory=lambda: np.array([]))
    lambda_dr: np.ndarray = field(default_factory=lambda: np.array([]))

class Simulator:
    def __init__(self, config=None):
        from models.pv_model import PVModel
        from models.wind_model import WindModel
        from models.battery_model import BatteryModel
        from control.pms import PMS
        from control.dr_logic import DRLogic
        from control.ems_mpc import EMSMPC
        from forecasting.data_generator import DataGenerator
        self.pv = PVModel()
        self.wind = WindModel()
        self.battery = BatteryModel()
        self.pms = PMS(config)
        self.dr = DRLogic(config)
        self.dg = DataGenerator()
        self.ems_mpc = EMSMPC(C_kwh=50.0, dt_h=1.0, N=24)
        self.config = config

    def run_outer(self, scenario_name='S5', n_hours=168, df=None, forecast_func=None):
        from engine.scenarios import get_scenario
        sc = get_scenario(scenario_name)
        if df is None:
            df = self.dg.generate_all(n_hours)
        soc = 0.50
        res = SimulationResults(scenario=sc.name)
        t, pv_l, wt_l, ba_l, gr_l, dr_l, vd_l, so_l, mo_l = \
            [], [], [], [], [], [], [], [], []
        pr_l, co_l, dm_l, ld_l, la_l = [], [], [], [], []
        prev = {'p_bat_ref': 0., 'p_grid_ref': 0., 'p_dr_ref': 0.}
        self.pms.prev_mode = 3
        fc_history = []

        for k in range(n_hours):
            row = df.iloc[k]
            p_pv = self.pv.compute_power(row['ghi'], row['temp'])
            p_w = self.wind.compute_power(row['wind'])
            load = row['load']
            if sc.use_tou:
                price = row['price']
            else:
                price = row['price_base']

            # LSTM forecast override
            if forecast_func is not None and k >= 12:
                fc_history.append({
                    'ghi': row['ghi'], 'temp': row['temp'], 'wind': row['wind'],
                    'load': row['load'], 'price': price,
                    'hour_sin': np.sin(2*np.pi*row['hour']/24),
                    'hour_cos': np.cos(2*np.pi*row['hour']/24),
                })
                if len(fc_history) > 12:
                    fc_history.pop(0)
                if len(fc_history) == 12:
                    import pandas as pd
                    fc = forecast_func(pd.DataFrame(fc_history))
                    if fc:
                        p_pv = fc.get('p_pv', p_pv)
                        p_w = fc.get('p_wind', p_w)
                        if sc.use_tou and 'price' in fc:
                            price = fc['price']
                        load = fc.get('load', load)
            p_net = load - p_pv - p_w
            is_on = (13 <= row['hour'] < 18)
            is_off = (row['hour'] >= 22 or row['hour'] < 6)

            # EMS-MPC: optimal battery scheduling over horizon
            if sc.use_mpc:
                horizon = min(self.ems_mpc.N, n_hours - k)
                if horizon >= 4:
                    p_net_fc = np.zeros(horizon)
                    price_fc = np.zeros(horizon)
                    for h in range(horizon):
                        idx = k + h
                        r = df.iloc[idx]
                        ppv = self.pv.compute_power(r['ghi'], r['temp'])
                        pww = self.wind.compute_power(r['wind'])
                        prc = r['price'] if sc.use_tou else r['price_base']
                        p_net_fc[h] = r['load'] - ppv - pww
                        price_fc[h] = prc
                    # TOU: economic arbitrage + peak penalty
                    # Flat: only peak shaving (no price signal)
                    peak_pen = 0.3 if sc.use_tou else 0.5
                    p_bat_opt, info = self.ems_mpc.solve(
                        p_net_fc, price_fc, soc_now=soc,
                        peak_penalty=peak_pen, p_peak=18.0)
                    p_bat_mpc = p_bat_opt[0] if info['status'] == 'solved' else None
                else:
                    p_bat_mpc = None
            else:
                p_bat_mpc = None

            mode, _ = self.pms.select_mode(p_net, soc, is_on, is_off)
            drp = self.dr.compute(p_net, soc, load, price)
            surp = max(-p_net, 0); deficit = max(p_net, 0)
            refs = self.pms.compute_references(mode, surp, deficit, p_pv, p_w)

            # Override battery with MPC optimal when use_mpc
            if p_bat_mpc is not None:
                p_bat = float(np.clip(p_bat_mpc, -25, 25))
            else:
                p_bat = refs['p_bat_ref']

            # Recompute grid power from power balance
            p_dr = refs['p_dr_ref']
            p_grid = load - p_pv - p_w - p_bat - p_dr

            if sc.use_threshold_dr and drp['dr_mode'] in ('PeakClip', 'ValleyFill'):
                p_dr_old = p_dr
                p_dr = drp['p_dr_max']
                p_grid = p_grid - (p_dr - p_dr_old)

            soc = self.battery.update_soc(p_bat, 3600)
            t.append(k); pv_l.append(p_pv); wt_l.append(p_w)
            ba_l.append(p_bat); gr_l.append(p_grid); dr_l.append(p_dr)
            vd_l.append(800 + np.random.normal(0, 5))
            so_l.append(soc); mo_l.append(mode); pr_l.append(price)
            co_l.append(price * p_grid - drp['lambda_dr'] * p_dr)
            dm_l.append(drp['dr_mode']); ld_l.append(load)
            la_l.append(drp['lambda_dr'])

        a = lambda x: np.array(x)
        res.time_h = a(t); res.p_pv = a(pv_l); res.p_wind = a(wt_l)
        res.p_bat = a(ba_l); res.p_grid = a(gr_l); res.p_dr = a(dr_l)
        res.vdc = a(vd_l); res.soc = a(so_l); res.mode = mo_l
        res.price = a(pr_l); res.cost = a(co_l); res.dr_mode = dm_l
        res.load = a(ld_l); res.lambda_dr = a(la_l)
        return res

    def run_all(self, n_hours=168):
        # Generate ONE dataset — all scenarios share the same weather/load/price
        df = self.dg.generate_all(n_hours)
        results = {}
        for s in ['S1', 'S2', 'S3', 'S4', 'S5']:
            print(f'Running {s}...')
            results[s] = self.run_outer(s, n_hours, df)
            print(f'  Cost: {results[s].cost.sum():.1f}, '
                  f'VDC std: {results[s].vdc.std():.1f}')
        return results
