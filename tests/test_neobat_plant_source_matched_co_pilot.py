"""Synthetic source-dataset matched plant transfer source restrictions."""
from __future__ import annotations
import unittest
from scripts import neobat_plant_source_matched_co_pilot as m


class TestDatasetMatchedPilot(unittest.TestCase):
    def test_co_observed_source_cells_only(self):
        cells={
          "CO":{
            (1,1):{"Ficus insipida","Other"},
            (2,2):{"Ficus insipida"},
            (3,3):{"Other"},
            (4,4):{"Other"},
          }
        }
        matches={
          ("Ficus insipida","CO"):({(1,1),(2,2)},{(3,3)},1),
        }
        rows,nd=m.source_filtered_observation_cells(
            cells,matches,"Ficus insipida","CO")
        self.assertEqual(nd,1)
        self.assertEqual({x[0] for x in rows},{(1,1),(3,3)})
        self.assertEqual(dict((x[0],x[1]) for x in rows),
                         {(1,1):1,(3,3):0})
        self.assertNotIn((2,2),{x[0] for x in rows})
        self.assertNotIn((4,4),{x[0] for x in rows})

    def test_crossborder_cell_excluded_from_training(self):
        cells={"MX":{
            (1,1):{"Ficus insipida","Other"},
            (2,2):{"Ficus insipida","Other"},
            (3,3):{"Other"}
        }}
        matches={("Ficus insipida","MX"):({(1,1),(2,2)},{(3,3)},1)}
        rows,_=m.source_filtered_observation_cells(cells,matches,
            "Ficus insipida","MX",excluded={(1,1)})
        self.assertEqual({x[0] for x in rows},{(2,2),(3,3)})

    def test_unfrozen_source_pair_is_terminal(self):
        with self.assertRaisesRegex(ValueError,"SOURCE_MISSING"):
            m.source_filtered_observation_cells({},{}, "Ficus insipida","CO")


if __name__=="__main__":
    unittest.main()
