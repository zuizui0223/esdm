# NumPyro inference backend v0.3

Status: frozen before backend outcomes.

## Goal

Make the current generative v0.3 kernel inferential without changing its ecological semantics.

The backend is generic across ecological systems. Pollination is not a privileged path.

## Runtime boundary

Core `esdm` remains importable on Python 3.10. NumPyro 0.21 requires Python >=3.11, so the backend is optional and tested on supported Python versions only.

## Scientific contract

1. The NumPyro model must consume the same `Model`, `LinearSuitability`, `EffortField`, and `PresenceOnly` contracts used by deterministic likelihood and simulation.
2. The backend may translate `PriorSpec` into NumPyro distributions, but must not duplicate ecological-process equations.
3. Presence-only likelihood is Poisson with expected records from `PresenceOnly.expected_rates()` semantics: ecological intensity x effort x detection.
4. `fit_numpyro` must return posterior draws by process parameter name and basic sampler diagnostics. It does not assign `Supported` claims by itself.
5. Knockout recovery and SBC use the same generative graph; misspecified effort worlds remain in `simulate.misspecified` and do not count as SBC.
6. Python 3.10 must continue to pass all core tests without NumPyro installed.
7. Backend examples and benchmarks must be generic across ecological systems; no pollination-specific runtime branch.

## Initial scope

- one or more species;
- current `LinearSuitability` process;
- current `PresenceOnly` count streams;
- fixed known effort and detection;
- NUTS/MCMC inference;
- posterior predictive ecological and record rates;
- helper for SBC rank extraction across replicated fits.

## Explicit non-scope

- state/activity/interaction/movement processes;
- bidirectional interactions;
- cut posterior;
- variational inference;
- latent effort inference;
- causal interaction claims;
- domain-specific biology.
