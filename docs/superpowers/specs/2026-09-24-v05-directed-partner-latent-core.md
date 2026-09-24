# v0.5 Directed Partner-Latent Core

Status: **implementation phase; no v0.5 promotion claim**

Base: frozen v0.4/R7 head `bb9c42c87bc179fb07c4475961c7d4dfa90724c4`.

## Purpose

v0.5 begins the first genuinely biotic generative process in the refactored ESDM core.

The runtime already declared a species-level latent dependency DAG, but process evaluation
did not receive upstream latent fields. Therefore the architectural rule

`partner observations -> partner latent field -> focal ecological effect`

was not yet executable.

This change makes that rule real.

## First directed process

`PartnerIntensityEffect` contributes to the focal `log_intensity` channel.

For source species j and focal species i:

`biotic_pressure_j(c) = softplus(log_intensity_j(c))`

`log_intensity_i(c) += beta_ij * biotic_pressure_j(c)`.

Properties:

- source input is the source species latent ecological field;
- raw source records are never read by the process;
- beta can be positive or negative;
- knockout sets only the partner contribution to zero;
- the source species is declared through `latent_species_dependencies`;
- reciprocal cycles remain rejected.

The softplus transform provides a positive partner-pressure scale while remaining stable
for low/high log intensity.

## Dependency execution

Model evaluation is changed from declaration-order species evaluation to deterministic
topological evaluation of the latent-species DAG.

This applies to both:

- scalar latent-field construction;
- array/JAX latent-field construction.

A focal process can therefore read a source species that was declared later in the input
mapping, provided the dependency graph is acyclic.

## Frozen core contracts for this implementation step

The implementation must demonstrate:

1. reverse declaration order still evaluates source before focal;
2. scalar and JAX array paths agree;
3. changing source observation effort does not directly change the focal ecological
   field at fixed latent source parameters;
4. process knockout restores the focal baseline;
5. unknown source species fail closed;
6. reciprocal source/focal dependencies fail closed.

## Non-claims

This core step does not yet establish:

- interaction parameter identification;
- causal biotic interaction;
- robustness to hidden shared environmental drivers;
- observed interaction-event support;
- reciprocal interaction;
- v0.5 promotion.

The next v0.5 gate must add known-truth positive/negative interaction worlds and a
direct interaction-event observation endpoint before any interaction evidence tier is
promoted.
