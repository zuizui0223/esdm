# v0.3 benchmark and promotion gates

This document freezes the validation structure for the v0.3 suitability + effort-aware presence-only kernel.

The benchmark is intentionally generic. It does not use pollination, any focal plant, or any particular interaction family. It tests whether the basic ecological-intensity / observation-process separation behaves as declared before richer community processes are added.

## Four independent axes

Promotion is conjunctive. Passing one axis cannot compensate for failing another.

1. **Calibration** — in-model simulation-based calibration is acceptably close to uniform rank behaviour under a predeclared threshold.
2. **Knockout recovery** — when suitability is knocked out in the generating graph, fitting the ordinary suitability model recovers an effect near zero.
3. **Misspecification sensitivity** — wrong observation-effort geometry and an omitted environmental driver produce detectable parameter shifts. This is a negative-control requirement, not a success claim about the misspecified fit.
4. **Claim restraint** — the claims layer must independently refuse over-strong interpretation under the misspecified worlds. This status is never inferred automatically from posterior bias.

## Matched worlds

### Correct effort (`in_model`)

Truth and fit use the same environmental suitability process and the same heterogeneous effort field. Records are generated through the production path:

`Model.latent_fields -> PresenceOnly.expected_rates -> simulate_presence_only`.

### Suitability knockout (`in_model`)

The generating graph replaces suitability with its declared no-effect knockout. The fitted graph nevertheless contains ordinary `LinearSuitability`, so a near-zero recovered slope is an inferential result rather than a term being structurally removed from the fit.

### Wrong effort geometry (`misspecified`)

Records are identical to those in the matched correct-effort world for the same seed and ecological truth, but the fitted graph is supplied an incorrect uniform effort field. The resulting parameter shift measures sensitivity to observation-process misspecification.

### Hidden environmental driver (`misspecified`)

The generating graph contains both an observed and a hidden environmental driver. The fitted graph receives only the observed driver. This tests omitted-process bias without relabelling the omitted driver as a biotic interaction.

## Separation from SBC

Only in-model worlds belong to SBC. Deliberately misspecified worlds are never pooled into the SBC rank histogram. Good SBC therefore cannot be used as evidence that the ecological or observation model is robust to omitted processes.

## Gate evidence

`V03GateEvidence` stores four numerical diagnostics plus the independently supplied claim-restraint decision. `evaluate_v03_promotion` returns four named axes and `promote=True` only when all four pass.

The current thresholds are software defaults for testability, not yet preregistered scientific thresholds. A larger benchmark study must freeze sample sizes, replicate counts, thresholds, and interval/claim rules before it is used as a scientific promotion decision.

## NumPyro fitting

`fit_v03_world_numpyro` rebuilds the declared fitted graph from a benchmark world and delegates to the production NumPyro NUTS backend. It returns only canonical `alpha` and `beta` posterior draws plus divergence count; backend-specific sample-site naming does not leak into downstream validation code.

## What this does not establish

These benchmarks do not establish universal SDM/JSDM superiority, ecological causal identification, robustness to every form of misspecification, or validity for any particular interaction family. They are the minimum promotion gate for the v0.3 generative kernel before adding state, activity, interaction, or movement processes.
