import matplotlib.pyplot as plt
from db import load_data_to_memory

# Stage
STAGE_SYMBOL = '1B'

# Load data
route_model_df, irradiance_df = load_data_to_memory()
route_model_df = route_model_df.sort_values(by="distance")

# Stage distance
stage_d = (route_model_df.loc[route_model_df['stage_name'].str.startswith(f'{STAGE_SYMBOL}_'), 'distance'].iloc[-1] - 
           route_model_df.loc[route_model_df['stage_name'].str.startswith(f'{STAGE_SYMBOL}_'), 'distance'].iloc[0]) / 1000
print(f'Stage {STAGE_SYMBOL} total distance: {stage_d:.2f} km')

# Stage elevation profile
plt.figure(figsize=(14, 7))
plt.plot(route_model_df.loc[route_model_df['stage_name'].str.startswith(f'{STAGE_SYMBOL}_')]['distance'], route_model_df.loc[route_model_df['stage_name'].str.startswith(f'{STAGE_SYMBOL}_')]['elevation'])
plt.title(f'{STAGE_SYMBOL} Elevation Profile')
plt.xlabel('Distance (m)')
plt.ylabel('Elevation (m)')

# Total elevation profile
plt.figure(figsize=(14, 7))
for symbol, subset in route_model_df.groupby('stage_name'):
    plt.plot(subset['distance'], subset['elevation'], label=symbol)
plt.title('Total Elevation Profile')
plt.xlabel('Distance (m)')
plt.ylabel('Elevation (m)')
plt.legend()