from dataclasses import dataclass

from stroke_ct_ai.classification.inference import (
    ClassificationResult,
    predict_classification,
)
from stroke_ct_ai.segmentation.inference import (
    SegmentationResult,
    predict_segmentation,
)


@dataclass
class PipelineResult:
    classification: ClassificationResult
    segmentation: SegmentationResult | None


def run_pipeline(image_path: str) -> PipelineResult:
    """
    Canonical inference flow for the demo app.

    1. Run classification
    2. If label is Stroke, run segmentation
    3. Return structured outputs
    """
    classification = predict_classification(image_path)

    if classification.label == "Normal":
        return PipelineResult(classification=classification, segmentation=None)

    segmentation = predict_segmentation(image_path)
    return PipelineResult(classification=classification, segmentation=segmentation)
