import csv
import requests
import psycopg2
import time
import math


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


def calculate_theta():
    connection = connect_to_db()
    cursor = connection.cursor()

    cursor.execute("SELECT * from base_route order by id")
    rows = cursor.fetchall()

    commit_interval = 500  # Commit after processing 500 rows
    count = 0

    for i in range(len(rows) - 1):
        current_row = rows[i]
        next_row = rows[i + 1]
        elevation_difference = next_row[9] - current_row[9]
        distance = next_row[6]

        if distance == 0:
            theta = 0
        else:
            theta = math.degrees(math.atan(elevation_difference / distance))

        cursor.execute(
            "UPDATE base_route SET elevation_angle = %s WHERE id = %s",
            (theta, current_row[0]),
        )

        count += 1
        if count % commit_interval == 0:
            connection.commit()
            print(f"Committed {count} rows")

    connection.commit()  # Commit any remaining changes
    cursor.close()
    connection.close()

    print("Updated elevation angles successfully.")


calculate_theta()
