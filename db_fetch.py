import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import timedelta


load_dotenv()


def connect_to_db():
    db_user, db_password, db_host, db_name = (
        os.getenv("DB_USER"),
        os.getenv("DB_PASSWORD"),
        os.getenv("HOST"),
        os.getenv("DB_NAME"),
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



