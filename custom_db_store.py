import psycopg2
import uuid
from datetime import datetime

class CustomDBStore:
    def __init__(self):
        self.connection = psycopg2.connect(
            dbname="jhm_vectordb",
            user="postgres",
            password="charizards",
            host="localhost",
            port="5435"
        )
        self.cursor = self.connection.cursor()

    def put(self, key, value, metadata):
        query = """
        INSERT INTO kb (id, name, data_type, metadata, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        self.cursor.execute(query, (str(uuid.uuid4()), key, 'text', metadata, 'active', datetime.now()))
        self.connection.commit()

    def close(self):
        self.cursor.close()
        self.connection.close()
