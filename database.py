import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def get_db_connection():
    connection = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=os.getenv("DB_PORT", "5432")  # Puerto por defecto de PostgreSQL
    )
    return connection