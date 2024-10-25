import psycopg2

try:
    connection = psycopg2.connect(
        dbname="jhm_vectordb",  
        user="postgres",  
        password="charizards",  
        host="localhost",
        port="5432"
    )
    print("Connection successful")
except Exception as e:
    print(f"Error: {e}")
