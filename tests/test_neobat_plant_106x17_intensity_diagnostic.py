"""No-network synthetic correctness guards for full 106x17 observational-process audit."""
from __future__ import annotations

import math
import unittest
from scripts import neobat_plant_106x17_intensity_diagnostic as f
from scripts import neobat_plant_source_matched_co_pilot as old


class TestFullSourceIntensity(unittest.TestCase):
    def test_per_source_cell_selection_matches_original_three_sentinel_code(self):
        focal="Ficus insipida"
        country="CO"
        obs={country:{
            (1,1):{focal,"Plant X"},
            (2,2):{focal},
            (3,3):{"Plant X"},
            (4,4):{"Plant Y"}
        }}
        matches={(focal,country):({(1,1),(2,2)},{(3,3),(4,4)},2)}
        new,ds=f.qualified_observations(focal,country,obs,matches)
        prior,nprior=old.source_filtered_observation_cells(obs,matches,focal,country)
        self.assertEqual(ds,nprior)
        self.assertEqual(sorted(new),sorted(prior))
        self.assertNotIn((2,2),{x[0] for x in new})

    def test_focal_plant_never_in_background(self):
        focal="Ficus insipida"
        obs={"CO":{(1,1):{focal,"Plant X"}}}
        matched={(focal,"CO"):({(1,1)},{(1,1)},1)}
        with self.assertRaisesRegex(RuntimeError,"FOCAL_OBSERVATION_LEAKS_INTO_BACKGROUND"):
            f.qualified_observations(focal,"CO",obs,matched)

    def test_known_truth_model_recovers_increment_versus_equal_effort(self):
        try:
            import sklearn  # noqa
        except ImportError:
            self.skipTest("scikit-learn unavailable")
        train=[]
        test=[]
        for i in range(80):
            y=int(i%2==0)
            env=1 if y else -1
            train.append((y,(env,env*.7,env*.3,math.log1p(2))))
        for i in range(20):
            y=int(i%2==0)
            env=1 if y else -1
            test.append((y,(env,env*.7,env*.3,math.log1p(3))))
        d=f.known_truth_score(train,test)
        self.assertEqual(d["AUC_abiotic_only"],1)
        self.assertEqual(d["AUC_effort_only"],.5)
        self.assertEqual(d["AUC_abiotic_plus_otherplant_effort"],1)
        self.assertAlmostEqual(d["delta_added_abiotic_beyond_source_intensity"],.5)
        self.assertEqual(d["exact_intensity_conditional_auc"]["comparable_pair_fraction"],1)

    def test_exploratory_full_denominator_aggregation_preserves_stops(self):
        rows=[]
        for name in ("Plant A","Plant B"):
            for country in ("BR","CO"):
                status=f.STATUS_STOP if (name,country)==("Plant B","BR") else f.STATUS_FITTED
                row={"plant":name,"holdout_country":country,"status":status}
                if status==f.STATUS_FITTED:
                    row.update({
                        "AUC_abiotic_only":.4,
                        "AUC_effort_only":.75,
                        "AUC_abiotic_plus_otherplant_effort":.80,
                        "delta_added_abiotic_beyond_source_intensity":.05,
                        "exact_intensity_conditional_auc":{"comparable_pair_fraction":.2}
                    })
                rows.append(row)
        out=f.summarise(rows)
        self.assertEqual(out["all_predeclared_species_country_pairs"],4)
        self.assertEqual(out["source_and_model_fit_eligible"],3)
        self.assertEqual(out["source_or_raster_stopped"],1)
        self.assertAlmostEqual(out["equal_country_mean_added_abiotic_delta"],.05)
        self.assertEqual(out["countries_with_any_successful_fit"],2)

    def test_no_exploratory_effect_if_all_fold_results_stopped(self):
        with self.assertRaisesRegex(RuntimeError,"NO_FITTED_COUNTRY"):
            f.summarise([
                {"plant":"Plant A","holdout_country":"CO","status":f.STATUS_STOP}
            ])


if __name__=="__main__":
    unittest.main()
