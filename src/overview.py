import datetime as dt
from db import load_data_to_memory

route_model_df, irradiance_df = load_data_to_memory()

STAGE_SYMBOL = '1B'
start_time = dt.datetime(year=2024, month=7, day=10, hour=10, minute=10) # start_time is the current time DEFINED IN UTC

stage_df = route_model_df[route_model_df['stage_name'].str.startswith(f'{STAGE_SYMBOL}_')][['stage_name', 'elevation', 'distance']]
stage_df = stage_df.sort_values(by='distance')

if not stage_df.empty:
    stage_d = stage_df['distance'].max()
    print(f'Stage {STAGE_SYMBOL} total distance: {stage_d / 1000:.2f} km')
else:
    print(f"No data found for stage {STAGE_SYMBOL}")

import matplotlib.pyplot as plt

stage_df['stage_distance_km'] = stage_df['distance'] / 1000

window_size = 5
stage_df['avg_elevation'] = stage_df['elevation'].rolling(window=window_size).mean()

plt.figure(figsize=(14, 7))
plt.plot(
    stage_df['stage_distance_km'], 
    stage_df['avg_elevation'], 
    color='tomato', 
    linewidth=2, 
    linestyle='-', 
    alpha=0.85
)

plt.title(f'{STAGE_SYMBOL} Elevation Profile', fontsize=18, fontweight='bold', color='darkblue')
plt.xlabel('Distance (km)', fontsize=14, fontweight='bold', color='darkblue')
plt.ylabel('Elevation (m)', fontsize=14, fontweight='bold', color='darkblue')

plt.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray', alpha=0.6)

plt.xticks(fontsize=12, color='darkblue')
plt.yticks(fontsize=12, color='darkblue')

plt.fill_between(stage_df['stage_distance_km'], stage_df['avg_elevation'], color='tomato', alpha=0.2)

plt.xlim(stage_df['stage_distance_km'].min(), stage_df['stage_distance_km'].max())
plt.ylim(stage_df['avg_elevation'].min() - 10, stage_df['avg_elevation'].max() + 10)

plt.show()

import matplotlib.pyplot as plt

total_elevation_df = route_model_df[['stage_name', 'elevation', 'distance']]

total_elevation_df = total_elevation_df.sort_values(by='distance')

total_elevation_df['stage_distance_km'] = total_elevation_df['distance'] / 1000

window_size = 5
total_elevation_df['avg_elevation'] = total_elevation_df['elevation'].rolling(window=window_size).mean()

plt.figure(figsize=(14, 7))

for symbol in total_elevation_df['stage_name'].unique():
    subset = total_elevation_df[total_elevation_df['stage_name'] == symbol]
    plt.plot(subset['stage_distance_km'], subset['avg_elevation'], label=symbol)
    plt.fill_between(subset['stage_distance_km'], subset['avg_elevation'], alpha=0.2)

plt.title('Total Elevation Profile', fontsize=18, fontweight='bold', color='darkblue')
plt.xlabel('Distance (km)', fontsize=14, fontweight='bold', color='darkblue')
plt.ylabel('Elevation (m)', fontsize=14, fontweight='bold', color='darkblue')
plt.legend(title='Symbol')
plt.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray', alpha=0.6)

plt.xticks(fontsize=12, color='darkblue')
plt.yticks(fontsize=12, color='darkblue')

plt.xlim(total_elevation_df['stage_distance_km'].min(), total_elevation_df['stage_distance_km'].max())
plt.ylim(total_elevation_df['avg_elevation'].min() - 10, total_elevation_df['avg_elevation'].max() + 10)

plt.show()