# v0.5d Pair-Event Count Observation Stream

Status: implementation phase; no new realized or causal promotion result.

Base: v0.5c event-evidence tier guard at
cd40313a5308ba6152e998ede1a3f945b9d00f99.

## Purpose

v0.5c made pair-event evidence a prerequisite for promotion beyond
PREDICTIVE_DEPENDENCE. v0.5d adds a generative likelihood for repeated pair-specific
event counts so such evidence can enter the same model/observation architecture.

## Observation contract

PairEventCount represents directed source-to-target realized event counts.

For context c:

event_rate(c)
= effort(c)
  * exp(event_intercept)
  * softplus(source log intensity(c))
  * softplus(target log intensity(c)).

The pair-specific event intercept is an observation-process parameter with a Normal prior
on the log-rate scale.

## Semantics

The stream measures realized pair events such as encounters, visits, attacks, transfers,
or other domain-defined events.

It does not assert that an observed event is beneficial, harmful, functional, or causal.

The source and target latent ecological fields are used as availability/opportunity
terms. Raw source observation effort never enters the pair-event rate directly.

## Model validation

PairEventCount declares exactly one target species and one distinct source species.

Model construction fails closed when:

- source species is unknown;
- target species is unknown;
- source lacks a log-intensity ecological process;
- target lacks a log-intensity ecological process.

A generic optional stream-level validate_model hook is added to Model construction so
future cross-species observation streams can enforce analogous contracts.

## Core tests

The implementation must verify:

- pair identity and design validity;
- event rate responds to source latent ecology;
- source observation effort does not directly alter event rate at fixed latent ecology;
- scalar and JAX array rate paths agree;
- unknown source species fail closed.

## Boundary

This implementation does not yet show that pair-event data rescue beta from hidden common
drivers, nor does it authorize CAUSAL claims.

The next fresh validation should combine the v0.5b hidden-driver world with independent
pair-event observations and test whether the event channel separates REALIZED edge
evidence from a spurious predictive partner coefficient.
