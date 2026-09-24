# v0.6a Accessibility Known-Truth Gate

Status: **FROZEN BEFORE v0.6a IDENTIFICATION OR MCMC OUTCOME**

v0.6a tests whether static suitability and accessibility can be separated only when the
observation design supplies an independent accessibility endpoint.

## Frozen positive model

One species with two ecological processes.

Suitability:
- intercept = 0.30;
- habitat slope = +0.75.

Accessibility:
- logit intercept = 0.40;
- distance slope = -1.10.

The habitat and distance covariates are deterministic non-collinear spatial contrasts
defined in the frozen fixture.

## Frozen observation design

### Joint occurrence stream

AccessiblePresenceOnly:
- effort = 8.0 in all 36 contexts;
- rate = ecological intensity * accessibility * effort.

### Direct accessibility stream

AccessibilityCount:
- effort = 20.0 in the first 24 training contexts;
- effort = 0.0 in the final 12 held-out contexts;
- rate = accessibility * effort.

The direct accessibility endpoint therefore has **zero held-out exposure**.

Train/heldout split:
- training spaces = first 24;
- held-out spaces = final 12.

## Frozen recovery targets

Exactly four:

- `sp.suitability.suitability_intercept = 0.30`;
- `sp.suitability.beta_habitat = +0.75`;
- `sp.accessibility.access_intercept = 0.40`;
- `sp.accessibility.beta_distance = -1.10`.

## Frozen pre-MCMC identification qualification

All four positive targets must pass:

- exact JAX structural identification;
- relative rank rtol = 1e-8;
- absolute rank atol = 1e-10;
- relative minimum singular value >= 1e-3;
- condition number <= 1e3;
- target SD proxy <= 0.25;
- Fisher ridge = 1e-10.

### Joint-only refusal

A separate 12-context control contains:

- intercept-only suitability;
- intercept-only accessibility;
- only AccessiblePresenceOnly.

Both:
- `sp.suitability.suitability_intercept`;
- `sp.accessibility.access_intercept`

must return exact-JAX `NotIdentified`.

If positive qualification or joint-only refusal fails, v0.6a = FAIL and replicated MCMC
must not run.

## Frozen replicated outcome profile

Only after qualification passes:

- replicates = 16;
- Full + accessibility-knockout fits per replicate;
- total fits = 32;
- credible mass = 0.90;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

Fresh seed family:
- base seed = 20261013;
- seed stride = 89;
- replicate r data seed = 20261013 + 89*r;
- Full fit seed = data seed + 1;
- accessibility-knockout fit seed = data seed + 2.

No scientific or MCMC setting is configurable from the command line.

## Frozen recovery criteria

For every one of the four targets:

- abs(mean posterior bias) <= 0.15;
- empirical 90% interval coverage >= 0.75.

## Frozen held-out transfer criterion

Held-out scoring uses only AccessiblePresenceOnly counts in the 12 held-out contexts.

The accessibility knockout sets accessibility exactly to 1.

Required:
- Full > accessibility knockout in >= 75% of replicates;
- mean Full-minus-knockout held-out log-score gain >= 0.005.

The direct AccessibilityCount stream is never scored in held-out transfer and has zero
held-out exposure.

## Frozen sampling criterion

Across all 32 fits:
- total divergences / 32 <= 0.10.

## Mechanical decision

v0.6a = PASS only if every frozen qualification, refusal, recovery, transfer, and
sampling criterion passes.

No failed criterion may be repaired inside v0.6a by changing:
- truth coefficients;
- covariates;
- train/heldout split;
- observation efforts;
- direct-calibration exposure;
- seed family;
- MCMC settings;
- recovery thresholds;
- held-out score.

## Interpretation boundary

PASS may support:

> Suitability and static accessibility can be separately estimated when an independent
> accessibility endpoint is available in training, while a joint-only product-confounded
> design is correctly refused. The learned accessibility component can retain predictive
> value where direct accessibility observations are unavailable.

PASS does not establish dynamic dispersal, movement kernels, colonization/extinction,
connectivity, or causal movement limitation.
