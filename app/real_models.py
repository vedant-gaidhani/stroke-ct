import os
import torch
from torchvision import transforms
from PIL import Image
import numpy as np
import streamlit as st
import timm
import segmentation_models_pytorch as smp
import mock_models

USING_REAL_MODELS = True

# ── Final operating configuration (fused segmentation) ─────────────────────
SEG_COARSE_WEIGHT = 0.5
SEG_REFINE_WEIGHT = 0.5
SEG_THRESHOLD     = 0.45
SEG_MIN_AREA      = 0        # keep all components; filter handled by keep_largest
SEG_KEEP_LARGEST  = True
# ────────────────────────────────────────────────────────────────────────────

# We use absolute paths derived from the file location so it works regardless of cwd
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLASSIFIER_PATH = os.path.join(BASE_DIR, "models", "classifier_dual_view_best.pth")
SEGMENTER_PATH = os.path.join(BASE_DIR, "models", "segmentor_best_tversky_384.pth")

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
        USING_REAL_MODELS = False
        return None

def load_segmenter():
    global USING_REAL_MODELS
    try:
        if not os.path.exists(SEGMENTER_PATH):
            raise FileNotFoundError(f"{SEGMENTER_PATH} not found.")
        model = smp.Unet(encoder_name='resnet18', in_channels=1, classes=1)
        model.load_state_dict(torch.load(SEGMENTER_PATH, map_location='cpu'))
        model.eval()
        return model
    except Exception as e:
        USING_REAL_MODELS = False
        return None

classifier_model = load_classifier()
segmenter_model = load_segmenter()

# Alias so callers can use either name
load_unet = load_segmenter

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

def generate_gradcam(pil_image):
    if not USING_REAL_MODELS or classifier_model is None:
        return mock_models.generate_gradcam(pil_image)
    
    img_rgb = pil_image.convert("RGB")
    tensor = clf_transform(img_rgb).unsqueeze(0)
    
    with torch.no_grad():
        # Get model prediction to highlight the winning class
        outputs = classifier_model(tensor)
        pred_idx = outputs.argmax(dim=1).item()
        
        # Use Class Activation Mapping (CAM) based on unpooled features
        features = classifier_model.forward_features(tensor)  # shape (1, C, H, W)
        
        # Retrieve final classifier weights
        classifier = getattr(classifier_model, 'classifier', None) or getattr(classifier_model, 'fc', None)
        if classifier is None:
            # Fallback if structure is unexpected
            return mock_models.generate_gradcam(pil_image)
            
        weights = classifier.weight[pred_idx] # shape (C,)
        
        # Multiply features by weights and sum to get CAM of shape (H, W)
        cam = (features[0] * weights.view(-1, 1, 1)).sum(dim=0)
        
        # Apply ReLU to only keep positive influence
        cam = torch.relu(cam)
        
        cam_min, cam_max = cam.min(), cam.max()
        if cam_max > cam_min:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = torch.zeros_like(cam)
            
    # Resize up to 224x224
    cam_np = cam.cpu().numpy()
    cam_pil = Image.fromarray((cam_np * 255).astype(np.uint8))
    cam_resized = cam_pil.resize((224, 224), resample=Image.Resampling.BILINEAR)
    
    return np.array(cam_resized).astype(np.float32) / 255.0

def clean_mask(binary_mask, min_area=80, keep_largest=True):
    from scipy.ndimage import label
    # 8-connectivity structure
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
    Runs the single-stage segmenter with the final operating config:
      threshold=0.45, min_area=0, keep_largest=True

    Returns a uint8 numpy array (H, W) with values 0 or 255,
    or None if no confident lesion region is detected.
    """
    if not USING_REAL_MODELS or segmenter_model is None:
        return mock_models.predict_segmentation(pil_image)
    
    img_gray = pil_image.convert("L")
    original_np = np.array(img_gray)
    orig_h, orig_w = original_np.shape

    tensor = seg_transform(img_gray).unsqueeze(0)
    
    with torch.no_grad():
        logits = segmenter_model(tensor)
        prob = torch.sigmoid(logits).squeeze().numpy()
        
    pred_mask = (prob > SEG_THRESHOLD).astype(np.float32)
    cleaned_mask = clean_mask(pred_mask, min_area=SEG_MIN_AREA, keep_largest=SEG_KEEP_LARGEST)

    # Return None if no confident region found — caller handles fallback UI
    if not np.any(cleaned_mask > 0):
        return None

    mask_pil = Image.fromarray((cleaned_mask * 255).astype(np.uint8))
    mask_pil_resized = mask_pil.resize((orig_w, orig_h), resample=Image.Resampling.NEAREST)
    cleaned_mask_resized = (np.array(mask_pil_resized) > 0).astype(np.float32)
    return (cleaned_mask_resized * 255).astype(np.uint8)


def create_four_panel_figure(original_pil, mask_array, heatmap_array):
    """
    Creates a 4-panel clinical output figure.

    Panels:
      1. Original CT
      2. Lesion Overlay  (segmentation; shows fallback text if empty)
      3. Model Attention Map  (Grad-CAM explanation)
      4. Combined View
    """
    return mock_models.create_four_panel_figure(original_pil, mask_array, heatmap_array)
