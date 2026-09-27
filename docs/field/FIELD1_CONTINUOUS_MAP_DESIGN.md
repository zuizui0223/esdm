# FIELD1 — Continuous-map latent field programme (draft)

Status: **DRAFT — NOT AUTHORIZED FOR OUTCOME EXECUTION**

Date drafted: 2026-09-27

## Scientific target

FIELD1 does **not** attempt to identify dispersal, gene flow, or movement mechanism.

Its target is narrower:

> estimate one coherent continuous spatial field underlying the map, and test whether
> geographic distance, environmental similarity, and a predeclared physical barrier
> improve held-out mapping beyond an ordinary environment-only SDM and a
> distance-only spatial field.

The latent field is a predictive/dependence object. A large field value is **not**
interpreted as dispersal limitation.

The active v0.4-R5b empirical endpoint remains unchanged. FIELD1 is a separately named
methodological programme and does not reopen the consumed Snapshot Japan endpoint.

## Model

For a focal species at spatial location `s` and temporal context `t`:

```text
log lambda(s,t)
    = environmental mean(s,t)
    + u(s)
```

FIELD1 v1 keeps `u` spatial-only and broadcasts it across day-of-year/hour contexts.
Spatiotemporal random fields are outside the first programme.

The spatial field is represented on a frozen graph/mesh with node vector `u_node`.
Predictions at arbitrary habitat coordinates use a frozen interpolation operator `A`:

```text
u(s) = A(s) u_node
```

### Edge conductance

For each frozen undirected edge `i--j`:

```text
w_ij =
  exp(
      - d_ij / rho
      - gamma * E_ij
      - beta  * B_ij
  )
```

where:

- `d_ij`: dimensionless geographic edge length, obtained by dividing physical edge
  length by a response-blind reference distance frozen from geometry alone;
- `E_ij`: predeclared environmental dissimilarity between edge endpoints;
- `B_ij`: predeclared barrier exposure on the edge, in `[0,1]`;
- `rho > 0`: geographic distance scale;
- `gamma >= 0`: environmental-similarity dependence strength;
- `beta >= 0`: physical-barrier dependence strength.

The terms are dependence parameters, not ecological mean effects.

### Proper graph-GMRF precision

FIELD1 v1 is a **graph-diffusion GMRF**, not a claim of a Matérn/SPDE construction.

Let `W` be the symmetric conductance matrix, `D = diag(W 1)`, and

```text
S = D^(-1/2) W D^(-1/2)
Q = sigma_u^(-2) [ I - alpha S ]
```

with frozen `alpha = 0.95`.

For a non-negative symmetric graph, the normalized adjacency has spectral radius at most
one, so `alpha < 1` keeps the precision proper. The field is sampled directly in a
fixed `m-1` dimensional zero-sum Helmert basis, so

```text
sum_i u_i = 0
```

by construction. This removes the constant spatial mode rather than sampling it and
centering afterward, keeping the ecological intercept separate without a prior-only
latent direction.

The first implementation may use dense factorization on a deliberately small mesh.
Sparse/JAX scaling is a later engineering gate, not an assumption of FIELD1 validity.

## Why this is separate from environmental suitability

Environmental covariates may appear in two mathematically different places:

1. **mean structure** — explains where expected abundance/intensity is high;
2. **dependence structure** — explains which residual map locations borrow strength.

Using the same raw environmental variable in both places is allowed only after passing a
factorial known-truth gate. FIELD1 must not infer `gamma > 0` merely because a missing
or misspecified mean effect leaves a spatial environmental gradient in the residuals.

## Knockout family

The confirmatory comparison family is finite and frozen.

| ID | Mean | Spatial field | Environment in dependence | Barrier |
| --- | --- | --- | --- | --- |
| M0 | yes | none | no | no |
| M1 | yes | distance-only | no | no |
| M2 | yes | distance + environment | yes | no |
| M3 | yes | distance + barrier | no | yes |
| M4 | yes | distance + environment + barrier | yes | yes |

Primary nested ladder:

```text
M0 -> M1 -> M2 -> M4
```

M3 is retained as a required factorial diagnostic so a barrier signal cannot be credited
to the environmental-dependence axis.

Knockout semantics:

- field knockout: `u(s) = 0`;
- environment-dependence knockout: `gamma = 0`;
- barrier knockout: `beta = 0`;
- distance-only model: `gamma = beta = 0`.

No knockout changes the environmental mean formula, observation effort, detection model,
data split, mesh, or response rows.

## Frozen edge construction contract

FIELD1 separates interpolation geometry from dependence geometry.

### Habitat nodes

- nodes are generated before response inspection;
- node locations depend only on study geometry and predeclared raster/vector layers;
- observation locations are not allowed to create response-density-adaptive mesh nodes.

### Dependence edges

- local edges: Delaunay or fixed-k nearest-neighbour edges within habitat components;
- cross-component bridge edges: a fixed number of nearest boundary-node pairs when the
  barrier leaves habitat components disconnected;
- all graph-building rules are frozen before fitting;
- edge list is identical for all M0-M4 models.

### Geographic distance scaling

The prior on `rho` is defined on dimensionless graph distance. Before any empirical
response is inspected, the child contract must freeze one positive reference distance
from geometry alone (default: median positive graph-edge length) and use

```text
d_ij = physical_edge_length_ij / reference_edge_length
```

for every FIELD1 model. Changing this scale after fitting is forbidden.

### Environmental dissimilarity

If multiple dependence covariates are used:

```text
E_ij = || z_i - z_j ||_2
```

where `z` is standardized from the training region only.

The dependence-covariate list must be frozen before response fitting.

### Barrier exposure

The empirical child contract must define one physical barrier operator before response
inspection.

Preferred first application class: **archipelago / terrestrial island system**.

For an island system, the default proposed barrier summary is:

```text
B_ij = fraction of the straight edge segment intersecting sea/non-habitat barrier
```

Alternative mountain/river barrier definitions require a new child contract and are not
interchangeable after outcomes are opened.

## Known-truth programme

The scientific gate is based on knockouts and held-out prediction, not on whether a
positive hyperparameter credible interval excludes zero.

At minimum the following worlds are required.

### K0 — independent residual world

Truth:

- environmental mean may be non-zero;
- `u = 0`.

Required behavior:

- M1-M4 do not show material held-out gain over M0;
- posterior field amplitude remains near the lower practical boundary;
- no environment/barrier dependence claim is authorized.

### K1 — distance-only field

Truth:

- spatial field present;
- `gamma = 0`;
- `beta = 0`.

Required behavior:

- M1 beats M0;
- M2 and M3 do not materially beat M1;
- M4 does not receive a false environment/barrier promotion.

### K2 — environmental dependence only

Truth:

- spatial field present;
- `gamma > 0`;
- `beta = 0`.

Required behavior:

- M2 beats M1;
- M3 does not substitute for M2;
- M4 need not beat M2 materially.

### K3 — barrier dependence only

Truth:

- spatial field present;
- `gamma = 0`;
- `beta > 0`.

Required behavior:

- M3 beats M1;
- M2 does not substitute for M3;
- M4 need not beat M3 materially.

### K4 — environment + barrier dependence

Truth:

- `gamma > 0`;
- `beta > 0`.

Required behavior:

- M4 beats M2 on barrier holdout;
- M4 beats M3 on environmentally mismatched holdout;
- both single-axis knockouts lose information in their targeted holdout.

### K5 — mean/environment covariance confounding control

A 2 x 2 factorial is mandatory:

```text
environmental mean effect:       absent / present
environmental covariance effect: absent / present
```

The dependence axis is qualified only if M2-vs-M1 behavior tracks the covariance truth
rather than the mean-effect truth.

### K6 — distance/barrier confounding control

Use matched edge-distance strata containing both barrier-crossing and non-crossing edges.

The barrier axis is qualified only if M3-vs-M1 behavior tracks barrier truth after
geographic edge length is matched.

## Held-out geometry

Two held-out geometries are required.

### H1 — spatial block interpolation/extrapolation

A contiguous spatial block is excluded from fitting. In the response-free Phase-A
fixture this is the top-middle two-node block `(c1r2, c2r2)`; this choice preserves
full-rank distance/environment/barrier edge axes in H1 training. This tests whether a
coherent field improves the map over environment-only prediction.

### H2 — learned-barrier transfer holdout

The Phase-A fixture contains two barriers of the same frozen type. One lies entirely
inside training, and a separate barrier defines the held-out rightmost region. Thus H2
tests whether a barrier-modified dependence rule learned on one barrier transfers across
another, while preserving overlap in the main environmental covariates where possible.

Barrier evidence is based primarily on H2.

All scores are normalized per held-out observation.

Training-edge rank is audited before fitting: M1/M2/M3/M4 must have centered active-axis
ranks 1/2/2/3 on both H1 and H2 training graphs. Exact rank failure blocks the relevant
claim before stochastic outcomes are opened.

## Promotion logic

FIELD1 does not use an overall winner label.

The following claims are separately gated:

- **FIELD_PRESENT**: M1 improves on M0 in the distance-field positive world without
  false promotion in K0.
- **ENV_DEPENDENCE_SUPPORTED**: M2 improves on M1 in K2/K4 and survives K5.
- **BARRIER_DEPENDENCE_SUPPORTED**: M3/M4 improve on their barrier knockouts in K3/K4
  and survive K6.
- **FULL_MAP_STRUCTURE_SUPPORTED**: M4 adds held-out information beyond the relevant
  single-axis model in K4.

A failed axis stays failed; another successful axis cannot rescue it.

Exact numerical thresholds are frozen in the machine-readable gate before any
confirmatory outcome execution.

## Empirical interpretation boundary

Allowed empirical statements:

- the spatial field improves held-out mapping;
- environmental similarity changes residual spatial dependence;
- a predeclared barrier changes residual spatial dependence;
- the barrier-aware field improves prediction beyond a distance-only or
  environment-dependent field.

Not allowed from FIELD1 alone:

- `u` is dispersal limitation;
- `gamma` proves isolation by environment as an evolutionary mechanism;
- `beta` measures migration probability;
- barrier effects imply gene flow;
- causal movement/connectivity inference;
- genetic isolation.

In prose, prefer **geographic-distance dependence**, **environmental-similarity
dependence**, and **barrier-modified dependence** over IBD/IBE when no genetic or movement
data are present.

## Integration with esdm

FIELD1 uses a **whitened GMRF parameterization** so the existing scalar-prior backend can
remain unchanged.

For graph nodes `1,...,m`, the existing backend samples independent innovations

```text
z_i ~ Normal(0, 1)
```

together with unconstrained scalar field hyperparameters. The spatial process transforms
them internally:

```text
H = orthonormal basis of {u : sum(u)=0}
Q_c = H^T Q H
Q_c = L_c L_c^T
a = L_c^-T z,       z in R^(m-1)
u = H a
```

Thus the field is sampled directly in the `m-1` dimensional zero-sum subspace. There is
no prior-only constant innovation direction, and the ecological intercept remains
separate by construction. Because this transform lives inside the ecological process,
simulation, deterministic likelihood evaluation, and NumPyro inference all traverse the
same field mathematics. No FIELD1-specific inference backend is required.

Implemented Phase A architecture:

```text
src/esdm/field/
    graph.py          frozen nodes and dependence-edge covariates
    precision.py      W, normalized adjacency, Q, dense whitened transform

src/esdm/process/
    spatial_field.py  samples through existing scalar PriorSpec sites and adds u to
                      log_intensity
```

Phase A restrictions:

- dense `Q` only;
- mesh/node count must be deliberately capped before confirmatory execution;
- exactly `m-1` iid standard-normal innovations are used for `m` graph nodes;
- the zero-sum basis is fixed deterministically from node order;
- `rho = exp(log_rho)` and `sigma = exp(log_sigma)`;
- active environmental/barrier strengths are sampled directly as
  `gamma ~ HalfNormal(1)` and `beta ~ HalfNormal(1)`, so the simpler knockout
  models are boundary special cases rather than being separated from zero by a
  softplus-transformed Normal prior;
- designs fail closed before fitting if edge distance has no variation, or if an active
  environmental/barrier axis has no edge-level variation;
- FIELD1 axis knockouts are implemented by constructing the finite M1-M4 process family,
  while the process-level knockout removes the whole field;
- end-to-end JAX differentiation through `Q -> Cholesky -> solve -> u` is required;
- no claim of scalable sparse inference.

Phase B is authorized only after Phase A scientific gates pass. It may replace dense
linear algebra with a verified sparse operator/solver without changing the scientific
model or its knockout semantics.

## Literature boundary

FIELD1 is not presented as invention of spatial Gaussian fields, SPDE/GMRF links,
non-stationary covariance, barrier fields, or landscape-resistance GMRFs.

Relevant prior work includes:

- Lindgren, Rue & Lindström (2011), SPDE representation of Gaussian fields as GMRFs,
  JRSS B, DOI 10.1111/j.1467-9868.2011.00777.x.
- Paciorek & Schervish (2006), nonstationary covariance functions,
  Environmetrics, DOI 10.1002/env.785.
- Ingebrigtsen, Lindgren & Steinsland (2014), explanatory variables in the dependence
  structure, Spatial Statistics, DOI 10.1016/j.spasta.2013.06.002.
- Hanks & Hooten (2013), GMRF/circuit-theory landscape connectivity,
  JASA, DOI 10.1080/01621459.2012.724647.
- Bakka et al. (2019), Gaussian fields with physical barriers,
  Spatial Statistics, DOI 10.1016/j.spasta.2019.01.002.

FIELD1's contribution, if its gates pass, is the **explicit process-knockout and
claim-bounded comparison of distance, environmental-similarity, and physical-barrier
dependence inside the same eSDM generative/validation architecture**.

## Stop rule

- no empirical response is authorized by this draft;
- no FIELD2 may be created to rescue a failed FIELD1 confirmatory gate;
- after a gate is frozen, threshold/mesh/edge/barrier retuning from outcomes is forbidden;
- an empirical candidate requires its own child contract fixing species, region,
  environmental dependence covariates, barrier layer, mesh, graph, and held-out geometry
  before response fitting.
