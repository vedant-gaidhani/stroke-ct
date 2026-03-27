# Classification Workspace

This folder is owned by the classification contributor.

## Frozen baseline

The current official classification baseline is:

- model: `EfficientNet-B0`
- input size: `224x224`
- loss: `CrossEntropyLoss`
- optimizer: `AdamW (lr=1e-4)`
- best epoch: `7`
- best validation accuracy: `0.9037`
- best validation F1: `0.8759`
- best validation AUC: `0.9682`

Checkpoint location is private and stays outside the repo.

## Purpose

Use this folder for classification-specific training notes and local runners. The reusable inference contract lives in [src/stroke_ct_ai/classification/inference.py](/D:/Desktop/hackathon_ai/src/stroke_ct_ai/classification/inference.py).

## What belongs here

- training notebook references
- classification-specific helper scripts
- local evaluation runners
- lightweight documentation

Do not store the dataset or exported checkpoints in this repo.

## Dataset note

The provided `split_manifest.csv` contained `test` rows that were missing from the local dataset copy. The classifier baseline was trained on the filtered manifest using only existing `train` and `val` files.

## Local VS Code run

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Point the code to your private checkpoint:

```powershell
$env:STROKE_CT_CLASSIFICATION_CHECKPOINT="D:\path\to\classifier_best_efficientnet_b0.pth"
```

4. Run local inference:

```powershell
python classification\run_local_inference.py --image "D:\path\to\ct_slice.jpg"
```

The script writes a `prediction.json` summary and a `*_preview.png` image to `classification\outputs\`.
