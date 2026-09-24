# v0.4-R7 Budget-Matched Calibration Design

Status: **approved prospective design, pre-outcome**

Base: frozen R6 PASS head `7d653108801369fd1ace6e90c29054c507ae060f`.

R7 addresses the main remaining internal alternative explanation for R5:

> Did direct state-composition calibration succeed because it supplies a different
> information geometry, or simply because R5 added more state labels?

## Paired calibration arms

Both arms inherit the exact R4 base model and the same 432 existing
StateAnnotatedCount contexts.

### Direct arm

The promoted R5 observation contract:

- add StateCompositionCount at the exact R4 36×12 training contexts;
- effort = 1.0 per context;
- total expected direct labels = 432;
- consumes only conditional state composition;
- zero east-heldout exposure.

### Passive arm

Replace the direct calibration stream with one additional ordinary
StateAnnotatedCount stream:

- same 36×12 training contexts;
- same known detection = 0.85;
- zero east-heldout exposure;
- one constant passive effort across all exposed contexts.

The passive effort is fixed before outcomes by:

`passive_effort = 432 / sum_c[exp(log_intensity_c) * activity_c * 0.85]`

evaluated at the already frozen promoted structured truth.

Therefore the passive arm also has exactly **432 expected additional state labels in
total** at the generating truth.

Unlike the direct arm, those labels remain abundance/activity weighted across contexts.

## Shared data contract

Within each replicate:

- Direct and Passive use the same random seed.
- Their first three streams are structurally identical and appear in the same order.
- The generated opportunistic, calibrated, and original annotated counts must therefore
  be byte-identical.
- Only the fourth calibration stream differs.
- East-heldout scoring uses only the shared original StateAnnotatedCount observations.

If the three base streams are not identical, the replicate fails closed as infrastructure.

## Frozen truth

R7 uses the exact promoted structured R5 truth.

No slope or intercept changes.

## Frozen replication profile

- replicates = 16;
- fits per replicate = 2;
- total fits = 32;
- base seed = 20260928;
- seed stride = 67;
- Direct fit seed = data seed + 1;
- Passive fit seed = data seed + 2;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept = 0.90.

## Primary predictive estimand

For each replicate:

`heldout_gain = Direct east StateAnnotatedCount LPD - Passive east StateAnnotatedCount LPD`.

Requirements:

- heldout_gain > 0 in >= 75% of replicates;
- mean heldout_gain >= 0.005.

## State-recovery estimand

For each fitted arm and replicate, compute the mean absolute posterior-mean error across
the four frozen state environmental slopes.

For each replicate:

`state_error_gain = Passive state MAE - Direct state MAE`.

Positive means Direct recovered state slopes more accurately.

Requirements:

- state_error_gain > 0 in >= 75% of replicates;
- mean state_error_gain > 0.

## Divergence requirement

Across 32 fits:

- mean divergences per fit <= 0.10.

## Interpretation boundary

R7 PASS can support:

> With the same expected number of added state labels, direct conditional state
> calibration provides more useful state information than additional
> abundance/activity-weighted annotations under the declared structured world.

R7 FAIL means the existing R5 evidence cannot distinguish a special information-geometry
benefit from a generic additional-label benefit under this budget-matching contract.

Even PASS does not establish equal field cost, because one conditional direct label and
one passive state-annotated record may have different acquisition costs.
