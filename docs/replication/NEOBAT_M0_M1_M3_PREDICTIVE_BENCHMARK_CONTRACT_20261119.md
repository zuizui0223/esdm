# NeoBat M0–M1–M3 predictive benchmark contract — prefit implementation v1

Date: 2026-11-19. Research branch PR #244. **This is a software contract, not an empirical confirmation of the hypothesis.**

## Central test

Does the combination of externally documented **fruit-partner identities**
predict bat GBIF **relative observation ranking** in withheld regions beyond
abiotic/landscape effects and generic plant suitability?

- M0 = temperature + precipitation + forest + terrain + target-group sampling-effort index.
- M1 = M0 + cross-fitted mean suitability across the fixed partner-plant candidate universe, B(x).
- M3 = M1 + cross-fitted mean suitability among the focal bat's fruit partners
  recorded only in independent **training** NeoBat sources, R_s(x).
- N1 = M1 + R_s^swap(x), with bipartite bat–plant degree-preserving swaps
  **of training-only links**, a same-parameter-complexity identity null.
- Primary ecological contrast (when legally fit): M3 held-out rank AUC
  minus M1 held-out rank AUC, plus its advantage against N1 draws
  **per independently eligible species×region**.

Same environmental columns, same training data, model fitting options,
reference/control design and held-out geography for all candidates.
No species selection or coefficient sign preconditions after looking
at the held-out bat presence ranks.

## Required immutable inputs, no fictitious DOI substitution

1. \`bat_cells.csv\`: one focal species × cell × source observation unit row,
   with columns \`bat,region,cell_id,source_event_id,source_dataset_key,role,
   temperature,precipitation,forest,topography,effort\`.
   \`role\` is \`presence\` or \`target_background\`, **never absence**.
   Each independent source-event is unique to one outer region; repeated
   site/position points must be consolidated and documented before fitting.
   Sampling-effort and source-bias methods must be declared, not inferred
   by treating unreported cells as zeros.
2. \`plant_predictions.csv\`: \`holdout_region,cell_id,plant,relative_suitability,
   excluded_from_plant_training\`. For all training/heldout bat rows in
   a fold, plant relative suitability comes from **one** model for that
   holdout region, trained without any plant-occurrence records from it.
   It must cover the same complete fixed plant candidate universe in
   every cell. Values within [0,1] are a *relative index*, not calibrated
   probability of presence.
3. \`source_fruit_links.csv\`: \`bat,plant,ref_id,source_country\` from author
   NeoBat, \`Interaction=Frugivory\`, \`TrophicGuild=Frugivore\`.
   **All** references appearing in the test country must be excluded
   from *every* region's training links before R_s construction. A
   source-less or after-the-fact imputed link is forbidden.
4. \`evidence_manifest.json\`: genuine GBIF download DOIs for BOTH
   bat presences and plants, immutable file SHA-256s and source IDs,
   environmental raster/version manifest, candidate plant universe,
   source-key mapping, and the exact list of fixed held-out regions.
   The software refuses to claim any source-backed effect if these
   are absent. DOI format alone is necessary, not sufficient.

## Full original-site reference embargo (mandatory input)

The model-input manifest MUST include `site_reference_embargo_by_holdout`
for every evaluated heldout region. This is computed from **all 200
original NeoBat study sites** in the author data, not from the
fruit-only partner table. A publication with one site in the withheld
country is excluded globally, including partner records observed
elsewhere. Frozen source file:
`docs/replication/neobat/NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json`
(author commit `d25292d19be32a85a21c60384a3f2d818e8081de`,
sites Git blob `f9672a8b5542b8f4ecd3434ca798756f865df541`).

The M3/N1 model core rejects a missing embargo, malformed references,
or an observed heldout-source link not represented in the embargo.
This guard does not itself prove independent survey events in
the GBIF bat response or plant training data.

## Evaluation and interpretation

- Pairwise held-out presence-vs-target-background rank probability
  (rank AUC) is an index of discrimination **against a sampled
  background**, not specificity, occupancy probability, or a population
  demographic response.
- Fit transformations/regularization on training only. No country
  country-specific tuning using withheld responses, no spatially
  adjacent random holdouts, and no selection by reported performance.
- For ecological inference: independent regions/studies are primary
  replicates, not individual GBIF rows or repeat GPS fixes. Report
  per-species and per-region deltas, cluster uncertainty, and
  leave-region-out sensitivity. Null draws are a conditional descriptive
  foil unless the exact source-exchangeability assumptions hold.
- Demand ≥3 training plants across ≥2 independent refs, both
  held-out presences AND target background; stop/skips are denominated
  rather than forced via relaxed thresholds.
- Exact source event duplication across train and test is forbidden.
  This gate does not by itself guarantee dataset-level independence.
- Missing plant scores or attempted using heldout plant occurrences
  for the predictor: fail closed before any bat response evaluation.
- For each fold, lock the bat response before extracting B/R prediction
  scores; an actual independent final test needs a separate unopened
  source or a future observation window. The earlier 14-taxon
  GBIF SEARCH first-page sample **has been inspected and is
  exploratory, not sealed independent validation**.
- A positive N1 comparison can show geographically transferrable
  **published fruit-link identity as a predictor**; neither causality
  nor actual fruit abundance, state-specific foraging, 3D height,
  within-cell encounter, competition or social information sharing.
- The existing \`sdmr\` Product-A empirical nonpromotion and
  \`esdm\` E5 0/17 qualification do not transfer into this project as
  model support; use their holdout/identifiability discipline only.

## Current execution gate (2026-11-19)

NeoBat+GBIF source metadata, 55 bounded sampled country pages and 9/16
country-resource *input* pairs are documented. No authenticated GBIF
download DOIs, complete occurrence cells, plant cross-fitted prediction
tables, or bat spatially independent target-group reference sets have
been obtained. Any code-level synthetic exercise is NOT a field result.
