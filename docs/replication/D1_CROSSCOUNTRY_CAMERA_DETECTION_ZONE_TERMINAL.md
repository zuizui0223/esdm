# D1 independent published camera-trap detection-zone transport: original one-shot schema stop

**2026-11-19. Terminal, scientific decision unchanged.** D1 opened the published authors' **EDD summary**, not individual animal events, after its exact analysis design had already been frozen as `docs/replication/D1_CROSSCOUNTRY_CAMERA_DETECTION_ZONE_FROZEN_DESIGN.md` in commit `27872ed37cb86fb8ed860652bf6d0900e3ff4cab`. The result was a **schema stop**, not a positive or negative country-transfer finding.

## Exact source and run

- Original Wiegers et al. (2025) public dataset DOI: https://doi.org/10.5061/dryad.gtht76j0c. Author code/data repository https://github.com/jnwiegers/predict_detection_zones, commit `7a1d0f05d6a8042615083a0c8397a92afff75484`.
- Pinned `LOOCV_data 2025.csv`: 56,728 bytes, Git blob SHA1 `64201f384e740031b4f3e9bbc116e3b2223d19dd`, used to verify the downloaded exact authors' copy **before reading the values**. Original authors' raw images, individual detections and other files were not downloaded.
- Initial authentication run [44448320111](https://github.com/zuizui0223/esdm/actions/runs/44448320111): GitHub Actions job `skipped` before any step; no source read. Corrected technical-restart authorization was recorded in `D1_COUNTRY_TRANSFER_TECHNICAL_RESTART.json`.
- **Only actual published-source opening**: [Actions run 44448539715](https://github.com/zuizui0223/esdm/actions/runs/44448539715), every job step completed successfully including 17 synthetic tests, source download, Git blob+length verification, and aggregate-only result upload.
- Exact original result [artifact 14493818950](https://github.com/zuizui0223/esdm/actions/runs/44448539715/artifacts/14493818950), archive SHA256 `b6cf84f9f5eedc7f7e441f030776197884bd5d43c61aae14a966c8514c47bf4c`, one inner JSON SHA256 `8740e8ad80d55391aba615e45d8559cbeae073cea14cf9df24189bed748e55f6` (276 bytes). Committed byte-identically under `D1_CROSSCOUNTRY_CAMERA_DETECTION_ZONE_FROZEN_RESULT.json`.

## What happened and what did not

The original predeclared rule required one **unique, nonblank `ID` per source EDD row**; the published summary does not satisfy that rule as interpreted by the frozen parser. The parser therefore returned:

`SCHEMA_STOP: source zone ID blank or duplicated`

This refusal is the **combined source-identity condition**. The result does not distinguish whether any ID is blank, duplicated, or both, does not report numbers or identities, and does not show that the authors' source is scientifically erroneous. Repeated zone identifiers may be meaningful under the authors' original statistical data grain. We **do not claim** a separate data-quality defect, a specific duplicate count, or an actual ecological outcome.

**Not computed:** eligible country count, country-heldout support, effective detection-distance MAE of M0/M1/M2, relative error improvement, direction of prediction effect, G3/G4 qualification, calibrated detector capture probability or an eSDM model fit. The response CSV has been consumed for this predeclared analysis; changing identity to `(ID, ref)` or removing duplicates and running again would constitute a **new, post-response-designed test**, not a confirmatory repair. D1 is frozen here. The original authors' published study-level findings can still be cited independently, but must not be recast as our D1 result.

## Current valid scientific conclusions

This attempt exposes a **schema/grain compatibility failure** in using a published zone-level training table for a different analysis. It does not show whether detection geometry is portable across countries. Independently calibrated *known animal passes missed by a motion camera* remain unavailable and **EDD estimated from triggered animal records is not `P(camera registers | independently known passage)`**. Original E5 remains 0/17 qualified and issue #242 remains an external data-acquisition dependency. E4/E7, Safari14, CamTrapAsia C1, NEON C2, Snapshot Europe C3 and algebraic M2 retain their previously frozen status. The published one-shot workflow is retired, with no source-opening reruns.
