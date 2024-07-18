import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT')

def connect_to_db():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        print(f"Connected to {DB_NAME} database on PostgreSQL on port {DB_PORT}")
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        return None

def execute_query(query, params=None):
    conn = connect_to_db()
    if conn is None:
        return
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        cur.close()
    except psycopg2.Error as e:
        print(f"Error executing query: {e}")
    finally:
        conn.close()

def fetch_query(query, params=None):
    conn = connect_to_db()
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        result = cur.fetchone()
        cur.close()
        return result
    except psycopg2.Error as e:
        print(f"Error fetching query: {e}")
        return None
    finally:
        conn.close()

def insert_user_key(discord_id, torn_id, torn_api_key):
    query = """
    INSERT INTO user_keys (discord_id, torn_id, torn_api_key)
    VALUES (%s, %s, %s)
    """
    params = (discord_id, torn_id, torn_api_key)
    execute_query(query, params)
    print(f"User key inserted/updated for torn ID: {torn_id}")

def test_insert_data():
    query = """
    INSERT INTO user_stats (torn_id, last_call, strength, speed, defense, dexterity, total)
    VALUES (%s, current_timestamp, %s, %s, %s, %s, %s)
    """
    params = ("discord_user_id", 100, 120, 80, 150, 450)  # Replace with actual data
    execute_query(query, params)
    print("Dummy data inserted successfully!")

def fetch_user_key(discord_id):
    query = "SELECT * FROM user_keys WHERE discord_id = %s"
    params = (discord_id,)
    result = fetch_query(query, params)
    if result:
        discord_id = result[0]
        return result
    else:
        return None

# Example usage
if __name__ == "__main__":
    connection = connect_to_db()
    
    # # Create table if not exists
    # create_table_query = """
    # CREATE TABLE IF NOT EXISTS user_keys (
    #     torn_id BIGINT PRIMARY KEY,
    #     torn_api_key VARCHAR(100) NOT NULL
    # );
    # """
    # execute_query(create_table_query)

    # Test insert operation
    insert_user_key('123456789', 'example_torn_api_key')

    # Fetch user info to verify
    # fetched_torn_id = fetch_user_info('123456789')
    # print(f"Fetched Discord ID: {fetched_torn_id}")

    # Close the connection when done
    if connection:
        connection.close()
        print("PostgreSQL connection is closed")
