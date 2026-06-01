"""
Streamlit UI components — sidebar, theme, KPI helpers.
"""

import plotly.io as pio
import streamlit as st
import pandas as pd
import numpy as np

from settings import (
    ALL_SCENARIOS, SCENARIO_LABELS,
    PARAM_DEFAULTS, PRESETS, SLIDER_HELP, THEMES,
)
from cache import cache_exists, clear_cache as _clear_cache_files


# ── Theme system ───────────────────────────────────────────────────
def get_theme():
    """Return current theme config from session state. Sets Plotly template."""
    key = st.session_state.get('theme', 'Thesis')
    cfg = THEMES.get(key, THEMES['Thesis'])
    pio.templates.default = cfg['template']
    return cfg


def colors():
    """Shortcut for current color palette."""
    return get_theme()['colors']


def apply_bg_theme():
    """Inject CSS to match Streamlit background to selected theme.
    Uses only CSS (no JS) — multiple style blocks are harmless because
    !important rules from the last-loaded block override earlier ones.
    """
    cfg = get_theme()
    mode = cfg['mode']

    if mode == 'dark':
        bg = '#0E1117'
        sb = '#1E2128'
        tc = '#E0E0E0'
        ml = '#A0A0A0'
    else:
        bg = '#FFFFFF'
        sb = '#F0F2F6'
        tc = '#31333F'
        ml = '#666666'

    st.markdown(f"""
    <style>
    .stApp   {{ background-color: {bg} !important; }}
    .stSidebar {{ background-color: {sb} !important; }}
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp p, .stApp li, .stApp label,
    .stApp .stMarkdown, .stApp .stMarkdown p,
    .stApp .stMarkdown h1, .stApp .stMarkdown h2,
    .stApp .stMarkdown h3, .stApp .stMarkdown h4,
    .stApp .stMarkdown strong {{ color: {tc} !important; }}
    .stApp .stCheckbox label, .stApp .stSlider label,
    .stApp .stSelectbox label, .stApp .stRadio label {{ color: {tc} !important; }}
    .stApp div[data-testid="stMetricValue"] {{ color: {tc} !important; }}
    .stApp div[data-testid="stMetricLabel"] {{ color: {ml} !important; }}
    .stApp button[kind="primary"] {{ background-color: #4E79A7 !important; color: #FFF !important; }}
    </style>
    """, unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────
def render_sidebar():
    """Build sidebar controls and return parameter dict."""
    with st.sidebar:
        st.title('MICROGRID SIM')

        st.divider()
        st.markdown('### SCENARIOS')
        selected = []
        for s in ALL_SCENARIOS:
            if st.checkbox(f'{s} — {SCENARIO_LABELS[s]}', value=(s == 'S5')):
                selected.append(s)
        if not selected:
            st.warning('Select at least one scenario')
            selected = ['S5']

        st.divider()
        st.markdown('### PARAMETERS')

        for k, v in PARAM_DEFAULTS.items():
            if k not in st.session_state:
                st.session_state[k] = v

        st.markdown('**Quick presets:**')
        pcols = st.columns(3)
        for i, (name, vals) in enumerate(PRESETS.items()):
            if pcols[i].button(name, use_container_width=True):
                for k, v in vals.items():
                    st.session_state[k] = v
                st.rerun()

        bat_cap = st.slider('Battery capacity (kWh)', 25, 100,
                            help=SLIDER_HELP['bat_cap'], key='bat_cap')
        dr_alpha = st.slider('DR clip ratio α', 0.05, 0.30,
                             help=SLIDER_HELP['dr_alpha'], key='dr_alpha')
        peak_pen = st.slider('Peak penalty weight', 0.0, 1.0,
                             help=SLIDER_HELP['peak_pen'], key='peak_pen')
        horizon = st.slider('MPC horizon (h)', 12, 48,
                            help=SLIDER_HELP['horizon'], key='horizon')
        n_hours = st.slider('Simulation duration (h)', 24, 336,
                            help=SLIDER_HELP['n_hours'], key='n_hours')
        pv_kwp = st.slider('PV capacity (kWp)', 10, 50,
                           help=SLIDER_HELP['pv_kwp'], key='pv_kwp')
        wind_kw = st.slider('Wind rated power (kW)', 5, 20,
                            help=SLIDER_HELP['wind_kw'], key='wind_kw')

        st.divider()
        st.markdown('### THEME')
        st.selectbox('Color palette', list(THEMES.keys()),
                     key='theme', label_visibility='collapsed')

        st.divider()
        st.markdown('### MONTE CARLO')
        mc_enabled = st.checkbox('Enable Monte Carlo', value=False,
                                 help='Run N times with different random seeds.')
        mc_runs = st.slider('Number of runs', 5, 50, 20, 5, disabled=not mc_enabled)

        st.divider()
        auto = st.checkbox('Auto-run on param change', value=False)
        run_btn = st.button('RUN SIMULATION', type='primary', use_container_width=True)

        # ── Cache controls ──────────────────────────────────────────
        if cache_exists():
            st.divider()
            st.markdown('### CACHE')
            st.caption('Cached results available — restored on load.')
            if st.button('🗑️ Clear Cache', use_container_width=True,
                         help='Remove saved results and reset.'):
                _clear_cache_files()
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

        return {
            'selected_scenarios': selected,
            'bat_cap': bat_cap, 'dr_alpha': dr_alpha,
            'peak_pen': peak_pen, 'horizon': horizon,
            'n_hours': n_hours, 'pv_kwp': pv_kwp, 'wind_kw': wind_kw,
            'mc_enabled': mc_enabled, 'mc_runs': mc_runs,
            'auto_run': auto, 'run_btn': run_btn,
        }


# ── KPI DataFrame builder ──────────────────────────────────────────
def build_kpi_dataframe(kpi_table):
    """Build a clean KPI DataFrame for display."""
    rows = []
    for s, k in kpi_table.items():
        rows.append({
            'Scenario': f'{s} — {SCENARIO_LABELS.get(s, "")}',
            'VRI (%)': f'{k.get("VRI", 0):.2f}',
            'Cost ($)': f'{k.get("Cost", 0):.1f}',
            'RE Ratio (%)': f'{k.get("RE_Ratio", 0):.1f}',
            'Peak Red. (%)': f'{k.get("Peak_Red", 0):.1f}',
            'Settle (s)': f'{k.get("Settle_Time", 0):.1f}',
            'Overshoot (%)': f'{k.get("Overshoot", 0):.1f}',
        })
    return pd.DataFrame(rows).set_index('Scenario')
