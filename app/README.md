# App Workspace

This folder is the shared integration zone.

## Purpose

Build the end-to-end demo app:

1. upload CT image
2. classify as `Normal` or `Stroke`
3. if `Stroke`, run segmentation
4. render lesion overlay

## Integration rule

The app should call only the shared inference contracts from `src/stroke_ct_ai/`.
It should not depend on training notebook internals.
