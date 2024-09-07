import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import timedelta

load_dotenv()


def connect_to_db():
    db_user, db_password, db_host, db_name = (
        os.getenv("LOCAL_DB_USER"),
        os.getenv("LOCAL_DB_PASSWORD"),
        os.getenv("LOCAL_DB_HOST"),
        os.getenv("LOCAL_DB_NAME"),
    )
    return psycopg2.connect(
        host=db_host, database=db_name, user=db_user, password=db_password
    )


def fetch_data(query):
    connection = connect_to_db()
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(results, columns=columns)
    except Exception as e:
        print(f"An error occurred: {e}")
        df = pd.DataFrame()  # Return an empty DataFrame in case of an error
    finally:
        cursor.close()
        connection.close()
    return df


def load_data_to_memory():
    connection = connect_to_db()

    base_route_query = "SELECT * FROM base_route ORDER BY id;"
    irradiance_query = "SELECT * FROM irradiance;"

    base_route_df = fetch_data(base_route_query)
    irradiance_df = fetch_data(irradiance_query)

    connection.close()

    return base_route_df, irradiance_df


def map_distance_to_id(base_route_df, route_symbol, distance):
    df = base_route_df[base_route_df["symbol"] == route_symbol].copy()
    df["distance_difference"] = abs(df["stage_elapsed_distance"] - distance)
    result_df = df.nsmallest(1, "distance_difference")
    return result_df


def map_distance_to_irradiance(
    irradiance_df,
    base_route_df,
    route_symbol,
    distance,
    time,
    start_time=None,
):
    df = base_route_df[base_route_df["symbol"] == route_symbol].copy()
    df["distance_difference"] = abs(df["stage_elapsed_distance"] - distance)
    stage_id, route_start_time = df.nsmallest(1, "distance_difference")[
        ["stage_id", "route_start_time"]
    ].values[0]

    if start_time:
        route_start_time = start_time

    time = int(time)
    target_time = route_start_time + timedelta(seconds=time)

    irradiance_df["time_difference"] = abs(
        (irradiance_df["period_end"] - target_time).dt.total_seconds()
    )
    result_df = irradiance_df[irradiance_df["route_model_id"] == stage_id].nsmallest(
        1, "time_difference"
    )
    return result_df
