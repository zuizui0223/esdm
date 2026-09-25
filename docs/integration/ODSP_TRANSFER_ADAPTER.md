# ODSP transfer adapter v1

eSDM and ODSP own different parts of the inference stack.

eSDM fits ecological process models and produces held-out predictive scores.
ODSP audits what additional **information** those scores support.

The adapter in `esdm.transfer.odsp_adapter` writes an ODSP-compatible
`scores.csv` plus `endpoint.json`. eSDM does not import ODSP.

## Required structure

Only strict nested information levels can be exported.

Valid:

```text
suitability
  subset
suitability + accessibility
```

Invalid:

```text
Direct accessibility evidence
vs
budget-matched extra joint occurrence
```

The second comparison changes evidence design while keeping the ecological
information target the same. It is a model/evidence comparison, not an ODSP
information filtration.

## First binding: v0.6a accessibility

The frozen v0.6a replicate already records two commensurate held-out log scores:

```text
accessibility_knockout_heldout_log_score
full_heldout_log_score
```

The adapter maps them to:

```text
suitability_only
    information = [suitability]

suitability_accessibility
    information = [suitability, accessibility]
```

Each known-truth replicate is one independent ODSP group.

The resulting ODSP analysis is labelled descriptive. The original v0.6a
filtration was frozen before outcome scoring, but the cross-repository population
summary was not itself part of the original promotion decision.

## Files

```bash
python scripts/export_v06a_odsp_transfer.py \
  --result V06A_RESULT.json \
  --out-dir build/odsp-transfer
```

This writes:

```text
build/odsp-transfer/scores.csv
build/odsp-transfer/endpoint.json
build/odsp-transfer/adapter_manifest.json
```

Then, in an environment with ODSP installed:

```bash
odsp transfer \
  --contract build/odsp-transfer/endpoint.json \
  --out build/odsp-transfer/receipt.json
```

## Future process layers

The same adapter can express a genuinely nested ladder such as:

```text
environment
subset environment + traits
subset environment + traits + movement
subset environment + traits + movement + activity
subset environment + traits + movement + activity + interactions
```

but only when every level is scored on the same held-out observations under a
common proper scoring rule and common reference measure.

A later process module does not automatically become a new level merely because
its algorithm is more complex.

## Downstream handoff

The intended cross-repository path is:

```text
eSDM held-out scores
 -> ODSP transfer
 -> population_result
 -> N2->N3 transfer-value payload
 -> EOG reachability/world integration
 -> ACSP survey action
```

This keeps process fitting, information attribution, reachability and field
action separate.


## Validated end-to-end binding

The first full cross-repository smoke is frozen in
`ODSP_TRANSFER_E2E_BINDING_V1.json` and
`ODSP_TRANSFER_E2E_RESULT_V1.json`.

Pinned inputs:

- frozen eSDM v0.6a result artifact: run `35989902607`;
- eSDM adapter merge: `e9bec1be8136a85c265af3604394d3389319998d`;
- ODSP transfer-value implementation: `0bd83e1ebb372c48839654ab0e42124fe37b8faf`.

Observed result:

```text
frozen eSDM mean accessibility gain       +0.3624419158
ODSP population mean gain                 +0.3624419158
ODSP population 95% interval              [0.2704104400, 0.4494118616]
ODSP population ceiling                   suitability_accessibility
N3 conservative mean transfer value       +0.2704104400
new-replicate prediction interval          [-0.0159813874, 0.7408652190]
legacy ODSP certified ceiling             suitability_only
```

The source and ODSP population means agree exactly. The difference between the
population and legacy certified ceilings is expected: v0.6a contributes one
aggregate held-out score per independent replicate, so the older within-group
minimum-block certification has zero estimable cells, whereas the population
estimand has 16 independent replicate gains.

The N3 payload preserves that distinction rather than treating certification
failure as absence of transfer value.

## Current EOG boundary

The present EOG-WF scientific mainline is closed and must not be reopened by this
integration. The transfer-value payload is therefore a **forward interface for a
future separately authorized N3 protocol/version**, not a new input to the
frozen EOG-WF endpoint denominator.

In particular, the validated payload does not feed the existing EOG survey
ranking implementation and does not authorize any N4 action.


## Second validated level: v0.7b dynamic occupancy

The same cross-repository path has now been validated for a second, independently
frozen information contrast:

```text
suitability
  subset
suitability + dynamic occupancy
```

The source is the authorized v0.7b known-truth result. Direct occupancy
calibration exists only in early training contexts; held-out contexts contain
joint occurrence only.

Frozen v0.7b result:

```text
replicates                              16
positive dynamic-occupancy gain        16 / 16
mean Full - occupancy-knockout gain    +7.0908279898 nats/context
minimum replicate gain                 +3.5637099446
divergences                            0 / 32 fits
```

Pinned ODSP audit:

```text
population mean gain                    +7.0908279898
95% group-bootstrap interval            [6.1125664615, 7.9616799541]
population ceiling                      suitability_dynamic_occupancy
legacy certified ceiling                suitability_only
```

The older certified ceiling again stops at the base level because each
known-truth replicate contributes one aggregate held-out score row. The
population estimand instead uses the 16 independent replicate gains directly.

The N2-to-N3 handoff carries:

```text
expected transfer value                 +7.0908279898
conservative mean value                 +6.1125664615
new-replicate prediction interval       [2.9856269032, 11.1960290763]
```

This establishes a software/inference interface for **marginal dynamic occupancy
information**. It does not turn the v0.7 process into a movement kernel,
connectivity model, realized colonization history, or field-survey priority.
