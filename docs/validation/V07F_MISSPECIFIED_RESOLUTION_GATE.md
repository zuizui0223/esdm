# v0.7f Out-of-Family Temporal-Resolution Robustness Gate

Status: **FROZEN BEFORE HELD-OUT OUTCOME**

Date frozen: 2026-09-25

## Scientific question

Does the bidirectional temporal-resolution discrimination established by v0.7d/v0.7e
persist when neither fitted candidate is the exact data-generating model?

This gate moves from exact candidate-class recovery to mild model misspecification while
keeping the fitted candidates, parameter count, observation programme, and held-out
scoring rule fixed.

## Frozen fitted candidates

The fitted models are exactly the v0.7d/v0.7e equal-dimension pair.

Dynamic candidate:

- suitability intercept alpha;
- initial occupancy logit;
- constant colonization logit;
- constant extinction logit;
- four ecological parameters total;
- recursive previous-state dependence.

Static candidate:

- suitability intercept alpha;
- occupancy intercept;
- linear time slope;
- quadratic time slope;
- four ecological parameters total;
- memoryless context-wise occupancy.

Both candidates retain the same priors and the same exact-JAX structural/practical
qualification already passed in v0.7d/v0.7e.

## Frozen out-of-family world A: dynamic_like

The generator is recursive but not contained in the fitted dynamic candidate.

Truth:

- suitability intercept alpha = 0.30;
- initial occupancy psi0 = 0.20;
- colonization intercept probability gamma0 = 0.30;
- extinction intercept probability epsilon0 = 0.12;
- colonization time coefficient = +0.55;
- extinction time coefficient = -0.35.

The generating transitions are:

    gamma_t = logistic(logit(0.30) + 0.55 * time_t)
    epsilon_t = logistic(logit(0.12) - 0.35 * time_t)

and occupancy is propagated recursively.

The fitted dynamic candidate omits both transition-time coefficients and assumes constant
gamma and epsilon. Therefore the class-matched dynamic candidate is deliberately
misspecified.

The frozen marginal occupancy trajectory remains interior rather than saturating:
approximately 0.20 at context 1 and 0.81 at context 12.

## Frozen out-of-family world B: static_like

The generator is memoryless but not contained in the fitted static candidate.

Truth:

- suitability intercept alpha = 0.30;
- occupancy intercept = -0.50;
- linear time slope = +1.50;
- quadratic time slope = +0.25;
- cubic time slope = +0.35.

Generating occupancy is:

    psi_t = logistic(
        -0.50
        + 1.50 * time_t
        + 0.25 * time_t^2
        + 0.35 * time_t^3
    )

The fitted static candidate omits the cubic term and remains quadratic. Therefore the
class-matched static candidate is deliberately misspecified.

The frozen occupancy trajectory also remains interior:
approximately 0.11 at context 1 and 0.83 at context 12.

## Frozen observation programme

For both worlds and both candidates:

- one spatial trajectory;
- 12 ordered contexts;
- joint occurrence generated at contexts 1-12;
- joint occurrence exposed for fitting at contexts 1-8 only;
- direct OccupancyCount exposed at contexts 1-4 only;
- contexts 9-12 used only for joint-occurrence scoring;
- direct occupancy exposure in contexts 9-12 exactly zero;
- joint-occurrence effort = 500;
- direct-occupancy effort = 500.

Within a world/replicate, both fitted candidates receive exactly the same generated
realization.

## Frozen candidate qualification

Before outcome, both fitted candidates must retain the inherited v0.7d exact-JAX
qualification:

- every free target structurally Identified;
- every free target practically non-weak;
- target-SD proxy <= 0.25;
- rank rtol = 1e-8;
- rank atol = 1e-10;
- relative minimum singular-value threshold = 1e-3;
- condition-number threshold = 1e3;
- Fisher ridge = 1e-10.

The generators themselves are not fitted and are intentionally outside the candidate
families.

## Frozen replicated outcome

For each world:

- replicates = 16;
- paired dynamic/static fits per replicate;
- fits per world = 32.

Across both worlds:

- generated datasets = 32;
- total fits = 64.

Seed families are independent by world.

dynamic_like:

- base seed = 20261217;
- seed stride = 173.

static_like:

- base seed = 20271217;
- seed stride = 173.

For every replicate:

- dynamic fit seed = data seed + 1;
- static fit seed = data seed + 2;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

No scientific or MCMC setting is configurable from the command line.

## Frozen primary comparisons

For dynamic_like:

    gain_dynamic_like
      = dynamic held-out mean log predictive density
        - static held-out mean log predictive density

For static_like:

    gain_static_like
      = static held-out mean log predictive density
        - dynamic held-out mean log predictive density

The resolution-matched candidate must pass separately in each world:

- correct-direction winner in at least 12/16 replicates, rate >= 0.75;
- mean correct-direction gain >= +0.25 nats per held-out context.

Minimum replicate gain is reported descriptively and is not a pass/fail criterion.

The thresholds are lower than the exact-world v0.7d/e gates because both fitted
candidates are intentionally misspecified; they are frozen before any v0.7f outcome.

## Frozen sampling criterion

Across all 64 fits:

- divergences / fit <= 0.10.

## Mechanical decision

v0.7f = PASS only if:

- both candidate identification qualifications pass;
- dynamic_like passes both predictive criteria;
- static_like passes both predictive criteria;
- the global sampling criterion passes.

No failed criterion may be repaired inside v0.7f by changing:

- either generating world;
- candidate model forms;
- time covariates;
- training/held-out split;
- observation effort;
- seed families;
- MCMC profile;
- qualification thresholds;
- predictive thresholds.

## Interpretation boundary

PASS may support:

> The temporal-resolution discrimination is not limited to cases where the true generator
> is exactly one of the fitted candidate models. Under two frozen mild misspecifications,
> the candidate preserving the generator's temporal dependence class retains predictive
> advantage beyond the direct calibration window.

PASS would support **out-of-family temporal-resolution robustness** in the frozen
semi-synthetic programme.

PASS would not establish:

- universal robustness to arbitrary model misspecification;
- universal model-selection consistency;
- realized binary occupancy histories;
- directly observed colonization/extinction events;
- movement or dispersal kernels;
- resistance or path connectivity;
- source-sink or rescue dynamics;
- causal movement limitation;
- empirical biological validity.
