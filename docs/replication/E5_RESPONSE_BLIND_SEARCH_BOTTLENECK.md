# E5 response-blind search bottleneck after 15 candidates

The E5 search has screened 15 independent candidate datasets without opening focal
biological response for selection. None qualifies.

The dominant bottleneck is **not lack of independent camera-trap data**. G1 passes for
14 of 15 candidates, and many candidates have ample physical replication or long
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

Kays41 is again the strongest named unresolved candidate, but it remains unqualified:
its dictionary route is transport-blocked and it has not demonstrated a separately
identifiable detection channel.

The Henrich10 stop sharpens the search criterion: **distance estimation is not the same
thing as response-independent detection calibration**. Future candidates should expose
the calibration object itself, not only downstream animal-distance outputs.
