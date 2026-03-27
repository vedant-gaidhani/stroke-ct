from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from stroke_ct_ai.classification.inference import (  # noqa: E402
    load_classification_model,
    predict_classification,
)


def main():
    parser = argparse.ArgumentParser(
        description="Run the frozen classification baseline locally."
    )
    parser.add_argument("--image", required=True, help="Path to a CT image")
    parser.add_argument(
        "--checkpoint",
        help="Path to the classification checkpoint. If omitted, uses STROKE_CT_CLASSIFICATION_CHECKPOINT.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "classification" / "outputs"),
        help="Directory for prediction artifacts.",
    )
    parser.add_argument("--image-size", type=int, default=224)
    args = parser.parse_args()

    model, device = load_classification_model(model_path=args.checkpoint)
    result = predict_classification(
        image_path=args.image,
        model=model,
        device=device,
        image_size=args.image_size,
    )

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(args.image).stem

    prediction_path = output_dir / f"{stem}_prediction.json"
    preview_path = output_dir / f"{stem}_preview.png"

    with prediction_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "label": result.label,
                "confidence": result.confidence,
                "normal_probability": result.normal_probability,
                "stroke_probability": result.stroke_probability,
            },
            f,
            indent=2,
        )

    image = Image.open(args.image).convert("RGB")
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.imshow(image)
    ax.set_title(
        f"Pred: {result.label}\n"
        f"Conf: {result.confidence:.3f}\n"
        f"Normal: {result.normal_probability:.3f} | Stroke: {result.stroke_probability:.3f}"
    )
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(preview_path)
    plt.close(fig)

    print("Classification completed.")
    print(f"Prediction JSON: {prediction_path}")
    print(f"Preview PNG    : {preview_path}")


if __name__ == "__main__":
    main()
