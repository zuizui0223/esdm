# v0.5b Hidden Common-Driver Stress Results

Status: **FAIL**

v0.5b prospectively tested whether the directed PartnerIntensityEffect would refuse a
false interaction when source and focal were jointly driven by an omitted common
environmental process.

The true partner coefficient was exactly zero.

## Frozen provenance

- outcome run: `35981265978`
- outcome head: `c7ed991830e69ba241bb88db3b55239da222985f`
- gate freeze commit: `0955decc9a3abfa3e30f3f4f57d90192cdecc46a`
- gate blob expected/observed:
  `8cb04d4195fbd6e8e61f24f58c4202298e9e3776`
- final artifact ID: `10800257515`
- artifact name: `v05b-result-35981265978`
- artifact digest / independently verified ZIP SHA256:
  `f0c6ff0c9555df266d9e8a2c0c38b793a2b0e36008e0a1f344ffdedcfd3421c2`

All 16 replicate jobs completed successfully. The aggregate failed only because the
frozen scientific refusal gate failed. `infrastructure_block = null`.

## Result

True generating value:

- `beta_partner = 0.0`.

Observed across 16 fresh replicates:

- mean fitted beta = **+0.98541**;
- zero coverage = **0/16 = 0.00**;
- nonzero 90% interval = **16/16 = 1.00**;
- interval entirely positive = **16/16 = 1.00**;
- Full > partner knockout heldout score = **16/16 = 1.00**;
- material positive heldout gain (>0.005) = **16/16 = 1.00**;
- mean Full-minus-knockout heldout gain = **+4.39472**;
- total divergences across 32 fits = **0**.

Every false-interaction criterion failed with a large margin.

The fitted partner coefficient was not merely slightly biased. The model inferred a
large, consistently positive directed effect in every replicate and the misspecified Full
model strongly outperformed the knockout on held-out focal presence-only records.

## Interpretation

This is a clean claim-ceiling result.

v0.5a established that:

- a true directed partner-latent effect is recoverable;
- measured shared environmental co-response does not reproduce the same signal.

v0.5b now establishes the complementary limitation:

> An omitted common driver that is correlated with source latent intensity can be absorbed
> almost perfectly by the directed partner-effect term.

Because the Full model also improves held-out prediction, ordinary predictive validation
does **not** solve this problem. In this world, a false ecological mechanism is
predictively useful.

Therefore:

- predictive skill is not sufficient for a realized or causal interaction claim;
- a nonzero posterior interaction coefficient is not sufficient;
- a partner knockout comparison is not sufficient;
- measured-environment controls are not sufficient against unmeasured common causes.

The safe evidence ceiling for presence-only partner coupling is
**PREDICTIVE_DEPENDENCE**, not REALIZED or CAUSAL.

## Next requirement

The next v0.5 programme should add an independent pair-specific interaction-event
observation endpoint and test claim authorization rather than trying to retune the
presence-only coefficient until the hidden-driver null passes.

A hidden-driver false positive should remain a valid model fit but must fail promotion to
a realized interaction edge when independent event evidence is absent.

## Claim boundary

v0.5b does not invalidate the v0.5a positive result. It narrows what that result permits
us to claim.

The directed partner-latent process remains a useful predictive component. Its coefficient
cannot be interpreted as a realized or causal biotic effect from presence-only records
alone under omitted-driver risk.
