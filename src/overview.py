import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timezone
from src.utils import _get_data, _map_irrad

def plot_elevation(sym):
    rdf, _ = _get_data()
    stage = rdf[rdf['stage_name'].str.startswith(f'{sym}_')]

    d0, d1 = stage['distance'].iloc[[0, -1]]
    print(f'Stage {sym} total distance: {(d1 - d0) / 1000:.2f} km')

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    ax1.plot(stage['distance'], stage['elevation'])
    ax1.set(title=f'{sym} Elevation Profile', xlabel='Distance (m)', ylabel='Elevation (m)')

    for name, group in rdf.groupby('stage_name'):
        ax2.plot(group['distance'], group['elevation'], label=name)
    ax2.set(title='Total Elevation Profile', xlabel='Distance (m)', ylabel='Elevation (m)')
    ax2.legend()

    plt.tight_layout()
    plt.show()

def plot_irradiance(d, t_start, t_end):
    _, idf = _get_data()

    sample = _map_irrad(d, t_start)
    lat, lon = sample['latitude'], sample['longitude']

    mask = ((idf['latitude'] == lat) & (idf['longitude'] == lon) &
            (idf['timestamp'] >= t_start) & (idf['timestamp'] <= t_end))
    data = (idf[mask]
            .sort_values('timestamp')
            .reset_index(drop=True)
            .assign(datetime=lambda x: pd.to_datetime(x['timestamp'], unit='s')))

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(data['datetime'], data['ghi'])
    ax.set(title=f'GHI Profile for ({lat:.2f}, {lon:.2f})',
           xlabel='Time (hrs)', ylabel='GHI (W/m²)')
    ax.grid(True)
    plt.show()

if __name__ == "__main__":
    plot_elevation("3H")
    plot_irradiance(
        d=10000,
        t_start=int(datetime(2024, 7, 1, 0, 0).timestamp()),
        t_end=int(datetime(2024, 7, 1, 23, 0).timestamp())
    )