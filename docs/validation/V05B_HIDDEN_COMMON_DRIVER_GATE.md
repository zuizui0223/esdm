# v0.5b Hidden Common-Driver Stress Gate

Status: **FROZEN BEFORE v0.5b OUTCOME**

v0.5b is a misspecification stress test of the directed PartnerIntensityEffect.

The true directed coefficient is zero. Source and focal are instead driven by a shared
environmental process that is omitted from the fitting model.

## Frozen base

Base result: v0.5a PASS at
`00f423e231da037a4dce0b89cce6cf91a991f2f0`.

The v0.5b fitting model is exactly the v0.5a model class:

- source-specific measured driver;
- focal-specific measured driver;
- measured shared environment;
- optional directed PartnerIntensityEffect;
- separate source/focal PresenceOnly streams.

The fitting model does not receive the hidden driver.

## Frozen generating world

True directed partner coefficient:

`beta_partner = 0.0`.

A `hidden_shared` covariate is added to both source and focal generating suitability.

Before training standardization, for ordered context index i:

`raw_hidden_i = 0.80 * source_driver_i
                + 0.65 * sin(2*pi*i/13)
                - 0.30 * cos(2*pi*i/5)`.

The raw hidden driver is standardized using the 24 training contexts only and then
applied to all 36 contexts.

Generating coefficients:

Source:
- source intercept = 0.40;
- source driver slope = 0.55;
- measured shared slope = 0.55;
- hidden shared slope = 0.90.

Focal:
- focal intercept = -0.10;
- focal driver slope = 0.65;
- measured shared slope = 0.60;
- hidden shared slope = 0.90;
- partner coefficient = 0.0.

The hidden driver is partly aligned with the observed source-specific driver so the fitted
source latent field can act as a proxy for omitted focal environment. This is deliberate
stress, not an accidental misspecification.

## Frozen geometry and observation design

Unchanged from v0.5a:

- 36 spatial contexts;
- first 24 are training;
- final 12 are held out;
- one temporal context;
- source/focal PresenceOnly effort = 6.0 everywhere;
- known constant detection.

Held-out scoring uses focal PresenceOnly data.

## Frozen execution profile

- replicates = 16;
- Full + partner-knockout fits per replicate;
- total fits = 32;
- base seed = 20261005;
- seed stride = 79;
- replicate r seed = 20261005 + 79*r;
- Full fit seed = data seed + 1;
- knockout fit seed = data seed + 2;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- credible mass = 0.90;
- target accept probability = 0.90.

No scientific or MCMC control is configurable from the command line.

## Frozen refusal criteria

The refusal thresholds are copied unchanged from the v0.5a measured-shared null.

All must pass:

- replicates = 16;
- fits = 32;
- abs(mean fitted beta) <= 0.10;
- 90% zero coverage >= 0.75;
- nonzero 90% interval rate <= 0.25;
- mean Full-minus-knockout held-out gain <= 0.005;
- proportion with held-out gain > 0.005 <= 0.25;
- mean divergences per fit <= 0.10.

## Mechanical decision

v0.5b = PASS only if all frozen refusal criteria pass.

A failed criterion is a valid scientific failure. It cannot be repaired inside v0.5b by
changing hidden-driver strength, hidden-driver alignment, seed family, priors, MCMC
settings, score definition, or refusal threshold.

## Interpretation

PASS would support robustness to this specific omitted common-driver proxy stress.

FAIL would show that latent-field coupling plus presence-only data cannot, by itself,
separate a true directed partner effect from this omitted shared driver. That would set a
clear claim ceiling below causal/realized interaction and motivate an independent
interaction-event observation channel.
