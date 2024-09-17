from db_setup.init import connect_to_db


def gpx_parser():
    data = []
    """
    Convert gpx files into an array with
    
    - stage name
    - lat
    - long
    - elevation (m)
    - distance (km)
    - orientation (deg)

    As the respective columns.
    """
    return data


def distance_calc():
    """
    Calculate cumulative distances of a stage at each point.
    """
    distances = []
    return distances


def orientation_calc():
    """
    Calculate the orientations of the car with North being 0 degrees.
    """
    orientations = []
    return orientations


def init_table():
    """
    Create table for route-model in postgres database.
    """
    return None


def insert_data():
    """
    Insert data into routmodel table in postgres database
    """
    return None

