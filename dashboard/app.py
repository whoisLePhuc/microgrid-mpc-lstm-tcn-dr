"""
Microgrid Simulation Dashboard — Streamlit
============================================
Interactive GUI for the PV-Wind-Battery microgrid with MPC + LSTM-TCN + DR.

Usage:
    streamlit run dashboard/app.py

Requires: streamlit, plotly  (pip install streamlit plotly)
"""

import sys
from pathlib import Path

# Path setup: import simulation modules
SRC = Path(__file__).resolve().parents[1] / 'simulation' / 'src'
sys.path.insert(0, str(SRC))

import json
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Local modules
from settings import SCENARIO_LABELS, REPO_ROOT, FORECAST_MODEL_PATH, FORECAST_METRICS_PATH
from settings import FORECAST_TS_IMG, FORECAST_SCATTER_IMG
from components import get_theme, apply_bg_theme, render_sidebar, build_kpi_dataframe, colors
from charts import (
    plot_time_series, plot_kpi_comparison, plot_cost_comparison,
    plot_cost_accumulation, plot_sensitivity, plot_mode_timeline, plot_dr_activation,
)
from simulation_runner import _run_with_progress, _param_hash
from cache import cache_exists, load_session, save_session

# Page config
st.set_page_config(
    page_title='Microgrid MPC + LSTM-TCN + DR',
    page_icon=None,
    layout='wide',
    initial_sidebar_state='expanded',
)


def main():
    get_theme()
    apply_bg_theme()

    params = render_sidebar()

    # Session state init
    for key in ['results', 'kpi_table', 'df', 'bat_sens', 'dr_sens', 'mc_data']:
        if key not in st.session_state:
            st.session_state[key] = None
    if '_run_key' not in st.session_state:
        st.session_state._run_key = 0
    if '_last_params' not in st.session_state:
        st.session_state._last_params = ''
    if '_has_run' not in st.session_state:
        st.session_state._has_run = False

    # Auto-restore cached results on fresh page load
    if not st.session_state._has_run and cache_exists():
        load_session(st.session_state)
        if st.session_state._has_run:
            st.toast('Restored previous results from cache')

    # Params change detection
    current_hash = _param_hash(params)
    params_changed = (
        st.session_state._has_run
        and current_hash != st.session_state._last_params
    )

    # Trigger simulation
    trigger = params['run_btn']
    if params['auto_run'] and params_changed:
        trigger = True

    if trigger:
        st.session_state._run_key += 1
        _run_with_progress(params)

    # Persist results to cache after a successful simulation run
    if st.session_state._has_run and st.session_state.results is not None:
        save_session(st.session_state)

    if params_changed:
        st.sidebar.warning(
            'Parameters changed - click **RUN** again'
            if not params['auto_run'] else 'Auto-running...',
        )

    # Main area
    has_results = st.session_state.results is not None

    if not has_results:
        st.markdown("""
        # MICROGRID SIMULATION DASHBOARD

        PV-Wind-Battery grid-connected microgrid with MPC + LSTM-TCN + Demand Response.

        Adjust parameters in the sidebar and click **RUN SIMULATION** to start.

        | Parameter | Default | Range |
        |-----------|---------|-------|
        | Battery capacity | 50 kWh | 25-100 |
        | DR clip ratio alpha | 0.15 | 0.05-0.30 |
        | Peak penalty | 0.5 | 0.0-1.0 |
        | MPC horizon | 24 h | 12-48 |
        | Simulation duration | 168 h (7 days) | 24-336 |
        | PV capacity | 20 kWp | 10-50 |
        | Wind rated power | 10 kW | 5-20 |
        """)
        return

    results = st.session_state.results or {}
    kpi_table = st.session_state.kpi_table or {}
    bat_sens = st.session_state.bat_sens or {}
    dr_sens = st.session_state.dr_sens or {}

    # KPI Summary bar
    cols = st.columns(len(results))
    for idx, s in enumerate(results):
        k = kpi_table[s]
        delta_cost = kpi_table.get('S1', {}).get('Cost', 0) - k.get('Cost', 0)
        with cols[idx]:
            label = SCENARIO_LABELS.get(s, s)
            st.metric(label=f'{s} - {label}',
                      value=f"${k.get('Cost', 0):.1f}",
                      delta=f"${delta_cost:.1f} vs S1")

    # Check for forecast artifacts
    has_model = FORECAST_MODEL_PATH.exists()

    # Tab list
    mc_tab = params['mc_enabled'] and has_results
    tab_labels = ['Time Series']
    if mc_tab:
        tab_labels.append('Monte Carlo')
    tab_labels += ['Scenario Comparison', 'Sensitivity',
                   'Control Timeline', 'Data', 'Export']
    if has_model:
        tab_labels.insert(1, 'Forecast')

    tabs = st.tabs(tab_labels)

    # Tab offsets
    pos = 0
    T_TS = pos; pos += 1
    T_FC = pos if has_model else None
    if has_model: pos += 1
    T_MC = pos if mc_tab else None
    if mc_tab: pos += 1
    T_SC = pos; pos += 1
    T_SE = pos; pos += 1
    T_CT = pos; pos += 1
    T_DT = pos; pos += 1
    T_EX = pos

    # Tab: Time Series
    with tabs[T_TS]:
        sel = st.multiselect('Select scenarios to overlay',
                             list(results.keys()),
                             default=list(results.keys())[:2],
                             format_func=lambda s: f'{s} - {SCENARIO_LABELS.get(s, s)}')
        if not sel:
            st.warning('Select at least one scenario')
        else:
            st.plotly_chart(plot_time_series(results, sel), width='stretch')

    # Tab: Forecast
    if has_model:
        with tabs[T_FC]:
            st.markdown('### LSTM-TCN Forecast Validation')
            st.info(
                'Comparing LSTM-TCN predictions against actual NASA POWER data '
                'from Da Nang (2021-2023). Model was trained on 75% of the data '
                'and evaluated on 15% held-out test set.'
            )
            if FORECAST_TS_IMG.exists():
                st.image(str(FORECAST_TS_IMG),
                         caption='LSTM-TCN Forecast: PV, Wind, Load - Predicted vs Actual',
                         width='stretch')
            if FORECAST_SCATTER_IMG.exists():
                st.image(str(FORECAST_SCATTER_IMG),
                         caption='Regression Scatter: Predicted vs Actual',
                         width='stretch')

            st.markdown('#### Forecast Accuracy (Test Set)')
            if FORECAST_METRICS_PATH.exists():
                metrics = json.loads(FORECAST_METRICS_PATH.read_text())
                rows = []
                for target, horizons in metrics.items():
                    row = {'Target': target}
                    for horizon, vals in horizons.items():
                        row[f'{horizon} R2'] = vals.get('R2', 0)
                        row[f'{horizon} RMSE'] = vals.get('RMSE', 0)
                    rows.append(row)
                df_m = pd.DataFrame(rows).set_index('Target')
                st.dataframe(df_m.style.highlight_max(
                    axis=0, subset=[c for c in df_m.columns if 'R2' in c]),
                    width='stretch')

    # Tab: Monte Carlo
    if mc_tab:
        with tabs[T_MC]:
            mc_data = st.session_state.get('mc_data')
            if mc_data and mc_data['costs']:
                costs = np.array(mc_data['costs'])
                scenario_label = SCENARIO_LABELS.get(list(results.keys())[0])

                st.markdown(f'### Monte Carlo: {scenario_label}')
                st.info(
                    f'{mc_data["n"]} runs with different random seeds. '
                    f'Each run uses different weather noise (AR1) and load variations.'
                )

                c1, c2, c3, c4 = st.columns(4)
                c1.metric('Mean Cost', f'${np.mean(costs):.1f}')
                c2.metric('Std Dev', f'${np.std(costs):.1f}')
                c3.metric('Min', f'${np.min(costs):.1f}')
                c4.metric('Max', f'${np.max(costs):.1f}')

                c1, c2 = st.columns([2, 1])
                with c1:
                    fig_hist = go.Figure()
                    fig_hist.add_trace(go.Histogram(
                        x=costs, nbinsx=20, marker_color=colors()[0], opacity=0.75))
                    fig_hist.add_vline(x=np.mean(costs), line_dash='dash',
                                       line_color='#E15759',
                                       annotation_text=f'Mean: ${np.mean(costs):.1f}')
                    fig_hist.update_layout(title='Cost Distribution Across Runs',
                                           xaxis_title='Total Cost ($)',
                                           yaxis_title='Frequency', height=350)
                    st.plotly_chart(fig_hist, width='stretch')

                    cum_avg = np.cumsum(costs) / (np.arange(len(costs)) + 1)
                    fig_conv = go.Figure()
                    fig_conv.add_trace(go.Scatter(y=cum_avg, mode='lines',
                                                  line=dict(color=colors()[1]),
                                                  name='Running average'))
                    fig_conv.add_hline(y=np.mean(costs), line_dash='dot', line_color='#E15759')
                    fig_conv.update_layout(title='Convergence of Mean Cost',
                                           xaxis_title='Run #',
                                           yaxis_title='Cumulative Average Cost ($)',
                                           height=300)
                    st.plotly_chart(fig_conv, width='stretch')

                with c2:
                    st.markdown('**Percentiles**')
                    st.dataframe(pd.DataFrame({
                        'Percentile': ['5%', '25%', '50%', '75%', '95%'],
                        'Cost ($)': [f'${np.percentile(costs, p):.1f}' for p in [5, 25, 50, 75, 95]],
                    }), width='stretch')
                    st.markdown('**Runs**')
                    st.dataframe(pd.DataFrame({
                        'Run': [f'#{i + 1}' for i in range(len(costs))],
                        'Cost ($)': [f'${c:.1f}' for c in costs],
                    }), width='stretch', height=300)

    # Tab: Scenario Comparison
    with tabs[T_SC]:
        c1, c2 = st.columns([2, 1])
        with c1:
            st.plotly_chart(plot_kpi_comparison(kpi_table), width='stretch')
            st.plotly_chart(plot_cost_comparison(results), width='stretch')
            st.plotly_chart(plot_cost_accumulation(results), width='stretch')
        with c2:
            st.markdown('### KPI Table')
            st.dataframe(build_kpi_dataframe(kpi_table), width='stretch')
            st.markdown('### Interpretation')
            s5_cost = kpi_table.get('S5', {}).get('Cost', 0)
            s1_cost = kpi_table.get('S1', {}).get('Cost', 0)
            saving = ((s1_cost - s5_cost) / s1_cost * 100) if s1_cost else 0
            st.info(
                f'S5 (Full DR) achieves **${s5_cost:.1f}** total cost, '
                f'a **{saving:.1f}%** reduction from S1 baseline.'
            )

    # Tab: Sensitivity
    with tabs[T_SE]:
        if bat_sens:
            sens_sc = st.selectbox('Select scenario', list(bat_sens.keys()),
                                   key='sens_sc',
                                   format_func=lambda s: f'{s} - {SCENARIO_LABELS.get(s, s)}')
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(plot_sensitivity(bat_sens[sens_sc], 'Battery Capacity (kWh)'),
                                width='stretch')
                st.caption('Sweeping battery capacity 25-100 kWh. Optimal around 75 kWh.')
            with c2:
                st.plotly_chart(plot_sensitivity(dr_sens[sens_sc], 'DR Ratio alpha'),
                                width='stretch')
                st.caption('Sweeping DR clip ratio 10%-25%. Higher alpha reduces cost.')
        else:
            st.warning('Run simulation to see sensitivity analysis.')

    # Tab: Control Timeline
    with tabs[T_CT]:
        sel2 = st.selectbox('Select scenario', list(results.keys()), key='timeline_sel',
                            format_func=lambda s: f'{s} - {SCENARIO_LABELS.get(s, s)}')
        st.plotly_chart(plot_mode_timeline(results[sel2]), width='stretch')
        st.plotly_chart(plot_dr_activation(results[sel2]), width='stretch')

        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            modes = np.array(results[sel2].mode)
            mode_counts = {f'M{m}': int(np.sum(modes == m)) for m in range(1, 7)}
            fig_pie = go.Figure(data=[go.Pie(
                labels=['M1: Charge', 'M2: ValleyFill', 'M3: Export',
                        'M4: PeakClip', 'M5: Discharge', 'M6: Import'],
                values=[mode_counts[f'M{m}'] for m in range(1, 7)],
                marker_colors=['#4E79A7', '#F28E2B', '#59A14F',
                               '#E15759', '#B07AA1', '#8C564B'],
                hole=0.4)])
            fig_pie.update_layout(title='PMS Mode Distribution', height=400)
            st.plotly_chart(fig_pie, width='stretch')

    # Tab: Data
    with tabs[T_DT]:
        st.markdown('### Raw KPI Data')
        st.dataframe(build_kpi_dataframe(kpi_table), width='stretch')

        sel3 = st.selectbox('Select scenario for raw data', list(results.keys()),
                            key='data_sel',
                            format_func=lambda s: f'{s} - {SCENARIO_LABELS.get(s, s)}')
        r = results[sel3]
        raw_df = pd.DataFrame({
            'Hour': np.arange(len(r.time_h)), 'Day': np.arange(len(r.time_h)) / 24.0,
            'PV (kW)': r.p_pv, 'Wind (kW)': r.p_wind,
            'Battery (kW)': r.p_bat, 'Grid (kW)': r.p_grid,
            'DR (kW)': r.p_dr, 'SOC (%)': r.soc * 100,
            'VDC (V)': r.vdc, 'Price ($)': r.price,
            'Cost ($)': r.cost, 'Mode': r.mode, 'DR Mode': r.dr_mode,
        })
        st.dataframe(raw_df, width='stretch', height=400)
        csv = raw_df.to_csv(index=False).encode('utf-8')
        st.download_button(label='Download CSV', data=csv,
                           file_name=f'{sel3}_results.csv', mime='text/csv')

    # Tab: Export
    with tabs[T_EX]:
        st.markdown('### Export All Results')

        kpi_json = json.dumps(kpi_table, indent=2, default=str).encode('utf-8')

        all_rows = []
        for s, r in results.items():
            for i in range(len(r.time_h)):
                all_rows.append({
                    'Scenario': s, 'Hour': int(r.time_h[i]),
                    'Day': r.time_h[i] / 24.0,
                    'PV_kW': float(r.p_pv[i]), 'Wind_kW': float(r.p_wind[i]),
                    'Battery_kW': float(r.p_bat[i]), 'Grid_kW': float(r.p_grid[i]),
                    'DR_kW': float(r.p_dr[i]), 'SOC_pct': float(r.soc[i] * 100),
                    'VDC_V': float(r.vdc[i]), 'Price_per_kWh': float(r.price[i]),
                    'Cost_$': float(r.cost[i]), 'Mode': int(r.mode[i]),
                    'DR_Mode': r.dr_mode[i],
                })
        combined_csv = pd.DataFrame(all_rows).to_csv(index=False).encode('utf-8')

        cl, cr = st.columns(2)
        cl.download_button('Download KPI JSON', data=kpi_json,
                           file_name='kpi_results.json', mime='application/json',
                           use_container_width=True)
        cr.download_button('Download All CSV', data=combined_csv,
                           file_name='all_scenarios.csv', mime='text/csv',
                           use_container_width=True)

        st.markdown('---')
        st.markdown('#### Simulation Parameters')
        st.json({
            'battery_capacity_kwh': params['bat_cap'],
            'dr_alpha': params['dr_alpha'],
            'peak_penalty': params['peak_pen'],
            'mpc_horizon_h': params['horizon'],
            'duration_h': params['n_hours'],
            'pv_capacity_kwp': params['pv_kwp'],
            'wind_power_kw': params['wind_kw'],
            'scenarios': list(params['selected_scenarios']),
        })


if __name__ == '__main__':
    main()
