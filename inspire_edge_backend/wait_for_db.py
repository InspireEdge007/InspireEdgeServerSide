import psycopg2
import time
import os

DB_HOST = os.getenv('DB_HOST', 'db')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'edgeAI_db')
DB_USER = os.getenv('DB_USER', 'edgeAI_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'yourpassword')

def wait_for_db():
    while True:
        try:
            print("Attempting to connect to the database...")
            conn = psycopg2.connect(
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
            )
            conn.close()
            print("Database is ready!")
            break
        except psycopg2.OperationalError:
            print("Database is not ready. Retrying in 1 second...")
            time.sleep(1)


if __name__ == "__main__":
    wait_for_db()
