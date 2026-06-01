"""
Session state persistence for the Streamlit dashboard.
Saves/loads simulation results to/from disk so they survive page refreshes.
"""

import pickle
from pathlib import Path
from settings import CACHE_DIR

CACHE_FILE = CACHE_DIR / 'session_state.pkl'
PARAM_FILE = CACHE_DIR / 'params.txt'

CACHE_KEYS = [
    'results', 'kpi_table', 'df', 'bat_sens', 'dr_sens',
    'mc_data', '_last_params', '_has_run',
]


def _ensure_cache_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def cache_exists():
    """Check whether a persisted cache is available."""
    return CACHE_FILE.exists()


def save_session(session_state):
    """Pickle relevant session_state keys to disk."""
    _ensure_cache_dir()
    data = {}
    for key in CACHE_KEYS:
        if key in session_state and session_state[key] is not None:
            data[key] = session_state[key]
    if data:
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(data, f)


def load_session(session_state):
    """Restore cached keys into session_state (only if missing)."""
    if not CACHE_FILE.exists():
        return False
    try:
        with open(CACHE_FILE, 'rb') as f:
            data = pickle.load(f)
    except Exception:
        return False
    for key, value in data.items():
        if key not in session_state or session_state[key] is None:
            session_state[key] = value
    return True


def save_params(param_hash):
    """Save the parameter hash that produced the cached result."""
    _ensure_cache_dir()
    PARAM_FILE.write_text(param_hash)


def load_params():
    """Return the saved param hash, or empty string."""
    if PARAM_FILE.exists():
        return PARAM_FILE.read_text().strip()
    return ''


def clear_cache():
    """Remove all cached files."""
    for p in [CACHE_FILE, PARAM_FILE]:
        if p.exists():
            p.unlink()
