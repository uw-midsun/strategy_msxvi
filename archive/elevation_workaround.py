import csv
import psycopg2
from psycopg2.extras import execute_values


def import_csv_to_temp_table(connection, csv_file_path):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TEMP TABLE IF NOT EXISTS temp_elevation (
                id INTEGER PRIMARY KEY,
                elevation DOUBLE PRECISION
            );
        """
        )
        with open(csv_file_path, "r") as f:
            reader = csv.reader(f)
            next(reader)  # Skip the header row
            execute_values(
                cursor,
                """
                INSERT INTO temp_elevation (id, elevation)
                VALUES %s;
            """,
                [(int(float(row[0])), float(row[9])) for row in reader if row[0] != ""],
            )
        connection.commit()


def update_main_table_with_elevation(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE base_route
            SET elevation = temp.elevation
            FROM temp_elevation AS temp
            WHERE base_route.id = temp.id;
        """
        )
        connection.commit()


def connect_to_db(db_user, db_password, db_host, db_name):
    return psycopg2.connect(
        host=db_host, database=db_name, user=db_user, password=db_password
    )


def main():
    db_user = ""
    db_password = ""
    db_host = ""
    db_name = ""

    # Connect to the PostgreSQL database
    connection = connect_to_db(db_user, db_password, db_host, db_name)

    try:
        # Import the CSV data into a temporary table
        import_csv_to_temp_table(connection, "base_route.csv")

        # Update the main table with elevation data
        update_main_table_with_elevation(connection)

    finally:
        connection.close()


if __name__ == "__main__":
    main()
