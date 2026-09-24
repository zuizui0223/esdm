# v0.7b dynamic occupancy recovery and held-out transfer gate

Status: **FROZEN BEFORE ANY v0.7b MCMC OR HELD-OUT OUTCOME**

Date frozen: 2026-09-25

## Question

After dynamic occupancy is structurally/practically identified by a short direct
occupancy calibration window, can the four frozen dynamic parameters be recovered
and does the learned marginal occupancy process improve prediction of later joint
occurrence where no direct occupancy observations are available?

This gate is intentionally narrower than movement or dispersal inference. The
latent state remains a marginal occupancy probability.

## Frozen ecological truth

Exactly the v0.7a truth:

alpha = 0.30
psi_0 = 0.20
gamma = 0.35
epsilon = 0.15

Fitted recovery targets:

- sp.suitability.alpha
- sp.occupancy.psi0_logit
- sp.occupancy.gamma_logit
- sp.occupancy.epsilon_logit

## Frozen temporal split

The full trajectory has 12 ordered contexts.

- training: doy 1-8
- future held-out scoring: doy 9-12
- joint OccupiedPresenceOnly effort = 500 in all 12 contexts
- direct OccupancyCount effort = 500 in contexts 1-4 only
- direct OccupancyCount effort = 0 in contexts 5-12

Thus direct occupancy exposure is exactly zero in every held-out context.

## Frozen prediction semantics

The held-out model is **not** rebuilt only on contexts 9-12.

For posterior prediction, every draw is propagated through the full chronological
trajectory 1-12 from the original initial occupancy. Only the joint occurrence
log predictive density at contexts 9-12 is then scored.

This prevents an artificial reinitialization of occupancy at the held-out boundary.

## Frozen lower-information comparator

The comparator is the explicit occupancy knockout: occupancy = 1.

The information contrast is:

suitability-only < suitability + dynamic occupancy

Both models are fitted on the frozen training contexts and scored on exactly the
same held-out joint occurrence counts with the same Poisson log predictive density.

The direct OccupancyCount stream is never scored in the held-out comparison.

## Pre-MCMC training-design qualification

Before any replicated MCMC may run, the actual 8-context training design must
satisfy all of the following.

For all four recovery targets:

- exact JAX structural status = Identified
- practical diagnostic is not weak
- relative minimum singular value >= 1e-3
- condition number <= 1e3
- target-SD proxy <= 0.35

Shared numerical settings:

- structural rtol = 1e-8
- structural atol = 1e-10
- Fisher ridge = 1e-10

The matched 8-context joint-only design must classify all four free parameters
as NotIdentified.

If qualification fails, the replicated outcome is not authorized.

## Frozen replicated profile

Only after qualification passes:

- replicates = 16
- Full + occupancy-knockout fits per replicate
- total fits = 32
- central posterior interval mass = 0.90
- warmup = 300
- retained posterior draws = 350
- chains = 2
- target accept probability = 0.90

Seed family:

- base seed = 20261029
- stride = 109
- replicate r data seed = 20261029 + 109*r
- Full fit seed = data seed + 1
- occupancy-knockout fit seed = data seed + 2

No scientific or MCMC parameter is configurable from the one-shot runner.

## Frozen recovery criteria

For each of the four targets:

- absolute mean posterior bias <= 0.25 on the fitted parameter scale
- empirical 90% interval coverage >= 0.75

These criteria concern the declared marginal dynamic parameters only.

## Frozen held-out transfer criteria

For every replicate the result artifact must retain both absolute scores:

- full_heldout_log_score
- occupancy_knockout_heldout_log_score

and derive occupancy_gain as their difference.

Required:

- Full > occupancy knockout in >= 75% of replicates
- mean Full-minus-knockout held-out log-score gain >= 0.005

No minimum-gain criterion is imposed across all replicates.

## ODSP readiness requirement

The absolute scores are part of the frozen result schema so the completed result
can be exported without reconstruction as:

- suitability_only: information = [suitability]
- suitability_dynamic_occupancy: information = [suitability, dynamic_occupancy]

Each independent known-truth replicate is one ODSP population group.

The ODSP audit, if run after this gate, is downstream/descriptive and cannot
change the v0.7b promotion decision.

## Sampling criterion

Across all 32 fits, mean divergences per fit <= 0.10.

## Mechanical decision

v0.7b = PASS only if all frozen qualification, refusal, recovery, held-out
transfer, absolute-score serialization and sampling checks pass.

A failed result may not be repaired inside v0.7b by changing:

- truth
- 8/4 temporal split
- direct occupancy exposure
- comparator
- posterior prediction chronology
- seed family
- MCMC settings
- recovery thresholds
- held-out score definition
- transfer thresholds

A material infrastructure bug invalidates the affected run; repair requires an
explicit replacement authorization that preserves every scientific element above.

## Interpretation boundary

PASS may support:

> A directly calibrated marginal colonization-extinction occupancy process can be
> recovered under the frozen known-truth design and can retain held-out predictive
> value for later joint occurrence after direct occupancy observations cease.

PASS does **not** establish:

- realized binary occupancy histories
- observed colonization/extinction events
- dispersal or movement kernels
- connectivity or resistance
- source-sink or rescue dynamics
- causal movement limitation
- empirical biological validity
