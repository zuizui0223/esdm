# ODSP transfer evidence ledger v2

Version 1 intentionally contained only validated ODSP-exportable transfer
contrasts. That made the numeric portfolio clean, but it also created a display
risk: a downstream reader could see only successful transfers and forget that
other frozen programmes had failed, were non-nested, or could not be serialized
without reconstruction.

Version 2 preserves the four validated numeric items and adds a mandatory
**excluded-source ledger**.

## Two evidence classes

### validated_items

These are the same four frozen transfer sources as portfolio v1:

- v0.4-R5b activity;
- v0.4-R5b state;
- v0.6a accessibility;
- v0.7b dynamic occupancy.

They have validated integration receipts and may carry numeric population
transfer summaries.

### excluded_sources

Every other source in the transfer-source registry appears here with:

- registry status;
- frozen scientific status;
- exclusion class;
- frozen receipt and receipt hash;
- reason for exclusion;
- numeric_transfer_value = null;
- numeric_transfer_value_authorized = false;
- unsupported_not_zero = true.

The last field is important. A source that is not authorized for an ODSP
transfer value is **not assigned zero ecological value**.

## Interaction replication example

The v0.5f directed-interaction replication is retained explicitly as a
scientific failure:

- interaction world: 16/16 positive gains;
- mean interaction-world held-out gain: +1.11905875495;
- measured-shared null: 5/16 material positive gains above +0.005;
- frozen maximum allowed: 4/16;
- null mean gain: -0.03268656164;
- failed check: null_material_gain_rate.

The correct downstream representation is therefore:

unsupported for validated interaction-transfer attribution

not interaction transfer value = 0, and not interaction transfer value = +1.119.

The positive signal exists, but the frozen specificity criterion failed.

## Other exclusion classes

The ledger distinguishes:

- serialization_ineligible: gain-only frozen result; absolute scores cannot be reconstructed;
- scientific_gate_failed: frozen scientific FAIL;
- different_evidence_estimand: useful evidence tier, but not a held-out nested transfer contrast;
- identification_only: identification result without a held-out transfer outcome;
- non_nested_information: model/evidence comparison where neither information set strictly contains the other.

## Selection boundary

A v2 consumer must not display the validated items as if they were the complete
eSDM evidence base while hiding the exclusions.

The ledger explicitly forbids:

- dropping excluded sources from a complete evidence display;
- converting unsupported sources to numeric zero;
- promoting a scientific FAIL into a numeric transfer value;
- reconstructing gain-only sources;
- relabelling non-nested comparisons as information transfer.

## Ranking and action boundaries

Version 2 does not create a global information ladder and does not authorize
cross-programme magnitude ranking.

It also does not authorize:

- EOG consumption;
- state promotion;
- spatial patch ranking;
- survey-site selection;
- N4 action.

The purpose is audit completeness, not decision automation.
