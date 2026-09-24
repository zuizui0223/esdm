# v0.6b Joint-Only Identification Audit

Status: prospective deterministic audit, pre-outcome.

Base: promoted v0.6 static accessibility head
`2942df9e23e5ae4d60e0cbe13b7ea1df77f3bd72`.

## Why this audit is necessary

v0.6a established two facts:

1. an intercept-only suitability × accessibility product is structurally
   non-identifiable;
2. adding an independent AccessibilityCount endpoint is sufficient to identify and recover
   the declared suitability/accessibility model.

That does **not** yet prove that an independent accessibility endpoint is universally
necessary.

When suitability and accessibility use distinct, varying covariates and different
functional forms, joint occurrence alone may carry enough shape information for local
identification.

v0.6b audits that possibility before allowing the promotion text to overgeneralize the
v0.6a refusal.

## Frozen designs

### A. Intercept-only refusal control

Exact v0.6a joint-only refusal:

- suitability intercept only;
- accessibility intercept only;
- AccessiblePresenceOnly only.

The two intercepts must remain structurally NotIdentified.

### B. Structured joint-only audit

Use the exact v0.6a positive ecological truth and first 24 training contexts:

- suitability intercept = 0.30;
- habitat slope = +0.75;
- accessibility intercept = 0.40;
- distance slope = -1.10;
- frozen non-collinear habitat/distance covariates.

Remove AccessibilityCount completely.

Observe only AccessiblePresenceOnly at effort 8.

Audit all four ecological parameters with the same exact-JAX/practical diagnostic used in
v0.6a:

- rtol = 1e-8;
- atol = 1e-10;
- relative minimum singular value threshold = 1e-3;
- condition number threshold = 1e3;
- target SD proxy threshold = 0.25;
- Fisher ridge = 1e-10.

## Frozen interpretation map

No tuning follows the outcome.

- If all four structured joint-only targets are structurally **and practically**
  identified, revise the v0.6 claim to:
  independent accessibility data are **sufficient but not universally necessary**;
  joint-only identification can arise from strong parametric/covariate structure.
- If structurally identified but any target is practically weak, revise the claim to:
  joint-only functional-form separation may exist formally, but direct accessibility data
  are required by the frozen design for practical recovery.
- If any structured joint-only target remains structurally NotIdentified, retain the
  stronger v0.6a interpretation for this geometry.

In every case, the intercept-only refusal must remain NotIdentified.

## Boundary

This audit is about local identification under a declared parametric model.

Even a structurally identified joint-only decomposition is not independent ecological
evidence of accessibility and does not establish movement causality.
