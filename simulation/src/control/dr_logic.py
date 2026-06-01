import numpy as np

class DRLogic:
    def __init__(self, config=None):
        self.peak_threshold = 0.70; self.valley_threshold = 0.15
        self.alpha_clip = 0.15; self.beta_fill = 0.0
        self.lambda_peak = 1.5; self.lambda_onpeak = 1.0
        self.lambda_offpeak = 1.0; self.lambda_normal = 0.3
        if config is not None:
            dr = config.dr
            self.peak_threshold = dr.peak_threshold
            self.valley_threshold = dr.valley_threshold
            self.alpha_clip = dr.alpha_clip
            self.beta_fill = dr.beta_fill

    def compute(self, p_net, soc, load_kw, price, p_peak=18.0):
        if price >= 0.2:
            priority = 'discharge'; lam = self.lambda_onpeak
        elif price <= 0.08:
            priority = 'charge'; lam = self.lambda_offpeak
        else:
            priority = 'normal'; lam = self.lambda_normal
        p_dr_max = 0.0; mode = 'Normal'
        if p_net > self.peak_threshold * p_peak and soc > 0.20:
            p_dr_max = min(self.alpha_clip * load_kw, 25.0)
            lam = self.lambda_peak; mode = 'PeakClip'
        elif p_net < self.valley_threshold * p_peak and soc < 0.90:
            p_dr_max = -min(self.beta_fill * load_kw, 25.0)
            lam = self.lambda_normal; mode = 'ValleyFill'
        else:
            mode = priority.capitalize() if priority != 'normal' else 'Normal'
        return {'lambda_dr': lam, 'p_dr_max': p_dr_max, 'dr_mode': mode, 'priority': priority}
