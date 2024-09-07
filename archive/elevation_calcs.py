import psycopg2
import pandas as pd
import numpy as np

M = 300
G = 9.81


def connect_to_db():
    db_user, db_password, db_host, db_name = (
        "",
        "",
        "",
        "",
    )
    return psycopg2.connect(
        host=db_host, database=db_name, user=db_user, password=db_password
    )


def fetch_symbols():
    conn = connect_to_db()
    query = "SELECT DISTINCT symbol FROM base_route ORDER BY symbol"
    symbols_df = pd.read_sql_query(query, conn)
    conn.close()
    return symbols_df["symbol"].tolist()


def fetch_data_for_symbol(symbol):
    conn = connect_to_db()
    query = f"SELECT * FROM base_route WHERE symbol = '{symbol}' ORDER BY id"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def calculate_elevation_weight(df):
    df["elevation_weight"] = 0.0
    elevation_weight = 0.0

    for index, row in df.iterrows():
        elevation_angle = row["elevation_angle"]
        if elevation_angle < 0:
            row_value = M * G * np.sin(np.radians(elevation_angle)) * 0.6
        else:
            row_value = M * G * np.sin(np.radians(elevation_angle))

        elevation_weight += row_value
        df.at[index, "elevation_weight"] = elevation_weight

    return df


def update_elevation_weight_in_db(df):
    conn = connect_to_db()
    cursor = conn.cursor()

    for index, row in df.iterrows():
        query = f"""
        UPDATE base_route
        SET elevation_weight = {row['elevation_weight']}
        WHERE id = {row['id']}
        """
        cursor.execute(query)

    conn.commit()
    cursor.close()
    conn.close()


def main():
    symbols = fetch_symbols()
    for symbol in symbols:
        df = fetch_data_for_symbol(symbol)
        df = calculate_elevation_weight(df)
        update_elevation_weight_in_db(df)
        print(f"Updated data for symbol {symbol}.")


if __name__ == "__main__":
    main()
