"""Source-free tests for a whole-GBIF-dataset embargo across country holdouts."""
from __future__ import annotations

import unittest

from scripts import neobat_plant_global_dataset_embargo_gate as m
from scripts import neobat_plant_within_dataset_source_gate as old


class TestGlobalDatasetSourceEmbargo(unittest.TestCase):
    def test_low_precision_heldout_source_still_embargoed(self):
        rows=[
            {"year":"2024","countryCode":"CO","datasetKey":"SHARED",
             "coordinateUncertaintyInMeters":""},
            {"year":"2021","countryCode":"MX","datasetKey":"SHARED",
             "coordinateUncertaintyInMeters":"100"},
            {"year":"1994","countryCode":"CO","datasetKey":"HISTORIC"}
        ]
        embargo, meta=m.country_keys_from_rows(rows,3)
        self.assertEqual(embargo["CO"],{"SHARED"})
        self.assertEqual(embargo["MX"],{"SHARED"})
        self.assertNotIn("HISTORIC",embargo["CO"])
        self.assertEqual(meta["original_plant_source_rows_read"],3)
        self.assertEqual(meta["total_unique_original_dataset_keys_any_country"],1)

    def test_source_matching_respects_global_source_embargo(self):
        cells={
            ("Plant A","MX"):{
                (1,1):{"SHARED"},
                (2,2):{"TRAIN_ONLY"}},
            ("Plant B","MX"):{
                (3,3):{"SHARED"},
                (4,4):{"TRAIN_ONLY"}},
        }
        source=old.country_dataset_cells(cells)
        p0,b0,n0=m.source_matched_country_excluding(
            "Plant A","MX",cells,source,set())
        self.assertEqual((p0,b0,n0),
                         ({(1,1),(2,2)},{(3,3),(4,4)},2))
        p,b,n=m.source_matched_country_excluding(
            "Plant A","MX",cells,source,{"SHARED"})
        self.assertEqual((p,b,n),({(2,2)},{(4,4)},1))
        p,b,n=m.source_matched_country_excluding(
            "Plant A","MX",cells,source,{"SHARED","TRAIN_ONLY"})
        self.assertEqual((p,b,n),(set(),set(),0))

    def test_full_original_species_country_roster_unchanged(self):
        species,countries=old.fixed_names_and_countries()
        self.assertEqual(len(species),106)
        self.assertEqual(len(countries),17)
        self.assertEqual(m.PASS_STATUS,
                         "EXPLORATORY_BOTANICAL_GLOBAL_DATASETKEY_EMBARGO_FEASIBILITY_ONLY")

    def test_source_record_count_must_match_original(self):
        with self.assertRaisesRegex(RuntimeError,"ROW_DENOMINATOR"):
            m.country_keys_from_rows(
                [{"year":"2024","countryCode":"CO","datasetKey":"X"}],2)

    def test_all_original_1802_prior_pair_rows_mandatory(self):
        with self.assertRaisesRegex(RuntimeError,"PRIOR_SOURCE_MATCH_FULL_1802_ROWS_REQUIRED"):
            m.audit({},{"CO":{"X"}},{},["Plant A"],["CO"],["CO"],{
                "status":m.SOURCE_STATUS,
                "plant_country_source_support":[]
            })


if __name__=="__main__":
    unittest.main()
