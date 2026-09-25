# v0.7j Population-Shift Transfer and Reversal Gate

Status: **FROZEN AFTER DETERMINISTIC SURFACE, BEFORE CONFIRMATORY MCMC OUTCOME**

Date frozen: 2026-09-25

## Scientific question

Does the pilot-selected occupancy-calibration schedule from v0.7i remain useful when the
confirmatory population has different dynamic parameters, and can the framework detect a
population shift large enough to reverse the preferred schedule?

This gate explicitly does **not** assume universal transportability of the fixed
`(2,6,7,8)` schedule.

## Frozen deterministic surface provenance

The pre-confirmatory surface evaluated the selected schedule `(2,6,7,8)` against the
early-four baseline `(1,2,3,4)` over 36 frozen dynamic-truth cells:

- psi0 in {0.10, 0.20, 0.50, 0.80};
- gamma in {0.15, 0.35, 0.55};
- epsilon in {0.05, 0.15, 0.30};
- suitability intercept alpha fixed at 0.30.

Surface run: `36111568220`.

Across the 36 cells:

- 35 were jointly practically eligible;
- 1 cell was ineligible;
- selected schedule better in 30/35 eligible cells;
- mean selected/baseline worst-dynamic-SD proxy ratio = 0.864681;
- minimum ratio = 0.580436;
- maximum ratio = 1.379226.

The surface was deterministic and contained no confirmatory MCMC outcome.

## Frozen stress-world selection

Two cells were selected from the deterministic surface before confirmatory MCMC.

### transfer_positive

Selection rule:

> among eligible cells with selected/baseline ratio <= 0.90, choose the largest ratio.

Frozen truth:

- psi0 = 0.20;
- gamma = 0.15;
- epsilon = 0.05;
- deterministic selected/baseline ratio = 0.8587764763960369.

This is a deliberately difficult positive-transfer case rather than an easy best case.

### reversal

Selection rule:

> choose the eligible cell with the largest selected/baseline ratio.

Frozen truth:

- psi0 = 0.80;
- gamma = 0.15;
- epsilon = 0.30;
- deterministic selected/baseline ratio = 1.3792264311715838.

This is the strongest frozen reversal cell in the surface.

## Frozen candidate schedules

Selected schedule:

- direct OccupancyCount at contexts (2,6,7,8);
- effort = 500 per selected context;
- total direct effort = 2000.

Baseline:

- direct OccupancyCount at contexts (1,2,3,4);
- effort = 500 per selected context;
- total direct effort = 2000.

Both schedules use exactly the same joint-occurrence programme:

- joint occurrence fit at contexts 1-8;
- contexts 9-12 held out for scoring;
- zero direct occupancy exposure in held-out contexts.

Within each world/replicate, selected and baseline fits receive the same generated
ecological realization.

## Frozen replicated programme

For each world:

- replicates = 16;
- paired selected/baseline fits per replicate;
- fits per world = 32.

Across both worlds:

- datasets = 32;
- total fits = 64.

Independent seed families:

transfer_positive:

- base seed = 20261301;
- seed stride = 179.

reversal:

- base seed = 20271301;
- seed stride = 179.

For each replicate:

- selected fit seed = data seed + 1;
- baseline fit seed = data seed + 2;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90;
- 90% intervals for recovery guardrails.

No scientific or MCMC setting is configurable from the command line.

## Frozen primary precision directions

Define:

    ratio = selected worst dynamic posterior SD
            / baseline worst dynamic posterior SD

where worst dynamic posterior SD is the maximum posterior SD across:

- initial occupancy logit;
- colonization logit;
- extinction logit.

### transfer_positive criteria

- selected schedule lower worst dynamic SD in at least 12/16 replicates:
  correct-direction rate >= 0.75;
- mean selected/baseline ratio <= 0.95.

### reversal criteria

- baseline schedule lower worst dynamic SD in at least 12/16 replicates:
  correct-direction rate >= 0.75;
- mean selected/baseline ratio >= 1.10.

The reversal criterion is a required scientific result, not a failure mode to be rescued.

## Frozen recovery guardrails

For the winning schedule in each world:

- abs(mean bias) <= 0.20 for every ecological parameter;
- 90% coverage >= 0.75 for every ecological parameter.

These are guardrails against obtaining the desired precision direction from a badly
miscalibrated fitted model.

## Frozen sampling criterion

Across all 64 confirmatory fits:

- divergences / fit <= 0.10.

## Descriptive-only prediction

Held-out joint-occurrence predictive gain is reported but is not a pass/fail endpoint.
The scientific target is information about the dynamic decomposition, not universal
predictive superiority.

## Mechanical decision

v0.7j = PASS only if all frozen transfer-positive, reversal, recovery, and sampling
criteria pass.

No failed criterion may be repaired within v0.7j by changing:

- stress-world truths;
- stress-world selection rules;
- candidate schedules;
- observation effort;
- train/held-out split;
- seed families;
- MCMC settings;
- recovery thresholds;
- precision-direction thresholds.

## Interpretation boundary

PASS may support:

> A pilot-selected calibration schedule can transfer across moderate population shift,
> but its advantage is not universal. Under a sufficiently different frozen dynamic
> population, the preferred schedule reverses, and the framework can detect that reversal.

This would establish a **transportability boundary** for the fixed schedule in the frozen
semi-synthetic programme.

PASS would not establish:

- universal transportability of (2,6,7,8);
- a universal rule for when re-optimization is required;
- robustness to arbitrary population shift;
- empirical field transportability;
- realized colonization/extinction events;
- movement kernels or connectivity.
