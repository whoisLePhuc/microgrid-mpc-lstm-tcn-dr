import numpy as np

class ConverterLTVModel:
    def __init__(self, l_pv=66e-3, rl_pv=0.066, l_bat=66e-3, rl_bat=0.066,
                 l_wind=5e-3, rl_wind=0.015, c_dc=1.04e-4, ts=100e-6):
        self.l_pv = l_pv; self.rl_pv = rl_pv
        self.l_bat = l_bat; self.rl_bat = rl_bat
        self.l_wind = l_wind; self.rl_wind = rl_wind
        self.c_dc = c_dc; self.ts = ts

    def build_matrices(self, u0, vdc0, il0):
        ts = self.ts; u_pv, u_bat, u_wind = u0
        i_pv, i_bat, i_wind = il0
        A = np.array([
            [1-ts*self.rl_pv/self.l_pv,0,0,ts*(u_pv-1)/self.l_pv,0],
            [0,1-ts*self.rl_bat/self.l_bat,0,ts*(u_bat-1)/self.l_bat,0],
            [0,0,1-ts*self.rl_wind/self.l_wind,ts*(u_wind-1)/self.l_wind,0],
            [ts*(1-u_pv)/self.c_dc,ts*(1-u_bat)/self.c_dc,ts*(1-u_wind)/self.c_dc,1,0],
            [0,ts/3600/50,0,0,1],
        ])
        B = np.array([
            [ts*vdc0/self.l_pv,0,0], [0,ts*vdc0/self.l_bat,0],
            [0,0,ts*vdc0/self.l_wind],
            [-ts*i_pv/self.c_dc,-ts*i_bat/self.c_dc,-ts*i_wind/self.c_dc],
            [0,0,0],
        ])
        Bd = np.array([
            [ts/self.l_pv,0,0], [0,ts/self.l_bat,0],
            [0,0,ts/self.l_wind], [0,0,-ts/self.c_dc], [0,0,0],
        ])
        return A, B, Bd
