import matplotlib.pyplot as plt
from db import load_data_to_memory

route_model_df, irradiance_df = load_data_to_memory() # Load data from the database. Make sure the database is running!

STAGE_SYMBOL = '1B' # Change this to the stage you want to analyze


#Filter the route model data to get the specified stage data
stage_df = route_model_df[route_model_df['stage_name'].str.startswith(f'{STAGE_SYMBOL}_')][['stage_name', 'elevation', 'distance']]
stage_df = stage_df.sort_values(by='distance')
stage_df['distance_km'] = stage_df['distance'] / 1000
stage_df['avg_elevation'] = stage_df['elevation'].rolling(window=5).mean()

#Make sure there is stage data
if not stage_df.empty:
    stage_d = stage_df['distance_km'].max()
    print(f'Stage {STAGE_SYMBOL} total distance: {stage_d:.2f} km')
else:
    print(f"No data found for stage {STAGE_SYMBOL}")

#Plot the elevation profile for the specified stage
plt.figure(figsize=(14, 7))
plt.plot(stage_df['distance_km'], stage_df['avg_elevation'], color='tomato', linewidth=2, linestyle='-', alpha=0.85)
plt.fill_between(stage_df['distance_km'], stage_df['avg_elevation'], color='tomato', alpha=0.2)

plt.title(f'{STAGE_SYMBOL} Elevation Profile', fontsize=18, fontweight='bold', color='darkblue')
plt.xlabel('Distance (km)', fontsize=14, fontweight='bold', color='darkblue')
plt.ylabel('Elevation (m)', fontsize=14, fontweight='bold', color='darkblue')
plt.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray', alpha=0.6)
plt.xticks(fontsize=12, color='darkblue')
plt.yticks(fontsize=12, color='darkblue')
plt.xlim(stage_df['distance_km'].min(), stage_df['distance_km'].max())
plt.ylim(stage_df['avg_elevation'].min() - 10, stage_df['avg_elevation'].max() + 10)

plt.show(block=False)


#Create a new dataframe containing the total elevation profile of the route
total_elevation_df = route_model_df[['stage_name', 'elevation', 'distance']]
total_elevation_df = total_elevation_df.sort_values(by='distance')
total_elevation_df['distance_km'] = total_elevation_df['distance'] / 1000
total_elevation_df['avg_elevation'] = total_elevation_df['elevation'].rolling(window=5).mean()


#Plot the total elevation profile of the route
plt.figure(figsize=(14, 7))

for symbol, subset in total_elevation_df.groupby('stage_name'):
    plt.plot(subset['distance_km'], subset['avg_elevation'], label=symbol)
    plt.fill_between(subset['distance_km'], subset['avg_elevation'], alpha=0.2)

plt.title('Total Elevation Profile', fontsize=18, fontweight='bold', color='darkblue')
plt.xlabel('Distance (km)', fontsize=14, fontweight='bold', color='darkblue')
plt.ylabel('Elevation (m)', fontsize=14, fontweight='bold', color='darkblue')
plt.legend(title='Symbol')
plt.grid(True, which='both', linestyle='--', linewidth=0.5, color='gray', alpha=0.6)

plt.xticks(fontsize=12, color='darkblue')
plt.yticks(fontsize=12, color='darkblue')

plt.xlim(total_elevation_df['distance_km'].min(), total_elevation_df['distance_km'].max())
plt.ylim(total_elevation_df['avg_elevation'].min() - 10, total_elevation_df['avg_elevation'].max() + 10)

plt.show()
