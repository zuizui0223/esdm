# v0.3.2 separation-hardening promotion gate

Status: **FROZEN BEFORE v0.3.2 Gate F-prime outcomes**

This gate does not rewrite or reinterpret the frozen v0.3.1 record. It adds a harder
pre-v0.4 requirement: esdm must separate ecological and observation processes when effort
is unknown, calibration coverage is partial, and transfer requires genuine covariate
extrapolation. Passing this gate is still semi-synthetic validation, not empirical proof.

## Principle

A v0.3.2 PASS requires all of the following at once:

1. the ecological and effort parameters are structurally identified under exact JAX
   Jacobians at every frozen anchor;
2. they are not practically weak under the frozen singular-value/Fisher diagnostics;
3. known ecological and effort coefficients are recovered across replicated fits;
4. held-out prediction improves over the neutral-suitability knockout under a real
   extrapolation split;
5. a deliberately weak calibration geometry is refused by the practical-identification
   criterion even when structural identification remains possible.

No one condition compensates for failure of another. No `Supported` claim is emitted by
this gate.

## Frozen source and domain

Gate F-prime reuses the v0.3.1 pinned real station geometry without changing source rows:

- source repository: `the-pudding/data`;
- source commit: `3dcb0a80c838ff9503e3957d7e004a7f4b888b0a`;
- source path: `rain/annual_precipitation.csv`;
- source blob SHA: `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`;
- station selection: first **120** data rows after the header;
- DOY bins: **15, 75, 135, 195, 255, 315**;
- hour bins: **0, 6, 12, 18**;
- total contexts: **2,880**.

Longitude blocks are unchanged:

- west: longitude `< -110`;
- central: `-110 <= longitude < -85`;
- east: longitude `>= -85`.

Training uses west + central. East is held out from every fit.

## Frozen covariates and extrapolation rule

Station-level precipitation, latitude, and longitude are standardized using **training
stations only**. The resulting ecological covariates are:

- `precip_z_train`;
- `lat_z_train`;
- `eastness_z_train` (standardized longitude; larger means farther east).

The east held-out block must satisfy the deterministic integrity condition

`min(heldout eastness_z_train) > max(training eastness_z_train)`.

If that inequality does not hold exactly, the fixture is invalid and Gate F-prime cannot
run. This makes the eastness term a true range extrapolation rather than interpolation.

## Frozen data-generating truth

Ecological log intensity is

`eta = -2.0 + 0.45*precip_z_train - 0.20*lat_z_train + 0.35*eastness_z_train`.

The opportunistic stream observes the same ecological field with unknown effort

`effort_opp = 4.0 * exp(gamma_precip * precip_z_train)`

with frozen truth

`gamma_precip = 0.40`.

Thus the opportunistic stream alone contains deliberate ecological/observation
confounding along precipitation.

A second calibrated stream has known effort **3.0** at its selected calibration spaces
and zero effort elsewhere. It uses the same ecological field and targets the same species.
The calibrated stream is therefore spatially partial by construction.

## Frozen positive and negative calibration profiles

### Positive profile

Select **12 training stations** by precipitation-rank quantiles. Sort training stations by
`precip_z_train`, then choose the nearest integer ranks to

`k*(n_train-1)/11`, for `k = 0..11`.

All 24 DOY/hour contexts for those 12 spaces receive calibrated effort 3.0. This selection
is deterministic and outcome-independent.

### Negative profile

Select exactly **one training station** whose absolute `precip_z_train` is minimal, with
station ID as the tie-breaker. All 24 DOY/hour contexts for that one space receive
calibrated effort 3.0; calibrated effort is zero elsewhere.

The negative profile changes only calibration geometry. Ecological truth, opportunistic
effort truth, domain, priors, and observation model are otherwise identical to the
positive profile.

## Frozen identification anchors

Both `sp.suitability.beta_precip` and `stream.opportunistic.gamma_precip` are checked at
three predeclared anchors. Parameters not listed below remain at generating truth.

- anchor A: generating truth;
- anchor B: ecological intercept `-1.7`, `beta_precip = 0.70`,
  `gamma_precip = 0.15`;
- anchor C: ecological intercept `-2.3`, `beta_precip = 0.20`,
  `gamma_precip = 0.65`.

Structural identification uses `jax.jacfwd` with relative SVD rank, `rtol = 1e-8` and
`atol = 1e-10`. A target passes structural identification only if it is `Identified` at
all three anchors.

Practical identification uses the exact Jacobian with frozen thresholds:

- relative minimum singular value `>= 1e-3`;
- condition number `<= 1e3`;
- Fisher-like target SD proxy `<= 0.20`;
- Fisher ridge `1e-10`.

For the positive profile, both precipitation targets must be non-weak at all three
anchors. For the negative profile, both targets must remain structurally identified, but
**at least one precipitation target must be practically weak at every anchor**. If the
negative profile is classified as practically strong, the gate fails because the refusal
control is not discriminating.

## Frozen inference profile

Positive-profile outcome runs use:

- replicated generated datasets: **20**;
- base seed: **20260922**;
- chains per fit: **2**, sequential;
- warmup draws per chain: **250**;
- retained draws per chain: **300**;
- target acceptance probability: **0.90**;
- parameter intervals: **90%**.

Every replicate generates both streams from the same known ecological field, then fits
both streams jointly on west + central only.

Each replicate also fits the neutral-suitability comparator. The comparator preserves the
ecological intercept and the entire observation model, including the unknown
`gamma_precip`; only ecological environmental slopes are neutralized.

## Frozen parameter-recovery criteria

Across the 20 positive-profile replicates:

- `abs(mean posterior bias) <= 0.15` for `beta_precip = 0.45`;
- `abs(mean posterior bias) <= 0.15` for `gamma_precip = 0.40`;
- `abs(mean posterior bias) <= 0.15` for `beta_eastness = 0.35`;
- 90% interval truth coverage `>= 0.75` separately for all three parameters.

Intercept and `beta_lat` are recorded but are not promotion targets.

## Frozen held-out transfer criteria

The full and neutral-knockout fits are evaluated on the same east held-out counts. The
score is Poisson log predictive density per context: posterior Poisson probabilities are
averaged over posterior draws before taking the log, then context scores are averaged.

Promotion requires:

- positive full-minus-knockout held-out gain in at least **80%** of replicates;
- mean full-minus-knockout held-out gain `>= 0.01` per context.

The held-out east block is never used for fitting, parameter standardization, calibration
space selection, threshold selection, or model choice.

## Frozen computation criterion

Across all positive-profile full and knockout fits, mean divergences per fit must be
`<= 0.10`.

A memory interruption, runner cancellation, or missing artifact is recorded as
`INFRASTRUCTURE_BLOCKED`, not PASS and not scientific FAIL. Thresholds may not be changed
after such an interruption without defining a new gate version.

## Mechanical PASS rule

`v0.3.2 Gate F-prime = PASS` only if every positive-profile structural, practical,
recovery, extrapolation, held-out gain, and computation check passes **and** the negative
profile is refused by the frozen practical-identification criterion.

The gate produces evidence objects and a mechanical decision only. It does not create a
scientific `Supported` claim or change the frozen v0.3.1 PASS record.
