# v0.7h Expected-Record-Matched Calibration Placement Gate

Status: **FROZEN AFTER DETERMINISTIC EXPECTED-COUNT CONTROL, BEFORE MCMC OUTCOME**

Date frozen: 2026-09-25

## Scientific question

Does the v0.7g calibration-placement precision advantage persist after removing the
difference in expected direct OccupancyCount record yield?

v0.7g matched the number of direct calibration contexts and total field effort. Under the
frozen truth, later calibration contexts have higher occupancy and therefore yield more
expected direct records at the same effort. v0.7h removes that alternative explanation.

## Frozen designs

Baseline:

- placement = (1,2,3,4);
- effort per direct context = 500;
- total direct effort = 2000.

Selected placement inherited unchanged from the pre-outcome v0.7g frontier:

- placement = (2,6,7,8).

Its effort is reduced uniformly to:

- effort per direct context = 369.15453700836173;
- total direct effort = 1476.618148033447.

Under the frozen v0.7b dynamic truth, this exactly matches expected direct record yield.

## Frozen deterministic expected-count control

Run: 36106319723.

Artifact:

- ID = 10850294862;
- SHA256 = 8f3092876bc867a11cb90e7632b79bbd5ab471cea424477767fbb2657788d40c.

Expected direct OccupancyCount total:

- baseline = 931.2500000000001;
- selected = 931.25;
- relative mismatch = 1.2207982574133264e-16.

Thus expected direct count is numerically identical.

Selected/baseline field-effort ratio:

    0.7383090740167234

The selected design therefore uses about 26.2% less field effort.

Fisher-like worst dynamic SD proxy:

- baseline = 0.23245395326115278;
- selected = 0.1703748190712751;
- selected/baseline = 0.7329400798783825.

The deterministic control predicts about a 26.7% precision improvement even after
expected direct record count is matched.

## Frozen ecological generator

The ecological truth remains exactly the v0.7b constant-transition world:

- alpha = 0.30;
- psi0 = 0.20;
- gamma = 0.35;
- epsilon = 0.15.

Joint occurrence:

- generated at contexts 1-12;
- effort = 500;
- fitting uses contexts 1-8;
- contexts 9-12 are held out.

No direct occupancy observation is exposed in held-out contexts.

## Frozen paired MCMC data generation

Each replicate uses one common joint occurrence realization.

Two independent direct calibration streams are generated from the same latent occupancy
trajectory:

- baseline_calibration at contexts 1,2,3,4 with effort 500;
- selected_calibration at contexts 2,6,7,8 with effort 369.15453700836173.

Their expected total direct counts are equal by construction.

Each candidate fit receives only its own calibration stream and the shared joint
occurrence realization.

## Frozen MCMC programme

- replicates = 16;
- paired selected/baseline fits per replicate;
- total fits = 32;
- base seed = 20270105;
- seed stride = 181;
- selected fit seed = data seed + 1;
- baseline fit seed = data seed + 2;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90;
- credible interval mass = 0.90.

No scientific or MCMC setting is configurable from the command line.

## Frozen primary precision endpoint

For each fit compute posterior SD on the fitted log/logit scale for:

- psi0_logit;
- gamma_logit;
- epsilon_logit.

Define worst_dynamic_posterior_sd as the maximum of those three SDs.

Primary criteria:

- selected worst SD < baseline worst SD in at least 12/16 replicates, rate >= 0.75;
- mean selected/baseline worst-SD ratio <= 0.90.

## Frozen selected-design recovery guardrail

For every ecological target:

- absolute mean posterior bias <= 0.15;
- empirical 90% interval coverage >= 0.75.

## Frozen sampling criterion

Across all 32 fits:

- divergences / fit <= 0.10.

## Descriptive prediction endpoint

Selected-minus-baseline held-out joint-occurrence log predictive gain on contexts 9-12 is
reported descriptively only and is not a promotion criterion.

## Mechanical decision

v0.7h = PASS only if every frozen precision, recovery, and sampling criterion passes.

No failed criterion may be repaired within v0.7h by changing:

- either placement;
- expected-count matching effort;
- ecological truth;
- observation split;
- seed family;
- MCMC profile;
- precision or recovery thresholds.

## Interpretation boundary

PASS may support:

> The v0.7g precision advantage is not explained solely by obtaining more direct records
> at later high-occupancy contexts. After expected direct record yield is matched, the
> selected temporal placement still carries more information about the dynamic
> decomposition, while requiring less field effort under the frozen truth.

PASS would not establish:

- universal optimality of the placement;
- optimality under unknown field occupancy;
- universal cost efficiency under arbitrary survey costs or detection models;
- universal predictive superiority;
- empirical biological validity.
