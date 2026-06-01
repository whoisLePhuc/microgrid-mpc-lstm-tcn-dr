#!/usr/bin/env python3
"""Evaluate LSTM-TCN forecast: RMSE, MAE, R², time-series plots."""

import os, sys, argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from forecasting.lstm_tcn_model import LSTMTCN


def rmse(y_true, y_pred):
    return np.sqrt(np.mean((y_true - y_pred) ** 2, axis=0))

def mae(y_true, y_pred):
    return np.mean(np.abs(y_true - y_pred), axis=0)

def r2_score(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2, axis=0)
    ss_tot = np.sum((y_true - np.mean(y_true, axis=0)) ** 2, axis=0)
    return 1 - ss_res / (ss_tot + 1e-10)


def plot_predictions(y_true, y_pred, target_names, save_path, n_samples=168):
    """Plot forecast vs actual for each target (first horizon step)."""
    n_targets = len(target_names)
    fig, axes = plt.subplots(n_targets, 1, figsize=(14, 3 * n_targets), sharex=True)

    if n_targets == 1:
        axes = [axes]

    for i, name in enumerate(target_names):
        ax = axes[i]
        ax.plot(y_true[:n_samples, i], label='Actual', color='blue', alpha=0.7, linewidth=1)
        ax.plot(y_pred[:n_samples, i], label='Forecast', color='red', alpha=0.7, linewidth=1,
                linestyle='--')
        ax.fill_between(range(n_samples),
                        y_true[:n_samples, i], y_pred[:n_samples, i],
                        alpha=0.15, color='red')
        ax.set_ylabel(name)
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(alpha=0.3)

    axes[-1].set_xlabel('Time (hours)')
    fig.suptitle('LSTM-TCN Forecast vs Actual (1-step ahead)', fontsize=13, y=1.02)
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"  Saved {save_path}")


def plot_scatter(y_true, y_pred, target_names, save_path):
    """Regression scatter: predicted vs actual."""
    n_targets = len(target_names)
    fig, axes = plt.subplots(2, 3, figsize=(14, 9))
    axes = axes.flatten()

    for i, name in enumerate(target_names):
        if i >= 6:
            break
        ax = axes[i]
        ax.scatter(y_true[:, i], y_pred[:, i], s=2, alpha=0.3, c='blue')
        lims = [min(y_true[:, i].min(), y_pred[:, i].min()),
                max(y_true[:, i].max(), y_pred[:, i].max())]
        ax.plot(lims, lims, 'r--', alpha=0.5, linewidth=1)
        ax.set_xlim(lims)
        ax.set_ylim(lims)
        ax.set_xlabel('Actual')
        ax.set_ylabel('Forecast')
        ax.set_title(name)
        ax.grid(alpha=0.3)
        ax.set_aspect('equal')

    for j in range(n_targets, 6):
        fig.delaxes(axes[j])

    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"  Saved {save_path}")


def main():
    parser = argparse.ArgumentParser(description='Evaluate LSTM-TCN forecast')
    parser.add_argument('--data-dir', default=None, help='Data directory')
    parser.add_argument('--model-path', default=None, help='Model .keras path')
    parser.add_argument('--output-dir', default=None, help='Output directory')
    args = parser.parse_args()

    script_dir = os.path.dirname(__file__)
    data_dir    = args.data_dir    or os.path.join(script_dir, '..', 'data')
    model_path  = args.model_path  or os.path.join(script_dir, '..', 'models', 'lstm_tcn_model.keras')
    output_dir  = args.output_dir  or os.path.join(script_dir, '..', 'models')
    os.makedirs(output_dir, exist_ok=True)

    print("=== Evaluate LSTM-TCN Forecast ===")

    # Load scalers
    print("\n[1/5] Loading metadata...")
    scalers = np.load(os.path.join(data_dir, 'scalers.npz'), allow_pickle=True)
    n_features  = int(scalers['n_features'][0])
    n_targets   = int(scalers['n_targets'][0])
    input_steps = int(scalers['input_steps'][0])
    horizon     = int(scalers['horizon'][0])
    target_names = list(scalers['target_names'])
    y_min = scalers['y_min']
    y_max = scalers['y_max']

    # Load test set
    print("\n[2/5] Loading test data...")
    test = np.load(os.path.join(data_dir, 'test.npz'))
    X_test   = test['X']
    y_test_s = test['y']
    y_test   = test['y_raw']
    print(f"  X_test: {X_test.shape}, y_test: {y_test.shape}")

    # Load model
    print("\n[3/5] Loading model...")
    if not os.path.exists(model_path):
        print(f"  ERROR: Model not found at {model_path}")
        print("  Run train_lstm_tcn.py first!")
        sys.exit(1)
    model = LSTMTCN(input_steps=input_steps, n_features=n_features,
                    n_targets=n_targets, horizon=horizon)
    model.load(model_path)
    print(f"  Loaded {model_path}")

    # Predict
    print("\n[4/5] Computing predictions...")
    y_pred_s = model.predict(X_test)
    # Inverse transform
    eps = 1e-8
    y_pred = y_pred_s * (y_max - y_min + eps) + y_min

    # Metrics for each target at each horizon step
    print("\n[5/5] Computing metrics...")
    print(f"\n{'Target':<12} {'Horizon':<8} {'RMSE':<10} {'MAE':<10} {'R²':<10}")
    print('-' * 50)

    all_metrics = {}
    for t in range(n_targets):
        all_metrics[target_names[t]] = {}
        for h in range(horizon):
            r = rmse(y_test[:, h, t], y_pred[:, h, t])
            m = mae(y_test[:, h, t], y_pred[:, h, t])
            r2 = r2_score(y_test[:, h, t], y_pred[:, h, t])
            all_metrics[target_names[t]][f'h+{h+1}'] = {'RMSE': float(r), 'MAE': float(m), 'R²': float(r2)}
            print(f'{target_names[t]:<12} h+{h+1:<6} {r:<10.3f} {m:<10.3f} {r2:<10.4f}')

    # Average across horizon
    print(f"\n{'Target':<12} {'Avg RMSE':<10} {'Avg MAE':<10} {'Avg R²':<10}")
    print('-' * 42)
    for t in range(n_targets):
        avg_r = np.mean([all_metrics[target_names[t]][f'h+{h+1}']['RMSE'] for h in range(horizon)])
        avg_m = np.mean([all_metrics[target_names[t]][f'h+{h+1}']['MAE'] for h in range(horizon)])
        avg_r2 = np.mean([all_metrics[target_names[t]][f'h+{h+1}']['R²'] for h in range(horizon)])
        print(f'{target_names[t]:<12} {avg_r:<10.3f} {avg_m:<10.3f} {avg_r2:<10.4f}')

    # Save metrics
    metrics_path = os.path.join(output_dir, 'forecast_metrics.json')
    import json
    with open(metrics_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\n  Saved {metrics_path}")

    # Plots
    print("\nGenerating plots...")
    y_true_1step = y_test[:, 0, :]
    y_pred_1step = y_pred[:, 0, :]

    plot_predictions(y_true_1step, y_pred_1step, target_names,
                     os.path.join(output_dir, 'forecast_timeseries.png'))
    plot_scatter(y_true_1step, y_pred_1step, target_names,
                 os.path.join(output_dir, 'forecast_scatter.png'))

    print("\nDone!")


if __name__ == '__main__':
    main()
