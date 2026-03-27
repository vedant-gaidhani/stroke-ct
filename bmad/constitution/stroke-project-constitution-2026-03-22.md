# Stroke CT Project Constitution

Date: 2026-03-22
Role: pm
Phase: planning
Workflow: vision -> constitution -> execution spec
Status: active

## Purpose

Define the durable project constitution for the `stroke-ct-ai` competition build so that all future work stays aligned with the organizer rules, the project vision, and the shortest path to a strong final submission.

## Article 1: Mission

Build a clinically legible, competition-compliant, two-stage AI system for brain CT scans that:

1. detects stroke presence as `Normal` or `Stroke`
2. localises hemorrhage regions with a segmentation mask for stroke-positive scans
3. presents both outputs in a stable prototype interface

## Article 2: Success Definition

Success requires all of the following:

- organizer compliance
- end-to-end functionality
- measurable model performance
- lesion visualisation
- reproducibility
- usable demo flow
- documentation strong enough for expert evaluation

## Article 3: Compliance Supremacy

If any implementation idea conflicts with the infobook, the infobook wins.

Practical implications:

- use only the provided dataset
- no external or supplementary data
- no augmentation
- no disallowed transformations or enrichments
- produce runtime dataset dimension output before training or inference
- declare all public pre-trained weights

## Article 4: Scope Lock

The project is permanently centered on:

- brain CT inputs
- stage 1 stroke classification
- stage 2 hemorrhage localisation
- judge-facing prototype
- required metrics and reporting

All other ambitions are subordinate and optional.

## Article 5: Product Philosophy

The system must prioritize:

- trustworthiness over flash
- clarity over feature count
- completion over novelty for novelty's sake
- one coherent story over many disconnected capabilities

## Article 6: Anti-Goals

The project will not drift into:

- broader neuroimaging research
- hospital productization
- unsupported explainability branches
- unrelated automation
- multimodal platform building
- infrastructure-heavy experiments with no submission value

## Article 7: Evidence Standard

No major claim is accepted without one of:

- code
- metrics
- screenshots
- logs
- report content
- BMAD artifact evidence

## Article 8: Architectural Bias

Default toward:

- public pre-trained backbones when useful
- deterministic and reproducible pipelines
- clear stage boundaries between classification and segmentation
- minimal UI for fast demo reliability
- evaluation scripts that can be rerun

## Article 9: Governance Durability

This constitution may be amended only when:

1. the user explicitly approves the change
2. the change is documented in BMAD artifacts
3. a checkpoint records the amendment and reason

## Article 10: Ruflo and BMAD Compatibility

This constitution supports Ruflo and BMAD by:

- requiring Ruflo routing and LSRA evidence
- using BMAD phase gates instead of ad hoc execution
- reducing divergence before it becomes implementation debt
- preserving project memory across sessions
