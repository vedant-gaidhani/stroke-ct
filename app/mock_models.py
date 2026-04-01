import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# --- FAKE CLASSIFICATION MODEL ---
def predict_classification(pil_image):
    """
    Simulates a two-class classification model.
    Returns: ('Ischemic Stroke', conf) or ('Normal', conf)
    """
    if random.choice([True, False]):
        return "Ischemic Stroke", round(random.uniform(0.76, 0.97), 4)
    else:
        return "Normal", round(random.uniform(0.82, 0.98), 4)

# --- FAKE SEGMENTATION MODEL ---
def predict_segmentation(pil_image):
    """
    Simulates a segmentation model.
    Returns a numpy array (224, 224) uint8 — stroke lesion region mask.
    Returns None occasionally to test empty-mask fallback.
    """
    # 20% chance of empty mask to test graceful fallback
    if random.random() < 0.2:
        return None

    mask = np.zeros((224, 224), dtype=np.uint8)
    img_pil = Image.fromarray(mask)
    draw = ImageDraw.Draw(img_pil)
    draw.ellipse([110, 60, 155, 125], fill=255)
    return np.array(img_pil)

# --- FAKE GRAD-CAM ---
def generate_gradcam(pil_image):
    """
    Simulates a Grad-CAM model attention map.
    Returns a numpy array (224, 224) float32 normalised to [0, 1].
    """
    heatmap = np.zeros((224, 224), dtype=np.float32)
    cx, cy, r = 130, 90, 30
    y_idx, x_idx = np.ogrid[:224, :224]
    dist = np.sqrt((x_idx - cx) ** 2 + (y_idx - cy) ** 2)
    heatmap[dist <= r] = 1.0

    img_pil = Image.fromarray((heatmap * 255).astype(np.uint8))
    blurred = img_pil.filter(ImageFilter.GaussianBlur(radius=20))
    heatmap = np.array(blurred).astype(np.float32) / 255.0

    if np.max(heatmap) > 0:
        heatmap = heatmap / np.max(heatmap)

    return heatmap

# --- 4-PANEL FIGURE VISUALIZATION ---
def create_four_panel_figure(original_pil, mask_array, heatmap_array):
    """
    Creates a 4-panel matplotlib figure for clinical output.

    Panels (in order):
      1. Original CT
      2. Lesion Overlay  (segmentation — shown only if mask is not None/empty)
      3. Model Attention Map  (Grad-CAM — labeled as explanation, not segmentation)
      4. Combined View

    Args:
        original_pil: PIL image (original CT)
        mask_array:   numpy uint8 (224,224) or None if no lesion detected
        heatmap_array: numpy float32 (224,224) normalised Grad-CAM
    """
    orig_resized = original_pil.resize((224, 224))
    orig_np = np.array(orig_resized)

    # Cyan overlay for stroke lesion (clinically neutral, avoids alarm-red on ischemic)
    cyan_colors = [(0, 0, 0, 0), (0, 0.85, 1.0, 1)]
    lesion_cmap = LinearSegmentedColormap.from_list("lesion_overlay", cyan_colors)

    has_mask = (mask_array is not None) and (np.any(mask_array > 0))
    mask_norm = (mask_array.astype(np.float32) / 255.0) if has_mask else np.zeros((224, 224), np.float32)

    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    fig.patch.set_facecolor('#0A0F1E')

    for ax in axes:
        ax.axis('off')

    def panel_title(ax, text):
        ax.set_title(text, color='#8FA3BF', fontsize=11, pad=8, fontweight='600',
                     fontfamily='monospace')

    # Panel 1 — Original CT
    panel_title(axes[0], "Original CT")
    axes[0].imshow(orig_np, cmap='gray')

    # Panel 2 — Lesion Overlay
    panel_title(axes[1], "Lesion Overlay")
    axes[1].imshow(orig_np, cmap='gray')
    if has_mask:
        axes[1].imshow(mask_norm, cmap=lesion_cmap, alpha=0.45)
    else:
        axes[1].text(0.5, 0.5, "No lesion\nregion detected",
                     transform=axes[1].transAxes, ha='center', va='center',
                     color='#8FA3BF', fontsize=10, alpha=0.7)

    # Panel 3 -- Model Attention Map (Grad-CAM explanation)
    panel_title(axes[2], "Model Attention Map")
    axes[2].imshow(orig_np, cmap='gray')
    if heatmap_array is not None:
        axes[2].imshow(heatmap_array, cmap='hot', alpha=0.5)
    else:
        axes[2].text(0.5, 0.5, "Grad-CAM\nnot available",
                     transform=axes[2].transAxes, ha='center', va='center',
                     color='#8FA3BF', fontsize=10, alpha=0.7)

    # Panel 4 -- Combined View
    panel_title(axes[3], "Combined View")
    axes[3].imshow(orig_np, cmap='gray')
    if heatmap_array is not None:
        axes[3].imshow(heatmap_array, cmap='hot', alpha=0.25)
    if has_mask:
        axes[3].imshow(mask_norm, cmap=lesion_cmap, alpha=0.45)

    plt.tight_layout(pad=1.2)
    return fig
