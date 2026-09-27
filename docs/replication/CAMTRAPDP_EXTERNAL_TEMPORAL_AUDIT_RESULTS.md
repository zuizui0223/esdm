# Independent Camtrap DP Temporal-Boundary Replication

Status: **AUDIT COMPLETE — ZERO INTERVAL VIOLATIONS**

This independently tests the exact deployment/event temporal rule that terminated the
first Snapshot Japan R5b empirical endpoint. It uses a different study, country, camera
deployment programme, and Camtrap DP export.

## Source

Amsterdamse Waterleidingduinen, pilot2:

- DOI: `10.5281/zenodo.11440456`
- file: `pilot2.zip`
- opened bytes: **345,939,445**
- MD5: `ac94e6e646c5702f67d939ea9a059641`
- SHA256:
  `243ae9a6f159abe99d836989686f04f458ca5ed38a6713e6617b361bd8604f51`
- deployment member: `pilot2/deployments.csv`
- observation member: `pilot2/observations.csv`

Audit run: `36298529369`.

Artifact:

- ID: `10924069778`
- SHA256:
  `8adac0ed5b92091ab80d2a6ab3a1b0a552368d5a7e1a4f0582a443405334d7d8`

Independent ZIP SHA256 matched the GitHub artifact digest.

## Result

- deployments: **2**
- observation rows: **194**
- unique event-level animal events: **86**
- unparseable animal-event rows: **0**
- exact interval matches: **86**
- before deployment start: **0**
- after deployment end: **0**
- missing deployment: **0**
- interval violations: **0/86 = 0%**

No ecological model was fitted and no heldout score was computed.

## Interpretation

The Snapshot Japan boundary failure did **not** replicate in this independent Camtrap DP
dataset.

That matters because it rules against the strongest generic explanation:

> exact deployment/event temporal matching is not intrinsically incompatible with
> Camtrap DP data.

In the independent pilot2 data, the exact frozen rule

`deploymentStart <= eventStart <= deploymentEnd`

worked for every audited animal event.

Combined with the Snapshot Japan audit, the current evidence is:

- Snapshot Japan: 13/7,620 all-animal events outside interval, all after deployment end;
- Amsterdam pilot2: 0/86 outside interval.

This makes a Snapshot-Japan-specific, export-specific, or curation-specific boundary issue
more plausible than a Camtrap-DP-wide rule failure.

## Limits

pilot2 is small: only two deployments and 86 unique animal events. This result therefore
does not prove that interval violations never occur elsewhere.

It also does not identify the exact mechanism behind the Snapshot Japan violations.

The first frozen R5b empirical endpoint remains unchanged and terminal. No row repair,
interval widening, model fitting, or reclassification is authorized by this replication.
