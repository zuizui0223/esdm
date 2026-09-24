# v0.5a Directed Interaction Known-Truth Gate

Status: **FROZEN BEFORE v0.5a IDENTIFICATION OR MCMC OUTCOME**

v0.5a is the first promotion-oriented gate for the directed partner-latent process.

## Frozen model

Two species:

- source;
- focal.

Source log intensity contains:

- source intercept;
- source-specific environmental driver;
- measured shared environment.

Focal log intensity contains:

- focal intercept;
- focal-specific environmental driver;
- measured shared environment;
- directed PartnerIntensityEffect from source latent log intensity.

The focal process reads source latent ecology only. Raw source observations are not used
as focal ecological covariates.

## Frozen worlds

### Interaction world

`beta_partner = +0.75`.

All environmental coefficients remain at their frozen fixture values.

### Measured-shared-environment null

`beta_partner = 0.0`.

All other source/focal environmental coefficients are identical to the interaction world.
Source and focal therefore remain correlated through a measured shared environment even
when no directed partner effect exists.

## Frozen geometry

- 36 spatial contexts;
- 24 training spaces;
- 12 held-out spaces;
- one day/hour context;
- source-specific, focal-specific, and shared environmental covariates fixed by code;
- source and focal PresenceOnly effort = 6.0 in every context.

## Frozen interaction target

`focal.partner_effect.beta_partner`.

## Frozen pre-MCMC identification gate

Both worlds must pass:

- exact JAX Jacobian structural identification;
- relative rank rtol = 1e-8;
- absolute rank atol = 1e-10;
- relative minimum singular value >= 1e-3;
- condition number <= 1e3;
- target SD proxy <= 0.25;
- Fisher ridge = 1e-10.

If either world's structural or practical identification fails, v0.5a = FAIL and the
replicated MCMC outcome is not run.

## Frozen replicated outcome profile

Only after identification qualification passes:

- replicates per world = 16;
- worlds = 2;
- fits per replicate = 2 (Full + partner knockout);
- total fits = 64;
- credible mass = 0.90;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

Fresh seed family:

- base seed = 20261001;
- seed stride = 73;
- null-world offset = 1000000;
- interaction replicate r seed = 20261001 + 73*r;
- null replicate r seed = 20261001 + 1000000 + 73*r;
- Full fit seed = generated-data seed + 1;
- knockout fit seed = generated-data seed + 2.

No scientific or MCMC control is configurable from the command line.

## Frozen positive-world recovery criteria

Interaction world must satisfy all:

- abs(mean beta bias) <= 0.15;
- 90% beta interval coverage >= 0.75;
- 90% beta interval entirely above zero in >= 0.75 of replicates;
- Full held-out focal log score > knockout in >= 0.75 of replicates;
- mean Full-minus-knockout held-out gain >= 0.005.

## Frozen measured-shared-null criteria

Null world must satisfy all:

- abs(mean fitted beta) <= 0.10;
- 90% interval coverage of beta=0 >= 0.75;
- nonzero 90% interval rate <= 0.25;
- mean Full-minus-knockout held-out gain <= 0.005;
- proportion with held-out gain > 0.005 <= 0.25.

The null world is allowed to prefer the simpler knockout.

## Frozen divergence criterion

Across all 64 fits:

- total divergences / 64 <= 0.10.

## Mechanical decision

v0.5a = PASS only if:

1. interaction structural identification passes;
2. interaction practical identification passes;
3. null structural identification passes;
4. null practical identification passes;
5. interaction replicate count = 16;
6. null replicate count = 16;
7. total fit count = 64;
8. every positive-world recovery/transfer criterion passes;
9. every null-world refusal criterion passes;
10. divergence criterion passes.

No failed term may be repaired inside v0.5a by changing truth, geometry, covariates,
thresholds, seed family, prior, MCMC controls, or held-out score.

## Interpretation boundary

PASS may support:

> One directed partner-latent effect is identifiable, recoverable, and predictively useful
> under the declared measured-environment world, while the same signal is refused when
> source and focal share only a measured environmental driver.

PASS does **not** establish:

- hidden-common-driver robustness;
- causal biotic interaction in empirical data;
- realized interaction events;
- reciprocal interaction;
- v0.5 promotion beyond this measured-environment scope.

Hidden shared drivers require a separate fresh programme, ideally with an independent
interaction-event endpoint.
