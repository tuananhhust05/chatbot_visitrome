
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection parameters
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# Folder containing SQL scripts
SQL_FOLDER = "./docker_init/scripts_sql"

def connect_to_database():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print("Connected to the database successfully!")
        return conn
    except (Exception, psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return None

def execute_sql_script(conn, script_path):
    try:
        cursor = conn.cursor()
        with open(script_path, 'r') as sql_file:
            sql_script = sql_file.read()
        cursor.execute(sql_script)
        conn.commit()
        print(f"SQL script '{script_path}' executed successfully!")
    except (Exception, psycopg2.Error) as error:
        print(f"Error executing SQL script '{script_path}':", error)
    finally:
        if cursor:
            cursor.close()

def main():
    conn = connect_to_database()
    if conn:
        for filename in os.listdir(SQL_FOLDER):
            if filename.endswith(".sql"):
                script_path = os.path.join(SQL_FOLDER, filename)
                execute_sql_script(conn, script_path)
        conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    main()
