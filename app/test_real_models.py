import os
import sys
from PIL import Image
import numpy as np

os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

import streamlit as st

# We mock st.cache_resource minimally if running out of streamlit context
# but streamlit actually allows running cached functions directly if not in app
from real_models import predict_classification, predict_segmentation, USING_REAL_MODELS

def main():
    print(f"USING_REAL_MODELS is {USING_REAL_MODELS}")
    if not USING_REAL_MODELS:
        print("FAIL: Fallback to mock models occurred. Check model loading.")
        sys.exit(1)
        
    print("Testing Classification...")
    img = Image.fromarray(np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8))
    label, conf = predict_classification(img)
    print(f"Classification Result: {label} ({conf:.4f})")
    
    print("Testing Segmentation...")
    mask = predict_segmentation(img)
    print(f"Segmentation Mask Shape: {mask.shape}, Range: {mask.min()} - {mask.max()}")
    
    if mask.shape != (384, 384):
        print("FAIL: Expected mask shape (384, 384)")
        sys.exit(1)
        
    print("SUCCESS: Both models loaded and successfully ran a forward pass.")

if __name__ == "__main__":
    main()
