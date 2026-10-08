# E5 response-blind search bottleneck after 17 candidates

The E5 search has screened 17 independent candidate datasets without opening focal
biological response for selection. None qualifies.

The dominant bottleneck is **not lack of independent camera-trap data**. G1 passes for
16 of 17 candidates, and many candidates have ample physical replication or long
temporal coverage.

The scarce design property is the **joint satisfaction of G3 and G4**:

1. geography must be crossed with source/protocol rather than perfectly confounded; and
2. the released data must retain a separately identifiable detection channel.

Several apparently strong paired-camera candidates failed because public data collapsed
the two camera members to a station-level record. Multiple camera models are also
insufficient by themselves: without overlap or an independent calibration stream they
cannot distinguish activity from detection.

Therefore future search should reverse the old order. Before checking sample size or
duration, require one of:

- paired-camera/double-observer data with **camera-member identity retained**;
- deployment-linked distance/detection calibration;
- an auxiliary detection stream tied to the same deployments;
- another predeclared design that identifies detection separately from activity.

That detection/source factor must then overlap at least two geographic regimes.

Only candidates surviving those two checks should receive detailed effort, six-month
temporal-support, and physical-location qualification.

Henrich10 has now stopped at G4 after a one-shot response-blind OSF manifest precheck.
The public package exposes 10 `Samplingdays_*_export.csv` effort files, 10
`distances_export_*.csv` CTDS/event-distance files and two distance-sampling scripts,
but no separately named ranging/reference-calibration material.

This distinction matters. Event-distance outputs can support a detection likelihood only
after biological observations are opened; they are not an external calibration stream.
The article describes ranging-pole reference images, but that calibration path is not
reproducibly exposed in the public manifest. Under the frozen three-route rule, Henrich10
therefore stops without opening README contents, headers, event rows or focal response.

The Henrich10 stop sharpens the search criterion: **distance estimation is not the same
thing as response-independent detection calibration**.

Candidate 16 changes the search direction. Wolfson et al.'s wild-pig dataset has a
two-by-two geography × observation-method design: Florida and California each contain
both camera-trap and GPS telemetry data, and both methods are represented in all four
seasons. Public methods report 44 and 48 camera sites and 62 and 21 GPS-tracked
individuals in Florida and California, respectively.

This is stronger than Kays41 because the second observation channel is not another
camera configuration: GPS telemetry can provide an external ecological-activity anchor.
It does **not** automatically pass G4. Final identifiability still requires the public
GPS schema to retain individual, time and movement/activity information and a frozen
joint model showing how the external activity channel identifies camera effective
detection. The next response-blind step is therefore header-only across the 16 pinned
seasonal CSVs; no data row or effect direction is authorized.

Kays41 remains unresolved but is no longer the strongest named candidate.

## Current frontier: retained camera-member identity (candidate 17)

The original standard E5 route remains **0/17 qualified**, even after the
Wolfson wild-pig GPS/camera alternative completed with frozen UNRESOLVED
transfer gain and a California sample-identity QC HOLD. That separate
activity-anchor route must never be treated as an original G4 pass.

Mayer et al.'s Rhode Island 2018–2023 survey is now the strongest *unresolved*
named original-E5 candidate at the public-design stage, not qualified. It
differs from earlier paired-camera failures: the Zenodo v3 description
explicitly states that camera-level identifiers survive in **both**
deployment and detection tables. The associated 2019–2023 methods place
two cameras at each site, approximately 50–100 m apart, across statewide
east/west sections and repeated summer/winter survey windows. The public
reported total is 249 survey sites.

But 50–100 m separation is **not** a double-observer shared-passage design.
Camera member identity alone cannot pass effective-detection G4. The
necessary next steps are one frozen ZIP member/CSV-header check, then
response-independent verification of paired physical site membership,
deployment overlap, geographically heldout effort and a structural
detection-identifiability argument for the actual paired geometry.
No focal event rows, taxon selection, effect directions or fits are
authorized by the initial ZIP-header route.

## Candidate 17 deployment-geometry outcome (2026-10-08)

The one-shot run [37765754779](https://github.com/zuizui0223/esdm/actions/runs/37765754779) succeeded on **deployment metadata only**, with 0 focal biological rows opened. It confirms 2,982 valid deployment rows and 1,488 site-period groups; 132 coordinate-consistent site identifiers in each operational longitudinal half, 126/120 paired-overlap site identifiers, and all 12 calendar-month numbers in each half. This is pooled over years, not proof of continuous exposure or matched original study zones.

The frozen result is **DEPLOYMENT_GEOMETRY_INCOMPLETE_OR_QC_HOLD**: one site ID has spatially inconsistent coordinates, and the 264 coordinate-consistent site IDs have no independently documented crosswalk to the published 249 survey sites. No identities have been inferred or corrected.

More decisively, **G4 fails under the released uncalibrated separated-camera design**. Camera members about 50–100 m apart with overlapping deployment dates are not matched observers of a known shared-passage denominator. The response-free multiplicative gauge proof records why common diel effective detection and diel activity are not uniquely separable from two event-rate streams. Camera-member identities are necessary for evaluating relative sources but insufficient to identify the common observation process. No detection CSV rows are authorized for opening or rescue.

Original E5 remains **0/17 qualified**. Rhode Island is a terminal negative qualification assessment for the currently available calibration route, **not a biological null result**. Kays41 remains an unresolved named data source with its dictionary transport blocked, not a qualified candidate. The next useful discovery must start from a truly independent sensor/passage calibration source rather than another uncalibrated camera-pair archive. See `E5_RHODE_ISLAND_DEPLOYMENT_GEOMETRY_RECEIPT.json` and `E5_RHODE_ISLAND_GEOMETRY_TERMINAL_INTERPRETATION.md`.
