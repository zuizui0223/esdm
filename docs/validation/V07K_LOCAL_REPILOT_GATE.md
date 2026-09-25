# v0.7k Local Re-Pilot Rescue Gate

Status: **FROZEN AFTER DETERMINISTIC AUDIT, BEFORE CONFIRMATORY MCMC OUTCOME**

Date frozen: 2026-09-25

## Scientific question

After the v0.7j transportability failure, can a small burned pilot collected in the
**shifted population itself** re-select the temporal occupancy-calibration schedule and
restore process-parameter precision on an independent confirmatory realization?

This is a fresh local-adaptation hypothesis. It does not retune or rescue the failed
v0.7j fixed-schedule gate.

## Frozen parent result

v0.7j established:

- fixed transferred schedule (2,6,7,8) was not universally transportable;
- transfer_positive missed the frozen mean precision threshold and extinction-bias guardrail;
- reversal strongly favored abandoning the transferred schedule.

v0.7k therefore changes the decision rule, not the v0.7j thresholds: it allows a local
burned pilot in the shifted population to select a new schedule before independent
confirmation.

## Frozen deterministic local-oracle audit

Audit run: `36118088393`.

Audit artifact:

- ID: `10855618140`;
- SHA256:
  `1a3505cda24e32b86f5ef18bfc79a0228786eb9357f718ce5003082b32621150`.

The audit evaluated all 70 choose(8,4) placements at each shifted truth. It contained no
confirmatory MCMC outcome.

### transfer_positive

- local oracle placement: (1,3,7,8);
- local-oracle / transferred-(2,6,7,8) worst-SD proxy ratio:
  0.9247321772913307;
- local-oracle / early-four baseline ratio:
  0.7941382408242843.

### reversal

- local oracle placement: (1,2,7,8);
- local-oracle / transferred-(2,6,7,8) ratio:
  0.6943717396344599;
- local-oracle / early-four baseline ratio:
  0.9576958563624403.

The local oracle differs by population. Oracle placements are descriptive benchmarks
only; the confirmatory selector does not receive truth or oracle labels.

## Frozen two-stage adaptive procedure

For every world and replicate:

### Stage 1: local burned pilot

- pilot population = the shifted confirmatory population class;
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

## Frozen shifted worlds

The worlds are exactly the v0.7j confirmatory worlds.

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

    ratio = adaptive worst dynamic posterior SD
            / transferred worst dynamic posterior SD

where worst dynamic posterior SD is the maximum posterior SD across:

- initial occupancy logit;
- colonization logit;
- extinction logit.

The local adaptive procedure must pass **separately in both worlds**:

- adaptive schedule lower worst dynamic SD in at least 12/16 replicates:
  rate >= 0.75;
- mean adaptive/transferred ratio <= 0.95.

These thresholds are frozen symmetrically across the two shifted worlds.

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

The scientific endpoint is restored information about the dynamic decomposition, not
universal predictive superiority or exact oracle recovery.

## Mechanical decision

v0.7k = PASS only if every frozen precision, recovery, and sampling criterion passes in
both shifted worlds.

No failed criterion may be repaired within v0.7k by changing:

- shifted truths;
- pilot placement;
- selector objective;
- candidate field effort;
- seed families;
- MCMC profile;
- precision thresholds;
- recovery thresholds.

## Interpretation boundary

PASS may support:

> When a previously optimized schedule is transported to a population with different
> occupancy dynamics, a small local burned pilot can re-optimize measurement timing and
> recover a precision advantage on independent confirmatory data.

PASS would support **local adaptive re-optimization after population shift** in the
frozen semi-synthetic programme.

PASS would not establish:

- a universal rule for when to trigger re-piloting;
- universal recovery under arbitrary population shift;
- empirical field transportability;
- universal cost optimality;
- realized colonization/extinction events;
- movement kernels or connectivity;
- biological validity.
