from dataclasses import dataclass

@dataclass
class ScenarioConfig:
    name: str; use_mpc: bool; use_tou: bool
    use_threshold_dr: bool; pms_only: bool; description: str

SCENARIOS = {
    'S1': ScenarioConfig('S1_RuleBased', False, False, False, True,
        'Rule-based PMS, no MPC/DR'),
    'S2': ScenarioConfig('S2_MPCOnly', True, False, False, False,
        'MPC tracking only'),
    'S3': ScenarioConfig('S3_PriceDR', True, True, False, False,
        'MPC + TOU pricing'),
    'S4': ScenarioConfig('S4_ThresholdDR', True, False, True, False,
        'MPC + Peak/Valley'),
    'S5': ScenarioConfig('S5_FullDR', True, True, True, False,
        'MPC + Full DR (proposed)'),
}

def get_scenario(name):
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {name}")
    return SCENARIOS[name]

def scenario_list():
    return list(SCENARIOS.keys())
