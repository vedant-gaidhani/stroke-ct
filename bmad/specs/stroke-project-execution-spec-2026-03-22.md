# Stroke CT Project Execution Spec

Date: 2026-03-22
Role: architect
Phase: solutioning
Workflow: constitution -> execution spec -> implementation handoff
Status: active

## Goal

Translate the constitution into enforceable execution rules that help agents and humans make consistent decisions with minimal iteration.

## 1. Canonical System Shape

The canonical project shape is:

- Stage 1: CT scan classification
  - input: brain CT image or scan representation supported by the dataset
  - output: `Normal` or `Stroke` plus confidence
- Stage 2: hemorrhage segmentation
  - input: stroke-positive CT input
  - output: lesion mask and overlay
- Stage 3: presentation layer
  - upload input
  - show stage 1 result
  - show stage 2 overlay
  - show key metrics and compliance-friendly context

## 2. Canonical Deliverable Set

The project must produce:

- classification training pipeline
- segmentation training pipeline
- evaluation scripts
- dataset integrity output
- trained artifacts or reproducible training path
- demo UI
- technical report content
- validation evidence

## 3. Mandatory Technical Behaviors

- Print dataset dimensions before training or inference.
- Keep one canonical data loading path.
- Keep one canonical inference path.
- Record assumptions for every model choice.
- Prefer deterministic runs when possible.
- Preserve a clean separation between experimentation and submission-ready artifacts.

## 4. Forbidden Behaviors

- hidden data changes
- augmentation in official training mode
- silent metric cherry-picking
- multiple parallel "main" pipelines
- demo-only code with no reproducible backend
- model outputs that cannot be explained in the report

## 5. Required Evaluation Surface

Classification must support:

- accuracy
- F1
- AUC-ROC if applicable
- confusion matrix

Segmentation must support:

- Dice
- IoU
- qualitative overlay inspection

Project-level validation must support:

- sample end-to-end demo cases
- runtime and failure notes
- limitations and known error modes

## 6. Interface Rules

The UI exists to prove the pipeline, not to become its own project.

The interface should only do what helps judges verify:

- the model receives CT input
- the classifier returns a result and confidence
- the segmentation stage returns an overlay
- the output is stable and legible

Everything else is optional.

## 7. Experiment Management Rules

- One baseline per stage before any optimization branch.
- Do not run new experiments until the baseline is documented.
- Do not keep dead branches alive in planning artifacts.
- If compute is limited, favor smaller reliable iterations over large speculative runs.

## 8. Handoff Rules

The next implementation agent must receive:

- current phase
- active artifact
- exact scope boundary
- unresolved blockers
- compliance constraints
- expected outputs

## 9. PM Enforcement Rules

Whenever a task is proposed, it must be labeled as one of:

- core
- support
- optional
- out-of-scope

Only `core` and required `support` work should block the critical path.

## 10. Conflict Resolution

When there is conflict between:

- ambition and finishability: choose finishability
- novelty and compliance: choose compliance
- model complexity and demo reliability: choose reliability
- extra features and report completeness: choose report completeness

## 11. Expected Artifact Path

Recommended BMAD artifact progression:

- brief
- prd
- architecture or tech spec
- implementation proof
- validation

No implementation stream should skip directly from idea to code without this path being acknowledged.
