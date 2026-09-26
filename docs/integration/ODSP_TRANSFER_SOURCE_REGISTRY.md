# ODSP transfer-source registry v1

The transfer adapter accepts only frozen eSDM results that actually contain the
score information required by an ODSP information contrast.

The authoritative registry is:

`ODSP_TRANSFER_SOURCE_REGISTRY_V1.json`

This is an eligibility registry, not a new scientific gate.

## Exportability rule

A frozen programme is ODSP-exportable only when all of the following are true:

1. a completed immutable result exists;
2. the result stores **absolute held-out scores** for every compared level;
3. compared levels were scored on the same held-out observations;
4. the same proper scoring rule and reference measure apply;
5. the declared information sets are strictly nested;
6. the adapter and a validated cross-repository integration receipt exist.

A scientific PASS alone is not sufficient.

In particular, a stored gain

`Full - knockout = +0.4`

does not authorize constructing artificial score columns such as `0` and
`+0.4`. ODSP receives the original absolute scores or nothing.

## Current validated exportable sources

### v0.4-R5b activity

Parallel contrast:

`suitability + state < suitability + state + activity`

Validated population mean gain: +0.00699856.

### v0.4-R5b latent state

Parallel contrast:

`suitability + activity < suitability + activity + state`

Validated population mean gain: +0.02896467.

Activity and state are deliberately not concatenated into a three-level chain.
Their knockouts condition on different sibling information and no natural order
has been frozen.

### v0.6a static accessibility

`suitability < suitability + accessibility`

Validated population mean gain: +0.36244192.

### v0.7b marginal dynamic occupancy

`suitability < suitability + dynamic occupancy`

Validated population mean gain: +7.09082799.

This is marginal occupancy information, not a movement kernel or realized
colonization/extinction event history.

## Sources that are intentionally not exportable

### v0.5a directed interaction

Scientific result: PASS.

Registry status: `gain_only_not_exportable`.

The frozen result retained held-out gain but not both absolute full and knockout
log scores. Reconstructing an arbitrary baseline would violate the score
contract.

### v0.5f independent interaction replication

Scientific result: FAIL.

Registry status: `scientific_fail_not_exportable`.

This replication intentionally fixed the old v0.5a serialization limitation:
all 32 records preserved original absolute Full and partner-knockout held-out log
scores, and the score identity was exact. The positive interaction world was
strong (16/16 positive gains; mean +1.11906 nats/context), but the frozen
measured-shared null specificity criterion failed by one replicate: 5/16 null
replicates exceeded gain > +0.005, while at most 4/16 were allowed.

Absolute score availability therefore does not override the scientific gate.
The generated ODSP-compatible CSV/contract is retained only as serialization
evidence and is not a validated transfer source.

### v0.5b hidden common driver

Scientific result: FAIL.

Registry status: `scientific_fail_not_exportable`.

Its large predictive gain is part of the frozen failure result, not a reason to
promote it into a transfer source.

### v0.5e interaction evidence separation

Registry status: `evidence_tier_not_transfer`.

This programme distinguishes predictive dependence and realized event evidence.
It did not define a nested held-out score filtration.

### v0.6b joint accessibility audit

Registry status: `identification_only_not_transfer`.

Identification evidence is not a held-out transfer result.

### v0.6c Direct versus MatchedJoint

Registry status: `non_nested_comparison_not_transfer`.

This compares two evidence designs for the same ecological target. It is not a
strict information-set nesting.

### v0.7a dynamic occupancy identification

Registry status: `identification_only_not_transfer`.

The programme established the identification boundary before a recovery or
held-out transfer result existed.

### v0.7c dynamic versus matched static occupancy

Scientific result: PASS.

Registry status: `non_nested_comparison_not_transfer`.

The recursive dynamic model outperformed a fully estimable memoryless static
occupancy comparator in 15/16 frozen replicates, with mean held-out gain
+3.32124 nats/context. That is evidence for the value of the dynamic
**representation**, not an ODSP information filtration: both candidates target
the same occupancy information under the same observation programme. A model
representation can win predictively without containing a strict superset of
ecological information.

## Usage

List all sources:

    python scripts/list_odsp_transfer_sources.py

List only sources that may be exported:

    python scripts/list_odsp_transfer_sources.py --exportable-only

Machine-readable output:

    python scripts/list_odsp_transfer_sources.py --json

Downstream code should call `require_exportable_transfer_source` rather than
guessing eligibility from programme names or PASS/FAIL labels.

## Boundary

The registry cannot:

- authorize a new scientific result;
- authorize a rerun;
- reconstruct missing absolute scores;
- invent an information ordering;
- reopen the frozen current EOG mainline;
- authorize N4 survey action.

A new programme becomes exportable only after its own frozen result schema stores
commensurate absolute held-out scores and a separate integration validation
passes.


## v0.7d equal-dimension static-versus-dynamic benchmark

v0.7d is deliberately **not** ODSP-exportable even though its frozen result is a
strong PASS.

The paired models have the same ecological-information target—occupancy—and the
same four-parameter dimension. They differ in representation:

- recursive colonization/extinction dynamics;
- memoryless quadratic occupancy trend.

Neither model's information set is a strict subset of the other. The result is
therefore a model-representation benchmark, not an information-transfer
filtration. Its frozen PASS cannot be relabeled as a new ODSP information level.


## v0.7e reciprocal static-world benchmark

v0.7e is also deliberately **not** ODSP-exportable.

Its reciprocal PASS strengthens the v0.7 model-resolution interpretation:
the recursive model wins in the dynamic generator world, while the
equal-dimension static model wins in the static generator world.

That result is a comparison of alternative representations of the **same**
occupancy information. Reversing the generator changes which representation is
better but does not create a lower-information / higher-information nesting.
Accordingly, no ODSP endpoint is authorized for v0.7e.
