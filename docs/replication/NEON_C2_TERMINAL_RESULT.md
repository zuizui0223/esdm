# NEON C2: terminal biological-response schema stop — NOT a mammal sorting result

**Date 2026-11-17 JST.** This account separates a successfully completed *technical workflow* from an ecological analysis that was **not** estimable. The one-shot C2 workflow [run 43900837691](https://github.com/zuizui0223/esdm/actions/runs/43900837691) executed at the independently frozen design/implementation in [PR #235](https://github.com/zuizui0223/esdm/pull/235). The [design was committed first](NEON_C2_REGION_CONSTRAINED_FROZEN_DESIGN.md) at `2b88e49eadfa9e8c90e6b717de0083836b604cee` before opening any camera sequence response.

## What was checked, and the exact terminal cause

- **Source independently identified and pinned:** [Zenodo NEON+forested plots v1, DOI 10.5281/zenodo.20826511](https://doi.org/10.5281/zenodo.20826511), publicly described as 13 NEON forest subprojects plus 4 additional US forest plots (2015–2022). No camera photographs were downloaded.
- **Synthetic correctness:** all **13/13** source-independent tests passed in the actual Actions job (source schema, fixed-margin trade conservation, camera sample construction, source hash refusal, support, dissimilarity arithmetic). The normal repository CI is separate.
- **Transport and integrity:** all three CSVs were fetched; published original MD5 checks completed successfully on the *exact* deployment/sequence/description data: `82537cdf0a586fa14c9a8b6afd7be470`, `7531a5b9fb3848ef33e162d5206a6f43`, and `be1502427995886ef1c64c10410d1ee2`. A metadata-only pre-response schema check showed the required `deployment_id,sequence_id,class,genus,species` fields.
- **One biological source opening:** after integrity passed, the frozen C2 parser encountered a *scientific binomial present with conflicting taxonomic class labels* (`Mammalia` vs another class). Under the prior immutable stop contract, this raises `RESPONSE_SCHEMA_STOP: taxonomic class conflicts for a binomial` **before** any null randomization or project effect estimation. It is a data QA/identification block, not a negative ecological test and not evidence that field species identities are biologically inconsistent. No binomial, camera ID, GPS or record timestamp involved in the stop was exported.
- **Workflow status `success` only means that the validator wrote the expected stop receipt and uploaded its artifact**. The ecological result status is **`RESPONSE_SCHEMA_STOP`**. The C2 design must not be changed in response to this observation.

## Immutable evidence and reproducibility

- Frozen action: [GitHub Actions run 43900837691](https://github.com/zuizui0223/esdm/actions/runs/43900837691), aggregate-only [artifact 14242175299](https://github.com/zuizui0223/esdm/actions/runs/43900837691/artifacts/14242175299).
- Artifact ZIP SHA256: `412f61d82aa9e7ee961bd8d77201fc5fbd2932c45275d47731f12c236b81ad05`.
- **Verbatim inner result JSON** at [NEON_C2_FROZEN_RESULT.json](NEON_C2_FROZEN_RESULT.json): 305 bytes, SHA256 `364c5eef71a5db979502d5de8a5d6ad6aebad066cbb5ccffa8433bc950b436fb`.
- Source scripts were not modified after the one biological response opening. The synthetic tests did not exercise any raw data. Regression guards verify the exact result and avoid elevating this stop to a biological null result.

## Ecological implications and what NOT to conclude

**No estimate** of region-conditioned project sorting, camera-level Simpson turnover excess, ecological barrier, true species-pool differences, observed occupancy or process-based eSDM superiority was obtained in C2. It would be methodologically incorrect to delete conflicting labels, relax the class consistency test, change region thresholds, pick different taxa or re-run this same biological opening to force a comparison. The C2 result is **not** a counterexample to the previously observed African Safari14 fixed-degree sorting, nor a replication of it. It also does not change the independent CamTrapAsia C1 negative incremental-environment prediction or the frozen E4/E5/E7/E7-C outcomes.

**Next scientifically useful route** must be independent and designed around demonstrably consistent taxonomy and separately recorded camera effort *before* exposing its focal response. Cross-region observations should allow environmental similarity versus available species pools to be tested while explicitly accounting for detection. Published 2025 community-occupancy literature shows why occurrence richness and detection-adjusted community state can yield different ecological stories; it is **external context**, not a completed new C2 test or an eSDM win. Any future source requires its own one-shot, original response-blind design; **no NEON-C2 rescue generation**.
