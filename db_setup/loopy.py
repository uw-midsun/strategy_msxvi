from init import connect_to_db
from dotenv import load_dotenv
import os
import numpy as np # Import for numpy array
import gpxpy # Import to allow easier parsing of gpx file
import math
import srtm #Import to query elevation data using lon and lat data
import psycopg2

load_dotenv()

# Create an instance of the SRTM elevation data
elevation_data = srtm.get_data()

def gpx_loop_parser(output_file="output.txt"):
    """
    Convert gpx files into an array with
    
    - lat
    - long
    - elevation (m)
    - distance (km)
    - orientation (deg)

    As the respective columns.
    """

    # Declare lists to hold data
    data, lats, lons, elevations = [], [], [], []

    # Open gpx file and utilize gpxpy to parse the file 
    with open("db_setup/gpx_asc24//1AL_PaducahLoop.gpx", "r") as gpx_file:
        # gpxpy stores the data in a much easier readable format
        gpx = gpxpy.parse(gpx_file)

    # Since there's only one track, access it directly
    track = gpx.tracks[0]

    # Iterate through all track segments and points
    for segment in track.segments:
        for point in segment.points:
            lat = point.latitude
            lon = point.longitude
            lats.append(lat)
            lons.append(lon)

            # Get elevation using SRTM and append to the elevations list
            elevation = get_srtm_elevation(lat, lon)
            elevations.append(elevation) 

    # Stores distance and orientation from returned data
    distance = distance_calc(lats, lons)
    orientation = orientation_calc(lats, lons)

    # Create a structured numpy array for easier handling of the data
    data = np.array(list(zip(
        lats,
        lons,
        elevations,
        distance,
        orientation
    )), dtype=[
        ("lat", object),
        ("lon", object),
        ("ele", object),
        ("distance", object),
        ("orientation", object),
    ])

    print("Data successfully extracted to structured array")
    return data

def get_srtm_elevation(lat, lon):
    """
    Fetch the elevation for a given latitude and longitude using SRTM library.
    """
    elevation = elevation_data.get_elevation(lat, lon)

    return elevation if elevation is not None else 0


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

gpx_loop_parser("gpx_output.txt")