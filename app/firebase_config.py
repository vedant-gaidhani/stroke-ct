import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth

# Load environment variables
load_dotenv(override=True)

# Get Firebase configuration from .env
cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")

# Resolve relative path for credentials
if cred_path and not os.path.isabs(cred_path):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.normpath(os.path.join(BASE_DIR, cred_path))

# Initialize Firebase app only if it hasn't been initialized yet
if not firebase_admin._apps:
    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'storageBucket': storage_bucket
        })
    else:
        print(f"Warning: Firebase credentials file not found at {cred_path}")

# Export Firestore client, Storage bucket, and Auth module
try:
    db = firestore.client()
    bucket = storage.bucket()
except ValueError as e:
    print(f"Error initializing Firebase services: {e}")
    db = None
    bucket = None
