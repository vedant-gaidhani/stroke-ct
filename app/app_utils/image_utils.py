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
        ds = pydicom.dcmread(uploaded_file)
        pixel_array = ds.pixel_array
        
        pixel_array = np.squeeze(pixel_array)
        if len(pixel_array.shape) == 3 and pixel_array.shape[-1] not in [3, 4]:
            pixel_array = pixel_array[pixel_array.shape[0] // 2]
        elif len(pixel_array.shape) < 2:
            raise ValueError(f"Invalid DICOM formatting. Unexpected shape: {ds.pixel_array.shape}")

        pixel_array = pixel_array.astype(float)
        max_val = pixel_array.max()
        if max_val == 0:
            max_val = 1
            
        rescaled_image = (np.maximum(pixel_array, 0) / max_val) * 255.0
        final_image = np.uint8(rescaled_image)
        
        pil_img = Image.fromarray(final_image)
        return pil_img.convert("RGB")
    else:
        pil_img = Image.open(uploaded_file)
        return pil_img.convert("RGB")

def load_study_volume(uploaded_file):
    """
    Returns a list of PIL images representing the volume.
    For standard images or 2D DICOMs, returns a single-item list.
    For 3D DICOMs, returns a list of all slices.
    """
    filename = uploaded_file.name.lower()
    
    if filename.endswith(".dcm"):
        uploaded_file.seek(0)
        ds = pydicom.dcmread(uploaded_file)
        pixel_array = ds.pixel_array
        
        pixel_array = np.squeeze(pixel_array)
        
        # Determine if it's a 3D volume
        if len(pixel_array.shape) == 3 and pixel_array.shape[-1] not in [3, 4]:
            slices = []
            for i in range(pixel_array.shape[0]):
                slice_arr = pixel_array[i].astype(float)
                max_val = slice_arr.max()
                if max_val == 0: max_val = 1
                rescaled_image = (np.maximum(slice_arr, 0) / max_val) * 255.0
                final_image = np.uint8(rescaled_image)
                pil_img = Image.fromarray(final_image).convert("RGB")
                slices.append(pil_img)
            return slices
        elif len(pixel_array.shape) < 2:
            raise ValueError(f"Invalid DICOM formatting. Unexpected shape: {ds.pixel_array.shape}")
        else:
            # 2D DICOM
            slice_arr = pixel_array.astype(float)
            max_val = slice_arr.max()
            if max_val == 0: max_val = 1
            rescaled_image = (np.maximum(slice_arr, 0) / max_val) * 255.0
            final_image = np.uint8(rescaled_image)
            pil_img = Image.fromarray(final_image).convert("RGB")
            return [pil_img]
    else:
        uploaded_file.seek(0)
        pil_img = Image.open(uploaded_file)
        return [pil_img.convert("RGB")]

def preprocess_for_model(pil_image):
    """
    Resizes image to 224x224 and ensures it is in RGB format.
    """
    return pil_image.resize((224, 224)).convert("RGB")

def get_triage(label, confidence):
    """
    Returns triage recommendation based on classification and confidence.
    
    Labels used:
      - "Ischemic Stroke" (positive prediction)
      - "Normal" (negative prediction)
    
    Returns: (display_text, severity_level, hex_color)
    """
    if label == "Normal":
        return ("Low Priority Review", "normal", "#1D9E75")         # teal
    elif confidence < 0.75:
        return ("Needs Review", "warning", "#EF9F27")               # amber
    else:
        return ("Urgent Review", "critical", "#E24B4A")             # red

def pil_to_bytes(pil_image):
    """
    Converts a PIL image to a bytes object for storage/uploading.
    """
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# Threshold above which we display ">99.5%" instead of the raw value.
# This prevents "100.00%" appearing from floating-point rounding.
_CONF_CAP = 0.995

def format_confidence(prob: float) -> str:
    """
    Format a raw model probability (0.0‒1.0) for clinical display.

    Rules (per integration brief):
      - Confidence is model certainty, NOT model accuracy.
      - Never show 100% unless the raw value is literally 1.0
        (and even then we cap at ">99.5%").
      - Always 2 decimal places.
      - If prob >= 0.995  → ">99.5%"
      - Otherwise         → "XX.XX%"

    Args:
        prob: raw float in [0, 1] from the classifier softmax output.

    Returns:
        A display string, e.g. "94.27%" or ">99.5%".
    """
    if prob >= _CONF_CAP:
        return ">99.5%"
    return f"{prob * 100:.2f}%"
