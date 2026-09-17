# v0.3.1 identification-first promotion gate

Status: **FROZEN BEFORE v0.3.1 promotion outcomes**

This gate supersedes the retired v0.3 promotion interpretation. The archived v0.3
runs remain implementation diagnostics only and cannot promote v0.3.1.

## Principle

v0.3.1 passes only if the framework refuses ecological claims when the observation
design cannot separate ecological and observation processes. Predictable bias under a
misspecified GLM is not a promotion criterion.

## Gate A — claim / identification separation

- posterior contraction may return `Identified` or `NotIdentified` only;
- contraction alone must never return scientific `Supported`;
- a design-uninformed parameter remains distinct from a confounded parameter.

This gate is deterministic and must pass in the unit suite.

## Gate B — stream target sets

For every observation stream:

- non-target taxa contribute no likelihood term;
- a missing data block for a declared target is an error, never an all-zero history;
- in a multi-species model, a stream targeting species A must not create pseudo-absence
  information for species B.

This gate is deterministic and must pass in the unit suite and NumPyro backend tests.

## Gate C — neutral-parameter knockout

For linear suitability

`eta(x) = alpha + beta*x`

the no-effect knockout is

`eta_knockout(x) = alpha`,

not zero total intensity. The v0.3.1 knockout benchmark must use the same baseline
intercept and observation effort geometry as its non-knockout counterpart, with only
`beta = 0` changed.

Frozen execution profile:

- replicates: **100**;
- base seed: **20260920**;
- chains per fit: **2**, sequential;
- warmup draws per chain: **250**;
- retained draws per chain: **300**;
- posterior interval: **90%**.

Pre-outcome criteria:

- `abs(mean posterior beta) <= 0.10`;
- zero coverage in `[0.82, 0.98]`;
- nonzero-interval rate `<= 0.12`;
- mean divergences per fit `<= 0.10`.

The previous v0.3 knockout result cannot be reused because its baseline intensity was
changed by the old knockout semantics.

## Gate D — structural identification negative control

Use an opportunistic presence-only stream with

`log effort(x) = log(e0) + gamma*x`

and ecological intensity

`log lambda(x) = alpha + beta*x`.

With this stream alone, observation rates depend on `beta + gamma`; therefore both
`beta` and `gamma` must be returned as `NotIdentified` by the local sensitivity-rank
diagnostic. `alpha` remains identifiable.

Add a second stream with known effort and the same ecological field. The additional
observation geometry must restore unique sensitivity directions, so both `beta` and
`gamma` must be returned as `Identified`.

Passing this gate is about the framework's refusal/authorization behavior, not about a
posterior mean being numerically close to truth.

## Gate E — all-parameter SBC with ESS-aware finite rank supports

The retired 10-bin total-variation gate is not used.

Frozen v0.3.1 SBC profile:

- prior-predictive replicates: **100**;
- base seed: **20260918**;
- chains per fit: **2**, run sequentially for portability;
- warmup draws per chain: **300**;
- retained draws per chain before ESS thinning: **400**;
- rank draws: ESS-thinned separately for every free parameter and replicate;
- parameters: **all free ecological and observation-process parameters**;
- ECDF evaluation points: **49**;
- familywise level: **alpha = 0.05**;
- null-envelope Monte Carlo simulations: **20,000**;
- envelope seed: **20260919**;
- divergences: mean per fit `<= 0.10`.

For each parameter/replicate, the post-thinning draw count is retained. The null rank is
therefore discrete uniform on `0..m_r` for that replicate-specific support `m_r`. The
calibration decision is a simulation-based simultaneous ECDF envelope over the maximum
absolute deviation across every parameter and every evaluation point. A single parameter
outside the familywise envelope fails the SBC gate.

This is an esdm-specific simulation implementation of the simultaneous-ECDF strategy;
it is not claimed to reproduce the optimization algorithm of Säilynoja, Bürkner &
Vehtari (2022) line-for-line.

## Gate F — pinned semi-synthetic real geography and held-out transfer

Gate F uses real station geometry and a real long-run climate covariate but **does not
use real biological outcomes**. Ecological coefficients, observation effort and all
record counts are generated from known truth through the same esdm graph used for
fitting. Passing Gate F is therefore a semi-synthetic transfer stress test, not empirical
biological validation.

### Frozen source and selection

- source repository: `the-pudding/data`;
- source commit: `3dcb0a80c838ff9503e3957d7e004a7f4b888b0a`;
- source path: `rain/annual_precipitation.csv`;
- pinned source blob SHA: `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`;
- station selection: **the first 120 data rows after the CSV header**, with no
  outcome-dependent filtering;
- real inputs used: station ID, latitude, longitude, and long-run average precipitation;
- source repository license: MIT; underlying climate data provenance: NOAA/NCEI
  GHCN-Daily / US Federal environmental data;
- the source CSV is precipitation-ordered, so this fixture is explicitly a
  **real-geometry stress fixture, not a representative sample of US climate stations**.

### Frozen domain and split

- spatial locations: **120 stations**;
- day-of-year bins: **15, 75, 135, 195, 255, 315**;
- hour bins: **0, 6, 12, 18**;
- total model contexts: **2,880**;
- longitude blocks:
  - west: longitude `< -110`;
  - central: `-110 <= longitude < -85`;
  - east: longitude `>= -85`;
- fitting blocks: **west + central**;
- held-out block: **east**;
- the east block is never used in fitting either the full model or its knockout
  comparator.

### Frozen data-generating truth

The ecological field is

`eta = -1.5 + 0.55*precip_z - 0.25*lat_z`.

`precip_z` and `lat_z` are standardized using the frozen 120-station fixture before the
space-time expansion. Observation effort is a deterministic positive function of real
latitude/longitude plus day-of-year and hour; it is not algebraically proportional to
`precip_z` or `lat_z`.

### Frozen execution profile

- replicated generated datasets: **20**;
- base seed: **20260921**;
- chains per fit: **2**, sequential;
- warmup draws per chain: **200**;
- retained draws per chain: **250**;
- parameter intervals: **90%**;
- every replicate fits two train-block models:
  1. full suitability (`intercept + beta_precip + beta_lat`),
  2. neutral suitability knockout (`intercept` only);
- both models are evaluated on the same held-out east counts;
- held-out score: Poisson log predictive density computed per context by averaging the
  Poisson probability over posterior rate draws before taking the log; scores are then
  averaged over held-out contexts.

### Pre-outcome Gate F criteria

For each ecological slope, across the 20 replicates:

- `abs(mean posterior bias) <= 0.15` for `beta_precip`;
- `abs(mean posterior bias) <= 0.15` for `beta_lat`;
- 90% interval truth coverage `>= 0.75` for each slope.

For held-out transfer:

- full-model minus knockout held-out mean log predictive density is positive in
  **at least 80% of replicates**;
- mean full-minus-knockout held-out gain is **>= 0.01 per context**.

Computation:

- mean divergences per fit across the 40 full/knockout fits is `<= 0.10`.

No threshold is applied to intercept recovery because the held-out comparison and slope
recovery are the declared Gate F targets.

Until the frozen Gate F runner has executed on the pinned source and all Gate F checks
pass, **v0.3.1 status is NOT_READY regardless of Gates A–E**.

## Promotion rule

`v0.3.1 = PASS` only when Gates A–F all pass. No weighted score and no compensating one
failure with another success.
