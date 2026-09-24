# v0.5b Source-Only Perturbation Identification Design

Status: **prospective design, pre-outcome**

Base: frozen v0.5a identification FAIL head
`90218bb168b0932dd4e0c53d8eb6c654b436f45d`.

## Motivation

v0.5a showed a clear asymmetry:

- beta = +0.80: structurally identified and practically non-weak;
- beta = 0: structurally identified but practically weak.

The next design does not lower the practical threshold and does not retune beta.

Instead it adds source-only exogenous variation so partner pressure varies independently
of the focal environmental surface.

## Source-only perturbation

Training spaces receive a deterministic three-level source perturbation:

`-1, 0, +1`.

Assignment is made from spatial/environmental geometry only, before any v0.5b
identification outcome. Consecutive ordered triplets use rotating permutations of the
three levels so the perturbation is not a monotone function of eastness.

Held-out east spaces receive perturbation = 0.

The source log-intensity becomes:

`source_intercept
 + source_beta_precip * precip
 + source_beta_lat * latitude
 + source_beta_perturbation * source_perturbation`.

Frozen perturbation coefficient:

`source_beta_perturbation = 1.0`.

The focal model does not include the perturbation covariate.

## Interaction worlds

Unchanged from v0.5a:

- directed_positive: beta_partner = +0.80;
- interaction_null: beta_partner = 0.0.

All other focal/source/observation parameters are inherited unchanged except for the
new source perturbation term.

## Qualification target

`focal.partner_effect.beta_partner`.

The same exact-JAX identification thresholds are reused:

- structural rtol = 1e-8;
- structural atol = 1e-10;
- relative minimum singular value >= 1e-3;
- condition number <= 1e3;
- target SD proxy <= 0.25;
- Fisher ridge = 1e-10.

Both worlds must pass structural and practical identification.

## Interpretation

A PASS would show that exogenous source variation can repair the null-information weakness
without changing the partner coefficient threshold or simply increasing observation
effort.

It still would not constitute empirical causal evidence. This is a semi-synthetic design
qualification for a manipulation-like source contrast.

If PASS, a separate replicated MCMC/held-out gate may be frozen.
