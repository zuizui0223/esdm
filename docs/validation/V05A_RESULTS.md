# v0.5a Directed Interaction Known-Truth Results

Status: **PASS**

v0.5a is the first full known-truth validation of the directed PartnerIntensityEffect.

The frozen programme required the interaction coefficient to be identifiable in both a
true-interaction world and a measured-shared-environment null before replicated MCMC was
allowed.

## Frozen provenance

- outcome run: `35970773843`
- outcome head: `3eb57ec0e3f81bffa87119ea0181b7a71000e30d`
- gate freeze commit: `c6b7630030b63a950008191e4e4842950b660b6e`
- gate blob expected/observed:
  `d3c4d3f1b3f29858c8fdc2c69eb2003d5552111e`
- qualification artifact ID: `10795343510`
- final result artifact ID: `10795932206`
- final artifact name: `v05a-result-35970773843`
- artifact digest / independently verified ZIP SHA256:
  `b3ae75e2d046ee29ac8a2df9cded81a67da3ef29522d8cdd5862616396835b4d`

All scientific checks passed. There were no infrastructure blocks.

## Identification qualification

Target:

`focal.partner_effect.beta_partner`

### Interaction world

- structural status: **Identified**
- full rank / without-target rank: **7 / 6**
- target SD proxy: **0.11197**
- frozen threshold: <= 0.25
- relative minimum singular value: **0.15014**
- condition number: **6.66**

### Measured-shared-environment null

- structural status: **Identified**
- full rank / without-target rank: **7 / 6**
- target SD proxy: **0.15676**
- frozen threshold: <= 0.25
- relative minimum singular value: **0.18074**
- condition number: **5.53**

Thus measured shared environmental structure did not destroy local identification of the
directed coefficient.

## Interaction world: beta = +0.75

Across 16 fresh replicates:

- mean beta bias = **+0.00200**
- 90% interval coverage = **1.00**
- interval entirely above zero = **16/16**
- Full model beat partner knockout held-out score = **16/16**
- material held-out gain (>0.005) = **16/16**
- mean Full-minus-knockout held-out gain = **+1.17726**

The directed coefficient was therefore recovered with negligible mean bias, and the
partner process added held-out predictive information in every replicate.

## Measured-shared-environment null: beta = 0

Source and focal both retained strong responses to the same measured shared environment.

Across 16 fresh null replicates:

- mean fitted beta = **+0.00138**
- 90% zero coverage = **0.75**
- nonzero 90% interval rate = **4/16 = 0.25**
- interval entirely positive = **1/16**
- Full > knockout held-out score = **4/16 = 0.25**
- material positive gain (>0.005) = **3/16 = 0.1875**
- mean Full-minus-knockout held-out gain = **−0.05074**

The frozen null thresholds were met exactly or with margin. On average, the more complex
interaction model was worse than the knockout when the true partner coefficient was zero.

## Sampling

- worlds: 2
- replicates per world: 16
- fits per replicate: 2
- total fits: **64**
- total divergences: **0**

## Interpretation

The v0.5a result supports a stronger statement than simple cross-species association.

Under this declared two-species known-truth system:

1. the focal partner coefficient is structurally and practically identifiable;
2. when a directed source->focal effect generates the data, the coefficient is recovered
   and improves held-out focal prediction;
3. when source and focal only co-vary through a **measured shared environmental driver**,
   the fitted partner coefficient returns to approximately zero and the interaction model
   does not retain the same predictive advantage.

This directly guards against one common source of spurious biotic effects: measured
environmental co-response.

## Claim boundary

v0.5a does **not** establish causal interaction in empirical ecology.

A hidden shared driver can still mimic a partner effect because it is absent from the
fitting model. The next v0.5 programme should therefore pair a hidden-common-driver null
with an independent interaction-event observation endpoint.

Reciprocal interactions remain intentionally unsupported and fail closed through the
latent dependency DAG.
