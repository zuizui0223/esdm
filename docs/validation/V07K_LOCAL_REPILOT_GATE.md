# v0.7k Local Re-Optimization Increment Gate

Status: **FROZEN AFTER DETERMINISTIC AUDIT, BEFORE CONFIRMATORY MCMC OUTCOME**

Date frozen: 2026-09-25

## Scientific question

After the fixed v0.7i calibration schedule has already shown robust precision transfer
across the three preregistered v0.7j confirmatory population shifts, can a small burned
pilot collected in the shifted population itself provide additional precision by
re-selecting measurement timing before an independent confirmatory realization?

This is an incremental local-adaptation hypothesis. It does not rescue or reinterpret
the successful v0.7j robustness gate and it does not change any v0.7j threshold.

## Frozen parent evidence

### v0.7j confirmatory robustness result

The final frozen v0.7j result passed all 36 checks. The transferred schedule
(2,6,7,8) retained lower worst dynamic posterior SD than the early-four reference in
35/36 paired replicates across three preregistered target populations:

- low occupancy: 12/12 wins; mean selected/reference ratio = 0.8050227851;
- high occupancy: 11/12 wins; mean ratio = 0.7261308066;
- high turnover: 12/12 wins; mean ratio = 0.8664152205;
- pooled: 35/36 wins; mean ratio = 0.7991896041;
- all recovery guardrails passed;
- divergences = 0 across 72 fits.

Therefore v0.7k does not test whether the transferred schedule is usable. That was
already supported by v0.7j.

### v0.7j deterministic transportability surface

Before the v0.7j confirmatory outcome, a deterministic 36-cell population-shift
surface showed that the transferred schedule was better than the early-four baseline
in 30/35 eligible cells but was not the local optimum everywhere.

Two stress cells were selected from that surface before any v0.7k confirmatory MCMC:

transfer_positive stress cell:

- psi0 = 0.20;
- gamma = 0.15;
- epsilon = 0.05;
- transferred/early-four predicted worst-SD ratio = 0.8587764764.

reversal stress cell:

- psi0 = 0.80;
- gamma = 0.15;
- epsilon = 0.30;
- transferred/early-four predicted worst-SD ratio = 1.3792264312.

These are stress-test points from the preregistered transportability surface. They are
not the three v0.7j confirmatory target populations.

## Frozen deterministic local-oracle audit

Audit run: 36118088393.

Audit artifact:

- ID: 10855618140;
- SHA256: 1a3505cda24e32b86f5ef18bfc79a0228786eb9357f718ce5003082b32621150.

The audit evaluated all 70 choose(8,4) placements at each frozen stress truth and
contained no confirmatory MCMC outcome.

transfer_positive:

- local oracle placement: (1,3,7,8);
- local-oracle / transferred-(2,6,7,8) worst-SD proxy ratio = 0.9247321773;
- local-oracle / early-four ratio = 0.7941382408.

reversal:

- local oracle placement: (1,2,7,8);
- local-oracle / transferred-(2,6,7,8) ratio = 0.6943717396;
- local-oracle / early-four ratio = 0.9576958564.

The local oracle differs by stress population. Oracle placements are descriptive
benchmarks only; the confirmatory selector does not receive truth or oracle labels.

## Frozen two-stage adaptive procedure

For every stress world and replicate:

### Stage 1: local burned pilot

- pilot population = the shifted stress population class;
- pilot direct OccupancyCount placement = contexts (1,2,3,4);
- pilot direct effort = 500 per selected context;
- pilot total direct effort = 2000;
- pilot joint occurrence uses training contexts 1-8;
- pilot is fit once with the dynamic model;
- selector receives only pilot posterior means for alpha, psi0, gamma, epsilon;
- selector rescans all 70 four-context placements using the frozen minimax dynamic-SD
  objective;
- generating truth, oracle placement, confirmatory counts, and confirmatory fits are not
  selector inputs.

### Stage 2: independent confirmation

- confirmatory data use a disjoint seed family from the pilot;
- adaptive schedule = pilot-selected placement;
- transferred reference = fixed v0.7i schedule (2,6,7,8);
- both receive exactly four direct contexts at effort 500/context;
- total direct field effort = 2000 for each confirmatory candidate;
- both receive the same confirmatory joint-occurrence realization;
- joint occurrence is fit at contexts 1-8;
- contexts 9-12 are held out;
- direct occupancy exposure in contexts 9-12 is exactly zero.

## Frozen stress worlds

The worlds are exactly the two preregistered stress cells above.

transfer_positive:

- psi0 = 0.20;
- gamma = 0.15;
- epsilon = 0.05;
- alpha = 0.30.

reversal:

- psi0 = 0.80;
- gamma = 0.15;
- epsilon = 0.30;
- alpha = 0.30.

## Frozen replicated programme

For each world:

- replicates = 16;
- pilot fits = 16;
- adaptive confirmatory fits = 16;
- transferred confirmatory fits = 16;
- fits per world = 48.

Across both worlds:

- pilot/confirm pairs = 32;
- total fits = 96.

Independent seed families:

transfer_positive:

- pilot base seed = 20261321;
- confirmatory base seed = 20261421.

reversal:

- pilot base seed = 20271321;
- confirmatory base seed = 20271421.

For all seed families:

- seed stride = 181.

Fit RNG offsets:

- pilot fit seed = pilot data seed + 1;
- adaptive confirmatory fit seed = confirmatory data seed + 1;
- transferred confirmatory fit seed = confirmatory data seed + 2.

MCMC profile:

- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90;
- 90% intervals for recovery guardrails.

No scientific or MCMC setting is configurable from the command line.

## Frozen primary precision criteria

For each confirmatory fit define:

ratio = adaptive worst dynamic posterior SD / transferred worst dynamic posterior SD.

Worst dynamic posterior SD is the maximum posterior SD across:

- initial occupancy logit;
- colonization logit;
- extinction logit.

The local adaptive procedure must pass separately in both stress worlds:

- adaptive schedule lower worst dynamic SD in at least 12/16 replicates;
- rate >= 0.75;
- mean adaptive/transferred ratio <= 0.95.

These thresholds are unchanged from the original frozen v0.7k programme.

## Frozen recovery guardrails

For the adaptive confirmatory fit in each world:

- abs(mean bias) <= 0.20 for every ecological parameter;
- 90% coverage >= 0.75 for every ecological parameter.

## Frozen sampling criterion

Across all 96 fits, including pilot fits:

- divergences / fit <= 0.10.

## Descriptive selector and prediction outputs

The following are reported but are not pass/fail endpoints:

- pilot-selected placement frequencies;
- oracle-placement selection rate;
- mean pilot-predicted adaptive/transferred SD ratio;
- held-out predictive gain.

The scientific endpoint is incremental precision from local adaptation beyond the fixed
transferred schedule, not universal predictive superiority or exact oracle recovery.

## Mechanical decision

v0.7k = PASS only if every frozen precision, recovery, and sampling criterion passes in
both stress worlds.

No failed criterion may be repaired within v0.7k by changing:

- stress truths;
- pilot placement;
- selector objective;
- candidate field effort;
- seed families;
- MCMC profile;
- precision thresholds;
- recovery thresholds.

## Interpretation boundary

PASS may support:

> Even when a previously optimized schedule is broadly robust to population shift, a
> small local burned pilot can add further parameter precision in preregistered stress
> populations by re-optimizing measurement timing before independent confirmation.

PASS would support local adaptive re-optimization as an incremental precision tool in
the frozen semi-synthetic stress programme.

PASS would not establish:

- that re-piloting is required for ordinary shifted populations;
- a universal rule for when to trigger re-piloting;
- universal recovery under arbitrary population shift;
- empirical field transportability;
- universal cost optimality;
- realized colonization/extinction events;
- movement kernels or connectivity;
- biological validity.
