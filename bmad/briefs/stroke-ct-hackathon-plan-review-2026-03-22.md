# Stroke CT Hackathon Plan Review

Date: 2026-03-22
Phase: analysis
Role: analyst
Workflow: plan review -> findings -> recommendation

## Goal

Evaluate `D:\Desktop\Stroke_CT_Hackathon_Plan.docx` against the AesCode infobook and the repository governance for the stroke CT project.

## Overall Assessment

The plan is strong as a speed-first execution draft, but it is not yet safe as the official project plan.

It has three major weaknesses:

1. It replaces required lesion segmentation with Grad-CAM heatmaps.
2. It suggests augmentation even though the infobook bans augmentation.
3. It creates a critical dependency bottleneck by having the second contributor join only on Day 4.

## What Is Good

- Clear bias toward a narrow, visually strong demo.
- Reasonable use of transfer learning for fast progress.
- Strong emphasis on Gradio for quick prototype delivery.
- Good instinct to save checkpoints and avoid getting stuck on errors.
- Good understanding that judges will care about explainability and live presentation quality.

## What Is Risky or Wrong

### 1. Grad-CAM is not equivalent to the required segmentation deliverable

The competition problem statement requires hemorrhage localisation as a segmentation output. A heatmap is helpful for explanation, but it is not the same as a lesion mask and should not be treated as the official substitute.

### 2. Augmentation conflicts with the infobook

The plan explicitly recommends adding augmentation if metrics are low. The infobook states augmentation is prohibited for this event. This must be removed from the execution path.

### 3. Team structure is too serial

The plan assumes one contributor is unavailable until Day 4, while the other person produces the model alone. This puts too much of the project on one dependency edge and reduces integration time.

### 4. Extra features are overvalued

The plan overestimates the value of features like patient history tracking, DICOM support, and batch processing. These are expensive side quests relative to the judging criteria and should not come before baseline segmentation, evaluation, and report quality.

### 5. Report and compliance work start too late

The technical report is deferred until Day 6. That is too late for a project with strict competition rules and required dataset-dimension evidence.

## Recommendation

Keep the overall spirit:

- fast transfer-learning baseline
- simple UI
- strong demo story

But change the plan to:

- make true segmentation or a defensible localisation output a first-class requirement
- ban augmentation in official training mode
- involve both contributors earlier
- move report and compliance artifacts earlier
- demote nearly all extra features until the end-to-end baseline is stable

## Final Judgment

Good execution instinct.

Not yet a good final execution plan.

It should be revised before being treated as the source of truth for implementation.
