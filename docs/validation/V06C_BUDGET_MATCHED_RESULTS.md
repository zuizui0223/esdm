# v0.6c Budget-Matched Accessibility Evidence Results

Status: **PASS**

This benchmark asked whether the practical advantage of direct accessibility calibration
in v0.6a came from observing the process itself or merely from adding more records.

## Frozen provenance

- gate freeze commit:
  `cd1088f1d60f771b4ab6d00d089c7a9f0b08150f`
- gate blob expected/observed:
  `f5fb2ae16ec8c0b37eeb1a9d87f688763ce18d83`
- valid replacement outcome run: `36015761438`
- valid outcome head:
  `ac9d2fd6000112371e16fb63539805cf6d93f529`
- final artifact ID: `10815097574`
- final artifact name: `v06c-result-36015761438`
- artifact digest / independently verified ZIP SHA256:
  `40e6ebb9e1626598f13650d42b8bcb1fabe9f0a6f9b3443972d5eccb897c95ae`

The first authorized run `36014064564` was an infrastructure-only block caused by
held-out stream metadata. It produced no accepted scientific replicate result. The repair
changed only held-out `informs` metadata; the frozen scientific gate, truth, budgets,
seeds, MCMC profile, endpoints, and thresholds were unchanged.

## Mechanical decision

**v0.6c = PASS. All 21 frozen checks passed.**

- 16 replicates;
- 32 total fits;
- total divergences = **0**.

## Exact budget match

The two auxiliary observation programmes were matched before outcome on expected total
record count under the frozen truth.

Expected counts:

- Direct AccessibilityCount = **280.36553**;
- MatchedJoint extra AccessiblePresenceOnly = **280.36553**;
- relative expected-budget error = **0**.

Realized mean auxiliary counts across replicates were also close:

- Direct = **281.06**;
- MatchedJoint = **274.63**.

Thus the comparison is not simply “more records versus fewer records.”

## Qualification: local information

At the same expected record budget, the direct accessibility endpoint supplied much more
local information about the accessibility parameters.

Target-SD proxy ratio Direct / MatchedJoint:

- accessibility intercept = **0.1913**;
- distance/accessibility slope = **0.3459**.

The MatchedJoint condition remained structurally identified but practically weak for the
two accessibility parameters, whereas the Direct condition passed the frozen practical
threshold for all four ecological parameters.

## Replicated posterior precision

### Accessibility intercept

Direct posterior SD was lower in:

- **16/16 = 1.00** replicates.

Mean posterior-SD ratio Direct / MatchedJoint:

- **0.1800**.

Thus the direct endpoint reduced posterior SD by about **82% on average** relative to the
budget-matched extra occurrence endpoint.

### Distance/accessibility slope

Direct posterior SD was lower in:

- **14/16 = 0.875** replicates.

Mean posterior-SD ratio Direct / MatchedJoint:

- **0.6220**.

Thus the direct endpoint reduced posterior SD by about **38% on average** for the
accessibility gradient, while not dominating every replicate.

Both targets passed their prospectively frozen precision gates.

## Parameter recovery

Direct-condition mean biases:

- suitability intercept = **−0.05485**;
- habitat slope = **+0.03251**;
- accessibility intercept = **+0.02157**;
- accessibility slope = **+0.03264**.

Direct 90% coverage:

- suitability intercept = **0.9375**;
- habitat slope = **0.9375**;
- accessibility intercept = **0.8750**;
- accessibility slope = **1.0000**.

For comparison, MatchedJoint mean biases were much larger for the shared/accessibility
intercepts:

- suitability intercept = **+0.46447**;
- accessibility intercept = **−0.78462**;
- accessibility slope = **+0.20732**.

These MatchedJoint quantities were descriptive rather than frozen gate targets.

## Held-out prediction

Held-out scoring used the same base joint-occurrence endpoint.

Direct minus MatchedJoint:

- mean held-out log-score gain = **+0.01752**;
- Direct better rate = **11/16 = 0.6875**.

This was predeclared as descriptive only.

The important result is therefore **not** a claim that direct accessibility evidence
universally yields better held-out occurrence prediction. Its clear advantage is the
precision and recovery of the process-specific accessibility parameters.

## Interpretation

The v0.6 static-accessibility programme now separates two ideas that ordinary record-count
comparisons conflate:

> Observation quantity and observation target are different dimensions of information.

At the same expected number of auxiliary records, direct measurements of accessibility
resolved accessibility parameters far more sharply than extra observations of the same
joint suitability × accessibility product.

This complements v0.6b:

- joint occurrence can create mathematical rank through model/covariate shape;
- more joint occurrence can add precision;
- but process-specific accessibility observations target the weak decomposition directly
  and were substantially more information-efficient for accessibility parameters.

## Claim boundary

This result supports process-specific **information efficiency** in the frozen
semi-synthetic accessibility model.

It does not establish:

- universal superiority of direct data for every parameter or every replicate;
- universal held-out predictive superiority;
- causal movement limitation;
- movement kernels, connectivity, colonization/extinction, or source-sink dynamics.

Those remain outside v0.6.
