# v0.5f Directed Interaction Transfer Replication Gate

Status: **FROZEN BEFORE v0.5f IDENTIFICATION OR MCMC OUTCOME**

Date frozen: 2026-09-25

## Purpose

v0.5f is an independent-seed replication of the already frozen v0.5a directed
partner-latent known-truth programme.

It does not modify or replace v0.5a.

Its scientific model, worlds, geometry, identification criteria, MCMC profile,
recovery criteria, null-refusal criteria, divergence criterion and interpretation
boundary are inherited unchanged from v0.5a.

The only new requirement is result serialization: every replicate must preserve
the original absolute Full and partner-knockout held-out log predictive densities
in addition to their difference, so a completed result can be audited as a strict
ODSP information contrast without reconstructing a baseline.

## Frozen inherited model

Exactly the v0.5a model:

- source suitability from source-specific plus measured shared environment;
- focal suitability from focal-specific plus measured shared environment;
- one directed PartnerIntensityEffect from source latent log intensity to focal;
- PresenceOnly observation streams for source and focal;
- no raw source observation used as a focal ecological covariate.

## Frozen inherited worlds

### Interaction world

beta_partner = +0.75.

### Measured-shared-environment null

beta_partner = 0.0.

All non-interaction ecological and observation parameters are identical to v0.5a.

## Frozen inherited geometry

- 36 spatial contexts;
- 24 training spaces;
- 12 held-out spaces;
- one day/hour context;
- source and focal PresenceOnly effort = 6.0 in every context;
- exact v0.5a covariate fields and held-out split.

## Frozen inherited identification thresholds

Both worlds must pass the exact v0.5a pre-MCMC gate:

- JAX structural identification;
- rank rtol = 1e-8;
- rank atol = 1e-10;
- relative minimum singular value >= 1e-3;
- condition number <= 1e3;
- target SD proxy <= 0.25;
- Fisher ridge = 1e-10.

The qualification implementation is the existing v0.5a qualification.

## Frozen replicated profile

Exactly the v0.5a profile:

- 16 replicates per world;
- 2 worlds;
- 2 fits per replicate: Full + partner knockout;
- total fits = 64;
- credible mass = 0.90;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

## Fresh disjoint seed family

v0.5f uses a new seed family that is disjoint from v0.5a:

- base seed = 20271001;
- seed stride = 73;
- null-world offset = 1000000;
- interaction replicate r seed = 20271001 + 73*r;
- null replicate r seed = 20271001 + 1000000 + 73*r;
- Full fit seed = generated-data seed + 1;
- knockout fit seed = generated-data seed + 2.

No scientific or MCMC control is configurable from the command line.

## Frozen inherited positive-world criteria

Exactly v0.5a:

- abs(mean beta bias) <= 0.15;
- 90% beta interval coverage >= 0.75;
- positive 90% interval rate >= 0.75;
- Full held-out focal log score > knockout in >= 0.75 of replicates;
- mean Full-minus-knockout held-out gain >= 0.005.

## Frozen inherited null-world criteria

Exactly v0.5a:

- abs(mean fitted beta) <= 0.10;
- 90% interval coverage of beta=0 >= 0.75;
- nonzero 90% interval rate <= 0.25;
- mean Full-minus-knockout held-out gain <= 0.005;
- proportion with held-out gain > 0.005 <= 0.25.

## Frozen inherited divergence criterion

Across all 64 fits:

- total divergences / 64 <= 0.10.

## New mandatory absolute-score serialization

Each replicate result must retain:

- full_heldout_log_score;
- partner_knockout_heldout_log_score.

The derived heldout_gain must equal:

full_heldout_log_score - partner_knockout_heldout_log_score

within absolute numerical tolerance 1e-12.

No synthetic zero baseline, gain-only reconstruction or post-hoc score recovery is
allowed.

## ODSP-ready information contrast

Only the interaction-world records are eligible for the downstream positive
interaction-value audit.

The frozen information filtration is:

measured_environment
  subset
measured_environment + directed_partner_latent

with score fields:

- lower: partner_knockout_heldout_log_score;
- upper: full_heldout_log_score.

Both scores are mean held-out Poisson log predictive densities on the identical
12 focal PresenceOnly held-out contexts.

The measured-shared-null world remains a specificity/refusal control and is not
mixed into the interaction-world population transfer payload.

## Mechanical decision

v0.5f = PASS only if:

1. all 18 inherited v0.5a gate checks pass under the fresh seed family;
2. all 32 replicate records retain both finite absolute held-out scores;
3. every recorded gain matches Full-minus-knockout within 1e-12.

The original v0.5a gate result is not reopened or replaced.

## Interpretation boundary

PASS may support:

> The frozen v0.5a directed partner-latent result independently replicates under
> a disjoint seed family, and the positive interaction-world predictive increment
> can be serialized from original absolute held-out scores as a downstream ODSP
> information-transfer source.

PASS does **not** establish:

- hidden-common-driver robustness;
- causal interaction in empirical data;
- realized interaction events;
- reciprocal interaction;
- a new interaction mechanism;
- empirical biological validity;
- EOG consumption or N4 survey action.
