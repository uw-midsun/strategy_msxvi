import numpy as np
import gpxpy
import math
from init import connect_to_db

def gpx_parser():
    """
    Parse GPX files to extract essential route data and save it to a structured array.
    
    Data includes:
    - Stage names
    - Latitudes
    - Longitudes
    - Elevations (m)
    - Distances (km)
    - Orientations (deg)
    - Road angles (deg)
    """

    # Initialize lists for each data component
    data, stage_names, lats, lons, elevations = [], [], [], [], []

    # Load and parse the GPX file
    with open("db_setup/gpx_asc24/0_FullBaseRoute.gpx", "r") as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    # Extract data from the GPX structure
    for track in gpx.tracks:
        for segment in track.segments:
            for points in segment.points:
                stage_names.append(track.name)
                lats.append(points.latitude)
                lons.append(points.longitude)
                elevations.append(points.elevation)

    # Calculate distances, orientations, and road angles
    distances = distance_calc(lats, lons).tolist()
    orientations = orientation_calc(lats, lons).tolist()
    road_angles = gradient_calculator(lats, lons, elevations, window_size=3).tolist()

    # Create a structured numpy array for easier handling of the data
    data = np.array(list(zip(
        stage_names,
        lats,
        lons,
        elevations,
        distances,
        orientations,
        road_angles
    )), dtype=[
        ("stage_name", object),
        ("lat", object),
        ("lon", object),
        ("ele", object),
        ("distance", object),
        ("orientation", object),
        ("road_angle", object),
    ])

    print("Data successfully extracted to structured array")
    return data


def init_table():
    """
    Initializes a table for route data in a PostgreSQL database. 
    It ensures that the table doesn't already exist before creating it.
    """
    connection = connect_to_db()
    cursor = connection.cursor()
    connection.autocommit = True

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
        print("Table route_model successfully created")
    except Exception as e:
        print(f"Error: Could not create route_model table: {e}")
    finally:
        cursor.close()
        connection.close()
    
    return None


def insert_data():
    """
    Insert data into route_model table in postgres database
    """
    connection = connect_to_db()
    cursor = connection.cursor()
    connection.autocommit = True

    try:
        insert_query = """
            INSERT INTO route_model (stage_name, lat, long, elevation, distance, orientation, road_angle)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(insert_query, gpx_parser())
        print("Data successfully inserted into route_model table")
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
    Computes the Euclidean distance between two geographical points.
    """
    R = 6371000  # Earth's radius in meters

    # Convert degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Convert spherical to Cartesian coordinates
    x1, y1, z1 = R * math.cos(lat1) * math.cos(lon1), R * math.cos(lat1) * math.sin(lon1), R * math.sin(lat1)
    x2, y2, z2 = R * math.cos(lat2) * math.cos(lon2), R * math.cos(lat2) * math.sin(lon2), R * math.sin(lat2)

    # Calculate the Euclidean distance
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2)


def distance_calc(lats, lons):
    """
    Computes cumulative distances for a series of latitude and longitude points.
    """
    if len(lats) != len(lons):
        raise ValueError("Latitude and longitude arrays must be the same length.")

    distances = np.zeros(len(lats))
    sum_distance = 0

    for i in range(1, len(lons)):
        current_distance = euclidean_distance(lats[i - 1], lons[i - 1], lats[i], lons[i])
        sum_distance += current_distance
        distances[i] = sum_distance

    print("Cumulative distances successfully calculated")
    return distances


def orientation_calc(lats, lons):
    """
    Calculate the orientations of the car (bearing) with True North being 0 degrees.
    Using this formula for bearing:
    https://www.movable-type.co.uk/scripts/latlong.html#:~:text=a%20constant%20bearing!-,Bearing,-In%20general%2C%20your
    """
    orientations = np.zeros(len(lats) - 1)
    for i in range(len(lats) - 1):
        lat1, lon1 = map(math.radians, (lats[i], lons[i]))
        lat2, lon2 = map(math.radians, (lats[i + 1], lons[i + 1]))

        # Spherical geometry to calculate bearing
        diff_lon = lon2 - lon1
        distance_y = math.sin(diff_lon) * math.cos(lat2)
        distance_x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(diff_lon)
        angle = math.atan2(distance_y, distance_x)
        bearing = (math.degrees(angle) + 360) % 360

        orientations[i] = bearing

    print("Orientations successfully calculated")
    return orientations


def moving_median(data, window_size):
    """
    Applies a moving median to the data.
    Pads the data to handle edge cases and calculates the median for each window.
    Outputs an array without the added padding.
    """

    medians = np.zeros(len(data))

    # half window size is used as our width to ensure that the window is centered.
    half_window = window_size // 2
    padded_data = np.pad(data, (half_window, half_window), mode="edge")

    for i in range(half_window, len(padded_data) - half_window):
        window = padded_data[i - half_window : i + half_window]
        medians[i - half_window] = np.median(window)
    
    print("Moving median successfully calculated")
    return medians


def gradient_calculator(lats, lons, elevations, window_size):
    """
    Calculates the angle of the road at each point in the route.
    Applies a moving average to smooth the elvation data.
    """

    angles = np.zeros(len(lats) - 1)

    for i in range(len(lats) - 1):
        if i == len(lats) - 2:
            # Calculate the horizontal distance using previous point
            distance = euclidean_distance(lats[i - 1], lons[i - 1], lats[i], lons[i])
            # Calculate the elevation difference using previous point
            elevation_diff = elevations[i] - elevations[i - 1]
            # Calculate the angle in radians and then convert to degrees
            angle = math.degrees(math.atan2(elevation_diff, distance))
            angles[i] = angle

        else:
            # Calculate the horizontal using next point
            distance = euclidean_distance(lats[i], lons[i], lats[i + 1], lons[i + 1])
            # Calculate the elevation difference using next point
            elevation_diff = elevations[i + 1] - elevations[i]
            # Calculate the angle in radians and then convert to degrees
            angle = math.degrees(math.atan2(elevation_diff, distance))
            angles[i] = angle

    smoothed_angles = moving_median(angles, window_size)

    print("Road angles successfully calculated")
    return smoothed_angles

if __name__ == "__main__":
    init_table()
    insert_data()
