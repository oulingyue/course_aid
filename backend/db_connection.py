import psycopg2

db_host = "courseaid-db.cnk8wwwum9xd.us-east-2.rds.amazonaws.com"
db_name = "postgres"
db_user = "courseaidadmin"
db_pass = "courseaid5200"

def connect():
    try:
        connection = psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass,
            port="5432"
        )
        cursor = connection.cursor()

        #execute queries with cursor
        cursor.execute('SELECT version();')
        db_version = cursor.fetchone()
        print(db_version)
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL:{e}")
        return

    return cursor, connection


def close(cursor, connection):

        cursor.close()
        connection.close()
        print("PostgreSQL connection closed.")




