import os
from dotenv import load_dotenv
import psycopg2


def create_db():
    """
    Initialize postgres database.
    """
    return None


def connect_to_db():
    # Load environment variables from .env file
    load_dotenv()

    # Retrieve the database configuration from environment variables
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    dbname = os.getenv("DB_NAME")

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