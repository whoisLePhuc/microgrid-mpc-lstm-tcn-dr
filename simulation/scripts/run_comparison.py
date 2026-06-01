#!/usr/bin/env python3
"""Compare Perfect Forecast vs LSTM-TCN Forecast using Simulator.run_outer(forecast_func=...)."""

import os, sys, argparse, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from engine.simulator import Simulator
from engine.scenarios import get_scenario
from analysis.kpi_calculator import compute_all, compare_scenarios
from visualization.plots import Plotter
from forecasting.lstm_tcn_model import LSTMTCN


def get_lstm_forecast(model, history_df, feature_cols, scalers):
    X_min, X_max = scalers['X_min'], scalers['X_max']
    y_min, y_max = scalers['y_min'], scalers['y_max']
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


def main():
    parser = argparse.ArgumentParser(description='Perfect vs LSTM-TCN forecast comparison')
    parser.add_argument('--data-dir', default=None)
    parser.add_argument('--model-path', default=None)
    parser.add_argument('--output-dir', default=None)
    parser.add_argument('--scenarios', nargs='+', default=['S1', 'S5'],
                        help='Scenarios to compare')
    parser.add_argument('--hours', type=int, default=168, help='Simulation hours')
    args = parser.parse_args()

    script_dir = os.path.dirname(__file__)
    data_dir   = args.data_dir   or os.path.join(script_dir, '..', 'data')
    model_path = args.model_path or os.path.join(script_dir, '..', 'models', 'lstm_tcn_model.keras')
    output_dir = args.output_dir or os.path.join(script_dir, '..', 'outputs', 'figures')
    os.makedirs(output_dir, exist_ok=True)

    print("=== Perfect vs LSTM-TCN Forecast Comparison ===\n")

    # Load data
    print("[1/4] Loading data...")
    df = pd.read_csv(os.path.join(data_dir, 'raw_data_2021_2023.csv'), index_col=0, parse_dates=True)
    df = df.iloc[:args.hours]
    if 'hour_sin' not in df.columns:
        hours = df['hour'].values if 'hour' in df.columns else np.arange(len(df)) % 24
        df['hour_sin'] = np.sin(2 * np.pi * hours / 24)
        df['hour_cos'] = np.cos(2 * np.pi * hours / 24)
    print(f"  Using {len(df)} hours of data")

    # Load model
    print("\n[2/4] Loading LSTM-TCN model...")
    scalers = np.load(os.path.join(data_dir, 'scalers.npz'), allow_pickle=True)
    feature_cols = list(scalers['feature_names'])
    model = LSTMTCN(
        int(scalers['input_steps'][0]), int(scalers['n_features'][0]),
        int(scalers['n_targets'][0]), int(scalers['horizon'][0]))
    model.load(model_path)
    print(f"  Loaded model: {model_path}")

    def forecast_func(hist_df):
        return get_lstm_forecast(model, hist_df, feature_cols, scalers)

    # Run simulations
    print("\n[3/4] Running simulations...")
    sim = Simulator()

    results_perfect = {}
    results_lstm = {}

    for s in args.scenarios:
        print(f"\n  {s}...")
        rp = sim.run_outer(s, args.hours, df)
        results_perfect[s] = rp
        print(f"    Perfect:   Cost={rp.cost.sum():.1f}")
        rl = sim.run_outer(s, args.hours, df, forecast_func=forecast_func)
        results_lstm[s] = rl
        print(f"    LSTM-TCN:  Cost={rl.cost.sum():.1f}")

    # KPIs
    print("\n[4/4] Computing KPIs...")
    kpi_perfect = compare_scenarios(results_perfect)
    s1_grid = results_perfect[args.scenarios[0]].p_grid
    kpi_lstm = {s: compute_all(r, baseline_grid=s1_grid) for s, r in results_lstm.items()}

    print(f"\n{'Scenario':<15} {'Cost(P)':<10} {'Cost(L)':<10} {'ΔCost%':<10}")
    print('-' * 45)
    for s in args.scenarios:
        cp = kpi_perfect[s]['Cost']
        cl = kpi_lstm[s]['Cost']
        delta = (cl - cp) / cp * 100 if cp else 0
        print(f'{s:<15} {cp:<10.1f} {cl:<10.1f} {delta:<+10.2f}')

    # Save
    out = {
        'perfect': {s: {k: float(v) for k, v in k.items()} for s, k in kpi_perfect.items()},
        'lstm': {s: {k: float(v) for k, v in k.items()} for s, k in kpi_lstm.items()},
    }
    with open(os.path.join(output_dir, 'comparison_perfect_vs_lstm.json'), 'w') as f:
        json.dump(out, f, indent=2)
    print(f"\n  Saved {output_dir}/comparison_perfect_vs_lstm.json")

    # Plot
    scenarios = args.scenarios
    cost_p = [kpi_perfect[s]['Cost'] for s in scenarios]
    cost_l = [kpi_lstm[s]['Cost'] for s in scenarios]
    sn_map = {'S1':'Rule-based','S2':'EMS-MPC','S3':'MPC+TOU','S4':'Threshold DR','S5':'Full DR'}
    snames = [sn_map.get(s, s) for s in scenarios]

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(scenarios)); w = 0.35
    ax.bar(x - w/2, cost_p, w, label='Perfect Forecast', color='steelblue')
    ax.bar(x + w/2, cost_l, w, label='LSTM-TCN Forecast', color='coral')
    ax.set_xticks(x); ax.set_xticklabels(snames, rotation=30, ha='right')
    ax.set_ylabel('Total Cost ($)')
    ax.set_title('Perfect vs LSTM-TCN Forecast: Cost Comparison')
    ax.legend(); ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'comparison_perfect_vs_lstm.png'), dpi=150)
    plt.close()
    print(f"  Saved {output_dir}/comparison_perfect_vs_lstm.png")

    print("\nDone!")


if __name__ == '__main__':
    main()
