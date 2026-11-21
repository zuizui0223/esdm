# BIEN external plant diagnostic Implementation Plan

> **For agentic workers:** Use the existing parallel implementation arrangement;
> the primary agent integrates and performs one whole-change independent review.

**Goal:** Run the frozen 106-plant component on CR/PA BIEN plot cells and preserve
an honest, source-stratified, aggregate-only exploratory diagnostic.

**Architecture:** An adapter replays the original immutable plant component.
Official R BIEN functions acquire complete tables into a temporary private file.
A dependency-light Python grouping/scoring layer creates public aggregates.
One Actions job joins those parts and uploads only explicitly named receipts.

**Tech Stack:** Python 3.12, pinned original numerical libraries, R BIEN/jsonlite,
GitHub Actions and pytest.

**Spec:** `docs/replication/NEOBAT_BIEN_EXTERNAL_PLANT_DIAGNOSTIC_FROZEN_20261121.md`.

## Global Constraints

- Fixed 106 taxa, CR/PA, 212 results per mode; original fit counts must match.
- No BIEN training/tuning, bat outcomes, ecological M3 or absence claims.
- Preserve frames, country-wide focal-positive background exclusion and exact
  per-taxon training overlap exclusion; use the three specified date modes.
- Publish no raw coordinates, plot/cell identifiers or individual predictions.
- Commit the comparison specification before computing any BIEN scores.

## Review Focus

- Duplicate stems/visits must not increase cell weights.
- A positive in another frame/date must not become background.
- Missing dates/precision and absent taxon matches must remain explicit unknowns.
- Frozen helper import paths and training counts must match the original source.
- Failed acquisition or private-output paths must not masquerade as a successful
  public result or leak into uploaded artifacts.

## Task 1: Frozen component adapter

Files: `scripts/neobat_bien_frozen_plant_adapter.py`,
`tests/test_neobat_bien_frozen_plant_adapter.py`.

- [x] Expose `FixedPlantComponent` context, ordered `.taxa`,
  `.predict(country,cells)`, `.training_cells(country,taxon)`, `.provenance()`.
- [x] Verify country/border exclusion and lazy imports with focused tests.
- [x] Fit all 212 against real original ZIP/rasters; compare 106 predictions
  with original code (maximum absolute difference 0.0).

## Task 2: Source-stratified aggregate diagnostic

Files: `scripts/neobat_bien_external_plant_diagnostic.py`,
`tests/test_neobat_bien_external_plant_diagnostic.py`.

- [ ] Write failing tests for each specified grouping/leakage/missingness
  invariant, frame-only AUC, ties and aggregate-output privacy.
- [ ] Implement `prepare_records(rows,project)` and
  `evaluate_country(country,taxa,records,predictions,training_cells)`; return
  aggregates only. Connect the frozen adapter through the specified CLI.
- [ ] Run tests and inspect expected counts/AUCs, not implementation internals.

## Task 3: Acquisition and actual execution

Files: `scripts/neobat_bien_external_acquire.R`,
`.github/workflows/neobat-bien-external-plant-diagnostic.yml`.

- [ ] Acquire both full country tables with the official filters; verify schema
  and roster; separately write safe citations and acquisition counts.
- [ ] Run dependencies/tests, SHA-check original ZIP, checkout original commit,
  acquire, score, and upload only two explicit public JSON output paths.
- [ ] Inspect successful receipt content, model counts, coverage and every mode.
- [ ] Preserve actual results and interpretation in the repository, independently
  review the whole change, pass CI on the exact final head, and merge.

The user's continuing instruction authorizes this execution. No additional
plan-selection or approval stop is introduced.
