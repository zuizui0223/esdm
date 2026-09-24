# v0.5a Directed Partner Identification Gate

Status: **FROZEN BEFORE v0.5a IDENTIFICATION OUTCOME**

This gate qualifies the first directed partner-latent process before any replicated MCMC
outcome is allowed.

## Target

`focal.partner_effect.beta_partner`

The process is:

`focal log-intensity += beta_partner * softplus(source latent log-intensity)`.

## Frozen geometry and observation contract

- real station geometry inherited from the v0.4 semi-synthetic source;
- one temporal context per station;
- west + central training;
- east held out;
- source PresenceOnly effort = 6.0, detection = 0.90;
- focal PresenceOnly effort = 6.0, detection = 0.90;
- no free observation parameter;
- focal species reads source latent intensity, never source counts.

## Frozen worlds

### directed_positive

`beta_partner = +0.80`.

### interaction_null

`beta_partner = 0.0`.

Every other ecological and observation parameter is identical.

## Exact identification diagnostic

Both worlds must be evaluated on the training block using:

- backend: JAX exact Jacobian;
- structural rtol = 1e-8;
- structural atol = 1e-10;
- practical relative minimum singular value >= 1e-3;
- practical condition number <= 1e3;
- target SD proxy <= 0.25;
- Fisher ridge = 1e-10.

## Mechanical qualification

v0.5a identification qualification = PASS only if beta_partner is:

1. structurally Identified in directed_positive;
2. practically non-weak in directed_positive;
3. structurally Identified in interaction_null;
4. practically non-weak in interaction_null.

No MCMC is allowed before all four terms pass.

## Planned post-qualification outcome profile

If and only if this gate passes, a separate frozen outcome gate may authorize:

- 16 replicates per world;
- Full and partner-knockout fits;
- 64 total fits;
- fresh seeds;
- beta recovery;
- east-heldout focal predictive gain;
- null-world false-positive refusal.

The exact outcome thresholds must be frozen before those MCMC outcomes.

## Claim ceiling

Even complete v0.5a qualification/outcome PASS is capped at
`PREDICTIVE_DEPENDENCE`.

No interaction event endpoint is present here, so this gate cannot establish REALIZED,
FUNCTIONAL, or CAUSAL interaction evidence.
