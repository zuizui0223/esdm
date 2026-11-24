# CC1 post-hoc size-matched portfolio counterfactual — exploratory control

Date 2026-11-24. This is **explicitly defined after observing** the first CC1 published-seed portfolio result and is **not a preregistered independent test**. Original results in `cc1_original_seed_portfolio_result_20261124.json` remain unchanged.

## Diagnostic question
Among the 11 frozen original NeoBat plants with exact matches in the Cocha Cashu seed-fall time series, do the observed *candidate* bat-linked plant combinations have unusually low or high aggregate temporal coefficient of variation (CV), relative to **all** combinations with the same number of plant species drawn from those 11?

## Calculation
- Input original author source CSV, immutable Git commit and blob SHA recorded in `NEOBAT_CC1_SEED_PORTFOLIO_FROZEN_20261124.md`; only the 11 exact names already in the preserved result are in the comparison pool. Original links from original NeoBat source, 26 original candidate bats.
- For each linked candidate set of >=3 plants and >=60 shared observation dates: calculate the **same observed CV** as in the frozen first result, using `log1p(seed_count)`, normalize each plant by its mean across shared dates, equal-weight mean of plants by date, across-date sample CV. Preserve all 26 bats, including 15 ineligible.
- For each size k observed among eligible bat candidates, enumerate **all C(11,k) combinations**, no score-based selection or random sampling, and compute their observed CV on matched complete observation dates with exactly the same formula. Compare the linked candidate CV against this complete size-k descriptive distribution using fraction of combinations with CV <= observed (ties included). Lower percentile indicates comparatively temporally stable observed candidate set; higher indicates higher temporal variability. This **is not a hypothesis-test p value**; related combinations and bat portfolios share plant records, sampling dates, plots, source study, and landscape.
- Report eight **distinct plant sets** separately from 11 candidate bat labels. If multiple candidate bats have identical partner sets, present the same CV but do not imply independent effect confirmation.
- No BCI substitute, no taxa beyond source-frozen 106, no new NeoBat site records, no plant abundance or feeding data fitted. Do not treat zeros from seed traps as unavailable fruit or bat diet, and do not infer M3−M1.
- Return explicit failure for missing original file source, differing SHA, invalid count, or source mismatch. Public output remains aggregate with names and CVs only; no raw sampling coordinates or bat records.
