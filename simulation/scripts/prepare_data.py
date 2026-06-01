#!/usr/bin/env python3
"""Prepare sliding windows for LSTM-TCN training from raw CSV data.
Output: train/val/test NPZ archives."""

import os, sys, argparse
import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from config import LSTMConfig


def create_sequences(data, input_steps, horizon):
    """Create sliding windows: X=(samples, input_steps, features), y=(samples, horizon, targets)."""
    X, y = [], []
    for i in range(len(data) - input_steps - horizon + 1):
        X.append(data[i : i + input_steps, :])
        y.append(data[i + input_steps : i + input_steps + horizon, :])
    return np.array(X), np.array(y)


def minmax_fit(data):
    """Compute per-feature min/max for scaling."""
    return {
        'min': data.min(axis=0),
        'max': data.max(axis=0),
    }


def minmax_transform(data, scaler):
    """Apply min-max scaling."""
    eps = 1e-8
    return (data - scaler['min']) / (scaler['max'] - scaler['min'] + eps)


def minmax_inverse(data, scaler):
    """Reverse min-max scaling."""
    eps = 1e-8
    return data * (scaler['max'] - scaler['min'] + eps) + scaler['min']


def main():
    parser = argparse.ArgumentParser(description='Prepare sliding windows for LSTM-TCN')
    parser.add_argument('--input', default=None, help='Input CSV path')
    parser.add_argument('--output-dir', default=None, help='Output directory')
    parser.add_argument('--input-steps', type=int, default=12, help='Look-back window')
    parser.add_argument('--horizon', type=int, default=4, help='Prediction horizon')
    parser.add_argument('--test-ratio', type=float, default=0.15, help='Test split ratio')
    parser.add_argument('--val-ratio', type=float, default=0.10, help='Validation split ratio')
    args = parser.parse_args()

    # Default paths
    script_dir = os.path.dirname(__file__)
    default_input = os.path.join(script_dir, '..', 'data', 'raw_data_2021_2023.csv')
    input_path = args.input or default_input
    output_dir = args.output_dir or os.path.join(script_dir, '..', 'data')
    os.makedirs(output_dir, exist_ok=True)

    input_steps = args.input_steps
    horizon = args.horizon

    print("=== Prepare Data for LSTM-TCN ===")
    print(f"Input:       {input_path}")
    print(f"Output:      {output_dir}/")
    print(f"Look-back:   {input_steps} steps")
    print(f"Horizon:     {horizon} steps")

    # Load data
    print("\n[1/5] Loading raw data...")
    df = pd.read_csv(input_path, index_col=0, parse_dates=True)
    print(f"  Shape: {df.shape}")
    print(f"  Date range: {df.index[0]} to {df.index[-1]}")

    # Select feature and target columns
    feature_cols = ['ghi', 'temp', 'wind', 'load', 'price', 'hour_sin', 'hour_cos']
    target_cols = ['p_pv', 'p_wind', 'temp', 'load', 'price']

    # Ensure all columns exist
    feature_cols = [c for c in feature_cols if c in df.columns]
    target_cols = [c for c in target_cols if c in df.columns]
    n_features = len(feature_cols)
    n_targets = len(target_cols)

    print(f"\n  Features ({n_features}): {feature_cols}")
    print(f"  Targets ({n_targets}):  {target_cols}")

    # Extract arrays
    features = df[feature_cols].values.astype(np.float32)
    targets = df[target_cols].values.astype(np.float32)

    # Handle any NaN
    nan_count = np.isnan(features).sum() + np.isnan(targets).sum()
    if nan_count > 0:
        print(f"\n  WARNING: {nan_count} NaN values found. Dropping...")
        valid = ~(np.isnan(features).any(axis=1) | np.isnan(targets).any(axis=1))
        features = features[valid]
        targets = targets[valid]
        print(f"  After drop: {len(features)} samples")

    # Create sequences — X gets only features, y gets only targets
    print("\n[2/5] Creating sliding windows...")
    X_all, y_all = create_sequences(np.hstack([features, targets]), input_steps, horizon)
    # X_all: (samples, input_steps, n_features + n_targets)
    # y_all: (samples, horizon, n_features + n_targets)
    X = X_all[:, :, :n_features]       # only feature channels
    y = y_all[:, :, n_features:]       # only target channels
    print(f"  X shape: {X.shape}")
    print(f"  y shape: {y.shape}")

    # Split: train / val / test (chronological order)
    print("\n[3/5] Splitting train/val/test...")
    n = len(X)
    n_test = int(n * args.test_ratio)
    n_val = int(n * args.val_ratio)
    n_train = n - n_test - n_val

    X_train, y_train = X[:n_train], y[:n_train]
    X_val,   y_val   = X[n_train:n_train + n_val], y[n_train:n_train + n_val]
    X_test,  y_test  = X[n_train + n_val:], y[n_train + n_val:]

    print(f"  Train: {X_train.shape[0]} samples")
    print(f"  Val:   {X_val.shape[0]} samples")
    print(f"  Test:  {X_test.shape[0]} samples")

    # MinMax scaling on TRAIN only
    print("\n[4/5] Fitting MinMax scaler on train set...")
    X_scaler = minmax_fit(X_train.reshape(-1, n_features))
    y_scaler = minmax_fit(y_train.reshape(-1, n_targets))

    X_train_s = minmax_transform(X_train, X_scaler)
    X_val_s   = minmax_transform(X_val,   X_scaler)
    X_test_s  = minmax_transform(X_test,  X_scaler)

    y_train_s = minmax_transform(y_train, y_scaler)
    y_val_s   = minmax_transform(y_val,   y_scaler)
    y_test_s  = minmax_transform(y_test,  y_scaler)

    # Save
    print("\n[5/5] Saving NPZ files...")
    np.savez(os.path.join(output_dir, 'train.npz'),
             X=X_train_s, y=y_train_s)
    np.savez(os.path.join(output_dir, 'val.npz'),
             X=X_val_s, y=y_val_s)
    np.savez(os.path.join(output_dir, 'test.npz'),
             X=X_test_s, y=y_test_s, y_raw=y_test)

    # Save scalers
    np.savez(os.path.join(output_dir, 'scalers.npz'),
             X_min=X_scaler['min'], X_max=X_scaler['max'],
             y_min=y_scaler['min'], y_max=y_scaler['max'],
             feature_names=feature_cols, target_names=target_cols,
             input_steps=np.array([input_steps]),
             horizon=np.array([horizon]),
             n_features=np.array([n_features]),
             n_targets=np.array([n_targets]))

    print(f"\n  Saved to {output_dir}/")
    print(f"    train.npz: {X_train_s.nbytes / 1e6:.1f} MB")
    print(f"    val.npz:   {X_val_s.nbytes / 1e6:.1f} MB")
    print(f"    test.npz:  {X_test_s.nbytes / 1e6:.1f} MB")
    print(f"    scalers.npz")
    print("\nDone!")


if __name__ == '__main__':
    main()
