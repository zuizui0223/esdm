# v0.4 promotion gate R2 — pre-outcome amendment 1

Status: **FROZEN BEFORE ANY R2 OUTCOME-PRODUCING RUN**

This amendment is part of the canonical R2 gate together with
`V04_PROMOTION_GATE_R2.md`.

No R2 outcome-producing workflow has been authorized or executed. The issue was found
while implementing the structural negative-control fixture, before any R2 fitted outcome,
replicate summary, artifact, PASS/FAIL result, or threshold-dependent result was viewed.

## Reason for amendment

The original R2 section "Frozen no-presence-calibration refusal" removed only the
calibrated presence stream while retaining the annotated streams.

That does not isolate the intended exact presence-effort confounding because every
`StateAnnotatedCount` rate also contains `exp(log_intensity)`. The annotated streams
can therefore provide independent information about the seasonal ecological-intensity
coefficient even when calibrated presence is absent.

## Replacement negative control

Replace the original "Frozen no-presence-calibration refusal" section with the following
independent structural-refusal submodel.

### Frozen presence-effort refusal submodel

Use the same:

- 120-station geometry;
- west+central training domain;
- training-only standardized spatial covariates;
- temporal covariates;
- ecological intensity truth;
- opportunistic presence effort truth;
- three positive anchor values for `beta_season` and
  `gamma_presence_season`.

The refusal submodel contains only:

1. the `LinearSuitability` ecological-intensity process;
2. the `presence_opportunistic` stream with unknown
   `gamma_presence_season`.

It contains no calibrated presence stream, no activity/state processes, and no annotated
streams.

At all three frozen positive anchor values:

- `sp.suitability.beta_season`;
- `stream.presence_opportunistic.gamma_presence_season`

must both be structurally `NotIdentified` under exact `jax.jacfwd`,
`rtol=1e-8`, `atol=1e-10`.

This submodel is a diagnostic refusal control only. It is not used for outcome MCMC or
held-out transfer scoring.

## Unchanged R2 conditions

All positive-profile streams, truths, temporal effects, calibration geometries,
identification/practical thresholds, activity/detection refusal, MCMC settings, recovery
thresholds, held-out transfer criteria, divergence threshold, seeds, and PASS conjunction
remain exactly as frozen in `V04_PROMOTION_GATE_R2.md`.
