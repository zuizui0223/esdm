# v0.3.2 separation-hardening validation results

Status: **PASS — frozen Gate F-prime passed**

This document records outcomes against the pre-outcome criteria in
`docs/validation/V032_PROMOTION_GATE.md`. That gate was frozen before outcome-producing
runs. The frozen v0.3.1 record remains unchanged.

`PASS` here means that the implementation satisfies the declared **v0.3.2 methodological
separation-hardening gate**. It is not empirical biological validation, not a universal
identifiability theorem, and not a scientific `Supported` claim.

## Frozen gate provenance

- gate document: `docs/validation/V032_PROMOTION_GATE.md`
- gate-freeze commit: `a393fccc34a38e63a64fdc07e08578754bde60b3`
- final scientific workflow run: `35245233309`
- workflow head: `e416bc54bf4bdd25117f17d63b4710dadeb9efde`
- artifact: `v032-gate-f-prime-35245233309`
- artifact id: `10507597165`
- artifact ZIP digest: `sha256:e9eae6d44b400ba4dc24926a9033c9287320f81ed92ba80ca90fcf67ad13c5d8`
- execution strategy: `sequential_fresh_python_process_per_replicate`

The downloaded artifact ZIP was independently hashed after retrieval and matched the
GitHub artifact digest exactly. The JSON summary was also independently recomputed from
the 20 replicate records; all reported bias, coverage, held-out gain, divergence, and fit
count values matched exactly.

## Source and extrapolation integrity: PASS

The run used the frozen source:

- repository: `the-pudding/data`
- source commit: `3dcb0a80c838ff9503e3957d7e004a7f4b888b0a`
- path: `rain/annual_precipitation.csv`
- expected Git blob SHA1: `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`
- observed Git blob SHA1: `40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949`
- source SHA256: `088263312c61c875cb5cda7d826ecdb7444ca4a55f7c4a594a1de96c7cf4e705`
- first 120 station rows, unchanged from v0.3.1
- train spaces: 67
- held-out east spaces: 53

Train-only standardization produced:

- maximum training eastness z: `0.7690432636975336`
- minimum held-out eastness z: `0.7831898085656614`

Therefore the frozen condition

`min(heldout eastness_z_train) > max(training eastness_z_train)`

held exactly. The east-block test is genuine covariate-range extrapolation for the
eastness term rather than interpolation.

## Identification controls: PASS

The positive calibration profile used 12 deterministic precipitation-quantile training
stations. At all three frozen parameter anchors:

- `sp.suitability.beta_precip` was structurally identified;
- `stream.opportunistic.gamma_precip` was structurally identified;
- both targets passed the frozen practical-identification thresholds.

The deliberately weak negative profile used only the single training station with
minimum absolute precipitation z. At every frozen anchor:

- both precipitation targets remained structurally identified;
- the practical-identification diagnostic refused the design as weak.

Thus Gate F-prime distinguishes **structural possibility** from **practical separation**
rather than treating every full-rank Jacobian as equally informative.

Mechanical checks:

- positive structural identification: **PASS**
- positive practical identification: **PASS**
- negative structural identification: **PASS**
- negative practical refusal: **PASS**

## Frozen inference profile

The successful run used exactly the frozen profile:

- replicated datasets: 20
- base seed: `20260922`
- seed stride: `41`
- chains per fit: 2, sequential
- warmup draws per chain: 250
- retained draws per chain: 300
- target acceptance probability: 0.90
- parameter interval: 90%
- full + neutral-knockout fits per replicate: 2
- total fits: 40

No frozen scientific control or threshold was changed after any interrupted attempt.

## Parameter recovery: PASS

Frozen truths:

- `beta_precip = 0.45`
- `gamma_precip = 0.40`
- `beta_eastness = 0.35`

Observed across 20 replicates:

- mean bias, `beta_precip`: `-0.023444356643543517`
  - criterion: `abs(mean bias) <= 0.15`
- mean bias, `gamma_precip`: `+0.02152197986898815`
  - criterion: `abs(mean bias) <= 0.15`
- mean bias, `beta_eastness`: `+0.0016887087007837255`
  - criterion: `abs(mean bias) <= 0.15`
- 90% coverage, `beta_precip`: `0.75`
  - criterion: `>= 0.75`
- 90% coverage, `gamma_precip`: `0.80`
  - criterion: `>= 0.75`
- 90% coverage, `beta_eastness`: `0.85`
  - criterion: `>= 0.75`

All six frozen recovery checks passed.

The precipitation ecological slope is deliberately the hardest recovery target because it
shares its covariate direction with the unknown opportunistic-effort slope. Its coverage
landed exactly on the frozen lower boundary, `0.75`, and therefore passes without any
post-outcome threshold adjustment.

## Held-out extrapolation transfer: PASS

For every replicate, the full model and the neutral-suitability knockout were fitted only
on west + central data and evaluated on the same held-out east opportunistic counts.

Observed:

- positive full-minus-knockout gain rate: `1.00`
  - 20/20 replicates positive
  - criterion: `>= 0.80`
- mean held-out gain: `0.06570524048536157` log predictive density per context
  - criterion: `>= 0.01`

This is materially harder than the retired v0.3.1 Gate F interpretation because the fit
must estimate an unknown effort gradient from a partially calibrated design and then
transfer over a covariate-range extrapolation boundary.

## Computation: PASS

Across all 40 full/knockout fits:

- total divergences: `0`
- mean divergences per fit: `0.0`
- frozen criterion: `<= 0.10`

## Infrastructure history

Two earlier attempts are preserved as infrastructure/debugging history and are not
scientific Gate F-prime failures.

### Attempt 1 — workflow precheck configuration

- run: `35244084505`
- head: `397c6f848befb8a6d526fc8042077b5dab08a653`
- benchmark outcomes were never executed
- contract verification failed because the one-shot workflow installed
  `.[inference]` without the pytest dependency
- no scientific artifact was produced

The workflow was changed to install `.[dev,inference]`; no scientific gate condition
changed.

### Attempt 2 — partial zero-exposure NumPyro initialization

- run: `35244253016`
- head: `36dbef5abdd535e7d4ced926a3daa41eb714836a`
- frozen contract precheck: 40 passed
- benchmark stopped at replicate 0 before a scientific summary
- artifact: `v032-gate-f-prime-35244253016`
- artifact id: `10507095336`
- artifact digest:
  `sha256:e610e98495ababd7f61d0fdb023ae9680d7a7176247efc764853538dca8807b1`
- status recorded as `INFRASTRUCTURE_BLOCKED`

A four-context regression test reproduced the same NumPyro
`Cannot find valid initial parameters` error. The cause was not gate geometry or model
non-identifiability: known-effort cells with exactly zero exposure were still entering the
HMC likelihood as boundary Poisson observations.

The backend was corrected so known-zero-exposure cells are excluded from the likelihood
while positive counts at known-zero exposure fail closed. The regression moved RED to
GREEN, and exact-head CI then passed on Python 3.10, 3.11, and 3.12.

No source, station selection, model truth, calibration selection rule, identification
threshold, inference profile, seed, held-out split, or PASS criterion changed.

## Exact-head software verification

At scientific-run head `e416bc54bf4bdd25117f17d63b4710dadeb9efde`:

- CI run: `35245233343`
- Python 3.10: success
- Python 3.11: success
- Python 3.12: success
- Python 3.12 full suite: **214 passed**
- Gate F-prime one-shot run `35245233309`: workflow success
- every one of the 15 mechanical Gate F-prime checks: `passed: true`

## Overall v0.3.2 hardening status

The frozen mechanical rule is strict conjunction across:

1. positive structural identification;
2. positive practical identification;
3. negative-control structural identification;
4. negative-control practical refusal;
5. extrapolation integrity;
6. three parameter-bias checks;
7. three parameter-coverage checks;
8. held-out positive-gain rate;
9. held-out mean gain;
10. divergence control.

Every term passed.

Therefore **`v0.3.2 Gate F-prime = PASS` under the frozen separation-hardening gate**.

This result strengthens the v0.3.1 foundation before v0.4. It supports the narrower
methodological statement that this frozen semi-synthetic design can separate ecological
and observation-process gradients under partial calibration and genuine extrapolation.
It does not establish empirical biological validity, causal interaction identification,
universal identifiability, or any scientific `Supported` claim.
