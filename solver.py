import numpy as np
from db import load_data_to_memory
from tqdm import tqdm
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from numpy import random

# Load data into memory
route_model_df, irradiance_df = load_data_to_memory()

## Setup
STAGE_SYMBOL = "1B"
current_d = 0 # current distance along stage (m)
start_time = datetime(year=2024, month=10, day=25, hour=5, minute=3) # simulation start time DEFINED IN UTC.

# Determines stage distance (km) dynamically
stage_df = route_model_df[route_model_df['stage_name'].str.startswith(f'{STAGE_SYMBOL}_')][['stage_name', 'distance']]
stage_df['distance_km'] = stage_df['distance'] / 1000
stage_d = stage_df['distance_km'].max()
print(f'Stage {STAGE_SYMBOL} total distance: {stage_d:.2f} km')

# Constants
m = 300.0  # Mass of vehicle (kg)
g = 9.81  # Acceleration due to gravity (m/s^2)
C_r1 = 0.004  # Rolling resistance coefficient 1
C_r2 = 0.052  # Rolling resistance coefficient 2
C_d = 0.13  # Drag coefficient
A_drag = 1.357  # Cross-sectional area (m^2)
p = 1.293  # Air density (kg/m^3)
n = 0.16  # Efficiency of solar panel (%)
A_solar = 4.0  # Area of solar panel (m^2)
bat_capacity = 40 * 3.63 * 36  # Pack capacity (Wh)

# Simulation parameters
disc = 32  # Discretization
inter = 900  # Time interval (s)

# Initialize arrays
velocities = [ # Velocity array of size 31
    10, 10, 10, 24, 24, 24, 24, 24, 24, 24, 24, 24,
    25, 27, 32, 32, 32, 32, 32, 32, 32, 32, 24,
    24, 25, 15, 15, 15, 15, 15, 15
]
velocities = np.array(velocities)
print(f'velocites: {velocities}')
times = np.arange(1, inter * disc, inter)
solar_power_values = np.zeros((disc, disc))
rolling_resistance_values = np.zeros((disc, disc))
drag_resistance_values = np.zeros((disc, disc))
gradient_resistance_values = np.zeros((disc, disc))
capacity_values = np.full((disc, disc), bat_capacity)

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

# Function to plot power profile with varying velocities
def plot_power_profiles(plot_solar=True, plot_rolling=True, plot_drag=True, plot_gradient=True, plot_consumed=True):
    """
    Visualizes the instantaneous power draw of the vehicle across various power components while accounting for varying velocities. 
    
    It integrates multiple power profiles, including solar power, rolling resistance, drag resistance, gradient resistance, and battery consumption.
    """
    
    fig, ax1 = plt.subplots(figsize=(24, 16))

    # Calculate cumulative distance using the actual velocities array
    cumulative_distance = np.cumsum(velocities * inter) / 1000  # Convert to kilometers
    cumulative_distance = np.insert(cumulative_distance, 0, 0)

    # Plot the power profiles
    if plot_solar:
        ax1.plot(solar_power_values.mean(axis=0), label='Solar Power (W)')
    if plot_rolling:
        ax1.plot(rolling_resistance_values.mean(axis=0), label='Rolling Resistance (W)')
    if plot_drag:
        ax1.plot(drag_resistance_values.mean(axis=0), label='Drag Resistance (W)')
    if plot_gradient:
        ax1.plot(gradient_resistance_values.mean(axis=0), label='Gradient Resistance (W)')
    if plot_consumed:
        ax1.plot(energy_consumed.mean(axis=0), label='Battery Power (W)')

    # Create the primary x-axis (time) and y-axis (power)
    ax1.set_xlabel('Time (Hours)')
    ax1.set_ylabel('Power (Watts)')
    ax1.set_title('Instantaneous Power Draw with Varying Velocities')
    time_ticks = np.arange(0, len(times))
    time_labels = [f'{i / 4}' for i in range(len(times))]
    ax1.set_xticks(time_ticks, time_labels)

    # Create the secondary x-axis (distance)
    ax2 = ax1.twiny()
    ax2.set_xlabel('Distance (km)')
    distance_ticks = np.arange(0, len(cumulative_distance) - 1) # Set distance ticks based on cumulative distance
    distance_labels = [f'{cumulative_distance[i]:.1f}' for i in distance_ticks]
    ax2.set_xticks(distance_ticks, distance_labels)

    # Mark the stage completion distance
    completion_mark = np.argmax(cumulative_distance >= stage_d)
    if completion_mark < len(cumulative_distance):
        ax1.axvline(x=completion_mark, color='grey', linestyle='--', linewidth=2, label='Stage Completion Distance')

    # Velocity Heatmap Overlay
    norm_velocities = (velocities - min(velocities)) / (max(velocities) - min(velocities))  # Normalize velocities to [0, 1]
    cmap = plt.get_cmap('magma')

    # Overlay the heatmap with increased transparency (alpha)
    for i in range(len(norm_velocities)):
        ax1.axvspan(i, i + 1, color=cmap(norm_velocities[i]), alpha=0.3)

    # Add a color bar for the velocity heatmap
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=min(velocities), vmax=max(velocities)))
    sm.set_array([])  # Only needed for the color bar
    cbar = plt.colorbar(sm, ax=ax1, alpha=0.3, orientation='vertical', pad=0.02)
    cbar.set_label('Velocity (m/s)', fontsize=12)
    
    ax1.set_xlim(ax2.get_xlim())
    ax1.xaxis.set_ticks_position('bottom')
    ax1.xaxis.set_label_position('bottom')
    ax2.xaxis.set_ticks_position('bottom')
    ax2.xaxis.set_label_position('bottom')
    ax2.spines['bottom'].set_position(('outward', 40))

    ax1.legend(loc='upper right')
    ax1.grid(True)

    plt.show(block=True)


def plot_capacity_dynamic(overlay_data, overlay_dist):
    """
    Plots battery capacity dynamically using a velocity array. Overlays true capacity data.
    """
    
    fig, ax1 = plt.subplots(figsize=(24, 16))
    
    # Calculate cumulative distance using the actual velocities array
    cumulative_distance = np.cumsum(velocities * inter) / 1000
    cumulative_distance = np.insert(cumulative_distance, 0, 0)

    # Map overlay distances to time indices using interpolation
    overlay_time_indices = np.interp(overlay_dist, cumulative_distance, np.arange(len(cumulative_distance)))
    ax1.plot(capacity_values.mean(axis=0), label='Predicted Capacity (Wh)', color='blue')
    ax1.plot(overlay_time_indices, overlay_data, label='True Capacity (Wh)', color='red', zorder=5)

    # Create primary x-axis (time) and y-axis (capacity)
    ax1.set_xlabel('Time (Hours)')
    ax1.set_ylabel('Remaining Capacity (Watt-Hours)')
    ax1.set_title('Battery Capacity Over Time and Distance')
    time_ticks = np.arange(0, len(times))
    time_labels = [f'{i / 4}' for i in range(len(times))]
    ax1.set_xticks(time_ticks, time_labels)

    # Create the secondary x-axis (distance)
    ax2 = ax1.twiny()
    ax2.set_xlabel('Distance (km)')
    distance_ticks = np.arange(0, len(cumulative_distance) - 1) # Set distance ticks based on cumulative distance
    distance_labels = [f'{cumulative_distance[i]:.1f}' for i in distance_ticks]
    ax2.set_xticks(distance_ticks, distance_labels)

    # Mark the stage completion distance
    completion_mark = np.argmax(cumulative_distance >= stage_d)
    if completion_mark < len(cumulative_distance):
        ax1.axvline(x=completion_mark, color='grey', linestyle='--', linewidth=2, label='Stage Completion Distance')

    # Velocity Heatmap Overlay
    norm_velocities = (velocities - min(velocities)) / (max(velocities) - min(velocities))  # Normalize velocities to [0, 1]
    cmap = plt.get_cmap('magma')

    # Overlay the heatmap with increased transparency (alpha)
    for i in range(len(norm_velocities)):
        ax1.axvspan(i, i + 1, color=cmap(norm_velocities[i]), alpha=0.3)

    # Add a color bar for the velocity heatmap
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=min(velocities), vmax=max(velocities)))
    sm.set_array([])  # Only needed for the color bar
    cbar = plt.colorbar(sm, ax=ax1, alpha=0.3, orientation='vertical', pad=0.02)
    cbar.set_label('Velocity (m/s)', fontsize=12)

    ax1.set_xlim(ax2.get_xlim())
    ax1.xaxis.set_ticks_position('bottom')
    ax1.xaxis.set_label_position('bottom')
    ax2.xaxis.set_ticks_position('bottom')
    ax2.xaxis.set_label_position('bottom')
    ax2.spines['bottom'].set_position(('outward', 40))

    ax1.legend(loc='upper right')
    ax1.grid(True)

    plt.show()

# User Input
overlay_data = np.array([4000, 4962, 4000, 3700, 200, 2000, 4000])  # real capacity data (Wh)
overlay_dist = np.array([110, 120, 150, 170, 220, 223, 236.80])  # corresponding distance (km)

plot_power_profiles(plot_solar=True, plot_rolling=True, plot_drag=True, plot_gradient=True, plot_consumed=True) # Toggle plots
plot_capacity_dynamic(overlay_data, overlay_dist)