import os
from dotenv import load_dotenv
import psycopg2


def create_db(is_local=False):
    """
    Initialize cloud postgres database (or local postgres database if is_local is True).
    """

    # Load environment variables from .env file
    load_dotenv()

    # Retrieve the database configuration from environment variables
    host = os.getenv("LOCAL_DB_HOST" if is_local else "DB_HOST")
    port = os.getenv("LOCAL_DB_PORT" if is_local else "DB_PORT")
    user = os.getenv("LOCAL_DB_USER" if is_local else "DB_USER")
    password = os.getenv("LOCAL_DB_PASSWORD" if is_local else "DB_PASSWORD")
    dbname = os.getenv("LOCAL_DB_NAME" if is_local else "DB_NAME")

    try:
        # Create a connection to the PostgreSQL database
        connection = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname="postgres"
        )
        connection.autocommit = True  # Set autocommit to True to create the database
        cursor = connection.cursor()

        # Create the database
        cursor.execute(f"CREATE DATABASE {dbname}")

        # Close the cursor and the connection
        cursor.close()
        connection.close()

        print("Database created successfully")
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return None # Return None if the connection fails

    return None


def connect_to_db(is_local=False):
    """
    Return connection to existing cloud postgres database (or local postgres database if is_local is True).
    """
    # Load environment variables from .env file
    load_dotenv()

    # Retrieve the database configuration from environment variables
    host = os.getenv("LOCAL_DB_HOST" if is_local else "DB_HOST")
    port = os.getenv("LOCAL_DB_PORT" if is_local else "DB_PORT")
    user = os.getenv("LOCAL_DB_USER" if is_local else "DB_USER")
    password = os.getenv("LOCAL_DB_PASSWORD" if is_local else "DB_PASSWORD")
    dbname = os.getenv("LOCAL_DB_NAME" if is_local else "DB_NAME")

    try:
        # Create a connection to the PostgreSQL database
        connection = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=dbname
        )
        print("Connection successful")
        return connection  # Return the connection object for further use

    except Exception as e:
        print(f"An error occurred: {e}")
        return None  # Return None if the connection fails
    
    
if __name__ == "__main__":
    
    # Connects to cloud database
    # Set arguments to True to connect to local database

    create_db()
    connect_to_db()
