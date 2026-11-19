"""Synthetic no-response tests for fixed 106-plant raster trainability gate."""
from __future__ import annotations

import copy
import unittest
from scripts import neobat_full106_raster_trainability_gate as g


def fixture():
    countries=[f"C{i:02d}" for i in range(17)]
    plants=[f"P{i:03d}" for i in range(106)]
    full={
        "status":"EXPLORATORY_ORIGINAL_106x17_PLANT_SOURCE_EFFORT_TRANSFER_COMPLETE",
        "frozen_106_species_universe_sha256":g.V2SHA,
        "plant_country_source_rank_results":[
            {"plant":p,"holdout_country":cc,
             "train_source_matched_focal_cells":25,
             "train_source_matched_target_background_cells":60}
            for p in plants for cc in countries
        ]
    }
    matched={
        "status":"DOI_PLANT_106x17_WITHIN_DATASETKEY_SOURCE_MATCH_FEASIBILITY",
        "summary":{"source_matched_trainable_plant_country_pairs":1802}
    }
    pairs=[{"bat":f"B{i}","holdout_country":countries[i%17]} for i in range(84)]
    partner={
        "status":"SOURCE_ONLY_V2_106_PLANT_REFERENCE_AND_N1_FEASIBILITY",
        "folds":[dict(x,v2_106_plant_input_qualified=i<79) for i,x in enumerate(pairs)]
    }
    bats={
        "status":"DOI_BAT_TARGETGROUP_BACKGROUND_INPUT_FEASIBILITY_ONLY",
        "folds":[dict(x,quantity_qualified=i<79) for i,x in enumerate(pairs)]
    }
    return full,matched,bats,partner


class TestFull106Trainability(unittest.TestCase):
    def test_all_106_per_country_truly_trainable(self):
        data=g.analyse(*fixture())
        self.assertEqual(data["original_106x17_plant_country_pairs"],1802)
        self.assertEqual(data["countries_with_all_106_plant_model_training_ready"],17)
        self.assertEqual(data["full_fixed_106_plant_training_and_bat_source_qualified_pairs"],79)

    def test_one_untrainable_plant_in_country_blocks_entire_fixed_universe(self):
        a,b,c,d=fixture()
        for r in a["plant_country_source_rank_results"]:
            if r["plant"]=="P000" and r["holdout_country"]=="C00":
                r["train_source_matched_focal_cells"]=19
                break
        result=g.analyse(a,b,c,d)
        self.assertEqual(result["countries_with_all_106_plant_model_training_ready"],16)
        self.assertEqual(result["full_fixed_106_plant_training_and_bat_source_qualified_pairs"],74)
        failing=next(r for r in result["per_country"] if r["country"]=="C00")
        self.assertIn("P000",failing["untrainable_plant_names"])
        self.assertEqual(failing["train_positive_cells_lt20"],1)

    def test_duplicate_plant_country_or_frozen_source_denominator_stops(self):
        a,b,c,d=fixture()
        a["plant_country_source_rank_results"][-1]=a["plant_country_source_rank_results"][0]
        with self.assertRaisesRegex(ValueError,"PLANT_COUNTRY_KEYS_DUPLICATE_OR_INCOMPLETE"):
            g.analyse(a,b,c,d)

    def test_original_79_bat_source_candidates_unchanged(self):
        a,b,c,d=fixture()
        d["folds"][80]["v2_106_plant_input_qualified"]=True
        with self.assertRaisesRegex(ValueError,"PREVIOUS_79_BAT_FOLDS_INTERSECTION_DRIFT"):
            g.analyse(a,b,c,d)


if __name__=="__main__":
    unittest.main()
