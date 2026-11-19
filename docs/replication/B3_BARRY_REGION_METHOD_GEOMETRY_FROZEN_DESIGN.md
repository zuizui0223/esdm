# B3: Barry camera × detection-dog sample-unit/ecoregion support — frozen response-blind geometry

**Frozen 2026-11-19 before accessing *any* camera/dog detection outcome value.** The existing independent B1/B2 Figshare source checks verified the original byte-level metadata, 3 exact CSV hashes and headers (no source response parsed). The new question is **whether sample-unit keys and publication-defined ecoregions are actually shared between camera and dog survey methods, and whether apparent camera hardware IDs move between sample units.** This is a technical *deployment geometry* response, not a new ecological occurrence effect, detection-parameter fit, or original E5 qualification.

## Exact input sources and metadata-only columns

- Figshare article [16821361 v1](https://doi.org/10.6084/m9.figshare.16821361.v1), official `CamStations_Ecosphere.csv` 211555 bytes MD5 `0c9963ee9a52fdf6d05c15ed1d13193c`, file ID `31117351`.
- Same article `DogTracks_Ecosphere.csv` 951580 bytes MD5 `f3ae1ac01ad3b0b48d909a3f86845552`, file ID `31117348`.
- From camera file ONLY: `Sample Unit`, `EcoProvence_number`, `Camera #`, `season`, `min_date`, `max_date`, `operating_days`.
- From detector-dog file ONLY: `SampleUnit`, `EcoProvence_number`, `SegmentID`.
- `Fisher`, `pepe`, `caminop`, `wild_*` and coordinate fields are explicitly **prohibited from access**, not compared or exported. The CSV parser necessarily reads each row to select metadata, so it is accurate to say **original survey metadata rows were inspected, but biological outcome fields were neither accessed nor analyzed**.

Only strip leading/trailing and compress internal whitespace in keys; exact composite `(EcoProvence_number, Sample Unit)` is the sole allowed cross-table join. Do **not** substitute `Camera #` (hardware) for a physical site, and do not guess spatial crosswalks using coordinates. Refuse any original input byte hash/size drift, required-field absence, CSV parse failures. No alternative source/version.

## Predeclared purely descriptive outputs

Counts of total camera deployment rows and dog track-segment rows; missing sample-unit/ecoregion keys; unique camera sample-unit keys and dog sample-unit keys per publication ecoregion; exact `(ecoregion,sample unit)` overlap; count ecoregions with both methods, with ≥10 distinct units of each method, and with ≥3 shared units; reused camera hardware IDs mapping across units, and unit strings recurring across ecoregions; number camera rows with nonblank date range, nonblank operating-days and distinct season labels. Do **not** reveal camera/animal coordinates, unit IDs, scat identities, detection values, or any actual fisher occurrence.

A result with ≥2 ecoregions represented by both modalities is a potential **design crossing only**. It does not demonstrate conditional independence, paired detection identification, independent same-zone passage denominator or time-of-day events. The dog table exposes **no timestamp/date/duration field**, so original E5 G2/G6 may remain blocked even if the region-method cross-tab is rich. Do not promote to E5 G3/G4 PASS merely from ecological-region labels. No ecological effect, occupancy posterior, p-value or heldout transfer claimed.

Perform the run **once on PR opening** under unique branch, save one honest artifact regardless of positive overlap or technical stop, then permanently retire its workflow. Keep original E5 0/17 qualified and all other frozen empirical outcomes unchanged. Later work on camera vs dog outcome would need a separate newly frozen hypothesis and physical identity/exposure check, not posthoc selection of favorable geographic units.
