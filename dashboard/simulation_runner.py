"""
Simulation computation — runs the microgrid simulation with progress feedback.
All simulation imports are lazy (inside functions) to keep startup fast.
"""

import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import streamlit as st


def _build_sim(cfg, horizon, bat_cap, dr_alpha, wind_kw, pv_kwp):
    """Build and configure a Simulator from a SystemConfig + overrides."""
    # Late import: engine.simulator triggers model/control imports
    from engine.simulator import Simulator

    sim = Simulator(config=cfg)
    sim.ems_mpc.N = horizon
    sim.battery.capacity_kwh = bat_cap
    sim.dr.alpha_clip = dr_alpha
    sim.wind.rated_power_kw = wind_kw
    sim.pv.area_m2 = 130.0 * (pv_kwp / 20.0)
    return sim


def _run_one_scenario(scenario, cfg, horizon, bat_cap, dr_alpha,
                      wind_kw, pv_kwp, n_hours, df, peak_pen):
    """Run a single scenario with its own Simulator — thread-safe."""
    sim = _build_sim(cfg, horizon, bat_cap, dr_alpha, wind_kw, pv_kwp)
    return sim.run_outer(scenario, n_hours, df, peak_penalty=peak_pen)


def _compute_simulation(bat_cap, dr_alpha, peak_pen, horizon, n_hours,
                        pv_kwp, wind_kw, scenarios_tuple):
    """
    Core computation — no Streamlit commands inside, safe for caching.
    Runs scenarios in parallel via ThreadPoolExecutor.
    Returns (results_dict, kpi_table_dict, df, bat_sens, dr_sens).
    """
    # Late imports: simulation modules (TensorFlow etc. kept out of critical path)
    from engine.simulator import Simulator
    from analysis.kpi_calculator import compare_scenarios, compute_all
    from config import (
        SystemConfig, PVConfig, WindConfig, BatteryConfig,
        MPCConfig, DRConfig, SimulationConfig,
    )

    pv_cfg = PVConfig(capacity_kwp=float(pv_kwp))
    wind_cfg = WindConfig(rated_power_kw=float(wind_kw))
    bat_cfg = BatteryConfig(capacity_kwh=float(bat_cap))
    mpc_cfg = MPCConfig(np_outer=horizon)
    dr_cfg = DRConfig(alpha_clip=dr_alpha)
    sim_cfg = SimulationConfig(n_hours=n_hours)
    cfg = SystemConfig(pv=pv_cfg, wind=wind_cfg, battery=bat_cfg,
                       mpc=mpc_cfg, dr=dr_cfg, sim=sim_cfg)

    # Build a template sim to generate shared data
    sim = _build_sim(cfg, horizon, bat_cap, dr_alpha, wind_kw, pv_kwp)
    df = sim.dg.generate_all(n_hours)

    # ── Parallel scenario execution ─────────────────────────────────
    results = {}
    n_scenarios = len(scenarios_tuple)
    max_workers = min(n_scenarios, 4)  # cap at 4 to avoid over-subscription

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        fut_map = {
            pool.submit(
                _run_one_scenario, s, cfg, horizon, bat_cap, dr_alpha,
                wind_kw, pv_kwp, n_hours, df, peak_pen,
            ): s for s in scenarios_tuple
        }
        for future in as_completed(fut_map):
            s = fut_map[future]
            try:
                results[s] = future.result()
            except Exception as e:
                # Fall back to sequential for this scenario on failure
                results[s] = _run_one_scenario(
                    s, cfg, horizon, bat_cap, dr_alpha,
                    wind_kw, pv_kwp, n_hours, df, peak_pen,
                )

    kpi_table = compare_scenarios(results)
    for s, r in results.items():
        if s not in kpi_table:
            continue
        lam = r.lambda_dr
        kpi_table[s]['Avg_l_DR'] = float(np.mean(lam)) if len(lam) > 0 else 0.0
        kpi_table[s]['Total_DR'] = float(np.sum(r.p_dr))
        kpi_table[s]['Peak_Grid'] = float(np.max(r.p_grid))

    # ── Sensitivity analysis — sweep for EVERY selected scenario ────
    bat_sens = {}
    dr_sens = {}
    for sc in scenarios_tuple:
        sim_s = _build_sim(cfg, horizon, bat_cap, dr_alpha, wind_kw, pv_kwp)
        df_s = sim_s.dg.generate_all(n_hours)

        bat_results = {}
        for cap in [25, 50, 75, 100]:
            sim_s.battery.capacity_kwh = cap
            r = sim_s.run_outer(sc, n_hours, df_s, peak_penalty=peak_pen)
            bat_results[f'{cap}kWh'] = compute_all(r)
        bat_sens[sc] = bat_results

        dr_results = {}
        for ratio in [0.10, 0.15, 0.20, 0.25]:
            sim_s.dr.alpha_clip = ratio
            r = sim_s.run_outer(sc, n_hours, df_s, peak_penalty=peak_pen)
            dr_results[f'{ratio:.0%}'] = compute_all(r)
        dr_sens[sc] = dr_results

    return results, kpi_table, df, bat_sens, dr_sens


@st.cache_data(show_spinner=False)
def _cached_compute(bat_cap, dr_alpha, peak_pen, horizon, n_hours,
                    pv_kwp, wind_kw, scenarios_tuple, _run_key):
    """Cached wrapper so results survive Streamlit reruns."""
    return _compute_simulation(bat_cap, dr_alpha, peak_pen, horizon,
                               n_hours, pv_kwp, wind_kw, scenarios_tuple)


def _run_with_progress(params):
    """
    Run simulation + sensitivity + Monte Carlo with a real progress bar.
    Stores results directly into st.session_state.
    """
    scenarios = tuple(params['selected_scenarios'])
    mc_enabled = params.get('mc_enabled', False) and params.get('mc_runs', 0) > 0
    mc_n = params.get('mc_runs', 20) if mc_enabled else 0
    total_steps = len(scenarios) + 3 + (1 if mc_enabled else 0)
    progress = st.progress(0, text='Initializing...')
    status = st.empty()

    try:
        status.info('Generating data...')
        progress.progress(1 / total_steps, text='Generating data...')

        results, kpi_table, df, bat_sens, dr_sens = _cached_compute(
            params['bat_cap'], params['dr_alpha'], params['peak_pen'],
            params['horizon'], params['n_hours'],
            params['pv_kwp'], params['wind_kw'], scenarios,
            st.session_state._run_key,
        )

        mc_data = None
        if mc_enabled:
            step = (total_steps - 1) / total_steps
            progress.progress(step, text='Monte Carlo simulation...')
            status.info(f'Running {mc_n} MC iterations...')
            mc_costs = []
            mc_res = []
            for i in range(mc_n):
                from forecasting.data_generator import DataGenerator
                from engine.simulator import Simulator
                sim_mc = Simulator()
                sim_mc.ems_mpc.N = params['horizon']
                sim_mc.battery.capacity_kwh = params['bat_cap']
                sim_mc.dr.alpha_clip = params['dr_alpha']
                sim_mc.dg = DataGenerator(seed=42 + i)
                df_mc = sim_mc.dg.generate_all(params['n_hours'])
                r = sim_mc.run_outer(scenarios[0], params['n_hours'], df_mc,
                                     peak_penalty=params['peak_pen'])
                cost = float(np.sum(r.cost))
                mc_costs.append(cost)
                mc_res.append(r)
                frac = step + (1 - step) * (i + 1) / mc_n
                progress.progress(min(frac, 0.99),
                                  text=f'MC run {i + 1}/{mc_n} - ${cost:.1f}')

            mc_data = {'costs': mc_costs, 'results': mc_res, 'n': mc_n}
            status.success(f'MC complete - {mc_n} runs')
            progress.progress(0.995, text='Finalizing...')

        progress.progress(1.0, text='Complete!')
        status.empty()

        st.session_state.results = results
        st.session_state.kpi_table = kpi_table
        st.session_state.df = df
        st.session_state.bat_sens = bat_sens
        st.session_state.dr_sens = dr_sens
        st.session_state.mc_data = mc_data
        st.session_state._last_params = _param_hash(params)
        st.session_state._has_run = True
        st.rerun()

    except Exception as e:
        progress.empty()
        status.error(f'Simulation failed: {e}')
        st.exception(e)
        st.stop()


def _param_hash(params):
    """Deterministic hash of current parameters for change detection."""
    raw = f'{params["bat_cap"]}_{params["dr_alpha"]}_{params["peak_pen"]}_' \
          f'{params["horizon"]}_{params["n_hours"]}_{params["pv_kwp"]}_' \
          f'{params["wind_kw"]}_{params["selected_scenarios"]}'
    return hashlib.md5(raw.encode()).hexdigest()
