# C3 Snapshot Europe 2021–2022: an independent time-transfer opportunity — source preflight only

**Date: 2026-11-18. Status: PUBLIC_SOURCE_RESPONSE_BLIND_PREFLIGHT.**

## New independent empirical opportunity

Iannarilli et al. (2026), *Ecology* 107:e70516, DOI [10.1002/ecy.70516](https://doi.org/10.1002/ecy.70516), released 2026-11-05, report 1,198 camera locations in 2021 and 967 in 2022, 90,230 trap days and 30 camera arrays sampled in both years across European countries. Public raw data and metadata are described as Supporting Information Data S1, a 106.4-MB ZIP, mirrored in Max Planck Edmond as [10.17617/3.7YLWMU](https://doi.org/10.17617/3.7YLWMU). The original supporting ZIP is available at `https://pmc.ncbi.nlm.nih.gov/articles/instance/13740659/bin/ECY-107-e70516-s001.zip`. Source license is CC BY-SA 4.0 (preserve attribution/share-alike for derived redistributed data).

Unlike the already consumed E7 Serengeti and Safari14, this is an **independent European** camera consortium with two separately observed years. This makes it a valuable candidate for a future frozen, prospective **2021-discovery to 2022-validation** test of geographically bounded recorded mammal assemblage structure and/or identifiable *composite* occupancy-and-effective-detection rates. Publication-reported field geometry is **not** demonstration of raw data parseability.

## What this PR is authorized to do (and no more)

- Read only **ZIP central-directory metadata and the first CSV/TSV header line** of each tabular file; calculate and record source SHA256, file count, extensions, sizes and column *names*.
- Never parse, summarize, export or expose any biological animal observations, spatial coordinates, species names from cells, identities, response directions, counts from record rows, detection histories, training/heldout scores or images.
- No new species threshold, model fit, E5 qualification, source-pool correction, or hypothesis promotion. A failed HTTP source download is a **transport stop**, not an ecological negative.
- Run exactly at the first PR-opening for the fixed head branch, with a subsequent **PR-number/head-SHA/attempt lock** before any new PR event. No `push`, `workflow_dispatch`, `schedule`, or `synchronize` source triggers.
- Read only the original publisher/PMC supporting data archive. A future alternative Edmond transport must be separately disclosed and source-pinned, never silently substituted.

## Pre-screen questions that matter

1. Is the public supporting ZIP truly available and hashable as published, or does it return an HTTP/HTML block?
2. Are *separate* deployment/exposure/effort and observation event tables present as documented, with explicit 2021/2022, physical camera and array identifiers?
3. Do the headers preserve habitat, survey protocol and source geography labels sufficiently to define a response-blind 2021/2022 transfer rule?
4. Does it expose an **independent non-trigger-selected known-passage reference stream**? If not, this **does not** qualify original E5 G4, even with repeated observations and full years.

## Decision after preflight

If headers are adequate, write **one subsequent untouched-outcome design** for exactly one ecological question and holdout. Reject if effort/deployment provenance or geography is too ambiguous. The observational q–d submodel (see `POOL_STATE_DETECTION_IDENTIFICATION_AUDIT.md`) remains the inference ceiling unless an independently identified reference is supplied. Do not re-open C1/C2, reduce E5 standards, or tune a synthetic generation. Original E4/E5/E7/Safari14/C1/C2 results are immutable.

This document is a source-readiness contract, **not** a positive ecological or identifiability result.

## Disclosed 2026-11-18 preflight transport follow-up

The initial PR #237 `opened` attempt stopped before any source request because its synthetic test import used a wrong repository-relative module path; the correction passed 10/10 source-free tests. The first technical `reopened` attempt then downloaded a HTTP-200 payload from the publisher-linked PMC endpoint, but `zipfile.is_zipfile` correctly rejected it as **not a ZIP**. No biological row was parsed. Result is a **publisher-linked transport STOP**, not an observation about European mammals. Do not re-fetch the same PMC endpoint in a rescue loop.

A **separate, explicit, response-blind** metadata check is now authorized using the original paper's second official repository: Max Planck Edmond dataset `doi:10.17617/3.7YLWMU` at its Dataverse public metadata API. The check reads only dataset version and file manifest, and downloads *one* public ZIP only when there is a unique unrestricted file under the frozen size cap. Any published checksum and size are checked before header inspection. The SHA256 and tabular column *names* only can be exported. If access or file ambiguity prevents ZIP preflight, stop without selecting a mirror or parsing animal records. No model fit or E5 qualification is authorized; original Safari14/C1/C2 outcomes remain unchanged.

## Edmond API metadata schema correction (no wildlife opening)

The first Edmond-only attempt, [Actions #44249905403](https://github.com/zuizui0223/esdm/actions/runs/44249905403), retrieved a JSON API response but the validator required `data.persistentId` exclusively. The native Dataverse API can also encode the immutable DOI in `latestVersion.datasetPersistentId` or in its `protocol/authority/identifier` fields. The program rejected this as `EDMOND_METADATA_STOP` **before extracting any file ID, downloading an archive, or parsing any animal row**. This was a pre-response tool-schema mismatch, not an ecological finding.

One final response-blind metadata attempt allows those native DOI representations only if they equal the *same original DOI exactly*; 23 synthetic tests pass. No different dataset, ecological threshold, biological response, or inference claim is selected. If no valid public ZIP schema is established, **freeze C3 as unavailable rather than retrying another route in this programme**.

## Final source result — official Edmond v2.0 (2026-11-18)

**Public-source preflight PASS with absolutely zero wildlife response cells.**
The final, exactly documented official-source [Actions run 44250276089](https://github.com/zuizui0223/esdm/actions/runs/44250276089) completed successfully after source-independent synthetic checks. Artifact 14404035505 contained only the original public Dataverse file metadata and CSV/TSV headers. The released `DataS1.zip` file ID 345505 at `https://edmond.mpg.de/api/access/datafile/345505` was checked against published **77,352,666 bytes** and MD5 **`102a0e35504eaa95c1b59bcd71c42a0d`**; independently computed SHA256 **`8c19b00949be1cea77447fbd1d9804ebfbfafc17ed8d9b2088b577fc3da02f54`**. It has five CSV members, including deployments, projects and sequences with year, country/project, physical camera/deployment, array-name, date, taxonomic identity and timestamp fields.

The exact [source-manifest receipt](SNAPSHOT_EUROPE_C3_EDMOND_PUBLIC_METADATA_RESULT.json) and [schema-only header receipt](SNAPSHOT_EUROPE_C3_HEADER_SCREEN_RESULT.json) are committed unchanged from the original Actions artifact. **No species/camera observation or detection outcome was opened, and this does not qualify E5 G4.** The consumed C3 header workflow has been retired by pinning the successful head SHA `f0e75da26c13d785b18044fca98b2a79a32d8b3e` plus original PR #237 and first attempt. Future PR opens cannot retrigger this data access.

The independent next response analysis is separately specified in `docs/replication/C3_CROSSYEAR_COUNTRY_PRIOR_FROZEN_DESIGN.md` on an **independent branch**, frozen at commit `a749550bf19a7fe73d0033fefcec9b37463f8bd4` before any source animal value is read. The preflight does not authorize any transfer claim by itself.
