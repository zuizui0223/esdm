# v0.7e Reciprocal Static-World Specificity Gate

Status: **FROZEN AFTER PRE-OUTCOME QUALIFICATION, BEFORE HELD-OUT OUTCOME**

Date frozen: 2026-09-25

## Scientific question

Does the v0.7 model comparison behave reciprocally when the data-generating world is
memoryless rather than recursive?

v0.7d showed that the four-parameter recursive dynamic model beats an equally
parameterized four-parameter static quadratic occupancy model when the generator is
dynamic. v0.7e reverses only the generator. If the benchmark is resolution-specific
rather than structurally biased toward the dynamic candidate, the static model should
win when the world itself is static.

## Frozen static generator

The generator is exactly the v0.7d equal-dimension static quadratic occupancy model:

- suitability intercept alpha = 0.30;
- occupancy intercept = -0.50;
- linear time slope beta_time = +1.50;
- quadratic time slope beta_time2 = +0.25;
- occupancy is memoryless across contexts;
- time runs linearly from -1 at context 1 to +1 at context 12.

No recursive previous-occupancy term is present in the generator.

## Frozen observation programme

Exactly the v0.7d programme:

- 12 ordered contexts;
- joint occurrence generated at contexts 1-12;
- joint occurrence exposed for fitting at contexts 1-8 only;
- direct OccupancyCount exposed at contexts 1-4 only;
- held-out joint scoring at contexts 9-12;
- direct occupancy exposure at contexts 9-12 = zero.

Both fitted candidates see the same realization within each replicate.

## Frozen equal-dimension fitted candidates

Dynamic candidate, four ecological parameters:

- suitability intercept alpha;
- initial occupancy logit;
- colonization logit;
- extinction logit;
- recursive occupancy dependence.

Static candidate, four ecological parameters:

- suitability intercept alpha;
- occupancy intercept;
- linear time slope;
- quadratic time slope;
- memoryless occupancy.

Parameter count is exactly matched at 4 versus 4.

## Frozen pre-outcome qualification

The fitted candidates are exactly those already qualified in v0.7d.

Required for both candidates:

- exact-JAX structural status = Identified for every free target;
- practical diagnostic not weak;
- relative minimum singular value >= 1e-3;
- condition number <= 1e3;
- target-SD proxy <= 0.25.

Structural rank settings:

- rtol = 1e-8;
- atol = 1e-10;
- Fisher ridge = 1e-10.

If either fitted candidate fails qualification, replicated outcome is not authorized.

## Frozen replicated outcome

Only after qualification passes:

- replicates = 16;
- paired Dynamic + Static fits per replicate;
- total fits = 32;
- base seed = 20261217;
- seed stride = 173;
- Dynamic fit seed = data seed + 1;
- Static fit seed = data seed + 2;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

No scientific or MCMC setting is configurable from the command line.

## Frozen reciprocal predictive comparison

For every replicate both candidates are scored on the same held-out joint occurrence
counts at contexts 9-12.

Define static_gain = Static held-out mean log predictive density minus Dynamic held-out
mean log predictive density.

Primary criteria:

- Static > Dynamic in at least 14/16 replicates, rate >= 0.875;
- mean Static-minus-Dynamic gain >= +0.50 nats per held-out context.

The minimum replicate gain is descriptive only.

These thresholds are exactly the v0.7d thresholds with the scientific direction
reversed.

## Frozen sampling criterion

Across all 32 fits:

- divergences per fit <= 0.10.

## Mechanical decision

v0.7e = PASS only if every qualification, reciprocal predictive, and sampling
criterion passes.

No failed criterion may be repaired inside v0.7e by changing:

- generator truth;
- candidate models;
- parameter count;
- training/held-out split;
- direct occupancy exposure;
- time or time-squared covariates;
- seed family;
- MCMC profile;
- qualification thresholds;
- predictive thresholds.

## Interpretation boundary

PASS may support:

> Under the frozen memoryless quadratic occupancy world and the same observation
> programme, the equally parameterized static representation predicts later occurrence
> better than the recursive dynamic representation.

Together with v0.7d, PASS would support reciprocal model-resolution specificity:
dynamic wins in a dynamic world, while static wins in a static world.

PASS does not establish:

- universal superiority of either occupancy representation;
- model selection guarantees outside the frozen world family;
- realized binary occupancy histories;
- observed colonization/extinction events;
- movement or dispersal kernels;
- resistance, connectivity, source-sink, or rescue dynamics;
- causal movement limitation;
- empirical biological validity.
