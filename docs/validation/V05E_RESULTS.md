# v0.5e Evidence-Separation Known-Truth Results

Status: **PASS**

v0.5e prospectively tested whether ESDM can keep predictive dependence, realized
pair-event evidence, and higher functional/causal claims separate under known truth.

## Frozen provenance

- outcome run: `35987048798`
- outcome head: `1efaca62b3ece185e286c507a9ea38371718f0fe`
- gate freeze commit: `8d3ffa928dcb6ff9c36a8b10eaa1c76028eaecf0`
- gate blob expected/observed:
  `c9dde4bf7ef95541fdcf183d1755b7c0a05c208b`
- final artifact ID: `10802094588`
- final artifact name: `v05e-result-35987048798`
- artifact digest / independently verified ZIP SHA256:
  `8167a961348f5b55b46a486bdfd0c3352ac20cbf54dc7b9129f21c07deb38204`

All 48 fits completed successfully. The final artifact reports
`infrastructure_block = null`.

## Mechanical decision

**v0.5e = PASS. All 24 frozen checks passed.**

Across all three worlds:

- 16 replicates/world;
- 48 total fits;
- total divergences = **0**.

No replicate reached FUNCTIONAL or CAUSAL because no functional endpoint or intervention
evidence was supplied.

## Hidden common driver + event-silent world

True values:

- `beta_partner = 0`;
- hidden shared environmental driver present and omitted from the fitting model;
- `event_intercept = -8`.

Observed:

- mean fitted beta bias = **+0.95255**;
- beta coverage = **0.00**;
- beta nonzero interval rate = **1.00**;
- beta positive interval rate = **1.00**;
- positive pair-event rate = **0/16 = 0.00**;
- PREDICTIVE_DEPENDENCE authorization = **16/16 = 1.00**;
- REALIZED authorization = **0/16**;
- FUNCTIONAL-or-higher = **0/16**.

This reproduces the v0.5b false partner coefficient, but the evidence guard prevents that
wrong coefficient from self-promoting to a realized interaction claim.

The event-intercept posterior does not recover the extreme `-8` truth well
(mean bias **+4.37675**, coverage **0**), but this is not a gate failure: all observed
pair-event counts are zero, so the data only support a low-rate boundary statement rather
than precise recovery of an extreme log-rate. The claim authorization remains correct.

## Realized-only world

True values:

- `beta_partner = 0`;
- `event_intercept = -1`.

Observed:

- mean beta bias = **+0.05754**;
- beta coverage = **0.875**;
- nonzero beta interval rate = **2/16 = 0.125**;
- positive pair-event rate = **16/16 = 1.00**;
- REALIZED authorization = **16/16 = 1.00**;
- mean event-intercept bias = **−0.15202**;
- event-intercept coverage = **0.9375**;
- FUNCTIONAL-or-higher = **0/16**.

This is the key separation case: a pair can be empirically **REALIZED even when the
directed focal effect coefficient is zero**.

Observed interaction and ecological effect are therefore not synonyms in the model.

## Directed + realized world

True values:

- `beta_partner = +0.75`;
- `event_intercept = -1`.

Observed:

- mean beta bias = **+0.02743**;
- beta coverage = **0.9375**;
- beta interval entirely positive = **16/16**;
- positive pair-event rate = **16/16**;
- REALIZED authorization = **16/16**;
- mean event-intercept bias = **−0.02627**;
- event-intercept coverage = **0.9375**;
- FUNCTIONAL-or-higher = **0/16**.

Thus directed ecological dependence and realized pair-event evidence can be recovered
together without automatically escalating to a functional or causal claim.

## Interpretation across v0.5a-v0.5e

The validation sequence now resolves several different questions.

### v0.5a

A true directed partner-latent coefficient can be identified, recovered, and improve
held-out prediction when relevant measured shared environmental structure is represented.

### v0.5b

An omitted common driver can generate a large false partner coefficient and strong
held-out predictive gain despite `beta_partner = 0`.

Therefore:

- nonzero beta is not enough;
- predictive gain is not enough;
- knockout superiority is not enough.

### v0.5c

The claim layer therefore caps model-only evidence at PREDICTIVE_DEPENDENCE and requires
independent pair-event evidence for REALIZED.

### v0.5d

PairEventCount provides a generative pair-specific event likelihood separate from the
partner-effect coefficient.

### v0.5e

The full separation now passes known-truth validation:

- hidden-driver false beta + no events -> **PREDICTIVE_DEPENDENCE**;
- beta zero + observed events -> **REALIZED**;
- beta positive + observed events -> **REALIZED**;
- no functional endpoint/intervention -> never FUNCTIONAL or CAUSAL.

The strongest supported methodological statement is therefore:

> Predictive ecological dependence, realized pair interaction, functional effect, and
> causal interaction are distinct evidence states. A model should not infer the higher
> state merely because a lower-level statistical signal is strong or predictively useful.

## Claim boundary

v0.5e does not repair hidden-confounding bias in the partner coefficient.

It instead validates that ESDM's evidence architecture can remain epistemically bounded
when the coefficient is wrong.

The current supported ceiling is:

- PREDICTIVE_DEPENDENCE from model-based partner coupling;
- REALIZED from independently authorized pair-event evidence;
- FUNCTIONAL requires an independent functional endpoint;
- CAUSAL requires intervention evidence in addition to the lower-tier prerequisites.

A future programme should test a functional endpoint rather than further retuning the
presence-only partner coefficient.
