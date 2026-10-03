# E5 candidate public pre-screen: Queensland Wet Tropics 2022–2023

Status: **E5_CANDIDATE_NOT_YET_QUALIFIED**

This pre-screen uses public project/method metadata only. No WildObs deployment row,
observation row, species count, diel outcome, or predictive score has been opened.

The candidate is stronger than the stopped Sumatra route because the original data are
stored as Camtrap DP with separate `deployments`, `observations`, and `covariates`
resources. The public ALA description also documents matched camera placements at each
sampling location: one camera on a road/linear feature and a second camera about 50 m
into the bush.

A related range-wide cassowary analysis demonstrates an explicit repeated-visit
observation model: cameras are converted to 5-day detection occasions, and the detection
formula considers active-camera effort, trail/bush status, feature type, camera brand,
deployment team, and season. That is a plausible E5 detection-identification route,
unlike simply assuming detection equals one.

It is **not yet a G4 pass**. Road and bush cameras sample different microhabitats, so the
physical pair alone cannot be interpreted as a pure detection calibration. The exact
repeated-visit/detection structure must be frozen after response-independent deployment
geometry is obtained.

## Current gate state

- G1 independent source: PASS
- G2 schema/effort/time: PROMISING; Camtrap DP deployments exist but have not been read
- G3 geography × source/protocol crossing: PROMISING/PENDING deployment cross-tab
- G4 detection identifiability: PROMISING repeated-visit path; paired layout alone insufficient
- G5 physical replication: PROMISING; exact package geometry pending
- G6 temporal support: PENDING split-specific deployment months
- G7 model freeze: NOT REACHED

WildObsR can return project metadata without tabular resources using
`metadata_only=TRUE`, but deployments require authenticated API access. A separate
child contract therefore permits only the WildObs `metadata` and `deployments`
collections; `observations` and `media` remain forbidden during candidate screening.
