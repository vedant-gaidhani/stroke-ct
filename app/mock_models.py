import random
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import cv2

# --- FAKE CLASSIFICATION MODEL ---
def predict_classification(pil_image):
    """
    Simulates a classification model.
    Randomly returns either ('Stroke', 0.91) or ('Normal', 0.97)
    so we can test both UI paths during development.
    """
    if random.choice([True, False]):
        return "Stroke", 0.91
    else:
        return "Normal", 0.97

# --- FAKE SEGMENTATION MODEL ---
def predict_segmentation(pil_image):
    """
    Simulates a segmentation model.
    Returns a numpy array of shape (224, 224) with a small white blob
    simulating a hemorrhage mask.
    """
    # Create empty black mask
    mask = np.zeros((224, 224), dtype=np.uint8)
    
    # Draw a simulated hemorrhage blob (white ellipse)
    # Center (x, y), axes (width, height), angle, start_angle, end_angle, color, thickness
    cv2.ellipse(mask, (130, 90), (15, 25), 45, 0, 360, 255, -1)
    
    # Add some noise to make it look slightly realistic
    noise = np.random.randint(0, 2, (224, 224), dtype=np.uint8)
    mask[mask > 0] = np.clip(mask[mask > 0] + noise[mask > 0] * 50, 0, 255)
    
    return mask

# --- FAKE GRAD-CAM ---
def generate_gradcam(pil_image):
    """
    Simulates a Grad-CAM model output.
    Returns a numpy array of shape (224, 224) with a gaussian blur blob
    simulating a heatmap of important regions.
    """
    heatmap = np.zeros((224, 224), dtype=np.float32)
    
    # Draw a bright spot at the same location as the segmentation blob
    cv2.circle(heatmap, (130, 90), 30, 1.0, -1)
    
    # Apply heavy gaussian blur to simulate Grad-CAM interpolation
    heatmap = cv2.GaussianBlur(heatmap, (51, 51), 0)
    
    # Normalize back to 0-1 range
    if np.max(heatmap) > 0:
        heatmap = heatmap / np.max(heatmap)
        
    return heatmap

# --- 4-PANEL FIGURE VISUALIZATION ---
def create_four_panel_figure(original_pil, mask_array, heatmap_array):
    """
    Uses matplotlib to create a figure with 4 subplots side-by-side:
    1. Original CT (grayscale)
    2. CT + segmentation mask overlay (red, alpha 0.4)
    3. CT + Grad-CAM heatmap overlay (jet colormap, alpha 0.5)
    4. CT + both overlays combined
    """
    # Ensure original image is exactly 224x224 to align with arrays
    orig_resized = original_pil.resize((224, 224))
    orig_np = np.array(orig_resized)
    
    # Create red colormap for segmentation (transparent to red)
    colors = [(0, 0, 0, 0), (1, 0, 0, 1)] # transparent to solid red
    red_cmap = LinearSegmentedColormap.from_list("red_overlay", colors)
    
    # Create figure with dark background matching the Streamlit theme
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    fig.patch.set_facecolor('#0A0F1E')
    
    for ax in axes:
        ax.axis('off') # Hide axes
        
    # Title styling function
    def add_title(ax, text):
        ax.set_title(text, color='#1D9E75', fontsize=12, pad=10, fontweight='bold')

    # Panel 1: Original
    add_title(axes[0], "Original CT")
    axes[0].imshow(orig_np, cmap='gray')
    
    # Panel 2: Segmentation Overlay
    add_title(axes[1], "Segmentation Mask")
    axes[1].imshow(orig_np, cmap='gray')
    # Use masked array to only show the segmented blob
    mask_normalized = mask_array / 255.0
    axes[1].imshow(mask_normalized, cmap=red_cmap, alpha=0.4)
    
    # Panel 3: Grad-CAM Overlay
    add_title(axes[2], "Grad-CAM Heatmap")
    axes[2].imshow(orig_np, cmap='gray')
    axes[2].imshow(heatmap_array, cmap='jet', alpha=0.5)
    
    # Panel 4: Combined Overlay
    add_title(axes[3], "Combined Analysis")
    axes[3].imshow(orig_np, cmap='gray')
    axes[3].imshow(heatmap_array, cmap='jet', alpha=0.3)
    axes[3].imshow(mask_normalized, cmap=red_cmap, alpha=0.5)
    
    # Tight layout with small padding
    plt.tight_layout(pad=1.0)
    
    return fig
