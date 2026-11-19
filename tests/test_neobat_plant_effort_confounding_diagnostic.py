"""Synthetic-only conditional rank and effort-only diagnostic regression."""
from __future__ import annotations
import math
import unittest

from scripts import neobat_plant_effort_confounding_diagnostic as m


class TestPlantEffortConditional(unittest.TestCase):
    def test_exact_count_pair_fraction_and_diagnostics(self):
        y=[1,0,1,0]
        score=[0.9,0.1,0.8,0.2]
        n=[1,1,2,2]
        r=m.conditional_auc(y,score,n,binned=False)
        self.assertEqual(r["comparable_positive_background_pairs"],2)
        self.assertAlmostEqual(r["comparable_pair_fraction"],0.5)
        self.assertAlmostEqual(r["auc"],1.0)
        self.assertEqual(r["source_effort_strata_with_both_classes"],2)

    def test_no_cross_intensity_comparisons_must_not_create_false_auc(self):
        y=[1,1,0,0]
        score=[0.2,0.4,0.8,0.9]
        n=[1,1,20,20]
        r=m.conditional_auc(y,score,n,binned=False)
        self.assertIsNone(r["auc"])
        self.assertEqual(r["comparable_positive_background_pairs"],0)
        self.assertEqual(r["comparable_pair_fraction"],0)

    def test_frozen_bins(self):
        self.assertEqual([m.bin_group(x) for x in (1,2,3,4,7,8,100)],
                         [0,1,1,2,2,3,3])
        y=[1,0,1,0]
        score=[0.9,0.2,0.8,0.3]
        n=[2,3,7,4]
        r=m.conditional_auc(y,score,n,binned=True)
        self.assertEqual(r["comparable_positive_background_pairs"],2)
        self.assertAlmostEqual(r["auc"],1.0)

    def test_effort_only_can_recover_known_effort_signal(self):
        train=[]
        test=[]
        for i in range(100):
            yes=(i%2==0)
            effort=math.log1p(8 if yes else 1)
            train.append((int(yes),(1+(i%5)/20,50+(i%4)/10,200+(i%3),effort)))
        for i in range(40):
            yes=(i%2==0)
            effort=math.log1p(8 if yes else 1)
            test.append((int(yes),(1+(i%5)/20,50+(i%4)/10,200+(i%3),effort)))
        r=m.model_diagnostics(train,test)
        self.assertGreater(r["AUC_effort_only"],0.99)
        self.assertGreaterEqual(r["AUC_abiotic_plus_otherplant_effort"],0.99)
        self.assertIsNone(r["conditional_same_exact_effort_abiotic_plus_effort"]["auc"])


if __name__=="__main__":
    unittest.main()
