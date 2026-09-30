"""Response-blind E5 candidate qualification.

This module implements the frozen G1-G7 design gates without reading any focal
response values. Unknown or incomplete metadata fail closed.
"""
from __future__ import annotations

from collections.abc import Mapping


PASS_STATUS = "E5_CANDIDATE_QUALIFIED_PRE_RESPONSE"
FAIL_STATUS = "E5_CANDIDATE_NOT_QUALIFIED"


def _truth(section: Mapping[str, object], *keys: str) -> bool:
    return all(section.get(key) is True for key in keys)


def qualify_e5_candidate_metadata(manifest: Mapping[str, object]) -> dict[str, object]:
    """Evaluate the frozen E5 metadata-only gates.

    The input is deliberately design-only. If the manifest declares that focal
    response values were opened or used for selection, qualification fails hard.
    """
    candidate_id = str(manifest.get("candidate_id", "")).strip()
    if not candidate_id:
        raise ValueError("candidate_id must be non-empty")

    firewall = manifest.get("response_firewall")
    if not isinstance(firewall, Mapping):
        raise ValueError("response_firewall is required")
    if firewall.get("focal_response_opened") is not False:
        raise ValueError("E5 candidate qualification requires unopened focal response")
    if firewall.get("response_values_used_for_selection") is not False:
        raise ValueError("E5 candidate selection may not use focal response values")

    independence = manifest.get("independence", {})
    schema = manifest.get("schema", {})
    crossed = manifest.get("crossed_domain", {})
    detection = manifest.get("detection", {})
    physical = manifest.get("physical_replication", {})
    temporal = manifest.get("temporal_support", {})
    frozen = manifest.get("model_freeze", {})
    for name, value in (
        ("independence", independence),
        ("schema", schema),
        ("crossed_domain", crossed),
        ("detection", detection),
        ("physical_replication", physical),
        ("temporal_support", temporal),
        ("model_freeze", frozen),
    ):
        if not isinstance(value, Mapping):
            raise ValueError(f"{name} must be an object")

    gates: dict[str, dict[str, object]] = {}

    g1 = _truth(
        independence,
        "new_response_dataset",
        "not_mica_derivative",
        "not_snapshot_japan_derivative",
    )
    gates["G1_INDEPENDENT_SOURCE"] = {
        "passed": g1,
        "reason": (
            "independent response dataset firewall satisfied"
            if g1 else
            "new independent response status is incomplete or fails the frozen firewall"
        ),
    }

    schema_keys = (
        "deployment_id",
        "physical_location_id",
        "effort_interval",
        "event_time_schema",
        "taxon_identity",
        "geography",
        "source_or_protocol",
    )
    g2 = _truth(schema, *schema_keys)
    gates["G2_SCHEMA_EFFORT_TIME"] = {
        "passed": g2,
        "reason": (
            "all frozen schema/effort/time fields are response-blind and parseable"
            if g2 else
            "one or more frozen schema/effort/time requirements are absent or unverified"
        ),
    }

    g3 = crossed.get("qualified_crossing") is True
    gates["G3_CROSSED_DOMAIN"] = {
        "passed": g3,
        "reason": (
            "geography and source/protocol are separable under a frozen acceptable design"
            if g3 else
            "geography/source crossing is absent or not yet established"
        ),
    }

    g4 = detection.get("separately_identifiable_effective_detection") is True
    gates["G4_DETECTION_IDENTIFIABILITY"] = {
        "passed": g4,
        "reason": (
            "effective detection has an independent identifying path"
            if g4 else
            "effective detection lacks a verified independent identifying path"
        ),
    }

    try:
        n_train = int(physical.get("training_independent_locations", -1))
        n_holdout = int(physical.get("heldout_independent_locations", -1))
        n_overlap = int(physical.get("heldout_training_location_overlap", -1))
    except (TypeError, ValueError):
        n_train = n_holdout = n_overlap = -1
    g5 = (
        physical.get("repeated_deployments_nested_under_location") is True
        and n_train >= 20
        and n_holdout >= 10
        and n_overlap == 0
    )
    gates["G5_PHYSICAL_REPLICATION"] = {
        "passed": g5,
        "training_independent_locations": n_train,
        "heldout_independent_locations": n_holdout,
        "heldout_training_location_overlap": n_overlap,
        "reason": (
            "physical replication and strict heldout geography satisfy frozen minima"
            if g5 else
            "physical-location replication or strict heldout geometry fails/has not been established"
        ),
    }

    try:
        train_months = int(temporal.get("training_distinct_calendar_months", -1))
        heldout_months = int(temporal.get("heldout_distinct_calendar_months", -1))
    except (TypeError, ValueError):
        train_months = heldout_months = -1
    g6 = (
        train_months >= 6
        and heldout_months >= 6
        and temporal.get("training_has_day_and_night_effort") is True
        and temporal.get("heldout_has_day_and_night_effort") is True
        and temporal.get("seasonal_coverage_overlaps") is True
    )
    gates["G6_TEMPORAL_SUPPORT"] = {
        "passed": g6,
        "training_distinct_calendar_months": train_months,
        "heldout_distinct_calendar_months": heldout_months,
        "reason": (
            "temporal support satisfies frozen month/day-night/season overlap requirements"
            if g6 else
            "frozen temporal-support requirements fail or are not yet established"
        ),
    }

    g7 = _truth(
        frozen,
        "activity_detection_structure_frozen",
        "geography_or_source_by_diel_frozen",
        "season_by_diel_frozen",
    )
    gates["G7_MODEL_FREEZE"] = {
        "passed": g7,
        "reason": (
            "required activity/detection and diel-nonstationarity structure is frozen"
            if g7 else
            "selected-candidate model structure is not yet fully frozen"
        ),
    }

    all_pass = all(bool(value["passed"]) for value in gates.values())
    return {
        "schema_version": 1,
        "programme_id": "E5_INDEPENDENT_ACTIVITY_DETECTION",
        "candidate_id": candidate_id,
        "status": PASS_STATUS if all_pass else FAIL_STATUS,
        "all_pre_response_gates_passed": all_pass,
        "gates": gates,
        "response_boundary": {
            "focal_response_opening_authorized": False,
            "model_fitting_authorized": False,
            "qualified_status_requires_separate_child_contract": True,
            "qualified_status_requires_separate_response_authorization": True,
        },
    }
