# v0.3.1 identification-first promotion gate

Status: **FROZEN BEFORE v0.3.1 promotion outcomes**

This gate supersedes the retired v0.3 promotion interpretation. The archived v0.3
runs remain implementation diagnostics only and cannot promote v0.3.1.

## Principle

v0.3.1 passes only if the framework refuses ecological claims when the observation
design cannot separate ecological and observation processes. Predictable bias under a
misspecified GLM is not a promotion criterion.

## Gate A — claim / identification separation

- posterior contraction may return `Identified` or `NotIdentified` only;
- contraction alone must never return scientific `Supported`;
- a design-uninformed parameter remains distinct from a confounded parameter.

This gate is deterministic and must pass in the unit suite.

## Gate B — stream target sets

For every observation stream:

- non-target taxa contribute no likelihood term;
- a missing data block for a declared target is an error, never an all-zero history;
- in a multi-species model, a stream targeting species A must not create pseudo-absence
  information for species B.

This gate is deterministic and must pass in the unit suite and NumPyro backend tests.

## Gate C — neutral-parameter knockout

For linear suitability

`eta(x) = alpha + beta*x`

the no-effect knockout is

`eta_knockout(x) = alpha`,

not zero total intensity. The v0.3.1 knockout benchmark must use the same baseline
intercept and observation effort geometry as its non-knockout counterpart, with only
`beta = 0` changed.

For the repeated-fit check, pre-outcome criteria are:

- 100 replicates;
- 90% posterior interval;
- `abs(mean posterior beta) <= 0.10`;
- zero coverage in `[0.82, 0.98]`;
- nonzero-interval rate `<= 0.12`;
- mean divergences per fit `<= 0.10`.

The previous v0.3 knockout result cannot be reused because its baseline intensity was
changed by the old knockout semantics.

## Gate D — structural identification negative control

Use an opportunistic presence-only stream with

`log effort(x) = log(e0) + gamma*x`

and ecological intensity

`log lambda(x) = alpha + beta*x`.

With this stream alone, observation rates depend on `beta + gamma`; therefore both
`beta` and `gamma` must be returned as `NotIdentified` by the local sensitivity-rank
diagnostic. `alpha` remains identifiable.

Add a second stream with known effort and the same ecological field. The additional
observation geometry must restore unique sensitivity directions, so both `beta` and
`gamma` must be returned as `Identified`.

Passing this gate is about the framework's refusal/authorization behavior, not about a
posterior mean being numerically close to truth.

## Gate E — all-parameter SBC with ESS-aware finite rank supports

The retired 10-bin total-variation gate is not used.

Frozen v0.3.1 SBC profile:

- prior-predictive replicates: **100**;
- base seed: **20260918**;
- chains per fit: **2**, run sequentially for portability;
- warmup draws per chain: **300**;
- retained draws per chain before ESS thinning: **400**;
- rank draws: ESS-thinned separately for every free parameter and replicate;
- parameters: **all free ecological and observation-process parameters**;
- ECDF evaluation points: **49**;
- familywise level: **alpha = 0.05**;
- null-envelope Monte Carlo simulations: **20,000**;
- envelope seed: **20260919**;
- divergences: mean per fit `<= 0.10`.

For each parameter/replicate, the post-thinning draw count is retained. The null rank is
therefore discrete uniform on `0..m_r` for that replicate-specific support `m_r`. The
calibration decision is a simulation-based simultaneous ECDF envelope over the maximum
absolute deviation across every parameter and every evaluation point. A single parameter
outside the familywise envelope fails the SBC gate.

This is an esdm-specific simulation implementation of the simultaneous-ECDF strategy;
it is not claimed to reproduce the optimization algorithm of Säilynoja, Bürkner &
Vehtari (2022) line-for-line.

## Gate F — semi-synthetic real geometry (mandatory, not yet satisfied)

Promotion remains blocked until a semi-synthetic fixture is committed **before its
outcomes are inspected**. It must use real spatial geometry / real environmental or
effort geometry, while ecological coefficients and observation counts are generated
from known truth through the same generative graph.

Minimum design:

- at least 100 spatial locations or cells;
- at least 6 day-of-year bins;
- at least 4 hour bins where the selected observation process makes hour relevant, or a
  documented reason why hour is not an estimand in the fixture;
- spatially structured environmental covariates;
- spatially structured observation effort not algebraically proportional to the focal
  ecological covariate;
- frozen train/held-out spatial blocks;
- provenance and license recorded with the fixture.

Until Gate F is implemented and frozen, **v0.3.1 status is NOT_READY regardless of all
other results**.

## Promotion rule

`v0.3.1 = PASS` only when Gates A–F all pass. No weighted score and no compensating one
failure with another success.
