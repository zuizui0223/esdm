# NeoBat cross-country interaction-link transport diagnostic (2026-11-19)

**Evidence lane:** exploratory original-source diagnostic, **not** phase-1
trophic SDM confirmation. The same network was previously inspected and
candidate rosters discussed; this is not a preregistered independent
validation data set. No GBIF occurrence responses, plant SDMs or bat
predictions are used.

## Primary question

When a country is left out, do observed bat × fruit-plant links recur from
independent other-country literature more often than expected from local
bat degree and plant degree alone?

This quantifies **source-observed link transfer**, not absolute true
interactions, false pair absences, or ecological mechanisms.

## Locked input & denominator

Author original repository gflorezm/NeoBat_Interactions, commit
d25292d19be32a85a21c60384a3f2d818e8081de, three original CSV
Git blobs verified by the existing NeoBat source receipt. Keep
Interaction=Frugivory, TrophicGuild=Frugivore and two-token binomial-like
both names. Candidate 26 bat species pass source-only global gate
>=3 named plants, >=2 reference IDs, >=2 source-country labels;
these are the same first-phase primary cohort, not selected based on
country-heldout link recurrence. Only unique bat × plant × country
edges enter; repeat citations at a site do not multiply edges.

## Leave-country-out split & source independence

For each heldout country c:

1. All records from sources with any site in c are removed from
   the **training** literature, even when an original reference sampled
   multiple countries.
2. Form the heldout *positive-edge* graph from literature in c, limited
   to bat and plant names that occur independently in the training graph.
3. A test country qualifies for the null only if >=2 bat vertices,
   >=3 plant vertices, >=6 distinct test links, >=2 independent
   test references and at least one legal bipartite degree-preserving swap.
4. Original link-recurrence statistic is the number of heldout
   positive edges that also occur in the independent training graph,
   divided by the number of heldout test edges. A positive not seen
   elsewhere is a **not documented**, not evidence of absence.

## Degree-preserving null

For each eligible heldout country, randomize the *heldout* bipartite
edge set with only valid double-edge swaps: replace (bat A, plant X)
and (bat B, plant Y) with (A,Y),(B,X), without duplicate edges.
This holds all heldout bat and plant degrees and the observed set of
test nodes fixed. Score each rewired graph against exactly the same
other-country training adjacency.

Primary = equal-country mean actual recurrence minus equal-country
mean null recurrence. Use 999 replicates and fixed PRNG seed
20261119, 20 × E swap attempts each replicate and initial 100 × E
burn-in. Countries with no legal swap are **not** eligible and their
counts remain in the observability denominator. Estimate a one-sided
Monte Carlo tail probability from (1+ # null replicate mean >= actual)/(1+999).
Also report all per-country observed/null recurrence, country and
reference denominators, and a sensitivity that requires at least
two independent train references per training link.

## Interpretation

- An excess indicates published link identity has geographic
  predictive information above source-graph degrees, **conditional on**
  heterogeneous study coverage and candidate selection.
- A negative or zero result would limit using geographically stable
  NeoBat edges as realized resources. It does not disprove trophic SDM
  based on local fruit data.
- No local non-edge is treated as true non-consumption.
- Without an independent interaction data source, this result stays
  *exploratory source-internal* even with a small p-value.
