# B1: Barry Figshare and Clare Dryad public manifest preflight (response blind)

**Frozen 2026-11-19 before opening either biological-response table.**

## Why this audit

Barry et al. (2021), *Ecosphere*, DOI [10.1002/ecs2.3886](https://doi.org/10.1002/ecs2.3886) integrate camera trapping and genetically identified detector-dog scat surveys over a large Oregon extent and distinct ecological regions. The published author-declared data/code DOI is [10.6084/m9.figshare.16821361.v1](https://doi.org/10.6084/m9.figshare.16821361.v1), though the project cannot yet confirm its **actual file list** or physical station×ecoregion×method joins. Clare et al. (2017), *Ecological Applications*, DOI [10.1002/eap.1587](https://doi.org/10.1002/eap.1587), have public Dryad [10.5061/dryad.4mt00](https://doi.org/10.5061/dryad.4mt00): six named files, including a 238-station/maximum-nine-occasion 4-category marten camera/snow track encounter table and station/fisher/covariate data. These sources test **different questions** and are not evidence of independent missing-camera passages.

This is deliberately **source-access preflight**, not another synthetic eSDM generation and **not** a new E5 candidate qualification. Prior mainline empirical outcomes Safari14, C1, C2, C3, D1, E4, E5 and E7 remain frozen; original E5 0/17 qualified remains unchanged.

## Immutable pre-response questions

1. Does Figshare API `https://api.figshare.com/v2/articles/16821361` expose a source metadata JSON whose article ID matches **16821361** and whose DOI equals article 16821361? If yes, record all *names, file IDs, byte sizes and available MD5s*; if no, emit transport/identity stop. Do **not** fetch Figshare `/files/` or article download members.
2. Does the Dryad public dataset metadata API `https://datadryad.org/api/v2/datasets/doi%3A10.5061%2Fdryad.4mt00` identify exact DOI `10.5061/dryad.4mt00`? Record dataset metadata keys and publicly exposed names/sizes if available. If API does not enumerate files, report an explicit `DATASET_METADATA_PRESENT_FILES_NOT_ENUMERATED`, not invented file hashes.
3. For each, cap API JSON at 6 MB and record byte SHA256; export **no animal row or response**, private location, detector-dog scat identity or images.
4. Route decision is exclusively **technical**: if Barry metadata is reachable and lists full archived data, a *separate* response-blind schema/geometry audit may be designed. If Barry unavailable, Clare's confirmed published Dryad file list is an independent fall-back for a **single-region two-method** observational analysis. Clare does **not** pass standard E5 G3 and its snow tracks are not an independently observed denominator of camera-zone passages.
5. No biological outcome, country split, E5 G4 pass or model superiority may be inferred from these metadata. A technical source stop is terminal for this narrow audit; do not launch a repeated rescue of its same source.

## Execution contract

The workflow triggers once on a uniquely named new PR **opened** action and exact source-inspection branch; it first runs synthetic tests, writes a default transport-stop artifact, then calls the two **metadata APIs only**. Source URLs are allowlisted in script. Afterwards, retire the API workflow by disabling its job, merge independently of whether access succeeded. Never let a future PR silently reopen the same source. An author contact or publication date is not needed to run public metadata screening.
