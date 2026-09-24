# v0.6b Joint-Only Identification Audit Gate

Status: **FROZEN BEFORE v0.6b AUDIT OUTCOME**

Design commit:
`9e1eba2c7efceec17b74dedc03a9db417381e831`.

## Frozen control

The exact v0.6a intercept-only joint-product control is rerun.

Required:

- suitability intercept = exact-JAX `NotIdentified`;
- accessibility intercept = exact-JAX `NotIdentified`.

This is a hard invariant.

## Frozen structured joint-only audit

The exact v0.6a ecological truth and 24 training contexts are used, but the direct
AccessibilityCount stream is removed.

Only AccessiblePresenceOnly remains.

Targets:

- `sp.suitability.suitability_intercept`;
- `sp.suitability.beta_habitat`;
- `sp.accessibility.access_intercept`;
- `sp.accessibility.beta_distance`.

Diagnostics are frozen to:

- JAX jacobian;
- rank rtol = 1e-8;
- rank atol = 1e-10;
- practical relative minimum singular value threshold = 1e-3;
- condition number threshold = 1e3;
- target SD proxy threshold = 0.25;
- Fisher ridge = 1e-10.

## Frozen interpretation

The structured joint-only result is descriptive, not a pass/fail target.

### Outcome A: all four structurally and practically identified

Interpretation:

> Independent accessibility observations are sufficient but not universally necessary.
> Under strong declared covariate/functional-form structure, joint occurrence alone can
> locally identify suitability and accessibility.

The v0.6 promotion text must be narrowed accordingly.

### Outcome B: all four structurally identified but at least one practically weak

Interpretation:

> Joint occurrence can provide formal local separation under the declared functional
> forms, but the frozen design does not support stable practical estimation without
> direct accessibility information.

### Outcome C: at least one structured target structurally NotIdentified

Interpretation:

> Even with the frozen non-collinear habitat/distance structure, joint occurrence alone
> does not fully separate suitability and accessibility in this design.

The v0.6a stronger interpretation may be retained for this geometry.

## Non-negotiable boundary

Regardless of outcome:

- local parametric identification is not independent ecological evidence;
- functional-form separation does not establish movement mechanism;
- no empirical causal accessibility claim is authorized;
- no thresholds or covariates may be changed after this gate is frozen.
