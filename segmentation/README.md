# Segmentation Workspace

This folder is owned by the segmentation contributor.

## Frozen baseline

The current official segmentation baseline is:

- model: `UNet(resnet18)`
- input size: `384x384`
- loss: `Tversky(alpha=0.3, beta=0.7)`
- threshold: `0.45`
- post-processing: connected-component cleanup with `keep_largest=True` and `min_area=80`
- best Dice: `0.4220`
- best IoU: `0.3012`

Checkpoint location is private and stays outside the repo.

## Purpose

Use this folder for segmentation-specific training notes and local runners. The reusable inference contract lives in [src/stroke_ct_ai/segmentation/inference.py](/D:/Desktop/hackathon_ai/src/stroke_ct_ai/segmentation/inference.py).

## What belongs here

- training notebook references
- segmentation-specific helper scripts
- local evaluation runners
- lightweight documentation

Do not store the dataset, exported checkpoints, or Drive artifacts in this repo.

## Local VS Code run

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Point the code to your private checkpoint:

```powershell
$env:STROKE_CT_SEGMENTATION_CHECKPOINT="D:\path\to\segmentor_best_tversky_384.pth"
```

4. Run local inference:

```powershell
python segmentation\run_local_inference.py --image "D:\path\to\ct_slice.jpg"
```

The script writes `*_ct.png`, `*_mask.png`, and `*_overlay.png` to `segmentation\outputs\`.
