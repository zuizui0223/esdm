# NeoBat bat target-group background feasibility — prospective source gate (2026-11-19)

## Research boundary

This is an **exploratory, previously opened GBIF discovery dataset** source audit, not an independent ecological holdout and not a comparison of M1 vs M3. It uses the **already DOI-minted, SHA-authenticated bat GBIF original ZIP only**, with no new GBIF download request, and counts 25-km strict-geoprecision *observed source cells*. All 84 original species×country folds are retained, including the fixed 106-plant v2 failure (*Sturnira tildae* × Colombia). The frozen 255-plant v1 inference remains unestimated and unchanged.

## Fixed source, rules and tests

1. Read the 85,912-record original bat DOI `10.15468/dl.nxu727`, archive SHA-256 `fc94ff92a127ec22655733a0b0cdaf12b5b24794fcc0129532e8a1e49fe856f0`, downloaded from the already approved public GBIF ZIP URL. Validate the exact original source header, accepted 26 bat species keys, all original strict country×species 25-km cell totals, and the same 84-fold immutable roster.
2. Strict fixed spatial provenance: 2000–2025 observed records, known `coordinateUncertaintyInMeters<=12500`, valid EPSG:4326 coordinates projected with EPSG:6933; `cell=(floor(x/25000), floor(y/25000))`; collapse duplicate GBIF IDs and collapse repeated coordinates into *unique source-observed cells*. Do **not** treat cells lacking a focal bat as absences.
3. For focal species `s`, a target-group background candidate is a cell containing **at least one different taxon among the same 26 accepted bats** but no *recorded* `s` occurrence in that cell. Its label is `target_background`, never `absence`, and neither presence nor other-species record proves nonoccupancy.
4. For the withheld country, compute counts of unique focal presence cells `P_test` and other-bat background cells `B_test` after removing focal-occupied cells. Also count `B_test_same_dataset`: background cells with at least one `datasetKey` also observed for focal `s` within that withheld country. This is source-dataset overlap only, not a survey-specific pairing or detection calibration.
5. For the training region (all other fixed 29-country source universe locations), analogously count `P_train`, `B_train`, and `B_train_same_dataset`, excluding focal-occupied cells independently in each country.
6. **Primary feasibility gate** (frozen before new audit): `P_test>=5, B_test>=5, P_train>=20, B_train>=20`. This is *conditional on source-known 26-species target-group background*, not independent sampling completeness. Report exact counts/STOP causes for **all 84 folds**, and separately a stricter *diagnostic* if `B_test_same_dataset>=5` and `B_train_same_dataset>=20`. Do not revise original folded species/regions after inspecting results.
7. Keep **NO raw coordinates, per-cell ID, GBIF ID, datasets IDs, original rows, point labels or bat track samples** in committed source receipts or Actions artifacts. Export only species×country aggregate counts, source hashes and gate statuses. Summaries for country/source concentration and limitations are allowed.
8. At this stage: `M0/M1/M2/M3/N1 heldout AUC = null`; do not compute background-conditioned AUC from raw species presence alone. The actual v2 106-plant crossfitted suitability, full continuous 25km forest and effort, and target-group background bias correction still need implementation.

## Interpretation

This gate asks **whether a consistent plant-independent bat response/background denominator is observable**, not whether bats track documented fruit partners. Source-matching via `datasetKey` is useful but cannot establish matched detection events; training and test source-specific bias and source-country clustering remain. A scientifically defensible M1/M3/N1 comparison still requires the same heldout rows and predictor sampling for every model, plus spatial/source independence checks. No update to `main`.
