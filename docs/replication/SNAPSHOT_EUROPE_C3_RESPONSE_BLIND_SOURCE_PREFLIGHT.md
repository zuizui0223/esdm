# C3 Snapshot Europe 2021–2022: an independent time-transfer opportunity — source preflight only

**Date: 2026-11-18. Status: PUBLIC_SOURCE_RESPONSE_BLIND_PREFLIGHT.**

## New independent empirical opportunity

Iannarilli et al. (2026), *Ecology* 107:e70516, DOI [10.1002/ecy.70516](https://doi.org/10.1002/ecy.70516), released 2026-11-05, report 1,198 camera locations in 2021 and 967 in 2022, 90,230 trap days and 30 camera arrays sampled in both years across European countries. Public raw data and metadata are described as Supporting Information Data S1, a 106.4-MB ZIP, mirrored in Max Planck Edmond as [10.17617/3.7YLWMU](https://doi.org/10.17617/3.7YLWMU). The original supporting ZIP is available at `https://pmc.ncbi.nlm.nih.gov/articles/instance/13740659/bin/ECY-107-e70516-s001.zip`. Source license is CC BY-SA 4.0 (preserve attribution/share-alike for derived redistributed data).

Unlike the already consumed E7 Serengeti and Safari14, this is an **independent European** camera consortium with two separately observed years. This makes it a valuable candidate for a future frozen, prospective **2021-discovery to 2022-validation** test of geographically bounded recorded mammal assemblage structure and/or identifiable *composite* occupancy-and-effective-detection rates. Publication-reported field geometry is **not** demonstration of raw data parseability.

## What this PR is authorized to do (and no more)

- Read only **ZIP central-directory metadata and the first CSV/TSV header line** of each tabular file; calculate and record source SHA256, file count, extensions, sizes and column *names*.
- Never parse, summarize, export or expose any biological animal observations, spatial coordinates, species names from cells, identities, response directions, counts from record rows, detection histories, training/heldout scores or images.
- No new species threshold, model fit, E5 qualification, source-pool correction, or hypothesis promotion. A failed HTTP source download is a **transport stop**, not an ecological negative.
- Run exactly at the first PR-opening for the fixed head branch, with a subsequent **PR-number/head-SHA/attempt lock** before any new PR event. No `push`, `workflow_dispatch`, `schedule`, or `synchronize` source triggers.
- Read only the original publisher/PMC supporting data archive. A future alternative Edmond transport must be separately disclosed and source-pinned, never silently substituted.

## Pre-screen questions that matter

1. Is the public supporting ZIP truly available and hashable as published, or does it return an HTTP/HTML block?
2. Are *separate* deployment/exposure/effort and observation event tables present as documented, with explicit 2021/2022, physical camera and array identifiers?
3. Do the headers preserve habitat, survey protocol and source geography labels sufficiently to define a response-blind 2021/2022 transfer rule?
4. Does it expose an **independent non-trigger-selected known-passage reference stream**? If not, this **does not** qualify original E5 G4, even with repeated observations and full years.

## Decision after preflight

If headers are adequate, write **one subsequent untouched-outcome design** for exactly one ecological question and holdout. Reject if effort/deployment provenance or geography is too ambiguous. The observational q–d submodel (see `POOL_STATE_DETECTION_IDENTIFICATION_AUDIT.md`) remains the inference ceiling unless an independently identified reference is supplied. Do not re-open C1/C2, reduce E5 standards, or tune a synthetic generation. Original E4/E5/E7/Safari14/C1/C2 results are immutable.

This document is a source-readiness contract, **not** a positive ecological or identifiability result.
