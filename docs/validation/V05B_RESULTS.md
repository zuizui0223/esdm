# v0.5b Hidden Common-Driver Stress Results

Status: **FAIL**

v0.5b tested the directed PartnerIntensityEffect under a deliberately misspecified world
with no true partner effect and a strong omitted environmental driver shared by source and
focal.

The refusal thresholds were copied unchanged from the successful v0.5a
measured-shared-environment null.

## Frozen provenance

- outcome run: `35976569558`
- outcome head: `7e7e647cd0ddf351af8a1e939458adb93d68bade`
- gate freeze commit: `0955decc9a3abfa3e30f3f4f57d90192cdecc46a`
- gate blob expected/observed:
  `8cb04d4195fbd6e8e61f24f58c4202298e9e3776`
- final artifact ID: `10798985190`
- final artifact name: `v05b-result-35976569558`
- artifact digest / independently verified ZIP SHA256:
  `8b7dd657d2a25d22bc33a47772a7f301988734f773d2cd3f6df1f349d6377a49`

All 16 replicate jobs completed successfully. The aggregate job failed only because the
frozen scientific gate failed. The final artifact reports
`infrastructure_block = null`.

## Hidden-driver null

True partner coefficient:

- **beta_partner = 0.0**

Observed across 16 fresh replicates:

- mean fitted beta = **+0.98541**
- minimum replicate posterior mean beta = **+0.69785**
- maximum replicate posterior mean beta = **+1.23613**
- 90% zero coverage = **0/16**
- nonzero interval rate = **16/16**
- positive interval rate = **16/16**

The directed coefficient therefore became a strong positive false interaction in every
replicate.

## Held-out knockout comparison

Full model beat the partner knockout in:

- **16/16 replicates**

Material held-out gain (>0.005):

- **16/16**

Mean Full-minus-knockout held-out gain:

- **+4.39472**

Even the smallest replicate-level held-out gain was:

- **+2.82213**

Thus held-out predictive gain did not protect against this omitted-driver confounding.
The misspecified interaction model predicted better precisely because the source latent
field acted as a proxy for the hidden focal driver.

## Sampling

- fits = **32**
- total divergences = **0**
- mean divergences per fit = **0.0**

This is not a sampling pathology.

## Interpretation

v0.5a and v0.5b establish a sharp boundary.

### What v0.5a showed

When shared environmental structure is measured and included in both source and focal
models:

- beta is identifiable;
- a true beta=+0.75 is recovered;
- beta returns to approximately zero when the true effect is absent;
- measured environmental co-response does not reproduce the same held-out signal.

### What v0.5b shows

When an important shared driver is omitted:

- source latent intensity can become a proxy for that missing focal environment;
- the partner coefficient can be strongly nonzero even when true beta=0;
- predictive knockout gain can strongly favor the false interaction model.

Therefore:

> A predictive directed partner-latent coefficient from occurrence data is not sufficient
> evidence for a realized or causal biotic interaction under hidden common-driver
> misspecification.

This is a stronger and more useful result than pretending the current model is universally
robust.

## Claim boundary

The directed PartnerIntensityEffect may support a **predictive-dependence** claim when its
validation conditions are met.

Presence-only partner coupling alone cannot be promoted to realized/functional/causal
interaction evidence.

The next v0.5 step should add an independent interaction-event observation endpoint and
test whether that extra evidence can distinguish a true directed interaction from the
frozen hidden-driver null.
