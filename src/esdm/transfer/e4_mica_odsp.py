"""ODSP serialization for the frozen E4 MICA empirical endpoint."""
from __future__ import annotations

from collections.abc import Mapping

from .odsp_adapter import (
    ODSPInformationLevel,
    ODSPTransferBundle,
    build_odsp_transfer_bundle,
)


EXPECTED_RESULT_ID = "e4-mica-exact-sparse-result-v1"
EXPECTED_PROGRAMME = "E4_MICA_SPARSE_NUTS"
EXPECTED_STATUS = "E4_SPARSE_EMPIRICAL_RESULT"
EXPECTED_ENDPOINT = "E3_MICA_REDUCED_NO_DIRECT_STATE_CALIBRATION"
EXPECTED_ROWS = 733
EXPECTED_FIXTURE_FINGERPRINT = (
    "2876b9f85bb34ddb600c39cd412fe196b3c78f47fa7306bca63c30245d740a23"
)
EXPECTED_TRAIN_HASH = (
    "41bd70aa1f913bcb1c988f6c5cdae3441ed978d4ee0f6791bcfc497290710646"
)
EXPECTED_HELDOUT_HASH = (
    "0ed3fb9e96b1323a4290b7cb92621d219e317b8b916201a1b2665db4a272b1d9"
)


def _e4_mica_records(
    result: Mapping[str, object],
) -> tuple[list[dict[str, object]], str | None]:
    if result.get("result_id") != EXPECTED_RESULT_ID:
        raise ValueError(f"expected {EXPECTED_RESULT_ID}")
    if result.get("programme_id") != EXPECTED_PROGRAMME:
        raise ValueError("E4 MICA programme drifted")
    if result.get("endpoint_id") != EXPECTED_ENDPOINT:
        raise ValueError("E4 MICA endpoint drifted")
    if result.get("status") != EXPECTED_STATUS:
        raise ValueError("E4 ODSP export requires completed empirical result")

    decision = result.get("decision")
    if not isinstance(decision, Mapping):
        raise ValueError("E4 result is missing decision")
    if decision.get("sampling_gate_passed") is not True:
        raise ValueError("E4 ODSP export requires sampling_gate_passed=true")

    boundary = result.get("response_boundary")
    if not isinstance(boundary, Mapping):
        raise ValueError("E4 result is missing response_boundary")
    if boundary.get("state_calibration_stream_present_in_fit") is not False:
        raise ValueError(
            "E4 ODSP export requires reduced endpoint without state calibration"
        )
    if boundary.get("new_external_response_gets") != 0:
        raise ValueError("E4 ODSP export requires immutable captured response")

    if result.get("fixture_fingerprint_sha256") != EXPECTED_FIXTURE_FINGERPRINT:
        raise ValueError("E4 fixture fingerprint drifted")

    compaction = result.get("compaction")
    if not isinstance(compaction, Mapping):
        raise ValueError("E4 result is missing exact-compaction record")
    train = compaction.get("training")
    heldout = compaction.get("heldout")
    if not isinstance(train, Mapping) or not isinstance(heldout, Mapping):
        raise ValueError("E4 compaction sections are missing")
    if int(train.get("compact_context_count", -1)) != 11531:
        raise ValueError("E4 training compact context count drifted")
    if int(heldout.get("compact_context_count", -1)) != 10168:
        raise ValueError("E4 heldout compact context count drifted")
    if train.get("retained_keys_sha256") != EXPECTED_TRAIN_HASH:
        raise ValueError("E4 training retained-key hash drifted")
    if heldout.get("retained_keys_sha256") != EXPECTED_HELDOUT_HASH:
        raise ValueError("E4 heldout retained-key hash drifted")

    serialization = result.get("odsp_serialization")
    if not isinstance(serialization, Mapping):
        raise ValueError("E4 result is missing ODSP serialization boundary")
    if int(serialization.get("row_count", -1)) != EXPECTED_ROWS:
        raise ValueError("E4 ODSP row count drifted")
    if serialization.get("absolute_scores_serialized") is not True:
        raise ValueError("E4 absolute score serialization is required")
    if serialization.get("gain_only_serialization") is not False:
        raise ValueError("E4 gain-only serialization is forbidden")
    if serialization.get("same_scored_cells_across_models") is not True:
        raise ValueError("E4 compared models must use identical scored cells")

    rows = result.get("heldout_deployment_scores")
    if not isinstance(rows, list) or len(rows) != EXPECTED_ROWS:
        raise ValueError("E4 ODSP export requires exactly 733 heldout rows")

    required = {
        "deploymentID",
        "full_heldout_log_score",
        "activity_knockout_heldout_log_score",
        "state_knockout_heldout_log_score",
    }
    prepared: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, Mapping):
            raise ValueError(f"E4 heldout row {index} must be an object")
        missing = sorted(required - set(raw))
        if missing:
            raise ValueError(f"E4 heldout row {index} missing fields: {missing!r}")
        deployment_id = str(raw["deploymentID"]).strip()
        if not deployment_id or deployment_id in seen:
            raise ValueError("E4 deploymentID values must be unique non-empty strings")
        seen.add(deployment_id)
        prepared.append(
            {
                "deploymentID": deployment_id,
                "endpoint_group": "MICA_MUSKRAT",
                "full_heldout_log_score": raw["full_heldout_log_score"],
                "activity_knockout_heldout_log_score": raw[
                    "activity_knockout_heldout_log_score"
                ],
                "state_knockout_heldout_log_score": raw[
                    "state_knockout_heldout_log_score"
                ],
            }
        )
    return prepared, None


def build_e4_mica_activity_odsp_bundle(
    result: Mapping[str, object],
) -> ODSPTransferBundle:
    """Export E4 empirical activity information as one descriptive endpoint."""

    records, git_sha = _e4_mica_records(result)
    return build_odsp_transfer_bundle(
        endpoint_id="esdm_e4_mica_activity_transfer_v1",
        levels=(
            ODSPInformationLevel(
                name="suitability_state",
                information=("suitability", "state"),
                source_score_field="activity_knockout_heldout_log_score",
            ),
            ODSPInformationLevel(
                name="suitability_state_activity",
                information=("suitability", "state", "activity"),
                source_score_field="full_heldout_log_score",
            ),
        ),
        records=records,
        group_field="endpoint_group",
        row_id_field="deploymentID",
        block_field="deploymentID",
        analysis_mode="descriptive",
        filtration_frozen_before_outcome_scoring=True,
        source_schema=EXPECTED_RESULT_ID,
        source_git_sha=git_sha,
        group_semantics=(
            "single exploratory MICA empirical endpoint; east-heldout deploymentID "
            "is a within-endpoint resampling block"
        ),
    )


def build_e4_mica_state_odsp_bundle(
    result: Mapping[str, object],
) -> ODSPTransferBundle:
    """Export E4 empirical state information as one descriptive endpoint."""

    records, git_sha = _e4_mica_records(result)
    return build_odsp_transfer_bundle(
        endpoint_id="esdm_e4_mica_state_transfer_v1",
        levels=(
            ODSPInformationLevel(
                name="suitability_activity",
                information=("suitability", "activity"),
                source_score_field="state_knockout_heldout_log_score",
            ),
            ODSPInformationLevel(
                name="suitability_activity_state",
                information=("suitability", "activity", "state"),
                source_score_field="full_heldout_log_score",
            ),
        ),
        records=records,
        group_field="endpoint_group",
        row_id_field="deploymentID",
        block_field="deploymentID",
        analysis_mode="descriptive",
        filtration_frozen_before_outcome_scoring=True,
        source_schema=EXPECTED_RESULT_ID,
        source_git_sha=git_sha,
        group_semantics=(
            "single exploratory MICA empirical endpoint; east-heldout deploymentID "
            "is a within-endpoint resampling block"
        ),
    )
