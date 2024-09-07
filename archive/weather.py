import random
import string
from datetime import datetime

import geopandas as gpd
import numpy as np
import pandas as pd
import requests
from geoalchemy2 import Geometry, WKTElement
import psycopg2

API_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(lat, long, API_KEY):
    units = "metric"
    exclude = "minutely,hourly,daily,alerts"  # To exclude certain weather reports, right now just using current
    url = f"{API_BASE_URL}?lat={lat}&lon={long}&units={units}&appid={API_KEY}"
    response = requests.get(url)
    if response.status_code != 200:
        print(response.json())
        raise response.raise_for_status()

    weather_data = response.json()
    precipitation = (
        0
        if "rain" not in weather_data
        else weather_data["rain"]["1h"] or weather_data["rain"]["3h"]
    )
    weather_dict = {
        "Latitude": lat,
        "Longitude": long,
        "Temperature (C)": weather_data["main"]["temp"],
        "Wind Speed (m/s)": weather_data["wind"]["speed"],
        "Wind Direction": weather_data["wind"]["deg"],
        "Weather": weather_data["weather"][0]["main"],
        "Weather Description": weather_data["weather"][0]["description"],
        "Pressure (hPa)": weather_data["main"]["pressure"],
        "Precipitation (mm)": precipitation,
        "Cloud Cover": weather_data["clouds"]["all"],
        "Humidity": weather_data["main"]["humidity"],
    }
    return weather_dict


def get_routemodel_gdf(db_user, db_password, db_host, db_name):
    engine = create_engine(
        f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}"
    )

    if not inspect(engine).has_table("base_route"):
        raise SystemError("base_route table does not exist in database")
    routemodel_gdf = gpd.GeoDataFrame(
        pd.read_sql_query(sql="SELECT * FROM base_route", con=engine)
    )
    return routemodel_gdf


def create_weather_update_routemodel(routemodel_gdf, API_KEY, WEATHER_RANGE):
    weather_idx = 0
    weather_df_rows = []
    routemodel_gdf["weather_id"] = (
        pd.to_numeric(routemodel_gdf["weather_id"], errors="coerce")
        .fillna(0)
        .astype(int)
    )

    for row in routemodel_gdf.itertuples():
        weather_fkey_index = int((row.geopy_elapsed_dist_m // WEATHER_RANGE) + 1)
        if weather_fkey_index > weather_idx:
            weather_data = get_weather(row.latitude, row.longitude, API_KEY)
            data = {
                "id": weather_fkey_index,
                "lat": row.latitude,
                "lon": row.longitude,
                "temperature": weather_data["Temperature (C)"],
                "humidity": weather_data["Humidity"],
                "wind_speed": weather_data["Wind Speed (m/s)"],
                "wind_direction": weather_data["Wind Direction"],
                "cloud_cover": weather_data["Cloud Cover"],
            }
            weather_df_rows.append(data)
            weather_idx = weather_fkey_index
        routemodel_gdf.at[row.id - 1, "weather_id"] = weather_idx

    weather_df = pd.DataFrame(weather_df_rows)
    weather_df.index += 1  # Make it 1-indexed
    return routemodel_gdf, weather_df


def update_database(routemodel_gdf, weather_df, db_user, db_password, db_host, db_name):
    engine = create_engine(
        f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}/{db_name}"
    )

    weather_response = weather_df.to_sql(  # weather first b/c of routemodel fkey
        name="weather",
        con=engine,
        schema="public",
        if_exists="replace",
        index=False,
        method="multi",
    )
    if weather_df.shape[0] != weather_response:
        raise SystemError("weather insertion failed")
    # routemodel_gdf["geometry"] = routemodel_gdf["geometry"].apply(
    #     lambda x: WKTElement(x.wkt, srid=4326)
    # )
    routemodel_response = routemodel_gdf.to_sql(
        name="base_route",
        con=engine,
        schema="public",
        if_exists="replace",
        index=False,
        method="multi",
        dtype={"geometry": Geometry("POINT", srid=4326)},
    )

    if routemodel_gdf.shape[0] != routemodel_response:
        raise SystemError("dataframe insertion failed")

    print("weather and routemodel dataframe insertion success")


def connect_to_db(db_user, db_password, db_host, db_name):
    return psycopg2.connect(
        host=db_host, database=db_name, user=db_user, password=db_password
    )


def main(db_user, db_password, db_host, db_name, API_KEY=""):
    connect_to_db(db_user, db_password, db_host, db_name)


if __name__ == "__main__":
    db_user = ""
    db_password = ""
    db_host = ""
    db_name = ""
    API_KEY = ""
    main(db_user, db_password, db_host, db_name, API_KEY)
