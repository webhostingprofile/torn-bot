import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Path to your service account key
SERVICE_ACCOUNT_KEY = os.getenv('SERVICE_ACCOUNT_KEY')

# Initialize the Firebase Admin SDK
cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
firebase_admin.initialize_app(cred)

# Initialize Firestore DB
db = firestore.client()

def insert_user_key(discord_id, torn_id, torn_api_key):
    doc_ref = db.collection('user_keys').document(discord_id)
    doc_ref.set({
        'discord_id': discord_id,
        'torn_id': torn_id,
        'torn_api_key': torn_api_key
    })
    print(f"User key inserted/updated for torn ID: {torn_id}")

def fetch_user_key(discord_id):
    doc_ref = db.collection('user_keys').document(discord_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    else:
        return None

def test_insert_data():
    doc_ref = db.collection('user_stats').document('discord_user_id')
    doc_ref.set({
        'torn_id': 'discord_user_id',
        'last_call': firestore.SERVER_TIMESTAMP,
        'strength': 100,
        'speed': 120,
        'defense': 80,
        'dexterity': 150,
        'total': 450
    })
    print("Dummy data inserted successfully!")

# Example usage
if __name__ == "__main__":
    # Test insert operation
    insert_user_key('123456789', 'example_torn_id', 'example_torn_api_key')

    # Fetch user key to verify
    fetched_user_key = fetch_user_key('123456789')
    print(f"Fetched User Key: {fetched_user_key}")

    # Test inserting dummy data
    test_insert_data()
