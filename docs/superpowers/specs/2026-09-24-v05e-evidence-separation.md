# v0.5e Evidence-Separation Known-Truth Benchmark

Status: prospective design, pre-outcome.

Base: v0.5d PairEventCount core at
b4af3e818c0b0391d88a9eb6f345fbc11d947a30.

## Question

Can ESDM keep three distinct statements separate under known truth?

1. a partner field is predictively associated with the focal;
2. a directed source-to-target event was actually observed;
3. the partner has a functional effect on focal ecology.

v0.5e tests the first two while deliberately withholding independent functional and
intervention evidence.

## Pair-event observation design

PairEventCount is exposed only in the 24 training spaces.

- event effort = 2.0 per training context;
- event effort = 0 in all 12 held-out spaces.

Thus realized-event evidence is independent of held-out focal prediction.

## Frozen worlds

### hidden_event_silent

Uses the exact v0.5b hidden-common-driver generating ecology:

- true beta_partner = 0;
- hidden shared environmental slopes = 0.90 for source and focal;
- hidden driver omitted from fitting model.

Pair-event truth:

- event_intercept = -8.0.

This produces an event-silent stress world while retaining the possibility that the
presence-only partner coefficient remains spuriously positive.

### realized_only

Uses the v0.5a measured-shared null ecology:

- true beta_partner = 0;
- no omitted hidden driver.

Pair-event truth:

- event_intercept = -1.0.

Events should be observed even though there is no functional partner coefficient.

### directed_realized

Uses the v0.5a interaction ecology:

- true beta_partner = +0.75.

Pair-event truth:

- event_intercept = -1.0.

Both directed predictive effect and realized event evidence are present.

## Claim authorization

For every replicate, the observed training pair-event count is converted to one
pair-specific authorized record:

- total event count > 0 -> authorized positive;
- total event count = 0 -> authorized negative, with the frozen known-effort negative
  gate passed.

The model evidence tier is fixed at PREDICTIVE_DEPENDENCE.

The benchmark requests CAUSAL and records the actual capped tier.

Because no functional endpoint or intervention is supplied:

- event-silent replicates should remain PREDICTIVE_DEPENDENCE;
- positive-event replicates may reach REALIZED;
- no replicate may reach FUNCTIONAL or CAUSAL.

## Frozen inference profile

Planned:

- 16 replicates per world;
- 3 worlds;
- 48 total fits;
- fresh seed family to be frozen before outcome;
- 300 warmup;
- 350 posterior samples;
- 2 chains;
- 90% intervals;
- target accept = 0.90.

## Planned scientific requirements

hidden_event_silent:

- positive pair-event rate <= 0.25;
- PREDICTIVE_DEPENDENCE authorization rate >= 0.75.

realized_only:

- positive pair-event rate >= 0.875;
- REALIZED authorization rate >= 0.875;
- beta abs mean bias <= 0.15;
- beta zero coverage >= 0.75;
- nonzero beta interval rate <= 0.25;
- event-intercept abs mean bias <= 0.30;
- event-intercept coverage >= 0.75.

directed_realized:

- positive pair-event rate >= 0.875;
- REALIZED authorization rate >= 0.875;
- beta abs mean bias <= 0.15;
- beta coverage >= 0.75;
- beta interval entirely positive in >= 0.75;
- event-intercept abs mean bias <= 0.30;
- event-intercept coverage >= 0.75.

All worlds:

- FUNCTIONAL-or-higher authorization rate = 0;
- mean divergences per fit <= 0.10.

## Interpretation boundary

PASS would establish a clean evidence separation:

- hidden-driver predictive dependence does not self-promote when pair events are absent;
- realized events can be authorized even when beta is zero;
- a positive beta plus events still does not self-authorize functional or causal claims.

PASS would not prove causal interaction. That remains reserved for a future independent
functional/intervention endpoint.
