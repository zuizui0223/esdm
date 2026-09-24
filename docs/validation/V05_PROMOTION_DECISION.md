# v0.5 Promotion Decision

Status: **PROMOTED WITHIN THE DECLARED EVIDENCE-TIERED DIRECTED-INTERACTION SCOPE**

Authoritative evidence chain: v0.5a PASS -> v0.5b FAIL -> v0.5c guard ->
v0.5d pair-event stream -> v0.5e PASS.

This promotion deliberately includes a negative result. The hidden-common-driver failure
defines the claim ceiling rather than being tuned away.

## Core implementation

The promoted v0.5 core adds:

- `PartnerIntensityEffect`: a signed source-latent-field contribution to focal
  log intensity;
- topological evaluation of acyclic latent-species dependencies;
- explicit partner-effect knockout;
- `PairEventCount`: a separate source-to-target realized-event observation stream;
- pair-specific event authorization;
- fail-closed evidence-tier authorization.

Reciprocal/cyclic dependencies remain rejected.

## v0.5a: measured-environment positive/null PASS

Frozen run: `35970773843`.

Interaction world, true beta = +0.75:

- mean beta bias = +0.00200;
- 90% coverage = 1.00;
- beta interval entirely positive = 16/16;
- Full > partner knockout held-out = 16/16;
- mean held-out gain = +1.17726.

Measured-shared-environment null, true beta = 0:

- mean fitted beta = +0.00138;
- zero coverage = 0.75;
- nonzero interval = 4/16;
- material held-out gain = 3/16;
- mean held-out gain = -0.05074.

All 18 frozen checks passed and 64 fits had zero divergences.

## v0.5b: hidden-common-driver FAIL

Frozen run: `35981265978`.

True beta = 0, but the fitting model omitted a common environmental driver correlated
with source latent intensity.

Observed:

- mean fitted beta = **+0.98541**;
- zero coverage = 0/16;
- nonzero positive interval = 16/16;
- Full > knockout held-out = 16/16;
- mean held-out gain = **+4.39472**;
- divergences = 0.

This is a valid scientific failure.

It establishes that:

- a nonzero partner coefficient is not sufficient for mechanistic interpretation;
- held-out predictive gain is not sufficient;
- knockout superiority is not sufficient;
- measured-environment controls do not protect against arbitrary omitted common causes.

Therefore model-based partner coupling alone is capped at
`PREDICTIVE_DEPENDENCE`.

## v0.5c-v0.5d: evidence separation encoded in the runtime

v0.5c introduced pair-specific event authorization and an edge-claim guard:

- model-only <= PREDICTIVE_DEPENDENCE;
- authorized positive pair event -> REALIZED;
- realized + independent functional endpoint -> FUNCTIONAL;
- realized + functional + intervention -> CAUSAL.

v0.5d added `PairEventCount`, a generative source-to-target event-count likelihood
separate from `beta_partner`.

## v0.5e: evidence-separation PASS

Frozen run: `35987048798`.

Gate freeze commit:
`8d3ffa928dcb6ff9c36a8b10eaa1c76028eaecf0`.

Gate blob:
`c9dde4bf7ef95541fdcf183d1755b7c0a05c208b`.

Final artifact:

- ID `10802094588`;
- SHA256
  `8167a961348f5b55b46a486bdfd0c3352ac20cbf54dc7b9129f21c07deb38204`.

All 24 frozen checks passed across 48 fits with zero divergences.

### Hidden common driver + event silent

- true beta = 0;
- mean fitted beta bias = +0.95255;
- beta nonzero positive interval = 16/16;
- positive pair events = 0/16;
- PREDICTIVE_DEPENDENCE authorization = 16/16;
- REALIZED = 0/16.

The inferential coefficient is wrong, but the claim is correctly bounded.

### Realized only

- true beta = 0;
- positive pair events = 16/16;
- REALIZED = 16/16;
- beta coverage = 0.875;
- nonzero beta interval = 2/16;
- event-intercept coverage = 0.9375.

A realized pair interaction can be supported without a nonzero focal effect coefficient.

### Directed + realized

- true beta = +0.75;
- beta interval positive = 16/16;
- beta coverage = 0.9375;
- positive pair events = 16/16;
- REALIZED = 16/16;
- event-intercept coverage = 0.9375.

No replicate in any world reached FUNCTIONAL or CAUSAL because those evidence endpoints
were deliberately absent.

## Promoted v0.5 contract

v0.5 is promoted for:

- acyclic directed partner-latent predictive dependence;
- explicit partner-effect knockouts;
- pair-specific realized-event observations;
- separation of predictive dependence from realized interaction;
- fail-closed evidence-tier authorization under the declared known-truth programmes.

v0.5 is **not** promoted for:

- causal interpretation of `beta_partner` under hidden confounding;
- functional effect from event occurrence alone;
- causal effect without intervention;
- reciprocal/fixed-point interactions;
- empirical correctness in a field system.

## Methodological conclusion

The strongest supported statement is:

> Predictive ecological dependence, realized pair interaction, functional consequence,
> and causal interaction are different evidence states. Strong posterior coefficients,
> knockout gains, and held-out predictive skill cannot substitute for the independent
> endpoint required by a higher evidence tier.

The next version should move to the separate movement/accessibility process rather than
retuning the v0.5 hidden-driver failure.
