import os
import time
import datetime
import pytz
import requests
import random
import math
import numpy as np
from dotenv import load_dotenv


# Need to import db functions from the /db directory
import sys
sys.path.append("db")
from connect import connect_to_db
from loader import load_data_to_memory


# Fake historical start time constant
# Required for grabbing fake historical data from Solcast: this will never be used in production at the race
# This is only used when MODE=2 is enabled for get_irradiance
# An arbitrary east coast summer date in 2024 at 9am; "-5" is EST
FAKE_START = datetime.datetime(2024,8,15,9,0,0, tzinfo=pytz.FixedOffset(-5 * 50))


# Time and distance discretization constants
# Time discretization governs how often we request data from the API on weather
# Distance discretization governs how far apart the points are that we sample
# Tweak as needed, though be wary of extra API call cost
TIME_DISCR = 0.5 # 0.5h = 30min
DIST_DISCR = 8000 # 8km = 8000m


def get_irradiance(API_KEY, lat, lon, azimuth, tilt, hours,
                   MODE=1, fake_historical_start_time=FAKE_START):
    """
    Retrieves irradiance data at a lat/lon point as an array from earliest entry to latest entry, in TIME_DISCR intervals,
      with each entry in the array as a dictionary containing the following fields:
    - air_temp (degC)
    - gti (tilted irradiance, W/m^2)
    - precipitation_rate (we only retrieve rain data as snow should not be factor in the summer, mm/h)
    - wind_speed_10m (wind speed at 10m elevation, m/s)
    - wind_direction_10m (wind direction at 10m elevation, degrees from 0 to 360)
    Has three modes:
    - 1: real: queries the Solcast forecast API
    - 2: fake-historical: queries the Solcast historical API
    - 3: fake-simulated: generates a fake version of the above output data using mathematical functions
    Try not to run mode 1 too often, as it consumes API tokens. Prefer mode 3 for testing.
    Requirements:
    - if start_time is provided, it must be a datetime object with timezone information specified
        via dt = dt.replace(tzinfo=pytz.FixedOffset(-h * 60))
    - note start_time will likely only function properly in the Western hemisphere
    """

    match MODE:

        case 1: # Actually call the forecast API

            URL = f"https://api.solcast.com.au/data/live/radiation_and_weather?api_key={API_KEY}" \
                f"&latitude={lat}&longitude={lon}&azimuth={azimuth}&tilt={tilt}&array_type=fixed" \
                f"&hours={hours}&period=PT30M&format=json" \
                f"&output_parameters=air_temp,gti,precipitation_rate,wind_speed_10m,wind_direction_10m"
            
            data = requests.get(url=URL).json()

            # Solcast formats the output as an object with a single field, "estimated-actuals", which contains a single array of all the data
            return data["estimated_actuals"]

        case 2: # Use historical data as an imitation of forecast data

            end_time = fake_historical_start_time + datetime.timedelta(hours=hours)
            if not fake_historical_start_time.utcoffset():
                raise Exception("Error: When fetching fake irradiance data, the start time datetime specified must have timezone information encoded.")
            timezone_hour_offset = fake_historical_start_time.utcoffset().seconds//3600 - 24 # note this will break in places other than the western hemisphere

            URL = f"https://api.solcast.com.au/data/historic/radiation_and_weather?api_key={API_KEY}" \
                f"&latitude={lat}&longitude={lon}&azimuth={azimuth}&tilt={tilt}&array_type=fixed" \
                f"&start={fake_historical_start_time.isoformat()}&end={end_time.isoformat()}&period=PT30M&format=json&time_zone={timezone_hour_offset}" \
                f"&output_parameters=air_temp,gti,precipitation_rate,wind_speed_10m,wind_direction_10m"

            data = requests.get(url=URL).json()

            # Solcast formats the output as an object with a single field, "estimated-actuals", which contains a single array of all the data
            return data["estimated_actuals"]

        case 3: # Simulate an imitation of forecast data for testing purposes

            output_array = []
            curr_time = datetime.datetime.now()
            end_time = curr_time + datetime.timedelta(hours=hours)

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
                return round(180 * math.sin(h/random.uniform(3,5))+180,2)

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
                curr_time += datetime.timedelta(hours=TIME_DISCR)
            return output_array

        case _: # invalid mode

            raise Exception("Error: get_irradiance must be called with a mode of either 1, 2, or 3.")


def map_distance_to_id(route_model_df, distance):
    """
    Grabs the route model row entry that is closest to a certain distance marker,
      measured in meters from the beginning of the race.
    """
    return route_model_df.iloc[(route_model_df['distance'] - distance).abs().idxmin()]


def run_irradiance_query(day_queries, MODE=1, fake_historical_start_time=FAKE_START):
    """
    Repeatedly runs get_irradiance for each day contained in day_queries at intervals defined by TIME_DISCR and DIST_DISCR.
    Outputs the data as a numpy array, with an entry for each position and times at those positions.
    Data outputted includes the fields mentioned in the docstring of get_irradiance, along with
      distance and timestamp information to aid with optimization and solver functionality.

    Each day_query in day_queries must be an object with three fields:
    - start_dist: meters travelled from the beginning of the race: this is where we begin retrieving irradiance data for this day
    - end_dist: meters travelled from the beginning of the race: this is where we stop retrieving irradiance data for this day
    - hours: we retrieve irradiance data from now, the current time, until this many hours in the future
    For example, setting day_queries to [{start_dist: 0, end_dist: 100000, hours: 8}] will retrieve irradiance data at points
    located DIST_DISCR meters apart from the beginning of the race to 1000km into the race, grabbing 8 hours of data at intervals
    of TIME_DISCR at each point, with get_irradiance being called (and thus the Solcast API being queried) a total of (100000-0)/DIST_DISCR times.
    
    Has three modes: see the docstring of get_irradiance for more information along with requirements for fake_historical_start_time.
    Try not to run mode 1 too often, as it consumes API tokens. Prefer mode 3 for testing.
    """

    diststamps, timestamps, air_temps, gtis, precipitation_rates, wind_speed_10ms, wind_direction_10ms = [], [], [], [], [], [], []
    route_model_df, _ = load_data_to_memory() # Need to read location data from route model and grab irradiance at those points
    api_calls = 0 # We print the amount of calls we make to get_irradiance at the end for logging purposes
    
    load_dotenv()
    API_KEY = os.getenv("SOLCAST_API_KEY")

    for i, day in enumerate(day_queries):

        print(f"Running irradiance queries for day {i}...")

        if MODE == 2 and fake_historical_start_time + datetime.timedelta(hours=(day['hours']+1)) > datetime.datetime.now():
            raise Exception("Error: When using fake historical data in insert_data, please ensure the start date chosen is early enough for corresponding data to exist in the Solcast historical database.")

        assert day['end_dist'] > day['start_dist']
        assert day['hours'] > 0

        curr_dist = day['start_dist']
        while curr_dist < day['end_dist']: # For each location in space along the route, at intervals of DIST_DISCR...
            curr_loc = map_distance_to_id(route_model_df, curr_dist)
            curr_loc_irradiance_data = \
                get_irradiance(API_KEY, curr_loc['lat'], curr_loc['long'],
                               # Note route_model returns orientations in [0,360] but Solcast requires them in [-180,180]
                               curr_loc['orientation'] if curr_loc['orientation'] <= 180 else (curr_loc['orientation'] - 360),
                               curr_loc['road_angle'],
                               day['hours'], MODE, fake_historical_start_time)
            api_calls += 1
            curr_time = time.time() # Get seconds since epoch
            for data_point in curr_loc_irradiance_data: # For each time in the future at this point, at intervals of TIME_DISCR...
                # Append everything to the arrays
                diststamps.append(curr_dist)
                timestamps.append(curr_time)
                air_temps.append(data_point['air_temp'])
                gtis.append(data_point['gti'])
                precipitation_rates.append(data_point['precipitation_rate'])
                wind_speed_10ms.append(data_point['wind_speed_10m'])
                wind_direction_10ms.append(data_point['wind_direction_10m'])

                curr_time += TIME_DISCR * 60 * 60 # Convert hours to seconds
            curr_dist += DIST_DISCR
    
    # Put everything into a succinct numpy array
    data = np.array(list(zip(
        diststamps,
        timestamps,
        air_temps,
        gtis,
        precipitation_rates,
        wind_speed_10ms,
        wind_direction_10ms
    )), dtype=[
        ("diststamp", object),
        ("timestamp", object),
        ("air_temp", object),
        ("gti", object),
        ("precipitation_rate", object),
        ("wind_speed_10m", object),
        ("wind_direction_10m", object)
    ])

    print(f"Irradiance data successfully extracted to structured array. Spent {api_calls} api calls.")
    return data


def init_table():
    """
    Creates seven-column unindexed table for irradiance in postgres database.
    Fields are those mentioned in the docstring of get_irradiance, along with
      diststamp, distance travelled in the race in meters, and timestamp,
      expressed in seconds since the epoch (1970).
    Presumes the postgres database has already been created.
    If table already exists, logs an error and does nothing.
    """

    connection = connect_to_db()
    connection.autocommit = True
    cursor = connection.cursor()

    try:
        cursor.execute("""
            CREATE TABLE irradiance (
                diststamp           FLOAT,
                timestamp           FLOAT,
                air_temp            FLOAT,
                gti                 FLOAT,
                precipitation_rate  FLOAT,
                wind_speed_10m      FLOAT,
                wind_direction_10m  FLOAT
            );
        """)
    except Exception as e:
        print(f"Error: Could not create irradiance table in postgres database: {e}")
    finally:
        cursor.close()
        connection.close()

    return None


def insert_data(day_queries, MODE=1, fake_historical_start_time=FAKE_START):
    """
    Inserts irradiance data into irradiance table in the postgres database according to a query array.
    See the docstrings of run_irradiance_query and get_irradiance for important specifications regarding
      day_queries, MODE, and fake_historical_start_time.
    Presumes that the irradiance table and postgress database have already been created.
    """
    
    connection = connect_to_db()
    cursor = connection.cursor()

    try:
        print("Clearing existing data from irradiance table...")
        cursor.execute("DELETE FROM irradiance")

        print("Inserting data into irradiance table... (this may take a while)")

        # Appends all queries together, then inserts all at once, to minimize expensive write operations
        args_str = ",".join("('%s', '%s', '%s', '%s', '%s', '%s', '%s')"
                            % (diststamp, timestamp, air_temp, gti, precipitation_rate, wind_speed_10m, wind_direction_10m)
                            for (diststamp, timestamp, air_temp, gti, precipitation_rate, wind_speed_10m, wind_direction_10m) \
                                  in run_irradiance_query(day_queries, MODE, fake_historical_start_time))
        cursor.execute("INSERT INTO irradiance VALUES" + args_str)
        connection.commit()

        print("Data successfully inserted into irradiance table")
    except Exception as e:
        print(f"Error: Could not insert data into irradiance table in postgres database: {e}")
    finally:
        cursor.close()
        connection.close()

    return None


if __name__ == "__main__":
    init_table()
    insert_data([
        { # Day 1
            'start_dist': 0, # stage 1A
            'end_dist': 256632,
            'hours': 8
        },
        { # Day 2
            'start_dist': 256632, # stage 1B
            'end_dist': 606355,
            'hours': 8+24
        },
        { # Day 3
            'start_dist': 606355, # stage 2C
            'end_dist': 870610,
            'hours': 8+24+24
        },
    ], 3) # Simulation mode, for now, as we do not have the Solcast API yet
