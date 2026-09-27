# FIELD1 post-mortem

Status: **POST-OUTCOME DIAGNOSTIC — DOES NOT REOPEN FIELD1**

Date: 2026-09-27

FIELD1 Phase-A is frozen as FAIL in
`docs/field/FIELD1_PHASE_A_FROZEN_RESULTS.json`. This note explains what can be learned
from that failure without changing the frozen decision.

No threshold, world, split, graph, prior, MCMC setting, or claim rule is changed here.
No new confirmatory FIELD1 generation is authorized.

## 1. What survived

The narrow `FIELD_PRESENT` flag passed its own predeclared positive/negative control:

- K1, M1-M0, H1: positive rate = **0.75**, mean gain = **+4.7197**;
- K0, M1-M0, H1: material-gain rate = **0.0625**, mean gain = **-0.0755**.

So the result is not "spatial fields do not work." The supported statement remains:

> in this known-truth programme, a coherent distance-structured latent field can add
> held-out mapping information beyond the environment-only model.

Because the overall programme failed its sampling guardrail, this remains an internal
frozen claim flag, not a promoted general method.

## 2. Environmental-dependence failure is not just low power

The environmental axis failed in both directions.

False promotion when environmental covariance was absent:

- K0 M2-M1 H1: material rate **0.5625**, mean gain **+0.00873**;
- K1 M2-M1 H1: material rate **0.6875**, mean gain **+0.02306**;
- K5 mean0/cov0: material rate **0.5625**, mean gain **+0.00762**.

Failure to classify covariance truth reliably when it was present:

- K5 mean0/cov1: positive rate **0.5625**, mean gain **+0.02257**;
- K5 mean1/cov1: positive rate **0.5625**, mean gain **-0.00088**.

The K5 firewall therefore did what it was intended to do: it showed that the M2-M1 gain
did not track covariance truth cleanly.

## 3. Full rank was not enough: distance and environmental dissimilarity are nearly the same edge axis

The pre-fit firewall checked only exact centered rank. That condition passed, but the
frozen response-free geometry is still strongly ill-conditioned.

Pearson correlation between edge distance and environmental dissimilarity:

| Geometry | correlation |
| --- | ---: |
| full frozen graph | **-0.9520** |
| H1 training edges | **-0.9494** |
| H2 training edges | **-0.9494** |

Thus `rho` and `gamma` are formally distinct but practically close to substitutes.

The same point appears after the nonlinear conductance normalization. Using the frozen
precision construction and finite-difference derivatives of the zero-sum projected
precision matrix:

| Truth point | cosine between dQ/drho and dQ/dgamma |
| --- | ---: |
| K1 boundary (gamma=0, beta=0) | **0.9595** |
| K2 (gamma=1.2, beta=0) | **0.9419** |
| K4 (gamma=1.2, beta=1.4) | **0.8999** |

A cosine near one means the two parameters perturb the precision matrix in nearly the
same direction. This provides a deterministic explanation for why the environmental
axis could false-promote even though the raw centered edge matrix had rank two.

The lesson is structural:

> exact rank is a necessary firewall, but not a practical-separation criterion for
> covariance parameters.

A future, independently motivated method should therefore assess the conditioning or
precision-sensitivity geometry of active dependence axes before treating them as
separately interpretable.

This is a post-mortem lesson, not authorization to rerun FIELD1 with a better-conditioned
fixture.

## 4. Barrier failure is different

The barrier axis cannot be dismissed as the same distance/environment collinearity
problem.

The response-free geometry audits all passed:

- H2 training active-axis rank: PASS;
- matched distance stratum at edge length 1.0: 3 non-barrier and 3 barrier edges;
- training-side barrier edges: 3;
- separate heldout-boundary barrier edges: 3.

Moreover, the precision-sensitivity alignment between `rho` and `beta` at the K4 truth
is much lower (cosine approximately **0.415**) than the `rho`-`gamma` alignment.

Yet the frozen predictive results were poor:

- K3 M3-M1 H2: positive rate **0.4375**, mean gain **-0.01489**;
- K4 M3-M1 H2: positive rate **0.625**, mean gain **+0.17012**;
- K4 M4-M2 H2: positive rate **0.4375**, mean gain **+0.00264**.

So the barrier failure is not explained by the exact-rank or simple edge-distance
firewalls. The current evidence leaves at least three unresolved possibilities:

1. the held-out geometry does not provide enough repeatable predictive leverage for
   `beta`;
2. latent-field realization uncertainty dominates the barrier contribution;
3. the current NUTS parameterization is too unstable for reliable axis-level comparison.

FIELD1 does not adjudicate among these after outcome.

## 5. Sampling instability is a separate terminal failure

The run accumulated:

- **360 divergences**
- across **704 fits**
- mean **0.51136 divergences per fit**
- frozen maximum: **0.10**

This is not evidence against spatial dependence itself. It is evidence that the complete
Phase-A inferential implementation did not meet its predeclared numerical reliability
criterion.

The whitened field removes the exact intercept/constant-mode confounding, but a dense
hierarchical field with `log_sigma`, `log_rho`, optional covariance axes, and many
latent innovations can still have difficult posterior geometry.

The frozen aggregate does not localize divergences by model/world, so this post-mortem
does not attribute them to a specific axis without a separate descriptive audit of the
already-produced shards.

## 6. Scientific endpoint

FIELD1 is terminal as a qualification programme.

Supported, narrowly:

- a distance-structured residual spatial field can improve held-out mapping in the
  predeclared K1/K0 control pair.

Not qualified:

- environmental-similarity dependence as a separable covariance axis;
- barrier-modified dependence as a separable covariance axis;
- the combined M4 structure;
- any dispersal, movement, migration, gene-flow, causal-connectivity, or evolutionary
  IBD/IBE interpretation.

## 7. What eSDM should carry forward

The useful design lesson is not "add more covariance knobs." It is:

1. allow one coherent latent spatial field when the goal is map continuity;
2. keep that field interpretation-bounded as residual spatial dependence;
3. require more than full rank before splitting spatial dependence into mechanistic axes;
4. treat covariance-axis separation as its own identification problem;
5. do not let better prediction turn an unresolved latent field into a dispersal claim.

FIELD1 itself should not be rerun or rescued. Any future spatial-field work must begin
from a scientifically independent question and a newly frozen programme, not from
retuning this failed gate.
