# v0.3 promotion gate retirement

Status: **retired as promotion evidence**.

The frozen v0.3 known-truth run remains useful as an implementation diagnostic, and its JSON artifacts and commit history are retained. It is not accepted as evidence that the v0.3 process/claim architecture is ready for promotion.

## Why the gate was retired

The v0.3 gate did not exercise several claim-critical contracts that were later found to be incorrect:

1. posterior contraction could be converted directly into a `Supported` claim;
2. a species missing from a stream data mapping could be interpreted as an observed all-zero record history;
3. suitability knockout removed the baseline intercept as well as the environmental gradient.

In addition, two misspecification controls were algebraically reducible to the fitted log-linear family under the frozen geometry:

- `wrong_effort_geometry`: `log effort = constant + 0.7 x`, so the fitted slope is exactly `beta_x + 0.7`;
- `hidden_driver`: the hidden covariate was exactly proportional to `x`, so its effect was absorbed into a single fitted slope.

Those worlds verified arithmetic and inference implementation, but did not validate claim refusal under genuine non-identification or model discrepancy.

## Interpretation of the completed v0.3 run

The completed frozen run may be cited only as evidence that:

- the declared simulator and NumPyro implementation agreed in the in-model world;
- the implementation reproduced the analytically predicted apparent slopes in the two reducible misspecification worlds;
- the historical zero-baseline knockout did not produce excessive slope false positives under that old benchmark.

It must not be used to claim:

- ecological identifiability;
- robustness to unknown effort;
- robustness to hidden environmental drivers;
- correctness of the claim layer;
- readiness for v0.4.

## v0.3.1 replacement

Promotion is reopened only after a new v0.3.1 gate is frozen and evaluated. At minimum it must include:

- identification status separated from claim support;
- explicit stream target taxa, with missing target data rejected rather than converted to zeros;
- a neutral suitability knockout that preserves baseline intensity while setting environmental slopes to zero;
- an identification negative control in which ecological and observation-process gradients are confounded and therefore return `NotIdentified`;
- a second, independently informative stream that restores identification under the same generative truth;
- at least one multi-species case in which a stream does not target every modeled species;
- SBC diagnostics over all free parameters, using an ECDF-based simultaneous calibration check rather than a single permissive TV threshold on one parameter.

The old v0.3 thresholds are not to be tuned or reused as the v0.3.1 gate.
