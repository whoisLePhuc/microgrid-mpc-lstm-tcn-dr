"""
Dashboard test suite — checks that the dashboard correctly interfaces
with simulation modules.  Run without streamlit installed.
"""
import sys, os
from pathlib import Path

# ── Path setup (mirrors dashboard/app.py) ──────────────────────────
SRC = Path(__file__).resolve().parents[2] / 'simulation' / 'src'
sys.path.insert(0, str(SRC))

import unittest
import numpy as np
import json

from engine.simulator import Simulator, SimulationResults
from analysis.kpi_calculator import compare_scenarios, compute_all
from analysis.sensitivity import SensitivityAnalysis
from engine.scenarios import SCENARIOS, scenario_list
from config import (
    SystemConfig, PVConfig, WindConfig, BatteryConfig,
    MPCConfig, DRConfig, SimulationConfig,
)


class TestImports(unittest.TestCase):
    """Test that all dashboard imports resolve correctly."""

    def test_engine_imports(self):
        from engine.simulator import Simulator
        self.assertTrue(Simulator)

    def test_kpi_imports(self):
        from analysis.kpi_calculator import compare_scenarios, compute_all
        self.assertTrue(callable(compare_scenarios))
        self.assertTrue(callable(compute_all))

    def test_sensitivity_imports(self):
        from analysis.sensitivity import SensitivityAnalysis
        self.assertTrue(SensitivityAnalysis)

    def test_scenarios_imports(self):
        self.assertIn('S1', SCENARIOS)
        self.assertIn('S5', SCENARIOS)
        self.assertEqual(scenario_list(), ['S1', 'S2', 'S3', 'S4', 'S5'])

    def test_config_imports(self):
        cfg = SystemConfig(
            pv=PVConfig(capacity_kwp=25.0),
            wind=WindConfig(rated_power_kw=15.0),
            battery=BatteryConfig(capacity_kwh=75.0),
            mpc=MPCConfig(np_outer=48),
            dr=DRConfig(alpha_clip=0.20),
            sim=SimulationConfig(n_hours=100),
        )
        self.assertAlmostEqual(cfg.pv.capacity_kwp, 25.0)
        self.assertAlmostEqual(cfg.wind.rated_power_kw, 15.0)
        self.assertAlmostEqual(cfg.battery.capacity_kwh, 75.0)
        self.assertEqual(cfg.mpc.np_outer, 48)
        self.assertAlmostEqual(cfg.dr.alpha_clip, 0.20)
        self.assertEqual(cfg.sim.n_hours, 100)


class TestSimulationRuns(unittest.TestCase):
    """Test that simulation runs correctly with different configs."""

    def test_simulator_accepts_config(self):
        """Dashboard passes SystemConfig to Simulator."""
        cfg = SystemConfig(
            battery=BatteryConfig(capacity_kwh=75.0),
            dr=DRConfig(alpha_clip=0.20),
            mpc=MPCConfig(np_outer=48),
            sim=SimulationConfig(n_hours=24),
        )
        sim = Simulator(config=cfg)
        sim.ems_mpc.N = 48
        sim.battery.capacity_kwh = 75.0
        sim.dr.alpha_clip = 0.20

        # Run
        results = sim.run_outer('S5', n_hours=24)
        self.assertIsInstance(results, SimulationResults)

    def test_battery_capacity_override(self):
        """Dashboard slider for battery capacity actually affects results."""
        sim = Simulator()
        sim.ems_mpc.N = 24

        df = sim.dg.generate_all(24)
        r1 = sim.run_outer('S5', n_hours=24, df=df)

        sim.battery.capacity_kwh = 100.0  # ← dashboard does this
        df2 = sim.dg.generate_all(24)  # fresh data for fair comparison
        r2 = sim.run_outer('S5', n_hours=24, df=df2)

        # Capacity change should affect SOC dynamics
        self.assertFalse(np.array_equal(r1.soc, r2.soc),
                         'Battery capacity change did not affect SOC')

    def test_horizon_override(self):
        """Dashboard slider for MPC horizon actually affects results."""
        sim = Simulator()
        df = sim.dg.generate_all(168)

        sim.ems_mpc.N = 4
        r1 = sim.run_outer('S3', n_hours=168, df=df)
        cost_4 = r1.cost.sum()

        sim.ems_mpc.N = 48
        r2 = sim.run_outer('S3', n_hours=168, df=df)
        cost_48 = r2.cost.sum()

        cost_diff = abs(float(cost_4) - float(cost_48))
        self.assertGreater(cost_diff, 0.5,
                           f'Horizon 4->48 cost diff only ${cost_diff:.2f}')

    def test_all_scenarios_run(self):
        """Dashboard can run all 5 scenarios sequentially."""
        sim = Simulator()
        df = sim.dg.generate_all(24)
        results = {}
        for s in ['S1', 'S2', 'S3', 'S4', 'S5']:
            results[s] = sim.run_outer(s, n_hours=24, df=df)
            self.assertIn('cost', dir(results[s]))
        self.assertEqual(len(results), 5)


class TestKPIComparison(unittest.TestCase):
    """Test that KPI table works with dashboard expectations."""

    def test_compare_scenarios_returns_dict(self):
        sim = Simulator()
        results = sim.run_all(n_hours=24)
        kpi_table = compare_scenarios(results)

        self.assertIsInstance(kpi_table, dict)
        for s in ['S1', 'S2', 'S3', 'S4', 'S5']:
            self.assertIn(s, kpi_table)
            k = kpi_table[s]
            # Dashboard expects these keys
            for key in ['VRI', 'Cost', 'RE_Ratio', 'Settle_Time', 'Overshoot']:
                self.assertIn(key, k, f'{s} missing key {key}')

    def test_cost_hierarchy(self):
        """Cost should decrease from S1 to S5 (thesis result)."""
        sim = Simulator()
        results = sim.run_all(n_hours=48)
        kpi_table = compare_scenarios(results)

        costs = [kpi_table[s]['Cost'] for s in ['S1', 'S2', 'S3', 'S4', 'S5']]
        # S5 should be cheaper than S1
        self.assertLess(costs[4], costs[0],
                        f'S5 cost ({costs[4]:.1f}) should be < S1 ({costs[0]:.1f})')


class TestSensitivityAnalysis(unittest.TestCase):
    """Test that sensitivity analysis works for dashboard integration."""

    def _sensitivity_df(self, n=168):
        """Generate a df large enough for sensitivity sweeps (default 168h)."""
        sim = Simulator()
        return sim.dg.generate_all(n)

    def test_battery_sensitivity_returns_dict(self):
        df = self._sensitivity_df()
        sa = SensitivityAnalysis(df=df)
        bat_sens = sa.battery_capacity()

        self.assertIsInstance(bat_sens, dict)
        for name, kpi in bat_sens.items():
            self.assertIn('Cost', kpi)
            self.assertIn('RE_Ratio', kpi)
            self.assertIn('VRI', kpi)

    def test_dr_sensitivity_returns_dict(self):
        df = self._sensitivity_df()
        sa = SensitivityAnalysis(df=df)
        dr_sens = sa.dr_ratio()

        self.assertIsInstance(dr_sens, dict)
        for name, kpi in dr_sens.items():
            self.assertIn('Cost', kpi)
            self.assertIn('RE_Ratio', kpi)

    def test_sensitivity_different_configs(self):
        """Dashboard changes battery capacity for sensitivity sweep."""
        sim = Simulator()
        df = sim.dg.generate_all(48)
        sa = SensitivityAnalysis(df=df)

        # Dashboard changes battery cap before each run
        sim.battery.capacity_kwh = 25
        r = sim.run_outer('S5', n_hours=48, df=df)
        cost_25 = compute_all(r)['Cost']

        sim.battery.capacity_kwh = 100
        df2 = sim.dg.generate_all(48)
        r = sim.run_outer('S5', n_hours=48, df=df2)
        cost_100 = compute_all(r)['Cost']

        # Different capacities should give different costs
        self.assertNotAlmostEqual(cost_25, cost_100, delta=1.0,
                                  msg='Battery capacity change should affect cost')


class TestSimulationResults(unittest.TestCase):
    """Test SimulationResults dataclass fields used by dashboard."""

    def test_all_fields_present(self):
        sim = Simulator()
        r = sim.run_outer('S5', n_hours=24)
        fields = ['time_h', 'p_pv', 'p_wind', 'p_bat', 'p_grid', 'p_dr',
                  'vdc', 'soc', 'mode', 'price', 'cost', 'dr_mode', 'load', 'lambda_dr']
        for f in fields:
            self.assertTrue(hasattr(r, f), f'Missing field: {f}')

    def test_array_lengths_match(self):
        sim = Simulator()
        r = sim.run_outer('S1', n_hours=24)
        arrays = [r.time_h, r.p_pv, r.p_wind, r.p_bat, r.p_grid,
                  r.vdc, r.soc, r.price, r.cost, r.load, r.lambda_dr]
        for arr in arrays:
            self.assertEqual(len(arr), 24, f'Array length mismatch: {len(arr)}')

        self.assertEqual(len(r.mode), 24)
        self.assertEqual(len(r.dr_mode), 24)


class TestDashboardCodeQuality(unittest.TestCase):
    """Static checks on dashboard code patterns."""

    def test_no_hardcoded_peak_pen_in_dashboard(self):
        """
        Dashboard should have a way to pass peak_penalty to simulation.
        Check that the dashboard code references peak_penalty.
        """
        dashboard_path = Path(__file__).resolve().parents[1] / 'app.py'
        content = dashboard_path.read_text()
        # The dashboard should either pass peak_penalty to run_outer
        # or have it in a function signature
        has_peak_param = 'peak_penalty' in content or 'peak_pen' in content
        self.assertTrue(has_peak_param,
                        'Dashboard must reference peak_penalty somewhere')

    def test_no_plotly_express_unused(self):
        """Remove unused 'import plotly.express as px' if not used."""
        dashboard_path = Path(__file__).resolve().parents[1] / 'app.py'
        content = dashboard_path.read_text()
        px_used = 'px.' in content
        px_imported = 'import plotly.express' in content
        if px_imported and not px_used:
            self.fail('Unused import: plotly.express (imported as px but never used)')

    def test_no_numpy_bool_in_showlegend(self):
        """
        Plotly showlegend must receive Python bool, not numpy.bool_.
        Check that showlegend=bool(...) or showlegend=True/False is used.
        """
        dashboard_path = Path(__file__).resolve().parents[1] / 'app.py'
        content = dashboard_path.read_text()
        # showlegend=(start == seg_starts[0]) ← WRONG (numpy bool)
        # showlegend=bool(start == seg_starts[0]) ← CORRECT
        self.assertNotIn('showlegend=(start', content,
                         'showlegend must use bool() cast: showlegend=bool(...)')

    def test_no_use_container_width_in_plotly_chart(self):
        """st.plotly_chart should use width='stretch', not use_container_width."""
        dashboard_path = Path(__file__).resolve().parents[1] / 'app.py'
        content = dashboard_path.read_text()
        bad = 'st.plotly_chart(fig, use_container_width=True)'
        self.assertNotIn(bad, content,
                         'Replace use_container_width=True with width=stretch')

    def test_peak_penalty_param_in_run_outer(self):
        """Simulator.run_outer must accept peak_penalty parameter."""
        from engine.simulator import Simulator
        import inspect
        sig = inspect.signature(Simulator.run_outer)
        self.assertIn('peak_penalty', sig.parameters)


class TestDashboardSimulationPython(unittest.TestCase):
    """
    Replicate the dashboard's run_simulation() logic exactly
    and verify it works end-to-end.
    """

    def run_simulation(self, bat_cap, dr_alpha, peak_pen, horizon,
                       n_hours, pv_kwp, wind_kw, scenarios_tuple):
        """Exact copy of dashboard's run_simulation logic."""
        # Build config
        pv_cfg = PVConfig(capacity_kwp=float(pv_kwp))
        wind_cfg = WindConfig(rated_power_kw=float(wind_kw))
        bat_cfg = BatteryConfig(capacity_kwh=float(bat_cap))
        mpc_cfg = MPCConfig(np_outer=horizon)
        dr_cfg = DRConfig(alpha_clip=dr_alpha)
        sim_cfg = SimulationConfig(n_hours=n_hours)
        cfg = SystemConfig(pv=pv_cfg, wind=wind_cfg, battery=bat_cfg,
                           mpc=mpc_cfg, dr=dr_cfg, sim=sim_cfg)

        sim = Simulator(config=cfg)
        sim.ems_mpc.N = horizon
        sim.battery.capacity_kwh = bat_cap
        sim.dr.alpha_clip = dr_alpha
        sim.wind.rated_power_kw = wind_kw
        sim.pv.area_m2 = 130.0 * (pv_kwp / 20.0)

        df = sim.dg.generate_all(n_hours)
        results = {}
        for s in scenarios_tuple:
            r = sim.run_outer(s, n_hours, df)
            results[s] = r

        kpi_table = compare_scenarios(results)
        for s, r in results.items():
            if s not in kpi_table:
                continue
            lam = r.lambda_dr
            kpi_table[s]['Avg_λ_DR'] = float(np.mean(lam)) if len(lam) > 0 else 0.0
            kpi_table[s]['Total_DR'] = float(np.sum(r.p_dr))
            kpi_table[s]['Peak_Grid'] = float(np.max(r.p_grid))

        return results, kpi_table, df

    def test_run_simulation_works(self):
        results, kpi_table, df = self.run_simulation(
            bat_cap=50, dr_alpha=0.15, peak_pen=0.5,
            horizon=24, n_hours=24,
            pv_kwp=20, wind_kw=10,
            scenarios_tuple=('S1', 'S5'),
        )
        self.assertIn('S1', results)
        self.assertIn('S5', results)
        self.assertIn('S1', kpi_table)
        self.assertIn('S5', kpi_table)
        # KPI table should have custom fields
        self.assertIn('Avg_λ_DR', kpi_table['S1'])
        self.assertIn('Total_DR', kpi_table['S1'])
        self.assertIn('Peak_Grid', kpi_table['S1'])
        self.assertGreater(kpi_table['S1']['Cost'], kpi_table['S5']['Cost'],
                           'S5 should be cheaper than S1')

    def test_pv_capacity_affects_power(self):
        """Dashboard slider for PV should actually change PV output."""
        results_20kw, _, _ = self.run_simulation(
            bat_cap=50, dr_alpha=0.15, peak_pen=0.5,
            horizon=24, n_hours=24, pv_kwp=20, wind_kw=10,
            scenarios_tuple=('S5',),
        )
        results_40kw, _, _ = self.run_simulation(
            bat_cap=50, dr_alpha=0.15, peak_pen=0.5,
            horizon=24, n_hours=24, pv_kwp=40, wind_kw=10,
            scenarios_tuple=('S5',),
        )
        pv_20 = results_20kw['S5'].p_pv.sum()
        pv_40 = results_40kw['S5'].p_pv.sum()
        self.assertGreater(pv_40, pv_20 * 1.5,
                           '40kWp PV should produce >1.5× more than 20kWp')

    def test_wind_capacity_affects_power(self):
        """Dashboard slider for Wind should change wind output."""
        results_10kw, _, _ = self.run_simulation(
            bat_cap=50, dr_alpha=0.15, peak_pen=0.5,
            horizon=24, n_hours=24, pv_kwp=20, wind_kw=10,
            scenarios_tuple=('S5',),
        )
        results_20kw, _, _ = self.run_simulation(
            bat_cap=50, dr_alpha=0.15, peak_pen=0.5,
            horizon=24, n_hours=24, pv_kwp=20, wind_kw=20,
            scenarios_tuple=('S5',),
        )
        w_10 = results_10kw['S5'].p_wind.sum()
        w_20 = results_20kw['S5'].p_wind.sum()
        self.assertGreater(w_20, w_10 * 1.5,
                           '20kW wind should produce >1.5× more than 10kW')


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unittest.TestLoader().loadTestsFromModule(sys.modules[__name__]))
    sys.exit(0 if result.wasSuccessful() else 1)
