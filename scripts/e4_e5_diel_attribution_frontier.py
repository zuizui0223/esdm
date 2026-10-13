"""Model-free E4/E5 diel attribution frontier from an immutable E4 summary.

This reads only the previously frozen post-result aggregate, does not access raw
observations, does not fit models, and does not qualify or rescue E5 candidates.
The output is an algebraic *sensitivity identity*, not ecological identification.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Sequence

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    REPOSITORY_ROOT
    / "docs"
    / "replication"
    / "E4_MICA_POSTRESULT_DOMAIN_SHIFT_SUPPLEMENT.json"
)
DEFAULT_RELATIVE_DETECTION = (0.2, 0.25, 0.5, 1.0, 2.0)


def attribution_frontier(
    training_observed_night_day: float,
    heldout_observed_night_day: float,
    relative_detection_diel_changes: Sequence[float] = DEFAULT_RELATIVE_DETECTION,
) -> dict:
    """Compute passage-by-detection factorizations of an observed ratio change.

    R_obs,r = R_pass,r * R_det,r for the *same* effort-weighted cohort,
    where R_det is a constructed effective recorded-event-yield factor, NOT
    independently measured per-pass detection in E4. Between regimes C=P*Q.
    All Q scenarios are hypothetical, not calibrated corrections.
    """
    ratios = (float(training_observed_night_day), float(heldout_observed_night_day))
    qs = tuple(float(x) for x in relative_detection_diel_changes)
    if any(not math.isfinite(x) or x <= 0 for x in (*ratios, *qs)):
        raise ValueError("all ratios and hypothesized detection changes must be finite and positive")
    if not qs:
        raise ValueError("at least one hypothetical detection scenario is required")

    observed_change = ratios[1] / ratios[0]
    return {
        "training_observed_night_day_rate_ratio": ratios[0],
        "heldout_observed_night_day_rate_ratio": ratios[1],
        "relative_observed_diel_contrast": observed_change,
        "reciprocal_observed_diel_contrast": 1.0 / observed_change,
        "log_relative_observed_diel_contrast": math.log(observed_change),
        "if_passage_diel_contrast_unchanged_required_relative_detection": observed_change,
        "if_detection_diel_contrast_unchanged_required_relative_passage": observed_change,
        "equal_log_contributions_hypothetical_factor": math.sqrt(observed_change),
        "hypothetical_scenarios": [
            {
                "relative_detection_diel_contrast": q,
                "required_relative_passage_diel_contrast": observed_change / q,
            }
            for q in qs
        ],
        "interpretation": "EXACT_AGGREGATE_ACCOUNTING_NONIDENTIFIED_NOT_A_FIT",
    }


def from_frozen_e4_summary(source: Path = SOURCE) -> dict:
    """Read exclusively the frozen *aggregate* E4 result and check provenance."""
    result = json.loads(source.read_text(encoding="utf-8"))
    if (
        result.get("status") != "POSTRESULT_EXPLORATORY_SUPPLEMENT"
        or result.get("source_result", {}).get("workflow_run_id") != 36622802225
        or result.get("source_result", {}).get("artifact_id") != 11059622869
    ):
        raise ValueError("not the pinned E4 post-result aggregate source")

    boundaries = result["analysis_boundary"]
    forbidden = (
        "new_model_fit", "posterior_refit", "retuning", "backend_switch",
        "claim_promotion", "frozen_e4_result_changed",
    )
    if any(boundaries.get(k) is not False for k in forbidden):
        raise ValueError("E4 post-result analysis boundary is not intact")

    observed = result["raw_diel_rate_shift"]
    a = observed["training_state_annotated"]["night_day_rate_ratio"]
    b = observed["heldout_D"]["night_day_rate_ratio"]
    frontier = attribution_frontier(a, b)
    return {
        "source": source.name,
        "frozen_e4_run_id": result["source_result"]["workflow_run_id"],
        "frozen_e4_artifact_id": result["source_result"]["artifact_id"],
        "source_cohorts": ["training_state_annotated", "heldout_D"],
        "analysis_status": "POSTRESULT_ALGEBRAIC_SENSITIVITY_ONLY",
        "does_not_identify_activity_or_detection": True,
        "raw_biological_rows_opened": 0,
        "model_fits": 0,
        "original_E5_G4_qualification_changed": False,
        "frontier": frontier,
    }


def main() -> None:
    print(json.dumps(from_frozen_e4_summary(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
