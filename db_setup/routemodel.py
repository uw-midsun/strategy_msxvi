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


gpx_parser("gpx_output.txt")
insert_data("gpx_output.txt")