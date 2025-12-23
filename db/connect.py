import os
from dotenv import load_dotenv
import psycopg2

def create_db(is_local=True):
    """
    Initialize cloud postgres database (or local postgres database if is_local is True).
    """
    load_dotenv()
    host = os.getenv("LOCAL_DB_HOST" if is_local else "DB_HOST")
    port = os.getenv("LOCAL_DB_PORT" if is_local else "DB_PORT")
    user = os.getenv("LOCAL_DB_USER" if is_local else "DB_USER")
    password = os.getenv("LOCAL_DB_PASSWORD" if is_local else "DB_PASSWORD")
    dbname = os.getenv("LOCAL_DB_NAME" if is_local else "DB_NAME")
    try:
        connection = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname="postgres"
        )
        connection.autocommit = True  # Set autocommit to True to create the database
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE {dbname}")
        cursor.close()
        connection.close()
        print("Database created successfully")
    except Exception as e:
        print(f"An error occurred: {e}")
        return None # Return None if the connection fails
    return None

def connect_to_db(is_local=True):
    """
    Return connection to existing cloud postgres database (or local postgres database if is_local is True).
    """
    load_dotenv()
    host = os.getenv("LOCAL_DB_HOST" if is_local else "DB_HOST")
    port = os.getenv("LOCAL_DB_PORT" if is_local else "DB_PORT")
    user = os.getenv("LOCAL_DB_USER" if is_local else "DB_USER")
    password = os.getenv("LOCAL_DB_PASSWORD" if is_local else "DB_PASSWORD")
    dbname = os.getenv("LOCAL_DB_NAME" if is_local else "DB_NAME")
    try:
        connection = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=dbname
        )
        print("Connection successful")
        return connection  # Return the connection object for further use
    except Exception as e:
        print(f"An error occurred: {e}")
        return None  # Return None if the connection fails
    
if __name__ == "__main__":
    create_db()
    connect_to_db()
