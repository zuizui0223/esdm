# v0.4-R3a budget-neutral qualification gate

Status: **FROZEN BEFORE R3a IDENTIFICATION OUTCOME**

This gate prospectively qualifies one fixed-budget observation design. It does not
promote v0.4 and it contains no posterior-recovery, transfer, or MCMC criterion.

R2 remains a frozen FAIL. Its gate, result, and machine-readable result records are not
modified by R3a.

## Purpose

R2 used 18 state-annotated training sites across all 24 DOY/hour combinations:

18 spatial sites × 24 temporal contexts = 432 state-annotation context opportunities.

R3a keeps the same total state-annotation context budget but redistributes it:

36 spatial sites × 12 temporal contexts = 432 state-annotation context opportunities.

The hypothesis is that practical state-slope precision depends on allocation of a fixed
annotation budget across independent spatial and temporal dimensions.

## Frozen source and domain

R3a inherits the exact R2 source and domain:

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

All spatial standardization remains training-only and unchanged from R2.

## Frozen ecological and observation truth

R3a inherits every R2 generating parameter unchanged.

This includes:

- ecological intensity truth;
- opportunistic PresenceOnly unknown multi-covariate effort;
- opportunistic PresenceOnly unknown global detection;
- calibrated PresenceOnly known observation process;
- activity spatial + temporal truth;
- state spatial + temporal truth;
- annotated-stream known effort and known detection.

No truth coefficient is changed in R3a.

## Stream O: opportunistic PresenceOnly

Unchanged exactly from R2.

Coverage, effort model, detection model, target species, informed process, consumed
channel, priors, and generating values are unchanged.

## Stream C: calibrated PresenceOnly

Unchanged exactly from R2.

The positive calibrated design is:

18 sites × 24 temporal contexts = 432 calibrated PresenceOnly context opportunities.

The 18 sites are the first 18 members of the deterministic spatial maximin sequence
defined below.

All six DOY values and all four hour values are exposed at those 18 sites.

## Stream A: StateAnnotatedCount

Only the positive training geometry changes.

Positive R3a training exposure is:

36 spatial sites × 12 temporal contexts = 432 state-annotation context opportunities.

Held-out east annotations remain generated on every frozen east site × all 24 temporal
contexts, exactly as in R2. They are never used in R3a qualification.

Annotated effort per exposed context remains 8.0.

Annotated detection remains known at probability 0.85.

## Frozen spatial selector

Candidate set = all training spaces.

Each candidate is represented only by:

(precip_z_train, eastness_z_train).

Selection algorithm:

1. Compute radius squared = precip_z_train^2 + eastness_z_train^2.
2. First site = candidate with maximum radius squared.
3. Geometric ties are resolved by station ID.
4. For each remaining candidate, compute its minimum squared Euclidean distance to the
   selected set in the two-dimensional standardized plane.
5. Select the candidate maximizing that minimum distance.
6. Geometric ties are resolved by station ID.
7. Continue until 36 sites are selected.

Floating representations of theoretically equal geometric distances are treated as ties
at 1e-12 distance precision before station-ID tie breaking.

The first 18 selected R3a sites must equal the frozen R2 positive calibration sequence
exactly and in the same order.

No observation count, posterior result, Jacobian, target-SD value, or R2 outcome enters
selection.

## Frozen temporal selector

Candidate set = the 24 declared DOY/hour combinations.

Each candidate is represented only by:

(season_sin, season_cos, hour_sin, hour_cos).

Selection algorithm:

1. Sort candidates lexicographically by (doy, hour).
2. First selected temporal context = (15, 0).
3. For each remaining candidate, compute its minimum squared Euclidean distance to the
   selected set in the four-dimensional cyclic coordinate space.
4. Select the candidate maximizing that minimum distance.
5. Geometric ties are resolved lexicographically by (doy, hour).
6. Continue until exactly 12 temporal contexts are selected.

Floating representations of theoretically equal geometric distances are treated as ties
at 1e-12 distance precision before lexicographic tie breaking.

No outcome or identification diagnostic enters temporal selection.

## Exact R3a budget invariants

The positive fixture must mechanically satisfy all of:

- annotated context count = 432;
- annotated site count = 36;
- annotated temporal-context count = 12;
- calibrated PresenceOnly context count = 432;
- calibrated PresenceOnly site count = 18;
- calibrated PresenceOnly temporal-context count = 24;
- first-18 prefix equality between the R3a 36-site annotated sequence and the frozen R2
  18-site calibration sequence.

Any violation is an R3a qualification FAIL.

## Positive identification targets

R3a reuses the exact 13 R2 identification targets.

Observation separation:

1. sp.suitability.beta_precip
2. stream.opportunistic.gamma_precip
3. stream.opportunistic.gamma_season
4. stream.opportunistic.gamma_hour
5. stream.opportunistic.detection_intercept

Activity:

6. sp.activity.activity_beta_precip
7. sp.activity.activity_beta_eastness
8. sp.activity.activity_beta_season
9. sp.activity.activity_beta_hour

State:

10. sp.state.beta_foraging_precip
11. sp.state.beta_foraging_eastness
12. sp.state.beta_foraging_season
13. sp.state.beta_foraging_hour

All 13 identification targets must pass at all three positive anchors.

## Positive anchors

R3a reuses the exact frozen R2 values for Anchor A, Anchor B, and Anchor C.

### Anchor A

Generating truth exactly as frozen in R2.

### Anchor B

Unchanged from R2:

- ecological beta_precip = 0.70;
- opportunistic gamma_precip = 0.10;
- opportunistic gamma_season = 0.55;
- opportunistic gamma_hour = -0.05;
- opportunistic detection_intercept = -0.70;
- activity intercept = -0.05;
- activity beta_precip = 0.70;
- activity beta_eastness = 0.15;
- activity beta_season = 0.30;
- activity beta_hour = 0.65;
- alpha_foraging = -0.10;
- state beta_precip = -0.20;
- state beta_eastness = 0.65;
- state beta_season = 0.25;
- state beta_hour = -0.70.

### Anchor C

Unchanged from R2:

- ecological beta_precip = 0.20;
- opportunistic gamma_precip = 0.60;
- opportunistic gamma_season = 0.10;
- opportunistic gamma_hour = -0.50;
- opportunistic detection_intercept = 0.35;
- activity intercept = -0.75;
- activity beta_precip = 0.25;
- activity beta_eastness = 0.60;
- activity beta_season = 0.75;
- activity beta_hour = 0.20;
- alpha_foraging = 0.50;
- state beta_precip = -0.70;
- state beta_eastness = 0.20;
- state beta_season = 0.70;
- state beta_hour = -0.20.

## Structural identification

Unchanged exactly from R2:

- exact method: JAX jax.jacfwd;
- rtol = 1e-8;
- atol = 1e-10.

Every one of the 13 positive targets must be structurally Identified at Anchor A,
Anchor B, and Anchor C.

## Practical identification

Unchanged exactly from R2:

- relative minimum singular value >= 1e-3;
- condition number <= 1e3;
- target SD proxy <= 0.25;
- Fisher ridge = 1e-10.

Every one of the 13 positive targets must be practically non-weak at Anchor A,
Anchor B, and Anchor C.

The target SD proxy <= 0.25 criterion is the same frozen criterion that caused the R2
negative result. It is not relaxed in R3a.

## Frozen sparse practical refusal

R3a does not redesign the sparse control.

The sparse practical refusal profile is exactly the frozen R2 sparse profile:

- the same four training sites minimizing
  precip_z_train^2 + eastness_z_train^2 with station-ID tie break;
- calibrated PresenceOnly exposure at those four sites × all 24 temporal contexts;
- StateAnnotatedCount exposure at those four sites × all 24 temporal contexts;
- unchanged R2 truth;
- unchanged R2 anchors;
- unchanged structural and practical thresholds.

Required sparse behavior:

- all 13 targets structurally Identified at all three sparse anchors;
- at least one target practically weak at every sparse anchor.

## Frozen unknown annotated-detection refusal

R3a does not redesign this control.

The unknown annotated-detection refusal is exactly the frozen R2 refusal profile:

- intercept-only activity;
- unknown annotated-stream LogitDetection;
- no independent detection information for the annotated stream;
- same R2 three refusal anchors.

Both targets:

- sp.activity.activity_intercept;
- stream.annotated.detection_intercept;

must remain structurally NotIdentified at all three anchors.

## R3a contains no MCMC

R3a contains no MCMC recovery benchmark.

R3a does not evaluate:

- posterior recovery bias;
- posterior interval coverage;
- held-out activity-knockout transfer;
- held-out state-knockout transfer;
- divergence rate.

Those are eligible only for a separately frozen R3b gate after an R3a PASS.

## Mechanical PASS rule

R3a qualification has exactly 10 required terms:

1. positive_structural_pass is true;
2. positive_practical_pass is true;
3. sparse_structural_pass is true;
4. sparse_practical_refused is true;
5. unknown_detection_refused is true;
6. annotated context count = 432;
7. annotated site count = 36;
8. annotated temporal-context count = 12;
9. calibrated PresenceOnly context count = 432;
10. first-18 prefix equality is true.

R3a = PASS only if all 10 terms pass.

## Outcome discipline

The R3a identification outcome may be executed only after this gate document is committed
and its exact blob is verified stable.

No threshold, selector, target, anchor, truth, refusal profile, site count, time count,
or PASS rule may be changed in response to the R3a outcome.

If R3a FAILS, R3 stops and R3b is not created.

If R3a PASSES, that result qualifies only this exact 36 × 12 design for a separately
frozen R3b outcome gate.

R3a PASS is not v0.4 promotion and is not empirical biological validation.
