# v0.6 Promotion Decision

Status: **PROMOTED WITH A STATIC ACCESSIBILITY CLAIM**

Authoritative endpoints: frozen v0.6a PASS plus frozen v0.6b assumption-reliance audit.

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

Therefore v0.6 refuses an inaccessible-versus-unsuitable decomposition when the joint
product contains no separating structure beyond the two intercepts.

## v0.6b structured joint-only audit

A fresh deterministic audit then removed AccessibilityCount from the exact structured
v0.6a training geometry while retaining distinct non-collinear habitat and distance
covariates.

All four targets were **structurally Identified**:

- full rank / without-target rank = **4 / 3**;
- relative minimum singular value = **0.03757**;
- condition number = **26.62**.

But practical identification remained weak for three targets:

- suitability intercept target-SD proxy = **0.49463**;
- accessibility intercept = **1.47533**;
- distance/accessibility slope = **0.91023**;
- habitat slope = **0.11028** and was the only target below 0.25.

Thus independent accessibility observations are **sufficient but not universally
necessary for structural identification**. In this frozen geometry, however, they are
required to meet the declared practical-estimability threshold across the full
suitability/accessibility parameter block.

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

## v0.6b assumption-reliance audit

v0.6b removed the direct AccessibilityCount endpoint from the exact v0.6a positive
training geometry while retaining the distinct habitat and distance covariates.

The intercept-only refusal control remained unchanged:

- both intercepts = **NotIdentified**;
- rank = **1** with or without either target.

The structured joint-only model behaved differently. All four parameters were locally
structurally identified:

- full rank = **4**;
- rank without each target = **3**;
- relative minimum singular value = **0.03757**;
- condition number = **26.62**.

But practical information was highly uneven:

- suitability intercept target-SD proxy = **0.49463** — weak;
- habitat slope = **0.11028** — passes;
- accessibility intercept = **1.47533** — weak;
- accessibility slope = **0.91023** — weak.

The frozen interpretation is therefore **Outcome B: structurally identified but
practically weak**.

This means direct accessibility information is sufficient and highly valuable, but not a
universal mathematical prerequisite for local structural identification. In the structured
joint-only design, the decomposition is supplied by the declared functional forms and
covariate geometry.

Comparing the same positive geometry with and without direct AccessibilityCount:

- suitability intercept SD proxy: **0.495 -> 0.106**;
- habitat slope: **0.110 -> 0.108**;
- accessibility intercept: **1.475 -> 0.178**;
- accessibility slope: **0.910 -> 0.198**.

The direct endpoint therefore primarily stabilizes the accessibility decomposition and the
shared intercept, rather than merely creating Jacobian rank.

## Promoted v0.6 contract

v0.6 may now serve as the stable base for later movement development under this bounded
interpretation:

1. ecological suitability and accessibility are distinct latent quantities;
2. an unstructured joint product can be genuinely `NotIdentified`;
3. structured joint occurrence can sometimes create local structural identification from
   covariate and link-function shape alone;
4. such structural identification is assumption-dependent and is not equivalent to
   independent ecological evidence for accessibility;
5. practical identifiability must therefore be evaluated separately from structural rank;
6. an independent accessibility observation channel can strongly stabilize the
   decomposition;
7. under the frozen direct-calibration design, all four targets were recoverable;
8. accessibility learned in training improved joint occurrence prediction where direct
   accessibility observations were absent.

## Strongest supported methodological claim

> Separating habitat suitability from accessibility requires either informative
> model structure or an independent accessibility channel, and those are not
> epistemically equivalent. Structural identifiability created by functional form should
> be reported as assumption-dependent; process-specific observations provide stronger,
> practically estimable evidence.

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
