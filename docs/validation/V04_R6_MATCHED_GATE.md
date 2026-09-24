# v0.4-R6 Matched Resolution Benchmark Gate

Status: **FROZEN BEFORE R6 OUTCOME**

R6 is a matched-model comparison of the promoted full-resolution v0.4 model against a
collapsed low-resolution baseline under two fresh known-truth worlds.

No R5b outcome is reused as an R6 replicate.

## Frozen model classes

### Full

Exact promoted v0.4/R5 model:

- suitability environmental response;
- conditional activity intercept + four environmental slopes;
- conditional state intercept + four environmental slopes;
- all four promoted observation streams.

### Collapsed baseline

Exact same model and streams, but both process knockouts are applied:

- activity baseline intercept retained;
- all activity environmental slopes removed;
- state baseline composition retained;
- all state environmental slopes removed.

Suitability, effort, detection, calibration geometry, priors for shared parameters, and
raw data are identical between candidates.

## Frozen observation/data contract

Both candidates receive exactly the same generated west+central training realization.

Streams:

- opportunistic PresenceOnly;
- calibrated PresenceOnly;
- StateAnnotatedCount;
- StateCompositionCount.

StateCompositionCount remains training-only:

- 432 training contexts;
- label effort = 1.0;
- zero east-heldout exposure.

Held-out scoring uses only the east StateAnnotatedCount resting/foraging blocks.

## Frozen worlds

### Structured

Generating truth = exact promoted R5 truth.

All four activity slopes and all four state slopes retain their non-zero promoted values.

### Resolution null

The same generating model and all same intercepts/observation processes are used, but
exactly these eight environmental slopes are set to zero:

- activity_beta_precip;
- activity_beta_eastness;
- activity_beta_season;
- activity_beta_hour;
- beta_foraging_precip;
- beta_foraging_eastness;
- beta_foraging_season;
- beta_foraging_hour.

No other parameter changes.

## Fresh replication profile

R6 uses a fresh seed family:

- replicates per world = 16;
- worlds = 2;
- fits per replicate = 2;
- total fits = 64;
- base seed = 20260924;
- replicate stride = 61;
- null-world seed offset = 1000000;
- full fit seed = generated-data seed + 1;
- collapsed fit seed = generated-data seed + 2;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

Structured replicate r uses:

`20260924 + 61*r`.

Resolution-null replicate r uses:

`20260924 + 1000000 + 61*r`.

No scientific or MCMC setting is configurable from the command line.

## Frozen estimand

For each replicate:

`resolution_gain = full east StateAnnotatedCount LPD - collapsed east StateAnnotatedCount LPD`.

Both scores are evaluated on the identical held-out realization.

Material gain threshold = **0.005**.

## Structured-world requirements

All must hold:

- replicates = 16;
- proportion with resolution_gain > 0 >= 0.75;
- mean resolution_gain >= 0.005.

## Resolution-null requirements

All must hold:

- replicates = 16;
- mean resolution_gain <= 0.005;
- proportion with resolution_gain > 0.005 <= 0.25.

The null guard is intentionally one-sided. The full model is allowed to lose to the
simpler baseline under a true low-resolution world. It is not allowed to show the same
material superiority claimed in the structured world.

## Divergence requirement

Across all 64 fits:

- total divergences / 64 <= 0.10.

## Mechanical R6 decision

R6 = PASS only if every structured-world, resolution-null, fit-count, and divergence
criterion above passes.

A failed term cannot be repaired inside R6 by changing:

- world definitions;
- model classes;
- seed family;
- replicate count;
- MCMC settings;
- held-out score;
- gain threshold;
- gate thresholds.

## Interpretation boundary

R6 PASS may support:

> The higher-resolution environmental activity/state representation improves held-out
> state-resolved prediction when those gradients generate the data, while the same
> material advantage does not appear when the gradients are absent.

R6 PASS does not establish:

- universal superiority over named SDM or JSDM software;
- empirical biological validity;
- robustness to arbitrary misspecification;
- field cost-effectiveness;
- causal correctness in real systems.
