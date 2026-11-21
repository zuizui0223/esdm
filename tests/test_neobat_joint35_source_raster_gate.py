"""Pure synthetic tests for strict joint 35-plant source/raster training audit."""
from __future__ import annotations
import unittest
from unittest.mock import patch

from scripts import neobat_joint35_source_raster_gate as m
from scripts import neobat_plant_within_dataset_source_gate as old


class TestJoint35(unittest.TestCase):
    def sample(self):
        plants={
            ("Plant A","MX"):{
                (1,1):{"BANNED"},
                (2,2):{"TRAIN_ONLY"}},
            ("Plant B","MX"):{
                (1,1):{"BANNED"},
                (2,2):{"TRAIN_ONLY"},
                (4,4):{"TRAIN_ONLY"}},
            ("Plant C","CO"):{
                (9,9):{"BANNED"}},
        }
        return plants,old.country_dataset_cells(plants)

    def test_source_heldout_dataset_ban_also_excludes_effort_features(self):
        plants,index=self.sample()
        kept=m.unbanned_plant_taxa_for_holdout(index,{"BANNED"},"CO")
        self.assertNotIn("CO",kept)
        self.assertNotIn((1,1),kept["MX"])
        self.assertEqual(kept["MX"][(2,2)],{"Plant A","Plant B"})
        self.assertEqual(kept["MX"][(4,4)],{"Plant B"})

    def test_joint_trainability_has_complete_source_class_denominators(self):
        plants,index=self.sample()
        allowed=m.unbanned_plant_taxa_for_holdout(index,{"BANNED"},"CO")
        # Pure fake raster: all labeled rows are valid source cells.
        with patch.object(m.pilot,"dataframe_rows",
              side_effect=lambda labeled, rasters, transform, cache:
                   ([(label,(10.,20.,30.,effort)) for cell,label,effort
                     in labeled],0)):
            out=m.evaluate_cell_trainability(
                plants,index,allowed,"Plant A","CO",["CO","MX"],
                {"BANNED"},{(9,9)},None,None,{})
        self.assertEqual(out["train_raw_positive_source_recorded_cells"],1)
        self.assertEqual(out["train_raw_targetgroup_background_cells"],1)
        self.assertEqual(out["train_raster_valid_focal_recorded_cells"],1)
        self.assertEqual(out["train_raster_valid_targetgroup_background_cells"],1)
        self.assertFalse(out["complete_train_20plus_each_class"])

    def test_nodata_exclusion_is_counted_for_source_positive(self):
        plants,index=self.sample()
        allowed=m.unbanned_plant_taxa_for_holdout(index,{"BANNED"},"CO")
        def screen(labeled, *_):
            return ([(label,(1.,2.,3.,effort))
                      for cell,label,effort in labeled if label==0],
                    sum(label for cell,label,effort in labeled))
        with patch.object(m.pilot,"dataframe_rows",side_effect=screen):
            out=m.evaluate_cell_trainability(
                plants,index,allowed,"Plant A","CO",["CO","MX"],
                {"BANNED"},{(9,9)},None,None,{})
        self.assertEqual(out["training_source_abiotic_nodata_excluded_cells"],1)
        self.assertEqual(out["train_raster_valid_focal_recorded_cells"],0)
        self.assertEqual(out["train_raster_valid_targetgroup_background_cells"],1)

    def test_no_Ecological_rank_result_is_ever_returned_by_gate(self):
        self.assertEqual(m.PASS,
            "EXPLORATORY_FIXED35_JOINT_DISJOINT_DATASET_AND_RASTER_TRAINABILITY")
        self.assertEqual(m.STOP,"FIXED35_JOINT_SOURCE_AND_RASTER_INPUT_STOP")


if __name__=="__main__":
    unittest.main()
