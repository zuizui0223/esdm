# State-Resolved Community v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested Phase-1 kernel for state-resolved community diversity, generic biotic interaction opportunity, conditional biotic information gain, and non-skippable point transfer ceilings.

**Architecture:** `esdm` is learner-agnostic. Core dataclasses represent state axes, community state distributions, and generic biotic edges. Diversity/overlap/interaction functions consume explicit probabilities or held-out scores. Known-truth analytic worlds verify that shared environment, hidden confounding, state partitioning, and true directed coupling remain distinguishable at the claim level.

**Tech Stack:** Python 3.10-3.12, standard library runtime, pytest for tests, GitHub Actions for CI.

**Spec:** `docs/superpowers/specs/2026-09-16-state-resolved-community-design.md`

## Global Constraints

- Runtime code uses the Python standard library only in v0.1.
- Pollination is an example only; no pollination-specific code or constants in core modules.
- Predictive dependence is never labelled causal interaction by the API.
- Potential interaction opportunity is never labelled realized interaction probability.
- Ordinary binary SDM remains representable as a special case.
- Point transfer ceiling is deterministic and non-skippable; no confidence guarantee is claimed.
- All tests must pass on Python 3.10, 3.11, and 3.12.

---

### Task 1: Package scaffold and core state/community objects

**Files:**
- Create: `pyproject.toml`
- Create: `src/esdm/__init__.py`
- Create: `src/esdm/core/__init__.py`
- Create: `src/esdm/core/state.py`
- Create: `src/esdm/core/community.py`
- Test: `tests/test_core.py`
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: `StateAxis`, `CommunityStateDistribution`.
- `CommunityStateDistribution.joint_probabilities() -> dict[tuple[str, str], float]`.

- [ ] **Step 1: Write failing core tests**

```python
from esdm.core import CommunityStateDistribution, StateAxis


def test_state_axis_rejects_duplicate_states():
    with pytest.raises(ValueError):
        StateAxis("activity", ("active", "active"))


def test_joint_distribution_multiplies_taxon_and_conditional_state_probabilities():
    community = CommunityStateDistribution(
        taxon_weights={"a": 0.25, "b": 0.75},
        state_probabilities={
            "a": {"low": 0.4, "high": 0.6},
            "b": {"low": 0.2, "high": 0.8},
        },
    )
    assert community.joint_probabilities() == {
        ("a", "low"): pytest.approx(0.10),
        ("a", "high"): pytest.approx(0.15),
        ("b", "low"): pytest.approx(0.15),
        ("b", "high"): pytest.approx(0.60),
    }
```

- [ ] **Step 2: Run CI and verify RED**

Expected: import failures because `esdm.core` does not yet exist.

- [ ] **Step 3: Implement strict probability/state validation and joint distribution**
- [ ] **Step 4: Run focused tests and full CI; require GREEN**
- [ ] **Step 5: Commit implementation**

---

### Task 2: Generic edge evidence hierarchy

**Files:**
- Create: `src/esdm/core/edge.py`
- Modify: `src/esdm/core/__init__.py`
- Test: `tests/test_edge.py`

**Interfaces:**
- Produces: `InteractionEvidenceTier`, `BioticEdge`.
- Tiers are ordered `COAVAILABLE < STATE_COMPATIBLE < PREDICTIVE_DEPENDENCE < REALIZED < FUNCTIONAL < CAUSAL`.

- [ ] **Step 1: Write failing tests for ordered evidence tiers and generic edge metadata**
- [ ] **Step 2: Verify RED in CI**
- [ ] **Step 3: Implement enum/dataclass without taxon-specific inference**
- [ ] **Step 4: Verify GREEN**
- [ ] **Step 5: Commit**

---

### Task 3: q=1 alpha diversity decomposition

**Files:**
- Create: `src/esdm/diversity/__init__.py`
- Create: `src/esdm/diversity/alpha.py`
- Test: `tests/test_alpha_diversity.py`

**Interfaces:**
- Produces: `shannon_entropy`, `hill_q1`, `AlphaDiversityQ1`, `alpha_diversity_q1`.
- `AlphaDiversityQ1` fields: `taxonomic`, `state_given_taxon`, `joint`.

- [ ] **Step 1: Write failing tests**

Required exact cases:
- two equally weighted taxa each deterministic in one state -> taxonomic=2, state=1, joint=2;
- two equally weighted taxa each with two equiprobable states -> taxonomic=2, state=2, joint=4;
- direct joint Hill number equals multiplicative decomposition.

- [ ] **Step 2: Verify RED**
- [ ] **Step 3: Implement entropy/Hill decomposition**
- [ ] **Step 4: Verify GREEN**
- [ ] **Step 5: Commit**

---

### Task 4: q=1 beta diversity decomposition

**Files:**
- Create: `src/esdm/diversity/beta.py`
- Modify: `src/esdm/diversity/__init__.py`
- Test: `tests/test_beta_diversity.py`

**Interfaces:**
- Produces: `BetaDiversityQ1`, `beta_diversity_q1(communities)`.
- Fields: `taxonomic`, `state_given_taxon`, `joint`.

- [ ] **Step 1: Write failing turnover tests**

Taxonomic turnover only:
- site 1 contains only taxon `a`, site 2 only taxon `b`;
- both use the same deterministic state;
- expect taxonomic=2, state_given_taxon=1, joint=2.

State turnover only:
- both sites have identical taxon weights;
- site 1 assigns every taxon to `early`, site 2 to `late`;
- expect taxonomic=1, state_given_taxon=2, joint=2.

- [ ] **Step 2: Verify RED**
- [ ] **Step 3: Implement pooled-minus-mean entropy beta decomposition**
- [ ] **Step 4: Verify multiplicative identity and GREEN**
- [ ] **Step 5: Commit**

---

### Task 5: Geographic versus ecological-state overlap

**Files:**
- Create: `src/esdm/interaction/__init__.py`
- Create: `src/esdm/interaction/overlap.py`
- Test: `tests/test_overlap.py`

**Interfaces:**
- Produces: `overlap_coefficient`, `geographic_overlap`, `state_overlap`.

- [ ] **Step 1: Write failing tests for identical geography/disjoint states**

```python
assert geographic_overlap([0.5, 0.5], [0.5, 0.5]) == pytest.approx(1.0)
assert state_overlap({"early": 1.0, "late": 0.0}, {"early": 0.0, "late": 1.0}) == pytest.approx(0.0)
```

Also reject negative, nonfinite, or all-zero vectors.

- [ ] **Step 2: Verify RED**
- [ ] **Step 3: Implement normalized overlap coefficient**
- [ ] **Step 4: Verify GREEN**
- [ ] **Step 5: Commit**

---

### Task 6: Generic interaction opportunity and evidence semantics

**Files:**
- Create: `src/esdm/interaction/opportunity.py`
- Modify: `src/esdm/interaction/__init__.py`
- Test: `tests/test_opportunity.py`

**Interfaces:**
- Produces: `interaction_opportunity(source_states, target_states, compatibility)`.
- Compatibility keys are `(source_state, target_state)` pairs and values in `[0,1]`.

- [ ] **Step 1: Write failing tests**

Required cases:
- identity compatibility with matching deterministic states -> 1;
- disjoint compatibility -> 0;
- mixed probability fixture matches manual weighted sum;
- same function works with neutral labels (`state_a`, `state_b`) and pollination-like labels, proving no domain-specific branch.

- [ ] **Step 2: Verify RED**
- [ ] **Step 3: Implement generic weighted compatibility calculation**
- [ ] **Step 4: Verify GREEN**
- [ ] **Step 5: Commit**

---

### Task 7: Conditional biotic information gain

**Files:**
- Create: `src/esdm/interaction/biotic_gain.py`
- Modify: `src/esdm/interaction/__init__.py`
- Test: `tests/test_biotic_gain.py`

**Interfaces:**
- Produces: `biotic_information_gain(without_biotic, with_biotic, weights=None) -> float`.
- Inputs are row-wise held-out log scores; function reports mean `with - without`.

- [ ] **Step 1: Write failing tests**

Required cases:
- equal scores -> 0;
- improved scores -> positive;
- degraded scores -> negative;
- weighted mean exactness;
- mismatched/nonfinite input rejected.

- [ ] **Step 2: Verify RED**
- [ ] **Step 3: Implement minimal learner-agnostic scorer**
- [ ] **Step 4: Verify GREEN**
- [ ] **Step 5: Commit**

---

### Task 8: Known-truth analytic worlds

**Files:**
- Create: `src/esdm/benchmarks/__init__.py`
- Create: `src/esdm/benchmarks/worlds.py`
- Test: `tests/test_known_truth_worlds.py`

**Interfaces:**
- Produces: `BinaryInteractionWorld`, `observed_shared_environment_world`, `hidden_shared_driver_world`, `directed_biotic_coupling_world`, `oracle_biotic_information_gain`.
- `BinaryInteractionWorld` stores a normalized joint distribution over `(environment, target_state, partner_state)` plus `interaction_truth: bool` and explanatory metadata.

- [ ] **Step 1: Write failing tests**

Required gates:
- observed shared environment: oracle gain `abs(gain) < 1e-12`, `interaction_truth is False`;
- hidden shared driver: oracle gain `> 0`, `interaction_truth is False`;
- directed coupling: oracle gain `> 0`, `interaction_truth is True`.

- [ ] **Step 2: Verify RED**
- [ ] **Step 3: Implement exact conditional-probability and expected-log-score calculations**
- [ ] **Step 4: Verify GREEN and ensure zero-probability events are never logged**
- [ ] **Step 5: Commit**

---

### Task 9: Non-skippable point transfer ceiling

**Files:**
- Create: `src/esdm/transfer/__init__.py`
- Create: `src/esdm/transfer/ceiling.py`
- Test: `tests/test_transfer_ceiling.py`

**Interfaces:**
- Produces: `TransferStepResult`, `PointTransferCeiling`, `point_transfer_ceiling`.
- Input: base level, ordered `(step_name, next_level)` sequence, `gains_by_step`, tolerance.

- [ ] **Step 1: Write failing tests**

Required cases:
- all groups positive at both steps -> final level;
- first step fails, later step positive -> remains base;
- first passes, second fails -> ceiling at first level;
- nonfinite group gain -> step unavailable and stops ceiling.

- [ ] **Step 2: Verify RED**
- [ ] **Step 3: Implement deterministic non-skippable logic**
- [ ] **Step 4: Verify GREEN**
- [ ] **Step 5: Commit**

---

### Task 10: Integration benchmark and pollination-as-example boundary

**Files:**
- Create: `examples/generic_interactions.py`
- Create: `examples/pollination_as_one_example.py`
- Create: `tests/test_domain_independence.py`
- Create: `docs/PROVENANCE.md`
- Modify: `README.md`

**Interfaces:**
- Generic example must demonstrate competition/mutualism-neutral state labels.
- Pollination example imports only generic public APIs and contains all pollination-specific labels locally.

- [ ] **Step 1: Write domain-independence test**

The test scans `src/esdm` Python files and fails if pollination-specific tokens such as `pollination`, `pollen`, `flower`, `bee`, or `proboscis` occur in runtime source.

- [ ] **Step 2: Verify RED until examples/docs are separated appropriately**
- [ ] **Step 3: Add examples, README architecture, and provenance boundaries**
- [ ] **Step 4: Verify GREEN**
- [ ] **Step 5: Commit**

---

### Task 11: Final verification and PR

**Files:**
- No new scientific files required.

- [ ] **Step 1: Run complete pytest suite on Python 3.10, 3.11, 3.12 via GitHub Actions**
- [ ] **Step 2: Confirm no test or workflow failure**
- [ ] **Step 3: Review diff for pollination leakage and unsupported causal/superiority language**
- [ ] **Step 4: Create PR to `main` with explicit v0.1 claim boundary**
- [ ] **Step 5: Do not merge until exact-head CI is green**
