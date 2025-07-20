import matplotlib.pyplot as plt
from db import load_data_to_memory

def get_stage_bounds(df, sym):
    d = df[df['stage_name'].str.startswith(f'{sym}_')]['distance']
    return d.iloc[0], d.iloc[-1]

def show_overview(sym, route_model_df=None):
    if route_model_df is None:
        df, _ = load_data_to_memory()
        df = df.sort_values('distance')
    else:
        df = route_model_df
    
    d0, d1 = get_stage_bounds(df, sym)
    print(f'Stage {sym} total distance: {(d1 - d0) / 1000:.2f} km')

    s = df[df['stage_name'].str.startswith(f'{sym}_')]
    plt.figure(figsize=(14, 7))
    plt.plot(s['distance'], s['elevation'])
    plt.title(f'{sym} Elevation Profile')
    plt.xlabel('Distance (m)')
    plt.ylabel('Elevation (m)')
    plt.show()

    plt.figure(figsize=(14, 7))
    for k, g in df.groupby('stage_name'):
        plt.plot(g['distance'], g['elevation'], label=k)
    plt.title('Total Elevation Profile')
    plt.xlabel('Distance (m)')
    plt.ylabel('Elevation (m)')
    plt.legend()
    plt.show()

if __name__ == "__main__":
    show_overview('1B')