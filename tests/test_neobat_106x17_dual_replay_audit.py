"""Source-free synthetic full-denominator compare guards for two NeoBat implementations."""
from __future__ import annotations

import copy
import unittest
from scripts import neobat_106x17_dual_replay_audit as audit


def two():
    heads={
        "AUC_abiotic_only":0.62,
        "AUC_source_intensity_only":0.77,
        "AUC_abiotic_plus_source_intensity":0.80,
        "delta_AUC_abiotic_added_to_source_intensity":0.03,
        "exact_same_intensity_heldout_AUC":0.58,
        "exact_same_intensity_comparable_pair_fraction":0.06
    }
    src={
        "status":audit.A_STATUS,
        "original_plant_GBIF_DOI":"10.15468/dl.xwc5zf",
        "original_plant_ZIP_SHA256":"example-same-archive",
        "frozen_106_species_universe_sha256":audit.V2_SHA,
        "previous_3sentinel_CO_AUCs_exactly_replayed":True,
        "summary":{
            "source_matched_plant_country_rank_AUC_measured":647,
            "per_country_equal_delta_AUC_mean":0.02539130916740804
        },
        "plant_country_source_rank_results":[]
    }
    dst={
        "status":audit.B_STATUS,
        "GBIF_plant_original_DOI":"10.15468/dl.xwc5zf",
        "GBIF_plant_original_zip_sha256":"example-same-archive",
        "frozen_106_plant_universe_sha256":audit.V2_SHA,
        "original_3_sentinel_CO_model_AUC_and_cells_exactly_replayed":True,
        "summary":{
            "source_and_model_fit_eligible":647,
            "equal_country_mean_added_abiotic_delta":0.025391309167408036
        },
        "all_1802_fold_rows":[]
    }
    countries=[f"C{i:02d}" for i in range(17)]
    for i in range(1802):
        name=f"Plant{i//17:03d}"
        cc=countries[i%17]
        yes=i<647
        a={
            "plant":name,"holdout_country":cc,
            "status":"EXPLORATORY_PLANT_COUNTRY_SOURCE_RANK_AUC" if yes else
                "PLANT_SOURCE_MATCHED_HELDOUT_QUANTITY_STOP",
            "train_source_matched_focal_cells":60,
            "train_source_matched_target_background_cells":100,
            "heldout_source_matched_focal_cells":10 if yes else 1,
            "heldout_source_matched_target_background_cells":20,
            "heldout_abiotic_nodata_cell_exclusions":3
        }
        b={
            "plant":name,"holdout_country":cc,
            "status":"EXPLORATORY_SOURCE_MATCHED_RANK_AUC" if yes else
                "FIXED_FOLD_SOURCE_OR_RASTER_QUANTITY_STOP",
            "train_positive_recorded_cells":60,
            "train_pseudo_background_cells":100,
            "heldout_positive_recorded_cells":10 if yes else 1,
            "heldout_pseudo_background_cells":20,
            "heldout_raster_nodata_removed_cells":3
        }
        for key,value in heads.items():
            a[key]=value if yes else None
        for akey,bkey in (
            ("AUC_abiotic_only","AUC_abiotic_only"),
            ("AUC_source_intensity_only","AUC_effort_only"),
            ("AUC_abiotic_plus_source_intensity","AUC_abiotic_plus_otherplant_effort"),
            ("delta_AUC_abiotic_added_to_source_intensity","delta_added_abiotic_beyond_source_intensity"),
        ):
            b[bkey]=a[akey]
        b["exact_intensity_conditional_auc"]={
            "auc":a["exact_same_intensity_heldout_AUC"],
            "comparable_pair_fraction":a["exact_same_intensity_comparable_pair_fraction"]
        } if yes else None
        src["plant_country_source_rank_results"].append(a)
        dst["all_1802_fold_rows"].append(b)
    return src,dst


class TestExactReplay(unittest.TestCase):
    def test_success_all_1802(self):
        a,b=two()
        r=audit.compare(a,b)
        self.assertEqual(r["status"],"FULL_1802_FOLD_TWO_IMPLEMENTATION_AGGREGATE_REPLAY_MATCH")
        self.assertEqual(r["same_source_rank_fitted_pairs"],647)
        self.assertEqual(r["both_source_or_quantity_STOP_pairs"],1155)
        self.assertEqual(r["status_pair_mismatches"],0)
        self.assertEqual(r["max_absolute_numeric_difference"],0)

    def test_single_auc_drift_not_allowed(self):
        a,b=two()
        b["all_1802_fold_rows"][22]["AUC_effort_only"]+=0.0001
        with self.assertRaisesRegex(RuntimeError,"CROSS_IMPLEMENTATION_DISCREPANCY"):
            audit.compare(a,b)

    def test_negative_source_stop_cannot_be_promoted(self):
        a,b=two()
        b["all_1802_fold_rows"][-1]["status"]="EXPLORATORY_SOURCE_MATCHED_RANK_AUC"
        with self.assertRaisesRegex(RuntimeError,"CROSS_IMPLEMENTATION_DISCREPANCY"):
            audit.compare(a,b)

    def test_different_test_source_cell_count_fails(self):
        a,b=two()
        b["all_1802_fold_rows"][1]["heldout_positive_recorded_cells"]+=1
        with self.assertRaisesRegex(RuntimeError,"CROSS_IMPLEMENTATION_DISCREPANCY"):
            audit.compare(a,b)

    def test_source_origin_change_fails(self):
        a,b=two()
        b["GBIF_plant_original_zip_sha256"]="different"
        with self.assertRaisesRegex(RuntimeError,"SOURCE_DOI_HASH_OR_UNIVERSE_NOT_IDENTICAL"):
            audit.compare(a,b)


if __name__=="__main__":
    unittest.main()
