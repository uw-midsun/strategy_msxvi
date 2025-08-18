import os
import requests
from psycopg2.extras import execute_values
import pytz
import datetime as dt
import numpy as np
from dotenv import load_dotenv
from db import connect_to_db, load_data_to_memory #to run this script: "python -m db.setup.irradiance"

load_dotenv()
API_KEY = os.getenv("SOLCAST_API_KEY")
TIME_DISCR = 0.5 #hours
DIST_DISCR = 8000 #meters
FAKE_START = dt.datetime(2024,8,15,9,0,0, tzinfo=pytz.timezone("America/New_York")) #MODE=2 for get_irradiance
COLS = ("diststamp","timestamp","air_temp","gti","precipitation_rate","wind_speed_10m","wind_direction_10m")


def init_table():
    """
    Creates table for irradiance data in postgres.
    """
    connection = connect_to_db()
    connection.autocommit = True
    cursor = connection.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS irradiance (
                diststamp           FLOAT,
                timestamp           FLOAT,
                air_temp            FLOAT,
                gti                 FLOAT,
                precipitation_rate  FLOAT,
                wind_speed_10m      FLOAT,
                wind_direction_10m  FLOAT
            );
        """)
    finally:
        cursor.close()
        connection.close()


def insert_data(day_queries, MODE, fake_historical_start_time=FAKE_START):
    """
    Inserts irradiance data into irradiance table in the postgres database.
    """
    rows = run_irradiance_query(day_queries, MODE, fake_historical_start_time)
    sql = f"INSERT INTO irradiance ({', '.join(COLS)}) VALUES %s"
    with connect_to_db() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM irradiance;")
        connection.commit()
        execute_values(cursor, sql, rows)
        print(f"Inserted [Mode {MODE}] data into irradiance table")
        connection.commit()


def run_irradiance_query(day_queries, MODE, fake_historical_start_time: dt.datetime = FAKE_START):
    """
    Returns array with data (get_irradiace) for days (objects in day_queries). 

    Each day_query in day_queries must be an object with three fields:
    - start_dist (m)
    - end_dist (m)
    - hours (h)

    Eg. day_queries = [{start_dist: 0, end_dist: 100000, hours: 8}] will retrieve 8 hours of irradiance data discretized by TIME_DISCR at points located DIST_DISCR meters apart.
    """
    if MODE in (1, 2) and not API_KEY:
        raise RuntimeError("SOLCAST_API_KEY not set")
    route_model_df, _ = load_data_to_memory()
    api_calls = 0
    for i, day in enumerate(day_queries):
        start_dist = float(day['start_dist'])
        end_dist = float(day['end_dist'])
        hours = int(day['hours'])
        if end_dist <= start_dist or hours <= 0:
            raise ValueError(f"Invalid day query: {day}")
        curr_dist = start_dist
        while curr_dist < end_dist:
            loc = map_distance_to_id(route_model_df, curr_dist)
            az = loc["orientation"] if loc["orientation"] <= 180 else (loc["orientation"] - 360)
            data = get_irradiance(API_KEY, loc["lat"], loc["long"], az, loc["road_angle"], hours, MODE, fake_historical_start_time)
            t = dt.datetime.now(dt.timezone.utc).timestamp()
            for d in data:
                yield (
                    curr_dist,
                    t,
                    float(d["air_temp"]),
                    float(d["gti"]),
                    float(d["precipitation_rate"]),
                    float(d["wind_speed_10m"]),
                    float(d["wind_direction_10m"]),
                )
                t += TIME_DISCR * 3600  # seconds
            curr_dist += DIST_DISCR


def map_distance_to_id(route_model_df, distance):
    """
    Returns id of route_model_df closest to inputted distance (m).
    """
    return route_model_df.iloc[(route_model_df['distance'] - distance).abs().idxmin()]


def get_irradiance(API_KEY, lat, lon, azimuth, tilt, hours, 
                   MODE, fake_historical_start_time=FAKE_START):
    """
    Returns array with irradiance data at given location in TIME_DISCR intervals:
    - air_temp (degC)
    - gti (tilted irradiance, W/m^2)
    - precipitation_rate (mm/h)
    - wind_speed_10m (wm/s)
    - wind_direction_10m (degrees)
    Has three modes:
    - 1: forecast: queries the Solcast forecast API. Consumes API tokens.
    - 2: historical: queries the Solcast historical API
    - 3: artificial: simulates forecast data for testing purposes
    """
    match MODE:
        case 1:
            URL = f"https://api.solcast.com.au/data/live/radiation_and_weather?api_key={API_KEY}" \
                f"&latitude={lat}&longitude={lon}&azimuth={azimuth}&tilt={tilt}&array_type=fixed" \
                f"&hours={hours}&period=PT30M&format=json" \
                f"&output_parameters=air_temp,gti,precipitation_rate,wind_speed_10m,wind_direction_10m"
            response = requests.get(url=URL)
            if response.status_code == 200:
                data = response.json()
                return data["estimated_actuals"]
            else:
                raise Exception(f"Error: Solcast API request failed with status code {response.status_code}.")
        case 2:
            end_time = fake_historical_start_time + dt.timedelta(hours=hours)
            if not fake_historical_start_time.utcoffset():
                raise Exception("Error: When fetching fake irradiance data, the start time datetime specified must have timezone information encoded.")
            timezone_hour_offset = fake_historical_start_time.utcoffset().seconds//3600 - 24 # note this will break in places other than the western hemisphere
            URL = f"https://api.solcast.com.au/data/historic/radiation_and_weather?api_key={API_KEY}" \
                f"&latitude={lat}&longitude={lon}&azimuth={azimuth}&tilt={tilt}&array_type=fixed" \
                f"&start={fake_historical_start_time.isoformat()}&end={end_time.isoformat()}&period=PT30M&format=json&time_zone={timezone_hour_offset}" \
                f"&output_parameters=air_temp,gti,precipitation_rate,wind_speed_10m,wind_direction_10m"
            response = requests.get(url=URL)
            if response.status_code == 200:
                data = response.json()
                return data["estimated_actuals"]
            else:
                raise Exception(f"Error: Solcast API request failed with status code {response.status_code}.")
        case 3:
            rng = np.random.default_rng(0)
            start = dt.datetime.now(dt.timezone.utc)
            n = int(hours / TIME_DISCR)
            step = dt.timedelta(hours=TIME_DISCR)
            times = [start + i * step for i in range(n)]
            h = np.array([t.hour + t.minute / 60 for t in times], dtype=float)
            OMEGA = 2 * np.pi / 24
            air_temp = 14 - 8 * np.cos(OMEGA * (h - 2)) + rng.uniform(-2, 2, h.shape)
            gti = np.clip(-13 * (h - 8) * (h - 20) + rng.uniform(0, 100, h.shape), 0, 1100)
            precip = np.clip(-5 * (h - 15) * (h - 17) + rng.uniform(-1, 1, h.shape), 0, None)
            wind_spd = np.clip(4 + 4 * np.sin(OMEGA * h) + rng.uniform(-1, 1, h.shape), 0, 25)
            wind_dir = np.mod(180 * np.sin(OMEGA * h) + 180 + rng.uniform(-5, 5, h.shape), 360)
            output_array = [
                {
                    "air_temp": float(air_temp[i]),
                    "gti": float(gti[i]),
                    "precipitation_rate": float(precip[i]),
                    "wind_speed_10m": float(wind_spd[i]),
                    "wind_direction_10m": float(wind_dir[i]),
                    "period_end": times[i].isoformat(),
                    "period": "PT30M",
                }
                for i in range(n)
            ]
            return output_array
        case _:
            raise Exception("Error: get_irradiance must be called with a mode of either 1, 2, or 3.")


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
    ], 3) # MODE = 3, as we do not have the Solcast API yet
