import os
import json
import tempfile
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
import streamlit as st

# Load local .env (ignored on cloud deployments)
load_dotenv(override=True)

# Storage bucket name
storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET", "")

# Optional local credential file path
cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
if cred_path and not os.path.isabs(cred_path):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    cred_path = os.path.normpath(os.path.join(BASE_DIR, cred_path))


def _deep_dict(obj):
    """Convert Streamlit AttrDict (or any nested mapping) to a plain Python dict."""
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if isinstance(obj, dict):
        return {k: _deep_dict(v) for k, v in obj.items()}
    return obj


# ── Initialize Firebase app (only once per process) ──────────────────────────
if not firebase_admin._apps:
    _service_account_info = None
    _source = "none"

    # ── SOURCE 1: Streamlit Community Cloud (st.secrets) ─────────────────
    try:
        if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
            raw = st.secrets["FIREBASE_SERVICE_ACCOUNT"]
            if isinstance(raw, str):
                _service_account_info = json.loads(raw)
            else:
                # TOML table → Streamlit AttrDict → plain dict
                _service_account_info = _deep_dict(dict(raw))
            _source = "st.secrets"
            # Also grab storage bucket from secrets if available
            if "FIREBASE_STORAGE_BUCKET" in st.secrets:
                storage_bucket = st.secrets["FIREBASE_STORAGE_BUCKET"]
    except Exception as e:
        print(f"[firebase_config] st.secrets read failed: {e}")

    # ── SOURCE 2: Render / Railway / Heroku (env var as JSON string) ─────
    if not _service_account_info:
        raw_json = os.getenv("FIREBASE_SERVICE_ACCOUNT", "")
        if raw_json:
            try:
                _service_account_info = json.loads(raw_json)
                _source = "env_var"
            except json.JSONDecodeError as e:
                print(f"[firebase_config] FIREBASE_SERVICE_ACCOUNT env var JSON error: {e}")

    # ── SOURCE 3: Local service account key file ─────────────────────────
    if not _service_account_info and cred_path and os.path.exists(cred_path):
        with open(cred_path) as f:
            _service_account_info = json.load(f)
        _source = "local_file"

    # ── INIT ─────────────────────────────────────────────────────────────
    if _service_account_info:
        try:
            cred = credentials.Certificate(_service_account_info)
            firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})
            print(f"[firebase_config] ✅ Firebase initialized from {_source}")
        except Exception as e:
            print(f"[firebase_config] ❌ Firebase init failed ({_source}): {e}")
    else:
        print(
            f"[firebase_config] ⚠️ No Firebase credentials found. "
            f"Checked: st.secrets, FIREBASE_SERVICE_ACCOUNT env var, {cred_path}"
        )

# ── Export shared clients ─────────────────────────────────────────────────────
try:
    db = firestore.client()
    bucket = storage.bucket()
    print("[firebase_config] ✅ Firestore client ready")
except Exception as e:
    print(f"[firebase_config] ❌ Firestore client failed: {e}")
    db = None
    bucket = None
