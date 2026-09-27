# v0.3 known-truth promotion gate

Status: **frozen before the large benchmark outcomes**.

This gate applies only to the v0.3 suitability + explicit observation-effort model. It is deliberately domain-neutral and is not evidence for any particular interaction family.

## Frozen benchmark universe

The benchmark uses exactly four worlds from `make_v03_known_truth_worlds()`:

1. `correct_effort` — the fitted observation-effort geometry matches the generating graph;
2. `wrong_effort_geometry` — effort covaries with the environmental axis in generation but is flattened at fit;
3. `hidden_driver` — a correlated environmental driver exists in generation but is omitted at fit;
4. `suitability_knockout` — the generating graph contains the explicit no-effect suitability knockout while the fitted graph retains the ordinary suitability process.

The two misspecified worlds are **negative controls**, not in-model calibration worlds.

## Frozen large-run profile

- 100 independent replicates per world;
- base seed: `20260916`;
- one chain per fit;
- 250 warmup draws;
- 300 retained posterior draws;
- central 90% posterior interval;
- no adaptive change to the world definitions, priors, target parameter, interval mass, or thresholds after benchmark outcomes are inspected.

The ordinary CI suite may run a smaller smoke profile. Smoke success is not promotion.

## Primary target

All four worlds target the fitted coefficient `sp.suitability.beta_x`.

For misspecified worlds, two targets are kept distinct:

- **ecological truth** — the direct generating coefficient on `x`;
- **expected apparent value** — the precomputed pseudo-true slope induced by the declared misspecification under the benchmark geometry.

The latter is a diagnostic target for the negative control; it is not relabelled as ecological truth.

## Promotion checks

### A. Correct-effort in-model recovery

Required:

- 100 replicates completed;
- absolute mean posterior bias from ecological truth <= 0.15;
- empirical coverage of the 90% interval for ecological truth in [0.80, 0.98];
- nonzero-interval rate >= 0.80;
- mean divergences per fit <= 0.10.

### B. Suitability-knockout negative-process recovery

Required:

- 100 replicates completed;
- absolute mean posterior <= 0.15;
- empirical coverage of zero by the 90% interval >= 0.80;
- nonzero-interval rate <= 0.15;
- mean divergences per fit <= 0.10.

This is the v0.3 process-knockout false-positive gate.

### C. Wrong-effort negative control

Required:

- 100 replicates completed;
- mean posterior bias relative to ecological truth >= +0.25;
- the mean posterior is closer to the predeclared expected-apparent value than to ecological truth;
- mean divergences per fit <= 0.10.

Passing this check means the benchmark successfully demonstrates the predicted observation-process confounding. It does **not** mean the misspecified model is acceptable.

### D. Hidden-driver negative control

Required:

- 100 replicates completed;
- mean posterior bias relative to the direct ecological coefficient >= +0.25;
- the mean posterior is closer to the predeclared expected-apparent value than to ecological truth;
- mean divergences per fit <= 0.10.

Passing this check means the benchmark successfully demonstrates the predicted omitted-driver bias. It does **not** establish robustness to unmeasured environment.

## Separate SBC gate

SBC is evaluated separately because in-model calibration and misspecification robustness answer different questions.

Frozen SBC profile for the v0.3 target `sp.suitability.beta_x`:

- model/covariate geometry: the declared `correct_effort` in-model world;
- 100 prior-predictive replicates;
- base seed: `20260917`;
- one chain per fit;
- 250 warmup draws;
- 300 retained posterior draws;
- 10 rank-histogram bins;
- maximum total-variation distance from a uniform rank histogram: 0.20;
- mean divergences per fit <= 0.10;
- zero requirement that misspecified worlds pass SBC, because they are outside the fitted model by construction.

SBC success cannot rescue failure of the known-truth knockout or observation-process controls, and vice versa.

## Overall promotion rule

v0.3 is promoted to the next process layer only if all of A, B, C, D, and the separate SBC gate pass under their frozen profiles.

Failure is informative: the model remains at v0.3 and the failed diagnostic is repaired without changing successful worlds into easier benchmarks.
