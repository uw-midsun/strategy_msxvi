from init import connect_to_db
from dotenv import load_dotenv
import os

load_dotenv()

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
    Creates six-column unindexed table for solar_irradiance in postgres database.
    Presumes the postgres database has already been created.
    If table already exists, logs an error and does nothing.
    """

    connection = connect_to_db(
        db_name=os.getenv("DB_NAME"),
        db_password=os.getenv("DB_PASSWORD")
    )
    connection.autocommit = True
    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE solar_irradiance (
                air_temp            FLOAT,
                gti                 FLOAT,
                precipitation_rate  FLOAT,
                relative_humidity   FLOAT,
                wind_direction_10m  FLOAT,
                wind_speed_10m      FLOAT
            );
        """)
    except Exception as e:
        print(f"Error: Could not create solar_irradiance table in postgres database: {e}")
    finally:
        cursor.close()
        connection.close()

    return None

def insert_data(csv_filepath):
    """
    Appends data from csv into solar_irradiance table in postgres database.
    Presumes that the csv file has the same columns as the solar_irradiance table
    and that the solar_irradiance table and postgress database have already been created.
    Requires the path to the csv file.
    """

    connection = connect_to_db(
        db_name=os.getenv("DB_NAME"),
        db_password=os.getenv("DB_PASSWORD")
    )
    connection.autocommit = True
    cursor = connection.cursor()

    try:
        with open(csv_filepath, 'r') as f:
            next(f)  # skip header
            cursor.copy_from(f, 'solar_irradiance', sep=',')
    except Exception as e:
        print(f"Error: Could not insert data into solar_irradiance table in postgres database: {e}")
    finally:
        cursor.close()
        connection.close()

    return None