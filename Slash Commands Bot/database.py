import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL')  # Get database URL from environment variable

def connect_to_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL database: {e}")

def execute_query(query, params=None):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    cur.close()
    conn.close()

def fetch_query(query, params=None):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(query, params)
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result
