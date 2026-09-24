# v0.6 Promotion Decision

Status: **PROMOTED WITH A STATIC ACCESSIBILITY CLAIM**

Authoritative endpoints: frozen v0.6a PASS, frozen v0.6b assumption-reliance audit, and frozen v0.6c finite identification frontier.

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

## v0.6c finite identification frontier

v0.6c froze nine cells before outcome:

- predictor geometry: distinct / aligned / flat-access;
- accessibility intercept: -2.0 / +0.40 / +2.0;
- each cell compared joint-only occurrence against the identical model plus direct
  AccessibilityCount.

The full finite pattern was:

| geometry | accessibility intercept | joint structural targets | joint practical targets | direct structural targets | direct practical targets |
| --- | ---: | ---: | ---: | ---: | ---: |
| distinct | -2.0 | 4/4 | 1/4 | 4/4 | 4/4 |
| distinct | +0.40 | 4/4 | 1/4 | 4/4 | 4/4 |
| distinct | +2.0 | 4/4 | 1/4 | 4/4 | 2/4 |
| aligned | -2.0 | 4/4 | 0/4 | 4/4 | 3/4 |
| aligned | +0.40 | 4/4 | 0/4 | 4/4 | 4/4 |
| aligned | +2.0 | 4/4 | 0/4 | 4/4 | 2/4 |
| flat-access | -2.0 | 1/4 | 0/4 | 3/4 | 0/4 |
| flat-access | +0.40 | 1/4 | 0/4 | 3/4 | 0/4 |
| flat-access | +2.0 | 1/4 | 0/4 | 3/4 | 0/4 |

Three distinct failure modes emerge.

### Functional-form rank without practical information

The aligned geometry is the strongest warning.

Even when habitat and distance are literally the same predictor, the nonlinear
accessibility link is enough to create local Jacobian rank 4. Yet joint-only practical
identification is **0/4** in all three accessibility regimes.

Thus full structural rank can be generated almost entirely by the assumed functional
forms.

### Saturation is an information limit

At accessibility intercept +2.0, direct observations do not make the accessibility
parameters practically identified:

- distinct direct target-SD proxies:
  accessibility intercept **0.531**, slope **0.552**;
- aligned direct target-SD proxies:
  accessibility intercept **0.498**, slope **0.531**.

When accessibility is close to saturation, its likelihood sensitivity is intrinsically
small. A process-specific endpoint cannot create information that the operating regime
does not contain.

### No predictor variation means no slope information

In the flat-access geometry, distance is exactly zero in every context.

The accessibility distance slope is therefore `DesignUninformed` under both joint-only
and direct-calibrated designs.

The direct endpoint identifies the accessibility intercept and separates the other
structural parameters, but it cannot identify a slope whose predictor never varies.

Because the full free-parameter system retains that uninformed slope, the frozen
system-level practical diagnostic marks the flat-access designs weak overall.

## Revised information principle

The v0.6 sequence now supports a sharper rule:

> Ecological process resolution is an information-design property, not a model-component
> switch. Stable separation requires predictor variation, an informative operating
> regime, and sufficient process-specific observation information.

Direct process-specific observations can stabilize a decomposition, but they cannot
rescue zero design variation or a nearly insensitive/saturated process.

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
   accessibility observations were absent;
9. full structural rank can be created by functional-form assumptions even when practical
   information is negligible;
10. direct process-specific data cannot rescue a slope with zero predictor variation or
    a process operating in a low-sensitivity saturated regime.

## Strongest supported methodological claim

> Separating habitat suitability from accessibility is an information-design problem.
> Structural rank may be created by functional form, but stable ecological resolution
> additionally requires predictor variation, an informative operating regime, and enough
> process-specific observation information. These sources of identification are not
> epistemically equivalent.

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
