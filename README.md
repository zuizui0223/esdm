# esdm

`esdm` develops **state-resolved community distribution modelling**: an upper layer over SDM/JSDM outputs that treats ordinary binary species occurrence as a special case and adds ecological state structure, community diversity decomposition, generic biotic-edge opportunity, and transfer-aware predictive dependence.

The repository name is historical/convenient. The project does **not** claim `ESDM` as a new acronym; that acronym is already used elsewhere in species-distribution modelling.

## Core idea

For a community context `c`, represent

```text
G_c = (N_c, Z_c, R_c)

N = nodes / taxa
Z = node states
R = biotic edges
```

A conventional SDM is recovered when a taxon has only a binary occurrence state and no explicit edge layer.

The Phase-1 package is learner-agnostic: external SDM, JSDM, Bayesian, machine-learning, or mechanistic models may supply probabilities or held-out scores. `esdm` evaluates the resulting community/state structure rather than imposing one universal fitting algorithm.

## What Phase 1 can do

### State-resolved community diversity

```python
from esdm.core import CommunityStateDistribution
from esdm.diversity import alpha_diversity_q1

community = CommunityStateDistribution(
    taxon_weights={"a": 0.5, "b": 0.5},
    state_probabilities={
        "a": {"early": 0.5, "late": 0.5},
        "b": {"early": 0.5, "late": 0.5},
    },
)

result = alpha_diversity_q1(community)
# taxonomic = 2
# state_given_taxon = 2
# joint = 4
```

For q=1, the established Shannon/Hill identity is used directly:

```text
D_joint = D_taxon * D_state_given_taxon
```

Beta diversity is likewise split into taxonomic turnover and state turnover conditional on taxon identity.

### Same place, different ecological state

```python
from esdm.interaction import geographic_overlap, state_overlap

geo = geographic_overlap([0.5, 0.5], [0.5, 0.5])
state = state_overlap(
    {"early": 1.0, "late": 0.0},
    {"early": 0.0, "late": 1.0},
)

# geo == 1.0
# state == 0.0
```

This is the basic representation needed to distinguish spatial coexistence from temporal, vertical, resource, phenological, or other state partitioning.

### Generic potential biotic edges

```python
from esdm.interaction import interaction_opportunity

opportunity = interaction_opportunity(
    {"source_ready": 0.7, "source_other": 0.3},
    {"target_ready": 0.6, "target_other": 0.4},
    {
        ("source_ready", "target_ready"): 0.9,
        ("source_ready", "target_other"): 0.1,
        ("source_other", "target_ready"): 0.2,
        ("source_other", "target_other"): 0.0,
    },
)
```

This returns **potential interaction opportunity under the supplied state distributions and compatibility kernel**. It is not a realized-interaction probability.

Pollination, competition, mutualism, predation, host-parasite association, and facilitation are possible domain applications of the same generic edge API. Pollination-specific labels live only in `examples/`; runtime source is deliberately domain-neutral.

### Predictive biotic dependence

```python
from esdm.interaction import biotic_information_gain

gain = biotic_information_gain(
    [-1.0, -0.8],
    [-0.7, -0.6],
)
```

`gain > 0` means that adding the supplied biotic information improved held-out log score on the declared rows. It does **not** identify competition, mutualism, or another causal mechanism.

The known-truth benchmark includes a hidden-shared-driver world in which biotic information gain is positive even though the generating truth contains no biotic interaction. This is an intentional guard against interpreting residual association as causality.

### Non-skippable transfer ceiling

```python
from esdm.transfer import point_transfer_ceiling

result = point_transfer_ceiling(
    base_level="abiotic",
    ordered_steps=[("add_state", "state"), ("add_biotic", "biotic")],
    gains_by_step={
        "add_state": [0.2, 0.1],
        "add_biotic": [0.05, 0.08],
    },
)
```

A later positive information step cannot rescue an earlier failed one. Phase 1 implements only a point diagnostic; calibrated uncertainty remains in the source ODSP project until a later `esdm` integration.

## Evidence hierarchy for edges

Runtime edges use an explicit evidence tier:

```text
COAVAILABLE
  -> STATE_COMPATIBLE
  -> PREDICTIVE_DEPENDENCE
  -> REALIZED
  -> FUNCTIONAL
  -> CAUSAL
```

Higher tiers are never inferred automatically from lower tiers.

## Known-truth worlds

Phase 1 contains analytic worlds for:

1. measured shared environment: co-response without interaction, conditional gain = 0;
2. hidden shared driver: predictive dependence without interaction, gain > 0;
3. state partitioning: geographic overlap can be 1 while state overlap is 0;
4. directed biotic coupling: partner state truly changes target-state distribution, gain > 0.

These are method-boundary tests, not biological evidence.

## Relationship to the existing research programme

`esdm` is intended as an upper-layer integration point:

- ODSP -> information ladders and transfer semantics;
- SDMR -> later set-valued process attribution;
- 284b -> later observation/negative-evidence authorization;
- EOG -> later finite-world compatibility and contraction;
- ACSP -> later next-observation candidate allocation.

See [`docs/PROVENANCE.md`](docs/PROVENANCE.md) for exact boundaries and source results.

## Explicit non-claims

Phase 1 does not claim:

- a universal new SDM/JSDM learner;
- causal interaction from co-occurrence or residual association;
- occupancy from a potential edge;
- realized or functional interaction without direct evidence;
- universal superiority over existing SDM/JSDM/network methods;
- pollination-specific validation;
- field-efficiency gains;
- certified uncertainty for the point transfer ceiling.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

CI runs the full suite on Python 3.10, 3.11, and 3.12.
