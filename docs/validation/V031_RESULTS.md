# v0.3.1 validation results

Status: **NOT_READY — Gate F is scientifically UNEVALUATED after an infrastructure OOM**

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

## Gate F — pinned real-geometry semi-synthetic transfer: INFRASTRUCTURE_BLOCKED / UNEVALUATED

Frozen full run:

- workflow run: `35089704914`
- job: `104772854056`
- workflow head: `ac61189bacfb00105c9225fc4b9ea315cddcddf0`
- pinned source repository: `the-pudding/data`
- pinned source commit: `3dcb0a80c838ff9503e3957d7e004a7f4b888b0a`
- pinned source path: `rain/annual_precipitation.csv`
- expected Git blob SHA1: `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`
- selected station rows: first 120 data rows under the pinned source ordering
- geometry: 120 real stations x 6 day-of-year bins x 4 hour bins
- training blocks: west + central
- completely held-out block: east
- replicates: 20

The workflow did not reach a scientific Gate F decision. During the benchmark step, the
JAX/LLVM backend terminated with memory-allocation failures and a `JaxRuntimeError` while
materializing compiled symbols. The process exited before
`artifacts/v031_semisynthetic_gate_f.json` was written, so no Gate F artifact exists for this
attempt.

Therefore this run is **not** a scientific Gate F failure. No parameter-recovery,
held-out-transfer, divergence, or aggregate gate metric is inferred from the interrupted run.
Gate F remains **UNEVALUATED** until the same frozen scientific profile completes under an
execution strategy that does not exhaust runner memory.

A non-promotional one-replicate memory diagnostic was added after the failure. Its first run
(`35093254567`) stopped before model execution because the temporary diagnostic script could
not import the repository `scripts` package; that run contains no model evidence. The import
path was corrected, and run `35093359984` tests one exact-profile replicate on the same runner
class. Diagnostic results do not count toward promotion.

## Exact-head CI

The last fully completed regular CI before the diagnostic-only commits was run `35091004410`
at head `d67f660d457ccfaf875d7c3a8fcadd894b095067`, and it completed successfully across the
repository test matrix. Regular CI also runs on the diagnostic-only commits; their completion
must be checked before any implementation fix is declared verified.

## Overall promotion status

`v0.3.1 = NOT_READY`. Gates A/B/C/D/E pass; Gate F has no scientific decision because the
frozen full run was interrupted by infrastructure OOM. The promotion rule remains strict
conjunction: **A AND B AND C AND D AND E AND F**.
