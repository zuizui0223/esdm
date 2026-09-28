# MAP1 terminal qualification result

Status: **FAIL (terminal)**  
Date: 2026-09-27  
Workflow run: `36326381655`

MAP1 completed all **48/48** frozen confirmatory replicates and all **144** model fits.
No replicate job failed.

## What worked

The coherent residual field was clearly detectable in the world where coherence was true.

- P1, BC - B0: positive-gain rate **0.8125**, mean gain **+1.3885**
- P1, BC - BX: positive-gain rate **0.8125**, mean gain **+0.07995**

The exchangeable-control world was also informative:

- N1, BX - B0: positive-gain rate **0.875**, mean gain **+3.4837**

So MAP1 did not fail because the coherent field was too weak to detect.

The sampling guardrail also passed:

- total divergences: **12 / 144 fits**
- mean divergences per fit: **0.0833**
- frozen maximum: **0.10**

## Why the programme failed

The problem was **null calibration**.

In N0, where no residual field exists:

- BC - B0 material-gain rate = **0.3125** (> 0.25 allowed)
- BC - BX material-gain rate = **0.4375**
- BC - BX mean gain = **+0.00556** (> +0.005 allowed)

In N1, where residual heterogeneity is exchangeable rather than geographically coherent:

- BC - BX material-gain rate = **0.375** (> 0.25 allowed)

Therefore `COHERENT_MAP_SUPPORTED = false`.

The bounded interpretation is:

> fixed geographic coherence can improve held-out prediction when coherence is truly
> present, but the frozen MAP1 model does not suppress that preference reliably enough
> when coherence is absent or exchangeable.

## Relation to FIELD1

FIELD1 failed mainly because extra covariance axes were not separable and the complete
hierarchical fit was numerically unstable. MAP1 removed those axes, fixed the geography
kernel, matched latent amplitude, and passed its sampling guardrail.

That simplification solved the numerical problem and preserved positive-world signal,
but it exposed a different limitation: **specificity**. The coherent model still wins
too often under null worlds.

## Terminal rule

MAP1 is not eligible for threshold retuning, world retuning, holdout retuning, or a
same-program rerun. No empirical response is authorized by this result.

Exact provenance:

- aggregate artifact ID: `10935415107`
- artifact ZIP SHA-256: `b7df841e710e867ca446bac74766fc09e017af52e95c06677d731e46ef2d1ed8`
- aggregate JSON SHA-256: `ab395cfbe60cc5f10ce3c9994f58a8c73123328db0ccd784e0abb690ff3f50ea`
