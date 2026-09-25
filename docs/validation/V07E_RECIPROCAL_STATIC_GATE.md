# v0.7e Reciprocal Static-World Specificity Gate

Status: **FROZEN AFTER PRE-OUTCOME QUALIFICATION, BEFORE HELD-OUT OUTCOME**

Date frozen: 2026-09-25

## Scientific question

Is the v0.7 dynamic-resolution result genuinely resolution-specific, or does the
benchmark machinery structurally favor the recursive dynamic model regardless of the
data-generating process?

v0.7d established that the recursive model beats an equal-dimension quadratic
memoryless occupancy model when the generating world is recursive. v0.7e reverses only
the generator and requires the reciprocal result.

## Frozen static generator

The data-generating occupancy process is exactly the equal-dimension v0.7d static
quadratic comparator:

    psi_c = logistic(
        occupancy_intercept
        + beta_time * time_c
        + beta_time2 * time_c^2
    )

Frozen truth:

- suitability intercept alpha = 0.30;
- occupancy intercept = -0.50;
- linear time slope = +1.50;
- quadratic time slope = +0.25.

Time remains frozen to the same linear scale from -1 at context 1 to +1 at context 12.

The generator has no dependence on previous occupancy.

## Frozen candidate models

The two fitted candidate models are exactly the same equal-dimension pair used in v0.7d.

Dynamic:

- suitability intercept;
- initial occupancy logit;
- colonization logit;
- extinction logit;
- four ecological parameters total;
- recursive previous-state dependence.

Static quadratic:

- suitability intercept;
- occupancy intercept;
- linear time slope;
- quadratic time slope;
- four ecological parameters total;
- memoryless context-wise occupancy.

The model classes, priors, and parameter counts are not changed for v0.7e.

## Frozen information split

For both candidates:

- joint occurrence is generated at contexts 1-12;
- joint occurrence is exposed for fitting at contexts 1-8 only;
- direct OccupancyCount is exposed at contexts 1-4 only;
- contexts 9-12 are used only for joint-occurrence scoring;
- direct occupancy exposure in contexts 9-12 is exactly zero.

Both models are fit to the same generated realization in every replicate.

## Frozen pre-outcome qualification

The candidate-model identification qualification is inherited unchanged from v0.7d.

Both candidates must remain:

- exact-JAX structurally Identified;
- practically non-weak under the frozen threshold;
- target-SD proxy <= 0.25 for every declared free parameter.

Exact-JAX settings:

- rank rtol = 1e-8;
- rank atol = 1e-10.

Practical settings:

- relative minimum singular value threshold = 1e-3;
- condition number threshold = 1e3;
- target-SD threshold = 0.25;
- Fisher ridge = 1e-10.

The ordinary pre-freeze CI passed before this gate was frozen.

## Frozen replicated outcome

Only after qualification passes:

- replicates = 16;
- paired dynamic/static fits per replicate;
- total fits = 32;
- base seed = 20261209;
- seed stride = 167;
- dynamic fit seed = data seed + 1;
- static fit seed = data seed + 2;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

No scientific or MCMC setting is configurable from the command line.

## Frozen primary comparison

For each replicate, both models are scored on the same held-out joint occurrence counts
from contexts 9-12.

Define:

    gain = static held-out mean log predictive density
           - dynamic held-out mean log predictive density

Primary criteria:

- static > dynamic in at least 14/16 replicates, i.e. rate >= 0.875;
- mean static-minus-dynamic gain >= +0.50 nats per held-out context.

The minimum replicate gain is reported descriptively but is not a pass/fail criterion.

These thresholds are deliberately symmetric with v0.7d.

## Frozen sampling criterion

Across all 32 fits:

- divergences / fit <= 0.10.

## Mechanical decision

v0.7e = PASS only if every frozen qualification, reciprocal predictive, and sampling
criterion passes.

No failed criterion may be repaired inside v0.7e by changing:

- static generator truth;
- candidate model forms;
- time or quadratic-time covariates;
- training/held-out split;
- observation effort;
- seed family;
- MCMC profile;
- qualification thresholds;
- predictive thresholds.

## Interpretation boundary

PASS may support:

> The matched benchmark is resolution-specific rather than intrinsically biased toward
> the recursive model: recursive truth favors the dynamic representation, whereas
> memoryless quadratic truth favors the memoryless representation under the same
> observation programme and equal parameter count.

Combined with v0.7d, PASS would establish **bidirectional model-resolution
discrimination** in the frozen semi-synthetic programme.

PASS would not establish:

- universal model-selection consistency outside the frozen worlds;
- realized binary occupancy histories;
- directly observed colonization or extinction events;
- movement or dispersal kernels;
- resistance or path connectivity;
- source-sink or rescue dynamics;
- causal movement limitation;
- empirical biological validity.
