"""Synthetic-only source provenance and denominator tests for 106×17 plant gate."""
from __future__ import annotations
import unittest
from scripts import neobat_plant_within_dataset_source_gate as g


class TestWithinDatasetPlant(unittest.TestCase):
    def test_only_focal_original_dataset_with_other_taxa_can_supply_background(self):
        plants={
          ("Ficus insipida","CO"):{(1,1):{"D1"},(2,2):{"D2"}},
          ("Other","CO"):{(1,1):{"D1"},(3,3):{"D1"},(4,4):{"D3"}},
        }
        datasets=g.country_dataset_cells(plants)
        p,b,nd=g.source_matched_country("Ficus insipida","CO",plants,datasets)
        self.assertEqual(p,{(1,1)})
        self.assertEqual(b,{(3,3)})
        self.assertEqual(nd,1)
        self.assertNotIn((1,1),b)  # co-recording cannot be pseudo-absence

    def test_no_matching_dataset_does_not_imply_focal_absence(self):
        plants={
            ("Ficus insipida","CO"):{(1,1):{"D1"}},
            ("Other","CO"):{(2,2):{"D2"}},
        }
        p,b,nd=g.source_matched_country(
            "Ficus insipida","CO",plants,g.country_dataset_cells(plants))
        self.assertEqual((len(p),len(b),nd),(0,0,0))

    def test_training_excludes_all_heldout_observed_cells_even_if_other_country(self):
        matched={
          ("Plant","CO"):({(1,1),(2,1),(3,1),(4,1),(5,1)},
                          {(i,2) for i in range(5)},1),
          ("Plant","MX"):({(i,1) for i in range(23)},
                          {(i,2) for i in range(25)},2)
        }
        full={"CO":{(1,1),(0,2)}}
        x=g.fold_counts("Plant","CO",matched,full,["CO","MX"])
        self.assertEqual(x["train_focal_source_matched_recorded_cells"],22)
        self.assertEqual(x["train_source_matched_otherplant_bg_cells"],24)
        self.assertTrue(x["source_matched_training_quantity_qualified"])
        self.assertTrue(x["source_matched_heldout_scoring_quantity_qualified"])

    def test_all_fixed_1802_denominator_accounted_even_with_source_stops(self):
        names=list(g.PILOT_SENTINELS)+[f"Plant{i:03d}" for i in range(103)]
        countries=["CO"]+[f"C{i:02d}" for i in range(16)]
        universe=countries+[f"Z{i:02d}" for i in range(12)]
        rows,summary,bycountry,sentinels=g.analyse({},names,countries,universe)
        self.assertEqual(len(rows),1802)
        self.assertEqual(len(bycountry),17)
        self.assertEqual(len(sentinels),3)
        self.assertEqual(summary["source_matched_trainable_plant_country_pairs"],0)
        self.assertEqual(summary["countries_with_full_106_source_matched_trainability"],0)

    def test_frozen_real_names_and_countries_unchanged(self):
        names,countries=g.fixed_names_and_countries()
        self.assertEqual(len(names),106)
        self.assertEqual(len(countries),17)
        self.assertEqual(set(g.PILOT_SENTINELS).difference(names),set())


if __name__=="__main__":
    unittest.main()
