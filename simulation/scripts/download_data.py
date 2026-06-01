#!/usr/bin/env python3
"""Download weather data from NASA POWER + generate synthetic load/price.
Output: CSV file ready for LSTM-TCN training."""

import os, sys, argparse
import numpy as np
import pandas as pd
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from forecasting.data_generator import DataGenerator

# Try pvlib; fall back to raw requests if unavailable
try:
    from pvlib.iotools.nasa_power import get_nasa_power
    HAVE_PVLIB = True
except ImportError:
    HAVE_PVLIB = False
    import requests


NASA_PARAMS = {
    'ALLSKY_SFC_SW_DWN': 'ghi',
    'T2M': 'temp_air',
    'WS10M': 'wind_speed',
    'WS50M': 'wind_speed_50m',
    'WD10M': 'wind_dir',
    'RH2M': 'humidity',
    'PS': 'pressure',
}


def fetch_nasa_power(lat, lon, start, end):
    """Fetch hourly weather data from NASA POWER."""
    if HAVE_PVLIB:
        print("  Using pvlib.nasa_power...")
        df, meta = get_nasa_power(
            lat, lon, start, end,
            parameters=list(NASA_PARAMS.keys()),
            map_variables=True,
        )
        df = df.rename(columns={
            'T2MDEW': 'dew_point',
            'WS50M': 'wind_speed_50m',
            'WD10M': 'wind_dir',
            'RH2M': 'humidity',
            'PS': 'pressure',
        })
    else:
        print("  pvlib not available, using raw requests...")
        url = "https://power.larc.nasa.gov/api/temporal/hourly/point"
        params = {
            'parameters': ','.join(NASA_PARAMS.keys()),
            'community': 'RE',
            'longitude': lon,
            'latitude': lat,
            'start': start.strftime('%Y%m%d'),
            'end': end.strftime('%Y%m%d'),
            'format': 'JSON',
            'time-standard': 'LST',
        }
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        raw = data['properties']['parameter']
        df = pd.DataFrame(raw)
        df.index = pd.to_datetime(df.index, format='%Y%m%d%H')
        df = df.rename(columns=NASA_PARAMS)
        df = df.replace(data['header']['fill_value'], np.nan)

    # Keep only desired columns
    keep = ['ghi', 'temp_air', 'wind_speed']
    for c in keep:
        if c not in df.columns:
            df[c] = np.nan
    df = df[keep].copy()
    df.columns = ['ghi', 'temp', 'wind']
    return df


def add_synthetic_variables(df, dg, price_base=0.12, load_peak=18.0):
    """Add load demand, price, hour features to the DataFrame."""
    n = len(df)
    hours = np.arange(n) % 24

    df['load'] = dg.generate_load(n, 1.0, load_peak)
    df['price'] = dg.get_tou_price(hours, price_base)
    df['price_base'] = np.full(n, price_base)
    df['hour'] = hours.astype(float)

    # Normalize hour cyclically
    df['hour_sin'] = np.sin(2 * np.pi * hours / 24)
    df['hour_cos'] = np.cos(2 * np.pi * hours / 24)
    return df


def compute_power(df, pv_model=None, wind_model=None):
    """Compute PV and wind power from weather data."""
    if pv_model is None:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
        from models.pv_model import PVModel
        from models.wind_model import WindModel
        pv_model = PVModel()
        wind_model = WindModel()

    df['p_pv'] = df.apply(lambda r: pv_model.compute_power(r['ghi'], r['temp']), axis=1)
    df['p_wind'] = df['wind'].map(wind_model.compute_power)
    return df


def main():
    parser = argparse.ArgumentParser(description='Download NASA POWER data + generate features')
    parser.add_argument('--lat', type=float, default=16.0, help='Latitude')
    parser.add_argument('--lon', type=float, default=108.0, help='Longitude')
    parser.add_argument('--start-year', type=int, default=2021, help='Start year')
    parser.add_argument('--end-year', type=int, default=2023, help='End year')
    parser.add_argument('--output', default=None, help='Output CSV path')
    args = parser.parse_args()

    outdir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(outdir, exist_ok=True)
    output = args.output or os.path.join(outdir, f'raw_data_{args.start_year}_{args.end_year}.csv')

    start = datetime(args.start_year, 1, 1)
    end = datetime(args.end_year, 12, 31)

    print(f"=== Download Data ===")
    print(f"Location: lat={args.lat}, lon={args.lon}")
    print(f"Period:   {start.date()} to {end.date()}")

    # Step 1: Fetch NASA POWER weather
    print("\n[1/4] Fetching NASA POWER weather data...")
    df_weather = fetch_nasa_power(args.lat, args.lon, start, end)
    print(f"  Records: {len(df_weather)}, range: {df_weather.index[0]} to {df_weather.index[-1]}")

    # Step 2: Add synthetic variables
    print("\n[2/4] Adding synthetic load + price + time features...")
    dg = DataGenerator(seed=42)
    df = add_synthetic_variables(df_weather, dg)

    # Step 3: Compute PV and wind power
    print("\n[3/4] Computing PV and wind power from weather...")
    df = compute_power(df)

    # Step 4: Save
    print(f"\n[4/4] Saving to {output}...")
    df.to_csv(output)
    print(f"  Shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    print(f"\n  Summary:\n{df[['ghi','temp','wind','load','price','p_pv','p_wind']].describe()}")
    print(f"\n  Missing values:\n{df.isnull().sum()}")
    print("\nDone!")


if __name__ == '__main__':
    main()
