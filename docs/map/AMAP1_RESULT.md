# AMAP1 terminal qualification result

Status: **FAIL (terminal)**  
Date: 2026-09-28  
Workflow run: `36369151809`

AMAP1 completed all **144/144** frozen confirmatory replicates and all **384** model fits.
No replicate job failed.

## What worked

The truth-aligned oracle structures were detectable in every field-positive world.
All six TX/TC detectability firewalls passed across G1-G3. Examples:

- G1 TX, BX-B0: positive-gain rate **0.9375**, mean gain **+3.5211**
- G2 TC, BC-B0: positive-gain rate **0.8125**, mean gain **+2.9822**
- G3 TX, BX-B0: positive-gain rate **1.0000**, mean gain **+3.3001**

The sampling guardrail also passed comfortably:

- total divergences: **3 / 384 fits**
- mean divergences per fit: **0.0078125**
- frozen maximum: **0.10**

## Why the programme failed

The failure is the primary low-regret target itself.

The frozen requirement was material-regret rate <= **0.25** in every geometry x truth
world. Instead, **all 9/9 worlds exceeded that limit**.

Material-regret rates were:

- G1: T0 **0.5625**, TX **0.5000**, TC **0.4375**
- G2: T0 **0.5625**, TX **0.7500**, TC **0.5000**
- G3: T0 **0.3750**, TX **0.6250**, TC **0.6875**

Several worlds also exceeded the mean-regret limit of +0.005. The largest mean regret was
G2 T0 at **+0.05406**.

Therefore:

```text
LOW_REGRET_MAP_SUPPORTED = false
```

The bounded conclusion is:

> allowing one residual field to continuously adapt between exchangeable and fixed
> geographic coherence did not keep held-out predictive regret sufficiently small across
> the frozen structural uncertainty.

This failure is not explained by oracle non-detectability or NUTS instability.

## Relation to FIELD1 and MAP1

FIELD1 showed that adding a spatial field can help, but extra covariance axes were not
separable and the full inferential programme was unstable. MAP1 fixed the covariance
structure and became numerically stable, but false-promoted coherence in null worlds.

AMAP1 asked a distinct robustness question: can one adaptive field avoid discrete
structure choice and stay close to the truth-aligned oracle? The answer under the frozen
multi-geometry universe is **no**.

AMAP1 does not alter the terminal decisions of FIELD1 or MAP1.

## Terminal rule

AMAP1 is not eligible for threshold retuning, geometry/truth retuning, or a same-program
rerun. No empirical response is authorized by this result.

Exact provenance:

- aggregate artifact ID: `10948844669`
- artifact ZIP digest:
  `sha256:1f49b3b983e0cf6cb04fcb8515019bd338bff993cdef755a0afc23868c470347`
- aggregate JSON SHA-256:
  `402f9c434e0da751711702f51204730e04da489887d94bcc99479c1a01112854`
