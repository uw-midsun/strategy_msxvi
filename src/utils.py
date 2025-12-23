import numpy as np
from datetime import datetime
from db.load import load_data_to_memory

_routedf = None
_irradf = None

def _get_data():
    """Lazy load data only when needed"""
    global _routedf, _irradf
    if _routedf is None or _irradf is None:
        _routedf, _irradf = load_data_to_memory()
    return _routedf, _irradf

def _map_route(d):
    routedf, _ = _get_data()
    return routedf.iloc[(routedf['distance'] - d).abs().idxmin()]

def _map_irrad(d, t):
    _, irradf = _get_data()
    lat, lon = irradf.iloc[int(d // 5000)][['latitude', 'longitude']]
    ds = irradf[(irradf['latitude'] == lat) & (irradf['longitude'] == lon)]
    idx_t = (ds['timestamp'] - t).abs().idxmin()
    return ds.loc[idx_t]