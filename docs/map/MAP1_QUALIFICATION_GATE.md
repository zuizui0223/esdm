# MAP1 qualification gate

Status: **FROZEN BEFORE ANY MAP1 CONFIRMATORY OUTCOME — EXECUTION NOT AUTHORIZED**

Date frozen: 2026-09-27

## Estimand

MAP1 qualifies one claim only:

`COHERENT_MAP_SUPPORTED`

The claim means that a fixed geography-coherent residual field adds held-out predictive
information beyond both an environment-only model and an equally parameterized
exchangeable residual field, while passing negative controls and the numerical sampling
guardrail.

It does not estimate or interpret a spatial range or a covariance mechanism.

## Replication profile

Exactly **16 independent replicates** are run in each of N0, N1, and P1.

Frozen execution cardinality:

- **48 shards**
- **128 fits**

Each field-positive replicate draws a fresh latent realization before Poisson counts.

## Predictive thresholds

Positive-qualified comparison:

- positive gain rate >= **0.75**
- mean gain >= **0.005** per held-out context

Null-qualified comparison:

- material gain rate above +0.005 <= **0.25**
- mean gain <= **0.005** per held-out context

These values are inherited from earlier eSDM held-out/false-promotion gates and are
frozen before MAP1 outcome execution.

## Worlds

### N0 — no residual field

Truth: B0.

Null-qualified:

- BC - B0 on H1
- BX - B0 on H1
- BC - BX on H1

### N1 — exchangeable residual heterogeneity

Truth: BX.

Null-qualified:

- BC - BX on H1

### P1 — coherent residual field

Truth: BC.

Positive-qualified:

- BC - B0 on H1
- BC - BX on H1

The second P1 comparison is the critical flexibility control: geographic coherence must
beat an equally parameterized latent field, not merely a smaller model.

## Sampling guardrail

Mean NUTS divergences per fit across the complete run must be <= **0.10**.

Confirmatory MCMC profile:

- warmup: **300**
- retained posterior draws: **350**
- chains: **2**
- target accept probability: **0.90**

## Interpretation boundary

A PASS supports predictive map coherence only.

It does not support dispersal, movement, migration, gene flow, environmental isolation,
barriers, an estimated range, or causal connectivity.

## Stop rule

After authorization, no world, graph, holdout, prior, threshold, seed rule, or MCMC
profile may change; no failed comparison may be removed; and no same-program rescue
generation may be created.
