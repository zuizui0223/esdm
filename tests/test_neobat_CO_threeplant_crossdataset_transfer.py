"""Source-free contract tests for source-disjoint plant effort features and roles."""
from __future__ import annotations
import unittest

from scripts import neobat_CO_threeplant_crossdataset_transfer as m
from scripts import neobat_plant_within_dataset_source_gate as ds


class TestSourceDisjointThreePlants(unittest.TestCase):
    def test_embargoed_original_sources_do_not_enter_training_effort(self):
        original={
          "MX":{
            "SHARED":{
              (1,1):{"Ficus insipida","Plant B"},
              (2,2):{"Plant C"}
            },
            "TRAIN_ONLY":{
              (1,1):{"Ficus insipida"},
              (3,3):{"Plant D","Plant E"}
            }
          },
          "CO":{
            "SHARED":{(4,4):{"Plant X","Plant Y"}}
          }
        }
        cleaned=m.unbanned_country_plant_taxa(original,{"SHARED"})
        self.assertNotIn("CO",cleaned)
        self.assertEqual(cleaned["MX"][(1,1)],{"Ficus insipida"})
        self.assertNotIn((2,2),cleaned["MX"])
        self.assertEqual(cleaned["MX"][(3,3)],{"Plant D","Plant E"})

    def test_training_uses_only_unbanned_source_cohorts(self):
        raw={
            ("Ficus insipida","MX"):{
                (1,1):{"SHARED"},
                (2,2):{"TRAIN_ONLY"}
            },
            ("Other plant","MX"):{
                (3,3):{"SHARED"},
                (4,4):{"TRAIN_ONLY"},
                (2,2):{"TRAIN_ONLY"}
            },
        }
        sources=ds.country_dataset_cells(raw)
        unbanned=m.unbanned_country_plant_taxa(sources,{"SHARED"})
        observations,nds=m.training_source_cells(
            "Ficus insipida","MX",raw,sources,unbanned,
            {"SHARED"},{(99,99)})
        # The TRAIN_ONLY source supports a focal+other cell (2,2)
        # and an other-only background (4,4).
        self.assertEqual(nds,1)
        self.assertEqual({r[0] for r in observations},{(2,2),(4,4)})
        self.assertEqual(dict((r[0],r[1]) for r in observations),
                         {(2,2):1,(4,4):0})
        self.assertTrue(all(r[0]!=(1,1) for r in observations))

    def test_excluded_holdout_border_cells_not_in_training(self):
        raw={
            ("Ficus insipida","MX"):{(2,2):{"TRAIN_ONLY"}},
            ("Other plant","MX"):{
                (2,2):{"TRAIN_ONLY"},(4,4):{"TRAIN_ONLY"}
            }
        }
        sources=ds.country_dataset_cells(raw)
        clean=m.unbanned_country_plant_taxa(sources,set())
        observed,_=m.training_source_cells(
            "Ficus insipida","MX",raw,sources,clean,
            set(),{(2,2)})
        self.assertTrue(all(x[0]!=(2,2) for x in observed))
        self.assertEqual(len(observed),1)
        self.assertEqual(observed[0][1],0)

    def test_fixed_three_species_contract(self):
        from scripts import neobat_plant_country_crossfit_pilot as pilot
        self.assertEqual(pilot.SENTINELS,(
            "Cecropia obtusifolia","Ficus insipida","Piper aduncum"
        ))
        self.assertEqual(pilot.HOLDOUT,"CO")
        self.assertEqual(m.PASS,"EXPLORATORY_POSTHOC_CO_3PLANT_DISJOINT_SOURCE_TRANSFER")


if __name__=="__main__":
    unittest.main()
