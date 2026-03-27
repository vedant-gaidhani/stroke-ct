# AesCode Stroke CT AI

Public code repository for the `AI-Based Brain Stroke Detection and Lesion Segmentation from CT Scans` hackathon project.

## Project Goal

Build a two-stage system that:

1. classifies a brain CT scan as `Normal` or `Stroke`
2. localizes hemorrhage regions with a lesion mask
3. presents results through a simple demo interface

## Repository Policy

- This repository is for code, planning, and documentation only.
- Organizer-provided datasets are **not** stored in this public repository.
- Model checkpoints and large artifacts should be kept in private Google Drive or other private storage.

## Working Setup

- Code: GitHub
- Training: Google Colab T4
- Data and checkpoints: Google Drive

## Team Split

- Classification owner: trains and evaluates the stroke classifier
- Segmentation owner: trains and evaluates the lesion segmentation model
- Shared: integration, report, slides, and demo

## Current Status

Planning and project governance are in place. Both classification and segmentation now have frozen baselines in code, and implementation continues under the BMAD and Ruflo workflow defined in [AGENTS.md](./AGENTS.md).

## Repository Structure

```text
classification/        # Friend-owned training and evaluation work for stroke classification
segmentation/          # Your training and evaluation work for lesion segmentation
app/                   # Shared demo app and integration layer
src/stroke_ct_ai/      # Shared Python package for pipeline contracts and inference orchestration
docs/                  # Shared setup and collaboration docs
bmad/                  # Governance, plans, constitution, checkpoints
```

## Parallel Work Rules

- `classification/` is owned by the classification contributor.
- `segmentation/` is owned by the segmentation contributor.
- `app/` and `src/stroke_ct_ai/pipeline/` are shared integration zones.
- Do not place dataset files, checkpoints, or Google Drive exports in this repository.
- Keep training artifacts in Google Drive and only push code, lightweight configs, and selected documentation here.

## Local Model Testing

The segmentation pipeline can be tested locally from VS Code without committing the checkpoint:

```powershell
$env:STROKE_CT_SEGMENTATION_CHECKPOINT="D:\path\to\segmentor_best_tversky_384.pth"
python segmentation\run_local_inference.py --image "D:\path\to\ct_slice.jpg"
```

The checkpoint remains private; only the code and lightweight docs belong in GitHub.

The classification pipeline can also be tested locally without committing its checkpoint:

```powershell
$env:STROKE_CT_CLASSIFICATION_CHECKPOINT="D:\path\to\classifier_best_efficientnet_b0.pth"
python classification\run_local_inference.py --image "D:\path\to\ct_slice.jpg"
```
