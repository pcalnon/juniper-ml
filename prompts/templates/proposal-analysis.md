# Proposal Analysis — {{!SUBJECT: the proposals / question to synthesize}}

<!--
Category template: synthesize and cross-validate prior proposals into one analysis doc
(analysis-class, produces a notes/ document). The Template Agent fills a COPY (never this
source -- D-5); validated against RUBRIC.md.
Convention: NAME fill, !NAME: hint required, ?NAME: hint optional.
-->

## Role

You are an experienced principal engineer and technical analyst synthesizing the proposals above into a single, rigorous, comprehensive analysis, surfacing agreements, gaps, and the best path forward.

## Resources

{{!RESOURCES: the discovery grounding bundle + the paths of the proposals/inputs to synthesize and any relevant architecture/dependency facts. Cite real document and code anchors, never invented ones.}}

## Primary Objective

Produce one unified analysis that captures every material issue raised across the inputs, notes which input identified each, and recommends a path forward.

## Assigned Tasks / Directives

1. Read each input proposal and extract its claims, findings, and recommendations.
2. Using multiple appropriately specialized **sub-agents for cross-validation**, ensure every issue raised in any input is captured in the final analysis, and note which proposal(s) correctly identified each.
3. Identify gaps no input covered, and flag any latent issue (e.g., a status-normalization gap in a relay path) for correction.
4. {{?EXTRA_DIRECTIVES: task-specific synthesis focus}}

## Key Deliverables & Requirements

- A single comprehensive analysis document written to `notes/`, named `JUNIPER_<SUBJECT>_ANALYSIS_<YYYY-MM-DD>.md`.
- A coverage map: each issue -> which input(s) caught it -> recommended resolution.

## Constraints

- This is an analysis/synthesis task -- do not implement code changes.
- Do not attribute a finding to an input that did not raise it, and do not invent issues; every claim must trace to an input or to verified repo state.

## Finalize / Validation

- Run a final sub-agent pass asking "what material issue or input did we miss?" and fold the answer in.
- Confirm every cited document/code anchor resolves before finalizing.
