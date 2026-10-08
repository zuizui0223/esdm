# E5 Findlay: a passage-referenced two-stage observation process

**Terminal status:** retrospective descriptive evidence; **no original E5 G4 promotion**. Source: [run 37770893387](https://github.com/zuizui0223/esdm/actions/runs/37770893387); artifact 11547502193. The aggregate result JSON is retained as an artifact; its ZIP and inner JSON SHA256 values are pinned in `E5_FINDLAY_STAGE_DESCRIPTIVE_RESULT_RECEIPT.json`.

## What was measured

Continuous CCTV provides a *pass denominator* that ordinary camera-trap data lack. Under the frozen two-file, lateral-pass and distance-bin rules, the descriptive quantities are:

- `P(trigger | CCTV pass)`;
- `P(registered | triggered pass)`;
- their product, conditional on the two stage cohorts being comparable.

| Fox lateral passes | <= 1 m | > 3 m |
|---|---:|---:|
| CCTV passes | 88 | 175 |
| Camera triggers | 55 | 47 |
| Registered triggered passes | 19 / 55 | 27 / 47 |
| Trigger probability | 62.5% | 26.86% |
| Conditional registration probability | 34.55% | 57.45% |
| Approximate two-stage recorded/pass probability | 21.59% | 15.43% |

The log far/near trigger shift is **−0.8446**, while the conditional registration shift is **+0.5086**; their sum is the composite shift **−0.3361**. The preregistered *descriptive* compensation index is **0.7517**. This means the *magnitude of opposing stage log-shifts* largely cancels; it does **not** imply that three-quarters of cameras are corrected or that recording is unbiased. The product still falls by approximately 28.5% (far versus near).

## Critical QC: badger, and the FOX linkage caveat

For badger far passes, the CCTV trigger source includes **16** triggered lateral passes, whereas the registration source retains **15** corresponding eligible rows; the fixed contract therefore prohibits a far/near badger composite estimate (`COHORT_NONCOMPARABLE`). The exact reason for the missing eligible row has not been established and must not be invented.

For FOX, bin-level trigger counts match registration eligibility counts (55 and 47 for the near/far contrast), allowing the frozen script's *count-aligned* stage product. **However, identical aggregate counts do not prove that the files contain the same individually matched passage records.** No source-backed per-pass join key/crosswalk was verified in this one-shot. Consequently this is a carefully qualified descriptive calculation, not a record-level cohort-validation or a new confirmatory effect.

## Ecological meaning, without overclaiming novelty

The nontrivial observation is that one final camera-recording proportion can conceal compensating upstream and downstream observation stages. More generally, an apparent stable diel camera pattern need not imply stationary trigger or registration mechanisms. Conversely, context-dependent passage-distance, gait and trajectory mixtures can shift the effective detection process even if the conditional hardware response functions remain the same.

Those last propositions are **mechanistic hypotheses** requiring new, jointly observed pass covariates and true day/night calibration—not findings established by this distance-bin reanalysis. The published Findlay paper already examined aspects of distance/gait and stage detection, and the qualitative direction was seen before this retrospective contract was frozen. This work is best presented as an audited replication/bridge to future E5 design, **not a novel discovery of a distance response**.

## Scope and stopping rule

- The source's two study contexts are small, short and taxonomically non-crossed; they cannot satisfy the original E5 geographic transfer G3, G5 or G6 gates.
- No passage time-of-day distribution, seasonal transport, out-of-geography test or inference interval was estimated.
- Original E5 stays **0/17 qualified**, original direct-detection G4 not passed. The frozen wild-pig UNRESOLVED/QC HOLD and Rhode Island G4 stop remain untouched.
- This exact one-shot must not be rerun, and threshold/species selection must not be revised post-outcome. Any further data access for per-pass joining must be transparently labeled exploratory and must not retroactively validate this result.

The strongest next ecological study is a geographically crossed *known-passage* camera dataset with a reliable per-pass ID, contemporaneous behavior (speed/distance/gait), stage-labeled trigger/registration, fixed settings and true exposure, rather than more uncalibrated paired-camera deployments.
