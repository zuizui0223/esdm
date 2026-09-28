# E2 MICA full-response terminal result

Status: **CONSUMED_STOP_SCHEMA_OR_ESTIMABILITY (terminal)**  
Date: 2026-09-28  
Workflow run: `36369531079`

E2 MICA passed its frozen response-blind geometry/header, temporal-integrity, and
WorldClim qualification stages, then opened the biological response exactly once.

The frozen capture adapter stopped before model fitting with:

```text
ValueError: deploymentEnd must be after deploymentStart
```

The consumed boundary is:

```text
full response opened = true
scientificName/count values read = true
model fits = 0
heldout scores = 0
fit authorized from capture = false
```

This is a data-contract/schema-or-estimability stop, not evidence for or against the
v0.4-R5b activity/state decomposition. Neither activity nor state predictive support was
evaluated.

The response is consumed. Row/deployment repair, interval widening, candidate switching,
response-conditioned model/threshold changes, a second response GET, and a same-program
rerun are not authorized.

Exact provenance:

- authorization commit: `ca2507e6ad0b50c694e333362385fdc0267d0874`
- capture artifact: `10947948379`
- artifact digest:
  `sha256:e598e37ec7b3c2568d4008fd1b94b30a609b2c1be32a485bfc12daba6d32f9d7`
- capture-result JSON SHA-256:
  `40e30397cd44d1a11122b01a0aa930d467b8efdfbe22334ed62bd0c2b1776e73`
