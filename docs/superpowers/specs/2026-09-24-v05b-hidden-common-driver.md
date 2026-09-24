# v0.5b Hidden Common Driver Stress Test

Status: **prospective misspecification test, pre-outcome**

Base: frozen v0.5a PASS head `00f423e231da037a4dce0b89cce6cf91a991f2f0`.

## Purpose

v0.5a showed that measured shared environmental response does not automatically create a
false directed partner effect.

v0.5b asks the harder question:

> Does the same partner-latent model refuse an interaction when source and focal share an
> important **unmeasured** environmental driver?

## Generating world

True directed partner coefficient:

`beta_partner = 0`.

The generating model contains one hidden environmental driver that affects both source
and focal positively.

To make the stress test nontrivial, the hidden driver is partially correlated with the
measured source-specific driver. Therefore the fitted source latent field can proxy part
of the omitted shared environment.

Generating hidden coefficients:

- source hidden slope = 0.90;
- focal hidden slope = 1.00.

## Fitting model

The fitted Full model is exactly the v0.5a model:

- source-specific measured driver;
- focal-specific measured driver;
- measured shared environment;
- PartnerIntensityEffect.

The hidden driver is absent from the fitted covariates.

The reference model is the exact partner-effect knockout.

## Frozen outcome profile

Planned gate:

- 16 fresh replicates;
- Full + knockout fits per replicate;
- 32 total fits;
- 90% posterior intervals;
- fresh seed family to be frozen before outcome;
- 300 warmup;
- 350 posterior samples;
- 2 chains;
- target accept = 0.90.

## Robustness criteria

The current v0.5 model passes hidden-driver robustness only if all hold:

- abs(mean fitted beta) <= 0.10;
- zero coverage >= 0.75;
- nonzero 90% interval rate <= 0.25;
- mean Full-minus-knockout heldout gain <= 0.005;
- material positive gain >0.005 in <=0.25 of replicates;
- mean divergences per fit <=0.10.

## Interpretation

A PASS would show robustness to this declared hidden-driver geometry.

A FAIL is scientifically informative and is **not** grounds for retuning v0.5b. It would
establish that latent-distribution data alone do not protect the directed coefficient
against this omitted shared cause, motivating an independent interaction-event endpoint.

Neither PASS nor FAIL establishes empirical causality.
