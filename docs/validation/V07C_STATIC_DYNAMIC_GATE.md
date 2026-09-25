# v0.7c Matched Static-versus-Dynamic Occupancy Gate

Status: **FROZEN BEFORE QUALIFICATION OR HELD-OUT OUTCOME**

Date frozen: 2026-09-25

## Scientific question

Does the recursive colonization/extinction representation add late-time predictive
information beyond a lower-resolution memoryless occupancy trend when both models receive
the same occurrence records and the same direct occupancy calibration?

This is the first v0.7 benchmark in which the reference model still contains an explicit
occupancy process. Passing v0.7b against the occupancy knockout is not sufficient for this
claim.

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

The generator is not changed to favor the static comparator or to create a new dynamic
regime.

## Frozen information split

For both fitted models:

- joint occurrence is generated at contexts 1-12;
- joint occurrence is exposed for fitting at contexts 1-8 only;
- direct OccupancyCount is exposed at contexts 1-4 only;
- contexts 9-12 are used only for joint-occurrence scoring;
- direct occupancy exposure in contexts 9-12 is exactly zero.

Both models are fit to the same realization in every replicate.

## Frozen candidate models

### Dynamic

The v0.7 colonization/extinction model has four ecological parameters:

- suitability intercept alpha;
- initial occupancy logit;
- colonization logit;
- extinction logit.

Occupancy is recursively propagated across the full trajectory.

### Static

The matched lower-resolution comparator is memoryless:

    psi_c = logistic(occupancy_intercept + beta_time * time_c)

where time is fixed before outcome to a linear scale from -1 at context 1 to +1 at
context 12.

The static model has three ecological parameters:

- suitability intercept alpha;
- occupancy intercept;
- occupancy time slope.

Each context is evaluated independently. Previous occupancy is not an input.

The static model therefore has fewer free parameters than the dynamic model. v0.7c does
not give the comparator extra flexibility in order to manufacture a negative dynamic
result, nor does it give the dynamic model a parameter-count advantage.

## Frozen pre-outcome qualification

Both models must be structurally and practically estimable under their training
observation design before replicated held-out fitting is allowed.

Exact-JAX structural settings:

- rank rtol = 1e-8;
- rank atol = 1e-10.

Practical settings:

- relative minimum singular value threshold = 1e-3;
- condition number threshold = 1e3;
- target-SD threshold = 0.25;
- Fisher ridge = 1e-10.

Dynamic qualification reuses the already frozen v0.7b positive identification contract.

Static qualification is evaluated at the pre-outcome nominal point:

- alpha = 0.30;
- occupancy intercept = -0.50;
- time slope = +1.50.

All declared free targets in both models must be structurally Identified and practically
non-weak. If either model fails qualification, replicated MCMC must not run.

## Frozen replicated outcome

Only after qualification passes:

- replicates = 16;
- paired dynamic/static fits per replicate;
- total fits = 32;
- base seed = 20261123;
- seed stride = 157;
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
           - static held-out mean log predictive density

Primary criteria:

- dynamic > static in at least 14/16 replicates, i.e. rate >= 0.875;
- mean dynamic-minus-static gain >= +0.50 nats per held-out context.

The minimum replicate gain is reported descriptively but is not a pass/fail criterion.

## Frozen sampling criterion

Across all 32 fits:

- divergences / fit <= 0.10.

## Mechanical decision

v0.7c = PASS only if every frozen qualification, paired predictive, and sampling criterion
passes.

No failed criterion may be repaired inside v0.7c by changing:

- generator truth;
- time covariate;
- model forms;
- training/held-out split;
- observation effort;
- seed family;
- MCMC profile;
- qualification thresholds;
- predictive thresholds.

## Interpretation boundary

PASS may support:

> Under the frozen marginal dynamic world and the same observation programme, recursive
> occupancy dynamics carried late-time predictive information beyond a simpler memoryless
> linear occupancy trend.

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
