# v0.5e Evidence-Separation Known-Truth Gate

Status: **FROZEN BEFORE v0.5e OUTCOME**

v0.5e validates evidence-tier separation after the v0.5b hidden-driver failure,
v0.5c tier guard, and v0.5d generative PairEventCount stream.

## Frozen pair-event observation design

PairEventCount is exposed only in the 24 training spaces.

- training event effort = 2.0 per context;
- held-out event effort = 0.0;
- source species = source;
- target species = focal;
- pair-event observation parameter = event_intercept.

Thus event evidence is collected independently of the 12 held-out contexts.

## Frozen worlds

### hidden_event_silent

Ecology is the exact v0.5b hidden-common-driver generating world:

- true beta_partner = 0.0;
- omitted hidden shared driver acts on source and focal;
- hidden source slope = 0.90;
- hidden focal slope = 0.90.

Pair-event truth:

- event_intercept = -8.0.

The fitting model still omits the hidden driver.

### realized_only

Ecology is the v0.5a measured-shared null:

- true beta_partner = 0.0;
- no omitted hidden driver.

Pair-event truth:

- event_intercept = -1.0.

This world contains realized pair events but no directed focal partner effect.

### directed_realized

Ecology is the v0.5a interaction world:

- true beta_partner = +0.75.

Pair-event truth:

- event_intercept = -1.0.

This world contains both a directed predictive effect and realized pair events.

## Frozen claim authorization rule

For each replicate, the total observed training pair-event count is converted into one
authorized pair-specific event record:

- total count > 0 -> raw positive -> authorized positive;
- total count = 0 -> raw negative with negative-evidence gate passed.

The model-only evidence tier is fixed at PREDICTIVE_DEPENDENCE.

The requested tier is CAUSAL.

No functional endpoint and no intervention evidence are supplied.

Therefore:

- no positive event -> maximum tier PREDICTIVE_DEPENDENCE;
- positive event -> maximum tier REALIZED;
- FUNCTIONAL and CAUSAL remain unauthorized in every world.

## Frozen inference profile

- replicates per world = 16;
- worlds = 3;
- fits per replicate = 1;
- total fits = 48;
- credible mass = 0.90;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

Fresh seed family:

- base seed = 20261009;
- seed stride = 83;
- hidden_event_silent offset = 0;
- realized_only offset = 1000000;
- directed_realized offset = 2000000;
- fit seed = data seed + 1.

No scientific or MCMC setting is configurable from the command line.

## Frozen hidden-event-silent criteria

All must pass:

- replicates = 16;
- positive pair-event rate <= 0.25;
- PREDICTIVE_DEPENDENCE authorization rate >= 0.75;
- FUNCTIONAL-or-higher authorization rate = 0.

No beta recovery/refusal criterion is imposed in this world.

This is deliberate: v0.5b already established that beta can be badly confounded by the
hidden driver. v0.5e tests whether claim authorization remains bounded even when inference
is wrong.

## Frozen realized-only criteria

All must pass:

- replicates = 16;
- positive pair-event rate >= 0.875;
- REALIZED authorization rate >= 0.875;
- abs(mean beta bias) <= 0.15;
- beta zero coverage >= 0.75;
- nonzero beta interval rate <= 0.25;
- abs(mean event-intercept bias) <= 0.30;
- event-intercept coverage >= 0.75;
- FUNCTIONAL-or-higher authorization rate = 0.

## Frozen directed-realized criteria

All must pass:

- replicates = 16;
- positive pair-event rate >= 0.875;
- REALIZED authorization rate >= 0.875;
- abs(mean beta bias) <= 0.15;
- beta truth coverage >= 0.75;
- beta interval entirely above zero in >= 0.75;
- abs(mean event-intercept bias) <= 0.30;
- event-intercept coverage >= 0.75;
- FUNCTIONAL-or-higher authorization rate = 0.

## Frozen sampling criterion

Across all 48 fits:

- total divergences / 48 <= 0.10.

## Mechanical decision

v0.5e = PASS only if every frozen criterion above passes.

A failed criterion cannot be repaired inside v0.5e by changing:

- world definitions;
- event effort;
- event intercept truths;
- claim authorization rule;
- seed family;
- MCMC profile;
- recovery thresholds;
- evidence-tier thresholds.

## Interpretation boundary

PASS may support:

> Predictive dependence, realized pair events, and functional/causal claims remain
> separately authorized under known truth. A hidden-driver false partner coefficient does
> not self-promote without pair-event evidence; pair events can authorize REALIZED even
> when beta is zero; and beta plus pair events still cannot self-authorize FUNCTIONAL or
> CAUSAL.

PASS does not establish empirical causality or prove that PairEventCount removes hidden
confounding from beta.
