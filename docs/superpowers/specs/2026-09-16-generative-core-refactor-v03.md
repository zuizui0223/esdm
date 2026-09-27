# Generative-core refactor v0.3

## Purpose

Move `esdm` from a learner-agnostic evaluation layer to a process-based generative ecological model plus claim-governance layer, while retaining the Phase 1-3 work as downstream summaries, validation, and claims.

## Seven principles

1. One generative graph: simulation, likelihood evaluation, and posterior prediction use the same process and observation modules.
2. Every ecological process has a no-effect knockout with explicit neutral semantics.
3. A process with no declared and computational path to an observation stream is rejected at model construction.
4. Identifiability is diagnosed, not assumed: design-path checks, prior-to-posterior contraction, and simulation-based calibration are distinct diagnostics.
5. Validation designs are process-specific and frozen before held-out outcomes are inspected.
6. Biotic interactions act through partner latent fields, never raw partner observation records as covariates.
7. Diversity, network, map, and claim summaries are posterior-derived outputs, never inputs to the generative model.

## v0.3 implemented scope

- `domain`: space x day-of-year x hour grid and state/refinement declarations.
- `process`: backend-neutral Process protocol, explicit PriorSpec, no-effect knockouts, linear environmental suitability.
- `observe`: explicit effort fields and Poisson presence-only observation stream.
- `model`: process/stream composition, design-path checks, DAG checks, latent-field construction, shared likelihood path, process knockouts.
- `simulate`: in-model generation from the same latent fields and stream rate code, plus a misspecification namespace.
- `identify`: prior-to-posterior contraction and basic rank-histogram SBC diagnostics.
- `claims`: typed claim status with DesignUninformed / Untested / NotIdentified / NotSupported / Supported and interaction evidence tier.
- `summarize`: downstream wrappers around existing diversity/network summaries.
- `validate`: downstream wrappers around existing transfer/ladder diagnostics.

## Non-goals

- no full NumPyro fitting backend in this refactor;
- no state/activity/interaction/movement process yet;
- no claim of causal interaction identification;
- no claim that contraction alone proves identification;
- no claim that in-model SBC establishes robustness to misspecification;
- no use of posterior summaries as generative covariates.

## Design checks

For every species-process pair, the model builds a static path:

`process -> latent channel -> stream`

A stream declaration (`informs`) alone is insufficient: the stream must also consume a latent channel produced by the process. Missing paths fail with `DesignUninformedError`.

The species dependency graph is checked for cycles. v0.3 has no interaction process, but the graph contract is added now so later directed interactions fail closed on cycles.

## Presence-only observation model

For grid context c and species i:

`log lambda_obs(i,c) = log lambda_ecological(i,c) + log effort(c) + log detection(c)`

Counts are Poisson. The ecological intensity is composed from the same Process objects used by simulation and likelihood evaluation.

## Identification boundary

- no computational design path -> `DesignUninformed`;
- path exists but posterior contraction below threshold -> `NotIdentified`;
- contraction is reported separately from SBC;
- SBC uses simulations generated from the same graph and therefore checks calibration under the declared model, not ecological robustness.

Misspecified worlds live under `simulate/misspecified.py` and are explicitly not used as SBC worlds.
