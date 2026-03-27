# Stroke CT Two-Person Execution Plan

Date: 2026-03-23
Phase: planning
Role: pm
Workflow: execution planning -> architect handoff
Project: `stroke-ct-ai`

## Objective

Execute the `AI-Based Brain Stroke Detection and Lesion Segmentation from CT Scans` project with two people on Google Colab T4 in a way that is:

- competition-compliant
- realistically finishable
- strong in demo quality
- strong in report quality
- strong enough to compete for the overall prize

## Core Strategy

Build two supervised pipelines in parallel:

1. **Classification pipeline**
   - input: CT image
   - output: `Normal` or `Stroke` + confidence
   - owner: Person A

2. **Segmentation pipeline**
   - input: CT image
   - output: lesion mask for hemorrhage localisation
   - owner: Person B

3. **Integrated inference pipeline**
   - classifier runs first
   - if predicted `Stroke`, run segmentation model
   - show lesion overlay in the UI
   - shared responsibility, but Person B owns mask logic and Person A owns orchestration

This is the safest and most defensible structure for judges.

## Non-Negotiable Rules

- Use only the official organizer-provided datasets.
- Do not use external data.
- Do not use supplementary data.
- Do not use augmentation in official training mode.
- Print dataset dimensions before any training or inference run.
- Save all major artifacts to Drive continuously.
- Use public pre-trained weights only, and declare them in the report.
- Build true segmentation from the provided segmentation dataset. Do not substitute Grad-CAM as the official segmentation output.

## Team Roles

### Person A: Classification Owner

Owns:

- classification dataset audit
- classifier training
- classifier metrics
- classifier checkpoints
- classifier inference wrapper
- integration gate logic in the app

Deliverables:

- best classifier weights
- classification notebook
- confusion matrix
- ROC curve
- accuracy, F1, AUC
- inference function returning label + confidence

### Person B: Segmentation Owner

Owns:

- segmentation dataset audit
- segmentation data loader
- segmentation model training
- segmentation metrics
- mask generation
- overlay generation

Deliverables:

- best segmentation weights
- segmentation notebook
- Dice, IoU
- qualitative overlay samples
- inference function returning mask

### Shared Ownership

- folder structure
- report
- demo app
- presentation
- submission bundle
- final validation checklist

## Shared Folder Contract

Use one Google Drive project root with stable paths:

```text
/stroke_ct_ai/
  /data_classification/
  /data_segmentation/
  /artifacts/
    /classification/
    /segmentation/
    /shared/
  /reports/
  /slides/
  /app/
```

Rules:

- no renaming shared directories mid-project
- no moving files without notifying the other person
- model filenames must be versioned
- logs and plots go into `artifacts/`

## Canonical Artifact Contract

### Classification outputs

- `classifier_best.pth`
- `classifier_metrics.json`
- `classifier_confusion_matrix.png`
- `classifier_roc_curve.png`
- `classifier_examples.csv`

### Segmentation outputs

- `segmentor_best.pth`
- `segmentor_metrics.json`
- `overlay_examples/`
- `mask_examples/`
- `segmentation_examples.csv`

### Shared outputs

- `dataset_dimensions.txt`
- `demo_test_cases.csv`
- `technical_report.md` or `.docx`
- `submission_manifest.md`

## Runtime Flow Contract

The app must work like this:

1. user uploads CT image
2. classifier predicts `Normal` or `Stroke`
3. if `Normal`, show classification result and stop
4. if `Stroke`, run segmentation model
5. generate lesion overlay
6. show original image, predicted class, confidence, and lesion overlay

This must be the only official inference path.

## Model Recommendations

### Classification

Start with:

- `EfficientNet-B0` or `ResNet18`

Escalate only if baseline is stable:

- `EfficientNet-B2`

Avoid starting with larger models unless the baseline is already good and training speed is acceptable.

### Segmentation

Start with:

- lightweight `UNet`

Optional next step:

- `UNet` with pretrained encoder if the baseline is stable

Avoid heavy segmentation architectures early.

## Day-by-Day Plan

## Day 1: Foundation and Dataset Integrity

### Person A

- Mount Drive and set up the shared root.
- Load classification dataset.
- Print and save dataset dimensions:
  - total image count
  - class counts
  - split counts
  - image sizes
  - dataset size on disk
- Display sample CT images.
- Create classification loader.
- Save a dataset audit note.

### Person B

- Load segmentation dataset.
- Print and save dataset dimensions:
  - total images
  - total masks
  - split counts
  - image-mask pairing count
  - image and mask sizes
  - dataset size on disk
- Display sample image-mask pairs.
- Verify image-mask alignment.
- Create segmentation loader.
- Save a dataset audit note.

### Shared end-of-day gate

- Both datasets load cleanly.
- Dataset dimension output is saved.
- Shared folder structure is locked.
- No compliance uncertainty remains.

## Day 2: Baseline Training

### Person A

- Train classification baseline.
- Use transfer learning.
- Run short baseline training.
- Save best checkpoint.
- Save first validation metrics.
- Identify misclassified samples.

### Person B

- Train segmentation baseline.
- Start with small image size if needed for stability.
- Save best checkpoint.
- Save first Dice and IoU.
- Save first overlay samples.

### Shared end-of-day gate

- Both pipelines have completed at least one real training run.
- Both have saved weights.
- Both have metrics and sample outputs.

## Day 3: Stabilize and Improve

### Person A

- Improve classifier with controlled tuning only.
- Try learning-rate adjustments or partial unfreezing.
- Freeze the best-performing model by end of day.
- Export metrics plots and final inference helper.

### Person B

- Improve segmentation baseline.
- Verify masks are meaningful, not just noisy blobs.
- Export overlay generation utilities.
- Freeze a stable segmentation candidate by end of day.

### Shared end-of-day gate

- Classifier is stable enough for UI integration.
- Segmentor is stable enough for overlay demos.
- No new training ideas unless they beat the baseline clearly.

## Day 4: Integration Start

### Person A

- Build the shared inference wrapper.
- Implement classifier-first gating logic.
- Start app skeleton with upload + result layout.

### Person B

- Provide segmentation inference helper.
- Provide mask postprocessing and overlay functions.
- Integrate segmentation output into the shared app.

### Shared end-of-day gate

- One image can go through the app.
- If `Stroke`, overlay appears.
- If `Normal`, segmentation is skipped.

## Day 5: Integration Stabilization and Evidence

### Person A

- Test classification outputs on known samples.
- Add confidence display.
- Add uncertainty note if appropriate.
- Save app screenshots.

### Person B

- Test segmentation on known stroke-positive samples.
- Tune overlay clarity.
- Save a gallery of strong examples and failure cases.

### Shared

- Run at least 20 integrated test cases.
- Log failures in `demo_test_cases.csv`.
- Start technical report sections using real outputs, not placeholders.

### End-of-day gate

- End-to-end app is stable enough to demo.
- Metrics and screenshots are already available for the report.

## Day 6: Report, Slides, and Judge Readiness

### Person A

- Write classification sections of the report.
- Write metrics interpretation.
- Prepare classifier architecture and evaluation slides.

### Person B

- Write segmentation sections of the report.
- Write localisation limitations and strengths.
- Prepare segmentation and overlay slides.

### Shared

- Merge report into one technical narrative.
- Prepare 8 to 10 clean slides.
- Practice the 3-minute story.
- Prepare answers for:
  - why this architecture
  - what the dataset is
  - what the metrics mean
  - what the limitations are

### End-of-day gate

- Report is near-final.
- Slides are usable.
- Demo script exists.

## Day 7: Final Lock

### Both

- Do not add new features.
- Re-run dataset dimension output.
- Re-run final evaluation.
- Verify model files, notebooks, plots, app, report, and screenshots.
- Run a full demo rehearsal.
- Record demo only after successful rehearsal.
- Package final submission.

### End-of-day gate

- All required deliverables exist.
- Submission bundle is complete.
- Demo is stable.

## Task Priority Order

Always prioritize in this order:

1. compliance
2. dataset integrity
3. classification baseline
4. segmentation baseline
5. end-to-end integration
6. report and slides
7. optional polish

## Optional Features Policy

Optional features are allowed only if the end-to-end baseline is already stable.

Allowed optional features if time remains:

- uncertainty warning
- polished clinical-style PDF summary
- improved UI layout

Not recommended during the main critical path:

- patient history tracker
- DICOM support
- batch upload
- multi-class stroke type
- infarct volume estimation

## Daily Sync Protocol

Every day, both people should exchange:

- current blocker
- current best metric
- current saved artifact path
- next 3 concrete tasks

This should be written in one shared note or document.

## Risk Register

### Risk 1: Classification good, segmentation weak

Response:

- keep segmentation model simple
- prioritize stable overlays over speculative architecture changes
- document limitations clearly

### Risk 2: Segmentation good, classifier weak

Response:

- reduce model size
- verify labels and class balance
- simplify training and tune conservatively

### Risk 3: Integration breaks late

Response:

- integrate on Day 4, not Day 6
- keep one canonical inference path
- save explicit test cases

### Risk 4: Colab disconnects or artifact loss

Response:

- save every epoch to Drive
- export metrics and plots immediately
- version model files

## Judge Strategy

The winning pitch is:

- stroke diagnosis is urgent
- CT is fast and clinically standard
- system first detects stroke, then localises hemorrhage
- pipeline is reproducible and clinically legible
- demo is simple and trustworthy

Do not oversell.
Do not pretend Grad-CAM is segmentation.
Do not hide limitations.

## Definition of Ready for Submission

Ready means:

- dataset dimensions are saved and report-ready
- classifier weights and metrics are final
- segmentation weights and metrics are final
- app runs the full pipeline
- overlay examples are saved
- technical report is complete
- slides are complete
- demo is practiced

If any of those are missing, the project is not submission-ready.
