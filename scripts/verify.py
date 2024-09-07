import psycopg2
import csv


def connect_to_db(db_user, db_password, db_host, db_name):
    return psycopg2.connect(
        host=db_host, database=db_name, user=db_user, password=db_password
    )


def fetch_data(conn, table_name):
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY id;")
        return cursor.fetchall(), [desc[0] for desc in cursor.description]


def verify_data(db_data, db_headers, csv_filename):
    with open(csv_filename, "r") as file:
        reader = csv.reader(file)
        csv_headers = next(reader)
        data = sorted(reader, key=lambda x: int(x[0]))

        if csv_headers != db_headers:
            return False, "Header mismatch"

        if len(db_data) != len(data):
            return False, "Row count mismatch"

        for db_row, csv_row in zip(db_data, data):
            if list(map(str, db_row)) != csv_row:
                print(db_row, csv_row)
                return False, "Data mismatch"

        return True, "Data matches"


conn = connect_to_db("", "", "", "")
try:
    data, headers = fetch_data(conn, "base_route")
    result, message = verify_data(data, headers, "base_route.csv")
    print(message)
finally:
    conn.close()
