import math
import psycopg2


def connect_to_db(db_user, db_password, db_host, db_name):
    return psycopg2.connect(
        host=db_host, database=db_name, user=db_user, password=db_password
    )


def main():
    db_user = ""
    db_password = ""
    db_host = ""
    db_name = ""

    connection = connect_to_db(db_user, db_password, db_host, db_name)

    cursor = connection.cursor()

    cursor.execute("SELECT id, latitude, longitude from base_route order by id")
    rows = cursor.fetchall()

    commit_interval = 500  # Commit after processing 500 rows
    count = 0

    for i in range(len(rows) - 1):
        current_row = rows[i]
        next_row = rows[i + 1]

        lat1, lon1 = current_row[1], current_row[2]
        lat2, lon2 = next_row[1], next_row[2]

        bearing = calculate_compass_bearing(lat1, lon1, lat2, lon2)
        direction = compass_direction(bearing)

        cursor.execute(
            "UPDATE base_route SET car_bearing = %s, car_direction = %s WHERE id = %s",
            (bearing, direction, current_row[0]),
        )

        count += 1
        if count % commit_interval == 0:
            connection.commit()
            print(f"Committed {count} rows")

    connection.commit()
    cursor.close()
    connection.close()

    print("Updated car bearings and directions successfully.")


def calculate_compass_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    delta_lon = lon2 - lon1

    x = math.sin(delta_lon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(
        delta_lon
    )
    initial_bearing = math.atan2(x, y)

    initial_bearing = (math.degrees(initial_bearing) + 360) % 360

    return initial_bearing


def compass_direction(bearing):
    directions = [
        "North",
        "North-East",
        "East",
        "South-East",
        "South",
        "South-West",
        "West",
        "North-West",
    ]
    idx = round(bearing / 45) % 8
    return directions[idx]


if __name__ == "__main__":
    main()
