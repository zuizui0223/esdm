# NeoBat GBIF country-stratified cell lower-bound pilot — 2026-11-19

## Status and motivation

**Response-blind operational successor to the abandoned exhaustive 14-taxon search paging attempt.** The earlier 14-taxon all-page GBIF SEARCH workflow ran for 29 minutes and was cancelled during the first species, after 6/6 synthetic spatial tests passed and before writing any source grid receipt. **No biological response or spatial cell count was produced.** This is a transport/runtime limitation, not a scientific result.

GBIF documentation states SEARCH pages are at most 300 records and total queries top out at 100,000; the API reference recommends DOI-bearing DOWNLOAD for jobs taking over 15 minutes or requiring citation. Therefore this successor is a **bounded lower-bound sampling preflight**, not a claim to exhaustively enumerate 25-km occupancy.

References: https://techdocs.gbif.org/en/openapi/ and https://techdocs.gbif.org/en/openapi/v1/occurrence.

## Fixed sample, no biological outcome-based selection

- Reuse the exact **4 bats + 10 plants** frozen in `NEOBAT_SPATIAL_CELL_PILOT_DESIGN_20261119.md`; no re-ranking by occurrence data.
- Reuse GBIF accepted usageKey from pinned 2026-11-19 source-only bat and plant name-match receipts.
- For each species, select **up to four countries** with the largest GBIF `regional_country_counts` from the pre-existing count-only metadata; include only preflight countries with >=5 coordinate records. Fixed tie-break by countryCode ascending.
- For each species × selected country use a single GBIF /v1/occurrence/search request with `taxonKey`, `country`, `hasCoordinate=true`, `hasGeospatialIssue=false`, `occurrenceStatus=PRESENT`, `year=2000,2025`, `offset=0`, `limit=300`. This is a **convenience-first-page sample**, not a random sample of all GBIF presences, and not a country-level census.
- Under a hard execution limit, issue **at most 56 distinct page requests** (14 taxa × 4 countries), with at most four concurrent requests and no more than two attempts per page. Stop on API rate-limiting; do not resume opportunistically by changing regions.
- Convert valid sampled coordinates to fixed EPSG:6933 25-km and 50-km grid IDs; store country × taxon counts only, not raw coordinates.
- Distinguish cells containing any indexed sampled record from cells with >=1 sampled record reporting coordinate uncertainty <=12,500m. The latter remain **reported precision**, not proof a record can be assigned unambiguously to a given 25-km grid cell, since its uncertainty radius may cross a grid edge.
- Emit per-taxon, per-country records returned, unique 25/50 km cell **lower bounds**, known-uncertainty cells, dataset count and status. Even 0 sampled cells must NOT be interpreted as an absent taxon or a failure of niche modeling.
- Aggregate total, errors, completion and the number of taxa meeting the **sufficient-only** sample threshold >=5 observed distinct 25-km cells in each of four sampled countries. A taxon not meeting that threshold is INDETERMINATE, not unsupported. The threshold was specified before sample coordinate results.
- All previous final 26-bat / 255-plant parent panels remain; this 14-taxon set is an *operational pilot*, not species selection on held-out SDM score.

## Claim boundary

If sufficient sample support: `GBIF_SAMPLED_CELL_LOWER_BOUND_CONFIRMED` — certain indexed taxa have at least that many cells across those countries. This **does not** certify independent records, unbiased coverage, comparable sampling effort, source independence, train/test fold adequacy, plant seasonality, relative suitability, GBIF citation DOI, or M3-vs-M1 predictive improvement.

If rate-limited, unreachable or incomplete: `SEARCH_SAMPLE_TRANSPORT_STOP` with a machine-readable partial receipt. The next full-data task remains an authenticated GBIF occurrence DOWNLOAD with DOI and properly frozen bat/plant origin, not unbounded synchronous SEARCH paging.

## Tests

Synthetic-only tests must verify: four-country selection from the independent metadata; deterministic tie-breaking; cap of one page per country; absence and uncertainty boundary; no raw coordinate leakage; stop on 429; no ecological result returned. CI cannot be interpreted as empirical spatial validation.
