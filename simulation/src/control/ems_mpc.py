"""Economic MPC for outer-loop battery scheduling.
Minimizes grid electricity cost over a 24h horizon by optimal battery dispatch."""

import numpy as np
from scipy import sparse
import osqp


class EMSMPC:
    """Economic MPC for energy management system battery scheduling.

    State:      SOC(k) ∈ [0, 1]     — battery state of charge
    Input:      P_bat(k) ∈ ℝ        — battery power (>0 discharge, <0 charge)
    Disturb:    P_net(k) = P_load - P_PV - P_wind  — net demand before battery
                price(k)            — electricity price ($/kWh)

    Dynamics:   SOC(k+1) = SOC(k) - P_bat(k) * dt_h / C_kwh
    Cost:       J = Σ price(k)·max(P_net(k) - P_bat(k), 0)
    """

    def __init__(self, C_kwh=50.0, dt_h=1.0, N=24, degrad_cost=0.01):
        self.C = C_kwh          # battery capacity (kWh)
        self.dt = dt_h          # time step (hours)
        self.N = N              # prediction horizon
        self.soc_min = 0.20
        self.soc_max = 0.90
        self.p_ch_max = 25.0    # max charge power (kW)
        self.p_dch_max = 25.0   # max discharge power (kW)
        self.w_degrad = degrad_cost  # battery degradation penalty

    def solve(self, p_net_fc, price_fc, soc_now=0.5, p_dr_fc=None, lambda_dr_fc=None,
              peak_penalty=0.0, p_peak=18.0):
        """Solve economic dispatch for battery over horizon.

        Args:
            p_net_fc:  (N,) array — forecast net load before battery [kW]
            price_fc:  (N,) array — forecast electricity price [$/kWh]
            soc_now:   float — current SOC
            p_dr_fc:   (N,) array or None — forecast DR adjustment [kW]
            lambda_dr_fc: (N,) array or None — DR incentive coefficients
            peak_penalty: float — additional cost on P_grid above threshold
            p_peak:    float — peak load threshold for penalty

        Returns:
            p_bat_opt: (N,) optimal battery schedule (>0 discharge, <0 charge)
            info:      dict with SOC trajectory, grid power, cost
        """
        N = len(p_net_fc)
        C = self.C

        # Net demand after DR
        p_net = p_net_fc.copy()
        if p_dr_fc is not None:
            p_net = p_net - p_dr_fc

        # QP: min 0.5·x'·P·x + q'·x  s.t.  l ≤ A·x ≤ u,  lb ≤ x ≤ ub
        # x = [P_bat(0), ..., P_bat(N-1)]

        # Cost: J = Σ price(k)·P_grid(k) + w_peak·P_grid(k)²
        # Where P_grid(k) = P_net(k) - P_bat(k) = P_net(k) - x(k)
        #
        # J = Σ price·(P_net - x) + w_peak·(P_net - x)²
        #   = Σ [price·P_net + w_peak·P_net²]  [constant, ignored]
        #     + Σ [(-price - 2·w_peak·P_net)·x]  [linear]
        #     + Σ [w_peak·x²]                     [quadratic]
        w_peak = peak_penalty
        base_reg = 1e-4

        # Quadratic term: w_peak·P_grid² + w_degrad·P_bat²
        # P_grid² contributes w_peak to each diagonal entry
        # P_bat² (degradation) adds w_degrad to each diagonal entry
        P_diag = np.full(N, base_reg + w_peak + self.w_degrad)
        P = sparse.diags(P_diag, format='csc')

        # Linear term: (-price - 2·w_peak·P_net)·x
        q = -price_fc.astype(np.float64) - 2.0 * w_peak * p_net.astype(np.float64)

        # Battery power limits + grid import/export limits combined
        # |P_bat| ≤ 25 (battery limit)
        # |P_grid| = |P_net - P_bat| ≤ 25 (grid limit) → P_net - 25 ≤ P_bat ≤ P_net + 25
        var_lb = np.maximum(-self.p_ch_max, p_net - 25.0)
        var_ub = np.minimum( self.p_dch_max, p_net + 25.0)

        # Inequality constraints: cumulative sum bounds for SOC
        # SOC(k+1) = soc_now - (1/C) * Σ_{i=0}^{k} P_bat(i)
        # SOC_min ≤ SOC(k) ≤ SOC_max
        # → Σ_{i=0}^{k-1} P_bat(i) ≤ (soc_now - SOC_min) * C
        # → Σ_{i=0}^{k-1} P_bat(i) ≥ (soc_now - SOC_max) * C

        soc_headroom = (soc_now - self.soc_min) * C  # max total discharge
        soc_capacity = (soc_now - self.soc_max) * C   # min total charge (negative)

        # Build constraint matrix A: (3N+1) × N
        # Rows 0..N-1:       variable bounds  (identity)
        # Rows N..2N-1:      SOC upper bound  (cumulative sum)
        # Rows 2N..3N-1:     SOC lower bound  (cumulative sum)
        # Row 3N:            end SOC

        rows, cols, vals = [], [], []
        n_rows = 3 * N + 1

        # Rows 0..N-1: Identity — variable bounds
        for i in range(N):
            rows.append(i); cols.append(i); vals.append(1.0)

        # Rows N..2N-1: SOC upper — cumulative sum ≤ soc_headroom
        for k in range(N):
            for i in range(k + 1):
                rows.append(N + k); cols.append(i); vals.append(1.0)

        # Rows 2N..3N-1: SOC lower — cumulative sum ≥ soc_capacity
        for k in range(N):
            for i in range(k + 1):
                rows.append(2 * N + k); cols.append(i); vals.append(1.0)

        # Row 3N: End SOC
        for i in range(N):
            rows.append(3 * N); cols.append(i); vals.append(1.0)

        A = sparse.coo_matrix((vals, (rows, cols)), shape=(n_rows, N)).tocsc()

        # Constraint bounds: l ≤ A·x ≤ u
        l = np.full(n_rows, -np.inf, dtype=np.float64)
        u = np.full(n_rows,  np.inf, dtype=np.float64)

        # Variable bounds
        u[:N] = var_ub
        l[:N] = var_lb

        # SOC upper: cumulative sum ≤ soc_headroom
        u[N:2*N] = max(soc_headroom, 0)

        # SOC lower: cumulative sum ≥ soc_capacity
        l[2*N:3*N] = soc_capacity

        # End SOC: allow ±5 kWh drift
        l[3*N] = -5.0
        u[3*N] = 5.0

        # Solve QP
        prob = osqp.OSQP()
        prob.setup(P, q, A, l, u, verbose=False, eps_abs=1e-4, eps_rel=1e-4,
                   max_iter=1000, warm_start=True)
        res = prob.solve()

        if res.info.status == 'solved':
            p_bat_opt = res.x
        else:
            # Fallback: no battery usage (import all from grid)
            p_bat_opt = np.zeros(N)

        # Compute resulting SOC and grid power
        soc_traj = np.zeros(N + 1)
        soc_traj[0] = soc_now
        p_grid = np.zeros(N)

        for k in range(N):
            p_bat = p_bat_opt[k]
            # SOC dynamics with efficiency
            if p_bat > 0:
                de = -p_bat * self.dt / 0.95  # discharging
            else:
                de = -p_bat * self.dt * 0.95  # charging
            soc_traj[k + 1] = soc_traj[k] + de / C
            soc_traj[k + 1] = np.clip(soc_traj[k + 1], self.soc_min, self.soc_max)
            p_grid[k] = max(p_net[k] - p_bat, 0)

        # Cost breakdown
        energy_cost = np.sum(price_fc * p_grid)
        dr_term = 0.0
        if p_dr_fc is not None and lambda_dr_fc is not None:
            dr_term = np.sum(lambda_dr_fc * p_dr_fc)
        total_cost = energy_cost - dr_term

        info = {
            'soc': soc_traj,
            'p_grid': p_grid,
            'energy_cost': energy_cost,
            'dr_term': dr_term,
            'total_cost': total_cost,
            'status': res.info.status,
        }
        return p_bat_opt, info
