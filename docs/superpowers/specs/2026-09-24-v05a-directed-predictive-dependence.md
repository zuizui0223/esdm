# v0.5a Directed Predictive Dependence Benchmark

Status: **prospective design; pre-qualification**

Base: v0.5 partner-latent core commit `8cff2b1410e5a47c5a81f5c0710abaf55efb0637`.

## Question

Can a one-way partner latent effect be identified, recovered, and transferred under known
truth without producing the same signal when the interaction coefficient is exactly zero?

## Geometry

The benchmark reuses the real station geometry and training-standardized covariates from
the promoted v0.4 semi-synthetic programme, but collapses time to one context per station
for a focused biotic-effect test.

- west + central = training;
- east = held out;
- east remains outside the training eastness range.

## Two species

### Source

Latent log intensity:

`source_intercept + source_beta_precip * precip + source_beta_lat * latitude`.

### Focal

Latent log intensity:

`focal_intercept + focal_beta_precip * precip + focal_beta_eastness * eastness
 + beta_partner * softplus(source_log_intensity)`.

The source species is declared after the focal species in the mapping so the benchmark
also exercises topological latent-field evaluation.

## Observation contract

Each species has its own known-effort PresenceOnly stream:

- effort = 6.0 at every context;
- detection = 0.90;
- no unknown observation parameter.

The focal process reads the source **latent field**, not source counts.

## Frozen worlds

### directed_positive

`beta_partner = +0.80`.

### interaction_null

`beta_partner = 0.0`.

Every other ecological and observation parameter is identical.

## Identification-first gate

Before outcome MCMC, beta_partner must be structurally identified and practically
non-weak in both worlds using the existing exact-JAX diagnostic:

- structural rtol = 1e-8;
- structural atol = 1e-10;
- relative minimum singular value >= 1e-3;
- condition number <= 1e3;
- target SD proxy <= 0.25;
- Fisher ridge = 1e-10.

## Planned replicated outcome

Fresh seed family, to be frozen before execution:

- 16 replicates per world;
- Full + partner-knockout fit per replicate;
- 64 fits total;
- 90% posterior interval for beta_partner;
- east-heldout focal PresenceOnly log predictive density.

## Claim ceiling

Even a complete PASS is capped at:

**PREDICTIVE_DEPENDENCE**.

Presence-only recovery and held-out gain do not demonstrate a realized interaction event,
functional consequence, or causality.

A later v0.5 stage must add an interaction-event observation endpoint before evidence can
rise to REALIZED.
