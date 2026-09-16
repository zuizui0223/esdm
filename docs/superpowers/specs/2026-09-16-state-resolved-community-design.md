# State-Resolved Community Distribution v0.1 Design

## Goal

Build `esdm` as an upper-layer framework for community ecology and biodiversity that treats ordinary species-distribution modelling as a binary-state special case and adds explicit ecological states, generic biotic edges, diversity decomposition, and transfer-aware interaction diagnostics.

The project is **not** a pollination model. Pollination is one example of a generic biotic-interaction edge alongside competition, mutualism, predation, host-parasite association, and facilitation.

## Scientific object

For community context `c`, represent the ecological graph state as

`G_c = (N_c, Z_c, R_c)`

where:

- `N_c`: taxon/node availability or occurrence;
- `Z_c`: node-state distributions such as activity, phenology, vertical layer, resource use, phenotype, or life stage;
- `R_c`: generic biotic-edge states between nodes.

Ordinary SDM is recovered when there is one taxon, one binary state axis (`absent`, `present`), and no biotic edges.

The framework does not fit a universal learner in v0.1. It consumes probabilities or held-out scores produced by external SDM/JSDM/ML workflows and supplies community-state inference and validation primitives.

## Core principles

1. **Species occurrence is a special state, not the only state.**
2. **Co-occurrence is not interaction.** Spatial overlap, state compatibility, predictive biotic dependence, realized interaction, functional interaction, and causal interaction are distinct evidence levels.
3. **Potential interaction is generic.** The core never infers interaction type from taxon identity. Domain examples may attach labels such as pollination, competition, or predation, but the mathematical edge API remains generic.
4. **Predictive dependence is not causality.** Positive biotic information gain after measured-environment conditioning is reported as transferable predictive dependence. Hidden shared drivers can produce the same signal and are a required negative-control benchmark.
5. **Diversity is state-resolved.** Taxonomic turnover and within-taxon state turnover are reported separately before any network-level extension.
6. **Transfer is non-skippable.** A finer information level cannot rescue a failed earlier level. v0.1 implements a point transfer ceiling; certified ODSP-style uncertainty is a later integration.
7. **Existing projects remain sources of validated primitives, not code dumps.** `esdm` distills concepts from ODSP, SDMR, 284b, EOG, and ACSP while retaining explicit provenance and claim boundaries.

## Phase-1 modules

### `core.state`

`StateAxis(name: str, states: tuple[str, ...])`

Requirements:
- non-empty axis name;
- at least two unique non-empty state labels;
- deterministic ordering;
- no domain-specific assumptions.

### `core.community`

`CommunityStateDistribution`

Inputs:
- `taxon_weights: Mapping[str, float]`, normalized to one;
- `state_probabilities: Mapping[str, Mapping[str, float]]`, each taxon's state probabilities normalized to one.

Methods:
- `taxa`;
- `joint_probabilities()` returning `(taxon, state) -> probability`;
- strict validation of finite non-negative probabilities and matching taxon sets.

Interpretation:
- taxon weights describe community composition under a declared weighting scheme;
- state probabilities describe conditional ecological-state use given taxon;
- the object is descriptive/probabilistic and does not imply causal niche structure.

### `core.edge`

`InteractionEvidenceTier`:

0. `COAVAILABLE`
1. `STATE_COMPATIBLE`
2. `PREDICTIVE_DEPENDENCE`
3. `REALIZED`
4. `FUNCTIONAL`
5. `CAUSAL`

`BioticEdge(source, target, tier, interaction_type=None, metadata=None)`.

`interaction_type` is optional descriptive metadata. The core does not classify an edge as pollination, competition, mutualism, predation, host-parasite, or facilitation from node identity.

## Diversity API

### Alpha diversity

For taxon identity `I` and ecological state `S`, use the q=1 Shannon/Hill decomposition:

`H(I,S) = H(I) + H(S|I)`

and therefore

`D_joint = D_taxon * D_state_given_taxon`.

Functions:
- `shannon_entropy(probabilities)`;
- `hill_q1(probabilities)`;
- `alpha_diversity_q1(community)` returning taxonomic, conditional-state, and joint effective diversity.

The entropy identity is established information theory and is not claimed as a new theorem.

### Beta diversity

For equally weighted communities/sites `C`, define multiplicative q=1 beta diversity by pooled entropy minus mean within-community entropy.

Return:
- `beta_taxon`;
- `beta_state_given_taxon`;
- `beta_joint`;

with identity

`beta_joint = beta_taxon * beta_state_given_taxon`.

Required known-truth cases:
- taxonomic turnover only -> `beta_taxon > 1`, `beta_state_given_taxon = 1`;
- state turnover only -> `beta_taxon = 1`, `beta_state_given_taxon > 1`.

## Overlap API

`overlap_coefficient(p, q)` computes normalized overlap `sum(min(p_k, q_k))` after validation.

Two explicit uses:
- geographic overlap from normalized spatial-use distributions;
- state overlap from normalized ecological-state distributions.

The framework must recover the benchmark `geographic overlap = 1` and `state overlap = 0` for perfectly co-located taxa using disjoint states.

## Generic interaction opportunity

`interaction_opportunity(source_states, target_states, compatibility)` computes

`sum_s sum_t P_source(s) P_target(t) K(s,t)`

where compatibility `K(s,t)` must be finite and in `[0,1]`.

This output is **potential interaction opportunity**, not realized interaction probability. A pollination compatibility matrix is one possible example; the same function must support any generic source/target state pair.

## Biotic information gain

`biotic_information_gain(log_score_without_biotic, log_score_with_biotic, weights=None)` returns the weighted held-out mean

`G_{j->i} = E[ log P(Z_i | E, Z_j) - log P(Z_i | E) ]`.

Interpretation:
- `G > 0`: supplied biotic information improves held-out prediction on the declared rows;
- `G = 0`: no incremental predictive value under the supplied models/scores;
- `G < 0`: supplied biotic information degrades held-out prediction.

This is predictive evidence only. It does not identify competition, mutualism, or another causal interaction.

## Point transfer ceiling

`point_transfer_ceiling(base_level, ordered_steps, gains_by_step, tolerance=0.0)`.

A step passes only if every declared validation group has finite gain strictly greater than tolerance. The ceiling advances consecutively and stops at the first failed/unavailable step. Later positive steps cannot rescue an earlier failure.

This is a deterministic point diagnostic, not a confidence procedure. Certified ODSP inference remains out of scope for v0.1.

## Known-truth benchmark worlds

### W0: observed shared environment

Two taxa depend on measured environment `E` but are conditionally independent given `E`.

Expected result:
- raw/coarse association can be positive;
- oracle biotic information gain conditional on `E` is zero;
- interaction truth is false.

### W1: hidden shared driver

Two taxa share an unmeasured driver `U`; the observed conditioning set omits `U`.

Expected result:
- biotic information gain can be positive;
- interaction truth remains false;
- benchmark explicitly demonstrates why predictive dependence must not be promoted to causal interaction.

### W2: state partitioning

Two taxa have identical geographic-use distributions but disjoint ecological-state distributions.

Expected result:
- geographic overlap = 1;
- state overlap = 0.

### W3: generic directed biotic coupling

Taxon `j` changes the conditional state distribution of taxon `i` after measured-environment conditioning.

Expected result:
- positive oracle biotic information gain;
- interaction truth true at the generating-model level.

### W4: optional domain example

Pollination may appear only as an example/fixture using the generic compatibility API. It must not introduce pollination-specific logic into `core`, `diversity`, `interaction`, or `transfer`.

## Comparator boundary

Phase 1 includes lightweight benchmark comparators, not claims of full JSDM equivalence:

- independent spatial/occurrence overlap;
- unconditioned association;
- trait/compatibility-only interaction opportunity;
- state-aware conditional biotic gain.

A future full methods comparison may plug in established JSDM or network models through external held-out score adapters.

## Provenance from existing repositories

- **ODSP**: information ladders, non-skippable transfer-ceiling semantics, held-out score comparison.
- **SDMR**: preserve set-valued process support rather than forcing a single mechanism; later process layer.
- **284b**: absence/non-detection authorization and fail-closed observation semantics; later authorization layer.
- **EOG**: finite-world compatibility/contraction; later worlds layer.
- **ACSP**: candidate observation sets rather than occupancy claims; later observe layer.

Phase 1 implements only the generic state/diversity/interaction/point-transfer core. Later imports must preserve each source project's claim ceiling and validation provenance.

## Promotion gates for v0.1

All must pass before describing the Phase-1 kernel as internally validated:

1. exact alpha q=1 decomposition tests;
2. exact beta turnover decomposition tests;
3. geographic-vs-state partitioning recovery;
4. generic interaction-opportunity validation and domain-independence test;
5. W0 oracle conditional biotic gain numerically zero;
6. W1 positive predictive gain while interaction truth remains false;
7. W3 positive predictive gain with generating biotic coupling;
8. non-skippable transfer-ceiling tests;
9. no pollination-specific imports or constants in core modules;
10. all tests pass on Python 3.10, 3.11, and 3.12.

## Explicit non-claims

v0.1 does not claim:
- a new universal SDM learner;
- JSDM replacement;
- causal interaction identification from co-occurrence;
- occupancy from potential edges;
- realized or functional interaction without corresponding evidence;
- universal superiority over SDM/JSDM/network models;
- pollination-specific predictive validation;
- certified uncertainty for transfer ceilings;
- field-survey efficiency.
