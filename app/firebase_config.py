import os
import json
import tempfile
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
import streamlit as st

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
    try:
        # Check if we are running on Streamlit Cloud with Secrets
        if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
            # Load from secrets (assuming it's a JSON string or dict)
            service_account_info = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
            if isinstance(service_account_info, str):
                service_account_info = json.loads(service_account_info)
            
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket
            })
        elif cred_path and os.path.exists(cred_path):
            # Load from local file
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket
            })
        else:
            print(f"Warning: Firebase credentials not found in secrets or at {cred_path}")
    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")

# Export Firestore client, Storage bucket, and Auth module
try:
    db = firestore.client()
    bucket = storage.bucket()
except ValueError as e:
    print(f"Error initializing Firebase services: {e}")
    db = None
    bucket = None
