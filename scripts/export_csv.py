import psycopg2
import csv


def connect_to_db(db_user, db_password, db_host, db_name):
    return psycopg2.connect(
        host=db_host, database=db_name, user=db_user, password=db_password
    )


def fetch_data(conn, table_name):
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table_name};")
        data = cursor.fetchall()
        headers = [desc[0] for desc in cursor.description]
        return headers, data


def write_to_csv(headers, data, table_name):
    with open(f"{table_name}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(data)


def main(db_user, db_password, db_host, db_name, table_name):
    conn = connect_to_db(db_user, db_password, db_host, db_name)
    try:
        headers, data = fetch_data(conn, table_name)
        write_to_csv(headers, data, table_name)
    finally:
        conn.close()


if __name__ == "__main__":
    main(
        "",
        "",
        "",
        "",
        "",
    )
