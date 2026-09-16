# Inference / Observation Loop v0.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add evidence authorization, set-valued process refinement, finite-world contraction, and non-ranked next-observation candidate sets above the Phase-2 community-network kernel.

**Architecture:** Keep the four layers independent and composable. Authorization converts raw observation states to positive/negative/unavailable evidence. Process refinement is monotone and uses only declared separator evidence. World contraction acts only on authorized observations inside a declared finite universe. Observation nomination returns a deterministic but non-ranked set of candidates that split surviving worlds.

**Tech Stack:** Python 3.10–3.12, standard library only at runtime, pytest for tests.

**Spec:** `docs/superpowers/specs/2026-09-16-inference-observation-loop-v03.md`

## Global Constraints

- Runtime dependencies remain standard-library only.
- Pollination-specific logic remains forbidden under `src/esdm`.
- `unavailable` must never be coerced to biological negative.
- Process refinement may remove but never add members.
- Surviving worlds are not historical truth.
- Next-observation output is non-ranked and carries no occupancy/field-efficiency/optimality claim.

---

### Task 1: Observation authorization

**Files:**
- Create: `src/esdm/authorization/__init__.py`
- Create: `src/esdm/authorization/evidence.py`
- Test: `tests/test_authorization.py`

**Interfaces:**
- Produces: `ObservationRecord`, `AuthorizedObservation`, `authorize_observation`.

- [ ] Write tests requiring positive -> positive, qualified negative -> negative, unqualified negative -> unavailable, and missing/unresolved/device_failure/occluded -> unavailable.
- [ ] Run full pytest and verify RED because `esdm.authorization` does not exist.
- [ ] Implement strict enums/validation and deterministic reasons.
- [ ] Run full pytest and verify GREEN.

### Task 2: Set-valued process refinement

**Files:**
- Create: `src/esdm/process/__init__.py`
- Create: `src/esdm/process/support.py`
- Test: `tests/test_process_support.py`

**Interfaces:**
- Produces: `ProcessSupportSet`, `SeparatorEvidence`, `ProcessRefinement`, `refine_process_support_set`.

- [ ] Write tests for empty/singleton/multi-member sets and duplicate rejection.
- [ ] Write tests showing missing/unavailable/indeterminate/compatible/unqualified separator evidence retains members.
- [ ] Write a test showing removal only under unanimous required `exclude` evidence with qualified/source-disjoint/preoutcome-frozen flags.
- [ ] Write a monotonicity test proving refinement cannot add a process.
- [ ] Run full pytest and verify RED.
- [ ] Implement the minimal standard-library refinement kernel.
- [ ] Run full pytest and verify GREEN.

### Task 3: Finite declared ecological worlds

**Files:**
- Create: `src/esdm/worlds/__init__.py`
- Create: `src/esdm/worlds/compatibility.py`
- Test: `tests/test_worlds.py`

**Interfaces:**
- Consumes: `AuthorizedObservation` from Task 1.
- Produces: `EcologicalWorld`, `EcologicalWorldSet`, `WorldContraction`, `contract_world_set`.

- [ ] Write tests showing unavailable evidence eliminates no world.
- [ ] Write tests showing an authorized conflicting positive/negative can eliminate a declaring world.
- [ ] Write sequential-contraction tests proving survivors never increase.
- [ ] Write a test requiring the singleton status label `identifiable_within_declared_universe` and no `truth` property.
- [ ] Run full pytest and verify RED.
- [ ] Implement finite-world compatibility and contraction.
- [ ] Run full pytest and verify GREEN.

### Task 4: Non-ranked next-observation candidate set

**Files:**
- Create: `src/esdm/observe/__init__.py`
- Create: `src/esdm/observe/candidates.py`
- Test: `tests/test_observe.py`

**Interfaces:**
- Consumes: `EcologicalWorldSet` from Task 3.
- Produces: `ObservationCandidate`, `DiscriminatingObservationSet`, `nominate_discriminating_observations`.

- [ ] Write tests admitting only candidates with conflicting declared outcomes across surviving worlds.
- [ ] Write tests showing deterministic lexical ordering but `ranked=False` and no score/occupancy fields.
- [ ] Write tests for one-world and zero-discrimination empty candidate sets.
- [ ] Run full pytest and verify RED.
- [ ] Implement candidate-set nomination without scientific ranking.
- [ ] Run full pytest and verify GREEN.

### Task 5: End-to-end cycle

**Files:**
- Create: `src/esdm/inference.py`
- Test: `tests/test_inference_cycle.py`

**Interfaces:**
- Consumes all Tasks 1–4.
- Produces: `InferenceObservationCycle`, `run_inference_observation_cycle`.

- [ ] Write a known-truth test with `shared_environment`, `competition`, and `mutualism` explanations where one raw negative is unavailable, an independent separator removes one process, one authorized positive contracts the world set, and the remaining disagreement nominates the next observation.
- [ ] Verify the unavailable negative has zero effect on world elimination.
- [ ] Run full pytest and verify RED.
- [ ] Implement the orchestration object without merging the process/world evidence streams.
- [ ] Run full pytest and verify GREEN.

### Task 6: Documentation, provenance, and exact-head verification

**Files:**
- Modify: `README.md`
- Modify: `docs/PROVENANCE.md`
- Create: `examples/inference_observation_loop.py`
- Modify: `tests/test_examples.py`

- [ ] Document the new four-stage inference loop and explicit non-claims.
- [ ] Record which rule is distilled from 284b / SDMR / EOG / ACSP and which source-project guarantees are not imported.
- [ ] Add a generic example with no pollination-specific runtime dependency.
- [ ] Run the complete suite on Python 3.10/3.11/3.12 in GitHub Actions.
- [ ] Compare stacked diff against `feature/community-network-rewiring-v02`.
- [ ] Open a draft stacked PR only after exact-head verification is green.
