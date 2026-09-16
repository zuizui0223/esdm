# Community Network Rewiring v0.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a generic interaction-network distribution layer that separates connectance, partner diversity, rewiring, and held-out community transfer.

**Architecture:** Build on Phase-1 generic edge/state primitives. `InteractionNetworkDistribution` owns a declared taxon set, eligible directed edge universe, and edge probabilities. Diversity/rewiring functions operate on normalized edge mass, while transfer scoring macro-averages independent held-out communities and reuses the ordered non-skippable information-ceiling semantics.

**Tech Stack:** Python 3.10–3.12 standard library, pytest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-16-community-network-rewiring-v02.md`

## Global Constraints

- Runtime dependencies remain standard-library only.
- Pollination-specific runtime tokens remain forbidden under `src/esdm`.
- Potential edge probability is not realized, functional, or causal interaction evidence.
- No fitted learner family is introduced.
- Network beta is a separate axis; do not claim a total multiplicative taxon × state × edge beta decomposition in Phase 2.
- Community transfer is macro-averaged by independent community.

---

### Task 1: Interaction network distribution

**Files:**
- Create: `src/esdm/network/distribution.py`
- Create: `src/esdm/network/__init__.py`
- Test: `tests/test_network_distribution.py`

**Interfaces:**
- Produces: `InteractionNetworkDistribution(taxa, edge_probabilities, allow_self_edges=False)`; methods `eligible_edges`, `edge_probability(source, target)`, `expected_connectance()`, `edge_mass_distribution()`.

- [ ] Write failing tests for validation, complete declared eligible edge universe, edge lookup, expected connectance, and normalized edge mass.
- [ ] Run CI and confirm RED because `esdm.network` is absent.
- [ ] Implement minimal validated object.
- [ ] Run full tests and confirm GREEN.

### Task 2: Interaction and partner diversity

**Files:**
- Create: `src/esdm/network/diversity.py`
- Test: `tests/test_network_diversity.py`

**Interfaces:**
- Produces: `interaction_diversity_q1(network)` and `partner_diversity_q1(network, source)`.

- [ ] Write failing identity tests: one effective edge -> 1, two equal edges -> 2, empty -> 0, two equal partners -> 2.
- [ ] Confirm RED.
- [ ] Implement Shannon effective-number summaries over positive normalized edge mass.
- [ ] Confirm GREEN.

### Task 3: Network turnover and rewiring

**Files:**
- Create: `src/esdm/network/turnover.py`
- Test: `tests/test_network_turnover.py`

**Interfaces:**
- Produces: `network_beta_q1(networks)`, `shared_taxon_rewiring_beta_q1(a, b)`, and `state_conditioned_connectance(networks_by_state)`.

- [ ] Write failing tests for stable network beta=1, pure rewiring beta>1, scalar connectance shift with rewiring beta=1, and taxon turnover with shared-taxon restriction.
- [ ] Confirm RED.
- [ ] Implement aligned edge-universe q=1 multiplicative beta and shared-taxon restriction.
- [ ] Confirm GREEN.

### Task 4: Held-out community transfer

**Files:**
- Create: `src/esdm/transfer/community.py`
- Modify: `src/esdm/transfer/__init__.py`
- Test: `tests/test_community_transfer.py`

**Interfaces:**
- Produces: `HeldoutCommunityPrediction`, `CommunityGainResult`, `community_log_score_gain`, `community_information_ceiling`.

- [ ] Write failing tests showing macro-community weighting, positive edge-level gain, null gain, and non-skippable information ladder.
- [ ] Confirm RED.
- [ ] Implement Bernoulli log score with clipping and macro aggregation by independent community.
- [ ] Reuse Phase-1 point ceiling semantics for ordered named community-level gains.
- [ ] Confirm GREEN.

### Task 5: Known-truth network worlds

**Files:**
- Create: `src/esdm/benchmarks/network_worlds.py`
- Modify: `src/esdm/benchmarks/__init__.py`
- Test: `tests/test_network_known_truth.py`

**Interfaces:**
- Produces deterministic fixtures `stable_network_world`, `pure_rewiring_world`, `connectance_shift_world`, `taxon_turnover_network_world`, `transfer_positive_network_world`, `transfer_null_network_world`.

- [ ] Write failing tests matching every spec benchmark.
- [ ] Confirm RED.
- [ ] Implement deterministic known-truth fixtures without fitted models.
- [ ] Confirm GREEN.

### Task 6: Documentation and boundary guards

**Files:**
- Modify: `README.md`
- Modify: `docs/PROVENANCE.md`
- Modify: `tests/test_domain_independence.py`
- Create: `examples/community_rewiring.py`
- Modify: `tests/test_examples.py`

**Interfaces:**
- Documents network distribution, connectance-vs-rewiring distinction, and community transfer boundary.

- [ ] Extend runtime-token guard to new network source.
- [ ] Add generic community rewiring example; no domain-specific labels required.
- [ ] Document that pollination remains only one optional example inherited from Phase 1.
- [ ] Run exact-head Python 3.10–3.12 CI.

### Task 7: Stacked PR and audit

**Files:** none.

- [ ] Compare `feature/state-resolved-community-v01...feature/community-network-rewiring-v02` and verify only Phase-2 changes.
- [ ] Open a draft PR with base `feature/state-resolved-community-v01`.
- [ ] Verify PR-triggered CI on the exact head.
- [ ] Keep Phase-1 PR #1 unchanged and unmerged.
