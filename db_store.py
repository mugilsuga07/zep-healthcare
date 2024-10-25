import psycopg2
import uuid

class CustomDBStore:
    def __init__(self):
        try:
            self.connection = psycopg2.connect(
                host="localhost",
                database="jhm_vectordb",
                user="postgres",
                password="charizards"
            )
            self.cursor = self.connection.cursor()
        except (Exception, psycopg2.Error) as error:
            print("Error while connecting to PostgreSQL", error)

    def save_data(self, data_type, name, metadata=None):
        try:
            if data_type == 'summaries':
                query = "INSERT INTO kb_docs (id, kb_id, title, text) VALUES (%s, %s, %s, %s)"
                self.cursor.execute(query, (str(uuid.uuid4()), str(uuid.uuid4()), name, metadata))
            elif data_type == 'kb':
                query = "INSERT INTO kb (id, name, data_type, metadata, status, created_by, created_date, last_modified_by, last_modified_date, organization_id, tenant_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                self.cursor.execute(query, (str(uuid.uuid4()), name, 'text', metadata, 'active', str(uuid.uuid4()), False, str(uuid.uuid4()), '{}', str(uuid.uuid4()), '{}'))
            self.connection.commit()
        except (Exception, psycopg2.Error) as error:
            print("Error while saving data to PostgreSQL", error)

    def close(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()

