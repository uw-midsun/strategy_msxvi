from db.connect import connect_to_db


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
    Creates six-column unindexed table for irradiance in postgres database.
    Presumes the postgres database has already been created.
    If table already exists, logs an error and does nothing.
    """

    connection = connect_to_db()
    connection.autocommit = True
    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE irradiance (
                air_temp            FLOAT,
                gti                 FLOAT,
                precipitation_rate  FLOAT,
                relative_humidity   FLOAT,
                wind_direction_10m  FLOAT,
                wind_speed_10m      FLOAT
            );
        """)
    except Exception as e:
        print(f"Error: Could not create irradiance table in postgres database: {e}")
    finally:
        cursor.close()
        connection.close()

    return None


def insert_data(csv_filepath):
    """
    Appends data from csv into irradiance table in postgres database.
    Presumes that the csv file has the same columns as the irradiance table
    and that the irradiance table and postgress database have already been created.
    Requires the path to the csv file.
    """

    # TODO
    #
    # This code is reading from a CSV, which is not the final behaviour we want.
    # Moreover it is writing to the database in an inefficient way.
    # Whoever works on the final irradiance.py insert_data system, make sure the cursor writing process (which is currently cursor.copy_from)
    # is changed to something similar to what happens in routemodel.py since running "execute" once is around 10x more efficient
    # than running it for each row.
    #
    # routemodel.py's code looks like the following:
    #
    #    args_str = ",".join("('%s', '%s', '%s', '%s', '%s', '%s', '%s')"
    #                         % (stage_name, lat, long, elevation, distance, orientation, road_angle)
    #                         for (stage_name, lat, long, elevation, distance, orientation, road_angle) in gpx_parser())
    #    cursor.execute("INSERT INTO route_model VALUES" + args_str)
    #    connection.commit()
    #
    # For more information see the following resource I found: http://aaronolszewski.com/psycopg2-execution-time/
    # - Eric Li (@ericli3690) 23 Nov 2024
    #

    connection = connect_to_db()
    cursor = connection.cursor()

    try:
        print("Clearing existing data from irradiance table...")
        cursor.execute("DELETE FROM irradiance")

        print("Inserting data into irradiance table... (this may take a while)")

        with open(csv_filepath, 'r') as f:
            next(f)  # skip header
            cursor.copy_from(f, 'irradiance', sep=',')
        connection.commit()

    except Exception as e:
        print(f"Error: Could not insert data into irradiance table in postgres database: {e}")
    finally:
        cursor.close()
        connection.close()

    return None

if __name__ == "__main__":
    init_table()
    # insert_data()