# v0.7f Out-of-Family Temporal-Resolution Robustness Results

Status: **PASS**

v0.7f asked whether the bidirectional resolution discrimination from v0.7d/v0.7e survives when neither fitted candidate is the exact data-generating model.

## Frozen provenance

- gate freeze commit: `09a6ac71bcc1ddfc6781253e8b48aa377115e5d1`
- gate blob: `092e3c706abe55912776f99fa5418e9ed205cc22`
- authorized outcome run: `36104026876`
- outcome head: `9303c3b8585e77d6da19bbe5535bc7aaa3651746`
- qualification artifact ID: `10850032780`
- qualification artifact SHA256: `792c0285a7eeba690cb234f4dd39f5222caf95a7cd93c5fabc9c73273ae35d3a`
- final result artifact ID: `10850478316`
- final artifact SHA256: `c1aaf342efe834f07ce05427f9d8aa4bfaa62bf524ccaf3d9c7f2f7171f67610`

Independent ZIP SHA256 values matched the GitHub artifact digests.

## Frozen candidates

The fitted pair remained exactly the equal-dimension v0.7d/e candidates:

- recursive dynamic occupancy: **4 ecological parameters**;
- memoryless quadratic occupancy: **4 ecological parameters**.

Both candidates passed the inherited exact-JAX structural and practical qualification.

## Out-of-family world A: dynamic_like

The generator was recursive, but its colonization and extinction probabilities varied with time. The fitted dynamic candidate still assumed constant transition probabilities, so the correct-resolution candidate was deliberately misspecified.

Across **16 paired replicates / 32 fits**:

- Dynamic > Static: **16/16 = 1.00**
- frozen requirement: **>=12/16 = 0.75**
- mean Dynamic-minus-Static held-out gain: **+1.84527 nats/context**
- frozen requirement: **>= +0.25**
- minimum replicate gain: **+0.01650**
- divergences: **0**

Even the weakest replicate remained in the frozen correct direction.

## Out-of-family world B: static_like

The generator was memoryless but included a cubic time term. The fitted static candidate remained quadratic, so it too was deliberately misspecified.

Across **16 paired replicates / 32 fits**:

- Static > Dynamic: **16/16 = 1.00**
- frozen requirement: **>=12/16 = 0.75**
- mean Static-minus-Dynamic held-out gain: **+16.21817 nats/context**
- frozen requirement: **>= +0.25**
- minimum replicate gain: **+8.64081**
- divergences: **0**

## Global decision

Across both worlds:

- datasets: **32**
- total fits: **64**
- total divergences: **0**
- frozen checks passed: **13/13**

Therefore **v0.7f = PASS**.

## Interpretation

The v0.7d/e result is not restricted to perfectly specified endpoint worlds.

> When both fitted candidates are wrong in their detailed functional form, the candidate preserving the generator's temporal-dependence class still wins beyond the direct occupancy-calibration window.

This supports **out-of-family temporal-resolution robustness** in the frozen semi-synthetic programme.

The full v0.7 chain is now:

1. occurrence time series alone can leave dynamic decomposition underidentified;
2. limited process-specific occupancy calibration resolves the missing scale;
3. the declared marginal dynamic parameters recover and transfer beyond the calibration window;
4. recursive dynamics beat memoryless alternatives when the world is recursive;
5. memoryless occupancy beats recursive dynamics when the world is memoryless;
6. the same bidirectional resolution discrimination persists under two fresh mild misspecifications where neither candidate is the exact generator.

## Boundary

This does not establish:

- universal robustness to arbitrary misspecification;
- universal model-selection consistency;
- universal superiority of either candidate class;
- realized binary occupancy histories;
- directly observed colonization/extinction events;
- movement or dispersal kernels;
- resistance or path connectivity;
- source-sink or rescue dynamics;
- causal movement limitation;
- empirical biological validity.
