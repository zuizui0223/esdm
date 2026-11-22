"""Read-only, post-hoc effective-cell support audit of frozen NeoBat BIEN scores.

No plant/BIEN/GBIF downloads, model refits, reweighting, thresholds for
acceptance, significance tests or pooled prediction scores are performed.
Contrasts share geographic cells and training data: descriptive counts only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

COUNTRIES = ("BR", "CR", "EC", "GF", "GT", "HN", "NI", "PA", "PE", "SV")
MODES = ("primary_2000_2025", "known_precision_2000_2025", "historical_undated_descriptive")
MIN_SUPPORT = (1, 2, 3, 5)  # Reporting lenses, NOT eligibility thresholds.
ROOT_REL = Path("docs/replication/neobat")
PANEL_NAME = "bien_fixed10_summary_20261122.json"
MANIFEST_NAME = "bien_fixed10_artifact_provenance_20261122.json"
OLD_NAME = "bien_external_plant_diagnostic_20261121.json"


def require(condition, explanation):
    if not condition:
        raise ValueError(explanation)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_receipts(root):
    """Reopen exact public receipts; verify hashes before using any score."""
    root = Path(root)
    panel = read_json(root / ROOT_REL / PANEL_NAME)
    manifest = read_json(root / ROOT_REL / MANIFEST_NAME)
    require(tuple(panel["country_order"]) == COUNTRIES, "panel country universe changed")
    require(len(panel["plant_taxa"]) == 106 and len(set(panel["plant_taxa"])) == 106,
            "plant universe is not the frozen 106")
    require(panel["taxon_country_results_per_mode"] == 1060, "panel denominator changed")
    prior_info = manifest["prior_CR_PA_reuse"]["files"][OLD_NAME]
    prior_path = root / prior_info["path"]
    require(sha256(prior_path) == prior_info["sha256"], "prior CR/PA hash mismatch")
    old = read_json(prior_path)
    require(set(old["countries"]) == {"CR", "PA"}, "prior countries changed")
    receipts = {cc: old for cc in ("CR", "PA")}
    for cc in COUNTRIES:
        if cc in ("CR", "PA"):
            continue
        members = manifest["countries"][cc]["files"]
        candidates = [f for f in members if f["path"].endswith(f"bien_fixed10_{cc}_diagnostic_20261122.json")]
        require(len(candidates) == 1, f"{cc}: expected exact diagnostic manifest member")
        info = candidates[0]
        path = root / info["path"]
        require(sha256(path) == info["sha256"], f"{cc}: diagnostic hash mismatch")
        receipts[cc] = read_json(path)
    require(set(receipts) == set(COUNTRIES), "country receipts incomplete")
    return panel, receipts, {cc: (old["fixed106_taxa_sha256"] if cc in ("CR", "PA") else
             receipts[cc]["fixed106_taxa_sha256"]) for cc in COUNTRIES}


def audited_contrasts(panel, receipts):
    """Validate fixed denominator and extract only already-scored frame AUCs."""
    taxa = set(panel["plant_taxa"])
    output = {mode: [] for mode in MODES}
    for cc in COUNTRIES:
        receipt = receipts[cc]
        require(receipt["fixed106_taxa_sha256"] == panel["fixed106_taxa_sha256"],
                f"{cc}: frozen taxon roster digest changed")
        d = receipt["countries"][cc]
        require(d["country"] == cc, f"{cc}: country payload mismatch")
        frames = {f["frame_id"]: f for f in d["frames"]}
        require(len(frames) == len(d["frames"]), f"{cc}: repeated frame ID")
        rows = d["taxon_results"]
        require(len(rows) == 106 and {r["taxon"] for r in rows} == taxa,
                f"{cc}: taxon coverage changed")
        require(len({r["taxon"] for r in rows}) == len(rows), f"{cc}: duplicate taxon")
        for mode in MODES:
            contrasts = []
            statuses = Counter()
            seen = set()
            for row in rows:
                val = row["modes"][mode]
                statuses[val["status"]] += 1
                scored = 0
                for f in val["frame_results"]:
                    key = (row["taxon"], f["frame_id"])
                    require(key not in seen, f"{cc}/{mode}: duplicate taxon frame")
                    seen.add(key)
                    require(f["frame_id"] in frames, f"{cc}/{mode}: unknown frame")
                    if f["status"] != "EVALUABLE_EXPLORATORY":
                        require(f["auc"] is None, f"{cc}/{mode}: unscored frame has AUC")
                        continue
                    scored += 1
                    a, p, b = f["auc"], f["positive_cells"], f["background_cells"]
                    require(type(a) in (float, int) and math.isfinite(a) and 0 <= a <= 1,
                            f"{cc}/{mode}: invalid AUC")
                    require(type(p) is int and type(b) is int and p >= 1 and b >= 1,
                            f"{cc}/{mode}: invalid cell support")
                    frame = frames[f["frame_id"]]
                    contrasts.append({"country": cc, "taxon": row["taxon"],
                                      "frame": f["frame_id"], "datasource_id": frame["datasource_id"],
                                      "dataset": frame["dataset"],
                                      "positive_cells": p, "background_cells": b, "auc": a})
                require((val["status"] == "EVALUABLE_EXPLORATORY") == (scored > 0),
                        f"{cc}/{mode}: taxon status disagrees with scored frames")
            expected = panel["countries"][cc]["modes"][mode]
            require(sum(statuses.values()) == 106 and dict(statuses) ==
                    {k: v for k, v in expected["taxon_status_counts"].items() if v},
                    f"{cc}/{mode}: panel taxon status mismatch")
            require(len(contrasts) == expected["estimable_taxon_frame_contrasts"],
                    f"{cc}/{mode}: panel contrast count mismatch")
            output[mode].extend(contrasts)
    return output


def median(data):
    if not data:
        return None
    values = sorted(data)
    n = len(values)
    return values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2


def describe(rows, minimum):
    xs = [r for r in rows if r["positive_cells"] >= minimum and
          r["background_cells"] >= minimum]
    by_direction = {"below_half": sum(r["auc"] < .5 for r in xs),
                    "at_half": sum(r["auc"] == .5 for r in xs),
                    "above_half": sum(r["auc"] > .5 for r in xs)}
    return {"minimum_cells_in_each_class": minimum, "contrasts": len(xs),
            "distinct_taxa": len({r["taxon"] for r in xs}),
            "countries": len({r["country"] for r in xs}),
            "country_frames": len({(r["country"], r["frame"]) for r in xs}),
            "source_dataset_ids": len({(r["datasource_id"], r["dataset"]) for r in xs}),
            "contrast_auc_median": median([r["auc"] for r in xs]),
            "contrast_auc_mean": (sum(r["auc"] for r in xs) / len(xs)) if xs else None,
            "directions": by_direction}


def build_audit(panel, receipts):
    results = audited_contrasts(panel, receipts)
    modes = {}
    for mode, rows in results.items():
        sources = {}
        for ds in sorted({(r["datasource_id"], r["dataset"]) for r in rows}):
            rr = [r for r in rows if (r["datasource_id"], r["dataset"]) == ds]
            sources[f"{ds[0]}: {ds[1]}"] = {
                "contrasts": len(rr),
                "countries": len({r["country"] for r in rr}),
                "three_cells_each_class": sum(r["positive_cells"] >= 3 and
                                              r["background_cells"] >= 3 for r in rr),
                "contrast_auc_median": median([r["auc"] for r in rr])}
        modes[mode] = {"all_contrasts": len(rows),
                       "one_positive_one_background": sum(r["positive_cells"] == 1 and
                                                          r["background_cells"] == 1 for r in rows),
                       "cell_support_lenses": [describe(rows, n) for n in MIN_SUPPORT],
                       "by_source_dataset": sources}
    return {"schema_version": 1, "status": "POSTHOC_DESCRIPTIVE_REAUDIT_COMPLETE",
            "frozen_panel": "docs/replication/neobat/" + PANEL_NAME,
            "taxa": 106, "countries": list(COUNTRIES), "taxon_country_denominator_per_mode": 1060,
            "modes": modes,
            "interpretation": {
                "posthoc_reporting_lenses_not_selection_thresholds": True,
                "auc_median_is_over_frame_contrasts_not_taxon_means": True,
                "geographic_frames_are_not_independent_replicates": True,
                "datasource_labels_do_not_prove_source_independence": True,
                "repeated_cells_can_cross_taxa_and_frames": True,
                "source_independence_from_GBIF_verified": False,
                "bat_predictions_or_trophic_M3_estimated": False,
                "new_models_fitted_or_original_scores_modified": False,
                "confidence_intervals_pvalues_or_pooled_auc_computed": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    panel, receipts, _ = load_receipts(args.repo_root)
    payload = json.dumps(build_audit(panel, receipts), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
