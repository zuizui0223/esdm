# v0.4-R4a phase-balanced temporal qualification gate

Status: **FROZEN BEFORE R4a IDENTIFICATION OUTCOME**

R4a is an identification-only prospective qualification. It does not promote v0.4 and
contains no posterior-recovery, transfer, or MCMC criterion.

R2 and R3a remain frozen FAIL results. Their gates, thresholds, anchors, selectors, and
result records are not modified by R4a.

## Hypothesis

At the exact same positive StateAnnotatedCount budget used by R3a,

36 spatial sites × 12 temporal contexts = 432 annotated context opportunities,

an explicitly phase-balanced temporal Cartesian design may provide stronger practical
separation of activity and state slopes than the R3a joint cyclic maximin temporal design.

The spatial design, total budget, truth, anchors, thresholds, and refusal controls are
unchanged. Only the 12 positive annotated temporal contexts change.

## Frozen source and domain

R4a inherits the exact R2/R3a source and domain:

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

All spatial standardization is training-only and unchanged.

## Frozen observation streams

### Opportunistic PresenceOnly

Unchanged from R2/R3a:

- broad west+central training coverage;
- unknown multi-covariate effort;
- unknown global detection;
- consumes only `log_intensity`.

### Calibrated PresenceOnly

Unchanged from R2/R3a:

- first 18 frozen spatial maximin sites;
- all 24 temporal contexts;
- known effort and detection;
- 18 × 24 = 432 calibrated contexts.

### StateAnnotatedCount

Positive training exposure is frozen at:

- exact R3a 36-site spatial maximin sequence;
- exact 12 R4a temporal contexts declared below;
- 36 × 12 = 432 annotated contexts;
- known effort = 8.0 per exposed context;
- known detection = 0.85.

Held-out east annotations remain exposed on every east site × all 24 temporal contexts and
are not used in R4a qualification.

## Frozen temporal allocation

The R4a temporal design is the Cartesian product of:

- seasonal phases: DOY 15, 135, 255;
- hourly phases: 0, 6, 12, 18.

The exact 12 contexts, in frozen order, are:

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

Each selected DOY therefore occurs four times and each hour occurs three times.

The selector uses declared domain coordinates only. It does not use counts, truth
coefficients, anchor values, Jacobians, singular values, Fisher information, target-SD
values, R2 outcomes, or R3a outcomes.

## Frozen spatial allocation

The 36 annotated sites must be exactly the R3a 36-site spatial maximin sequence, in the
same order. The first 18 must therefore also equal the frozen R2 calibration sequence.

R4a does not reselect or retune space.

## Frozen identification target set

The same 13 targets as R2/R3a are required.

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

R4a reuses the exact R2 Anchor A, Anchor B, and Anchor C parameter values.

No anchor is changed, added, removed, or weakened.

## Structural identification threshold

Unchanged:

- exact JAX `jax.jacfwd`;
- rtol = 1e-8;
- atol = 1e-10.

All 13 targets must be structurally `Identified` at all three anchors.

## Practical identification threshold

Unchanged:

- relative minimum singular value >= 1e-3;
- condition number <= 1e3;
- target SD proxy <= 0.25;
- Fisher ridge = 1e-10.

All 13 targets must be practically non-weak at all three anchors.

No threshold may be relaxed after observing R4a.

## Frozen refusal controls

### Sparse practical refusal

The sparse profile is exactly the frozen R2 sparse design.

Required at all three sparse anchors:

- all 13 targets structurally `Identified`;
- at least one target practically weak.

### Unknown annotated-detection refusal

The unknown annotated-detection profile is exactly the frozen R2 refusal design.

At all three refusal anchors both:

- `sp.activity.activity_intercept`;
- `stream.annotated.detection_intercept`;

must remain structurally `NotIdentified`.

## Mechanical R4a decision

R4a = PASS only if all 13 required terms are true:

1. positive structural identification passes;
2. positive practical identification passes;
3. sparse structural identification passes;
4. sparse practical refusal passes;
5. unknown annotated-detection refusal passes;
6. annotated context count = 432;
7. annotated site count = 36;
8. annotated temporal-context count = 12;
9. calibrated PresenceOnly context count = 432;
10. calibrated PresenceOnly site count = 18;
11. calibrated PresenceOnly temporal-context count = 24;
12. exact R3a 36-site spatial sequence is preserved;
13. exact R4a 3 × 4 phase-balanced temporal sequence is preserved.

R4a contains no MCMC.

## Outcome discipline

The R4a identification outcome may be executed only after this gate is committed and its
Git blob is pinned by the qualification runner.

If R4a FAILS, the result is recorded as-is. The temporal phases, site count, time count,
budget, thresholds, anchors, truth, or refusal controls are not changed within R4.

If R4a PASSES, a separate R4b full recovery/transfer gate may be frozen prospectively.
R4a PASS alone is not v0.4 promotion.

## Claim boundary

R4a can support only a semi-synthetic observation-design qualification statement.

It cannot establish empirical biological validity, universal optimality of factorial
sampling, posterior recovery, held-out transfer, or v0.4 promotion.
