# One-shot empirical source workflows: accidental NEON C2 replay and permanent PR-event guard

**Audit date:** 2026-11-18 JST. **Nature:** technical workflow integrity, not a new wildlife ecology result.

## What was discovered

The already-merged NEON C2 workflow (`.github/workflows/neon-c2-region-pool-null.yml`) had:

```yaml
on:
  pull_request:
    types: [opened]
# ...
    if: github.event.action == 'opened'
```

This guarded the **event kind** but did not guard the **exact PR identity or source-opening commit**. Therefore **every new PR opened in `esdm`**, not just C2's original PR, could run the already-consumed source-download and biological schema check. This contradicts C2's original one-opening freeze. On opening the unrelated structural-identification PR #236, the workflow actually ran again:

| GitHub run | Original head | Meaning | Result |
| --- | --- | --- | --- |
| [43900837691](https://github.com/zuizui0223/esdm/actions/runs/43900837691) | `b3921e1d9cb3a10ff5ae525836a93c04761a8d54` (PR #235) | originally authorized one-off NEON C2 opening | `RESPONSE_SCHEMA_STOP`; species-class conflict; no ecological fit |
| [44245953747](https://github.com/zuizui0223/esdm/actions/runs/44245953747) | `25f976637f4e823f7c6c93ad288630ba1d9ff87d` (unrelated PR #236) | **unintended repeat due to broad trigger** | same terminal `RESPONSE_SCHEMA_STOP`; no ecological fit |

The unintended workflow was **complete before its trigger defect was detected**. Its result ZIP artifact is [14401303446](https://github.com/zuizui0223/esdm/actions/runs/44245953747/artifacts/14401303446), ZIP SHA256 `37860592683b45aae91eebc7d12e6e9e30b8505f5db436ca13e0e16d8fd0683d`, inner JSON SHA256 `364c5eef71a5db979502d5de8a5d6ad6aebad066cbb5ccffa8433bc950b436fb`. The inner JSON reports unchanged `RESPONSE_SCHEMA_STOP` with reason `taxonomic class conflicts for a binomial`, `model_fit_performed=false` and `previous_results_changed=false`. The workflow itself returned `success` because it successfully **published the terminal stop**; do not confuse green Actions with ecological success.

This violation is documented rather than hidden. No new biological estimate, repaired taxonomic label, or changed C2 scientific endpoint is accepted from the unintended run. Original C2 result is the only frozen scientific source receipt.

## Implemented change

The C2 source-opening job now runs only if **all** are true:

```
github.event.action == 'opened'
github.event.pull_request.number == 235
github.event.pull_request.head.sha == 'b3921e1d9cb3a10ff5ae525836a93c04761a8d54'
github.run_attempt == 1
```

The other consumed independent source, CamTrapAsia C1, also had a potentially broad `pull_request: [opened,reopened]` trigger on its related-file paths **without a head identity gate**. Although it did **not** rerun on PR #236, a future PR modifying C1 files could have reopened its already-consumed biological response. This is now pinned to its actually authorized original source opening **PR #234, `reopened`, head `8cb348c1996343c25b55c7c86d9679beb04d9449`, first attempt only** ([run 43894683151](https://github.com/zuizui0223/esdm/actions/runs/43894683151)).

A new regression test, `tests/test_consumed_source_workflow_guards.py`, fails if either job loses an exact PR number, immutable head SHA or `run_attempt == 1`, or gains another GitHub event trigger. It also tests that new PR #236 and attempts >1 are rejected under the fixed event predicates. Existing Safari14 and E7 one-shot empirical workflows already pin their original source-opening head SHA and were left unchanged.

### Important remaining operational boundary

Editing a workflow file now guards **future runs using the new workflow revision**. It does not retroactively invalidate historical GitHub Actions snapshots already stored for old runs: a user with appropriate permissions could still request a rerun of an original old Actions run, which would use that older workflow snapshot. Therefore the exact source-opening rule is also a **procedural prohibition on manual reruns**; full server-level enforcement would require GitHub Actions permissions/workflow management beyond this source patch. Do not claim that the code change makes every possible GitHub-level replay physically impossible.

Original E4/E5/E7, Safari14, C1 and C2 ecological conclusions and frozen numerical outputs remain unchanged. This incident is separate from the [minimal-model structural identifiability audit](POOL_STATE_DETECTION_IDENTIFICATION_AUDIT.md).
