# esdm

`esdm` develops **state-resolved community distribution modelling**: an upper layer over SDM/JSDM outputs that treats ordinary binary species occurrence as a special case and adds ecological state structure, community diversity decomposition, generic biotic-edge opportunity, interaction-network turnover, and transfer-aware predictive dependence.

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

The package is learner-agnostic: external SDM, JSDM, Bayesian, machine-learning, or mechanistic models may supply probabilities or held-out scores. `esdm` evaluates the resulting community/state/network structure rather than imposing one universal fitting algorithm.

## Phase 1 — state-resolved community kernel

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

A later positive information step cannot rescue an earlier failed one. The current implementation is a point diagnostic; calibrated uncertainty remains in the source ODSP project until a later `esdm` integration.

## Phase 2 — community interaction-network distributions

Phase 2 adds a generic edge-distribution layer without changing the evidence hierarchy.

```python
from esdm.network import InteractionNetworkDistribution

network = InteractionNetworkDistribution(
    taxa=("a", "b", "c"),
    edge_probabilities={
        ("a", "b"): 0.8,
        ("b", "c"): 0.4,
    },
)

network.expected_connectance()
network.edge_mass_distribution()
```

Unspecified eligible edges have probability zero. Edge probabilities remain at the evidence tier supplied by the caller; they are not automatically realized, functional, or causal interactions.

### Connectance and rewiring are different quantities

Expected connectance uses the absolute edge probabilities. Rewiring uses the **normalized distribution of edge mass among partners**.

Therefore multiplying every edge probability by the same scalar changes expected connectance but leaves rewiring unchanged. This prevents a general weakening of all interactions from being mislabelled as partner-network rewiring.

### Interaction and partner diversity

```python
from esdm.network import interaction_diversity_q1, partner_diversity_q1

interaction_diversity_q1(network)
partner_diversity_q1(network, "a")
```

These are q=1 effective numbers computed from normalized positive edge mass.

### Network turnover and shared-taxon rewiring

```python
from esdm.benchmarks import pure_rewiring_world
from esdm.network import network_beta_q1, shared_taxon_rewiring_beta_q1

before, after = pure_rewiring_world()
network_beta_q1((before, after))
shared_taxon_rewiring_beta_q1(before, after)
```

`network_beta_q1` compares the full declared edge distributions. `shared_taxon_rewiring_beta_q1` first conditions on taxa present in both communities, so taxon turnover is not silently relabelled as rewiring.

Phase 2 deliberately reports taxon turnover, state turnover, and edge/network turnover as **separate axes**. It does not yet claim that the three multiply into one total community-beta identity.

### State-conditioned connectance

A set of network slices can be summarized separately by declared ecological state:

```python
from esdm.network import state_conditioned_connectance

state_conditioned_connectance({"resting": network_a, "active": network_b})
```

The state labels are supplied by the caller. The framework does not infer a causal state transition.

### Held-out community transfer

```python
from esdm.transfer import HeldoutCommunityPrediction, community_log_score_gain

result = community_log_score_gain(
    (
        HeldoutCommunityPrediction(
            community_id="site_A",
            outcomes=(1, 0),
            baseline_probabilities=(0.6, 0.4),
            enriched_probabilities=(0.85, 0.15),
        ),
        HeldoutCommunityPrediction(
            community_id="site_B",
            outcomes=(0, 1),
            baseline_probabilities=(0.4, 0.6),
            enriched_probabilities=(0.15, 0.85),
        ),
    )
)
```

Scores are first averaged within each independent community and then macro-averaged across communities. A community with many rows therefore cannot dominate the transfer estimand merely because it is larger.

The ordered community information ceiling remains non-skippable: a later positive interaction/function step cannot rescue an earlier failed state or biotic step. This is still a point diagnostic, not calibrated familywise inference.

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

Current analytic/deterministic worlds cover:

1. measured shared environment: co-response without interaction, conditional gain = 0;
2. hidden shared driver: predictive dependence without interaction, gain > 0;
3. state partitioning: geographic overlap can be 1 while state overlap is 0;
4. directed biotic coupling: partner state truly changes target-state distribution, gain > 0;
5. stable interaction networks: edge beta = 1;
6. pure rewiring: unchanged taxa but shared-taxon edge beta > 1;
7. connectance shift without rewiring: absolute edge probability changes while normalized partner structure does not;
8. taxon turnover with stable shared-taxon edge structure;
9. transfer-positive and transfer-null held-out network worlds.

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

The current package does not claim:

- a universal new SDM/JSDM learner;
- causal interaction from co-occurrence, residual association, or rewiring;
- occupancy from a potential edge;
- realized or functional interaction without corresponding evidence;
- universal superiority over existing SDM/JSDM/network methods;
- a total multiplicative taxon × state × edge beta identity;
- pollination-specific validation;
- field-efficiency gains;
- certified uncertainty for the point transfer ceilings.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

CI runs the full suite on Python 3.10, 3.11, and 3.12.
