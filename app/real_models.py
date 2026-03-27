import os
import torch
from torchvision import transforms
from PIL import Image
import numpy as np
import streamlit as st
import timm
import segmentation_models_pytorch as smp
import mock_models

# Pass-through visualization functions
generate_gradcam = mock_models.generate_gradcam
create_four_panel_figure = mock_models.create_four_panel_figure

USING_REAL_MODELS = True

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
        
    class_names = ["Normal", "Stroke"]
    pred_idx = int(probs.argmax())
    return class_names[pred_idx], float(probs[pred_idx])

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
    if not USING_REAL_MODELS or segmenter_model is None:
        return mock_models.predict_segmentation(pil_image)
    
    img_gray = pil_image.convert("L")
    original_np = np.array(img_gray)
    orig_h, orig_w = original_np.shape

    tensor = seg_transform(img_gray).unsqueeze(0)
    
    with torch.no_grad():
        logits = segmenter_model(tensor)
        prob = torch.sigmoid(logits).squeeze().numpy()
        
    pred_mask = (prob > 0.45).astype(np.float32)
    cleaned_mask = clean_mask(pred_mask, min_area=80, keep_largest=True)

    # Convert to PIL Image for resizing instead of cv2
    from PIL import Image
    mask_pil = Image.fromarray((cleaned_mask * 255).astype(np.uint8))
    mask_pil_resized = mask_pil.resize((orig_w, orig_h), resample=Image.Resampling.NEAREST)
    cleaned_mask_resized = (np.array(mask_pil_resized) > 0).astype(np.float32)
        
    mask_uint8 = (cleaned_mask_resized * 255).astype(np.uint8)
    return mask_uint8
