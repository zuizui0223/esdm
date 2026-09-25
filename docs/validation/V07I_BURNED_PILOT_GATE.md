# v0.7i Disjoint Burned-Pilot Adaptive Calibration Gate

Status: **FROZEN AFTER PRE-OUTCOME CI, BEFORE CONFIRMATORY OUTCOME**

Date frozen: 2026-09-25

## Scientific question

Can the direct-occupancy placement advantage established by v0.7g/v0.7h be recovered
without using the known generating truth to choose the calibration schedule?

This gate replaces truth-based placement selection with a two-stage adaptive procedure:

1. fit a burned pilot;
2. choose the four calibration contexts from pilot posterior means only;
3. evaluate that frozen choice on a completely independent confirmatory realization.

## Frozen ecological world

The ecological generator remains exactly the v0.7b marginal dynamic truth:

- suitability intercept alpha = 0.30;
- initial occupancy psi0 = 0.20;
- colonization probability gamma = 0.35;
- extinction probability epsilon = 0.15;
- 12 ordered contexts;
- joint-occurrence effort = 500.

The truth is used to generate pilot and confirmatory data and to score recovery after the
fact. It is **not an input to the placement selector**.

## Frozen burned pilot

For every replicate, the pilot uses:

- joint occurrence generated at contexts 1-12;
- joint occurrence exposed for fitting at contexts 1-8 only;
- direct OccupancyCount at contexts **1,2,3,4** only;
- direct effort = 500 per pilot calibration context;
- total pilot direct effort = 2000;
- contexts 9-12 are not used for pilot fitting.

Pilot MCMC:

- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

The selector receives only the posterior mean of:

- alpha;
- psi0 logit;
- gamma logit;
- epsilon logit.

## Frozen adaptive selector

The selector evaluates all **70 = choose(8,4)** four-context placements within training
contexts 1-8.

Every candidate placement has:

- 4 direct calibration contexts;
- effort 500 per selected context;
- total direct field effort = 2000;
- zero held-out direct occupancy exposure.

For each placement, one exact-JAX design Jacobian is evaluated at the pilot posterior
mean. The Fisher-like covariance proxy is computed from the expected-rate Jacobian.

The objective is frozen as:

    minimize max(
        SD_proxy(psi0_logit),
        SD_proxy(gamma_logit),
        SD_proxy(epsilon_logit)
    )

Eligibility requires:

- exact structural full rank;
- relative minimum singular value >= 1e-3;
- condition number <= 1e3.

Ties are resolved lexicographically by placement.

The selector has no argument for generating truth and receives no confirmatory data.

## Frozen independent confirmation

For each replicate, confirmatory data are generated from a different seed family than the
pilot.

The pilot-selected design and the early-four baseline are compared on the same
confirmatory ecological realization.

Both confirmatory candidates receive:

- the same joint occurrence realization;
- joint occurrence fit at contexts 1-8;
- exactly 4 direct occupancy calibration contexts;
- 500 direct effort per context;
- total direct field effort = 2000;
- no direct occupancy exposure in held-out contexts 9-12.

The baseline is fixed at contexts **(1,2,3,4)**.

Confirmatory selected and baseline fits each use:

- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

## Frozen seed families

Replicates = 16.

Pilot data seeds:

- base seed = 20270105;
- seed stride = 191.

Confirmatory data seeds:

- base seed = 20280105;
- seed stride = 193.

Within each replicate:

- pilot fit seed = pilot data seed + 1;
- selected confirmatory fit seed = confirmatory data seed + 1;
- baseline confirmatory fit seed = confirmatory data seed + 2.

Pilot and confirmatory seed families are disjoint.

## Frozen primary endpoint

For each confirmatory fit, define:

    worst_dynamic_SD = max(
        posterior_SD(psi0_logit),
        posterior_SD(gamma_logit),
        posterior_SD(epsilon_logit)
    )

and

    ratio = selected worst_dynamic_SD / baseline worst_dynamic_SD

Primary criteria:

- selected design has lower worst dynamic SD in at least 12/16 confirmatory pairs,
  rate >= 0.75;
- mean selected/baseline worst-SD ratio <= 0.90.

## Frozen recovery guardrails

For the pilot-selected confirmatory design:

- absolute mean bias <= 0.15 for each of alpha, psi0 logit, gamma logit, epsilon logit;
- empirical 90% interval coverage >= 0.75 for each target.

These are guardrails against gaining nominal precision through pathological bias or
undercoverage.

## Frozen sampling criterion

Across 16 pilot fits + 16 selected confirmatory fits + 16 baseline confirmatory fits:

- total fits = 48;
- divergences / fit <= 0.10.

## Descriptive quantities only

The following are reported but are not promotion criteria:

- frequency with which the pilot selector chooses the truth-oracle v0.7g placement
  (2,6,7,8);
- distribution of selected placements;
- pilot-predicted selected/baseline SD-proxy ratio;
- held-out selected-minus-baseline joint-occurrence score on contexts 9-12.

Prediction remains descriptive because v0.7g/v0.7h already showed that process precision
can change materially while held-out predictive score changes very little.

## Mechanical decision

v0.7i = PASS only if all frozen confirmatory precision, recovery, and sampling criteria
pass.

No failed criterion may be repaired inside v0.7i by changing:

- pilot observation design;
- selector objective;
- selector eligibility thresholds;
- field-effort budget;
- pilot/confirmatory seed families;
- ecological truth;
- MCMC profile;
- recovery thresholds;
- precision thresholds.

## Interpretation boundary

PASS may support:

> A small burned pilot can select a temporally targeted direct-occupancy schedule that
> improves later dynamic-parameter precision on independent data, without using the
> generating truth to choose the schedule.

PASS would support **pilot-adaptive calibration placement** in the frozen semi-synthetic
programme.

PASS would not establish:

- universal optimality of the selected schedules;
- universal optimality under different truths, costs, detection models, or horizons;
- optimality when pilot and confirmatory populations differ;
- universal cost efficiency;
- realized colonization/extinction events;
- movement kernels or connectivity;
- empirical biological validity.
