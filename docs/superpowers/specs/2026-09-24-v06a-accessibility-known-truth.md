# v0.6a Accessibility Known-Truth Programme

Status: prospective design, pre-outcome.

Base: v0.6 accessibility core head
`d9de5288e76735230a8dc9939f7b546311c66dab`.

## Question

Can habitat suitability and accessibility be separated, recovered, and transferred when
a direct accessibility endpoint is available, while an exactly confounded joint-only
design is refused?

## Positive world

One species across 36 spatial contexts.

Latent suitability:

- intercept = 0.30;
- habitat slope = +0.75.

Latent accessibility:

- logit intercept = 0.40;
- distance slope = -1.10.

The deterministic habitat and distance covariates are non-collinear oscillatory spatial
contrasts fixed in code before outcome.

## Observation design

### Joint occurrence

AccessiblePresenceOnly:

- effort = 8.0 in all 36 contexts;
- rate = ecological intensity × accessibility × effort.

### Direct accessibility calibration

AccessibilityCount:

- effort = 20.0 in the first 24 training contexts;
- effort = 0 in the final 12 held-out contexts;
- rate = accessibility × effort.

Thus held-out prediction receives no direct accessibility observations.

Train/heldout split:

- first 24 spaces: training;
- final 12 spaces: held out.

## Pre-MCMC qualification

All four positive targets must pass exact-JAX structural and practical identification:

- suitability intercept;
- habitat slope;
- accessibility intercept;
- distance slope.

Practical thresholds:

- relative minimum singular value >= 1e-3;
- condition number <= 1e3;
- target SD proxy <= 0.25;
- relative rank rtol = 1e-8;
- absolute rank atol = 1e-10;
- Fisher ridge = 1e-10.

## Frozen refusal control

A separate 12-context model contains:

- intercept-only suitability;
- intercept-only accessibility;
- only AccessiblePresenceOnly.

The two intercepts enter one product.

Both intercept targets must return exact-JAX `NotIdentified`.

This refusal is part of the v0.6a gate and cannot be relaxed after outcome.

## Planned replicated outcome

Only after qualification passes:

- 16 fresh replicates;
- Full + accessibility-knockout fits per replicate;
- 32 total fits;
- 90% posterior intervals;
- fresh seed family to be frozen before outcome;
- 300 warmup;
- 350 posterior samples;
- 2 chains;
- target accept = 0.90.

## Recovery requirements

For all four targets:

- abs mean bias <= 0.15;
- empirical 90% interval coverage >= 0.75.

## Held-out transfer

Held-out score uses only the 12-context AccessiblePresenceOnly endpoint.

The accessibility knockout sets accessibility exactly to one.

Required:

- Full beats knockout in >= 75% of replicates;
- mean Full-minus-knockout held-out log-score gain >= 0.005.

## Sampling requirement

- mean divergences per fit <= 0.10.

## Interpretation boundary

PASS may support:

> Static environmental suitability and accessibility can be separated when an independent
> accessibility endpoint is available in training, and the recovered accessibility
> process can improve joint occurrence prediction where direct accessibility observations
> are absent.

PASS does not establish dynamic dispersal, colonization, movement kernels, connectivity,
or causal movement limitation.
