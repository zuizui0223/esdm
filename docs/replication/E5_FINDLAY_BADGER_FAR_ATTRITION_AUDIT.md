# E5 Findlay BADGER far-bin attrition — post-result aggregate/code reconciliation

**Date:** 2026-10-13. **Status:** source-code and immutable-receipt reconciliation only. This is a *post-outcome diagnostic*, **not** a new biological response opening, re-fit, reclassification of the original Findlay one-shot, or a new E5-qualified dataset.

## Precisely what the frozen materials say

The already frozen Findlay stage receipt (`E5_FINDLAY_STAGE_DESCRIPTIVE_RESULT_RECEIPT.json`) reports the following lateral CCTV reference passes and trigger-conditioned registration eligibility:

| Species and fixed distance bin | Triggered CCTV passes | Eligible registration records | Difference |
|---|---:|---:|---:|
| BADGER near ≤1 m | 36 | 36 | 0 |
| BADGER middle 1–3 m | 89 | 89 | 0 |
| **BADGER far >3 m** | **16** | **15** | **1** |
| FOX near ≤1 m | 55 | 55 | 0 |
| FOX middle 1–3 m | 97 | 97 | 0 |
| FOX far >3 m | 47 | 47 | 0 |
| **Total across those fixed bins** | **340** | **339** | **1** |

The unchanged frozen parser's registration exclusion tally includes exactly **one `invalid_capture`**, while both source files contained **881** rows. Its eligibility pipeline is: species → lateral orientation → valid distance → valid `TRIGGER` → require `TRIGGER=1` for the registration stage → require `CAPTURE` to be a binary 0 or 1. A missing, empty or otherwise non-binary `CAPTURE` is therefore rejected from its registration denominator.

A **separate, completed** forensic receipt (`E5_FINDLAY_PASSAGE_LINKAGE_FORENSIC_RECEIPT.json`) reports **881/881** same-row shared covariate matches and **881/881** same-row `TRIGGER` agreement across released files. Under this source-row agreement and the frozen bin rules, **the unique one-record loss in the ESDM registration parser is localized to the BADGER far bin**. No new row-value access or recomputation of the original stage result is necessary for that accounting conclusion.

The [original authors' pinned R script](https://github.com/melaniefindlay/CT-Detection/blob/abc72f535bb59ebed202fb7acca852fc1647e97a/Defining%20component%20processes%20of%20detectability-Findlay%20Briers%20White%2030%2012%2018.R#L299-L323) independently shows that BADGER registration analyses select lateral records, then `TRIGGER=1`, then apply `na.omit()` (lines 313–320). This is **consistent with a missing-value exclusion mechanism**. It does not tell us the precise original `CAPTURE` field content, why the value was missing/invalid, or whether the original R `na.omit()` handled it identically to the retrospective ESDM 0/1 parser.

## What is now narrower, and what remains unresolved

**Reconciled only at the analytical processing layer:** the previously recorded 16-versus-15 BADGER far discrepancy is completely accounted for by the one non-binary/missing `CAPTURE` exclusion in the frozen ESDM stage pipeline. That is more specific than merely saying the two eligible groups have different sizes.

**Still unproven:** the originating reason for the missing/non-binary response, whether that source passage has a valid registration response in original annotations, the absence of actual passage-to-passage mismatch between exported tables, and the existence of an independently documented persistent CCTV passage identifier. Row-order agreement is *not* a stable physical passage key, especially with 351 duplicated covariate fingerprints.

Do not silently treat `CAPTURE` missing as 0, impute it, or compute a BADGER far/near composite from 16 and 15 unmatched eligible records. Do not change the original one-shot result's `COHORT_NONCOMPARABLE` or `mismatch_reason_not_proven` flags; those are historically frozen and are not contradicted by a separate **proximate parser-level** explanation. Do not promote FOX aggregate agreement to confirmed passage-level linkage, and do not claim diel/geographic transfer or original E5 G4 success.

The narrowed external request to [Findlay et al.](https://doi.org/10.1007/s13364-020-00478-y) is: **(i)** a codebook identifying how `CAPTURE` non-response/missingness was generated and represented (especially for one far BADGER trigger), **(ii)** a de-identified stable passage key or annotation timestamp/camera-position crosswalk for both stage exports. There is no need for original videos, individual animal IDs, or sensitive coordinates.

## Reproducibility without opening a response file

The immutable existing inputs are the two cited E5 JSON receipts and the original Git-pinned R *code* (not original biological rows). The accompanying regression test asserts the frozen cohort totals, singular mismatch, unique invalid-capture count, 881/881 same-row agreement, and the original STOP status. No new fit, database search, download, response-side figure, or confidence interval is introduced.
