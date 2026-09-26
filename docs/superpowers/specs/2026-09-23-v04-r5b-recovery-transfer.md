# v0.4-R5b Recovery and Held-Out Transfer Design

Status: **approved prospective design, pre-outcome**

Base: frozen R5a PASS head `5a84e2c7a061364b027a2dafcfd8e168d1b5164c`.

R5a established that the exact direct state-composition calibration design passes the
hard pre-MCMC identification gate. R5b now asks whether the same qualified design
recovers parameters and contributes held-out predictive information.

## Immutable R5a design

R5b changes no scientific component of R5a:

- same opportunistic PresenceOnly stream;
- same calibrated PresenceOnly stream;
- same R4a StateAnnotatedCount geometry;
- same StateCompositionCount stream;
- 432 direct calibration contexts;
- label effort = 1.0 per context;
- no direct state-calibration exposure in the east held-out block;
- same ecological/observation/activity/state truths;
- same training and east-heldout partition.

## Outcome profile inherited from frozen R2

R5b deliberately reuses the original R2 outcome criteria rather than inventing easier
criteria after the R5a PASS:

- replicates = 16;
- three fits per replicate: full, activity knockout, state knockout;
- total fits = 48;
- base seed = 20260926;
- seed stride = 47;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- credible mass = 0.90;
- target accept = 0.90.

All 13 original recovery targets are retained.

## Frozen recovery criteria

For every one of the 13 targets:

- absolute mean bias <= 0.18;
- empirical 90% interval coverage >= 0.75.

## Frozen held-out transfer criteria

On the east block, evaluated using only the original StateAnnotatedCount observations:

Activity knockout:

- positive full-minus-knockout log-score gain in >= 75% of replicates;
- mean gain >= 0.005.

State knockout:

- positive full-minus-knockout log-score gain in >= 75% of replicates;
- mean gain >= 0.005.

The direct state-composition calibration stream has zero east-heldout exposure, so it
cannot directly contribute held-out labels to the score.

## Divergence criterion

Across all 48 fits:

- mean divergences per fit <= 0.10.

## Execution architecture

Each replicate is executed in a separate GitHub Actions matrix job. This changes only
resource isolation, not the scientific profile.

Each shard:

1. verifies the pinned source blob;
2. generates one complete dataset using its frozen seed;
3. fits full/activity-knockout/state-knockout models;
4. records posterior recovery intervals, held-out scores, and divergences.

A final aggregation job verifies all 16 shard identities and seeds, reconstructs the
frozen R5a qualification, summarizes all records, and applies the combined gate.

No shard may alter thresholds, seeds, geometry, MCMC settings, or model definitions.

## Claim boundary

R5b PASS would establish semi-synthetic parameter recovery and east-heldout predictive
value of activity and state slopes under the exact qualified observation contract.

It would not establish empirical biological validity, causal truth in real systems,
universal superiority to SDM/JSDM alternatives, or field cost-effectiveness.
