# v0.5b Hidden Common Driver Robustness Gate

Status: **FROZEN BEFORE v0.5b OUTCOME**

v0.5b is a deliberate model-misspecification stress test.

## Frozen fitting model

The fitting model is exactly the v0.5a model that passed the measured-shared-environment
programme:

- source measured source-specific driver;
- focal measured focal-specific driver;
- measured shared environment in both species;
- PartnerIntensityEffect from source latent field to focal;
- separate source/focal PresenceOnly streams;
- known effort = 6.0.

No hidden covariate is available to the fitting model.

## Frozen generating world

True directed partner coefficient:

`beta_partner = 0.0`.

The generating model adds one hidden common driver to both species.

Hidden coefficients:

- source hidden slope = 0.90;
- focal hidden slope = 1.00.

The hidden driver is fixed by code as a combination of:

- 0.75 × measured source-specific driver;
- an additional sinusoidal component absent from all fitted covariates.

Thus the hidden driver is neither independent of the modeled source field nor identical
to any fitted covariate.

## Frozen geometry

Inherited exactly from v0.5a:

- 36 spaces;
- 24 training spaces;
- 12 held-out spaces;
- one day/hour context;
- separate source/focal PresenceOnly streams.

## Frozen target

`focal.partner_effect.beta_partner`.

Truth = 0.

## Frozen replicated profile

- replicates = 16;
- fits per replicate = 2 (Full + partner knockout);
- total fits = 32;
- credible mass = 0.90;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

Fresh seed family:

- base seed = 20261005;
- seed stride = 83;
- replicate r seed = 20261005 + 83*r;
- Full fit seed = data seed + 1;
- knockout fit seed = data seed + 2.

No scientific or MCMC control is configurable from the command line.

## Frozen robustness criteria

The existing partner-latent model passes this hidden-driver stress test only if all hold:

- abs(mean fitted beta) <= 0.10;
- 90% interval coverage of beta=0 >= 0.75;
- nonzero 90% interval rate <= 0.25;
- mean Full-minus-knockout held-out focal log-score gain <= 0.005;
- proportion with held-out gain > 0.005 <= 0.25;
- total divergences / 32 <= 0.10.

## Mechanical decision

v0.5b = PASS only if:

1. replicates = 16;
2. fits = 32;
3. mean beta criterion passes;
4. zero-coverage criterion passes;
5. nonzero-interval criterion passes;
6. mean held-out gain criterion passes;
7. material-gain-rate criterion passes;
8. divergence criterion passes.

No failed criterion may be repaired inside v0.5b by changing the hidden-driver geometry,
thresholds, seed family, priors, MCMC controls, held-out score, or target.

## Interpretation

A PASS supports robustness to this declared omitted shared cause.

A FAIL is an expected and scientifically useful possibility. It would show that a
partner-latent distribution model can mistake an omitted shared cause for a directed
biotic effect even though measured shared environment was safely handled in v0.5a.

A FAIL therefore motivates, rather than invalidates, the planned independent
interaction-event observation layer.

Neither outcome establishes empirical causality.
