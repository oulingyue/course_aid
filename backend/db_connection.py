import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def connect():
    try:
        connection = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT')
        )
        cursor = connection.cursor()

        #execute queries with cursor
        cursor.execute('SELECT version();')
        db_version = cursor.fetchone()
        print(db_version)
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL:{e}")
        return

    return connection


def close(connection):

        connection.close()
        print("PostgreSQL connection closed.")




