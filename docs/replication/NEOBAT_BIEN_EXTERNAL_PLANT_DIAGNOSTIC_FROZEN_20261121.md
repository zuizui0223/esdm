# BIEN CR/PA external plant diagnostic: frozen comparison

Frozen before BIEN prediction scores on 2026-11-21 (Asia/Tokyo).

## Question and scope

Can the existing climate-only plant component rank BIEN-recorded focal-plant
cells above other-plant sampled cells within the same returned survey frame
in Costa Rica (CR) and Panama (PA)? This is an exploratory geographic-transfer
diagnostic. Original-source independence is unresolved. This does not estimate
ecological M3, bat prediction improvement, occupancy, fruit yield, or absence.

Retain all 106 fixed taxa and both countries: 212 taxon-country results in each
mode, including unknown and non-estimable results. Do not choose taxa using
plot counts or observed performance. Exact returned binomials are matched to
the existing roster; no new synonym decisions are made after scores.

## Fixed model replay

- Original code: `d65817fcb3c39060ed544261c291d76a198299c6`.
- Roster SHA-256: `41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6`.
- Original GBIF plant ZIP: DOI `10.15468/dl.xwc5zf`, SHA-256
  `4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b`.
- Reuse original country-excluded training selection, StandardScaler and
  LogisticRegression (`C=1`, balanced classes, lbfgs, max_iter=400,
  random_state=20261119), using BIO1, BIO12 and elevation.
- Verify original training positive/background counts for all 212 fits.
  Fit all models before providing any BIEN evaluation cells. Do not tune or
  refit using BIEN labels. No bat outcome files are opened.
- Reuse original SHA-verified WorldClim files and 25 km EPSG:6933 cell-centre
  extraction. Scores are relative model indices, not calibrated probabilities.

## Observation frame and exclusions

Retrieve complete native-only country tables through official
`BIEN_plot_country(country=..., all.metadata=TRUE, natives.only=TRUE,
cultivated=FALSE)`. The denominator includes plots with no match to any of the
106 taxa. Do not query only focal taxa or use only focal-supporting plots.

Frame membership is the exact tuple of country, datasource ID, datasource and
dataset names, sampling protocol, methodology reference/description, plot area,
and all returned growth-form/taxon inclusion and exclusion metadata. Normalize
missing values and whitespace, but do not merge different observed frames.
Equal or missing metadata does not establish equivalent effort. Classify frames
as `METHOD_METADATA_PRESENT` if any of the three method fields is populated,
otherwise `METHOD_METADATA_MISSING`; report the two classes separately.

Convert finite geographic coordinates to the frozen cells. Multiple records,
stems, subplots and census visits in a cell count once per focal taxon and
frame. Source frames may share cells and are not independent replicates.

For each taxon-country-mode-frame:

1. Positive cells contain an eligible exact focal-name record.
2. Background cells contain any eligible plant record in that same frame.
   Remove every cell with a known focal-name record anywhere in the country,
   including in another frame or date mode. This conservative exclusion uses
   all valid-coordinate focal records, including records excluded by precision
   or date, and prevents known positives becoming pseudo-background.
3. Remove cells present in that taxon's actual original training-cell union
   from both classes. Preserve the original model; report overlap counts.
4. Remove raster-invalid cells from both classes and report counts.

Invalid geographic coordinates and negative/non-numeric known uncertainty are
excluded. Missing coordinate uncertainty is explicitly unknown. Known
uncertainty above 12,500 m is excluded from every mode. BIEN's geovalid flag
does not itself establish a measured coordinate-uncertainty bound.

## Three fixed date/precision modes

| Mode | Observation year | Coordinate uncertainty |
| --- | --- | --- |
| `primary_2000_2025` | Actual returned year 2000 through 2025 | Known <=12,500 m or missing, with missing counts disclosed |
| `known_precision_2000_2025` | Actual returned year 2000 through 2025 | Known nonnegative <=12,500 m only |
| `historical_undated_descriptive` | Returned year <=2025, or unknown | Known <=12,500 m or missing, with missing counts disclosed |

Use an explicit four-digit returned year or the leading year of an ISO-style
date. Unparseable dates remain unknown. Never substitute publication year or
program-wide date ranges. Records dated after 2025 are excluded in all modes.
The third mode is separately labelled descriptive and does not replace the
primary mode when the primary mode is non-estimable.

## Metrics, missingness and reporting

Compute pairwise rank AUC within each frame only when at least one retained
positive cell and one retained background cell exist. Ties contribute 0.5.
Do not pool scores across survey frames. Report cell counts with every AUC.
There is no additional minimum-plot eligibility threshold.

For each taxon-country-mode, report the equal-weight mean of estimable frame
AUCs separately for frames with and without method metadata. These are
descriptive summaries, not independent-replicate estimates. Report the number
of frames entering each mean. Do not issue p-values, confidence intervals,
success thresholds, or a pooled overall superiority claim from this diagnostic.

All 212 taxon-country entries remain in the output. A taxon never observed in
the returned table is `NO_MATCH_UNKNOWN`; an observed taxon without eligible
positive cells is `NO_ELIGIBLE_POSITIVE_CELLS`; positive support without any
within-frame background contrast is `NO_WITHIN_FRAME_COMPARISON`. None of
these statuses is an absence or a zero AUC.

Publish acquisition/source metadata, aggregate model provenance, counts,
within-frame AUCs and all missingness statuses. Do not publish or upload raw
tables, coordinates, plot/cell identifiers, model coefficients or individual
predictions. Private inputs may exist temporarily inside the job and must be
kept outside explicitly uploaded public output paths.

## Verification and interpretation

Before the run, test duplicate invariance, cross-frame positive exclusion,
within-frame calculation, exact training-overlap removal, unknown preservation,
date/precision handling, ties and public-output privacy. Verify model replay
against the original code and original source inputs. After the run, inspect
receipt status and actual denominators, not just workflow exit status.

Source IDs, citations and proximate-provider metadata are retained for further
provenance resolution. Shared institutions or similar titles do not prove
dataset identity or independence. Method differences, time mismatch, spatial
coarseness and sparse contrasts remain limitations even if AUC is high.
