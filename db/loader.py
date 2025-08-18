import pandas as pd
import sys


sys.path.append("db")
from connect import connect_to_db


def fetch_data(query):
    connection = connect_to_db(verbose=False)
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
    route_model_query = "SELECT * FROM route_model;"
    irradiance_query = "SELECT * FROM irradiance;"

    route_model_df = fetch_data(route_model_query)
    irradiance_df = fetch_data(irradiance_query)

    print("Data successfully loaded to memory")
    return route_model_df, irradiance_df


if __name__ == "__main__":
    route_model_df, irradiance_df = load_data_to_memory()