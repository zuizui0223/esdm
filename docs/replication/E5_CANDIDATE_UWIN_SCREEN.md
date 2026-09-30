# E5 candidate screen: UWIN/Gallo 10-city diel-activity dataset

Status: **E5_CANDIDATE_NOT_QUALIFIED**

The public UWIN package was inventoried through the published Zenodo mirror after the
canonical Dryad transport route returned HTTP 403. Mirror bytes matched the published
Dryad MD5 before any inventory. Only ZIP member names and `ForDryad/README.md` were
opened; **zero data rows and zero response rows** were read.

The dataset is attractive for a different reason: it contains a large multi-city,
multi-year camera-trap study of diel activity. Published methods report 453 sampling sites
across 10 U.S. metropolitan areas and 41,594 trap nights from 2017–2018.

It nevertheless fails the frozen E5 qualification **before biological response opening**.

- **G3 crossed domain: FAIL.** The cities share one UWIN survey design; a second
  source/protocol domain overlapping geography is not declared.
- **G4 detection identifiability: FAIL.** Each sampling site used one motion-triggered
  Bushnell camera. No paired/simultaneous camera calibration, independent detection-
  distance calibration, or auxiliary detection stream is declared.
- G2 remains partial because the package README does not declare a separate
  response-independent deployment table with explicit start/end intervals.
- Physical replication and temporal duration are strong, but they cannot rescue G3/G4.

No response table is opened, no threshold is relaxed, and no E5 fit is authorized.

UWIN remains potentially valuable for a separately named study of geographic
nonstationarity in diel behavior. It must not be relabelled as the E5
activity-versus-detection test.
