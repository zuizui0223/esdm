# v0.6c Budget-Matched Accessibility Evidence Gate

Status: **FROZEN BEFORE v0.6c QUALIFICATION OR MCMC OUTCOME**

Design commit:
`8d9900e61c3154ca7300beb4175dbe4a4333f71b`.

## Frozen scientific question

Does a direct process-specific AccessibilityCount endpoint provide more practical
information about accessibility than the same expected number of extra joint occurrence
records?

## Frozen shared ecology

Exact v0.6a truth and geometry:

- 36 contexts;
- first 24 training;
- final 12 held-out;
- suitability intercept = 0.30;
- habitat slope = +0.75;
- accessibility intercept = 0.40;
- distance/accessibility slope = -1.10.

## Frozen shared base stream

Both conditions receive the same Base AccessiblePresenceOnly realization.

- effort = 8.0 in all 36 contexts.

## Frozen auxiliary budgets

### Direct

AccessibilityCount:

- effort = 20.0 in each training context;
- effort = 0 in held-out.

### MatchedJoint

Independent AccessiblePresenceOnly:

- effort = 12.168687798294679 in each training context;
- effort = 0 in held-out.

This constant was derived pre-outcome so that total expected auxiliary records match
under the frozen truth.

Required expected-budget relative error:

- <= 1e-12.

Realized auxiliary counts may differ because the two streams are independent Poisson
draws.

## Frozen exact-JAX qualification

Diagnostics:

- rank rtol = 1e-8;
- rank atol = 1e-10;
- relative minimum singular value threshold = 1e-3;
- condition number threshold = 1e3;
- target SD proxy threshold = 0.25;
- Fisher ridge = 1e-10.

Required:

- Direct: all four targets structurally identified;
- Direct: all four targets practically identified;
- MatchedJoint: all four targets structurally identified.

For each accessibility target:

- Direct target-SD proxy / MatchedJoint target-SD proxy <= 0.50.

Targets:

- `sp.accessibility.access_intercept`;
- `sp.accessibility.beta_distance`.

If qualification fails, replicated MCMC must not run.

## Frozen replicated profile

Only after qualification passes:

- replicates = 16;
- two fits per replicate;
- total fits = 32;
- shared Base joint realization within each replicate;
- credible mass = 0.90;
- warmup = 300;
- posterior samples = 350;
- chains = 2;
- target accept probability = 0.90.

Fresh seed family:

- base seed = 20261021;
- seed stride = 101;
- replicate r data seed = 20261021 + 101*r;
- Direct fit seed = data seed + 1;
- MatchedJoint fit seed = data seed + 2.

No scientific or MCMC setting is configurable from the command line.

## Frozen Direct recovery criteria

For all four targets:

- abs(mean posterior bias) <= 0.15;
- empirical 90% interval coverage >= 0.75.

## Frozen budget-matched precision criteria

For both accessibility targets:

- Direct posterior SD < MatchedJoint posterior SD in >= 0.875 of replicates;
- mean Direct / MatchedJoint posterior-SD ratio <= 0.75.

## Frozen sampling criterion

Across all 32 fits:

- divergences / 32 <= 0.10.

## Held-out score

Both fitted conditions are scored on the same held-out Base AccessiblePresenceOnly
realization.

Neither auxiliary stream has held-out exposure.

The Direct-minus-MatchedJoint held-out log-score difference and win rate are reported
descriptively only.

They are not pass/fail criteria.

## Mechanical decision

v0.6c = PASS only if every frozen qualification, Direct recovery, precision, and sampling
criterion passes.

No failed criterion may be repaired inside v0.6c by changing:

- the matched effort;
- truth coefficients;
- covariates;
- split;
- base or auxiliary efforts;
- seed family;
- MCMC settings;
- SD-ratio thresholds;
- recovery thresholds.

## Interpretation boundary

PASS may support:

> Under the frozen static-accessibility geometry, a direct accessibility endpoint carries
> materially more accessibility-parameter information per expected auxiliary record than
> collecting more joint occurrence records.

PASS would not show that direct accessibility observations are universally necessary,
nor would it establish causal movement limitation.
