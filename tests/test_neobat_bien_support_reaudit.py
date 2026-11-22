"""Verify descriptive support calculations and untouched frozen BIEN receipts."""
import copy
from pathlib import Path

import pytest

from scripts.neobat_bien_support_reaudit import (
    COUNTRIES, MODES, MIN_SUPPORT, build_audit, describe, load_receipts,
    audited_contrasts,
)


def row(pos, bg, auc, country="PE", frame="F1", taxon="Species a", dataset="Gentry"):
    return {"country": country, "taxon": taxon, "frame": frame,
            "datasource_id": "40", "dataset": dataset, "positive_cells": pos,
            "background_cells": bg, "auc": auc}


def test_one_pair_is_not_same_as_five_pairs():
    a = [row(1, 1, 1.0), row(2, 2, 0.25, taxon="Species b"),
         row(3, 4, 0.5, taxon="Species c"),
         row(5, 5, 0.6, country="EC", taxon="Species d")]
    assert [describe(a, n)["contrasts"] for n in MIN_SUPPORT] == [4, 3, 2, 1]
    assert describe(a, 1)["contrast_auc_median"] == .55
    assert describe(a, 2)["contrast_auc_median"] == .5
    assert describe(a, 2)["directions"] == {"below_half": 1, "at_half": 1, "above_half": 1}
    assert describe(a, 2)["countries"] == 2
    assert describe(a, 2)["country_frames"] == 2
    assert describe(a, 2)["source_dataset_ids"] == 1


def test_unknown_metric_is_null():
    d = describe([row(1, 1, 0.7)], 3)
    assert d["contrasts"] == 0
    assert d["contrast_auc_median"] is None
    assert d["contrast_auc_mean"] is None


@pytest.fixture(scope="module")
def actual():
    root = Path(__file__).resolve().parents[1]
    panel, receipts, _ = load_receipts(root)
    return panel, receipts


def test_all_original_model_outputs_are_reused_not_refitted(actual):
    panel, receipts = actual
    assert tuple(panel["country_order"]) == COUNTRIES
    assert len(receipts) == 10
    audit = build_audit(panel, receipts)
    assert audit["taxon_country_denominator_per_mode"] == 1060
    assert audit["interpretation"]["new_models_fitted_or_original_scores_modified"] is False
    assert audit["interpretation"]["source_independence_from_GBIF_verified"] is False
    primary = audit["modes"]["primary_2000_2025"]
    history = audit["modes"]["historical_undated_descriptive"]
    strict = audit["modes"]["known_precision_2000_2025"]
    assert primary["all_contrasts"] == 14
    assert primary["one_positive_one_background"] == 11
    assert strict["all_contrasts"] == 0
    assert history["all_contrasts"] == 133
    assert history["one_positive_one_background"] == 31
    assert [x["contrasts"] for x in primary["cell_support_lenses"]] == [14, 2, 0, 0]
    assert [x["contrasts"] for x in history["cell_support_lenses"]] == [133, 41, 26, 5]
    assert history["cell_support_lenses"][2]["countries"] == 3
    assert history["cell_support_lenses"][2]["country_frames"] == 5
    assert history["cell_support_lenses"][2]["source_dataset_ids"] == 3
    assert history["cell_support_lenses"][2]["contrast_auc_median"] < 0.5


def test_unexpected_auc_refused(actual):
    panel, receipts = actual
    modified = dict(receipts)
    copy_data = copy.deepcopy(receipts["BR"])
    item = next(r for r in copy_data["countries"]["BR"]["taxon_results"]
                if r["modes"]["primary_2000_2025"]["status"] == "EVALUABLE_EXPLORATORY")
    frame = next(r for r in item["modes"]["primary_2000_2025"]["frame_results"]
                 if r["status"] == "EVALUABLE_EXPLORATORY")
    frame["auc"] = 100
    modified["BR"] = copy_data
    with pytest.raises(ValueError, match="invalid AUC"):
        audited_contrasts(panel, modified)


def test_missing_species_denominator_refused(actual):
    panel, receipts = actual
    modified = dict(receipts)
    copy_data = copy.deepcopy(receipts["BR"])
    copy_data["countries"]["BR"]["taxon_results"].pop()
    modified["BR"] = copy_data
    with pytest.raises(ValueError, match="taxon coverage"):
        audited_contrasts(panel, modified)
