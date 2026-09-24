# v0.5a Directed Interaction Known-Truth Programme

Status: **prospective design, pre-outcome**

Base: v0.5 directed partner-latent core at
`8cff2b1410e5a47c5a81f5c0710abaf55efb0637`.

## Question

Can ESDM recover a directed partner-latent effect when it exists, while refusing the
same interaction signal when source and focal only co-vary through a measured shared
environment?

## Two fresh worlds

### Interaction world

- source responds to a source-specific driver and shared environment;
- focal responds to a focal-specific driver and shared environment;
- focal additionally receives a directed partner-latent effect;
- true `beta_partner = +0.75`.

### Measured-shared-environment null

The exact same environmental responses are retained, but:

- true `beta_partner = 0`.

This is a difficult but model-contained null: source and focal can still be strongly
correlated because both respond to the same measured environmental field.

## Observation design

Both species are observed with separate PresenceOnly streams and known constant effort.
The focal process reads the source latent ecological intensity; it never reads source
records directly.

Train/heldout split:

- 24 training spaces;
- 12 held-out spaces;
- one temporal context.

The held-out score is focal PresenceOnly log predictive density.

## Identification prerequisite

The partner coefficient target is:

`focal.partner_effect.beta_partner`.

Both worlds must pass:

- exact JAX structural identification;
- relative minimum singular value >= 1e-3;
- condition number <= 1e3;
- target SD proxy <= 0.25.

## Frozen outcome profile

Planned full gate:

- 16 replicates per world;
- 2 worlds;
- Full + partner-knockout fits per replicate;
- 64 fits total;
- 90% posterior interval;
- fresh seed family to be frozen before outcome;
- 300 warmup;
- 350 posterior samples;
- 2 chains;
- target accept = 0.90.

## Positive-world targets

Required:

- abs mean beta bias <= 0.15;
- beta truth coverage >= 0.75;
- 90% interval entirely positive in >= 0.75 of replicates;
- Full beats partner-knockout heldout score in >= 0.75;
- mean heldout gain >= 0.005.

## Null-world targets

Required:

- abs mean beta <= 0.10;
- zero coverage >= 0.75;
- nonzero interval rate <= 0.25;
- mean Full-minus-knockout heldout gain <= 0.005;
- material gain > 0.005 in <= 0.25 of replicates.

## Boundary

PASS supports identification/recovery/predictive value of one directed partner-latent
effect under measured shared-environment controls.

It does not solve hidden common drivers, causal identification, reciprocal interactions,
or interaction-event validation. Those require a later v0.5 programme.
