# Phase 3 — inference / observation loop v0.3

## Goal

Extend the Phase-1/2 state/community/network kernel with four generic inference-governance primitives:

1. observation/evidence authorization;
2. set-valued process explanation and monotone refinement;
3. finite declared ecological-world contraction;
4. non-ranked next-observation candidate sets.

The phase closes the loop

```text
predict state/network
    -> authorize observations
    -> preserve/refine process explanations
    -> contract declared ecological worlds
    -> nominate discriminating next observations
```

It does not add a universal learner, causal identification, or an optimal survey planner.

## Source-project contracts distilled

### 284b -> authorization

Import only the inference boundary:
- unresolved, missing, device-failure, occluded, or otherwise unqualified records are not biological negatives;
- a negative claim may open only when its observation process has an explicitly satisfied calibration/authorization contract;
- `unavailable` is a first-class state, not a negative.

The exact 284b v8.2 field calibration sample sizes and Clopper-Pearson evaluator remain owned by 284b and are not copied into `esdm`.

### SDMR -> set-valued explanations

Import the v23/v24 rule:
- a supported explanation set may have zero, one, or multiple members;
- a member may be removed only by genuinely new, predeclared separating evidence;
- every required separator must be present, qualified, source-disjoint from the support evidence, frozen before outcomes, and return `exclude`;
- missing, unavailable, indeterminate, compatible, or unqualified evidence retains the member;
- no new member can be added by refinement;
- no unique winner is forced.

### EOG -> finite declared worlds

Import only exact finite-world semantics:
- `W(O)` is the subset of a declared world universe compatible with authorized observations;
- positive/negative observations can eliminate declared worlds only under their declared prediction contract;
- unavailable evidence does not eliminate worlds;
- adding authorized observations may retain or shrink the world set, never enlarge it;
- one surviving declared world means identifiable *within the declared finite universe*, not historical truth or universal ecological truth.

### ACSP -> candidate-set semantics

Import only the product-shape lesson:
- next-observation output is a bounded/non-ranked candidate set, not an occupancy probability, priority rank, route, or field-efficiency claim;
- candidates are admitted because they discriminate among currently surviving declared worlds;
- no optimality or expected-information-gain claim is made in Phase 3.

## Runtime objects

### `esdm.authorization`

`ObservationRecord`
- `observation_id`
- `raw_state`: `positive | negative | missing | unresolved | device_failure | occluded`
- `negative_gate_passed`
- optional provenance flags

`authorize_observation(record)` returns an `AuthorizedObservation` with:
- `evidence_state`: `positive | negative | unavailable`
- explicit reason

Rules:
- positive resolved observations are usable without a negative-detection gate;
- negative is usable only when `negative_gate_passed=True`;
- all unresolved/failure states are `unavailable`;
- an unqualified negative is `unavailable`, not `negative`.

### `esdm.process`

`ProcessSupportSet`
- ordered unique member names;
- empty/singleton/multi-member all legal.

`SeparatorEvidence`
- process
- separator_id
- evidence_state: `exclude | compatible | indeterminate | unavailable`
- qualified
- source_disjoint
- preoutcome_frozen

`refine_process_support_set(...)`
- monotone subset refinement only;
- unanimous qualified exclusion across every required separator to remove a member;
- otherwise retain;
- returns member audit and contraction summary.

### `esdm.worlds`

`EcologicalWorld`
- `world_id`
- declared mapping `observation_id -> expected evidence state(s)`;
- predictions are limited to `positive | negative`; absence of a prediction means the world makes no declared claim for that observation.

`EcologicalWorldSet`
- declared universe;
- surviving subset;
- history of authorized observations and eliminated worlds.

`contract_world_set(...)`
- ignores `unavailable` evidence;
- eliminates a world only when it declares a prediction for that observation and the authorized observed state is incompatible;
- never re-adds eliminated worlds;
- returns contraction diagnostics;
- `identifiable_within_declared_universe=True` only when one survivor remains.

### `esdm.observe`

`ObservationCandidate`
- candidate_id
- declared predicted binary outcome by world.

`nominate_discriminating_observations(...)`
- considers only surviving worlds;
- candidate is admitted when at least two surviving worlds make conflicting declared binary predictions;
- candidates with missing world predictions may be retained only if at least two declared predictions conflict;
- output ordering is deterministic but explicitly **not a scientific ranking**;
- output carries no occupancy/field-efficiency/optimality claim.

## Integration object

`run_inference_observation_cycle(...)` combines:
1. authorization of raw observations;
2. process-set refinement from separately supplied separator evidence;
3. world-set contraction from authorized observations;
4. nomination of discriminating next observations.

The process and world streams remain logically separate. Process refinement must not inspect world truth labels, and world contraction must not coerce unavailable records into negatives.

## Known-truth gates

Phase 3 must demonstrate:

1. unresolved/device-failure/non-calibrated negatives become `unavailable`;
2. unavailable evidence cannot eliminate a world;
3. calibrated negative evidence can eliminate a world that declared `positive`;
4. process refinement preserves members under missing/unavailable/compatible/indeterminate evidence;
5. unanimous qualified source-disjoint pre-outcome exclusion can remove a member;
6. refinement can never add a process;
7. sequential world contraction is monotone;
8. one surviving world is labelled only as identifiable within the declared universe;
9. next-observation output contains exactly discriminating candidates and is explicitly non-ranked;
10. an end-to-end cycle can reduce both process/world uncertainty and nominate the unresolved next observation without using unavailable evidence as a biological negative.

## Non-claims

Phase 3 does not claim:
- causal interaction identification;
- exact 284b calibration parity;
- formal SDMR confidence/identified sets;
- universal EOG impossibility outside a declared finite universe;
- ACSP field-efficiency or candidate-patch validation for this new observation selector;
- optimal experimental design;
- pollination-specific inference.
