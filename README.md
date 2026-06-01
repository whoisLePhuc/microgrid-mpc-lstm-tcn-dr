# Microgrid MPC + LSTM-TCN + Demand Response

**Real-time control simulation for a grid-connected PV–Wind–Battery microgrid** integrating Model Predictive Control (MPC), hybrid LSTM-TCN time-series forecasting, and a two-layer Demand Response (DR) strategy.

[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![TensorFlow](https://img.shields.io/badge/tensorflow-2.16+-orange.svg)](https://www.tensorflow.org/)
[![OSQP](https://img.shields.io/badge/osqp-0.6+-green.svg)](https://osqp.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

---

## Overview

This project implements an **energy management system (EMS)** for a grid-connected microgrid consisting of:

| Component | Specification |
|-----------|---------------|
| ☀️ PV array | 20 kWp (80 × ASW-250P modules) |
| 💨 Wind turbine | 10 kW (IEC class, rotor Ø7 m) |
| 🔋 Battery storage | 50 kWh Li-ion, 120 V, SOC 20–90% |
| ⚡ Bidirectional inverter | 30 kVA |
| 🔌 Grid connection | 25 kW max import/export |
| 💡 Peak load | 18 kW |

**Three controllers** operate hierarchically:

1. **EMSMPC** — Economic MPC for outer-loop battery scheduling (24 h horizon, OSQP QP solver)
2. **PMS** — 6-mode Power Management System (state machine with hysteresis)
3. **DRLogic** — 2-layer Demand Response (price-based TOU + threshold-based Peak/Valley)

The forecasting module uses a **hybrid LSTM–TCN** model (R² = 0.94 for PV power) trained on 3 years of NASA POWER data from Da Nang, Vietnam.

---

## 5 Simulation Scenarios

| # | Scenario | MPC | TOU Price | Threshold DR | Description |
|---|----------|:---:|:---------:|:------------:|-------------|
| S1 | Rule-based | ❌ | ❌ | ❌ | PMS only baseline |
| S2 | EMS-MPC | ✅ | ❌ | ❌ | Peak shaving with flat price |
| S3 | MPC + TOU | ✅ | ✅ | ❌ | Economic arbitrage |
| S4 | Threshold DR | ✅ | ❌ | ✅ | Peak/Valley clipping |
| **S5** | **Full DR** | ✅ | ✅ | ✅ | Proposed method |

### Key Results (168 h / 7-day simulation)

| Scenario | Cost ($) | VRI (%) | RE Ratio (%) | PeakRed (%) |
|----------|:--------:|:-------:|:------------:|:-----------:|
| S1 | 127.0 | 0.51 | 45.9 | 0.0 |
| S2 | 109.7 | 0.50 | 45.5 | −16.1 |
| S3 | **72.9** | 0.50 | 45.6 | −15.8 |
| S4 | 16.2 | 0.47 | 46.7 | −16.1 |
| **S5** | **−18.8** | 0.47 | 46.8 | −15.8 |

> S5 is the **only profitable scenario** — it sells energy back to the grid at peak TOU rates, achieving negative net cost.

### LSTM-TCN Forecast Accuracy

| Target | R² | Notes |
|--------|:---|-------|
| PV Power | **0.941** | Excellent |
| Temperature | **0.871** | Good |
| Load | **0.870** | Good |
| Price | **1.000** | Perfect (deterministic TOU) |
| Wind Power | −0.026 | Poor — chaotic at hourly resolution |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      main.py (Orchestrator)                      │
│  run_perfect_forecast() → run_lstm_forecast() → Sensitivity      │
│                             → Plotter (12 thesis-quality plots)  │
└──────┬─────────────────────┬─────────────────────┬───────────────┘
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐
│  Simulator   │   │  LSTMTCN     │   │  SensitivityAnalysis │
│ .run_outer() │   │  .predict()  │   │  battery / dr / err  │
│  .run_all()  │   │  (TensorFlow)│   └──────────────────────┘
└──────┬───────┘   └──────────────┘
       │
       ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
│  EMSMPC      │   │  PMS         │   │  DRLogic         │
│  OSQP QP     │   │  6-mode      │   │  Price + Peak    │
│  24h horizon │   │  state mach. │   │  Valley Fill     │
└──────────────┘   └──────────────┘   └──────────────────┘
       │                     │                     │
       └─────────────────────┼─────────────────────┘
                             ▼
               ┌─────────────────────────┐
               │  Models Layer           │
               │  PVModel · WindModel    │
               │  BatteryModel · LTV Conv│
               └─────────────────────────┘
                             ▼
               ┌─────────────────────────┐
               │  DataGenerator          │
               │  (synthetic weather) +  │
               │  NASA POWER (real data) │
               └─────────────────────────┘
```

### PMS 6 Operating Modes

```
EPM (P_net < 0 — surplus):
  M1: Charge battery from excess RE
  M2: Valley Fill — charge from grid (off-peak)
  M3: Export to grid

DPM (P_net > 0 — deficit):
  M4: Peak Clip — discharge + shed 15% load
  M5: Discharge battery
  M6: Import from grid
```

---

## Repository Structure

```
microgrid-mpc-lstm-tcn-dr/
├── simulation/
│   ├── src/                          # Core source code
│   │   ├── main.py                   # Entry point
│   │   ├── config.py                 # Dataclass parameters
│   │   ├── models/                   # Physical models
│   │   │   ├── pv_model.py           # PV single-diode
│   │   │   ├── wind_model.py         # Wind turbine IEC cubic
│   │   │   └── battery_model.py      # Battery Coulomb counting
│   │   ├── control/
│   │   │   ├── ems_mpc.py            # Economic MPC (OSQP)
│   │   │   ├── mpc_controller.py     # Inner-loop MPC (OSQP)
│   │   │   ├── pms.py                # 6-mode PMS state machine
│   │   │   ├── dr_logic.py           # 2-layer DR logic
│   │   │   └── converter_model.py    # LTV converter (5-state)
│   │   ├── forecasting/
│   │   │   ├── lstm_tcn_model.py     # LSTM-TCN hybrid model
│   │   │   └── data_generator.py     # Synthetic weather/load
│   │   ├── engine/
│   │   │   ├── simulator.py          # Core simulation engine
│   │   │   └── scenarios.py          # S1–S5 definitions
│   │   ├── analysis/
│   │   │   ├── kpi_calculator.py     # 7 KPI functions
│   │   │   └── sensitivity.py        # Sensitivity sweeps
│   │   └── visualization/
│   │       └── plots.py              # 12 plot types (thesis)
│   ├── scripts/                      # Pipeline scripts
│   │   ├── download_data.py          # NASA POWER → CSV
│   │   ├── prepare_data.py           # Sliding windows → NPZ
│   │   ├── train_lstm_tcn.py         # Train LSTM-TCN model
│   │   ├── evaluate_forecast.py      # RMSE/MAE/R² plots
│   │   └── run_comparison.py         # Perfect vs LSTM
│   ├── data/                         # Training data (NPZ + CSV)
│   ├── models/                       # Trained model + metrics
│   ├── outputs/figures/              # Result figures + JSON
│   └── requirements.txt
├── theory/                           # Thesis (Vietnamese)
│   ├── thesis/                       # 5 chapters
│   ├── modules/                      # 5 module documents
│   ├── design/                       # Design docs
│   └── references/                   # 57 APA 7th refs + PDFs
├── graphify-out/                     # Code knowledge graph
│   ├── GRAPH_REPORT.md               # 177 nodes, 317 edges
│   ├── graph.html                    # Interactive visualization
│   └── graph.json
└── logs/                             # Implementation history
```

---

## Quick Start

### Prerequisites

- Python 3.13+
- TensorFlow 2.16+
- OSQP solver

### Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/microgrid-mpc-lstm-tcn-dr.git
cd microgrid-mpc-lstm-tcn-dr

# Install dependencies
pip install -r simulation/requirements.txt

# Run the full simulation
python simulation/src/main.py
```

### Pipeline Steps (Optional)

```bash
# 1. Download weather data from NASA POWER
python simulation/scripts/download_data.py

# 2. Prepare sliding windows
python simulation/scripts/prepare_data.py

# 3. Train LSTM-TCN forecast model
python simulation/scripts/train_lstm_tcn.py

# 4. Evaluate forecasting accuracy
python simulation/scripts/evaluate_forecast.py

# 5. Compare perfect vs LSTM forecast
python simulation/scripts/run_comparison.py
```

---

## Dependencies

```
numpy>=1.26
scipy>=1.13
pandas>=2.2
matplotlib>=3.9
osqp>=0.6
tensorflow>=2.16
```

---

## Theory & References

This project builds on three foundational papers:

1. **Limouni et al. (2025)** — *Intelligent real time control strategy and power management based on MPC and LSTM-TCN model* — MPC + LSTM-TCN for standalone DC microgrid [Paper](theory/references/papers/)
2. **Panda et al. (2025)** — *Optimization-based energy management for grid-connected photovoltaic–battery systems using demand response* — PSO + DR for grid-connected PV-battery [Paper](theory/references/papers/)
3. **Geetha (2026)** — *Hybrid solar–wind–battery microgrid optimization using reinforcement learning* — RL for autonomous energy management

**Research gap filled**: No prior work combines **PV + Wind + MPC + LSTM-TCN + DR (TOU + Threshold)** in a single grid-connected microgrid system.

Full references: [REFERENCES_MASTER.md](theory/references/REFERENCES_MASTER.md) (57 citations, APA 7th ed.)

### Thesis (Vietnamese)

| Chapter | Title | Content |
|---------|-------|---------|
| Ch. 1 | Introduction | Motivation, objectives, research gap |
| Ch. 2 | Theoretical foundations | PV model, wind turbine, MPC, LSTM-TCN, DR |
| Ch. 3 | System model | Architecture, parameters, cost function, DR integration |
| Ch. 4 | Proposed control algorithms | LSTM-TCN, MPC loop, DR scheduling, PMS state machine |
| Ch. 5 | Simulation & results | 5 scenarios, KPIs, sensitivity analysis |

---

## Outputs

All simulation outputs are saved to `simulation/outputs/figures/`:

- `kpi_comparison.png` — 6-panel KPI bar chart across scenarios
- `time_series_s5.png` — 5-panel time series (PV, wind, battery, grid, VDC)
- `cost_bar.png` — Cost comparison across scenarios
- `cost_accumulation.png` — Cumulative cost over time
- `load_profile_dr.png` — Load with DR activation markers
- `mode_timeline.png` — PMS mode Gantt chart
- `soc_comparison.png` — SOC comparison S1 vs S3 vs S5
- `dr_activation.png` — DR activation timeline
- `bat_sensitivity.png` — Battery capacity sensitivity
- `dr_sensitivity.png` — DR ratio sensitivity
- `forecast_validation.png` — Forecast vs actual (PV, load, price)
- `comparison_perfect_vs_lstm.png` — Perfect vs LSTM forecast cost

---
