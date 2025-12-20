from db.load import load_data_to_memory

_routedf = None
_irradf = None

def _get_data():
    """Lazy load data only when needed"""
    global _routedf, _irradf
    if _routedf is None or _irradf is None:
        _routedf, _irradf = load_data_to_memory()
    return _routedf, _irradf