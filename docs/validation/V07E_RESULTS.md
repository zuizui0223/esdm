# v0.7e Reciprocal Static-World Specificity Result

Status: **PASS**

Frozen outcome run: `36088717290` (attempt 1)

## Result

Under the frozen memoryless quadratic occupancy generator, the equally
parameterized static model beat the recursive dynamic model in **16/16** paired
replicates.

- Static > Dynamic rate: **1.000**
- mean Static-minus-Dynamic held-out gain: **+13.89265 nats/context**
- minimum replicate gain: **+8.14855 nats/context**
- divergences: **0 / 32 fits**

All 9 frozen qualification, predictive, and sampling checks passed.

## Reciprocal interpretation with v0.7d

v0.7d used the same observation programme and the same 4-vs-4 candidate models,
but generated data from the recursive dynamic world:

- Dynamic > Static: **16/16**
- mean Dynamic-minus-Static gain: **+14.14426 nats/context**.

v0.7e reverses only the generator and reverses the predictive winner:

- Static > Dynamic: **16/16**
- mean Static-minus-Dynamic gain: **+13.89265 nats/context**.

Together these results support **reciprocal model-resolution specificity** in
the frozen semi-synthetic worlds. The dynamic result is not explained by a
generic preference of the scoring pipeline for the recursive candidate.

## Boundary

This remains a model-representation benchmark, not an ODSP information
filtration. Dynamic and static candidates encode the same occupancy information
with alternative temporal representations.

The result does not establish movement/dispersal kernels, realized occupancy
histories, connectivity, source-sink dynamics, or empirical biological validity.
