import os
import datetime
import pytz
import requests
import random
import math
from dotenv import load_dotenv


# need to import connect_to_db from db/connect.py
import sys
sys.path.append("db")
from connect import connect_to_db


def get_irradiance(API_KEY, lat, lon, azimuth, tilt, hours,
                   is_getting_fake_data=False, use_historical_as_fake_instead_of_simulated=False, start_time=datetime.datetime(2024,8,15,9,30,0, tzinfo=pytz.FixedOffset(-5 * 50))):
    """
    Retrieves irradiance data at a lat/lon point as an array from earliest entry to latest entry
    With each entry in the array as an object containing the following fields:
    - air_temp (degC)
    - gti (tilted irradiance, W/m^2)
    - precipitation_rate (we only retrieve rain data as snow should not be factor in the summer, mm/h)
    - wind_speed_10m (wind speed at 10m elevation, m/s)
    - wind_direction_10m (wind direction at 10m elevation, degrees from 0 to 360)
    Has three modes:
    - real: queries the Solcast forecast API
    - fake-historical: queries the Solcast historical API
    - fake-simulated: generates a facsimile of the above output data using mathematical functions
    Requirements:
    - if start_time is provided, it must be a datetime object with timezone information specified
        via dt = dt.replace(tzinfo=pytz.FixedOffset(-h * 60)); the start_time default parameter is
        an arbitrary East Coast summer date in 2024 that has this already specified
    - note start_time will likely only function properly in the Western hemisphere
    """

    URL = ""
    if is_getting_fake_data:

        end_time = start_time + datetime.timedelta(hours=hours)

        if use_historical_as_fake_instead_of_simulated:

            # Use historical data as a facsimile of forecast data
            if not start_time.utcoffset():
                raise Exception("Error: When fetching fake irradiance data, the start time datetime specified must have timezone information encoded.")
            timezone_hour_offset = start_time.utcoffset().seconds//3600 - 24 # note this will break in places other than the western hemisphere
            URL = f"https://api.solcast.com.au/data/historic/radiation_and_weather?api_key={API_KEY}" \
                f"&latitude={lat}&longitude={lon}&azimuth={azimuth}&tilt={tilt}&array_type=fixed" \
                f"&start={start_time.isoformat()}&end={end_time.isoformat()}&period=PT30M&format=json&time_zone={timezone_hour_offset}" \
                f"&output_parameters=air_temp,gti,precipitation_rate,wind_speed_10m,wind_direction_10m"
            
        else:

            # Simulate a facsimile of solcast data for testing purposes
            output_array = []
            curr_time = start_time

            def air_temp_sim_at_hour(h):
                """
                Returns a simulation of temperature in degrees Celsius using a sinusoidal graph
                Includes some randomization, is based on hour, outputs to two decimal places
                Requires a float hour in the range 0.0 to 24.0, inclusive
                """
                return round(-8 * math.cos(math.pi / 12 * (h - 2)) + 14 + random.uniform(-2, 2), 2)
            
            def gti_sim_at_hour(h):
                """
                Returns a simulation of gti in W/m^2 using a parabolic graph
                Includes some randomization, is based on hour, outputs to two decimal places
                Requires a float hour in the range 0.0 to 24.0, inclusive
                """
                return max(round(-13 * (h-8) * (h-20) + random.uniform(0, 100), 2), 0)
                
            def precipitation_rate_sim_at_hour(h):
                """
                Returns a simulation of a little bit of afternoon rain in mm/h using a parabolic graph
                Includes some randomization, is based on hour, outputs to two decimal places
                Requires a float hour in the range 0.0 to 24.0, inclusive
                """
                return max(round(-5 * (h-15) * (h-17) + random.uniform(-1,1), 2), 0)
            
            def wind_speed_10m_sim_at_hour(h):
                """
                Returns a simulation of wind speed in m/s using a sinusoidal graph
                Includes some randomization, is based on hour, outputs to two decimal places
                Requires a float hour in the range 0.0 to 24.0, inclusive
                """
                return max(round(4 * math.sin(h) + 4 + random.uniform(-1, 1), 2), 0)
            
            def wind_direction_10m_sim_at_hour(h):
                """
                Returns a simulation of wind direction, in degrees from 0 to 360, using a sinusoidal graph
                Includes some randomization, is based on hour, outputs to two decimal places
                Requires a float hour in the range 0.0 to 24.0, inclusive
                """
                return round(180 * math.sin(h/random.uniform(48,52))+180,2)

            while curr_time < end_time:
                curr_hour_float = curr_time.hour + curr_time.minute/60
                output_array.append({
                    "air_temp": air_temp_sim_at_hour(curr_hour_float),
                    "gti": gti_sim_at_hour(curr_hour_float),
                    "precipitation_rate": precipitation_rate_sim_at_hour(curr_hour_float),
                    "wind_speed_10m": wind_speed_10m_sim_at_hour(curr_hour_float),
                    "wind_direction_10m": wind_direction_10m_sim_at_hour(curr_hour_float),
                    # We follow the solcast data return format, which also always includes the following:
                    "period_end": curr_time.isoformat(),
                    "period": "PT30M"

                })
                curr_time += datetime.timedelta(minutes=30) # 0.5 hour discretization
            return output_array

    else:

        # Actually call the forecast API
        URL = f"https://api.solcast.com.au/data/live/radiation_and_weather?api_key={API_KEY}" \
              f"&latitude={lat}&longitude={lon}&azimuth={azimuth}&tilt={tilt}&array_type=fixed" \
              f"&hours={hours}&period=PT30M&format=json" \
              f"&output_parameters=air_temp,gti,precipitation_rate,wind_speed_10m,wind_direction_10m"

    data = requests.get(url=URL).json()
    # Solcast formats the output as an object with a single field, "estimated-actuals", which contains a single array of all the data
    return data["estimated_actuals"]


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


def insert_dummy_data(days, days_prior):
    # TODO docstring, ensure error message is right
    # TODO use this https://docs.python.org/3/library/datetime.html#datetime-objects
    # TODO and datetime.datetime.now().isoformat()

    # try to create dt timezone info using
    # import datetime, import pytz
    # dt = dt.replace(tzinfo=pytz.FixedOffset(-h * 60))
    # print(dt.utcoffset().seconds//3600 - 24)
    # note the latter line will probably break in places other than the states

    if days_prior <= days:
        raise Exception("Error: When using insert_dummy_data, please ensure days_prior is at least days + 1 to ensure enough historical data exists in the Solcast historical database.")
    startTime = datetime.datetime.now() + datetime.timedelta(days=-days_prior)
    pass


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
    # init_table()
    # insert_data()
    # TODO UNCOMMENT THE ABOVE

    load_dotenv()

    print(get_irradiance(os.getenv("SOLCAST_API_KEY"),43.464049, -80.559942, 0, 0, 5, True))
