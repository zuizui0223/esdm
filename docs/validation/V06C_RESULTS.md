# v0.6c Covariate-Alignment Stress Results

Status: **PASS**

## Provenance

- outcome run: `36000626129`
- outcome head: `b9ae94cb67da4bd05570ec6b203bd5ff334b4981`
- gate freeze commit: `def179b40608c85ca2809e98517ea72deb3c4757`
- gate blob expected/observed:
  `108828a22c857b76baa7e3ca1a4ebc86a19ceb3a`
- artifact ID: `10807694192`
- artifact SHA256:
  `fee5cd4490b8398a769bf6b001057ff19e42d1c128ae145caed517f30f9280ab`

Both frozen primary checks passed.

## Result

Joint-only practical targets:

| habitat-distance rho | practical targets | condition number |
| --- | ---: | ---: |
| 0.00 | 1/4 | 19.14 |
| 0.50 | 1/4 | 16.17 |
| 0.90 | 1/4 | 21.87 |
| 0.99 | 0/4 | 43.29 |

Direct-calibrated practical targets were **4/4 at every rho**, with condition numbers
between **4.50 and 5.10**.

At rho = 0.99, joint-only target-SD proxies were:

- suitability intercept = **1.07957**;
- habitat slope = **0.54742**;
- accessibility intercept = **2.69012**;
- accessibility slope = **0.53082**.

With direct AccessibilityCount at the same rho:

- suitability intercept = **0.10903**;
- habitat slope = **0.11476**;
- accessibility intercept = **0.18895**;
- accessibility slope = **0.18508**.

## Interpretation

All joint-only designs retained local structural rank, so covariate alignment did not
erase formal identifiability under the declared nonlinear model.

It did erase practical usefulness by rho = 0.99.

The independent accessibility endpoint protected all four practical targets across the
entire frozen alignment series.

The supported statement is therefore:

> Occurrence-only suitability/accessibility separation can remain mathematically
> identifiable while becoming practically unstable as habitat and accessibility gradients
> align. Process-specific accessibility observations can stabilize that decomposition.

## Boundary

This is a deterministic identification stress. It does not show that any empirical
fragmented landscape or island system has the frozen correlation structure, and it does
not establish movement kernels, connectivity, colonization dynamics, or causal isolation
effects.
