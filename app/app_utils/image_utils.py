# image preprocessing, DICOM support
import pydicom
import numpy as np
from PIL import Image
import io

def load_image(uploaded_file):
    """
    Accepts a Streamlit UploadedFile object.
    Supports .dcm (DICOM) and standard image formats (PNG, JPG, etc.).
    """
    filename = uploaded_file.name.lower()
    
    if filename.endswith(".dcm"):
        # Handle DICOM image
        ds = pydicom.dcmread(uploaded_file)
        pixel_array = ds.pixel_array
        
        # Handle invalid shapes (e.g., 3D volume or weird 1D lines)
        pixel_array = np.squeeze(pixel_array)
        if len(pixel_array.shape) == 3 and pixel_array.shape[-1] not in [3, 4]:
            # If it's a 3D volume (e.g. multi-slice CT), take the middle slice
            pixel_array = pixel_array[pixel_array.shape[0] // 2]
        elif len(pixel_array.shape) < 2:
            raise ValueError(f"Invalid DICOM formatting. Unexpected shape: {ds.pixel_array.shape}")

        # Normalize pixel values to 0-255 range
        pixel_array = pixel_array.astype(float)
        # Avoid division by zero if image is completely black
        max_val = pixel_array.max()
        if max_val == 0:
            max_val = 1
            
        rescaled_image = (np.maximum(pixel_array, 0) / max_val) * 255.0
        final_image = np.uint8(rescaled_image)
        
        # Convert to a PIL Image and ensure it is RGB
        pil_img = Image.fromarray(final_image)
        return pil_img.convert("RGB")
    else:
        # Handle regular image formats using PIL
        pil_img = Image.open(uploaded_file)
        return pil_img.convert("RGB")

def preprocess_for_model(pil_image):
    """
    Resizes image to 224x224 and ensures it is in RGB format.
    """
    # Simply resize to target size for inference
    return pil_image.resize((224, 224)).convert("RGB")

def get_triage(label, confidence):
    """
    Returns triage status based on model classification and confidence.
    Returns: (display_text, severity_level, hex_color)
    """
    if label == "Normal":
        return ("NORMAL - No Acute Findings", "normal", "#1D9E75") # Teal
    elif confidence < 0.75:
        return ("LOW CONFIDENCE - Radiologist Review Recommended", "warning", "#EF9F27") # Orange
    else:
        return ("STROKE DETECTED - Urgent Intervention Required", "critical", "#E24B4A") # Red

def pil_to_bytes(pil_image):
    """
    Converts a PIL image to a bytes object for storage/uploading.
    """
    img_byte_arr = io.BytesIO()
    # Save as PNG by default
    pil_image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
