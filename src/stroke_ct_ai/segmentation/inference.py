from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
import segmentation_models_pytorch as smp
import torch
from torchvision import transforms


DEFAULT_IMAGE_SIZE = 384
DEFAULT_THRESHOLD = 0.45
DEFAULT_MIN_AREA = 80
DEFAULT_OVERLAY_ALPHA = 0.35
CHECKPOINT_ENV_VAR = "STROKE_CT_SEGMENTATION_CHECKPOINT"


@dataclass
class SegmentationResult:
    mask: np.ndarray
    overlay: np.ndarray


def _resolve_checkpoint_path(model_path: str | os.PathLike[str] | None = None) -> str:
    if model_path is not None:
        return str(model_path)

    env_path = os.getenv(CHECKPOINT_ENV_VAR)
    if env_path:
        return env_path

    raise ValueError(
        f"No segmentation checkpoint path provided. Set `{CHECKPOINT_ENV_VAR}` "
        "or pass `model_path` explicitly."
    )


def _resolve_device(device: str | None = None) -> str:
    if device is not None:
        return device
    return "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=2)
def _load_cached_model(model_path: str, device: str):
    model = smp.Unet(
        encoder_name="resnet18",
        encoder_weights=None,
        in_channels=1,
        classes=1,
    ).to(device)

    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    return model


def load_segmentation_model(
    model_path: str | os.PathLike[str] | None = None,
    device: str | None = None,
):
    resolved_path = _resolve_checkpoint_path(model_path)
    resolved_device = _resolve_device(device)
    return _load_cached_model(resolved_path, resolved_device), resolved_device


def preprocess_ct_image(
    image_path: str | os.PathLike[str],
    image_size: int = DEFAULT_IMAGE_SIZE,
):
    image = Image.open(image_path).convert("L")

    original_np = np.array(image)
    original_h, original_w = original_np.shape

    transform = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5]),
        ]
    )

    tensor = transform(image).unsqueeze(0)
    return tensor, original_np, (original_h, original_w)


def clean_mask(
    binary_mask: np.ndarray,
    min_area: int = DEFAULT_MIN_AREA,
    keep_largest: bool = True,
):
    mask_uint8 = (binary_mask.astype(np.uint8) * 255)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        mask_uint8, connectivity=8
    )
    cleaned = np.zeros_like(mask_uint8)

    if num_labels <= 1:
        return binary_mask

    components = []
    for label_idx in range(1, num_labels):
        area = stats[label_idx, cv2.CC_STAT_AREA]
        components.append((label_idx, area))

    if keep_largest:
        label_idx, area = max(components, key=lambda item: item[1])
        if area >= min_area:
            cleaned[labels == label_idx] = 255
    else:
        for label_idx, area in components:
            if area >= min_area:
                cleaned[labels == label_idx] = 255

    return (cleaned > 0).astype(np.float32)


def create_overlay(
    image_np: np.ndarray,
    mask_np: np.ndarray,
    alpha: float = DEFAULT_OVERLAY_ALPHA,
):
    image_rgb = np.stack([image_np] * 3, axis=-1).astype(np.float32)
    if image_rgb.max() > 0:
        image_rgb = image_rgb / image_rgb.max()

    overlay = image_rgb.copy()
    red = np.zeros_like(image_rgb)
    red[..., 0] = 1.0

    mask_3d = np.expand_dims(mask_np, axis=-1)
    overlay = np.where(mask_3d > 0, (1 - alpha) * overlay + alpha * red, overlay)

    return np.clip(overlay, 0, 1)


def predict_segmentation(
    image_path: str | os.PathLike[str],
    model=None,
    device: str | None = None,
    image_size: int = DEFAULT_IMAGE_SIZE,
    threshold: float = DEFAULT_THRESHOLD,
    min_area: int = DEFAULT_MIN_AREA,
) -> SegmentationResult:
    resolved_device = _resolve_device(device)
    if model is None:
        model, resolved_device = load_segmentation_model(device=resolved_device)

    input_tensor, original_np, (orig_h, orig_w) = preprocess_ct_image(
        image_path, image_size=image_size
    )
    input_tensor = input_tensor.to(resolved_device)

    with torch.no_grad():
        logits = model(input_tensor)
        prob = torch.sigmoid(logits).squeeze().cpu().numpy()

    pred_mask = (prob > threshold).astype(np.float32)
    cleaned_mask = clean_mask(pred_mask, min_area=min_area, keep_largest=True)

    cleaned_mask_resized = cv2.resize(
        cleaned_mask,
        (orig_w, orig_h),
        interpolation=cv2.INTER_NEAREST,
    )

    overlay = create_overlay(original_np, cleaned_mask_resized)

    return SegmentationResult(mask=cleaned_mask_resized, overlay=overlay)


def save_segmentation_outputs(
    result: SegmentationResult,
    output_dir: str | os.PathLike[str],
    stem: str = "prediction",
):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    mask_path = output_path / f"{stem}_mask.png"
    overlay_path = output_path / f"{stem}_overlay.png"

    Image.fromarray((result.mask * 255).astype(np.uint8)).save(mask_path)
    Image.fromarray((result.overlay * 255).astype(np.uint8)).save(overlay_path)

    return mask_path, overlay_path
