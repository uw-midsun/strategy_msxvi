from db.connect import connect_to_db
from psycopg2.extras import execute_values

class DBUpload:
    def __init__(self):
        self.connection = connect_to_db()
        self.cursor = self.connection.cursor()
        self.init_table()

    def init_table(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_name VARCHAR(50),
                    value FLOAT 
                );
            """)
            self.connection.commit()
        except Exception as e:
            print(f"Error creating table: {e}")

    def insert_data_point(self, key, value):
        self.cursor.execute("""
            INSERT INTO telemetry (message_name, value)
            VALUES (%s, %s)
        """, (key, float(value)))

    def upload(self, buffer):
        try:
            values = [(key, float(value)) for data in buffer for key, value in data.items()] 
            execute_values(self.cursor, """
                INSERT INTO telemetry (message_name, value)
                VALUES %s
            """, values)
            self.connection.commit()
            print("Data uploaded successfully")
        except Exception as e:
            print(f"Error uploading data: {e}")
            self.connection.rollback()