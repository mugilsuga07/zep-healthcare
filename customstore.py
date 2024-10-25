import psycopg2
from psycopg2 import sql

class CustomStore:
    def __init__(self, db_name='your_db_name', user='your_user', password='your_password', host='localhost', port='5432'):
        self.connection = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        self.cursor = self.connection.cursor()
        self.create_tables()

    def create_tables(self):
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS assessment (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS plan (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS summary (
                id SERIAL PRIMARY KEY,
                text TEXT NOT NULL
            )
        ''')
        self.connection.commit()

    def save_data(self, section, text):
        query = sql.SQL("INSERT INTO {} (text) VALUES (%s)").format(sql.Identifier(section))
        self.cursor.execute(query, [text])
        self.connection.commit()

    def retrieve_data(self, section):
        query = sql.SQL("SELECT * FROM {}").format(sql.Identifier(section))
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def close(self):
        self.cursor.close()
        self.connection.close()
