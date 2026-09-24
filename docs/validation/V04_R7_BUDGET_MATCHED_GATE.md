# v0.4-R7 Budget-Matched Calibration Gate

Status: **FROZEN BEFORE R7 OUTCOME**

R7 compares two additional calibration channels under the same expected added state-label
budget. It is designed to separate an information-geometry effect from a generic
additional-data effect.

## Frozen base model and truth

Both arms inherit the exact promoted v0.4 structured truth and R4 base observation design.

Unchanged base streams:

- opportunistic PresenceOnly;
- calibrated PresenceOnly;
- original StateAnnotatedCount.

The original three generated streams must be identical between paired arms within each
replicate.

## Direct arm

The fourth stream is the promoted StateCompositionCount:

- exact R4 36×12 training contexts;
- effort = 1.0 at every exposed context;
- 432 exposed contexts;
- total expected direct state labels = 432.0;
- consumes only conditional state composition;
- zero east-heldout exposure.

## Passive arm

The fourth stream is an additional ordinary StateAnnotatedCount:

- exact same R4 36×12 training contexts;
- known detection = 0.85;
- zero east-heldout exposure;
- constant effort across all 432 exposed contexts;
- consumes ecological intensity × activity × state composition.

The passive effort is frozen by:

`passive_effort = 432 / sum_c exp(log_intensity_c) * activity_c * 0.85`

where the sum is over the exact 432 R4 training contexts and is evaluated at the already
frozen promoted structured truth.

Therefore:

- total expected passive labels = 432.0;
- total expected direct labels = 432.0.

No R7 outcome is used to set passive effort.

## Pairing contract

Within each replicate:

1. Direct and Passive use the exact same data-generation seed.
2. The first three streams are generated before the fourth stream in both models.
3. Opportunistic, calibrated, and original annotated count maps must be exactly equal.
4. If those base observations differ, the replicate fails closed as infrastructure.
5. Only the fourth calibration stream differs between arms.
6. East-heldout scoring uses only the shared original StateAnnotatedCount data.

## Frozen replication/MCMC profile

- replicates = 16;
- fits per replicate = 2;
- total fits = 32;
- base seed = 20260928;
- seed stride = 67;
- Direct fit seed = replicate seed + 1;
- Passive fit seed = replicate seed + 2;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

Replicate r uses:

`20260928 + 67*r`, for r = 0,...,15.

No scientific or MCMC setting is configurable from the command line.

## Frozen predictive estimand

For each replicate:

`heldout_gain = Direct east StateAnnotatedCount LPD - Passive east StateAnnotatedCount LPD`.

Required:

- heldout_gain > 0 in >= 75% of replicates;
- mean heldout_gain >= 0.005.

## Frozen state-recovery estimand

The four state environmental slopes are:

- beta_foraging_precip;
- beta_foraging_eastness;
- beta_foraging_season;
- beta_foraging_hour.

Within each arm and replicate, compute the mean absolute posterior-mean error across these
four slopes.

For each replicate:

`state_error_gain = Passive state MAE - Direct state MAE`.

Required:

- state_error_gain > 0 in >= 75% of replicates;
- mean state_error_gain > 0.

## Frozen budget checks

At aggregation:

- Direct expected labels = 432.0 within absolute tolerance 1e-8;
- Passive expected labels = 432.0 within absolute tolerance 1e-8;
- all paired replicates preserve identical base observations.

Realized label totals are recorded as diagnostics but are not gate criteria because both
arms use Poisson count observation models.

## Divergence criterion

Across all 32 fits:

- total divergences / 32 <= 0.10.

## Mechanical decision

R7 = PASS only if all of the following pass:

1. replicates = 16;
2. fits = 32;
3. all paired base observations are identical;
4. Direct expected labels = 432.0;
5. Passive expected labels = 432.0;
6. heldout positive-gain rate >= 0.75;
7. mean heldout gain >= 0.005;
8. state-error positive-gain rate >= 0.75;
9. mean state-error gain > 0;
10. mean divergences per fit <= 0.10.

No failed term can be repaired inside R7 by changing the budget definition, passive
effort, score, recovery target, threshold, seed family, or MCMC profile.

## Interpretation boundary

R7 PASS may support:

> At equal expected added state-label count, direct conditional state calibration carries
> more useful information for state-effect recovery and east-heldout prediction than
> additional abundance/activity-weighted state annotation in the declared structured
> world.

R7 PASS does not prove equal field cost per label or universal superiority of one
sampling protocol.

R7 FAIL means the existing R5 evidence cannot distinguish a special information-geometry
benefit from a generic additional-label benefit under this budget-matched contract.
