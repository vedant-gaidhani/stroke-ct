# AesCode Infobook Expectations Brief

Date: 2026-03-20
Phase: analysis
Role: analyst
Workflow: overview -> brief -> expectation analysis

## Goal

Determine what AesCode Nexus organizers explicitly require and what they implicitly expect from teams, especially from likely finalists and winners.

## Source

- `D:\Desktop\AesCodeNexus_infobook.pdf`
- Extracted text file: `D:\Desktop\hackathon_ai\AesCodeNexus_infobook.txt`

## Explicit Organizer Requirements

### Eligibility and format

- Only undergraduate engineering students may participate.
- Teams must have 1 to 5 members.
- Each participant can belong to only one team.
- A Team Lead is mandatory.

### Timeline

- Round 1 runs 21 March to 27 March 2026.
- Round 1 deliverable is due by EOD 27 March 2026.
- Shortlisting happens 27 March to 29 March 2026.
- Round 2 runs 30 March to 3 April 2026.
- Final submission is due by EOD 3 April 2026.
- Final presentation is on 4 April 2026.
- No extensions will be granted.

### Round 1 expectations

- Show problem understanding.
- Propose a credible technical approach and system design.
- Finalize the tech stack.
- Explore the dataset.
- Build backend or model components, data pipelines, and feature engineering.
- Show initial model training or application build progress.

### Round 2 expectations

- Test and iterate the model.
- Validate clinical relevance.
- Stabilize the UI and workflow.
- Prepare the demo and technical documentation.
- Package the final submission professionally.

### Final submission requirements

- Trained ML model with saved weights or exported files.
- Complete source code.
- Code must be clean, commented, and reproducible.
- Functional UI prototype.
- Technical report with architecture, dataset, preprocessing, training, evaluation, limitations, and future work.
- Runtime dataset dimension output.

### Data rules

- Organizer-provided dataset is mandatory.
- No external datasets.
- No supplementary datasets.
- No web-scraped data.
- No augmentation.
- No transformation, rebalancing, or enrichment of data.
- Breaking these rules causes immediate and permanent disqualification.

### Technical rules

- Open-source tools are allowed.
- Public pre-trained weights are allowed if fully declared.
- Commercial AI APIs cannot be a core part of the solution.
- AutoML that generates the whole solution is not allowed.
- Wholesale AI-generated code without understanding or adaptation is not allowed.

### Integrity rules

- Work must be original and developed during the hackathon window.
- Open-source references are allowed only with attribution.
- Similarity checks are expected.

## Implicit Expectations

The organizers are not running a pure idea hackathon. They are running a controlled, reproducibility-heavy research engineering contest.

They expect:

- disciplined execution over hype
- auditable handling of data
- measurable model results
- a usable prototype, not just a notebook
- documentation strong enough for expert review
- enough technical understanding to defend choices live

## What Finalists and Winners Likely Need

### To survive Round 1

- A narrow, realistic scope.
- Evidence that the pipeline already works.
- Real progress artifacts, not plans alone.
- Clear documentation that makes reviewers trust the team can finish.

### To win Round 2

- Strong quantitative metrics.
- A convincing explanation of clinical relevance.
- A reliable and polished UI demo.
- Clean, reproducible code and a complete report.
- Confident answers to judge questions on data integrity, methodology, and limitations.

## Key Strategic Insight

The strongest teams will look like small product-plus-research teams:

- one owner for model training and evaluation
- one owner for data pipeline and reproducibility
- one owner for UI/demo
- one owner for report and presentation narrative

The event rewards balanced completeness more than a single flashy model result.
