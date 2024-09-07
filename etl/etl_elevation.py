import csv
import requests
import psycopg2
import time

API_BASE_URL = "https://api.opentopodata.org/v1/srtm30m"


def connect_to_db(db_user, db_password, db_host, db_name):
    return psycopg2.connect(
        host=db_host, database=db_name, user=db_user, password=db_password
    )


def get_elevation(lat, lon):
    params = {"locations": f"{lat},{lon}", "interpolation": "bilinear"}
    response = requests.get(API_BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()
    time.sleep(0.75)  # Manage API rate limits
    return data["results"][0]["elevation"]


def process_elevations(elevations, connection, filename, is_final=False):
    write_elevations_to_csv(elevations, filename, is_final)
    batch_update_elevations(connection, elevations)
    elevations.clear()  # Clear the dictionary after processing


def write_elevations_to_csv(elevations, filename, is_final):
    mode = "a" if not is_final else "w"
    header = not is_final
    with open(filename, mode=mode, newline="") as file:
        writer = csv.writer(file)
        if header:
            writer.writerow(["ID", "Elevation"])
        for id, elevation in elevations.items():
            writer.writerow([id, elevation])
    print("Elevation data written to CSV.")


def batch_update_elevations(connection, elevations):
    cursor = connection.cursor()
    for id, elevation in elevations.items():
        try:
            cursor.execute(
                "UPDATE base_route SET elevation = %s WHERE id = %s", (elevation, id)
            )
            print(f"Updated elevation for ID {id} to {elevation} meters.")
        except Exception as e:
            print(f"Failed to update elevation for ID {id}: {e}")
    connection.commit()
    cursor.close()


def fetch_elevations(connection, batch_size=500):
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id, latitude, longitude FROM base_route WHERE elevation IS NULL"
    )
    rows = cursor.fetchall()
    elevations = {}
    for idx, row in enumerate(rows):
        id, lat, lon = row
        try:
            elevations[id] = get_elevation(lat, lon)
            print(f"Got {elevations[id]} for {lat, lon}, {id}")
            if (idx + 1) % batch_size == 0:
                process_elevations(elevations, connection, "elevations_backup.csv")
        except Exception as e:
            print(f"Failed to retrieve elevation for ID {id}: {e}")
    cursor.close()
    if elevations:  # Process remaining elevations if any
        process_elevations(
            elevations, connection, "elevations_backup.csv", is_final=True
        )


def main(db_user, db_password, db_host, db_name):
    connection = connect_to_db(db_user, db_password, db_host, db_name)
    fetch_elevations(connection)
    connection.close()


main("", "", "", "")
