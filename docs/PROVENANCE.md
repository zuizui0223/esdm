# Provenance and source-project boundaries

`esdm` is now a process-based generative ecological model plus downstream validation/claim-governance layers. It does not copy whole source projects or inherit their strongest claims by default. Each imported idea keeps its original evidence boundary.

## ODSP -> validation semantics

Reused idea:
- explicit information ladders;
- non-skippable transfer ceilings;
- held-out proper-score gain as the quantity asking whether added resolution transfers.

Relevant positive source result:
- prospectively qualified one-sided directional transfer recovered additional correct ceilings relative to the matched two-sided route on the same known-truth worlds;
- independent-group comparison: 196 ceiling advances and 0 regressions across 6,000 paired datasets;
- paired shared-block comparison: 227 advances and 0 regressions across 6,000 paired datasets.

These are methodological simulation results, not biological evidence. `esdm.validate` currently retains point-ceiling and held-out-community gain primitives; it does not reproduce ODSP's calibrated familywise bootstrap-t inference.

## SDMR -> claims/process support

Reused idea:
- do not force one mechanism when evidence supports several;
- sharpen a co-supported process set only with genuinely new separating evidence;
- missing/unavailable/nonexcluding evidence must retain rather than silently eliminate a member.

Relevant source boundary:
- v23 preserved useful multi-member support after forced ranking failed;
- v24 froze monotone contraction using required qualified, source-disjoint, pre-outcome separator evidence.

The canonical `esdm` location is now `esdm.claims`. A temporary compatibility export remains under `esdm.process` while the refactor is in flight. `esdm` does not claim a formal SDMR confidence set, exhaustive identified set, or causal process set.

## 284b -> claims/evidence authorization

Reused idea:
- non-detection, missingness, device failure, occlusion, or unresolved adjudication must not silently become biological absence;
- downstream negative evidence requires an explicit observation-process gate.

Relevant source boundary:
- 284b v8.2 prospectively froze calibration targets and preserved its exact evaluator before field outcomes.

`esdm.claims` imports only the generic authorization boundary. It does not copy 284b's 30/93 targets, exact Clopper-Pearson field gate, retained candidate roster, or field-specific empirical claim.

## EOG -> claims/finite-world contraction

Reused idea:
- a declared finite world universe is not historical truth;
- authorized evidence can contract compatible worlds monotonically;
- unavailable evidence cannot support exclusion.

Relevant source boundary:
- Layer A is a structural compatibility/contraction/falsification architecture;
- Layer-B predictive augmentation was heterogeneous across fresh endpoints.

`esdm.claims` retains only a small generic finite-world contract. It does not copy EOG dynamic reachability, first-passage machinery, relaxation frontiers, fingerprints, or universalize exclusion beyond the declared universe.

## ACSP -> bounded follow-up candidate semantics

Reused idea:
- a useful downstream product can be a bounded candidate set rather than an occupancy probability or priority rank.

Relevant source boundary:
- ACSP's validated product is a non-ranked robust candidate-patch generator with its own frozen constants and validation frame.

The Phase-3 `esdm.observe` discriminating-candidate primitive is new and unvalidated. It is not ACSP candidate-patch validation, field-efficiency evidence, routing, access modelling, or occupancy prediction.

## Previous `esdm` phases: new downstream role

Phase 1 and Phase 2 remain implemented but are no longer the conceptual model entry point.

Their canonical role after the generative-core refactor is:
- state-resolved alpha/beta diversity -> `esdm.summarize`;
- interaction/network diversity and rewiring -> `esdm.summarize`;
- point/community transfer ceilings -> `esdm.validate`;
- observation authorization, process support, world contraction -> `esdm.claims`.

Compatibility imports remain temporarily so earlier tests and examples continue to execute while the code is migrated.

## Generative-core v0.3 boundary

Implemented now:
- discrete `Space × DayOfYear × Hour` domain;
- state-space / partition / refinement declarations;
- backend-neutral ecological `Process` contract and explicit `PriorSpec`;
- `LinearSuitability` environmental contribution to ecological log intensity;
- explicit no-effect suitability knockout;
- effort fields as observation-process inputs, separate from ecological suitability;
- Poisson presence-only record stream with effort and detection;
- `Model.check_design()` static process -> latent-channel -> stream checks;
- latent-species DAG checking and cycle rejection;
- one shared latent-field/rate path for likelihood and in-model simulation;
- prior-to-posterior contraction diagnostic;
- lightweight SBC rank-histogram calibration diagnostic;
- separate misspecified-effort negative-control namespace;
- typed claim status `DesignUninformed / Untested / NotIdentified / NotSupported / Supported` crossed with the existing interaction evidence tier.

The v0.3 SBC layer checks calibration under the declared model only. It is not evidence of robustness to ecological or observation-process misspecification.

## Explicitly not yet implemented / not claimed

- full NumPyro fitting backend;
- posterior fitting in this branch;
- state-process / activity-process generative modules;
- partner-latent-field interaction process;
- camera/annotation observation streams;
- bidirectional or fixed-point interaction models;
- movement/accessibility process;
- calibrated ODSP familywise inference inside `esdm`;
- causal interaction identification;
- universal superiority over SDM/JSDM/ecological-network methods;
- pollination-specific model or validation.

Pollination remains one possible application of the generic future interaction process, not the purpose of `esdm`.
