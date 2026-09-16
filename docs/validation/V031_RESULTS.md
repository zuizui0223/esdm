# v0.3.1 validation results

Status: **NOT_READY — Gate F frozen rerun is in progress after an infrastructure-only fix**

This document records outcomes against the pre-outcome criteria in
`docs/validation/V031_PROMOTION_GATE.md`. Thresholds are not changed in response to these
outcomes. The earlier v0.3 promotion interpretation is retired; its runs remain historical
implementation diagnostics only.

## Gate A — claim / identification separation: PASS

The deterministic contract requires posterior contraction to return identification status,
not scientific support. Current exact-head CI verifies that contraction can yield
`Identified` / `NotIdentified`, while `Supported` remains a separate claim type.

## Gate B — stream target sets: PASS

Current exact-head CI verifies that:

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

Current exact-head CI verifies the predeclared design result:

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

## Gate F — pinned real-geometry semi-synthetic transfer: RERUN_IN_PROGRESS / UNEVALUATED

Frozen scientific profile:

- pinned source repository: `the-pudding/data`
- pinned source commit: `3dcb0a80c838ff9503e3957d7e004a7f4b888b0a`
- pinned source path: `rain/annual_precipitation.csv`
- expected Git blob SHA1: `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`
- selected station rows: first 120 data rows under the pinned source ordering
- geometry: 120 real stations x 6 day-of-year bins x 4 hour bins
- training blocks: west + central
- completely held-out block: east
- replicates: 20
- base seed: `20260921`, replicate stride: `37`
- warmup: `200`, posterior samples: `250`, chains: `2`

### Interrupted first full attempt

The first full run (`35089704914`, job `104772854056`, head
`ac61189bacfb00105c9225fc4b9ea315cddcddf0`) did not reach a scientific Gate F decision.
During the benchmark step, the JAX/LLVM backend terminated with memory-allocation failures and
a `JaxRuntimeError` while materializing compiled symbols. The process exited before
`artifacts/v031_semisynthetic_gate_f.json` was written, so no Gate F artifact exists for that
attempt.

Therefore that run is **not** a scientific Gate F failure. No parameter-recovery,
held-out-transfer, divergence, or aggregate gate metric is inferred from the interrupted run.

### Memory diagnosis

A non-promotional one-replicate exact-profile diagnostic was run after the failure. The first
diagnostic attempt (`35093254567`) stopped before model execution because of a diagnostic-only
import-path error and contains no model evidence. After correcting that path, run
`35093359984` completed successfully on the same GitHub-hosted runner class:

- artifact: `v031-gate-f-memory-diagnostic-35093359984`
- artifact id: `10445003190`
- profile: one replicate, base seed `20260921`, warmup `200`, samples `250`, chains `2`
- pinned source blob observed: `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949` (matches frozen expected blob)
- train spaces: `67`; held-out east spaces: `53`
- beta_precip posterior mean: `0.5509501427412034`
- beta_lat posterior mean: `-0.25639462321996687`
- full held-out log score: `-1.1757906118758865`
- knockout held-out log score: `-1.5123634232500267`
- diagnostic held-out gain: `0.3365728113741402`
- full divergences: `0`; knockout divergences: `0`
- maximum resident set size reported by `/usr/bin/time -v`: `3852368` kB

These numbers are **diagnostic only** and do not count toward Gate F or promotion. The
important infrastructure conclusion is narrower: one exact-profile replicate can complete,
while its peak memory is already about 3.7 GiB. This supports cumulative JAX/XLA process
memory as the cause of the 20-replicate in-process failure.

### Infrastructure-only execution fix

The frozen runner now executes each of the 20 predeclared replicates in a fresh sequential
Python process and aggregates their records afterward. The scientific profile is unchanged:
no threshold, seed, seed stride, geometry, warmup count, sample count, chain count, source, or
gate criterion was modified. Regular CI at implementation head
`d50dccf3e5aec675c7a12e368add148695abdb10` passes on Python 3.10, 3.11, and 3.12; the
Python 3.10 job reports `165 passed, 8 skipped`.

The frozen full rerun is:

- workflow run: `35099678744`
- workflow head: `52a86146a1497a2e434c9f904f6abff52b081572`
- execution: sequential fresh Python process per replicate
- scientific status: **UNEVALUATED until the final Gate F artifact exists**

No scientific result is inferred from partial worker completion or elapsed runtime.

## Overall promotion status

`v0.3.1 = NOT_READY`. Gates A/B/C/D/E pass; Gate F remains scientifically unevaluated until
the frozen rerun completes and its mechanical decision is recorded. The promotion rule remains
strict conjunction: **A AND B AND C AND D AND E AND F**.
