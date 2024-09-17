import psycopg2


def create_db():
    """
    Initialize postgres database.
    """
    return None


def connect_to_db(db_user='postgres', db_host='localhost', db_name='', db_password=''):
    """
    Connect to database.
    """
    return psycopg2.connect(host=db_host, database=db_name, user=db_user, password=db_password)






