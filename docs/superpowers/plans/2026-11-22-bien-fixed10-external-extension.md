# BIEN fixed-ten-country extension implementation plan

**Goal:** Execute the unchanged external plant comparison for all eight unopened
members of the existing ten-country roster and preserve the full combined panel.

**Specification:**
`docs/replication/NEOBAT_BIEN_FIXED10_EXTERNAL_EXTENSION_FROZEN_20261122.md`.

**Architecture:** Retain the existing adapter, country scorer and official R
acquisition boundary. Add explicit requested-country arguments with the old
CR/PA defaults. Run one private acquisition/model job per new country. A small
stdlib summary consumes the eight public results plus the preserved CR/PA file.

## Owned tasks and checks

1. **Python scope extension** — adapter/scorer and their two tests. Accept only
   the existing ten-country universe, verify 106 fits per requested country,
   preserve exact metrics and default CR/PA behavior. Check new country scope,
   unsupported/duplicate countries, empty-table unknowns and result accounting.
2. **R acquisition and matrix workflow** — R script/test and a new workflow.
   Preserve complete tables and safe bibliography retrieval; distinguish empty
   successful data from query failure. Eight fixed matrix entries, bounded
   concurrency, explicit public-file upload paths and private-input cleanup.
3. **Combined summary and actual result** — stdlib script and focused tests.
   Reject missing/duplicate/wrong-country inputs and altered CR/PA receipt bytes;
   verify all 1,060 pairs, training counts and null/status invariants. Calculate
   only the summaries specified before scores. Preserve actual receipts and
   write the scientific result with denominator and source limitations visible.

## Execution order

- Commit the specification before running any new-country acquisition/scoring.
- Implement the independent Python and R/workflow changes in parallel, then
  inspect their interface and run focused tests.
- Execute all eight country jobs, resolve actual failures, inspect/download the
  public artifacts, and produce the combined result without selecting countries.
- Independently review code and actual outputs, preserve the result, pass CI on
  that exact final head, and integrate. Integration status is recorded by the PR
  checks and merge event rather than a retrospective plan-status commit.

The user's instruction to continue authorizes this work. No additional
plan-selection or approval stop is introduced.
