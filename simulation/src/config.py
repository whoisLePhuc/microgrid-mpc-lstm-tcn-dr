from dataclasses import dataclass, field

@dataclass
class PVConfig:
    capacity_kwp: float = 20.0
    n_modules: int = 80
    module_pmax: float = 250.0
    module_voc: float = 43.22
    module_isc: float = 7.76
    module_vmp: float = 35.2
    module_imp: float = 7.1
    temp_coeff_voc: float = -0.30278
    temp_coeff_isc: float = 0.035271
    eta_pv: float = 0.18
    area_m2: float = 130.0

@dataclass
class WindConfig:
    rated_power_kw: float = 10.0
    v_cut_in: float = 3.0
    v_rated: float = 12.0
    v_cut_out: float = 25.0
    rotor_diameter_m: float = 7.0
    hub_height_m: float = 30.0
    ref_height_m: float = 10.0
    roughness_alpha: float = 0.14
    cp_max: float = 0.45

@dataclass
class BatteryConfig:
    capacity_kwh: float = 50.0
    voltage_nominal: float = 120.0
    soc_min: float = 0.20
    soc_max: float = 0.90
    soc_init: float = 0.50
    eta_ch: float = 0.95
    eta_dch: float = 0.95
    p_ch_max_kw: float = 25.0
    p_dch_max_kw: float = 25.0

@dataclass
class ConverterConfig:
    l_pv: float = 66e-3
    rl_pv: float = 0.066
    l_bat: float = 66e-3
    rl_bat: float = 0.066
    l_wind: float = 5e-3
    rl_wind: float = 0.015
    c_dc: float = 1.04e-4
    f_sw: float = 10e3
    v_dc_ref: float = 800.0
    v_dc_min: float = 720.0
    v_dc_max: float = 880.0

@dataclass
class MPCConfig:
    dt_inner: float = 4e-6
    dt_mpc: float = 100e-6
    np_inner: int = 2
    nc_inner: int = 1
    w_pv: float = 10.0
    w_bat: float = 50.0
    w_wind: float = 10.0
    w_dc: float = 100.0
    w_soc: float = 1.0
    f_effort: float = 0.04
    dt_outer: float = 3600.0
    np_outer: int = 24
    nc_outer: int = 24
    beta_dr: float = 1.0

@dataclass
class DRConfig:
    price_offpeak: float = 0.5
    price_valley: float = 0.8
    price_midpeak: float = 1.0
    price_onpeak: float = 2.0
    price_evening: float = 1.2
    price_base: float = 0.12
    peak_threshold: float = 0.70
    valley_threshold: float = 0.15
    alpha_clip: float = 0.15
    beta_fill: float = 0.0
    lambda_peak: float = 1.5
    lambda_offpeak: float = 1.0
    lambda_onpeak: float = 1.0
    lambda_normal: float = 0.3
    sigmoid_z: float = 10.0
    soc_charge_stop: float = 0.85
    soc_charge_resume: float = 0.80
    soc_discharge_stop: float = 0.30
    soc_discharge_resume: float = 0.35
    hysteresis_power: float = 0.05

@dataclass
class LSTMConfig:
    input_steps: int = 12
    n_features: int = 6
    n_targets: int = 5
    horizon: int = 4
    lstm_units_1: int = 256
    lstm_units_2: int = 64
    tcn_blocks: int = 3
    tcn_filters: int = 128
    kernel_size: int = 3
    dropout: float = 0.2
    learning_rate: float = 0.001
    epochs: int = 100
    batch_size: int = 100
    early_stopping_patience: int = 10

@dataclass
class SimulationConfig:
    n_hours: int = 168
    n_days: int = 7
    load_peak_kw: float = 18.0
    grid_max_kw: float = 25.0
    inv_max_kva: float = 30.0
    p_rated_total: float = 30.0

@dataclass
class SystemConfig:
    pv: PVConfig = field(default_factory=PVConfig)
    wind: WindConfig = field(default_factory=WindConfig)
    battery: BatteryConfig = field(default_factory=BatteryConfig)
    converter: ConverterConfig = field(default_factory=ConverterConfig)
    mpc: MPCConfig = field(default_factory=MPCConfig)
    dr: DRConfig = field(default_factory=DRConfig)
    lstm: LSTMConfig = field(default_factory=LSTMConfig)
    sim: SimulationConfig = field(default_factory=SimulationConfig)
