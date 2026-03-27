from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from stroke_ct_ai.segmentation.inference import (  # noqa: E402
    load_segmentation_model,
    predict_segmentation,
    save_segmentation_outputs,
)


def main():
    parser = argparse.ArgumentParser(
        description="Run the frozen 2D stroke CT segmentation baseline locally."
    )
    parser.add_argument("--image", required=True, help="Path to a CT image")
    parser.add_argument(
        "--checkpoint",
        help="Path to the segmentation checkpoint. If omitted, uses STROKE_CT_SEGMENTATION_CHECKPOINT.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(REPO_ROOT / "segmentation" / "outputs"),
        help="Directory for the predicted mask and overlay.",
    )
    parser.add_argument("--image-size", type=int, default=384)
    parser.add_argument("--threshold", type=float, default=0.45)
    parser.add_argument("--min-area", type=int, default=80)
    args = parser.parse_args()

    model, device = load_segmentation_model(model_path=args.checkpoint)
    result = predict_segmentation(
        image_path=args.image,
        model=model,
        device=device,
        image_size=args.image_size,
        threshold=args.threshold,
        min_area=args.min_area,
    )

    mask_path, overlay_path = save_segmentation_outputs(
        result, args.output_dir, stem=Path(args.image).stem
    )

    original_out = Path(args.output_dir) / f"{Path(args.image).stem}_ct.png"
    Image.open(args.image).convert("L").save(original_out)

    print("Segmentation completed.")
    print(f"Original: {original_out}")
    print(f"Mask    : {mask_path}")
    print(f"Overlay : {overlay_path}")


if __name__ == "__main__":
    main()
