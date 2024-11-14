import numpy as np
from db import load_data_to_memory
from tqdm import tqdm
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

## Setup
STAGE_SYMBOL = "1B"
current_d = 0 # current distance along stage (m)
start_time = datetime(year=2024, month=10, day=25, hour=5, minute=3) # simulation start time DEFINED IN UTC.
stage_d = 256000 # total distance of the stage (m)

# Constants
m = 300.0  # mass of the vehicle (kg)
g = 9.81  # acceleration due to gravity (m/s^2)
C_r1 = 0.004  # rolling resistance coefficient 1
C_r2 = 0.052  # rolling resistance coefficient 2
C_d = 0.13  # drag coefficient
A_drag = 1.357  # cross-sectional area (m^2)
p = 1.293  # air density (kg/m^3)
n = 0.16  # efficiency of solar panel (%)
A_solar = 4.0  # area of solar panel (m^2)
bat_capacity = 40 * 3.63 * 36  # pack capacity (Wh)

# Simulation parameters
disc = 32  # discretization
inter = 900  # time intervals

# Initialize arrays
velocities = np.arange(1, 1 + disc)
times = np.arange(1, inter * disc, inter)
solar_power_values = np.zeros((disc, disc))
rolling_resistance_values = np.zeros((disc, disc))
drag_resistance_values = np.zeros((disc, disc))
gradient_resistance_values = np.zeros((disc, disc))
capacity_values = np.full((disc, disc), bat_capacity)

# Load data into memory
route_model_df, irradiance_df = load_data_to_memory()

# Function for pulling the closest row in the route model dataframe given the distance and stage name
def map_distance_to_id(route_model_df, stage_name, distance):
    stage_df = route_model_df[route_model_df["stage_name"].str.contains(stage_name, na=False)].copy()
    stage_df["stage_distance"] = stage_df["distance"] - stage_df["distance"].min()
    closest_row = stage_df.iloc[(stage_df['stage_distance'] - distance).abs().argmin()]
    return closest_row

# Needs refactoring. Same as map_distance_to_id but for irradiance data
def map_distance_to_irradiance(
    irradiance_df,
    base_route_df,
    route_symbol,
    distance,
    time,
    start_time=None,
):
    df = base_route_df[base_route_df["symbol"] == route_symbol].copy()
    df["distance_difference"] = abs(df["stage_elapsed_distance"] - distance)
    stage_id, route_start_time = df.nsmallest(1, "distance_difference")[
        ["stage_id", "route_start_time"]
    ].values[0]

    if start_time:
        route_start_time = start_time

    time = int(time)
    target_time = route_start_time + timedelta(seconds=time)

    irradiance_df["time_difference"] = abs(
        (irradiance_df["period_end"] - target_time).dt.total_seconds()
    )
    result_df = irradiance_df[irradiance_df["route_model_id"] == stage_id].nsmallest(
        1, "time_difference"
    )
    return result_df

def mock_irradiance(time_seconds, day_duration=28800, peak_irradiance=1000):
    """ 
    Simulate solar irradiance using a parabolic curve.
    
    Parameters:
        time_seconds (int): The elapsed time in seconds (0 to day_duration).
        day_duration (int): The total duration of the simulated day (default is 8 hours)
        peak_irradiance (float): The maximum irradiance value (default is 1000 W/m²).
    
    Returns:
        float: Simulated irradiance value (W/m²).
    """
    # Normalize the time to the range [0, 1]
    normalized_time = time_seconds / day_duration

    # Parabolic curve formula: y = -4 * (x - 0.5)² + 1
    # This creates a peak at x = 0.5 (midday) and 0 at the start and end of the day.
    irradiance = peak_irradiance * (-4 * (normalized_time - 0.5)**2 + 1)

    # Ensure the irradiance is non-negative
    return max(irradiance, 0)

# Power (In/Out)
def rolling_resistance(v):
    """Calculate power drawn due to rolling resistance."""
    return (m * g * C_r1 + 4 * C_r2 * v) * v

def drag_resistance(v):
    """Calculate power drawn due to drag."""
    return 0.5 * p * C_d * A_drag * v ** 3

def gradient_resistance(v, theta):
    """Calculate power drawn due to gradients."""
    return m * g * np.sin(theta) * v

def solar_power(G):
    """Calculate power available from solar irradiance."""
    return A_solar * G * n

# Progress bar
pbar = tqdm(total=disc ** 2, desc="Simulating", unit="step")

# Perform simulation
for i, v in enumerate(velocities):
    for j, t in enumerate(times):
        try:
            d = current_d + v * t
            # v_wind = map_distance_to_irradiance(irradiance_df, route_model_df, STAGE_SYMBOL, d, t, start_time=start_time)['wind_speed_10m'].values[0] * np.cos(
                # np.deg2rad(map_distance_to_id(route_model_df, STAGE_SYMBOL, d)['car_bearing'].values[0] - map_distance_to_irradiance(irradiance_df, route_model_df, STAGE_SYMBOL, d, t, start_time=start_time)['wind_direction_10m'].values[0]))

            #v_adj = v_wind + v
            theta = np.deg2rad(map_distance_to_id(route_model_df, STAGE_SYMBOL, d)['road_angle'])
            #irradiance = map_distance_to_irradiance(irradiance_df, base_route_df, STAGE_SYMBOL, d, t, start_time=start_time)['gti'].values[0]
            
            elapsed_time = j * inter  # Elapsed time in seconds
            irradiance = mock_irradiance(elapsed_time)
            solar_power_values[i, j] = solar_power(irradiance)
            rolling_resistance_values[i, j] = rolling_resistance(v)
            drag_resistance_values[i, j] = drag_resistance(v) #should be v_adj: change when irradiance available
            gradient_resistance_values[i, j] = gradient_resistance(v, theta)

        except IndexError:
            print("INDEX ERROR")
            exit

        pbar.update(1)

pbar.close()

# Calculate energy consumed
energy_consumed = - solar_power_values + rolling_resistance_values + drag_resistance_values + gradient_resistance_values

# Calculate battery capacity over time
for j in range(1, disc):
    capacity_values[:, j] = capacity_values[:, j - 1] - energy_consumed[:, j - 1]

print(f"8hr simulation for Stage {STAGE_SYMBOL} from {current_d/1000} km @ {start_time} COMPLETE.")

# Function to plot the capacity & distance matrix
def plot_capacity_matrix():
    plt.figure(figsize=(18, 18)) 
    plt.title('Capacity (Wh) & Distance (km) Matrix')
    plt.xlabel('Time (hours)')
    plt.ylabel('Velocity (m/s)')
    plt.imshow(capacity_values, cmap='magma', vmin=-10000, vmax=26000)
    ax = plt.gca()

    # Progress bar
    pbar = tqdm(total=disc**2, desc="Plotting", unit="step")

    for (i, j), val in np.ndenumerate(capacity_values):
        d = (current_d + i * j * inter) / 1000
        if d > stage_d / 1000 and val > 0:
            rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1, color='green', alpha=0.8)
            ax.add_patch(rect)
        if val < 0:
            rect = plt.Rectangle((j - 0.5, i - 0.5), 1, 1, color='black', alpha=1)
            ax.add_patch(rect)
        plt.text(j, i, f'{val:.1f}', ha='center', va='bottom', color='white', fontsize=6)
        plt.text(j, i, f'{d:.1f}', ha='center', va='top', color='black', fontsize=6)
        pbar.update(1)

    pbar.close()

    plt.xticks(ticks=np.arange(0, capacity_values.shape[1]), labels=[f'{i / 4}' for i in range(capacity_values.shape[1])])
    plt.text(0, -2.5, 'Black text: Distance (km)', color='black', fontsize=10)
    plt.text(0, -2, 'White text: Capacity (Wh)', color='black', fontsize=10)
    plt.gca().invert_yaxis()

    # Adding legend
    legend_patches = [
        plt.Rectangle((0, 0), 1, 1, color='green', alpha=0.8, label='Target Operation'),
        plt.Rectangle((0, 0), 1, 1, color='black', alpha=1, label='Dead Battery')
    ]
    plt.legend(handles=legend_patches, loc='upper right', fontsize=10)

    plt.show(block=True)

# Function to plot power profiles
def plot_power_profiles(velocity, plot_solar=True, plot_rolling=True, plot_drag=True, plot_gradient=True, plot_consumed=True):
    fig, ax1 = plt.subplots(figsize=(24, 16))
    
    if plot_solar:
        ax1.plot(solar_power_values[velocity, :], label='Solar Power (W)')
    if plot_rolling:
        ax1.plot(rolling_resistance_values[velocity, :], label='Rolling Resistance (W)')
    if plot_drag:
        ax1.plot(drag_resistance_values[velocity, :], label='Drag Resistance (W)')
    if plot_gradient:
        ax1.plot(gradient_resistance_values[velocity, :], label='Gradient Resistance (W)')
    if plot_consumed:
        ax1.plot(energy_consumed[velocity, :], label='Battery Power (W)')
    
    ax1.set_xlabel('Time (Hours)')
    ax1.set_ylabel('Power (Watts)')
    ax1.set_title(f'Instantaneous Power Draw at {velocity} m/s')
    ax1.set_xticks(np.arange(0, capacity_values.shape[1]))
    ax1.set_xticklabels([f'{i/4}' for i in range(capacity_values.shape[1])])

    ax2 = ax1.twiny()
    ax2.set_xlabel('Distance (km)')
    ax2.set_xticks(np.arange(0, capacity_values.shape[1]))
    ax2.set_xticklabels([f'{(current_d+velocity*inter*i)/1000:.2f}' for i in range(capacity_values.shape[1])])
    
    x_values = np.arange(0, capacity_values.shape[1])
    threshold_index = np.argmax((current_d + velocity * inter * x_values) / 1000 >= stage_d/1000)  
    ax1.axvline(x=x_values[threshold_index], color='grey', linestyle='--', linewidth=2, label='Stage Completion Distance')
    ax1.legend(loc='upper right') 

    ax1.set_xlim(ax2.get_xlim())
    ax1.xaxis.set_ticks_position('bottom')
    ax1.xaxis.set_label_position('bottom')
    ax2.xaxis.set_ticks_position('bottom')
    ax2.xaxis.set_label_position('bottom')
    ax2.spines['bottom'].set_position(('outward', 40))  

    ax1.legend()
    ax1.grid(True)
    
    plt.show(block=True)

#User Input
plot_capacity_matrix()
velocity = 10
plot_power_profiles(velocity, plot_solar=True, plot_rolling=True, plot_drag=True, plot_gradient=True, plot_consumed=True) # Toggle plots

import matplotlib.pyplot as plt
import numpy as np

def plot_capacity(velocity, overlay_data, overlay_dist):
    scale_fac = velocity*inter/1000
    overlay_dist = overlay_dist.astype(float)
    overlay_dist -= current_d/1000
    overlay_dist /= scale_fac

    fig, ax1 = plt.subplots(figsize=(24, 16)) 
    ax1.plot(capacity_values[velocity, :], label='Predicited Capacity (Wh)')
    ax1.plot(overlay_dist, overlay_data, label='True Capacity (Wh)', color='red') 
   
    ax1.set_xlabel('Time (Hours)')
    ax1.set_ylabel('Remaining Capacity (Watt-Hours)')
    ax1.set_title(f'Battery Capacity at {velocity} m/s')

    ax1.set_xticks(np.arange(0, capacity_values.shape[1]))
    ax1.set_xticklabels([f'{i/4}' for i in range(capacity_values.shape[1])])
    
    ax2 = ax1.twiny()
    ax2.set_xlabel('Distance (km)')
    ax2.set_xticks(np.arange(0, capacity_values.shape[1]))
    ax2.set_xticklabels([f'{(current_d+velocity*inter*i)/1000:.2f}' for i in range(capacity_values.shape[1])]) 
    
    x_values = np.arange(0, capacity_values.shape[1])
    threshold_index = np.argmax((current_d+ velocity * inter * x_values) / 1000 >= stage_d / 1000)
    ax1.axvline(x=x_values[threshold_index], color='grey', linestyle='--', linewidth=2, label='Stage Completion Distance')
    ax1.legend(loc='upper right') 

    ax1.set_xlim(ax2.get_xlim())
    ax1.xaxis.set_ticks_position('bottom')
    ax1.xaxis.set_label_position('bottom')
    ax2.xaxis.set_ticks_position('bottom')
    ax2.xaxis.set_label_position('bottom')
    ax2.spines['bottom'].set_position(('outward', 40))

    ax1.legend()
    ax1.grid(True)

    plt.show()

# User Input
velocity = 12
overlay_data = np.array([4000, 4962, 4000, 3700, 200, 2000, 4000])  # real capacity data (Wh)
overlay_dist = np.array([110, 120, 150, 170, 220, 223, 236.80])  # corresponding distance (km)
# plot_capacity(velocity, overlay_data, overlay_dist)