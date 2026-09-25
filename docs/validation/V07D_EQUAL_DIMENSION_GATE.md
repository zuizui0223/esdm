# v0.7d Equal-Dimension Static-versus-Dynamic Occupancy Gate

Status: **FROZEN AFTER PRE-OUTCOME QUALIFICATION, BEFORE HELD-OUT OUTCOME**

Date frozen: 2026-09-25

## Scientific question

Does the late-time predictive advantage of the v0.7 recursive colonization/extinction
representation persist when the memoryless occupancy comparator has the **same number of
free ecological parameters** and receives the same observations?

v0.7c established an advantage over a three-parameter linear-time static occupancy model.
v0.7d removes the remaining parameter-count explanation.

## Frozen generator

The data-generating world is exactly the frozen v0.7b marginal dynamic world:

- one spatial trajectory;
- 12 ordered contexts;
- suitability intercept alpha = 0.30;
- initial occupancy psi0 = 0.20;
- colonization probability gamma = 0.35;
- extinction probability epsilon = 0.15;
- joint-occurrence effort = 500;
- direct-occupancy effort = 500.

The generator is unchanged from v0.7b/v0.7c.

## Frozen information split

For both fitted models:

- joint occurrence is generated at contexts 1-12;
- joint occurrence is exposed for fitting at contexts 1-8 only;
- direct OccupancyCount is exposed at contexts 1-4 only;
- contexts 9-12 are used only for joint-occurrence scoring;
- direct occupancy exposure in contexts 9-12 is exactly zero.

Both models are fit to the same realization in each replicate.

## Frozen equal-dimension candidate models

### Dynamic

Four ecological parameters:

- suitability intercept alpha;
- initial occupancy logit;
- colonization logit;
- extinction logit.

Occupancy is recursively propagated across the full trajectory.

### Static quadratic

Four ecological parameters:

- suitability intercept alpha;
- occupancy intercept;
- occupancy linear time slope;
- occupancy quadratic time slope.

The occupancy model is memoryless:

    psi_c = logistic(
        occupancy_intercept
        + beta_time * time_c
        + beta_time2 * time_c^2
    )

where time is frozen to a linear scale from -1 at context 1 to +1 at context 12.

Each context is evaluated independently. Previous occupancy is never an input.

Thus both models contain exactly four free ecological parameters. Parameter count cannot
explain a positive dynamic result.

## Frozen pre-outcome qualification

Both models must be structurally and practically estimable before replicated held-out
fitting is authorized.

Exact-JAX structural settings:

- rank rtol = 1e-8;
- rank atol = 1e-10.

Practical settings:

- relative minimum singular value threshold = 1e-3;
- condition number threshold = 1e3;
- target-SD threshold = 0.25;
- Fisher ridge = 1e-10.

Dynamic qualification reuses the frozen v0.7b positive identification contract.

Static qualification is evaluated at the pre-outcome nominal point:

- alpha = 0.30;
- occupancy intercept = -0.50;
- linear time slope = +1.50;
- quadratic time slope = +0.25.

All declared free targets in both models must be structurally Identified and practically
non-weak. If either model fails qualification, replicated MCMC must not run.

The pre-freeze ordinary CI confirmed this qualification on Python 3.12 before this gate
was frozen.

## Frozen replicated outcome

Only after qualification passes:

- replicates = 16;
- paired dynamic/static fits per replicate;
- total fits = 32;
- base seed = 20261201;
- seed stride = 163;
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

    gain = dynamic held-out mean log predictive density
           - equal-dimension static held-out mean log predictive density

Primary criteria:

- dynamic > static in at least 14/16 replicates, i.e. rate >= 0.875;
- mean dynamic-minus-static gain >= +0.50 nats per held-out context.

The minimum replicate gain is reported descriptively but is not a pass/fail criterion.

## Frozen sampling criterion

Across all 32 fits:

- divergences / fit <= 0.10.

## Mechanical decision

v0.7d = PASS only if every frozen qualification, paired predictive, and sampling criterion
passes.

No failed criterion may be repaired inside v0.7d by changing:

- generator truth;
- time or quadratic-time covariates;
- either model form;
- training/held-out split;
- observation effort;
- seed family;
- MCMC profile;
- qualification thresholds;
- predictive thresholds.

## Interpretation boundary

PASS may support:

> Under the frozen marginal dynamic world and the same observation programme, recursive
> occupancy dynamics carried late-time predictive information beyond an equally
> parameterized memoryless quadratic occupancy trend.

PASS would rule out the simple explanation that the v0.7c advantage arose only because
the dynamic model had one additional free ecological parameter.

PASS would not establish:

- universal superiority of dynamic occupancy models;
- realized binary occupancy histories;
- directly observed colonization or extinction events;
- movement or dispersal kernels;
- resistance or path connectivity;
- source-sink or rescue dynamics;
- causal movement limitation;
- empirical biological validity.

A biological or movement claim requires additional empirical/process-specific evidence.
