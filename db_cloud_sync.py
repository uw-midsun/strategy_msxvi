import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv


load_dotenv()


def get_table_definition(cursor, table_name):
    """
    Retrieves the column definitions for a given table.

    Parameters:
    cursor (psycopg2.cursor): Cursor to the cloud database.
    table_name (str): The name of the table to get the definition for.

    Returns:
    list of tuples: A list of column definitions (name, type).
    """
    cursor.execute(
        f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
    """
    )
    return cursor.fetchall()


def sync_databases(cloud_db_config, local_db_config, table_name):
    """
    Synchronizes a table from a cloud database to a local database.

    Parameters:
    cloud_db_config (dict): Configuration for the cloud database connection.
    local_db_config (dict): Configuration for the local database connection.
    table_name (str): The name of the table to synchronize.
    """

    print("Connecting to cloud database...")
    cloud_conn = psycopg2.connect(**cloud_db_config)
    cloud_cursor = cloud_conn.cursor(cursor_factory=RealDictCursor)

    print("Connecting to local database...")
    local_conn = psycopg2.connect(**local_db_config)
    local_cursor = local_conn.cursor()

    try:
        print(f"Fetching data from cloud database table '{table_name}'...")
        cloud_cursor.execute(f"SELECT * FROM {table_name}")
        cloud_data = cloud_cursor.fetchall()

        print(f"Fetching table definition for '{table_name}' from cloud database...")
        table_definition = get_table_definition(cloud_cursor, table_name)

        print(f"Checking if table '{table_name}' exists in local database...")
        local_cursor.execute(
            f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name = '{table_name}'
            );
        """
        )
        table_exists = local_cursor.fetchone()[0]

        if not table_exists:
            print(
                f"Table '{table_name}' does not exist in local database. Creating table..."
            )
            if table_definition:
                create_table_query = f"""
                    CREATE TABLE {table_name} (
                        {', '.join([f"{col['column_name']} {col['data_type']}" for col in table_definition])}
                    );
                """
                local_cursor.execute(create_table_query)

        print(f"Clearing existing data from local database table '{table_name}'...")
        local_cursor.execute(f"DELETE FROM {table_name}")

        if cloud_data:
            print(f"Inserting data into local database table '{table_name}'...")
            columns = cloud_data[0].keys()
            column_names = ", ".join(columns)
            column_placeholders = ", ".join(["%s"] * len(columns))
            insert_query = f"INSERT INTO {table_name} ({column_names}) VALUES ({column_placeholders})"

            for row in cloud_data:
                values = tuple(row.values())
                local_cursor.execute(insert_query, values)

        local_conn.commit()
        print("Synchronization complete.")

    except Exception as e:
        print(f"Error: {e}")
        local_conn.rollback()

    finally:
        cloud_cursor.close()
        cloud_conn.close()
        local_cursor.close()
        local_conn.close()
        print("Connections closed.")


def main(table_name):
    cloud_db_config = {
        "host": os.getenv("HOST"),
        "database": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "port": 5432,
    }

    local_db_config = {
        "host": os.getenv("LOCAL_DB_HOST"),
        "database": os.getenv("LOCAL_DB_NAME"),
        "user": os.getenv("LOCAL_DB_USER"),
        "password": os.getenv("LOCAL_DB_PASSWORD"),
        "port": 5432,
    }

    sync_databases(cloud_db_config, local_db_config, table_name)


if __name__ == "__main__":
    main("irradiance")