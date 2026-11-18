# C3 Snapshot Europe: does a 2021 country-specific *recorded assemblage prior* predict independent 2022 cameras?

**Frozen 2026-11-18 BEFORE opening any 2021 or 2022 animal-record row.** This is a separate, independent exploratory source with a *heldout-year and new-array* endpoint. Not E5 G4, not an eSDM fit, not a test of causal dispersal or true source-pool access. Earlier Safari14, CamTrapAsia C1, NEON C2 and E4/E5/E7 outcomes remain immutable.

## Evidence and exact frozen source

Iannarilli et al. (2026), *Ecology* 107:e70516, DOI https://doi.org/10.1002/ecy.70516; Dataset DOI https://doi.org/10.17617/3.7YLWMU, **Edmond released version 2.0**, file ID **345505**, `DataS1.zip`, **77,352,666 bytes**, published **MD5 `102a0e35504eaa95c1b59bcd71c42a0d`**, independently computed **SHA256 `8c19b00949be1cea77447fbd1d9804ebfbfafc17ed8d9b2088b577fc3da02f54`**. The exact URL is `https://edmond.mpg.de/api/access/datafile/345505`; no mirrors or alternate versions. This repository will not mirror wildlife rows/images. Attribution and CC BY-SA 4.0 source license must be respected.

**Pre-response schema verified in successful Github Actions `44250276089`, artifact `14404035505`:**
- `DataS1/Snapshot_Europe_2021_2022_deployments.csv`: year, project_id, deployment_id, longitude, latitude, start_date, end_date, camera_id, camera_functioning, subproject_name_no_year, subproject_name.
- `DataS1/Snapshot_Europe_2021_2022_projects.csv`: year, project_id, country_code.
- `DataS1/Snapshot_Europe_2021_2022_sequences.csv`: year, project_id, deployment_id, sequence_id, is_blank, class, genus, species, start_time, end_time.
- `images.csv` and `cameras.csv` are **not opened** by C3 biological analysis. Only header names and ZIP metadata were inspected previously, no species values, taxon directions or outcomes.

## Biological estimand and rationale

For a camera with verified deployment exposure, binary *recorded* taxon occurrence is the target (not independent animal passages or true occupancy). We compare two prospectively fixed predictors of mammal detection on a **2022 camera from an array that was not represented by the same named array in 2021**:

- `G`: 2021 all-Europe, species-specific camera-recording frequency (smoothed with one positive and one negative pseudo-record).
- `G+C`: the same global prior plus each country's 2021 camera frequency, shrunk toward `G` with **20 pseudo-cameras**. Countries with fewer than 10 eligible 2021 cameras use `G` unchanged. Neither model uses 2022 outcomes to select taxa, countries, smoothing strength or split.

For species `s`, define `p_global=(x_s+1)/(N_2021+2)`; for country `c` with at least 10 training cameras, `p_country=(x_{sc}+20*p_global)/(N_{c,2021}+20)`, else `p_country=p_global`. Predictions are clipped only to [0,1], which is already satisfied algebraically. The unit is a camera × taxon incidence in the publisher's common 1 September–31 October window. Predictions apply to camera *records* in 2022, never confirmed pool membership.

## Immutable extraction protocol

1. Use **only** three public CSVs listed above from the hash-pinned ZIP; stream content, do not open the much larger images table. CSV headers must match the exact published header fields and all required columns; missing fields → `RESPONSE_SCHEMA_STOP`, no rescue.
2. Metadata join is exact `(year, project_id)` from projects and `(year, project_id, deployment_id)` from deployments. Reject duplicated conflicting metadata keys; count/reject duplicate exact rows deterministically. Require explicit project `country_code` and nonempty `subproject_name_no_year` (trim whitespace only). Array key is `(country_code, subproject_name_no_year)`, not an inferred nearest coordinate.
3. Require valid ISO start/end calendar date and overlap with **September 1–October 31 inclusive** in that year of **at least 20 days**, valid `camera_id`, valid longitude/latitude bounds; if `camera_functioning` is explicitly negative (`false`, `no`, `0`, `n`, `broken`, `not functioning`) exclude. Unknown or blank functioning flag is retained but counted as unknown, not asserted operational. Do not infer effort from biological sequences. Group repeated eligible deployments under `(year, project_id, camera_id)`, and require a consistent `(country, array)` mapping for that group; do not count one physical camera twice.
4. From sequences, require exact `(year, project_id, deployment_id)` join to an eligible deployment; **nonempty** `sequence_id`; year 2021 or 2022; `class` exactly case-insensitive `Mammalia`, binomial defined by an alphabetic genus plus single valid species epithet. Exclude known domestic/human taxa (`Homo sapiens`, `Felis catus`, `Canis familiaris`, `Bos taurus`, `Equus caballus`, `Ovis aries`, `Capra hircus`) frozen now. A `true/yes/1/y` `is_blank` excludes the record. `start_time` must have parseable ISO YYYY-MM-DD prefix and lie inside September–October and the declared camera's overlapping survey period; unparseable and ineligible records are excluded with counts, not silently imputed. Deduplicate sequence ID × species × physical camera. Ambiguous conflicting `(year,project,sequence_id)` deployment identity is a technical stop. No image or individual ID export.
5. From eligible **2021 only**, rank taxa by number of physical cameras with positive records, selecting the first **up to 20** recorded on ≥10 cameras and across ≥3 separate countries (lexicographic tie-breaking). If fewer than **8** such taxa, terminal support stop. The 2022 records must never change this roster. Species not present in the 2021 roster are outside the predictive target and their count is not interpreted as true local absence.
6. Exclude every 2022 array key `(country_code, subproject_name_no_year)` seen in the 2021 eligible metadata; all remaining cameras are the **prospective new-array** validation set. Require ≥200 2022 validation cameras, ≥5 countries each having ≥10 eligible cameras in *both* training and new-array validation; otherwise `INSUFFICIENT_TRANSFER_SUPPORT`, no fallback to shared arrays. Require ≥200 2021 eligible cameras and ≥8 roster species.

## Frozen primary decision and diagnostics

Across the **complete** target-species × heldout-camera binary matrix, calculate `Brier = mean((y-p)^2)` for `G` and `G+C`; primary **gain** is `Brier_G - Brier_G+C` (positive means country borrowing improves). Require **gain ≥ +0.002** AND positive country gain in **at least 60%** of estimable shared countries (each with ≥10 2021 and ≥10 2022 validation cameras) to call `POSITIVE_DESCRIPTIVE_COUNTRY_PRIOR_TRANSFER`. Otherwise `NO_USEFUL_COUNTRY_PRIOR_TRANSFER`. All countries are included in total score, including countries without training cameras, for which G+C falls back to G.

Report training/validation camera counts, arrays and country counts; target roster size only (not individual species names), nonfocal 2022 taxon count, all exclusions/unknown functioning flags, global and country Brier, signed gain and country-positive fraction. No pairwise pseudo-replicate p-value, no fabricated CI or binomial abundance. A secondary descriptive check on only qualifying shared countries may be shown but may not override primary. Exact SHA/MD5 of source, script commit, run ID and decision recorded. No alternate source, post-outcome smoothing changes, thresholds, taxon switching or resampling after outcome.

## Inference firewall

A country label is only an **imperfect, administrative proxy** for accessible regional species pools. Predictive improvement would support transferable *recorded community regionality*, not explain it by IBD, IBE, dispersal, environment or biological species access, and cannot distinguish true occupancy from effort, species activity or detection. Negative results would apply only to this frozen source, grain and priors, not disprove source pools. A camera's non-record is not a true absence. Even a positive result does **not** qualify E5 detection G4 or prove eSDM superiority to a standard SDM; no jointly identified regional pool/occupancy/detector model is fitted.
