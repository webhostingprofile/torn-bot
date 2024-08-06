import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Path to your service account key
SERVICE_ACCOUNT_KEY = os.getenv('SERVICE_ACCOUNT_KEY')
# Create a dictionary with the environment variables
firebase_credentials = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
    "universe_domain": os.getenv("UNIVERSE_DOMAIN"),
}

# Initialize Firebase app
cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred)


# Initialize Firestore DB
db = firestore.client()

def get_firestore_db():
    return db

def insert_user_key(discord_id, torn_id, torn_api_key):
    doc_ref = db.collection('user_keys').document(discord_id)
    doc_ref.set({
        'discord_id': discord_id,
        'torn_id': torn_id,
        'torn_api_key': torn_api_key,
        'timezone': "",
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
