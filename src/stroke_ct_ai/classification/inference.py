from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import timm
import torch
from PIL import Image
from torchvision import transforms


ClassificationLabel = Literal["Normal", "Stroke"]

DEFAULT_IMAGE_SIZE = 224
CHECKPOINT_ENV_VAR = "STROKE_CT_CLASSIFICATION_CHECKPOINT"
CLASS_NAMES: list[ClassificationLabel] = ["Normal", "Stroke"]


@dataclass
class ClassificationResult:
    label: ClassificationLabel
    confidence: float
    normal_probability: float
    stroke_probability: float


def _resolve_checkpoint_path(model_path: str | os.PathLike[str] | None = None) -> str:
    if model_path is not None:
        return str(model_path)

    env_path = os.getenv(CHECKPOINT_ENV_VAR)
    if env_path:
        return env_path

    raise ValueError(
        f"No classification checkpoint path provided. Set `{CHECKPOINT_ENV_VAR}` "
        "or pass `model_path` explicitly."
    )


def _resolve_device(device: str | None = None) -> str:
    if device is not None:
        return device
    return "cuda" if torch.cuda.is_available() else "cpu"


@lru_cache(maxsize=2)
def _load_cached_model(model_path: str, device: str):
    model = timm.create_model("efficientnet_b0", pretrained=False, num_classes=2)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()
    return model


def load_classification_model(
    model_path: str | os.PathLike[str] | None = None,
    device: str | None = None,
):
    resolved_path = _resolve_checkpoint_path(model_path)
    resolved_device = _resolve_device(device)
    return _load_cached_model(resolved_path, resolved_device), resolved_device


def _build_transform(image_size: int = DEFAULT_IMAGE_SIZE):
    return transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )


def preprocess_classification_image(
    image: str | os.PathLike[str] | Image.Image,
    image_size: int = DEFAULT_IMAGE_SIZE,
):
    if isinstance(image, (str, os.PathLike)):
        pil_image = Image.open(image).convert("RGB")
    else:
        pil_image = image.convert("RGB")

    transform = _build_transform(image_size=image_size)
    tensor = transform(pil_image).unsqueeze(0)
    return pil_image, tensor


def predict_classification(
    image_path: str | os.PathLike[str] | Image.Image,
    model=None,
    device: str | None = None,
    image_size: int = DEFAULT_IMAGE_SIZE,
) -> ClassificationResult:
    resolved_device = _resolve_device(device)
    if model is None:
        model, resolved_device = load_classification_model(device=resolved_device)

    _, tensor = preprocess_classification_image(image_path, image_size=image_size)
    tensor = tensor.to(resolved_device)

    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)[0].cpu().numpy()

    pred_idx = int(probs.argmax())
    label = CLASS_NAMES[pred_idx]

    return ClassificationResult(
        label=label,
        confidence=float(probs[pred_idx]),
        normal_probability=float(probs[0]),
        stroke_probability=float(probs[1]),
    )
