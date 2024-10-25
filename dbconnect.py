import psycopg2

def connect_to_db():
    try:
      
        connection = psycopg2.connect(
            dbname='jhm_vectordb',
            user='postgres',
            password='charizards',  
            host='localhost',
            port='5435'  
        )
        
        
        cursor = connection.cursor()
        
        
        print(connection.get_dsn_parameters(), "\n")
        
      
        cursor.execute("SELECT version();")
        
        
        record = cursor.fetchone()
        print("You are connected to - ", record, "\n")
        
        return connection, cursor

    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)

def close_connection(connection, cursor):
    if connection:
        cursor.close()
        connection.close()
        print("PostgreSQL connection is closed")

if __name__ == "__main__":
    conn, cur = connect_to_db()
    
    close_connection(conn, cur)
