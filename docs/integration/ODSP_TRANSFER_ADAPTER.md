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
