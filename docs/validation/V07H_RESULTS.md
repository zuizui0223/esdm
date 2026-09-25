# v0.7h Expected-Record-Matched Calibration Placement Results

Status: **PASS**

v0.7h tested whether the v0.7g placement advantage survives after matching the expected
number of direct occupancy records, rather than only matching the number of calibration
contexts.

## Frozen deterministic control

Baseline:

- placement **(1,2,3,4)**
- effort **500/context**
- total field effort **2000**
- expected direct records **931.25**

Selected:

- placement **(2,6,7,8)**
- effort **369.154537/context**
- total field effort **1476.618148**
- expected direct records **931.25**

Expected-record relative mismatch was only **1.22e-16**.

Thus the selected design used only **73.8%** of the baseline field effort while matching
expected direct record yield exactly.

Deterministic Fisher-like worst dynamic SD proxy:

- baseline **0.232454**
- selected **0.170375**
- ratio **0.73294**

This predicted a **26.7%** precision gain after expected-record matching.

## Frozen provenance

- deterministic control run: `36106319723`
- deterministic artifact ID: `10850294862`
- deterministic artifact SHA256:
  `8f3092876bc867a11cb90e7632b79bbd5ab471cea424477767fbb2657788d40c`
- gate freeze commit:
  `66f3c4d3637744c13377e503957b5fa518c52f61`
- gate blob:
  `508f49699339c95729bc88f3061db8a0e2ed7efc`
- authorized MCMC run: `36106813627`
- outcome head:
  `afee7e94f84940305f7401c844f196faebd4e760`
- final result artifact ID: `10851168463`
- final artifact SHA256:
  `f3c21a0edb16f5126b1684fa00d608da372e7d84918cf200c1891b6e89740a1e`

Independent ZIP SHA256 matched the GitHub artifact digest.

## Confirmatory precision result

Across **16 fresh paired replicates / 32 fits**:

- selected worst dynamic posterior SD < baseline: **16/16 = 1.00**
- frozen requirement: **>=12/16 = 0.75**
- mean selected/baseline worst-SD ratio: **0.77672**
- frozen requirement: **<=0.90**
- minimum ratio: **0.60866**
- maximum ratio: **0.98306**
- total divergences: **0**

Thus every replicate retained a precision advantage even after expected direct record
count was matched. The observed mean reduction was about **22.3%**.

## Selected-design recovery

Mean posterior bias:

- alpha: **-0.01081**
- initial occupancy logit: **+0.04858**
- colonization logit: **+0.01120**
- extinction logit: **-0.04391**

Empirical 90% coverage:

- alpha: **0.8125**
- initial occupancy: **0.9375**
- colonization: **0.9375**
- extinction: **0.8750**

All frozen recovery guardrails passed.

## Descriptive held-out prediction

Prediction remained descriptive only:

- selected > baseline: **6/16 = 0.375**
- mean selected-minus-baseline gain: **-0.01454 nats/context**
- minimum gain: **-0.19504**

So the two observation designs again had essentially similar held-out predictive skill
despite a substantial difference in dynamic-parameter precision.

## Interpretation

v0.7h removes the remaining simple record-yield explanation for v0.7g:

> The selected late-weighted calibration schedule is more informative about the dynamic
> decomposition even when it is forced to have the same expected direct record count as
> the early-only baseline.

Under the frozen truth it achieved that precision advantage while using about **26% less
field effort**.

Together v0.7g and v0.7h sharpen the eSDM observation-design claim:

> The timing of process-specific measurements changes what can be learned about ecological
> dynamics, even when prediction, sample count, and expected record yield provide little
> indication of that difference.

## Boundary

This does not establish:

- universal optimality of (2,6,7,8);
- optimality when occupancy is unknown before fieldwork;
- universal survey-cost efficiency;
- universal predictive superiority;
- realized colonization/extinction events;
- movement kernels or connectivity;
- empirical biological validity.
