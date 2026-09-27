# FIELD1 Phase-A qualification gate

Status: **FROZEN BEFORE ANY FIELD1 CONFIRMATORY OUTCOME — EXECUTION NOT AUTHORIZED**

Date frozen: 2026-09-27

This gate qualifies the continuous-map latent-field programme. It does not reopen the
v0.4-R5b empirical endpoint and it does not authorize an empirical response opening.

## Estimand

FIELD1 is qualified on **held-out predictive information**, not recovery of `rho`,
`gamma`, `beta`, individual node effects, dispersal, or connectivity.

For every comparison:

```text
gain = candidate mean held-out log predictive density
     - reference mean held-out log predictive density
```

The score is averaged only over the explicit held-out model domain.

## Replication profile

Each stochastic known-truth world is run for exactly **16 independent replicates**.

A comparison is **positive-qualified** only if both hold:

- proportion of replicate gains > 0: **>= 0.75**
- mean gain: **>= 0.005** per held-out context

A comparison is **null-qualified** only if both hold:

- proportion of replicate gains > 0.005: **<= 0.25**
- mean gain: **<= 0.005** per held-out context

The +0.005 material-gain threshold and 0.75/0.25 replicate frequencies are inherited
from earlier frozen eSDM held-out/false-promotion gates rather than tuned to FIELD1
outcomes.

Sampling guardrail:

- mean divergences per fit across the complete FIELD1 outcome run: **<= 0.10**

No PASS requires a posterior interval for a spatial hyperparameter to exclude zero.

## Primary worlds

### K0 — no residual field

Truth model: M0.

Must be null-qualified:

- M1 - M0 on H1
- M2 - M1 on H1
- M3 - M1 on H2
- M4 - M2 on H2

### K1 — distance field only

Truth model: M1.

Must be positive-qualified:

- M1 - M0 on H1

Must be null-qualified:

- M2 - M1 on H1
- M3 - M1 on H2
- M4 - M1 on H2

### K2 — environmental-similarity dependence

Truth model: M2.

Must be positive-qualified:

- M1 - M0 on H1
- M2 - M1 on H1

Must be null-qualified:

- M3 - M1 on H2
- M4 - M2 on H2

### K3 — barrier dependence

Truth model: M3.

Must be positive-qualified:

- M1 - M0 on H1
- M3 - M1 on H2

Must be null-qualified:

- M2 - M1 on H1
- M4 - M3 on H1

### K4 — environmental + barrier dependence

Truth model: M4.

Must be positive-qualified:

- M1 - M0 on H1
- M2 - M1 on H1
- M3 - M1 on H2
- M4 - M2 on H2
- M4 - M3 on H1

## K5 mean/covariance confounding firewall

The same M2-M1 H1 comparison is evaluated in the frozen 2 x 2 factorial:

- environmental mean absent, covariance absent: null-qualified
- environmental mean present, covariance absent: null-qualified
- environmental mean absent, covariance present: positive-qualified
- environmental mean present, covariance present: positive-qualified

The ENV_DEPENDENCE claim cannot pass if comparison behavior tracks mean truth instead of
covariance truth.

## K6 distance/barrier geometry firewall

K6 is a deterministic geometry qualification, not an additional stochastic outcome
world.

Before the K3/K4 barrier results can count, the frozen graph must contain at least one
edge-distance stratum with both:

- barrier-crossing edge(s)
- non-barrier edge(s)

The current response-free 4 x 3 fixture satisfies this requirement at horizontal
distance 1.0.

## Claim gates

### FIELD_PRESENT

Requires:

- K1 M1-M0 H1 positive-qualified
- K0 M1-M0 H1 null-qualified

### ENV_DEPENDENCE_SUPPORTED

Requires all:

- K2 M2-M1 H1 positive-qualified
- K1 M2-M1 H1 null-qualified
- all four K5 factorial checks pass

### BARRIER_DEPENDENCE_SUPPORTED

Requires all:

- K3 M3-M1 H2 positive-qualified
- K1 M3-M1 H2 null-qualified
- K6 deterministic distance-match audit passes

### FULL_MAP_STRUCTURE_SUPPORTED

Requires all:

- FIELD_PRESENT
- ENV_DEPENDENCE_SUPPORTED
- BARRIER_DEPENDENCE_SUPPORTED
- K4 M4-M2 H2 positive-qualified
- K4 M4-M3 H1 positive-qualified

No failed axis can be rescued by another axis.

## MCMC profile

The confirmatory profile is frozen by inheritance from the promoted R5b programme:

- warmup draws: **300**
- retained posterior draws: **350**
- chains: **2**
- target accept probability: **0.90**
- progress bar: disabled in confirmatory automation

This profile was fixed without opening any FIELD1 K0-K5 outcome. Implementation-only
smoke tests may establish compilation and numerical stability, but may not alter this
profile in response to scientific FIELD1 outcomes. A material sampling failure requires
an explicit replacement authorization preserving every scientific world, threshold,
graph, split, comparison, and claim rule.

## Stop rule

After outcome authorization:

- no world truth may change;
- no graph edge/covariate/barrier value may change;
- no held-out split may change;
- no score threshold or replicate-frequency threshold may change;
- no failed comparison may be dropped;
- no FIELD1b/FIELD2 confirmatory generation may be created solely to rescue a failed
  FIELD1 scientific gate.

A material implementation bug may be repaired only with an explicit replacement
authorization preserving every scientific item above.
