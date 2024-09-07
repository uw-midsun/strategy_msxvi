import json
import pandas as pd
from sqlalchemy import create_engine
from geoalchemy2 import Geometry, WKTElement
import geopandas as gpd
from shapely.geometry import Point
from geopy.distance import great_circle


def json_to_geodf(json_filepath):
    with open(json_filepath, "r") as file:
        data = json.load(file)

    routes = []
    last_point = None
    total_distance = 0
    id = 0

    for feature in data["features"]:
        route_name = feature["properties"]["Name"]
        description = feature["properties"]["description"]
        for segment in feature["geometry"]["coordinates"]:
            for lon, lat in segment:
                point = {"longitude": lon, "latitude": lat}
                if last_point:
                    distance_from_last = great_circle(
                        (last_point["latitude"], last_point["longitude"]), (lat, lon)
                    ).meters
                    total_distance += distance_from_last
                else:
                    distance_from_last = 0

                routes.append(
                    {
                        "id": id,
                        "name": route_name.strip(),
                        "description": description,
                        "longitude": lon,
                        "latitude": lat,
                        "weather_id": None,
                        "geopy_dist_from_last_m": distance_from_last,
                        "geopy_elapsed_dist_m": total_distance,
                    }
                )
                id += 1
                last_point = point

    df = pd.DataFrame(routes)
    gdf = gpd.GeoDataFrame(
        df, geometry=[Point(xy) for xy in zip(df.longitude, df.latitude)]
    )
    gdf.set_crs(epsg=4326, inplace=True)

    return gdf


def gdf_to_postgres(gdf, engine, table_name):
    dtype = {"geometry": Geometry(geometry_type="POINT", srid=4326)}
    gdf["geometry"] = gdf["geometry"].apply(lambda x: WKTElement(x.wkt, srid=4326))
    gdf.to_sql(table_name, con=engine, if_exists="replace", index=False, dtype=dtype)
    print("Data inserted successfully")


def main(gpx_json_filepath, db_user, db_password, db_host, db_name, table_name):
    print("1) Converting JSON to GeoDataFrame...")
    gdf = json_to_geodf(gpx_json_filepath)

    csv_filepath = gpx_json_filepath.replace(".geojson", ".csv")
    gdf.to_csv(csv_filepath)
    print(f"CSV file created at: {csv_filepath}")

    print("2) Inserting GeoDataFrame into PostgreSQL...")
    engine = create_engine(f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}")
    gdf_to_postgres(gdf, engine, table_name)


if __name__ == "__main__":
    gpx_json_filepath = ""
    db_user = ""
    db_password = ""
    db_host = ""
    db_name = ""
    table_name = ""
    main(gpx_json_filepath, db_user, db_password, db_host, db_name, table_name)
