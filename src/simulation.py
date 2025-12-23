import numpy as np
from datetime import datetime
from tqdm import tqdm
import matplotlib.pyplot as plt
from db.load import load_data_to_memory
from src.utils import _get_data, _map_route, _map_irrad

M_VEHICLE = 300.0  # Mass of vehicle (kg)
GRAVITY = 9.81  # Acceleration due to gravity (m/s^2)
C_R1 = 0.004  # Rolling resistance coefficient 1
C_R2 = 0.052  # Rolling resistance coefficient 2
C_D = 0.13  # Drag coefficient
A_DRAG = 1.357  # Cross-sectional area (m^2)
P_AIR = 1.293  # Air density (kg/m^3)
N_SOLAR = 0.16  # Efficiency of solar panel (%)
A_SOLAR = 4.0  # Area of solar panel (m^2)
BAT_CAPACITY = 40 * 3.63 * 36 * 3600  # Pack capacity (J)

def rr(v): 
    return (M_VEHICLE * GRAVITY * C_R1 + 4 * C_R2 * v) * v

def drag(v): 
    return 0.5 * P_AIR * C_D * A_DRAG * v**3

def grad(v, theta): 
    return max(0, M_VEHICLE * GRAVITY * np.sin(theta) * v)

def solar(i): 
    return A_SOLAR * i * N_SOLAR

def sim(vs, dt, d0, t0):
    n = len(vs)

    solar_power, rolling_resistance, drag_resistance, gradient_resistance, battery_capacity = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n), np.full(n, BAT_CAPACITY)

    d = d0
    t = t0

    for i, v in enumerate(tqdm(vs, desc="Running simulation", unit="step")):
        solar_irradiance = _map_irrad(d, t)['ghi']
        
        solar_power[i] = solar(solar_irradiance) * dt
        rolling_resistance[i] = rr(v) * dt
        theta = np.deg2rad(_map_route(d)['road_angle']); drag_resistance[i] = drag(v) * dt
        gradient_resistance[i] = grad(v, theta) * dt

        battery_capacity[i] = battery_capacity[i-1] + solar_power[i] - rolling_resistance[i] - drag_resistance[i] - gradient_resistance[i]
        
        if battery_capacity[i] > BAT_CAPACITY: 
            battery_capacity[i] = BAT_CAPACITY

        if battery_capacity[i] < 0: 
            break
        
        d += v * dt
        t += dt

    return np.column_stack((solar_power, rolling_resistance,  drag_resistance, gradient_resistance, battery_capacity)), d, t

if __name__ == "__main__":
    vs = np.full(3600, 15).astype(int)
    dt = int(1)
    d0 = int(1)
    t0 = int(datetime(2024, 7, 1, 12, 0).timestamp())

    results, d_final, t_final = sim(vs, dt, d0, t0)
    results /= 3600  # Convert J to Wh
    print(f"Distance: {d_final:.0f} m | Time: {datetime.fromtimestamp(t_final)} | Battery: {results[-1, 4]:.1f} Wh")