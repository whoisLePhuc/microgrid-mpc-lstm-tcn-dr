import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.simulator import Simulator
from analysis.kpi_calculator import compare_scenarios, compute_all
from analysis.sensitivity import SensitivityAnalysis
from visualization.plots import Plotter


def run_perfect_forecast(sim, outdir):
    """Run S1-S5 with perfect forecast."""
    print('\n[1/5] Running 5 scenarios (perfect forecast)...')
    results = sim.run_all()

    print('\n[2/5] Computing KPIs...')
    kpi_table = compare_scenarios(results)
    print(f'\n{"Scenario":<15} {"VRI(%)":<10} {"Cost($)":<12} {"RE(%)":<10} {"PeakRed(%)":<12}')
    print('-' * 60)
    for s, k in kpi_table.items():
        print(f'{s:<15} {k["VRI"]:<10.2f} {k["Cost"]:<12.1f} {k["RE_Ratio"]:<10.1f} {k["Peak_Red"]:<12.1f}')

    with open(f'{outdir}/kpi_results.json', 'w') as f:
        json.dump(kpi_table, f, indent=2)
    print(f'KPI table saved to {outdir}/kpi_results.json')
    return results, kpi_table


def get_lstm_forecast(model, history_df, feature_cols, scalers):
    """LSTM-TCN predicts next step from recent history."""
    X_min = scalers['X_min']; X_max = scalers['X_max']
    y_min = scalers['y_min']; y_max = scalers['y_max']
    last_12 = history_df[feature_cols].values[-12:].astype(np.float32)
    if len(last_12) < 12:
        return None
    eps = 1e-8
    last_12_s = (last_12 - X_min) / (X_max - X_min + eps)
    y_pred_s = model.predict(last_12_s.reshape(1, 12, -1))
    y_pred = y_pred_s * (y_max - y_min + eps) + y_min
    return {
        'p_pv':   max(float(y_pred[0, 0, 0]), 0),
        'p_wind': max(float(y_pred[0, 0, 1]), 0),
        'load':   max(float(y_pred[0, 0, 3]), 0),
        'price':  max(float(y_pred[0, 0, 4]), 0),
    }


def run_lstm_forecast(sim, outdir, data_path, model_path, kpi_table):
    """Run S1-S5 with LSTM-TCN forecast using Simulator.run_outer(forecast_func=...)."""
    import pandas as pd
    from forecasting.lstm_tcn_model import LSTMTCN

    df = pd.read_csv(data_path, index_col=0, parse_dates=True)
    df = df.iloc[:168]
    if 'hour_sin' not in df.columns:
        hours = df['hour'].values if 'hour' in df.columns else np.arange(len(df)) % 24
        df['hour_sin'] = np.sin(2 * np.pi * hours / 24)
        df['hour_cos'] = np.cos(2 * np.pi * hours / 24)

    scalers = np.load(os.path.join(os.path.dirname(data_path), 'scalers.npz'), allow_pickle=True)
    n_features = int(scalers['n_features'][0])
    n_targets = int(scalers['n_targets'][0])
    input_steps = int(scalers['input_steps'][0])
    horizon = int(scalers['horizon'][0])
    feature_cols = list(scalers['feature_names'])

    model = LSTMTCN(input_steps, n_features, n_targets, horizon)
    model.load(model_path)

    def forecast_func(hist_df):
        return get_lstm_forecast(model, hist_df, feature_cols, scalers)

    print('\n[4/5] Running LSTM-TCN forecast scenarios...')
    results_lstm = {}
    for s in ['S1', 'S2', 'S3', 'S4', 'S5']:
        print(f'  {s} (LSTM forecast)...')
        r = sim.run_outer(s, 168, df, forecast_func=forecast_func)
        results_lstm[s] = r
        print(f'    Cost: {r.cost.sum():.1f}')

    kpi_lstm = {}
    s1_grid = results_lstm['S1'].p_grid if 'S1' in results_lstm else None
    for name, res in results_lstm.items():
        kpi_lstm[name] = compute_all(res, baseline_grid=s1_grid)

    print(f'\n{"Scenario":<15} {"Cost(P)":<10} {"Cost(L)":<10} {"ΔCost%":<10} {"PeakR(P)":<10} {"PeakR(L)":<10}')
    print('-' * 65)
    for s in sorted(kpi_lstm.keys()):
        p = kpi_table.get(s, {})
        l = kpi_lstm.get(s, {})
        cp = p.get('Cost', 0)
        cl = l.get('Cost', 0)
        delta = (cl - cp) / cp * 100 if cp else 0
        print(f'{s:<15} {cp:<10.1f} {cl:<10.1f} {delta:<+10.2f} {p.get("Peak_Red",0):<10.1f} {l.get("Peak_Red",0):<10.1f}')

    out = {'perfect': kpi_table, 'lstm': kpi_lstm}
    with open(f'{outdir}/comparison_perfect_vs_lstm.json', 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f'\n  Saved {outdir}/comparison_perfect_vs_lstm.json')

    # Bar chart
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        sn_map = {'S1':'Rule-based','S2':'EMS-MPC','S3':'MPC+TOU','S4':'Threshold DR','S5':'Full DR'}
        scenarios = sorted(kpi_table.keys())
        snames = [sn_map[s] for s in scenarios]
        cost_p = [kpi_table[s]['Cost'] for s in scenarios]
        cost_l = [kpi_lstm[s]['Cost'] for s in scenarios]
        fig, ax = plt.subplots(figsize=(10, 5))
        x = np.arange(len(scenarios)); w = 0.35
        ax.bar(x - w/2, cost_p, w, label='Perfect Forecast', color='steelblue')
        ax.bar(x + w/2, cost_l, w, label='LSTM-TCN Forecast', color='coral')
        ax.set_xticks(x); ax.set_xticklabels(snames, rotation=30, ha='right')
        ax.set_ylabel('Total Cost ($)')
        ax.set_title('Perfect vs LSTM-TCN Forecast: Cost Comparison')
        ax.legend(); ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(f'{outdir}/comparison_perfect_vs_lstm.png', bbox_inches='tight', dpi=150)
        plt.close()
        print(f'  Saved {outdir}/comparison_perfect_vs_lstm.png')
    except Exception as e:
        print(f'  Plot skipped: {e}')

    return results_lstm, kpi_lstm


def main():
    import numpy as np
    print('=' * 60)
    print('Microgrid Simulation: PV-Wind-Battery with MPC + DR')
    print('=' * 60)

    script_dir = os.path.join(os.path.dirname(__file__), '..', 'scripts')
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    outdir = os.path.join(os.path.dirname(__file__), '..', 'outputs', 'figures')
    os.makedirs(outdir, exist_ok=True)

    sim = Simulator()

    # Part 1: Perfect forecast scenarios
    results, kpi_table = run_perfect_forecast(sim, outdir)

    # Part 2: Sensitivity analysis (dùng chung dataset với main)
    print('\n[3/5] Sensitivity analysis...')
    shared_df = sim.dg.generate_all(168)
    sa = SensitivityAnalysis(df=shared_df)
    print('  Battery capacity sweep...')
    bat_sens = sa.battery_capacity()
    print('  DR ratio sweep...')
    dr_sens = sa.dr_ratio()

    # Part 3: LSTM forecast comparison (if model exists)
    data_path = os.path.join(data_dir, 'raw_data_2021_2023.csv')
    model_path = os.path.join(model_dir, 'lstm_tcn_model.keras')
    if os.path.exists(model_path) and os.path.exists(data_path):
        run_lstm_forecast(sim, outdir, data_path, model_path, kpi_table)

    # Part 4: Generate plots
    print('\n[5/5] Generating plots...')
    plotter = Plotter()
    plotter.plot_scenario_comparison(kpi_table, f'{outdir}/kpi_comparison.png')
    plotter.plot_time_series(results['S5'], f'{outdir}/time_series_s5.png')
    plotter.plot_cost_comparison(results, f'{outdir}/cost_bar.png')
    plotter.plot_sensitivity(bat_sens, 'Battery Capacity', f'{outdir}/bat_sensitivity.png')
    plotter.plot_sensitivity(dr_sens, 'DR Ratio', f'{outdir}/dr_sensitivity.png')

    # NEW plots for thesis
    plotter.plot_cost_accumulation(results, f'{outdir}/cost_accumulation.png')
    plotter.plot_load_profile_dr(results['S1'], results['S5'], f'{outdir}/load_profile_dr.png')
    plotter.plot_mode_timeline(results['S5'], f'{outdir}/mode_timeline.png')
    plotter.plot_soc_comparison(results, f'{outdir}/soc_comparison.png')
    plotter.plot_dr_activation(results['S5'], f'{outdir}/dr_activation.png')

    # Forecast validation plot (uses LSTM model + NASA POWER data)
    if os.path.exists(model_path) and os.path.exists(data_path):
        try:
            import pandas as pd
            from forecasting.lstm_tcn_model import LSTMTCN
            df_v = pd.read_csv(data_path, index_col=0, parse_dates=True)
            scalers_v = np.load(os.path.join(os.path.dirname(data_path), 'scalers.npz'), allow_pickle=True)
            nf = int(scalers_v['n_features'][0])
            nt = int(scalers_v['n_targets'][0])
            ins = int(scalers_v['input_steps'][0])
            hrz = int(scalers_v['horizon'][0])
            fcols = list(scalers_v['feature_names'])
            mdl = LSTMTCN(ins, nf, nt, hrz)
            mdl.load(model_path)
            plotter.plot_forecast_validation(df_v, mdl, scalers_v,
                f'{outdir}/forecast_validation.png', feature_cols=fcols)
        except Exception as e:
            print(f'  Forecast validation plot skipped: {e}')

    print('\nDone! All results saved to simulation/outputs/figures/')


if __name__ == '__main__':
    main()
