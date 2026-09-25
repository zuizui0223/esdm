# v0.7e Reciprocal Static-World Specificity Results

Status: **PASS**

v0.7e asked whether the strong v0.7d advantage of recursive occupancy dynamics reflected
genuine model-resolution specificity or an intrinsic tendency of the benchmark to prefer
the dynamic candidate.

The reciprocal test changed only the data-generating occupancy process. The generator was
the frozen four-parameter memoryless quadratic occupancy model; the fitted candidates,
parameter count, observation programme, training/held-out split, MCMC profile, and
decision thresholds remained matched to v0.7d.

## Frozen provenance

- gate freeze commit:
  `a047fdb0fd7843b83169d5b168d86de005143c3b`
- gate blob:
  `e089e43ff009d11e87a16cd7f1c18276b0017f41`
- unique authorized outcome run:
  `36088717290`
- outcome head:
  `0ca249e3acaadc69eace3166970f4bf6619924ab`
- qualification artifact ID:
  `10844318765`
- qualification artifact SHA256:
  `6f224e599e5a78e5e796651565fcfb1019fe0b7f0a7adea2fefd81962b888f11`
- final result artifact ID:
  `10844319589`
- final artifact SHA256:
  `e4b0c42dfff5442f1ac388b55cba296db0c2d66dfde1ff93b3c99a26e0db3dcc`

The independently computed ZIP hashes matched the GitHub artifact digests for both
artifacts. The one-shot authorization marker was removed only after the authorized
workflow completed successfully.

## Reciprocal generator

The v0.7e generating world was memoryless:

```text
psi_c = logistic(
    occupancy_intercept
    + beta_time * time_c
    + beta_time2 * time_c^2
)
```

Frozen truth:

- suitability intercept alpha = **0.30**;
- occupancy intercept = **-0.50**;
- linear time slope = **+1.50**;
- quadratic time slope = **+0.25**.

No previous-occupancy term was present in the generator.

## Matched candidates and observations

Both fitted candidates had exactly four ecological parameters.

Dynamic candidate:

- suitability intercept;
- initial occupancy;
- colonization;
- extinction;
- recursive previous-state dependence.

Static candidate:

- suitability intercept;
- occupancy intercept;
- linear time slope;
- quadratic time slope;
- no previous-state dependence.

Both models received the same realization in every replicate:

- joint occurrence generated at contexts **1-12**;
- joint occurrence used for fitting at contexts **1-8**;
- direct OccupancyCount used at contexts **1-4** only;
- held-out joint scoring at contexts **9-12**;
- direct occupancy exposure in held-out contexts = **zero**.

## Qualification

**PASS for both fitted candidates.**

The frozen v0.7d exact-JAX/practical identification qualification remained satisfied:

- dynamic structural identification = PASS;
- dynamic practical identification = PASS;
- static structural identification = PASS;
- static practical identification = PASS.

Therefore the reciprocal result is not explained by either candidate being
non-identifiable.

## Frozen reciprocal result

**v0.7e = PASS. All 9 frozen checks passed.**

Across **16 fresh paired replicates / 32 fits**:

- Static > Dynamic: **16/16 = 1.00**;
- frozen requirement: **>= 14/16 = 0.875**;
- mean Static-minus-Dynamic held-out gain:
  **+13.89265 nats/context**;
- frozen requirement: **>= +0.50 nats/context**;
- minimum replicate gain:
  **+8.14855 nats/context**;
- median gain:
  **+13.46193 nats/context**;
- maximum gain:
  **+19.06234 nats/context**;
- total divergences:
  **0**.

Every replicate favored the correctly resolved memoryless model.

## Combined v0.7d + v0.7e interpretation

The reciprocal pair now rules out a simple benchmark-direction artifact.

- **v0.7d:** under recursive colonization/extinction truth, Dynamic > equal-dimension
  Static in **16/16** replicates, with mean gain **+14.14426 nats/context**.
- **v0.7e:** under memoryless quadratic truth, Static > equal-dimension Dynamic in
  **16/16** replicates, with mean gain **+13.89265 nats/context**.

Thus the benchmark does not merely reward the recursive model. It favors the
representation whose temporal resolution matches the frozen generating process.

The supported statement is:

> With equal parameter count and an identical observation programme, the value of dynamic
> occupancy resolution is conditional on the underlying process: recursive truth favors
> recursive representation, while memoryless truth favors memoryless representation.

This is a **bidirectional model-resolution specificity** result in the frozen
semi-synthetic programme.

## Claim boundary

v0.7e does not establish:

- universal model-selection consistency outside the frozen world family;
- universal superiority of either occupancy representation;
- realized binary occupancy histories;
- directly observed colonization/extinction events;
- movement or dispersal kernels;
- resistance or path connectivity;
- source-sink or rescue dynamics;
- causal movement limitation;
- empirical biological validity.

The next scientifically useful extension should therefore move away from another
polynomial comparator and test robustness to **mild process misspecification**: for
example time-varying colonization/extinction or an omitted dynamic driver, while retaining
the same prospective gate discipline.
