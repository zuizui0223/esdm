# v0.4 state/activity promotion gate

Status: **FROZEN BEFORE v0.4 outcome-producing validation**

Freeze base: PR #9 head `f0b269c026e944e922fef539505be450a0a72122`.

This gate evaluates whether the implemented v0.4 factorization can recover and transfer
conditional activity and categorical state while preserving the separation between
ecological and observation processes.

Passing this gate is semi-synthetic methodological validation only. It is not empirical
biological validation and it does not create a scientific `Supported` claim.

## Principle

A v0.4 PASS requires all of the following at once:

1. known-detection state/activity targets are structurally identified at every frozen
   positive anchor;
2. those targets are not practically weak under the frozen positive calibration geometry;
3. a deliberately sparse known-detection annotation geometry is refused by the frozen
   practical-identification criterion;
4. an intercept-only activity process observed through unknown global detection is
   structurally refused as `NotIdentified`;
5. known activity/state slopes are recovered across replicated fits;
6. the full model transfers better than explicit activity and state knockouts on held-out
   state-annotated counts under genuine eastness extrapolation;
7. computation remains stable under the frozen MCMC profile.

No one check compensates for failure of another.

## Frozen source and domain

v0.4 reuses the pinned real station geometry already frozen for v0.3.1/v0.3.2:

- source repository: `the-pudding/data`;
- source commit: `3dcb0a80c838ff9503e3957d7e004a7f4b888b0a`;
- source path: `rain/annual_precipitation.csv`;
- source blob SHA1: `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`;
- selected rows: first **120** data rows after the header;
- DOY bins: **15, 75, 135, 195, 255, 315**;
- hour bins: **0, 6, 12, 18**;
- total contexts: **2,880**.

Longitude blocks remain:

- west: longitude `< -110`;
- central: `-110 <= longitude < -85`;
- east: longitude `>= -85`.

Training uses west + central only. East is held out from every fit.

## Frozen covariates and extrapolation rule

Station precipitation, latitude, and longitude are standardized using **training stations
only**:

- `precip_z_train`;
- `lat_z_train`;
- `eastness_z_train`.

The fixture is valid only if

`min(heldout eastness_z_train) > max(training eastness_z_train)`.

This rule is checked before any fit. The held-out east block is therefore outside the
training eastness range.

## Frozen ecological truth

### Ecological intensity

The v0.3.2 ecological intensity truth is retained:

`eta = -2.0 + 0.45*precip_z_train - 0.20*lat_z_train + 0.35*eastness_z_train`.

### Conditional activity

Activity is conditional on ecological availability:

`activity_logit = -0.35 + 0.55*precip_z_train + 0.40*eastness_z_train`.

Thus

`activity = sigmoid(activity_logit)`.

### Conditional categorical state

The frozen state space is:

- reference state: `resting`;
- non-reference state: `foraging`.

The reference-state logit is fixed to zero. The foraging logit is

`state_logit_foraging = 0.20 - 0.50*precip_z_train + 0.45*eastness_z_train`.

The two state probabilities are obtained by softmax over
`(0, state_logit_foraging)`.

## Frozen observation streams

### Broad presence-only stream

A broad `PresenceOnly` stream covers every station with:

- known effort: **5.0** in every context;
- detection probability: **1.0**;
- consumed ecological channel: `log_intensity` only.

Its purpose is to anchor broad ecological intensity independently of activity/state
annotation.

### State-annotated stream

The `StateAnnotatedCount` stream has:

- known effort: **8.0** in annotation-exposed contexts;
- known detection probability: **0.85** for the positive and sparse profiles;
- state labels: `resting`, `foraging`;
- consumed channels: `log_intensity`, `activity`, `state`.

Annotation effort is non-zero at:

1. the frozen training calibration spaces for the profile; and
2. every east held-out space.

East annotations are generated for evaluation but are never included in fitting.

For state `s`:

`lambda_annotated[c,s] = exp(eta[c]) * activity[c] * q[c,s] * 8.0 * 0.85`.

## Frozen positive calibration profile

Select exactly **18 training stations** by eastness-rank quantiles.

Sort training spaces by
`(eastness_z_train, station_id)`, then choose the nearest integer ranks to

`k*(n_train-1)/17`, for `k = 0..17`.

All 24 DOY/hour contexts for those 18 spaces receive annotated effort 8.0.

This selection is deterministic and outcome-independent.

## Frozen sparse practical-refusal profile

The sparse known-detection profile selects exactly **6 training stations** with the
smallest squared standardized distance

`precip_z_train^2 + eastness_z_train^2`,

using station ID as the final tie-breaker.

All 24 temporal contexts for those six spaces receive annotated effort 8.0.

The sparse profile changes only the training annotation geometry. Ecological truth,
activity truth, state truth, broad presence stream, known detection, priors, held-out
geometry, and observation model are otherwise identical to the positive profile.

Required sparse-profile behavior:

- all four frozen state/activity slope targets remain structurally `Identified` at every
  anchor;
- at least one of those four targets is practically weak at every anchor.

If the sparse profile is classified practically strong at any anchor, the refusal control
fails.

## Frozen unknown-detection structural-refusal profile

This profile is separate from the positive/sparse profiles.

It uses:

- the same ecological intensity truth;
- the same state process and positive 18-space annotation geometry;
- **intercept-only activity** with
  `activity_logit = -0.35`;
- `LogitDetection(intercept_parameter="detection_intercept")`;
- nominal detection intercept truth **0.40**.

No independent detection information is supplied.

The following two targets must be structurally `NotIdentified` at every frozen anchor:

- `sp.activity.activity_intercept`;
- `stream.annotated.detection_intercept`.

Posterior contraction or prior regularization may not override this structural result.

## Frozen identification anchors

Positive and sparse known-detection profiles are evaluated at three anchors.

Parameters not listed remain at generating truth.

### Anchor A

Generating truth.

### Anchor B

- activity intercept: `-0.10`;
- activity `beta_precip = 0.75`;
- activity `beta_eastness = 0.20`;
- foraging state intercept: `-0.10`;
- state `beta_precip = -0.25`;
- state `beta_eastness = 0.70`.

### Anchor C

- activity intercept: `-0.70`;
- activity `beta_precip = 0.30`;
- activity `beta_eastness = 0.65`;
- foraging state intercept: `0.50`;
- state `beta_precip = -0.75`;
- state `beta_eastness = 0.20`.

The four frozen identification slope targets are:

- `sp.activity.activity_beta_precip`;
- `sp.activity.activity_beta_eastness`;
- `sp.state.beta_foraging_precip`;
- `sp.state.beta_foraging_eastness`.

Structural identification uses exact `jax.jacfwd` with:

- relative SVD `rtol = 1e-8`;
- absolute `atol = 1e-10`.

A positive-profile target passes structural identification only if it is
`Identified` at all three anchors.

## Frozen practical-identification thresholds

For the same four slope targets, practical identification uses:

- relative minimum singular value `>= 1e-3`;
- condition number `<= 1e3`;
- Fisher-like target SD proxy `<= 0.25`;
- Fisher ridge `1e-10`.

The positive profile requires all four targets to be non-weak at all three anchors.

The sparse profile requires all four targets to remain structurally identified, while at
least one target is practically weak at every anchor.

## Frozen unknown-detection anchors

The structural-refusal profile is checked at three anchors.

### Detection anchor U-A

Generating intercepts:

- activity intercept `-0.35`;
- detection intercept `0.40`.

### Detection anchor U-B

- activity intercept `0.20`;
- detection intercept `-0.30`.

### Detection anchor U-C

- activity intercept `-0.90`;
- detection intercept `0.90`.

All other parameters remain at generating truth.

Both refusal targets must be `NotIdentified` at all three anchors.

## Frozen inference profile

Positive-profile outcome runs use:

- replicated generated datasets: **16**;
- base seed: **20260924**;
- seed stride: **43**;
- chains per fit: **2**, sequential;
- warmup draws per chain: **250**;
- retained draws per chain: **300**;
- target acceptance probability: **0.90**;
- parameter intervals: **90%**.

Every replicate generates the complete broad presence stream and the complete annotated
stream, including east held-out annotations, from the same known truth.

Only west + central data are supplied to fitting.

Each replicate fits three models to exactly the same training data:

1. full model;
2. activity knockout: preserve activity intercept, neutralize activity environmental
   slopes;
3. state knockout: preserve baseline state composition, neutralize state environmental
   slopes.

The intensity process and observation model are unchanged across all three fits.

## Frozen parameter-recovery criteria

Across 16 positive-profile full fits, promotion targets are:

- activity `beta_precip = 0.55`;
- activity `beta_eastness = 0.40`;
- state `beta_foraging_precip = -0.50`;
- state `beta_foraging_eastness = 0.45`.

For each target separately:

- `abs(mean posterior bias) <= 0.15`;
- 90% interval truth coverage `>= 0.75`.

Activity/state intercepts and intensity parameters are recorded but are not v0.4
promotion targets.

## Frozen held-out transfer score

All three fits are evaluated against the same east held-out **state-annotated counts**.

The score is state-specific Poisson log predictive density per state-context:

1. compute posterior Poisson probability for each held-out state count under every draw;
2. average probability over posterior draws;
3. take the log;
4. average over all held-out state-context observations.

Two independent knockout comparisons are required.

### Activity-transfer comparison

`gain_activity = full_score - activity_knockout_score`.

Promotion requires:

- `gain_activity > 0` in at least **75%** of replicates;
- mean `gain_activity >= 0.005` per held-out state-context.

### State-transfer comparison

`gain_state = full_score - state_knockout_score`.

Promotion requires:

- `gain_state > 0` in at least **75%** of replicates;
- mean `gain_state >= 0.005` per held-out state-context.

The east block is never used for fitting, covariate standardization, calibration-space
selection, threshold selection, or model choice.

## Frozen computation criterion

There are **48** positive-profile fits in total: 16 replicates × 3 fits.

Across those fits:

- mean divergences per fit must be `<= 0.10`.

A memory interruption, runner cancellation, missing artifact, source mismatch, or worker
process failure is recorded as `INFRASTRUCTURE_BLOCKED`, not PASS and not scientific
FAIL.

Thresholds, seeds, calibration geometry, or priors may not be changed after an
infrastructure interruption without defining a new gate version.

## Mechanical PASS rule

`v0.4 state/activity promotion = PASS` only if every one of the following is true:

1. positive structural identification passes;
2. positive practical identification passes;
3. sparse structural identification passes;
4. sparse practical refusal passes;
5. unknown-detection structural refusal passes;
6. extrapolation integrity passes;
7. all four recovery-bias checks pass;
8. all four recovery-coverage checks pass;
9. activity-knockout positive-gain rate passes;
10. activity-knockout mean held-out gain passes;
11. state-knockout positive-gain rate passes;
12. state-knockout mean held-out gain passes;
13. divergence criterion passes;
14. exactly 16 valid replicates and 48 valid fits are present.

The gate emits evidence and a mechanical decision only. It does not emit a scientific
`Supported` claim and it does not alter the frozen v0.3.1/v0.3.2 records.
