"""
Dashboard configuration — constants, themes, presets, and slider help text.
No Streamlit or plotting dependencies — can be imported by any module.
"""

from pathlib import Path

# ── Repo root ─────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[1]

# ── Scenarios ──────────────────────────────────────────────────────
SCENARIO_LABELS = {
    'S1': 'Rule-based', 'S2': 'EMS-MPC', 'S3': 'MPC+TOU',
    'S4': 'Threshold DR', 'S5': 'Full DR',
}
ALL_SCENARIOS = ['S1', 'S2', 'S3', 'S4', 'S5']

# ── Parameter defaults & presets ───────────────────────────────────
PARAM_DEFAULTS = {
    'bat_cap': 50, 'dr_alpha': 0.15, 'peak_pen': 0.5,
    'horizon': 24, 'n_hours': 168, 'pv_kwp': 20, 'wind_kw': 10,
}
PRESETS = {
    'Default': PARAM_DEFAULTS,
    'Max Save': {'bat_cap': 75, 'dr_alpha': 0.25, 'peak_pen': 0.3,
                 'horizon': 48, 'n_hours': 168, 'pv_kwp': 20, 'wind_kw': 10},
    'High RE':  {'bat_cap': 100, 'dr_alpha': 0.20, 'peak_pen': 0.5,
                 'horizon': 24, 'n_hours': 168, 'pv_kwp': 50, 'wind_kw': 20},
}
SLIDER_HELP = {
    'bat_cap': 'Larger battery stores more solar energy but costs more. Thesis: 50 kWh.',
    'dr_alpha': 'Fraction of load shed during Peak Clip events. Higher = more aggressive DR. Thesis: 0.15.',
    'peak_pen': 'Quadratic penalty on grid import above threshold. TOU scenarios use 0.3, flat use 0.5.',
    'horizon': 'MPC look-ahead hours. Longer horizon captures more TOU cycles but slower. Thesis: 24.',
    'n_hours': 'Total simulation length. 168h = 7 days for thesis results.',
    'pv_kwp': 'PV array rated capacity. Thesis: 20 kWp (80 x 250W modules).',
    'wind_kw': 'Wind turbine rated power. Thesis: 10 kW, rotor 7m.',
}

# ── Color themes ───────────────────────────────────────────────────
THEMES = {
    'Thesis': {
        'colors': ['#6C6C6C', '#4E79A7', '#59A14F', '#F28E2B', '#E15759'],
        'template': 'plotly_white',
        'mode': 'light',
    },
    'Dark': {
        'colors': ['#BBBBBB', '#5DA5DA', '#60BD68', '#FAA43A', '#F15854'],
        'template': 'plotly_dark',
        'mode': 'dark',
    },
    'Vibrant': {
        'colors': ['#333333', '#1F77B4', '#2CA02C', '#FF7F0E', '#D62728'],
        'template': 'plotly_white',
        'mode': 'light',
    },
    'Pastel': {
        'colors': ['#B3B3B3', '#8DA0CB', '#66C2A5', '#FFD92F', '#E78AC3'],
        'template': 'plotly_white',
        'mode': 'light',
    },
}

# ── Paths for forecast artifacts ───────────────────────────────────
FORECAST_MODEL_PATH = REPO_ROOT / 'simulation' / 'models' / 'lstm_tcn_model.keras'
FORECAST_METRICS_PATH = REPO_ROOT / 'simulation' / 'models' / 'forecast_metrics.json'
FORECAST_TS_IMG = REPO_ROOT / 'simulation' / 'models' / 'forecast_timeseries.png'
FORECAST_SCATTER_IMG = REPO_ROOT / 'simulation' / 'models' / 'forecast_scatter.png'

# ── Cache ──────────────────────────────────────────────────────────
CACHE_DIR = REPO_ROOT / 'dashboard' / '.cache'
