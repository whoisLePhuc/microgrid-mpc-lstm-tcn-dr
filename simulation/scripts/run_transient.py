#!/usr/bin/env python3
"""Transient analysis: event-triggered inner loop simulation.
Runs 4μs converter model + MPC for ~5ms at each mode change event."""

import os, sys, json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def run_transient(p_pv, p_wind, p_load, p_bat, soc, vdc0=800.0,
                  dt_inner=4e-6, dt_mpc=100e-6, duration=0.01):
    """Run inner loop transient for one event.

    Args:
        p_pv, p_wind, p_load: power (kW)
        p_bat: battery power (>0 discharge, <0 charge) (kW)
        soc: state of charge
        vdc0: initial DC bus voltage (V)
        dt_inner: PWM switching period (s)
        dt_mpc: MPC update period (s)
        duration: simulation duration (s)

    Returns:
        vdc_log: list of VDC values
        t_log: list of time values
        overshoot: percentage
        settling_time: seconds to ±2%
    """
    from control.converter_model import ConverterLTVModel
    from control.mpc_controller import MPCController

    # Estimate currents from power (V ≈ 800V for PV/wind, 120V for battery)
    v_pv = 400.0; v_bat = 120.0; v_wind = 200.0
    i_pv = p_pv * 1000 / v_pv if p_pv > 0 else 0
    i_bat = p_bat * 1000 / v_bat if abs(p_bat) > 0 else 0
    i_wind = p_wind * 1000 / v_wind if p_wind > 0 else 0

    x = np.array([i_pv, i_bat, i_wind, vdc0, soc], dtype=np.float64)
    u = np.array([0.5, 0.5, 0.5], dtype=np.float64)  # initial duty cycles

    converter = ConverterLTVModel(l_pv=66e-3, rl_pv=0.066, l_bat=66e-3, rl_bat=0.066,
                                   l_wind=5e-3, rl_wind=0.015, c_dc=1.04e-4, ts=dt_mpc)
    mpc = MPCController(nx=5, nu=3, np_inner=2)

    # Reference: track desired battery current, regulate VDC to 800V, maintain SOC
    x_ref = np.array([i_pv, i_bat, i_wind, 800.0, soc], dtype=np.float64)
    u_min = np.array([0.0, 0.0, 0.0])
    u_max = np.array([1.0, 1.0, 1.0])

    steps = int(duration / dt_inner)
    mpc_steps = int(dt_mpc / dt_inner)
    vdc_log = []; t_log = []

    for k in range(steps):
        t = k * dt_inner * 1e6  # time in μs

        # MPC update at 10kHz
        if k % mpc_steps == 0:
            Ad, Bd, _ = converter.build_matrices(u, x[3], x[:3])
            u_opt = mpc.solve(x, Ad, Bd, x_ref, u_min, u_max)
            u = u_opt.copy()

        # State update at switching level (simplified forward Euler)
        # I_PV dynamics
        di_pv = (-converter.rl_pv / converter.l_pv) * x[0] + \
                (u[0] - 1) * x[3] / converter.l_pv + v_pv / converter.l_pv
        # I_bat dynamics
        di_bat = (-converter.rl_bat / converter.l_bat) * x[1] + \
                 (u[1] - 1) * x[3] / converter.l_bat + v_bat / converter.l_bat
        # I_wind dynamics
        di_wind = (-converter.rl_wind / converter.l_wind) * x[2] + \
                  (u[2] - 1) * x[3] / converter.l_wind + v_wind / converter.l_wind
        # V_DC dynamics
        dv_dc = ((1 - u[0]) * x[0] + (1 - u[1]) * x[1] + (1 - u[2]) * x[2]) / converter.c_dc
        # SOC dynamics (very slow, update at mpc rate)
        dsoc = 0.0

        x[0] += di_pv * dt_inner
        x[1] += di_bat * dt_inner
        x[2] += di_wind * dt_inner
        x[3] += dv_dc * dt_inner
        x[4] += dsoc * dt_inner

        if k % 10 == 0:
            vdc_log.append(x[3])
            t_log.append(t)

    vdc_arr = np.array(vdc_log)

    # Overshoot
    vdc_max = vdc_arr.max()
    overshoot = (vdc_max - 800.0) / 800.0 * 100

    # Settling time (±2% of 800V = 784-816V)
    settled = np.where(np.abs(vdc_arr - 800.0) / 800.0 <= 0.02)[0]
    settling_time = (settled[0] * 10 * dt_inner) if len(settled) > 0 else duration

    return vdc_arr, np.array(t_log), overshoot, settling_time


def analyze_all_transients(results, outdir):
    """Run transient analysis for all mode changes across all scenarios."""
    print("\n=== Transient Analysis ===")

    all_events = []
    for s_name in ['S1', 'S5']:
        if s_name not in results:
            continue
        r = results[s_name]
        modes = np.array(r.mode)
        # Detect mode changes
        changes = np.where(np.diff(modes) != 0)[0]
        print(f"\n{s_name}: {len(changes)} mode changes detected")

        events_analyzed = 0
        for idx in changes[:10]:  # max 10 events per scenario
            if events_analyzed >= 5:
                break
            t_hour = idx
            p_pv = float(r.p_pv[idx]); p_w = float(r.p_wind[idx])
            p_l = float(r.load[idx]); p_b = float(r.p_bat[idx])
            soc = float(r.soc[idx])
            mode_from = int(modes[idx]); mode_to = int(modes[idx+1])

            vdc, t_us, ov, st = run_transient(p_pv, p_w, p_l, p_b, soc)
            events_analyzed += 1
            all_events.append({
                'scenario': s_name, 'hour': int(t_hour),
                'mode_from': mode_from, 'mode_to': mode_to,
                'overshoot_pct': float(ov),
                'settling_time_s': float(st),
                'vdc_min': float(vdc.min()), 'vdc_max': float(vdc.max()),
                'vdc_std': float(vdc.std()),
                'vdc': vdc.tolist(), 'time_us': t_us.tolist(),
            })
            print(f"  Event {events_analyzed}: h={t_hour} mode {mode_from}→{mode_to}, "
                  f"overshoot={ov:.2f}%, settling={st*1000:.1f}ms")

    # Save results
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'transient_results.json')
    with open(path, 'w') as f:
        json.dump(all_events, f, indent=2, default=str)
    print(f"\nSaved {path}")
    return all_events


def plot_transients(events, save_path):
    """Plot VDC transient response for selected events."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    n_plots = min(len(events), 6)
    if n_plots == 0:
        return

    fig, axes = plt.subplots(n_plots, 1, figsize=(10, 2.5 * n_plots), sharex=True)
    if n_plots == 1:
        axes = [axes]

    for i in range(n_plots):
        ax = axes[i]
        e = events[i]
        t = np.array(e['time_us'])
        vdc = np.array(e['vdc'])
        ax.plot(t, vdc, color='#E15759', linewidth=0.8)
        ax.axhline(800, color='#333', linestyle='--', alpha=0.5, linewidth=0.8)
        ax.axhline(816, color='#999', linestyle=':', alpha=0.4, linewidth=0.6)
        ax.axhline(784, color='#999', linestyle=':', alpha=0.4, linewidth=0.6)
        ax.set_ylabel('VDC (V)')
        ax.set_title(f'{e["scenario"]}: mode {e["mode_from"]}→{e["mode_to"]} '
                     f'(h={e["hour"]}), OS={e["overshoot_pct"]:.1f}%',
                     fontsize=10)
        ax.set_ylim(780, 820)
        ax.grid(alpha=0.3)

    axes[-1].set_xlabel('Time (μs)')
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"Saved {save_path}")


if __name__ == '__main__':
    # Quick test with single event
    print("Testing single transient...")
    vdc, t, ov, st = run_transient(p_pv=0, p_wind=0, p_load=15, p_bat=10, soc=0.5)
    print(f"Overshoot: {ov:.2f}%")
    print(f"Settling time: {st*1000:.1f}ms")
    print(f"VDC range: {vdc.min():.0f} - {vdc.max():.0f} V")
