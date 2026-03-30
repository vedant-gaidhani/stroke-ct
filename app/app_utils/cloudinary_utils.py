import os
import io
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv(override=True)

# --- Configure Cloudinary from .env ---
cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip(),
    api_key    = os.getenv("CLOUDINARY_API_KEY", "").strip(),
    api_secret = os.getenv("CLOUDINARY_API_SECRET", "").strip(),
    secure     = True,
)

import tempfile

def upload_to_cloudinary(file_bytes: bytes, filename: str, folder: str = "neurotriage", resource_type: str = "image") -> str:
    """
    Uploads bytes to Cloudinary using a temporary file to preserve metadata.
    """
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
