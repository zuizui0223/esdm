# Provenance and source-project boundaries

`esdm` is an upper-layer synthesis. It does not copy whole source projects or inherit their strongest-sounding claims by default. Each imported idea keeps its original evidence boundary.

## ODSP -> transfer semantics

Reused idea:
- explicit information ladders;
- non-skippable transfer ceilings;
- held-out proper-score gain as the quantity that asks whether additional resolution transfers.

Relevant positive source result:
- prospectively qualified one-sided directional transfer inference recovered additional correct ceilings on the same known-truth worlds relative to the two-sided route;
- independent-group comparison: 196 paired ceiling advances and 0 regressions across 6,000 paired datasets;
- paired shared-block comparison: 227 advances and 0 regressions across 6,000 paired datasets;
- these are methodological simulation results, not biological evidence.

Current `esdm` implementation imports deterministic point-ceiling semantics and a macro-heldout-community gain wrapper. It does not reproduce ODSP's calibrated familywise bootstrap-t inference.

## SDMR -> set-valued process interpretation

Reused idea:
- do not force one mechanism when the evidence supports several;
- sharpen a co-supported process set only with genuinely new separating evidence;
- delete a member only under unanimously excluding required separators that are qualified, source-disjoint, and frozen before separator outcomes.

Relevant positive source result:
- prospective v21 occurrence-based `supported` tier: precision 0.9079, true-process positive rate 0.4417, false-process positive rate 0.0448;
- consumed-development v23 showed that preserving multi-member support retained substantial correct joint-process information, while the prior forced pairwise ranking line failed;
- v24 froze monotone set contraction with new separating evidence and fail-closed handling of missing/unavailable/nonexcluding evidence.

Phase 3 implements a **generic standard-library `esdm.process` contract** with those monotone semantics. It does not import SDMR's data model, process names, occurrence learner, empirical thresholds, or claim that its support set is a formal confidence/identified/causal set.

## 284b -> evidence authorization

Reused idea:
- non-detection, missingness, device failure, occlusion, or unresolved adjudication must not silently become biological absence;
- downstream negative biological evidence opens only after an explicit observation-process gate passes.

Relevant positive source result:
- v8.2 prospectively hardened the Level-C calibration plan before field outcomes, preserving the exact sensitivity/specificity rules and mechanically enforcing resolved sampling targets;
- this is design/authorization evidence, not a biological result.

Phase 3 implements only the generic authorization boundary in `esdm.authorization`:
- positive resolved observations can be positive evidence;
- a raw negative becomes negative evidence only when `negative_gate_passed=True`;
- unqualified negatives and failure/unresolved states become `unavailable`.

`esdm` does **not** copy 284b's 30/93 resolved targets, exact Clopper-Pearson evaluator, retained candidates, or field-specific calibration claim.

## EOG -> finite-world compatibility

Reused idea:
- distinguish a declared finite world universe from historical truth;
- authorized evidence can contract the compatible world set;
- positive/unavailable evidence semantics must remain explicit;
- adding evidence may retain or shrink a compatible set but cannot justify a universal impossibility claim outside the declared universe.

Relevant source boundary:
- EOG Layer A remains a structural compatibility/contraction/falsification architecture;
- fresh Layer-B endpoints were heterogeneous (two favorable, one adverse), so predictive augmentation is context-dependent rather than universally beneficial;
- EOG explicitly preserves compatible worlds rather than collapsing them into one historical explanation.

Phase 3 implements a small generic `esdm.worlds` layer:
- worlds declare expected positive/negative outcomes for named observations;
- `unavailable` evidence cannot eliminate worlds;
- a world that makes no declaration for an observation is retained;
- singleton survival is labelled only `identifiable_within_declared_universe`.

It does **not** copy EOG's dynamic-reachability operators, first-passage calculations, finite-universe fingerprints, relaxation frontiers, predictive Layer-B representation, or universalize EOG's structural claims.

## ACSP -> next-observation set semantics

Reused idea:
- a useful survey output can be a bounded candidate set rather than an occupancy probability or priority rank;
- the end of one inference cycle can become the start of the next observation.

Relevant positive source result:
- the validated Japanese robust candidate-patch product showed positive recovery lift over same-size random patches under its frozen boundary;
- a later fresh automatic global adapter also passed its preregistered conditional confirmation gates within the tested provider/evidence-aware frame;
- the validated product is explicitly non-ranked and is not a calibrated occupancy probability.

Phase 3 implements `esdm.observe` as a **new, unvalidated discriminating-observation candidate-set primitive**. A candidate is admitted when currently surviving declared worlds make conflicting binary predictions for it. Lexical ordering is for reproducibility only and `ranked=False` is explicit.

This is not ACSP candidate-patch validation, field-efficiency evidence, expected-information-gain optimality, routing, access modelling, or occupancy prediction.

## `esdm` Phase-1 scientific boundary

Implemented in Phase 1:
- generic ecological state axes;
- community taxon/state distributions;
- q=1 alpha and beta state-resolved diversity decomposition;
- geographic versus state overlap;
- generic potential interaction opportunity;
- held-out biotic information gain;
- analytic known-truth worlds separating measured shared environment, hidden shared driver, and true directed coupling;
- deterministic non-skippable point transfer ceiling.

## `esdm` Phase-2 scientific boundary

Implemented in Phase 2:
- generic directed interaction-network distributions over declared taxa;
- expected connectance from absolute edge probabilities;
- q=1 interaction and source-specific partner diversity from normalized positive edge mass;
- q=1 network beta diversity;
- shared-taxon rewiring that conditions out unique taxa before comparing edge distributions;
- state-conditioned connectance for caller-declared state slices;
- held-out Bernoulli log-score gain macro-averaged by independent community;
- a non-skippable community-level point information ceiling;
- deterministic known-truth worlds for stable networks, pure rewiring, connectance shift without rewiring, taxon turnover, positive transfer, and null transfer.

Phase 2 keeps **absolute connectance** separate from **normalized rewiring**, and keeps taxon, state, and network turnover as separate axes rather than claiming one total multiplicative beta identity.

## `esdm` Phase-3 scientific boundary

Implemented in Phase 3:
- raw observation -> `positive | negative | unavailable` evidence authorization;
- explicit protection against treating unqualified non-detection/failure as biological absence;
- empty/singleton/multi-member process support sets;
- monotone process-set contraction only under unanimous qualified/source-disjoint/pre-outcome exclusion evidence;
- finite declared ecological-world sets with monotone contraction from authorized observations;
- explicit `identifiable_within_declared_universe` singleton status without a historical-truth claim;
- non-ranked sets of observations that discriminate surviving worlds;
- one-cycle orchestration that keeps process and world evidence streams separate.

The Phase-3 selector is a method primitive only. It has no field-validation, optimality, cost, routing, or discovery-rate evidence.

## Still not implemented / not claimed

- calibrated ODSP familywise uncertainty inside `esdm`;
- exact 284b calibration statistics or field authorization parity;
- formal SDMR confidence/identified sets;
- EOG dynamic reachability / finite-universe certification machinery;
- ACSP validated patch generation or field-efficiency transfer to the new selector;
- optimal experimental design or expected-information-gain ranking;
- a fitted universal learner;
- causal interaction identification;
- realized or functional interaction from potential edge probabilities;
- universal superiority over JSDM or ecological-network methods.

Pollination remains an example only. Core runtime code is intentionally free of pollination-specific logic.
