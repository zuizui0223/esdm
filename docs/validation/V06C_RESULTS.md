# v0.6c Accessibility Identification Frontier Results

Status: **COMPLETE**

v0.6c prospectively mapped nine static-accessibility identification designs. No cell was
selected after outcome.

## Provenance

- outcome run: `35995579705`
- outcome head: `6c0eb31ada689cdab2cecb82c2f51df27f588b43`
- gate freeze commit: `1441d7ca241b09cad54563f3b6c0ed53bae6aa90`
- gate blob expected/observed:
  `f09f1857756bf1b14c2f8c9888f35cf1d6a44ab7`
- artifact ID: `10805868158`
- artifact name: `v06c-frontier-35995579705`
- artifact digest / independently verified ZIP SHA256:
  `0c7983dfdcdb4553700a0af89e9563bd43121921231493296645707337e10691`

The intercept-only hard refusal remained valid.

## Finite frontier

| geometry | access intercept | joint structural | joint practical | direct structural | direct practical |
| --- | ---: | ---: | ---: | ---: | ---: |
| distinct | -2.0 | 4/4 | 1/4 | 4/4 | 4/4 |
| distinct | +0.40 | 4/4 | 1/4 | 4/4 | 4/4 |
| distinct | +2.0 | 4/4 | 1/4 | 4/4 | 2/4 |
| aligned | -2.0 | 4/4 | 0/4 | 4/4 | 3/4 |
| aligned | +0.40 | 4/4 | 0/4 | 4/4 | 4/4 |
| aligned | +2.0 | 4/4 | 0/4 | 4/4 | 2/4 |
| flat-access | -2.0 | 1/4 | 0/4 | 3/4 | 0/4 |
| flat-access | +0.40 | 1/4 | 0/4 | 3/4 | 0/4 |
| flat-access | +2.0 | 1/4 | 0/4 | 3/4 | 0/4 |

Counts are numbers of the four frozen targets meeting the relevant criterion.

## Result 1: structural rank can be assumption-driven

For all distinct and aligned joint-only cells, all four targets are structurally
identified.

The aligned case is especially revealing because distance is set exactly equal to habitat.
The only remaining source of separation is the different declared functional form of
intensity and accessibility.

Despite full structural rank, aligned joint-only practical identification is **0/4** in
all regimes.

Therefore structural identification is not evidence that the data independently resolve
the two ecological processes.

## Result 2: direct process-specific data strongly stabilizes the decomposition

At the middle regime (+0.40), direct calibration raises practical identification:

- distinct: **1/4 -> 4/4**;
- aligned: **0/4 -> 4/4**.

This is consistent with v0.6a recovery and held-out transfer.

## Result 3: direct data is not universally sufficient

At high accessibility (+2.0), the accessibility response is close to saturation.

Even with direct calibration:

- distinct practical = **2/4**;
- aligned practical = **2/4**.

Accessibility target-SD proxies remain about **0.50–0.55**, above the frozen 0.25
threshold.

Thus a process-specific endpoint cannot recover information when the process is operating
in a low-sensitivity regime.

## Result 4: no predictor variation cannot be rescued

In flat-access cells, distance is exactly zero everywhere.

The accessibility distance slope is `DesignUninformed` under both observation designs.

Direct calibration can identify the accessibility intercept and separate other structural
parameters, but it cannot create information about a slope whose predictor never varies.

Because the full free-parameter system remains rank-deficient, the frozen system-level
practical diagnostic marks every flat-access cell weak overall.

## Final v0.6 information boundary

The v0.6a–c sequence supports:

> Stable suitability/accessibility separation requires three things: design variation in
> the process-specific predictor, an operating regime with adequate likelihood
> sensitivity, and sufficient observation information. Direct process-specific
> observations can strongly stabilize the decomposition, but structural rank alone is not
> enough and direct data cannot rescue an intrinsically uninformed design.

This is a static identifiability result, not a movement or dispersal model.

## Remaining boundary

Still unsupported:

- dispersal kernels;
- connectivity/resistance inference;
- colonization/extinction dynamics;
- source-sink dynamics;
- causal movement limitation;
- empirical accessibility claims without field validation.
