# E5 independent activity–detection candidate qualification

Status: **pre-candidate-search only**

E5 is not an E4 rerun. Its purpose is to find a genuinely independent empirical design
that can separate conditional ecological activity from effective observation detection
before testing transfer again.

## Why this is necessary

E4 robustly showed that the frozen activity channel failed to generalize in its heldout
domain, but the failure cannot be given a causal behavioral interpretation. Geography,
source domain, diel structure, deployment metadata, and annotation metadata changed
together, while the annotated observation stream fixed detection at 1.

A new dataset is useful only if it breaks that confounding rather than supplying more
records of the same structure.

## Hard requirements before focal response opening

A candidate must provide:

1. a new response dataset not used in E2–E4 or Snapshot Japan;
2. physical location IDs, deployments, effort intervals, event times, taxon IDs, and
   source/protocol metadata;
3. geography and survey/source represented in a crossed or otherwise separable design;
4. an independent information path for effective detection (paired sensors, calibrated
   detection, repeated visits, or another auxiliary observation stream);
5. enough independent physical locations for a strict heldout geographic test;
6. overlapping temporal/day-night exposure;
7. the activity/detection model, including source-or-region × diel and season × diel
   terms, frozen before heldout outcomes.

Camera metadata by itself is not detection identification. A model that simply fixes
annotated detection to one does not qualify.

## Current authorization

Candidate search and response-blind metadata/schema/geometry screening are authorized.
Focal response opening and model fitting are **not** authorized. A selected candidate
requires its own frozen child contract and separate response-opening authorization.
