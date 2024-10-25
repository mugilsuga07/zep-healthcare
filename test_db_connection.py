# test_db_connection.py
import psycopg2

try:
    connection = psycopg2.connect(
        dbname="jhm_vectordb",  # Ensure this matches your created DB name
        user="postgres",  # Replace with your actual username
        password="charizards",  # Replace with your actual password
        host="localhost",
        port="5435"
    )
    print("Connection successful")
except Exception as e:
    print(f"Error: {e}")
