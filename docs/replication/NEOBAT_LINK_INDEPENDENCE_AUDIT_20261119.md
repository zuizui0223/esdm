# NeoBat primary-frugivore link source-independence audit — 2026-11-19

Evidence tier: original source-only descriptive network structural audit;
NOT SDM predictive performance, habitat/resource utilization, ecological
selection, or causal interaction validation.

Input authors' repository: https://github.com/gflorezm/NeoBat_Interactions
Pinned source commit d25292d19be32a85a21c60384a3f2d818e8081de.
CSV identity recorded in NEOBAT_PHASE1_SOURCE_PREFLIGHT_20261119.md.

## Method

1. Keep Interaction=Frugivory and TrophicGuild=Frugivore.
2. Require two-term species-like strings in CurrentBatSpecies and CurrentPlantSpecies.
3. Candidate bats have >=3 distinct named plants, >=2 RefCode and >=2
   Country labels in the original sites table. They number 26.
4. Deduplicate (bat species string, plant species string). Within each link
   separately count independent RefCode and country labels.
5. This treats distinct study publications and named countries as coarse
   independent-source strata. It does NOT resolve shared raw field surveys,
   cryptic taxonomy, actual plant abundance, or presence/absence.

## Outcome

- 26 bat species; 1,106 original candidate bat×plant interaction rows.
- 709 deduplicated bat×plant links; 261 named plant strings.
- 497/709 links (70.1%) are supported by only one reference; 212/709 by >=2.
- 73/709 links (10.3%) have observations in at least two countries.
- 12/26 bat species have >=1 link observed in >=2 countries;
  only 4/26 have >=3 cross-country links.
- Across all 325 distinct unordered pairs of candidate bats, median
  raw linked-plant Jaccard overlap is approximately 0.036. This low
  overlap is strongly conditioned on unequal and incomplete observation
  efforts and must not be interpreted as demonstrated diet partitioning.

Highest independent cross-country link support in this source:
Carollia perspicillata (23 links), Artibeus jamaicensis (17),
Artibeus lituratus (16), Artibeus planirostris (7).
These four correspond to the >=3 cross-country-link subset.

## Scientific implication

Network availability supports a question about whether *documented potential
partners* add prediction above climate and generic plant distributions.
It does not by itself show that links are active or conserved across the
unobserved places. A transfer-success result in M3 would support an
out-of-region predictor, not that feeding interactions were directly
verified in the heldout region. Keep the entire predeclared 26-source
candidate denominator, report subset sensitivity without selecting
species by observed bat prediction score.
