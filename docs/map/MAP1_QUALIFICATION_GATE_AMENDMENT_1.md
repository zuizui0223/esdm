# MAP1 qualification gate — Amendment 1

Status: **FROZEN BEFORE ANY MAP1 CONFIRMATORY OUTCOME — EXECUTION NOT AUTHORIZED**

Date frozen: 2026-09-27

## Trigger

The initial MAP1 design gave BC and BX the same latent dimension and the same
`sigma ~ HalfNormal(0.75)` prior, but the fixed coherent transform
`H Q_c^{-1/2}` did not preserve the same total zero-sum prior variance as the
exchangeable transform `H`.

This is a response-free fairness issue in the central BC-vs-BX control. No MAP1
confirmatory outcome, shard, fit, or held-out gain has been opened.

For the frozen irregular 5 x 4 fixture before this amendment, the unnormalized coherent
transform had approximately 1.355 times the zero-sum expected squared norm of BX at the
same sigma (about 1.164 times the RMS amplitude).

## Frozen correction

Let

```text
Q_c = H^T Q0 H
c   = sqrt((m-1) / tr(Q_c^-1))
```

and define

```text
u_BC = sigma * c * H * Q_c^-1/2 * z
u_BX = sigma     * H              * z
```

with `z ~ Normal(0, I)`.

Therefore, conditional on any common sigma,

```text
E[||u_BC||^2] = E[||u_BX||^2] = sigma^2 (m-1).
```

The normalization constant is deterministic from the frozen response-blind graph,
`rho=1`, and `alpha=0.90`. It is not estimated and cannot change after outcome.

## Scientific invariants

This amendment changes none of:

- the independent MAP1 question;
- B0/BX/BC model roles;
- N0/N1/P1 worlds;
- H1 held-out geometry;
- 16 replicates per world;
- fresh latent realization per replicate;
- sigma prior;
- predictive thresholds;
- divergence guardrail;
- MCMC profile;
- claim boundary.

It only makes the flexibility control fairer by ensuring that BC and BX differ in
coherence structure rather than latent RMS scale.

