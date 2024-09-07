import csv
import io
import requests
import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


def connect_to_db(db_user, db_password, db_host, db_name):
    print("Connecting to database...")
    conn = psycopg2.connect(
        host=db_host, database=db_name, user=db_user, password=db_password
    )
    print(f"Connected to database: {db_name}")
    return conn


def refresh_forecast_irradiance(lat, long, API_KEY):
    url = f"https://api.solcast.com.au/data/forecast/radiation_and_weather?latitude={lat}&longitude={long}&hours=72&output_parameters=air_temp%2Cghi%2Cgti%2Cclearsky_ghi%2Cclearsky_gti%2Cdewpoint_temp%2Cprecipitation_rate%2Crelative_humidity%2Cwind_direction_10m%2Cwind_speed_10m&array_type=fixed&terrain_shading=true&format=csv&api_key={API_KEY}"
    response = requests.get(url)
    return response.content


def refresh_live_irradiance(lat, long, API_KEY):
    url = f"https://api.solcast.com.au/data/live/radiation_and_weather?latitude={lat}&longitude={long}&hours=72&output_parameters=air_temp%2Cghi%2Cgti%2Cclearsky_ghi%2Cclearsky_gti%2Cdewpoint_temp%2Cprecipitation_rate%2Crelative_humidity%2Cwind_direction_10m%2Cwind_speed_10m&array_type=fixed&terrain_shading=true&format=csv&api_key={API_KEY}"
    response = requests.get(url)
    return response.content


def parse_weather_data(data):
    rows = []
    reader = csv.DictReader(io.StringIO(data.decode("utf-8")))
    for row in reader:
        try:
            period_end = datetime.strptime(row["period_end"], "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            period_end = datetime.strptime(row["period_end"], "%Y-%m-%d")
        rows.append(
            (
                int(row["air_temp"]),
                int(row["ghi"]),
                int(row["gti"]),
                int(row["clearsky_ghi"]),
                int(row["clearsky_gti"]),
                float(row["dewpoint_temp"]),
                float(row["precipitation_rate"]),
                float(row["relative_humidity"]),
                int(row["wind_direction_10m"]),
                float(row["wind_speed_10m"]),
                period_end,
                row["period"],
            )
        )
    return rows


def insert_weather_data(cursor, conn, data, stage_id, data_type):
    rows = parse_weather_data(data)
    query = """
        INSERT INTO irradiance_staging (
            air_temp, ghi, gti, clearsky_ghi, clearsky_gti, dewpoint_temp, 
            precipitation_rate, relative_humidity, wind_direction_10m, wind_speed_10m,
            period_end, period, route_model_id, data_type, last_updated_time
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    last_updated_time = datetime.now()
    data_to_insert = [(*row, stage_id, data_type, last_updated_time) for row in rows]
    cursor.executemany(query, data_to_insert)
    conn.commit()


def delete_existing_data(cursor, stage_id):
    query = "DELETE FROM irradiance WHERE route_model_id = %s"
    cursor.execute(query, (stage_id,))


def move_data_from_staging(cursor, stage_id):
    query = """
    INSERT INTO irradiance (
        air_temp, ghi, gti, clearsky_ghi, clearsky_gti, dewpoint_temp, 
        precipitation_rate, relative_humidity, wind_direction_10m, wind_speed_10m,
        period_end, period, route_model_id, data_type, last_updated_time
    )
    SELECT air_temp, ghi, gti, clearsky_ghi, clearsky_gti, dewpoint_temp, 
           precipitation_rate, relative_humidity, wind_direction_10m, wind_speed_10m,
           period_end, period, route_model_id, data_type, last_updated_time
    FROM irradiance_staging
    WHERE route_model_id = %s
    """
    cursor.execute(query, (stage_id,))
    cursor.execute(
        "DELETE FROM irradiance_staging WHERE route_model_id = %s", (stage_id,)
    )


def main(connection, stage_symbol, replace_existing=False):
    API_KEY = os.getenv("IRRADIANCE_API")
    cursor = connection.cursor()
    clause = f"WHERE symbol = '{stage_symbol}'" if stage_symbol else ""
    query = f"""
    SELECT DISTINCT ON (name, stage_id) name, latitude, longitude, stage_id
    FROM base_route
    {clause}
    ORDER BY name, stage_id, id ASC
    """
    try:
        cursor.execute(query)
        rows = cursor.fetchall()

        for _, latitude, longitude, stage_id in tqdm(rows, desc="Processing stages"):
            forecast_result = refresh_forecast_irradiance(latitude, longitude, API_KEY)
            insert_weather_data(
                cursor, connection, forecast_result, stage_id, "forecast"
            )

            live_result = refresh_live_irradiance(latitude, longitude, API_KEY)
            insert_weather_data(cursor, connection, live_result, stage_id, "live")

            if replace_existing:
                delete_existing_data(cursor, stage_id)

            move_data_from_staging(cursor, stage_id)

    except Exception as e:
        connection.rollback()
        print(f"An error occurred: {e}")
    finally:
        cursor.close()
        connection.close()
        print("Database connection closed.")


if __name__ == "__main__":
    connection = connect_to_db("postgres", 'QSeR,",L`|86=%kD', "34.121.96.129", "prod")
    stage_symbol = "1A"
    main(connection, stage_symbol, replace_existing=True)
