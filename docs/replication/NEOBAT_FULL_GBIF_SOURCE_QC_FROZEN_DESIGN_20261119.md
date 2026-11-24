# NeoBat DOI source full-row QC — pre-specified source inspection v1 (2026-11-19)

**Purpose:** From the two already minted and SHA-pinned original GBIF SIMPLE_CSV ZIP archives, establish the actual denominator of usable taxon × country × 25/50-km *recorded-presence cells* before species distribution model fitting. This is **source-data quality control**, not a model fit, heldout response test, or ecological effect.

## Frozen sources

- Bats: 26 GBIF taxon-key concepts, download key `0001156-261118162104854`, DOI `10.15468/dl.nxu727`, 85,912 records, archive SHA256 `fc94ff92a127ec22655733a0b0cdaf12b5b24794fcc0129532e8a1e49fe856f0`.
- Plants: 255 taxon-key concepts, key `0001157-261118162104854`, DOI `10.15468/dl.xwc5zf`, 367,988 records, archive SHA256 `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b`.
- Source and header receipt `docs/replication/neobat/gbif_archive_header_preflight.json` with original GBIF ZIP entry names and 50 headers.
- Name mappings from previously checked `gbif_search_preflight.json` and `plant_search_preflight.json`, including one documented `Carollia brevicauda/brevicaudum` bat alias. No post-outcome relabelling.
- Country proxy: the fixed 29 country codes in the original GBIF request; this does not define a biogeographic Neotropical boundary.

## Verified fields and row-level checks

Read the GBIF ZIP inside a temporary GitHub Actions runner without extracting or committing individual records. Verify original archive SHA256 and check exactly the pinned header before biological data inspection.

1. `gbifID`: unique per source ZIP. Duplicate gbifIDs are flagged; no repeated entry creates independent biological evidence.
2. Species: map **GBIF indexed `speciesKey`** to the exact accepted species taxon-key roster. Where `taxonKey` is in the roster but `speciesKey` is not, report conflict; DO NOT silently reassign species. An ancestor/subspecies can have a valid speciesKey, but we cannot treat subspecies and species as independent records.
3. Source `datasetKey` and original `occurrenceID`: count the number of distinct datasets and the repeated (`datasetKey`, `occurrenceID`) combinations. Missing event IDs do not constitute unique biological events.
4. `decimalLatitude`/`decimalLongitude`: must be numeric, finite and within bounds, then transform EPSG:4326 → EPSG:6933 (always_xy=True).
5. `coordinateUncertaintyInMeters`: classify **known ≤12,500 m**, known >12,500 m, missing/invalid. Even a recorded 12.5 km uncertainty does NOT guarantee a point belongs to one 25-km cell; the full uncertainty envelope can cross cell boundaries.
6. `countryCode`: verify in fixed requested universe. Records outside are a schema-provenance stop.
7. `year`: 2000–2025 inclusive; out-of-range values indicate source inconsistency.
8. Report `basisOfRecord`, study source datasets and country-level unique coordinate cells. Never interpret GBIF missing records as true absence.

## Output

- Whole-archive denominators and QC stratification for both groups.
- For every registered taxon: rows, strict-known-precision rows, cells at 25/50 km, strict-known-precision cells, country support counts, distinct contributing dataset keys.
- For every species×country: all valid recorded cells, precision-restricted cells, country record counts, distinct datasets, basis-of-record breakdown.
- **Eligibility is descriptive only:** ≥5 cells in a candidate heldout country and ≥20 outside-country cells for the same species, using independently de-duplicated cells. This is **not** an independent holdout validation; the published country/source aggregation has already been observed during feasibility investigation.
- No raw GBIF rows, coordinates, identifier-level tables, event IDs or source ZIP bytes committed to GitHub. Aggregates and hashes only.
- Failure modes must be separate: `TRANSPORT_STOP`, `SOURCE_HASH_MISMATCH`, `SCHEMA_STOP`, `TAXON_KEY_STOP`, `QC_INDETERMINATE`, with source-denominator coverage preserved.

## Claim boundary

Even a successful full-source QC cannot establish **plant availability/fruiting, co-occurrence within a cell, causal resource tracking, true occupancy, predictive model gain**, or any vertical niche response. `M3−M1` remains null/uncomputed until independently structured plant SDMs and bat reference/holdout data are fit and compared against source-matched nulls.

This is a newly frozen QC analysis built after public GBIF country-sample exploratory results; it is **not** an unopened independent ecological validation.
