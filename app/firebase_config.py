import os
import json
import tempfile
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
import streamlit as st

# Load local .env (ignored on cloud deployments where env vars come from the platform)
load_dotenv(override=True)

# Storage bucket name (used across all credential sources)
storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET", "")

# Optional local credential file path
cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
if cred_path and not os.path.isabs(cred_path):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.normpath(os.path.join(BASE_DIR, cred_path))

# ── Initialize Firebase app (only once per process) ──────────────────────────
if not firebase_admin._apps:
    try:
        _service_account_info = None

        # ── SOURCE 1: Streamlit Community Cloud (st.secrets) ─────────────────
        try:
            if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
                _service_account_info = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
                if isinstance(_service_account_info, str):
                    _service_account_info = json.loads(_service_account_info)
                if "FIREBASE_STORAGE_BUCKET" in st.secrets:
                    storage_bucket = st.secrets["FIREBASE_STORAGE_BUCKET"]
        except Exception:
            pass  # No st.secrets on Render/local

        # ── SOURCE 2: Render / Railway / Heroku (plain env var as JSON string) ─
        if not _service_account_info:
            raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT", "")
            if raw_json:
                try:
                    _service_account_info = json.loads(raw_json)
                except json.JSONDecodeError:
                    print("Warning: FIREBASE_SERVICE_ACCOUNT env var is not valid JSON")

        # ── SOURCE 3: Local service account key file ──────────────────────────
        if _service_account_info:
            cred = credentials.Certificate(_service_account_info)
            firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})
        elif cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})
        else:
            print(
                f"Warning: Firebase credentials not found. "
                f"Set FIREBASE_SERVICE_ACCOUNT env var on Render, "
                f"or FIREBASE_CREDENTIALS_PATH for local dev."
            )

    except Exception as e:
        print(f"Failed to initialize Firebase: {e}")

# ── Export shared clients ─────────────────────────────────────────────────────
try:
    db = firestore.client()
    bucket = storage.bucket()
except Exception as e:
    print(f"Error initializing Firebase services: {e}")
    db = None
    bucket = None
