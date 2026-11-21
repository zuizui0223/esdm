# NeoBat v2 abiotic/terrain/forest source qualification — response-blind freeze

Date: 2026-11-19. Child branch of draft NeoBat PR #244; no modification to main or the frozen v1 255-plant M0/M1/M3/N1 contrast. **No bat/plant occurrence response or SDM is read or fitted in this source audit.**

## Fixed products before any new source fetch

1. **Temperature** WorldClim v2.1 BIO1 and **precipitation** BIO12, 10 arcminutes, baseline 1970–2000; official fixed source `https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_bio.zip`, archive SHA-256 `00513224583665ec0f2f955a4ec252730c4deb2004cce9e793492a3f26df4dcf`; correct BIO12 member SHA `1e823e951ace0186c6eadd7368b4d0385c8f51cc952282c0f2d640bf7790fea5`. The earlier source check had a **job path wiring mistake** even though it logged `SOURCE_GEOHEADER_QUALIFIED` and exit 0. Preserve both the old failed-action and the corrected source receipt; do not rewrite the original.
2. **Topography first candidate** WorldClim v2.1 10 arcminutes elevation derived from SRTM: `https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_elev.zip`. First independent source pin requires two separate download byte checksums to agree. Record original ZIP/member SHA-256, GeoTIFF band count/CRS/shape/resolution, scale, nodata and units; do not treat this coarse mean elevation as terrain ruggedness. Until pinned, it is a **provisional** source.
3. **Forest first candidate** ESA WorldCover 2021 v200 10m classified canopy, class `10` tree cover, cloud-optimized EPSG:4326 GeoTIFFs in 3×3° tiles. Source: `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N03W075_Map.tif`, a single arbitrary Colombia tile used solely for API/header accessibility, not selected on bat/plant outcomes. This one-tile probe cannot establish continental coverage or 25km forest fractions; a `SOURCE_UNAVAILABLE` or `NOT_SAMPLED` result is preserved, never silently replaced. No 117GB global download.
4. **Environmental compatibility**: even passing all original-source checks does not make this an identical-time ecosystem snapshot: WorldClim is the 1970–2000 climatology, WorldCover the **2021** classification, and GBIF occurrence sources cover **2000–2025**. This is a cross-sectional macroecological baseline, not annual fruit availability.

## Source-only outcome and stop rules

- BIO1/BIO12 must pass the original *pinned* archive and member source checks, both EPSG:4326, single-band, valid raster bounds and transform. Never bypass the previous original ZIP pin.
- Elevation must pass two HTTP byte-exact reads of the same official source, one nonduplicate elevation GeoTIFF, EPSG:4326, one valid band, and inspectable nodata. Different source hashes, malformed raster or download error = explicit terrain STOP without fabricating the environmental predictor.
- WorldCover probe is optional diagnostic and, if access/metadata fails, is logged as a **forest source gate unresolved**, not evidence of forest absence. A successful one-tile check is **not** the full 17-country forest predictor.
- Export only hashes, source names and geoheader metadata; no original raster pixels, raw ZIPs, fine-scale bat/plant coordinates, GBIF rows or species×cell predictor tables.
- Do not fit any M0, M1, M2, M3, N1 ecological AUC until country-crossfit plant model inputs, independently sourced forest summaries, target-group effort/background and geographic holdout leakage checks are fixed. The exploratory 106-plant v2 source qualification remains 83/84 folds, not a prediction result.
