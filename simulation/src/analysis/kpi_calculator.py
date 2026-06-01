import numpy as np

def calc_vri(vdc, vref=800.0):
    return float(np.mean(np.abs(vdc - vref) / vref) * 100)

def calc_total_cost(price, p_grid, p_dr, lambda_dr):
    energy_cost = np.sum(price * p_grid)
    dr_reward = np.sum(lambda_dr * p_dr)
    return float(energy_cost - dr_reward)

def calc_re_ratio(p_pv, p_wind, p_grid):
    p_re = np.sum(p_pv + p_wind)
    p_imp = np.sum(np.maximum(p_grid, 0))
    if p_re + p_imp == 0:
        return 0.0
    return float(p_re / (p_re + p_imp) * 100)

def calc_peak_reduction(p_grid_baseline, p_grid_dr):
    peak_base = np.max(p_grid_baseline) if len(p_grid_baseline) > 0 else 0
    peak_dr = np.max(p_grid_dr) if len(p_grid_dr) > 0 else 0
    if peak_base == 0:
        return 0.0
    return float((peak_base - peak_dr) / peak_base * 100)

def calc_settling_time(vdc, vref=800.0, tol=0.02):
    settled = np.where(np.abs(vdc - vref) / vref <= tol)[0]
    if len(settled) == 0:
        return float(len(vdc))
    return float(settled[0])

def calc_overshoot(vdc, vref=800.0):
    max_dev = np.max(np.abs(vdc - vref))
    return float(max_dev / vref * 100)

def compute_all(results, baseline_grid=None):
    lam = results.lambda_dr if hasattr(results, 'lambda_dr') and len(results.lambda_dr) > 0 else np.full_like(results.price, 0.5)
    kpi = {
        'VRI': calc_vri(results.vdc),
        'Cost': calc_total_cost(results.price, results.p_grid, results.p_dr, lam),
        'RE_Ratio': calc_re_ratio(results.p_pv, results.p_wind, results.p_grid),
        'Settle_Time': calc_settling_time(results.vdc),
        'Overshoot': calc_overshoot(results.vdc),
    }
    if baseline_grid is not None:
        kpi['Peak_Red'] = calc_peak_reduction(baseline_grid, results.p_grid)
    else:
        kpi['Peak_Red'] = 0.0
    return kpi

def compare_scenarios(all_results):
    kpis = {}
    s1_grid = None
    if 'S1' in all_results:
        s1_grid = all_results['S1'].p_grid
    for name, res in all_results.items():
        kpis[name] = compute_all(res, baseline_grid=s1_grid)
    return kpis
