from init import connect_to_db
from dotenv import load_dotenv
import os
import numpy as np # Import for numpy array
import gpxpy # Import to allow easier parsing of gpx file
import math

load_dotenv()

def gpx_parser(output_file="output_w3.txt"):
    """
    Convert gpx files into an array with
    
    - stage name
    - lat
    - long
    - elevation (m)
    - distance (km)
    - orientation (deg)
    - smoothed elevation (m)
    - road angle (deg)

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
    distance = distance_calc(lats, lons)
    orientation = orientation_calc(lats, lons)
    smoothed_elevation = moving_median(elevations, window_size=10)
    road_angles = gradient_calculator(lats, lons, elevations, window_size=10)
    
    # Convert lists to numpy arrays
    np_stage_names = np.array(stage_names)
    np_lats = np.array(lats)
    np_lons = np.array(lons)
    np_elevations = np.array(elevations)
    np_distance = np.array(distance)
    np_orientation = np.array(orientation)
    np_road_angles = np.array(road_angles)
    
    # Zip the individual arrays together 
    # Specify a structured dtype (data type) for each column
    # Need to add distance and orientation after
    data = np.array(list(zip(np_stage_names, np_lats, np_lons, np_elevations, np_distance, np_orientation, smoothed_elevation, np_road_angles)), dtype=[
            ('stage_name', 'U50'), 
            ('lat', 'f8'), 
            ('lon', 'f8'), 
            ('ele', 'f8'), 
            ('distance', 'f8'),
            ('orientation', 'f8'),
            ('smoothed_elevation', 'f8'),
            ('road_angles', 'f8'),
        ])

    # To test
    np.savetxt(output_file, data, fmt="%s,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f", header="Stage Name, Latitude, Longitude, Elevation, Distance, Orientation, Smoothed Elevation, Road Angle", delimiter=',', comments='')
    
    return data


def distance_calc(lats, lons):
    """
    Calculate cumulative distances of a stage at each point.
    """
    # checking longitude and latitude array lengths
    if len(lats) != len(lons):
        raise ValueError("Issue in arrays.")
    
    # initializing cumulative distance array
    distances = []
    sum_distance = 0

    # applying euclidean distances method
    for i in range(len(lons) - 1):
        current_distance = euclidean_distance(lats[i], lons[i], lats[i+1], lons[i+1])
        sum_distance = sum_distance + current_distance
        distances.append(sum_distance)

    return distances


def orientation_calc(lats, lons):
    """
    Calculate the orientations of the car (bearing) with True North being 0 degrees.
    Using this formula for bearing: 
    https://www.movable-type.co.uk/scripts/latlong.html#:~:text=a%20constant%20bearing!-,Bearing,-In%20general%2C%20your
    """
    orientations = []
    for i in range(len(lats)-1):
        lat1 = lats[i]
        lon1 = lons[i]
        lat2 = lats[i+1]
        lon2 = lons[i+1]
        
        # math functions need values in radians
        rad_x1 = math.radians(lon1)
        rad_x2 = math.radians(lon2)
        rad_y1 = math.radians(lat1)
        rad_y2 = math.radians(lat2)
        diff_lon = rad_x2 - rad_x1
        
        # using spherical geometry for this formula
        distance_y = math.sin(diff_lon) * math.cos(rad_y2)
        distance_x = math.cos(rad_y1) * math.sin(rad_y2) - \
            math.sin(rad_y1) * math.cos(rad_y2) * math.cos(diff_lon)
        angle = math.atan2(distance_y, distance_x)
        # convert angle to bearing in degrees
        bearing = (angle*180/math.pi + 360) % 360
        
        orientations.append(bearing)
    return orientations


def init_table():
    """
    Creates six-column unindexed table for route_model in postgres database.
    Presumes the postgres database has already been created.
    If table already exists, logs an error and does nothing.
    """
    connection = connect_to_db(
        db_user=os.getenv("DB_USER"),
        db_host=os.getenv("HOST"),
        db_name=os.getenv("DB_NAME"),
        db_password=os.getenv("DB_PASSWORD")
    )

    connection.autocommit = True
    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE route_model (
                stage_name       VARCHAR(255),
                lat              FLOAT,
                long             FLOAT,
                elevation        FLOAT,
                distance         FLOAT,
                orientation      FLOAT
            );
        """)
    except Exception as e:
        print(f"Error: Could not create route_model table in postgres database: {e}")
    finally:
        cursor.close()
        connection.close()

    return None


def insert_data(txt_filepath):
    """
    Insert data into route_model table in postgres database
    """
    connection = connect_to_db(
        db_user=os.getenv("DB_USER"),
        db_host=os.getenv("HOST"),
        db_name=os.getenv("DB_NAME"),
        db_password=os.getenv("DB_PASSWORD")
    )
    
    connection.autocommit = True
    cursor = connection.cursor()

    try:
        with open(txt_filepath, 'r') as f:
            next(f)  # skip header
            cursor.copy_from(f, 'route_model', sep=',')
    except Exception as e:
        print(f"Error: Could not insert data into route_model table in postgres database: {e}")
    finally:
        cursor.close()
        connection.close()

    return None

def euclidean_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the Euclidean distance between two points given latitudes and longitudes.
    """
    # Approximate radius of the Earth in meters
    R = 6371000

    # Convert latitudes and longitudes from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Convert spherical coordinates to Cartesian coordinates
    x1 = R * math.cos(lat1) * math.cos(lon1)
    y1 = R * math.cos(lat1) * math.sin(lon1)
    z1 = R * math.sin(lat1)
    x2 = R * math.cos(lat2) * math.cos(lon2)
    y2 = R * math.cos(lat2) * math.sin(lon2)
    z2 = R * math.sin(lat2)

    # Calculate differences in Cartesian coordinates
    delta_x = x2 - x1
    delta_y = y2 - y1
    delta_z = z2 - z1

    # Calculate the Euclidean distance
    distance = math.sqrt(delta_x**2 + delta_y**2 + delta_z**2)
    
    return distance

def moving_median(data, window_size):
    """
    Applies a moving median to the data.
    Pads the data to handle edge cases and calculates the median for each window.   
    Outputs an array without the added padding.
    """

    medians = []

    # half window size is used as our width to ensure that the window is centered.
    half_window = window_size // 2
    padded_data = np.pad(data, (half_window, half_window), mode='edge')
    
    for i in range(half_window, len(padded_data) - half_window):
        window = padded_data[i - half_window:i + half_window]
        medians.append(np.median(window))

    return np.array(medians)


def gradient_calculator(lats, lons, elevations, window_size):
    """
    Calculates the angle of the road at each point in the route.
    Applies a moving average to smooth the elvation data.    
    """

    # Applies moving median function to smooth the elevation data
    smoothed_elevations = moving_median(elevations, window_size)

    angles = []
    
    for i in range(len(lats)):
        if i == 0:
            # Calculate the gradient for the first point using the first two points
            distance = euclidean_distance(lats[i], lons[i], lats[i+1], lons[i+1])
            elevation_diff = smoothed_elevations[i+1] - smoothed_elevations[i]
        else:
            # Calculate the horizontal distance between points
            distance = euclidean_distance(lats[i-1], lons[i-1], lats[i], lons[i])
            # Calculate the elevation difference between points
            elevation_diff = smoothed_elevations[i] - smoothed_elevations[i-1]
        
        # Calculate the angle in radians and then convert to degrees
        angle = math.degrees(math.atan2(elevation_diff, distance))
        
        angles.append(angle)

    return angles


# Example data
data = [1, 2, 3, 10, 5, 6, 7, 8, 9, 10]

# Set the window size
window_size = 10  # Even window size

# Apply moving median
smoothed_data = moving_median(data, window_size)

# Print the smoothed data
print("Smoothed Data:", smoothed_data)

gpx_parser()