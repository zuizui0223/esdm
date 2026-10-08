# Rhode Island 2018–2023: deployment-only qualification adjudication

**Original E5: NOT QUALIFIED — G4 hard stop for this released uncalibrated pair design.**

The one-shot deployment-metadata workflow [37765754779](https://github.com/zuizui0223/esdm/actions/runs/37765754779) completed successfully. The archive ZIP SHA256 and the result JSON SHA256 are recorded in
`E5_RHODE_ISLAND_DEPLOYMENT_GEOMETRY_RECEIPT.json`. Its ZIP contains biological event data, but only its deployment metadata CSV was decoded (2,982 rows), while the detection CSV stream remained unopened.

## Observed deployment structure

- **2,982** valid deployment-effort rows; **1,488** Site × YearSeason groups
- **264** coordinate-consistent site identifiers, plus **one** spatially inconsistent site ID; original paper reports **249 survey sites**. Without a source-supplied ID crosswalk these are not guaranteed to represent 264 independent, distinct physical sites
- Operational longitude-median WEST/EAST blocks have **132 / 132** coordinate-consistent site identifiers with valid effort
- **126 / 120** site IDs have a paired-camera deployment overlap in the WEST / EAST blocks
- **692 / 630** site-period groups have paired-camera overlap, respectively
- Both blocks contain deployment dates in **all 12 calendar-month numbers**, pooled across years. This is not proof of uninterrupted exposure, matched season-specific overlap or all months at every site
- One site ID violates the frozen `0.02°` coordinate-consistency criterion

Paired deployments started from summer 2019 in the reported survey structure. The frozen result's status is `DEPLOYMENT_GEOMETRY_INCOMPLETE_OR_QC_HOLD`, not a candidate PASS.

## Why G4 does not follow from site pairing

The source reports cameras **about 50–100 m apart** (related 2019–2023 methods give a mean ~55 m and range 20–130 m). Camera members can have different local animal passage intensities; their observations are not matched records of the same known passages.

Even under a favorable simplifying assumption that both cameras share one encounter-intensity curve,
`E[Y_j(t)] = e_j(t) A(t) p_j(t)`,
the replacement `A'(t)=h(t)A(t)`, `p'_j(t)=p_j(t)/h(t)` leaves each expected observation rate unchanged for any admissible nonconstant positive `h(t)`. This is the response-free non-identification witness recorded in
`E5_RHODE_ISLAND_PAIRED_PRODUCT_NONIDENTIFICATION.json`.

Paired member IDs and overlapping dates are useful for site design but **cannot recover common diel effective detection apart from ecological activity**, without independent calibration, same-passage histories under justified assumptions or another demonstration that the predeclared detection model is structurally identifiable.

## Frozen gate interpretation

| Gate | Decision |
|---|---|
| G1 | Independent dataset: public source PASS |
| G2 | Deployment identities/effort confirmed; detection values remain unopened — partial |
| G3 | Within-site paired exposure observed, actual source/protocol crossing and original geographic split not established — partial |
| G4 | **FAIL for current uncalibrated two-camera product route** |
| G5 | Numerically sufficient operational site IDs, but source site-ID crosswalk/coordinate QC HOLD — provisional |
| G6 | Twelve calendar-month numbers per operational region; site-season support and diel effort not fully established — provisional |
| G7 | Not reached; no empirical model or response opening |

The published study is not declared invalid. The failure is of the **frozen E5 requirement** that detection be separately identifiable. The 249 versus 264 identifier mismatch and one spatial conflict are independent quality limitations and do not justify retroactively matching IDs to desired counts.

**Stop this candidate route.** Do not re-run either one-shot; do not inspect species/event records to repair the original G4; do not create further semi-synthetic gates to make it pass. A substantively new independent calibration resource, if discovered before focal outcomes, may justify a separate prospective candidate/route. Continue E5 only with explicitly documented detection information.

Sources: [Ecology 2025 paper](https://doi.org/10.1002/ecy.70094); [public data](https://zenodo.org/records/14508932); [related paired-camera methods](https://doi.org/10.1002/ece3.73834).
