"""Synthetic source-free tests for NeoBat target-group background gate."""
from __future__ import annotations
import unittest
from scripts import neobat_bat_targetgroup_background_gate as g


class TestTargetGroupGate(unittest.TestCase):
    def test_country_cell_background_excludes_focal_presence(self):
        cells={
            ("Bat A","CO"):{(1,1):{"D1"},(2,1):{"D2"}},
            ("Bat B","CO"):{(1,1):{"D1"},(3,1):{"D1"}},
            ("Bat C","CO"):{(4,1):{"D3"}}
        }
        country=g.build_country_cells(cells)
        p,b=g.candidate_cells(country,"Bat A","CO")
        self.assertEqual(len(p),2)
        self.assertEqual(len(b),2)
        self.assertNotIn((1,1),b)
        self.assertEqual(b[(3,1)],{"D1"})

    def test_frozen_thresholds_and_within_country_dataset_matching(self):
        raw={}
        for cc in ("CO","MX"):
            pN=5 if cc=="CO" else 20
            bgN=6 if cc=="CO" else 22
            raw["Bat A",cc]={(i,1):{"D1"} for i in range(pN)}
            raw["Bat B",cc]={(i,2):{"D1"} for i in range(bgN)}
        result=g.count_fold(g.build_country_cells(raw),"Bat A","CO",["CO","MX"])
        self.assertTrue(result["quantity_qualified"])
        self.assertTrue(result["stricter_same_dataset_quantity_diagnostic"])
        self.assertEqual(result["test_bg_cells_sharing_focal_datasetKey_in_country"],6)
        self.assertEqual(result["train_bg_cells_sharing_focal_datasetKey_within_country"],22)
        self.assertEqual(result["test_other_bat_background_cells"],6)
        self.assertEqual(result["train_other_bat_background_cells"],22)

    def test_stop_when_background_missing_even_if_focal_source_cells_sufficient(self):
        cells={
          ("Bat A","CO"):{(i,1):{"D1"} for i in range(5)},
          ("Bat A","MX"):{(i,1):{"D1"} for i in range(20)},
          ("Bat B","MX"):{(i,2):{"D2"} for i in range(30)}
        }
        result=g.count_fold(g.build_country_cells(cells),"Bat A","CO",["CO","MX"])
        self.assertFalse(result["quantity_qualified"])
        self.assertEqual(result["test_other_bat_background_cells"],0)

    def test_dataset_matching_requires_local_focal_dataset(self):
        # The same dataset in another country is not enough for the heldout
        # test country's source-matched background diagnostic.
        cells={
          ("Bat A","CO"):{(i,1):{"CO_A"} for i in range(5)},
          ("Bat B","CO"):{(i,2):{"MX_A"} for i in range(5)},
          ("Bat A","MX"):{(i,1):{"MX_A"} for i in range(20)},
          ("Bat B","MX"):{(i,2):{"MX_A"} for i in range(20)}
        }
        result=g.count_fold(g.build_country_cells(cells),"Bat A","CO",["CO","MX"])
        self.assertTrue(result["quantity_qualified"])
        self.assertFalse(result["stricter_same_dataset_quantity_diagnostic"])
        self.assertEqual(result["test_bg_cells_sharing_focal_datasetKey_in_country"],0)

    def test_unlisted_holdout_fails_closed(self):
        with self.assertRaisesRegex(ValueError,"HELDOUT_NOT_IN_FIXED_COUNTRIES"):
            g.count_fold({},"Bat A","CO",["MX"])


if __name__=="__main__":
    unittest.main()
