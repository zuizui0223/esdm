# v0.5c Pair-Event Evidence Tier Guard

Status: implemented claim-governance core; no new causal claim.

Base: frozen v0.5b hidden-common-driver FAIL at
5572d4bb9b7515acb14323b2002203c136eb2a25.

## Motivation

v0.5b produced a decisive failure:

- true partner coefficient = 0;
- fitted mean beta approximately +0.985;
- 16/16 intervals excluded zero;
- Full beat partner knockout in 16/16 held-out replicates.

Therefore posterior interaction strength and predictive gain can both support a false
mechanistic interpretation when a common driver is omitted.

The correct response is not to retune beta. The correct response is to enforce an
evidence-tier ceiling.

## Pair-specific event endpoint

v0.5c introduces InteractionEventRecord.

Each record names:

- directed source;
- directed target;
- observation ID;
- raw observation state;
- negative-evidence gate status.

The generic observation authorization rules are reused:

- resolved positive -> authorized positive event;
- raw negative -> biological negative only if its negative-evidence gate passes;
- missing/unresolved/device failure/occlusion -> unavailable.

Pair identity is explicit and evidence from one edge cannot authorize another edge.

## Claim guard

EdgeClaimEvidence.model_tier represents the strongest non-event model evidence and is
hard-capped at PREDICTIVE_DEPENDENCE.

Promotion rules:

- model-only evidence can reach at most PREDICTIVE_DEPENDENCE;
- at least one authorized positive pair event unlocks REALIZED;
- a functional endpoint plus realized event unlocks FUNCTIONAL;
- explicit intervention support plus functional and realized evidence unlocks CAUSAL.

Negative or unavailable event records do not promote a claim.

A requested tier above the evidence ceiling is automatically capped.

## Consequence for v0.5b

The hidden-driver result may remain a strong predictive-dependence fit. In the absence of
an independently authorized positive source-to-focal event, it is not permitted to become
a REALIZED, FUNCTIONAL, or CAUSAL edge.

This makes the v0.5b failure part of the runtime claim contract rather than a narrative
warning in documentation.

## Boundary

v0.5c does not yet fit an event-rate model or establish that event observations identify
the sign or magnitude of beta.

A later programme may add generative event-count likelihoods. This core step only
enforces the epistemic rule that model dependence cannot promote itself into realized
interaction evidence.
