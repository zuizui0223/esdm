# v0.5b Hidden Common Driver Stress Test

Status: **prospective design, pre-outcome**

Base: frozen v0.5a PASS head `00f423e231da037a4dce0b89cce6cf91a991f2f0`.

## Purpose

v0.5a showed that a directed partner-latent effect can be recovered when present and is
not reproduced by a **measured** shared environmental driver.

v0.5b asks the harder question:

> Does the same fitting model spuriously infer a partner effect when source and focal are
> jointly driven by an omitted common environmental process?

## Generating world

True directed partner effect:

`beta_partner = 0`.

The generating source and focal both contain an additional `hidden_shared` environmental
covariate that is absent from the fitting model.

The hidden driver is deterministic and frozen before outcome:

- partly aligned with the source-specific observed driver;
- partly independent nonlinear spatial variation;
- standardized using training contexts only.

Generating coefficients:

- source hidden-driver slope = 0.90;
- focal hidden-driver slope = 0.90.

This deliberately creates a difficult proxy-confounding world: the fitted source latent
field can become correlated with omitted focal environmental structure.

## Fitting model

Exactly the v0.5a directed model:

- source-specific observed driver;
- focal-specific observed driver;
- measured shared environment;
- optional directed PartnerIntensityEffect.

The fitting model never receives `hidden_shared`.

## Frozen refusal criteria

Use the **same null refusal thresholds as v0.5a**, without relaxation:

- abs(mean fitted beta) <= 0.10;
- 90% zero coverage >= 0.75;
- nonzero 90% interval rate <= 0.25;
- mean Full-minus-knockout held-out gain <= 0.005;
- material held-out gain > 0.005 in <= 0.25 of replicates.

## Frozen execution profile

- replicates = 16;
- Full + partner-knockout fits per replicate;
- total fits = 32;
- fresh base seed = 20261005;
- seed stride = 79;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- credible mass = 0.90;
- target accept = 0.90.

## Interpretation

PASS would show robustness to this specific omitted common-driver stress.

FAIL would be equally informative: it would establish that presence-only latent-field
coupling alone cannot distinguish true directed effects from this hidden-driver proxy
world. That failure would directly motivate an independent interaction-event endpoint.

No tuning is allowed inside v0.5b after outcome.
