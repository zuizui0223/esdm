"""Source-free synthetic country equal effect and model known-truth tests."""
from __future__ import annotations
import math
import unittest

from scripts import neobat_106plant_17country_source_effort_transfer as m


class Test106x17SourceTransfer(unittest.TestCase):
    def test_frozen_universe_and_original_country_denominator(self):
        from scripts import neobat_plant_within_dataset_source_gate as s
        taxa,countries=s.fixed_names_and_countries()
        self.assertEqual(len(taxa),106)
        self.assertEqual(len(countries),17)
        self.assertEqual(m.N_FIXED,1802)

    def test_frozen_models_recover_abiotic_signal_without_effort_leak(self):
        data=[]
        test=[]
        for i in range(120):
            label=int(i%2==0)
            x=2.0 if label else -2.0
            data.append((label,(x,x*2,x/2,math.log1p(2))))
        for i in range(20):
            label=int(i%2==0)
            x=1.0 if label else -1.0
            test.append((label,(x,x*2,x/2,math.log1p(3))))
        out=m.measure_three(data,test)
        self.assertAlmostEqual(out["AUC_abiotic_only"],1.0)
        self.assertAlmostEqual(out["AUC_abiotic_plus_source_intensity"],1.0)
        self.assertAlmostEqual(out["AUC_source_intensity_only"],0.5)
        self.assertAlmostEqual(out["delta_AUC_abiotic_added_to_source_intensity"],0.5)

    def test_region_equal_weight_not_row_weight(self):
        def row(species,country,delta,status="EXPLORATORY_PLANT_COUNTRY_SOURCE_RANK_AUC"):
            return {
                "plant":species,"holdout_country":country,
                "delta_AUC_abiotic_added_to_source_intensity":delta,
                "status":status
            }
        # Country A has two plants and country B only one. Country-equal
        # mean must be ((0.1+0.1)/2+0.7)/2 = 0.4, NOT (0.9)/3.
        rows=[row("P1","A",.1),row("P2","A",.1),row("P1","B",.7),
              row("P2","B",None,"PLANT_SOURCE_MATCHED_HELDOUT_QUANTITY_STOP")]
        result=m.summarize(rows)
        self.assertAlmostEqual(result["per_plantcountry_equal_delta_AUC_mean"],.3)
        self.assertAlmostEqual(result["per_country_equal_delta_AUC_mean"],.4)
        self.assertEqual(result["source_matched_plant_country_rank_AUC_measured"],3)
        self.assertEqual(result["source_or_nodata_quantity_STOP_pairs"],m.N_FIXED-3)
        self.assertEqual(len(result["country_cluster_bootstrap_2000_percentile_interval"]),2)

    def test_zero_qualified_cannot_be_reported_as_ecology(self):
        with self.assertRaisesRegex(RuntimeError,"NO_PLANT_COUNTRY_HELDOUT_RANK_SCORES"):
            m.summarize([{"plant":"P","holdout_country":"A",
              "status":"PLANT_SOURCE_MATCHED_HELDOUT_QUANTITY_STOP"}])


if __name__=="__main__":
    unittest.main()
