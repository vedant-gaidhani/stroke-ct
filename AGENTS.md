# STROKE CT PROJECT GOVERNANCE

This repository exists to execute one specific competition project correctly:

`AI-Based Brain Stroke Detection and Lesion Segmentation from CT Scans`

The purpose of this file is to act like a permanent PM, architect, and integrity officer in the room.
It must reduce drift, prevent subvergence, preserve Ruflo and BMAD workflows, and keep the project aligned with the competition rules.

If another instruction conflicts with this file, resolve by the authority stack below.

## AUTHORITY STACK

Highest to lowest:

1. Organizer rules in `D:\Desktop\AesCodeNexus_infobook.pdf`
2. This `AGENTS.md`
3. Project constitution and execution spec under `bmad/`
4. Current BMAD artifact for the active phase
5. Local implementation details

If a lower-level artifact conflicts with a higher-level artifact, the higher-level artifact wins.

## PROJECT IDENTITY

- Project name: `stroke-ct-ai`
- Competition track: `AI-Based Brain Stroke Detection and Lesion Segmentation from CT Scans`
- Clinical target: rapid support for stroke detection from brain CT and lesion localisation for hemorrhagic stroke
- Output style: end-to-end, clinically legible, reproducible, demo-ready system

## NON-NEGOTIABLE PROJECT VISION

This project is not a generic AI demo.

This project must always remain:

- an end-to-end two-stage system
- focused on brain CT scans only
- clinically legible to judges
- competition-compliant under the infobook
- reproducible from code and documented artifacts
- narrow enough to finish within the hackathon timeline

Any work that weakens those properties is off-vision and must be blocked.

## IMMUTABLE OUTCOME

The target deliverable is a working two-stage pipeline:

1. classify a CT scan as `Normal` or `Stroke` with confidence
2. for stroke-positive scans, produce a lesion mask overlay for hemorrhage localisation
3. present both through a simple, reliable interface

The system must always optimize for:

- correctness under competition constraints
- clarity in a live judge demo
- reproducibility
- low iteration cost
- minimal scope drift

## HARD SCOPE BOUNDARIES

Allowed scope:

- brain CT classification
- hemorrhage lesion segmentation
- preprocessing that preserves organizer compliance
- training, evaluation, inference, reporting, and demo packaging
- UI strictly for upload, prediction, overlay, metrics, and explanation

Disallowed scope unless the user explicitly overrides and records a checkpoint:

- multi-disease expansion
- MRI, ultrasound, fundus, or non-CT modalities
- hospital platform ambitions
- EHR integration
- mobile app expansion
- cloud platform expansion
- chatbot features
- explainability work that threatens core delivery
- research branches not needed for the competition submission

## COMPETITION COMPLIANCE RULES

These are mandatory and override convenience:

- Use only the organizer-provided dataset.
- Do not use external datasets.
- Do not use supplementary datasets.
- Do not use web-scraped data.
- Do not use alternative data sources.
- Do not augment, rebalance, enrich, or transform the dataset in ways disallowed by the infobook.
- The infobook bans augmentation even if a softer challenge description suggests otherwise.
- Emit dataset dimension output at runtime before training or inference.
- Keep logs or screenshots of dataset dimensions for the final report.
- Use publicly available pre-trained weights only if fully declared.
- Do not use commercial AI APIs as a core project component.
- Do not rely on AutoML for the solution.
- Do not submit wholesale AI-generated code without understanding and adaptation.

Any planned change that risks disqualification must be blocked immediately and recorded as a blocker.

## RUFLO_MANDATORY_POLICY

- Use Ruflo MCP for task routing/orchestration first whenever `mcp__ruflo__*` tools are available.
- Keep Ruflo as the default orchestration path for code, analysis, and planning.
- If Ruflo MCP is unavailable in a session, report it explicitly and continue with local tools.

## RUFLO_LSRA_POLICY

- For medium/large tasks, execute `learn -> store -> recall -> apply`.
- Store learned items in Ruflo memory namespaces: `knowledge`, `learnings`, `skills` as appropriate.
- Recall from those namespaces before implementation and apply recalled signal in the work.
- Mark task incomplete if LSRA evidence is missing.
- Store decisions that reduce future drift, especially around compliance, architecture, evaluation, and demo scope.

## RUFLO_USAGE_MAXIMIZER

- Route every non-trivial task with a Ruflo routing/hook call first.
- Prefer parallel Ruflo/tool operations where safe.
- Include explicit Ruflo evidence in task summaries.
- Use Ruflo memory to preserve the active vision, blocked ideas, and resolved tradeoffs.

## BMAD_MODE

- BMAD is mandatory.
- Work spec-first, not code-first.
- Restore BMAD state before substantial work.
- Keep provenance accurate.
- Prefer explicit role handoffs.
- Use checkpoints as proof, not decoration.

## BMAD_EXECUTION_CONTRACT

Always begin substantial work by reporting:

- current phase
- current role
- next role
- active workflow
- blockers
- open decisions
- required next artifact

Preferred sequence:

1. understand the goal
2. confirm the active BMAD phase
3. update the required artifact
4. write a checkpoint
5. hand off to the next role

Required checkpoint fields:

- role
- phase
- workflow
- artifact created or updated
- blockers
- decisions
- handoff target
- completion state

Phase gates:

- analysis -> planning requires `overview` or `brief`
- planning -> solutioning requires `prd`
- solutioning -> implementation requires `architecture` or `tech_spec`
- implementation -> done requires `validation`

Definition of done:

- validation exists
- final checkpoint exists
- next role is `complete`

## DECISION FILTER

Before accepting any major idea, ask:

1. Does it strengthen the two-stage CT pipeline?
2. Does it preserve competition compliance?
3. Does it improve demo reliability?
4. Does it reduce iteration count or ambiguity?
5. Can it be finished within the hackathon window?

If the answer to any of 1 to 3 is `no`, reject it.
If the answer to 4 and 5 is `no`, deprioritize or reject it.

## SUBVERGENCE BLOCKERS

The project must reject common failure modes:

- chasing SOTA instead of shipping
- expanding beyond CT stroke scope
- building UI beyond what supports the demo
- spending time on infrastructure not needed for submission
- training complexity that exceeds available compute and time
- undocumented experiments
- silent dataset handling changes
- deferring report and validation work until the end
- optimizing only the classifier while neglecting segmentation or interface

If a task creates side quests, the task must be narrowed before execution.

## DEFAULT TEAM SHAPE

When assigning work, prefer these lanes:

- `data-repro owner`: dataset loading, integrity checks, runtime dimension output, reproducibility
- `classification owner`: stage 1 model, metrics, inference path
- `segmentation owner`: stage 2 model, masks, overlay generation, segmentation metrics
- `demo-doc owner`: UI, report, judge narrative, packaging

If the team is smaller, combine lanes but do not drop responsibilities.

## ARCHITECTURAL BIAS

Prefer:

- the simplest model stack that can win
- pre-trained public backbones when allowed
- stable data loaders and deterministic training settings
- explicit evaluation scripts
- a thin, reliable UI layer
- one canonical inference path

Avoid:

- exotic pipelines without clear demo upside
- multiple competing architectures in the same branch
- loosely specified preprocessing
- over-engineered deployment

## DOCUMENTATION REQUIREMENTS

Every substantial implementation stream must ultimately produce:

- purpose
- inputs and outputs
- assumptions
- compliance notes
- evaluation method
- known limitations

No major component should exist as "just code."

## CHANGE CONTROL

These rules are intended to be durable.

Do not weaken the constitution, compliance rules, scope boundaries, or BMAD/Ruflo requirements unless:

1. the user explicitly instructs the change
2. the reason is documented in a BMAD artifact
3. a checkpoint records the governance change

## REQUIRED ARTIFACTS FOR THIS PROJECT

The repository should maintain these canonical artifacts as the project progresses:

- constitution
- execution spec
- brief
- prd
- architecture or tech spec
- implementation proof
- validation
- release notes if completed

## CURRENT STRATEGIC TRUTH

The competition rewards balanced completeness, not raw ambition.

The winning shape is:

- compliant data handling
- credible classification
- credible lesion segmentation
- robust end-to-end demo
- clear metrics
- strong documentation
- confident judge defense

Anything that threatens that shape must be treated as a blocker.
