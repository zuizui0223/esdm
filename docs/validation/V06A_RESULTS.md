# v0.6a Static Accessibility Known-Truth Results

Status: **PASS**

v0.6a prospectively tested whether habitat suitability and ecological accessibility can
be separated only when the observation design contains independent accessibility
information.

## Frozen provenance

- outcome run: `35989902607`
- outcome head: `9552fff0a1d580d446c1793a6c889351bbe63821`
- gate freeze commit: `425fc21b4d6e2285a8e04690f08d30fd4b5a34ab`
- gate blob expected/observed:
  `8b601d3919284af9129aca0bf94563305c7cf0f2`
- qualification artifact ID: `10803373374`
- final result artifact ID: `10804831269`
- final artifact name: `v06a-result-35989902607`
- artifact digest / independently verified ZIP SHA256:
  `978a10cbd9c6d0fcd382a925b47e6311e26658ad5c91c8ec9b2a50f4442b73e5`

All frozen checks passed. There were no infrastructure blocks.

## Joint-only refusal

The negative control used:

- an intercept-only suitability process;
- an intercept-only accessibility process;
- one joint AccessiblePresenceOnly stream.

Both parameters enter only through the same suitability × accessibility product.

The exact JAX diagnostic returned both intercepts as **NotIdentified**.

For either target:

- full local rank = **1**;
- rank without target = **1**.

Practical target-SD proxies were enormous:

- suitability intercept: **4228.41**;
- accessibility intercept: **10536.45**.

Thus the model refuses to decompose low occurrence into unsuitable versus inaccessible
when only the joint product is observed.

## Positive identification with direct accessibility information

The positive design added an AccessibilityCount stream in the 24 training contexts while
retaining joint occurrence records in all 36 contexts.

All four targets were structurally identified:

- full rank / without-target rank = **4 / 3**;
- relative minimum singular value = **0.21977**;
- condition number = **4.55**.

Target-SD proxies:

- suitability intercept: **0.10610**;
- habitat slope: **0.10783**;
- accessibility intercept: **0.17776**;
- distance/accessibility slope: **0.19828**.

All are below the frozen practical threshold of 0.25.

## Replicated recovery

Across 16 fresh replicates and 32 total fits:

Mean biases:

- suitability intercept: **+0.01779**;
- habitat slope: **+0.00234**;
- accessibility intercept: **−0.04019**;
- distance/accessibility slope: **+0.05556**.

90% interval coverage:

- suitability intercept: **0.9375**;
- habitat slope: **1.0000**;
- accessibility intercept: **0.9375**;
- distance/accessibility slope: **0.8750**.

All frozen recovery thresholds passed.

Total divergences: **0**.

## Held-out transfer

Direct AccessibilityCount effort was exactly zero in all 12 held-out contexts.

Held-out scoring used only the shared AccessiblePresenceOnly endpoint.

Full versus accessibility-knockout:

- Full better in **16/16 = 1.00** replicates;
- mean held-out gain = **+0.36244**;
- minimum gain = **+0.03242**.

Therefore the accessibility process was not merely fitting the direct calibration endpoint.
Information learned from training accessibility observations transferred to unseen
contexts where only joint occurrence was scored.

## Interpretation

v0.6a supports a clean static distinction between suitability and accessibility.

The important result is conditional:

> A low occurrence rate can be decomposed into habitat suitability and accessibility only
> when the observation design contains an independent accessibility channel.

Without that channel, the decomposition is refused as NotIdentified.

With it, the declared accessibility gradient is identified, recovered, and improves
held-out joint occurrence prediction even where direct accessibility observations are
absent.

## Claim boundary

v0.6a validates a **static accessibility layer**, not a full movement model.

It does not establish:

- movement kernels or dispersal-distance distributions;
- path connectivity or resistance surfaces;
- dynamic colonization/extinction;
- source-sink dynamics;
- causal movement limitation in empirical systems.

Those require later process modules and dedicated observation endpoints.
