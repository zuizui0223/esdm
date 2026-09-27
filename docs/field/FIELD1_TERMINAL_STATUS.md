# FIELD1 Phase-A terminal result

Status: **FAIL**

Date: 2026-09-27

FIELD1 completed the frozen replacement qualification run `36316137677` on
`field1/qualification-v1-r2`.

## Execution integrity

- 9 known-truth worlds
- 16 replicates per world
- **144 / 144 shards**
- **704 / 704 fits**
- no missing or extra frozen fit plans
- H1/H2 training edge-axis rank audits: PASS
- K6 training-only distance match: PASS
- learned-barrier H2 transfer geometry: PASS

The first authorization attempt remains separately frozen as an infrastructure-only
stop with zero scientific shards.

## Frozen decision

```text
FIELD1 Phase-A overall: FAIL

FIELD_PRESENT:                  true
ENV_DEPENDENCE_SUPPORTED:      false
BARRIER_DEPENDENCE_SUPPORTED:  false
FULL_MAP_STRUCTURE_SUPPORTED:  false
```

The distance-only field did what it was supposed to do in the central positive/negative
control: M1-M0 on H1 was positive-qualified in K1 (positive rate 0.75; mean gain
+4.7197) and null-qualified in K0 (material rate 0.0625; mean gain -0.0755).

The extra dependence axes did not separate cleanly. In particular, M2-M1 false-promoted
under K0 and K1, and the K5 mean/covariance firewall did not classify covariance truth
reliably. The barrier axis also failed its positive worlds: K3 M3-M1 H2 had positive
rate 0.4375 and mean gain -0.0149.

The full model did not pass K4: M4-M2 on H2 had positive rate 0.4375 and mean gain
+0.00264, below both frozen positive criteria.

## Sampling guardrail

The run accumulated **360 divergences across 704 fits**, or **0.51136 divergences per
fit**, exceeding the frozen maximum 0.10.

Therefore the overall programme does not promote FIELD1 Phase-A even though the internal
`FIELD_PRESENT` claim flag is true.

## Scientific interpretation

What survives is narrow:

> a coherent distance-structured latent spatial field can add held-out mapping
> information beyond the environment-only model in this known-truth programme.

FIELD1 does **not** qualify the environmental-similarity or barrier-modified covariance
axes, and it does not support dispersal, movement, gene flow, or evolutionary IBD/IBE
mechanism claims.

No same-program rerun, threshold retuning, or rescue generation is authorized by this
result.

## Provenance

- workflow run: `36316137677`
- aggregate artifact: `10932280009`
- artifact digest:
  `sha256:a6a9e40d7f31dfb3190ecd1c58f6770afee6fd21442a81ec3fdfa69358cf84e7`
- machine-readable receipt:
  `docs/field/FIELD1_PHASE_A_FROZEN_RESULTS.json`

## Post-outcome diagnostic

A descriptive, non-promotional post-mortem is frozen in
`docs/field/FIELD1_POSTMORTEM.md` with machine-readable geometry diagnostics in
`docs/field/FIELD1_POSTMORTEM_DIAGNOSTICS.json`.

It does not reopen FIELD1. Its main structural finding is that the frozen distance and
environmental-dissimilarity edge axes are formally full-rank but practically
near-collinear, while the barrier failure remains only partly explained.

