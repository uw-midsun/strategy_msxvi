import numpy as np
from db.load import load_data_to_memory
from src.utils import _get_data

M = 300.0  # Mass of vehicle (kg)
G = 9.81  # Acceleration due to gravity (m/s^2)
C_R1 = 0.004  # Rolling resistance coefficient 1
C_R2 = 0.052  # Rolling resistance coefficient 2
C_D = 0.13  # Drag coefficient
A_DRAG = 1.357  # Cross-sectional area (m^2)
P = 1.293  # Air density (kg/m^3)
N = 0.16  # Efficiency of solar panel (%)
A_SOLAR = 4.0  # Area of solar panel (m^2)
BAT_CAPACITY = 40 * 3.63 * 36 * 3600  # Pack capacity (J)

def map_route(d): 
    routedf, _ = _get_data()
    return routedf.iloc[(routedf['distance'] - d).abs().idxmin()]

# def map_irrad(d, t):
#     _, irradf = _get_data()
#     idx_t = (irradf['timestamp'] - t).abs().idxmin()
#     idx_d = d // 5000 - 1
#     ds = irradf[irradf['timestamp'] == irradf.loc[idx_t, 'timestamp']]
#     return ds.index[np.abs(ds.index - idx_d).argmin()]

def map_irrad(d, t):
    _, irradf = _get_data()
    idx_t = (irradf['timestamp'] - t).abs().idxmin()
    ts = irradf.loc[idx_t, 'timestamp']
    ds = irradf[irradf['timestamp'] == ts]
    idx_d = d // 5000 - 1
    pos = np.abs(ds.index - idx_d).argmin()
    return ds.iloc[pos]

def rr(v): return (M * G * C_R1 + 4 * C_R2 * v) * v
def drag(v): return 0.5 * P * C_D * A_DRAG * v**3
def grad(v, theta): return max(0, M * G * np.sin(theta) * v)
def solar(G): return A_SOLAR * G * N

def sim(vs, dt, d0):
    n = len(vs)
    sp, rr_v, dr_v, gr_v, cap = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n), np.full(n, BAT_CAPACITY)
    d = d0
    _, irradf = _get_data()
    t0 = irradf['timestamp'][0]

    for i, v in enumerate(vs):
        d += v * dt
        t = t0 + i * dt
        theta = np.deg2rad(map_route(d)['road_angle'])
        G = map_irrad(d, t)['ghi']

        sp[i] = solar(G) * dt
        rr_v[i] = rr(v) * dt
        dr_v[i] = drag(v) * dt
        gr_v[i] = grad(v, theta) * dt

        # Update battery capacity
        if i > 0:
            cap[i] = cap[i-1] + sp[i-1] - rr_v[i-1] - dr_v[i-1] - gr_v[i-1]
            if cap[i] > BAT_CAPACITY: cap[i] = BAT_CAPACITY
            if cap[i] < 0: d -= v * dt  # If we run out of battery at this step, don't reward the optimization function by letting distance travelled continue to accumulate

    cap /= dt # J to Wh
    return -cap[-1], np.column_stack((sp, rr_v, dr_v, gr_v, cap)), d

map_irrad(0,0)