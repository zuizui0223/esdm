# v0.7g Budget-Matched Calibration-Placement Validation Gate

Status: **FROZEN AFTER DETERMINISTIC DESIGN SELECTION, BEFORE MCMC OUTCOME**

Date frozen: 2026-09-25

## Scientific question

At a fixed direct-occupancy field-effort budget, can the temporal placement of calibration
measurements materially improve estimation of marginal colonization/extinction dynamics?

v0.7a-v0.7f established that direct occupancy calibration can resolve the missing
occupancy scale. v0.7g asks where to spend the same calibration effort.

## Deterministic pre-outcome selection

The joint-occurrence training window remains contexts 1-8.

Exactly four direct OccupancyCount contexts are chosen from those eight contexts.
Every selected context receives effort 500, so every candidate design has:

- direct calibration contexts = 4;
- total direct effort = 2000;
- zero direct occupancy exposure in held-out contexts 9-12.

All 8 choose 4 = **70 placements** were evaluated before MCMC outcome.

The selection objective was frozen as:

    minimize max(
        SD_proxy(psi0_logit),
        SD_proxy(gamma_logit),
        SD_proxy(epsilon_logit)
    )

using the same exact-JAX/Fisher-like local diagnostic at the frozen v0.7b truth.
Lexicographic placement order breaks exact ties.

No stochastic replicate or held-out outcome was used for design selection.

## Frozen deterministic result

Selection run: 36105062429.

Artifact:

- ID: 10850198439;
- SHA256: 45d19db95b45f03c0144a9e11e5636edd3387ff1c8e393eaefbbe0478356eae5.

All 70 placements remained structurally identified and passed the frozen conditioning
bounds.

Selected design:

    contexts = (2, 6, 7, 8)

Early baseline inherited from v0.7b:

    contexts = (1, 2, 3, 4)

Both use total direct effort = 2000.

Deterministic worst dynamic SD proxy:

- selected = 0.1588310516922439;
- baseline = 0.23245395326115278;
- selected / baseline = 0.6832796322194767.

Thus the deterministic design stage predicts about a 31.7% reduction in the minimax
dynamic-parameter SD proxy.

## Frozen paired MCMC data generation

The ecological generator is exactly the frozen v0.7b constant-transition dynamic world:

- alpha = 0.30;
- psi0 = 0.20;
- gamma = 0.35;
- epsilon = 0.15.

For each replicate, one common super-realization is generated:

- joint occurrence at contexts 1-12 with effort 500;
- direct OccupancyCount at every training context 1-8 with effort 500;
- direct occupancy effort = 0 at contexts 9-12.

Each fitted design sees only its own four selected direct-calibration contexts:

- baseline sees 1,2,3,4;
- optimized sees 2,6,7,8.

Both fits receive the identical joint occurrence realization. Shared direct contexts reuse
the same generated count. Neither fit receives more than total direct effort 2000.

Held-out contexts 9-12 are never used for fitting.

## Frozen MCMC programme

- replicates = 16;
- paired baseline/optimized fits per replicate;
- total fits = 32;
- base seed = 20261225;
- seed stride = 179;
- optimized fit seed = data seed + 1;
- baseline fit seed = data seed + 2;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90;
- credible interval mass = 0.90.

No scientific or MCMC setting is configurable from the command line.

## Frozen primary precision endpoint

For each fitted model and replicate, compute posterior SD on the fitted log/logit scale for:

- psi0_logit;
- gamma_logit;
- epsilon_logit.

Define:

    worst_dynamic_posterior_sd
      = max(SD(psi0_logit), SD(gamma_logit), SD(epsilon_logit))

and

    ratio = optimized worst_dynamic_posterior_sd
            / baseline worst_dynamic_posterior_sd

Primary criteria:

- optimized worst SD < baseline worst SD in at least 12/16 replicates, rate >= 0.75;
- mean optimized/baseline worst-SD ratio <= 0.85.

These thresholds are frozen before any MCMC replicate outcome.

## Frozen optimized-design recovery guardrail

The optimized design must still recover the known truth rather than becoming
overconfident.

For each of the four ecological targets:

- absolute mean posterior bias <= 0.15;
- empirical 90% interval coverage >= 0.75.

## Frozen sampling criterion

Across all 32 fits:

- divergences / fit <= 0.10.

## Descriptive held-out endpoint

Both fits are also scored on the same held-out joint occurrence counts at contexts 9-12.

Optimized-minus-baseline mean log predictive density, its positive-replicate rate, and
minimum replicate gain are reported **descriptively only**. They are not v0.7g promotion
criteria because placement was selected for parameter precision, not prediction.

## Mechanical decision

v0.7g = PASS only if every frozen precision, optimized recovery, and sampling criterion
passes.

No failed criterion may be repaired within v0.7g by changing:

- selected placement;
- baseline placement;
- total direct effort;
- generator truth;
- observation split;
- seed family;
- MCMC profile;
- precision thresholds;
- recovery thresholds.

## Interpretation boundary

PASS may support:

> With the same number of direct occupancy observations and the same total field-effort
> budget, temporal placement can materially improve precision of marginal dynamic
> parameters. In the frozen design, one early calibration plus three late-training
> calibrations is more informative under a minimax dynamic-parameter criterion than
> concentrating all four calibrations at the beginning.

PASS would not establish:

- that (2,6,7,8) is universally optimal;
- optimal placement under different truths, costs, effort-response functions, or survey
  designs;
- that equal effort implies equal expected record count;
- universal predictive superiority of the selected placement;
- realized colonization/extinction events;
- movement kernels or connectivity;
- empirical biological validity.
