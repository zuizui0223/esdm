# E2 MICA full-response terminal result

Status: **CONSUMED_STOP_SCHEMA_OR_ESTIMABILITY (terminal)**  
Date: 2026-09-28  
Workflow run: `36369531079`

E2 MICA reached the one-shot full biological response opening after passing all
prospective pre-response gates:

- response-blind geometry/header: **PASS**
- temporal integrity: **PASS**
- frozen WorldClim climate mapping: **PASS**

The full response was then consumed exactly once. The frozen capture adapter stopped
before model fitting with:

```text
ValueError: deploymentEnd must be after deploymentStart
```

The captured terminal receipt records:

- `full_response_opened = true`
- `scientific_name_values_read = true`
- `count_values_read = true`
- `model_fits = 0`
- `heldout_scores = 0`
- `fit_authorized_from_capture = false`

Therefore this is a **data-contract/schema-or-estimability stop**, not an empirical
result for the ecological activity/state decomposition.

## Scientific boundary

E2 MICA does **not** support or refute:

- transferred activity-process predictive information;
- transferred state-process predictive information;
- any biological mechanism claim.

Those endpoints were never reached because the one-shot capture stopped before fitting.

## Terminal rule

The response is consumed. The same E2 MICA programme is not eligible for:

- row repair and rerun;
- deployment-interval repair or widening;
- response-conditioned threshold/model changes;
- candidate switching after the consumed response;
- a second biological-response GET.

Exact provenance:

- authorization commit: `ca2507e6ad0b50c694e333362385fdc0267d0874`
- capture artifact: `10947948379`
- artifact digest:
  `sha256:e598e37ec7b3c2568d4008fd1b94b30a609b2c1be32a485bfc12daba6d32f9d7`
- captured result JSON SHA-256:
  `40e30397cd44d1a11122b01a0aa930d467b8efdfbe22334ed62bd0c2b1776e73`
