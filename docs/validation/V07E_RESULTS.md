# v0.7e Reciprocal Static-World Specificity Results

Status: **PASS**

v0.7e asked whether the v0.7 benchmark is genuinely sensitive to the data-generating
temporal structure or whether it is intrinsically biased toward the recursive dynamic
model.

The only substantive reversal from v0.7d was the generator: v0.7e generated data from
the frozen equal-dimension memoryless quadratic occupancy model, while fitting the same
dynamic and static candidate models under the same observation programme.

## Frozen provenance

- gate freeze commit:
  `3f542a4069bb77eda706e99347dda51414132ce9`
- gate blob:
  `e4bc1e342808353f65067a2379c9813a13e867a4`
- successful replacement outcome run: `36102363743`
- outcome head:
  `beb373cca11d4c12a56558565e13159a5fc37767`
- qualification artifact ID: `10849895700`
- qualification artifact SHA256:
  `f434e06e55125e96e7301fb5fba3ea4b4e15eefd95bccdb20e88f02db4d7bba1`
- final result artifact ID: `10850405096`
- final artifact SHA256:
  `e05fecc31d680b52fd84f85e21b4ee4243c7ba2cc7029e512976967c378803b5`

Independent ZIP hashes matched the GitHub artifact digests for both artifacts.

The first authorized attempt, run `36088734964`, passed qualification but was cancelled
by workflow concurrency before any replicate job started when the authorization marker
was removed. That run produced no scientific replicate outcome. The infrastructure-only
repair changed `cancel-in-progress` from true to false and changed no generator, model,
seed, MCMC, split, or decision setting.

## Frozen static generating world

The generator was the exact v0.7d equal-dimension static comparator:

```text
psi_t = logistic(
    occupancy_intercept
    + beta_time * time_t
    + beta_time2 * time_t^2
)
```

with:

- suitability intercept alpha = **0.30**;
- occupancy intercept = **-0.50**;
- linear time slope = **+1.50**;
- quadratic time slope = **+0.25**.

The generator was memoryless and had no previous-state dependence.

## Candidate models and information split

The fitted candidate pair was unchanged from v0.7d.

Dynamic:

- suitability intercept;
- initial occupancy;
- colonization;
- extinction;
- **4 ecological parameters**.

Static quadratic:

- suitability intercept;
- occupancy intercept;
- linear time slope;
- quadratic time slope;
- **4 ecological parameters**.

Both models received exactly the same observations:

- joint occurrence generated at contexts **1-12**;
- joint occurrence fit at contexts **1-8**;
- direct OccupancyCount fit at contexts **1-4** only;
- held-out joint scoring at contexts **9-12**;
- direct occupancy exposure in held-out contexts = **zero**.

## Qualification

Both candidates passed the inherited frozen structural and practical identification
requirements before replicated fitting:

- dynamic structural: **PASS**;
- dynamic practical: **PASS**;
- static structural: **PASS**;
- static practical: **PASS**.

## Replicated reciprocal result

Across **16 fresh paired replicates / 32 fits**:

- Static > Dynamic: **16/16 = 1.00**;
- frozen requirement: **>= 14/16 = 0.875**;
- mean Static-minus-Dynamic held-out gain:
  **+13.1664 nats/context**;
- frozen requirement: **>= +0.50 nats/context**;
- minimum replicate gain:
  **+9.8628 nats/context**;
- total divergences: **0**.

All **9/9 frozen checks passed**.

## Bidirectional result with v0.7d

The reciprocal pair is now symmetric:

- **dynamic generating world (v0.7d):**
  Dynamic > Static in **16/16**, mean gain **+14.1443** nats/context;
- **static generating world (v0.7e):**
  Static > Dynamic in **16/16**, mean gain **+13.1664** nats/context.

The same observation programme and equal parameter count were used in both directions.

## Interpretation

v0.7e removes an important alternative explanation for the v0.7d result:

> The matched benchmark does not simply prefer the recursive model. It discriminates in
> both directions: recursive truth favors the recursive representation, while memoryless
> quadratic truth favors the memoryless representation.

Together, v0.7d and v0.7e support **bidirectional temporal-resolution discrimination** in
the frozen semi-synthetic programme.

The v0.7 sequence now supports a sharper chain:

1. occurrence time series alone can leave dynamic decomposition underidentified;
2. limited process-specific occupancy calibration resolves the missing scale;
3. the declared dynamic parameters recover and transfer beyond the calibration window;
4. recursive dynamics outperform lower- and equal-dimensional memoryless alternatives
   when the world is recursive;
5. the equal-dimensional memoryless model wins decisively when the world is memoryless.

## Boundary

This remains a semi-synthetic model-resolution result.

It does not establish:

- universal model-selection consistency outside the frozen worlds;
- universal superiority of either dynamic or static occupancy models;
- realized binary occupancy histories;
- directly observed colonization/extinction events;
- movement or dispersal kernels;
- resistance or path connectivity;
- source-sink or rescue dynamics;
- causal movement limitation;
- empirical biological validity.
