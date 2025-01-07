import numpy as np
from db import load_data_to_memory

# Constants
M = 300.0  # Mass of vehicle (kg)
G = 9.81  # Acceleration due to gravity (m/s^2)
C_R1 = 0.004  # Rolling resistance coefficient 1
C_R2 = 0.052  # Rolling resistance coefficient 2
C_D = 0.13  # Drag coefficient
A_DRAG = 1.357  # Cross-sectional area (m^2)
P = 1.293  # Air density (kg/m^3)
N = 0.16  # Efficiency of solar panel (%)
A_SOLAR = 4.0  # Area of solar panel (m^2)
BAT_CAPACITY = 40 * 3.63 * 36  # Pack capacity (Wh)

# ETL & Utils
route_model_df, irradiance_df = load_data_to_memory()

def map_distance_to_id(route_model_df, stage_name, distance):
    closest_row = route_model_df.iloc[(route_model_df['distance'] - distance).abs().idxmin()]
    return closest_row

# Power (In/Out)
def rolling_resistance(v):
    return (M * G * C_R1 + 4 * C_R2 * v) * v

def drag_resistance(v):
    return 0.5 * P * C_D * A_DRAG * v ** 3

def gradient_resistance(v, theta):
    return M * G * np.sin(theta) * v

def mock_irradiance(time_seconds, day_duration=28800, peak_irradiance=1000):
    normalized_time = time_seconds / day_duration
    irradiance = peak_irradiance * (-4 * (normalized_time - 0.5)**2 + 1)
    return max(irradiance, 0)

def solar_power(G):
    return A_SOLAR * G * N

# Simulation
def sim(velocities, DISC, INTER, STAGE_SYMBOL, CURRENT_D):
    """
    Simulate a stage and return the final capacity for a given velocity profile.
    
    Parameters:
    - velocities (np.array): Velocity profile over time steps.
    - DISC (int): Number of time steps (discretization).
    - INTER (int): Time interval in seconds.
    - STAGE_SYMBOL (str): Symbol representing the stage (e.g., "1B").
    - CURRENT_D (float): Starting distance along the stage in meters.
    
    Returns:
    - final_capacity (float): The negative of the final battery capacity.
    """
    solar_power_values = np.zeros(DISC)
    rolling_resistance_values = np.zeros(DISC)
    drag_resistance_values = np.zeros(DISC)
    gradient_resistance_values = np.zeros(DISC)
    capacity_values = np.full(DISC, 5200)
    times = np.arange(1, INTER * DISC, INTER)
    for i, v in enumerate(velocities):
        try:
            d = CURRENT_D + v * times[i]
            theta = np.deg2rad(map_distance_to_id(route_model_df, STAGE_SYMBOL, d)['road_angle'])
            irradiance = mock_irradiance(times[i])
            solar_power_values[i] = solar_power(irradiance)
            rolling_resistance_values[i] = rolling_resistance(v)
            drag_resistance_values[i] = drag_resistance(v)
            gradient_resistance_values[i] = gradient_resistance(v, theta)
            capacity_values[i] = capacity_values[i - 1] + solar_power_values[i - 1] - \
                rolling_resistance_values[i - 1] - drag_resistance_values[i - 1] - gradient_resistance_values[i - 1]
        except IndexError:
            print("INDEX ERROR")
            break
    return -capacity_values[-1]