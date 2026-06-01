import numpy as np
import pandas as pd
from scipy import signal, stats

class DataGenerator:
    def __init__(self, seed=42):
        self.rng = np.random.default_rng(seed)

    def _ar1(self, n: int, rho: float, sigma: float = 1.0) -> np.ndarray:
        eps = self.rng.normal(0, sigma, n)
        return signal.lfilter([1], [1, -rho], eps)

    def generate_ghi(self, n_steps: int, dt_hours: float = 1.0) -> np.ndarray:
        hours = np.arange(n_steps) * dt_hours % 24
        day_angle = 2 * np.pi * (hours - 6) / 12
        clear_sky = np.maximum(0, np.sin(day_angle))
        csi = 0.5 + 0.3 * np.sin(2 * np.pi * hours / (48 + self.rng.uniform(-4, 4)))
        csi += 0.1 * self._ar1(n_steps, 0.95, 0.05)
        csi = np.clip(csi, 0.05, 1.0)
        ghi = clear_sky * csi * 1000
        return np.where((hours < 5) | (hours > 19), 0, ghi)

    def generate_temperature(self, n_steps: int, dt_hours: float = 1.0) -> np.ndarray:
        hours = np.arange(n_steps) * dt_hours % 24
        t_base = 30 + 8 * np.sin(2 * np.pi * (hours - 14) / 24)
        noise = 0.5 * self._ar1(n_steps, 0.9, 0.3)
        return t_base + noise

    def generate_wind(self, n_steps: int, dt_hours: float = 1.0,
                      weibull_k: float = 2.1, weibull_a: float = 8.0) -> np.ndarray:
        hours = np.arange(n_steps) * dt_hours % 24
        diurnal = 2.0 * np.sin(2 * np.pi * (hours - 6) / 24)
        z = np.zeros(n_steps)
        innovations = self.rng.standard_normal(n_steps)
        for t in range(1, n_steps):
            z[t] = 0.9 * z[t-1] + np.sqrt(1 - 0.9**2) * innovations[t]
        z_diurnal = z + diurnal / weibull_a
        u = stats.norm.cdf(z_diurnal)
        wind = weibull_a * np.power(-np.log(np.clip(1 - u, 1e-10, 1)), 1.0 / weibull_k)
        return np.clip(wind, 0, 25)

    def generate_load(self, n_steps: int, dt_hours: float = 1.0,
                      peak_kw: float = 18.0, base_kw: float = 8.0) -> np.ndarray:
        hours = np.arange(n_steps) * dt_hours % 24
        morning = 0.6 * np.maximum(0, np.sin(2 * np.pi * (hours - 7) / 8))
        evening = 0.8 * np.maximum(0, np.sin(2 * np.pi * (hours - 18) / 8))
        night = 0.3 * np.ones(n_steps)
        load = base_kw + (peak_kw - base_kw) * (morning + evening + night) / (0.6 + 0.8 + 0.3)
        noise = self.rng.normal(0, 0.5, n_steps)
        return np.clip(load + noise, 3, peak_kw * 1.1)

    def get_tou_price(self, hours: np.ndarray, price_base: float = 0.12) -> np.ndarray:
        price = np.zeros_like(hours)
        price[(hours >= 22) | (hours < 6)] = 0.5 * price_base
        price[(hours >= 6) & (hours < 9)] = 0.8 * price_base
        price[(hours >= 9) & (hours < 13)] = 1.0 * price_base
        price[(hours >= 13) & (hours < 18)] = 2.0 * price_base
        price[(hours >= 18) & (hours < 22)] = 1.2 * price_base
        return price

    def generate_all(self, n_steps: int, dt_hours: float = 1.0, price_base: float = 0.12) -> pd.DataFrame:
        hours = np.arange(n_steps) * dt_hours
        hour_of_day = hours % 24
        return pd.DataFrame({
            'ghi': self.generate_ghi(n_steps, dt_hours),
            'temp': self.generate_temperature(n_steps, dt_hours),
            'wind': self.generate_wind(n_steps, dt_hours),
            'load': self.generate_load(n_steps, dt_hours),
            'price': self.get_tou_price(hour_of_day, price_base),
            'price_base': np.full(n_steps, price_base),
            'hour': hour_of_day,
        })
