from db_setup.init import connect_to_db


def get_irradiance(lat, long, API_KEY):
    """
    Pull 72 hrs data from solcast api as a csv
    - air temp
    - global tilted irradiance
    - precipitation_rate
    - relative humidity
    - wind_direction_10m
    - wind_speed_10m
    """

    url = f"https://api.solcast.com.au/data/live/radiation_and_weather?latitude={lat}&longitude={long}&hours=72&output_parameters=air_temp%2Cgti%2Cprecipitation_rate%2Crelative_humidity%2Cwind_direction_10m%2Cwind_speed_10m&array_type=fixed&terrain_shading=true&format=csv&api_key={API_KEY}"

    return None


def init_table():
    """
    Create table for solar-irradiance in postgres database.
    """
    return None


def insert_data():
    """
    Insert data from csv into solar-irradiance table in postgres database.
    """
    return None
