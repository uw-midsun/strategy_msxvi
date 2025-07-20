import matplotlib.pyplot as plt
from db import load_data_to_memory

def show_overview(STAGE_SYMBOL):
    # Load data
    route_model_df, _ = load_data_to_memory()
    route_model_df = route_model_df.sort_values(by="distance")

    # Stage distance
    stage_d = get_stage_dist(route_model_df, STAGE_SYMBOL)
    stage_d_in_km = stage_d / 1000
    print(f'Stage {STAGE_SYMBOL} total distance: {stage_d_in_km:.2f} km')

    # Stage elevation profile
    plt.figure(figsize=(14, 7))
    plt.plot(route_model_df.loc[route_model_df['stage_name'].str.startswith(f'{STAGE_SYMBOL}_')]['distance'], route_model_df.loc[route_model_df['stage_name'].str.startswith(f'{STAGE_SYMBOL}_')]['elevation'])
    plt.title(f'{STAGE_SYMBOL} Elevation Profile')
    plt.xlabel('Distance (m)')
    plt.ylabel('Elevation (m)')

    plt.show()

    # Total elevation profile
    plt.figure(figsize=(14, 7))
    for symbol, subset in route_model_df.groupby('stage_name'):
        plt.plot(subset['distance'], subset['elevation'], label=symbol)
    plt.title('Total Elevation Profile')
    plt.xlabel('Distance (m)')
    plt.ylabel('Elevation (m)')
    plt.legend()

    plt.show()

def get_stage_dist(sorted_route_model_df, STAGE_SYMBOL):
    return get_stage_end_dist(sorted_route_model_df, STAGE_SYMBOL) - get_stage_start_dist(sorted_route_model_df, STAGE_SYMBOL)

def get_stage_start_dist(sorted_route_model_df, STAGE_SYMBOL):
    return sorted_route_model_df.loc[sorted_route_model_df['stage_name'].str.startswith(f'{STAGE_SYMBOL}_'), 'distance'].iloc[0]

def get_stage_end_dist(sorted_route_model_df, STAGE_SYMBOL):
    return sorted_route_model_df.loc[sorted_route_model_df['stage_name'].str.startswith(f'{STAGE_SYMBOL}_'), 'distance'].iloc[-1]

if __name__ == "__main__":
    show_overview('1B')
