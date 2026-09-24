# v0.4-R6 Matched Resolution Benchmark Design

Status: **approved prospective design, pre-outcome**

Base: promoted v0.4 head `3320431b300f34b326363713fb1d993ea5e43a87`.

R6 is the first matched-model comparison after the internal v0.4 promotion programme.
It does not add a new ecological process.

## Scientific question

R5b showed that the full state/activity model recovers its generating parameters and
transfers information to an east held-out block. That alone does not prove that the added
ecological resolution is preferable to a simpler representation.

R6 asks:

> Does environmental state/activity resolution improve held-out state-resolved prediction
> when those gradients truly exist, without producing the same apparent advantage when
> those gradients are absent?

## Matched model classes

Both candidates use the exact same four observation streams, training contexts, effort,
detection model, covariates, priors for shared parameters, and east-heldout evaluation.

### Full resolution

The promoted R5 model:

- suitability environmental response;
- conditional activity intercept + environmental slopes;
- conditional state intercept/composition + environmental slopes.

### Collapsed resolution baseline

The exact same model after applying both frozen knockouts:

- activity knockout preserves the baseline activity intercept but removes all activity
  environmental slopes;
- state knockout preserves the baseline state composition but removes all state
  environmental slopes;
- suitability and every observation stream remain unchanged.

The baseline therefore remains capable of ingesting StateAnnotatedCount and
StateCompositionCount. It differs only in whether environmental variation is represented
inside activity/state.

This is a low-resolution matched baseline, not a claim that it reproduces every SDM or
JSDM implementation.

## Fresh known-truth worlds

R6 uses new random seeds not used by R5b.

### Structured world

Generating truth = exact promoted R5 truth.

Activity and state environmental slopes are non-zero.

Prediction: the full-resolution model should beat the collapsed baseline on east-heldout
StateAnnotatedCount log predictive density.

### Resolution-null world

All eight environmental activity/state slopes are set exactly to zero in the generating
truth:

- four activity slopes = 0;
- four state slopes = 0.

All intercepts, suitability, observation effort/detection, geometry, and streams remain
the same.

Both candidate model classes can represent this world. The full model has extra
environmental slope freedom but no generating advantage.

Prediction: the full model must not reproduce the same material held-out advantage under
this null.

## Data equality

Within each replicate:

1. generate one dataset once;
2. fit Full and Collapsed to the identical west+central training realization;
3. evaluate both on the identical east-heldout StateAnnotatedCount realization.

StateCompositionCount remains training-only and has zero east-heldout exposure.

No model receives extra observations.

## Frozen replication/MCMC profile

Planned frozen profile:

- 16 replicates per world;
- 2 worlds;
- 2 fits per replicate;
- 64 total fits;
- base seed = 20260924;
- seed stride = 61;
- null-world seed offset = 1,000,000;
- full fit seed = replicate seed + 1;
- collapsed fit seed = replicate seed + 2;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

## Primary estimand

For each replicate:

`resolution_gain = full east state-resolved LPD - collapsed east state-resolved LPD`.

The held-out score uses only StateAnnotatedCount resting/foraging blocks, exactly as R5b.

## Planned gate logic

Structured world:

- positive resolution_gain in >= 75% of replicates;
- mean resolution_gain >= 0.005.

Resolution-null world:

- mean resolution_gain <= 0.005;
- proportion with resolution_gain > 0.005 <= 25%.

The null guard is deliberately one-sided. A simpler baseline may outperform the full
model under a true low-resolution world; R6 only forbids claiming an ESDM advantage when
the generating gradients are absent.

Across all 64 fits:

- mean divergences per fit <= 0.10.

## Interpretation boundary

A PASS can support:

- conditional predictive superiority of the higher-resolution representation in the
  declared structured world;
- absence of the same material advantage under the declared resolution-null world.

It cannot support:

- universal superiority over named SDM/JSDM implementations;
- empirical biological validity;
- superiority under arbitrary misspecification;
- field cost-effectiveness of direct calibration.
