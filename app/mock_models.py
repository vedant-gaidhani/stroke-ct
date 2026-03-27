import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

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
    Simulates a segmentation model using pure numpy/PIL.
    Returns a numpy array of shape (224, 224) with a small white blob.
    """
    mask = np.zeros((224, 224), dtype=np.uint8)
    
    # Draw an ellipse using PIL
    img_pil = Image.fromarray(mask)
    draw = ImageDraw.Draw(img_pil)
    # Ellipse bounding box (x0, y0, x1, y1)
    draw.ellipse([110, 60, 155, 125], fill=255)
    
    return np.array(img_pil)

# --- FAKE GRAD-CAM ---
def generate_gradcam(pil_image):
    """
    Simulates a Grad-CAM output using pure numpy.
    Returns a numpy array of shape (224, 224) with a gaussian blob.
    """
    heatmap = np.zeros((224, 224), dtype=np.float32)

    # Draw a filled circle using coordinate math
    cx, cy, r = 130, 90, 30
    y_idx, x_idx = np.ogrid[:224, :224]
    dist = np.sqrt((x_idx - cx) ** 2 + (y_idx - cy) ** 2)
    heatmap[dist <= r] = 1.0

    # Apply a simple box blur to simulate gaussian blur
    img_pil = Image.fromarray((heatmap * 255).astype(np.uint8))
    blurred = img_pil.filter(ImageFilter.GaussianBlur(radius=20))
    heatmap = np.array(blurred).astype(np.float32) / 255.0

    if np.max(heatmap) > 0:
        heatmap = heatmap / np.max(heatmap)

    return heatmap

# --- 4-PANEL FIGURE VISUALIZATION ---
def create_four_panel_figure(original_pil, mask_array, heatmap_array):
    """
    Uses matplotlib to create a figure with 4 subplots side-by-side.
    """
    orig_resized = original_pil.resize((224, 224))
    orig_np = np.array(orig_resized)

    colors = [(0, 0, 0, 0), (1, 0, 0, 1)]
    red_cmap = LinearSegmentedColormap.from_list("red_overlay", colors)

    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    fig.patch.set_facecolor('#0A0F1E')

    for ax in axes:
        ax.axis('off')

    def add_title(ax, text):
        ax.set_title(text, color='#1D9E75', fontsize=12, pad=10, fontweight='bold')

    add_title(axes[0], "Original CT")
    axes[0].imshow(orig_np, cmap='gray')

    add_title(axes[1], "Segmentation Mask")
    axes[1].imshow(orig_np, cmap='gray')
    mask_normalized = mask_array / 255.0
    axes[1].imshow(mask_normalized, cmap=red_cmap, alpha=0.4)

    add_title(axes[2], "Grad-CAM Heatmap")
    axes[2].imshow(orig_np, cmap='gray')
    axes[2].imshow(heatmap_array, cmap='jet', alpha=0.5)

    add_title(axes[3], "Combined Analysis")
    axes[3].imshow(orig_np, cmap='gray')
    axes[3].imshow(heatmap_array, cmap='jet', alpha=0.3)
    axes[3].imshow(mask_normalized, cmap=red_cmap, alpha=0.5)

    plt.tight_layout(pad=1.0)

    return fig
