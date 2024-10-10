from init import connect_to_db
from dotenv import load_dotenv
import os
import numpy as np  # Import for numpy array
import gpxpy  # Import to allow easier parsing of gpx file
import math

load_dotenv()

OUTPUT_FILE = "outputtest.txt"


def gpx_parser(output_file=OUTPUT_FILE):
    """
    Convert gpx files into an array with

    - stage name
    - lat
    - long
    - elevation (m)
    - distance (km)
    - orientation (deg)
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
    road_angles = gradient_calculator(lats, lons, elevations, window_size=3)

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
    data = np.array(
        list(
            zip(
                np_stage_names,
                np_lats,
                np_lons,
                np_elevations,
                np_distance,
                np_orientation,
                np_road_angles,
            )
        ),
        dtype=[
            ("stage_name", "U50"),
            ("lat", "f8"),
            ("lon", "f8"),
            ("ele", "f8"),
            ("distance", "f8"),
            ("orientation", "f8"),
            ("road_angles", "f8"),
        ],
    )

    # To test
    np.savetxt(
        output_file,
        data,
        fmt="%s,%.8f,%.8f,%.8f,%.8f,%.8f,%.8f",
        header="Stage Name, Latitude, Longitude, Elevation, Distance, Orientation, Road Angle",
        delimiter=",",
        comments="",
    )

    return data


def distance_calc(lats, lons):
    """
    Calculate cumulative distances of a stage at each point.
    """
    # checking longitude and latitude array lengths
    if len(lats) != len(lons):
        raise ValueError("Issue in arrays.")

    # initializing cumulative distance array
    distances = [0]
    sum_distance = 0

    # applying euclidean distances method
    for i in range(1, len(lons)):
        current_distance = euclidean_distance(
            lats[i - 1], lons[i - 1], lats[i], lons[i]
        )
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
    for i in range(len(lats) - 1):
        lat1 = lats[i]
        lon1 = lons[i]
        lat2 = lats[i + 1]
        lon2 = lons[i + 1]

        # Convert latitudes and longitudes from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # using spherical geometry for this formula
        diff_lon = lon2 - lon1
        distance_y = math.sin(diff_lon) * math.cos(lat2)
        distance_x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(
            lat2
        ) * math.cos(diff_lon)
        angle = math.atan2(distance_y, distance_x)
        # convert angle to bearing in degrees
        bearing = (angle * 180 / math.pi + 360) % 360

        orientations.append(bearing)
    return orientations


def init_table():
    """
    Creates seven-column unindexed table for route_model in postgres database.
    Presumes the postgres database has already been created.
    If table already exists, logs an error and does nothing.
    """
    connection = connect_to_db(
        db_user=os.getenv("DB_USER"),
        db_host=os.getenv("HOST"),
        db_name=os.getenv("DB_NAME"),
        db_password=os.getenv("DB_PASSWORD"),
    )

    connection.autocommit = True
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            CREATE TABLE route_model (
                stage_name       VARCHAR(255),
                lat              FLOAT,
                long             FLOAT,
                elevation        FLOAT,
                distance         FLOAT,
                orientation      FLOAT,
                road_angle       FLOAT
            );
        """
        )
    except Exception as e:
        print(f"Error: Could not create route_model table in postgres database: {e}")
    finally:
        cursor.close()
        connection.close()

    return None


def insert_data(output_file=OUTPUT_FILE):
    """
    Insert data into route_model table in postgres database
    """
    connection = connect_to_db(
        db_user=os.getenv("DB_USER"),
        db_host=os.getenv("HOST"),
        db_name=os.getenv("DB_NAME"),
        db_password=os.getenv("DB_PASSWORD"),
    )

    connection.autocommit = True
    cursor = connection.cursor()

    try:
        with open(output_file, "r") as f:
            next(f)  # skip header
            cursor.copy_from(f, "route_model", sep=",")
    except Exception as e:
        print(
            f"Error: Could not insert data into route_model table in postgres database: {e}"
        )
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
    padded_data = np.pad(data, (half_window, half_window), mode="edge")

    for i in range(half_window, len(padded_data) - half_window):
        window = padded_data[i - half_window : i + half_window]
        medians.append(np.median(window))

    return np.array(medians)


def gradient_calculator(lats, lons, elevations, window_size):
    """
    Calculates the angle of the road at each point in the route.
    Applies a moving average to smooth the elvation data.
    """

    angles = []

    for i in range(len(lats) - 1):
        if i == len(lats) - 2:
            # Calculate the horizontal distance using previous point
            distance = euclidean_distance(lats[i - 1], lons[i - 1], lats[i], lons[i])
            # Calculate the elevation difference using previous point
            elevation_diff = elevations[i] - elevations[i - 1]
            # Calculate the angle in radians and then convert to degrees
            angle = math.degrees(math.atan2(elevation_diff, distance))
            angles.append(angle)

        else:
            # Calculate the horizontal using next point
            distance = euclidean_distance(lats[i], lons[i], lats[i + 1], lons[i + 1])
            # Calculate the elevation difference using next point
            elevation_diff = elevations[i + 1] - elevations[i]
            # Calculate the angle in radians and then convert to degrees
            angle = math.degrees(math.atan2(elevation_diff, distance))
            angles.append(angle)

    smoothed_angles = moving_median(angles, window_size)

    return smoothed_angles


gpx_parser()
insert_data()
