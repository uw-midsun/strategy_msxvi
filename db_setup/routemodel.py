# from db_setup.init import connect_to_db
import numpy as np # Import for numpy array
import gpxpy # Import to allow easier parsing of gpx file


def gpx_parser(output_file="output.txt"):
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
    
    # Declare lists to hold data
    data = []
    stage_names = []
    lats = []
    lons = []
    elevations = []

    # Open gpx file and utilize gpxpy to parse the file
    with open("gpx_asc24/0_FullBaseRoute.gpx", "r") as gpx_file:
        # gpxpy stores the data in a much easier readable format
        gpx = gpxpy.parse(gpx_file)

    # Iterate through all track segments and points
    for track in gpx.tracks:
        for segment in track.segments:
            for points in segment.points:
                stage_names.append(track.name)
                lats.append(points.latitude)
                lons.append(points.longitude)
                elevations.append(points.elevation)
    
    # Stores distance and orientation from returned data
    distance = distance_calc()
    orientation = orientation_calc()
    
    # Convert lists to numpy arrays
    np_stage_names = np.array(stage_names)
    np_lats = np.array(lats)
    np_lons = np.array(lons)
    np_elevations = np.array(elevations)
    np_distance = np.array(distance) # Assuming returend data was list
    np_orientation = np.array(orientation) # Assuming returend data was list
    
    # Zip the individual arrays together 
    # Specify a structured dtype (data type) for each column
    # Need to add distance and orientation after
    data = np.array(list(zip(np_stage_names, np_lats, np_lons, np_elevations)), dtype=[
            ('stage_name', 'U50'), 
            ('lat', 'f8'), 
            ('lon', 'f8'), 
            ('ele', 'f8') 
        ])

    # To test
    np.savetxt(output_file, data, fmt="%s,%.8f,%.8f,%.2f", header="Stage Name, Latitude, Longitude, Elevation", delimiter=',', comments='')
    
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

gpx_parser("gpx_output.txt")