# v0.7j Pilot-Selected Calibration Under Population Shift

Status: **FROZEN BEFORE ANY v0.7j OUTCOME**

Date frozen: 2026-09-25

## Question

Does the occupancy-calibration schedule selected by the disjoint burned pilot in
v0.7i retain its dynamic-parameter precision advantage when the confirmatory
population has different occupancy dynamics from the pilot population?

This is a transfer-of-observation-design test, not an ODSP information-transfer
endpoint.

## Frozen deployed schedule

The deployed schedule is fixed from the already frozen v0.7i result:

- selected placement = (2, 6, 7, 8);
- baseline placement = (1, 2, 3, 4);
- four direct OccupancyCount contexts in both designs;
- effort = 500 per direct context;
- total direct effort = 2000;
- joint occurrence fit at contexts 1-8;
- held-out contexts 9-12 contain zero direct occupancy exposure.

No new pilot is fit in v0.7j. No target-population data are used to alter the
selected schedule.

## Frozen source population

The schedule originates from the v0.7i burned-pilot programme with:

- alpha = 0.30;
- psi0 = 0.20;
- gamma = 0.35;
- epsilon = 0.15.

The v0.7i frozen result selected (2,6,7,8) in 16/16 pilots.

## Frozen target-population shifts

Alpha remains 0.30. Only occupancy dynamics shift.

### Low-occupancy target

- psi0 = 0.10;
- gamma = 0.20;
- epsilon = 0.30.

### High-occupancy target

- psi0 = 0.50;
- gamma = 0.55;
- epsilon = 0.10.

### High-turnover target

- psi0 = 0.20;
- gamma = 0.55;
- epsilon = 0.40.

These three target worlds are frozen before outcome generation and may not be
replaced after result access.

## Frozen replicated design

For each target world:

- replicates = 12;
- selected and baseline are fit to the same generated ecological realization;
- fits per target world = 24;
- total fits across three target worlds = 72;
- warmup = 300;
- retained posterior draws = 350;
- chains = 2;
- central posterior interval mass = 0.90;
- target accept probability = 0.90.

Fresh seed families:

- low-occupancy base = 20300117, stride = 211;
- high-occupancy base = 20310117, stride = 223;
- high-turnover base = 20320117, stride = 227.

Within each replicate:

- selected fit seed = data seed + 1;
- baseline fit seed = data seed + 2.

## Frozen primary endpoint

For each fit:

worst_dynamic_SD = max(
  posterior_SD(psi0_logit),
  posterior_SD(gamma_logit),
  posterior_SD(epsilon_logit)
)

For each paired replicate:

ratio = selected worst_dynamic_SD / baseline worst_dynamic_SD

A target world passes the precision-transfer criterion only if:

- selected has lower worst dynamic SD in at least 9/12 pairs;
- mean selected/baseline worst-SD ratio <= 0.95.

The full v0.7j robustness claim requires all three target worlds to pass both
criteria.

## Frozen recovery guardrails

Within each target world, for the selected design:

- absolute mean bias <= 0.20 for alpha, psi0 logit, gamma logit, epsilon logit;
- empirical 90% interval coverage >= 2/3 for every target.

These guard against apparent precision gains produced by severe bias or
undercoverage under population shift.

## Frozen sampling criterion

Across all 72 fits:

- divergences / fit <= 0.10.

## Descriptive prediction only

For each target world, also report:

- selected > baseline held-out score fraction;
- mean selected-minus-baseline held-out log-score gain;
- minimum selected-minus-baseline gain.

These are not promotion criteria because both candidates measure the same
ecological information with different observation schedules.

## Mechanical decision

v0.7j = PASS only if:

1. every target world passes the paired precision criterion;
2. every selected-design recovery guardrail passes;
3. the global sampling criterion passes.

No failed criterion may be repaired inside v0.7j by changing target worlds,
schedule, baseline, effort, seed families, MCMC profile, recovery thresholds or
precision thresholds.

## Interpretation boundary

PASS may support:

> A direct-occupancy schedule selected from the frozen source-population pilot
> retains a precision advantage across the three preregistered shifted dynamic
> populations.

PASS does not establish:

- universal transfer to arbitrary populations;
- optimality under other detection models, costs or horizons;
- superiority in held-out prediction;
- a new ODSP information-transfer level;
- movement or connectivity;
- empirical biological validity.
