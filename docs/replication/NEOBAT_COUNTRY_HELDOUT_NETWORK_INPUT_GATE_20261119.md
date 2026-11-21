# NeoBat leave-source-country-out resource predictor support gate — 2026-11-19

Stage: source and public GBIF **count metadata only**, no spatial GBIF
occurrences, plant model, bat SDM or ecological predictive comparison.

## Purpose

A frugivore may have at least three globally documented fruit partners
yet lose almost all of them when literature from a test country is withheld.
This source-only gate asks whether the potential resource-predictor input
can still be assembled from independent outside-country source studies.

## Deterministic procedure

1. Read author-original NeoBat CSV Records/Sites at commit
   d25292d19be32a85a21c60384a3f2d818e8081de.
2. Keep only primary cohort 26 bats with literal
   Interaction=Frugivory, TrophicGuild=Frugivore,
   source species-like names, >=3 plants, >=2 references, >=2 countries.
3. Plant names are admitted if the 2026-11-19 GBIF metadata audit
   has exact species match and >=5 indexed georeferenced records in
   each of at least **two** countries. 218/261 plant strings satisfy
   this preliminary **record count** gate; no 25-km spatial-cell
   independence is inferred.
4. For each focal bat and each country where that bat has a source
   fruit record, remove that country and **all records sharing a
   RefCode observed in the withheld country** from the training
   NeoBat network (including any multi-country publications).
5. Count distinct admitted plant partners and source RefCode in the
   remaining training literature. A source fold is provisionally
   admissible if >=3 plants and >=2 RefCode survive. These are
   *network-input* folds, not validated bat SDM heldout folds.

## Result

- 26 source candidate frugivorous bat species.
- 7/26 have at least four country-heldout folds retaining
  >=3 screened plants and >=2 independent training source references.
- 17/26 have at least two such source folds.
- 3/26 have zero: *Artibeus concolor*, *A. cinereus*, *A. gnomus*.
- The seven with >=4 source folds are:
  *Carollia perspicillata* (10), *Artibeus lituratus* (8),
  *Artibeus planirostris* (5), *Sturnira giannae* (5),
  *Carollia brevicauda* (5; GBIF nomenclature alias separately
  documented), *Artibeus jamaicensis* (5), *Chiroderma villosum* (4).

## Interpretation and restrictions

These numbers show that country-withheld *network predictors* remain
defined in at least four countries for seven source taxa. They do not
show any cross-country bat occurrences or plant 25-km cells, let alone
a transportable fitted SDM. Country labels are source metadata, not
biome-matched independent geographies. Source literature heterogeneity
remains. Keeping original 26 denominator and distinguishing the
seven-species high-coverage exploratory stratum prevents post hoc
selection by model performance.

Next independently necessary check is bat+plant 25/50 km grid
occupancy-by-record distributions, then DOI-bearing data, spatial
buffered holdouts and M3 vs M1 / rewire null.
