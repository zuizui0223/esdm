# NeoBat bat/plant 25/50-km GBIF coordinate-cell pilot — design (2026-11-19)

**Stage:** spatial feasibility preflight only; no training, scoring or biological
outcome. Separately tracked from source-internal NeoBat country-link transfer.

## Predetermined pilot taxa from NeoBat network, not SDM prediction outcomes

Bat candidates with >=3 distinct *fruit* links documented in multiple
countries: Carollia perspicillata, Artibeus lituratus, Artibeus jamaicensis,
Artibeus planirostris (4 focal bats).

Plants with highest number of these 26 primary frugivore bat species
documented as fruit consumers (top 10, source-only network ranking):
Cecropia obtusifolia; Cecropia obtusa; Ficus insipida; Ficus yoponensis;
Solanum rugosum; Piper aduncum; Ficus citrifolia; Cecropia ficifolia;
Ficus trigonata; Ficus popenoei.

The complete first-stage cohort is 26 bat species and 261 named plants,
but this **14-taxon pilot** is a transport/source observability diagnostic.
No taxon is added or removed after seeing spatial-cell counts.

## Input source and non-DOI metadata caveat

- NeoBat original author CSVs pinned to GitHub source commit
  d25292d19be32a85a21c60384a3f2d818e8081de.
- Bat nomenclature and public search counts in
  docs/replication/neobat/gbif_search_preflight.json.
- Plant nomenclature and public search counts in
  docs/replication/neobat/plant_search_preflight.json.
- Re-query original accepted GBIF taxonKey from the above, with explicit
  accepted-name matching, not name-only occurrence searching.
- GBIF occurrence SEARCH: date 2000–2025, occurrenceStatus=PRESENT,
  hasCoordinate=true, hasGeospatialIssue=false. Maximum page size 300,
  maximum 100,000 hits per query. Fail closed on larger responses.
  API search does NOT generate a citable GBIF occurrence-download DOI.
  For the final paper, an authenticated DOI-bearing download and source
  reconciliation are mandatory.

## Geographical and grid conventions

- Equal-area CRS EPSG:6933; 25-km and 50-km square grid from projected
  coordinates (floor(x/25,000),floor(y/25,000)).
- Focal screening region = explicit listed American/Caribbean country codes
  in the upstream GBIF preflight. This is a **country-based proxy** for
  the Neotropical geographic region, not a rigorous ecoregional boundary.
- Distinct cells per species/country are counted, not claimed independent
  observations or true occupancy. A cell with an indexable presence record
  is not known to lack a species when no records occur there.
- Count geographic data-quality tiers:
  all indexed geospatially unflagged coordinates; explicitly
  coordinateUncertaintyInMeters <= 12,500 (known-precision subset);
  coordinate uncertainty missing; coordinate uncertainty >12,500 m.
  Unknown precision is NEVER silently counted as high-precision.
- Aggregate by indexed countryCode; retain number of distinct datasetKey
  per country and basisOfRecord counts; do not persist exact occurrence
  coordinates or sensitive event-level attributes in public receipts.
- Country with >=5 distinct 25-km cells can be an *exploratory candidate*
  heldout region. An apparently adequate sample does NOT pass ecological
  independence or leakage-safe spatial-block certification; train/test
  countries require future buffers, independent sources and legitimate
  counterfactual background.

## Termination

- Missing/mismatched source manifest or accepted taxon: SOURCE/TAXON_STOP.
- API count >100k per taxon or response schema without coordinates:
  API_LIMIT/RESPONSE_SCHEMA_STOP for that taxon.
- HTTP failure after bounded retry: REMOTE_STOP (save partial per-taxon
  receipts but do not claim an exhaustive pilot success).
- No post hoc relaxation of known coordinate accuracy or geographic
  inclusion to force sample sizes.
- Explicitly store zero for: DOI-bearing source download, verified
  absence, SDM prediction difference, geographic heldout test.

## Report

For each of 14 fixed taxa: matched taxonKey and live queried count,
relevant/overall coordinate rows, distinct 25/50km cells, known-accuracy
cells, country-level cells and dataset counts, countries with >=5 cells,
records with unknown uncertainty, and terminal status. Keep the
full 14-taxon denominator including data failures.
