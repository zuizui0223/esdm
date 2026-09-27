# Community network rewiring v0.2 — design spec

## Goal
Extend Phase 1 from node/state distributions to generic community interaction-network distributions without turning predictive association into causal interaction.

## Scope
Phase 2 adds learner-agnostic network summaries and held-out community transfer diagnostics. It remains generic across competition, mutualism, predation, host–parasite association, facilitation, pollination, and unknown interaction classes.

## Core object
For a declared taxon set T and eligible directed pair set E, a community interaction network is represented by edge probabilities

p_e = P(R_e = 1 | declared context),  e in E,

with 0 <= p_e <= 1.

These probabilities are potential/declared edge probabilities at the evidence tier supplied by the caller. They are not automatically realized, functional, or causal interactions.

## Quantities

### Expected connectance
Mean edge probability across the declared eligible pair set. This tracks overall edge occupancy/intensity separately from how edge mass is distributed among partners.

### Interaction diversity q=1
For total edge mass M = sum_e p_e > 0, define normalized edge mass w_e = p_e / M. Interaction effective number is exp(-sum_e w_e log w_e). Empty networks return 0.

### Partner diversity q=1
For a source taxon i, normalize its outgoing positive edge mass across eligible partners and return the q=1 effective number. No outgoing mass returns 0.

### Network beta diversity q=1
For multiple communities, align the union of declared edge categories, normalize each non-empty network to an edge-mass distribution, and compute multiplicative beta diversity as

D_beta = exp(H(gamma) - mean_c H(alpha_c)).

With two equally weighted communities, D_beta is in [1, 2]. Empty-vs-nonempty comparisons are treated explicitly rather than silently normalized.

### Shared-taxon rewiring
To distinguish rewiring from taxon turnover, restrict both networks to directed edges among taxa shared by both communities, then compute q=1 network beta diversity on that common edge universe. This is a rewiring diagnostic conditional on shared taxa, not a causal interaction metric.

### State-conditioned connectance
A mapping from declared ecological state labels to network distributions may be summarized by expected connectance per state. The framework does not infer state labels or causal transitions.

## Community transfer
Held-out community predictions are scored with Bernoulli log score. Rows are first averaged within independent community, then communities are macro-averaged. This prevents large communities from dominating the transfer estimand.

For each information level L,

G_L = mean_community[ score_L - score_previous_level ].

The ordered information ladder is non-skippable: a later positive increment cannot rescue an earlier failed or unavailable increment. Phase 2 remains a point diagnostic; calibrated familywise uncertainty is not claimed.

## Known-truth benchmarks
1. **Stable network**: same taxa and same edge distribution across communities -> edge beta = 1 and shared-taxon rewiring = 1.
2. **Pure rewiring**: same taxa, same node/state composition, different partner edges -> taxon/state turnover absent while shared-taxon edge beta > 1.
3. **Connectance shift without rewiring**: multiply all edge probabilities by a common scalar within bounds -> expected connectance changes while normalized edge distribution and rewiring remain unchanged.
4. **Taxon turnover**: differing taxon sets may change all-edge beta, while shared-taxon rewiring is computed only on common taxa.
5. **Transfer-positive edge world**: interaction-level predictions improve held-out community log score over a state-only baseline.
6. **Transfer-null world**: interaction-level predictions equal the state-only baseline and gain is 0.

## Explicit non-claims
- no causal interaction identification;
- no realized interaction claim from potential edge probability;
- no universal superiority over JSDMs or network models;
- no fitted learner family is introduced;
- no claim that taxon, state, and edge beta axes multiply into one total community beta quantity in Phase 2;
- no pollination-specific runtime behavior.

## Promotion gate
Phase 2 is reviewable only if tests show:
1. stable network identity;
2. pure rewiring detection with unchanged taxa;
3. connectance-vs-rewiring separation;
4. shared-taxon conditioning under taxon turnover;
5. macro held-out community gain behavior;
6. no pollination specialization in runtime source;
7. full Python 3.10–3.12 CI green.
