# Nexus AESCODE Winning Problem Brief

Date: 2026-03-20
Phase: analysis
Role: analyst
Workflow: overview -> brief -> recommendation

## Goal

Identify the strongest problem statement on the Nexus AESCODE challenge page for maximizing hackathon win probability.

## Source Evidence

- Challenge source extracted from `https://nexusaescode.netlify.app/#challenges` by inspecting the live app bundle.
- FAQ judging criteria on the same site: clinical relevance, technical innovation, and solution feasibility.
- Presentation format on the same site: 5 minutes total, split into 3 minutes presentation and 2 minutes Q&A.
- Mentor mix on the site includes strong neurology and stroke expertise.

## Candidate Problem Statements

1. AI-Based Prediction of High-Risk Plantar Pressure Zones for Prevention of Diabetic Foot Ulcers
2. AI-Based Early Warning System for Patient Physiological Deterioration Using Vital Sign Time-Series Data
3. AI-Based Osteoporosis Risk Screening from Routine X-Ray Radiographs
4. AI-Based Detection of Incorrect Exercise Form Using Human Pose Estimation
5. AI-Based Brain Stroke Detection and Lesion Segmentation from CT Scans

## Decision Criteria

- Clinical relevance: How severe, urgent, and medically meaningful the problem is.
- Technical innovation: How compelling the ML approach and output look to judges.
- Solution feasibility: Whether a convincing prototype and story can be delivered within hackathon constraints.
- Demo strength: Whether the output is visually obvious and easy to explain in 3 minutes.

## Assessment

### Recommended First Choice

AI-Based Brain Stroke Detection and Lesion Segmentation from CT Scans

Why:

- Highest clinical urgency and strongest life-or-death narrative.
- Very strong visual demo: upload CT, classify stroke, show lesion overlay.
- Two-stage pipeline looks technically substantial without requiring excessive product complexity.
- Neurology/stroke mentor presence likely increases resonance with judges.

Risks:

- Harder than other options because it requires both classification and segmentation.
- Needs disciplined scope control to avoid an incomplete prototype.

### Strongest Feasibility Alternative

AI-Based Early Warning System for Patient Physiological Deterioration Using Vital Sign Time-Series Data

Why:

- Excellent balance of relevance and feasibility.
- Easier to prototype reliably than CT segmentation.
- Good fit for a dashboard demo and time-series ML story.

Why it ranks second:

- Less visually striking than stroke imaging.
- Slightly weaker "wow" factor in a short live pitch.

## Recommendation

If the team is strong in computer vision and can execute with discipline, choose the stroke CT problem.

If the team is more likely to win by shipping a cleaner, lower-risk system, choose physiological deterioration.

Overall pick for highest upside: AI-Based Brain Stroke Detection and Lesion Segmentation from CT Scans.
