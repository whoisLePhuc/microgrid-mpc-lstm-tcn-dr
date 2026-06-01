#!/usr/bin/env python3
"""Train LSTM-TCN model from prepared NPZ data.
Output: trained model (.keras) + training history plot + loss curves."""

import os, sys, argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from forecasting.lstm_tcn_model import LSTMTCN


def plot_training_history(history, save_path):
    """Plot train/val loss curves."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Loss
    axes[0].plot(history.history['loss'], label='Train', linewidth=1.5)
    axes[0].plot(history.history['val_loss'], label='Validation', linewidth=1.5)
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('MSE Loss')
    axes[0].set_title('Training History')
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    # Log scale
    axes[1].plot(history.history['loss'], label='Train', linewidth=1.5)
    axes[1].plot(history.history['val_loss'], label='Validation', linewidth=1.5)
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('MSE Loss (log)')
    axes[1].set_yscale('log')
    axes[1].set_title('Training History (log scale)')
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', dpi=150)
    plt.close()
    print(f"  Saved {save_path}")


def main():
    parser = argparse.ArgumentParser(description='Train LSTM-TCN forecast model')
    parser.add_argument('--data-dir', default=None, help='Data directory with NPZ files')
    parser.add_argument('--output-dir', default=None, help='Output directory')
    parser.add_argument('--epochs', type=int, default=100, help='Max training epochs')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    args = parser.parse_args()

    script_dir = os.path.dirname(__file__)
    data_dir = args.data_dir or os.path.join(script_dir, '..', 'data')
    output_dir = args.output_dir or os.path.join(script_dir, '..', 'models')
    os.makedirs(output_dir, exist_ok=True)

    print("=== Train LSTM-TCN ===")
    print(f"Data:   {data_dir}/")
    print(f"Output: {output_dir}/")
    print(f"Epochs: {args.epochs}, Batch: {args.batch_size}, LR: {args.lr}")

    # Load scalers for metadata
    print("\n[1/5] Loading data...")
    scalers = np.load(os.path.join(data_dir, 'scalers.npz'), allow_pickle=True)
    n_features = int(scalers['n_features'][0])
    n_targets  = int(scalers['n_targets'][0])
    input_steps = int(scalers['input_steps'][0])
    horizon     = int(scalers['horizon'][0])
    feature_names = list(scalers['feature_names'])
    target_names  = list(scalers['target_names'])
    print(f"  Features: {n_features} ({feature_names})")
    print(f"  Targets:  {n_targets} ({target_names})")
    print(f"  Look-back: {input_steps}, Horizon: {horizon}")

    # Load NPZ
    train = np.load(os.path.join(data_dir, 'train.npz'))
    val   = np.load(os.path.join(data_dir, 'val.npz'))
    X_train, y_train = train['X'], train['y']
    X_val,   y_val   = val['X'], val['y']
    print(f"  Train: X={X_train.shape}, y={y_train.shape}")
    print(f"  Val:   X={X_val.shape}, y={y_val.shape}")

    # Build model
    print("\n[2/5] Building LSTM-TCN model...")
    model = LSTMTCN(input_steps=input_steps, n_features=n_features,
                    n_targets=n_targets, horizon=horizon)
    model.build()
    model.model.summary()
    total_params = model.model.count_params()
    print(f"  Total params: {total_params:,}")

    # Train
    print(f"\n[3/5] Training (max {args.epochs} epochs)...")
    history = model.train(X_train, y_train, X_val, y_val,
                          epochs=args.epochs, batch_size=args.batch_size)

    best_val_loss = min(history.history['val_loss'])
    best_epoch = np.argmin(history.history['val_loss']) + 1
    print(f"  Best val_loss: {best_val_loss:.6f} at epoch {best_epoch}")

    # Save model
    print("\n[4/5] Saving model...")
    model_path = os.path.join(output_dir, 'lstm_tcn_model.keras')
    model.save(model_path)
    print(f"  Saved {model_path} ({os.path.getsize(model_path) / 1e6:.1f} MB)")

    # Save training history
    hist_path = os.path.join(output_dir, 'training_history.csv')
    import pandas as pd
    pd.DataFrame(history.history).to_csv(hist_path, index=False)
    print(f"  Saved {hist_path}")

    # Plot
    print("\n[5/5] Plotting training history...")
    plot_path = os.path.join(output_dir, 'training_history.png')
    plot_training_history(history, plot_path)

    print("\nDone! Model ready for evaluation.")


if __name__ == '__main__':
    main()
