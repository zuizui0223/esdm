# v0.5b Source-Only Perturbation Identification Gate

Status: **FROZEN BEFORE v0.5b IDENTIFICATION OUTCOME**

v0.5b tests whether exogenous source-only variation repairs the null-information weakness
that caused the frozen v0.5a FAIL.

## Frozen target

`focal.partner_effect.beta_partner`

## Frozen worlds

- directed_positive: beta_partner = +0.80
- interaction_null: beta_partner = 0.0

All focal ecological and observation parameters are inherited unchanged from v0.5a.

## Frozen source perturbation

Training spaces receive a deterministic three-level source-only covariate:

- -1
- 0
- +1

Assignment uses only the pre-existing spatial/environmental geometry and rotating
three-level permutations. No v0.5b identification outcome enters assignment.

Held-out east spaces receive perturbation = 0.

The source process contains:

`source_beta_perturbation = 1.0`.

The focal suitability and partner-effect process do not consume the perturbation
covariate directly.

## Observation contract

Unchanged from v0.5a:

- source PresenceOnly effort = 6.0, detection = 0.90
- focal PresenceOnly effort = 6.0, detection = 0.90
- no free observation parameter
- one temporal context per station
- west + central training
- east held out

No observation count is increased relative to v0.5a.

## Exact identification diagnostic

Both worlds use:

- JAX exact Jacobian
- structural rtol = 1e-8
- structural atol = 1e-10
- relative minimum singular value >= 1e-3
- condition number <= 1e3
- target SD proxy <= 0.25
- Fisher ridge = 1e-10

## Mechanical qualification

v0.5b = PASS only if beta_partner is:

1. structurally identified in directed_positive
2. practically non-weak in directed_positive
3. structurally identified in interaction_null
4. practically non-weak in interaction_null

No MCMC is permitted before all four pass.

## Interpretation boundary

A PASS would show that source-only exogenous variation can make the partner coefficient
practically estimable near both the positive and null worlds without changing the
precision threshold or simply adding observation effort.

It would remain a semi-synthetic design result, not empirical causal evidence.

A FAIL is retained as evidence that this perturbation design is insufficient; no
within-v0.5b retuning is permitted.
