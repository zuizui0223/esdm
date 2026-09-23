# v0.4-R5a direct state-composition calibration qualification gate

Status: **FROZEN BEFORE R5a IDENTIFICATION OUTCOME**

R5a is an identification-only prospective qualification. It does not promote v0.4 and
contains no posterior-recovery, held-out-transfer, or MCMC criterion.

R2, R3a, and R4a remain frozen results. Their gates, thresholds, anchors, selectors, and
result records are not modified by R5a.

## Scientific hypothesis

R4a showed that a phase-balanced 36-site × 12-time allocation can remove all practical
failures at Anchors A and B while the four state slopes remain practically weak at hard
Anchor C.

R5a therefore stops rearranging the same 432 StateAnnotatedCount context cells.

The prospective hypothesis is:

> direct conditional state-composition calibration supplies state-specific information
> that abundance/activity-weighted annotated counts cannot provide reliably in a hard
> low-information state regime.

## Frozen source and domain

R5a inherits the exact R2/R3a/R4a source and domain:

- repository: the-pudding/data;
- source commit: 3dcb0a80c838ff9503e3957d7e004a7f4b888b0a;
- source path: rain/annual_precipitation.csv;
- source Git blob SHA1: 40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949;
- first 120 data rows;
- DOY values: 15, 75, 135, 195, 255, 315;
- hour values: 0, 6, 12, 18;
- total full-domain contexts: 2,880;
- training block: west + central;
- held-out block: east.

All spatial standardization remains training-only and unchanged.

## Existing positive streams

The first three positive streams are inherited unchanged from R4a.

### Opportunistic PresenceOnly

Unchanged broad west+central coverage with unknown multi-covariate effort and unknown
global detection. It consumes only ecological log intensity.

### Calibrated PresenceOnly

Unchanged:

- 18 frozen spatial maximin sites;
- all 24 temporal contexts;
- 18 × 24 = 432 calibrated contexts;
- known observation process.

### StateAnnotatedCount

Unchanged from R4a:

- exact R3a/R4a 36-site spatial sequence;
- exact R4a 12-context phase-balanced temporal sequence;
- 36 × 12 = 432 positive annotated training contexts;
- effort = 8.0;
- known detection = 0.85;
- consumes ecological intensity, activity, and state.

Held-out east StateAnnotatedCount exposure remains unchanged and is not used in R5a
qualification.

## New direct state-composition calibration stream

R5a adds one and only one positive stream: `state_calibration`.

For exposed context c and state s:

`lambda[c,s] = label_effort[c] × P(state=s | active, available, c)`.

Frozen contract:

- stream class: `StateCompositionCount`;
- target species: `sp`;
- state space: `resting, foraging`;
- consumes exactly `state`;
- informs exactly `state`;
- does not consume ecological intensity;
- does not consume activity;
- has no detection parameter;
- has no free observation parameter;
- uses backend-neutral Poisson observation blocks.

### Frozen calibration geometry

The state-calibration stream is exposed at exactly the same 36 × 12 R4a positive
training contexts and nowhere else.

Its temporal contexts are exactly:

1. (15, 0)
2. (15, 6)
3. (15, 12)
4. (15, 18)
5. (135, 0)
6. (135, 6)
7. (135, 12)
8. (135, 18)
9. (255, 0)
10. (255, 6)
11. (255, 12)
12. (255, 18)

The 36 spatial sites must equal the exact R4a annotated spatial sequence.

### Frozen direct-label effort

`label_effort = 1.0` at every one of the 432 exposed training contexts.

Therefore:

- direct calibration context count = 432;
- total expected direct state labels = 432.0;
- held-out direct-calibration context count = 0.

The value 1.0 is a unit-label prospective design. It is not selected from any R4a
target-SD value or R5a outcome.

## Frozen ecological and observation truth

Every generating coefficient inherited from R4a remains unchanged.

The new state-calibration stream has no free observation-process truth because it has no
free observation parameter.

## Frozen identification target set

The same 13 R2/R3a/R4a targets are required.

Observation separation:

- `sp.suitability.beta_precip`;
- `stream.opportunistic.gamma_precip`;
- `stream.opportunistic.gamma_season`;
- `stream.opportunistic.gamma_hour`;
- `stream.opportunistic.detection_intercept`.

Activity:

- `sp.activity.activity_beta_precip`;
- `sp.activity.activity_beta_eastness`;
- `sp.activity.activity_beta_season`;
- `sp.activity.activity_beta_hour`.

State:

- `sp.state.beta_foraging_precip`;
- `sp.state.beta_foraging_eastness`;
- `sp.state.beta_foraging_season`;
- `sp.state.beta_foraging_hour`.

## Frozen anchors

R5a reuses the exact R2 Anchor A, Anchor B, and Anchor C parameter values.

No anchor is changed, added, removed, or weakened.

## Structural identification threshold

Unchanged:

- exact JAX `jax.jacfwd`;
- rtol = 1e-8;
- atol = 1e-10.

All 13 targets must be structurally `Identified` at all three positive anchors.

## Practical identification threshold

Unchanged:

- relative minimum singular value >= 1e-3;
- condition number <= 1e3;
- target SD proxy <= 0.25;
- Fisher ridge = 1e-10.

All 13 targets must be practically non-weak at all three positive anchors.

No threshold may be relaxed after observing R5a.

## Frozen refusal controls

The new state-calibration stream is not added to either refusal control.

### Sparse practical refusal

The sparse profile remains exactly the frozen R2 sparse design.

Required at all three sparse anchors:

- all 13 targets structurally `Identified`;
- at least one target practically weak.

### Unknown annotated-detection refusal

The unknown annotated-detection profile remains exactly the frozen R2 refusal design.

At all three refusal anchors both:

- `sp.activity.activity_intercept`;
- `stream.annotated.detection_intercept`;

must remain structurally `NotIdentified`.

## Mechanical R5a decision

R5a = PASS only if all twelve required terms are true:

1. positive structural identification passes;
2. positive practical identification passes;
3. sparse structural identification passes;
4. sparse practical refusal passes;
5. unknown annotated-detection refusal passes;
6. existing StateAnnotatedCount training context count = 432;
7. calibrated PresenceOnly training context count = 432;
8. direct state-calibration training context count = 432;
9. total expected direct state labels = 432.0;
10. held-out direct state-calibration context count = 0;
11. exact R4a annotated geometry is preserved;
12. the new stream preserves the state-only, no-free-observation-parameter contract.

R5a contains no MCMC.

## Outcome discipline

The R5a identification outcome may be executed only after this gate is committed and its
Git blob is pinned by the qualification runner.

If R5a FAILS, label effort, calibration geometry, thresholds, anchors, truth, or refusal
controls are not changed within R5.

If R5a PASSES, a separate R5b full recovery and held-out-transfer gate may be frozen
prospectively. R5a PASS alone is not v0.4 promotion.

## Claim boundary

R5a can establish only whether one prospectively fixed direct state-composition
calibration contract passes the semi-synthetic pre-MCMC identification gate.

It cannot establish posterior recovery, transfer, empirical protocol feasibility,
causality, universal optimality, or v0.4 promotion.
