# v0.6b Joint-Only Identification Audit Results

Status: **COMPLETE — OUTCOME B**

Frozen interpretation:
**structurally identified but practically weak**.

## Provenance

- outcome run: `35994013730`
- outcome head: `1bd3c7f164c3ae0ee1bed5a94c287ff07a9b5556`
- gate freeze commit: `a4cd5f2ac809fd4db65ce4418f0648a55978fd59`
- gate blob expected/observed:
  `31d121519fe018c4cc20d75bfbfadbecc932f7a7`
- artifact ID: `10805592942`
- artifact name: `v06b-joint-audit-35994013730`
- artifact digest / independently verified ZIP SHA256:
  `4aafe370268e5204c11a47ec5fb305874bb53b5f504a5e471a38dc9b84b12571`

The workflow completed successfully with no infrastructure block.

## Intercept-only refusal control

The exact v0.6a joint-product negative control passed again.

For both the suitability and accessibility intercepts:

- structural status = **NotIdentified**;
- full rank = **1**;
- rank without target = **1**.

Practical SD proxies remained effectively unbounded:

- suitability intercept = **4228.41**;
- accessibility intercept = **10536.45**.

This confirms that an unstructured multiplicative product cannot be decomposed merely by
declaring two latent processes.

## Structured joint-only audit

The direct AccessibilityCount stream was removed from the exact v0.6a training geometry.

Only AccessiblePresenceOnly remained, with distinct non-collinear habitat and distance
covariates and the declared linear-intensity/logistic-accessibility forms.

All four targets became locally structurally identified:

- full rank = **4**;
- rank without each target = **3**;
- singular values =
  **5.39447, 3.67242, 1.78349, 0.20265**;
- relative minimum singular value = **0.03757**;
- condition number = **26.62**.

Thus direct accessibility observations are **not universally necessary for local
structural rank**.

The separation can instead be supplied by the shape of the parametric model and covariate
geometry.

## Practical identification

That structural result did not translate into uniformly usable information.

Target-SD proxies:

- suitability intercept = **0.49463** — weak;
- habitat slope = **0.11028** — passes;
- accessibility intercept = **1.47533** — weak;
- accessibility slope = **0.91023** — weak.

Three of four targets fail the frozen practical threshold of 0.25.

Therefore the correct frozen outcome is **B**, not A.

## What direct accessibility observations add

The same v0.6a positive geometry with direct AccessibilityCount had target-SD proxies:

- suitability intercept = **0.10610**;
- habitat slope = **0.10783**;
- accessibility intercept = **0.17776**;
- accessibility slope = **0.19828**.

Joint-only versus direct-calibrated:

- suitability intercept: **0.495 -> 0.106**;
- habitat slope: **0.110 -> 0.108**;
- accessibility intercept: **1.475 -> 0.178**;
- accessibility slope: **0.910 -> 0.198**.

So the process-specific endpoint does more than create formal rank. It sharply reduces
uncertainty in the accessibility parameters and the shared baseline decomposition.

## Revised v0.6 interpretation

The strongest supported statement is now:

> Suitability and accessibility can sometimes be locally separated from joint occurrence
> through distinct covariate and link-function structure, but such separation can be
> assumption-driven and practically weak. Independent accessibility observations provide
> a separate information channel that makes the frozen decomposition practically
> estimable and supports its ecological interpretation more directly.

The distinction matters:

- **structural identification** asks whether parameters are locally separable under the
  declared model;
- **practical identification** asks whether the observation design contains enough
  information for stable estimation;
- **independent ecological evidence** asks whether accessibility is observed through a
  process-specific endpoint rather than inferred only from the shape assumptions of a
  joint occurrence model.

These are different claims.

## Boundary

v0.6b does not test parameter recovery from the joint-only structured model.

It also does not establish:

- movement kernels;
- connectivity or resistance surfaces;
- dynamic colonization/extinction;
- source-sink dynamics;
- causal movement limitation.

A useful next stress test is to perturb the assumptions that created joint-only
structural rank — for example covariate geometry or accessibility link specification —
and ask whether direct accessibility observations protect the decomposition.
