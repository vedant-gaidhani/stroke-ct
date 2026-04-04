import os
import torch
from torchvision import transforms
from PIL import Image
import numpy as np
import streamlit as st
import timm
import segmentation_models_pytorch as smp
import mock_models

# ── GLOBALS ───────────────────────────────────────────────────────────────
USING_REAL_MODELS = True

# ── Final operating configuration (fused segmentation) ─────────────────────
SEG_COARSE_WEIGHT = 0.5
SEG_REFINE_WEIGHT = 0.5
SEG_THRESHOLD     = 0.45
SEG_MIN_AREA      = 0        # filter handled by keep_largest
SEG_KEEP_LARGEST  = True
# ────────────────────────────────────────────────────────────────────────────

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

CLASSIFIER_PATH = os.path.join(MODELS_DIR, "classifier_dual_view_best.pth")

# Fusion Models (ResNet34)
COARSE_PATH = os.path.join(MODELS_DIR, "segmentor_best_resnet34_tversky_384.pth")
REFINE_PATH = os.path.join(MODELS_DIR, "segmentor_best_roi_refine_resnet34_tversky_384.pth")

# ── LOAD MODELS ───────────────────────────────────────────────────────────

def load_classifier():
    global USING_REAL_MODELS
    try:
        if not os.path.exists(CLASSIFIER_PATH):
            raise FileNotFoundError(f"{CLASSIFIER_PATH} not found.")
        model = timm.create_model('efficientnet_b0', pretrained=False, num_classes=2)
        model.load_state_dict(torch.load(CLASSIFIER_PATH, map_location='cpu'))
        model.eval()
        return model
    except Exception as e:
        print(f"[AI] Classifier load failed: {e}")
        USING_REAL_MODELS = False
        return None

def load_segmenter(path, name="Segmenter"):
    global USING_REAL_MODELS
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"{path} not found.")
        # Switch to resnet34 for final best handoff
        model = smp.Unet(encoder_name='resnet34', in_channels=1, classes=1)
        model.load_state_dict(torch.load(path, map_location='cpu'))
        model.eval()
        print(f"[AI] ✅ {name} loaded successfully (ResNet34)")
        return model
    except Exception as e:
        print(f"[AI] {name} load failed: {e}")
        USING_REAL_MODELS = False
        return None

classifier_model = load_classifier()
coarse_model = load_segmenter(COARSE_PATH, "Coarse Segmenter")
refine_model = load_segmenter(REFINE_PATH, "Refinement Segmenter")

# Legacy/Mock support
segmenter_model = coarse_model 

# Alias so callers (2_New_Scan, 4_Batch_Upload) can use the old name without throwing an ImportError
def load_unet():
    return coarse_model

# ── TRANSFORMS ────────────────────────────────────────────────────────────

clf_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

seg_transform = transforms.Compose([
    transforms.Resize((384, 384)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

# ── INFERENCE FUNCTIONS ───────────────────────────────────────────────────

def predict_classification(pil_image):
    if not USING_REAL_MODELS or classifier_model is None:
        return mock_models.predict_classification(pil_image)
    
    img_rgb = pil_image.convert("RGB")
    tensor = clf_transform(img_rgb).unsqueeze(0)
    
    with torch.no_grad():
        outputs = classifier_model(tensor)
        probs = torch.softmax(outputs, dim=1)[0].numpy()
        
    class_names = ["Normal", "Ischemic Stroke"]
    pred_idx = int(probs.argmax())
    return class_names[pred_idx], float(probs[pred_idx])

def generate_gradcam(pil_image, filename=None, mask_array=None):
    """
    Returns a precomputed Model Attention Map if it exists for the given filename.
    Fallback: Uses lesion mask to create a synthetic heatmap if no precomputed map is found.
    """
    return mock_models.generate_gradcam(pil_image, filename=filename, mask_array=mask_array)

def clean_mask(binary_mask, min_area=80, keep_largest=True):
    from scipy.ndimage import label
    structure = np.ones((3, 3), dtype=int)
    labeled_array, num_features = label(binary_mask, structure=structure)
    
    cleaned = np.zeros_like(binary_mask)
    if num_features == 0:
        return binary_mask
        
    components = []
    for label_idx in range(1, num_features + 1):
        area = np.sum(labeled_array == label_idx)
        components.append((label_idx, area))
        
    if keep_largest:
        label_idx, area = max(components, key=lambda x: x[1])
        if area >= min_area:
            cleaned[labeled_array == label_idx] = 1.0
    else:
        for label_idx, area in components:
            if area >= min_area:
                cleaned[labeled_array == label_idx] = 1.0
                
    return cleaned.astype(np.float32)

def predict_segmentation(pil_image):
    """
    Runs the DUAL-MODEL FUSION (ResNet34 Coarse + Refine)
    Weighted sum: 0.5 * Coarse + 0.5 * Refine
    """
    if not USING_REAL_MODELS or coarse_model is None or refine_model is None:
        return mock_models.predict_segmentation(pil_image)
    
    img_gray = pil_image.convert("L")
    original_np = np.array(img_gray)
    orig_h, orig_w = original_np.shape

    tensor = seg_transform(img_gray).unsqueeze(0)
    
    with torch.no_grad():
        # Forward pass 1: Coarse
        logits_coarse = coarse_model(tensor)
        # Forward pass 2: Refine
        logits_refine = refine_model(tensor)
        
        # FUSED LOGITS / PROBS
        # Final best setup uses mean fusion
        fused_logits = (SEG_COARSE_WEIGHT * logits_coarse) + (SEG_REFINE_WEIGHT * logits_refine)
        prob = torch.sigmoid(fused_logits).squeeze().numpy()
        
    # Apply Threshold and cleanup
    pred_mask = (prob > SEG_THRESHOLD).astype(np.float32)
    cleaned_mask = clean_mask(pred_mask, min_area=SEG_MIN_AREA, keep_largest=SEG_KEEP_LARGEST)

    if not np.any(cleaned_mask > 0):
        return None

    # Rescale to original CT dimensions
    mask_pil = Image.fromarray((cleaned_mask * 255).astype(np.uint8))
    mask_pil_resized = mask_pil.resize((orig_w, orig_h), resample=Image.Resampling.NEAREST)
    cleaned_mask_resized = (np.array(mask_pil_resized) > 0).astype(np.float32)
    return (cleaned_mask_resized * 255).astype(np.uint8)

def create_four_panel_figure(original_pil, mask_array, heatmap_array):
    return mock_models.create_four_panel_figure(original_pil, mask_array, heatmap_array)
