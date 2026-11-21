# NeoBat full DOI-source country × resource qualification gate (2026-11-19)

Status: PREFIT source observability. No species-distribution model has been fitted and no independently heldout ecological result is claimed.

## Pinned cohort

- Full GBIF source QC: 26 bats, DOI 10.15468/dl.nxu727, 85,912 occurrence rows; 255 plants, DOI 10.15468/dl.xwc5zf, 367,988 rows.
- Original author NeoBat interactions, gflorezm/NeoBat_Interactions commit d25292d19be32a85a21c60384a3f2d818e8081de; source file hashes verified in earlier receipt.
- Exact primary bat names from Frugivory + TrophicGuild=Frugivore with >=3 named plants, >=2 source references, >=2 source countries; require exact match with 26 GBIF names. Plant names must be in original 255 exact-match GBIF plant accepted-name panel. No after-result name reassignment.
- Country universe: fixed 29 GBIF download country codes. Enumerate every 26 x 29 combination (754 rows) regardless of outcome, including those with no records.

## Prefit cell and source requirements

For both broader indexed records and stricter reported coordinate uncertainty <=12,500m:

1. A bat requires >=5 distinct 25-km recorded cells inside heldout country plus >=20 outside. A reported uncertainty below threshold may still cross grid boundaries. No negative/absence inference.
2. Exclude ALL NeoBat RefCode with any original site in heldout country, including records of those references collected elsewhere. Build bat-plant links only from remaining source rows.
3. Eligible fruit plant must be in 255-name original panel and show >=5 distinct 25-km recorded cells in heldout country and >=20 outside, on the same precision stream. This is **not** a cross-fitted plant SDM.
4. Potential source-country input fold requires >=3 different such plants with >=2 remaining independent RefCode supporting them.
5. Count nonpartner plants in all 255 that pass the same country cell gate, to inform generic pool M1 and degree-rewired N1; do not silently restrict generic plant pool to partner plants.
6. Keep every failure and report reasons. Do not change 5/20 or 3/2 thresholds after observing outcomes. Source country labels mapped to audited ISO2 map; unknown mapping is a STOP.
7. Record counts, duplicate species-country pairs, and approved source cohorts are checked against immutable receipts.

## Claim ceiling

Results certify only *input observability*, conditioned on highly uneven public GBIF sampling. They do NOT establish same-cell co-occurrence, feeding behavior, actual fruit abundance, taxon-interaction mechanisms, independent holdout generalization, source sampling effort calibration, or any M3-minus-M1 predictive gain. Earlier full GBIF records and country samples are already discovery-exposed. Independent confirmation requires an explicitly held back source/period and no post-hoc taxon or threshold changes. Main remains unaffected.
