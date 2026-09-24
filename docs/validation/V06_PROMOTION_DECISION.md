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

## v0.6c covariate-alignment stress

v0.6c tested whether the v0.6b joint-only fragility becomes worse when habitat and
accessibility predictors align, a common risk in fragmented-landscape and island
applications where environmental quality and isolation may covary.

Frozen habitat-distance correlations were:

- **0.00**;
- **0.50**;
- **0.90**;
- **0.99**.

At every alignment, both the joint-only and direct-calibrated models remained locally
structurally identified.

Practical identification separated sharply.

Joint-only number of practical targets:

- rho 0.00: **1/4**;
- rho 0.50: **1/4**;
- rho 0.90: **1/4**;
- rho 0.99: **0/4**.

At rho 0.99, joint-only target-SD proxies were:

- suitability intercept: **1.07957**;
- habitat slope: **0.54742**;
- accessibility intercept: **2.69012**;
- accessibility slope: **0.53082**.

The joint-only condition number rose to **43.29**.

With direct AccessibilityCount, all four targets remained practical at every alignment.
At rho 0.99, target-SD proxies were:

- suitability intercept: **0.10903**;
- habitat slope: **0.11476**;
- accessibility intercept: **0.18895**;
- accessibility slope: **0.18508**.

The direct-calibrated condition number was only **5.10**.

The frozen v0.6c gate therefore **PASSed**.

This strengthens the v0.6 interpretation:

> Functional-form structure can create local rank, but correlated habitat and
> accessibility gradients can make occurrence-only decomposition practically unstable.
> A process-specific accessibility endpoint can preserve practical separation under the
> same geometry.

This remains an identification result, not evidence that any empirical island system has
the tested correlation structure.

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
