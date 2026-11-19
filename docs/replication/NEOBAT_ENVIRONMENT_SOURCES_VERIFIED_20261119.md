# NeoBat environment source checks: original climate, elevation, one forest tile

Date: 2026-11-19. Executed once as response-blind source-only [Actions #44530544903](https://github.com/zuizui0223/esdm/actions/runs/44530544903), with source gate tests successful. Raw source TIFF pixels and any biological locations were not committed.

Result: `docs/replication/neobat/abiotic_terrain_forest_source_preflight.json`.

- **WorldClim v2.1 BIO1/BIO12 original ZIP PASS**: SHA-256 `00513224583665ec0f2f955a4ec252730c4deb2004cce9e793492a3f26df4dcf` matches original immutable source; both individual raster members are single-band **EPSG:4326**, **2160×1080**. The previously identified corrected BIO12 member digest was validated. This persists actual qualified metadata and supersedes the earlier *workflow path* failure, without overwriting that historical run.
- **WorldClim v2.1 elevation source PASS**: two independently requested byte-identical original elevation ZIPs SHA-256 `6a9f4e9a37f289d594ed1567b63be344a4dacf247f0b69756e81df031087e3bd`; member `wc2.1_10m_elev.tif`, EPSG:4326, 2160×1080, one band. This is coarse **elevation**, not measured ruggedness and not independent of WorldClim's terrain-derived climatology.
- **ESA WorldCover 2021 v200 tree-cover one-tile access PASS**: one fixed tile `N03W075`, HTTP byte range **206** and a valid TIFF signature from public S3. This does NOT qualify the complete continental forest coverage, individual COG geoheaders, forest percentages, or mapping to 25km sample units. Source class 10 denotes tree cover, not necessarily continuous biomass or current fruit supply.
- **Temporal mismatch remains explicit**: climate baseline 1970–2000, classified landcover 2021, GBIF occurrences 2000–2025. These are broad habitat/climatology covariates, not annual resource dynamics or actual feeding.
- No 106-plant species distribution surfaces, spatial target-group sampling effort/background, bat model heldout AUC, causal mechanism, or independent external validation was estimated.

## Next scientific implementation gate

Prepare a **country-excluded, complete and consistent fixed-106 plant prediction matrix**. This needs full per-fold abiotic/habitat predictors (including forest in all 17 heldout countries and target-group effort), model calibration on outside-country plant occurrences only, and a strictly predeclared scoring universe. Do not silently substitute a single 10m WorldCover point value for 25km forest proportion, or a 1970–2000 raster for contemporary fruit crop intensity. Report failed rasters/plants/folds before any M3 vs M1/N1 empirical ranking.

The 255-plant v1 contract remains unestimated; exploratory v2 source support is 83/84 with structurally possible focal N1 swaps. **Main unmodified.**
