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
BAT_CAPACITY = 40 * 3.63 * 36 * 3600  # Pack capacity (J)

# ETL & Utils
route_model_df, irradiance_df = load_data_to_memory()

def map_routemodel(route_model_df, distance):
    closest_row = route_model_df.iloc[(route_model_df['distance'] - distance).abs().idxmin()]
    return closest_row

def map_irradiance(irradiance_df, distance, time):
    closest_distance_idx = (irradiance_df['diststamp'] - distance).abs().idxmin()
    closest_distance_row = irradiance_df.iloc[closest_distance_idx]
    closest_time_idx = (irradiance_df[irradiance_df['diststamp'] == closest_distance_row['diststamp']]['timestamp'] - time).abs().idxmin()
    closest_row = irradiance_df.iloc[closest_time_idx]
    return closest_row

# Power (In/Out)
def rolling_resistance(v):
    return (M * G * C_R1 + 4 * C_R2 * v) * v

def drag_resistance(v):
    return 0.5 * P * C_D * A_DRAG * v ** 3

def gradient_resistance(v, theta):
    if theta < 0:
        return 0
    return M * G * np.sin(theta) * v

def solar_power(G):
    return A_SOLAR * G * N

# Simulation
def sim(velocities, STEP, CURRENT_D):
    # Initialize arrays
    solar_power_values = np.zeros(len(velocities))
    rolling_resistance_values = np.zeros(len(velocities))
    drag_resistance_values = np.zeros(len(velocities))
    gradient_resistance_values = np.zeros(len(velocities))
    capacity_values = np.full(len(velocities), BAT_CAPACITY)
    d = CURRENT_D
    
    for i, v in enumerate(velocities):
        # Preliminary calcs
        d += v * STEP
        time = irradiance_df['timestamp'][0] + i * STEP
        theta = np.deg2rad(map_routemodel(route_model_df, d)['road_angle'])
        irradiance = map_irradiance(irradiance_df, d, time)['gti']
        
        # Calculate solar power
        solar_power_values[i] = solar_power(irradiance) * STEP
        
        # Calculate resistances
        rolling_resistance_values[i] = rolling_resistance(v) * STEP
        drag_resistance_values[i] = drag_resistance(v) * STEP
        gradient_resistance_values[i] = gradient_resistance(v, theta) * STEP
        
        # Update battery capacity
        if capacity_values[i-1] > BAT_CAPACITY:
            capacity_values[i] = BAT_CAPACITY
        else:
            capacity_values[i] = capacity_values[i - 1] + solar_power_values[i - 1] - rolling_resistance_values[i - 1] - drag_resistance_values[i - 1] - gradient_resistance_values[i - 1]

        # If we run out of battery at this step, don't reward the optimization function by letting distance travelled continue to accumulate
        if capacity_values[i] < 0:
            d -= v * STEP

    capacity_values /= STEP # Joules --> Wh
    
    # Stack the results into a single matrix
    sim_data = np.column_stack((
        solar_power_values,
        rolling_resistance_values,
        drag_resistance_values,
        gradient_resistance_values,
        capacity_values
    ))
    
    return -capacity_values[-1], sim_data, d