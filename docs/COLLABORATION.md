# Collaboration Flow

This repository is structured so two contributors can work in parallel with minimal overlap.

## Ownership

### Classification owner

Owns:

- `classification/`
- `src/stroke_ct_ai/classification/`

Responsible for:

- training and evaluating the classification model
- exporting the classifier checkpoint to private storage
- maintaining the classifier inference contract

### Segmentation owner

Owns:

- `segmentation/`
- `src/stroke_ct_ai/segmentation/`

Responsible for:

- training and evaluating the segmentation model
- exporting the segmentation checkpoint to private storage
- maintaining the segmentation inference contract

### Shared integration zone

Shared:

- `app/`
- `src/stroke_ct_ai/pipeline/`
- `docs/`

Responsible for:

- end-to-end inference flow
- UI integration
- demo preparation
- report and setup documentation

## Branching

- Classification owner works on `feature/classification-*`
- Segmentation owner works on `feature/segmentation-*`
- Shared app integration works on `feature/app-*`

## Contract-first integration

The two model owners should not import each other's notebooks or ad hoc training code.

Integration should happen only through the shared Python contracts:

- `src/stroke_ct_ai/classification/inference.py`
- `src/stroke_ct_ai/segmentation/inference.py`
- `src/stroke_ct_ai/pipeline/run_pipeline.py`

## Artifacts policy

Keep these outside the public repo:

- datasets
- masks and images
- checkpoints
- heavy plots and generated exports

Only commit:

- code
- notebooks if needed
- requirements
- lightweight screenshots if intentionally curated
- docs
