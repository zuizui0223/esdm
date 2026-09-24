# v0.6 Promotion Decision

Status: **PROMOTED WITH A STATIC ACCESSIBILITY CLAIM**

Authoritative endpoint: frozen v0.6a PASS.

## Scientific question

Observed absence or low occurrence can arise because a context is unsuitable, because the
species cannot access it, or both.

v0.6 asks whether ESDM can separate those components without silently inventing
accessibility information.

## Core contract

v0.6 adds:

- `LinearAccessibility`;
- latent `log_accessibility` and `accessibility`;
- `AccessiblePresenceOnly`;
- direct `AccessibilityCount`;
- posterior accessibility fields;
- explicit accessibility knockout = 1.

The existing `PresenceOnly` contract remains accessibility-blind.

## Frozen refusal result

The negative control contained:

- one suitability intercept;
- one accessibility intercept;
- only a joint AccessiblePresenceOnly endpoint.

Both intercepts were **NotIdentified**.

For each target:

- full local sensitivity rank = **1**;
- rank without target = **1**.

Practical uncertainty was effectively unbounded:

- suitability target-SD proxy = **4228.41**;
- accessibility target-SD proxy = **10536.45**.

Therefore v0.6 does not infer an inaccessible-versus-unsuitable decomposition from the
joint product alone.

## Frozen positive design

The positive design added direct AccessibilityCount observations in the 24 training
contexts while retaining joint occurrence records across all 36 contexts.

All four targets were structurally and practically identified:

- full rank / without-target rank = **4 / 3**;
- relative minimum singular value = **0.21977**;
- condition number = **4.55**;
- target-SD proxies = **0.106–0.198**.

## Replicated recovery

Across 16 fresh replicates / 32 fits:

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

Total divergences = **0**.

## Held-out transfer

Direct AccessibilityCount effort was frozen at exactly zero in all 12 held-out contexts.

Held-out scoring used only the joint AccessiblePresenceOnly endpoint.

Full versus accessibility knockout:

- Full better = **16/16**;
- mean gain = **+0.36244**;
- minimum gain = **+0.03242**.

Thus training accessibility information transferred to unseen contexts instead of merely
explaining its direct calibration stream.

## Promoted v0.6 contract

v0.6 may now serve as the stable base for later movement development under this bounded
interpretation:

1. ecological suitability and accessibility are distinct latent quantities;
2. joint occurrence alone need not identify them separately;
3. when only the product is informed, ESDM must return `NotIdentified`;
4. an independent accessibility observation channel can authorize the decomposition;
5. under the frozen static known-truth design, the accessibility component is recoverable;
6. accessibility learned in training can improve joint occurrence prediction where direct
   accessibility observations are absent.

## Strongest supported methodological claim

> A model should not explain low occurrence as either habitat unsuitability or
> inaccessibility unless the observation design contains information that distinguishes
> those processes.

## Promotion boundary

This promotion supports a **static accessibility layer** only.

It does not support:

- dispersal-distance kernels;
- transition or movement matrices;
- path connectivity or resistance surfaces;
- dynamic colonization/extinction;
- source-sink population dynamics;
- causal movement limitation in empirical systems.

Those require future process modules and fresh prospective validation rather than
reinterpretation of the static accessibility coefficient.
