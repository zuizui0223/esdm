"""Source-only fixed 35×17 WorldClim input counts and bat fold accounting.

All original data-derived tests read only already committed aggregate JSON;
no raw botanical occurrences or raster pixels need to be opened.
"""
from __future__ import annotations
import copy
import unittest
from scripts import neobat_v3_source35_raster_gate as m


class TestSource35RasterGate(unittest.TestCase):
    def originals(self):
        v3=m.read(m.D/"v3_source_disjoint35_partner_gate.json")
        original=m.read(m.D/"plant_106x17_global_source_embargo.json")
        return v3,original

    def test_locked_35_species_17_holdouts_and_595_pairs(self):
        v3,full=self.originals()
        plants,holdouts,prior=m.freeze_inputs(v3,full)
        self.assertEqual(len(plants),35)
        self.assertEqual(len(holdouts),17)
        self.assertEqual(len(prior),1802)
        self.assertTrue(all(prior[plant,country]["train_quantity_eligible_after_global_dataset_embargo"]
                       for plant in plants for country in holdouts))

    def test_source_35_name_sha_mutation_fails_closed(self):
        v3,full=self.originals()
        changed=copy.deepcopy(v3)
        changed["source_disjoint_global35_plant_names"][0]="Plant nonexistent"
        with self.assertRaisesRegex(RuntimeError,"GLOBAL_SOURCE35_NAMES_OR_HOLDOUTS_DRIFT"):
            m.freeze_inputs(changed,full)

    def test_original_source_pair_missing_fails_closed(self):
        v3,full=self.originals()
        changed=copy.deepcopy(full)
        changed["plant_country_input_gates"].pop()
        with self.assertRaisesRegex(RuntimeError,"PREVIOUS_SOURCE_DISJOINT_1802_GATE_NOT_COMPLETE"):
            m.freeze_inputs(v3,changed)

    def test_complete_raster_fixture_intersects_original_84_folds_without_selection(self):
        v3,full=self.originals()
        plants,holdouts,prior=m.freeze_inputs(v3,full)
        fake=[{
            "plant":p,"holdout_country":c,
            "train_quantity_qualified_after_raster":True,
            "train_and_heldout_source_quantity_qualified_after_raster":False
        } for p in plants for c in holdouts]
        o=m.report(fake,v3,plants,holdouts,{},{"sha256":"synthetic"},{})
        self.assertEqual(o["summary"]["fixed_35_plant_17_country_pairs"],595)
        self.assertEqual(o["summary"]["countries_with_all35_source_disjoint_post_raster_trainable"],17)
        self.assertEqual(o["summary"]["source_disjoint35_post_raster_training_qualified_pairs"],595)
        self.assertEqual(o["summary"]["new_source_disjoint35_raster_and_bat_source_qualified_folds"],63)
        self.assertEqual(len(o["original_84_bat_country_folds"]),84)
        self.assertFalse(o["no_bat_or_plant_model_fitted"] is False)

    def test_incomplete_raster_fixture_stops_country_wide_fixed35_use(self):
        v3,full=self.originals()
        names,holdouts,_=m.freeze_inputs(v3,full)
        fake=[{
            "plant":p,"holdout_country":c,
            "train_quantity_qualified_after_raster":not(p==names[0] and c==holdouts[0]),
            "train_and_heldout_source_quantity_qualified_after_raster":False
        } for p in names for c in holdouts]
        o=m.report(fake,v3,names,holdouts,{},{"sha256":"synthetic"},{})
        self.assertEqual(o["summary"]["countries_with_all35_source_disjoint_post_raster_trainable"],16)
        self.assertEqual(o["summary"]["source_disjoint35_post_raster_training_qualified_pairs"],594)
        self.assertEqual(len(o["original_84_bat_country_folds"]),84)


if __name__=="__main__":
    unittest.main()
