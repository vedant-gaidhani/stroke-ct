import streamlit as st
import os
import io
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv(override=True)

def _get_secret(key: str) -> str:
    """Read from st.secrets first (Streamlit Cloud), then fall back to env vars (local)."""
    try:
        return st.secrets.get(key, os.getenv(key, "")).strip()
    except Exception:
        return os.getenv(key, "").strip()

# --- Configure Cloudinary (works on Streamlit Cloud & local) ---
cloudinary.config(
    cloud_name = _get_secret("CLOUDINARY_CLOUD_NAME"),
    api_key    = _get_secret("CLOUDINARY_API_KEY"),
    api_secret = _get_secret("CLOUDINARY_API_SECRET"),
    secure     = True,
)

import tempfile

def upload_to_cloudinary(file_bytes: bytes, filename: str, folder: str = "neurotriage", resource_type: str = "auto") -> str:
    """
    Uploads bytes to Cloudinary using a temporary file to preserve metadata.
    """
    # By default, use "image" for PDFs too so Cloudinary serves them correctly 
    # to the browser with application/pdf content type (avoiding 401s on raw files)
    if resource_type == "auto" and filename.lower().endswith(".pdf"):
        resource_type = "image"
    try:
        # 1. Create a temporary file to store the bytes
        ext = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            # 2. Upload the temporary file
            # By using resource_type="image" even for PDFs, Cloudinary
            # correctly sets the Content-Type to application/pdf so browsers
            # will display it inline rather than forcing a download of a raw file.
            p_id = os.path.splitext(filename)[0]

            result = cloudinary.uploader.upload(
                tmp_path,
                public_id=p_id,
                folder=folder,
                resource_type=resource_type,
                overwrite=True
            )
            return result.get("secure_url", "")
        finally:
            # 3. Clean up the temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        raise Exception(f"[Cloudinary] {str(e)}")
