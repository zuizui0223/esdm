"""Synthetic regression for frozen Colombia-outcrossfit plant predictors."""
from __future__ import annotations
import math
import unittest
from unittest.mock import patch

from scripts import neobat_plant_country_crossfit_pilot as m


class TestPlantCrossfitPilot(unittest.TestCase):
    def test_positive_and_background_require_other_targetgroup_plants(self):
        plants={
           ("Ficus insipida","CO"):{(1,1):{"D1"},(2,1):{"D1"}},
           ("Plant other","CO"):{(1,1):{"D2"},(3,1):{"D2"}}
        }
        data=m.country_cell_taxa(plants)
        observations=m.make_labeled_cells(data,"Ficus insipida","CO")
        self.assertEqual({x[0] for x in observations},{(1,1),(3,1)})
        self.assertEqual(dict((x[0],x[1]) for x in observations),
                         {(1,1):1,(3,1):0})
        self.assertTrue(all(x[2]==math.log(2) for x in observations))
        # A focal-only source observation must be excluded from BOTH
        # the supposed observed presence and any targetgroup background.
        self.assertNotIn((2,1),{x[0] for x in observations})

    def test_explicit_25km_holdout_boundary_overlap_exclusion(self):
        cells={
            ("Ficus insipida","CO"):{(1,1):{"c"}},
            ("Plant other","CO"):{(1,1):{"c"},(9,9):{"c"}},
            ("Ficus insipida","MX"):{(1,1):{"m"},(2,2):{"m"}},
            ("Plant other","MX"):{(1,1):{"m"},(2,2):{"m"},(3,3):{"m"}},
        }
        data=m.country_cell_taxa(cells)
        test_cells=set(data["CO"])
        training=m.make_labeled_cells(data,"Ficus insipida","MX",excluded_cells=test_cells)
        self.assertNotIn((1,1),{v[0] for v in training})
        self.assertIn((2,2),{v[0] for v in training})

    def test_known_truth_logistic_can_rank_heldout_plant_sources(self):
        # Covariates: true plant species is associated with environment
        # (NOT a claim about real Neotropical plants).
        try:
            import sklearn  # noqa: F401
        except ImportError:
            self.skipTest("sklearn not installed")
        train=[]
        test=[]
        for i in range(50):
            case=i%2==0
            env=0.9 if case else -0.9
            train.append((int(case),(env,env*2,env*3,math.log1p(2))))
        for i in range(12):
            case=i%2==0
            env=1.0 if case else -1.0
            test.append((int(case),(env,env*2,env*3,math.log1p(3))))
        scores=m.train_and_score(train,test)
        self.assertGreaterEqual(scores["abiotic_only"],0.99)
        self.assertGreaterEqual(scores["abiotic_plus_other_plant_effort"],0.99)

    def test_empty_pseudobackground_is_not_negative_absence(self):
        cells={
            ("Ficus insipida","CO"):{(1,1):{"d"}},
            ("Cecropia obtusifolia","CO"):{(1,1):{"d"}},
        }
        test=m.make_labeled_cells(m.country_cell_taxa(cells),"Ficus insipida","CO")
        self.assertEqual(len(test),1)
        self.assertEqual(test[0][1],1)


if __name__=="__main__":
    unittest.main()
