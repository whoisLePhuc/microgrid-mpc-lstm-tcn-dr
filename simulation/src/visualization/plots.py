import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# Thesis-quality plot configuration
THESIS_COLORS = ['#6C6C6C', '#4E79A7', '#59A14F', '#F28E2B', '#E15759']
THESIS_ALPHA = 0.85

plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'font.serif': ['DejaVu Serif', 'Times New Roman', 'Times', 'serif'],
    'axes.titlesize': 13,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 200,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'grid.alpha': 0.35,
    'grid.linestyle': '--',
    'grid.linewidth': 0.6,
    'axes.grid': True,
    'axes.axisbelow': True,
    'legend.frameon': True,
    'legend.fancybox': False,
    'legend.edgecolor': '#333',
    'legend.framealpha': 0.9,
})

class Plotter:
    SCENARIO_NAMES = {
        'S1': 'Rule-based',
        'S2': 'EMS-MPC',
        'S3': 'MPC+TOU',
        'S4': 'Threshold DR',
        'S5': 'Full DR',
    }

    def __init__(self):
        pass

    def _sn(self, key):
        """Map scenario key to display name."""
        return self.SCENARIO_NAMES.get(key, key)

    def plot_scenario_comparison(self, kpi_table, save_path='figures/kpi_comparison.png'):
        import pandas as pd
        df = pd.DataFrame(kpi_table).T
        df.index = [self._sn(k) for k in df.index]
        fig, axes = plt.subplots(2, 3, figsize=(14, 8))
        kpi_labels = {
            'VRI': 'VRI (%)', 'Cost': 'Total Cost ($)', 'RE_Ratio': 'RE Ratio (%)',
            'Settle_Time': 'Settling Time (s)', 'Overshoot': 'Overshoot (%)', 'Peak_Red': 'Peak Reduction (%)',
        }
        for i, col in enumerate(df.columns):
            if i >= 6:
                break
            ax = axes[i // 3, i % 3]
            bars = ax.bar(df.index, df[col], color=THESIS_COLORS[:len(df)], alpha=THESIS_ALPHA,
                         edgecolor='white', linewidth=0.5)
            ax.set_title(kpi_labels.get(col, col), fontsize=12, fontweight='bold')
            ax.set_ylabel(kpi_labels.get(col, col))
            ax.tick_params(axis='x', rotation=30)
            for bar in bars:
                h = bar.get_height()
                if abs(h) < 1:
                    ax.text(bar.get_x() + bar.get_width()/2, h, f'{h:.2f}',
                            ha='center', va='bottom' if h >= 0 else 'top', fontsize=7)
                elif abs(h) < 1000:
                    ax.text(bar.get_x() + bar.get_width()/2, h, f'{h:.1f}',
                            ha='center', va='bottom' if h >= 0 else 'top', fontsize=7)
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        print(f'Saved {save_path}')

    def plot_time_series(self, results, save_path='figures/time_series.png'):
        fig, axes = plt.subplots(5, 1, figsize=(12, 12), sharex=True)
        t = np.arange(len(results.time_h)) / 24.0
        axes[0].stackplot(t, results.p_pv, results.p_wind, labels=['PV', 'Wind'],
                          colors=['#F28E2B', '#4E79A7'], alpha=0.8)
        axes[0].set_ylabel('Renewable (kW)'); axes[0].legend(loc='upper right')
        axes[1].fill_between(t, 0, results.p_bat, where=results.p_bat >= 0,
                             color='#E15759', alpha=0.5, label='Discharge')
        axes[1].fill_between(t, 0, results.p_bat, where=results.p_bat < 0,
                             color='#59A14F', alpha=0.5, label='Charge')
        axes[1].axhline(0, color='#333', linewidth=0.5)
        axes[1].set_ylabel('Battery (kW)'); axes[1].legend(loc='upper right')
        axes[2].plot(t, results.soc * 100, color='#59A14F', linewidth=1.5)
        axes[2].fill_between(t, 0, results.soc * 100, color='#59A14F', alpha=0.15)
        axes[2].axhline(20, color='#E15759', linestyle=':', alpha=0.6, label='SOC limits')
        axes[2].axhline(90, color='#E15759', linestyle=':', alpha=0.6)
        axes[2].set_ylabel('SOC (%)'); axes[2].set_ylim(0, 100)
        axes[3].fill_between(t, 0, results.p_grid, where=results.p_grid >= 0,
                             color='#E15759', alpha=0.5, label='Import')
        axes[3].fill_between(t, 0, results.p_grid, where=results.p_grid < 0,
                             color='#4E79A7', alpha=0.5, label='Export')
        axes[3].axhline(0, color='#333', linewidth=0.5)
        axes[3].set_ylabel('Grid (kW)'); axes[3].legend(loc='upper right')
        axes[4].plot(t, results.vdc, color='#333', linewidth=0.8, alpha=0.7)
        axes[4].axhline(800, color='#E15759', linestyle='--', alpha=0.5)
        axes[4].set_ylabel('DC Bus (V)')
        axes[4].set_xlabel('Time (days)')
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        print(f'Saved {save_path}')

    def plot_cost_comparison(self, results_dict, save_path='figures/cost_bar.png'):
        keys = list(results_dict.keys())
        names = [self._sn(k) for k in keys]
        costs = [np.sum(results_dict[k].cost) for k in keys]
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(names, costs, color=THESIS_COLORS[:len(keys)], alpha=THESIS_ALPHA,
                     edgecolor='white', linewidth=0.5)
        ax.set_ylabel('Total Cost ($)')
        ax.set_title('Economic Comparison Across Scenarios', fontweight='bold')
        ax.axhline(0, color='#333', linewidth=0.5)
        for bar, val in zip(bars, costs):
            y = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, y, f'${val:.0f}',
                    ha='center', va='bottom' if y >= 0 else 'top', fontsize=10)
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        print(f'Saved {save_path}')

    def plot_sensitivity(self, sens_results, param_name, save_path=None):
        fig, ax = plt.subplots(figsize=(8, 5))
        names = list(sens_results.keys())
        costs = [sens_results[n]['Cost'] for n in names]
        x = np.arange(len(names))
        ax.plot(x, costs, marker='s', linewidth=2, color='#E15759', markersize=8)
        ax.fill_between(x, costs, alpha=0.1, color='#E15759')
        ax.set_xticks(x); ax.set_xticklabels(names)
        ax.set_xlabel(param_name, fontweight='bold')
        ax.set_ylabel('Total Cost ($)')
        ax.set_title(f'Sensitivity: {param_name}', fontweight='bold')
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        print(f'Saved {save_path}')

    def plot_cost_accumulation(self, results_dict, save_path='figures/cost_accumulation.png'):
        fig, ax = plt.subplots(figsize=(10, 5))
        pairs = [('S1', '#6C6C6C', '-'), ('S3', '#59A14F', '-'), ('S5', '#E15759', '-')]
        for key, color, ls in pairs:
            if key in results_dict:
                cum = np.cumsum(results_dict[key].cost)
                ax.plot(cum, label=self._sn(key), color=color, linewidth=1.5, linestyle=ls)
        ax.set_xlabel('Time (hours)'); ax.set_ylabel('Cumulative Cost ($)')
        ax.set_title('Cost Accumulation Over Time', fontweight='bold')
        ax.axhline(0, color='#333', linewidth=0.5)
        ax.legend(loc='upper left')
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        print(f'Saved {save_path}')

    def plot_load_profile_dr(self, results_ref, results_dr, save_path='figures/load_profile_dr.png'):
        fig, ax = plt.subplots(figsize=(12, 5))
        t = np.arange(len(results_ref.load)) / 24.0
        ax.plot(t, results_ref.load, label='Original Load', color='#4E79A7', linewidth=1.2)
        effective = results_dr.load - results_dr.p_dr
        ax.plot(t, effective, label='Load after DR', color='#E15759', linewidth=1.2, linestyle='--')
        ax.fill_between(t, results_ref.load, effective, alpha=0.1, color='#E15759')
        clip_mask = np.array(results_dr.dr_mode) == 'PeakClip'
        fill_mask = np.array(results_dr.dr_mode) == 'ValleyFill'
        if clip_mask.any():
            ax.scatter(t[clip_mask], effective[clip_mask], color='#59A14F', s=20,
                       marker='v', label=f'PeakClip ({clip_mask.sum()}h)', zorder=5, edgecolor='white')
        if fill_mask.any():
            ax.scatter(t[fill_mask], effective[fill_mask], color='#F28E2B', s=20,
                       marker='^', label=f'ValleyFill ({fill_mask.sum()}h)', zorder=5, edgecolor='white')
        ax.set_xlabel('Time (days)'); ax.set_ylabel('Power (kW)')
        ax.set_title('Load Profile Before and After Demand Response', fontweight='bold')
        ax.legend(loc='upper right')
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        print(f'Saved {save_path}')

    def plot_mode_timeline(self, results, save_path='figures/mode_timeline.png'):
        fig, ax = plt.subplots(figsize=(12, 3.5))
        modes = np.array(results.mode)
        t = np.arange(len(modes)) / 24.0
        colors_map = ['#4E79A7','#F28E2B','#59A14F','#E15759','#B07AA1','#8C564B']
        labels = ['M1: Charge','M2: ValleyFill','M3: Export','M4: PeakClip','M5: Discharge','M6: Import']
        for m in range(1, 7):
            mask = modes == m
            if mask.any():
                ax.fill_between(t, 0, 1, where=mask, alpha=0.35, color=colors_map[m-1],
                                transform=ax.get_xaxis_transform(), label=labels[m-1])
        ax.set_xlabel('Time (days)'); ax.set_ylabel('PMS Mode')
        ax.set_title('PMS Operating Mode Timeline (Full DR)', fontweight='bold')
        ax.set_yticks([]); ax.legend(ncol=3, fontsize=9, loc='lower center',
                                      bbox_to_anchor=(0.5, -0.45))
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        print(f'Saved {save_path}')

    def plot_soc_comparison(self, results_dict, save_path='figures/soc_comparison.png'):
        fig, ax = plt.subplots(figsize=(12, 4))
        pairs = [('S1', '#6C6C6C', '-'), ('S3', '#59A14F', '-'), ('S5', '#E15759', '-')]
        for key, color, ls in pairs:
            if key in results_dict:
                t = np.arange(len(results_dict[key].soc)) / 24.0
                ax.plot(t, results_dict[key].soc * 100, label=self._sn(key), color=color,
                       linewidth=1.5, linestyle=ls)
        ax.axhline(20, color='#333', linestyle=':', alpha=0.5, label='SOC limits')
        ax.axhline(90, color='#333', linestyle=':', alpha=0.5)
        ax.set_xlabel('Time (days)'); ax.set_ylabel('SOC (%)'); ax.set_ylim(0, 100)
        ax.set_title('Battery State of Charge Comparison', fontweight='bold')
        ax.legend(loc='lower right')
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        print(f'Saved {save_path}')

    def plot_dr_activation(self, results, save_path='figures/dr_activation.png'):
        fig, ax = plt.subplots(figsize=(12, 2.5))
        modes = np.array(results.dr_mode)
        t = np.arange(len(modes)) / 24.0
        clip_idx = modes == 'PeakClip'
        fill_idx = modes == 'ValleyFill'
        y = np.zeros(len(modes))
        y[clip_idx] = 1; y[fill_idx] = -1
        ax.fill_between(t, 0, y, where=clip_idx, color='#59A14F', alpha=0.6, label='PeakClip')
        ax.fill_between(t, 0, y, where=fill_idx, color='#F28E2B', alpha=0.6, label='ValleyFill')
        ax.set_xlabel('Time (days)'); ax.set_ylabel('DR')
        ax.set_title('Demand Response Activation Timeline', fontweight='bold')
        ax.set_yticks([-1, 0, 1]); ax.set_yticklabels(['ValleyFill','Off','PeakClip'])
        ax.legend(loc='upper right')
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        print(f'Saved {save_path}')

    def plot_forecast_validation(self, df, model, scalers, save_path='figures/forecast_validation.png',
                                 n_hours=168, feature_cols=None):
        if feature_cols is None:
            feature_cols = ['ghi', 'temp', 'wind', 'load', 'price', 'hour_sin', 'hour_cos']

        X_min, X_max = scalers['X_min'], scalers['X_max']
        y_min, y_max = scalers['y_min'], scalers['y_max']
        input_steps = int(scalers['input_steps'][0])
        horizon = int(scalers['horizon'][0])

        df = df.iloc[:n_hours].copy()
        if 'hour_sin' not in df.columns:
            h = df['hour'].values if 'hour' in df.columns else np.arange(len(df)) % 24
            df['hour_sin'] = np.sin(2 * np.pi * h / 24)
            df['hour_cos'] = np.cos(2 * np.pi * h / 24)

        raw_features = df[feature_cols].values.astype(np.float32)
        target_cols = ['p_pv', 'p_wind', 'temp', 'load', 'price']
        all_preds = {t: [] for t in target_cols}
        eps = 1e-8

        for i in range(len(raw_features) - input_steps - horizon + 1):
            x_in = raw_features[i:i + input_steps]
            x_s = (x_in - X_min) / (X_max - X_min + eps)
            y_s = model.predict(x_s.reshape(1, input_steps, -1))
            y_p = y_s * (y_max - y_min + eps) + y_min
            for j, t in enumerate(target_cols):
                val = y_p[0, 0, j]
                all_preds[t].append(max(val, 0) if t in ('price',) else val)

        align = len(all_preds[target_cols[0]])
        actuals = {t: df[t].values[input_steps:input_steps + align] for t in target_cols}

        fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True)
        cfg = [
            (0, 'p_pv', 'PV Power (kW)', 'PV Power Forecast', '#F28E2B'),
            (1, 'load', 'Load (kW)', 'Load Demand Forecast', '#4E79A7'),
            (2, 'price', 'Price ($/kWh)', 'Electricity Price Forecast', '#59A14F'),
        ]
        t = np.arange(align) / 24.0
        for ax_idx, col, ylabel, title, color in cfg:
            ax = axes[ax_idx]
            ax.plot(t, actuals[col], label='Actual', color=color, linewidth=1.5)
            ax.plot(t, all_preds[col], label='LSTM-TCN', color='#E15759', linewidth=1.2, linestyle='--')
            ax.fill_between(t, actuals[col], all_preds[col], alpha=0.12, color='#E15759')
            ax.set_ylabel(ylabel)
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.legend(loc='upper right')

        axes[-1].set_xlabel('Time (days)')
        plt.tight_layout()
        plt.savefig(save_path)
        plt.close()
        print(f'Saved {save_path}')
