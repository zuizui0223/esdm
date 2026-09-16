# v0.3.1 validation results

Status: **PASS — all frozen Gates A–F passed**

This document records outcomes against the pre-outcome criteria in
`docs/validation/V031_PROMOTION_GATE.md`. Thresholds were not changed in response to these
outcomes. The earlier v0.3 promotion interpretation is retired; its runs remain historical
implementation diagnostics only.

`PASS` here means that the implementation satisfies the declared **v0.3.1 methodological
promotion gate**. It is not empirical validation of a biological system, not evidence that every
future process is identifiable, and not a causal-interaction claim.

## Gate A — claim / identification separation: PASS

The deterministic contract requires posterior contraction to return identification status,
not scientific support. Exact-head CI verifies that contraction can yield
`Identified` / `NotIdentified`, while `Supported` remains a separate claim type.

## Gate B — stream target sets: PASS

Exact-head CI verifies that:

- non-target taxa contribute no likelihood term;
- a missing block for a declared target raises `MissingTargetDataError`;
- missing taxa are not converted to observed all-zero histories;
- deterministic and NumPyro paths use the same target-set contract.

## Gate C — neutral-parameter knockout: PASS

Frozen full run:

- workflow run: `35089665238`
- artifact: `v031-gate-c-35089665238`
- artifact id: `10443743215`
- workflow head: `4f6f165bb3574249e037462b5dd621672059f8aa`
- replicates: 100
- generating rule: preserve baseline intercept and set only the environmental slope to zero

Observed summary:

- mean posterior beta: `-0.004444473068341464`
- absolute mean posterior beta: `0.004444473068341464` (criterion `<= 0.10`)
- zero coverage: `0.92` (criterion `[0.82, 0.98]`)
- nonzero-interval rate: `0.08` (criterion `<= 0.12`)
- total divergences: `0`
- mean divergences per fit: `0.0` (criterion `<= 0.10`)

Mechanical Gate C decision: **PASS**.

## Gate D — structural-identification negative control: PASS

Exact-head CI verifies the predeclared design result:

1. one opportunistic presence-only stream with unknown log-linear effort gradient has
   `beta_x` and `gamma_x` as `NotIdentified`, because only their sum is observable;
2. the ecological intercept remains identified in that design;
3. adding a second known-effort stream restores unique sensitivity directions, so both
   `beta_x` and `gamma_x` become `Identified`.

This gate is a refusal/authorization check, not a point-estimate recovery check.

## Gate E — all-parameter ESS-aware simultaneous-ECDF SBC: PASS

Frozen full run:

- workflow run: `35089684927`
- artifact: `v031-gate-e-35089684927`
- artifact id: `10443399472`
- workflow head: `3b56b92c57c679aed317de7bcd52513baf3dc0e5`
- prior-predictive replicates: 100
- chains per fit: 2
- all free parameters tested: ecological intercept, ecological slope, observation-effort slope

Observed simultaneous-ECDF result:

- familywise critical max deviation: `0.14154832656452426`
- observed familywise max deviation: `0.069801670882707`
- ecological slope (`beta_x`) max deviation: `0.05059413139894264`
- intercept max deviation: `0.069801670882707`
- observation-effort slope (`gamma_x`) max deviation: `0.06875935054475224`
- mean divergences per fit: `0.03` (criterion `<= 0.10`)

ESS / post-thinning support ranges retained in the artifact:

- `beta_x`: ESS `149.185 .. 539.121`, rank-draw support `134 .. 400`
- intercept: ESS `106.289 .. 590.704`, rank-draw support `100 .. 400`
- `gamma_x`: ESS `128.787 .. 567.510`, rank-draw support `115 .. 400`

Mechanical Gate E decision: **PASS**.

## Gate F — pinned real-geometry semi-synthetic transfer: PASS

Frozen scientific profile:

- pinned source repository: `the-pudding/data`
- pinned source commit: `3dcb0a80c838ff9503e3957d7e004a7f4b888b0a`
- pinned source path: `rain/annual_precipitation.csv`
- expected Git blob SHA1: `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`
- selected station rows: first 120 data rows under the pinned source ordering
- geometry: 120 real stations x 6 day-of-year bins x 4 hour bins
- training blocks: west + central
- completely held-out block: east
- train spaces: 67; held-out east spaces: 53
- replicates: 20
- base seed: `20260921`, replicate stride: `37`
- warmup: `200`, posterior samples: `250`, chains: `2`

### Infrastructure history

The first full attempt (`35089704914`) did not reach a scientific decision. JAX/LLVM
terminated with memory-allocation failures before the final JSON artifact was written. It is
therefore recorded as an **infrastructure interruption, not a scientific Gate F failure**.

A non-promotional one-replicate exact-profile diagnostic then established that the scientific
profile itself fits on the same runner class:

- successful diagnostic run: `35093359984`
- artifact id: `10445003190`
- maximum resident set size: `3852368` kB (about 3.7 GiB)
- replicate-0 held-out gain: `0.3365728113741402`
- divergences: 0

The diagnosis supported cumulative JAX/XLA memory lifetime across repeated fits in one Python
process. The execution layer was therefore changed to run each **predeclared replicate in a
fresh sequential Python process**, then aggregate the resulting records. No source, seed,
seed stride, geometry, warmup count, sample count, chain count, model, truth, held-out split,
threshold, or Gate F criterion changed.

### Frozen isolated rerun

- workflow run: `35099678744`
- workflow head: `52a86146a1497a2e434c9f904f6abff52b081572`
- artifact: `v031-gate-f-35099678744`
- artifact id: `10449104051`
- artifact digest: `sha256:7e0f21dbafc31ba3e03cc0f5d7725295c3c2d9aa0b47912164885f19acb20762`
- execution strategy: `sequential_fresh_python_process_per_replicate`
- observed source Git blob SHA1: `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`
- source SHA256: `088263312c61c875cb5cda7d826ecdb7444ca4a55f7c4a594a1de96c7cf4e705`

Observed summary against the frozen criteria:

- replicates: `20` (criterion `== 20`)
- mean bias, `beta_precip`: `0.00043211981058116633` (criterion `abs(bias) <= 0.15`)
- mean bias, `beta_lat`: `-5.4800346493719124e-05` (criterion `abs(bias) <= 0.15`)
- 90% truth coverage, `beta_precip`: `0.90` (criterion `>= 0.75`)
- 90% truth coverage, `beta_lat`: `0.90` (criterion `>= 0.75`)
- positive held-out gain rate: `1.00` (criterion `>= 0.80`)
- mean held-out full-minus-knockout gain: `0.3562608092382287` per context
  (criterion `>= 0.01`)
- total divergences across all full/knockout fits: `0`
- mean divergences per fit: `0.0` (criterion `<= 0.10`)

All 20 held-out east-block replicates favored the full suitability model over the neutral
knockout. All eight mechanical Gate F checks in the artifact are `passed: true`.

Mechanical Gate F decision: **PASS**.

## Overall promotion status

The frozen rule is strict conjunction: **A AND B AND C AND D AND E AND F**.

- Gate A: PASS
- Gate B: PASS
- Gate C: PASS
- Gate D: PASS
- Gate E: PASS
- Gate F: PASS

Therefore **`v0.3.1 = PASS` under the frozen identification-first promotion gate**.

This closes the v0.3.1 foundation only: separation of ecological intensity from observation
process, explicit target sets, neutral-process knockout semantics, structural refusal under
confounding, all-parameter in-model calibration, and real-geometry semi-synthetic held-out
transfer. It does not by itself authorize state/activity/interaction/movement claims in later
versions; those require their own frozen gates.
