class WindModel:
    def __init__(self, rated_power_kw: float = 10.0, v_ci: float = 3.0,
                 v_r: float = 12.0, v_co: float = 25.0,
                 hub_height: float = 30.0, ref_height: float = 10.0,
                 alpha: float = 0.14):
        self.rated_power_kw = rated_power_kw
        self.v_ci = v_ci
        self.v_r = v_r
        self.v_co = v_co
        self.hub_height = hub_height
        self.ref_height = ref_height
        self.alpha = alpha

    def adjust_speed(self, v_ref: float) -> float:
        return v_ref * (self.hub_height / self.ref_height) ** self.alpha

    def compute_power(self, wind_speed: float) -> float:
        if wind_speed < self.v_ci or wind_speed > self.v_co:
            return 0.0
        if wind_speed >= self.v_r:
            return self.rated_power_kw
        ratio = (wind_speed - self.v_ci) / (self.v_r - self.v_ci)
        return self.rated_power_kw * ratio ** 3
