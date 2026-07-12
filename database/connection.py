import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    database_url=os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("Database Url not set!")
    
    conn=psycopg2.connect(database_url)

    return conn
