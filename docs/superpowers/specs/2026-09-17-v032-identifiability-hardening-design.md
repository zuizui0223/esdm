# v0.3.2 Identifiability Hardening Design

## Purpose

Preserve the frozen v0.3.1 promotion record unchanged while strengthening the foundation required before any v0.4 state/activity process is added. The hardening must address four linked risks: scalar-per-context JAX tracing, conflation of structural and practical identifiability, a transfer fixture that treats effort as known, and an ambiguous `targets=None` observation contract.

This branch is stacked on `feature/v031-identification-fixes` at `ea00493c`. Existing v0.3.1 Gate A–F documents and frozen result artifacts remain historical records and are not rewritten.

## Non-goals

- Do not add ecological state-transition or activity-time processes.
- Do not reinterpret the frozen v0.3.1 PASS.
- Do not create an automatic route from identification diagnostics to `ClaimStatus.SUPPORTED`.
- Do not privilege pollination or another interaction family.
- Do not make JAX a mandatory base dependency for ordinary non-inference use.

## 1. Array-first latent and observation representation

### Problem

`Model.latent_fields` currently iterates through every context in Python and calls process scalar arithmetic separately. `PresenceOnly.expected_rates` repeats the same pattern, and the NumPyro backend only stacks the resulting scalar map at the end. Large domains therefore produce large traced scalar graphs. Adding a state axis would multiply this graph size.

### Design

Introduce an internal ordered-context array representation without deleting the mapping API used by existing callers.

- `ContextArray` stores the fixed `domain.keys` order and one backend array/value vector for the context axis.
- `LatentFieldArrays` maps species to context arrays of log intensity.
- `Model.latent_field_arrays(theta, covariates, *, array_module)` builds latent fields with vectorized process methods.
- Existing `Model.latent_fields(...)` remains as the compatibility mapping path.
- JAX/NumPyro code must call the array path directly and must not construct one traced scalar node per context before stacking.
- Process classes used by the current v0.3.1 graph (`LinearSuitability`, `NeutralSuitability`) gain vector methods that consume covariate arrays in domain order.
- Effort classes gain vector methods with the same ordering contract.
- `PresenceOnly.expected_rate_array(...)` combines ecological log intensity, effort and detection probability as arrays.

The current context axis is one-dimensional and ordered exactly as `Grid.keys`. Future state or activity dimensions may be leading axes, but this change does not invent state semantics. Existing `StateSpace` declarations remain independent until a later design binds them to generative processes.

### Compatibility

The scalar/mapping public methods remain available and numerically equivalent. Tests must compare scalar and array results. NumPyro switches to the array path.

## 2. Structural and practical identification are separate diagnostics

### Structural identification

Structural identification asks whether the target sensitivity direction is exactly redundant under the declared model at a local anchor.

Replace finite-difference sensitivities with JAX automatic differentiation in a new exact-JAX path:

1. Flatten all declared ecological and observation parameters into a stable site order.
2. Define a pure function from the parameter vector to concatenated log expected-rate arrays.
3. Use `jax.jacfwd` to compute the Jacobian.
4. Compute singular values using SVD.
5. Determine numerical rank with a relative rule `s_i > rtol * s_max` plus an absolute floor only for the zero-Jacobian case.
6. A target is structurally identified when removing its column lowers this relative rank.

The diagnostic remains local. The returned evidence must include anchor information, singular values/rank summary, and thresholds. The API may accept one or multiple explicit anchors; multiple anchors are combined conservatively, reporting parameter identification only if every requested anchor is structurally identified. No hidden “true value” is implied by the API.

If JAX is unavailable and the caller requests exact structural diagnostics, raise an explicit availability error rather than silently falling back to finite differences. The legacy finite-difference helper may remain private only for backwards test comparison during the migration.

### Practical identification

Practical identification is a second diagnostic and does not change `IdentificationStatus`.

Add `PracticalIdentificationDiagnostic` containing at least:

- target site;
- minimum relative singular value;
- Jacobian condition number;
- target variance proxy from a regularized inverse Fisher-like matrix `J.T @ W @ J` (identity weights are acceptable for the first implementation; Poisson expected-rate weights are preferred when available);
- configured thresholds;
- `weak: bool` and machine-readable reasons.

A nearly collinear design can therefore be structurally `Identified` while practical identification is weak. Required regression cases:

- exact `h=x`: structural `NotIdentified`;
- `h=x+epsilon`, epsilon scale `1e-6`: structural `Identified`, practical weak;
- sufficiently independent calibrated second stream: structural identified and practical not weak;
- a nonlinear toy rate graph where autodiff preserves the exact dependency that a fixed finite-difference tolerance can misclassify.

## 3. Explicit target contract

`targets=None` must no longer mean “all model species”. Omission of a target declaration is unsafe because absent species blocks can become pseudo-absence histories.

Preferred contract:

- `PresenceOnly.targets` is required and must be a non-empty frozen set; or
- an explicit sentinel such as `ALL_SPECIES` may opt into all-species behavior.

There must be no ambiguous `None -> all species` path. Existing fixtures and tests are migrated to explicit targets. A compatibility warning is insufficient because the dangerous behavior is silent; code using `None` should fail fast with a clear message.

## 4. Reusable validation ladder

Validation logic should not remain exclusively in `validate/v031_*` benchmark modules.

Introduce reusable evidence types/functions under `esdm.validate` (or a small focused sibling module):

- `compare_knockout(...)` returns held-out/full-vs-knockout predictive evidence without making a claim.
- `evaluate_transfer(...)` packages held-out predictive evidence and parameter recovery summaries.
- `diagnose_identification(...)` combines structural and practical diagnostics for requested targets.
- an `EvidenceBundle` (name may vary) can carry identification, transfer and knockout evidence to claim-policy code.

These functions return evidence only. They must not generate `ClaimStatus.SUPPORTED`. Existing claim types remain authoritative; a later explicit authorization/promotion policy may consume evidence bundles.

## 5. Frozen Gate F-prime

Existing Gate F remains unchanged and explicitly remains a semi-synthetic known-effort fixture.

Add a new frozen pre-v0.4 Gate F-prime document before running the benchmark. The fixture must include all of the following simultaneously:

1. Primary observation stream with unknown effort using `LogLinearEffort` (or a vector-equivalent extension).
2. A second calibrated/known-effort stream that covers only a declared subset of the training geography.
3. Held-out evaluation containing genuine covariate extrapolation: at least one ecological covariate has held-out values outside the min/max training range.
4. Ecological truth and effort truth generated by the same graph used for fitting, so the gate tests separation/identification rather than model misspecification.
5. A positive-control geometry where ecological and observation gradients are recoverable.
6. A negative-control geometry where the calibrated stream is too sparse/aligned and practical identification must flag weakness rather than permit a promotion interpretation.
7. Neutral suitability knockout preserving the intercept and zeroing only environmental slopes.

### Frozen PASS criteria

The positive control passes only if all predeclared conditions hold:

- target ecological and effort parameters are structurally identified;
- practical diagnostics are not weak under frozen thresholds;
- ecological and effort slope recovery meets frozen bias/coverage or interval criteria;
- held-out full-minus-neutral-knockout predictive gain is positive under a frozen aggregate/replicate criterion;
- held-out covariate-range checks prove the declared extrapolation actually occurred;
- no fixture-source or profile integrity check fails.

The negative control passes only if the frozen practical-identification diagnostic flags weakness (or structural non-identification, if intentionally exact) and the result is not promoted as evidence of process separation.

Thresholds and replicate profile must be written to `docs/validation/V032_PROMOTION_GATE.md` before outcome-producing full runs. Results go to a separate `V032_RESULTS.md` and machine-readable snapshot; v0.3.1 result files remain untouched.

## 6. Performance acceptance

Add a deterministic array-construction benchmark/smoke test using the Gate F scale (2,880 contexts and current three free parameters or the closest lightweight equivalent). It must verify scalar/array numerical equivalence and record evidence that the JAX representation is materially smaller/cheaper than the old scalar graph.

The initial acceptance may use one or more stable proxies rather than platform-specific peak RSS, for example:

- JAXPR equation count scaling approximately with process count rather than context count;
- successful JIT compile/evaluation at 2,880 contexts without the previous scalar trace explosion;
- optional wall/RSS diagnostic in CI as non-normative metadata.

The promotion criterion should rely on deterministic graph-shape checks where possible; raw wall time and RSS remain diagnostics because hosted runners vary.

## 7. Testing and compatibility

Implementation is test-driven. Existing v0.3.1 tests remain regression tests. New focused suites cover:

- scalar/array equivalence for suitability, effort, expected rates and NumPyro model construction;
- 2,880-context JAXPR/compile smoke;
- exact and near confounding;
- multiple explicit anchors;
- nonlinear autodiff rank case;
- required target declarations;
- reusable evidence API never returning `Supported`;
- Gate F-prime fixture geometry and frozen gate mechanics.

If the full test suite exceeds runner memory, run and record logically separated sub-suites and use fresh processes for inference-heavy suites. Do not represent an infrastructure interruption as a scientific PASS or FAIL.

## 8. Completion condition before v0.4

v0.4 state/activity work may begin only after:

- array-first JAX path is merged and the large-context smoke passes;
- structural/practical identification tests pass;
- target declaration ambiguity is removed;
- Gate F-prime criteria are frozen before the full run;
- the positive and negative controls produce interpretable results under the frozen criteria;
- evidence/claim separation remains intact.
